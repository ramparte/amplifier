"""Bracket matching movement (%) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class BracketMovement:
    """Implementation of bracket matching movement."""

    # Default bracket pairs
    DEFAULT_PAIRS = {
        "(": ")",
        ")": "(",
        "[": "]",
        "]": "[",
        "{": "}",
        "}": "{",
        "<": ">",
        ">": "<",
    }

    def __init__(self, buffer: "TextBuffer", bracket_pairs: dict[str, str] | None = None):
        """Initialize the bracket movement handler.

        Args:
            buffer: Text buffer to operate on
            bracket_pairs: Optional custom bracket pairs mapping
        """
        self.buffer = buffer
        self.bracket_pairs = bracket_pairs if bracket_pairs is not None else self.DEFAULT_PAIRS

    def find_matching_bracket(self) -> bool:
        """Find and move to matching bracket (% command).

        Returns:
            True if matching bracket found and cursor moved, False otherwise
        """
        row, col = self.buffer.get_cursor()

        if row >= len(self.buffer.lines):
            return False

        line = self.buffer.lines[row]

        # Find the nearest bracket on current line at or after cursor
        start_char = None
        start_pos = None

        # First check character under cursor
        if col < len(line) and line[col] in self.bracket_pairs:
            start_char = line[col]
            start_pos = (row, col)
        else:
            # Search forward on current line for a bracket
            for i in range(col, len(line)):
                if line[i] in self.bracket_pairs:
                    start_char = line[i]
                    start_pos = (row, i)
                    break

        if not start_char or not start_pos:
            return False

        # Determine if we're looking for opening or closing bracket
        match_char = self.bracket_pairs[start_char]

        # Determine search direction based on bracket type
        # Opening brackets: (, [, {, <
        # Closing brackets: ), ], }, >
        is_opening = start_char in "([{<"

        if is_opening:
            # Search forward for closing bracket
            return self._search_forward(start_pos, start_char, match_char)
        # Search backward for opening bracket
        return self._search_backward(start_pos, start_char, match_char)

    def _search_forward(self, start_pos: tuple[int, int], open_char: str, close_char: str) -> bool:
        """Search forward for matching closing bracket.

        Args:
            start_pos: Starting position (row, col)
            open_char: Opening bracket character
            close_char: Closing bracket character to find

        Returns:
            True if found and cursor moved, False otherwise
        """
        start_row, start_col = start_pos
        nesting_level = 1

        # Start searching from position after the opening bracket
        row = start_row
        col = start_col + 1

        while row < len(self.buffer.lines):
            line = self.buffer.lines[row]

            # Search rest of current line
            while col < len(line):
                if line[col] == open_char:
                    nesting_level += 1
                elif line[col] == close_char:
                    nesting_level -= 1
                    if nesting_level == 0:
                        # Found matching bracket
                        self.buffer.set_cursor(row, col)
                        return True
                col += 1

            # Move to next line
            row += 1
            col = 0

        return False

    def _search_backward(self, start_pos: tuple[int, int], close_char: str, open_char: str) -> bool:
        """Search backward for matching opening bracket.

        Args:
            start_pos: Starting position (row, col)
            close_char: Closing bracket character
            open_char: Opening bracket character to find

        Returns:
            True if found and cursor moved, False otherwise
        """
        start_row, start_col = start_pos
        nesting_level = 1

        # Start searching from position before the closing bracket
        row = start_row
        col = start_col - 1

        while row >= 0:
            if col < 0:
                # Move to previous line
                row -= 1
                if row >= 0:
                    col = len(self.buffer.lines[row]) - 1
                continue

            line = self.buffer.lines[row]

            # Search backwards on current line
            while col >= 0:
                if col < len(line):
                    if line[col] == close_char:
                        nesting_level += 1
                    elif line[col] == open_char:
                        nesting_level -= 1
                        if nesting_level == 0:
                            # Found matching bracket
                            self.buffer.set_cursor(row, col)
                            return True
                col -= 1

            # Move to previous line
            row -= 1
            if row >= 0:
                col = len(self.buffer.lines[row]) - 1

        return False

    def get_bracket_range(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Get the range between matching brackets (inclusive).

        This is useful for operators that work with the % motion.

        Returns:
            Tuple of (start_pos, end_pos) or None if no matching bracket
        """
        start_pos = self.buffer.get_cursor()

        # Find matching bracket
        if self.find_matching_bracket():
            end_pos = self.buffer.get_cursor()

            # Restore original position
            self.buffer.set_cursor(start_pos[0], start_pos[1])

            # Normalize so start is before end
            if start_pos[0] > end_pos[0] or (start_pos[0] == end_pos[0] and start_pos[1] > end_pos[1]):
                return (end_pos, start_pos)
            return (start_pos, end_pos)

        return None

    def set_bracket_pairs(self, pairs: dict[str, str]) -> None:
        """Update the bracket pairs mapping.

        Args:
            pairs: New bracket pairs mapping
        """
        self.bracket_pairs = pairs

    def add_bracket_pair(self, open_char: str, close_char: str) -> None:
        """Add a new bracket pair.

        Args:
            open_char: Opening bracket character
            close_char: Closing bracket character
        """
        self.bracket_pairs[open_char] = close_char
        self.bracket_pairs[close_char] = open_char
