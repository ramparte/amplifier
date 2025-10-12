"""Search functionality implementation for the vi editor."""


class SearchManager:
    """Handles search and find operations in the vi editor."""

    def __init__(self, editor):
        """Initialize the search manager.

        Args:
            editor: Reference to the main editor instance
        """
        self.editor = editor
        self.last_search_pattern: str | None = None
        self.last_search_direction: str = "forward"  # "forward" or "backward"
        self.search_history: list[str] = []
        self.max_history = 50

    def search_forward(self, pattern: str, start_pos: tuple[int, int] | None = None) -> tuple[int, int] | None:
        """Search forward for a pattern in the buffer.

        Args:
            pattern: The pattern to search for
            start_pos: Starting position for search (default: current cursor)

        Returns:
            Position of match (row, col) or None if not found
        """
        if not pattern:
            # Use last search pattern if empty
            if self.last_search_pattern:
                pattern = self.last_search_pattern
            else:
                return None

        # Update search state
        self.last_search_pattern = pattern
        self.last_search_direction = "forward"
        self._add_to_history(pattern)

        lines = self.editor.buffer.get_lines()
        if not lines:
            return None

        if start_pos is None:
            start_pos = self.editor.cursor_pos

        if start_pos is None:
            return None

        start_row, start_col = start_pos

        # Search from current position to end of current line
        if start_row < len(lines):
            line = lines[start_row]
            # Start searching from next character
            search_start = start_col + 1 if start_col < len(line) else start_col
            pos = line.find(pattern, search_start)
            if pos != -1:
                return (start_row, pos)

        # Search subsequent lines
        for row in range(start_row + 1, len(lines)):
            pos = lines[row].find(pattern)
            if pos != -1:
                return (row, pos)

        # Wrap around to beginning
        for row in range(0, start_row + 1):
            if row < start_row:
                # Search entire line if before start
                pos = lines[row].find(pattern)
            else:
                # Search up to start position on start line
                line = lines[row]
                pos = line[:start_col].find(pattern)

            if pos != -1:
                return (row, pos)

        return None

    def search_backward(self, pattern: str, start_pos: tuple[int, int] | None = None) -> tuple[int, int] | None:
        """Search backward for a pattern in the buffer.

        Args:
            pattern: The pattern to search for
            start_pos: Starting position for search (default: current cursor)

        Returns:
            Position of match (row, col) or None if not found
        """
        if not pattern:
            # Use last search pattern if empty
            if self.last_search_pattern:
                pattern = self.last_search_pattern
            else:
                return None

        # Update search state
        self.last_search_pattern = pattern
        self.last_search_direction = "backward"
        self._add_to_history(pattern)

        lines = self.editor.buffer.get_lines()
        if not lines:
            return None

        if start_pos is None:
            start_pos = self.editor.cursor_pos

        if start_pos is None:
            return None

        start_row, start_col = start_pos

        # Search from beginning of current line to current position
        if start_row < len(lines) and start_col > 0:
            line = lines[start_row]
            # Search backwards in current line up to current position
            search_text = line[:start_col]
            pos = search_text.rfind(pattern)
            if pos != -1:
                return (start_row, pos)

        # Search previous lines (in reverse)
        for row in range(start_row - 1, -1, -1):
            line = lines[row]
            pos = line.rfind(pattern)
            if pos != -1:
                return (row, pos)

        # Wrap around to end
        for row in range(len(lines) - 1, start_row - 1, -1):
            if row > start_row:
                # Search entire line if after start
                pos = lines[row].rfind(pattern)
            elif row == start_row:
                # Search from current position to end on start line
                if start_col < len(lines[row]):
                    search_text = lines[row][start_col + 1 :]
                    pos = search_text.rfind(pattern)
                    if pos != -1:
                        return (row, start_col + 1 + pos)
                continue
            else:
                continue

            if pos != -1:
                return (row, pos)

        return None

    def find_next(self) -> tuple[int, int] | None:
        """Find the next occurrence of the last search pattern.

        Returns:
            Position of next match or None if not found
        """
        if not self.last_search_pattern:
            return None

        if self.last_search_direction == "forward":
            return self.search_forward(self.last_search_pattern)
        return self.search_backward(self.last_search_pattern)

    def find_previous(self) -> tuple[int, int] | None:
        """Find the previous occurrence of the last search pattern.

        Returns:
            Position of previous match or None if not found
        """
        if not self.last_search_pattern:
            return None

        # Reverse the search direction
        if self.last_search_direction == "forward":
            return self.search_backward(self.last_search_pattern)
        return self.search_forward(self.last_search_pattern)

    def execute_search(self, command: str) -> bool:
        """Execute a search command.

        Args:
            command: The search command (e.g., "/pattern" or "?pattern")

        Returns:
            True if search was successful, False otherwise
        """
        if not command:
            return False

        # Determine search type
        if command.startswith("/"):
            # Forward search
            pattern = command[1:]
            result = self.search_forward(pattern)
        elif command.startswith("?"):
            # Backward search
            pattern = command[1:]
            result = self.search_backward(pattern)
        else:
            return False

        # Move cursor if match found
        if result:
            self.editor.cursor_pos = result
            return True

        return False

    def clear_search(self) -> None:
        """Clear the current search pattern."""
        self.last_search_pattern = None

    def get_last_pattern(self) -> str | None:
        """Get the last search pattern.

        Returns:
            The last search pattern or None
        """
        return self.last_search_pattern

    def _add_to_history(self, pattern: str) -> None:
        """Add a pattern to search history.

        Args:
            pattern: The pattern to add
        """
        # Remove pattern if it already exists (to move to end)
        if pattern in self.search_history:
            self.search_history.remove(pattern)

        # Add to end of history
        self.search_history.append(pattern)

        # Maintain maximum history size
        if len(self.search_history) > self.max_history:
            self.search_history.pop(0)

    def get_history(self) -> list[str]:
        """Get the search history.

        Returns:
            List of previous search patterns
        """
        return self.search_history.copy()

    def highlight_matches(self) -> list[tuple[int, int]]:
        """Get all positions of the current search pattern for highlighting.

        Returns:
            List of (row, col) positions of all matches
        """
        if not self.last_search_pattern:
            return []

        matches = []
        lines = self.editor.buffer.get_lines()

        for row, line in enumerate(lines):
            col = 0
            while True:
                pos = line.find(self.last_search_pattern, col)
                if pos == -1:
                    break
                matches.append((row, pos))
                col = pos + 1

        return matches
