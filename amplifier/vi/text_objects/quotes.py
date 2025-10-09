"""Quote text objects for vi editor."""

from typing import Protocol

from amplifier.vi.text_objects.base import TextObject
from amplifier.vi.text_objects.base import TextObjectRange


class TextBufferProtocol(Protocol):
    """Protocol for text buffer interface."""

    def get_line(self, line_num: int) -> str | None:
        """Get a line by number."""
        ...

    def line_count(self) -> int:
        """Get total number of lines."""
        ...


class QuoteTextObject(TextObject):
    """Base class for quote-based text objects."""

    def __init__(self, buffer: TextBufferProtocol, quote_char: str):
        """Initialize quote text object.

        Args:
            buffer: Text buffer interface
            quote_char: Quote character (", ', or `)
        """
        super().__init__(buffer)
        self.quote_char = quote_char

    def find_object_at(self, line: int, col: int, include_surrounding: bool = False) -> TextObjectRange | None:
        """Find quote-enclosed text object at position.

        Args:
            line: Current line number (0-based)
            col: Current column number (0-based)
            include_surrounding: If True, include quotes ("a" mode)

        Returns:
            TextObjectRange if found, None otherwise
        """
        line_text = self.buffer.get_line(line)
        if not line_text:
            return None

        # Check if we're on a quote
        if col < len(line_text) and line_text[col] == self.quote_char:
            # On opening quote - find closing
            if self._is_opening_quote(line_text, col):
                close_col = self._find_closing_quote(line_text, col)
                if close_col is not None:
                    if include_surrounding:
                        return TextObjectRange(line, col, line, close_col, inclusive=True)
                    if close_col > col + 1:  # Has content
                        return TextObjectRange(line, col + 1, line, close_col - 1, inclusive=True)
                    return None

            # On closing quote - find opening
            elif self._is_closing_quote(line_text, col):
                open_col = self._find_opening_quote(line_text, col)
                if open_col is not None:
                    if include_surrounding:
                        return TextObjectRange(line, open_col, line, col, inclusive=True)
                    if col > open_col + 1:  # Has content
                        return TextObjectRange(line, open_col + 1, line, col - 1, inclusive=True)
                    return None

        # Not on quote, find enclosing quotes
        quote_pair = self._find_enclosing_quotes(line_text, col)
        if quote_pair:
            open_col, close_col = quote_pair
            if include_surrounding:
                return TextObjectRange(line, open_col, line, close_col, inclusive=True)
            if close_col > open_col + 1:  # Has content
                return TextObjectRange(line, open_col + 1, line, close_col - 1, inclusive=True)

        return None

    def _is_opening_quote(self, line_text: str, col: int) -> bool:
        """Check if quote at position is an opening quote.

        Args:
            line_text: Line text
            col: Column position of quote

        Returns:
            True if this is likely an opening quote
        """
        if col >= len(line_text) or line_text[col] != self.quote_char:
            return False

        # Count quotes before this position
        quotes_before = 0
        for i in range(col):
            if line_text[i] == self.quote_char and not self._is_escaped(line_text, i):
                quotes_before += 1

        # Even number of quotes before = this is opening
        return quotes_before % 2 == 0

    def _is_closing_quote(self, line_text: str, col: int) -> bool:
        """Check if quote at position is a closing quote.

        Args:
            line_text: Line text
            col: Column position of quote

        Returns:
            True if this is likely a closing quote
        """
        if col >= len(line_text) or line_text[col] != self.quote_char:
            return False

        # Count quotes before this position
        quotes_before = 0
        for i in range(col):
            if line_text[i] == self.quote_char and not self._is_escaped(line_text, i):
                quotes_before += 1

        # Odd number of quotes before = this is closing
        return quotes_before % 2 == 1

    def _find_closing_quote(self, line_text: str, start_col: int) -> int | None:
        """Find closing quote from opening quote position.

        Args:
            line_text: Line text
            start_col: Column of opening quote

        Returns:
            Column of closing quote or None
        """
        for i in range(start_col + 1, len(line_text)):
            if line_text[i] == self.quote_char and not self._is_escaped(line_text, i):
                return i
        return None

    def _find_opening_quote(self, line_text: str, end_col: int) -> int | None:
        """Find opening quote from closing quote position.

        Args:
            line_text: Line text
            end_col: Column of closing quote

        Returns:
            Column of opening quote or None
        """
        for i in range(end_col - 1, -1, -1):
            if line_text[i] == self.quote_char and not self._is_escaped(line_text, i):
                # Check if this forms a valid pair
                close = self._find_closing_quote(line_text, i)
                if close == end_col:
                    return i
        return None

    def _find_enclosing_quotes(self, line_text: str, col: int) -> tuple[int, int] | None:
        """Find quotes enclosing the cursor position.

        Args:
            line_text: Line text
            col: Cursor column

        Returns:
            (open_col, close_col) or None
        """
        # Find all quote pairs in the line
        pairs = self._find_all_quote_pairs(line_text)

        # Find the innermost pair containing cursor
        for open_col, close_col in pairs:
            if open_col < col < close_col:
                return (open_col, close_col)

        # Check if cursor is right after a closing quote (for 'a' commands)
        if col > 0 and col <= len(line_text):
            for open_col, close_col in pairs:
                if close_col == col - 1:
                    return (open_col, close_col)

        return None

    def _find_all_quote_pairs(self, line_text: str) -> list[tuple[int, int]]:
        """Find all valid quote pairs in a line.

        Args:
            line_text: Line text

        Returns:
            List of (open_col, close_col) tuples
        """
        pairs = []
        i = 0

        while i < len(line_text):
            if line_text[i] == self.quote_char and not self._is_escaped(line_text, i):
                # Found opening quote, look for closing
                close = self._find_closing_quote(line_text, i)
                if close is not None:
                    pairs.append((i, close))
                    i = close + 1
                else:
                    i += 1
            else:
                i += 1

        return pairs

    def _is_escaped(self, line_text: str, col: int) -> bool:
        """Check if character at position is escaped.

        Args:
            line_text: Line text
            col: Column position

        Returns:
            True if character is escaped
        """
        if col == 0:
            return False

        # Count consecutive backslashes before position
        backslash_count = 0
        i = col - 1
        while i >= 0 and line_text[i] == "\\":
            backslash_count += 1
            i -= 1

        # Odd number of backslashes means escaped
        return backslash_count % 2 == 1


# Concrete implementations for specific quote types


class DoubleQuoteTextObject(QuoteTextObject):
    """Text object for double quotes."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize double quote text object."""
        super().__init__(buffer, '"')


class SingleQuoteTextObject(QuoteTextObject):
    """Text object for single quotes."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize single quote text object."""
        super().__init__(buffer, "'")


class BacktickTextObject(QuoteTextObject):
    """Text object for backticks."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize backtick text object."""
        super().__init__(buffer, "`")


# Factory functions for command registration


def create_inner_double_quotes_handler():
    """Create handler for i" text object."""

    def handler(context):
        text_obj = DoubleQuoteTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_double_quotes_handler():
    """Create handler for a" text object."""

    def handler(context):
        text_obj = DoubleQuoteTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_inner_single_quotes_handler():
    """Create handler for i' text object."""

    def handler(context):
        text_obj = SingleQuoteTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_single_quotes_handler():
    """Create handler for a' text object."""

    def handler(context):
        text_obj = SingleQuoteTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_inner_backticks_handler():
    """Create handler for i` text object."""

    def handler(context):
        text_obj = BacktickTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_backticks_handler():
    """Create handler for a` text object."""

    def handler(context):
        text_obj = BacktickTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler
