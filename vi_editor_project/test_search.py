"""Test file for search functionality in the vi editor."""

from test_framework import BaseViTest  # type: ignore[attr-defined]  # pyright: ignore[reportAttributeAccessIssue]


class TestSearch(BaseViTest):
    """Test search and find operations."""

    def test_forward_search_simple(self):
        """Test basic forward search."""
        self.set_buffer_content("Hello world\nHello again\nGoodbye world")

        # Search for "world"
        self.execute_command("/world")
        self.send_key("Enter")

        assert self.editor.cursor_pos == (0, 6)  # First occurrence

    def test_forward_search_next(self):
        """Test finding next occurrence with n."""
        self.set_buffer_content("Hello world\nHello again\nGoodbye world")

        # Search for "world"
        self.execute_command("/world")
        self.send_key("Enter")
        assert self.editor.cursor_pos == (0, 6)

        # Find next occurrence
        self.execute_command("n")
        assert self.editor.cursor_pos == (2, 8)  # Second occurrence

    def test_forward_search_wrap(self):
        """Test search wrapping to beginning of file."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.move_cursor(1, 0)  # Start at second line

        # Search for "First"
        self.execute_command("/First")
        self.send_key("Enter")

        # Should wrap to beginning
        assert self.editor.cursor_pos == (0, 0)

    def test_backward_search_simple(self):
        """Test basic backward search."""
        self.set_buffer_content("Hello world\nHello again\nGoodbye world")
        self.move_cursor(2, 0)  # Start at last line

        # Backward search for "Hello"
        self.execute_command("?Hello")
        self.send_key("Enter")

        assert self.editor.cursor_pos == (1, 0)  # Second line

    def test_backward_search_previous(self):
        """Test finding previous occurrence with N."""
        self.set_buffer_content("Hello world\nHello again\nGoodbye world")

        # Forward search first
        self.execute_command("/Hello")
        self.send_key("Enter")

        # Find next
        self.execute_command("n")
        assert self.editor.cursor_pos == (1, 0)

        # Find previous with N
        self.execute_command("N")
        assert self.editor.cursor_pos == (0, 0)

    def test_backward_search_wrap(self):
        """Test backward search wrapping to end of file."""
        self.set_buffer_content("First line\nSecond line\nThird line")
        self.move_cursor(1, 0)  # Start at second line

        # Backward search for "Third"
        self.execute_command("?Third")
        self.send_key("Enter")

        # Should wrap to end
        assert self.editor.cursor_pos == (2, 0)

    def test_search_not_found(self):
        """Test searching for non-existent text."""
        self.set_buffer_content("Hello world")

        # Search for non-existent text
        self.execute_command("/xyz")
        self.send_key("Enter")

        # Cursor should not move
        assert self.editor.cursor_pos == (0, 0)
        # Should have error message (if implemented)

    def test_search_empty_pattern(self):
        """Test search with empty pattern."""
        self.set_buffer_content("Hello world")

        # Empty search pattern
        self.execute_command("/")
        self.send_key("Enter")

        # Should not move or should repeat last search
        assert self.editor.cursor_pos == (0, 0)

    def test_search_case_sensitive(self):
        """Test that search is case-sensitive by default."""
        self.set_buffer_content("Hello HELLO hello")

        # Search for lowercase
        self.execute_command("/hello")
        self.send_key("Enter")

        # Should find the lowercase version at end
        assert self.editor.cursor_pos == (0, 12)

    def test_search_multiline(self):
        """Test search across multiple lines."""
        self.set_buffer_content("First line\nSecond line\nThird line")

        # Search for "Second"
        self.execute_command("/Second")
        self.send_key("Enter")

        assert self.editor.cursor_pos == (1, 0)

        # Continue to "Third"
        self.execute_command("/Third")
        self.send_key("Enter")

        assert self.editor.cursor_pos == (2, 0)

    def test_search_special_chars(self):
        """Test searching for special characters."""
        self.set_buffer_content("Hello (world) [test] {code}")

        # Search for parenthesis
        self.execute_command("/(world)")
        self.send_key("Enter")

        assert self.editor.cursor_pos == (0, 6)

    def test_search_repeat_forward(self):
        """Test repeating search in same direction."""
        self.set_buffer_content("test one test two test three")

        # Initial search
        self.execute_command("/test")
        self.send_key("Enter")
        assert self.editor.cursor_pos == (0, 0)

        # Repeat with n
        self.execute_command("n")
        assert self.editor.cursor_pos == (0, 9)

        self.execute_command("n")
        assert self.editor.cursor_pos == (0, 18)

    def test_search_repeat_reverse(self):
        """Test reversing search direction."""
        self.set_buffer_content("test one test two test three")

        # Initial forward search
        self.execute_command("/test")
        self.send_key("Enter")
        self.execute_command("n")
        self.execute_command("n")
        assert self.editor.cursor_pos == (0, 18)  # At third "test"

        # Reverse direction with N
        self.execute_command("N")
        assert self.editor.cursor_pos == (0, 9)  # Back to second "test"

    def test_search_at_end_of_line(self):
        """Test search starting from end of line."""
        self.set_buffer_content("Hello world\nNext line")
        self.move_cursor(0, 10)  # End of first line

        # Search for "Next"
        self.execute_command("/Next")
        self.send_key("Enter")

        assert self.editor.cursor_pos == (1, 0)

    def test_search_escape_cancels(self):
        """Test that escape cancels search."""
        self.set_buffer_content("Hello world")
        original_pos = self.editor.cursor_pos

        # Start search but cancel
        self.execute_command("/test")
        self.send_key("Escape")

        # Cursor should not have moved
        assert self.editor.cursor_pos == original_pos


if __name__ == "__main__":
    import unittest

    unittest.main()
