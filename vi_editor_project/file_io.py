#!/usr/bin/env python3
"""
File I/O operations for vi editor.

Handles reading and writing files, managing file metadata,
and dealing with permissions and errors.
"""

import contextlib
import os
import shutil
from datetime import datetime
from pathlib import Path


class FileIOError(Exception):
    """Custom exception for file I/O errors."""

    pass


class FileIO:
    """Handles all file I/O operations for the vi editor."""

    def __init__(self):
        self.current_file: Path | None = None
        self.original_content: list[str] | None = None
        self.last_saved: datetime | None = None
        self.backup_enabled = True
        self.encoding = "utf-8"

    def read_file(self, filepath: str | Path) -> list[str]:
        """
        Read a file and return its contents as a list of lines.

        Args:
            filepath: Path to the file to read

        Returns:
            List of lines from the file (without newline characters)

        Raises:
            FileIOError: If file cannot be read
        """
        filepath = Path(filepath).expanduser().resolve()

        try:
            if not filepath.exists():
                # New file - return empty content
                self.current_file = filepath
                self.original_content = []
                return []

            if not filepath.is_file():
                raise FileIOError(f"'{filepath}' is not a regular file")

            # Check read permissions
            if not os.access(filepath, os.R_OK):
                raise FileIOError(f"Permission denied: cannot read '{filepath}'")

            # Read the file
            with open(filepath, encoding=self.encoding) as f:
                lines = f.read().splitlines()

            self.current_file = filepath
            self.original_content = lines.copy()
            return lines

        except PermissionError:
            raise FileIOError(f"Permission denied: cannot read '{filepath}'")
        except UnicodeDecodeError:
            raise FileIOError(f"Cannot decode '{filepath}' with {self.encoding} encoding")
        except OSError as e:
            raise FileIOError(f"Error reading '{filepath}': {e}")

    def write_file(
        self,
        filepath: str | Path | None,
        content: list[str],
        force: bool = False,
        append: bool = False,
    ) -> None:
        """
        Write content to a file.

        Args:
            filepath: Path to write to (None uses current file)
            content: List of lines to write
            force: Force write even if file has external modifications
            append: Append to file instead of overwriting

        Raises:
            FileIOError: If file cannot be written
        """
        if filepath is None:
            if self.current_file is None:
                raise FileIOError("No file name")
            filepath = self.current_file
        else:
            filepath = Path(filepath).expanduser().resolve()

        # Check write permissions for existing files
        if filepath.exists():
            if not os.access(filepath, os.W_OK):
                raise FileIOError(f"Permission denied: cannot write '{filepath}'")

            # Check for external modifications
            if not force and filepath == self.current_file and self._file_modified_externally():
                raise FileIOError(f"Warning: '{filepath}' has been modified externally. Use :w! to override")

        # Check parent directory permissions for new files
        elif not os.access(filepath.parent, os.W_OK):
            raise FileIOError(f"Permission denied: cannot create '{filepath}'")

        try:
            # Create backup if enabled
            if self.backup_enabled and filepath.exists():
                self._create_backup(filepath)

            # Write the file
            mode = "a" if append else "w"
            with open(filepath, mode, encoding=self.encoding) as f:
                for i, line in enumerate(content):
                    f.write(line)
                    if i < len(content) - 1 or line:  # Add newline except for last empty line
                        f.write("\n")

            self.last_saved = datetime.now()

            # Update current file if writing to a new file
            if filepath != self.current_file:
                self.current_file = filepath
                self.original_content = content.copy()

        except PermissionError:
            raise FileIOError(f"Permission denied: cannot write '{filepath}'")
        except OSError as e:
            raise FileIOError(f"Error writing '{filepath}': {e}")

    def save_file(self, content: list[str], force: bool = False) -> None:
        """
        Save content to the current file.

        Args:
            content: Content to save
            force: Force save even with external modifications

        Raises:
            FileIOError: If no current file or cannot save
        """
        if self.current_file is None:
            raise FileIOError("No file name")

        self.write_file(None, content, force)
        self.original_content = content.copy()

    def _file_modified_externally(self) -> bool:
        """Check if the current file has been modified externally."""
        if self.current_file is None or not self.current_file.exists():
            return False

        # For now, we'll skip external modification detection
        # In a full implementation, we'd track file mtime
        return False

    def _create_backup(self, filepath: Path) -> None:
        """Create a backup of the file before overwriting."""

        backup_path = filepath.with_suffix(filepath.suffix + "~")
        with contextlib.suppress(OSError, shutil.Error):
            shutil.copy2(filepath, backup_path)

    def has_unsaved_changes(self, current_content: list[str]) -> bool:
        """
        Check if there are unsaved changes.

        Args:
            current_content: Current buffer content

        Returns:
            True if content differs from original
        """
        if self.original_content is None:
            return len(current_content) > 0

        return current_content != self.original_content

    def get_file_info(self) -> dict:
        """
        Get information about the current file.

        Returns:
            Dictionary with file information
        """
        if self.current_file is None:
            return {
                "filename": "[No Name]",
                "exists": False,
                "size": 0,
                "modified": False,
                "readonly": False,
            }

        exists = self.current_file.exists()
        return {
            "filename": str(self.current_file),
            "exists": exists,
            "size": self.current_file.stat().st_size if exists else 0,
            "modified": self.last_saved is not None,
            "readonly": not os.access(self.current_file, os.W_OK) if exists else False,
        }


