#!/usr/bin/env python3
"""
Display and UI module for vi editor.

Handles terminal display, status bar, line numbers, and visual feedback.
"""

import contextlib
import curses


class Display:
    """Manages terminal display for the vi editor."""

    def __init__(self, stdscr=None):
        """
        Initialize the display.

        Args:
            stdscr: Curses standard screen object (optional for testing)
        """
        self.stdscr = stdscr
        self.show_line_numbers = False
        self.status_message = ""
        self.command_line = ""
        self.mode = "NORMAL"
        self.filename = "[No Name]"
        self.modified = False
        self.cursor_pos = (0, 0)
        self.visual_start = None
        self.visual_end = None
        self.screen_height = 24
        self.screen_width = 80
        self.viewport_top = 0  # First visible line

        if stdscr:
            self.screen_height, self.screen_width = stdscr.getmaxyx()
            curses.curs_set(1)  # Show cursor

    def init_curses(self):
        """Initialize curses for terminal control."""
        if not self.stdscr:
            self.stdscr = curses.initscr()
            curses.noecho()
            curses.cbreak()
            self.stdscr.keypad(True)
            self.screen_height, self.screen_width = self.stdscr.getmaxyx()

    def cleanup_curses(self):
        """Clean up curses and restore terminal."""
        if self.stdscr:
            curses.nocbreak()
            self.stdscr.keypad(False)
            curses.echo()
            curses.endwin()

    def render(self, buffer_lines: list[str], cursor: tuple[int, int]):
        """
        Render the entire display.

        Args:
            buffer_lines: Lines of text to display
            cursor: (row, col) cursor position
        """
        if not self.stdscr:
            return

        self.cursor_pos = cursor
        self.stdscr.clear()

        # Calculate viewport
        self._update_viewport(cursor[0])

        # Draw buffer content
        self._draw_buffer(buffer_lines)

        # Draw status bar
        self._draw_status_bar()

        # Draw command line
        self._draw_command_line()

        # Position cursor
        self._position_cursor(cursor)

        self.stdscr.refresh()

    def _update_viewport(self, cursor_row: int):
        """Update viewport to ensure cursor is visible."""
        # Reserve lines for status bar and command line
        visible_lines = self.screen_height - 2

        # Scroll up if cursor is above viewport
        if cursor_row < self.viewport_top:
            self.viewport_top = cursor_row

        # Scroll down if cursor is below viewport
        elif cursor_row >= self.viewport_top + visible_lines:
            self.viewport_top = cursor_row - visible_lines + 1

    def _draw_buffer(self, buffer_lines: list[str]):
        """Draw the buffer content with optional line numbers."""
        if not self.stdscr:
            return

        visible_lines = self.screen_height - 2  # Reserve for status and command line
        line_num_width = 0

        if self.show_line_numbers:
            # Calculate width needed for line numbers
            max_line = min(len(buffer_lines), self.viewport_top + visible_lines)
            line_num_width = len(str(max_line)) + 1  # +1 for space

        for screen_row in range(visible_lines):
            buffer_row = self.viewport_top + screen_row

            if buffer_row < len(buffer_lines):
                line = buffer_lines[buffer_row]

                # Draw line number if enabled
                col_offset = 0
                if self.show_line_numbers:
                    line_num = str(buffer_row + 1).rjust(line_num_width - 1)
                    try:
                        self.stdscr.addstr(screen_row, 0, line_num, curses.A_DIM)
                        self.stdscr.addstr(screen_row, line_num_width - 1, " ")
                    except curses.error:
                        pass
                    col_offset = line_num_width

                # Draw line content
                # Highlight visual selection if active
                if self._is_visual_mode() and self._is_line_in_selection(buffer_row):
                    attrs = curses.A_REVERSE
                else:
                    attrs = 0

                # Truncate line if too long
                max_width = self.screen_width - col_offset
                display_line = line[:max_width] if len(line) > max_width else line

                with contextlib.suppress(curses.error):
                    self.stdscr.addstr(screen_row, col_offset, display_line, attrs)
            else:
                # Draw tilde for empty lines beyond buffer
                with contextlib.suppress(curses.error):
                    self.stdscr.addstr(screen_row, 0, "~", curses.A_DIM)

    def _draw_status_bar(self):
        """Draw the status bar at the bottom."""
        if not self.stdscr:
            return

        status_row = self.screen_height - 2

        # Build status line
        mode_str = f"-- {self.mode} --"
        file_str = self.filename
        if self.modified:
            file_str += " [+]"

        pos_str = f"{self.cursor_pos[0] + 1},{self.cursor_pos[1] + 1}"

        # Combine status elements
        left_status = f" {mode_str} {file_str}"
        right_status = f"{pos_str} "

        # Calculate padding
        padding = self.screen_width - len(left_status) - len(right_status)
        if padding < 0:
            padding = 0

        status_line = left_status + " " * padding + right_status

        # Draw status bar with inverse video
        with contextlib.suppress(curses.error):
            self.stdscr.addstr(status_row, 0, status_line[: self.screen_width], curses.A_REVERSE)

    def _draw_command_line(self):
        """Draw the command line at the bottom."""
        if not self.stdscr:
            return

        cmd_row = self.screen_height - 1

        if self.command_line:
            with contextlib.suppress(curses.error):
                self.stdscr.addstr(cmd_row, 0, self.command_line[: self.screen_width])
        elif self.status_message:
            with contextlib.suppress(curses.error):
                self.stdscr.addstr(cmd_row, 0, self.status_message[: self.screen_width])

    def _position_cursor(self, cursor: tuple[int, int]):
        """Position the hardware cursor."""
        if not self.stdscr:
            return

        row, col = cursor
        screen_row = row - self.viewport_top

        # Account for line numbers if shown
        col_offset = 0
        if self.show_line_numbers:
            max_line = self.viewport_top + self.screen_height - 2
            line_num_width = len(str(max_line)) + 1
            col_offset = line_num_width

        # Ensure cursor is within screen bounds
        if 0 <= screen_row < self.screen_height - 2:
            screen_col = min(col + col_offset, self.screen_width - 1)
            with contextlib.suppress(curses.error):
                self.stdscr.move(screen_row, screen_col)

    def set_mode(self, mode: str):
        """Set the current editor mode."""
        mode_map = {
            "command": "NORMAL",
            "insert": "INSERT",
            "replace": "REPLACE",
            "visual": "VISUAL",
            "visual_line": "VISUAL LINE",
        }
        self.mode = mode_map.get(mode, mode.upper())

    def set_filename(self, filename: str):
        """Set the current filename."""
        self.filename = filename if filename else "[No Name]"

    def set_modified(self, modified: bool):
        """Set the modified flag."""
        self.modified = modified

    def set_status_message(self, message: str):
        """Set a status message to display."""
        self.status_message = message

    def set_command_line(self, command: str):
        """Set the command line text."""
        self.command_line = command

    def enable_line_numbers(self, enable: bool = True):
        """Enable or disable line number display."""
        self.show_line_numbers = enable

    def set_visual_selection(self, start: tuple[int, int] | None, end: tuple[int, int] | None):
        """Set the visual selection range."""
        self.visual_start = start
        self.visual_end = end

    def _is_visual_mode(self) -> bool:
        """Check if visual mode is active."""
        return self.visual_start is not None and self.visual_end is not None

    def _is_line_in_selection(self, line_num: int) -> bool:
        """Check if a line is part of the visual selection."""
        if not self._is_visual_mode() or self.visual_start is None or self.visual_end is None:
            return False

        start_row = min(self.visual_start[0], self.visual_end[0])
        end_row = max(self.visual_start[0], self.visual_end[0])

        return start_row <= line_num <= end_row

    def get_input(self) -> str | None:
        """
        Get a single character input from the user.

        Returns:
            Character pressed or None if no input
        """
        if not self.stdscr:
            return None

        try:
            ch = self.stdscr.getch()

            # Handle special keys
            if ch == curses.KEY_UP:
                return "KEY_UP"
            if ch == curses.KEY_DOWN:
                return "KEY_DOWN"
            if ch == curses.KEY_LEFT:
                return "KEY_LEFT"
            if ch == curses.KEY_RIGHT:
                return "KEY_RIGHT"
            if ch == curses.KEY_BACKSPACE or ch == 127:
                return "KEY_BACKSPACE"
            if ch == curses.KEY_DC:
                return "KEY_DELETE"
            if ch == 27:  # ESC
                return "KEY_ESC"
            if ch == 10 or ch == curses.KEY_ENTER:  # Enter
                return "KEY_ENTER"
            if 0 <= ch <= 255:
                return chr(ch)
            return None

        except Exception:
            return None


def create_display() -> Display:
    """Create and initialize a display instance."""
    display = Display()
    display.init_curses()
    return display


def test_display():
    """Test display functionality without curses."""
    # Create display without curses for testing
    display = Display()

    # Test mode setting
    display.set_mode("insert")
    assert display.mode == "INSERT"

    display.set_mode("command")
    assert display.mode == "NORMAL"

    # Test filename
    display.set_filename("test.txt")
    assert display.filename == "test.txt"

    display.set_filename("")
    assert display.filename == "[No Name]"

    # Test modified flag
    display.set_modified(True)
    assert display.modified == True

    # Test visual selection
    display.set_visual_selection((0, 0), (2, 5))
    assert display._is_visual_mode() == True
    assert display._is_line_in_selection(1) == True
    assert display._is_line_in_selection(5) == False

    print("Display module tests passed!")


if __name__ == "__main__":
    test_display()
