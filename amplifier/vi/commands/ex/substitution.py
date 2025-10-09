"""Substitution command implementation for ex mode."""

import re
from collections.abc import Callable

from amplifier.vi.buffer.core import TextBuffer

from .parser import ExCommand


class ExSubstitution:
    """Handle substitution commands in ex mode."""

    def __init__(self, buffer: TextBuffer):
        """Initialize with text buffer.

        Args:
            buffer: The text buffer instance
        """
        self.buffer = buffer
        self.last_pattern: str | None = None
        self.last_replacement: str | None = None
        self.last_flags: str = ""

    def execute(self, command: ExCommand) -> tuple[bool, str]:
        """Execute a substitution command.

        Args:
            command: Parsed ex command with substitution info

        Returns:
            Tuple of (success, message)
        """
        # Parse pattern and replacement from args
        if "/" in command.args:
            parts = command.args.split("/", 1)
            pattern = parts[0]
            replacement = parts[1] if len(parts) > 1 else ""
        else:
            # Use last pattern/replacement if available
            if not self.last_pattern:
                return (False, "No previous substitute pattern")
            pattern = self.last_pattern
            replacement = self.last_replacement or ""

        # Save for repeat
        self.last_pattern = pattern
        self.last_replacement = replacement
        self.last_flags = command.flags

        # Determine range
        start_line, end_line = self._get_range(command)

        # Parse flags
        global_flag = "g" in command.flags
        ignore_case = "i" in command.flags
        confirm = "c" in command.flags

        # Compile regex
        try:
            re_flags = re.IGNORECASE if ignore_case else 0
            regex = re.compile(pattern, re_flags)
        except re.error as e:
            return (False, f"Invalid pattern: {e}")

        # Perform substitution
        if confirm:
            count = self._substitute_with_confirm(regex, replacement, start_line, end_line, global_flag)
        else:
            count = self._substitute(regex, replacement, start_line, end_line, global_flag)

        # Report results
        if count == 0:
            return (True, "Pattern not found")
        if count == 1:
            return (True, "1 substitution")
        return (True, f"{count} substitutions")

    def _get_range(self, command: ExCommand) -> tuple[int, int]:
        """Get line range for substitution.

        Args:
            command: Ex command with range info

        Returns:
            Tuple of (start_line, end_line) as 0-indexed line numbers
        """
        lines = self.buffer.get_lines()
        current_line = self.buffer.get_cursor()[0]

        # Default to current line if no range specified
        if command.range_start is None and command.range_end is None:
            return (current_line, current_line)

        # Resolve start line
        if command.range_start is None or command.range_start == 0:
            start = current_line
        elif command.range_start == -1:
            start = len(lines) - 1
        elif command.range_start > 0:
            start = command.range_start - 1  # Convert to 0-indexed
        else:
            start = max(0, current_line + command.range_start)

        # Resolve end line
        if command.range_end is None:
            end = start
        elif command.range_end == 0:
            end = current_line
        elif command.range_end == -1:
            end = len(lines) - 1
        elif command.range_end > 0:
            # Handle relative ranges like .,+5
            if command.range_start == 0 and command.range_end <= 100:
                # This might be a relative offset
                end = min(current_line + command.range_end, len(lines) - 1)
            else:
                end = command.range_end - 1  # Convert to 0-indexed
        else:
            end = max(0, current_line + command.range_end)

        # Ensure valid range
        start = max(0, min(start, len(lines) - 1))
        end = max(start, min(end, len(lines) - 1))

        return (start, end)

    def _substitute(
        self, regex: re.Pattern, replacement: str, start_line: int, end_line: int, global_flag: bool
    ) -> int:
        """Perform substitution without confirmation.

        Args:
            regex: Compiled regex pattern
            replacement: Replacement string
            start_line: Starting line (0-indexed)
            end_line: Ending line (0-indexed, inclusive)
            global_flag: Whether to replace all occurrences

        Returns:
            Number of substitutions made
        """
        lines = self.buffer.get_lines()
        total_count = 0

        # Save state before modifications
        self.buffer.save_state()

        for line_num in range(start_line, min(end_line + 1, len(lines))):
            line = lines[line_num]

            if global_flag:
                # Replace all occurrences
                new_line, count = regex.subn(replacement, line)
            else:
                # Replace first occurrence only
                new_line, count = regex.subn(replacement, line, count=1)

            if count > 0:
                self.buffer._lines[line_num] = new_line
                total_count += count

        return total_count

    def _substitute_with_confirm(
        self,
        regex: re.Pattern,
        replacement: str,
        start_line: int,
        end_line: int,
        global_flag: bool,
        confirm_callback: Callable[[str, str, int], bool] | None = None,
    ) -> int:
        """Perform substitution with confirmation for each match.

        Args:
            regex: Compiled regex pattern
            replacement: Replacement string
            start_line: Starting line (0-indexed)
            end_line: Ending line (0-indexed, inclusive)
            global_flag: Whether to replace all occurrences
            confirm_callback: Optional callback for confirmation (for testing)

        Returns:
            Number of substitutions made
        """
        lines = self.buffer.get_lines()
        total_count = 0

        # Save state before modifications
        self.buffer.save_state()

        for line_num in range(start_line, min(end_line + 1, len(lines))):
            line = lines[line_num]
            new_line = line
            line_count = 0

            # Find all matches in the line
            for match in regex.finditer(line):
                if not global_flag and line_count > 0:
                    break

                # For actual implementation, this would need UI interaction
                # For now, we'll just confirm all if no callback provided
                if confirm_callback:
                    should_replace = confirm_callback(match.group(), replacement, line_num)
                else:
                    should_replace = True

                if should_replace:
                    # Replace this specific match
                    start, end = match.span()
                    new_line = new_line[:start] + replacement + new_line[end:]
                    line_count += 1

            if line_count > 0:
                self.buffer._lines[line_num] = new_line
                total_count += line_count

        return total_count

    def repeat_last(self) -> tuple[bool, str]:
        """Repeat the last substitution.

        Returns:
            Tuple of (success, message)
        """
        if not self.last_pattern:
            return (False, "No previous substitute pattern")

        # Create a command with saved pattern/replacement
        command = ExCommand(
            command="substitute",
            args=f"{self.last_pattern}/{self.last_replacement or ''}",
            flags=self.last_flags,
        )

        return self.execute(command)
