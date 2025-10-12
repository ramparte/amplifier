#!/usr/bin/env python3
"""Create comprehensive buffer management test cases."""

import json
from pathlib import Path


def create_test(test_dir: str, input_content: str, actions: str, expected: str, description: str):
    """Create a single test case."""
    test_path = Path("tests/buffer") / test_dir
    test_path.mkdir(parents=True, exist_ok=True)

    (test_path / "input.txt").write_text(input_content)
    (test_path / "actions.txt").write_text(actions)
    (test_path / "expected.txt").write_text(expected)

    metadata = {"name": test_dir, "description": description, "category": "buffer"}
    (test_path / "metadata.json").write_text(json.dumps(metadata, indent=2))

    print(f"Created test: {test_dir}")


# Test 1: Empty file handling
create_test(
    "test_empty_file",
    "",  # Empty input
    "# Test empty file - just move around\njjj\nkkk\nlll\nhhh",
    "",  # Should remain empty
    "Test cursor movement in empty file",
)

# Test 2: Single line file
create_test(
    "test_single_line",
    "Hello World",
    "# Test navigation on single line\n0\n$\n5l\n3h",
    "Hello World",
    "Test cursor movement on single line",
)

# Test 3: Multi-line file navigation
create_test(
    "test_multi_line",
    "Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    "# Navigate through multiple lines\nj\nj\nk\n$\n0",
    "Line 1\nLine 2\nLine 3\nLine 4\nLine 5",
    "Test navigation in multi-line file",
)

# Test 4: Line insertion at beginning
create_test(
    "test_insert_line_beginning",
    "Line 1\nLine 2\nLine 3",
    "# Insert new line at beginning\nO\nNew First Line\n<ESC>",
    "New First Line\nLine 1\nLine 2\nLine 3",
    "Test inserting line at file beginning",
)

# Test 5: Line insertion in middle
create_test(
    "test_insert_line_middle",
    "Line 1\nLine 2\nLine 3",
    "# Insert line in middle\nj\no\nInserted Line\n<ESC>",
    "Line 1\nLine 2\nInserted Line\nLine 3",
    "Test inserting line in middle of file",
)

# Test 6: Line deletion
create_test(
    "test_delete_line",
    "Line 1\nLine 2\nLine 3\nLine 4",
    "# Delete second line\nj\ndd",
    "Line 1\nLine 3\nLine 4",
    "Test deleting a line",
)

# Test 7: Character insertion
create_test(
    "test_insert_chars", "Hello", "# Insert characters\n$\na\n World\n<ESC>", "Hello World", "Test character insertion"
)

# Test 8: Character deletion
create_test("test_delete_chars", "Hello World", "# Delete characters\n5l\n5x", "Hello", "Test character deletion")

# Test 9: Large file handling
lines = [f"Line {i}" for i in range(1, 1001)]
create_test(
    "test_large_file",
    "\n".join(lines),
    "# Navigate large file\nG\ngg\n500j\nG",
    "\n".join(lines),
    "Test handling 1000+ line file",
)

# Test 10: Special characters and Unicode
create_test(
    "test_special_chars",
    "Hello 世界!\n#include <stdio.h>\n$PATH = /usr/bin\n🎉 Unicode émojis",
    "# Navigate special characters\nj\n$\n0\nj\n$",
    "Hello 世界!\n#include <stdio.h>\n$PATH = /usr/bin\n🎉 Unicode émojis",
    "Test special characters and Unicode",
)

# Test 11: Cursor boundaries
create_test(
    "test_cursor_boundaries",
    "Short\nA much longer line here\nTiny",
    "# Test cursor boundaries\nj\n$\nj\nlllllllll\nk\n$",
    "Short\nA much longer line here\nTiny",
    "Test cursor boundary constraints",
)

# Test 12: Empty line handling
create_test(
    "test_empty_lines",
    "Line 1\n\n\nLine 4\n\nLine 6",
    "# Navigate through empty lines\nj\nj\nj\nx\nj",
    "Line 1\n\n\nLine 4\n\nLine 6",
    "Test handling empty lines",
)

print(f"\nCreated {12} buffer management tests in tests/buffer/")
