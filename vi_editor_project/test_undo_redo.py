"""Test file for undo/redo functionality in the vi editor."""

from test_framework import BaseViTest


class TestUndoRedo(BaseViTest):
    """Test undo and redo operations."""

    def test_undo_single_insertion(self):
        """Test undoing a single character insertion."""
        self.set_buffer_content("Hello")
        self.execute_command("a")  # Enter insert mode
        self.send_key("x")
        self.send_key("Escape")

        # Should have "Hellox"
        assert self.get_buffer_content() == "Hellox"

        # Undo the insertion
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello"

    def test_undo_multiple_insertions(self):
        """Test undoing multiple character insertions."""
        self.set_buffer_content("Hello")
        self.execute_command("a")
        self.send_key("x")
        self.send_key("y")
        self.send_key("z")
        self.send_key("Escape")

        # Should have "Helloxyz"
        assert self.get_buffer_content() == "Helloxyz"

        # Single undo should undo entire insert session
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello"

    def test_undo_deletion(self):
        """Test undoing a deletion operation."""
        self.set_buffer_content("Hello world")
        self.execute_command("d")
        self.execute_command("w")  # Delete word

        assert self.get_buffer_content() == "world"

        # Undo the deletion
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello world"

    def test_undo_line_deletion(self):
        """Test undoing line deletion."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.execute_command("d")
        self.execute_command("d")  # Delete entire line

        assert self.get_buffer_content() == "Second line\nThird line"

        # Undo the deletion
        self.execute_command("u")
        assert self.get_buffer_content() == "First line\nSecond line\nThird line"

    def test_redo_after_undo(self):
        """Test redo operation after undo."""
        self.set_buffer_content("Hello")
        self.execute_command("a")
        self.send_key("x")
        self.send_key("Escape")

        # Undo
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello"

        # Redo
        self.send_key("Ctrl+r")
        assert self.get_buffer_content() == "Hellox"

    def test_multiple_undo_redo(self):
        """Test multiple undo and redo operations."""
        self.set_buffer_content("")

        # Action 1: Insert "Hello"
        self.execute_command("i")
        self.send_key("H")
        self.send_key("e")
        self.send_key("l")
        self.send_key("l")
        self.send_key("o")
        self.send_key("Escape")
        assert self.get_buffer_content() == "Hello"

        # Action 2: Add " world"
        self.execute_command("a")
        self.send_key(" ")
        self.send_key("w")
        self.send_key("o")
        self.send_key("r")
        self.send_key("l")
        self.send_key("d")
        self.send_key("Escape")
        assert self.get_buffer_content() == "Hello world"

        # Undo twice
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello"

        self.execute_command("u")
        assert self.get_buffer_content() == ""

        # Redo twice
        self.send_key("Ctrl+r")
        assert self.get_buffer_content() == "Hello"

        self.send_key("Ctrl+r")
        assert self.get_buffer_content() == "Hello world"

    def test_undo_replace_operation(self):
        """Test undoing character replacement."""
        self.set_buffer_content("Hello")
        self.execute_command("r")
        self.send_key("X")  # Replace H with X

        assert self.get_buffer_content() == "Xello"

        # Undo the replacement
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello"

    def test_undo_yank_and_paste(self):
        """Test undoing paste operation."""
        self.set_buffer_content("Hello\nWorld")
        self.execute_command("y")
        self.execute_command("y")  # Yank line
        self.execute_command("p")  # Paste below

        assert self.get_buffer_content() == "Hello\nHello\nWorld"

        # Undo the paste
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello\nWorld"

    def test_undo_visual_mode_deletion(self):
        """Test undoing deletion in visual mode."""
        self.set_buffer_content("Hello world")
        self.execute_command("v")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("d")  # Delete selection

        assert self.get_buffer_content() == " world"

        # Undo the visual deletion
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello world"

    def test_undo_stack_limit(self):
        """Test that undo history has reasonable depth."""
        self.set_buffer_content("")

        # Perform many operations
        for i in range(10):
            self.execute_command("i")
            self.send_key(str(i))
            self.send_key("Escape")

        # Should be able to undo at least 10 operations
        for i in range(9, -1, -1):
            self.execute_command("u")
            expected = "".join(str(j) for j in range(i))
            assert self.get_buffer_content() == expected

    def test_redo_cleared_after_new_change(self):
        """Test that redo stack is cleared after a new change."""
        self.set_buffer_content("Hello")

        # Add text
        self.execute_command("a")
        self.send_key("x")
        self.send_key("Escape")
        assert self.get_buffer_content() == "Hellox"

        # Undo
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello"

        # Make new change
        self.execute_command("a")
        self.send_key("y")
        self.send_key("Escape")
        assert self.get_buffer_content() == "Helloy"

        # Redo should do nothing (redo stack cleared)
        self.send_key("Ctrl+r")
        assert self.get_buffer_content() == "Helloy"

    def test_undo_preserves_cursor_position(self):
        """Test that undo restores cursor position correctly."""
        self.set_buffer_content("Hello world")
        self.move_cursor(0, 6)  # Move to 'w'

        # Delete word
        self.execute_command("d")
        self.execute_command("w")
        assert self.get_buffer_content() == "Hello "
        assert self.editor.cursor_pos == (0, 5)  # At space

        # Undo should restore cursor to original position
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello world"
        assert self.editor.cursor_pos == (0, 6)  # Back at 'w'

    def test_undo_multi_line_change(self):
        """Test undoing changes that affect multiple lines."""
        self.set_buffer_content("Line 1\nLine 2\nLine 3")

        # Delete two lines
        self.execute_command("2")
        self.execute_command("d")
        self.execute_command("d")

        assert self.get_buffer_content() == "Line 3"

        # Undo
        self.execute_command("u")
        assert self.get_buffer_content() == "Line 1\nLine 2\nLine 3"

    def test_undo_join_lines(self):
        """Test undoing line join operation."""
        self.set_buffer_content("Hello\nworld")
        self.execute_command("J")  # Join lines

        assert self.get_buffer_content() == "Hello world"

        # Undo the join
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello\nworld"

    def test_undo_change_command(self):
        """Test undoing change command."""
        self.set_buffer_content("Hello world")
        self.execute_command("c")
        self.execute_command("w")  # Change word
        self.send_key("G")
        self.send_key("r")
        self.send_key("e")
        self.send_key("e")
        self.send_key("t")
        self.send_key("Escape")

        assert self.get_buffer_content() == "Greet world"

        # Undo the change
        self.execute_command("u")
        assert self.get_buffer_content() == "Hello world"


if __name__ == "__main__":
    import unittest

    unittest.main()
