"""Enhanced selection management for visual modes in vi editor."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer import TextBuffer


class SelectionMode(Enum):
    """Visual selection modes."""

    CHARACTER = "character"  # v - character-wise selection
    LINE = "line"  # V - line-wise selection
    BLOCK = "block"  # Ctrl+v - block-wise selection


@dataclass
class SelectionRange:
    """Represents a selection range with start and end positions."""

    start_row: int
    start_col: int
    end_row: int
    end_col: int
    mode: SelectionMode

    def normalize(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Get normalized (top-left, bottom-right) positions.

        Returns:
            Tuple of (start, end) where start <= end
        """
        if self.start_row < self.end_row or (self.start_row == self.end_row and self.start_col <= self.end_col):
            return (self.start_row, self.start_col), (self.end_row, self.end_col)
        return (self.end_row, self.end_col), (self.start_row, self.start_col)

    def contains(self, row: int, col: int) -> bool:
        """Check if a position is within this selection.

        Args:
            row: Row position to check
            col: Column position to check

        Returns:
            True if position is within selection
        """
        (start_row, start_col), (end_row, end_col) = self.normalize()

        if self.mode == SelectionMode.LINE:
            return start_row <= row <= end_row

        if self.mode == SelectionMode.BLOCK:
            min_col = min(self.start_col, self.end_col)
            max_col = max(self.start_col, self.end_col)
            return start_row <= row <= end_row and min_col <= col <= max_col

        # Character mode
        if row < start_row or row > end_row:
            return False
        if row == start_row and row == end_row:
            return start_col <= col <= end_col
        if row == start_row:
            return col >= start_col
        if row == end_row:
            return col <= end_col
        return True


