"""Unit tests for editing commands."""

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.editing.case import CaseCommand
from amplifier.vi.commands.editing.indent import IndentCommand
from amplifier.vi.commands.editing.join import JoinCommand
from amplifier.vi.commands.editing.repeat import RepeatCommand
from amplifier.vi.commands.editing.repeat import RepeatManager


class TestJoinCommand:
    """Test join command functionality."""

    def test_join_two_lines(self):
        """Test joining two lines with space."""
        buffer = TextBuffer("Hello\nWorld")
        join_cmd = JoinCommand(buffer)

        assert join_cmd.join_lines(1, add_space=True)
        assert buffer.get_content() == "Hello World"

    def test_join_without_space(self):
        """Test joining without adding space (gJ)."""
        buffer = TextBuffer("Hello\nWorld")
        join_cmd = JoinCommand(buffer)

        assert join_cmd.join_lines(1, add_space=False)
        assert buffer.get_content() == "HelloWorld"

    def test_join_multiple_lines(self):
        """Test joining multiple lines."""
        buffer = TextBuffer("Line 1\nLine 2\nLine 3\nLine 4")
        join_cmd = JoinCommand(buffer)

        # Join 3 lines (current + next 2)
        assert join_cmd.join_lines(3, add_space=True)
        assert buffer.get_content() == "Line 1 Line 2 Line 3\nLine 4"

    def test_join_with_whitespace(self):
        """Test joining handles whitespace correctly."""
        buffer = TextBuffer("  Hello  \n  World  ")
        join_cmd = JoinCommand(buffer)

        assert join_cmd.join_lines(1, add_space=True)
        assert buffer.get_content() == "  Hello World  "

    def test_join_at_last_line(self):
        """Test join fails gracefully at last line."""
        buffer = TextBuffer("Only line")
        join_cmd = JoinCommand(buffer)

        assert not join_cmd.join_lines(1, add_space=True)
        assert buffer.get_content() == "Only line"

    def test_join_visual_selection(self):
        """Test joining lines in visual selection."""
        buffer = TextBuffer("Line 1\nLine 2\nLine 3\nLine 4")
        join_cmd = JoinCommand(buffer)

        assert join_cmd.join_lines_visual(1, 2, add_space=True)
        assert buffer.get_content() == "Line 1\nLine 2 Line 3\nLine 4"


class TestCaseCommand:
    """Test case conversion commands."""

    def test_toggle_case_single_char(self):
        """Test toggling case of single character."""
        buffer = TextBuffer("Hello World")
        case_cmd = CaseCommand(buffer)
        buffer.set_cursor(0, 0)

        assert case_cmd.toggle_case_char(1)
        assert buffer.get_content() == "hello World"

    def test_toggle_case_multiple_chars(self):
        """Test toggling case of multiple characters."""
        buffer = TextBuffer("Hello WORLD")
        case_cmd = CaseCommand(buffer)
        buffer.set_cursor(0, 0)

        assert case_cmd.toggle_case_char(5)
        assert buffer.get_content() == "hELLO WORLD"

    def test_convert_to_lowercase(self):
        """Test converting text to lowercase."""
        buffer = TextBuffer("HELLO WORLD")
        case_cmd = CaseCommand(buffer)

        assert case_cmd.convert_case_range(0, 0, 0, 11, "lower")
        assert buffer.get_content() == "hello world"

    def test_convert_to_uppercase(self):
        """Test converting text to uppercase."""
        buffer = TextBuffer("hello world")
        case_cmd = CaseCommand(buffer)

        assert case_cmd.convert_case_range(0, 0, 0, 11, "upper")
        assert buffer.get_content() == "HELLO WORLD"

    def test_toggle_case_range(self):
        """Test toggling case in a range."""
        buffer = TextBuffer("Hello WORLD")
        case_cmd = CaseCommand(buffer)

        assert case_cmd.convert_case_range(0, 0, 0, 11, "toggle")
        assert buffer.get_content() == "hELLO world"

    def test_convert_case_multiline(self):
        """Test case conversion across multiple lines."""
        buffer = TextBuffer("Hello\nWORLD")
        case_cmd = CaseCommand(buffer)

        assert case_cmd.convert_case_range(0, 0, 1, 5, "lower")
        assert buffer.get_content() == "hello\nworld"


