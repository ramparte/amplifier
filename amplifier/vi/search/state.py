"""Search state management for vi editor.

This module maintains search state including patterns, history, and match tracking.
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum

from amplifier.vi.search.engine import SearchDirection
from amplifier.vi.search.engine import SearchEngine
from amplifier.vi.search.engine import SearchMatch


class SearchMode(Enum):
    """Search modes for different search behaviors."""

    NORMAL = "normal"  # Regular search
    WORD = "word"  # Word under cursor search (* and #)
    INCREMENTAL = "incremental"  # Incremental search (future)


@dataclass
class SearchState:
    """Complete search state for the vi editor."""

    # Current search configuration
    pattern: str = ""
    direction: SearchDirection = SearchDirection.FORWARD
    mode: SearchMode = SearchMode.NORMAL

    # Search options
    case_sensitive: bool = True
    use_regex: bool = True
    wrap_around: bool = True
    highlight_matches: bool = True

    # Current match tracking
    current_match: SearchMatch | None = None
    all_matches: list[SearchMatch] = field(default_factory=list)
    match_index: int = -1

    # Search history
    search_history: list[str] = field(default_factory=list)
    history_index: int = -1
    max_history: int = 50

    # Last search position (for n/N commands)
    last_search_row: int = 0
    last_search_col: int = 0

    def add_to_history(self, pattern: str) -> None:
        """Add a pattern to search history.

        Args:
            pattern: Search pattern to add
        """
        if not pattern:
            return

        # Remove if already in history to avoid duplicates
        if pattern in self.search_history:
            self.search_history.remove(pattern)

        # Add to end of history
        self.search_history.append(pattern)

        # Limit history size
        if len(self.search_history) > self.max_history:
            self.search_history.pop(0)

        # Reset history index
        self.history_index = len(self.search_history) - 1

    def get_previous_history(self) -> str | None:
        """Get previous pattern from history.

        Returns:
            Previous pattern or None if at start
        """
        if self.history_index > 0:
            self.history_index -= 1
            return self.search_history[self.history_index]
        if self.history_index == 0 and self.search_history:
            return self.search_history[0]
        return None

    def get_next_history(self) -> str | None:
        """Get next pattern from history.

        Returns:
            Next pattern or None if at end
        """
        if self.history_index < len(self.search_history) - 1:
            self.history_index += 1
            return self.search_history[self.history_index]
        return None

    def clear_matches(self) -> None:
        """Clear all match tracking."""
        self.all_matches = []
        self.current_match = None
        self.match_index = -1

    def set_matches(self, matches: list[SearchMatch], current_row: int, current_col: int) -> None:
        """Set all matches and find the closest one to current position.

        Args:
            matches: List of all matches
            current_row: Current cursor row
            current_col: Current cursor column
        """
        self.all_matches = matches

        if not matches:
            self.current_match = None
            self.match_index = -1
            return

        # Find closest match based on direction
        if self.direction == SearchDirection.FORWARD:
            # Find first match after current position
            for i, match in enumerate(matches):
                if match.row > current_row or (match.row == current_row and match.start_col > current_col):
                    self.current_match = match
                    self.match_index = i
                    return

            # Wrap around if enabled
            if self.wrap_around and matches:
                self.current_match = matches[0]
                self.match_index = 0
        else:
            # Find last match before current position
            for i in range(len(matches) - 1, -1, -1):
                match = matches[i]
                if match.row < current_row or (match.row == current_row and match.start_col < current_col):
                    self.current_match = match
                    self.match_index = i
                    return

            # Wrap around if enabled
            if self.wrap_around and matches:
                self.current_match = matches[-1]
                self.match_index = len(matches) - 1

    def next_match(self) -> SearchMatch | None:
        """Move to next match in current direction.

        Returns:
            Next match or None if no matches
        """
        if not self.all_matches:
            return None

        if self.direction == SearchDirection.FORWARD:
            self.match_index = (self.match_index + 1) % len(self.all_matches)
        else:
            self.match_index = (self.match_index - 1) % len(self.all_matches)

        self.current_match = self.all_matches[self.match_index]
        return self.current_match

    def previous_match(self) -> SearchMatch | None:
        """Move to previous match (opposite of current direction).

        Returns:
            Previous match or None if no matches
        """
        if not self.all_matches:
            return None

        if self.direction == SearchDirection.FORWARD:
            self.match_index = (self.match_index - 1) % len(self.all_matches)
        else:
            self.match_index = (self.match_index + 1) % len(self.all_matches)

        self.current_match = self.all_matches[self.match_index]
        return self.current_match

    def toggle_case_sensitive(self) -> None:
        """Toggle case sensitivity option."""
        self.case_sensitive = not self.case_sensitive

    def toggle_regex(self) -> None:
        """Toggle regex mode."""
        self.use_regex = not self.use_regex

    def toggle_wrap(self) -> None:
        """Toggle wrap around option."""
        self.wrap_around = not self.wrap_around

    def toggle_highlight(self) -> None:
        """Toggle match highlighting."""
        self.highlight_matches = not self.highlight_matches

    def reset(self) -> None:
        """Reset search state but keep history."""
        self.pattern = ""
        self.direction = SearchDirection.FORWARD
        self.mode = SearchMode.NORMAL
        self.clear_matches()
        self.last_search_row = 0
        self.last_search_col = 0


class SearchManager:
    """Manager for search operations and state."""

    def __init__(self):
        """Initialize search manager."""
        self.state = SearchState()
        self.engine = SearchEngine()

        # Character search state (for f/F/t/T commands)
        self.last_char_search: tuple[str, str] | None = None  # (char, command)

    def search(
        self, pattern: str, lines: list[str], row: int, col: int, direction: SearchDirection | None = None
    ) -> SearchMatch | None:
        """Perform a search from current position.

        Args:
            pattern: Pattern to search
            lines: Buffer lines
            row: Current row
            col: Current column
            direction: Search direction (uses state direction if None)

        Returns:
            First match found or None
        """
        if not pattern:
            return None

        # Update state
        self.state.pattern = pattern
        if direction is not None:
            self.state.direction = direction

        # Add to history
        self.state.add_to_history(pattern)

        # Configure engine
        self.engine.case_sensitive = self.state.case_sensitive
        self.engine.use_regex = self.state.use_regex

        # Find match based on direction
        if self.state.direction == SearchDirection.FORWARD:
            match = self.engine.find_next(lines, pattern, row, col, self.state.wrap_around)
        else:
            match = self.engine.find_previous(lines, pattern, row, col, self.state.wrap_around)

        # Update match state
        if match:
            self.state.current_match = match
            self.state.last_search_row = row
            self.state.last_search_col = col

            # Find all matches for highlighting
            if self.state.highlight_matches:
                text = "\n".join(lines)
                self.state.all_matches = self.engine.find_all_matches(text, pattern, self.state.case_sensitive)

                # Find index of current match
                for i, m in enumerate(self.state.all_matches):
                    if m.row == match.row and m.start_col == match.start_col:
                        self.state.match_index = i
                        break
        else:
            self.state.clear_matches()

        return match

    def repeat_search(self, lines: list[str], row: int, col: int, reverse: bool = False) -> SearchMatch | None:
        """Repeat last search (n/N commands).

        Args:
            lines: Buffer lines
            row: Current row
            col: Current column
            reverse: If True, search in opposite direction

        Returns:
            Next match or None
        """
        if not self.state.pattern:
            return None

        # Determine effective direction
        direction = self.state.direction
        if reverse:
            direction = SearchDirection.BACKWARD if direction == SearchDirection.FORWARD else SearchDirection.FORWARD

        # Search from current position
        if direction == SearchDirection.FORWARD:
            match = self.engine.find_next(lines, self.state.pattern, row, col, self.state.wrap_around)
        else:
            match = self.engine.find_previous(lines, self.state.pattern, row, col, self.state.wrap_around)

        # Update state
        if match:
            self.state.current_match = match
            self.state.last_search_row = row
            self.state.last_search_col = col

            # Update match index if we have all matches
            if self.state.all_matches:
                for i, m in enumerate(self.state.all_matches):
                    if m.row == match.row and m.start_col == match.start_col:
                        self.state.match_index = i
                        break

        return match

    def search_word_under_cursor(
        self, lines: list[str], row: int, col: int, forward: bool = True
    ) -> SearchMatch | None:
        """Search for word under cursor (* and # commands).

        Args:
            lines: Buffer lines
            row: Current row
            col: Current column
            forward: Search forward (*) or backward (#)

        Returns:
            First match or None
        """
        if row >= len(lines):
            return None

        # Find word boundaries at cursor
        line = lines[row]
        boundaries = self.engine.find_word_boundaries(line, col)

        if not boundaries:
            return None

        start, end = boundaries
        word = line[start:end]

        # Escape the word for regex and add word boundaries
        escaped = self.engine.escape_regex(word)
        pattern = f"\\b{escaped}\\b"

        # Set search mode and direction
        self.state.mode = SearchMode.WORD
        self.state.direction = SearchDirection.FORWARD if forward else SearchDirection.BACKWARD

        # Perform search
        return self.search(pattern, lines, row, col, self.state.direction)

    def set_char_search(self, char: str, command: str) -> None:
        """Store character search for repeat (f/F/t/T).

        Args:
            char: Character searched
            command: Command used (f/F/t/T)
        """
        self.last_char_search = (char, command)

    def get_char_search(self) -> tuple[str, str] | None:
        """Get last character search for repeat.

        Returns:
            Tuple of (char, command) or None
        """
        return self.last_char_search

    def get_match_positions(self) -> list[tuple[int, int, int]]:
        """Get all match positions for highlighting.

        Returns:
            List of (row, start_col, end_col) tuples
        """
        return [(m.row, m.start_col, m.end_col) for m in self.state.all_matches]

    def clear_highlights(self) -> None:
        """Clear search highlighting."""
        self.state.clear_matches()

    def get_status_string(self) -> str:
        """Get search status for display.

        Returns:
            Status string showing current search state
        """
        if not self.state.pattern:
            return ""

        parts = []

        # Pattern
        parts.append(f"/{self.state.pattern}/")

        # Match count
        if self.state.all_matches:
            current = self.state.match_index + 1 if self.state.match_index >= 0 else 0
            total = len(self.state.all_matches)
            parts.append(f"[{current}/{total}]")
        else:
            parts.append("[No matches]")

        # Options
        options = []
        if not self.state.case_sensitive:
            options.append("i")
        if not self.state.use_regex:
            options.append("F")  # Fixed string
        if not self.state.wrap_around:
            options.append("W")  # No wrap

        if options:
            parts.append(f"({','.join(options)})")

        return " ".join(parts)
