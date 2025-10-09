"""Enhanced terminal renderer for vi editor with complete display features."""

import os
import sys


class Renderer:
    """Handles terminal rendering for the vi editor."""

    def __init__(self):
        """Initialize renderer with terminal settings."""
        self._width = self._get_terminal_width()
        self._height = self._get_terminal_height()
        self._viewport_start = 0  # First visible line
        self._viewport_height = self._height - 2  # Reserve for status/command
        self._status_message = ""
        self._command_line = ""
        self._show_line_numbers = False
        self._line_number_width = 0
        self._search_pattern = ""
        self._last_render_state = {}

    def render(
        self,
        buffer,
        mode_manager,
        filename: str | None = None,
        readonly: bool = False,
        modified: bool = False,
    ) -> None:
        """Render the complete editor interface.

        Args:
            buffer: The text buffer to render
            mode_manager: Mode manager for current mode
            filename: Current filename (optional)
            readonly: Whether file is read-only
            modified: Whether buffer has been modified
        """
        # Clear screen for complete redraw
        self._clear_screen()

        # Get buffer state
        lines = buffer.get_lines()
        cursor_row, cursor_col = buffer.get_cursor()
        mode = mode_manager.get_mode()

        # Calculate line number width if enabled
        if self._show_line_numbers:
            self._line_number_width = len(str(len(lines))) + 1

        # Adjust viewport to keep cursor visible
        self._adjust_viewport(cursor_row)

        # Render main buffer area
        self._render_buffer(lines, cursor_row, cursor_col, buffer)

        # Render status line
        self._render_status_line(
            mode_manager,
            cursor_row,
            cursor_col,
            len(lines),
            filename,
            readonly,
            modified,
        )

        # Render command line or message
        if mode == "command":
            self._render_command_line()
        elif self._status_message:
            self._render_message()

        # Position cursor appropriately
        self._position_cursor(cursor_row, cursor_col, mode)

    def _render_buffer(self, lines: list[str], cursor_row: int, cursor_col: int, buffer) -> None:
        """Render the visible portion of the buffer with optional line numbers."""
        # Calculate visible content width
        content_start = self._line_number_width if self._show_line_numbers else 0
        content_width = self._width - content_start

        for i in range(self._viewport_height):
            line_idx = self._viewport_start + i

            # Move to start of line
            self._move_cursor_to(i, 0)

            if line_idx < len(lines):
                # Render line number if enabled
                if self._show_line_numbers:
                    line_num = str(line_idx + 1).rjust(self._line_number_width - 1)
                    sys.stdout.write(f"\033[90m{line_num} \033[0m")  # Gray color

                # Get line content
                line = lines[line_idx]

                # Handle visual mode highlighting
                if hasattr(buffer, "visual_start") and buffer.visual_start:
                    highlighted_line = self._apply_visual_highlighting(line, line_idx, buffer)
                    sys.stdout.write(highlighted_line[:content_width])
                else:
                    # Truncate line if too long
                    if len(line) > content_width:
                        sys.stdout.write(line[: content_width - 1] + "…")
                    else:
                        sys.stdout.write(line)

            else:
                # Empty line indicator
                if self._show_line_numbers:
                    sys.stdout.write(" " * (self._line_number_width - 1) + " ")
                sys.stdout.write("\033[90m~\033[0m")  # Gray tilde

            # Clear to end of line
            sys.stdout.write("\033[K")

        sys.stdout.flush()

    def _apply_visual_highlighting(self, line: str, line_idx: int, buffer) -> str:
        """Apply visual mode highlighting to a line."""
        start_row, start_col = buffer.visual_start
        end_row, end_col = buffer.get_cursor()

        # Ensure start is before end
        if start_row > end_row or (start_row == end_row and start_col > end_col):
            start_row, end_row = end_row, start_row
            start_col, end_col = end_col, start_col

        # Check if this line is in the visual selection
        if start_row <= line_idx <= end_row:
            if start_row == end_row:
                # Single line selection
                if line_idx == start_row:
                    return (
                        line[:start_col]
                        + "\033[7m"  # Inverse video
                        + line[start_col : end_col + 1]
                        + "\033[0m"  # Reset
                        + line[end_col + 1 :]
                    )
            elif line_idx == start_row:
                # First line of multi-line selection
                return line[:start_col] + "\033[7m" + line[start_col:] + "\033[0m"
            elif line_idx == end_row:
                # Last line of multi-line selection
                return "\033[7m" + line[: end_col + 1] + "\033[0m" + line[end_col + 1 :]
            else:
                # Middle line - fully selected
                return "\033[7m" + line + "\033[0m"

        return line

    def _render_status_line(
        self,
        mode_manager,
        cursor_row: int,
        cursor_col: int,
        total_lines: int,
        filename: str | None,
        readonly: bool,
        modified: bool,
    ) -> None:
        """Render the status line with file info and position."""
        # Get mode indicator
        mode = mode_manager.get_mode()
        mode_map = {
            "normal": "",
            "insert": "-- INSERT --",
            "visual": "-- VISUAL --",
            "visual_line": "-- VISUAL LINE --",
            "visual_block": "-- VISUAL BLOCK --",
            "replace": "-- REPLACE --",
            "command": "",
        }
        mode_indicator = mode_map.get(mode, mode.upper())

        # Build filename part
        if filename:
            file_part = filename
            if readonly:
                file_part += " [RO]"
            if modified:
                file_part += " [+]"
        else:
            file_part = "[No Name]"
            if modified:
                file_part += " [+]"

        # Build position part
        position = f"{cursor_row + 1},{cursor_col + 1}"
        if total_lines > 0:
            percentage = int((cursor_row + 1) / total_lines * 100)
            position += f" {percentage}%"
        else:
            position += " 100%"

        # Build complete status line
        left_part = f" {mode_indicator}"
        middle_part = f" {file_part}"
        right_part = f" {position} "

        # Calculate spacing
        used_width = len(left_part) + len(middle_part) + len(right_part)
        if used_width < self._width:
            padding = self._width - used_width
            status_line = left_part + middle_part + " " * padding + right_part
        else:
            # Truncate if too long
            status_line = (left_part + middle_part + right_part)[: self._width]

        # Write status line with inverse colors
        self._move_cursor_to(self._height - 2, 0)
        sys.stdout.write("\033[7m")  # Inverse video
        sys.stdout.write(status_line)
        sys.stdout.write("\033[0m")  # Reset
        sys.stdout.flush()

    def _render_command_line(self) -> None:
        """Render the command line at bottom of screen."""
        self._move_cursor_to(self._height - 1, 0)
        sys.stdout.write("\033[K")  # Clear line
        sys.stdout.write(":" + self._command_line)
        sys.stdout.flush()

    def _render_message(self) -> None:
        """Render a status message at bottom of screen."""
        if self._status_message:
            self._move_cursor_to(self._height - 1, 0)
            sys.stdout.write("\033[K")  # Clear line
            # Truncate message if too long
            message = self._status_message[: self._width - 1]
            sys.stdout.write(message)
            sys.stdout.flush()

    def _adjust_viewport(self, cursor_row: int) -> None:
        """Adjust viewport to keep cursor visible."""
        # Scroll up if cursor above viewport
        if cursor_row < self._viewport_start:
            self._viewport_start = cursor_row

        # Scroll down if cursor below viewport
        elif cursor_row >= self._viewport_start + self._viewport_height:
            self._viewport_start = cursor_row - self._viewport_height + 1

        # Ensure viewport doesn't go negative
        self._viewport_start = max(0, self._viewport_start)

    def _position_cursor(self, buffer_row: int, buffer_col: int, mode: str) -> None:
        """Position the terminal cursor based on buffer cursor and mode."""
        screen_row = buffer_row - self._viewport_start

        if 0 <= screen_row < self._viewport_height:
            # Adjust column for line numbers
            screen_col = buffer_col
            if self._show_line_numbers:
                screen_col += self._line_number_width

            # In command mode, position at end of command
            if mode == "command":
                self._move_cursor_to(self._height - 1, len(self._command_line) + 1)
            else:
                # Ensure column is within screen bounds
                screen_col = min(screen_col, self._width - 1)
                self._move_cursor_to(screen_row, screen_col)

    def _clear_screen(self) -> None:
        """Clear the terminal screen."""
        sys.stdout.write("\033[2J")  # Clear entire screen
        sys.stdout.write("\033[H")  # Move cursor to home
        sys.stdout.flush()

    def _move_cursor_to(self, row: int, col: int) -> None:
        """Move terminal cursor to specified position."""
        # ANSI positions are 1-based
        sys.stdout.write(f"\033[{row + 1};{col + 1}H")
        sys.stdout.flush()

    def _get_terminal_width(self) -> int:
        """Get terminal width."""
        try:
            return os.get_terminal_size().columns
        except (OSError, AttributeError):
            return 80

    def _get_terminal_height(self) -> int:
        """Get terminal height."""
        try:
            return os.get_terminal_size().lines
        except (OSError, AttributeError):
            return 24

    def update_command_line(self, text: str) -> None:
        """Update the command line text."""
        self._command_line = text
        self._status_message = ""  # Clear any message when entering command

    def clear_command_line(self) -> None:
        """Clear the command line."""
        self._command_line = ""
        self._move_cursor_to(self._height - 1, 0)
        sys.stdout.write("\033[K")  # Clear line
        sys.stdout.flush()

    def show_message(self, message: str) -> None:
        """Show a temporary message on the status line."""
        self._status_message = message
        self._command_line = ""  # Clear command when showing message

    def set_line_numbers(self, enabled: bool) -> None:
        """Enable or disable line number display."""
        self._show_line_numbers = enabled

    def set_search_pattern(self, pattern: str) -> None:
        """Set the current search pattern for highlighting."""
        self._search_pattern = pattern

    def resize(self) -> None:
        """Handle terminal resize."""
        self._width = self._get_terminal_width()
        self._height = self._get_terminal_height()
        self._viewport_height = self._height - 2

    def beep(self) -> None:
        """Sound the terminal bell for errors."""
        sys.stdout.write("\a")
        sys.stdout.flush()
