"""Command executor for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..buffer.core import TextBuffer
    from ..modes.state import ModeManager
    from ..terminal.render import Renderer


class CommandExecutor:
    """Executes vi commands on buffer."""

    def __init__(self, buffer: "TextBuffer", modes: "ModeManager", renderer: "Renderer"):
        """Initialize command executor with buffer, modes, and renderer."""
        self.buffer = buffer
        self.modes = modes
        self.renderer = renderer
        self._repeat_count = ""
        self._last_command = ""
        self._pending_operator = ""
        self._pending_count = 1  # Count to use for pending operator

        # Initialize visual mode and register manager
        from ..buffer.registers import BufferRegisterManager
        from ..modes.visual import VisualMode

        self.visual = VisualMode(buffer)
        self.registers = BufferRegisterManager()

    def execute_normal_command(self, char: str) -> bool:
        """Execute a command in normal mode.

        Returns True if command was handled, False otherwise.
        """
        # Handle digits for repeat count
        if char.isdigit() and (char != "0" or self._repeat_count):
            self._repeat_count += char
            return True

        # Get repeat count
        count = int(self._repeat_count) if self._repeat_count else 1
        self._repeat_count = ""

        # Handle pending commands with arguments FIRST (before regular commands)
        if self._last_command == "m":
            # Set mark
            self._last_command = ""
            if "a" <= char <= "z":
                self.buffer.set_named_mark(char)
                self.renderer.show_message(f"Mark {char} set")
                return True
            return False

        if self._last_command == "'":
            # Jump to mark (line)
            self._last_command = ""
            if "a" <= char <= "z":
                if self.buffer.jump_to_mark(char):
                    # Move to first non-blank of line
                    self.buffer.move_to_first_non_blank()
                    return True
                self.renderer.show_message(f"Mark {char} not set")
                return True
            return False

        if self._last_command == "`":
            # Jump to mark (exact position)
            self._last_command = ""
            if "a" <= char <= "z":
                if self.buffer.jump_to_mark(char):
                    return True
                self.renderer.show_message(f"Mark {char} not set")
                return True
            return False

        if self._last_command == "r":
            # Replace character
            self._last_command = ""
            if ord(char) >= 32:  # Printable character
                self.buffer.replace_char(char)
                return True
            return False

        # Movement commands
        if char in "hjkl":
            return self._execute_move(char, count)

        # Line movement commands
        if char == "0":
            return self._execute_line_start()
        if char == "$":
            return self._execute_line_end()
        if char == "^":
            return self._execute_first_non_blank()
        if char == "G":
            return self._execute_goto_line(count)
        if char == "g":
            if self._last_command == "g":
                self._last_command = ""
                return self._execute_goto_first_line()
            self._last_command = "g"
            return True

        # Word movement
        if char == "w":
            return self._execute_word_forward(count)
        if char == "b":
            return self._execute_word_backward(count)
        if char == "e":
            return self._execute_word_end(count)

        # Mode changes
        if char == "i":
            self.modes.to_insert()
            return True
        if char == "a":
            self.buffer.move_cursor_right()
            self.modes.to_insert()
            return True
        if char == "A":
            self._execute_line_end()
            self.modes.to_insert()
            return True
        if char == "I":
            self._execute_first_non_blank()
            self.modes.to_insert()
            return True
        if char == "o":
            self._execute_open_line_below()
            self.modes.to_insert()
            return True
        if char == "O":
            self._execute_open_line_above()
            self.modes.to_insert()
            return True

        # Visual mode
        if char == "v":
            self.buffer.set_mark()
            self.visual.enter_visual("character")
            self.modes.to_visual()
            return True
        if char == "V":
            self.buffer.set_mark()
            self.visual.enter_visual("line")
            self.modes.to_visual(line_mode=True)
            return True

        # Delete commands
        if char == "x":
            return self._execute_delete_char(count)
        if char == "d":
            if self._last_command == "d":
                self._last_command = ""
                # Use the saved count from when first 'd' was pressed
                return self._execute_delete_line(self._pending_count)
            self._last_command = "d"
            self._pending_count = count  # Save count for when second 'd' arrives
            return True
        if char == "D":
            return self._execute_delete_to_end()

        # Change commands
        if char == "c":
            if self._last_command == "c":
                self._last_command = ""
                # Use the saved count from when first 'c' was pressed
                return self._execute_change_line(self._pending_count)
            self._last_command = "c"
            self._pending_count = count  # Save count for when second 'c' arrives
            return True
        if char == "C":
            return self._execute_change_to_end()

        # Replace
        if char == "r":
            self._last_command = "r"
            return True

        # Yank
        if char == "y":
            if self._last_command == "y":
                self._last_command = ""
                # Use the saved count from when first 'y' was pressed
                return self._execute_yank_line(self._pending_count)
            self._last_command = "y"
            self._pending_count = count  # Save count for when second 'y' arrives
            return True

        # Put
        if char == "p":
            return self._execute_put_after()
        if char == "P":
            return self._execute_put_before()

        # Marks
        if char == "m":
            self._last_command = "m"
            return True
        if char == "'":
            self._last_command = "'"
            return True
        if char == "`":
            self._last_command = "`"
            return True

        # Jump list navigation
        if char == "\x0f":  # Ctrl-O - jump older
            if self.buffer.jump_older():
                return True
            self.renderer.show_message("Oldest position in jump list")
            return True
        if char == "\x09":  # Ctrl-I (Tab) - jump newer
            if self.buffer.jump_newer():
                return True
            self.renderer.show_message("Newest position in jump list")
            return True

        # Undo/redo (placeholder for now)
        if char == "u":
            self.renderer.show_message("Undo not implemented")
            return True
        if char == "\x12":  # Ctrl-R
            self.renderer.show_message("Redo not implemented")
            return True

        # Clear any pending operator on unrecognized command
        self._last_command = ""
        return False

    def _execute_move(self, direction: str, count: int = 1) -> bool:
        """Execute movement command using TextBuffer.move_cursor_relative.

        Args:
            direction: One of 'h', 'j', 'k', 'l'
            count: Number of times to repeat movement

        Returns:
            True if movement was executed
        """
        try:
            # Use the buffer's move_cursor_relative method
            self.buffer.move_cursor_relative(direction, count)
            return True
        except ValueError:
            # Invalid direction - should not happen with h,j,k,l
            return False

    def _execute_line_start(self) -> bool:
        """Move to start of line (column 0)."""
        row, _ = self.buffer.get_cursor()
        self.buffer.set_cursor(row, 0)
        return True

    def _execute_line_end(self) -> bool:
        """Move to end of line."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            # Position at last character, not past it (vi behavior)
            line_len = len(lines[row])
            self.buffer.set_cursor(row, max(0, line_len - 1))
        return True

    def _execute_first_non_blank(self) -> bool:
        """Move to first non-blank character of line."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            line = lines[row]
            col = 0
            for i, char in enumerate(line):
                if not char.isspace():
                    col = i
                    break
            self.buffer.set_cursor(row, col)
        return True

    def _execute_goto_line(self, line_num: int) -> bool:
        """Go to specific line number (G command)."""
        # Push current position to jump list
        self.buffer.push_jump_position()

        lines = self.buffer.get_lines()
        if line_num == 1:  # No count means last line
            target_row = len(lines) - 1
        else:
            target_row = min(line_num - 1, len(lines) - 1)
        self.buffer.set_cursor(target_row, 0)
        return True

    def _execute_goto_first_line(self) -> bool:
        """Go to first line (gg command)."""
        # Push current position to jump list
        self.buffer.push_jump_position()

        self.buffer.set_cursor(0, 0)
        return True

    def _execute_word_forward(self, count: int) -> bool:
        """Move forward by words."""
        for _ in range(count):
            row, col = self.buffer.get_cursor()
            lines = self.buffer.get_lines()

            if row >= len(lines):
                break

            line = lines[row]

            # Skip current word
            while col < len(line) and not line[col].isspace():
                col += 1

            # Skip whitespace
            while col < len(line) and line[col].isspace():
                col += 1

            # If at end of line, move to next line
            if col >= len(line) and row < len(lines) - 1:
                row += 1
                col = 0
                # Skip leading whitespace on new line
                if row < len(lines):
                    line = lines[row]
                    while col < len(line) and line[col].isspace():
                        col += 1

            # In normal mode, cursor must stay on a character, not past it
            if row < len(lines) and col >= len(lines[row]) and len(lines[row]) > 0:
                col = len(lines[row]) - 1

            self.buffer.set_cursor(row, col)
        return True

    def _execute_word_backward(self, count: int) -> bool:
        """Move backward by words."""
        for _ in range(count):
            row, col = self.buffer.get_cursor()
            lines = self.buffer.get_lines()

            if row >= len(lines):
                break

            # Move back one position first
            if col > 0:
                col -= 1
            elif row > 0:
                row -= 1
                col = len(lines[row]) - 1 if row < len(lines) else 0

            if row < len(lines):
                line = lines[row]

                # Skip whitespace backwards
                while col > 0 and line[col].isspace():
                    col -= 1

                # Skip word backwards
                while col > 0 and not line[col - 1].isspace():
                    col -= 1

            self.buffer.set_cursor(row, col)
        return True

    def _execute_word_end(self, count: int) -> bool:
        """Move to end of word."""
        for _ in range(count):
            row, col = self.buffer.get_cursor()
            lines = self.buffer.get_lines()

            if row >= len(lines):
                break

            line = lines[row]

            # Move forward one if at start of word
            if col < len(line) - 1:
                col += 1

            # Skip to end of current word
            while col < len(line) - 1 and not line[col].isspace():
                col += 1

            self.buffer.set_cursor(row, col)
        return True

    def _execute_delete_char(self, count: int) -> bool:
        """Delete characters at cursor."""
        deleted = ""
        for _ in range(count):
            char = self.buffer.get_char_at_cursor()
            if char:
                deleted += char
                self.buffer.delete_char()
        if deleted:
            self.registers.delete_and_yank(deleted)
        return True

    def _execute_delete_line(self, count: int) -> bool:
        """Delete entire lines."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()

        # Collect lines to delete
        end_row = min(row + count, len(lines))
        deleted_lines = lines[row:end_row]

        # Only store if we actually deleted something
        if deleted_lines:
            deleted_text = "\n".join(deleted_lines) + "\n"
        else:
            deleted_text = ""

        # Delete the lines
        for _ in range(count):
            if row < len(self.buffer.get_lines()):
                self.buffer.delete_line()

        # Store in register only if we deleted something
        if deleted_text:
            self.registers.delete_and_yank(deleted_text, is_linewise=True)
        return True

    def _execute_delete_to_end(self) -> bool:
        """Delete from cursor to end of line."""
        row, col = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            line = lines[row]
            # Get text to delete
            deleted = line[col:]
            # Delete from cursor to end
            self.buffer._lines[row] = line[:col]
            # Store in register
            if deleted:
                self.registers.delete_and_yank(deleted)
        return True

    def _execute_change_line(self, count: int) -> bool:
        """Change entire lines."""
        self._execute_delete_line(count)
        self._execute_open_line_above()
        self.modes.to_insert()
        return True

    def _execute_change_to_end(self) -> bool:
        """Change from cursor to end of line."""
        self._execute_delete_to_end()
        self.modes.to_insert()
        return True

    def _execute_yank_line(self, count: int) -> bool:
        """Yank lines to register."""
        row, _ = self.buffer.get_cursor()
        yanked_text = self.registers.yank_lines(self.buffer, row, count)
        line_count = len(yanked_text.split("\n")) - 1  # -1 for trailing newline
        self.renderer.show_message(f"{line_count} line(s) yanked")
        return True

    def _execute_put_after(self) -> bool:
        """Put after cursor from register."""
        if self.registers.put_after(self.buffer):
            return True
        self.renderer.show_message("Nothing to put")
        return True

    def _execute_put_before(self) -> bool:
        """Put before cursor from register."""
        if self.registers.put_before(self.buffer):
            return True
        self.renderer.show_message("Nothing to put")
        return True

    def _execute_open_line_below(self) -> bool:
        """Open new line below current line."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            # Move to end of current line
            line_len = len(lines[row])
            self.buffer.set_cursor(row, line_len)
            # Insert newline
            self.buffer.insert_char("\n")
        return True

    def _execute_open_line_above(self) -> bool:
        """Open new line above current line."""
        row, _ = self.buffer.get_cursor()
        # Move to start of line
        self.buffer.set_cursor(row, 0)
        # Insert newline
        self.buffer.insert_char("\n")
        # Move back up to new line
        self.buffer.move_cursor_up()
        return True

    def execute_visual_command(self, char: str) -> bool:
        """Execute a command in visual mode.

        Returns True if command was handled, False otherwise.
        """
        # Update visual selection with current cursor position
        cursor_pos = self.buffer.get_cursor()
        self.visual.update_selection(cursor_pos)

        # Movement in visual mode
        if char in "hjkl":
            count = int(self._repeat_count) if self._repeat_count else 1
            self._repeat_count = ""
            result = self._execute_move(char, count)
            # Update selection after movement
            new_pos = self.buffer.get_cursor()
            self.visual.update_selection(new_pos)
            return result

        # Exit visual mode
        if char == "\x1b":  # Escape
            self.visual.exit_visual()
            self.buffer.clear_mark()
            self.modes.to_normal()
            return True

        if char == "v":  # v again toggles off
            self.visual.exit_visual()
            self.buffer.clear_mark()
            self.modes.to_normal()
            return True

        # Delete selection
        if char == "d" or char == "x":
            deleted = self.visual.delete_selection()
            if deleted:
                self.registers.delete_and_yank(deleted, is_linewise=self.visual.mode_type == "line")
                self.renderer.show_message(
                    f"{len(deleted.splitlines())} lines deleted"
                    if "\n" in deleted
                    else f"{len(deleted)} characters deleted"
                )
            self.buffer.clear_mark()
            self.modes.to_normal()
            return True

        # Yank selection
        if char == "y":
            yanked = self.visual.yank_selection()
            if yanked:
                self.registers.yank_text(yanked, is_linewise=self.visual.mode_type == "line")
                self.renderer.show_message(
                    f"{len(yanked.splitlines())} lines yanked" if "\n" in yanked else f"{len(yanked)} characters yanked"
                )
            self.visual.exit_visual()
            self.buffer.clear_mark()
            self.modes.to_normal()
            return True

        # Change selection
        if char == "c":
            deleted = self.visual.change_selection()
            if deleted:
                self.registers.delete_and_yank(deleted, is_linewise=self.visual.mode_type == "line")
            self.buffer.clear_mark()
            self.modes.to_insert()
            return True

        return False

    def execute_insert_command(self, char: str) -> bool:
        """Execute a command in insert mode.

        Returns True if command was handled, False otherwise.
        """
        if char == "\x1b":  # Escape
            self.modes.to_normal()
            # Move cursor back one position if not at start of line
            row, col = self.buffer.get_cursor()
            if col > 0:
                self.buffer.move_cursor_left()
            return True
        if char == "\r" or char == "\n":  # Enter
            self.buffer.insert_char("\n")
            return True
        if char == "\x7f" or char == "\b":  # Backspace
            self.buffer.backspace()
            return True
        if ord(char) >= 32:  # Printable characters
            self.buffer.insert_char(char)
            return True

        return False

    def reset(self) -> None:
        """Reset command state."""
        self._repeat_count = ""
        self._last_command = ""
        self._pending_operator = ""
        self._pending_count = 1

    # Test API aliases for compatibility with torture tests
    def execute_normal(self, command: str) -> bool:
        """Alias for execute_normal_command that handles multi-character commands.

        Args:
            command: Single or multi-character command string (e.g., "100dd", "gg")

        Returns:
            True if all characters were handled successfully
        """
        # For multi-character commands, we need to process them as a complete unit
        # not character by character, to preserve count handling

        # If command starts with digits, extract the count and the rest
        count_str = ""
        cmd_start = 0

        for i, char in enumerate(command):
            if char.isdigit() and (char != "0" or count_str):
                count_str += char
                cmd_start = i + 1
            else:
                break

        # Feed the count digits first if any
        result = True
        for char in count_str:
            if not self.execute_normal_command(char):
                result = False

        # Then feed the remaining command characters
        for char in command[cmd_start:]:
            if not self.execute_normal_command(char):
                result = False

        return result

    def execute_visual(self, command: str) -> bool:
        """Alias for execute_visual_command for test compatibility."""
        return self.execute_visual_command(command)
