"""Text buffer implementation using gap buffer algorithm.

The gap buffer is an efficient data structure for text editors that provides:
- O(1) insertion/deletion at cursor position
- O(n) movement to arbitrary positions
- Efficient memory usage for large files
"""


class GapBuffer:
    """Gap buffer implementation for efficient text editing."""

    def __init__(self, initial_text: str = ""):
        """Initialize buffer with optional initial text."""
        self.text = list(initial_text)
        self.gap_start = 0
        self.gap_end = 0
        self.size = len(initial_text)

        # Create initial gap at the beginning
        gap_size = max(100, len(initial_text) // 10)  # 10% of text or 100 chars
        self.text = [""] * gap_size + self.text
        self.gap_end = gap_size

    def _expand_gap(self, new_size: int = 100):
        """Expand the gap when it becomes too small."""
        new_gap = [""] * new_size
        self.text = self.text[: self.gap_start] + new_gap + self.text[self.gap_end :]
        self.gap_end = self.gap_start + new_size

    def _move_gap_to(self, position: int):
        """Move gap to specified position."""
        if position < 0:
            position = 0
        if position > self.size:
            position = self.size

        if position < self.gap_start:
            # Move text after gap to before gap
            delta = self.gap_start - position
            self.text[self.gap_end - delta : self.gap_end] = self.text[position : self.gap_start]
            self.gap_start = position
            self.gap_end -= delta
        elif position > self.gap_start:
            # Move text before gap to after gap
            delta = position - self.gap_start
            self.text[self.gap_start : self.gap_start + delta] = self.text[self.gap_end : self.gap_end + delta]
            self.gap_start = position
            self.gap_end += delta

    def insert(self, position: int, text: str):
        """Insert text at the specified position."""
        self._move_gap_to(position)

        # Expand gap if necessary
        if len(text) > self.gap_end - self.gap_start:
            self._expand_gap(len(text) + 100)

        # Insert text
        for char in text:
            self.text[self.gap_start] = char
            self.gap_start += 1
            self.size += 1

    def delete(self, position: int, length: int) -> str:
        """Delete characters starting from position."""
        if position < 0 or position >= self.size:
            return ""

        self._move_gap_to(position)

        # Calculate actual deletion length
        actual_length = min(length, self.size - position)

        # Save deleted text
        deleted = "".join(self.text[self.gap_end : self.gap_end + actual_length])

        # Expand gap to delete
        self.gap_end += actual_length
        self.size -= actual_length

        return deleted

    def get_text(self) -> str:
        """Get the entire buffer text."""
        return "".join(self.text[: self.gap_start] + self.text[self.gap_end :])

    def get_char(self, position: int) -> str | None:
        """Get character at position."""
        if position < 0 or position >= self.size:
            return None

        if position < self.gap_start:
            return self.text[position]
        return self.text[position + (self.gap_end - self.gap_start)]


class Buffer:
    """High-level text buffer with line management."""

    def __init__(self, initial_text: str = ""):
        """Initialize buffer."""
        self.gap_buffer = GapBuffer(initial_text)
        self._line_cache = None
        self._line_cache_valid = False

    def _invalidate_line_cache(self):
        """Invalidate the line cache."""
        self._line_cache_valid = False

    def _rebuild_line_cache(self):
        """Rebuild the line cache."""
        text = self.gap_buffer.get_text()
        self._line_cache = text.split("\n")
        self._line_cache_valid = True

    def get_lines(self) -> list[str]:
        """Get all lines in the buffer."""
        if not self._line_cache_valid:
            self._rebuild_line_cache()
        assert self._line_cache is not None
        return self._line_cache.copy()

    def get_line(self, line_num: int) -> str | None:
        """Get a specific line."""
        lines = self.get_lines()
        if 0 <= line_num < len(lines):
            return lines[line_num]
        return None

    def get_line_count(self) -> int:
        """Get the number of lines."""
        return len(self.get_lines())

    def insert(self, line: int, col: int, text: str):
        """Insert text at line:col position."""
        position = self._get_position(line, col)
        if position is not None:
            self.gap_buffer.insert(position, text)
            self._invalidate_line_cache()

    def delete(self, line: int, col: int, length: int) -> str:
        """Delete characters from line:col position."""
        position = self._get_position(line, col)
        if position is not None:
            deleted = self.gap_buffer.delete(position, length)
            self._invalidate_line_cache()
            return deleted
        return ""

    def _get_position(self, line: int, col: int) -> int | None:
        """Convert line:col to absolute position."""
        lines = self.get_lines()
        if line < 0 or line >= len(lines):
            return None

        position = sum(len(line_text) + 1 for line_text in lines[:line])  # +1 for newlines
        position += min(col, len(lines[line]))
        return position

    def get_text(self) -> str:
        """Get the entire buffer text."""
        return self.gap_buffer.get_text()

    def set_text(self, text: str):
        """Replace entire buffer content."""
        self.gap_buffer = GapBuffer(text)
        self._invalidate_line_cache()

    def search(self, pattern: str, start_line: int = 0, start_col: int = 0) -> tuple[int, int] | None:
        """Search for pattern in buffer, returns (line, col) or None."""
        lines = self.get_lines()

        for line_num in range(start_line, len(lines)):
            line = lines[line_num]
            search_start = start_col if line_num == start_line else 0

            pos = line.find(pattern, search_start)
            if pos != -1:
                return (line_num, pos)

        return None
