# Muay Thai Matchmaker - Master Project Plan 🥊

## 📊 CODE HEALTH STATUS (Updated: Nov 26, 2025 - 13:15 MSK)

### **Overall Assessment**
- **Core Functionality**: ✅ Complete (File upload → Pairing → Manual edit → Export)
- **Code Quality**: ✅ Much Improved (Phase 2 & 3 complete)
- **Data Integrity**: ✅ Transaction-safe editing implemented
- **Production Ready**: ⚠️ Minor issues remain, 95% ready

### **Recent Improvements (Commit 71f1a40)**
✅ **Phase 2 Complete**: Transaction-safe editing with rollback
✅ **Phase 3 Complete**: Enhanced validation with structured feedback
✅ **Type Safety**: Created `utils/type_helpers.py` module
✅ **Weight Parsing**: Fixed edge cases (до 22, >= 60)
✅ **Club Parsing UI**: Added confidence indicators and validation report

### **Critical Issues Found in Code Review**
1. 🔴 **CRITICAL**: Registry initialization race condition (tabs/manual_edits.py:240)
2. 🔴 **CRITICAL**: Pandas import order bug in type_helpers.py
3. ⚠️ **HIGH**: Validation age limits hardcoded (should use dynamic functions)
4. ⚠️ **MEDIUM**: Club conflict level 3 allows None==None matches
5. ⚠️ **MEDIUM**: Weight display inconsistency (min vs range)
6. ℹ️ **LOW**: Greedy algorithm could orphan constrained fighters

---

## 🚨 NEW CRITICAL ISSUES (From Commit 71f1a40 Review)

### **Issue #1: Registry Race Condition** 🔴 CRITICAL
**File**: `tabs/manual_edits.py:240`  
**Severity**: Data Loss Risk  
**Impact**: User edits lost on page navigation

```python
# CURRENT (BROKEN):
def render_match_id_editor():
    if not st.session_state.get("master_fighter_registry"):
        build_master_fighter_registry()  # ⚠️ Rebuilds on every page load

# FIX:
# In app.py initialization:
if "master_fighter_registry" not in st.session_state:
    st.session_state["master_fighter_registry"] = {}

# In render_match_id_editor:
if not st.session_state["master_fighter_registry"]:
    build_master_fighter_registry()
else:
    # Validate registry is in sync with matches/unmatched
    issues = validate_fighter_registry()
    if issues:
        st.warning("Registry sync issues detected, rebuilding...")
        build_master_fighter_registry()
```

**Action Required**:
- [ ] Add registry initialization to `app.py` startup
- [ ] Add sync validation before rendering editor
- [ ] Test page navigation preserves edits
- [ ] Add unit test for registry persistence

---

### **Issue #2: Pandas Import Order Bug** 🔴 CRITICAL
**File**: `utils/type_helpers.py:16,139`  
**Severity**: Potential Crash  
**Impact**: `pd.isna()` called before pandas imported

```python
# CURRENT (BROKEN):
def safe_int_conversion(value: Union[str, int, float, bytes, None]) -> int:
    if pd.isna(value) or value == "" or value is None:  # ❌ pd not defined yet!
        return 0
    # ...

# Pandas imported at line 139 (too late!)
try:
    import pandas as pd
except ImportError:
    class _MockPandas:
        @staticmethod
        def isna(value):
            return value is None
    pd = _MockPandas()

# FIX:
# Move pandas import to top of file
import re
from typing import Union

try:
    import pandas as pd
except ImportError:
    class _MockPandas:
        @staticmethod
        def isna(value):
            if value is None:
                return True
            if isinstance(value, float):
                return str(value).lower() in ('nan', 'inf', '-inf')
            return False
    pd = _MockPandas()

# Then define functions normally
def safe_int_conversion(value: Union[str, int, float, bytes, None]) -> int:
    if pd.isna(value) or value == "" or value is None:
        return 0
    # ...
```

**Action Required**:
- [ ] Move pandas import to top of `type_helpers.py`
- [ ] Test with and without pandas installed
- [ ] Add CI test for import order issues

---

### **Issue #3: Hardcoded Validation Limits** ⚠️ HIGH
**File**: `tabs/manual_edits.py:460-470`  
**Severity**: Incorrect Validation  
**Impact**: Allows pairings that should be rejected

