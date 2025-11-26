# Muay Thai Matchmaker - Master Project Plan 🥊

## 📊 CODE HEALTH STATUS (Updated: Nov 27, 2025 - 00:24 MSK)

### **Overall Assessment**
- **Core Functionality**: ⚠️ **BROKEN** - Look-ahead causes 0 pairings
- **Code Quality**: ✅ Much Improved (Phase 2 & 3 complete)
- **Data Integrity**: ✅ Transaction-safe editing implemented
- **Production Ready**: 🔴 **CRITICAL BUG** - Look-ahead needs immediate fix
- **Pairing Quality**: ✅ Greedy works (90-95%), 🔴 Look-ahead broken (0%)

### **🚨 CRITICAL PRODUCTION BLOCKERS**
🔴 **IMMEDIATE ACTION REQUIRED** - Look-ahead algorithm implemented but broken!

**Symptoms**: 
- `use_lookahead=True` → 0 fighters paired (all marked unmatched)
- `use_lookahead=False` → Normal pairing works (90-95% matched)
- Look-ahead is rejecting ALL candidate pairs as "would orphan someone"

**Root Cause Analysis**: Over-strict orphaning detection causing false positives

### **Recent Progress (Nov 26-27)**
✅ **VRVS Integration**: Complete Russian weight categories
✅ **2kg Rule**: Implemented for undefined categories
✅ **Look-Ahead Core**: Function implemented (`would_orphan_fighter`)
🔴 **Look-Ahead Integration**: BROKEN - needs debugging
✅ **Professional Docs**: README & PAIRING_ALGORITHM.md complete

### **Critical Issues Priority Order**
1. 🔴 **CRITICAL** [NEW]: Look-ahead algorithm pairs 0 fighters (utils/pairing.py:~900)
2. 🔴 **CRITICAL** [NEW]: `would_orphan_fighter` too strict - returns truthy for all pairs
3. 🔴 **CRITICAL** [NEW]: Wrong `remaining` list passed to orphan check
4. 🔴 **CRITICAL**: Registry initialization race condition (tabs/manual_edits.py:240)
5. 🔴 **CRITICAL**: Pandas import order bug in type_helpers.py
6. ⚠️ **HIGH**: Validation age limits hardcoded (should use dynamic functions)
7. ⚠️ **MEDIUM**: Club conflict level 3 allows None==None matches
8. ⚠️ **MEDIUM**: Weight display inconsistency (min vs range)

---

## 🚨 NEW CRITICAL ISSUES - LOOK-AHEAD BUG

### **Issue #7: Look-Ahead Pairs Zero Fighters** 🔴 CRITICAL
**File**: `utils/pairing.py` lines ~850-950  
**Severity**: **PRODUCTION BLOCKER**  
**Impact**: Look-ahead feature completely broken, pairs 0 fighters

**Problem Description**:
The `use_lookahead=True` parameter causes ALL fighters to be marked as unmatched. The algorithm rejects every possible pairing because `would_orphan_fighter()` returns a truthy value for every candidate pair.

**Root Causes**:

1. **Over-Strict Orphan Detection** (Primary Issue):
   ```python
   # CURRENT (TOO STRICT):
   def would_orphan_fighter(f1, f2, remaining):
       temp_remaining = [f for f in remaining if f not in (f1, f2)]
       for fighter in temp_remaining:
           if count_valid_opponents(fighter, temp_remaining) == 0:
               return fighter  # Returns fighter object (always truthy!)
       return None
   
   # In caller:
   if would_orphan_fighter(current, candidate, fighters):
       continue  # ❌ SKIPS ALL CANDIDATES
   ```

   **Why This Fails**:
   - In constrained tournaments, MANY hypothetical pairs leave someone with 0 options
   - This is NORMAL in greedy - some fighters will be unmatched
   - Look-ahead should prevent *catastrophic* orphaning, not *any* orphaning
   - Function returns fighter object (always truthy) instead of boolean with threshold

2. **Wrong `remaining` List** (Secondary Issue):
   ```python
   # CURRENT (INCORRECT):
   while len(fighters) > 1:
       current_fighter = fighters.pop(0)  # Current removed from fighters list
       
       for opponent in fighters:
           # BUG: fighters doesn't include current_fighter anymore!
           orphaned = would_orphan_fighter(current_fighter, opponent, fighters)
   
   # Should be:
   while len(fighters) > 1:
       current_fighter = fighters[0]  # Don't pop yet
       
       for opponent in fighters[1:]:
           remaining = fighters  # Includes current
           orphaned = would_orphan_fighter(current_fighter, opponent, remaining)
       
       # Pop only after deciding
       fighters.pop(0)
   ```

