"""Core search engine for pattern matching in vi editor."""

import re
from dataclasses import dataclass
from enum import Enum


class SearchDirection(Enum):
    """Search direction for pattern matching."""

    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass
class SearchMatch:
    """Represents a search match in the buffer."""

    row: int
    start_col: int
    end_col: int
    text: str

    def contains(self, row: int, col: int) -> bool:
        """Check if position is within this match."""
        return self.row == row and self.start_col <= col < self.end_col


@dataclass
class SearchState:
    """Current search state including pattern and last match."""

    pattern: str = ""
    direction: SearchDirection = SearchDirection.FORWARD
    last_match: SearchMatch | None = None
    case_sensitive: bool = True
    use_regex: bool = True
    wrap_search: bool = True

    def clear(self):
        """Clear the search state."""
        self.pattern = ""
        self.last_match = None


class SearchEngine:
    """Pattern matching engine for text search."""

    def __init__(self, case_sensitive: bool = True, use_regex: bool = True):
        """Initialize search engine.

        Args:
            case_sensitive: Whether searches are case-sensitive
            use_regex: Whether to use regex patterns
        """
        self.case_sensitive = case_sensitive
        self.use_regex = use_regex
        self._compiled_patterns: dict[str, re.Pattern] = {}

    def compile_pattern(self, pattern: str, case_sensitive: bool | None = None) -> re.Pattern | None:
        """Compile a search pattern to regex.

        Args:
            pattern: The search pattern
            case_sensitive: Override default case sensitivity

        Returns:
            Compiled regex pattern or None if invalid
        """
        if not pattern:
            return None

        case_sens = case_sensitive if case_sensitive is not None else self.case_sensitive

        # Create cache key
        cache_key = f"{pattern}:{case_sens}"
        if cache_key in self._compiled_patterns:
            return self._compiled_patterns[cache_key]

        try:
            flags = 0 if case_sens else re.IGNORECASE

            if self.use_regex:
                # Use pattern as-is for regex
                compiled = re.compile(pattern, flags)
            else:
                # Escape special characters for literal search
                escaped = re.escape(pattern)
                compiled = re.compile(escaped, flags)

            self._compiled_patterns[cache_key] = compiled
            return compiled

        except re.error:
            return None

    def find_all_matches(self, text: str, pattern: str, case_sensitive: bool | None = None) -> list[SearchMatch]:
        """Find all matches of pattern in text.

        Args:
            text: Text to search in
            pattern: Pattern to search for
            case_sensitive: Override case sensitivity

        Returns:
            List of all matches
        """
        regex = self.compile_pattern(pattern, case_sensitive)
        if not regex:
            return []

        matches = []
        lines = text.split("\n")

        for row, line in enumerate(lines):
            for match in regex.finditer(line):
                matches.append(SearchMatch(row=row, start_col=match.start(), end_col=match.end(), text=match.group()))

        return matches

    def find_next(
        self, lines: list[str], pattern: str, start_row: int, start_col: int, wrap: bool = True
    ) -> SearchMatch | None:
        """Find next occurrence of pattern from position.

        Args:
            lines: Buffer lines
            pattern: Pattern to search
            start_row: Starting row
            start_col: Starting column
            wrap: Whether to wrap around

        Returns:
            Next match or None
        """
        regex = self.compile_pattern(pattern)
        if not regex or not lines:
            return None

        # Search from current position to end
        for row in range(start_row, len(lines)):
            line = lines[row]
            search_start = start_col + 1 if row == start_row else 0

            match = regex.search(line, search_start)
            if match:
                return SearchMatch(row=row, start_col=match.start(), end_col=match.end(), text=match.group())

        # Wrap around if enabled
        if wrap:
            for row in range(0, start_row + 1):
                line = lines[row]
                max_col = start_col if row == start_row else len(line)

                match = regex.search(line, 0, max_col)
                if match:
                    return SearchMatch(row=row, start_col=match.start(), end_col=match.end(), text=match.group())

        return None

    def find_previous(
        self, lines: list[str], pattern: str, start_row: int, start_col: int, wrap: bool = True
    ) -> SearchMatch | None:
        """Find previous occurrence of pattern from position.

        Args:
            lines: Buffer lines
            pattern: Pattern to search
            start_row: Starting row
            start_col: Starting column
            wrap: Whether to wrap around

        Returns:
            Previous match or None
        """
        regex = self.compile_pattern(pattern)
        if not regex or not lines:
            return None

        # Search backward from current position
        for row in range(start_row, -1, -1):
            line = lines[row]

            # Find all matches in this line
            matches = list(regex.finditer(line))

            if matches:
                # Filter matches before cursor on same line
                if row == start_row:
                    matches = [m for m in matches if m.start() < start_col]

                if matches:
                    # Return the last match (closest to cursor)
                    match = matches[-1]
                    return SearchMatch(row=row, start_col=match.start(), end_col=match.end(), text=match.group())

        # Wrap around if enabled
        if wrap:
            for row in range(len(lines) - 1, start_row - 1, -1):
                line = lines[row]

                # Find all matches
                matches = list(regex.finditer(line))

                if matches:
                    # Filter matches after cursor on same line
                    if row == start_row:
                        matches = [m for m in matches if m.start() > start_col]

                    if matches:
                        match = matches[-1]
                        return SearchMatch(row=row, start_col=match.start(), end_col=match.end(), text=match.group())

        return None

    def find_word_boundaries(self, line: str, col: int) -> tuple[int, int] | None:
        """Find word boundaries at the given position.

        Args:
            line: Line of text
            col: Column position

        Returns:
            Tuple of (start, end) positions or None
        """
        if not line or col < 0 or col >= len(line):
            return None

        # Check if we're on a word character
        if not line[col].isalnum() and line[col] != "_":
            return None

        # Find start of word
        start = col
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1

        # Find end of word
        end = col
        while end < len(line) - 1 and (line[end + 1].isalnum() or line[end + 1] == "_"):
            end += 1

        return (start, end + 1)

    def escape_regex(self, text: str) -> str:
        """Escape special regex characters in text.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for regex
        """
        return re.escape(text)