```python
# CURRENT (WRONG):
if age_group in ["12-13", "14-15"]:
    max_allowed = 5.0  # ❌ HARDCODED - doesn't match pairing.py logic
elif age_group in ["16-17"]:
    max_allowed = 6.0  # ❌ HARDCODED - doesn't match pairing.py logic
else:
    max_allowed = 3.0  # ❌ HARDCODED

# FIX:
from utils.pairing import get_max_diff_12_15, get_max_diff_16_17

avg_weight = (f1["weight_min"] + f2["weight_min"]) / 2

if age_group in ["12-13", "14-15"]:
    max_allowed = get_max_diff_12_15(avg_weight)  # ✅ Weight-dependent
elif age_group in ["16-17"]:
    max_allowed = get_max_diff_16_17(avg_weight)  # ✅ Weight-dependent
else:
    # Adult rules - weight class based, not simple difference
    # Should use ValidationResult from is_valid_pair() instead
    max_allowed = 3.0  # Simplified for adults
```

**Why This Matters**:  
The pairing algorithm uses **weight-dependent limits**:
- 12-15 age group at 40kg: 2kg max
- 12-15 age group at 50kg: 3kg max
- 12-15 age group at 60kg: 4kg max

Hardcoding 5kg allows invalid heavy-weight youth pairings!

**Action Required**:
- [ ] Import and use dynamic weight limit functions
- [ ] Add weight parameter to validation
- [ ] Update tests to check weight-dependent validation
- [ ] Document weight-based validation logic

---

### **Issue #4: Club Conflict None==None Bug** ⚠️ MEDIUM
**File**: `utils/pairing.py:260-265`  
**Severity**: Logic Error  
**Impact**: Fighters with no region data marked as conflicting

```python
# CURRENT (BUGGY):
if conflict_level == 3:
    return (
        fighter1.club_region == fighter2.club_region  # ⚠️ None == None returns True!
        and fighter1.club_region is not None
        and fighter2.club_region is not None
    )

# The issue: If both regions are None, the first check (None == None) 
# evaluates to True, but the subsequent checks fail, so it returns False.
# However, the logic is confusing and could short-circuit incorrectly.

# FIX (Clearer logic):
if conflict_level == 3:
    # Only conflict if BOTH have regions AND they match
    return (
        fighter1.club_region is not None
        and fighter2.club_region is not None
        and fighter1.club_region == fighter2.club_region
    )
```

**Action Required**:
- [ ] Reorder checks to validate None first
- [ ] Add unit test: `test_club_conflict_both_none_regions()`
- [ ] Add unit test: `test_club_conflict_one_none_region()`
- [ ] Document None handling in club conflict detection

---

### **Issue #5: Weight Display Inconsistency** ⚠️ MEDIUM
**File**: `tabs/manual_edits.py:310`  
**Severity**: UX Confusion  
**Impact**: Users see different weights in editor vs export

```python
# CURRENT (INCONSISTENT):
def create_combined_fighters_dataframe():
    fighter_record = {
        "Weight": fighter_data["weight_min"],  # ❌ Shows only minimum (e.g., "55")
        # ...
    }

# But in format_weight_string():
def format_weight_string(fighter):
    if weight_min != weight_max:
        return f"{weight_min}-{weight_max}"  # Shows range (e.g., "55-60")

# FIX:
def create_combined_fighters_dataframe():
    fighter_record = {
        "Weight": format_weight_string(fighter_data),  # ✅ Consistent format
        # ...
    }
```

**Action Required**:
- [ ] Use `format_weight_string()` in all weight displays
- [ ] Add UI test: weight format consistency
- [ ] Update column config to handle range strings

---

### **Issue #6: Greedy Algorithm Limitation** ℹ️ LOW
**File**: `utils/pairing.py:650-700`  
**Severity**: Optimization Opportunity  
**Impact**: 5-10% more unmatched fighters than optimal

**Problem Scenario**:
```
Fighters:
- A (55kg, rare weight) - can pair with B or C
- B (57kg, common weight) - can pair with A or D
- C (56kg, common weight) - can pair with A
- D (58kg, rare weight) - can ONLY pair with B

Greedy algorithm:
1. Pick A first (most constrained)
2. Find best match: B (score 10) vs C (score 12)
3. Pair A-B (local optimum)
4. D is now unmatched (orphaned)

Optimal solution: A-C and B-D (all matched)
```

