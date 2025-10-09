"""Register manager for vi buffer - integrates with editing/registers.py."""

from typing import TYPE_CHECKING

from ..commands.editing.registers import RegisterContent
from ..commands.editing.registers import RegisterManager as BaseRegisterManager

if TYPE_CHECKING:
    from .core import TextBuffer


class BufferRegisterManager:
    """Register manager integrated with text buffer for vi operations."""

    def __init__(self):
        """Initialize the buffer register manager."""
        self._register_manager = BaseRegisterManager()

    def yank_text(self, text: str, register: str | None = None, is_linewise: bool = False) -> None:
        """Yank (copy) text to a register.

        Args:
            text: Text to yank
            register: Register name (None for unnamed)
            is_linewise: Whether this was a line-based operation
        """
        self._register_manager.set(register, text, is_linewise=is_linewise)

    def yank_lines(self, buffer: "TextBuffer", start_row: int, count: int, register: str | None = None) -> str:
        """Yank complete lines from the buffer.

        Args:
            buffer: TextBuffer instance
            start_row: Starting row to yank
            count: Number of lines to yank
            register: Target register (None for unnamed)

        Returns:
            The yanked text
        """
        lines = buffer.get_lines()
        end_row = min(start_row + count, len(lines))

        # Extract lines with newlines
        yanked_lines = lines[start_row:end_row]
        yanked_text = "\n".join(yanked_lines) + "\n"  # Add trailing newline for linewise

        # Store in register
        self.yank_text(yanked_text, register, is_linewise=True)

        return yanked_text

    def yank_region(
        self,
        buffer: "TextBuffer",
        start_row: int,
        start_col: int,
        end_row: int,
        end_col: int,
        register: str | None = None,
    ) -> str:
        """Yank a region of text from the buffer.

        Args:
            buffer: TextBuffer instance
            start_row, start_col: Start position
            end_row, end_col: End position
            register: Target register (None for unnamed)

        Returns:
            The yanked text
        """
        lines = buffer.get_lines()

        # Ensure positions are valid
        start_row = max(0, min(start_row, len(lines) - 1))
        end_row = max(0, min(end_row, len(lines) - 1))

        # Single line
        if start_row == end_row:
            line = lines[start_row]
            yanked_text = line[start_col:end_col]
        else:
            # Multiple lines
            result = []
            for row in range(start_row, end_row + 1):
                line = lines[row]
                if row == start_row:
                    result.append(line[start_col:])
                elif row == end_row:
                    result.append(line[:end_col])
                else:
                    result.append(line)
            yanked_text = "\n".join(result)

        # Store in register
        self.yank_text(yanked_text, register, is_linewise=False)

        return yanked_text

    def delete_and_yank(self, text: str, register: str | None = None, is_linewise: bool = False) -> None:
        """Store deleted text in register (for d, c, x commands).

        Args:
            text: Deleted text
            register: Register name (None for unnamed, '_' for black hole)
            is_linewise: Whether this was a line-based deletion
        """
        # Don't store single character deletions in numbered registers
        # unless explicitly targeting a register
        if register is None and len(text) == 1 and not is_linewise:
            # Still store in unnamed register but not numbered
            self._register_manager.state.unnamed = RegisterContent(text, is_linewise)
        else:
            self._register_manager.set(register, text, is_linewise=is_linewise, is_delete=True)

    def put_after(self, buffer: "TextBuffer", register: str | None = None, count: int = 1) -> bool:
        """Put (paste) register content after cursor position.

        Args:
            buffer: TextBuffer instance
            register: Source register (None for unnamed)
            count: Number of times to paste

        Returns:
            True if successful, False if register was empty
        """
        content = self._register_manager.get(register)
        if not content or not content.text:
            return False

        row, col = buffer.get_cursor()

        for _ in range(count):
            if content.is_linewise:
                # Linewise put - insert after current line
                new_lines = content.text.rstrip("\n").split("\n")

                # Insert after current line
                for i, line in enumerate(new_lines):
                    buffer._lines.insert(row + 1 + i, line)

                # Move cursor to first non-blank of first pasted line
                buffer.set_cursor(row + 1, 0)
                buffer.move_to_first_non_blank()
            else:
                # Character-wise put - insert after cursor
                # Move cursor right first (unless at end of line)
                line = buffer.get_current_line()
                if col < len(line):
                    buffer.move_cursor_right()

                # Insert the text
                buffer.insert_text(content.text)

        return True

    def put_before(self, buffer: "TextBuffer", register: str | None = None, count: int = 1) -> bool:
        """Put (paste) register content before cursor position.

        Args:
            buffer: TextBuffer instance
            register: Source register (None for unnamed)
            count: Number of times to paste

        Returns:
            True if successful, False if register was empty
        """
        content = self._register_manager.get(register)
        if not content or not content.text:
            return False

        row, col = buffer.get_cursor()

        for _ in range(count):
            if content.is_linewise:
                # Linewise put - insert before current line
                new_lines = content.text.rstrip("\n").split("\n")

                # Insert before current line
                for i, line in enumerate(new_lines):
                    buffer._lines.insert(row + i, line)

                # Move cursor to first non-blank of first pasted line
                buffer.set_cursor(row, 0)
                buffer.move_to_first_non_blank()
            else:
                # Character-wise put - insert at cursor
                buffer.insert_text(content.text)

        return True

    def get_register_content(self, register: str | None = None) -> RegisterContent | None:
        """Get content from a register.

        Args:
            register: Register name (None for unnamed)

        Returns:
            RegisterContent or None if empty
        """
        return self._register_manager.get(register)

    def clear(self, register: str | None = None) -> None:
        """Clear register(s).

        Args:
            register: Specific register to clear, or None for all
        """
        self._register_manager.clear(register)

    def list_registers(self) -> dict[str, str]:
        """Get a list of all non-empty registers for display.

        Returns:
            Dictionary mapping register names to their content (truncated)
        """
        return self._register_manager.get_register_list()

    @property
    def manager(self) -> BaseRegisterManager:
        """Get the underlying register manager for direct access."""
        return self._register_manager
