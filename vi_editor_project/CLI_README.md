# Vi Editor CLI Interface

## Overview

A fully functional vi text editor implementation in Python with complete terminal support using curses.

## Installation & Usage

### Running the Editor

```bash
# Run directly with Python
python3 main.py [filename]

# Or use the executable wrapper
./vi [filename]

# View version
python3 main.py --version
```

### Command-Line Arguments

- `filename` (optional): File to edit. If the file doesn't exist, it will be created on save.
- `--version`: Display version information
- `--help`: Show help message

## Features

### Modes

- **Normal Mode**: Default mode for navigation and commands
- **Insert Mode**: Text insertion
- **Visual Mode**: Text selection (character and line-wise)
- **Command Mode**: Ex commands (`:w`, `:q`, etc.)

### Normal Mode Commands

#### Navigation
- `h`, `j`, `k`, `l` or arrow keys: Move cursor left/down/up/right
- `w`: Move forward one word
- `b`: Move backward one word
- `0`: Move to start of line
- `$`: Move to end of line
- `gg`: Move to first line
- `G`: Move to last line

#### Editing
- `x`: Delete character under cursor
- `dd`: Delete current line
- `dw`: Delete word
- `d$`: Delete to end of line
- `r<char>`: Replace character under cursor with `<char>`

#### Insert Mode Entry
- `i`: Insert before cursor
- `I`: Insert at start of line
- `a`: Append after cursor
- `A`: Append at end of line
- `o`: Open line below
- `O`: Open line above

#### Copy/Paste
- `yy`: Yank (copy) current line
- `p`: Paste after cursor

#### Visual Mode
- `v`: Enter character-wise visual mode
- `V`: Enter line-wise visual mode
- (in visual mode) `d`: Delete selection
- (in visual mode) `y`: Yank selection

#### Search
- `/pattern`: Search forward for pattern
- `n`: Jump to next match
- `N`: Jump to previous match

#### Undo/Redo
- `u`: Undo last change
- `Ctrl-R`: Redo

#### Commands
- `:`: Enter command mode

### Insert Mode Commands

- `ESC`: Exit to normal mode
- `Backspace`: Delete character before cursor
- `Enter`: Insert new line
- All printable characters: Insert at cursor

### Visual Mode Commands

- `ESC`: Exit to normal mode
- Navigation keys: Extend selection
- `d`: Delete selection
- `y`: Yank (copy) selection

### Ex Commands (Command Mode)

#### File Operations
- `:w`: Write (save) file
- `:w filename`: Write to specified filename
- `:q`: Quit (fails if modified)
- `:q!`: Quit without saving
- `:wq`: Write and quit
- `:x`: Write if modified, then quit

#### Display
- `:set number`: Show line numbers
- `:set nonumber`: Hide line numbers

#### Navigation
- `:123`: Jump to line 123

## Signal Handling

- `Ctrl-C`: Gracefully exit the editor (with prompt if modified)
- Terminal is properly restored on exit

## Module Architecture

The CLI integrates the following modules:

- **buffer.py**: Text buffer and cursor management
- **command_mode.py**: Normal mode command processing
- **insert_mode.py**: Insert mode text input
- **visual_mode.py**: Visual mode selection
- **display.py**: Terminal rendering with curses
- **file_io.py**: File reading/writing
- **search.py**: Pattern searching
- **undo_redo.py**: Undo/redo system

## Implementation Details

### Event Loop

The main event loop:
1. Renders the current buffer state
2. Waits for user input
3. Processes the input based on current mode
4. Updates buffer and cursor state
5. Repeats

### Mode State Machine

```
NORMAL ←→ INSERT
  ↓         ↑
  ↓         ↑
VISUAL ←----┘
  ↓
COMMAND (transient)
```

### Cursor Management

- Cursor position is maintained as `(row, col)` tuple (0-based)
- All modules update `buffer.cursor` to ensure consistency
- Display handles viewport scrolling automatically

### Undo/Redo System

- Automatically saves state before destructive operations
- Supports batch operations for multi-step commands
- Maximum history: 100 states (configurable)

### Error Handling

- File I/O errors are displayed in the status line
- Invalid commands are silently ignored (vi behavior)
- Terminal is always restored on exit

## Testing

The editor can be tested with:

```bash
# Test with new file
./vi test.txt

# Test with existing file
./vi CLI_README.md

# Test without filename
./vi
```

## Keyboard Shortcuts Reference

| Key      | Mode   | Action                    |
|----------|--------|---------------------------|
| ESC      | Any    | Return to normal mode     |
| i        | Normal | Insert before cursor      |
| a        | Normal | Insert after cursor       |
| o        | Normal | Open line below           |
| h/j/k/l  | Normal | Navigate                  |
| dd       | Normal | Delete line               |
| yy       | Normal | Yank line                 |
| p        | Normal | Paste                     |
| u        | Normal | Undo                      |
| Ctrl-R   | Normal | Redo                      |
| v        | Normal | Visual mode (char)        |
| V        | Normal | Visual mode (line)        |
| /        | Normal | Search forward            |
| :w       | Command| Save file                 |
| :q       | Command| Quit                      |

## Known Limitations

- No syntax highlighting (future extension)
- Single buffer only (future extension)
- No split windows (future extension)
- Basic regex search (no advanced patterns)

## Future Enhancements

Planned features for future versions:
- Multiple buffers/tabs
- Split window support
- Syntax highlighting
- Configuration file support
- Macro recording
- Plugin system
