#!/usr/bin/env python3
"""
Test suite for file I/O operations in vi editor.

Tests ex commands like :w, :q, :wq, :q!, :e, and file handling.
"""

from pathlib import Path


def create_file_io_tests():
    """Create comprehensive file I/O test cases."""
    test_root = Path("tests/file_io")
    test_root.mkdir(parents=True, exist_ok=True)

    # Test 1: Save file with :w
    test_dir = test_root / "test_save_file"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Initial content\nSecond line\n")
    (test_dir / "actions.txt").write_text("""# Test saving file with :w
i<ESC>
A modified<ESC>
:w<ENTER>
""")
    (test_dir / "expected.txt").write_text("Initial content modified\nSecond line\n")
    (test_dir / "metadata.json").write_text('{"description": "Test :w save command"}')

    # Test 2: Save and quit with :wq
    test_dir = test_root / "test_save_quit"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Original text\n")
    (test_dir / "actions.txt").write_text("""# Test save and quit with :wq
o
New line added<ESC>
:wq<ENTER>
""")
    (test_dir / "expected.txt").write_text("Original text\nNew line added\n")
    (test_dir / "metadata.json").write_text('{"description": "Test :wq save and quit command"}')

    # Test 3: Quit without saving with :q
    test_dir = test_root / "test_quit_no_changes"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Unchanged content\n")
    (test_dir / "actions.txt").write_text("""# Test quit without changes
:q<ENTER>
""")
    (test_dir / "expected.txt").write_text("Unchanged content\n")
    (test_dir / "metadata.json").write_text('{"description": "Test :q quit without changes"}')

    # Test 4: Force quit with :q!
    test_dir = test_root / "test_force_quit"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Original content\n")
    (test_dir / "actions.txt").write_text("""# Test force quit discarding changes
i
Modified but not saved<ESC>
:q!<ENTER>
""")
    (test_dir / "expected.txt").write_text("Original content\n")
    (test_dir / "metadata.json").write_text('{"description": "Test :q! force quit discarding changes"}')

    # Test 5: Write to new file with :w filename
    test_dir = test_root / "test_write_new_file"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Content to save\nIn new file\n")
    (test_dir / "actions.txt").write_text("""# Test writing to specific file
:w newfile.txt<ENTER>
""")
    (test_dir / "expected.txt").write_text("Content to save\nIn new file\n")
    (test_dir / "metadata.json").write_text('{"description": "Test :w filename to save to specific file"}')

    # Test 6: Open file with :e
    test_dir = test_root / "test_open_file"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Current file\n")
    (test_dir / "actions.txt").write_text("""# Test opening another file
:e testfile.txt<ENTER>
""")
    # Expected would depend on testfile.txt content
    (test_dir / "expected.txt").write_text("")  # Would be replaced with testfile.txt content
    (test_dir / "metadata.json").write_text('{"description": "Test :e filename to open another file"}')

    # Test 7: Handle write permission error
    test_dir = test_root / "test_write_permission_error"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("Some content\n")
    (test_dir / "actions.txt").write_text("""# Test handling permission error
:w /root/readonly.txt<ENTER>
""")
    (test_dir / "expected.txt").write_text("Some content\n")
    (test_dir / "metadata.json").write_text('{"description": "Test handling write permission error"}')

    # Test 8: Save empty file
    test_dir = test_root / "test_save_empty"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("")
    (test_dir / "actions.txt").write_text("""# Test saving empty file
:w<ENTER>
""")
    (test_dir / "expected.txt").write_text("")
    (test_dir / "metadata.json").write_text('{"description": "Test saving empty file"}')

    # Test 9: Save large file
    test_dir = test_root / "test_save_large_file"
    test_dir.mkdir(exist_ok=True)
    # Create large content
    large_content = "\n".join([f"Line {i}" for i in range(1000)])
    (test_dir / "input.txt").write_text(large_content)
    (test_dir / "actions.txt").write_text("""# Test saving large file
G
o
Last line added<ESC>
:w<ENTER>
""")
    (test_dir / "expected.txt").write_text(large_content + "\nLast line added\n")
    (test_dir / "metadata.json").write_text('{"description": "Test saving large file with 1000+ lines"}')

    # Test 10: Append to existing file
    test_dir = test_root / "test_append_file"
    test_dir.mkdir(exist_ok=True)
    (test_dir / "input.txt").write_text("First part\n")
    (test_dir / "actions.txt").write_text("""# Test appending to file
o
Second part<ESC>
:w >> output.txt<ENTER>
""")
    (test_dir / "expected.txt").write_text("First part\nSecond part\n")
    (test_dir / "metadata.json").write_text('{"description": "Test appending to file with :w >>"}')

    print(f"Created {len(list(test_root.glob('test_*')))} file I/O test cases in {test_root}")


def run_file_io_tests(editor_factory):
    """Run all file I/O tests."""
    from test_framework import TestRunner

    runner = TestRunner(Path("tests/file_io"))
    return runner.run_tests(editor_factory)


if __name__ == "__main__":
    # Create the test cases
    create_file_io_tests()

    print("\nFile I/O tests have been created.")
    print("\nTo run these tests, implement the file_io module and then:")
    print("  from test_file_io import run_file_io_tests")
    print("  from editor import create_editor")
    print("  passed, failed = run_file_io_tests(create_editor)")
