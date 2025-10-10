"""Test runner for vimunit compatibility tests.

This module runs vimunit test files against our vi implementation to validate
compatibility with standard vi/vim behavior.

vimunit test format:
    :start Test description
        Initial|Text
    :type commands
        Expected|Result
    :type more
        Final|Result
    :end

The '|' character represents the cursor position.
"""

from pathlib import Path
from typing import NamedTuple

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.executor import CommandExecutor
from amplifier.vi.modes.state import ModeManager
from amplifier.vi.terminal.renderer import Renderer


class TestCase(NamedTuple):
    """A single vimunit test case."""

    name: str
    steps: list[tuple[str, str]]  # List of (keystrokes, expected_text)


class VimunitParser:
    """Parse vimunit test files."""

    def parse_file(self, filepath: Path) -> list[TestCase]:
        """Parse a vimunit test file.

        Args:
            filepath: Path to the .vimunit file

        Returns:
            List of TestCase objects
        """
        with open(filepath) as f:
            content = f.read()

        tests = []
        current_test = None
        initial_text = []
        current_steps = []
        current_text = []
        current_keys = None
        in_initial_state = False

        for line in content.split("\n"):
            # Skip comments
            if line.startswith("#"):
                continue

            # Start of new test
            if line.startswith(":start "):
                if current_test:
                    # Save previous test
                    if current_text and current_keys is not None:
                        current_steps.append((current_keys, "\n".join(current_text)))
                    tests.append(TestCase(current_test, current_steps))

                current_test = line[7:].strip()
                initial_text = []
                current_steps = []
                current_text = []
                current_keys = None
                in_initial_state = True
                continue

            # End of test
            if line.startswith(":end"):
                if current_test:
                    # Save final step
                    if current_text and current_keys is not None:
                        current_steps.append((current_keys, "\n".join(current_text)))
                    tests.append(TestCase(current_test, current_steps))

                current_test = None
                initial_text = []
                current_steps = []
                current_text = []
                current_keys = None
                in_initial_state = False
                continue

            # Type directive
            if line.startswith(":type "):
                # If we were collecting initial state, save it as step 0
                if in_initial_state and initial_text:
                    current_steps.append(("", "\n".join(initial_text)))
                    initial_text = []
                    in_initial_state = False

                # Save previous step if exists
                if current_text and current_keys is not None:
                    current_steps.append((current_keys, "\n".join(current_text)))
                    current_text = []

                # Parse keystrokes (remove leading tab if present)
                keys = line[6:]
                if keys.startswith("\t"):
                    keys = keys[1:]
                current_keys = keys.strip()
                continue

            # Buffer text line (first non-directive after :start or :type)
            if current_test is not None:
                # Remove leading tab if present
                text_line = line[1:] if line.startswith("\t") else line

                if in_initial_state:
                    initial_text.append(text_line)
                else:
                    current_text.append(text_line)

        return tests

    def parse_keys(self, key_string: str) -> list[str]:
        """Parse vimunit keystroke notation into individual keys.

        Args:
            key_string: String with vimunit notation (e.g., "iHello\\<esc>")

        Returns:
            List of individual keys/commands
        """
        keys = []
        i = 0
        while i < len(key_string):
            # Handle escape sequences
            if key_string[i : i + 2] == "\\<":
                # Find closing >
                end = key_string.find(">", i + 2)
                if end != -1:
                    # Extract special key
                    special = key_string[i + 2 : end].lower()

                    # Map to our key names
                    key_map = {
                        "esc": "ESC",
                        "cr": "ENTER",
                        "^m": "ENTER",
                        "enter": "ENTER",
                        "return": "ENTER",
                        "tab": "TAB",
                        "space": " ",
                        "bs": "BACKSPACE",
                        "backspace": "BACKSPACE",
                        "del": "DELETE",
                        "up": "UP",
                        "down": "DOWN",
                        "left": "LEFT",
                        "right": "RIGHT",
                    }

                    mapped_key = key_map.get(special, special.upper())
                    keys.append(mapped_key)
                    i = end + 1
                    continue

            # Regular character
            keys.append(key_string[i])
            i += 1

        return keys

    def extract_cursor_pos(self, text: str) -> tuple[str, int, int]:
        """Extract cursor position from text with | marker.

        Args:
            text: Text with | representing cursor position

        Returns:
            Tuple of (text_without_marker, row, col)
        """
        lines = text.split("\n")
        for row, line in enumerate(lines):
            col = line.find("|")
            if col != -1:
                # Remove the | marker
                lines[row] = line[:col] + line[col + 1 :]
                return ("\n".join(lines), row, col)

        # No cursor marker found - default to (0, 0)
        return (text, 0, 0)

    def format_with_cursor(self, text: str, row: int, col: int) -> str:
        """Add | cursor marker to text at specified position.

        Args:
            text: Text content
            row: Cursor row (0-indexed)
            col: Cursor column (0-indexed)

        Returns:
            Text with | marker at cursor position
        """
        lines = text.split("\n")
        if 0 <= row < len(lines):
            line = lines[row]
            # Ensure col is within bounds
            col = min(col, len(line))
            lines[row] = line[:col] + "|" + line[col:]

        return "\n".join(lines)


