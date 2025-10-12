#!/usr/bin/env python3
"""Create comprehensive file-based tests for insert mode functionality.

This script generates test cases for all insert mode operations including:
- i,I insert at cursor/line start
- a,A append after cursor/line end
- o,O open line below/above
- Text insertion and escape
- Special key handling (backspace, enter)
"""

from pathlib import Path


def create_test_case(test_dir: Path, name: str, description: str, input_text: str, actions: list[str], expected: str):
    """Create a single test case with input, actions, and expected files."""
    test_path = test_dir / name
    test_path.mkdir(parents=True, exist_ok=True)

    # Write description
    (test_path / "description.txt").write_text(description)

    # Write input file
    (test_path / "input.txt").write_text(input_text)

    # Write actions file
    (test_path / "actions.txt").write_text("\n".join(actions))

    # Write expected output
    (test_path / "expected.txt").write_text(expected)

    print(f"Created test case: {name}")


def create_insert_mode_tests():
    """Create all insert mode test cases."""
    test_dir = Path("/workspaces/amplifier/vi_editor_project/tests/insert")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Test 1: 'i' - insert at cursor position
    create_test_case(
        test_dir,
        "test_i_insert",
        "Test 'i' command - insert at cursor position",
        "Hello world\nThis is line two\nLine three",
        ["j", "5l", "i", "INSERTED", "<ESC>"],
        "Hello world\nThis INSERTEDis line two\nLine three",
    )

    # Test 2: 'I' - insert at beginning of line
    create_test_case(
        test_dir,
        "test_I_insert_line_start",
        "Test 'I' command - insert at beginning of line",
        "    Indented line\nNormal line\n    Another indented",
        ["j", "I", "START", "<ESC>"],
        "    Indented line\nSTARTNormal line\n    Another indented",
    )

    # Test 3: 'a' - append after cursor
    create_test_case(
        test_dir,
        "test_a_append",
        "Test 'a' command - append after cursor",
        "Hello world\nTest line\nEnd",
        ["5l", "a", " beautiful", "<ESC>"],
        "Hello beautiful world\nTest line\nEnd",
    )

    # Test 4: 'A' - append at end of line
    create_test_case(
        test_dir,
        "test_A_append_line_end",
        "Test 'A' command - append at end of line",
        "First line\nSecond line\nThird line",
        ["j", "A", " - appended", "<ESC>"],
        "First line\nSecond line - appended\nThird line",
    )

    # Test 5: 'o' - open line below
    create_test_case(
        test_dir,
        "test_o_open_below",
        "Test 'o' command - open new line below",
        "Line one\nLine two\nLine three",
        ["j", "o", "New line inserted", "<ESC>"],
        "Line one\nLine two\nNew line inserted\nLine three",
    )

    # Test 6: 'O' - open line above
    create_test_case(
        test_dir,
        "test_O_open_above",
        "Test 'O' command - open new line above",
        "First\nSecond\nThird",
        ["j", "O", "Inserted above", "<ESC>"],
        "First\nInserted above\nSecond\nThird",
    )

    # Test 7: Text insertion with multiple characters
    create_test_case(
        test_dir,
        "test_text_insertion",
        "Test inserting multiple characters and escape",
        "Original text",
        ["$", "i", " with more text added", "<ESC>"],
        "Original text with more text added",
    )

    # Test 8: Backspace handling in insert mode
    create_test_case(
        test_dir,
        "test_backspace",
        "Test backspace key in insert mode",
        "Test line",
        ["$", "a", " extra", "<BS>", "<BS>", "<BS>", "<BS>", "<BS>", "<BS>", "new", "<ESC>"],
        "Test linenew",
    )

    # Test 9: Enter/newline in insert mode
    create_test_case(
        test_dir,
        "test_enter_newline",
        "Test enter key creating new lines in insert mode",
        "Single line",
        ["$", "a", "<CR>", "Second line", "<CR>", "Third line", "<ESC>"],
        "Single line\nSecond line\nThird line",
    )

    # Test 10: Insert mode on empty file
    create_test_case(
        test_dir,
        "test_empty_file_insert",
        "Test insert mode operations on empty file",
        "",
        ["i", "First line of text", "<ESC>"],
        "First line of text",
    )

    # Test 11: Insert at file boundaries
    create_test_case(
        test_dir,
        "test_boundary_insert",
        "Test insert mode at file start and end boundaries",
        "Middle content",
        ["gg", "I", "Start: ", "<ESC>", "G", "A", " :End", "<ESC>"],
        "Start: Middle content :End",
    )

    # Test 12: Multiple mode transitions
    create_test_case(
        test_dir,
        "test_mode_transitions",
        "Test multiple transitions between command and insert modes",
        "Initial text",
        ["i", "1-", "<ESC>", "l", "l", "a", "2-", "<ESC>", "$", "a", "-3", "<ESC>"],
        "1-I2-nitial text-3",
    )

    # Test 13: 'i' on empty line
    create_test_case(
        test_dir,
        "test_i_empty_line",
        "Test 'i' command on empty line",
        "Line one\n\nLine three",
        ["j", "i", "Inserted on empty", "<ESC>"],
        "Line one\nInserted on empty\nLine three",
    )

    # Test 14: 'o' at end of file
    create_test_case(
        test_dir,
        "test_o_end_of_file",
        "Test 'o' command at end of file",
        "Last line",
        ["o", "New last line", "<ESC>"],
        "Last line\nNew last line",
    )

    # Test 15: Complex insertion with special characters
    create_test_case(
        test_dir,
        "test_special_chars",
        "Test inserting special characters",
        "Normal text",
        ["$", "a", " !@#$%^&*()", "<ESC>"],
        "Normal text !@#$%^&*()",
    )

    print(f"\nCreated {15} insert mode test cases in {test_dir}")
    print("\nTest cases cover:")
    print("- Basic insert commands (i, I)")
    print("- Append commands (a, A)")
    print("- Open line commands (o, O)")
    print("- Special key handling (backspace, enter)")
    print("- Edge cases (empty files, boundaries)")
    print("- Mode transitions")


if __name__ == "__main__":
    create_insert_mode_tests()
    print("\nInsert mode tests created successfully!")
    print("Run tests with: python test_framework.py tests/insert/")
