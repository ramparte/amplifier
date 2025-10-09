"""Insert mode variations for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..buffer import TextBuffer as Buffer


class InsertMode:
    """Manages insert mode variations and behaviors."""

    def __init__(self, buffer: "Buffer"):
        """Initialize insert mode manager.

        Args:
            buffer: The buffer to work with
        """
        self.buffer = buffer
        self.variation = "before_cursor"
        self.insert_point: tuple[int, int] | None = None

    def enter_insert(self, key: str) -> None:
        """Enter insert mode based on the key pressed.

        Args:
            key: The key that triggered insert mode
        """
        row, col = self.buffer.get_cursor_position()
        lines = self.buffer.get_lines()

        if key == "i":
            # Insert before cursor
            self.variation = "before_cursor"
            self.insert_point = (row, col)

        elif key == "I":
            # Insert at beginning of line
            self.variation = "line_start"
            # Find first non-whitespace character
            line = lines[row] if row < len(lines) else ""
            first_non_space = len(line) - len(line.lstrip())
            self.buffer.set_cursor_position(row, first_non_space)
            self.insert_point = (row, first_non_space)

        elif key == "a":
            # Insert after cursor
            self.variation = "after_cursor"
            line = lines[row] if row < len(lines) else ""
            new_col = min(col + 1, len(line))
            self.buffer.set_cursor_position(row, new_col)
            self.insert_point = (row, new_col)

        elif key == "A":
            # Insert at end of line
            self.variation = "line_end"
            line = lines[row] if row < len(lines) else ""
            self.buffer.set_cursor_position(row, len(line))
            self.insert_point = (row, len(line))

        elif key == "o":
            # Open new line below
            self.variation = "open_below"
            # Insert new line after current
            if row < len(lines):
                lines.insert(row + 1, "")
            else:
                lines.append("")
            self.buffer.set_lines(lines)
            self.buffer.set_cursor_position(row + 1, 0)
            self.insert_point = (row + 1, 0)

        elif key == "O":
            # Open new line above
            self.variation = "open_above"
            # Insert new line before current
            lines.insert(row, "")
            self.buffer.set_lines(lines)
            self.buffer.set_cursor_position(row, 0)
            self.insert_point = (row, 0)

        elif key == "s":
            # Substitute character
            self.variation = "substitute_char"
            # Delete character under cursor
            if row < len(lines) and col < len(lines[row]):
                line = lines[row]
                lines[row] = line[:col] + line[col + 1 :]
                self.buffer.set_lines(lines)
            self.insert_point = (row, col)

        elif key == "S":
            # Substitute entire line
            self.variation = "substitute_line"
            # Clear the current line
            if row < len(lines):
                # Preserve indentation
                line = lines[row]
                indent = len(line) - len(line.lstrip())
                lines[row] = " " * indent
                self.buffer.set_lines(lines)
                self.buffer.set_cursor_position(row, indent)
                self.insert_point = (row, indent)

        elif key == "c":
            # Change (requires motion)
            self.variation = "change"
            self.insert_point = (row, col)

        elif key == "C":
            # Change to end of line
            self.variation = "change_to_eol"
            # Delete from cursor to end of line
            if row < len(lines):
                line = lines[row]
                lines[row] = line[:col]
                self.buffer.set_lines(lines)
            self.insert_point = (row, col)

    def exit_insert(self) -> None:
        """Exit insert mode and adjust cursor position."""
        # Move cursor back one position if not at start of line
        row, col = self.buffer.get_cursor_position()
        if col > 0:
            self.buffer.set_cursor_position(row, col - 1)
        self.insert_point = None
        self.variation = "before_cursor"

    def get_variation(self) -> str:
        """Get the current insert mode variation.

        Returns:
            The variation name
        """
        return self.variation

    def handle_character(self, char: str) -> None:
        """Handle character input in insert mode.

        Args:
            char: The character to insert
        """
        row, col = self.buffer.get_cursor_position()
        lines = self.buffer.get_lines()

        # Ensure row exists
        while row >= len(lines):
            lines.append("")

        line = lines[row]

        if char == "\n":
            # Split line at cursor
            before = line[:col]
            after = line[col:]
            lines[row] = before
            lines.insert(row + 1, after)
            self.buffer.set_lines(lines)
            self.buffer.set_cursor_position(row + 1, 0)
        elif char == "\b" or char == "\x7f":  # Backspace
            if col > 0:
                # Delete character before cursor
                lines[row] = line[: col - 1] + line[col:]
                self.buffer.set_lines(lines)
                self.buffer.set_cursor_position(row, col - 1)
            elif row > 0:
                # Join with previous line
                prev_line = lines[row - 1]
                lines[row - 1] = prev_line + line
                del lines[row]
                self.buffer.set_lines(lines)
                self.buffer.set_cursor_position(row - 1, len(prev_line))
        elif char == "\t":
            # Insert tab (as spaces)
            spaces = "    "  # Use 4 spaces for tab
            lines[row] = line[:col] + spaces + line[col:]
            self.buffer.set_lines(lines)
            self.buffer.set_cursor_position(row, col + len(spaces))
        else:
            # Normal character insertion
            lines[row] = line[:col] + char + line[col:]
            self.buffer.set_lines(lines)
            self.buffer.set_cursor_position(row, col + 1)

    def handle_arrow_key(self, direction: str) -> None:
        """Handle arrow key in insert mode.

        Args:
            direction: One of 'up', 'down', 'left', 'right'
        """
        row, col = self.buffer.get_cursor_position()
        lines = self.buffer.get_lines()

        if direction == "up" and row > 0:
            new_row = row - 1
            new_col = min(col, len(lines[new_row]))
            self.buffer.set_cursor_position(new_row, new_col)
        elif direction == "down" and row < len(lines) - 1:
            new_row = row + 1
            new_col = min(col, len(lines[new_row]))
            self.buffer.set_cursor_position(new_row, new_col)
        elif direction == "left" and col > 0:
            self.buffer.set_cursor_position(row, col - 1)
        elif direction == "right":
            max_col = len(lines[row]) if row < len(lines) else 0
            if col < max_col:
                self.buffer.set_cursor_position(row, col + 1)

    def get_insert_point(self) -> tuple[int, int] | None:
        """Get the point where insert mode was entered.

        Returns:
            The (row, col) position or None
        """
        return self.insert_point