3. **No Fallback for "All Options Bad"**:
   ```python
   # CURRENT:
   for opponent in fighters:
       if would_orphan_fighter(current, opponent, remaining):
           continue  # Skip this opponent
   
   # If ALL opponents orphan someone:
   if best_opponent is None:
       unmatched.append(current)  # ❌ Current marked unmatched
   
   # SHOULD BE:
   if best_opponent is None and use_lookahead:
       # Fall back to greedy for this fighter
       for opponent in fighters:
           score = calculate_pair_score(current, opponent)
           # Pick best even if it orphans someone
   ```

**Detailed Fix Plan**:

#### **Fix 1: Make Orphan Detection Boolean with Threshold**
```python
# FIXED VERSION:
def would_orphan_fighter(f1: Fighter, f2: Fighter, remaining: List[Fighter], 
                        threshold: int = 2) -> bool:
    """Check if pairing would orphan MULTIPLE fighters (catastrophic).
    
    Args:
        f1, f2: Proposed pair
        remaining: All unpaired fighters (must include f1 and f2)
        threshold: Max orphans to tolerate (default 2)
    
    Returns:
        True if pairing would orphan > threshold fighters (BAD)
        False if orphaning is minimal/acceptable (OK to pair)
    """
    temp_remaining = [f for f in remaining if f not in (f1, f2)]
    orphan_count = 0
    
    for fighter in temp_remaining:
        valid_opponents = sum(
            1 for opp in temp_remaining
            if opp is not fighter and is_valid_pair(fighter, opp).is_valid
        )
        if valid_opponents == 0:
            orphan_count += 1
    
    # Only block if MANY fighters orphaned (catastrophic)
    return orphan_count > threshold
```

**Why This Works**:
- Returns `bool` instead of `Fighter` object (clear true/false)
- Tolerates some orphaning (normal in greedy)
- Only blocks catastrophic cases (>2 orphans)
- Threshold tunable based on tournament size

---

#### **Fix 2: Correct `remaining` List**
```python
# FIXED VERSION:
def pair_fighters(..., use_lookahead=False):
    fighters = create_fighters(df)
    # ... sorting ...
    
    matches = []
    unmatched = []
    
    while len(fighters) > 1:
        current_fighter = fighters[0]  # Don't pop yet!
        best_opponent = None
        best_idx = -1
        best_score = float("inf")
        
        for i, opponent in enumerate(fighters[1:], start=1):
            # Check validity
            if not is_valid_pair(current_fighter, opponent).is_valid:
                continue
            
            # Check orphaning with FULL remaining list
            if use_lookahead:
                would_orphan = would_orphan_fighter(
                    current_fighter, 
                    opponent, 
                    fighters  # ✅ Includes current_fighter
                )
                if would_orphan:
                    continue  # Try next opponent
            
            # Score this pair
            score = calculate_pair_score(current_fighter, opponent)
            if score < best_score:
                best_opponent = opponent
                best_idx = i
                best_score = score
        
        # Decision point
        if best_opponent:
            # Create match
            matches.append(create_match(current_fighter, best_opponent))
            # Remove both fighters
            fighters.pop(best_idx)  # Remove opponent first (higher index)
            fighters.pop(0)         # Then remove current
        else:
            # No valid opponent found
            unmatched.append(fighters.pop(0))
    
    # Handle odd fighter
    if fighters:
        unmatched.extend(fighters)
```

---

#### **Fix 3: Penalty-Based Scoring Instead of Hard Veto**
```python
# BETTER APPROACH: Use orphan risk as penalty, not hard block
def pair_fighters(..., use_lookahead=False):
    while len(fighters) > 1:
        current_fighter = fighters[0]
        best_opponent = None
        best_idx = -1
        best_score = float("inf")
        
        for i, opponent in enumerate(fighters[1:], start=1):
            if not is_valid_pair(current_fighter, opponent).is_valid:
                continue
            
            # Base score
            score = calculate_pair_score(current_fighter, opponent)
            
            # Add orphan penalty if look-ahead enabled
            if use_lookahead:
                would_orphan = would_orphan_fighter(
                    current_fighter, opponent, fighters, threshold=2
                )
                if would_orphan:
                    score += 100  # Heavy penalty, but not infinite
            
            # Still consider this pair, just with penalty
            if score < best_score:
                best_opponent = opponent
                best_idx = i
                best_score = score
        
        # Now we ALWAYS have a best_opponent (unless no valid pairs at all)
        if best_opponent:
            matches.append(create_match(current_fighter, best_opponent))
            fighters.pop(best_idx)
            fighters.pop(0)
        else:
            unmatched.append(fighters.pop(0))
```

