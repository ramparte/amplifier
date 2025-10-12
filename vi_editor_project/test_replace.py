#!/usr/bin/env python3
"""
Test suite for vi editor replace operations.

Tests the following replace commands:
- r: Replace single character under cursor
- R: Enter replace mode (overwrite characters)
- s: Substitute character (delete and enter insert mode)
- S: Substitute line (delete entire line and enter insert mode)
- c: Change command with motions (cw, cb, c$, etc.)
- C: Change to end of line
- ~: Toggle case of character
"""

import sys
from pathlib import Path

from buffer import Buffer
from command_mode import CommandMode
from test_framework import FileBasedTest


def create_replace_test_cases():
    """Create test cases for replace operations."""
    test_base = Path("/workspaces/amplifier/vi_editor_project/tests/replace")
    test_base.mkdir(parents=True, exist_ok=True)

    # Test case 1: r - replace single character
    test_dir = test_base / "replace_single_char_r"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Hello World")
    (test_dir / "actions.txt").write_text("# Replace H with J\nset_cursor:0,0\nrJ")
    (test_dir / "expected.txt").write_text("Jello World")

    # Test case 2: r with different positions
    test_dir = test_base / "replace_char_middle"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text("# Replace u with a\nset_cursor:0,6\nra")
    (test_dir / "expected.txt").write_text("The qaick brown fox")

    # Test case 3: R - replace mode
    test_dir = test_base / "replace_mode_R"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Replace this text")
    (test_dir / "actions.txt").write_text("# Enter replace mode and overwrite\nset_cursor:0,0\nROverwrite<ESC>")
    (test_dir / "expected.txt").write_text("Overwritehis text")

    # Test case 4: R - replace mode with longer text
    test_dir = test_base / "replace_mode_extend"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Short")
    (test_dir / "actions.txt").write_text("# Replace with longer text\nset_cursor:0,0\nRMuch longer text<ESC>")
    (test_dir / "expected.txt").write_text("Much longer text")

    # Test case 5: s - substitute character
    test_dir = test_base / "substitute_char_s"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Hello World")
    (test_dir / "actions.txt").write_text("# Substitute H with Hi\nset_cursor:0,0\nsiH<ESC>")
    (test_dir / "expected.txt").write_text("iHello World")

    # Test case 6: s with count (3s)
    test_dir = test_base / "substitute_count_3s"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("ABCDEFG")
    (test_dir / "actions.txt").write_text("# Substitute 3 characters\nset_cursor:0,1\n3sXYZ<ESC>")
    (test_dir / "expected.txt").write_text("AXYZE EFG")

    # Test case 7: S - substitute entire line
    test_dir = test_base / "substitute_line_S"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nReplace this line\nLine 3")
    (test_dir / "actions.txt").write_text("# Substitute entire line\nset_cursor:1,0\nSNew content<ESC>")
    (test_dir / "expected.txt").write_text("Line 1\nNew content\nLine 3")

    # Test case 8: cw - change word
    test_dir = test_base / "change_word_cw"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text("# Change 'quick' to 'slow'\nset_cursor:0,4\ncwslow<ESC>")
    (test_dir / "expected.txt").write_text("The slow brown fox")

    # Test case 9: cb - change word backward
    test_dir = test_base / "change_word_back_cb"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("The quick brown fox")
    (test_dir / "actions.txt").write_text("# Change backward from 'k' in quick\nset_cursor:0,8\ncbslow<ESC>")
    (test_dir / "expected.txt").write_text("The slowk brown fox")

    # Test case 10: c$ - change to end of line
    test_dir = test_base / "change_to_eol"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Keep this replace rest")
    (test_dir / "actions.txt").write_text("# Change to end of line\nset_cursor:0,10\nc$and new text<ESC>")
    (test_dir / "expected.txt").write_text("Keep this and new text")

    # Test case 11: c0 - change to beginning of line
    test_dir = test_base / "change_to_bol"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Replace this keep rest")
    (test_dir / "actions.txt").write_text("# Change to beginning of line\nset_cursor:0,13\nc0New start <ESC>")
    (test_dir / "expected.txt").write_text("New start keep rest")

    # Test case 12: C - change to end of line (shorthand)
    test_dir = test_base / "change_C_shorthand"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Keep this delete rest")
    (test_dir / "actions.txt").write_text("# Change to end using C\nset_cursor:0,10\nCand add new<ESC>")
    (test_dir / "expected.txt").write_text("Keep this and add new")

    # Test case 13: cc - change entire line
    test_dir = test_base / "change_line_cc"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\nReplace this\nLine 3")
    (test_dir / "actions.txt").write_text("# Change entire line\nset_cursor:1,5\nccCompletely new<ESC>")
    (test_dir / "expected.txt").write_text("Line 1\nCompletely new\nLine 3")

    # Test case 14: ~ - toggle case
    test_dir = test_base / "toggle_case_tilde"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("HeLLo WoRLd")
    (test_dir / "actions.txt").write_text("# Toggle case of first 5 characters\nset_cursor:0,0\n~~~~~")
    (test_dir / "expected.txt").write_text("hEllO WoRLd")

    # Test case 15: Replace at end of line
    test_dir = test_base / "replace_at_eol"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line1\nLine2")
    (test_dir / "actions.txt").write_text("# Replace last character\nset_cursor:0,4\nrX")
    (test_dir / "expected.txt").write_text("LineX\nLine2")

    # Test case 16: Replace on empty line
    test_dir = test_base / "replace_empty_line"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Line 1\n\nLine 3")
    (test_dir / "actions.txt").write_text("# Try replace on empty line\nset_cursor:1,0\nrX")
    (test_dir / "expected.txt").write_text("Line 1\nX\nLine 3")

    # Test case 17: Replace mode crossing lines
    test_dir = test_base / "replace_mode_multiline"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("First line\nSecond line")
    (test_dir / "actions.txt").write_text("# Replace across line boundary\nset_cursor:0,6\nRnew text goes here<ESC>")
    (test_dir / "expected.txt").write_text("First new text goes here")

    # Test case 18: Multiple replacements with r
    test_dir = test_base / "multiple_r_replacements"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("aaaaa")
    (test_dir / "actions.txt").write_text(
        "# Replace chars at different positions\nset_cursor:0,0\nrb\nset_cursor:0,2\nrc\nset_cursor:0,4\nrd"
    )
    (test_dir / "expected.txt").write_text("babcd")

    # Test case 19: Change with count (2cw)
    test_dir = test_base / "change_count_2cw"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("one two three four")
    (test_dir / "actions.txt").write_text("# Change two words\nset_cursor:0,4\n2cwnumbers<ESC>")
    (test_dir / "expected.txt").write_text("one numbers four")

    # Test case 20: Substitute at last position
    test_dir = test_base / "substitute_last_char"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Test")
    (test_dir / "actions.txt").write_text("# Substitute last character\nset_cursor:0,3\nsted<ESC>")
    (test_dir / "expected.txt").write_text("Tesed")

    print(f"Created {len(list(test_base.iterdir()))} replace operation test cases in {test_base}")


