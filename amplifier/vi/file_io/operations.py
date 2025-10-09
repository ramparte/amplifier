"""File operations wrapper for vi editor."""

from pathlib import Path

from .loader import load_file
from .saver import save_file
from .state import FileState


class FileOperations:
    """Simplified file operations interface for the vi editor."""

    def __init__(self):
        """Initialize file operations handler."""
        # Store states per filepath
        self.file_states: dict[str, FileState] = {}

    def read_file(self, filepath: str) -> str | None:
        """Read a file and return its content.

        Args:
            filepath: Path to the file to read.

        Returns:
            File content as string, or None if file doesn't exist.
        """
        path = Path(filepath)

        if not path.exists():
            return None

        try:
            content, encoding, state = load_file(filepath)

            # Store file state
            self.file_states[filepath] = state

            return content

        except Exception:
            # Return None for any read errors
            # The editor will handle this as a new file
            return None

    def write_file(self, filepath: str, content: str) -> bool:
        """Write content to a file.

        Args:
            filepath: Path to the file to write.
            content: Content to write to the file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Get current file state if it exists
            state = self.file_states.get(filepath)

            # Use encoding from state if available, otherwise UTF-8
            encoding = state.encoding if state else "utf-8"

            # Save file
            success = save_file(filepath, content, encoding=encoding)

            if success:
                # Update or create file state
                new_state = FileState(filepath=Path(filepath))
                new_state.mark_saved()
                self.file_states[filepath] = new_state

            return success

        except Exception:
            return False

    def file_exists(self, filepath: str) -> bool:
        """Check if a file exists.

        Args:
            filepath: Path to check.

        Returns:
            True if file exists, False otherwise.
        """
        return Path(filepath).exists()

    def is_readonly(self, filepath: str) -> bool:
        """Check if a file is read-only.

        Args:
            filepath: Path to check.

        Returns:
            True if file is read-only, False otherwise.
        """
        path = Path(filepath)
        if not path.exists():
            return False

        try:
            # Check if we can write to the file
            import os

            return not os.access(path, os.W_OK)
        except Exception:
            return True

    def get_file_info(self, filepath: str) -> dict | None:
        """Get file information.

        Args:
            filepath: Path to the file.

        Returns:
            Dictionary with file info, or None if file doesn't exist.
        """
        state = self.file_states.get(filepath)

        if not state:
            # Try to create state for existing file
            path = Path(filepath)
            if path.exists():
                state = FileState(filepath=path)
                self.file_states[filepath] = state
            else:
                return None

        return {
            "size": state.file_size,
            "modified": state.is_modified,
            "encoding": state.encoding,
            "line_ending": state.line_ending,
            "readonly": state.is_readonly,
        }
