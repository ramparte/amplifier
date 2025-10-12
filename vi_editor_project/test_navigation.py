#!/usr/bin/env python3
"""
Test runner for navigation commands.

This script tests the navigation implementation against all the test cases.
"""

import sys
from pathlib import Path

from buffer import Buffer
from command_mode import CommandMode
from test_framework import FileBasedTest


def create_navigation_executor(buffer: Buffer, cmd_mode: CommandMode):
    """Create an executor function for navigation tests."""

    def executor(test_buffer: Buffer, actions: list[str]) -> str:
        """Execute navigation actions on the buffer."""
        # Use the provided buffer and command mode
        for action in actions:
            if action.startswith("set_cursor:"):
                # Parse set_cursor command
                coords = action.replace("set_cursor:", "").split(",")
                row, col = int(coords[0]), int(coords[1])
                buffer.move_cursor(row, col)
            else:
                # Process as navigation command
                cmd_mode.process_command(action)

        # Return buffer state
        return "\n".join(buffer.get_lines())

    return executor


def run_navigation_tests():
    """Run all navigation tests and report results."""
    test_dir = Path("/workspaces/amplifier/vi_editor_project/tests/navigation")

    if not test_dir.exists():
        print(f"Error: Test directory {test_dir} does not exist")
        return False

    print(f"Running navigation tests from {test_dir}")
    print("=" * 60)

    # Count passed and failed tests
    passed = 0
    failed = 0
    failed_tests = []

    # Run each test directory
    for test_path in sorted(test_dir.iterdir()):
        if not test_path.is_dir():
            continue

        try:
            # Create test case
            test = FileBasedTest(test_path)

            # Load test data
            input_lines = test.load_input()
            actions = test.load_actions()
            expected_lines = test.load_expected()

            # Create fresh buffer and command mode for each test
            buffer = Buffer(input_lines.copy() if input_lines else [""])
            cmd_mode = CommandMode(buffer)

            # Execute all actions
            for action in actions:
                if action.startswith("set_cursor:"):
                    # Parse set_cursor command
                    coords = action.replace("set_cursor:", "").split(",")
                    row, col = int(coords[0]), int(coords[1])
                    buffer.move_cursor(row, col)
                else:
                    # Process as navigation command
                    cmd_mode.process_command(action)

            # Get actual output
            actual_output = buffer.get_content()
            expected_output = expected_lines

            # Compare outputs
            if actual_output == expected_output:
                print(f"✓ {test_path.name}")
                passed += 1
            else:
                print(f"✗ {test_path.name}")
                print(f"  Expected: {expected_output}")
                print(f"  Got:      {actual_output}")
                failed += 1
                failed_tests.append(test_path.name)

        except Exception as e:
            print(f"✗ {test_path.name}: {e}")
            failed += 1
            failed_tests.append(test_path.name)

    # Print summary
    print("=" * 60)
    print(f"Navigation Test Results: {passed} passed, {failed} failed")
    total = passed + failed
    if total > 0:
        print(f"Success rate: {passed}/{total} ({passed * 100 // total}%)")
    else:
        print("No tests were run")

    if failed_tests:
        print("\nFailed tests:")
        for test_name in failed_tests:
            print(f"  - {test_name}")

    return failed == 0


if __name__ == "__main__":
    success = run_navigation_tests()
    sys.exit(0 if success else 1)
