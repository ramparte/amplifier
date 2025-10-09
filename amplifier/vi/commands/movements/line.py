"""Line positioning commands (0, ^, $, g_, _) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class LineMovements:
    """Implements line positioning commands."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize with buffer reference."""
        self.buffer = buffer

    def to_line_start(self) -> bool:
        """Move to start of line (0 command).

        Returns:
            True if movement executed
        """
        self.buffer.move_to_line_start()
        return True

    def to_first_non_blank(self) -> bool:
        """Move to first non-blank character (^ command).

        Returns:
            True if movement executed
        """
        self.buffer.move_to_first_non_blank()
        return True

    def to_line_end(self) -> bool:
        """Move to end of line ($ command).

        Returns:
            True if movement executed
        """
        self.buffer.move_to_line_end()
        return True

    def to_last_non_blank(self) -> bool:
        """Move to last non-blank character (g_ command).

        Returns:
            True if movement executed
        """
        row = self.buffer._cursor_row
        if row < len(self.buffer.lines):
            line = self.buffer.lines[row]
            col = len(line) - 1
            # Find last non-blank
            while col >= 0 and line[col].isspace():
                col -= 1
            # Position cursor
            self.buffer.set_cursor(row, max(0, col))
        return True

    def to_first_non_blank_same_indent(self) -> bool:
        """Move to first non-blank at same indent level (_ command).

        Returns:
            True if movement executed
        """
        # For now, just move to first non-blank (can be enhanced later)
        self.buffer.move_to_first_non_blank()
        return True
