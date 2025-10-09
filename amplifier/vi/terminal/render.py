"""Terminal rendering for vi editor."""

import os
import sys


class Renderer:
    """Handles terminal rendering for the vi editor."""

    def __init__(self):
        """Initialize renderer with terminal settings."""
        self._width = self._get_terminal_width()
        self._height = self._get_terminal_height()
        self._viewport_start = 0  # First visible line
        self._viewport_height = self._height - 2  # Reserve space for status/command line
        self._status_message = ""
        self._command_line = ""

    def render(self, buffer, mode_manager) -> None:
        """Render the buffer and UI to terminal."""
        # Clear screen
        self._clear_screen()

        # Get buffer state using proper methods
        lines = buffer.get_lines()  # Use get_lines() method instead of .lines property
        cursor_row, cursor_col = buffer.get_cursor()
        mode = mode_manager.get_mode()

        # Adjust viewport if cursor moved outside
        self._adjust_viewport(cursor_row)

        # Render buffer content
        self._render_buffer(lines, cursor_row, cursor_col)

        # Render status line
        self._render_status_line(mode_manager, cursor_row, cursor_col, len(lines))

        # Render command line if in command mode
        if mode == "command":
            self._render_command_line()

        # Position cursor
        self._position_cursor(cursor_row, cursor_col)

    def _render_buffer(self, lines: list[str], cursor_row: int, cursor_col: int) -> None:
        """Render the visible portion of the buffer."""
        for i in range(self._viewport_height):
            line_idx = self._viewport_start + i

            if line_idx < len(lines):
                # Render actual line
                line = lines[line_idx]
                self._write_line(i, line)
            else:
                # Render tilde for empty lines beyond buffer
                self._write_line(i, "~")

    def _render_status_line(self, mode_manager, cursor_row: int, cursor_col: int, total_lines: int) -> None:
        """Render the status line at bottom of screen."""
        mode_indicator = mode_manager.get_mode_indicator()
        position = f"{cursor_row + 1},{cursor_col + 1}"
        percentage = int((cursor_row + 1) / total_lines * 100) if total_lines > 0 else 0

        # Build status line
        left_part = f" {mode_indicator}"
        right_part = f"{position} {percentage}% "

        # Fill middle with spaces
        middle_spaces = self._width - len(left_part) - len(right_part)
        if middle_spaces > 0:
            status_line = left_part + " " * middle_spaces + right_part
        else:
            status_line = f"{left_part} {right_part}"[: self._width]

        # Write status line with inverse colors
        self._move_cursor_to(self._height - 2, 0)
        sys.stdout.write("\033[7m")  # Inverse video
        sys.stdout.write(status_line[: self._width])
        sys.stdout.write("\033[0m")  # Reset
        sys.stdout.flush()

    def _render_command_line(self) -> None:
        """Render the command line at very bottom."""
        self._move_cursor_to(self._height - 1, 0)
        sys.stdout.write(":" + self._command_line)
        sys.stdout.flush()

    def _adjust_viewport(self, cursor_row: int) -> None:
        """Adjust viewport to keep cursor visible."""
        # If cursor above viewport, scroll up
        if cursor_row < self._viewport_start:
            self._viewport_start = cursor_row

        # If cursor below viewport, scroll down
        elif cursor_row >= self._viewport_start + self._viewport_height:
            self._viewport_start = cursor_row - self._viewport_height + 1

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        sys.stdout.write("\033[2J")  # Clear entire screen
        sys.stdout.write("\033[H")  # Move cursor to home
        sys.stdout.flush()

    def _write_line(self, screen_row: int, text: str) -> None:
        """Write a line of text at the specified screen row."""
        self._move_cursor_to(screen_row, 0)
        # Truncate or pad line to terminal width
        if len(text) > self._width:
            sys.stdout.write(text[: self._width - 1] + "…")
        else:
            sys.stdout.write(text)
        sys.stdout.flush()

    def _move_cursor_to(self, row: int, col: int) -> None:
        """Move terminal cursor to specified position."""
        # Terminal positions are 1-based
        sys.stdout.write(f"\033[{row + 1};{col + 1}H")
        sys.stdout.flush()

    def _position_cursor(self, buffer_row: int, buffer_col: int) -> None:
        """Position the terminal cursor based on buffer cursor."""
        screen_row = buffer_row - self._viewport_start
        if 0 <= screen_row < self._viewport_height:
            self._move_cursor_to(screen_row, min(buffer_col, self._width - 1))

    def _get_terminal_width(self) -> int:
        """Get terminal width."""
        try:
            return os.get_terminal_size().columns
        except (OSError, AttributeError):
            return 80  # Default fallback

    def _get_terminal_height(self) -> int:
        """Get terminal height."""
        try:
            return os.get_terminal_size().lines
        except (OSError, AttributeError):
            return 24  # Default fallback

    def update_command_line(self, text: str) -> None:
        """Update the command line text."""
        self._command_line = text

    def clear_command_line(self) -> None:
        """Clear the command line."""
        self._command_line = ""
        self._move_cursor_to(self._height - 1, 0)
        sys.stdout.write(" " * self._width)
        sys.stdout.flush()

    def show_message(self, message: str) -> None:
        """Show a temporary message on the status line."""
        self._status_message = message

    def resize(self) -> None:
        """Handle terminal resize."""
        self._width = self._get_terminal_width()
        self._height = self._get_terminal_height()
        self._viewport_height = self._height - 2
