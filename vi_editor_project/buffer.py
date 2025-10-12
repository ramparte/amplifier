#!/usr/bin/env python3
"""
Buffer management module for vi editor.

Handles text storage, cursor position, and basic text operations.
"""


class Buffer:
    """
    Line-based text buffer with cursor tracking.

    The buffer stores text as a list of strings (one per line).
    Cursor position is tracked as (row, col) with 0-based indexing.
    """

    def __init__(self, lines: list[str] | None = None):
        """
        Initialize buffer with optional initial content.

        Args:
            lines: Initial lines of text (without newline characters)
        """
        self._lines = lines.copy() if lines else [""]
        self._cursor_row = 0
        self._cursor_col = 0

    @property
    def cursor(self) -> tuple[int, int]:
        """Get current cursor position as (row, col)."""
        return (self._cursor_row, self._cursor_col)

    def move_cursor(self, row: int, col: int) -> None:
        """
        Move cursor to specified position.

        Position is constrained to valid bounds.

        Args:
            row: Target row (0-based)
            col: Target column (0-based)
        """
        # Constrain row to valid range
        row = max(0, min(row, len(self._lines) - 1))

        # Constrain column to valid range for the row
        line_length = len(self._lines[row]) if self._lines else 0
        col = max(0, min(col, line_length))

        self._cursor_row = row
        self._cursor_col = col

    def move_cursor_relative(self, rows: int = 0, cols: int = 0) -> None:
        """
        Move cursor relative to current position.

        Args:
            rows: Number of rows to move (positive = down, negative = up)
            cols: Number of columns to move (positive = right, negative = left)
        """
        new_row = self._cursor_row + rows
        new_col = self._cursor_col + cols
        self.move_cursor(new_row, new_col)

    def get_line(self, row: int) -> str:
        """
        Get text of specified line.

        Args:
            row: Line number (0-based)

        Returns:
            Line text or empty string if row is out of bounds
        """
        if 0 <= row < len(self._lines):
            return self._lines[row]
        return ""

    def insert_line(self, row: int, text: str) -> None:
        """
        Insert a new line at specified position.

        Args:
            row: Position to insert at (0-based)
            text: Text of the new line
        """
        # Ensure row is within valid range for insertion
        row = max(0, min(row, len(self._lines)))
        self._lines.insert(row, text)

    def delete_line(self, row: int) -> None:
        """
        Delete the line at specified position.

        Args:
            row: Line to delete (0-based)
        """
        if 0 <= row < len(self._lines):
            self._lines.pop(row)

        # Ensure at least one line exists
        if not self._lines:
            self._lines = [""]

        # Adjust cursor if necessary
        if self._cursor_row >= len(self._lines):
            self._cursor_row = len(self._lines) - 1

        # Adjust column for new current line
        line_length = len(self._lines[self._cursor_row])
        if self._cursor_col > line_length:
            self._cursor_col = line_length

    def modify_line(self, row: int, text: str) -> None:
        """
        Replace the text of a line.

        Args:
            row: Line to modify (0-based)
            text: New text for the line
        """
        if 0 <= row < len(self._lines):
            self._lines[row] = text

            # Adjust cursor column if on modified line
            if row == self._cursor_row:
                line_length = len(text)
                if self._cursor_col > line_length:
                    self._cursor_col = line_length

    def insert_char(self, row: int, col: int, char: str) -> None:
        """
        Insert a character at specified position.

        Args:
            row: Row position (0-based)
            col: Column position (0-based)
            char: Character to insert
        """
        if 0 <= row < len(self._lines):
            line = self._lines[row]
            # Ensure column is within valid range
            col = max(0, min(col, len(line)))
            self._lines[row] = line[:col] + char + line[col:]

    def delete_char(self, row: int, col: int) -> None:
        """
        Delete character at specified position.

        Args:
            row: Row position (0-based)
            col: Column position (0-based)
        """
        if 0 <= row < len(self._lines):
            line = self._lines[row]
            if 0 <= col < len(line):
                self._lines[row] = line[:col] + line[col + 1 :]

    def get_content(self) -> list[str]:
        """
        Get all buffer content as list of lines.

        Returns:
            Copy of all lines in the buffer
        """
        return self._lines.copy()

    def get_buffer_content(self) -> list[str]:
        """
        Alias for get_content() to match test framework expectations.

        Returns:
            Copy of all lines in the buffer
        """
        return self.get_content()

    def line_count(self) -> int:
        """
        Get number of lines in buffer.

        Returns:
            Total number of lines
        """
        return len(self._lines)

    def get_current_line(self) -> str:
        """Get text of line at cursor position."""
        return self.get_line(self._cursor_row)

    def get_line_length(self, row: int) -> int:
        """
        Get length of specified line.

        Args:
            row: Line number (0-based)

        Returns:
            Length of line or 0 if out of bounds
        """
        if 0 <= row < len(self._lines):
            return len(self._lines[row])
        return 0

    def is_empty(self) -> bool:
        """Check if buffer is empty (single empty line)."""
        return len(self._lines) == 1 and self._lines[0] == ""

    def move_to_line_start(self) -> None:
        """Move cursor to start of current line."""
        self._cursor_col = 0

    def move_to_line_end(self) -> None:
        """Move cursor to end of current line."""
        self._cursor_col = len(self.get_current_line())

    def move_to_first_line(self) -> None:
        """Move cursor to first line of buffer."""
        self._cursor_row = 0

    def move_to_last_line(self) -> None:
        """Move cursor to last line of buffer."""
        self._cursor_row = len(self._lines) - 1

    def insert_text_at_cursor(self, text: str) -> None:
        """
        Insert text at current cursor position.

        Args:
            text: Text to insert (may contain newlines)
        """
        lines = text.split("\n")

        if len(lines) == 1:
            # Single line insertion
            self.insert_char(self._cursor_row, self._cursor_col, text)
            self._cursor_col += len(text)
        else:
            # Multi-line insertion
            current_line = self.get_current_line()
            before = current_line[: self._cursor_col]
            after = current_line[self._cursor_col :]

            # Modify current line with first part
            self.modify_line(self._cursor_row, before + lines[0])

            # Insert middle lines
            for i, line in enumerate(lines[1:-1], start=1):
                self.insert_line(self._cursor_row + i, line)

            # Insert last line with remainder
            self.insert_line(self._cursor_row + len(lines) - 1, lines[-1] + after)

            # Update cursor position
            self._cursor_row += len(lines) - 1
            self._cursor_col = len(lines[-1])

    def delete_char_at_cursor(self) -> None:
        """Delete character at cursor position."""
        self.delete_char(self._cursor_row, self._cursor_col)

    def delete_line_at_cursor(self) -> None:
        """Delete line at cursor position."""
        self.delete_line(self._cursor_row)

    def snapshot(self) -> dict:
        """
        Create a snapshot of buffer state for undo/redo.

        Returns:
            Dictionary containing buffer state
        """
        return {"lines": self._lines.copy(), "cursor_row": self._cursor_row, "cursor_col": self._cursor_col}

    def restore(self, snapshot: dict) -> None:
        """
        Restore buffer from a snapshot.

        Args:
            snapshot: Dictionary containing buffer state
        """
        self._lines = snapshot["lines"].copy()
        self._cursor_row = snapshot["cursor_row"]
        self._cursor_col = snapshot["cursor_col"]