class VimunitRunner:
    """Run vimunit tests against vi implementation."""

    def __init__(self):
        """Initialize the test runner."""
        self.parser = VimunitParser()
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_test_file(self, filepath: Path, verbose: bool = False) -> dict:
        """Run all tests in a vimunit file.

        Args:
            filepath: Path to the .vimunit file
            verbose: Whether to print detailed output

        Returns:
            Dictionary with test results
        """
        tests = self.parser.parse_file(filepath)
        file_passed = 0
        file_failed = 0
        file_errors = []

        for test in tests:
            try:
                passed, error = self.run_test_case(test, verbose)
                if passed:
                    file_passed += 1
                    self.passed += 1
                else:
                    file_failed += 1
                    self.failed += 1
                    error_msg = f"{filepath.name}: {test.name} - {error}"
                    file_errors.append(error_msg)
                    self.errors.append(error_msg)
            except Exception as e:
                file_failed += 1
                self.failed += 1
                error_msg = f"{filepath.name}: {test.name} - Exception: {e}"
                file_errors.append(error_msg)
                self.errors.append(error_msg)

        return {
            "file": filepath.name,
            "passed": file_passed,
            "failed": file_failed,
            "total": file_passed + file_failed,
            "errors": file_errors,
        }

    def run_test_case(self, test: TestCase, verbose: bool = False) -> tuple[bool, str]:
        """Run a single test case.

        Args:
            test: TestCase to run
            verbose: Whether to print detailed output

        Returns:
            Tuple of (passed, error_message)
        """
        if verbose:
            print(f"  Running: {test.name}")

        # Initialize vi components
        buffer = TextBuffer()
        modes = ModeManager()
        renderer = Renderer()
        executor = CommandExecutor(buffer, modes, renderer)

        # First step should be the initial buffer state (empty keys)
        if test.steps and test.steps[0][0] == "":
            first_keys, first_state = test.steps[0]
            initial_text, initial_row, initial_col = self.parser.extract_cursor_pos(first_state)
            buffer._lines = initial_text.split("\n") if initial_text else [""]
            buffer.set_cursor(initial_row, initial_col)
            start_idx = 1
        else:
            start_idx = 0

        # Run remaining steps
        for step_idx in range(start_idx, len(test.steps)):
            keys, expected = test.steps[step_idx]

            # Parse expected state
            expected_text, expected_row, expected_col = self.parser.extract_cursor_pos(expected)

            # Execute keystrokes
            key_list = self.parser.parse_keys(keys)
            for key in key_list:
                # Get current mode
                mode = modes.get_mode()

                # Execute key based on mode
                if mode == "normal":
                    executor.execute_normal_command(key)
                elif mode == "insert":
                    if key == "ESC":
                        modes.to_normal()
                        # Move cursor back one if not at start
                        row, col = buffer.get_cursor()
                        if col > 0:
                            buffer.set_cursor(row, col - 1)
                    else:
                        executor.execute_insert_command(key)
                elif mode == "visual":
                    if key == "ESC":
                        modes.to_normal()
                    else:
                        executor.execute_visual_command(key)

            # Check result
            actual_text = buffer.get_content()
            actual_row, actual_col = buffer.get_cursor()

            # Compare
            if actual_text != expected_text:
                if verbose:
                    print("    FAILED: Text mismatch")
                    print(f"      Expected: {repr(expected_text)}")
                    print(f"      Got:      {repr(actual_text)}")
                return (
                    False,
                    f"Step {step_idx}: Text mismatch. Expected {repr(expected_text)}, got {repr(actual_text)}",
                )

            if actual_row != expected_row or actual_col != expected_col:
                if verbose:
                    print("    FAILED: Cursor mismatch")
                    print(f"      Expected: ({expected_row}, {expected_col})")
                    print(f"      Got:      ({actual_row}, {actual_col})")
                return (
                    False,
                    f"Step {step_idx}: Cursor at ({actual_row}, {actual_col}), expected ({expected_row}, {expected_col})",
                )

        if verbose:
            print("    PASSED")

        return (True, "")

    def run_level(self, vimunit_dir: Path, level: int, verbose: bool = False) -> dict:
        """Run all tests in a specific vimunit level.

        Args:
            vimunit_dir: Path to vimunit directory
            level: Level number (0-6)
            verbose: Whether to print detailed output

        Returns:
            Dictionary with aggregated results
        """
        level_dir = vimunit_dir / f"level{level}"
        if not level_dir.exists():
            return {"level": level, "passed": 0, "failed": 0, "total": 0, "files": []}

        test_files = sorted(level_dir.glob("*.vimunit"))
        file_results = []

        print(f"\nRunning Level {level} tests...")
        for test_file in test_files:
            print(f"  {test_file.name}...")
            result = self.run_test_file(test_file, verbose)
            file_results.append(result)
            print(f"    {result['passed']}/{result['total']} passed")

        total_passed = sum(r["passed"] for r in file_results)
        total_failed = sum(r["failed"] for r in file_results)
        total_tests = sum(r["total"] for r in file_results)

        return {
            "level": level,
            "passed": total_passed,
            "failed": total_failed,
            "total": total_tests,
            "files": file_results,
        }


