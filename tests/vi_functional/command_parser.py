"""Parser for vi command script files (.vicmd format)."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class TestCommand:
    """Represents a parsed test command."""

    input_file: str
    expected_output: str
    description: str
    commands: list[str]
    timeout: int = 5


class CommandParser:
    """Parse .vicmd test files into executable commands."""

    SPECIAL_KEYS = {
        "<ESC>": "\x1b",
        "<CR>": "\r",
        "<ENTER>": "\r",
        "<TAB>": "\t",
        "<BS>": "\x7f",
        "<BACKSPACE>": "\x7f",
        "<DEL>": "\x7f",
        "<DELETE>": "\x7f",
        "<SPACE>": " ",
        "<CTRL-O>": "\x0f",
        "<CTRL-I>": "\x09",
        "<CTRL-R>": "\x12",
    }

    def __init__(self, vicmd_path: str | Path):
        """Initialize parser with path to .vicmd file.

        Args:
            vicmd_path: Path to .vicmd test file
        """
        self.vicmd_path = Path(vicmd_path)
        if not self.vicmd_path.exists():
            raise FileNotFoundError(f"Test file not found: {vicmd_path}")

    def parse(self) -> TestCommand:
        """Parse the .vicmd file and return TestCommand.

        Returns:
            TestCommand object with all parsed information

        Raises:
            ValueError: If required directives are missing or invalid
        """
        with open(self.vicmd_path, encoding="utf-8") as f:
            lines = f.readlines()

        input_file = None
        expected_output = None
        description = "No description"
        timeout = 5
        commands = []

        for line in lines:
            line = line.rstrip("\n")

            # Skip empty lines
            if not line.strip():
                continue

            # Parse directives
            if line.startswith("@INPUT_FILE"):
                input_file = line.split(maxsplit=1)[1].strip()
            elif line.startswith("@EXPECTED_OUTPUT"):
                expected_output = line.split(maxsplit=1)[1].strip()
            elif line.startswith("@DESCRIPTION"):
                description = line.split(maxsplit=1)[1].strip()
            elif line.startswith("@TIMEOUT"):
                timeout = int(line.split(maxsplit=1)[1].strip())
            elif line.startswith("#"):
                # Skip comment lines
                continue
            else:
                # Command line - parse it
                parsed_command = self._parse_command_line(line)
                if parsed_command:
                    commands.append(parsed_command)

        # Validate required fields
        if not input_file:
            raise ValueError(f"Missing @INPUT_FILE directive in {self.vicmd_path}")
        if not expected_output:
            raise ValueError(f"Missing @EXPECTED_OUTPUT directive in {self.vicmd_path}")
        if not commands:
            raise ValueError(f"No commands found in {self.vicmd_path}")

        return TestCommand(
            input_file=input_file,
            expected_output=expected_output,
            description=description,
            commands=commands,
            timeout=timeout,
        )

    def _parse_command_line(self, line: str) -> str:
        """Parse a command line, converting special key notation.

        Args:
            line: Raw command line from .vicmd file

        Returns:
            Parsed command string with special keys converted
        """
        # Remove inline comments
        if "#" in line:
            # Find comment start (not escaped)
            parts = line.split("#")
            if len(parts) > 1:
                line = parts[0].rstrip()

        if not line.strip():
            return ""

        # Replace special key sequences
        for key_name, key_char in self.SPECIAL_KEYS.items():
            line = line.replace(key_name, key_char)

        return line

    @staticmethod
    def validate_files(test_cmd: TestCommand, fixtures_dir: Path) -> tuple[bool, str]:
        """Validate that required files exist.

        Args:
            test_cmd: Parsed test command
            fixtures_dir: Directory containing fixture files

        Returns:
            Tuple of (success, error_message)
        """
        input_path = fixtures_dir / test_cmd.input_file
        if not input_path.exists():
            return False, f"Input file not found: {input_path}"

        expected_path = fixtures_dir / test_cmd.expected_output
        if not expected_path.exists():
            return False, f"Expected output file not found: {expected_path}"

        return True, ""
