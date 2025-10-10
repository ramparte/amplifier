"""Text buffer implementation for vi editor."""

import re


class TextBuffer:
    """Text buffer that manages document content and cursor position."""

    def __init__(self, content: str = ""):
        """Initialize buffer with optional content."""
        self._lines = content.split("\n") if content else [""]
        self._cursor_row = 0
        self._cursor_col = 0
        self._mark_row: int | None = None
        self._mark_col: int | None = None

        # Marks for navigation (a-z)
        self._marks: dict[str, tuple[int, int]] = {}

        # Jump list for navigation history
        self._jump_list: list[tuple[int, int]] = []
        self._jump_list_index: int = -1  # Current position in jump list
        self._max_jump_list_size: int = 100

        # Search state
        self._search_pattern: str | None = None
        self._search_direction: str = "forward"  # "forward" or "backward"
        self._search_matches: list[tuple[int, int]] = []  # List of (row, col) positions
        self._current_match_index: int = -1  # Index in search_matches
        self._last_search_pos: tuple[int, int] | None = None  # For repeat search

        # Undo/Redo state management
        self._undo_stack: list[dict] = []  # Stack of buffer states for undo
        self._redo_stack: list[dict] = []  # Stack of buffer states for redo
        self._max_undo_levels: int = 100  # Maximum undo history
        self._pending_change: bool = False  # Track if we're in the middle of a change

    @property
    def lines(self) -> list[str]:
        """Get all lines as a list."""
        return self._lines

    def get_lines(self) -> list[str]:
        """Get all lines in the buffer."""
        return self._lines

    def set_lines(self, lines: list[str]) -> None:
        """Set buffer content from list of lines.

        Args:
            lines: List of strings, one per line
        """
        # Accept empty list for testing edge cases, otherwise ensure at least one line
        self._lines = lines if isinstance(lines, list) else [""]
        if not self._lines:
            # Allow empty buffer for testing but ensure it's a valid list
            self._lines = []
        # Adjust cursor if needed - this will add a line if truly empty
        if self._lines:  # Only adjust if we have content
            self._adjust_cursor_bounds()
        else:
            # Empty buffer - set cursor to origin
            self._cursor_row = 0
            self._cursor_col = 0

    def get_cursor(self) -> tuple[int, int]:
        """Get current cursor position as (row, col)."""
        return (self._cursor_row, self._cursor_col)

    def get_content(self) -> str:
        """Get entire buffer content as a single string."""
        return "\n".join(self._lines)

    def set_cursor(self, row: int, col: int) -> None:
        """Set cursor position with bounds checking."""
        if not self._lines:
            # Empty buffer - keep cursor at origin
            self._cursor_row = 0
            self._cursor_col = 0
            return

        # Ensure row is within bounds
        self._cursor_row = max(0, min(row, len(self._lines) - 1))

        # Ensure column is within bounds for current row
        max_col = len(self._lines[self._cursor_row])
        self._cursor_col = max(0, min(col, max_col))

    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor to absolute position (row, col) with bounds checking.

        This is the primary cursor positioning method that other movement
        methods can use internally.

        Args:
            row: Target row (0-indexed)
            col: Target column (0-indexed)
        """
        # Ensure we have at least one line
        if not self._lines:
            self._lines = [""]

        # Clamp row to valid range
        self._cursor_row = max(0, min(row, len(self._lines) - 1))

        # Clamp column to valid range for the target row
        max_col = len(self._lines[self._cursor_row])
        self._cursor_col = max(0, min(col, max_col))

    def move_cursor_relative(self, direction: str, count: int = 1) -> None:
        """Move cursor relative to current position.

        Args:
            direction: One of 'h' (left), 'j' (down), 'k' (up), 'l' (right)
            count: Number of times to move (default 1)
        """
        if direction == "h":  # Left
            for _ in range(count):
                self.move_cursor_left()
        elif direction == "j":  # Down
            for _ in range(count):
                self.move_cursor_down()
        elif direction == "k":  # Up
            for _ in range(count):
                self.move_cursor_up()
        elif direction == "l":  # Right
            for _ in range(count):
                self.move_cursor_right()
        else:
            raise ValueError(f"Invalid direction: {direction}. Must be one of 'h', 'j', 'k', 'l'")

    def move_cursor_up(self) -> None:
        """Move cursor up one line."""
        if not self._lines or self._cursor_row == 0:
            return
        if self._cursor_row > 0:
            self._cursor_row -= 1
            self._adjust_column()

    def move_cursor_down(self) -> None:
        """Move cursor down one line."""
        if not self._lines:
            return
        if self._cursor_row < len(self._lines) - 1:
            self._cursor_row += 1
            self._adjust_column()

    def move_cursor_left(self) -> None:
        """Move cursor left one character."""
        if not self._lines:
            return
        if self._cursor_col > 0:
            self._cursor_col -= 1
        elif self._cursor_row > 0:
            # Move to end of previous line
            self._cursor_row -= 1
            self._cursor_col = len(self._lines[self._cursor_row])

    def move_cursor_right(self) -> None:
        """Move cursor right one character."""
        if not self._lines:
            return
        current_line = self._lines[self._cursor_row]
        # In normal mode, cursor should stay ON a character, not past it
        # Can move right if we're not on the last character
        if current_line and self._cursor_col < len(current_line) - 1:
            self._cursor_col += 1
        elif not current_line:
            # Empty line - stay at column 0
            pass
        elif self._cursor_row < len(self._lines) - 1:
            # At end of line, move to start of next line
            self._cursor_row += 1
            self._cursor_col = 0

    def move_to_line_start(self) -> None:
        """Move cursor to start of current line."""
        if self._lines:
            self._cursor_col = 0

    def move_to_line_end(self) -> None:
        """Move cursor to end of current line."""
        if self._lines:
            self._cursor_col = len(self._lines[self._cursor_row])

    def move_to_first_line(self) -> None:
        """Move cursor to first line of buffer."""
        if self._lines:
            self._cursor_row = 0
            self._adjust_column()

    def move_to_last_line(self) -> None:
        """Move cursor to last line of buffer."""
        if self._lines:
            self._cursor_row = len(self._lines) - 1
            self._adjust_column()

    def insert_char(self, char: str) -> None:
        """Insert a character at cursor position."""
        # Save state before modification
        self.save_state()

        if char == "\n":
            self._split_line()
        else:
            line = self._lines[self._cursor_row]
            self._lines[self._cursor_row] = line[: self._cursor_col] + char + line[self._cursor_col :]
            self._cursor_col += 1

    def insert_text(self, text: str) -> None:
        """Insert text at cursor position.

        Handles multi-character strings and newlines properly.
        """
        for char in text:
            self.insert_char(char)

    def delete_char(self) -> None:
        """Delete character at cursor position."""
        if not self._lines:
            return  # Nothing to delete in empty buffer
        line = self._lines[self._cursor_row]
        if self._cursor_col < len(line):
            self._lines[self._cursor_row] = line[: self._cursor_col] + line[self._cursor_col + 1 :]
        elif self._cursor_row < len(self._lines) - 1:
            # Join with next line
            self._lines[self._cursor_row] += self._lines[self._cursor_row + 1]
            del self._lines[self._cursor_row + 1]

    def delete_line(self) -> None:
        """Delete current line."""
        if not self._lines:
            return  # Nothing to delete in empty buffer
        if len(self._lines) > 1:
            del self._lines[self._cursor_row]
            # Adjust cursor if we deleted the last line
            if self._cursor_row >= len(self._lines):
                self._cursor_row = len(self._lines) - 1
            # Reset column to start of line
            self._cursor_col = 0
        else:
            # If only one line, delete it completely (allow empty buffer for testing)
            self._lines = []
            self._cursor_row = 0
            self._cursor_col = 0

    def backspace(self) -> None:
        """Delete character before cursor position."""
        if self._cursor_col > 0:
            self._cursor_col -= 1
            self.delete_char()
        elif self._cursor_row > 0:
            # Join with previous line
            prev_line = self._lines[self._cursor_row - 1]
            self._cursor_col = len(prev_line)
            self._lines[self._cursor_row - 1] += self._lines[self._cursor_row]
            del self._lines[self._cursor_row]
            self._cursor_row -= 1

    def _split_line(self) -> None:
        """Split current line at cursor position."""
        line = self._lines[self._cursor_row]
        self._lines[self._cursor_row] = line[: self._cursor_col]
        self._lines.insert(self._cursor_row + 1, line[self._cursor_col :])
        self._cursor_row += 1
        self._cursor_col = 0

    def _adjust_column(self) -> None:
        """Adjust column position after row change to stay within line bounds."""
        if not self._lines:
            self._cursor_col = 0
            return
        max_col = len(self._lines[self._cursor_row])
        if self._cursor_col > max_col:
            self._cursor_col = max_col

    def set_mark(self) -> None:
        """Set mark at current cursor position."""
        self._mark_row = self._cursor_row
        self._mark_col = self._cursor_col

    def get_mark(self) -> tuple[int, int] | None:
        """Get mark position if set."""
        if self._mark_row is not None and self._mark_col is not None:
            return (self._mark_row, self._mark_col)
        return None

    def clear_mark(self) -> None:
        """Clear the mark."""
        self._mark_row = None
        self._mark_col = None

    def get_selected_text(self) -> str | None:
        """Get text between mark and cursor position.

        Returns None if no mark is set.
        """
        mark = self.get_mark()
        if mark is None:
            return None

        mark_row, mark_col = mark
        cursor_row, cursor_col = self.get_cursor()

        # Normalize selection (start before end)
        if mark_row < cursor_row or (mark_row == cursor_row and mark_col < cursor_col):
            start_row, start_col = mark_row, mark_col
            end_row, end_col = cursor_row, cursor_col
        else:
            start_row, start_col = cursor_row, cursor_col
            end_row, end_col = mark_row, mark_col

        # Extract text
        if start_row == end_row:
            # Selection within single line
            return self._lines[start_row][start_col:end_col]
        # Multi-line selection
        selected = []
        for row in range(start_row, end_row + 1):
            if row == start_row:
                selected.append(self._lines[row][start_col:])
            elif row == end_row:
                selected.append(self._lines[row][:end_col])
            else:
                selected.append(self._lines[row])
        return "\n".join(selected)

    def replace_char(self, char: str) -> None:
        """Replace character at cursor position."""
        if self._cursor_row < len(self._lines):
            line = self._lines[self._cursor_row]
            if self._cursor_col < len(line):
                self._lines[self._cursor_row] = line[: self._cursor_col] + char + line[self._cursor_col + 1 :]

    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return len(self._lines) == 1 and self._lines[0] == ""

    def get_line_count(self) -> int:
        """Get total number of lines in buffer."""
        return len(self._lines)

    def get_char_count(self) -> int:
        """Get total character count in buffer."""
        return len(self.get_content())

    def get_current_line(self) -> str:
        """Get the text of the current line."""
        if self._cursor_row < len(self._lines):
            return self._lines[self._cursor_row]
        return ""

    def get_char_at_cursor(self) -> str | None:
        """Get the character at the current cursor position.

        Returns:
            The character at cursor, or None if cursor is at end of line/file.
        """
        if self._cursor_row < len(self._lines):
            line = self._lines[self._cursor_row]
            if self._cursor_col < len(line):
                return line[self._cursor_col]
        return None

    def get_line(self, row: int) -> str | None:
        """Get text of specified line.

        Returns None if row is out of bounds.
        """
        if 0 <= row < len(self._lines):
            return self._lines[row]
        return None

    # Enhanced cursor movement methods

    def move_to_start(self) -> None:
        """Move cursor to the start of the buffer (first line, first column)."""
        self._cursor_row = 0
        self._cursor_col = 0

    def move_to_end(self) -> None:
        """Move cursor to the end of the buffer (last line, last character)."""
        if self._lines:
            self._cursor_row = len(self._lines) - 1
            self._cursor_col = len(self._lines[self._cursor_row])

    def move_left(self, count: int = 1) -> None:
        """Move cursor left by count characters.

        Wraps to previous line if needed.
        """
        for _ in range(count):
            self.move_cursor_left()

    def move_right(self, count: int = 1) -> None:
        """Move cursor right by count characters.

        Wraps to next line if needed.
        """
        for _ in range(count):
            self.move_cursor_right()

    def move_up(self, count: int = 1) -> None:
        """Move cursor up by count lines."""
        for _ in range(count):
            self.move_cursor_up()

    def move_down(self, count: int = 1) -> None:
        """Move cursor down by count lines."""
        for _ in range(count):
            self.move_cursor_down()

    # Word movement methods

    def move_word_forward(self, count: int = 1) -> None:
        """Move cursor forward by count words.

        A word is a sequence of non-whitespace characters.
        """
        for _ in range(count):
            row, col = self.get_cursor()

            if row >= len(self._lines):
                break

            line = self._lines[row]

            # Skip current word
            while col < len(line) and not line[col].isspace():
                col += 1

            # Skip whitespace
            while col < len(line) and line[col].isspace():
                col += 1

            # If at end of line, move to next line
            if col >= len(line) and row < len(self._lines) - 1:
                row += 1
                col = 0
                # Skip leading whitespace on new line
                if row < len(self._lines):
                    line = self._lines[row]
                    while col < len(line) and line[col].isspace():
                        col += 1

            self.set_cursor(row, col)

    def move_word_backward(self, count: int = 1) -> None:
        """Move cursor backward by count words to word beginning."""
        for _ in range(count):
            row, col = self.get_cursor()

            if row >= len(self._lines):
                break

            # Move back one position first
            if col > 0:
                col -= 1
            elif row > 0:
                row -= 1
                col = len(self._lines[row]) - 1 if row < len(self._lines) else 0

            if row < len(self._lines):
                line = self._lines[row]

                # Skip whitespace backwards
                while col > 0 and line[col].isspace():
                    col -= 1

                # Skip word backwards to beginning
                while col > 0 and not line[col - 1].isspace():
                    col -= 1

            self.set_cursor(row, col)

    def move_word_end(self, count: int = 1) -> None:
        """Move cursor to end of word."""
        for _ in range(count):
            row, col = self.get_cursor()

            if row >= len(self._lines):
                break

            line = self._lines[row]

            # If on whitespace, skip to next word first
            if col < len(line) and line[col].isspace():
                while col < len(line) and line[col].isspace():
                    col += 1

            # Move to end of current word
            if col < len(line) and not line[col].isspace():
                while col < len(line) - 1 and not line[col + 1].isspace():
                    col += 1

            self.set_cursor(row, col)

    def move_word_end_backward(self, count: int = 1) -> None:
        """Move cursor backward to end of previous word (ge command)."""
        for _ in range(count):
            row, col = self.get_cursor()

            # Move back one position
            if col > 0:
                col -= 1
            elif row > 0:
                row -= 1
                col = len(self._lines[row]) - 1 if row < len(self._lines) else 0
            else:
                break

            if row < len(self._lines):
                line = self._lines[row]

                # Skip whitespace backwards
                while col > 0 and row >= 0:
                    if col >= 0 and col < len(line) and line[col].isspace():
                        col -= 1
                        if col < 0 and row > 0:
                            row -= 1
                            line = self._lines[row]
                            col = len(line) - 1
                    else:
                        break

                # We're now on a word, stay at its end
                while col < len(line) - 1 and not line[col + 1].isspace():
                    col += 1

            self.set_cursor(row, col)

    # Character search methods

    def find_char_forward(self, char: str, till: bool = False) -> bool:
        """Find character forward in current line.

        Args:
            char: Character to search for
            till: If True, stop before the character (t command)

        Returns:
            True if character was found, False otherwise
        """
        row, col = self.get_cursor()
        if row >= len(self._lines):
            return False

        line = self._lines[row]
        start_col = col + 1

        for i in range(start_col, len(line)):
            if line[i] == char:
                target_col = i - 1 if till else i
                self.set_cursor(row, target_col)
                return True

        return False

    def find_char_backward(self, char: str, till: bool = False) -> bool:
        """Find character backward in current line.

        Args:
            char: Character to search for
            till: If True, stop after the character (T command)

        Returns:
            True if character was found, False otherwise
        """
        row, col = self.get_cursor()
        if row >= len(self._lines):
            return False

        line = self._lines[row]

        for i in range(col - 1, -1, -1):
            if line[i] == char:
                target_col = i + 1 if till else i
                self.set_cursor(row, target_col)
                return True

        return False

    # Screen-relative positioning

    def move_to_screen_top(self, viewport_start: int, viewport_height: int, offset: int = 0) -> None:
        """Move cursor to top of screen (H command).

        Args:
            viewport_start: First visible line number
            viewport_height: Number of visible lines
            offset: Lines from top (default 0)
        """
        target_row = min(viewport_start + offset, len(self._lines) - 1)
        self.set_cursor(target_row, 0)
        self.move_to_first_non_blank()

    def move_to_screen_middle(self, viewport_start: int, viewport_height: int) -> None:
        """Move cursor to middle of screen (M command)."""
        middle = viewport_start + viewport_height // 2
        target_row = min(middle, len(self._lines) - 1)
        self.set_cursor(target_row, 0)
        self.move_to_first_non_blank()

    def move_to_screen_bottom(self, viewport_start: int, viewport_height: int, offset: int = 0) -> None:
        """Move cursor to bottom of screen (L command).

        Args:
            viewport_start: First visible line number
            viewport_height: Number of visible lines
            offset: Lines from bottom (default 0)
        """
        bottom = viewport_start + viewport_height - 1
        target_row = max(viewport_start, min(bottom - offset, len(self._lines) - 1))
        self.set_cursor(target_row, 0)
        self.move_to_first_non_blank()

    def move_to_first_non_blank(self) -> None:
        """Move cursor to first non-blank character of current line."""
        row, _ = self.get_cursor()
        if row < len(self._lines):
            line = self._lines[row]
            col = 0
            for i, char in enumerate(line):
                if not char.isspace():
                    col = i
                    break
            self.set_cursor(row, col)

    # Cursor state serialization for undo/redo

    def get_cursor_state(self) -> dict:
        """Get cursor state for serialization.

        Returns:
            Dictionary with cursor position and mark.
        """
        state = {
            "cursor_row": self._cursor_row,
            "cursor_col": self._cursor_col,
            "mark_row": self._mark_row,
            "mark_col": self._mark_col,
        }
        return state

    def set_cursor_state(self, state: dict) -> None:
        """Restore cursor state from serialized data.

        Args:
            state: Dictionary with cursor position and mark.
        """
        self._cursor_row = state.get("cursor_row", 0)
        self._cursor_col = state.get("cursor_col", 0)
        self._mark_row = state.get("mark_row")
        self._mark_col = state.get("mark_col")

        # Validate cursor position
        self._adjust_cursor_bounds()

    def _adjust_cursor_bounds(self) -> None:
        """Ensure cursor is within valid bounds."""
        # Allow truly empty buffers (for testing edge cases)
        if not self._lines:
            # Empty buffer - reset cursor to origin
            self._cursor_row = 0
            self._cursor_col = 0
            return

        # Clamp row to valid range
        self._cursor_row = max(0, min(self._cursor_row, len(self._lines) - 1))

        # Clamp column to valid range for current row
        max_col = len(self._lines[self._cursor_row])
        self._cursor_col = max(0, min(self._cursor_col, max_col))

    # Undo/Redo functionality

    def _create_snapshot(self) -> dict:
        """Create a snapshot of the current buffer state.

        Returns:
            Dictionary containing complete buffer state
        """
        return {
            "lines": list(self._lines),  # Deep copy of lines
            "cursor_row": self._cursor_row,
            "cursor_col": self._cursor_col,
            "mark_row": self._mark_row,
            "mark_col": self._mark_col,
        }

    def _restore_snapshot(self, snapshot: dict) -> None:
        """Restore buffer state from a snapshot.

        Args:
            snapshot: Dictionary containing buffer state to restore
        """
        self._lines = list(snapshot["lines"])  # Deep copy
        self._cursor_row = snapshot["cursor_row"]
        self._cursor_col = snapshot["cursor_col"]
        self._mark_row = snapshot["mark_row"]
        self._mark_col = snapshot["mark_col"]

        # Ensure cursor is within bounds after restore
        self._adjust_cursor_bounds()

    def save_state(self) -> None:
        """Save current state to undo stack before a change.

        This should be called before any operation that modifies the buffer.
        """
        # Don't save if we're in the middle of a compound change
        if self._pending_change:
            return

        # Create snapshot and add to undo stack
        snapshot = self._create_snapshot()
        self._undo_stack.append(snapshot)

        # Limit undo history size
        if len(self._undo_stack) > self._max_undo_levels:
            self._undo_stack.pop(0)

        # Clear redo stack when new changes are made
        self._redo_stack.clear()

    def begin_compound_change(self) -> None:
        """Begin a compound change that groups multiple operations.

        Used for operations that involve multiple buffer modifications
        that should be undone/redone as a single unit.
        """
        if not self._pending_change:
            self.save_state()
            self._pending_change = True

    def end_compound_change(self) -> None:
        """End a compound change."""
        self._pending_change = False

    def undo(self) -> bool:
        """Undo the last change.

        Returns:
            True if undo was performed, False if nothing to undo
        """
        if not self._undo_stack:
            return False

        # Save current state to redo stack
        current_state = self._create_snapshot()
        self._redo_stack.append(current_state)

        # Restore previous state
        previous_state = self._undo_stack.pop()
        self._restore_snapshot(previous_state)

        return True

    def redo(self) -> bool:
        """Redo the last undone change.

        Returns:
            True if redo was performed, False if nothing to redo
        """
        if not self._redo_stack:
            return False

        # Save current state to undo stack
        current_state = self._create_snapshot()
        self._undo_stack.append(current_state)

        # Restore next state
        next_state = self._redo_stack.pop()
        self._restore_snapshot(next_state)

        return True

    def get_undo_count(self) -> int:
        """Get number of available undo operations."""
        return len(self._undo_stack)

    def get_redo_count(self) -> int:
        """Get number of available redo operations."""
        return len(self._redo_stack)

    def clear_undo_history(self) -> None:
        """Clear all undo/redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    # Marks management methods

    def set_named_mark(self, mark_name: str) -> None:
        """Set a named mark (a-z) at current cursor position.

        Args:
            mark_name: Single lowercase letter (a-z) for the mark
        """
        if len(mark_name) == 1 and "a" <= mark_name <= "z":
            self._marks[mark_name] = (self._cursor_row, self._cursor_col)

    def jump_to_mark(self, mark_name: str) -> bool:
        """Jump to a named mark.

        Args:
            mark_name: Single lowercase letter (a-z) for the mark

        Returns:
            True if mark exists and jump was successful, False otherwise
        """
        if mark_name in self._marks:
            row, col = self._marks[mark_name]
            # Push current position to jump list before jumping
            self.push_jump_position()
            # Validate and jump to mark
            if 0 <= row < len(self._lines):
                self.set_cursor(row, col)
                return True
        return False

    def clear_named_mark(self, mark_name: str) -> None:
        """Clear a specific named mark.

        Args:
            mark_name: Single lowercase letter (a-z) for the mark
        """
        self._marks.pop(mark_name, None)

    def clear_all_marks(self) -> None:
        """Clear all named marks."""
        self._marks.clear()

    def get_named_marks(self) -> dict[str, tuple[int, int]]:
        """Get all current named marks.

        Returns:
            Dictionary of mark names to positions
        """
        return self._marks.copy()

    # Jump list management methods

    def push_jump_position(self) -> None:
        """Push current cursor position to the jump list.

        This is typically called before making a large movement.
        """
        current_pos = (self._cursor_row, self._cursor_col)

        # If we're not at the end of the jump list, truncate forward history
        if self._jump_list_index < len(self._jump_list) - 1:
            self._jump_list = self._jump_list[: self._jump_list_index + 1]

        # Don't add duplicate consecutive positions
        if not self._jump_list or self._jump_list[-1] != current_pos:
            self._jump_list.append(current_pos)

            # Limit jump list size
            if len(self._jump_list) > self._max_jump_list_size:
                self._jump_list.pop(0)
            else:
                self._jump_list_index = len(self._jump_list) - 1

    def jump_older(self) -> bool:
        """Jump to an older position in the jump list (Ctrl-O).

        Returns:
            True if jump was successful, False if at oldest position
        """
        if self._jump_list_index > 0:
            # If at the end of list, first save current position
            if self._jump_list_index == len(self._jump_list) - 1:
                current_pos = (self._cursor_row, self._cursor_col)
                if not self._jump_list or self._jump_list[-1] != current_pos:
                    self._jump_list.append(current_pos)
                    if len(self._jump_list) > self._max_jump_list_size:
                        self._jump_list.pop(0)
                    else:
                        self._jump_list_index += 1

            # Move to older position
            self._jump_list_index -= 1
            row, col = self._jump_list[self._jump_list_index]

            # Validate and jump
            if 0 <= row < len(self._lines):
                self.set_cursor(row, col)
                return True
        return False

    def jump_newer(self) -> bool:
        """Jump to a newer position in the jump list (Ctrl-I).

        Returns:
            True if jump was successful, False if at newest position
        """
        if self._jump_list_index < len(self._jump_list) - 1:
            self._jump_list_index += 1
            row, col = self._jump_list[self._jump_list_index]

            # Validate and jump
            if 0 <= row < len(self._lines):
                self.set_cursor(row, col)
                return True
        return False

    def get_jump_list_info(self) -> tuple[list[tuple[int, int]], int]:
        """Get jump list and current position for debugging/display.

        Returns:
            Tuple of (jump_list, current_index)
        """
        return (self._jump_list.copy(), self._jump_list_index)

    def clear_jump_list(self) -> None:
        """Clear the jump list."""
        self._jump_list.clear()
        self._jump_list_index = -1

    def substitute_range(self, start_row: int, end_row: int, pattern: str, replacement: str, flags: str = "") -> int:
        """Perform substitution on a range of lines.

        Args:
            start_row: Starting line number (0-indexed)
            end_row: Ending line number (0-indexed, inclusive)
            pattern: Regular expression pattern to match
            replacement: Replacement string
            flags: Substitution flags (g for global, i for case-insensitive)

        Returns:
            Number of substitutions made
        """

        # Save state before modification
        self.save_state()

        # Parse flags
        global_flag = "g" in flags
        case_insensitive = "i" in flags

        # Compile regex with appropriate flags
        re_flags = re.IGNORECASE if case_insensitive else 0
        try:
            regex = re.compile(pattern, re_flags)
        except re.error:
            return 0

        # Perform substitution
        total_substitutions = 0
        for row in range(start_row, min(end_row + 1, len(self._lines))):
            line = self._lines[row]
            if global_flag:
                # Replace all occurrences
                new_line, count = regex.subn(replacement, line)
            else:
                # Replace first occurrence only
                new_line, count = regex.subn(replacement, line, count=1)

            if count > 0:
                self._lines[row] = new_line
                total_substitutions += count

        return total_substitutions