class EnhancedSelectionManager:
    """Enhanced selection manager with support for all visual modes."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize the selection manager.

        Args:
            buffer: The text buffer to work with
        """
        self.buffer = buffer
        self.anchor: tuple[int, int] | None = None
        self.cursor: tuple[int, int] | None = None
        self.mode: SelectionMode | None = None
        self.previous_selection: SelectionRange | None = None
        self._selection_active = False

    def start_selection(self, mode: SelectionMode) -> None:
        """Start a new selection in the specified mode.

        Args:
            mode: The selection mode to use
        """
        pos = self.buffer.get_cursor_position()
        self.anchor = pos
        self.cursor = pos
        self.mode = mode
        self._selection_active = True

    def update_cursor(self, row: int, col: int) -> None:
        """Update the cursor position and extend selection.

        Args:
            row: New cursor row
            col: New cursor column
        """
        if self._selection_active:
            self.cursor = (row, col)

    def end_selection(self) -> SelectionRange | None:
        """End the current selection and return the range.

        Returns:
            The selection range or None if no selection
        """
        if not self._selection_active or not self.anchor or not self.cursor:
            return None

        selection = self.get_current_selection()
        self.previous_selection = selection
        self.clear()
        return selection

    def clear(self) -> None:
        """Clear the current selection."""
        self.anchor = None
        self.cursor = None
        self.mode = None
        self._selection_active = False

    def is_active(self) -> bool:
        """Check if a selection is currently active.

        Returns:
            True if selection is active
        """
        return self._selection_active

    def get_current_selection(self) -> SelectionRange | None:
        """Get the current selection range.

        Returns:
            The current selection range or None
        """
        if not self._selection_active or not self.anchor or not self.cursor or not self.mode:
            return None

        return SelectionRange(
            start_row=self.anchor[0],
            start_col=self.anchor[1],
            end_row=self.cursor[0],
            end_col=self.cursor[1],
            mode=self.mode,
        )

    def get_selected_text(self) -> str:
        """Get the text within the current selection.

        Returns:
            The selected text or empty string
        """
        selection = self.get_current_selection()
        if not selection:
            return ""

        lines = self.buffer.get_lines()
        (start_row, start_col), (end_row, end_col) = selection.normalize()

        if selection.mode == SelectionMode.LINE:
            # Line mode: complete lines
            selected_lines = lines[start_row : end_row + 1]
            return "\n".join(selected_lines)

        if selection.mode == SelectionMode.BLOCK:
            # Block mode: rectangular selection
            result = []
            min_col = min(selection.start_col, selection.end_col)
            max_col = max(selection.start_col, selection.end_col)

            for row in range(start_row, min(end_row + 1, len(lines))):
                if row < len(lines):
                    line = lines[row]
                    if min_col < len(line):
                        result.append(line[min_col : min(max_col + 1, len(line))])
                    else:
                        result.append("")
            return "\n".join(result)

        # Character mode
        if start_row == end_row:
            # Single line
            if start_row < len(lines):
                return lines[start_row][start_col : end_col + 1]
            return ""

        # Multi-line character selection
        result = []
        for row in range(start_row, min(end_row + 1, len(lines))):
            if row < len(lines):
                line = lines[row]
                if row == start_row:
                    result.append(line[start_col:])
                elif row == end_row:
                    result.append(line[: end_col + 1])
                else:
                    result.append(line)
        return "\n".join(result)

    def get_selected_lines(self) -> list[int]:
        """Get list of line indices that are selected.

        Returns:
            List of selected line indices
        """
        selection = self.get_current_selection()
        if not selection:
            return []

        (start_row, _), (end_row, _) = selection.normalize()
        return list(range(start_row, end_row + 1))

    def swap_anchor_cursor(self) -> None:
        """Swap the anchor and cursor positions (visual mode 'o' command)."""
        if self._selection_active and self.anchor and self.cursor:
            self.anchor, self.cursor = self.cursor, self.anchor
            self.buffer.set_cursor_position(self.cursor[0], self.cursor[1])

    def extend_to_word_boundary(self, forward: bool = True) -> None:
        """Extend selection to next/previous word boundary.

        Args:
            forward: If True, extend forward; otherwise backward
        """
        if not self._selection_active or not self.cursor:
            return

        row, col = self.cursor
        lines = self.buffer.get_lines()
        if row >= len(lines):
            return

        line = lines[row]

        if forward:
            # Find next word boundary
            # Skip current word
            while col < len(line) and not line[col].isspace():
                col += 1
            # Skip whitespace
            while col < len(line) and line[col].isspace():
                col += 1
        else:
            # Find previous word boundary
            # Skip whitespace
            while col > 0 and line[col - 1].isspace():
                col -= 1
            # Skip to word start
            while col > 0 and not line[col - 1].isspace():
                col -= 1

        self.cursor = (row, col)
        self.buffer.set_cursor_position(row, col)

    def extend_to_line_boundary(self, end: bool = True) -> None:
        """Extend selection to start/end of line.

        Args:
            end: If True, extend to end; otherwise to start
        """
        if not self._selection_active or not self.cursor:
            return

        row, _ = self.cursor
        lines = self.buffer.get_lines()
        if row >= len(lines):
            return

        if end:
            col = len(lines[row]) - 1 if lines[row] else 0
        else:
            col = 0

        self.cursor = (row, col)
        self.buffer.set_cursor_position(row, col)

    def convert_mode(self, new_mode: SelectionMode) -> None:
        """Convert current selection to a different mode.

        Args:
            new_mode: The new selection mode
        """
        if self._selection_active:
            self.mode = new_mode

    def reselect_previous(self) -> bool:
        """Reselect the previous selection (gv command).

        Returns:
            True if previous selection was restored
        """
        if not self.previous_selection:
            return False

        self.anchor = (self.previous_selection.start_row, self.previous_selection.start_col)
        self.cursor = (self.previous_selection.end_row, self.previous_selection.end_col)
        self.mode = self.previous_selection.mode
        self._selection_active = True
        self.buffer.set_cursor_position(self.cursor[0], self.cursor[1])
        return True
