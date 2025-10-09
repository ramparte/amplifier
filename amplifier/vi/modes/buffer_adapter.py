"""Buffer adapter for mode management modules."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..buffer import TextBuffer


class BufferAdapter:
    """Adapter to provide a consistent interface for mode modules."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize adapter with a TextBuffer.

        Args:
            buffer: The TextBuffer to adapt
        """
        self.buffer = buffer

    def get_cursor_position(self) -> tuple[int, int]:
        """Get current cursor position.

        Returns:
            Tuple of (row, col)
        """
        return self.buffer.get_cursor()

    def get_cursor(self) -> tuple[int, int]:
        """Get current cursor position (alias for compatibility).

        Returns:
            Tuple of (row, col)
        """
        return self.buffer.get_cursor()

    def set_cursor_position(self, row: int, col: int) -> None:
        """Set cursor position.

        Args:
            row: Row position
            col: Column position
        """
        self.buffer.set_cursor(row, col)

    def set_cursor(self, row: int, col: int) -> None:
        """Set cursor position (alias for compatibility).

        Args:
            row: Row position
            col: Column position
        """
        self.buffer.set_cursor(row, col)

    def get_lines(self) -> list[str]:
        """Get all lines in the buffer.

        Returns:
            List of lines
        """
        return self.buffer.get_lines()

    def set_lines(self, lines: list[str]) -> None:
        """Set all lines in the buffer.

        Args:
            lines: New lines to set
        """
        # Direct modification of internal lines
        self.buffer._lines = list(lines)
        # Ensure cursor is within bounds
        row, col = self.buffer.get_cursor()
        if row >= len(lines):
            row = max(0, len(lines) - 1)
        if row < len(lines) and col > len(lines[row]):
            col = len(lines[row])
        self.buffer.set_cursor(row, col)

    def get_content(self) -> str:
        """Get entire buffer content.

        Returns:
            Buffer content as string
        """
        return self.buffer.get_content()

    def insert_char(self, char: str) -> None:
        """Insert character at cursor.

        Args:
            char: Character to insert
        """
        self.buffer.insert_char(char)

    def delete_char(self) -> None:
        """Delete character at cursor."""
        self.buffer.delete_char()

    def delete_line(self) -> None:
        """Delete current line."""
        self.buffer.delete_line()
