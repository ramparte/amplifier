"""Unit tests for bracket movement command."""

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.movements.brackets import BracketMovement


class TestBracketMovement:
    """Test bracket matching movement."""

    def test_match_parentheses(self):
        """Test matching parentheses."""
        buffer = TextBuffer("int func(int x, int y) { return x + y; }")
        bracket_cmd = BracketMovement(buffer)

        # Position on opening parenthesis
        buffer.set_cursor(0, 8)  # On '(' after func
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 21)  # On closing ')'

    def test_match_square_brackets(self):
        """Test matching square brackets."""
        buffer = TextBuffer("array[0][1] = value")
        bracket_cmd = BracketMovement(buffer)

        # Position on opening bracket
        buffer.set_cursor(0, 5)  # On first '['
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 7)  # On first ']'

    def test_match_curly_braces(self):
        """Test matching curly braces."""
        buffer = TextBuffer("if (x) { y = 1; }")
        bracket_cmd = BracketMovement(buffer)

        # Position on opening brace
        buffer.set_cursor(0, 7)  # On '{'
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 16)  # On '}'

    def test_match_angle_brackets(self):
        """Test matching angle brackets."""
        buffer = TextBuffer("template<typename T>")
        bracket_cmd = BracketMovement(buffer)

        # Position on opening angle bracket
        buffer.set_cursor(0, 8)  # On '<'
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 19)  # On '>'

    def test_match_nested_brackets(self):
        """Test matching with nested brackets."""
        buffer = TextBuffer("func(a, (b + c), d)")
        bracket_cmd = BracketMovement(buffer)

        # Position on outer opening parenthesis
        buffer.set_cursor(0, 4)  # On first '('
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 18)  # On last ')'

        # Position on inner opening parenthesis
        buffer.set_cursor(0, 8)  # On second '('
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 14)  # On second ')'

    def test_match_backward(self):
        """Test matching from closing bracket to opening."""
        buffer = TextBuffer("int func(int x) { return x; }")
        bracket_cmd = BracketMovement(buffer)

        # Position on closing parenthesis
        buffer.set_cursor(0, 14)  # On ')' after x
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 8)  # On '(' after func

    def test_match_multiline(self):
        """Test matching across multiple lines."""
        buffer = TextBuffer("{\n  line1;\n  line2;\n}")
        bracket_cmd = BracketMovement(buffer)

        # Position on opening brace
        buffer.set_cursor(0, 0)  # On '{'
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (3, 0)  # On '}' on last line

        # Position on closing brace
        buffer.set_cursor(3, 0)  # On '}'
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 0)  # On '{' on first line

    def test_no_matching_bracket(self):
        """Test when no matching bracket exists."""
        buffer = TextBuffer("func(x, y")  # Missing closing parenthesis
        bracket_cmd = BracketMovement(buffer)

        # Position on opening parenthesis
        buffer.set_cursor(0, 4)  # On '('
        assert not bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 4)  # Cursor unchanged

    def test_search_from_non_bracket(self):
        """Test searching for bracket from non-bracket position."""
        buffer = TextBuffer("text (inside) more")
        bracket_cmd = BracketMovement(buffer)

        # Position on 't' in text
        buffer.set_cursor(0, 0)
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 12)  # On ')' - found first bracket forward

    def test_custom_bracket_pairs(self):
        """Test with custom bracket pairs."""
        buffer = TextBuffer("«custom text»")
        custom_pairs = {"«": "»", "»": "«"}
        bracket_cmd = BracketMovement(buffer, custom_pairs)

        # Position on opening custom bracket
        buffer.set_cursor(0, 0)  # On '«'
        assert bracket_cmd.find_matching_bracket()
        assert buffer.get_cursor() == (0, 12)  # On '»'

    def test_get_bracket_range(self):
        """Test getting range between brackets."""
        buffer = TextBuffer("func(arg1, arg2)")
        bracket_cmd = BracketMovement(buffer)

        # Position on opening parenthesis
        buffer.set_cursor(0, 4)  # On '('
        range_result = bracket_cmd.get_bracket_range()

        assert range_result is not None
        assert range_result == ((0, 4), (0, 15))
        # Cursor should be restored
        assert buffer.get_cursor() == (0, 4)