class ExCommandHandler:
    """Handles ex commands related to file I/O."""

    def __init__(self, file_io: FileIO):
        self.file_io = file_io

    def handle_write(self, args: str, buffer_content: list[str]) -> tuple[bool, str]:
        """
        Handle :w command variants.

        Args:
            args: Arguments to the write command
            buffer_content: Current buffer content

        Returns:
            (success, message) tuple
        """
        force = args.endswith("!")
        if force:
            args = args[:-1].strip()

        # Parse filename if provided
        filename = args.strip() if args.strip() else None

        # Handle append mode (>>)
        append = False
        if filename and filename.startswith(">>"):
            append = True
            filename = filename[2:].strip()

        try:
            if filename:
                self.file_io.write_file(filename, buffer_content, force, append)
                return True, f'"{filename}" written'
            self.file_io.save_file(buffer_content, force)
            lines = len(buffer_content)
            return True, f'"{self.file_io.current_file}" {lines}L written'

        except FileIOError as e:
            return False, str(e)

    def handle_quit(self, force: bool, buffer_content: list[str]) -> tuple[bool, str]:
        """
        Handle :q command variants.

        Args:
            force: Whether to force quit (:q!)
            buffer_content: Current buffer content

        Returns:
            (can_quit, message) tuple
        """
        if not force and self.file_io.has_unsaved_changes(buffer_content):
            return False, "No write since last change (add ! to override)"

        return True, ""

    def handle_edit(self, filename: str) -> tuple[bool, list[str], str]:
        """
        Handle :e command to open a file.

        Args:
            filename: File to open

        Returns:
            (success, content, message) tuple
        """
        if not filename:
            return False, [], "No file name"

        try:
            content = self.file_io.read_file(filename)
            return True, content, f'"{filename}" {len(content)}L'

        except FileIOError as e:
            return False, [], str(e)

    def handle_write_quit(self, args: str, buffer_content: list[str]) -> tuple[bool, str]:
        """
        Handle :wq command.

        Args:
            args: Arguments (typically empty)
            buffer_content: Current buffer content

        Returns:
            (success, message) tuple
        """
        success, message = self.handle_write(args, buffer_content)
        if success:
            return True, message

        return False, message


def integrate_file_io_with_editor(editor):
    """
    Integrate file I/O capabilities with an editor instance.

    This function adds file I/O handling to the editor's ex command processing.

    Args:
        editor: Editor instance to enhance with file I/O
    """
    file_io = FileIO()
    ex_handler = ExCommandHandler(file_io)

    # Store original ex command handler if it exists
    original_handle_ex = getattr(editor, "handle_ex_command", None)

    def enhanced_handle_ex_command(command: str) -> tuple[bool, str]:
        """Enhanced ex command handler with file I/O support."""
        cmd_parts = command.split(None, 1)
        if not cmd_parts:
            return False, ""

        cmd = cmd_parts[0].lower()
        args = cmd_parts[1] if len(cmd_parts) > 1 else ""

        # File I/O commands
        if cmd in ["w", "write"]:
            return ex_handler.handle_write(args, editor.buffer.lines)

        if cmd in ["q", "quit"]:
            force = cmd.endswith("!") or args.startswith("!")
            return ex_handler.handle_quit(force, editor.buffer.lines)

        if cmd in ["wq", "x"]:
            return ex_handler.handle_write_quit(args, editor.buffer.lines)

        if cmd == "q!":
            return True, ""  # Force quit

        if cmd in ["e", "edit"]:
            success, content, message = ex_handler.handle_edit(args)
            if success:
                editor.buffer.lines = content
                editor.buffer.cursor_line = 0
                editor.buffer.cursor_col = 0
            return success, message

        # Fall back to original handler if it exists
        if original_handle_ex:
            return original_handle_ex(command)

        return False, f"Unknown command: {cmd}"

    # Replace the ex command handler
    editor.handle_ex_command = enhanced_handle_ex_command

    # Add file_io reference to editor for direct access
    editor.file_io = file_io

    return editor
