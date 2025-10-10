# Vimunit Level 0 & Level 1 Completion Plan

**Goal**: Achieve 100% pass rate on Level 0 and 80%+ on Level 1

**Current Status**:
- Level 0: 4/6 passed (66.7%)
- Level 1: 5/19 passed (26.3%)

**Target Status**:
- Level 0: 6/6 passed (100%) ✅
- Level 1: 15/19+ passed (80%+) ✅

---

## Phase 1: Level 0 - Basic Framework (6 tests)

**Current**: 4/6 passing (66.7%)
**Target**: 6/6 passing (100%)

### Failing Tests Analysis

#### Test 1: Motion h (left, single)
**Issue**: Step 2: Cursor at (0, 11), expected (1, 0)
**Root Cause**: h command wrapping to previous line instead of staying on current line
**Fix**: Update h movement to not wrap at line boundaries

#### Test 2: Motion l (right, single)
**Issue**: Step 2: Cursor at (1, 0), expected (0, 10)
**Root Cause**: l command wrapping to next line instead of staying at end of current line
**Fix**: Update l movement to not wrap at line boundaries

### Tasks for Level 0 Completion

1. **Fix h (left) movement**
   - Location: `amplifier/vi/commands/executor.py` or movement files
   - Change: Ensure h stops at column 0, doesn't wrap to previous line
   - Test: `basics.vimunit: Motion h (left, single)`

2. **Fix l (right) movement**
   - Location: `amplifier/vi/commands/executor.py` or movement files
   - Change: Ensure l stops at end of line, doesn't wrap to next line
   - Test: `basics.vimunit: Motion l (right, single)`

---

## Phase 2: Level 1 - Counts and Basic Operations (19 tests)

**Current**: 5/19 passing (26.3%)
**Target**: 15/19+ passing (80%+)

### Failing Tests by Category

#### Category A: Backspace Parsing (2 tests)
**Tests**:
- insertion.vimunit: Insert mode backspace
- misc.vimunit: Backspacing in insert mode

**Issue**: `ord() expected a character, but string of length 9 found`
**Root Cause**: Key parser not handling `\<backspace>` or `\<bs>` correctly
**Fix**: Update `vimunit_runner.py` key parser to handle backspace notation

#### Category B: Command Variants (2 tests)
**Tests**:
- yanks.vimunit: Command [count]X (delete previous char)
- yanks.vimunit: Command [count]Y, [count]P (yank lines, put above)

**Issue**: X and Y commands not working correctly
**Root Cause**:
- X not implemented or not deleting backward
- Y should behave like yy (yank line), not like y$ (yank to end)

**Fix**:
- Implement X command (delete previous character)
- Fix Y command to yank entire line (like yy)

#### Category C: Operator-with-Count (5+ tests)
**Tests**:
- motion.vimunit: Motion [count]h (left, multiple) - `d2h` not working
- motion.vimunit: Motion [count]l (right, multiple) - `d2l` not working
- yanks.vimunit: Command [count]x (delete char) - `2x` deleting wrong amount
- repetition.vimunit: Command repetitions (d,X,p,P) - dot repeat issues
- repetition.vimunit: Command repetition counts (x) - numeric repeat issues

**Issue**: Operators combined with counts not working properly
**Root Cause**:
- Count handling for operators like `d2h` (delete 2 left)
- Count with simple commands like `2x` (delete 2 chars)

**Fix**:
- Review `commands/executor.py` numeric handling
- Ensure counts properly multiply: `2d3h` = delete 6 chars left
- Fix `x` command to respect count: `3x` deletes 3 chars

#### Category D: Insertion Mode Variants (4 tests)
**Tests**:
- insertion.vimunit: Command i (insert) - text mismatch
- insertion.vimunit: Command a (append) - cursor positioning
- insertion.vimunit: Command A (append to line) - text mismatch
- insertion.vimunit: Command I (prepend to line) - text mismatch

**Issue**: Some insert mode entry commands not positioning cursor correctly
**Root Cause**:
- `i` - may have issues with certain text patterns
- `a` - should move cursor right one before entering insert
- `A` - should move to end of line before entering insert
- `I` - should move to first non-whitespace before entering insert

**Fix**:
- Review insert mode entry in `event_loop.py` and `executor.py`
- Ensure correct cursor positioning for each variant

#### Category E: Motion Edge Cases (4 tests)
**Tests**:
- motion.vimunit: Motion [count]$ (end of line) - cursor positioning
- motion.vimunit: Motion [count]j (down, multiple) - cursor positioning
- motion.vimunit: Motion [count]k (up, multiple) - cursor positioning
- motion.vimunit: Motion ^ (first nonwhitespace char) - may have issues

