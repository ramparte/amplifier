# Vi Editor Completion - Super-Planner Master Plan

## Vision
A production-ready, CLI-launchable vi editor in Python that behaves identically to traditional vi, with comprehensive automated testing that validates ALL functionality against known-good outputs.

## Project Structure

This will be organized as a super-planner project with clear phases, dependencies, and deliverables.

## Phase 1: File I/O System (CRITICAL - FOUNDATION)
**Priority: P0 - Blocking**
**Estimated Complexity: Medium**

### Tasks:
1. **File Loading Module**
   - Read file from disk with encoding detection (UTF-8, ASCII, Latin-1)
   - Handle missing files (create new buffer)
   - Handle permission errors gracefully
   - Support large file streaming (>10MB)
   - Preserve line endings (LF, CRLF, CR)

2. **File Saving Module**
   - Write buffer to disk with original encoding
   - Atomic write (write to temp, then rename)
   - Backup file creation (.bak)
   - Handle permission errors
   - Preserve file permissions and timestamps

3. **File State Management**
   - Track modified state (dirty flag)
   - Track file path and name
   - Detect external file changes
   - Handle read-only files

**Deliverables:**
- `amplifier/vi/file_io/loader.py`
- `amplifier/vi/file_io/saver.py`
- `amplifier/vi/file_io/state.py`
- Unit tests for all file operations
- Integration tests with buffer

**Success Criteria:**
- Load file, edit, save, verify byte-identical output
- Handle all edge cases (missing, readonly, large files)
- 100% test coverage

---

## Phase 2: Ex Command System (CRITICAL - USER INTERFACE)
**Priority: P0 - Blocking**
**Estimated Complexity: High**
**Dependencies: Phase 1 (file I/O for :w, :e commands)**

### Tasks:
1. **Ex Command Parser**
   - Parse command line input (`:command args`)
   - Handle ranges (`:1,10d`, `:%s/old/new/`)
   - Parse substitution syntax (`:s/pattern/replacement/flags`)
   - Support command abbreviations (`:w` = `:write`)
   - Handle multiple commands (`:w | q`)

2. **Core Ex Commands**
   - `:w [file]` - Write to file
   - `:q` - Quit (check modified)
   - `:q!` - Quit force
   - `:wq` - Write and quit
   - `:x` - Write if modified and quit
   - `:e file` - Edit file
   - `:e!` - Reload current file
   - `:r file` - Read file into buffer

3. **Substitution Command**
   - `:s/pattern/replacement/` - Substitute on current line
   - `:%s/pattern/replacement/` - Substitute all lines
   - `:1,10s/pattern/replacement/` - Substitute range
   - Flags: `g` (global), `i` (ignore case), `c` (confirm)
   - Regex pattern support

4. **Global Commands**
   - `:g/pattern/command` - Execute command on matching lines
   - `:v/pattern/command` - Execute on non-matching lines

5. **Buffer Commands**
   - `:bn` - Next buffer
   - `:bp` - Previous buffer
   - `:bd` - Delete buffer
   - `:ls` - List buffers

6. **Settings Commands**
   - `:set number` - Show line numbers
   - `:set nonumber` - Hide line numbers
   - `:set ignorecase` - Case insensitive search
   - `:set tabstop=4` - Tab width
   - `:set expandtab` - Use spaces for tabs

7. **Utility Commands**
   - `:!command` - Execute shell command
   - `:r !command` - Read command output into buffer

**Deliverables:**
- `amplifier/vi/commands/ex/parser.py`
- `amplifier/vi/commands/ex/executor.py`
- `amplifier/vi/commands/ex/substitution.py`
- `amplifier/vi/commands/ex/global.py`
- `amplifier/vi/commands/ex/settings.py`
- Comprehensive ex command tests

**Success Criteria:**
- All core ex commands work
- Substitution handles regex correctly
- Global commands execute properly
- Settings persist during session
- 100% test coverage on ex commands

---

## Phase 3: Search System (CRITICAL - CORE FEATURE)
**Priority: P0 - Blocking**
**Estimated Complexity: Medium**
**Dependencies: None (search engine exists, needs integration)**

### Tasks:
1. **Search Command Integration**
   - `/pattern` - Search forward from cursor
   - `?pattern` - Search backward from cursor
   - `n` - Next match
   - `N` - Previous match (reverse direction)
   - `*` - Search word under cursor forward
   - `#` - Search word under cursor backward

2. **Search Features**
   - Regex pattern matching
   - Case-sensitive/insensitive modes
   - Wrap around buffer option
   - Incremental search highlighting
   - Search history (up/down arrows in search)

3. **Search State Management**
   - Remember last search pattern
   - Search direction persistence
   - Match highlighting
   - Match count display

