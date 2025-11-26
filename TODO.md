# Muay Thai Matchmaker - Master Project Plan 🥊

## 📊 CODE HEALTH STATUS (Updated: Nov 26, 2025)

### **Overall Assessment**
- **Core Functionality**: ✅ Complete (File upload → Pairing → Manual edit → Export)
- **Code Quality**: ⚠️ Needs Refactoring (Duplicate code, type safety issues)
- **Data Integrity**: ⚠️ Session state management needs improvement
- **Production Ready**: 🔄 Basic version works, enterprise features planned

### **Critical Issues Identified**
1. ❌ **Dead/Duplicate Code** in `utils/pairing.py` (~200 lines of redundant functions)
2. ⚠️ **Session State Complexity** in `tabs/manual_edits.py` (data consistency risks)
3. ⚠️ **Weight Parsing Inconsistencies** (multiple handlers with different behaviors)
4. ⚠️ **Missing Type Safety** (no type hints, no mypy validation)
5. 🐛 **Club Conflict Detection Bug** (null-safety issues in level 2 checks)

---

## 🚀 IMMEDIATE ACTION ITEMS (Do First - Quick Wins)

### **Week 1: Critical Code Cleanup**

#### **Day 1-2: Remove Duplicate Code**
- [ ] **Task 1.1**: Clean `utils/pairing.py` (Lines 47-62, 119-148, 289-310)
  - Remove duplicate `get_max_diff_*()` functions
  - Remove duplicate `parse_club_hierarchy()` function
  - Remove unused `JUNIOR_PAIRING_RULES` dictionary
  - Consolidate `get_weight_category()` definitions
  - **Estimated time**: 2-3 hours
  - **Impact**: Reduce file from 700+ to ~500 lines

- [ ] **Task 1.2**: Fix `format_weight_string()` duplicate in `tabs/manual_edits.py`
  - Remove second definition (lines 35-45)
  - Ensure consistency with pairing output format
  - **Estimated time**: 15 minutes
  - **Impact**: Eliminate confusion, consistent weight display

#### **Day 3: Consolidate Type Conversions**
- [ ] **Task 1.3**: Create `utils/type_helpers.py`
  ```python
  def safe_int_conversion(value) -> int:
      """Single source of truth for int conversion"""
  
  def safe_float_conversion(value) -> float:
      """Single source of truth for float conversion"""
  ```
- [ ] Remove duplicate `safe_int_conversion()` from:
  - `utils/pairing.py` (lines 76-98)
  - `tabs/manual_edits.py` (lines 7-29)
- [ ] Replace all instances with imports
- **Estimated time**: 45 minutes
- **Impact**: Single source of truth, easier to maintain

#### **Day 4: Fix Critical Bugs**
- [ ] **Task 6.1**: Fix club conflict detection null-safety
  ```python
  # File: utils/pairing.py, lines 200-245
  if conflict_level == 2:
      return (
          bool(fighter1.club_region and fighter2.club_region)  # Both must exist
          and fighter1.club_region == fighter2.club_region
          and fighter1.club_name == fighter2.club_name
      )
  ```
- [ ] **Task 1.2**: Fix weight range parsing edge cases
  - "до 22" should be (0, 22) not (22, 22)
  - ">= 60" should be (60, 999) not (60, 60)
- **Estimated time**: 1-2 hours
- **Impact**: Correct pairing behavior

---

## 📋 PHASE 1: CODE QUALITY & REFACTORING (Priority: CRITICAL)

### **1.1: Pairing Algorithm Cleanup**
**File**: `utils/pairing.py`

- [x] Basic pairing algorithm implementation
- [ ] **Remove deprecated functions**:
  - [ ] Lines 47-62: Legacy `get_max_diff_12_14()`, `get_max_diff_15_16()`
  - [ ] Lines 159-175: Unused `JUNIOR_PAIRING_RULES` dictionary
- [ ] **Consolidate duplicate functions**:
  - [ ] Lines 119-148: Remove second `parse_club_hierarchy()`
  - [ ] Lines 289-310: Remove second `get_weight_category()`
- [ ] **Fix logic inconsistencies**:
  - [ ] Lines 402-420: Youth weight rules fallback conflicts with adult categories
  - [ ] Add clear separation between adult/youth validation paths

**Success Metrics**:
- File reduced from 700+ lines to ~500 lines
- Zero duplicate function definitions
- All unit tests pass

---

### **1.2: Weight Handling Refactor**
**File**: `utils/pairing.py`