def main():
    """Run vimunit tests."""
    import sys

    vimunit_dir = Path("/tmp/vimunit")
    if not vimunit_dir.exists():
        print(f"Error: vimunit directory not found at {vimunit_dir}")
        print("Please clone it with: git clone https://github.com/jimrandomh/vimunit.git /tmp/vimunit")
        sys.exit(1)

    runner = VimunitRunner()

    # Run levels 0-3 (implemented levels)
    all_results = []
    for level in range(4):
        result = runner.run_level(vimunit_dir, level, verbose=False)
        all_results.append(result)

    # Print summary
    print("\n" + "=" * 60)
    print("VIMUNIT TEST SUMMARY")
    print("=" * 60)

    for result in all_results:
        level = result["level"]
        passed = result["passed"]
        total = result["total"]
        pct = (passed / total * 100) if total > 0 else 0
        status = "✅" if passed == total else "⚠️"
        print(f"Level {level}: {status} {passed}/{total} passed ({pct:.1f}%)")

    # Overall summary
    total_passed = sum(r["passed"] for r in all_results)
    total_tests = sum(r["total"] for r in all_results)
    overall_pct = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"\nOverall: {total_passed}/{total_tests} passed ({overall_pct:.1f}%)")

    # Print errors if any
    if runner.errors:
        print("\n" + "=" * 60)
        print("FAILURES")
        print("=" * 60)
        for error in runner.errors[:20]:  # Show first 20 errors
            print(f"  {error}")

        if len(runner.errors) > 20:
            print(f"  ... and {len(runner.errors) - 20} more failures")

    sys.exit(0 if total_passed == total_tests else 1)


if __name__ == "__main__":
    main()
