#!/usr/bin/env python3
"""
Test suite for vi editor delete operations.

Tests the following delete commands:
- x: Delete character under cursor
- X: Delete character before cursor
- dd: Delete current line
- dw: Delete word forward
- db: Delete word backward
- d$: Delete to end of line
- d0: Delete to beginning of line
- D: Delete to end of line (shorthand)
- dj: Delete current and next line
- dk: Delete current and previous line
"""

import sys
from pathlib import Path

from buffer import Buffer
from command_mode import CommandMode
from test_framework import FileBasedTest


def create_delete_test_cases():
    """Create test cases for delete operations."""
    test_base = Path("/workspaces/amplifier/vi_editor_project/tests/delete")
    test_base.mkdir(parents=True, exist_ok=True)

    # Test case 1: x - delete character under cursor
    test_dir = test_base / "delete_char_x"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Hello World")
    (test_dir / "actions.txt").write_text("# Delete character under cursor\nset_cursor:0,0\nx")
    (test_dir / "expected.txt").write_text("ello World")

    # Test case 2: X - delete character before cursor
    test_dir = test_base / "delete_char_before_X"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Hello World")
    (test_dir / "actions.txt").write_text("# Delete character before cursor\nset_cursor:0,5\nX")
    (test_dir / "expected.txt").write_text("Hell World")

    # Test case 3: dd - delete entire line
    test_dir = test_base / "delete_line_dd"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nLine 2\nLine 3")
    (test_dir / "actions.txt").write_text("# Delete entire line\nset_cursor:1,0\ndd")
    (test_dir / "expected.txt").write_text("Line 1\nLine 3")

    # Test case 4: dw - delete word forward
    test_dir = test_base / "delete_word_dw"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text("# Delete word forward\nset_cursor:0,4\ndw")
    (test_dir / "expected.txt").write_text("The brown fox")

    # Test case 5: db - delete word backward
    test_dir = test_base / "delete_word_back_db"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text("# Delete word backward\nset_cursor:0,9\ndb")
    (test_dir / "expected.txt").write_text("The  brown fox")

    # Test case 6: d$ - delete to end of line
    test_dir = test_base / "delete_to_eol"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Delete from here onwards")
    (test_dir / "actions.txt").write_text("# Delete to end of line\nset_cursor:0,7\nd$")
    (test_dir / "expected.txt").write_text("Delete ")

    # Test case 7: d0 - delete to beginning of line
    test_dir = test_base / "delete_to_bol"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Delete up to here")
    (test_dir / "actions.txt").write_text("# Delete to beginning of line\nset_cursor:0,13\nd0")
    (test_dir / "expected.txt").write_text("here")

    # Test case 8: D - delete to end of line (shorthand)
    test_dir = test_base / "delete_D_shorthand"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Keep this delete rest")
    (test_dir / "actions.txt").write_text("# Delete to end using D\nset_cursor:0,10\nD")
    (test_dir / "expected.txt").write_text("Keep this ")

    # Test case 9: Multiple x deletions
    test_dir = test_base / "delete_multiple_x"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("ABCDEFG")
    (test_dir / "actions.txt").write_text("# Delete multiple chars with x\nset_cursor:0,2\nxxx")
    (test_dir / "expected.txt").write_text("ABFG")

    # Test case 10: Delete at line boundaries
    test_dir = test_base / "delete_line_boundary"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("First\nSecond\nThird")
    (test_dir / "actions.txt").write_text("# Delete at line end\nset_cursor:0,4\nx")
    (test_dir / "expected.txt").write_text("Firs\nSecond\nThird")

    # Test case 11: Delete empty line
    test_dir = test_base / "delete_empty_line"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\n\nLine 3")
    (test_dir / "actions.txt").write_text("# Delete empty line\nset_cursor:1,0\ndd")
    (test_dir / "expected.txt").write_text("Line 1\nLine 3")

    # Test case 12: Delete last line
    test_dir = test_base / "delete_last_line"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nLine 2\nLine 3")
    (test_dir / "actions.txt").write_text("# Delete last line\nset_cursor:2,0\ndd")
    (test_dir / "expected.txt").write_text("Line 1\nLine 2")

    # Test case 13: Delete with count (3x)
    test_dir = test_base / "delete_with_count"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("123456789")
    (test_dir / "actions.txt").write_text("# Delete 3 characters\nset_cursor:0,2\n3x")
    (test_dir / "expected.txt").write_text("126789")

    # Test case 14: Delete word at end of line
    test_dir = test_base / "delete_word_eol"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Delete last word")
    (test_dir / "actions.txt").write_text("# Delete word at line end\nset_cursor:0,12\ndw")
    (test_dir / "expected.txt").write_text("Delete last ")

    # Test case 15: Delete from empty buffer
    test_dir = test_base / "delete_empty_buffer"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("")
    (test_dir / "actions.txt").write_text("# Try to delete from empty buffer\nx")
    # Buffer always maintains at least one line, even if empty
    (test_dir / "expected.txt").write_text("")

    print(f"Created {len(list(test_base.iterdir()))} delete operation test cases in {test_base}")


def run_delete_tests():
    """Run all delete operation tests."""
    test_dir = Path("/workspaces/amplifier/vi_editor_project/tests/delete")

    if not test_dir.exists():
        print("Creating test cases...")
        create_delete_test_cases()

    print(f"Running delete operation tests from {test_dir}")
    print("=" * 60)

    passed = 0
    failed = 0
    failed_tests = []

    # Run each test
    for test_path in sorted(test_dir.iterdir()):
        if not test_path.is_dir():
            continue

        try:
            # Create test case
            test = FileBasedTest(test_path)

            # Load test data
            input_lines = test.load_input()
            expected_lines = test.load_expected()

            # Create fresh buffer and command mode
            buffer = Buffer(input_lines.copy() if input_lines else [""])
            cmd_mode = CommandMode(buffer)

            # Read and process actions line by line
            with open(test.actions_file) as f:
                for line in f:
                    # Remove comments and whitespace
                    if "#" in line:
                        line = line[: line.index("#")]
                    line = line.strip()

                    if not line:
                        continue

                    if line.startswith("set_cursor:"):
                        # Parse set_cursor command
                        coords = line.replace("set_cursor:", "").split(",")
                        row, col = int(coords[0]), int(coords[1])
                        buffer.move_cursor(row, col)
                    else:
                        # Process each character in the command
                        for char in line:
                            cmd_mode.process_command(char)

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
    print(f"Delete Operation Test Results: {passed} passed, {failed} failed")
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
    # First create the test cases
    create_delete_test_cases()

    # Then run the tests
    success = run_delete_tests()
    sys.exit(0 if success else 1)