**Why Penalty Approach is Better**:
- ✅ Never leaves all fighters unmatched
- ✅ Prefers non-orphaning pairs when available
- ✅ Falls back to "best of bad options" when necessary
- ✅ More robust to edge cases

---

### **Issue #8: `would_orphan_fighter` Returns Wrong Type** 🔴 CRITICAL
**File**: `utils/pairing.py:~780`  
**Severity**: Logic Error  
**Impact**: Function always truthy, breaks conditional checks

**Problem**:
```python
# CURRENT:
def would_orphan_fighter(f1, f2, remaining) -> Optional[Fighter]:
    # ...
    if valid_opponents == 0:
        return fighter  # ❌ Returns Fighter object (always truthy!)
    return None

# In caller:
if would_orphan_fighter(current, opponent, fighters):  # ❌ Always True if any orphan!
    continue
```

**Fix**:
```python
# OPTION 1: Return bool
def would_orphan_fighter(f1, f2, remaining, threshold=2) -> bool:
    orphan_count = 0
    # ... count orphans ...
    return orphan_count > threshold

# OPTION 2: Return count for more control
def count_orphans_if_paired(f1, f2, remaining) -> int:
    # ... count orphans ...
    return orphan_count

# Caller:
if count_orphans_if_paired(current, opponent, fighters) > 2:
    score += 100  # Penalty, not block
```

---

### **Issue #9: No Greedy Fallback When All Options Bad** 🔴 CRITICAL
**File**: `utils/pairing.py:~920`  
**Severity**: Missing Edge Case Handling  
**Impact**: Leaves fighters unmatched unnecessarily

**Problem**:
```python
# CURRENT:
for opponent in fighters:
    if use_lookahead and would_orphan_fighter(current, opponent, fighters):
        continue  # Skip ALL opponents

if best_opponent is None:
    unmatched.append(current)  # ❌ Marked unmatched even if valid pairs exist!
```

**Fix**:
```python
# SOLUTION 1: Two-pass approach
if use_lookahead:
    # Pass 1: Try to find non-orphaning pair
    for opponent in fighters:
        if is_valid_pair(current, opponent).is_valid:
            if not would_orphan_fighter(current, opponent, fighters):
                # Found safe pair!
                best_opponent = opponent
                break

# Pass 2: If no safe pair, fall back to greedy
if best_opponent is None:
    for opponent in fighters:
        if is_valid_pair(current, opponent).is_valid:
            score = calculate_pair_score(current, opponent)
            if score < best_score:
                best_opponent = opponent
                best_score = score

# SOLUTION 2: Penalty-based (better)
# See Fix 3 above - use orphan risk as penalty weight
```

---

## 🔧 IMMEDIATE ACTION PLAN - LOOK-AHEAD DEBUG

### **Priority 0: Emergency Debug (TONIGHT - 30 min)**

1. **Add Debug Logging** (5 min):
   ```python
   def would_orphan_fighter(f1, f2, remaining, threshold=2):
       import logging
       logger = logging.getLogger(__name__)
       
       temp_remaining = [f for f in remaining if f not in (f1, f2)]
       logger.info(f"[ORPHAN CHECK] Pair: {f1.name} - {f2.name}")
       logger.info(f"  Remaining fighters: {len(remaining)}")
       logger.info(f"  After removal: {len(temp_remaining)}")
       
       orphan_count = 0
       orphaned_names = []
       for fighter in temp_remaining:
           valid_opponents = sum(...)
           if valid_opponents == 0:
               orphan_count += 1
               orphaned_names.append(fighter.name)
       
       logger.info(f"  Orphans detected: {orphan_count} - {orphaned_names}")
       logger.info(f"  Would block: {orphan_count > threshold}")
       
       return orphan_count > threshold
   ```

2. **Test with Minimal Data** (10 min):
   ```python
   # Create 4-fighter test case
   test_df = pd.DataFrame([
       {"Name": "A", "Gender": "м", "Age": 18, "Weight": "60", 
        "Club": "C1", "Trainer": "T1", "Record": 5},
       {"Name": "B", "Gender": "м", "Age": 18, "Weight": "62", 
        "Club": "C2", "Trainer": "T2", "Record": 5},
       {"Name": "C", "Gender": "м", "Age": 18, "Weight": "61", 
        "Club": "C3", "Trainer": "T3", "Record": 5},
       {"Name": "D", "Gender": "м", "Age": 18, "Weight": "63", 
        "Club": "C4", "Trainer": "T4", "Record": 5},
   ])
   
   # Test both modes
   matches_greedy, _ = pair_fighters(test_df, use_lookahead=False)
   matches_lookahead, _ = pair_fighters(test_df, use_lookahead=True)
   
   print(f"Greedy: {len(matches_greedy)} pairs")
   print(f"Lookahead: {len(matches_lookahead)} pairs")  # Should be > 0!
   ```

