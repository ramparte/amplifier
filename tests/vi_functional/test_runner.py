"""Test runner for vi editor golden-master tests."""

import difflib
import re
import time
from dataclasses import dataclass
from pathlib import Path

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.executor import CommandExecutor
from amplifier.vi.modes.state import ModeManager

from .command_parser import CommandParser


@dataclass
class TestResult:
    """Result of running a single test."""

    name: str
    passed: bool
    duration: float
    error: str = ""
    diff: str = ""


class ViTestRunner:
    """Execute vi command tests and validate output."""

    def __init__(self, fixtures_dir: Path):
        """Initialize test runner.

        Args:
            fixtures_dir: Directory containing input/output fixture files
        """
        self.fixtures_dir = Path(fixtures_dir)
        if not self.fixtures_dir.exists():
            raise ValueError(f"Fixtures directory not found: {fixtures_dir}")

    def run_test(self, vicmd_path: Path) -> TestResult:
        """Run a single test from a .vicmd file.

        Args:
            vicmd_path: Path to .vicmd test file

        Returns:
            TestResult with pass/fail status and details
        """
        start_time = time.time()
        test_name = vicmd_path.stem

        try:
            # Parse test file
            parser = CommandParser(vicmd_path)
            test_cmd = parser.parse()

            # Validate files exist
            valid, error = parser.validate_files(test_cmd, self.fixtures_dir)
            if not valid:
                duration = time.time() - start_time
                return TestResult(name=test_name, passed=False, duration=duration, error=error)

            # Load input file
            input_path = self.fixtures_dir / test_cmd.input_file
            with open(input_path, encoding="utf-8") as f:
                input_content = f.read()

            # Execute commands
            try:
                output_content = self._execute_commands(input_content, test_cmd.commands, test_cmd.timeout)
            except TimeoutError:
                duration = time.time() - start_time
                return TestResult(
                    name=test_name, passed=False, duration=duration, error=f"Test timed out after {test_cmd.timeout}s"
                )
            except Exception as e:
                duration = time.time() - start_time
                return TestResult(name=test_name, passed=False, duration=duration, error=f"Execution error: {e}")

            # Load expected output
            expected_path = self.fixtures_dir / test_cmd.expected_output
            with open(expected_path, encoding="utf-8") as f:
                expected_content = f.read()

            # Compare outputs
            if output_content == expected_content:
                duration = time.time() - start_time
                return TestResult(name=test_name, passed=True, duration=duration)

            # Generate diff for failure
            diff = self._generate_diff(expected_content, output_content, test_name)
            duration = time.time() - start_time
            return TestResult(name=test_name, passed=False, duration=duration, error="Output mismatch", diff=diff)

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(name=test_name, passed=False, duration=duration, error=f"Test error: {e}")

    def _execute_commands(self, initial_content: str, commands: list[str], timeout: int) -> str:
        """Execute vi commands on content and return final state.

        Args:
            initial_content: Initial buffer content
            commands: List of command strings to execute
            timeout: Maximum execution time in seconds

        Returns:
            Final buffer content after commands

        Raises:
            TimeoutError: If execution exceeds timeout
        """
        start_time = time.time()

        # Initialize vi components (without terminal)
        buffer = TextBuffer(initial_content)
        modes = ModeManager()
        executor = CommandExecutor(buffer, modes, renderer=None)  # No renderer for tests

        # Track if we're building a command line command
        command_buffer = ""
        in_command_mode = False

        # Execute each command
        for cmd_str in commands:
            if time.time() - start_time > timeout:
                raise TimeoutError()

            for char in cmd_str:
                # Handle command mode specially
                if char == ":":
                    in_command_mode = True
                    command_buffer = ""
                    modes.to_command()
                    continue

                if in_command_mode:
                    if char == "\r" or char == "\n":  # Execute command
                        self._execute_ex_command(buffer, command_buffer)
                        command_buffer = ""
                        in_command_mode = False
                        modes.to_normal()
                    elif char == "\x1b":  # Cancel command
                        command_buffer = ""
                        in_command_mode = False
                        modes.to_normal()
                    else:
                        command_buffer += char
                    continue

                # Execute based on mode
                mode = modes.get_mode()
                if mode == ModeManager.NORMAL:
                    executor.execute_normal_command(char)
                elif mode == ModeManager.INSERT:
                    executor.execute_insert_command(char)
                elif mode == ModeManager.VISUAL:
                    executor.execute_visual_command(char)

        return buffer.get_content()

    def _execute_ex_command(self, buffer: TextBuffer, command: str) -> None:
        """Execute an ex command line command.

        Args:
            buffer: Text buffer to operate on
            command: Command string (without leading :)
        """

        # Handle basic commands
        if command == "q" or command == "q!":
            # Quit is a no-op in tests
            pass
        elif command == "w":
            # Write is a no-op in tests (we capture buffer content directly)
            pass
        elif command == "wq":
            # Write and quit
            pass
        elif self._is_substitute_command(command):
            self._execute_substitute(buffer, command)

    def _is_substitute_command(self, command: str) -> bool:
        """Check if command is a substitute command."""
        patterns = [
            r"^\d*,?\d*s/",
            r"^%s/",
            r"^s/",
        ]
        return any(re.match(pattern, command) for pattern in patterns)

    def _execute_substitute(self, buffer: TextBuffer, command: str) -> None:
        """Execute a substitute command on buffer."""
        import re

        # Parse substitute command
        match = re.match(r"^(?:(\d+),(\d+)|(%))?\s*s/((?:[^/\\]|\\.)*)/((?:[^/\\]|\\.)*)/?([gi]*)$", command)

        if not match:
            return

        start_line_str, end_line_str, percent, pattern, replacement, flags = match.groups()

        # Determine range
        if percent:
            start_row = 0
            end_row = len(buffer.get_lines()) - 1
        elif start_line_str and end_line_str:
            start_row = int(start_line_str) - 1
            end_row = int(end_line_str) - 1
        else:
            start_row, _ = buffer.get_cursor()
            end_row = start_row

        # Unescape pattern and replacement
        pattern = pattern.replace(r"\/", "/")
        replacement = replacement.replace(r"\/", "/")

        # Execute substitution
        buffer.substitute_range(start_row, end_row, pattern, replacement, flags)

    def _generate_diff(self, expected: str, actual: str, test_name: str) -> str:
        """Generate unified diff between expected and actual output.

        Args:
            expected: Expected content
            actual: Actual content
            test_name: Name of test for diff headers

        Returns:
            Unified diff string
        """
        expected_lines = expected.splitlines(keepends=True)
        actual_lines = actual.splitlines(keepends=True)

        diff = difflib.unified_diff(
            expected_lines, actual_lines, fromfile=f"expected/{test_name}", tofile=f"actual/{test_name}", lineterm=""
        )

        return "".join(diff)

    def run_tests(self, test_dir: Path) -> list[TestResult]:
        """Run all .vicmd tests in a directory.

        Args:
            test_dir: Directory containing .vicmd test files

        Returns:
            List of TestResult objects
        """
        test_files = sorted(Path(test_dir).glob("*.vicmd"))
        results = []

        for test_file in test_files:
            result = self.run_test(test_file)
            results.append(result)

        return results
