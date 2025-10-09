"""Replace mode implementation for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..buffer import TextBuffer as Buffer


class ReplaceMode:
    """Manages replace mode operations."""

    def __init__(self, buffer: "Buffer"):
        """Initialize replace mode manager.

        Args:
            buffer: The buffer to work with
        """
        self.buffer = buffer
        self.original_text: list[str] = []
        self.replace_start: tuple[int, int] | None = None
        self.single_char_mode = False

    def enter_replace(self, single_char: bool = False) -> None:
        """Enter replace mode.

        Args:
            single_char: If True, only replace a single character
        """
        self.single_char_mode = single_char
        self.replace_start = self.buffer.get_cursor_position()

        # Store original text for undo
        lines = self.buffer.get_lines()
        self.original_text = list(lines)

    def exit_replace(self) -> None:
        """Exit replace mode."""
        self.single_char_mode = False
        self.replace_start = None
        self.original_text = []

    def handle_character(self, char: str) -> bool:
        """Handle character input in replace mode.

        Args:
            char: The character to replace with

        Returns:
            True if should exit replace mode (for single char mode)
        """
        row, col = self.buffer.get_cursor_position()
        lines = self.buffer.get_lines()

        # Ensure row exists
        while row >= len(lines):
            lines.append("")

        line = lines[row]

        if char == "\n":
            if not self.single_char_mode and row < len(lines) - 1:
                # In replace mode, Enter moves to next line
                self.buffer.set_cursor_position(row + 1, 0)
            return self.single_char_mode

        if char == "\b" or char == "\x7f":  # Backspace
            if not self.single_char_mode and col > 0:
                # Move back and restore original character
                if self.replace_start and row < len(self.original_text):
                    orig_line = self.original_text[row]
                    if col - 1 < len(orig_line):
                        lines[row] = line[: col - 1] + orig_line[col - 1] + line[col:]
                        self.buffer.set_lines(lines)
                self.buffer.set_cursor_position(row, col - 1)
            return False

        # Replace character at cursor position
        if col < len(line):
            # Replace existing character
            lines[row] = line[:col] + char + line[col + 1 :]
        else:
            # Append at end of line
            lines[row] = line + char

        self.buffer.set_lines(lines)

        # Move cursor forward
        if not self.single_char_mode:
            self.buffer.set_cursor_position(row, col + 1)

        # Exit if single character mode
        return self.single_char_mode

    def handle_arrow_key(self, direction: str) -> None:
        """Handle arrow keys in replace mode.

        Args:
            direction: One of 'up', 'down', 'left', 'right'
        """
        if self.single_char_mode:
            return  # No movement in single char replace

        row, col = self.buffer.get_cursor_position()
        lines = self.buffer.get_lines()

        if direction == "up" and row > 0:
            new_row = row - 1
            new_col = min(col, len(lines[new_row]))
            self.buffer.set_cursor_position(new_row, new_col)
        elif direction == "down" and row < len(lines) - 1:
            new_row = row + 1
            new_col = min(col, len(lines[new_row]))
            self.buffer.set_cursor_position(new_row, new_col)
        elif direction == "left" and col > 0:
            self.buffer.set_cursor_position(row, col - 1)
        elif direction == "right":
            max_col = len(lines[row]) if row < len(lines) else 0
            if col < max_col:
                self.buffer.set_cursor_position(row, col + 1)

    def get_original_text(self) -> list[str]:
        """Get the original text before replace mode.

        Returns:
            The original lines
        """
        return self.original_text.copy()

    def is_single_char(self) -> bool:
        """Check if in single character replace mode.

        Returns:
            True if in single character mode
        """
        return self.single_char_mode
