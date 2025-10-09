"""Bracket text objects for vi editor."""

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

    def get_char_at(self, line: int, col: int) -> str | None:
        """Get character at position."""
        ...


class BracketTextObject(TextObject):
    """Base class for bracket-based text objects."""

    def __init__(self, buffer: TextBufferProtocol, open_delim: str, close_delim: str):
        """Initialize bracket text object.

        Args:
            buffer: Text buffer interface
            open_delim: Opening delimiter character
            close_delim: Closing delimiter character
        """
        super().__init__(buffer)
        self.open_delim = open_delim
        self.close_delim = close_delim

    def find_object_at(self, line: int, col: int, include_surrounding: bool = False) -> TextObjectRange | None:
        """Find bracket-enclosed text object at position.

        Args:
            line: Current line number (0-based)
            col: Current column number (0-based)
            include_surrounding: If True, include delimiters ("a" mode)

        Returns:
            TextObjectRange if found, None otherwise
        """
        # First check if we're on a delimiter
        if self._is_valid_position(line, col):
            line_text = self.buffer.get_line(line)
            if line_text and col < len(line_text):
                char = line_text[col]

                # If on opening delimiter, find closing
                if char == self.open_delim:
                    close_pos = self._find_matching_delimiter(
                        line, col, self.open_delim, self.close_delim, search_backward=False
                    )
                    if close_pos:
                        close_line, close_col = close_pos
                        if include_surrounding:
                            return TextObjectRange(line, col, close_line, close_col, inclusive=True)
                        # Inside excludes delimiters
                        start_col = col + 1
                        end_col = close_col - 1
                        # Handle empty object
                        if line == close_line and start_col > end_col:
                            return None
                        return TextObjectRange(line, start_col, close_line, end_col, inclusive=True)

                # If on closing delimiter, find opening
                elif char == self.close_delim:
                    open_pos = self._find_matching_delimiter(
                        line, col, self.open_delim, self.close_delim, search_backward=True
                    )
                    if open_pos:
                        open_line, open_col = open_pos
                        if include_surrounding:
                            return TextObjectRange(open_line, open_col, line, col, inclusive=True)
                        # Inside excludes delimiters
                        start_col = open_col + 1
                        end_col = col - 1
                        # Handle empty object
                        if open_line == line and start_col > end_col:
                            return None
                        return TextObjectRange(open_line, start_col, line, end_col, inclusive=True)

        # Not on delimiter, search for enclosing pair
        enclosing = self._find_enclosing_pair(line, col)
        if enclosing:
            open_line, open_col, close_line, close_col = enclosing
            if include_surrounding:
                return TextObjectRange(open_line, open_col, close_line, close_col, inclusive=True)
            # Inside excludes delimiters
            start_col = open_col + 1
            end_col = close_col - 1
            # Handle empty object
            if open_line == close_line and start_col > end_col:
                return None
            return TextObjectRange(open_line, start_col, close_line, end_col, inclusive=True)

        return None

    def _find_enclosing_pair(self, line: int, col: int) -> tuple[int, int, int, int] | None:
        """Find the nearest enclosing bracket pair around position.

        Args:
            line: Current line number
            col: Current column number

        Returns:
            (open_line, open_col, close_line, close_col) or None
        """
        # Search backward for opening delimiter
        open_pos = self._search_for_opening(line, col)
        if not open_pos:
            return None

        open_line, open_col = open_pos

        # Find matching closing delimiter
        close_pos = self._find_matching_delimiter(
            open_line, open_col, self.open_delim, self.close_delim, search_backward=False
        )
        if not close_pos:
            return None

        close_line, close_col = close_pos

        # Verify that cursor is inside the pair
        if self._is_position_inside(line, col, open_line, open_col, close_line, close_col):
            return (open_line, open_col, close_line, close_col)

        return None

    def _search_for_opening(self, line: int, col: int) -> tuple[int, int] | None:
        """Search backward for an unmatched opening delimiter.

        Args:
            line: Starting line
            col: Starting column

        Returns:
            (line, col) of opening delimiter or None
        """
        current_line = line
        depth = 0

        while current_line >= 0:
            line_text = self.buffer.get_line(current_line)
            if not line_text:
                current_line -= 1
                continue

            # Set search range for this line
            if current_line == line:
                start_col = col
            else:
                start_col = len(line_text) - 1

            # Search backward through line
            for c in range(start_col, -1, -1):
                char = line_text[c]

                if char == self.close_delim:
                    depth += 1
                elif char == self.open_delim:
                    if depth == 0:
                        # Found unmatched opening delimiter
                        return (current_line, c)
                    depth -= 1

            current_line -= 1

        return None

    def _is_position_inside(
        self, line: int, col: int, open_line: int, open_col: int, close_line: int, close_col: int
    ) -> bool:
        """Check if position is inside the given bracket pair.

        Args:
            line: Position line
            col: Position column
            open_line: Opening bracket line
            open_col: Opening bracket column
            close_line: Closing bracket line
            close_col: Closing bracket column

        Returns:
            True if position is inside the bracket pair
        """
        # Check line boundaries
        if line < open_line or line > close_line:
            return False

        # Check column boundaries for same-line brackets
        if open_line == close_line:
            return open_col <= col <= close_col

        # Check column for opening line
        if line == open_line:
            return col >= open_col

        # Check column for closing line
        if line == close_line:
            return col <= close_col

        # Position is on a line between opening and closing
        return True


# Concrete implementations for specific bracket types


class ParenthesesTextObject(BracketTextObject):
    """Text object for parentheses ()."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize parentheses text object."""
        super().__init__(buffer, "(", ")")


class SquareBracketsTextObject(BracketTextObject):
    """Text object for square brackets []."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize square brackets text object."""
        super().__init__(buffer, "[", "]")


class CurlyBracesTextObject(BracketTextObject):
    """Text object for curly braces {}."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize curly braces text object."""
        super().__init__(buffer, "{", "}")


class AngleBracketsTextObject(BracketTextObject):
    """Text object for angle brackets <>."""

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize angle brackets text object."""
        super().__init__(buffer, "<", ">")


# Factory functions for command registration


def create_inner_parentheses_handler():
    """Create handler for i( text object."""

    def handler(context):
        text_obj = ParenthesesTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            # Set visual selection for operator
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_parentheses_handler():
    """Create handler for a( text object."""

    def handler(context):
        text_obj = ParenthesesTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            # Set visual selection for operator
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_inner_square_brackets_handler():
    """Create handler for i[ text object."""

    def handler(context):
        text_obj = SquareBracketsTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_square_brackets_handler():
    """Create handler for a[ text object."""

    def handler(context):
        text_obj = SquareBracketsTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_inner_curly_braces_handler():
    """Create handler for i{ and iB text objects."""

    def handler(context):
        text_obj = CurlyBracesTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_curly_braces_handler():
    """Create handler for a{ and aB text objects."""

    def handler(context):
        text_obj = CurlyBracesTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_inner_angle_brackets_handler():
    """Create handler for i< text object."""

    def handler(context):
        text_obj = AngleBracketsTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_angle_brackets_handler():
    """Create handler for a< text object."""

    def handler(context):
        text_obj = AngleBracketsTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler
