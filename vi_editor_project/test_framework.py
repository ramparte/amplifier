#!/usr/bin/env python3
"""
File-based test framework for vi editor.

This framework reads test cases from file triplets:
- input.txt: Initial buffer content
- actions.txt: Commands to execute
- expected.txt: Expected final buffer content
"""

import difflib
import json
import sys
from pathlib import Path
from typing import Any


class TestResult:
    """Result of a single test execution."""

    def __init__(self, name: str, passed: bool, message: str = "", diff: list[str] | None = None):
        self.name = name
        self.passed = passed
        self.message = message
        self.diff = diff or []

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        output = f"[{status}] {self.name}"
        if self.message:
            output += f"\n  {self.message}"
        if self.diff:
            output += "\n  Diff:\n"
            for line in self.diff:
                output += f"    {line}"
        return output


class ActionParser:
    """Parse action files into executable commands."""

    def __init__(self):
        self.special_keys = {
            "<ESC>": "\x1b",
            "<ENTER>": "\n",
            "<TAB>": "\t",
            "<BACKSPACE>": "\x7f",
            "<DELETE>": "\x7f",
            "<UP>": "\x1b[A",
            "<DOWN>": "\x1b[B",
            "<LEFT>": "\x1b[D",
            "<RIGHT>": "\x1b[C",
            "<CTRL-C>": "\x03",
            "<CTRL-D>": "\x04",
            "<CTRL-R>": "\x12",
            "<CTRL-U>": "\x15",
            "<CTRL-W>": "\x17",
        }

    def parse_line(self, line: str) -> list[str]:
        """
        Parse a single action line into keystrokes.

        Handles:
        - Comments (lines starting with #)
        - Special keys like <ESC>, <ENTER>
        - Literal text
        - Repeat counts like 5j, 3dd
        """
        # Remove comments
        if "#" in line:
            line = line[: line.index("#")]
        line = line.strip()

        if not line:
            return []

        # Handle special keys
        keystrokes = []
        i = 0
        while i < len(line):
            # Check for special key markers
            if line[i] == "<":
                end = line.find(">", i)
                if end != -1:
                    special = line[i : end + 1].upper()
                    if special in self.special_keys:
                        keystrokes.append(self.special_keys[special])
                        i = end + 1
                        continue

            # Regular character
            keystrokes.append(line[i])
            i += 1

        return keystrokes

    def parse_file(self, filepath: Path) -> list[str]:
        """Parse an actions file into a list of keystrokes."""
        if not filepath.exists():
            return []

        keystrokes = []
        with open(filepath, encoding="utf-8") as f:
            for line in f:
                keystrokes.extend(self.parse_line(line))

        return keystrokes


class FileBasedTest:
    """A single file-based test case."""

    def __init__(self, test_dir: Path):
        self.test_dir = test_dir
        self.name = test_dir.name
        self.input_file = test_dir / "input.txt"
        self.actions_file = test_dir / "actions.txt"
        self.expected_file = test_dir / "expected.txt"
        self.metadata_file = test_dir / "metadata.json"
        self.parser = ActionParser()

    def load_metadata(self) -> dict[str, Any]:
        """Load test metadata if available."""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        return {}

    def load_input(self) -> list[str]:
        """Load initial buffer content."""
        if not self.input_file.exists():
            return []

        with open(self.input_file, encoding="utf-8") as f:
            # Preserve line endings but split into list
            return f.read().splitlines()

    def load_expected(self) -> list[str]:
        """Load expected output."""
        if not self.expected_file.exists():
            return []

        with open(self.expected_file, encoding="utf-8") as f:
            return f.read().splitlines()

    def load_actions(self) -> list[str]:
        """Load and parse actions."""
        return self.parser.parse_file(self.actions_file)

    def compare_output(self, actual: list[str], expected: list[str]) -> tuple[bool, list[str]]:
        """
        Compare actual output with expected.

        Returns (passed, diff_lines).
        """
        if actual == expected:
            return True, []

        # Generate unified diff
        diff = list(difflib.unified_diff(expected, actual, fromfile="expected.txt", tofile="actual.txt", lineterm=""))

        return False, diff

    def run(self, editor_factory) -> TestResult:
        """
        Run the test case.

        Args:
            editor_factory: Callable that returns an editor instance

        Returns:
            TestResult with pass/fail status and any diff
        """
        try:
            # Load test data
            input_lines = self.load_input()
            actions = self.load_actions()
            expected = self.load_expected()
            metadata = self.load_metadata()

            # Create editor instance with input
            editor = editor_factory(input_lines)

            # Execute actions
            for keystroke in actions:
                editor.process_key(keystroke)

            # Get output
            actual = editor.get_buffer_content()

            # Compare
            passed, diff = self.compare_output(actual, expected)

            if passed:
                return TestResult(self.name, True)
            return TestResult(self.name, False, "Output mismatch", diff)

        except Exception as e:
            return TestResult(self.name, False, f"Test execution failed: {str(e)}")


class TestRunner:
    """Run multiple file-based tests."""

    def __init__(self, test_root: Path):
        self.test_root = test_root

    def discover_tests(self, pattern: str = "*") -> list[Path]:
        """Discover test directories matching pattern."""
        tests = []

        # Find all directories containing actions.txt
        for test_dir in self.test_root.glob(f"**/{pattern}"):
            if test_dir.is_dir() and (test_dir / "actions.txt").exists():
                tests.append(test_dir)

        return sorted(tests)

    def run_tests(self, editor_factory, pattern: str = "*", verbose: bool = True) -> tuple[int, int]:
        """
        Run all discovered tests.

        Args:
            editor_factory: Callable that returns editor instance
            pattern: Glob pattern for test discovery
            verbose: Print detailed output

        Returns:
            (passed_count, failed_count)
        """
        test_dirs = self.discover_tests(pattern)

        if not test_dirs:
            print(f"No tests found in {self.test_root}")
            return 0, 0

        passed = 0
        failed = 0
        failed_tests = []

        print(f"Running {len(test_dirs)} tests...")
        print("-" * 60)

        for test_dir in test_dirs:
            test = FileBasedTest(test_dir)
            result = test.run(editor_factory)

            if result.passed:
                passed += 1
                if verbose:
                    print(f"✓ {result.name}")
            else:
                failed += 1
                failed_tests.append(result)
                if verbose:
                    print(f"✗ {result.name}")
                    if result.message:
                        print(f"  {result.message}")

        print("-" * 60)
        print(f"Results: {passed} passed, {failed} failed")

        # Show detailed failure info
        if failed_tests and verbose:
            print("\nFailed Tests:")
            print("=" * 60)
            for result in failed_tests:
                print(result)
                print()

        return passed, failed


class TestGenerator:
    """Generate test case templates."""

    @staticmethod
    def create_test(test_dir: Path, description: str = ""):
        """Create a new test case template."""
        test_dir.mkdir(parents=True, exist_ok=True)

        # Create empty input file
        (test_dir / "input.txt").write_text("")

        # Create actions template
        actions_template = f"""# Test: {test_dir.name}
# {description}
#
# Available special keys:
#   <ESC> <ENTER> <TAB> <BACKSPACE> <DELETE>
#   <UP> <DOWN> <LEFT> <RIGHT>
#   <CTRL-C> <CTRL-D> <CTRL-R> <CTRL-U> <CTRL-W>
#
# Example actions:
# i                    # Enter insert mode
# Hello World          # Type text
# <ESC>                # Return to command mode
# :wq<ENTER>           # Save and quit

"""
        (test_dir / "actions.txt").write_text(actions_template)

        # Create empty expected file
        (test_dir / "expected.txt").write_text("")

        # Create metadata
        metadata = {"name": test_dir.name, "description": description, "created": str(Path.cwd())}
        (test_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))

        print(f"Created test template in {test_dir}")


def main():
    """CLI for test framework."""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_framework.py run <test_root> [pattern]")
        print("  python test_framework.py create <test_dir> [description]")
        print("  python test_framework.py validate <test_dir>")
        sys.exit(1)

    command = sys.argv[1]

    if command == "create":
        if len(sys.argv) < 3:
            print("Usage: python test_framework.py create <test_dir> [description]")
            sys.exit(1)

        test_dir = Path(sys.argv[2])
        description = sys.argv[3] if len(sys.argv) > 3 else ""
        TestGenerator.create_test(test_dir, description)

    elif command == "validate":
        if len(sys.argv) < 3:
            print("Usage: python test_framework.py validate <test_dir>")
            sys.exit(1)

        test_dir = Path(sys.argv[2])
        test = FileBasedTest(test_dir)

        # Check required files
        missing = []
        if not test.input_file.exists():
            missing.append("input.txt")
        if not test.actions_file.exists():
            missing.append("actions.txt")
        if not test.expected_file.exists():
            missing.append("expected.txt")

        if missing:
            print(f"Missing files in {test_dir}: {', '.join(missing)}")
            sys.exit(1)
        else:
            print(f"Test {test_dir.name} is valid")

    elif command == "run":
        print("Test runner requires editor implementation")
        print("Use this in your test suite:")
        print()
        print("from test_framework import TestRunner")
        print("runner = TestRunner(Path('tests'))")
        print("passed, failed = runner.run_tests(create_editor)")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