**Deliverables:**
- `amplifier/vi/search/commands.py` (integrate with existing engine)
- Search command tests
- Integration with normal mode commands

**Success Criteria:**
- All search commands work
- Search wraps correctly
- Highlights match under cursor
- History works
- 100% test coverage

---

## Phase 4: Missing Normal Mode Commands (HIGH PRIORITY)
**Priority: P1 - High**
**Estimated Complexity: Low-Medium**
**Dependencies: Phase 3 (search for % command)**

### Tasks:
1. **Repeat Command**
   - `.` - Repeat last change
   - Track last change with full context
   - Handle complex changes (operator + motion)

2. **Line Operations**
   - `J` - Join current line with next
   - `gJ` - Join without space
   - Support count: `3J` joins 3 lines

3. **Case Operations**
   - `~` - Toggle case of character under cursor
   - `gu{motion}` - Lowercase motion
   - `gU{motion}` - Uppercase motion
   - `g~{motion}` - Toggle case motion

4. **Indent Operations**
   - `>>` - Indent line right
   - `<<` - Indent line left
   - `={motion}` - Auto-indent
   - Support count and visual mode

5. **Bracket Matching**
   - `%` - Jump to matching bracket/paren/brace
   - Support: (), [], {}, <>, /* */
   - HTML/XML tag matching

6. **Advanced Movement**
   - `[(` - Jump to previous unmatched (
   - `])` - Jump to next unmatched )
   - `[[` - Jump to previous section
   - `]]` - Jump to next section

**Deliverables:**
- `amplifier/vi/commands/editing/repeat.py`
- `amplifier/vi/commands/editing/join.py`
- `amplifier/vi/commands/editing/case.py`
- `amplifier/vi/commands/editing/indent.py`
- `amplifier/vi/commands/movements/brackets.py`
- `amplifier/vi/commands/movements/sections.py`
- Tests for all new commands

**Success Criteria:**
- All commands work with counts
- Work in visual mode where applicable
- Integrate with existing operator system
- 100% test coverage

---

## Phase 5: Text Objects Completion (MEDIUM PRIORITY)
**Priority: P2 - Medium**
**Estimated Complexity: Medium**
**Dependencies: Phase 4 (bracket matching)**

### Tasks:
1. **Bracket Text Objects**
   - `i(`, `a(` - Inside/around parentheses
   - `i[`, `a[` - Inside/around square brackets
   - `i{`, `a{` - Inside/around curly braces
   - `i<`, `a<` - Inside/around angle brackets

2. **Quote Text Objects**
   - `i"`, `a"` - Inside/around double quotes
   - `i'`, `a'` - Inside/around single quotes
   - `i\``, `a\`` - Inside/around backticks

3. **Tag Text Objects**
   - `it`, `at` - Inside/around HTML/XML tags
   - Handle self-closing tags
   - Handle nested tags

4. **Block Text Objects**
   - `iB` - Inside { } block
   - `aB` - Around { } block

**Deliverables:**
- `amplifier/vi/text_objects/brackets.py`
- `amplifier/vi/text_objects/quotes.py`
- `amplifier/vi/text_objects/tags.py`
- Text object tests

**Success Criteria:**
- All text objects work with operators (d, c, y)
- Handle nested structures
- Work in visual mode
- 100% test coverage

---

## Phase 6: Macro System (MEDIUM PRIORITY)
**Priority: P2 - Medium**
**Estimated Complexity: High**
**Dependencies: Phase 4 (repeat command for understanding change tracking)**

### Tasks:
1. **Macro Recording**
   - `q{register}` - Start recording to register
   - `q` - Stop recording
   - Capture all keystrokes during recording
   - Store in register system

2. **Macro Playback**
   - `@{register}` - Execute macro from register
   - `@@` - Repeat last executed macro
   - `{count}@{register}` - Execute macro count times
   - Handle errors during playback

3. **Macro Persistence**
   - Save macros to registers
   - Restore macros across sessions (optional)

**Deliverables:**
- `amplifier/vi/commands/macros/recorder.py`
- `amplifier/vi/commands/macros/player.py`
- Macro tests

**Success Criteria:**
- Record and playback work
- Complex macros work
- Count works
- 100% test coverage

---

## Phase 7: CLI Launcher (CRITICAL - DELIVERY)
**Priority: P0 - Blocking for delivery**
**Estimated Complexity: Low-Medium**
**Dependencies: Phase 1 (file I/O), Phase 2 (ex commands)**

### Tasks:
1. **Main Entry Point**
   - `vi` command that launches editor
   - `vi filename` - Open file
   - `vi +{line}` - Open at line
   - `vi +/{pattern}` - Open at pattern
   - `vi -R` - Read-only mode

2. **Terminal Integration**
   - Raw terminal mode setup
   - Cursor positioning
   - Screen refresh
   - Color support (if needed)
   - Signal handling (Ctrl-C, Ctrl-Z)

