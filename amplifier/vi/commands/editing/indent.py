"""Indentation commands (>>, <<, =) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class IndentCommand:
    """Implementation of indentation commands."""

    def __init__(self, buffer: "TextBuffer", tabstop: int = 4):
        """Initialize the indent command handler.

        Args:
            buffer: Text buffer to operate on
            tabstop: Number of spaces per indent level (default 4)
        """
        self.buffer = buffer
        self.tabstop = tabstop

    def indent_lines(self, start_row: int, count: int = 1, direction: str = "right") -> bool:
        """Indent or unindent lines.

        Args:
            start_row: First line to indent
            count: Number of lines to indent
            direction: 'right' to indent (>>), 'left' to unindent (<<)

        Returns:
            True if successful, False otherwise
        """
        if start_row >= len(self.buffer.lines):
            return False

        # Save state for undo
        self.buffer.save_state()

        end_row = min(start_row + count - 1, len(self.buffer.lines) - 1)

        for row in range(start_row, end_row + 1):
            line = self.buffer.lines[row]

            if direction == "right":
                # Add indentation
                self.buffer.lines[row] = " " * self.tabstop + line
            elif direction == "left":
                # Remove indentation
                # Count leading spaces
                spaces_to_remove = 0
                for char in line:
                    if char == " " and spaces_to_remove < self.tabstop:
                        spaces_to_remove += 1
                    elif char == "\t":
                        # Treat tab as tabstop spaces
                        spaces_to_remove = self.tabstop
                        break
                    else:
                        break

                # Remove the indentation
                if spaces_to_remove > 0:
                    if line[0] == "\t":
                        self.buffer.lines[row] = line[1:]
                    else:
                        self.buffer.lines[row] = line[spaces_to_remove:]

        return True

    def indent_visual(self, start_row: int, end_row: int, direction: str = "right") -> bool:
        """Indent or unindent visual selection.

        Args:
            start_row: First row of selection
            end_row: Last row of selection
            direction: 'right' to indent, 'left' to unindent

        Returns:
            True if successful, False otherwise
        """
        # Normalize range
        if start_row > end_row:
            start_row, end_row = end_row, start_row

        count = end_row - start_row + 1
        return self.indent_lines(start_row, count, direction)

    def auto_indent_lines(self, start_row: int, count: int = 1) -> bool:
        """Auto-indent lines (= command).

        For simplicity, this normalizes indentation to match surrounding context
        or removes all leading whitespace if no context is available.

        Args:
            start_row: First line to auto-indent
            count: Number of lines to auto-indent

        Returns:
            True if successful, False otherwise
        """
        if start_row >= len(self.buffer.lines):
            return False

        # Save state for undo
        self.buffer.save_state()

        end_row = min(start_row + count - 1, len(self.buffer.lines) - 1)

        # Find reference indentation from previous non-empty line
        reference_indent = 0
        for row in range(start_row - 1, -1, -1):
            line = self.buffer.lines[row]
            if line.strip():  # Non-empty line
                # Count leading spaces
                for char in line:
                    if char == " ":
                        reference_indent += 1
                    elif char == "\t":
                        reference_indent += self.tabstop
                    else:
                        break
                break

        # Apply indentation to target lines
        for row in range(start_row, end_row + 1):
            line = self.buffer.lines[row]

            # Skip empty lines
            if not line.strip():
                continue

            # Remove existing indentation
            stripped_line = line.lstrip()

            # Apply reference indentation
            self.buffer.lines[row] = " " * reference_indent + stripped_line

        return True

    def auto_indent_visual(self, start_row: int, end_row: int) -> bool:
        """Auto-indent visual selection.

        Args:
            start_row: First row of selection
            end_row: Last row of selection

        Returns:
            True if successful, False otherwise
        """
        # Normalize range
        if start_row > end_row:
            start_row, end_row = end_row, start_row

        count = end_row - start_row + 1
        return self.auto_indent_lines(start_row, count)

    def set_tabstop(self, value: int) -> None:
        """Set the tabstop value.

        Args:
            value: New tabstop value (number of spaces per indent)
        """
        if value > 0:
            self.tabstop = value
