"""Ex command parser for vi editor."""

import re
from dataclasses import dataclass


@dataclass
class ExCommand:
    """Parsed ex command with all its components."""

    command: str  # The actual command (w, q, s, etc.)
    range_start: int | None = None  # Starting line number (1-indexed)
    range_end: int | None = None  # Ending line number (1-indexed)
    args: str = ""  # Command arguments
    flags: str = ""  # Command flags
    force: bool = False  # Force flag (!)
    raw: str = ""  # Original command string


class ExCommandParser:
    """Parse ex commands into structured components."""

    # Command abbreviations mapping
    ABBREVIATIONS = {
        "w": "write",
        "q": "quit",
        "wq": "writequit",
        "x": "exit",
        "e": "edit",
        "r": "read",
        "s": "substitute",
        "se": "set",
        "set": "set",
    }

    # Range patterns
    RANGE_PATTERN = re.compile(
        r"""
        ^
        (?:
            (\d+)                   # Line number
            |(\.)                   # Current line
            |(\$)                   # Last line
            |(\%)                   # All lines
            |('.)                   # Mark
            |(/[^/]+/)              # Forward search
            |(\?[^?]+\?)            # Backward search
        )
        (?:
            ([+\-])(\d+)?           # Offset
        )?
        """,
        re.VERBOSE,
    )

    def parse(self, command_str: str) -> ExCommand | None:
        """Parse an ex command string.

        Args:
            command_str: Ex command string (e.g., ":w file.txt", ":%s/old/new/g")

        Returns:
            Parsed ExCommand object or None if invalid
        """
        if not command_str:
            return None

        # Remove leading colon if present
        if command_str.startswith(":"):
            command_str = command_str[1:]

        # Handle empty command (just ":")
        if not command_str:
            return ExCommand(command="", raw=":")

        # Parse range if present
        range_start, range_end, remainder = self._parse_range(command_str)

        # Special handling for substitution command - check early
        if remainder.startswith("s/") or remainder.startswith("substitute/"):
            return self._parse_substitution(command_str, range_start, range_end)

        # Parse command and arguments
        parts = remainder.split(None, 1)
        if not parts:
            return None

        command_part = parts[0]
        args = parts[1] if len(parts) > 1 else ""

        # Check for force flag
        force = command_part.endswith("!")
        if force:
            command_part = command_part[:-1]

        # Expand abbreviation
        command = self.ABBREVIATIONS.get(command_part, command_part)

        # Handle piped commands
        if "|" in args:
            # For now, just take the first command
            args = args.split("|")[0].strip()

        return ExCommand(
            command=command,
            range_start=range_start,
            range_end=range_end,
            args=args.strip(),
            force=force,
            raw=command_str,
        )

    def _parse_range(self, command_str: str) -> tuple[int | None, int | None, str]:
        """Parse range specification from command.

        Returns:
            Tuple of (start_line, end_line, remainder)
            Line numbers are 1-indexed, None means not specified
        """
        # Check for special range patterns
        if command_str.startswith("%"):
            # % means all lines (1,$)
            return (1, -1, command_str[1:])  # -1 means last line

        if command_str.startswith("."):
            # . means current line
            return (0, 0, command_str[1:])  # 0 means current line

        if command_str.startswith("$"):
            # $ means last line
            return (-1, -1, command_str[1:])

        # Look for numeric ranges like "1,10" or "5"
        match = re.match(r"^(\d+)(?:,(\d+|\$|\.))?\s*", command_str)
        if match:
            start = int(match.group(1))
            if match.group(2):
                if match.group(2) == "$":
                    end = -1  # Last line
                elif match.group(2) == ".":
                    end = 0  # Current line
                else:
                    end = int(match.group(2))
            else:
                end = start
            remainder = command_str[match.end() :]
            return (start, end, remainder)

        # Look for relative ranges like ".,+5" or ".,-3"
        match = re.match(r"^\.([,+\-])(\d+)?\s*", command_str)
        if match:
            operator = match.group(1)
            offset = int(match.group(2)) if match.group(2) else 1

            if operator == ",":
                # .,N means current line to line N
                return (0, offset, command_str[match.end() :])
            if operator == "+":
                # .,+N means current line to current+N
                return (0, offset, command_str[match.end() :])
            if operator == "-":
                # .,-N means current line to current-N
                return (0, -offset, command_str[match.end() :])

        # No range found
        return (None, None, command_str)

    def _parse_substitution(self, command_str: str, range_start: int | None, range_end: int | None) -> ExCommand:
        """Parse substitution command specially.

        Args:
            command_str: Original command string
            range_start: Start of range (if any)
            range_end: End of range (if any)

        Returns:
            ExCommand with parsed substitution
        """
        # Find the 's' or 'substitute' command
        if "substitute" in command_str:
            sub_part = command_str[command_str.index("substitute") + 10 :].lstrip()
        else:
            # Look for 's' command with delimiter
            match = re.search(r"\bs(/.*)", command_str)
            if match:
                sub_part = match.group(1)
            else:
                sub_part = ""

        # Parse substitution pattern
        if sub_part and len(sub_part) > 0:
            delimiter = sub_part[0]
            parts = sub_part.split(delimiter)

            if len(parts) >= 3:
                pattern = parts[1]
                replacement = parts[2]
                flags = parts[3] if len(parts) > 3 else ""

                # Build args string in format: pattern/replacement
                args = f"{pattern}/{replacement}"

                return ExCommand(
                    command="substitute",
                    range_start=range_start,
                    range_end=range_end,
                    args=args,
                    flags=flags,
                    raw=command_str,
                )

        # Invalid substitution format
        return ExCommand(
            command="substitute",
            range_start=range_start,
            range_end=range_end,
            args="",
            flags="",
            raw=command_str,
        )

    def parse_multiple(self, command_str: str) -> list[ExCommand]:
        """Parse multiple commands separated by |.

        Args:
            command_str: Command string possibly containing multiple commands

        Returns:
            List of parsed ExCommand objects
        """
        # Remove leading colon
        if command_str.startswith(":"):
            command_str = command_str[1:]

        # Split by pipe, but be careful with substitution commands
        # that might have | in their patterns
        commands = []
        current = ""
        in_pattern = False
        delimiter = None

        for char in command_str:
            if char == "|" and not in_pattern:
                if current.strip():
                    cmd = self.parse(":" + current.strip())
                    if cmd:
                        commands.append(cmd)
                current = ""
            else:
                current += char

                # Track if we're inside a substitution pattern
                if not in_pattern and current.strip().startswith("s") and len(current) > 1:
                    delimiter = current.strip()[1]
                    in_pattern = True
                elif in_pattern and char == delimiter:
                    # Count delimiters to know when we're done
                    count = current.count(delimiter)
                    if count >= 3:  # s/pattern/replacement/ has 3 delimiters minimum
                        in_pattern = False

        # Don't forget the last command
        if current.strip():
            cmd = self.parse(":" + current.strip())
            if cmd:
                commands.append(cmd)

        return commands
