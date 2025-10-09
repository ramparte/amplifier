"""Word movement commands (w, W, e, E, b, B) for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


class WordMovements:
    """Implements word movement commands."""

    def __init__(self, buffer: "TextBuffer"):
        """Initialize with buffer reference."""
        self.buffer = buffer

    def word_forward(self, count: int = 1, big_word: bool = False) -> bool:
        """Move forward by words (w/W commands).

        Args:
            count: Number of words to move
            big_word: If True, use WORD (non-whitespace) boundaries

        Returns:
            True if movement executed
        """
        for _ in range(count):
            row, col = self.buffer.get_cursor()
            if row >= len(self.buffer.lines):
                break

            line = self.buffer.lines[row]

            if big_word:
                # Skip current WORD (non-whitespace)
                while col < len(line) and not line[col].isspace():
                    col += 1
                # Skip whitespace
                while col < len(line) and line[col].isspace():
                    col += 1
            else:
                # Skip current word (alphanumeric/underscore)
                if col < len(line) and (line[col].isalnum() or line[col] == "_"):
                    while col < len(line) and (line[col].isalnum() or line[col] == "_"):
                        col += 1
                # Skip punctuation
                elif col < len(line) and not line[col].isspace():
                    while col < len(line) and not line[col].isspace() and not line[col].isalnum() and line[col] != "_":
                        col += 1
                # Skip whitespace
                while col < len(line) and line[col].isspace():
                    col += 1

            # Move to next line if at end
            if col >= len(line) and row < len(self.buffer.lines) - 1:
                row += 1
                col = 0
                # Skip leading whitespace on new line
                if row < len(self.buffer.lines):
                    line = self.buffer.lines[row]
                    while col < len(line) and line[col].isspace():
                        col += 1

            self.buffer.set_cursor(row, col)
        return True

    def word_backward(self, count: int = 1, big_word: bool = False) -> bool:
        """Move backward by words (b/B commands).

        Args:
            count: Number of words to move
            big_word: If True, use WORD (non-whitespace) boundaries

        Returns:
            True if movement executed
        """
        for _ in range(count):
            row, col = self.buffer.get_cursor()

            # Move back one position first
            if col > 0:
                col -= 1
            elif row > 0:
                row -= 1
                col = len(self.buffer.lines[row]) if row < len(self.buffer.lines) else 0

            if row < len(self.buffer.lines) and col > 0:
                line = self.buffer.lines[row]

                if big_word:
                    # Skip whitespace backwards
                    while col > 0 and col < len(line) and line[col].isspace():
                        col -= 1
                    # Skip WORD backwards
                    while col > 0 and not line[col - 1].isspace():
                        col -= 1
                else:
                    # Skip whitespace backwards
                    while col > 0 and col < len(line) and line[col].isspace():
                        col -= 1

                    # Determine word type at current position
                    if col < len(line):
                        if line[col].isalnum() or line[col] == "_":
                            # Skip alphanumeric word backwards
                            while col > 0 and (line[col - 1].isalnum() or line[col - 1] == "_"):
                                col -= 1
                        else:
                            # Skip punctuation backwards
                            while (
                                col > 0
                                and not line[col - 1].isspace()
                                and not line[col - 1].isalnum()
                                and line[col - 1] != "_"
                            ):
                                col -= 1

            self.buffer.set_cursor(row, col)
        return True

    def word_end_forward(self, count: int = 1, big_word: bool = False) -> bool:
        """Move to end of word (e/E commands).

        Args:
            count: Number of word ends to move to
            big_word: If True, use WORD (non-whitespace) boundaries

        Returns:
            True if movement executed
        """
        for _ in range(count):
            row, col = self.buffer.get_cursor()
            if row >= len(self.buffer.lines):
                break

            line = self.buffer.lines[row]

            # Move forward one if not at end of line
            if col < len(line) - 1:
                col += 1
            elif row < len(self.buffer.lines) - 1:
                # Move to next line
                row += 1
                col = 0
                line = self.buffer.lines[row]

            if big_word:
                # Skip whitespace forward
                while col < len(line) and line[col].isspace():
                    col += 1
                    if col >= len(line) and row < len(self.buffer.lines) - 1:
                        row += 1
                        col = 0
                        line = self.buffer.lines[row]

                # Move to end of WORD
                while col < len(line) - 1 and not line[col + 1].isspace():
                    col += 1
            else:
                # Skip whitespace forward
                while col < len(line) and line[col].isspace():
                    col += 1
                    if col >= len(line) and row < len(self.buffer.lines) - 1:
                        row += 1
                        col = 0
                        line = self.buffer.lines[row]

                # Move to end of word based on type
                if col < len(line):
                    if line[col].isalnum() or line[col] == "_":
                        # Move to end of alphanumeric word
                        while col < len(line) - 1 and (line[col + 1].isalnum() or line[col + 1] == "_"):
                            col += 1
                    else:
                        # Move to end of punctuation sequence
                        while (
                            col < len(line) - 1
                            and not line[col + 1].isspace()
                            and not line[col + 1].isalnum()
                            and line[col + 1] != "_"
                        ):
                            col += 1

            self.buffer.set_cursor(row, col)
        return True
