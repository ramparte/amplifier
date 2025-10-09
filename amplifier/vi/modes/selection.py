"""Selection management for visual modes in vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..buffer import TextBuffer as Buffer


class SelectionManager:
    """Manages selections for visual modes."""

    def __init__(self, buffer: "Buffer"):
        """Initialize selection manager.

        Args:
            buffer: The buffer to work with
        """
        self.buffer = buffer
        self.anchor: tuple[int, int] | None = None
        self.cursor: tuple[int, int] | None = None
        self.mode: str = "character"  # character, line, or block

    def start_selection(self, mode: str = "character") -> None:
        """Start a new selection.

        Args:
            mode: Selection mode ('character', 'line', 'block')
        """
        self.mode = mode
        pos = self.buffer.get_cursor_position()
        self.anchor = pos
        self.cursor = pos

    def update_selection(self) -> None:
        """Update selection with current cursor position."""
        if self.anchor is not None:
            self.cursor = self.buffer.get_cursor_position()

    def clear_selection(self) -> None:
        """Clear the current selection."""
        self.anchor = None
        self.cursor = None
        self.mode = "character"

    def get_selection_bounds(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Get normalized selection bounds.

        Returns:
            Tuple of (start, end) positions or None if no selection
        """
        if self.anchor is None or self.cursor is None:
            return None

        anchor_row, anchor_col = self.anchor
        cursor_row, cursor_col = self.cursor

        # Normalize based on mode
        if self.mode == "line":
            # Line mode: select complete lines
            start_row = min(anchor_row, cursor_row)
            end_row = max(anchor_row, cursor_row)
            lines = self.buffer.get_lines()
            end_col = len(lines[end_row]) - 1 if end_row < len(lines) else 0
            return (start_row, 0), (end_row, end_col)

        if self.mode == "block":
            # Block mode: rectangular selection
            start_row = min(anchor_row, cursor_row)
            end_row = max(anchor_row, cursor_row)
            start_col = min(anchor_col, cursor_col)
            end_col = max(anchor_col, cursor_col)
            return (start_row, start_col), (end_row, end_col)

        # character mode
        # Character mode: normal selection
        if anchor_row < cursor_row or (anchor_row == cursor_row and anchor_col <= cursor_col):
            return self.anchor, self.cursor
        return self.cursor, self.anchor

    def is_position_selected(self, row: int, col: int) -> bool:
        """Check if a position is within the selection.

        Args:
            row: Row position
            col: Column position

        Returns:
            True if position is selected
        """
        bounds = self.get_selection_bounds()
        if not bounds:
            return False

        (start_row, start_col), (end_row, end_col) = bounds

        if self.mode == "line":
            return start_row <= row <= end_row

        if self.mode == "block":
            return start_row <= row <= end_row and start_col <= col <= end_col

        # character mode
        if row < start_row or row > end_row:
            return False
        if row == start_row and row == end_row:
            return start_col <= col <= end_col
        if row == start_row:
            return col >= start_col
        if row == end_row:
            return col <= end_col
        return True

    def get_selected_lines(self) -> list[int]:
        """Get list of selected line numbers.

        Returns:
            List of line numbers that are selected
        """
        bounds = self.get_selection_bounds()
        if not bounds:
            return []

        (start_row, _), (end_row, _) = bounds
        return list(range(start_row, end_row + 1))

    def get_selected_text(self) -> str:
        """Get the selected text.

        Returns:
            The selected text as a string
        """
        bounds = self.get_selection_bounds()
        if not bounds:
            return ""

        (start_row, start_col), (end_row, end_col) = bounds
        lines = self.buffer.get_lines()

        if self.mode == "line":
            # Select complete lines
            selected_lines = lines[start_row : end_row + 1]
            return "\n".join(selected_lines)

        if self.mode == "block":
            # Select rectangular block
            selected_lines = []
            for row in range(start_row, min(end_row + 1, len(lines))):
                if row < len(lines):
                    line = lines[row]
                    # Handle lines shorter than the selection
                    if start_col < len(line):
                        selected_lines.append(line[start_col : min(end_col + 1, len(line))])
                    else:
                        selected_lines.append("")
            return "\n".join(selected_lines)

        # character mode
        if start_row == end_row:
            # Single line selection
            if start_row < len(lines):
                return lines[start_row][start_col : end_col + 1]
            return ""
        # Multi-line selection
        selected = []
        for row in range(start_row, min(end_row + 1, len(lines))):
            if row < len(lines):
                line = lines[row]
                if row == start_row:
                    selected.append(line[start_col:])
                elif row == end_row:
                    selected.append(line[: end_col + 1])
                else:
                    selected.append(line)
        return "\n".join(selected)

    def extend_selection_word(self, forward: bool = True) -> None:
        """Extend selection by word boundary.

        Args:
            forward: If True, extend forward; otherwise backward
        """
        if self.cursor is None:
            return

        row, col = self.cursor
        lines = self.buffer.get_lines()
        if row >= len(lines):
            return

        line = lines[row]

        if forward:
            # Find next word boundary
            while col < len(line) and not line[col].isspace():
                col += 1
            while col < len(line) and line[col].isspace():
                col += 1
        else:
            # Find previous word boundary
            while col > 0 and line[col - 1].isspace():
                col -= 1
            while col > 0 and not line[col - 1].isspace():
                col -= 1

        self.cursor = (row, col)
        self.buffer.set_cursor_position(row, col)

    def extend_selection_line(self, down: bool = True) -> None:
        """Extend selection by line.

        Args:
            down: If True, extend down; otherwise up
        """
        if self.cursor is None:
            return

        row, col = self.cursor
        lines = self.buffer.get_lines()

        if down and row < len(lines) - 1:
            row += 1
        elif not down and row > 0:
            row -= 1

        # Adjust column to stay within line bounds
        if row < len(lines):
            col = min(col, len(lines[row]) - 1)

        self.cursor = (row, col)
        self.buffer.set_cursor_position(row, col)

    def swap_anchor_cursor(self) -> None:
        """Swap anchor and cursor positions."""
        if self.anchor is not None and self.cursor is not None:
            self.anchor, self.cursor = self.cursor, self.anchor
            self.buffer.set_cursor_position(self.cursor[0], self.cursor[1])
