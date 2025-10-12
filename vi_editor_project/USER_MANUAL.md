# Vi Editor - User Manual

## Table of Contents
1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Editor Modes](#editor-modes)
4. [Command Reference](#command-reference)
5. [Keyboard Shortcuts](#keyboard-shortcuts)
6. [Tips and Tricks](#tips-and-tricks)

## Installation

### Requirements
- Python 3.11 or higher
- Unix-like terminal with curses support (Linux, macOS, WSL)

### Quick Start
```bash
# Navigate to the vi editor directory
cd /workspaces/amplifier/vi_editor_project

# Make the main script executable
chmod +x main.py

# Run the editor
./main.py [filename]

# Or use Python directly
python3 main.py [filename]
```

## Getting Started

### Opening Files
```bash
# Open an existing file
./main.py myfile.txt

# Create a new file
./main.py newfile.txt

# Start without a file
./main.py
```

### Basic Workflow
1. Start in **NORMAL** mode - for navigation and commands
2. Press `i` to enter **INSERT** mode - for typing text
3. Press `ESC` to return to NORMAL mode
4. Type `:w` to save your work
5. Type `:q` to quit (or `:wq` to save and quit)

## Editor Modes

### NORMAL Mode (Default)
The command mode where you navigate and execute commands. This is the default mode when you start the editor.

### INSERT Mode
Text input mode. Enter from NORMAL mode using:
- `i` - Insert before cursor
- `I` - Insert at beginning of line
- `a` - Append after cursor
- `A` - Append at end of line
- `o` - Open new line below
- `O` - Open new line above

Press `ESC` to return to NORMAL mode.

### VISUAL Mode
Selection mode for operating on text regions. Enter from NORMAL mode using:
- `v` - Character-wise visual mode
- `V` - Line-wise visual mode

Press `ESC` to return to NORMAL mode.

### COMMAND Mode
Ex command mode for file operations and settings. Enter from NORMAL mode by typing `:`.

## Command Reference

### Navigation Commands

| Command | Description |
|---------|-------------|
| `h` or `←` | Move cursor left |
| `j` or `↓` | Move cursor down |
| `k` or `↑` | Move cursor up |
| `l` or `→` | Move cursor right |
| `w` | Jump to next word |
| `b` | Jump to previous word |
| `0` | Jump to beginning of line |
| `$` | Jump to end of line |
| `gg` | Jump to first line |
| `G` | Jump to last line |
| `:[n]` | Jump to line number [n] |

### Editing Commands

#### Insert Mode Transitions
| Command | Description |
|---------|-------------|
| `i` | Insert before cursor |
| `I` | Insert at beginning of line |
| `a` | Append after cursor |
| `A` | Append at end of line |
| `o` | Open new line below |
| `O` | Open new line above |

#### Delete Commands
| Command | Description |
|---------|-------------|
| `x` | Delete character under cursor |
| `dd` | Delete entire line |
| `dw` | Delete word |
| `d$` | Delete from cursor to end of line |
| `d` (in VISUAL) | Delete selected text |

#### Copy and Paste
| Command | Description |
|---------|-------------|
| `yy` | Yank (copy) current line |
| `y` (in VISUAL) | Yank selected text |
| `p` | Paste after cursor/line |

#### Replace
| Command | Description |
|---------|-------------|
| `r[char]` | Replace character under cursor with [char] |

#### Undo/Redo
| Command | Description |
|---------|-------------|
| `u` | Undo last change |
| `Ctrl-R` | Redo undone change |

### Search Commands

| Command | Description |
|---------|-------------|
| `/pattern` | Search forward for pattern |
| `n` | Repeat last search forward |
| `N` | Repeat last search backward |

### File Commands (Ex Commands)

| Command | Description |
|---------|-------------|
| `:w` | Save file |
| `:w filename` | Save as filename |
| `:q` | Quit (fails if unsaved changes) |
| `:q!` | Force quit (discards changes) |
| `:wq` or `:x` | Save and quit |
| `:set number` | Show line numbers |
| `:set nonumber` | Hide line numbers |

## Keyboard Shortcuts

### Quick Reference Card

#### Normal Mode
```
Movement:           Editing:            File:
h j k l - arrows   x    - delete char   :w  - save
w       - word →   dd   - delete line   :q  - quit
b       - word ←   yy   - yank line     :wq - save & quit
0       - line ↹   p    - paste
$       - line end r    - replace char
gg      - file top u    - undo
G       - file end ^R   - redo
```

#### Mode Switching
```
Normal → Insert:    Normal → Visual:    Any → Normal:
i - insert before  v - char select     ESC - escape
a - insert after   V - line select
o - new line below
```

## Tips and Tricks

### Efficient Editing

1. **Quick Save and Continue**
   - While in NORMAL mode, type `:w` and press Enter to save without quitting
   - This preserves your cursor position and mode

2. **Jump to Specific Lines**
   - Type `:42` to jump to line 42
   - Use `gg` for first line, `G` for last line

3. **Word Navigation**
   - Use `w` and `b` to quickly move between words
   - Combine with delete: `dw` deletes from cursor to end of word

4. **Line Operations**
   - `dd` deletes a line and stores it in the yank buffer
   - Follow with `p` to move the line elsewhere

5. **Visual Selection**
   - Use `v` for precise character selection
   - Use `V` for quick line selection
   - Selected text can be deleted (`d`) or yanked (`y`)

### Common Workflows

#### Find and Replace (Manual)
1. Search with `/pattern`
2. Navigate with `n` and `N`
3. Replace with `r` for single character
4. Or delete and insert for longer replacements

#### Moving Lines
1. Position cursor on line to move
2. `dd` to cut the line
3. Navigate to destination
4. `p` to paste below current line

#### Copying Text Blocks
1. Enter visual mode with `v` or `V`
2. Select desired text with navigation keys
3. `y` to yank (copy)
4. Navigate to destination
5. `p` to paste

### Troubleshooting

**Can't exit?**
- Press `ESC` to ensure you're in NORMAL mode
- Type `:q!` to force quit without saving
- Or `:wq` to save and quit

**Cursor won't move in INSERT mode?**
- INSERT mode is for text entry only
- Press `ESC` to return to NORMAL mode for navigation

**Lost your changes?**
- Use `u` to undo recent changes
- Use `Ctrl-R` to redo if you undo too much

**File won't save?**
- Check file permissions
- Ensure you have write access to the directory
- Try `:w!` to force write if you own the file

### Best Practices

1. **Stay in NORMAL mode** - Only enter INSERT mode when actually typing
2. **Use the right tool** - Each command has its purpose, learn when to use each
3. **Practice the basics** - Master `h,j,k,l` navigation before learning advanced commands
4. **Save often** - Use `:w` regularly to save your work
5. **Learn incrementally** - Start with basic commands, add more as you get comfortable

## Quick Start Tutorial

### Lesson 1: Basic Navigation
1. Open a test file: `./main.py test.txt`
2. Use `h`, `j`, `k`, `l` to move around
3. Try `w` and `b` for word jumping
4. Use `0` and `$` for line start/end

### Lesson 2: Making Changes
1. Press `i` to enter INSERT mode
2. Type some text
3. Press `ESC` to return to NORMAL mode
4. Position cursor and press `x` to delete characters
5. Press `u` to undo changes

### Lesson 3: Saving Your Work
1. Make some changes to your file
2. Press `ESC` to ensure you're in NORMAL mode
3. Type `:w` and press Enter to save
4. Type `:q` and press Enter to quit

### Lesson 4: Efficient Editing
1. Try `dd` to delete a whole line
2. Use `yy` to copy a line
3. Move cursor and press `p` to paste
4. Experiment with visual mode using `v` or `V`

## Version Information

Vi Editor v1.0.0 - A minimal vi implementation in Python

For bug reports and feature requests, please contact the development team.