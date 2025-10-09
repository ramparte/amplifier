"""Terminal interface for low-level terminal control."""

import os
import sys
import termios
import tty


class TerminalInterface:
    """Handles low-level terminal operations for vi editor."""

    def __init__(self):
        """Initialize terminal interface."""
        self.original_settings: list | None = None
        self.is_raw = False

    def setup(self) -> None:
        """Set up terminal for raw mode operation."""
        if self.is_raw:
            return

        try:
            # Save current terminal settings
            self.original_settings = termios.tcgetattr(sys.stdin)

            # Set terminal to raw mode
            # This disables line buffering and echo
            tty.setraw(sys.stdin.fileno())
            self.is_raw = True

            # Hide cursor while setting up
            sys.stdout.write("\033[?25h")  # Show cursor
            sys.stdout.flush()

        except Exception:
            # Not a terminal, might be running in tests
            self.is_raw = False

    def restore(self) -> None:
        """Restore terminal to original settings."""
        if not self.is_raw or self.original_settings is None:
            return

        try:
            # Restore original terminal settings
            termios.tcsetattr(
                sys.stdin.fileno(),
                termios.TCSADRAIN,
                self.original_settings,
            )
            self.is_raw = False

            # Show cursor
            sys.stdout.write("\033[?25h")
            sys.stdout.flush()

        except Exception:
            # Ignore errors during restore
            pass

    def read_key(self) -> str:
        """Read a single key from terminal.

        Returns:
            The key pressed, with special keys mapped to readable names.
        """
        if not self.is_raw:
            # Fallback for non-raw mode (e.g., testing)
            return sys.stdin.read(1)

        # Read first byte
        char = sys.stdin.read(1)

        if char == "\x1b":  # ESC sequence
            # Check if more bytes are available
            if self._is_data_available():
                next_char = sys.stdin.read(1)

                if next_char == "[":
                    # ANSI escape sequence
                    seq = ""
                    while self._is_data_available():
                        seq_char = sys.stdin.read(1)
                        seq += seq_char
                        if seq_char.isalpha() or seq_char == "~":
                            break

                    # Map common sequences
                    key_map = {
                        "A": "UP",
                        "B": "DOWN",
                        "C": "RIGHT",
                        "D": "LEFT",
                        "H": "HOME",
                        "F": "END",
                        "3~": "DELETE",
                        "5~": "PAGEUP",
                        "6~": "PAGEDOWN",
                        "2~": "INSERT",
                    }

                    return key_map.get(seq, f"ESC[{seq}")

                if next_char == "O":
                    # Alt+O sequences (F1-F4 on some terminals)
                    if self._is_data_available():
                        func_char = sys.stdin.read(1)
                        func_map = {
                            "P": "F1",
                            "Q": "F2",
                            "R": "F3",
                            "S": "F4",
                        }
                        return func_map.get(func_char, f"ESC-O-{func_char}")

                else:
                    # Alt+key combination
                    return f"ALT-{next_char}"

            # Just ESC key
            return "ESC"

        if char == "\x7f":
            # Backspace (DEL char)
            return "BACKSPACE"

        if char == "\r":
            # Enter key
            return "ENTER"

        if char == "\t":
            # Tab key
            return "TAB"

        if ord(char) < 32:
            # Control characters
            # Ctrl+A = 1, Ctrl+B = 2, etc.
            ctrl_char = chr(ord(char) + 64)
            return f"CTRL-{ctrl_char}"

        # Regular character
        return char

    def _is_data_available(self, timeout: float = 0.01) -> bool:
        """Check if data is available to read without blocking.

        Args:
            timeout: Timeout in seconds to wait for data.

        Returns:
            True if data is available, False otherwise.
        """
        import select

        try:
            # Use select to check for available data
            readable, _, _ = select.select([sys.stdin], [], [], timeout)
            return bool(readable)
        except Exception:
            return False

    def get_terminal_size(self) -> tuple[int, int]:
        """Get current terminal size.

        Returns:
            Tuple of (width, height).
        """
        try:
            size = os.get_terminal_size()
            return size.columns, size.lines
        except (OSError, AttributeError):
            # Default fallback
            return 80, 24

    def clear_screen(self) -> None:
        """Clear the terminal screen."""
        sys.stdout.write("\033[2J")  # Clear screen
        sys.stdout.write("\033[H")  # Move to home position
        sys.stdout.flush()

    def move_cursor(self, row: int, col: int) -> None:
        """Move cursor to specified position.

        Args:
            row: Row position (0-based).
            col: Column position (0-based).
        """
        # ANSI escape sequences use 1-based positioning
        sys.stdout.write(f"\033[{row + 1};{col + 1}H")
        sys.stdout.flush()

    def set_cursor_visible(self, visible: bool) -> None:
        """Show or hide the cursor.

        Args:
            visible: True to show cursor, False to hide.
        """
        if visible:
            sys.stdout.write("\033[?25h")  # Show cursor
        else:
            sys.stdout.write("\033[?25l")  # Hide cursor
        sys.stdout.flush()

    def set_alternate_screen(self, enable: bool) -> None:
        """Switch to/from alternate screen buffer.

        Args:
            enable: True to switch to alternate screen, False to return to normal.
        """
        if enable:
            sys.stdout.write("\033[?1049h")  # Enter alternate screen
        else:
            sys.stdout.write("\033[?1049l")  # Exit alternate screen
        sys.stdout.flush()

    def enable_mouse(self) -> None:
        """Enable mouse support in terminal."""
        sys.stdout.write("\033[?1000h")  # Enable mouse reporting
        sys.stdout.flush()

    def disable_mouse(self) -> None:
        """Disable mouse support in terminal."""
        sys.stdout.write("\033[?1000l")  # Disable mouse reporting
        sys.stdout.flush()

    def beep(self) -> None:
        """Sound terminal bell."""
        sys.stdout.write("\a")
        sys.stdout.flush()