- [ ] **Refactor** `parse_weight_range()` (lines 250-285):
  ```python
  def parse_weight_range(weight_str: str) -> Tuple[float, float]:
      """
      Parse weight range with clear semantics:
      - "до 22" (up to) → (0, 22)
      - ">= 60" (at least) → (60, 999)
      - "55-60" (range) → (55, 60)
      - "58" (exact) → (58, 58)
      """
  ```
- [ ] **Add unit tests** in `tests/test_pairing.py`:
  ```python
  def test_parse_weight_range_edge_cases():
      assert parse_weight_range("до 22") == (0, 22)
      assert parse_weight_range(">= 60") == (60, 999)
      assert parse_weight_range("55-60") == (55, 60)
      assert parse_weight_range("58") == (58, 58)
      assert parse_weight_range("") == (0, 999)  # Default fallback
  ```

**Success Metrics**:
- All weight formats parsed consistently
- Test coverage > 95% for weight parsing

---

### **1.3: Type Safety Implementation**
**All Python files**

- [ ] **Create** `utils/type_helpers.py`:
  - [ ] Move `safe_int_conversion()` (single source of truth)
  - [ ] Add `safe_float_conversion()`
  - [ ] Add `safe_str_conversion()`
- [ ] **Add type hints** to core functions:
  - [ ] `utils/pairing.py`: All public functions
  - [ ] `utils/data_loader.py`: All public functions
  - [ ] `tabs/*.py`: All render functions
- [ ] **Configure mypy**:
  ```toml
  # pyproject.toml
  [tool.mypy]
  python_version = "3.11"
  warn_return_any = true
  warn_unused_configs = true
  disallow_untyped_defs = true
  ```
- [ ] **Run mypy in CI**: Add to GitHub Actions workflow

**Success Metrics**:
- Zero mypy errors on strict mode
- All functions have complete type hints

---

## 📋 PHASE 2: DATA INTEGRITY & SESSION STATE (Priority: HIGH)

### **2.1: Master Fighter Registry Refactor**
**File**: `tabs/manual_edits.py`

- [x] Basic registry implementation
- [ ] **Optimize** `build_master_fighter_registry()` (lines 100-180):
  - Current: O(n²) complexity, rebuilds on every edit
  - Target: O(n) with incremental updates
  ```python
  def update_fighter_in_registry(fighter_name: str, updates: dict):
      """Incremental update instead of full rebuild"""
  
  def validate_fighter_registry() -> List[str]:
      """Check registry for data consistency issues"""
      issues = []
      # Check for missing fighters
      # Check for duplicate match IDs
      # Check for orphaned records
      return issues
  ```

**Success Metrics**:
- Registry updates < 100ms for typical edits
- Zero data corruption in stress tests

---

### **2.2: Transaction-Safe Match Editing**
**File**: `tabs/manual_edits.py`

- [ ] **Refactor** `update_session_state_from_match_id()` (lines 345-420):
  ```python
  def validate_before_save(edited_df) -> Tuple[bool, List[str]]:
      """Comprehensive pre-save validation"""
      errors = []
      # Check same-club violations
      # Check gender mismatches
      # Check weight/age constraints
      return (len(errors) == 0, errors)
  
  def update_session_state_from_match_id(edited_df):
      """Transaction-like behavior with rollback"""
      is_valid, errors = validate_before_save(edited_df)
      if not is_valid:
          st.error("Cannot save changes:")
          for error in errors:
              st.error(f"  - {error}")
          return False
      
      # Create backup of current state
      backup_matches = st.session_state["matches"].copy()
      backup_unmatched = st.session_state["unmatched"].copy()
      
      try:
          # Apply changes
          # ... update logic ...
          return True
      except Exception as e:
          # Rollback on error
          st.session_state["matches"] = backup_matches
          st.session_state["unmatched"] = backup_unmatched
          st.error(f"Update failed: {e}")
          return False
  ```

**Success Metrics**:
- Zero invalid states saved
- Clear error messages for all validation failures
- Rollback works correctly on errors

---

## 📋 PHASE 3: VALIDATION & USER EXPERIENCE (Priority: MEDIUM)

### **3.1: Enhanced Validation Messages**
**File**: `utils/pairing.py`

- [ ] **Improve** `is_valid_pair()` return messages (lines 440-490):
  ```python
  @dataclass
  class ValidationResult:
      is_valid: bool
      message: str
      severity: str  # "info", "warning", "error"
      suggested_fix: Optional[str] = None
      
  # Example improved messages:
  # Current: "Weight diff exceeds limit"
  # New: "Weight diff 7.2kg exceeds youth limit 5.0kg for 12-15 age group. Suggested: Find fighter in 53-57kg range."
  ```