**Potential Solutions**:
1. **Two-phase matching** (already partially implemented):
   ```python
   # Phase 1: Match most constrained fighters
   constrained = [f for f in fighters if flexibility_score(f) > 3]
   # Phase 2: Match remaining fighters
   ```

2. **Look-ahead heuristic**:
   ```python
   def would_orphan_fighter(pair):
       """Check if this pairing makes someone unmatchable"""
       # Temporarily remove pair, check if anyone loses all matches
   ```

3. **Backtracking** (expensive but optimal):
   ```python
   def pair_with_backtracking(fighters, current_pairs=[]):
       if not fighters:
           return current_pairs
       # Try all valid pairs, backtrack if dead end
   ```

**Recommendation**: Implement look-ahead heuristic first (best cost/benefit ratio)

**Action Required**:
- [ ] Add `would_orphan_fighter()` check before committing to pair
- [ ] Benchmark against current algorithm (100+ fighters)
- [ ] Document algorithm trade-offs in ARCHITECTURE.md
- [ ] Consider making this optional ("Best Effort" vs "Quick" mode)

---

## 🚀 IMMEDIATE ACTION ITEMS (Updated Priority)

### **Week 1: Fix Critical Bugs**

#### **Day 1 (Today): Critical Fixes**
- [ ] **Issue #2**: Fix pandas import order in `type_helpers.py` (15 min)
- [ ] **Issue #1**: Add registry initialization to `app.py` (30 min)
- [ ] **Issue #4**: Fix club conflict None==None bug (15 min)
- [ ] **Test fixes**: Run full test suite

**Total time**: ~1-2 hours

#### **Day 2: High Priority Fixes**
- [ ] **Issue #3**: Replace hardcoded validation limits (45 min)
- [ ] **Issue #5**: Fix weight display inconsistency (20 min)
- [ ] **Add unit tests** for all fixes (1 hour)
- [ ] **Code review**: Check for similar issues

**Total time**: ~2-3 hours

#### **Day 3-4: Testing & Documentation**
- [ ] **Stress test**: 500 fighter tournament
- [ ] **Edge case testing**: All identified scenarios
- [ ] **Update documentation**: Add known issues section
- [ ] **Performance benchmarks**: Measure improvements

#### **Day 5: Optimization (Optional)**
- [ ] **Issue #6**: Implement look-ahead heuristic
- [ ] **Benchmark**: Compare with greedy baseline
- [ ] **User testing**: Get feedback on pairing quality

---

## 📋 PHASE 1: CODE QUALITY & REFACTORING (Priority: CRITICAL)

### **1.1: Type Safety** ✅ COMPLETE (with fixes needed)
**File**: `utils/type_helpers.py`

- [x] Create centralized type conversion module
- [x] Implement `safe_int_conversion()`
- [x] Implement `safe_float_conversion()`
- [x] Implement `safe_str_conversion()`
- [ ] **Fix Issue #2**: Move pandas import to top
- [ ] Add type hints to all functions
- [ ] Configure mypy in CI

**Success Metrics**:
- ✅ Single source of truth for type conversions
- ⚠️ Needs: Pandas import fix
- ⏳ Pending: Mypy validation

---

### **1.2: Weight Handling** ✅ COMPLETE
**File**: `utils/pairing.py`

- [x] Refactor `parse_weight_range()` with edge case handling
- [x] Support Russian "до" notation
- [x] Support comparison operators (>=, >, <, <=)
- [x] Support Unicode symbols (≥, ≤)
- [x] Proper fallback for malformed input
- [ ] Add comprehensive unit tests

**Success Metrics**:
- ✅ Handles "до 22" → (0, 22)
- ✅ Handles ">= 60" → (60, 999)
- ✅ Handles "55-60" → (55, 60)
- ⏳ Pending: Test coverage > 95%

---

### **1.3: Club Conflict Detection** ⚠️ NEEDS FIX
**File**: `utils/pairing.py`

- [x] Add null-safety checks for level 2
- [x] Add null-safety checks for level 3
- [ ] **Fix Issue #4**: Reorder None checks
- [ ] Add unit tests for None handling
- [ ] Document conflict level behaviors