3. **Main Event Loop**
   - Key input handling
   - Command dispatch
   - Screen rendering
   - Status line display
   - Mode indicator

4. **Error Handling**
   - Graceful error messages
   - Recovery from exceptions
   - Clean terminal restoration on exit

**Deliverables:**
- `amplifier/vi/main.py`
- `amplifier/vi/cli.py`
- `bin/vi` or setup.py entry point
- CLI integration tests

**Success Criteria:**
- Launch with `vi` command
- Opens files correctly
- All modes work via terminal
- Clean exit
- Handles errors gracefully

---

## Phase 8: Comprehensive Testing Framework (CRITICAL - VALIDATION)
**Priority: P0 - Blocking for delivery**
**Estimated Complexity: High**
**Dependencies: Phase 7 (CLI launcher)**

### Test Strategy:

### 1. **Unit Tests** (Already largely done)
   - Test each module independently
   - Mock dependencies
   - Fast execution

### 2. **Integration Tests**
   - Test module interactions
   - Buffer + modes + commands
   - File I/O + buffer

### 3. **Functional Tests** (THE KEY PART)
   - Test complete workflows
   - Simulate user interactions
   - Compare against expected output

### 4. **Golden Master Tests** (YOUR REQUEST)
   - Start with input file
   - Execute sequence of vi commands
   - Compare output to known-good file
   - Byte-for-byte comparison

### Golden Master Test Design:

```python
# Test structure:
class ViGoldenTest:
    def test_scenario(self):
        # 1. Setup
        input_file = "test_input.txt"
        commands = load_commands("test_scenario.vicmd")
        expected_output = "test_expected.txt"

        # 2. Execute
        run_vi_commands(input_file, commands)

        # 3. Verify
        assert_files_identical("test_input.txt", expected_output)
```

### Test Scenarios to Create:

1. **Basic Editing** (`test_basic_editing.vicmd`)
   - Open file
   - Move cursor
   - Insert text
   - Delete text
   - Save and quit

2. **Advanced Navigation** (`test_navigation.vicmd`)
   - Word movements
   - Line movements
   - Search movements
   - Marks and jumps

3. **Operators and Motions** (`test_operators.vicmd`)
   - Delete with motions
   - Change with motions
   - Yank and put
   - Text objects

4. **Visual Mode** (`test_visual.vicmd`)
   - Character selection
   - Line selection
   - Block selection
   - Visual operations

5. **Ex Commands** (`test_ex_commands.vicmd`)
   - Substitution
   - Global commands
   - File operations
   - Range commands

6. **Search and Replace** (`test_search.vicmd`)
   - Forward/backward search
   - Repeat search
   - Substitution with regex

7. **Macros** (`test_macros.vicmd`)
   - Record macro
   - Play macro
   - Recursive macros

8. **Complex Workflows** (`test_complex.vicmd`)
   - Real-world editing scenarios
   - Multiple operations in sequence
   - Edge cases

### Test File Format (.vicmd):

```
# Vi Command Test File
# Lines starting with # are comments
# Each line is a command or special directive

@INPUT_FILE test_basic.txt
@EXPECTED_OUTPUT test_basic_expected.txt
@DESCRIPTION Basic editing test: insert, move, delete

# Commands (one per line):
i                    # Enter insert mode
Hello World<ESC>     # Type text and exit insert
0                    # Move to line start
w                    # Move to next word
dw                   # Delete word
:wq<CR>              # Save and quit
```

### Test Infrastructure:

**Deliverables:**
- `tests/vi_functional/test_runner.py` - Execute .vicmd files
- `tests/vi_functional/test_golden_master.py` - Golden master tests
- `tests/vi_functional/command_parser.py` - Parse .vicmd format
- `tests/vi_functional/scenarios/*.vicmd` - Test scenarios (20+)
- `tests/vi_functional/fixtures/` - Input and expected files
- `tests/vi_torture/` - Stress tests and edge cases

**Success Criteria:**
- 20+ golden master test scenarios
- 100% command coverage
- All tests pass
- Tests run in < 5 seconds total
- Easy to add new tests

---

## Phase 9: Multiple Buffers (OPTIONAL - ENHANCEMENT)
**Priority: P3 - Low**
**Estimated Complexity: Medium**
**Dependencies: Phase 2 (ex commands for buffer management)**

### Tasks:
1. **Buffer Management**
   - Multiple file buffers
   - Buffer list tracking
   - Switch between buffers

2. **Window System** (If time permits)
   - Split windows (horizontal/vertical)
   - Window navigation
   - Window resize

**Deliverables:**
- `amplifier/vi/buffers/manager.py`
- `amplifier/vi/windows/manager.py` (optional)
- Buffer management tests

