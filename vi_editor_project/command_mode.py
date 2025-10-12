#!/usr/bin/env python3
"""
Command mode implementation for vi editor.

Handles navigation commands and movement operations including:
- h,j,k,l basic movement
- w,b word movement
- 0,$ line start/end
- gg,G file start/end
- Numbered movements (5j, 10l, etc.)
"""

import re

from buffer import Buffer


class CommandMode:
    """Handles command mode operations for the vi editor."""

    def __init__(self, buffer: Buffer):
        """
        Initialize command mode with a buffer.

        Args:
            buffer: The Buffer instance to operate on
        """
        self.buffer = buffer
        self.pending_count = ""  # Store numeric prefix for commands

    def process_command(self, command: str) -> bool:
        """
        Process a command mode input.

        Args:
            command: The command string to process

        Returns:
            True if command was processed successfully, False otherwise
        """
        # Check if it's a digit (accumulating count)
        if command.isdigit():
            self.pending_count += command
            return True

        # Get the repeat count (default to 1)
        count = int(self.pending_count) if self.pending_count else 1
        self.pending_count = ""  # Reset after use

        # Handle single character movements
        if command == "h":
            self._move_left(count)
            return True
        if command == "j":
            self._move_down(count)
            return True
        if command == "k":
            self._move_up(count)
            return True
        if command == "l":
            self._move_right(count)
            return True
        if command == "w":
            self._move_word_forward(count)
            return True
        if command == "b":
            self._move_word_backward(count)
            return True
        if command == "0":
            self._move_line_start()
            return True
        if command == "$":
            self._move_line_end()
            return True

        # Handle multi-character commands
        if command == "gg":
            self._move_file_start()
            return True
        if command == "G":
            self._move_file_end()
            return True

        # Handle numbered commands (e.g., "5j", "10l")
        match = re.match(r"^(\d+)([hjklwb])$", command)
        if match:
            count = int(match.group(1))
            cmd = match.group(2)

            if cmd == "h":
                self._move_left(count)
            elif cmd == "j":
                self._move_down(count)
            elif cmd == "k":
                self._move_up(count)
            elif cmd == "l":
                self._move_right(count)
            elif cmd == "w":
                self._move_word_forward(count)
            elif cmd == "b":
                self._move_word_backward(count)
            return True

        return False

    def _move_left(self, count: int = 1) -> None:
        """Move cursor left by count characters."""
        for _ in range(count):
            row, col = self.buffer.cursor
            new_col = max(0, col - 1)
            self.buffer.move_cursor(row, new_col)

    def _move_right(self, count: int = 1) -> None:
        """Move cursor right by count characters."""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)
            max_col = len(line) - 1 if line else 0
            new_col = min(max_col, col + 1)
            self.buffer.move_cursor(row, new_col)

    def _move_up(self, count: int = 1) -> None:
        """Move cursor up by count lines."""
        for _ in range(count):
            row, col = self.buffer.cursor
            new_row = max(0, row - 1)
            # Adjust column if new line is shorter
            line = self.buffer.get_line(new_row)
            max_col = len(line) - 1 if line else 0
            new_col = min(col, max_col)
            self.buffer.move_cursor(new_row, new_col)

    def _move_down(self, count: int = 1) -> None:
        """Move cursor down by count lines."""
        for _ in range(count):
            row, col = self.buffer.cursor
            new_row = min(self.buffer.line_count() - 1, row + 1)
            # Adjust column if new line is shorter
            line = self.buffer.get_line(new_row)
            max_col = len(line) - 1 if line else 0
            new_col = min(col, max_col)
            self.buffer.move_cursor(new_row, new_col)

    def _move_word_forward(self, count: int = 1) -> None:
        """Move cursor forward by count words."""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            if not line:
                # Empty line, move to next line
                if row < self.buffer.line_count() - 1:
                    self.buffer.move_cursor(row + 1, 0)
                continue

            # Skip current word (if on a word)
            while col < len(line) and not line[col].isspace() and line[col] not in ".,!?;:()[]{}":
                col += 1

            # Skip whitespace and punctuation
            while col < len(line) and (line[col].isspace() or line[col] in ".,!?;:()[]{}"):
                col += 1

            if col >= len(line):
                # Move to next line
                if row < self.buffer.line_count() - 1:
                    self.buffer.move_cursor(row + 1, 0)
                else:
                    # Stay at end of last line
                    self.buffer.move_cursor(row, len(line) - 1)
            else:
                self.buffer.move_cursor(row, col)

    def _move_word_backward(self, count: int = 1) -> None:
        """Move cursor backward by count words."""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            if not line or col == 0:
                # At beginning of line, move to previous line
                if row > 0:
                    prev_line = self.buffer.get_line(row - 1)
                    self.buffer.move_cursor(row - 1, len(prev_line) - 1 if prev_line else 0)
                continue

            # Move back one character to start
            col = max(0, col - 1)

            # Skip whitespace and punctuation backwards
            while col > 0 and (line[col].isspace() or line[col] in ".,!?;:()[]{}"):
                col -= 1

            # Move to beginning of current word
            while col > 0 and not line[col - 1].isspace() and line[col - 1] not in ".,!?;:()[]{}":
                col -= 1

            self.buffer.move_cursor(row, col)

    def _move_line_start(self) -> None:
        """Move cursor to start of current line."""
        row, _ = self.buffer.cursor
        self.buffer.move_cursor(row, 0)

    def _move_line_end(self) -> None:
        """Move cursor to end of current line."""
        row, _ = self.buffer.cursor
        line = self.buffer.get_line(row)
        end_col = len(line) - 1 if line else 0
        self.buffer.move_cursor(row, end_col)

    def _move_file_start(self) -> None:
        """Move cursor to start of file (first line, first column)."""
        self.buffer.move_cursor(0, 0)

    def _move_file_end(self) -> None:
        """Move cursor to last line of file."""
        last_row = self.buffer.line_count() - 1
        self.buffer.move_cursor(last_row, 0)
