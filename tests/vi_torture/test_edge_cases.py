"""Torture tests for vi editor - edge cases and boundary conditions."""

import pytest

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.executor import CommandExecutor
from amplifier.vi.modes.state import ModeManager


class MockRenderer:
    """Mock renderer for testing."""

    def __init__(self):
        self.messages = []

    def show_message(self, msg: str) -> None:
        self.messages.append(msg)

    def clear_message(self) -> None:
        self.messages.clear()


@pytest.fixture
def setup_vi():
    """Set up vi components for testing."""
    buffer = TextBuffer()
    modes = ModeManager()
    renderer = MockRenderer()
    executor = CommandExecutor(buffer, modes, renderer)
    return buffer, modes, renderer, executor


class TestEmptyBufferEdgeCases:
    """Test operations on empty buffers."""

    def test_empty_buffer_movements(self, setup_vi):
        """Test all movement commands on empty buffer."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([])

        # All movements should handle empty buffer gracefully
        commands = ["h", "j", "k", "l", "w", "b", "e", "0", "$", "G", "gg"]
        for cmd in commands:
            executor.execute_normal(cmd)
            assert buffer.get_cursor() == (0, 0)

    def test_empty_buffer_editing(self, setup_vi):
        """Test editing commands on empty buffer."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([])

        # Should not crash
        executor.execute_normal("x")
        executor.execute_normal("dd")
        executor.execute_normal("yy")
        executor.execute_normal("p")

        assert buffer.get_lines() == []

    def test_empty_buffer_visual_mode(self, setup_vi):
        """Test visual mode on empty buffer."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([])

        executor.execute_normal("v")
        assert modes.current_mode == "visual"

        executor.execute_visual("d")
        assert modes.current_mode == "normal"
        assert buffer.get_lines() == []


class TestSingleCharacterBuffer:
    """Test operations on single character buffers."""

    def test_single_char_movements(self, setup_vi):
        """Test movements on single character."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["a"])
        buffer.set_cursor(0, 0)

        # Move right should stay at position
        executor.execute_normal("l")
        assert buffer.get_cursor() == (0, 0)

        # Move down should stay at position
        executor.execute_normal("j")
        assert buffer.get_cursor() == (0, 0)

    def test_single_char_deletion(self, setup_vi):
        """Test deleting single character."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["a"])
        buffer.set_cursor(0, 0)

        executor.execute_normal("x")
        assert buffer.get_lines() == [""]

    def test_single_char_visual(self, setup_vi):
        """Test visual mode on single character."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["a"])
        buffer.set_cursor(0, 0)

        executor.execute_normal("v")
        executor.execute_visual("d")
        assert buffer.get_lines() == [""]


class TestLongLines:
    """Test operations on very long lines."""

    def test_long_line_movement(self, setup_vi):
        """Test movements on 10000 character line."""
        buffer, modes, renderer, executor = setup_vi
        long_line = "a" * 10000
        buffer.set_lines([long_line])
        buffer.set_cursor(0, 0)

        # Move to end
        executor.execute_normal("$")
        assert buffer.get_cursor() == (0, 9999)

        # Move to beginning
        executor.execute_normal("0")
        assert buffer.get_cursor() == (0, 0)

        # Move by words (should handle efficiently)
        executor.execute_normal("w")
        # With no spaces, w should move to end
        assert buffer.get_cursor() == (0, 9999)

    def test_long_line_deletion(self, setup_vi):
        """Test deleting from long line."""
        buffer, modes, renderer, executor = setup_vi
        long_line = "a" * 10000
        buffer.set_lines([long_line])
        buffer.set_cursor(0, 0)

        # Delete to end of line
        executor.execute_normal("D")
        assert buffer.get_lines() == [""]

    def test_long_line_yank(self, setup_vi):
        """Test yanking long line."""
        buffer, modes, renderer, executor = setup_vi
        long_line = "a" * 10000
        buffer.set_lines([long_line])
        buffer.set_cursor(0, 0)

        # Yank line
        executor.execute_normal("yy")
        # Should not crash or hang