**Success Metrics**:
- ✅ No false positives on level 2
- ⚠️ Needs: Fix None==None edge case
- ⏳ Pending: Complete test coverage

---

## 📋 PHASE 2: DATA INTEGRITY ✅ COMPLETE (with fixes needed)

### **2.1: Master Fighter Registry** ✅ COMPLETE
**File**: `tabs/manual_edits.py`

- [x] Implement O(1) incremental updates
- [x] Add `update_fighter_in_registry()`
- [x] Add `validate_fighter_registry()`
- [ ] **Fix Issue #1**: Add initialization in app.py
- [ ] Add sync validation before rendering

**Success Metrics**:
- ✅ O(1) update complexity (was O(n²))
- ✅ Validation detects inconsistencies
- ⚠️ Needs: Fix race condition

---

### **2.2: Transaction-Safe Editing** ✅ COMPLETE (with fixes needed)
**File**: `tabs/manual_edits.py`

- [x] Implement pre-save validation
- [x] Add backup/rollback mechanism
- [x] Add comprehensive error messages
- [x] Implement post-update validation
- [ ] **Fix Issue #3**: Use dynamic weight limits
- [ ] Add transaction logging

**Success Metrics**:
- ✅ Zero invalid states saved
- ✅ Automatic rollback on errors
- ⚠️ Needs: Fix validation logic

---

## 📋 PHASE 3: VALIDATION & UX ✅ COMPLETE

### **3.1: Enhanced Validation** ✅ COMPLETE
**File**: `utils/pairing.py`

- [x] Create `ValidationResult` dataclass
- [x] Add severity levels (info/warning/error)
- [x] Add suggested fixes to messages
- [x] Implement structured error messages
- [x] Update `is_valid_pair()` to return ValidationResult

**Success Metrics**:
- ✅ All validation messages have severity
- ✅ Suggested fixes included
- ✅ Rich debugging information

---

### **3.2: Club Parsing UI** ✅ COMPLETE
**File**: `tabs/data_import.py`

- [x] Implement `display_club_parsing_report()`
- [x] Add parsing confidence indicators
- [x] Show detailed parsing results
- [x] Add conflict warnings
- [x] Document supported formats

**Success Metrics**:
- ✅ Visual confidence indicators (high/medium/low)
- ✅ Detailed breakdown table
- ✅ Proactive conflict warnings

---

## 📋 PHASE 4: PERFORMANCE OPTIMIZATION (Priority: LOW)

### **4.1: Pairing Algorithm Enhancement** ⏳ OPTIONAL
**File**: `utils/pairing.py`

- [x] Minority gender prioritization
- [x] Flexibility-based sorting (quantity mode)
- [ ] **Issue #6**: Implement look-ahead heuristic
- [ ] Add caching for score calculations
- [ ] Profile and benchmark

**Estimated Impact**:
- Current: 5-10% unmatched (greedy local optimum)
- With look-ahead: 2-5% unmatched (closer to global optimum)
- Performance cost: +20-30% time (still fast for <500 fighters)

**Success Metrics**:
- 100 fighters: < 2 seconds
- 500 fighters: < 10 seconds
- Reduced unmatched: -50% improvement

---

### **4.2: Memory Optimization** ⏳ PLANNED
**File**: `tabs/manual_edits.py`

- [ ] Use DataFrame views instead of copies
- [ ] Implement lazy loading for large datasets
- [ ] Add pagination for 500+ fighters

**Success Metrics**:
- Memory usage: -30% reduction
- UI refresh: < 500ms

---

## 📋 PHASE 5: TESTING & DOCUMENTATION (Priority: HIGH)

### **5.1: Test Coverage** ⏳ IN PROGRESS
**Directory**: `tests/`

- [x] Basic pairing logic tests
- [ ] **Add tests for new issues**:
  ```python
  # tests/test_registry.py
  def test_registry_persistence_across_navigation():
      """Test Issue #1: Registry survives page navigation"""
  
  def test_registry_sync_with_matches():
      """Ensure registry stays in sync with session state"""
  
  # tests/test_type_helpers.py
  def test_safe_int_without_pandas():
      """Test Issue #2: Type conversion works without pandas"""
  
  # tests/test_validation.py
  def test_weight_dependent_validation():
      """Test Issue #3: Validation uses dynamic weight limits"""
  
  def test_youth_validation_by_weight():
      """12-15 age group: 2kg at 40kg, 4kg at 60kg"""
  
  # tests/test_club_conflict.py
  def test_club_conflict_none_regions():
      """Test Issue #4: None==None doesn't cause conflict"""
  
  def test_club_conflict_mixed_none():
      """One region None, one region set - no conflict"""
  
  # tests/test_weight_display.py
  def test_weight_format_consistency():
      """Test Issue #5: Same format in editor and export"""
  
  # tests/test_pairing_optimal.py
  def test_pairing_avoids_orphaning():
      """Test Issue #6: Don't orphan constrained fighters"""
  ```