**Success Metrics**:
- All validation messages include:
  - What went wrong
  - Why it's a problem
  - How to fix it

---

### **3.2: Club Parsing Validation**
**File**: `utils/pairing.py`

- [x] Basic club parsing implementation
- [ ] **Add validation UI** in data import tab:
  ```python
  def display_club_parsing_report(df: pd.DataFrame):
      """Show how clubs were parsed after upload"""
      validation = validate_club_parsing(df)
      if validation["valid"]:
          st.success("All clubs parsed successfully")
      else:
          st.warning("Some clubs may need manual review")
          st.dataframe(pd.DataFrame(validation["parsed_clubs"]))
  ```

**Success Metrics**:
- Users can review club parsing before pairing
- Clear indication of parsing issues

---

## 📋 PHASE 4: PERFORMANCE OPTIMIZATION (Priority: LOW)

### **4.1: Pairing Algorithm Optimization**
**File**: `utils/pairing.py`

- [x] Greedy pairing algorithm
- [ ] **Add caching** for expensive calculations:
  ```python
  from functools import lru_cache
  
  @lru_cache(maxsize=1000)
  def calculate_pair_score_cached(
      f1_weight: float, f1_age: int, f1_exp: int,
      f2_weight: float, f2_age: int, f2_exp: int
  ) -> float:
      """Cache score calculations"""
  ```
- [ ] **Profile and benchmark**:
  ```python
  # tests/test_performance.py
  def test_pairing_performance():
      # Test with 100, 500, 1000 fighters
      assert pair_100_fighters() < 2.0  # seconds
      assert pair_500_fighters() < 10.0  # seconds
  ```

**Success Metrics**:
- 100 fighters: < 2 seconds
- 500 fighters: < 10 seconds
- 1000 fighters: < 30 seconds

---

### **4.2: DataFrame Memory Optimization**
**File**: `tabs/manual_edits.py`

- [ ] **Use views instead of copies** (lines 200-250):
  ```python
  # Current: Multiple df.copy() calls
  # Improved: Use .loc[] views for read-only operations
  def get_fighters_view(match_id: int) -> pd.DataFrame:
      """Return view, not copy"""
      return combined_df.loc[combined_df["Match_ID"] == match_id]
  ```

**Success Metrics**:
- Memory usage reduced by 30%+
- UI refresh time < 500ms

---

## 📋 PHASE 5: TESTING & DOCUMENTATION (Priority: MEDIUM)

### **5.1: Expand Test Coverage**
**Directory**: `tests/`

- [x] Basic pairing logic tests
- [ ] **Add edge case tests**:
  ```python
  # tests/test_pairing_edge_cases.py
  def test_single_fighter_pairing():
      """Ensure algorithm handles odd numbers"""
  
  def test_all_same_club():
      """Verify behavior when all fighters from one club"""
  
  def test_extreme_weight_differences():
      """Test boundary conditions"""
  
  def test_empty_dataframe():
      """Handle empty input gracefully"""
  
  def test_malformed_weight_strings():
      """Handle corrupted data"""
  ```
- [ ] **Add integration tests**:
  ```python
  # tests/test_workflow.py
  def test_full_pairing_workflow():
      """Test: Upload → Pair → Edit → Export pipeline"""
  
  def test_manual_edit_workflow():
      """Test: Pair → Manual swap → Validate → Save"""
  ```
- [ ] **Add property-based tests** using `hypothesis`:
  ```python
  from hypothesis import given, strategies as st
  
  @given(st.lists(st.integers(min_value=12, max_value=60), min_size=2))
  def test_pairing_never_crashes(fighter_ages):
      """Pairing should never crash regardless of input"""
  ```

**Success Metrics**:
- Code coverage > 80%
- All edge cases covered
- Zero crashes on random input

---

### **5.2: Comprehensive Documentation**
**All Python files**

