"""Screen-relative movement commands (H, M, L) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class ScreenMovements:
    """Implements screen-relative movement commands."""

    def __init__(self, buffer: "TextBuffer", viewport_start: int = 0, viewport_height: int = 24):
        """Initialize with buffer reference and viewport info.

        Args:
            buffer: Text buffer reference
            viewport_start: First visible line number
            viewport_height: Number of visible lines
        """
        self.buffer = buffer
        self.viewport_start = viewport_start
        self.viewport_height = viewport_height

    def update_viewport(self, viewport_start: int, viewport_height: int) -> None:
        """Update viewport information.

        Args:
            viewport_start: First visible line number
            viewport_height: Number of visible lines
        """
        self.viewport_start = viewport_start
        self.viewport_height = viewport_height

    def to_screen_top(self, offset: int = 0) -> bool:
        """Move to top of screen (H command).

        Args:
            offset: Lines from top (default 0)

        Returns:
            True if movement executed
        """
        self.buffer.move_to_screen_top(self.viewport_start, self.viewport_height, offset)
        return True

    def to_screen_middle(self) -> bool:
        """Move to middle of screen (M command).

        Returns:
            True if movement executed
        """
        self.buffer.move_to_screen_middle(self.viewport_start, self.viewport_height)
        return True

    def to_screen_bottom(self, offset: int = 0) -> bool:
        """Move to bottom of screen (L command).

        Args:
            offset: Lines from bottom (default 0)

        Returns:
            True if movement executed
        """
        self.buffer.move_to_screen_bottom(self.viewport_start, self.viewport_height, offset)
        return True
