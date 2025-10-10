"""Visual mode implementations for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..buffer import TextBuffer as Buffer


class VisualMode:
    """Manages visual mode selections and operations."""

    def __init__(self, buffer: "Buffer"):
        """Initialize visual mode manager.

        Args:
            buffer: The buffer to work with
        """
        self.buffer = buffer
        self.start_pos: tuple[int, int] | None = None
        self.end_pos: tuple[int, int] | None = None
        self.mode_type: str = "character"  # character, line, or block

    def enter_visual(self, mode_type: str = "character") -> None:
        """Enter visual mode.

        Args:
            mode_type: Type of visual mode ('character', 'line', 'block')
        """
        self.mode_type = mode_type
        cursor_pos = self.buffer.get_cursor()
        self.start_pos = cursor_pos
        self.end_pos = cursor_pos

    def exit_visual(self) -> None:
        """Exit visual mode and clear selection."""
        self.start_pos = None
        self.end_pos = None
        self.mode_type = "character"

    def update_selection(self, new_pos: tuple[int, int]) -> None:
        """Update selection end position.

        Args:
            new_pos: New cursor position
        """
        if self.start_pos:
            self.end_pos = new_pos

    def get_selection_range(self) -> tuple[tuple[int, int], tuple[int, int]] | None:
        """Get the normalized selection range.

        Returns:
            Tuple of (start, end) positions or None if no selection
        """
        if not self.start_pos or not self.end_pos:
            return None

        # Normalize selection (ensure start <= end)
        start_row, start_col = self.start_pos
        end_row, end_col = self.end_pos

        if start_row > end_row or (start_row == end_row and start_col > end_col):
            return (end_row, end_col), (start_row, start_col)
        return (start_row, start_col), (end_row, end_col)

    def get_selected_text(self) -> str:
        """Get the currently selected text.

        Returns:
            The selected text
        """
        selection = self.get_selection_range()
        if not selection:
            return ""

        (start_row, start_col), (end_row, end_col) = selection
        lines = self.buffer.get_lines()

        # Empty buffer protection
        if not lines:
            return ""

        if self.mode_type == "line":
            # Select complete lines
            return "\n".join(lines[start_row : end_row + 1])

        if self.mode_type == "block":
            # Select rectangular block
            selected_lines = []
            for row in range(start_row, min(end_row + 1, len(lines))):
                if row < len(lines):
                    line = lines[row]
                    selected_lines.append(line[start_col : end_col + 1])
            return "\n".join(selected_lines)

        # character mode
        if start_row == end_row:
            # Single line selection - protect from index errors
            if start_row >= len(lines):
                return ""
            return lines[start_row][start_col : end_col + 1]
        # Multi-line selection
        selected = []
        # First line from start_col to end
        if start_row < len(lines):
            selected.append(lines[start_row][start_col:])
        # Middle lines completely
        for row in range(start_row + 1, end_row):
            if row < len(lines):
                selected.append(lines[row])
        # Last line from beginning to end_col
        if end_row < len(lines):
            selected.append(lines[end_row][: end_col + 1])
        return "\n".join(selected)

    def delete_selection(self) -> str:
        """Delete the selected text and return it.

        Returns:
            The deleted text
        """
        selected = self.get_selected_text()
        if not selected:
            return ""

        selection = self.get_selection_range()
        if not selection:
            return ""

        (start_row, start_col), (end_row, end_col) = selection
        lines = self.buffer.get_lines()

        if self.mode_type == "line":
            # Delete complete lines
            del lines[start_row : end_row + 1]
            self.buffer._lines = lines
            self.buffer.set_cursor(min(start_row, len(self.buffer._lines) - 1), 0)

        elif self.mode_type == "block":
            # Delete rectangular block
            for row in range(start_row, min(end_row + 1, len(lines))):
                if row < len(lines):
                    line = lines[row]
                    lines[row] = line[:start_col] + line[end_col + 1 :]
            self.buffer._lines = lines
            self.buffer.set_cursor(start_row, start_col)

        else:  # character mode
            if start_row == end_row:
                # Single line deletion
                line = lines[start_row]
                lines[start_row] = line[:start_col] + line[end_col + 1 :]
            else:
                # Multi-line deletion
                # Combine first and last line
                if start_row < len(lines) and end_row < len(lines):
                    lines[start_row] = lines[start_row][:start_col] + lines[end_row][end_col + 1 :]
                    # Delete intermediate lines
                    del lines[start_row + 1 : end_row + 1]

            self.buffer._lines = lines
            self.buffer.set_cursor(start_row, start_col)

        self.exit_visual()
        return selected

    def yank_selection(self) -> str:
        """Yank (copy) the selected text.

        Returns:
            The yanked text
        """
        return self.get_selected_text()

    def change_selection(self) -> str:
        """Delete selection and enter insert mode.

        Returns:
            The deleted text
        """
        return self.delete_selection()

    def indent_selection(self, dedent: bool = False) -> None:
        """Indent or dedent the selected lines.

        Args:
            dedent: If True, dedent instead of indent
        """
        selection = self.get_selection_range()
        if not selection:
            return

        (start_row, _), (end_row, _) = selection
        lines = self.buffer.get_lines()

        for row in range(start_row, min(end_row + 1, len(lines))):
            if row < len(lines):
                if dedent:
                    # Remove leading spaces/tab
                    if lines[row].startswith("    "):
                        lines[row] = lines[row][4:]
                    elif lines[row].startswith("\t"):
                        lines[row] = lines[row][1:]
                    elif lines[row].startswith(" "):
                        lines[row] = lines[row].lstrip(" ")[:1]
                else:
                    # Add indentation
                    lines[row] = "    " + lines[row]

        self.buffer._lines = lines

    def toggle_case_selection(self) -> None:
        """Toggle case of selected text."""
        selection = self.get_selection_range()
        if not selection:
            return

        (start_row, start_col), (end_row, end_col) = selection
        lines = self.buffer.get_lines()

        if self.mode_type == "line":
            for row in range(start_row, min(end_row + 1, len(lines))):
                if row < len(lines):
                    lines[row] = lines[row].swapcase()

        elif self.mode_type == "block":
            for row in range(start_row, min(end_row + 1, len(lines))):
                if row < len(lines):
                    line = lines[row]
                    block = line[start_col : end_col + 1]
                    lines[row] = line[:start_col] + block.swapcase() + line[end_col + 1 :]

        else:  # character mode
            if start_row == end_row:
                line = lines[start_row]
                selected = line[start_col : end_col + 1]
                lines[start_row] = line[:start_col] + selected.swapcase() + line[end_col + 1 :]
            else:
                # First line
                if start_row < len(lines):
                    line = lines[start_row]
                    lines[start_row] = line[:start_col] + line[start_col:].swapcase()
                # Middle lines
                for row in range(start_row + 1, end_row):
                    if row < len(lines):
                        lines[row] = lines[row].swapcase()
                # Last line
                if end_row < len(lines):
                    line = lines[end_row]
                    lines[end_row] = line[: end_col + 1].swapcase() + line[end_col + 1 :]

        self.buffer._lines = lines

    def is_active(self) -> bool:
        """Check if visual mode is active.

        Returns:
            True if visual mode is active
        """
        return self.start_pos is not None