- [ ] **Add Google-style docstrings** to all public functions:
  ```python
  def pair_fighters(
      df: pd.DataFrame,
      club_conflict_level: int = 3,
      sort_strategy: str = "quantity"
  ) -> Tuple[pd.DataFrame, pd.DataFrame]:
      """Perform greedy pairing of fighters based on IFMA rules.
      
      Args:
          df: DataFrame with fighter data. Required columns:
              - Name (str): Fighter's full name
              - Gender (str): 'м' or 'ж'
              - Age (int): Fighter's age (12-60)
              - Weight (str): Weight range (e.g., "55-60", ">= 60")
              - Club (str): Club affiliation
              - Trainer (str): Trainer name
              - Record (int): Total fights count
          club_conflict_level: Club matching strictness:
              1 - Exact club match (strictest)
              2 - Same region + club, ignore subgroup [RECOMMENDED]
              3 - Same region only
              4 - No conflicts (allow all)
          sort_strategy: Fighter prioritization:
              "quality" - Experienced fighters first
              "quantity" - Maximize total pairs
      
      Returns:
          matches_df: Paired fighters with columns:
              Match_ID, Red_Corner, Blue_Corner, Gender, Age_*, 
              Weight_*, Club_*, Weight_Diff, Age_Diff
          unmatched_df: Unpaired fighters with original columns
      
      Raises:
          ValueError: If df missing required columns
          TypeError: If column types invalid
      
      Example:
          >>> fighters = pd.read_excel("roster.xlsx")
          >>> matches, unmatched = pair_fighters(
          ...     fighters,
          ...     club_conflict_level=2,
          ...     sort_strategy="quantity"
          ... )
          >>> print(f"Created {len(matches)} pairs")
      
      Notes:
          - Uses greedy algorithm with soft scoring
          - Adult weight classes follow IFMA standards
          - Youth pairings use age-based weight tolerances
      """
  ```
- [ ] **Create** `CONTRIBUTING.md`:
  - Code style guide
  - How to run tests
  - How to submit PRs
- [ ] **Create** `ARCHITECTURE.md`:
  - System overview diagram
  - Data flow explanation
  - Module responsibilities

**Success Metrics**:
- All public functions documented
- New contributors can onboard in < 1 hour

---

## 📋 PHASE 6: ADVANCED FEATURES (From Original TODO)

### **6.1: Database Integration** ✅ *Schema Ready*
- [x] Database schema design
- [x] Supabase project setup
- [ ] **Implement CRUD operations**:
  - [ ] Fighters: Create, Read, Update, Archive
  - [ ] Clubs: Create, Read, Update
  - [ ] Events: Create, Read, Update
  - [ ] Matches: Create, Read (history)
- [ ] **Fighter Management UI** (`tabs/fighter_management.py`):
  - [ ] Add new fighter form with validation
  - [ ] Bulk edit fighter roster
  - [ ] Archive/reactivate fighters
  - [ ] Import from CSV to database

**Status**: Schema complete, implementation pending

---

### **6.2: Google Sheets Integration** ⏳ *Planned*
- [ ] **Google Sheets connector**:
  - [ ] OAuth setup with service account
  - [ ] Sheet URL input field
  - [ ] Column mapping interface
  - [ ] Live preview before import
- [ ] **Update** `tabs/data_import.py`:
  ```python
  def render_google_sheets_import():
      """Import fighters directly from Google Sheets"""
      sheet_url = st.text_input("Sheet URL")
      if sheet_url:
          # Connect via st.connection("gsheets")
          # Show column mapper
          # Preview data
          # Import to session state or database
  ```

**Status**: Dependencies added to requirements.txt, implementation pending

---

### **6.3: Tournament Bracket System** ✅ *Implemented*
- [x] Bracket generation UI
- [x] Winner selection interface
- [ ] **Enhance** `tabs/tournament_bracket.py`:
  - [ ] Save bracket state to database
  - [ ] Generate bracket PDF export
  - [ ] Support double-elimination format
  - [ ] Add bracket visualization improvements

**Status**: Core features complete, enhancements pending

---

## 📋 PHASE 7: DEPLOYMENT & PRODUCTION (Priority: FUTURE)

### **7.1: Containerization** ✅ *Complete*
- [x] Dockerfile created
- [x] Docker health checks
- [ ] **Optimize Docker image**:
  - [ ] Multi-stage build to reduce size
  - [ ] Cache pip dependencies
  - [ ] Add docker-compose.yml for local dev

---

### **7.2: Cloud Deployment** ⏳ *Planned*
- [ ] **Streamlit Cloud setup**:
  - [ ] Create streamlit cloud project
  - [ ] Configure secrets management
  - [ ] Setup custom domain (optional)
- [ ] **Production configuration**:
  - [ ] Environment-based config (dev/staging/prod)
  - [ ] Logging setup
  - [ ] Error tracking (Sentry integration)
  - [ ] Analytics (optional)

---

