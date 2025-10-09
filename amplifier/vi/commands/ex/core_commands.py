"""Core ex commands for file operations and editor control."""

import logging
from pathlib import Path

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.file_io.loader import FileLoader
from amplifier.vi.file_io.saver import FileSaver

from .parser import ExCommand

logger = logging.getLogger(__name__)


class ExCoreCommands:
    """Handle core ex commands like write, quit, edit."""

    def __init__(self, buffer: TextBuffer):
        """Initialize with text buffer.

        Args:
            buffer: The text buffer instance
        """
        self.buffer = buffer
        self.loader = FileLoader()
        self.saver = FileSaver()
        self.current_file: Path | None = None
        self.encoding = "utf-8"
        self.line_ending = "\n"
        self.modified = False

    def execute(self, command: ExCommand) -> tuple[bool, str]:
        """Execute a core command.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        handlers = {
            "write": self._handle_write,
            "writequit": self._handle_writequit,
            "quit": self._handle_quit,
            "exit": self._handle_exit,
            "edit": self._handle_edit,
            "read": self._handle_read,
        }

        handler = handlers.get(command.command)
        if not handler:
            return (False, f"Unknown command: {command.command}")

        try:
            return handler(command)
        except Exception as e:
            logger.error(f"Error executing {command.command}: {e}")
            return (False, str(e))

    def _handle_write(self, command: ExCommand) -> tuple[bool, str]:
        """Handle :w[rite] command.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        # Determine target file
        if command.args:
            target_file = Path(command.args.strip())
        elif self.current_file:
            target_file = self.current_file
        else:
            return (False, "No file name")

        # Handle range (partial write)
        content = self._get_content_for_range(command)

        # Save file
        success = self.saver.save_file(
            target_file,
            content,
            encoding=self.encoding,
            line_ending=self.line_ending,
            create_backup=not command.force,
        )

        if success:
            # Update current file if writing whole buffer
            if not command.range_start and not command.range_end:
                self.current_file = target_file
                self.modified = False

            line_count = len(content.split("\n"))
            char_count = len(content)
            return (True, f'"{target_file}" {line_count}L, {char_count}C written')
        return (False, f"Failed to write {target_file}")

    def _handle_quit(self, command: ExCommand) -> tuple[bool, str]:
        """Handle :q[uit] command.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        if self.modified and not command.force:
            return (False, "No write since last change (add ! to override)")

        # This would trigger actual quit in the main application
        return (True, "quit")

    def _handle_writequit(self, command: ExCommand) -> tuple[bool, str]:
        """Handle :wq command.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        # First write
        success, msg = self._handle_write(command)
        if not success:
            return (False, msg)

        # Then quit
        return (True, "quit")

    def _handle_exit(self, command: ExCommand) -> tuple[bool, str]:
        """Handle :x command - write if modified and quit.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        if self.modified:
            success, msg = self._handle_write(command)
            if not success:
                return (False, msg)

        return (True, "quit")

    def _handle_edit(self, command: ExCommand) -> tuple[bool, str]:
        """Handle :e[dit] command.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        # Check for unsaved changes
        if self.modified and not command.force:
            return (False, "No write since last change (add ! to override)")

        # Determine file to edit
        if command.args:
            target_file = Path(command.args.strip())
        elif self.current_file and command.force:
            # :e! reloads current file
            target_file = self.current_file
        else:
            return (False, "No file name")

        # Load file
        content, encoding, line_ending = self.loader.load_file(target_file)

        # Update buffer
        self.buffer._lines = content.split("\n") if content else [""]
        self.buffer.set_cursor(0, 0)

        # Update state
        self.current_file = target_file
        self.encoding = encoding
        self.line_ending = line_ending
        self.modified = False

        if target_file.exists():
            line_count = len(self.buffer.get_lines())
            char_count = len(content)
            return (True, f'"{target_file}" {line_count}L, {char_count}C')
        return (True, f'"{target_file}" [New File]')

    def _handle_read(self, command: ExCommand) -> tuple[bool, str]:
        """Handle :r[ead] command - read file into buffer at cursor.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        if not command.args:
            return (False, "No file name")

        target_file = Path(command.args.strip())

        # Load file content
        content, _, _ = self.loader.load_file(target_file)

        if not target_file.exists():
            return (False, f'"{target_file}" [No such file]')

        # Insert at cursor position or after specified line
        if command.range_start is not None:
            insert_row = self._resolve_line_number(command.range_start)
        else:
            insert_row = self.buffer.get_cursor()[0]

        # Insert content
        lines = content.split("\n") if content else []
        for i, line in enumerate(lines):
            self.buffer._lines.insert(insert_row + i + 1, line)

        self.modified = True

        line_count = len(lines)
        char_count = len(content)
        return (True, f'"{target_file}" {line_count}L, {char_count}C')

    def _get_content_for_range(self, command: ExCommand) -> str:
        """Get buffer content for specified range.

        Args:
            command: Ex command with range info

        Returns:
            Content string for the range
        """
        lines = self.buffer.get_lines()

        # No range means entire buffer
        if command.range_start is None and command.range_end is None:
            return "\n".join(lines)

        # Resolve line numbers
        start = self._resolve_line_number(command.range_start) if command.range_start is not None else 0
        end = self._resolve_line_number(command.range_end) if command.range_end is not None else start

        # Ensure valid range
        start = max(0, min(start, len(lines) - 1))
        end = max(start, min(end, len(lines) - 1))

        # Extract lines (inclusive)
        return "\n".join(lines[start : end + 1])

    def _resolve_line_number(self, line_spec: int) -> int:
        """Resolve a line specification to actual line number.

        Args:
            line_spec: Line specification (1-indexed, 0=current, -1=last)

        Returns:
            0-indexed line number
        """
        if line_spec == 0:
            # Current line
            return self.buffer.get_cursor()[0]
        if line_spec == -1:
            # Last line
            return len(self.buffer.get_lines()) - 1
        if line_spec > 0:
            # Convert from 1-indexed to 0-indexed
            return line_spec - 1
        # Relative offset from current line
        current = self.buffer.get_cursor()[0]
        return max(0, current + line_spec)

    def set_modified(self, modified: bool) -> None:
        """Set the modified flag.

        Args:
            modified: Whether buffer has been modified
        """
        self.modified = modified

    def set_current_file(self, filepath: Path | None) -> None:
        """Set the current file path.

        Args:
            filepath: File path or None
        """
        self.current_file = filepath
