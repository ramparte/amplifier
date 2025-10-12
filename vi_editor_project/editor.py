#!/usr/bin/env python3
"""
Main editor class that integrates all vi editor components.

This class brings together:
- Buffer management
- Command mode operations
- Insert mode operations
- Mode switching
"""

from buffer import Buffer
from command_mode import CommandMode
from insert_mode import InsertMode


class Editor:
    """Main vi editor class that manages modes and coordinates operations."""

    def __init__(self, initial_lines: list[str] | None = None):
        """
        Initialize the editor with optional initial content.

        Args:
            initial_lines: Initial lines of text for the buffer
        """
        # Initialize buffer
        self.buffer = Buffer(initial_lines)

        # Initialize modes
        self.command_mode = CommandMode(self.buffer)
        self.insert_mode = InsertMode(self.buffer)

        # Start in command mode
        self.current_mode = "command"

    def process_key(self, key: str) -> None:
        """
        Process a keystroke based on current mode.

        Args:
            key: The keystroke to process (character or special key)
        """
        if self.current_mode == "command":
            self._process_command_key(key)
        elif self.current_mode == "insert":
            self._process_insert_key(key)

    def _process_command_key(self, key: str) -> None:
        """
        Process a keystroke in command mode.

        Args:
            key: The keystroke to process
        """
        # Check if this is an insert mode entry command
        if key in ["i", "I", "a", "A", "o", "O"]:
            # Enter insert mode
            if self.insert_mode.enter_insert_mode(key):
                self.current_mode = "insert"
        else:
            # Process as a command mode operation
            self.command_mode.process_command(key)

    def _process_insert_key(self, key: str) -> None:
        """
        Process a keystroke in insert mode.

        Args:
            key: The keystroke to process
        """
        # Process the input (returns False if exited to command mode)
        if not self.insert_mode.process_input(key):
            self.current_mode = "command"

    def get_buffer_content(self) -> list[str]:
        """
        Get the current buffer content.

        Returns:
            List of lines in the buffer
        """
        return self.buffer.get_content()

    def get_cursor_position(self) -> tuple[int, int]:
        """
        Get current cursor position.

        Returns:
            Tuple of (row, col) with 0-based indexing
        """
        return self.buffer.cursor

    def get_current_mode(self) -> str:
        """
        Get the current editor mode.

        Returns:
            Current mode ("command" or "insert")
        """
        return self.current_mode

    def is_in_insert_mode(self) -> bool:
        """
        Check if editor is in insert mode.

        Returns:
            True if in insert mode, False otherwise
        """
        return self.current_mode == "insert"


def create_editor(initial_lines: list[str] | None = None) -> Editor:
    """
    Factory function to create an editor instance.

    This is the interface expected by the test framework.

    Args:
        initial_lines: Initial lines of text for the buffer

    Returns:
        Configured Editor instance
    """
    return Editor(initial_lines)