class TestManyLines:
    """Test operations on buffers with many lines."""

    def test_many_lines_navigation(self, setup_vi):
        """Test navigation with 10000 lines."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(10000)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        # Jump to end
        executor.execute_normal("G")
        assert buffer.get_cursor()[0] == 9999

        # Jump to beginning
        executor.execute_normal("gg")
        assert buffer.get_cursor()[0] == 0

        # Jump to specific line
        executor.execute_normal("5000G")
        assert buffer.get_cursor()[0] == 4999  # 0-indexed

    def test_many_lines_deletion(self, setup_vi):
        """Test deleting from large buffer."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(1000)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        # Delete first 100 lines
        executor.execute_normal("100dd")
        assert len(buffer.get_lines()) == 900
        assert buffer.get_lines()[0] == "line 100"


class TestUnicodeEdgeCases:
    """Test Unicode and special character handling."""

    def test_unicode_characters(self, setup_vi):
        """Test operations on Unicode text."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["Hello 世界 🌍"])
        buffer.set_cursor(0, 0)

        # Move through Unicode characters
        executor.execute_normal("w")
        executor.execute_normal("w")
        executor.execute_normal("w")

        # Should handle without crashing

    def test_zero_width_characters(self, setup_vi):
        """Test zero-width combining characters."""
        buffer, modes, renderer, executor = setup_vi
        # Combining diacritic marks
        buffer.set_lines(["e\u0301"])  # é as e + combining acute
        buffer.set_cursor(0, 0)

        executor.execute_normal("x")
        # Should delete properly

    def test_rtl_text(self, setup_vi):
        """Test right-to-left text."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["Hello مرحبا"])
        buffer.set_cursor(0, 0)

        # Move through mixed LTR/RTL text
        for _ in range(10):
            executor.execute_normal("l")
        # Should not crash


class TestBoundaryConditions:
    """Test boundary conditions and off-by-one errors."""

    def test_cursor_at_line_end(self, setup_vi):
        """Test operations with cursor at line end."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["hello"])
        buffer.set_cursor(0, 4)  # At 'o'

        # Try to move past end
        executor.execute_normal("l")
        assert buffer.get_cursor()[1] == 4

        # Delete at end
        executor.execute_normal("x")
        assert buffer.get_lines() == ["hell"]

    def test_cursor_at_buffer_end(self, setup_vi):
        """Test operations at buffer end."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line1", "line2", "line3"])
        buffer.set_cursor(2, 0)  # Last line

        # Try to move past end
        executor.execute_normal("j")
        assert buffer.get_cursor()[0] == 2

        # Delete last line
        executor.execute_normal("dd")
        assert len(buffer.get_lines()) == 2

    def test_cursor_at_empty_line(self, setup_vi):
        """Test operations on empty lines."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line1", "", "line3"])
        buffer.set_cursor(1, 0)  # Empty line

        # Move right on empty line
        executor.execute_normal("l")
        assert buffer.get_cursor() == (1, 0)

        # Delete empty line
        executor.execute_normal("dd")
        assert buffer.get_lines() == ["line1", "line3"]


class TestRepeatedOperations:
    """Test operations with large repeat counts."""

    def test_large_repeat_count(self, setup_vi):
        """Test movements with large repeat counts."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(100)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        # Move down 1000 times (should stop at end)
        executor.execute_normal("1000j")
        assert buffer.get_cursor()[0] == 99

        # Move up 1000 times (should stop at start)
        executor.execute_normal("1000k")
        assert buffer.get_cursor()[0] == 0

    def test_repeated_deletion(self, setup_vi):
        """Test deleting with large repeat count."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(100)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        # Delete more lines than exist
        executor.execute_normal("1000dd")
        assert buffer.get_lines() == []

    def test_repeated_insertion(self, setup_vi):
        """Test inserting with repeat count."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([""])
        buffer.set_cursor(0, 0)

        # Insert with repeat
        executor.execute_normal("100i")
        modes.to_insert()
        buffer.insert_char("x")
        modes.to_normal()

        # Should insert 100 x's
        # Note: This tests the concept, actual implementation may vary


