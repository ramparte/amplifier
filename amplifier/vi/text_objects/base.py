"""Base text object class for vi editor."""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class TextObjectRange:
    """Represents a text object selection range."""

    start_line: int
    start_col: int
    end_line: int
    end_col: int
    inclusive: bool = True  # Whether end position is inclusive

    def is_empty(self) -> bool:
        """Check if the range is empty."""
        return self.start_line == self.end_line and self.start_col == self.end_col


class TextBufferProtocol(Protocol):
    """Protocol for text buffer interface."""

    def get_line(self, line_num: int) -> str:
        """Get a line by number."""
        ...

    def line_count(self) -> int:
        """Get total number of lines."""
        ...

    def get_char_at(self, line: int, col: int) -> str | None:
        """Get character at position."""
        ...


class TextObject:
    """Base class for all text objects."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize text object with buffer."""
        self.buffer = buffer

    def find_object_at(self, line: int, col: int, include_surrounding: bool = False) -> TextObjectRange | None:
        """
        Find text object at given position.

        Args:
            line: Current line number (0-based)
            col: Current column number (0-based)
            include_surrounding: If True, include surrounding delimiters/whitespace ("a" mode)
                                 If False, only inner content ("i" mode)

        Returns:
            TextObjectRange if found, None otherwise
        """
        raise NotImplementedError("Subclasses must implement find_object_at")

    def _is_valid_position(self, line: int, col: int) -> bool:
        """Check if position is valid in buffer."""
        if line < 0 or line >= self.buffer.line_count():
            return False
        line_text = self.buffer.get_line(line)
        return 0 <= col < len(line_text)

    def _find_matching_delimiter(
        self, line: int, col: int, open_delim: str, close_delim: str, search_backward: bool = False
    ) -> tuple[int, int] | None:
        """
        Find matching delimiter from current position.

        Args:
            line: Starting line
            col: Starting column
            open_delim: Opening delimiter character
            close_delim: Closing delimiter character
            search_backward: If True, search backward for opening delimiter

        Returns:
            (line, col) of matching delimiter or None
        """
        depth = 1 if not search_backward else 0

        # Determine search direction and delimiters to track
        if search_backward:
            # Searching backward for opening delimiter
            inc_delim = close_delim
            dec_delim = open_delim
        else:
            # Searching forward for closing delimiter
            inc_delim = open_delim
            dec_delim = close_delim

        # Search through buffer
        current_line = line
        current_col = col

        while 0 <= current_line < self.buffer.line_count():
            line_text = self.buffer.get_line(current_line)

            # Set column range for this line
            if search_backward:
                start_col = current_col if current_line == line else len(line_text) - 1
                end_col = -1
                step = -1
            else:
                start_col = current_col if current_line == line else 0
                end_col = len(line_text)
                step = 1

            # Search within line
            for c in range(start_col, end_col, step):
                if c < 0 or c >= len(line_text):
                    continue

                char = line_text[c]

                # Skip the starting position
                if current_line == line and c == col:
                    continue

                # Update depth based on delimiters
                if char == inc_delim:
                    depth += 1
                elif char == dec_delim:
                    depth -= 1

                    # Found matching delimiter
                    if depth == 0:
                        return (current_line, c)

            # Move to next/previous line
            current_line += -1 if search_backward else 1

        return None

    def _expand_to_whitespace(
        self, start_line: int, start_col: int, end_line: int, end_col: int, before: bool = True, after: bool = True
    ) -> tuple[int, int, int, int]:
        """
        Expand range to include surrounding whitespace.

        Args:
            start_line: Starting line
            start_col: Starting column
            end_line: Ending line
            end_col: Ending column
            before: Include whitespace before
            after: Include whitespace after

        Returns:
            (start_line, start_col, end_line, end_col) with whitespace
        """
        # Expand before
        if before and start_col > 0:
            line_text = self.buffer.get_line(start_line)
            while start_col > 0 and line_text[start_col - 1].isspace():
                start_col -= 1

        # Expand after
        if after:
            line_text = self.buffer.get_line(end_line)
            while end_col < len(line_text) - 1 and line_text[end_col + 1].isspace():
                end_col += 1

        return start_line, start_col, end_line, end_col
