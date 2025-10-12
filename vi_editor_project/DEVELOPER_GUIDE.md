# Vi Editor - Developer Guide

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Module Descriptions](#module-descriptions)
3. [Code Organization](#code-organization)
4. [Testing Strategy](#testing-strategy)
5. [Contributing Guidelines](#contributing-guidelines)
6. [Known Limitations](#known-limitations)

## Architecture Overview

### Design Philosophy
The vi editor is built with a modular architecture that separates concerns and makes the codebase maintainable and testable. The design follows these principles:

- **Separation of Concerns**: Each module handles a specific aspect of functionality
- **Clear Interfaces**: Modules communicate through well-defined interfaces
- **State Management**: Centralized state management through the Buffer and main Editor
- **Event-Driven**: User input drives state transitions and actions

### Core Components

```
┌──────────────────────────────────────────┐
│             main.py (ViEditor)           │
│         Central orchestrator              │
└────┬───────┬────────┬────────┬──────────┘
     │       │        │        │
     v       v        v        v
┌────────┐ ┌──────┐ ┌───────┐ ┌──────────┐
│ Buffer │ │Display│ │FileIO │ │ Commands │
│        │ │      │ │       │ │          │
└────────┘ └──────┘ └───────┘ └──────────┘
     ^                             ^
     │                             │
┌────────┐ ┌──────────┐ ┌────────┴────────┐
│ Search │ │UndoRedo  │ │  Mode Handlers  │
│        │ │          │ │ (Insert/Visual) │
└────────┘ └──────────┘ └─────────────────┘
```

### Mode State Machine

```
        ┌─────────┐
        │ NORMAL  │ ←──── ESC ────┐
        └────┬────┘               │
         /   │   \                │
        /    │    \               │
       v     v     v              │
   ┌──────┐ ┌────────┐ ┌─────────┴┐
   │INSERT│ │COMMAND │ │  VISUAL  │
   └──────┘ └────────┘ └──────────┘
```

## Module Descriptions

### main.py - Application Entry Point
**Purpose**: Central orchestrator that manages the editor lifecycle and coordinates between modules.

**Key Responsibilities**:
- Initialize all components
- Handle main event loop
- Route keystrokes to appropriate handlers
- Manage mode transitions
- Coordinate between modules

**Key Classes**:
- `ViEditor`: Main application class

### buffer.py - Text Buffer Management
**Purpose**: Manages the text content and cursor position.

**Key Responsibilities**:
- Store and manipulate text lines
- Track cursor position
- Provide text manipulation primitives
- Handle bounds checking

**Key Classes**:
- `Buffer`: Text buffer with cursor management

**Public Interface**:
```python
class Buffer:
    lines: list[str]
    cursor: tuple[int, int]

    def get_lines() -> list[str]
    def set_lines(lines: list[str])
    def get_char_at(row: int, col: int) -> str
    def insert_char(char: str, row: int, col: int)
    def delete_char(row: int, col: int)
```

### display.py - Terminal Display Management
**Purpose**: Handles all terminal rendering and input operations using curses.

**Key Responsibilities**:
- Initialize and manage curses
- Render text with syntax highlighting (if enabled)
- Display status line and mode indicator
- Handle terminal resize
- Show line numbers (optional)
- Visual selection highlighting

**Key Classes**:
- `Display`: Terminal display manager

**Public Interface**:
```python
class Display:
    def init_curses()
    def cleanup_curses()
    def render(lines: list[str], cursor: tuple[int, int])
    def get_input() -> str
    def set_status_message(msg: str)
    def set_mode(mode: str)
```

### command_mode.py - Normal Mode Commands
**Purpose**: Implements vi normal mode commands.

**Key Responsibilities**:
- Navigation commands (h,j,k,l,w,b,etc.)
- Deletion commands (x,dd,dw,d$)
- Yank and paste operations
- Text replacement
- Command parsing and execution

**Key Classes**:
- `CommandMode`: Command processor

**Supported Commands**:
- Movement: `h`, `j`, `k`, `l`, `w`, `b`, `0`, `$`, `gg`, `G`
- Delete: `x`, `dd`, `dw`, `d$`
- Yank/Paste: `yy`, `p`
- Replace: `r[char]`

### insert_mode.py - Insert Mode Handler
**Purpose**: Handles text insertion and editing in INSERT mode.

**Key Responsibilities**:
- Character insertion
- Backspace handling
- Enter key (line splitting)
- Mode entry variations (i,I,a,A,o,O)

**Key Classes**:
- `InsertMode`: Insert mode handler

### visual_mode.py - Visual Selection Mode
**Purpose**: Implements visual selection and operations.

**Key Responsibilities**:
- Character-wise selection (v)
- Line-wise selection (V)
- Selection operations (delete, yank)
- Selection rendering coordination

**Key Classes**:
- `VisualMode`: Visual mode handler

**Key Methods**:
```python
def enter_visual_mode(mode_type: str)
def update_selection(cursor_pos: tuple[int, int])
def delete_selection() -> str
def yank_selection() -> str
```

### search.py - Search Functionality
**Purpose**: Implements text search capabilities.

**Key Responsibilities**:
- Forward search (/)
- Backward search (?)
- Find next/previous (n/N)
- Pattern matching

**Key Classes**:
- `SearchManager`: Search engine

**Public Interface**:
```python
def search_forward(pattern: str, start_pos: tuple[int, int]) -> tuple[int, int] | None
def search_backward(pattern: str, start_pos: tuple[int, int]) -> tuple[int, int] | None
```

### undo_redo.py - Undo/Redo System
**Purpose**: Implements undo and redo functionality.

**Key Responsibilities**:
- Save editor states
- Navigate history (undo/redo)
- Manage state stack
- Memory optimization

**Key Classes**:
- `UndoRedoManager`: History manager

**Key Methods**:
```python
def save_state(description: str)
def undo() -> bool
def redo() -> bool
```

### file_io.py - File Operations
**Purpose**: Handles reading and writing files.

**Key Responsibilities**:
- Read files with encoding detection
- Write files with proper line endings
- Handle file permissions
- Error handling and reporting

**Key Classes**:
- `FileIO`: File operations handler

**Public Interface**:
```python
def read_file(filepath: str) -> list[str]
def write_file(filepath: str, lines: list[str])
```

## Code Organization

### Directory Structure
```
vi_editor_project/
├── main.py              # Entry point and main application
├── buffer.py            # Text buffer management
├── display.py           # Terminal display (curses)
├── command_mode.py      # Normal mode commands
├── insert_mode.py       # Insert mode handling
├── visual_mode.py       # Visual selection mode
├── search.py           # Search functionality
├── undo_redo.py        # Undo/redo system
├── file_io.py          # File operations
├── test_*.py           # Test files for each module
├── test_framework.py    # Testing utilities
├── USER_MANUAL.md      # User documentation
└── DEVELOPER_GUIDE.md  # This file
```

### Import Structure
The project uses a flat import structure with minimal dependencies between modules:

```python
# main.py imports all modules
from buffer import Buffer
from display import Display
from file_io import FileIO
from command_mode import CommandMode
from insert_mode import InsertMode
from visual_mode import VisualMode
from search import SearchManager
from undo_redo import UndoRedoManager

# Modules import only what they need
# Most modules depend on Buffer
# Visual and UndoRedo depend on the main Editor
```

### State Management
- **Global State**: Managed by `ViEditor` class in main.py
- **Buffer State**: Text content and cursor in `Buffer`
- **Display State**: Terminal state in `Display`
- **Mode State**: Current mode tracked in `ViEditor.mode`
- **History State**: Undo/redo stack in `UndoRedoManager`

## Testing Strategy

### Test Framework
Custom lightweight test framework in `test_framework.py` provides:
- Test discovery and execution
- Assertion helpers
- Mock objects
- Test reporting

### Test Organization
Each module has a corresponding test file:
- `test_buffer.py` - Buffer operations
- `test_display.py` - Display rendering
- `test_navigation.py` - Cursor movement
- `test_insert.py` - Insert mode
- `test_delete.py` - Delete operations
- `test_visual.py` - Visual mode
- `test_search.py` - Search functionality
- `test_undo_redo.py` - History management
- `test_file_io.py` - File operations
- `test_integration.py` - End-to-end tests

### Running Tests
```bash
# Run all tests
python3 test_framework.py

# Run specific test file
python3 test_buffer.py

# Run with verbose output
python3 test_framework.py -v
```

### Writing Tests
Example test structure:
```python
from test_framework import TestCase, run_tests

class TestMyFeature(TestCase):
    def setUp(self):
        # Initialize test state
        self.buffer = Buffer()

    def test_specific_behavior(self):
        # Arrange
        self.buffer.lines = ["test"]

        # Act
        result = self.buffer.get_char_at(0, 0)

        # Assert
        self.assertEqual(result, "t")

if __name__ == "__main__":
    run_tests(TestMyFeature)
```

## Contributing Guidelines

### Code Style
- Follow PEP 8 style guidelines
- Use type hints for function signatures
- Keep functions focused and small
- Document complex logic with comments

### Adding New Features

1. **Plan the Feature**
   - Identify which module(s) need changes
   - Consider impact on existing functionality
   - Design the interface first

2. **Implement with Tests**
   - Write tests first (TDD approach)
   - Implement the feature
   - Ensure all tests pass

3. **Integration**
   - Update main.py if new mode or command
   - Update command_mode.py for new commands
   - Ensure proper state management

### Example: Adding a New Command
```python
# 1. Add to command_mode.py
def process_command(self, command: str) -> bool:
    # ... existing commands ...
    elif command == "new_cmd":
        return self._handle_new_command()

def _handle_new_command(self) -> bool:
    # Implementation
    pass

# 2. Add key binding in main.py
def _process_normal_mode(self, key: str):
    # ... existing bindings ...
    elif key == "x":  # Your key
        self.command_mode.process_command("new_cmd")

# 3. Write tests in test_command.py
def test_new_command(self):
    # Test implementation
```

### Debugging Tips

1. **Enable Debug Mode**
   ```python
   # Add to main.py temporarily
   import logging
   logging.basicConfig(filename='vi_debug.log', level=logging.DEBUG)
   ```

2. **Curses Debugging**
   ```python
   # Temporarily disable curses for print debugging
   def debug_print(msg):
       with open('debug.txt', 'a') as f:
           f.write(f"{msg}\n")
   ```

3. **State Inspection**
   - Add status line debug info
   - Log state transitions
   - Track command execution

## Known Limitations

### Current Limitations

1. **No Regex Support**
   - Search uses literal string matching
   - No pattern matching or regular expressions

2. **Limited Ex Commands**
   - Basic subset implemented (:w, :q, :wq, etc.)
   - No range operations (:%s///)
   - No shell commands (:!)

3. **No Syntax Highlighting**
   - Display module has hooks but not implemented
   - Would require language-specific parsers

4. **No Multiple Buffers**
   - Single file editing only
   - No split windows or tabs

5. **Limited Visual Mode**
   - Basic character and line selection
   - No block visual mode (Ctrl-V)

6. **No Macros**
   - No recording or playback (q command)
   - No repeat last command (.)

7. **Platform Limitations**
   - Requires Unix-like terminal with curses
   - May not work on Windows without WSL

### Future Enhancements

#### High Priority
- [ ] Multiple buffers/windows
- [ ] Syntax highlighting framework
- [ ] Configuration file support (.virc)
- [ ] Plugin system architecture

#### Medium Priority
- [ ] Regex search support
- [ ] More ex commands
- [ ] Block visual mode
- [ ] Macro recording/playback

#### Low Priority
- [ ] Mouse support
- [ ] Unicode handling improvements
- [ ] Performance optimizations for large files

### Performance Considerations

- **Large Files**: Not optimized for files > 10MB
- **Long Lines**: May have rendering issues with lines > 1000 chars
- **Undo History**: Memory usage grows with edit history

### Security Considerations

- No command execution from files
- No arbitrary code execution
- File permissions respected
- No network operations

## Conclusion

This vi editor implementation provides a solid foundation for a text editor with room for growth. The modular architecture makes it easy to add new features or modify existing ones. The test suite ensures reliability as the codebase evolves.

For questions or contributions, please refer to the project repository documentation.