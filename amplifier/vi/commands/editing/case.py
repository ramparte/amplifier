"""Case conversion commands (~, gu, gU, g~) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class CaseCommand:
    """Implementation of case conversion commands."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize the case command handler.

        Args:
            buffer: Text buffer to operate on
        """
        self.buffer = buffer

    def toggle_case_char(self, count: int = 1) -> bool:
        """Toggle case of character(s) under cursor (~).

        Args:
            count: Number of characters to toggle

        Returns:
            True if successful, False otherwise
        """
        row, col = self.buffer.get_cursor()

        if row >= len(self.buffer.lines):
            return False

        # Save state for undo
        self.buffer.save_state()

        line = self.buffer.lines[row]
        chars_toggled = 0

        # Toggle characters starting from cursor position
        new_chars = []
        for i in range(col, min(col + count, len(line))):
            char = line[i]
            if char.isupper():
                new_chars.append(char.lower())
            elif char.islower():
                new_chars.append(char.upper())
            else:
                new_chars.append(char)
            chars_toggled += 1

        # Replace the characters in the line
        if new_chars:
            self.buffer.lines[row] = line[:col] + "".join(new_chars) + line[col + chars_toggled :]

            # Move cursor to the right by the number of characters toggled
            # (standard vi behavior for ~)
            new_col = min(col + chars_toggled, len(self.buffer.lines[row]))
            self.buffer.set_cursor(row, new_col)

        return True

    def convert_case_range(self, start_row: int, start_col: int, end_row: int, end_col: int, operation: str) -> bool:
        """Convert case in a range.

        Args:
            start_row: Starting row
            start_col: Starting column
            end_row: Ending row
            end_col: Ending column
            operation: 'lower', 'upper', or 'toggle'

        Returns:
            True if successful, False otherwise
        """
        # Normalize range
        if start_row > end_row or (start_row == end_row and start_col > end_col):
            start_row, start_col, end_row, end_col = end_row, end_col, start_row, start_col

        # Save state for undo
        self.buffer.save_state()

        # Process each line in range
        for row in range(start_row, min(end_row + 1, len(self.buffer.lines))):
            line = self.buffer.lines[row]

            # Determine column range for this line
            if row == start_row and row == end_row:
                # Single line range
                col_start = start_col
                col_end = end_col
            elif row == start_row:
                # First line of multi-line range
                col_start = start_col
                col_end = len(line)
            elif row == end_row:
                # Last line of multi-line range
                col_start = 0
                col_end = end_col
            else:
                # Middle line - process entire line
                col_start = 0
                col_end = len(line)

            # Convert case for the range
            if col_start < len(line):
                prefix = line[:col_start]
                middle = line[col_start : min(col_end, len(line))]
                suffix = line[min(col_end, len(line)) :]

                if operation == "lower":
                    middle = middle.lower()
                elif operation == "upper":
                    middle = middle.upper()
                elif operation == "toggle":
                    middle = "".join(c.lower() if c.isupper() else c.upper() if c.islower() else c for c in middle)

                self.buffer.lines[row] = prefix + middle + suffix

        return True

    def convert_case_motion(self, operation: str, motion_start: tuple[int, int], motion_end: tuple[int, int]) -> bool:
        """Convert case for a motion range.

        Args:
            operation: 'lower', 'upper', or 'toggle'
            motion_start: Starting position (row, col)
            motion_end: Ending position (row, col)

        Returns:
            True if successful, False otherwise
        """
        start_row, start_col = motion_start
        end_row, end_col = motion_end

        return self.convert_case_range(start_row, start_col, end_row, end_col, operation)

    def convert_case_line(self, row: int, operation: str) -> bool:
        """Convert case for an entire line.

        Args:
            row: Line number to convert
            operation: 'lower', 'upper', or 'toggle'

        Returns:
            True if successful, False otherwise
        """
        if row >= len(self.buffer.lines):
            return False

        line_len = len(self.buffer.lines[row])
        return self.convert_case_range(row, 0, row, line_len, operation)

    def convert_case_lines(self, start_row: int, count: int, operation: str) -> bool:
        """Convert case for multiple lines.

        Args:
            start_row: First line to convert
            count: Number of lines to convert
            operation: 'lower', 'upper', or 'toggle'

        Returns:
            True if successful, False otherwise
        """
        end_row = min(start_row + count - 1, len(self.buffer.lines) - 1)

        # Save state for undo
        self.buffer.save_state()

        for row in range(start_row, end_row + 1):
            self.convert_case_line(row, operation)

        return True

    def convert_case_visual(self, visual_start: tuple[int, int], visual_end: tuple[int, int], operation: str) -> bool:
        """Convert case in visual selection.

        Args:
            visual_start: Start of visual selection (row, col)
            visual_end: End of visual selection (row, col)
            operation: 'lower', 'upper', or 'toggle'

        Returns:
            True if successful, False otherwise
        """
        return self.convert_case_range(visual_start[0], visual_start[1], visual_end[0], visual_end[1], operation)
