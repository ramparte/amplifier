"""Basic movement commands (h, j, k, l) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class BasicMovements:
    """Implements basic hjkl movement commands."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize with buffer reference."""
        self.buffer = buffer

    def move_left(self, count: int = 1) -> bool:
        """Move cursor left (h command).

        Args:
            count: Number of positions to move

        Returns:
            True if movement executed
        """
        self.buffer.move_left(count)
        return True

    def move_down(self, count: int = 1) -> bool:
        """Move cursor down (j command).

        Args:
            count: Number of lines to move

        Returns:
            True if movement executed
        """
        self.buffer.move_down(count)
        return True

    def move_up(self, count: int = 1) -> bool:
        """Move cursor up (k command).

        Args:
            count: Number of lines to move

        Returns:
            True if movement executed
        """
        self.buffer.move_up(count)
        return True

    def move_right(self, count: int = 1) -> bool:
        """Move cursor right (l command).

        Args:
            count: Number of positions to move

        Returns:
            True if movement executed
        """
        self.buffer.move_right(count)
        return True