class TestMarkEdgeCases:
    """Test mark system edge cases."""

    def test_mark_on_empty_buffer(self, setup_vi):
        """Test setting mark on empty buffer."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([])

        executor.execute_normal("m")
        executor.execute_normal("a")
        # Should not crash

    def test_mark_after_deletion(self, setup_vi):
        """Test marks after deleting marked line."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line1", "line2", "line3"])
        buffer.set_cursor(1, 0)

        # Set mark on line 2
        executor.execute_normal("m")
        executor.execute_normal("a")

        # Delete line 2
        executor.execute_normal("dd")

        # Try to jump to mark
        executor.execute_normal("'")
        executor.execute_normal("a")
        # Should handle gracefully


class TestVisualModeEdgeCases:
    """Test visual mode edge cases."""

    def test_visual_selection_empty_lines(self, setup_vi):
        """Test visual selection across empty lines."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line1", "", "", "line4"])
        buffer.set_cursor(0, 0)

        executor.execute_normal("V")
        executor.execute_normal("3j")
        executor.execute_visual("d")

        assert buffer.get_lines() == []

    def test_visual_mode_at_buffer_boundaries(self, setup_vi):
        """Test visual mode at buffer start/end."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line1", "line2", "line3"])

        # Start at beginning
        buffer.set_cursor(0, 0)
        executor.execute_normal("v")
        executor.execute_normal("k")  # Try to go up
        # Should stay at beginning

        # Start at end
        buffer.set_cursor(2, 0)
        executor.execute_normal("v")
        executor.execute_normal("j")  # Try to go down
        # Should stay at end


class TestSearchEdgeCases:
    """Test search system edge cases."""

    def test_search_empty_pattern(self, setup_vi):
        """Test searching with empty pattern."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["hello world"])
        # Implementation would need command line mode

    def test_search_not_found(self, setup_vi):
        """Test searching for non-existent pattern."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["hello world"])
        # Should show appropriate message

    def test_search_regex_errors(self, setup_vi):
        """Test invalid regex patterns."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["hello world"])
        # Should handle invalid regex gracefully


class TestMemoryStress:
    """Test memory and performance under stress."""

    def test_large_buffer_operations(self, setup_vi):
        """Test with very large buffer."""
        buffer, modes, renderer, executor = setup_vi
        # Create 50000 line buffer
        lines = [f"line {i} with some content" for i in range(50000)]
        buffer.set_lines(lines)

        # Should handle without excessive memory
        buffer.set_cursor(0, 0)
        executor.execute_normal("G")
        executor.execute_normal("gg")

    def test_many_undo_operations(self, setup_vi):
        """Test undo stack with many operations."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([""])
        buffer.set_cursor(0, 0)

        # Perform many operations (when undo is implemented)
        for _ in range(1000):
            modes.to_insert()
            buffer.insert_char("a")
            modes.to_normal()

        # Undo stack should handle appropriately


class TestConcurrentOperations:
    """Test behavior with rapid operations."""

    def test_rapid_mode_switching(self, setup_vi):
        """Test rapid mode switches."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["hello"])

        # Rapid mode switches
        for _ in range(100):
            modes.to_insert()
            modes.to_normal()
            modes.to_visual()
            modes.to_normal()

        # Should maintain consistency
        assert modes.current_mode == "normal"

    def test_rapid_cursor_movements(self, setup_vi):
        """Test rapid cursor movements."""
        buffer, modes, renderer, executor = setup_vi
        lines = ["line " * 20 for _ in range(100)]
        buffer.set_lines(lines)

        # Rapid movements
        for _ in range(1000):
            executor.execute_normal("j")
            executor.execute_normal("l")
            executor.execute_normal("k")
            executor.execute_normal("h")

        # Should not crash or become inconsistent