3. **Check Logs** (5 min):
   - Look for patterns in orphan detection
   - Verify `remaining` list size is correct
   - Confirm threshold logic works

4. **Apply Minimal Fix** (10 min):
   - Change return type to `bool`
   - Add threshold parameter (default 2)
   - Fix `remaining` list to include current fighter

### **Priority 1: Permanent Fix (TOMORROW - 2 hours)**

**Hour 1: Implement Fixes**
- [ ] Apply Fix #1: Boolean return with threshold
- [ ] Apply Fix #2: Correct `remaining` list
- [ ] Apply Fix #3: Penalty-based scoring
- [ ] Add comprehensive logging

**Hour 2: Testing & Validation**
- [ ] Test with 10, 50, 100 fighter datasets
- [ ] Compare greedy vs look-ahead results
- [ ] Verify look-ahead pairs > 90% of fighters
- [ ] Benchmark performance overhead < 50%

**Acceptance Criteria**:
- ✅ `use_lookahead=True` pairs at least 90% of fighters
- ✅ Look-ahead pairs ≥ greedy pairs (never worse)
- ✅ Performance overhead < 50% vs greedy
- ✅ All existing tests still pass

---

## 🚀 IMMEDIATE ACTION ITEMS (UPDATED CRITICAL PATH)

### **TONIGHT (Nov 27, 00:00-01:00 MSK) - EMERGENCY**
- [ ] **Issue #7**: Debug look-ahead with logging (30 min)
- [ ] **Issue #8**: Fix return type to bool (10 min)
- [ ] **Issue #9**: Add greedy fallback (20 min)
- [ ] **Quick test**: Verify 4-fighter scenario pairs correctly

### **Day 1 (Nov 27) - CRITICAL FIXES**
- [ ] **Issue #7-9**: Complete look-ahead fix (2 hours)
- [ ] **Issue #2**: Fix pandas import order in `type_helpers.py` (15 min)
- [ ] **Issue #1**: Add registry initialization to `app.py` (30 min)
- [ ] **Issue #4**: Fix club conflict None==None bug (15 min)
- [ ] **Test suite**: Run all tests, verify > 95% pass

**Total time**: ~3-4 hours

### **Day 2 (Nov 28) - HIGH PRIORITY**
- [ ] **Issue #3**: Replace hardcoded validation limits (45 min)
- [ ] **Issue #5**: Fix weight display inconsistency (20 min)
- [ ] **Comprehensive tests**: Add tests for all fixes (1 hour)
- [ ] **Performance benchmarks**: Measure look-ahead overhead

**Total time**: ~2-3 hours

### **Day 3-4 (Nov 29-30) - VALIDATION**
- [ ] **Stress test**: 500 fighter tournament
- [ ] **A/B testing**: Compare greedy vs look-ahead quality
- [ ] **Documentation**: Update PAIRING_ALGORITHM.md with fixes
- [ ] **User guide**: Add look-ahead usage guidelines

---

## 📈 SUCCESS METRICS - LOOK-AHEAD FIX

### **Minimum Viable Fix** (Tonight)
- ✅ Look-ahead pairs > 0 fighters (not all unmatched)
- ✅ Basic 4-fighter test passes
- ✅ No crashes or exceptions

### **Production Ready** (Tomorrow)
- ✅ Look-ahead pairs ≥ 90% of fighters
- ✅ Look-ahead quality ≥ greedy quality
- ✅ Performance overhead < 50%
- ✅ All unit tests pass
- ✅ Logging provides clear feedback

### **Optimal** (This Week)
- ✅ Look-ahead improves matching by 5-10%
- ✅ Orphaning reduced by 50-80%
- ✅ Performance overhead < 30%
- ✅ Comprehensive test coverage
- ✅ Documentation complete

---

## 📊 ORIGINAL TODO CONTINUES BELOW...

(Rest of TODO.md content remains unchanged from previous version)

---

**Last Updated**: November 27, 2025 00:24 MSK  
**Status**: 🔴 **CRITICAL** - Look-ahead broken, immediate fix required  
**Next Review**: November 27, 2025 12:00 MSK (After emergency fix)  
**ETA Production Ready**: Nov 28-29 (after critical fixes)