**Issue**: Motion commands with counts have cursor positioning issues
**Root Cause**: Column position not being preserved/adjusted correctly
**Fix**: Review motion implementations for proper cursor column handling

#### Category F: Yank/Put Semantics (2+ tests)
**Tests**:
- yanks.vimunit: Putting yanked text ([count]y[motion], [count]p)
- yanks.vimunit: Putting deleted text (d, x, X, p)

**Issue**: Yank and put not behaving exactly like vim
**Root Cause**:
- Put positioning may be off by one
- Yank with motion may not be storing correctly

**Fix**:
- Review register system and put command
- Ensure put places text correctly relative to cursor

---

## Implementation Strategy

### Step 1: Quick Fixes (Est: 30 min)
1. Fix backspace parsing in vimunit_runner.py
2. Fix h/l line wrapping behavior
3. Run tests → Should reach Level 0: 100%, Level 1: ~35%

### Step 2: Command Implementation (Est: 1 hour)
1. Implement X command (delete backward)
2. Fix Y command to yank line (not to end)
3. Run tests → Should reach Level 1: ~45%

### Step 3: Operator-Count Handling (Est: 1-2 hours)
1. Debug numeric prefix handling in executor
2. Fix count application for operators with motions
3. Fix count application for simple commands (x, X)
4. Test with: 2x, 3X, d2h, d3l, 2dd, 3yy
5. Run tests → Should reach Level 1: ~65%

### Step 4: Insertion Mode Refinement (Est: 1 hour)
1. Fix cursor positioning for a, A, I commands
2. Review insert mode text handling
3. Run tests → Should reach Level 1: ~75%

### Step 5: Motion Refinement (Est: 1 hour)
1. Fix column positioning for j/k with counts
2. Fix $ with counts (2$ should go to end of next line)
3. Run tests → Should reach Level 1: ~80%+

### Step 6: Yank/Put Polish (Est: 30 min - 1 hour)
1. Fix put positioning (p vs P)
2. Ensure yank/delete store correctly
3. Run tests → Should reach Level 1: ~85%+

---

## Success Criteria

### Level 0: 100% (6/6 tests)
- ✅ All basic motions work without line wrapping
- ✅ Insert mode entry/exit works perfectly
- ✅ Basic delete command works

### Level 1: 80%+ (15+/19 tests)
- ✅ Counts work with all operators
- ✅ Command variants (X, Y) implemented
- ✅ Insertion mode variants work correctly
- ✅ Motion commands preserve cursor column
- ✅ Yank/put semantics match vim

---

## Critical Files to Modify

1. **amplifier/vi/vimunit_runner.py**
   - Fix backspace key parsing

2. **amplifier/vi/commands/executor.py**
   - Fix numeric prefix handling
   - Implement X command
   - Fix Y command behavior
   - Fix operator-count interactions

3. **amplifier/vi/commands/movements/basic.py**
   - Fix h/l line wrapping behavior

4. **amplifier/vi/event_loop.py**
   - Fix insertion mode entry cursor positioning (a, A, I)

5. **amplifier/vi/buffer/registers.py** (maybe)
   - Review yank/put semantics

---

## Testing Protocol

After each phase:
1. Run vimunit tests: `uv run python -m amplifier.vi.vimunit_runner`
2. Check Level 0 and Level 1 pass rates
3. Review failure messages for patterns
4. Continue to next phase

Final validation:
1. Level 0: 6/6 passing (100%)
2. Level 1: 15+/19 passing (80%+)
3. Run our torture tests to ensure no regressions: `make test`
4. Create comprehensive commit documenting improvements

---

## Notes for Context Compaction

**CRITICAL CONTEXT TO PRESERVE**:
- Goal: 100% Level 0, 80%+ Level 1 vimunit compliance
- Current: L0=66.7% (4/6), L1=26.3% (5/19)
- Test runner: `uv run python -m amplifier.vi.vimunit_runner`
- Main issues: h/l wrapping, backspace parsing, X/Y commands, operator-count handling
- Files: executor.py, movements/basic.py, event_loop.py, vimunit_runner.py
- Validation: Run vimunit tests after each fix, ensure torture tests still pass

**DO NOT LOSE**:
- Specific failing test names from VIMUNIT_TEST_RESULTS.md
- Root cause analysis for each failure category
- Implementation strategy with time estimates
- Success criteria (6/6 Level 0, 15+/19 Level 1)
