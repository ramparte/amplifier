"""File state tracking for vi editor."""

import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class FileState:
    """Track file state and modification status."""

    # File information
    filepath: Path | None = None
    encoding: str = "utf-8"
    line_ending: str = "\n"

    # State tracking
    is_modified: bool = False
    is_readonly: bool = False
    is_new_file: bool = True

    # File metadata
    last_saved_time: datetime | None = None
    last_modified_time: float | None = None  # mtime from os.stat
    file_size: int = 0

    # Content hash for change detection (optional)
    content_hash: str | None = None

    def __post_init__(self):
        """Initialize state after creation."""
        if self.filepath:
            self.update_from_disk()

    def set_filepath(self, filepath: str | Path) -> None:
        """Set or change the filepath.

        Args:
            filepath: New filepath
        """
        self.filepath = Path(filepath) if filepath else None
        if self.filepath:
            self.update_from_disk()

    def update_from_disk(self) -> None:
        """Update state from disk file."""
        if not self.filepath:
            return

        if self.filepath.exists():
            self.is_new_file = False

            # Check if readonly
            self.is_readonly = not os.access(self.filepath, os.W_OK)

            # Get file metadata
            try:
                stat_info = os.stat(self.filepath)
                self.last_modified_time = stat_info.st_mtime
                self.file_size = stat_info.st_size
            except OSError:
                # Can't stat file, keep defaults
                pass
        else:
            # New file
            self.is_new_file = True
            self.is_readonly = False
            self.last_modified_time = None
            self.file_size = 0

    def mark_modified(self) -> None:
        """Mark buffer as modified."""
        self.is_modified = True

    def mark_saved(self) -> None:
        """Mark buffer as saved."""
        self.is_modified = False
        self.last_saved_time = datetime.now()
        self.is_new_file = False

        # Update metadata from disk
        if self.filepath and self.filepath.exists():
            try:
                stat_info = os.stat(self.filepath)
                self.last_modified_time = stat_info.st_mtime
                self.file_size = stat_info.st_size
            except OSError:
                pass

    def check_external_changes(self) -> bool:
        """Check if file has been modified externally.

        Returns:
            True if file was modified externally since last check
        """
        if not self.filepath or not self.filepath.exists():
            return False

        if self.last_modified_time is None:
            return False

        try:
            current_mtime = os.stat(self.filepath).st_mtime
            return current_mtime > self.last_modified_time
        except OSError:
            return False

    def get_display_path(self) -> str:
        """Get display-friendly filepath.

        Returns:
            Filepath string or [No Name] for new files
        """
        if not self.filepath:
            return "[No Name]"

        # Try to make path relative to cwd for cleaner display
        try:
            return str(self.filepath.relative_to(Path.cwd()))
        except ValueError:
            # Not relative to cwd, show absolute
            return str(self.filepath)

    def get_status_string(self) -> str:
        """Get status string for display.

        Returns:
            Status string like "[Modified]" or "[Read Only]"
        """
        status_parts = []

        if self.is_new_file and not self.filepath:
            status_parts.append("New")
        elif self.is_new_file:
            status_parts.append("New File")

        if self.is_modified:
            status_parts.append("Modified")

        if self.is_readonly:
            status_parts.append("Read Only")

        if status_parts:
            return f"[{', '.join(status_parts)}]"
        return ""

    def can_write(self) -> bool:
        """Check if file can be written.

        Returns:
            True if file can be written
        """
        if self.is_readonly:
            return False

        if not self.filepath:
            # No filepath set, can't write
            return False

        if self.filepath.exists():
            # Check existing file
            return os.access(self.filepath, os.W_OK)
        # Check parent directory for new file
        parent = self.filepath.parent
        if parent.exists():
            return os.access(parent, os.W_OK)
        # Parent doesn't exist, check if we can create it
        try:
            # Find first existing parent
            for p in parent.parents:
                if p.exists():
                    return os.access(p, os.W_OK)
        except Exception:
            pass

        return False

    def prompt_for_overwrite(self) -> str:
        """Get prompt message for overwrite confirmation.

        Returns:
            Prompt message if file exists and was modified externally
        """
        if not self.filepath:
            return ""

        if self.check_external_changes():
            return f"WARNING: {self.filepath} has been modified externally. Overwrite? (y/n): "

        return ""


class FileStateManager:
    """Manage file states for multiple buffers."""

    def __init__(self):
        """Initialize the file state manager."""
        self.states: dict[int, FileState] = {}  # buffer_id -> FileState

    def create_state(self, buffer_id: int, filepath: str | Path | None = None) -> FileState:
        """Create a new file state for a buffer.

        Args:
            buffer_id: Buffer identifier
            filepath: Optional initial filepath

        Returns:
            New FileState instance
        """
        state = FileState(filepath=Path(filepath) if filepath else None)
        self.states[buffer_id] = state
        return state

    def get_state(self, buffer_id: int) -> FileState | None:
        """Get file state for a buffer.

        Args:
            buffer_id: Buffer identifier

        Returns:
            FileState or None if not found
        """
        return self.states.get(buffer_id)

    def remove_state(self, buffer_id: int) -> None:
        """Remove file state for a buffer.

        Args:
            buffer_id: Buffer identifier
        """
        self.states.pop(buffer_id, None)

    def get_modified_buffers(self) -> list[int]:
        """Get list of buffer IDs with unsaved changes.

        Returns:
            List of buffer IDs that have modifications
        """
        return [bid for bid, state in self.states.items() if state.is_modified]

    def check_all_external_changes(self) -> dict[int, bool]:
        """Check all buffers for external changes.

        Returns:
            Dict of buffer_id -> has_external_changes
        """
        results = {}
        for buffer_id, state in self.states.items():
            results[buffer_id] = state.check_external_changes()
        return results
