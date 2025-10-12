#!/usr/bin/env python3
"""
Test suite for vi editor yank (copy) and paste operations.

Tests the following yank/paste commands:
- yy: Yank current line
- yw: Yank word forward
- yb: Yank word backward
- y$: Yank to end of line
- y0: Yank to beginning of line
- p: Paste after cursor
- P: Paste before cursor
- dd + p: Delete line and paste (cut/paste)
"""

import sys
from pathlib import Path

from buffer import Buffer
from command_mode import CommandMode
from test_framework import FileBasedTest


def create_yank_paste_test_cases():
    """Create test cases for yank and paste operations."""
    test_base = Path("/workspaces/amplifier/vi_editor_project/tests/yank_paste")
    test_base.mkdir(parents=True, exist_ok=True)

    # Test case 1: yy + p - yank line and paste after
    test_dir = test_base / "yank_line_paste_after"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nLine 2\nLine 3")
    (test_dir / "actions.txt").write_text("# Yank line 2 and paste after line 3\nset_cursor:1,0\nyy\nset_cursor:2,0\np")
    (test_dir / "expected.txt").write_text("Line 1\nLine 2\nLine 3\nLine 2")

    # Test case 2: yy + P - yank line and paste before
    test_dir = test_base / "yank_line_paste_before"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nLine 2\nLine 3")
    (test_dir / "actions.txt").write_text(
        "# Yank line 1 and paste before line 3\nset_cursor:0,0\nyy\nset_cursor:2,0\nP"
    )
    (test_dir / "expected.txt").write_text("Line 1\nLine 2\nLine 1\nLine 3")

    # Test case 3: yw + p - yank word and paste
    test_dir = test_base / "yank_word_paste"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text(
        "# Yank 'quick' and paste after 'fox'\nset_cursor:0,4\nyw\nset_cursor:0,18\np"
    )
    (test_dir / "expected.txt").write_text("The quick brown foxquick ")

    # Test case 4: yb + p - yank word backward and paste
    test_dir = test_base / "yank_word_back_paste"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text("# Yank 'quick' backward and paste\nset_cursor:0,9\nyb\nset_cursor:0,18\np")
    (test_dir / "expected.txt").write_text("The quick brown foxquick")

    # Test case 5: y$ + p - yank to end of line and paste
    test_dir = test_base / "yank_to_eol_paste"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Copy this part onwards")
    (test_dir / "actions.txt").write_text("# Yank from 'part' to end and paste\nset_cursor:0,10\ny$\nset_cursor:0,0\np")
    (test_dir / "expected.txt").write_text("Cpart onwardsopy this part onwards")

    # Test case 6: y0 + p - yank to beginning of line and paste
    test_dir = test_base / "yank_to_bol_paste"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Copy up to here")
    (test_dir / "actions.txt").write_text("# Yank from beginning to 'here'\nset_cursor:0,11\ny0\nset_cursor:0,14\np")
    (test_dir / "expected.txt").write_text("Copy up to hereCopy up to ")

    # Test case 7: dd + p - delete line and paste (cut/paste)
    test_dir = test_base / "delete_line_paste"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nLine 2\nLine 3\nLine 4")
    (test_dir / "actions.txt").write_text(
        "# Delete line 2 and paste after line 3\nset_cursor:1,0\ndd\nset_cursor:1,0\np"
    )
    (test_dir / "expected.txt").write_text("Line 1\nLine 3\nLine 2\nLine 4")

    # Test case 8: Multiple yanks (last yank wins)
    test_dir = test_base / "multiple_yanks"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("First Second Third")
    (test_dir / "actions.txt").write_text(
        "# Yank First, then Second, paste Second\nset_cursor:0,0\nyw\nset_cursor:0,6\nyw\nset_cursor:0,17\np"
    )
    (test_dir / "expected.txt").write_text("First Second ThirdSecond ")

    # Test case 9: Yank empty line
    test_dir = test_base / "yank_empty_line"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\n\nLine 3")
    (test_dir / "actions.txt").write_text("# Yank empty line and paste\nset_cursor:1,0\nyy\nset_cursor:2,0\np")
    (test_dir / "expected.txt").write_text("Line 1\n\nLine 3\n")

    # Test case 10: Paste with count (3p)
    test_dir = test_base / "paste_with_count"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("A B C")
    (test_dir / "actions.txt").write_text("# Yank A and paste 3 times\nset_cursor:0,0\nyw\nset_cursor:0,4\n3p")
    (test_dir / "expected.txt").write_text("A B CA A A ")

    # Test case 11: Yank and paste at beginning of buffer
    test_dir = test_base / "yank_paste_beginning"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("First line\nSecond line")
    (test_dir / "actions.txt").write_text(
        "# Yank second line and paste at beginning\nset_cursor:1,0\nyy\nset_cursor:0,0\nP"
    )
    (test_dir / "expected.txt").write_text("Second line\nFirst line\nSecond line")

    # Test case 12: Yank and paste at end of buffer
    test_dir = test_base / "yank_paste_end"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("First line\nSecond line")
    (test_dir / "actions.txt").write_text("# Yank first line and paste at end\nset_cursor:0,0\nyy\nset_cursor:1,10\np")
    (test_dir / "expected.txt").write_text("First line\nSecond line\nFirst line")

    # Test case 13: dw + p - delete word and paste
    test_dir = test_base / "delete_word_paste"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Move this word here")
    (test_dir / "actions.txt").write_text(
        "# Delete 'this' and paste after 'here'\nset_cursor:0,5\ndw\nset_cursor:0,13\np"
    )
    (test_dir / "expected.txt").write_text("Move word herethis ")

    # Test case 14: Y (capital) - yank line (synonym for yy)
    test_dir = test_base / "yank_line_capital_Y"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nLine 2")
    (test_dir / "actions.txt").write_text("# Yank with Y and paste\nset_cursor:0,0\nY\nset_cursor:1,0\np")
    (test_dir / "expected.txt").write_text("Line 1\nLine 2\nLine 1")

    # Test case 15: Paste into empty buffer
    test_dir = test_base / "paste_empty_buffer"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Text to copy\n")
    (test_dir / "actions.txt").write_text("# Yank line, delete all, paste\nset_cursor:0,0\nyy\ndd\ndd\np")
    (test_dir / "expected.txt").write_text("Text to copy")

    print(f"Created {len(list(test_base.iterdir()))} yank/paste test cases in {test_base}")


def run_yank_paste_tests():
    """Run all yank and paste operation tests."""
    test_dir = Path("/workspaces/amplifier/vi_editor_project/tests/yank_paste")

    if not test_dir.exists():
        print("Creating test cases...")
        create_yank_paste_test_cases()

    print(f"Running yank/paste operation tests from {test_dir}")
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
    print(f"Yank/Paste Test Results: {passed} passed, {failed} failed")
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
    create_yank_paste_test_cases()

    # Then run the tests
    success = run_yank_paste_tests()
    sys.exit(0 if success else 1)