def run_replace_tests():
    """Run all replace operation tests."""
    test_dir = Path("/workspaces/amplifier/vi_editor_project/tests/replace")

    if not test_dir.exists():
        print("Creating test cases...")
        create_replace_test_cases()

    print(f"Running replace operation tests from {test_dir}")
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

            # Track if we're in insert/replace mode
            in_special_mode = False

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
                        # Process the command string
                        i = 0
                        while i < len(line):
                            # Check for special sequences
                            if line[i : i + 5] == "<ESC>":
                                # Exit insert/replace mode
                                if hasattr(cmd_mode, "exit_insert_mode"):
                                    cmd_mode.exit_insert_mode()
                                elif hasattr(cmd_mode, "exit_replace_mode"):
                                    cmd_mode.exit_replace_mode()
                                in_special_mode = False
                                i += 5
                                continue

                            # Process regular character
                            char = line[i]

                            if in_special_mode:
                                # In insert or replace mode, add text directly
                                if hasattr(cmd_mode, "insert_text"):
                                    cmd_mode.insert_text(char)
                                elif hasattr(cmd_mode, "replace_text"):
                                    cmd_mode.replace_text(char)
                            else:
                                # Process as command
                                _ = cmd_mode.process_command(char)
                                # Check if we entered a special mode
                                if char in "iIaAsScCrR" or (hasattr(cmd_mode, "mode") and cmd_mode.mode != "command"):
                                    in_special_mode = True

                            i += 1

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
    print(f"Replace Operation Test Results: {passed} passed, {failed} failed")
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
    create_replace_test_cases()

    # Then run the tests
    success = run_replace_tests()
    sys.exit(0 if success else 1)
