"""Join lines commands (J, gJ) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class JoinCommand:
    """Implementation of line join commands."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize the join command handler.

        Args:
            buffer: Text buffer to operate on
        """
        self.buffer = buffer

    def join_lines(self, count: int = 1, add_space: bool = True) -> bool:
        """Join current line with next line(s).

        Args:
            count: Number of lines to join (default 1 means join with next line)
            add_space: If True, add space between joined lines (J command)
                      If False, don't add space (gJ command)

        Returns:
            True if join was successful, False otherwise
        """
        row, col = self.buffer.get_cursor()

        # Can't join if on last line
        if row >= len(self.buffer.lines) - 1:
            return False

        # Save state for undo
        self.buffer.save_state()

        # Calculate how many joins to perform
        # count of 2 means join current + next line (1 join)
        # count of 3 means join current + next 2 lines (2 joins), etc.
        joins_to_perform = max(1, count - 1) if count > 1 else 1

        # Perform the joins
        for _ in range(joins_to_perform):
            if row >= len(self.buffer.lines) - 1:
                break  # No more lines to join

            current_line = self.buffer.lines[row]
            next_line = self.buffer.lines[row + 1]

            # Trim trailing whitespace from current line
            current_line = current_line.rstrip()

            # Trim leading whitespace from next line
            next_line_trimmed = next_line.lstrip()

            # Determine separator
            if add_space:
                # Add space if:
                # - Current line doesn't end with space
                # - Next line isn't empty
                # - Current line isn't empty
                if current_line and next_line_trimmed:
                    separator = " "
                else:
                    separator = ""
            else:
                # gJ - no space added
                separator = ""

            # Join the lines
            self.buffer.lines[row] = current_line + separator + next_line_trimmed

            # Remove the next line
            del self.buffer.lines[row + 1]

        # Position cursor at the join point of the first join
        # This is where the first line ended (before any space was added)
        if self.buffer.lines[row]:
            # Find where the original first line ended
            # Move to the position just before where we added content
            original_end = len(self.buffer.lines[row].rstrip())
            if add_space and original_end > 0:
                # If we added a space, position before it
                cursor_pos = original_end
            else:
                cursor_pos = original_end
            self.buffer.set_cursor(row, cursor_pos)

        return True

    def join_lines_visual(self, start_row: int, end_row: int, add_space: bool = True) -> bool:
        """Join lines in visual selection.

        Args:
            start_row: First row of selection
            end_row: Last row of selection
            add_space: If True, add space between joined lines

        Returns:
            True if join was successful, False otherwise
        """
        # Normalize range
        if start_row > end_row:
            start_row, end_row = end_row, start_row

        # Can't join a single line
        if start_row == end_row:
            return False

        # Save state for undo
        self.buffer.save_state()

        # Position on first line
        self.buffer.set_cursor(start_row, 0)

        # Join all selected lines
        lines_to_join = end_row - start_row + 1
        return self.join_lines(lines_to_join, add_space)
