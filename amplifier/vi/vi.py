"""Main vi editor implementation."""

import re
import sys
import termios
import tty

from .buffer.core import TextBuffer
from .commands.executor import CommandExecutor
from .modes.state import ModeManager
from .terminal.render import Renderer


class Vi:
    """Main vi editor class that coordinates buffer, modes, and rendering."""

    def __init__(self, filename: str | None = None):
        """Initialize vi editor with optional file to open."""
        self.buffer = TextBuffer()
        self.modes = ModeManager()
        self.renderer = Renderer()
        self.executor = CommandExecutor(self.buffer, self.modes, self.renderer)
        self.filename = filename
        self.running = False
        self._command_buffer = ""

        # Load file if provided
        if filename:
            self._load_file(filename)

    def _load_file(self, filename: str) -> None:
        """Load a file into the buffer."""
        try:
            with open(filename, encoding="utf-8") as f:
                content = f.read()
                self.buffer = TextBuffer(content)
        except FileNotFoundError:
            # New file - start with empty buffer
            self.buffer = TextBuffer()
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)

    def _save_file(self) -> bool:
        """Save buffer content to file."""
        if not self.filename:
            self.renderer.show_message("No filename")
            return False

        try:
            content = self.buffer.get_content()
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(content)

            lines = len(self.buffer.get_lines())
            chars = len(content)
            self.renderer.show_message(f'"{self.filename}" {lines}L, {chars}C written')
            return True
        except Exception as e:
            self.renderer.show_message(f"Error saving: {e}")
            return False

    def run(self) -> None:
        """Main editor loop."""
        self.running = True

        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            # Set terminal to raw mode
            tty.setraw(sys.stdin)

            # Initial render
            self.renderer.render(self.buffer, self.modes)

            # Main loop
            while self.running:
                # Read keyboard input
                char = sys.stdin.read(1)

                # Handle input based on current mode
                self._handle_input(char)

                # Render updated state
                if self.running:
                    self.renderer.render(self.buffer, self.modes)

        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            # Clear screen on exit
            print("\033[2J\033[H", end="")

    def _handle_input(self, char: str) -> None:
        """Handle keyboard input based on current mode."""
        mode = self.modes.get_mode()

        if mode == ModeManager.NORMAL:
            self._handle_normal_mode(char)
        elif mode == ModeManager.INSERT:
            self._handle_insert_mode(char)
        elif mode == ModeManager.VISUAL:
            self._handle_visual_mode(char)
        elif mode == ModeManager.COMMAND:
            self._handle_command_mode(char)

    def _handle_normal_mode(self, char: str) -> None:
        """Handle input in normal mode."""
        # Delegate to CommandExecutor for normal mode commands
        handled = self.executor.execute_normal_command(char)

        # Handle commands not in executor
        if not handled:
            # Command mode
            if char == ":":
                self.modes.to_command()
                self.renderer.update_command_line("")
            # Quit
            elif char == "q":
                self.running = False
            # Escape key - clear any pending state
            elif char == "\x1b":
                self.executor._last_command = ""
                self.executor._repeat_count = ""

    def _handle_insert_mode(self, char: str) -> None:
        """Handle input in insert mode."""
        # Delegate to CommandExecutor for insert mode commands
        self.executor.execute_insert_command(char)

    def _handle_visual_mode(self, char: str) -> None:
        """Handle input in visual mode."""
        # Delegate to CommandExecutor for visual mode commands
        self.executor.execute_visual_command(char)

    def _handle_command_mode(self, char: str) -> None:
        """Handle input in command mode."""
        if char == "\x1b":  # Escape
            self._command_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
        elif char == "\r" or char == "\n":  # Enter - execute command
            self._execute_command(self._command_buffer)
            self._command_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
        elif char == "\x7f" or char == "\b":  # Backspace
            if self._command_buffer:
                self._command_buffer = self._command_buffer[:-1]
                self.renderer.update_command_line(self._command_buffer)
        elif ord(char) >= 32:  # Printable characters
            self._command_buffer += char
            self.renderer.update_command_line(self._command_buffer)

    def _execute_command(self, command: str) -> None:
        """Execute a command line command."""
        if command == "q" or command == "q!":
            self.running = False
        elif command == "w":
            self._save_file()
        elif command == "wq":
            if self._save_file():
                self.running = False
        elif command.startswith("w "):
            self.filename = command[2:].strip()
            self._save_file()
        elif command.startswith("e "):
            filename = command[2:].strip()
            self._load_file(filename)
            self.filename = filename
        elif self._is_substitute_command(command):
            self._execute_substitute(command)
        else:
            self.renderer.show_message(f"Unknown command: {command}")

    def _is_substitute_command(self, command: str) -> bool:
        """Check if command is a substitute command."""
        # Match patterns like: s/pattern/replacement/, 1,5s/.../, %s/.../
        patterns = [
            r"^\d*,?\d*s/",  # Range followed by s/
            r"^%s/",  # %s/ for all lines
            r"^s/",  # Simple s/
        ]
        return any(re.match(pattern, command) for pattern in patterns)

    def _execute_substitute(self, command: str) -> None:
        """Execute a substitute command.

        Supported formats:
        - :s/pattern/replacement/ - substitute on current line
        - :s/pattern/replacement/g - global substitute on current line
        - :s/pattern/replacement/i - case-insensitive
        - :s/pattern/replacement/gi - global and case-insensitive
        - :1,5s/pattern/replacement/ - substitute on lines 1-5
        - :%s/pattern/replacement/ - substitute on all lines
        """
        # Parse the command to extract range, pattern, replacement, and flags
        match = re.match(r"^(?:(\d+),(\d+)|(%))?\s*s/((?:[^/\\]|\\.)*)/((?:[^/\\]|\\.)*)/?([gi]*)$", command)

        if not match:
            self.renderer.show_message("Invalid substitute syntax")
            return

        start_line_str, end_line_str, percent, pattern, replacement, flags = match.groups()

        # Determine the range
        if percent:
            # % means all lines
            start_row = 0
            end_row = len(self.buffer.get_lines()) - 1
        elif start_line_str and end_line_str:
            # Explicit range (1-indexed in vi)
            start_row = int(start_line_str) - 1
            end_row = int(end_line_str) - 1
        else:
            # No range means current line only
            start_row, _ = self.buffer.get_cursor()
            end_row = start_row

        # Validate range
        max_row = len(self.buffer.get_lines()) - 1
        start_row = max(0, min(start_row, max_row))
        end_row = max(0, min(end_row, max_row))

        if start_row > end_row:
            start_row, end_row = end_row, start_row

        # Unescape the pattern and replacement
        pattern = pattern.replace(r"\/", "/")
        replacement = replacement.replace(r"\/", "/")

        # Perform substitution
        try:
            count = self.buffer.substitute_range(start_row, end_row, pattern, replacement, flags)

            # Show feedback message
            if count == 0:
                self.renderer.show_message("Pattern not found")
            elif count == 1:
                self.renderer.show_message("1 substitution on 1 line")
            else:
                lines_affected = end_row - start_row + 1
                if lines_affected == 1:
                    self.renderer.show_message(f"{count} substitutions on 1 line")
                else:
                    self.renderer.show_message(f"{count} substitutions on {lines_affected} lines")
        except Exception as e:
            self.renderer.show_message(f"Substitution error: {str(e)}")


def main():
    """Main entry point for vi editor."""
    import argparse

    parser = argparse.ArgumentParser(description="Vi-like text editor")
    parser.add_argument("filename", nargs="?", help="File to edit")
    args = parser.parse_args()

    editor = Vi(args.filename)
    editor.run()


if __name__ == "__main__":
    main()
