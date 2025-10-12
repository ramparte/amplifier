#!/usr/bin/env python3
"""
Insert mode implementation for vi editor.

Handles text insertion operations including:
- i,I insert at cursor/line start
- a,A append after cursor/line end
- o,O open line below/above
- Text insertion and special key handling
- Mode transitions back to command mode
"""

from buffer import Buffer


class InsertMode:
    """Handles insert mode operations for the vi editor."""

    def __init__(self, buffer: Buffer):
        """
        Initialize insert mode with a buffer.

        Args:
            buffer: The Buffer instance to operate on
        """
        self.buffer = buffer
        self.in_insert_mode = False
        self.entry_command = None  # Track how we entered insert mode

    def enter_insert_mode(self, command: str) -> bool:
        """
        Enter insert mode with the specified command.

        Args:
            command: The command that triggers insert mode (i, I, a, A, o, O)

        Returns:
            True if successfully entered insert mode, False otherwise
        """
        self.entry_command = command
        self.in_insert_mode = True

        row, col = self.buffer.cursor

        if command == "i":
            # Insert at current cursor position
            # No cursor movement needed
            return True

        if command == "I":
            # Insert at beginning of line (first non-blank character)
            self.buffer.move_cursor(row, 0)
            return True

        if command == "a":
            # Append after cursor (move cursor right by one)
            line = self.buffer.get_line(row)
            # Move cursor one position to the right (after current character)
            # But don't go past the end of the line
            new_col = min(col + 1, len(line))
            self.buffer.move_cursor(row, new_col)
            return True

        if command == "A":
            # Append at end of line
            line = self.buffer.get_line(row)
            self.buffer.move_cursor(row, len(line))
            return True

        if command == "o":
            # Open new line below current line
            # Insert empty line after current row
            self.buffer.insert_line(row + 1, "")
            # Move cursor to new line
            self.buffer.move_cursor(row + 1, 0)
            return True

        if command == "O":
            # Open new line above current line
            # Insert empty line at current row
            self.buffer.insert_line(row, "")
            # Move cursor to new line
            self.buffer.move_cursor(row, 0)
            return True

        # Unknown command, don't enter insert mode
        self.in_insert_mode = False
        self.entry_command = None
        return False

    def process_input(self, input_str: str) -> bool:
        """
        Process input while in insert mode.

        Args:
            input_str: The input to process (character, special key, or ESC)

        Returns:
            True if still in insert mode, False if exited to command mode
        """
        if not self.in_insert_mode:
            return False

        # Check for escape to exit insert mode
        if input_str == "<ESC>":
            self.exit_insert_mode()
            return False

        # Handle special keys
        if input_str == "<BS>":
            self._handle_backspace()
            return True

        if input_str == "<CR>":
            self._handle_enter()
            return True

        # Regular character insertion
        self._insert_text(input_str)
        return True

    def _insert_text(self, text: str) -> None:
        """
        Insert text at current cursor position.

        Args:
            text: Text to insert
        """
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        # Insert text at cursor position
        new_line = line[:col] + text + line[col:]
        self.buffer.modify_line(row, new_line)

        # Move cursor forward by the length of inserted text
        self.buffer.move_cursor(row, col + len(text))

    def _handle_backspace(self) -> None:
        """Handle backspace key in insert mode."""
        row, col = self.buffer.cursor

        if col > 0:
            # Delete character before cursor
            line = self.buffer.get_line(row)
            new_line = line[: col - 1] + line[col:]
            self.buffer.modify_line(row, new_line)
            # Move cursor back
            self.buffer.move_cursor(row, col - 1)
        elif row > 0:
            # At beginning of line, join with previous line
            current_line = self.buffer.get_line(row)
            prev_line = self.buffer.get_line(row - 1)

            # Combine lines
            new_line = prev_line + current_line
            self.buffer.modify_line(row - 1, new_line)

            # Delete current line
            self.buffer.delete_line(row)

            # Move cursor to join point
            self.buffer.move_cursor(row - 1, len(prev_line))

    def _handle_enter(self) -> None:
        """Handle enter key in insert mode."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        # Split line at cursor
        before = line[:col]
        after = line[col:]

        # Update current line
        self.buffer.modify_line(row, before)

        # Insert new line with remainder
        self.buffer.insert_line(row + 1, after)

        # Move cursor to beginning of new line
        self.buffer.move_cursor(row + 1, 0)

    def exit_insert_mode(self) -> None:
        """Exit insert mode and return to command mode."""
        self.in_insert_mode = False

        # Adjust cursor position if needed (vi typically moves cursor left on ESC)
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        # Move cursor left by one if not at beginning of line
        # This matches vi behavior where cursor moves left when exiting insert mode
        if col > 0 and col == len(line):
            # If at end of line, move to last character
            self.buffer.move_cursor(row, col - 1)
        elif col > 0:
            # Otherwise just ensure we're within bounds
            max_col = len(line) - 1 if line else 0
            if col > max_col:
                self.buffer.move_cursor(row, max_col)

        self.entry_command = None

    def is_in_insert_mode(self) -> bool:
        """
        Check if currently in insert mode.

        Returns:
            True if in insert mode, False otherwise
        """
        return self.in_insert_mode
