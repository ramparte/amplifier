"""Visual mode implementation for the vi editor."""


class VisualMode:
    """Handles visual mode operations including selection and operations."""

    def __init__(self, editor):
        """Initialize visual mode handler.

        Args:
            editor: Reference to the main editor instance
        """
        self.editor = editor
        self.visual_start: tuple[int, int] | None = None
        self.visual_end: tuple[int, int] | None = None
        self.visual_mode_type: str | None = None  # "char" or "line"
        self.is_active = False

    def enter_visual_mode(self, mode_type: str = "char") -> None:
        """Enter visual mode.

        Args:
            mode_type: "char" for character-wise, "line" for line-wise
        """
        self.is_active = True
        self.visual_mode_type = mode_type
        cursor_row, cursor_col = self.editor.cursor_pos

        if mode_type == "char":
            self.visual_start = (cursor_row, cursor_col)
            self.visual_end = (cursor_row, cursor_col)
        else:  # line mode
            self.visual_start = (cursor_row, 0)
            self.visual_end = (cursor_row, -1)  # -1 indicates full line

        self.editor.mode = "VISUAL"

    def exit_visual_mode(self) -> None:
        """Exit visual mode and return to normal mode."""
        self.is_active = False
        self.visual_start = None
        self.visual_end = None
        self.visual_mode_type = None
        self.editor.mode = "NORMAL"

    def update_selection(self, new_cursor_pos: tuple[int, int]) -> None:
        """Update visual selection based on cursor movement.

        Args:
            new_cursor_pos: New cursor position (row, col)
        """
        if not self.is_active:
            return

        if self.visual_mode_type == "char":
            self.visual_end = new_cursor_pos
        else:  # line mode
            # In line mode, update to include full lines
            self.visual_end = (new_cursor_pos[0], -1)

    def get_selection_bounds(self) -> tuple[tuple[int, int], tuple[int, int]]:
        """Get the normalized bounds of the visual selection.

        Returns:
            Tuple of (start_pos, end_pos) where start is before end
        """
        if not self.is_active or self.visual_start is None or self.visual_end is None:
            return ((0, 0), (0, 0))

        start_row, start_col = self.visual_start
        end_row, end_col = self.visual_end

        # Handle line mode
        if self.visual_mode_type == "line":
            start_col = 0
            if end_col == -1:
                # Get actual line length for end position
                lines = self.editor.buffer.get_lines()
                if end_row < len(lines):
                    end_col = len(lines[end_row])
                else:
                    end_col = 0

        # Normalize so start is always before end
        if start_row > end_row or (start_row == end_row and start_col > end_col):
            return ((end_row, end_col), (start_row, start_col))

        return ((start_row, start_col), (end_row, end_col))

    def get_selected_text(self) -> str:
        """Get the text currently selected in visual mode.

        Returns:
            The selected text as a string
        """
        if not self.is_active:
            return ""

        (start_row, start_col), (end_row, end_col) = self.get_selection_bounds()
        lines = self.editor.buffer.get_lines()

        if not lines:
            return ""

        if self.visual_mode_type == "line":
            # Line mode: include full lines with newlines
            selected_lines = lines[start_row : end_row + 1]
            if selected_lines:
                return "\n".join(selected_lines) + "\n"
            return ""

        # Character mode
        if start_row == end_row:
            # Single line selection
            if start_row < len(lines):
                line = lines[start_row]
                return line[start_col : end_col + 1]
            return ""

        # Multi-line character selection
        result = []

        # First line (from start_col to end)
        if start_row < len(lines):
            result.append(lines[start_row][start_col:])

        # Middle lines (full lines)
        for row in range(start_row + 1, end_row):
            if row < len(lines):
                result.append(lines[row])

        # Last line (from beginning to end_col)
        if end_row < len(lines):
            result.append(lines[end_row][: end_col + 1])

        return "\n".join(result)

    def delete_selection(self) -> str:
        """Delete the visual selection and return deleted text.

        Returns:
            The deleted text
        """
        if not self.is_active:
            return ""

        deleted_text = self.get_selected_text()
        (start_row, start_col), (end_row, end_col) = self.get_selection_bounds()

        lines = self.editor.buffer.get_lines()

        if self.visual_mode_type == "line":
            # Delete full lines
            del lines[start_row : end_row + 1]

            # Position cursor at beginning of deletion point
            if lines and start_row < len(lines):
                self.editor.cursor_pos = (start_row, 0)
            elif lines:
                # Deleted last lines, position at end of new last line
                self.editor.cursor_pos = (len(lines) - 1, 0)
            else:
                # Buffer is now empty
                lines.append("")
                self.editor.cursor_pos = (0, 0)

        else:  # Character mode
            if start_row == end_row:
                # Single line deletion
                line = lines[start_row]
                lines[start_row] = line[:start_col] + line[end_col + 1 :]
                self.editor.cursor_pos = (start_row, start_col)

            else:
                # Multi-line deletion
                # Combine first and last line parts
                first_line = lines[start_row][:start_col]
                last_line = lines[end_row][end_col + 1 :] if end_row < len(lines) else ""

                # Delete the lines in between
                del lines[start_row : end_row + 1]

                # Insert combined line
                lines.insert(start_row, first_line + last_line)
                self.editor.cursor_pos = (start_row, start_col)

        self.editor.buffer.lines = lines
        self.exit_visual_mode()

        return deleted_text

    def yank_selection(self) -> str:
        """Yank (copy) the visual selection.

        Returns:
            The yanked text
        """
        if not self.is_active:
            return ""

        yanked_text = self.get_selected_text()

        # Store in yank buffer
        self.editor.yank_buffer = yanked_text
        self.editor.yank_is_line = self.visual_mode_type == "line"

        # Return cursor to start of selection and exit visual mode
        (start_row, start_col), _ = self.get_selection_bounds()
        self.editor.cursor_pos = (start_row, start_col)
        self.exit_visual_mode()

        return yanked_text

    def handle_escape(self) -> None:
        """Handle escape key in visual mode."""
        # Just exit visual mode, keeping cursor at current position
        self.exit_visual_mode()
