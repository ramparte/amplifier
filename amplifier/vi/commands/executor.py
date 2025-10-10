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

        # Check if we have a pending operator (d, c, y) that needs a motion
        if self._last_command in ["d", "c", "y"]:
            # Handle operator-motion combinations
            result = self._handle_operator_motion(self._last_command, char, count)
            if result is not None:  # Motion was handled (or invalid)
                self._last_command = ""
                self._pending_count = 1
                return result
            # If not a motion, continue to check for double-operator (dd, cc, yy)

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
            # Append after cursor - move right one position if not at end of line
            row, col = self.buffer.get_cursor()
            lines = self.buffer.get_lines()
            if row < len(lines):
                line = lines[row]
                # Only move right if we're not at the end of the line
                if line and col < len(line):
                    self.buffer.set_cursor(row, col + 1)
            self.modes.to_insert()
            return True
        if char == "A":
            # Append at end of line - position AFTER last character
            row, _ = self.buffer.get_cursor()
            lines = self.buffer.get_lines()
            if row < len(lines):
                line = lines[row]
                # For insert mode, position at len(line), not len(line) - 1
                self.buffer.set_cursor(row, len(line))
            self.modes.to_insert()
            return True
        if char == "I":
            # Insert at first non-blank character
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
        if char == "X":
            return self._execute_delete_backward(count)
        if char == "d":
            if self._last_command == "d":
                self._last_command = ""
                # Use the saved count from when first 'd' was pressed
                return self._execute_delete_line(self._pending_count)
            self._last_command = "d"
            self._pending_count = count  # Save count for when 'd' is pressed (for dd or d-motion)
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
            self._pending_count = count  # Save count for when 'c' is pressed (for cc or c-motion)
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
            self._pending_count = count  # Save count for when 'y' is pressed (for yy or y-motion)
            return True
        if char == "Y":
            # Y behaves exactly like yy (special case in vim)
            return self._execute_yank_line(count)

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

    def _execute_delete_backward(self, count: int) -> bool:
        """Delete characters before cursor (X command)."""
        row, col = self.buffer.get_cursor()

        # Can't delete backward if at start of line
        if col == 0:
            return True

        # Determine how many characters we can actually delete
        actual_count = min(count, col)

        # Collect characters to delete (for register)
        lines = self.buffer.get_lines()
        if row < len(lines):
            line = lines[row]
            start_col = max(0, col - actual_count)
            deleted = line[start_col:col]

            # Move cursor to deletion start point
            self.buffer.set_cursor(row, start_col)

            # Delete the characters
            for _ in range(len(deleted)):
                self.buffer.delete_char()

            # Store in register
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

    def _handle_operator_motion(self, operator: str, motion: str, count: int) -> bool | None:
        """Handle operator-motion combinations like d2h, c3w, y$.

        Args:
            operator: The operator (d, c, y)
            motion: The motion command
            count: The count for the motion

        Returns:
            True if handled successfully, False if invalid, None if not a motion
        """
        # Combine the operator count with the motion count
        # e.g., "2d3h" means delete 6 characters to the left
        total_count = self._pending_count * count

        # Save current position for yanking/deleting
        start_row, start_col = self.buffer.get_cursor()

        # Check if this is a valid motion command
        is_motion = False

        # hjkl movements
        if motion in "hjkl":
            is_motion = True
            # Actually execute the motion to find the endpoint
            self._execute_move(motion, total_count)
        # Word movements
        elif motion == "w":
            is_motion = True
            self._execute_word_forward(total_count)
        elif motion == "b":
            is_motion = True
            self._execute_word_backward(total_count)
        elif motion == "e":
            is_motion = True
            self._execute_word_end(total_count)
        # Line movements
        elif motion == "0":
            is_motion = True
            self._execute_line_start()
        elif motion == "$":
            is_motion = True
            self._execute_line_end()
        elif motion == "^":
            is_motion = True
            self._execute_first_non_blank()
        elif motion == "G":
            is_motion = True
            self._execute_goto_line(total_count)
        # Special case: operator repetition (dd, cc, yy)
        elif motion == operator:
            # This is handled elsewhere, return None to continue
            return None
        else:
            # Not a motion command
            return None

        if not is_motion:
            return None

        # Now apply the operator to the motion range
        end_row, end_col = self.buffer.get_cursor()

        # For delete and change operations
        if operator == "d":
            # Delete from start to end position
            self._delete_motion_range(start_row, start_col, end_row, end_col)
            return True
        if operator == "c":
            # Delete range and enter insert mode
            self._delete_motion_range(start_row, start_col, end_row, end_col)
            self.modes.to_insert()
            return True
        if operator == "y":
            # Yank the range
            self._yank_motion_range(start_row, start_col, end_row, end_col)
            # Return cursor to original position after yank
            self.buffer.set_cursor(start_row, start_col)
            return True

        return False

    def _delete_motion_range(self, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        """Delete text from start to end position.

        Args:
            start_row, start_col: Original cursor position before motion
            end_row, end_col: Cursor position after motion
        """
        lines = self.buffer.get_lines()
        deleted_text = ""

        # Determine the actual range to delete
        # We delete from the leftmost position to just before the rightmost
        if (start_row, start_col) > (end_row, end_col):
            # Motion went backward (e.g., h, b)
            from_row, from_col = end_row, end_col
            to_row, to_col = start_row, start_col
        else:
            # Motion went forward (e.g., l, w)
            from_row, from_col = start_row, start_col
            to_row, to_col = end_row, end_col

        if from_row == to_row:
            # Single line deletion
            if from_row < len(lines):
                line = lines[from_row]
                # Delete from 'from_col' up to but not including 'to_col'
                # For d2h from col 8: motion goes to col 6, delete cols 6-7
                # For d2l from col 6: motion goes to col 8, delete cols 6-7
                deleted_text = line[from_col:to_col]
                self.buffer._lines[from_row] = line[:from_col] + line[to_col:]
                # Position cursor at the leftmost position
                self.buffer.set_cursor(from_row, from_col)
        else:
            # Multi-line deletion
            if start_row < len(lines) and end_row < len(lines):
                # Collect deleted text
                deleted_lines = []
                # First line: from start_col to end
                deleted_lines.append(lines[start_row][start_col:])
                # Middle lines: entire lines
                for i in range(start_row + 1, end_row):
                    if i < len(lines):
                        deleted_lines.append(lines[i])
                # Last line: from beginning to end_col
                deleted_lines.append(lines[end_row][: end_col + 1])
                deleted_text = "\n".join(deleted_lines)

                # Perform deletion: join remainder of first and last lines
                new_line = lines[start_row][:start_col] + lines[end_row][end_col + 1 :]
                self.buffer._lines[start_row] = new_line

                # Delete the lines in between
                for _ in range(end_row - start_row):
                    if start_row + 1 < len(self.buffer._lines):
                        del self.buffer._lines[start_row + 1]

                # Position cursor at deletion point
                self.buffer.set_cursor(start_row, min(start_col, len(new_line) - 1))

        # Store in register
        if deleted_text:
            self.registers.delete_and_yank(deleted_text)

    def _yank_motion_range(self, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        """Yank text from start to end position."""
        # Ensure start comes before end
        if (start_row, start_col) > (end_row, end_col):
            start_row, start_col, end_row, end_col = end_row, end_col, start_row, start_col

        lines = self.buffer.get_lines()
        yanked_text = ""

        if start_row == end_row:
            # Single line yank
            if start_row < len(lines):
                line = lines[start_row]
                yanked_text = line[start_col : end_col + 1]
        else:
            # Multi-line yank
            if start_row < len(lines) and end_row < len(lines):
                yanked_lines = []
                # First line: from start_col to end
                yanked_lines.append(lines[start_row][start_col:])
                # Middle lines: entire lines
                for i in range(start_row + 1, end_row):
                    if i < len(lines):
                        yanked_lines.append(lines[i])
                # Last line: from beginning to end_col
                yanked_lines.append(lines[end_row][: end_col + 1])
                yanked_text = "\n".join(yanked_lines)

        # Store in register
        if yanked_text:
            self.registers.yank_text(yanked_text, is_linewise=False)
            if "\n" in yanked_text:
                line_count = yanked_text.count("\n") + 1
                self.renderer.show_message(f"{line_count} lines yanked")
            else:
                self.renderer.show_message(f"{len(yanked_text)} characters yanked")

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
