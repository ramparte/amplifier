#!/usr/bin/env python3
"""
Create comprehensive navigation command tests for the vi editor.

This script generates test cases for all navigation commands including:
- h,j,k,l movement (left, down, up, right)
- w,b word movement (forward, backward)
- 0,$ line start/end
- gg,G file start/end
- Numbered movements (5j, 10l, etc.)
- Edge cases: empty lines, file boundaries, word boundaries
"""

from pathlib import Path


def create_test_directory(base_path: Path, test_name: str) -> Path:
    """Create a test directory with the given name."""
    test_dir = base_path / test_name
    test_dir.mkdir(parents=True, exist_ok=True)
    return test_dir


def write_test_files(test_dir: Path, input_content: str, actions: list, expected_content: str, description: str):
    """Write the three test files for a test case."""
    # Write description
    (test_dir / "description.txt").write_text(description)

    # Write input file
    (test_dir / "input_file.txt").write_text(input_content)

    # Write actions file
    (test_dir / "actions.txt").write_text("\n".join(actions))

    # Write expected output
    (test_dir / "expected_output.txt").write_text(expected_content)


def create_navigation_tests():
    """Create all navigation test cases."""
    base_path = Path("/workspaces/amplifier/vi_editor_project/tests/navigation")

    # Test 1: Basic h movement (left)
    test_dir = create_test_directory(base_path, "test_h_movement")
    write_test_files(
        test_dir,
        input_content="Hello world\nSecond line\nThird line",
        actions=["set_cursor:0,5", "h", "h", "h"],  # Start at 'w' in world, move left 3 times
        expected_content="Hello world\nSecond line\nThird line",
        description="Test h (left) movement - cursor should move left",
    )

    # Test 2: Basic j movement (down)
    test_dir = create_test_directory(base_path, "test_j_movement")
    write_test_files(
        test_dir,
        input_content="First line\nSecond line\nThird line\nFourth line",
        actions=["set_cursor:0,0", "j", "j"],  # Move down 2 lines
        expected_content="First line\nSecond line\nThird line\nFourth line",
        description="Test j (down) movement - cursor should move down",
    )

    # Test 3: Basic k movement (up)
    test_dir = create_test_directory(base_path, "test_k_movement")
    write_test_files(
        test_dir,
        input_content="First line\nSecond line\nThird line",
        actions=["set_cursor:2,0", "k", "k"],  # Start at third line, move up 2
        expected_content="First line\nSecond line\nThird line",
        description="Test k (up) movement - cursor should move up",
    )

    # Test 4: Basic l movement (right)
    test_dir = create_test_directory(base_path, "test_l_movement")
    write_test_files(
        test_dir,
        input_content="Hello world\nTest line",
        actions=["set_cursor:0,0", "l", "l", "l", "l"],  # Move right 4 times
        expected_content="Hello world\nTest line",
        description="Test l (right) movement - cursor should move right",
    )

    # Test 5: Word forward movement (w)
    test_dir = create_test_directory(base_path, "test_w_movement")
    write_test_files(
        test_dir,
        input_content="The quick brown fox jumps",
        actions=["set_cursor:0,0", "w", "w", "w"],  # Move forward 3 words
        expected_content="The quick brown fox jumps",
        description="Test w (word forward) movement",
    )

    # Test 6: Word backward movement (b)
    test_dir = create_test_directory(base_path, "test_b_movement")
    write_test_files(
        test_dir,
        input_content="The quick brown fox jumps",
        actions=["set_cursor:0,16", "b", "b"],  # Start at 'f' in fox, move back 2 words
        expected_content="The quick brown fox jumps",
        description="Test b (word backward) movement",
    )

    # Test 7: Line start movement (0)
    test_dir = create_test_directory(base_path, "test_0_movement")
    write_test_files(
        test_dir,
        input_content="    Indented line\nAnother line",
        actions=["set_cursor:0,10", "0"],  # Move to start of line
        expected_content="    Indented line\nAnother line",
        description="Test 0 (line start) movement",
    )

    # Test 8: Line end movement ($)
    test_dir = create_test_directory(base_path, "test_dollar_movement")
    write_test_files(
        test_dir,
        input_content="Short line\nA much longer line here",
        actions=["set_cursor:1,0", "$"],  # Move to end of second line
        expected_content="Short line\nA much longer line here",
        description="Test $ (line end) movement",
    )

    # Test 9: File start movement (gg)
    test_dir = create_test_directory(base_path, "test_gg_movement")
    write_test_files(
        test_dir,
        input_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        actions=["set_cursor:3,2", "gg"],  # Start at line 4, go to file start
        expected_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        description="Test gg (file start) movement",
    )

    # Test 10: File end movement (G)
    test_dir = create_test_directory(base_path, "test_G_movement")
    write_test_files(
        test_dir,
        input_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        actions=["set_cursor:1,2", "G"],  # Start at line 2, go to file end
        expected_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        description="Test G (file end) movement",
    )

    # Test 11: Numbered j movement (5j)
    test_dir = create_test_directory(base_path, "test_numbered_j")
    write_test_files(
        test_dir,
        input_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7",
        actions=["set_cursor:0,0", "5j"],  # Move down 5 lines
        expected_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7",
        description="Test numbered j movement (5j)",
    )

    # Test 12: Numbered l movement (10l)
    test_dir = create_test_directory(base_path, "test_numbered_l")
    write_test_files(
        test_dir,
        input_content="This is a very long line with many characters",
        actions=["set_cursor:0,0", "10l"],  # Move right 10 characters
        expected_content="This is a very long line with many characters",
        description="Test numbered l movement (10l)",
    )

    # Test 13: Boundary test - can't move past last line
    test_dir = create_test_directory(base_path, "test_boundary_bottom")
    write_test_files(
        test_dir,
        input_content="Line 1\nLine 2\nLine 3",
        actions=["set_cursor:2,0", "j", "j", "j"],  # Try to move past last line
        expected_content="Line 1\nLine 2\nLine 3",
        description="Test boundary - cursor stays at last line when moving down",
    )

    # Test 14: Boundary test - can't move past first line
    test_dir = create_test_directory(base_path, "test_boundary_top")
    write_test_files(
        test_dir,
        input_content="Line 1\nLine 2\nLine 3",
        actions=["set_cursor:0,0", "k", "k"],  # Try to move past first line
        expected_content="Line 1\nLine 2\nLine 3",
        description="Test boundary - cursor stays at first line when moving up",
    )

    # Test 15: Word boundary with punctuation
    test_dir = create_test_directory(base_path, "test_word_punctuation")
    write_test_files(
        test_dir,
        input_content="hello, world! test-case (parenthesis)",
        actions=["set_cursor:0,0", "w", "w", "w", "w"],  # Navigate through punctuated words
        expected_content="hello, world! test-case (parenthesis)",
        description="Test word movement with punctuation",
    )

    # Test 16: Empty line navigation
    test_dir = create_test_directory(base_path, "test_empty_lines")
    write_test_files(
        test_dir,
        input_content="Line 1\n\n\nLine 4\n\nLine 6",
        actions=["set_cursor:0,0", "j", "j", "j"],  # Navigate through empty lines
        expected_content="Line 1\n\n\nLine 4\n\nLine 6",
        description="Test navigation through empty lines",
    )

    # Test 17: Line end boundary - can't move past line end
    test_dir = create_test_directory(base_path, "test_boundary_line_end")
    write_test_files(
        test_dir,
        input_content="Short",
        actions=["set_cursor:0,4", "l", "l", "l"],  # Try to move past line end
        expected_content="Short",
        description="Test boundary - cursor stays at line end",
    )

    # Test 18: Numbered k movement (3k)
    test_dir = create_test_directory(base_path, "test_numbered_k")
    write_test_files(
        test_dir,
        input_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        actions=["set_cursor:4,0", "3k"],  # Move up 3 lines from line 5
        expected_content="Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
        description="Test numbered k movement (3k)",
    )

    # Test 19: Numbered h movement (5h)
    test_dir = create_test_directory(base_path, "test_numbered_h")
    write_test_files(
        test_dir,
        input_content="This is a test line",
        actions=["set_cursor:0,10", "5h"],  # Move left 5 characters
        expected_content="This is a test line",
        description="Test numbered h movement (5h)",
    )

    # Test 20: Complex navigation sequence
    test_dir = create_test_directory(base_path, "test_complex_navigation")
    write_test_files(
        test_dir,
        input_content="First line here\nSecond line\nThird line\nFourth line",
        actions=["set_cursor:0,0", "j", "l", "l", "l", "j", "$", "k", "0"],  # Complex sequence
        expected_content="First line here\nSecond line\nThird line\nFourth line",
        description="Test complex navigation sequence",
    )

    print("Created 20 navigation test cases in /workspaces/amplifier/vi_editor_project/tests/navigation/")

    # List all created tests
    test_dirs = sorted([d for d in base_path.iterdir() if d.is_dir()])
    print("\nCreated tests:")
    for test_dir in test_dirs:
        desc_file = test_dir / "description.txt"
        if desc_file.exists():
            desc = desc_file.read_text().strip()
            print(f"  - {test_dir.name}: {desc}")


if __name__ == "__main__":
    create_navigation_tests()