class TestIndentCommand:
    """Test indentation commands."""

    def test_indent_right(self):
        """Test indenting lines to the right."""
        buffer = TextBuffer("Hello\nWorld")
        indent_cmd = IndentCommand(buffer, tabstop=4)

        assert indent_cmd.indent_lines(0, 2, "right")
        assert buffer.get_content() == "    Hello\n    World"

    def test_indent_left(self):
        """Test unindenting lines to the left."""
        buffer = TextBuffer("    Hello\n    World")
        indent_cmd = IndentCommand(buffer, tabstop=4)

        assert indent_cmd.indent_lines(0, 2, "left")
        assert buffer.get_content() == "Hello\nWorld"

    def test_indent_left_partial(self):
        """Test unindenting with partial indentation."""
        buffer = TextBuffer("  Hello\n    World")
        indent_cmd = IndentCommand(buffer, tabstop=4)

        assert indent_cmd.indent_lines(0, 2, "left")
        assert buffer.get_content() == "Hello\nWorld"

    def test_auto_indent(self):
        """Test auto-indentation."""
        buffer = TextBuffer("    function test() {\nlet x = 1;\n}")
        indent_cmd = IndentCommand(buffer, tabstop=4)

        assert indent_cmd.auto_indent_lines(1, 1)
        # Should match the indentation of the previous non-empty line
        assert buffer.get_content() == "    function test() {\n    let x = 1;\n}"

    def test_indent_visual_selection(self):
        """Test indenting visual selection."""
        buffer = TextBuffer("Line 1\nLine 2\nLine 3")
        indent_cmd = IndentCommand(buffer, tabstop=2)

        assert indent_cmd.indent_visual(0, 1, "right")
        assert buffer.get_content() == "  Line 1\n  Line 2\nLine 3"


class TestRepeatCommand:
    """Test repeat command functionality."""

    def test_repeat_text_insertion(self):
        """Test repeating text insertion."""
        buffer = TextBuffer("Hello")
        repeat_mgr = RepeatManager()
        repeat_cmd = RepeatCommand(buffer, repeat_mgr)

        # Record a change
        change = repeat_mgr.create_change_from_context(
            command="i",
            count=1,
            text_inserted=" World",
        )
        repeat_mgr.stop_recording(change)

        # Create a mock context
        class MockContext:
            count = 1

        ctx = MockContext()

        # Execute repeat
        buffer.set_cursor(0, 5)  # Position at end
        assert repeat_cmd.execute_repeat(ctx)
        assert buffer.get_content() == "Hello World"

    def test_repeat_with_count(self):
        """Test repeating with a different count."""
        buffer = TextBuffer("")
        repeat_mgr = RepeatManager()
        repeat_cmd = RepeatCommand(buffer, repeat_mgr)

        # Record a change
        change = repeat_mgr.create_change_from_context(
            command="i",
            count=1,
            text_inserted="x",
        )
        repeat_mgr.stop_recording(change)

        # Create a mock context with count
        class MockContext:
            count = 3

        ctx = MockContext()

        # Execute repeat with count
        assert repeat_cmd.execute_repeat(ctx)
        assert buffer.get_content() == "xxx"

    def test_no_repeat_available(self):
        """Test repeat when no change is recorded."""
        buffer = TextBuffer("Hello")
        repeat_mgr = RepeatManager()
        repeat_cmd = RepeatCommand(buffer, repeat_mgr)

        class MockContext:
            count = 1

        ctx = MockContext()

        assert not repeat_cmd.execute_repeat(ctx)
        assert buffer.get_content() == "Hello"
