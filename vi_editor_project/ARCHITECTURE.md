# Vi Editor Architecture Document

## Overview

This document defines the modular architecture for a Python implementation of the vi text editor, following Test-Driven Development (TDD) principles with a file-based testing approach.

## Core Philosophy

- **Ruthless Simplicity**: Each module does one thing well
- **Clear Boundaries**: Minimal coupling between modules
- **Testability First**: Design driven by test requirements
- **File-Based Testing**: All tests use input/action/expected files
- **Emergent Complexity**: Simple components compose into rich functionality

## Module Architecture

### 1. Buffer Management Module (`buffer.py`)

**Purpose**: Manages the text content and cursor position

**Core Responsibilities**:
- Store text as list of lines
- Track cursor position (row, col)
- Provide line insertion/deletion/modification
- Handle cursor boundary constraints
- Support efficient operations for large files

**Public Interface**:
```python
class Buffer:
    def __init__(self, lines: list[str] = None)
    def get_line(self, row: int) -> str
    def insert_line(self, row: int, text: str)
    def delete_line(self, row: int)
    def modify_line(self, row: int, text: str)
    def insert_char(self, row: int, col: int, char: str)
    def delete_char(self, row: int, col: int)

    @property
    def cursor(self) -> tuple[int, int]
    def move_cursor(self, row: int, col: int)
    def get_content(self) -> list[str]
    def line_count(self) -> int
```

### 2. Mode Management Module (`modes/`)

Organized as separate modules for each mode:
- `modes/command_mode.py`
- `modes/insert_mode.py`
- `modes/visual_mode.py`

**Base Mode Interface** (`modes/base.py`):
```python
class Mode:
    def process_key(self, key: str, buffer: Buffer, context: dict) -> tuple[str, dict]:
        """Returns (next_mode, updated_context)"""
```

**Command Mode** (`modes/command_mode.py`):
- Parse and execute movement commands (h,j,k,l,w,b,$,0,gg,G)
- Handle delete operations (x,dd,dw,d$)
- Process mode transitions (i,I,a,A,o,O,v,V)
- Execute ex commands (:w,:q,:wq)

**Insert Mode** (`modes/insert_mode.py`):
- Insert characters at cursor
- Handle special keys (backspace, enter, escape)
- Update buffer on each keystroke

**Visual Mode** (`modes/visual_mode.py`):
- Track selection start/end
- Extend selection with movements
- Apply operations to selection (d,y)

### 3. Command Parser Module (`parser.py`)

**Purpose**: Parse and tokenize vi commands

**Public Interface**:
```python
class CommandParser:
    def parse(self, input_str: str) -> Command

class Command:
    type: str  # 'movement', 'delete', 'yank', 'mode_change', 'ex'
    count: int
    operator: str
    motion: str
    args: list[str]
```

### 4. Registry Module (`registry.py`)

**Purpose**: Manage yank/delete register

**Public Interface**:
```python
class Registry:
    def set(self, name: str, content: list[str], is_line: bool)
    def get(self, name: str) -> tuple[list[str], bool]
    def clear(self, name: str = None)
```

### 5. Undo System Module (`undo.py`)

**Purpose**: Track and reverse operations

**Public Interface**:
```python
class UndoStack:
    def push_state(self, buffer_snapshot: dict)
    def undo(self) -> dict  # Returns buffer state to restore
    def redo(self) -> dict
    def can_undo(self) -> bool
    def can_redo(self) -> bool
```

### 6. Search Module (`search.py`)

**Purpose**: Find patterns in buffer

**Public Interface**:
```python
class SearchEngine:
    def find_next(self, pattern: str, buffer: Buffer, from_pos: tuple) -> tuple[int, int]
    def find_previous(self, pattern: str, buffer: Buffer, from_pos: tuple) -> tuple[int, int]
    def get_all_matches(self, pattern: str, buffer: Buffer) -> list[tuple]
```

### 7. File I/O Module (`file_io.py`)

**Purpose**: Read and write files

**Public Interface**:
```python
class FileIO:
    def read_file(self, filepath: str) -> list[str]
    def write_file(self, filepath: str, lines: list[str])
    def file_exists(self, filepath: str) -> bool
    def can_write(self, filepath: str) -> bool
```

