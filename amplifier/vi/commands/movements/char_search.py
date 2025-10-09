"""Character search movement commands (f, F, t, T, ;, ,) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class CharSearchMovements:
    """Implements character search movement commands."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize with buffer reference."""
        self.buffer = buffer
        self.last_search_char: str | None = None
        self.last_search_forward: bool = True
        self.last_search_till: bool = False

    def find_char_forward(self, char: str, count: int = 1, till: bool = False) -> bool:
        """Find character forward in line (f/t commands).

        Args:
            char: Character to search for
            count: Number of occurrences to find
            till: If True, stop before the character (t command)

        Returns:
            True if character was found
        """
        # Save search state for repeat
        self.last_search_char = char
        self.last_search_forward = True
        self.last_search_till = till

        found = False
        for _ in range(count):
            if not self.buffer.find_char_forward(char, till):
                break
            found = True
        return found

    def find_char_backward(self, char: str, count: int = 1, till: bool = False) -> bool:
        """Find character backward in line (F/T commands).

        Args:
            char: Character to search for
            count: Number of occurrences to find
            till: If True, stop after the character (T command)

        Returns:
            True if character was found
        """
        # Save search state for repeat
        self.last_search_char = char
        self.last_search_forward = False
        self.last_search_till = till

        found = False
        for _ in range(count):
            if not self.buffer.find_char_backward(char, till):
                break
            found = True
        return found

    def repeat_search(self, count: int = 1) -> bool:
        """Repeat last character search (; command).

        Args:
            count: Number of times to repeat

        Returns:
            True if search was repeated successfully
        """
        if self.last_search_char is None:
            return False

        if self.last_search_forward:
            return self.find_char_forward(self.last_search_char, count, self.last_search_till)
        return self.find_char_backward(self.last_search_char, count, self.last_search_till)

    def repeat_search_reverse(self, count: int = 1) -> bool:
        """Repeat last character search in opposite direction (, command).

        Args:
            count: Number of times to repeat

        Returns:
            True if search was repeated successfully
        """
        if self.last_search_char is None:
            return False

        # Reverse the direction
        if self.last_search_forward:
            return self.find_char_backward(self.last_search_char, count, self.last_search_till)
        return self.find_char_forward(self.last_search_char, count, self.last_search_till)