### **7.3: CI/CD Pipeline** ⏳ *Planned*
- [ ] **GitHub Actions workflow**:
  ```yaml
  # .github/workflows/ci.yml
  name: CI
  on: [push, pull_request]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v3
        - name: Run tests
          run: |
            pip install -r requirements.txt
            pip install -r requirements-dev.txt
            pytest --cov=. --cov-report=xml
        - name: Run mypy
          run: mypy .
        - name: Run linters
          run: |
            black --check .
            ruff check .
  ```
- [ ] **Automated deployment**:
  - [ ] Deploy to staging on PR merge to develop
  - [ ] Deploy to production on release tag

---

## 🎯 CURRENT SPRINT (This Week)

### **Sprint Goal**: Clean up codebase and fix critical bugs

#### **Monday-Tuesday**
- [x] Code analysis complete
- [ ] Task 1.1: Remove duplicates in `pairing.py`
- [ ] Task 1.2: Fix weight parsing edge cases

#### **Wednesday-Thursday**
- [ ] Task 1.3: Consolidate type conversions
- [ ] Task 6.1: Fix club conflict bug
- [ ] Add unit tests for fixes

#### **Friday**
- [ ] Code review and testing
- [ ] Update documentation
- [ ] Plan next sprint

---

## 📈 METRICS & SUCCESS CRITERIA

### **Code Quality**
- [ ] Lines of code reduced by 20%+
- [ ] Zero duplicate function definitions
- [ ] Mypy passes on strict mode
- [ ] Ruff/Black formatting compliance

### **Testing**
- [ ] Code coverage > 80%
- [ ] All edge cases tested
- [ ] Performance benchmarks pass

### **User Experience**
- [ ] Manual edits save in < 500ms
- [ ] Clear error messages for all failures
- [ ] Zero data corruption bugs

---

## 🗓️ ESTIMATED TIMELINE

| Phase | Priority | Duration | Status |
|-------|----------|----------|--------|
| Phase 1: Code Cleanup | CRITICAL | 2-3 days | 🔄 In Progress |
| Phase 2: Data Integrity | HIGH | 1-2 days | ⏳ Planned |
| Phase 3: Validation | MEDIUM | 1-2 days | ⏳ Planned |
| Phase 4: Performance | LOW | 1 day | ⏳ Planned |
| Phase 5: Testing/Docs | MEDIUM | 2 days | ⏳ Planned |
| Phase 6: Advanced Features | FUTURE | 2-3 weeks | 📅 Backlog |
| Phase 7: Production | FUTURE | 1 week | 📅 Backlog |

**Total for Phases 1-5**: ~1-1.5 weeks
**Total for Phases 6-7**: ~3-4 weeks additional

---

## 🔧 DEVELOPMENT SETUP

### **Prerequisites**
```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing/linting
```

### **Running Tests**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_pairing.py -v

# Run with type checking
mypy .
```

### **Code Formatting**
```bash
# Format code
black .

# Check formatting
black --check .

# Run linter
ruff check .
```

---

## 📝 NOTES & DECISIONS

### **Design Decisions**
1. **Club Conflict Level 2 Recommended**: Allows subgroup pairings from same club (e.g., different age groups)
2. **Quantity Sort Strategy Default**: Maximizes number of pairings over perfect matches
3. **Transaction-Safe Edits**: Prevents data corruption from invalid manual edits

### **Known Limitations**
- Manual edits don't validate same-trainer constraint (by design - allows flexibility)
- Weight categories for <45kg fighters use youth floating rules
- Large tournaments (500+ fighters) may have slower pairing times

### **Future Considerations**
- Consider moving to PostgreSQL views for faster queries
- Add Redis caching for repeated calculations
- Implement WebSocket updates for real-time collaborative editing

---

## ✅ COMPLETED FEATURES (From Original TODO)

- [x] **Basic File Upload & Validation**: Excel upload with column checking
- [x] **Core Pairing Algorithm**: Greedy matching with hard/soft constraints
- [x] **Manual Match Editing**: `st.data_editor` for adjusting pairs
- [x] **Export Functionality**: PDF bout sheets and Excel exports
- [x] **UI/UX**: Tabbed interface, statistics display, warnings
- [x] **Internationalization**: Full Russian translation support
- [x] **Docker Deployment**: Containerized app with health checks
- [x] **Testing**: Unit tests for core pairing logic
- [x] **Git Management**: Proper branching and remote setup
- [x] **Authentication Layer**: Login screen and session management
- [x] **Database Schema**: Designed and ready for implementation

---

**Last Updated**: November 26, 2025
**Next Review**: December 3, 2025 (After Week 1 Sprint)