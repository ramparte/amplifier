#!/usr/bin/env python3
"""
Vi Editor - Main CLI Entry Point

A minimal vi editor implementation in Python with full terminal support.
"""

import argparse
import curses
import signal
import sys

from buffer import Buffer
from command_mode import CommandMode
from display import Display
from file_io import FileIO
from insert_mode import InsertMode
from search import SearchManager
from undo_redo import UndoRedoManager
from visual_mode import VisualMode


class ViEditor:
    """Main vi editor application."""

    def __init__(self, filename: str | None = None):
        """Initialize the vi editor.

        Args:
            filename: Optional file to open on startup
        """
        self.filename = filename
        self.modified = False
        self.quit_requested = False
        self.cursor_pos = (0, 0)
        self.mode = "NORMAL"
        self.yank_buffer = ""
        self.yank_is_line = False
        self.last_search = ""
        self.status_message = ""
        self.command_input = ""
        self.in_command_mode = False

        # Initialize components
        self.buffer = Buffer()
        self.file_io = FileIO()
        self.display = Display()
        self.search_engine = SearchManager(self.buffer)
        self.command_mode = CommandMode(self.buffer)
        self.insert_mode = InsertMode(self.buffer)
        self.visual_mode = VisualMode(self)
        self.undo_redo = UndoRedoManager(self)

        # Load file if specified
        if filename:
            self._load_file(filename)

    def _load_file(self, filename: str) -> None:
        """Load a file into the buffer."""
        try:
            lines = self.file_io.read_file(filename)
            self.buffer.lines = lines if lines else [""]
            self.filename = filename
            self.modified = False
            self.status_message = f'"{filename}" {len(lines)} lines'
        except FileNotFoundError:
            # New file
            self.buffer.lines = [""]
            self.filename = filename
            self.modified = False
            self.status_message = f'"{filename}" [New File]'
        except Exception as e:
            self.buffer.lines = [""]
            self.status_message = f"Error loading file: {e}"

    def _save_file(self, filename: str | None = None) -> bool:
        """Save the buffer to a file.

        Args:
            filename: Optional filename to save to (overrides current)

        Returns:
            True if save was successful
        """
        target = filename or self.filename

        if not target:
            self.status_message = "No file name"
            return False

        try:
            lines = self.buffer.get_lines()
            self.file_io.write_file(target, lines)
            self.filename = target
            self.modified = False
            self.status_message = f'"{target}" {len(lines)}L written'
            return True
        except Exception as e:
            self.status_message = f"Error writing file: {e}"
            return False

    def run(self) -> None:
        """Main editor loop."""
        try:
            # Initialize curses
            self.display.init_curses()
            self.display.set_filename(self.filename or "[No Name]")
            self.display.set_modified(self.modified)

            # Save initial state for undo
            self.undo_redo.save_state("initial")

            # Main event loop
            while not self.quit_requested:
                self._render()
                key = self.display.get_input()

                if key:
                    self._process_key(key)

        except KeyboardInterrupt:
            # Ctrl-C pressed
            if self.modified:
                # TODO: Prompt to save changes
                pass
        finally:
            self.display.cleanup_curses()

    def _render(self) -> None:
        """Render the current editor state."""
        # Update display state
        self.display.set_mode(self.mode)
        self.display.set_filename(self.filename or "[No Name]")
        self.display.set_modified(self.modified)
        self.display.set_status_message(self.status_message)

        # Update visual selection if active
        if self.visual_mode.is_active:
            self.display.set_visual_selection(self.visual_mode.visual_start, self.visual_mode.visual_end)
        else:
            self.display.set_visual_selection(None, None)

        # Update command line
        if self.in_command_mode:
            self.display.set_command_line(self.command_input)
        else:
            self.display.set_command_line("")

        # Render
        lines = self.buffer.get_lines()
        self.display.render(lines, self.cursor_pos)

    def _process_key(self, key: str) -> None:
        """Process a keystroke based on current mode."""
        # Clear status message on next key
        if self.status_message and not self.in_command_mode:
            self.status_message = ""

        if self.in_command_mode:
            self._process_command_input(key)
        elif self.mode == "INSERT":
            self._process_insert_mode(key)
        elif self.mode == "VISUAL":
            self._process_visual_mode(key)
        else:  # NORMAL mode
            self._process_normal_mode(key)

    def _process_normal_mode(self, key: str) -> None:
        """Process keystrokes in normal mode."""
        row, col = self.cursor_pos

        # Mode transitions
        if key in ["i", "I", "a", "A", "o", "O"]:
            self._enter_insert_mode(key)
        elif key == "v":
            self.visual_mode.enter_visual_mode("char")
            self.mode = "VISUAL"
        elif key == "V":
            self.visual_mode.enter_visual_mode("line")
            self.mode = "VISUAL"
        elif key == ":":
            self.in_command_mode = True
            self.command_input = ":"

        # Undo/Redo
        elif key == "u":
            if self.undo_redo.undo():
                self.status_message = "Undo"
            else:
                self.status_message = "Already at oldest change"
            self.cursor_pos = self.cursor_pos  # Updated by undo_redo
        elif key == "\x12":  # Ctrl-R
            if self.undo_redo.redo():
                self.status_message = "Redo"
            else:
                self.status_message = "Already at newest change"
            self.cursor_pos = self.cursor_pos  # Updated by undo_redo

        # Navigation
        elif key in ["h", "KEY_LEFT"]:
            self.command_mode.process_command("h")
            self.cursor_pos = self.buffer.cursor
        elif key in ["j", "KEY_DOWN"]:
            self.command_mode.process_command("j")
            self.cursor_pos = self.buffer.cursor
        elif key in ["k", "KEY_UP"]:
            self.command_mode.process_command("k")
            self.cursor_pos = self.buffer.cursor
        elif key in ["l", "KEY_RIGHT"]:
            self.command_mode.process_command("l")
            self.cursor_pos = self.buffer.cursor
        elif key == "w":
            self.command_mode.process_command("w")
            self.cursor_pos = self.buffer.cursor
        elif key == "b":
            self.command_mode.process_command("b")
            self.cursor_pos = self.buffer.cursor
        elif key == "0":
            self.command_mode.process_command("0")
            self.cursor_pos = self.buffer.cursor
        elif key == "$":
            self.command_mode.process_command("$")
            self.cursor_pos = self.buffer.cursor
        elif key == "g":
            # Wait for next 'g' for gg command
            next_key = self.display.get_input()
            if next_key == "g":
                self.command_mode.process_command("gg")
                self.cursor_pos = self.buffer.cursor
        elif key == "G":
            self.command_mode.process_command("G")
            self.cursor_pos = self.buffer.cursor

        # Delete operations
        elif key == "x":
            self.undo_redo.save_state("delete char")
            self.command_mode.process_command("x")
            self.cursor_pos = self.buffer.cursor
            self.modified = True
        elif key == "d":
            next_key = self.display.get_input()
            if next_key == "d":
                self.undo_redo.save_state("delete line")
                self.command_mode.process_command("dd")
                self.cursor_pos = self.buffer.cursor
                self.modified = True
            elif next_key == "w":
                self.undo_redo.save_state("delete word")
                self.command_mode.process_command("dw")
                self.cursor_pos = self.buffer.cursor
                self.modified = True
            elif next_key == "$":
                self.undo_redo.save_state("delete to end")
                self.command_mode.process_command("d$")
                self.cursor_pos = self.buffer.cursor
                self.modified = True

        # Yank and paste
        elif key == "y":
            next_key = self.display.get_input()
            if next_key == "y":
                self.command_mode.process_command("yy")
                # Get yanked text from buffer
                row, _ = self.cursor_pos
                lines = self.buffer.get_lines()
                if row < len(lines):
                    self.yank_buffer = lines[row] + "\n"
                    self.yank_is_line = True
                    self.status_message = "Yanked line"
        elif key == "p":
            if self.yank_buffer:
                self.undo_redo.save_state("paste")
                self.command_mode.process_command("p")
                self.cursor_pos = self.buffer.cursor
                self.modified = True

        # Replace
        elif key == "r":
            next_key = self.display.get_input()
            if next_key and len(next_key) == 1:
                self.undo_redo.save_state("replace char")
                self.command_mode.process_command(f"r{next_key}")
                self.cursor_pos = self.buffer.cursor
                self.modified = True

        # Search
        elif key == "/":
            self.in_command_mode = True
            self.command_input = "/"
        elif key == "n":
            if self.last_search:
                result = self.search_engine.search_forward(self.last_search, self.cursor_pos)
                if result:
                    self.cursor_pos = result
                    self.buffer.cursor = result
                    self.status_message = f"Found: {self.last_search}"
                else:
                    self.status_message = "Pattern not found"
        elif key == "N" and self.last_search:
            result = self.search_engine.search_backward(self.last_search, self.cursor_pos)
            if result:
                self.cursor_pos = result
                self.buffer.cursor = result
                self.status_message = f"Found: {self.last_search}"
            else:
                self.status_message = "Pattern not found"

    def _process_visual_mode(self, key: str) -> None:
        """Process keystrokes in visual mode."""
        if key == "KEY_ESC" or key == "\x1b":
            self.visual_mode.exit_visual_mode()
            self.mode = "NORMAL"

        # Movement updates selection
        elif key in ["h", "j", "k", "l", "w", "b", "$", "0", "KEY_LEFT", "KEY_DOWN", "KEY_UP", "KEY_RIGHT"]:
            # Process movement in normal mode
            self._process_normal_mode(key)
            # Update visual selection
            self.visual_mode.update_selection(self.cursor_pos)

        # Operations on selection
        elif key == "d":
            self.undo_redo.save_state("visual delete")
            deleted = self.visual_mode.delete_selection()
            self.yank_buffer = deleted
            self.yank_is_line = self.visual_mode.visual_mode_type == "line"
            self.modified = True
            self.mode = "NORMAL"
        elif key == "y":
            yanked = self.visual_mode.yank_selection()
            self.yank_buffer = yanked
            self.yank_is_line = self.visual_mode.visual_mode_type == "line"
            self.status_message = "Yanked"
            self.mode = "NORMAL"

    def _process_insert_mode(self, key: str) -> None:
        """Process keystrokes in insert mode."""
        if key == "KEY_ESC" or key == "\x1b":
            self.mode = "NORMAL"
            # Move cursor left if not at start of line
            row, col = self.cursor_pos
            if col > 0:
                self.cursor_pos = (row, col - 1)
                self.buffer.cursor = self.cursor_pos
            return

        # Save state before first character
        if not self.modified:
            self.undo_redo.save_state("insert")

        if key == "KEY_BACKSPACE":
            row, col = self.cursor_pos
            lines = self.buffer.get_lines()

            if col > 0:
                # Delete character before cursor
                line = lines[row]
                lines[row] = line[: col - 1] + line[col:]
                self.cursor_pos = (row, col - 1)
                self.buffer.cursor = self.cursor_pos
                self.modified = True
            elif row > 0:
                # Join with previous line
                current_line = lines[row]
                prev_line = lines[row - 1]
                new_col = len(prev_line)
                lines[row - 1] = prev_line + current_line
                del lines[row]
                self.cursor_pos = (row - 1, new_col)
                self.buffer.cursor = self.cursor_pos
                self.modified = True

        elif key == "KEY_ENTER" or key == "\n":
            row, col = self.cursor_pos
            lines = self.buffer.get_lines()
            line = lines[row]

            # Split line at cursor
            lines[row] = line[:col]
            lines.insert(row + 1, line[col:])
            self.cursor_pos = (row + 1, 0)
            self.buffer.cursor = self.cursor_pos
            self.modified = True

        elif len(key) == 1 and key.isprintable():
            # Insert character
            row, col = self.cursor_pos
            lines = self.buffer.get_lines()
            line = lines[row]
            lines[row] = line[:col] + key + line[col:]
            self.cursor_pos = (row, col + 1)
            self.buffer.cursor = self.cursor_pos
            self.modified = True

    def _enter_insert_mode(self, command: str) -> None:
        """Enter insert mode with the specified command."""
        row, col = self.cursor_pos
        lines = self.buffer.get_lines()

        self.mode = "INSERT"

        if command == "i":
            # Insert before cursor
            pass
        elif command == "I":
            # Insert at start of line
            self.cursor_pos = (row, 0)
            self.buffer.cursor = self.cursor_pos
        elif command == "a":
            # Append after cursor
            if lines and row < len(lines):
                line_len = len(lines[row])
                new_col = min(col + 1, line_len)
                self.cursor_pos = (row, new_col)
                self.buffer.cursor = self.cursor_pos
        elif command == "A":
            # Append at end of line
            if lines and row < len(lines):
                new_col = len(lines[row])
                self.cursor_pos = (row, new_col)
                self.buffer.cursor = self.cursor_pos
        elif command == "o":
            # Open line below
            self.undo_redo.save_state("open line below")
            lines.insert(row + 1, "")
            self.cursor_pos = (row + 1, 0)
            self.buffer.cursor = self.cursor_pos
            self.modified = True
        elif command == "O":
            # Open line above
            self.undo_redo.save_state("open line above")
            lines.insert(row, "")
            self.cursor_pos = (row, 0)
            self.buffer.cursor = self.cursor_pos
            self.modified = True

    def _process_command_input(self, key: str) -> None:
        """Process command line input."""
        if key == "KEY_ESC" or key == "\x1b":
            self.in_command_mode = False
            self.command_input = ""
            return

        if key == "KEY_BACKSPACE":
            if len(self.command_input) > 1:
                self.command_input = self.command_input[:-1]
            else:
                self.in_command_mode = False
                self.command_input = ""
            return

        if key == "KEY_ENTER" or key == "\n":
            self._execute_command(self.command_input)
            self.in_command_mode = False
            self.command_input = ""
            return

        if len(key) == 1 and key.isprintable():
            self.command_input += key

    def _execute_command(self, command: str) -> None:
        """Execute an ex command."""
        if not command or len(command) < 2:
            return

        cmd = command[1:].strip()  # Remove : or /

        if command.startswith(":"):
            # Ex commands
            if cmd == "q":
                if self.modified:
                    self.status_message = "No write since last change (use :q! to override)"
                else:
                    self.quit_requested = True
            elif cmd == "q!":
                self.quit_requested = True
            elif cmd == "w":
                self._save_file()
            elif cmd.startswith("w "):
                filename = cmd[2:].strip()
                self._save_file(filename)
            elif cmd == "wq":
                if self._save_file():
                    self.quit_requested = True
            elif cmd == "x":
                if self.modified:
                    if self._save_file():
                        self.quit_requested = True
                else:
                    self.quit_requested = True
            elif cmd.isdigit():
                # Jump to line number
                line_num = int(cmd) - 1  # Convert to 0-based
                lines = self.buffer.get_lines()
                if 0 <= line_num < len(lines):
                    self.cursor_pos = (line_num, 0)
                    self.buffer.cursor = self.cursor_pos
            elif cmd == "set number":
                self.display.enable_line_numbers(True)
            elif cmd == "set nonumber":
                self.display.enable_line_numbers(False)
            else:
                self.status_message = f"Unknown command: {cmd}"

        elif command.startswith("/") and cmd:
            # Search
            self.last_search = cmd
            result = self.search_engine.search_forward(cmd, self.cursor_pos)
            if result:
                self.cursor_pos = result
                self.buffer.cursor = result
                self.status_message = f"Found: {cmd}"
            else:
                self.status_message = "Pattern not found"


def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""

    def signal_handler(signum, frame):
        # Restore terminal on Ctrl-C
        curses.endwin()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)


def main() -> int:
    """Main entry point for the vi editor."""
    parser = argparse.ArgumentParser(description="Vi text editor in Python")
    parser.add_argument("file", nargs="?", help="File to edit")
    parser.add_argument("--version", action="version", version="vi 1.0.0")

    args = parser.parse_args()

    # Set up signal handlers
    setup_signal_handlers()

    # Create and run editor
    editor = ViEditor(args.file)
    editor.run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