**Success Criteria:**
- Open multiple files
- Switch between buffers
- Save all buffers

---

## Phase 10: Configuration System (OPTIONAL - ENHANCEMENT)
**Priority: P3 - Low**
**Estimated Complexity: Low**
**Dependencies: Phase 2 (settings commands)**

### Tasks:
1. **Config File Support**
   - `.virc` file parsing
   - Settings persistence
   - Key remapping

2. **Runtime Configuration**
   - Apply settings on startup
   - `:set` command integration

**Deliverables:**
- `amplifier/vi/config/loader.py`
- `amplifier/vi/config/parser.py`
- Config tests

**Success Criteria:**
- Load .virc on startup
- Settings work
- Key remapping works

---

## Implementation Order (Critical Path)

### Sprint 1: Make It Launchable (Weeks 1-2)
1. Phase 1: File I/O System
2. Phase 7: CLI Launcher (basic version)
3. Test: Can launch vi, edit file, save

### Sprint 2: Essential Commands (Weeks 3-4)
1. Phase 2: Ex Command System (core: :w, :q, :wq, :e)
2. Phase 3: Search System
3. Test: Can do basic vi workflow

### Sprint 3: Complete Core Features (Weeks 5-6)
1. Phase 4: Missing Normal Mode Commands
2. Phase 5: Text Objects Completion
3. Test: Can do advanced editing

### Sprint 4: Power Features (Week 7)
1. Phase 6: Macro System
2. Phase 2: Ex Commands (advanced: substitution, global)
3. Test: Can automate complex tasks

### Sprint 5: Testing & Polish (Week 8)
1. Phase 8: Comprehensive Testing Framework
2. Create 20+ golden master tests
3. Fix all failing tests
4. Performance optimization

### Sprint 6: Enhancements (Optional, Week 9+)
1. Phase 9: Multiple Buffers
2. Phase 10: Configuration System
3. Documentation and examples

---

## Success Metrics

### Minimum Viable Product (MVP):
- ✅ Launches with `vi filename`
- ✅ All modes work (normal, insert, visual, command)
- ✅ Can edit, save, quit
- ✅ Core ex commands work (:w, :q, :e, :s)
- ✅ Search works (/, ?, n, N)
- ✅ All basic movements and operators
- ✅ 90% test coverage

### Complete Product:
- ✅ Everything in MVP
- ✅ Macros work
- ✅ All text objects
- ✅ Advanced ex commands
- ✅ 20+ passing golden master tests
- ✅ 95% test coverage
- ✅ Documentation complete

### Excellent Product:
- ✅ Everything in Complete
- ✅ Multiple buffers
- ✅ Configuration system
- ✅ Performance optimized
- ✅ 30+ golden master tests
- ✅ 98% test coverage

---

## Risk Assessment

### High Risk:
1. **Terminal handling complexity** - May need curses or similar
2. **Ex command parser complexity** - Ranges, regex, etc.
3. **Test automation** - Simulating real vi input

### Medium Risk:
1. File encoding edge cases
2. Large file performance
3. Macro recording edge cases

### Mitigation:
- Use existing terminal libraries (blessed, prompt_toolkit)
- Start with simple ex commands, add complexity gradually
- Build test framework early, iterate

---

## Deliverables Summary

### Code Modules (New):
1. `amplifier/vi/file_io/` - File operations
2. `amplifier/vi/commands/ex/` - Ex command system
3. `amplifier/vi/search/commands.py` - Search integration
4. `amplifier/vi/commands/editing/` - New editing commands
5. `amplifier/vi/text_objects/` - Complete text objects
6. `amplifier/vi/commands/macros/` - Macro system
7. `amplifier/vi/main.py` - CLI launcher
8. `amplifier/vi/cli.py` - Terminal interface

### Test Infrastructure:
1. `tests/vi_functional/` - Functional test framework
2. `tests/vi_functional/scenarios/` - 20+ test scenarios
3. `tests/vi_functional/fixtures/` - Test files
4. `tests/vi_torture/` - Stress tests

### Documentation:
1. `amplifier/vi/README.md` - Updated with new features
2. `amplifier/vi/TESTING.md` - Testing guide
3. `amplifier/vi/CLI_GUIDE.md` - Command-line usage
4. `amplifier/vi/IMPLEMENTATION_COMPLETE.md` - Final report

---

## Timeline Estimate

- **Aggressive (1 developer, full-time):** 6-8 weeks
- **Realistic (1 developer, full-time):** 8-10 weeks
- **Conservative (1 developer, part-time):** 12-16 weeks

With AI assistance and existing codebase: **4-6 weeks to MVP, 6-8 weeks to Complete**

---

## Next Steps

1. Create super-planner project with this plan
2. Break into individual tasks
3. Assign agents to tasks
4. Begin Sprint 1: Make It Launchable
