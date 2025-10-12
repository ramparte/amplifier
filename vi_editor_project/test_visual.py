"""Test file for visual mode functionality in the vi editor."""

from test_framework import BaseViTest  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]


class TestVisualMode(BaseViTest):
    """Test visual mode operations."""

    def test_visual_char_mode_enter(self):
        """Test entering visual character mode."""
        self.set_buffer_content("Hello world\nSecond line\nThird line")
        self.execute_command("v")
        assert self.editor.mode == "VISUAL"
        assert self.editor.visual_mode_type == "char"
        assert self.editor.visual_start == (0, 0)
        assert self.editor.visual_end == (0, 0)

    def test_visual_line_mode_enter(self):
        """Test entering visual line mode."""
        self.set_buffer_content("Hello world\nSecond line\nThird line")
        self.execute_command("V")
        assert self.editor.mode == "VISUAL"
        assert self.editor.visual_mode_type == "line"
        assert self.editor.visual_start == (0, 0)
        assert self.editor.visual_end == (0, -1)  # Full line selection

    def test_visual_char_selection_movement(self):
        """Test character-wise visual selection with movement."""
        self.set_buffer_content("Hello world\nSecond line")
        self.execute_command("v")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")

        assert self.editor.mode == "VISUAL"
        assert self.editor.visual_start == (0, 0)
        assert self.editor.visual_end == (0, 3)
        assert self.get_visual_selection() == "Hell"

    def test_visual_line_selection_movement(self):
        """Test line-wise visual selection with movement."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.execute_command("V")
        self.execute_command("j")

        assert self.editor.mode == "VISUAL"
        assert self.editor.visual_mode_type == "line"
        assert self.get_visual_selection() == "First line\nSecond line"

    def test_visual_delete_chars(self):
        """Test deleting characters in visual mode."""
        self.set_buffer_content("Hello world")
        self.execute_command("v")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("d")

        assert self.editor.mode == "NORMAL"
        assert self.get_buffer_content() == " world"
        assert self.editor.cursor_pos == (0, 0)

    def test_visual_delete_lines(self):
        """Test deleting lines in visual line mode."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.execute_command("V")
        self.execute_command("j")
        self.execute_command("d")

        assert self.editor.mode == "NORMAL"
        assert self.get_buffer_content() == "Third line"
        assert self.editor.cursor_pos == (0, 0)

    def test_visual_yank_chars(self):
        """Test yanking characters in visual mode."""
        self.set_buffer_content("Hello world")
        self.execute_command("v")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("l")
        self.execute_command("y")

        assert self.editor.mode == "NORMAL"
        assert self.get_buffer_content() == "Hello world"  # Content unchanged
        assert self.editor.yank_buffer == "Hello"
        assert self.editor.cursor_pos == (0, 0)

    def test_visual_yank_lines(self):
        """Test yanking lines in visual line mode."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.execute_command("V")
        self.execute_command("j")
        self.execute_command("y")

        assert self.editor.mode == "NORMAL"
        assert self.get_buffer_content() == "First line\nSecond line\nThird line"
        assert self.editor.yank_buffer == "First line\nSecond line\n"
        assert self.editor.cursor_pos == (0, 0)

    def test_visual_mode_escape(self):
        """Test escaping from visual mode."""
        self.set_buffer_content("Hello world")
        self.execute_command("v")
        self.execute_command("l")
        self.execute_command("l")
        self.send_key("Escape")

        assert self.editor.mode == "NORMAL"
        assert not hasattr(self.editor, "visual_start") or self.editor.visual_start is None
        assert self.editor.cursor_pos == (0, 2)  # Cursor stays at current position

    def test_visual_selection_word_movement(self):
        """Test visual selection with word movements."""
        self.set_buffer_content("Hello world from vi editor")
        self.execute_command("v")
        self.execute_command("w")

        assert self.get_visual_selection() == "Hello "

        self.execute_command("w")
        assert self.get_visual_selection() == "Hello world "

    def test_visual_selection_end_movement(self):
        """Test visual selection with end-of-word movement."""
        self.set_buffer_content("Hello world from vi")
        self.execute_command("v")
        self.execute_command("e")

        assert self.get_visual_selection() == "Hello"

    def test_visual_selection_line_end(self):
        """Test visual selection to end of line."""
        self.set_buffer_content("Hello world")
        self.execute_command("v")
        self.execute_command("$")

        assert self.get_visual_selection() == "Hello world"

    def test_visual_selection_line_start(self):
        """Test visual selection from middle to start of line."""
        self.set_buffer_content("Hello world")
        self.move_cursor(0, 6)  # Start at 'w'
        self.execute_command("v")
        self.execute_command("0")

        # Visual selection should be reversed
        assert self.get_visual_selection() == "Hello "

    def test_visual_empty_selection(self):
        """Test visual mode with no movement (single character selection)."""
        self.set_buffer_content("Hello")
        self.execute_command("v")

        assert self.get_visual_selection() == "H"

    def test_visual_multiline_char_selection(self):
        """Test character visual selection across multiple lines."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.execute_command("v")
        self.execute_command("j")
        self.execute_command("l")
        self.execute_command("l")

        assert self.get_visual_selection() == "First line\nSec"

    def test_visual_selection_at_eof(self):
        """Test visual selection at end of file."""
        self.set_buffer_content("Single line")
        self.move_cursor(0, 10)  # Move to last character
        self.execute_command("v")

        assert self.get_visual_selection() == "e"

    def test_visual_backwards_selection(self):
        """Test visual selection moving backwards."""
        self.set_buffer_content("Hello world")
        self.move_cursor(0, 6)  # Start at 'w'
        self.execute_command("v")
        self.execute_command("h")
        self.execute_command("h")

        # Selection from position 4 to 6
        assert self.get_visual_selection() == "o w"


if __name__ == "__main__":
    import unittest

    unittest.main()