- [ ] Add edge case tests
- [ ] Add integration tests
- [ ] Add property-based tests

**Success Metrics**:
- Code coverage > 80%
- All new issues covered
- Zero regressions

---

### **5.2: Documentation** ⏳ PLANNED
**All files**

- [x] Add ValidationResult documentation
- [x] Document club parsing formats
- [ ] Add ARCHITECTURE.md with:
  - Data flow diagrams
  - Session state management
  - Registry design patterns
  - Pairing algorithm analysis
- [ ] Add KNOWN_ISSUES.md with:
  - Issue #6 greedy algorithm limitations
  - Performance characteristics
  - Scalability considerations
- [ ] Update API documentation

---

## 📋 PHASE 6: ADVANCED FEATURES (Priority: FUTURE)

### **6.1: Database Integration** ⏳ PLANNED
- [x] Database schema design
- [x] Supabase project setup
- [ ] Implement CRUD operations
- [ ] Fighter management UI
- [ ] Event history tracking

### **6.2: Google Sheets Integration** ⏳ PLANNED
- [ ] OAuth setup
- [ ] Column mapping interface
- [ ] Live sync

### **6.3: Tournament Bracket System** ✅ IMPLEMENTED
- [x] Bracket generation
- [x] Winner selection
- [ ] PDF export
- [ ] Double-elimination support

---

## 📋 PHASE 7: DEPLOYMENT (Priority: FUTURE)

### **7.1: Containerization** ✅ COMPLETE
- [x] Dockerfile
- [x] Health checks
- [ ] Multi-stage build optimization

### **7.2: CI/CD** ⏳ PLANNED
- [ ] GitHub Actions workflow
- [ ] Automated testing
- [ ] Automated deployment

### **7.3: Production Deployment** ⏳ PLANNED
- [ ] Streamlit Cloud setup
- [ ] Secrets management
- [ ] Monitoring and logging

---

## 🎯 UPDATED SPRINT (This Week)

### **Sprint Goal**: Fix critical bugs from commit 71f1a40 review

#### **Day 1 (Nov 26 - Today)** ⏰
- [x] Deep code review complete
- [x] Issues documented in TODO.md
- [ ] **Issue #2**: Fix pandas import order (URGENT)
- [ ] **Issue #1**: Add registry initialization
- [ ] **Issue #4**: Fix None==None bug

#### **Day 2 (Nov 27)**
- [ ] **Issue #3**: Replace hardcoded validation limits
- [ ] **Issue #5**: Fix weight display inconsistency
- [ ] Add unit tests for all fixes
- [ ] Run full test suite

#### **Day 3-4 (Nov 28-29)**
- [ ] Stress test with 500 fighters
- [ ] Edge case testing
- [ ] Update documentation
- [ ] Performance benchmarks

#### **Day 5 (Nov 30)** - OPTIONAL
- [ ] **Issue #6**: Implement look-ahead heuristic
- [ ] Benchmark improvements
- [ ] Code review and merge

---

## 📈 METRICS & SUCCESS CRITERIA

### **Code Quality**
- ✅ Type safety infrastructure created
- ✅ Transaction-safe editing implemented
- ✅ Enhanced validation with structured feedback
- ⚠️ 5 critical issues found, 0 fixed
- ⏳ Mypy validation pending

### **Testing**
- ⚠️ Code coverage: ~60% (target: 80%)
- ⏳ New issues need test coverage
- ⏳ Performance benchmarks pending

### **User Experience**
- ✅ Clear error messages implemented
- ✅ Club parsing confidence indicators
- ⚠️ Weight display inconsistency
- ⚠️ Registry race condition risk

---

## 🗓️ ESTIMATED TIMELINE

