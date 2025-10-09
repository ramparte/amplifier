"""HTML/XML tag text objects for vi editor."""

import re
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


class TagTextObject(TextObject):
    """Text object for HTML/XML tags."""

    # Regular expressions for tag matching
    TAG_START_PATTERN = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)[^>]*?>")
    TAG_END_PATTERN = re.compile(r"</([a-zA-Z][a-zA-Z0-9-]*)>")
    SELF_CLOSING_PATTERN = re.compile(r"<([a-zA-Z][a-zA-Z0-9-]*)[^>]*?/>")

    def __init__(self, buffer: TextBufferProtocol):
        """Initialize tag text object."""
        super().__init__(buffer)

    def find_object_at(self, line: int, col: int, include_surrounding: bool = False) -> TextObjectRange | None:
        """Find tag-enclosed text object at position.

        Args:
            line: Current line number (0-based)
            col: Current column number (0-based)
            include_surrounding: If True, include tags ("at" mode); if False, content only ("it" mode)

        Returns:
            TextObjectRange if found, None otherwise
        """
        # Find enclosing tag pair
        tag_info = self._find_enclosing_tag(line, col)
        if not tag_info:
            return None

        open_line, open_start, open_end, close_line, close_start, close_end = tag_info

        if include_surrounding:
            # Include the tags themselves
            return TextObjectRange(open_line, open_start, close_line, close_end - 1, inclusive=True)
        # Only the content between tags
        # Handle empty tags
        if open_line == close_line and open_end >= close_start:
            return None
        return TextObjectRange(open_line, open_end, close_line, close_start - 1, inclusive=True)

    def _find_enclosing_tag(self, cursor_line: int, cursor_col: int) -> tuple[int, int, int, int, int, int] | None:
        """Find the enclosing tag pair around cursor position.

        Returns:
            Tuple of (open_line, open_start_col, open_end_col, close_line, close_start_col, close_end_col)
            or None if no enclosing tag found
        """
        # Strategy: Search backward for opening tags, then verify they enclose cursor

        # Collect all text up to and including cursor position
        search_text = []
        for line_num in range(min(cursor_line + 1, self.buffer.line_count())):
            line_text = self.buffer.get_line(line_num)
            if line_text is not None:
                if line_num == cursor_line:
                    # Include text up to and including cursor
                    search_text.append(
                        (line_num, line_text[: cursor_col + 1] if cursor_col < len(line_text) else line_text)
                    )
                else:
                    search_text.append((line_num, line_text))

        # Find all opening tags before or at cursor
        opening_tags = []
        for line_num, line_text in search_text:
            for match in self.TAG_START_PATTERN.finditer(line_text):
                tag_name = match.group(1)
                opening_tags.append((tag_name, line_num, match.start(), match.end()))

        # For each opening tag (in reverse order), find its closing tag
        for tag_name, open_line, open_start, open_end in reversed(opening_tags):
            # Skip if cursor is before the opening tag ends
            if open_line == cursor_line and open_end > cursor_col + 1:
                continue

            # Look for matching closing tag
            close_info = self._find_closing_tag(tag_name, open_line, open_end)
            if close_info:
                close_line, close_start, close_end = close_info

                # Check if cursor is inside this tag pair
                if self._is_cursor_inside_tag(cursor_line, cursor_col, open_line, open_end, close_line, close_start):
                    return (open_line, open_start, open_end, close_line, close_start, close_end)

        return None

    def _find_closing_tag(self, tag_name: str, start_line: int, start_col: int) -> tuple[int, int, int] | None:
        """Find the closing tag for a given opening tag.

        Args:
            tag_name: Name of the tag to match
            start_line: Line where opening tag ends
            start_col: Column where opening tag ends

        Returns:
            Tuple of (line, start_col, end_col) for closing tag, or None
        """
        depth = 1  # We've already seen the opening tag

        for line_num in range(start_line, self.buffer.line_count()):
            line_text = self.buffer.get_line(line_num)
            if line_text is None:
                continue

            # Determine where to start searching in this line
            search_start = start_col if line_num == start_line else 0
            search_text = line_text[search_start:]

            # Track position offset for this line
            offset = search_start

            # Find all tags in remaining text
            while search_text:
                # Look for next tag (opening or closing)
                next_open = self.TAG_START_PATTERN.search(search_text)
                next_close = self.TAG_END_PATTERN.search(search_text)

                # Determine which comes first
                if next_open and next_close:
                    if next_open.start() < next_close.start():
                        # Found opening tag first
                        if next_open.group(1) == tag_name:
                            depth += 1
                        search_text = search_text[next_open.end() :]
                        offset += next_open.end()
                    else:
                        # Found closing tag first
                        if next_close.group(1) == tag_name:
                            depth -= 1
                            if depth == 0:
                                # Found matching closing tag
                                return (line_num, offset + next_close.start(), offset + next_close.end())
                        search_text = search_text[next_close.end() :]
                        offset += next_close.end()
                elif next_close:
                    # Only closing tag found
                    if next_close.group(1) == tag_name:
                        depth -= 1
                        if depth == 0:
                            return (line_num, offset + next_close.start(), offset + next_close.end())
                    search_text = search_text[next_close.end() :]
                    offset += next_close.end()
                elif next_open:
                    # Only opening tag found
                    if next_open.group(1) == tag_name:
                        depth += 1
                    search_text = search_text[next_open.end() :]
                    offset += next_open.end()
                else:
                    # No more tags in this line
                    break

        return None

    def _is_cursor_inside_tag(
        self,
        cursor_line: int,
        cursor_col: int,
        open_line: int,
        open_end_col: int,
        close_line: int,
        close_start_col: int,
    ) -> bool:
        """Check if cursor is inside a tag pair.

        Args:
            cursor_line: Cursor line
            cursor_col: Cursor column
            open_line: Opening tag line
            open_end_col: Column where opening tag ends
            close_line: Closing tag line
            close_start_col: Column where closing tag starts

        Returns:
            True if cursor is inside the tag pair
        """
        # Check line boundaries
        if cursor_line < open_line or cursor_line > close_line:
            return False

        # Same line as opening tag
        if cursor_line == open_line:
            if cursor_line == close_line:
                # All on same line
                return open_end_col <= cursor_col <= close_start_col
            # Opening tag line, but closing is on different line
            return cursor_col >= open_end_col

        # Same line as closing tag
        if cursor_line == close_line:
            return cursor_col <= close_start_col

        # Between opening and closing lines
        return True


# Factory functions for command registration


def create_inner_tag_handler():
    """Create handler for it text object."""

    def handler(context):
        text_obj = TagTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=False)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler


def create_around_tag_handler():
    """Create handler for at text object."""

    def handler(context):
        text_obj = TagTextObject(context.buffer)
        row, col = context.buffer.get_cursor()
        range_obj = text_obj.find_object_at(row, col, include_surrounding=True)

        if range_obj:
            context.visual_start = (range_obj.start_line, range_obj.start_col)
            context.visual_end = (range_obj.end_line, range_obj.end_col)
            return True
        return False

    return handler
