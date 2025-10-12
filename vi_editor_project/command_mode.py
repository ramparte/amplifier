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
from insert_mode import InsertMode


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
        self.pending_command = ""  # Store partial commands like 'd' or 'y' waiting for motion
        self.yank_buffer = ""  # Store yanked/deleted text for paste operations
        self.yank_type = "char"  # Type of yank: "char" or "line"
        self.insert_mode = InsertMode(buffer)  # Handle insert mode operations
        self.replace_mode = False  # Track if in replace mode
        self.mode = "command"  # Track current mode: "command", "insert", "replace"

    def process_command(self, command: str) -> bool:
        """
        Process a command mode input.

        Args:
            command: The command string to process

        Returns:
            True if command was processed successfully, False otherwise
        """
        # Handle mode-specific processing
        if self.mode == "insert":
            if command == "\x1b" or command == "<ESC>":  # ESC key
                self.exit_insert_mode()
                return True
            self.insert_text(command)
            return True

        if self.mode == "replace":
            if command == "\x1b" or command == "<ESC>":  # ESC key
                self.exit_replace_mode()
                return True
            self.replace_text(command)
            return True

        # Check if waiting for a character for 'r' command
        if self.pending_command == "r":
            self._replace_char(command, int(self.pending_count) if self.pending_count else 1)
            self.pending_command = ""
            self.pending_count = ""
            return True

        # Check if waiting for motion for 'c' command
        if self.pending_command == "c":
            result = self._handle_change_motion(command, int(self.pending_count) if self.pending_count else 1)
            self.pending_command = ""
            self.pending_count = ""
            return result

        # Check if it's a digit (accumulating count)
        if command.isdigit() and not self.pending_command:
            self.pending_count += command
            return True

        # Get the repeat count (default to 1)
        count = int(self.pending_count) if self.pending_count else 1

        # Handle pending delete command with motion
        if self.pending_command == "d":
            result = self._handle_delete_motion(command, count)
            self.pending_command = ""  # Clear pending command
            self.pending_count = ""  # Reset count
            return result

        # Handle pending yank command with motion
        if self.pending_command == "y":
            result = self._handle_yank_motion(command, count)
            self.pending_command = ""  # Clear pending command
            self.pending_count = ""  # Reset count
            return result

        # Reset count after use for non-pending commands
        self.pending_count = ""

        # Handle yank commands
        if command == "y":
            # Start a yank command, wait for motion
            self.pending_command = "y"
            return True
        if command == "Y":
            # Yank entire line (synonym for yy)
            self._yank_lines(count)
            return True

        # Handle delete commands
        if command == "d":
            # Start a delete command, wait for motion
            self.pending_command = "d"
            return True
        if command == "x":
            # Delete character under cursor
            self._delete_char(count)
            return True
        if command == "X":
            # Delete character before cursor
            self._delete_char_before(count)
            return True
        if command == "D":
            # Delete from cursor to end of line
            self._delete_to_end_of_line()
            return True

        # Handle paste commands
        if command == "p":
            # Paste after cursor/line
            self._paste_after(count)
            return True
        if command == "P":
            # Paste before cursor/line
            self._paste_before(count)
            return True

        # Handle replace commands
        if command == "r":
            # Replace single character (wait for next char)
            self.pending_command = "r"
            return True
        if command == "R":
            # Enter replace mode
            self.mode = "replace"
            return True
        if command == "s":
            # Substitute character(s) - delete and enter insert mode
            self._delete_char(count)
            self.mode = "insert"
            return True
        if command == "S":
            # Substitute entire line
            self._delete_lines(1)
            self.buffer.insert_line(self.buffer.cursor[0], "")
            self.buffer.move_cursor(self.buffer.cursor[0], 0)
            self.mode = "insert"
            return True
        if command == "c":
            # Start change command (wait for motion)
            self.pending_command = "c"
            return True
        if command == "C":
            # Change to end of line
            self._delete_to_end_of_line()
            self.mode = "insert"
            return True
        if command == "~":
            # Toggle case of character under cursor
            self._toggle_case(count)
            return True

        # Handle insert mode commands
        if command == "i":
            # Enter insert mode at cursor
            self.mode = "insert"
            self.insert_mode.enter_insert_mode("i")
            return True
        if command == "I":
            # Enter insert mode at beginning of line
            self.mode = "insert"
            self.insert_mode.enter_insert_mode("I")
            return True
        if command == "a":
            # Enter insert mode after cursor
            self.mode = "insert"
            self.insert_mode.enter_insert_mode("a")
            return True
        if command == "A":
            # Enter insert mode at end of line
            self.mode = "insert"
            self.insert_mode.enter_insert_mode("A")
            return True
        if command == "o":
            # Open line below
            self.mode = "insert"
            self.insert_mode.enter_insert_mode("o")
            return True
        if command == "O":
            # Open line above
            self.mode = "insert"
            self.insert_mode.enter_insert_mode("O")
            return True

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

    def _handle_delete_motion(self, motion: str, count: int) -> bool:
        """
        Handle delete command with motion.

        Args:
            motion: The motion command (e.g., 'd' for line, 'w' for word, etc.)
            count: Number of times to repeat the operation

        Returns:
            True if motion was valid, False otherwise
        """
        if motion == "d":
            # dd - delete entire line(s)
            self._delete_lines(count)
            return True
        if motion == "w":
            # dw - delete word(s) forward
            self._delete_word_forward(count)
            return True
        if motion == "b":
            # db - delete word(s) backward
            self._delete_word_backward(count)
            return True
        if motion == "$":
            # d$ - delete to end of line
            self._delete_to_end_of_line()
            return True
        if motion == "0":
            # d0 - delete to beginning of line
            self._delete_to_beginning_of_line()
            return True
        if motion == "j":
            # dj - delete current and next line
            self._delete_lines(count + 1)  # Current + count lines down
            return True
        if motion == "k":
            # dk - delete current and previous line
            # Move up first, then delete
            row, col = self.buffer.cursor
            new_row = max(0, row - count)
            self.buffer.move_cursor(new_row, 0)
            self._delete_lines(count + 1)  # Delete from new position
            return True

        return False

    def _delete_char(self, count: int = 1) -> None:
        """Delete character(s) under cursor."""
        deleted_text = ""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            # Only delete if there's a character to delete
            if col < len(line):
                deleted_text += line[col]  # Save deleted character
                self.buffer.delete_char(row, col)
                # Adjust cursor if at end of line after deletion
                new_line = self.buffer.get_line(row)
                if col >= len(new_line) and len(new_line) > 0:
                    self.buffer.move_cursor(row, len(new_line) - 1)

        if deleted_text:
            self.yank_buffer = deleted_text
            self.yank_type = "char"

    def _delete_char_before(self, count: int = 1) -> None:
        """Delete character(s) before cursor (X command)."""
        for _ in range(count):
            row, col = self.buffer.cursor
            if col > 0:
                # Move cursor back and delete
                self.buffer.move_cursor(row, col - 1)
                self.buffer.delete_char(row, col - 1)

    def _delete_lines(self, count: int = 1) -> None:
        """Delete entire line(s) at cursor."""
        deleted_lines = []
        start_row = self.buffer.cursor[0]

        for i in range(count):
            row = self.buffer.cursor[0]
            if row < self.buffer.line_count():
                deleted_lines.append(self.buffer.get_line(row))
                self.buffer.delete_line(row)
                # Cursor position is adjusted by Buffer.delete_line()

        if deleted_lines:
            self.yank_buffer = "\n".join(deleted_lines)
            self.yank_type = "line"

    def _delete_word_forward(self, count: int = 1) -> None:
        """Delete from cursor to beginning of next word."""
        deleted_text = ""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            if not line:
                # Empty line, delete it
                if row < self.buffer.line_count() - 1:
                    self.buffer.delete_line(row)
                continue

            start_col = col

            # Find end of deletion (beginning of next word or end of line)
            while col < len(line) and not line[col].isspace():
                col += 1
            while col < len(line) and line[col].isspace():
                col += 1

            # Delete from start_col to col
            if col > start_col:
                deleted_text += line[start_col:col]
                new_line = line[:start_col] + line[col:]
                self.buffer.modify_line(row, new_line)

        if deleted_text:
            self.yank_buffer = deleted_text
            self.yank_type = "char"

    def _delete_word_backward(self, count: int = 1) -> None:
        """Delete from cursor backward to beginning of word."""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            if col == 0:
                continue

            end_col = col

            # Move backward to beginning of word
            col = col - 1
            while col > 0 and line[col].isspace():
                col -= 1
            while col > 0 and not line[col - 1].isspace():
                col -= 1

            # Delete from col to end_col
            new_line = line[:col] + line[end_col:]
            self.buffer.modify_line(row, new_line)
            self.buffer.move_cursor(row, col)

    def _delete_to_end_of_line(self) -> None:
        """Delete from cursor to end of line (D or d$ command)."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        if col < len(line):
            new_line = line[:col]
            self.buffer.modify_line(row, new_line)
            # Move cursor back if it's beyond the new line end
            if col > 0 and col >= len(new_line):
                self.buffer.move_cursor(row, len(new_line) - 1)

    def _delete_to_beginning_of_line(self) -> None:
        """Delete from cursor to beginning of line (d0 command)."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        if col > 0:
            new_line = line[col:]
            self.buffer.modify_line(row, new_line)
            self.buffer.move_cursor(row, 0)

    def _handle_yank_motion(self, motion: str, count: int) -> bool:
        """
        Handle yank command with motion.

        Args:
            motion: The motion command (e.g., 'y' for line, 'w' for word, etc.)
            count: Number of times to repeat the operation

        Returns:
            True if motion was valid, False otherwise
        """
        if motion == "y":
            # yy - yank entire line(s)
            self._yank_lines(count)
            return True
        if motion == "w":
            # yw - yank word(s) forward
            self._yank_word_forward(count)
            return True
        if motion == "b":
            # yb - yank word(s) backward
            self._yank_word_backward(count)
            return True
        if motion == "$":
            # y$ - yank to end of line
            self._yank_to_end_of_line()
            return True
        if motion == "0":
            # y0 - yank to beginning of line
            self._yank_to_beginning_of_line()
            return True

        return False

    def _yank_lines(self, count: int = 1) -> None:
        """Yank entire line(s) at cursor."""
        yanked_lines = []
        row = self.buffer.cursor[0]

        for i in range(count):
            if row + i < self.buffer.line_count():
                yanked_lines.append(self.buffer.get_line(row + i))

        if yanked_lines:
            self.yank_buffer = "\n".join(yanked_lines)
            self.yank_type = "line"

    def _yank_word_forward(self, count: int = 1) -> None:
        """Yank from cursor to beginning of next word."""
        yanked_text = ""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        for _ in range(count):
            if not line or col >= len(line):
                break

            start_col = col

            # Find end of word
            while col < len(line) and not line[col].isspace():
                col += 1
            while col < len(line) and line[col].isspace():
                col += 1

            yanked_text += line[start_col:col]

        if yanked_text:
            self.yank_buffer = yanked_text
            self.yank_type = "char"

    def _yank_word_backward(self, count: int = 1) -> None:
        """Yank from cursor backward to beginning of word."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        if col == 0:
            return

        end_col = col
        col = col - 1

        # Move backward to beginning of word
        while col > 0 and line[col].isspace():
            col -= 1
        while col > 0 and not line[col - 1].isspace():
            col -= 1

        yanked_text = line[col:end_col]
        if yanked_text:
            self.yank_buffer = yanked_text
            self.yank_type = "char"

    def _yank_to_end_of_line(self) -> None:
        """Yank from cursor to end of line."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        if col < len(line):
            self.yank_buffer = line[col:]
            self.yank_type = "char"

    def _yank_to_beginning_of_line(self) -> None:
        """Yank from cursor to beginning of line."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        if col > 0:
            self.yank_buffer = line[:col]
            self.yank_type = "char"

    def _paste_after(self, count: int = 1) -> None:
        """Paste yanked text after cursor/line."""
        if not self.yank_buffer:
            return

        row, col = self.buffer.cursor

        if self.yank_type == "line":
            # Paste entire lines after current line
            for _ in range(count):
                for i, line in enumerate(self.yank_buffer.split("\n")):
                    self.buffer.insert_line(row + 1 + i, line)
                    row = row + 1
        else:
            # Paste characters after cursor
            line = self.buffer.get_line(row)
            insert_pos = min(col + 1, len(line))
            repeated_text = self.yank_buffer * count
            new_line = line[:insert_pos] + repeated_text + line[insert_pos:]
            self.buffer.modify_line(row, new_line)
            # Move cursor to end of pasted text
            self.buffer.move_cursor(row, insert_pos + len(repeated_text) - 1)

    def _paste_before(self, count: int = 1) -> None:
        """Paste yanked text before cursor/line."""
        if not self.yank_buffer:
            return

        row, col = self.buffer.cursor

        if self.yank_type == "line":
            # Paste entire lines before current line
            for _ in range(count):
                for i, line in enumerate(self.yank_buffer.split("\n")):
                    self.buffer.insert_line(row + i, line)
                    row = row + 1
        else:
            # Paste characters before cursor
            line = self.buffer.get_line(row)
            repeated_text = self.yank_buffer * count
            new_line = line[:col] + repeated_text + line[col:]
            self.buffer.modify_line(row, new_line)
            # Move cursor to end of pasted text
            self.buffer.move_cursor(row, col + len(repeated_text) - 1)

    def _handle_change_motion(self, motion: str, count: int) -> bool:
        """
        Handle change command with motion.

        Args:
            motion: The motion command (e.g., 'c' for line, 'w' for word, etc.)
            count: Number of times to repeat the operation

        Returns:
            True if motion was valid, False otherwise
        """
        if motion == "c":
            # cc - change entire line
            self._delete_lines(1)
            self.buffer.insert_line(self.buffer.cursor[0], "")
            self.buffer.move_cursor(self.buffer.cursor[0], 0)
            self.mode = "insert"
            return True
        if motion == "w":
            # cw - change word forward
            self._delete_word_forward(count)
            self.mode = "insert"
            return True
        if motion == "b":
            # cb - change word backward
            self._delete_word_backward(count)
            self.mode = "insert"
            return True
        if motion == "$":
            # c$ - change to end of line
            self._delete_to_end_of_line()
            self.mode = "insert"
            return True
        if motion == "0":
            # c0 - change to beginning of line
            self._delete_to_beginning_of_line()
            self.mode = "insert"
            return True
        return False

    def _replace_char(self, replacement: str, count: int = 1) -> None:
        """Replace character(s) at cursor with replacement character."""
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)

        if col < len(line):
            # Replace count characters with the replacement char
            end_col = min(col + count, len(line))
            new_line = line[:col] + replacement * (end_col - col) + line[end_col:]
            self.buffer.modify_line(row, new_line)

    def _toggle_case(self, count: int = 1) -> None:
        """Toggle case of character(s) at cursor and move right."""
        for _ in range(count):
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            if col < len(line):
                char = line[col]
                if char.isupper():
                    new_char = char.lower()
                elif char.islower():
                    new_char = char.upper()
                else:
                    new_char = char

                new_line = line[:col] + new_char + line[col + 1 :]
                self.buffer.modify_line(row, new_line)

                # Move cursor right
                if col < len(line) - 1:
                    self.buffer.move_cursor(row, col + 1)

    def insert_text(self, text: str) -> None:
        """Insert text at current cursor position (for insert mode)."""
        if self.mode == "insert":
            self.insert_mode.process_input(text)

    def replace_text(self, text: str) -> None:
        """Replace text at current cursor position (for replace mode)."""
        if self.mode == "replace":
            row, col = self.buffer.cursor
            line = self.buffer.get_line(row)

            # Replace character at cursor position
            if col < len(line):
                new_line = line[:col] + text + line[col + 1 :]
            else:
                # Extend line if at end
                new_line = line + text

            self.buffer.modify_line(row, new_line)
            # Move cursor forward
            self.buffer.move_cursor(row, col + 1)

    def exit_insert_mode(self) -> None:
        """Exit insert mode and return to command mode."""
        self.mode = "command"
        self.insert_mode.exit_insert_mode()

    def exit_replace_mode(self) -> None:
        """Exit replace mode and return to command mode."""
        self.mode = "command"
        self.replace_mode = False

        # Adjust cursor position like vi does
        row, col = self.buffer.cursor
        line = self.buffer.get_line(row)
        if col > 0 and col >= len(line):
            self.buffer.move_cursor(row, len(line) - 1 if line else 0)