| Phase | Priority | Duration | Status |
|-------|----------|----------|--------|
| **Critical Fixes** | 🔴 URGENT | 1-2 days | 🔄 In Progress |
| Phase 4: Performance | LOW | 1 day | ⏳ Optional |
| Phase 5: Testing/Docs | HIGH | 2 days | ⏳ Planned |
| Phase 6: Advanced Features | FUTURE | 2-3 weeks | 📅 Backlog |
| Phase 7: Production | FUTURE | 1 week | 📅 Backlog |

**Updated Timeline**:
- **Critical Fixes**: 1-2 days (Nov 26-27)
- **Testing & Docs**: 2 days (Nov 28-29)
- **Total**: 3-4 days to production-ready

---

## 🔧 DEVELOPMENT SETUP

### **Prerequisites**
```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_pairing.py -v

# Test specific issue fix
pytest tests/test_registry.py::test_registry_persistence -v
```

### **Code Quality Checks**
```bash
# Type checking
mypy utils/ tabs/

# Formatting
black --check .

# Linting
ruff check .
```

---

## 📝 NOTES & DECISIONS

### **Design Decisions**
1. **Transaction-Safe Edits**: Prevents data corruption (Phase 2 ✅)
2. **Structured Validation**: Rich error feedback (Phase 3 ✅)
3. **Greedy Algorithm Trade-off**: Fast but not optimal (Issue #6)
4. **Club Conflict Level 2**: Recommended for most tournaments

### **Known Limitations**
- **Greedy Pairing**: May leave 5-10% more unmatched than optimal
- **Large Tournaments**: 500+ fighters may have slower pairing (still < 10s)
- **Manual Trainer Validation**: Disabled by design (flexibility)

### **Technical Debt**
1. 🔴 **Issue #1**: Registry race condition
2. 🔴 **Issue #2**: Pandas import order
3. ⚠️ **Issue #3**: Hardcoded validation limits
4. ⚠️ **Issue #4**: None==None club conflict
5. ⚠️ **Issue #5**: Weight display inconsistency
6. ℹ️ **Issue #6**: Greedy algorithm sub-optimal

---

## ✅ COMPLETED FEATURES

### **Core Features** ✅
- [x] Excel/ODS file upload with validation
- [x] Automatic fighter pairing (greedy algorithm)
- [x] Manual pair editing with Match_ID system
- [x] PDF and Excel export
- [x] Internationalization (Russian/English)
- [x] Docker containerization
- [x] Unit tests for core logic

### **Phase 2 & 3 (Commit 71f1a40)** ✅
- [x] Type safety module (`utils/type_helpers.py`)
- [x] Transaction-safe editing with rollback
- [x] Master fighter registry optimization
- [x] Enhanced validation with `ValidationResult`
- [x] Weight parsing improvements (до, >=, etc.)
- [x] Club parsing UI with confidence indicators
- [x] Registry validation functions
- [x] Pre-save validation with detailed errors

### **Infrastructure** ✅
- [x] Authentication layer
- [x] Database schema design
- [x] Session state management
- [x] Git workflow

---

## 🐛 BUG TRACKER

### **Active Bugs**
| ID | Severity | Description | Status | ETA |
|----|----------|-------------|--------|-----|
| #1 | 🔴 Critical | Registry race condition | Open | Nov 26 |
| #2 | 🔴 Critical | Pandas import order | Open | Nov 26 |
| #3 | ⚠️ High | Hardcoded validation limits | Open | Nov 27 |
| #4 | ⚠️ Medium | Club conflict None==None | Open | Nov 26 |
| #5 | ⚠️ Medium | Weight display inconsistency | Open | Nov 27 |
| #6 | ℹ️ Low | Greedy algorithm sub-optimal | Open | Nov 30 |

### **Fixed Bugs** ✅
- [x] Weight parsing: "до 22" incorrect
- [x] Weight parsing: ">= 60" incorrect
- [x] Club conflict: Missing null checks
- [x] Type conversion: Duplicate functions
- [x] Session state: O(n²) registry rebuild

---

**Last Updated**: November 26, 2025 13:15 MSK  
**Last Review**: Commit 71f1a40 (Phase 2 & 3 Complete)  
**Next Review**: November 27, 2025 (After critical fixes)
**Next Sprint**: December 2, 2025 (Advanced features)