### 8. Display Module (`display.py`)

**Purpose**: Render buffer to terminal

**Public Interface**:
```python
class Display:
    def __init__(self, terminal: Terminal)
    def render(self, buffer: Buffer, mode: str, status: dict)
    def show_command_line(self, text: str)
    def clear_command_line(self)
    def set_status(self, message: str)
```

### 9. Main Application Module (`editor.py`)

**Purpose**: Orchestrate all modules

**Core Flow**:
```python
class Editor:
    def __init__(self):
        self.buffer = Buffer()
        self.mode = CommandMode()
        self.display = Display()
        self.undo = UndoStack()
        self.registry = Registry()
        self.search = SearchEngine()
        self.file_io = FileIO()

    def run(self):
        while not self.quit:
            self.display.render(self.buffer, self.mode.name, self.status)
            key = self.get_input()
            self.mode, context = self.mode.process_key(key, self.buffer, context)
```

## Testing Architecture

### File-Based Test Framework (`test_framework.py`)

```python
class FileBasedTest:
    def __init__(self, test_dir: str):
        self.input_file = f"{test_dir}/input.txt"
        self.actions_file = f"{test_dir}/actions.txt"
        self.expected_file = f"{test_dir}/expected.txt"

    def run(self) -> bool:
        # 1. Load input into buffer
        # 2. Execute actions
        # 3. Compare output with expected
        # 4. Return pass/fail with diff
```

### Test Organization

```
tests/
├── buffer/
│   ├── test_empty_file/
│   │   ├── input.txt
│   │   ├── actions.txt
│   │   └── expected.txt
│   └── test_cursor_movement/
│       └── ...
├── navigation/
│   ├── test_hjkl/
│   ├── test_word_movement/
│   └── ...
├── insert/
│   ├── test_insert_mode/
│   └── ...
└── integration/
    ├── test_complex_editing/
    └── ...
```

### Actions File Format

```
# Comment lines start with #
# Each line is a command
i                  # Enter insert mode
Hello World        # Type text
<ESC>              # Escape key
:w output.txt      # Write file
```

## Data Flow

```
Input → Parser → Mode → Command → Buffer → Display
         ↓                ↓         ↓
      Validation      Registry    Undo
                         ↓         ↓
                      File I/O   Search
```

## Key Design Decisions

1. **Line-Based Buffer**: Text stored as list of strings for simplicity
2. **Mode Objects**: Each mode is a separate class with common interface
3. **Command Pattern**: Commands are parsed then executed
4. **Snapshot Undo**: Complete buffer state saved for undo
5. **File-Based Tests**: All testing through file I/O for clarity

## Implementation Order

1. Buffer + Basic cursor movement
2. Test framework
3. Navigation commands
4. Insert mode
5. Delete operations
6. Yank/paste
7. Visual mode
8. Undo/redo
9. Search
10. Replace
11. File I/O
12. Display
13. Integration

## Module Dependencies

```
editor.py
    ├── buffer.py (no deps)
    ├── modes/
    │   ├── base.py (no deps)
    │   ├── command_mode.py → parser.py
    │   ├── insert_mode.py → base.py
    │   └── visual_mode.py → base.py
    ├── parser.py (no deps)
    ├── registry.py (no deps)
    ├── undo.py (no deps)
    ├── search.py (no deps)
    ├── file_io.py (no deps)
    └── display.py (no deps)
```

## Error Handling

- Invalid commands: Ignore silently (vi behavior)
- File I/O errors: Display in status line
- Out of bounds: Constrain to valid positions
- Invalid regex: Show error message

## Performance Considerations

- Lazy loading for large files
- Efficient cursor movement (O(1))
- Minimal screen redraws
- Simple data structures

## Future Extensions

The modular design allows easy addition of:
- Syntax highlighting
- Multiple buffers
- Split windows
- Macros
- Plugins

## Conclusion

This architecture provides a clean, testable foundation for a vi editor implementation. Each module has a single responsibility and minimal dependencies, enabling parallel development and comprehensive testing.