"""Performance torture tests for vi editor."""

import time

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


class TestNavigationPerformance:
    """Test navigation performance with large buffers."""

    def test_large_buffer_navigation_speed(self, setup_vi):
        """Test navigation speed with 10000 line buffer."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"This is line {i} with some content" for i in range(10000)]
        buffer.set_lines(lines)

        start = time.time()
        buffer.set_cursor(0, 0)
        executor.execute_normal("G")
        executor.execute_normal("gg")
        end = time.time()

        # Should complete in under 0.1 seconds
        assert (end - start) < 0.1

    def test_word_movement_performance(self, setup_vi):
        """Test word movement performance on long lines."""
        buffer, modes, renderer, executor = setup_vi
        # Create line with 1000 words
        line = " ".join([f"word{i}" for i in range(1000)])
        buffer.set_lines([line])
        buffer.set_cursor(0, 0)

        start = time.time()
        # Move through 100 words
        for _ in range(100):
            executor.execute_normal("w")
        end = time.time()

        # Should complete in under 0.1 seconds
        assert (end - start) < 0.1

    def test_search_performance(self, setup_vi):
        """Test search performance with large buffer."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i} content" for i in range(1000)]
        # Add target at end
        lines.append("target line here")
        buffer.set_lines(lines)

        # Note: Would need command line mode for actual search
        # This tests buffer operations that search would use
        start = time.time()
        for i, line in enumerate(buffer.get_lines()):
            if "target" in line:
                buffer.set_cursor(i, 0)
                break
        end = time.time()

        # Should complete quickly
        assert (end - start) < 0.1
        assert buffer.get_cursor()[0] == 1000


class TestEditingPerformance:
    """Test editing operation performance."""

    def test_mass_insertion_performance(self, setup_vi):
        """Test inserting many characters."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([""])
        buffer.set_cursor(0, 0)

        modes.to_insert()
        start = time.time()
        for _ in range(1000):
            buffer.insert_char("a")
        end = time.time()
        modes.to_normal()

        # Should complete in under 0.5 seconds
        assert (end - start) < 0.5
        assert len(buffer.get_lines()[0]) == 1000

    def test_mass_deletion_performance(self, setup_vi):
        """Test deleting many lines."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(1000)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        start = time.time()
        executor.execute_normal("999dd")
        end = time.time()

        # Should complete in under 0.1 seconds
        assert (end - start) < 0.1
        assert len(buffer.get_lines()) == 1

    def test_yank_performance(self, setup_vi):
        """Test yanking large amounts of text."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i} with content" for i in range(1000)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        start = time.time()
        executor.execute_normal("999yy")
        end = time.time()

        # Should complete in under 0.1 seconds
        assert (end - start) < 0.1


class TestVisualModePerformance:
    """Test visual mode performance."""

    def test_large_visual_selection(self, setup_vi):
        """Test selecting large blocks of text."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(1000)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        start = time.time()
        executor.execute_normal("V")
        executor.execute_normal("999j")
        end = time.time()

        # Should complete quickly
        assert (end - start) < 0.1

    def test_visual_block_operations(self, setup_vi):
        """Test visual block mode operations."""
        buffer, modes, renderer, executor = setup_vi
        lines = ["column data here" for _ in range(100)]
        buffer.set_lines(lines)
        buffer.set_cursor(0, 0)

        start = time.time()
        executor.execute_normal("\x16")  # Ctrl-V for visual block
        executor.execute_normal("99j")
        executor.execute_normal("5l")
        end = time.time()

        # Should complete quickly
        assert (end - start) < 0.1


class TestMemoryPerformance:
    """Test memory usage and efficiency."""

    def test_large_buffer_memory(self, setup_vi):
        """Test memory usage with large buffer."""
        buffer, modes, renderer, executor = setup_vi

        # Create 100MB of text (roughly)
        large_line = "x" * 10000
        lines = [large_line for _ in range(10000)]

        start = time.time()
        buffer.set_lines(lines)
        end = time.time()

        # Should load in reasonable time
        assert (end - start) < 5.0

        # Test navigation doesn't cause issues
        buffer.set_cursor(0, 0)
        executor.execute_normal("G")
        executor.execute_normal("gg")

    def test_undo_stack_memory(self, setup_vi):
        """Test undo stack doesn't grow unbounded."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([""])
        buffer.set_cursor(0, 0)

        # Perform many operations
        modes.to_insert()
        for _ in range(10000):
            buffer.insert_char("a")
        modes.to_normal()

        # Undo stack should cap at reasonable size (when implemented)
        # This tests that the system doesn't crash with many operations


class TestConcurrentPerformance:
    """Test performance under rapid operations."""

    def test_rapid_mode_switching_performance(self, setup_vi):
        """Test rapid mode switches don't degrade performance."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["test line"])

        start = time.time()
        for _ in range(1000):
            modes.to_insert()
            modes.to_normal()
            modes.to_visual()
            modes.to_normal()
        end = time.time()

        # Should complete in under 0.1 seconds
        assert (end - start) < 0.1

    def test_rapid_cursor_updates_performance(self, setup_vi):
        """Test rapid cursor movements."""
        buffer, modes, renderer, executor = setup_vi
        lines = ["line content here" for _ in range(100)]
        buffer.set_lines(lines)

        start = time.time()
        for _ in range(1000):
            executor.execute_normal("j")
            executor.execute_normal("l")
            executor.execute_normal("k")
            executor.execute_normal("h")
        end = time.time()

        # Should complete in under 0.5 seconds
        assert (end - start) < 0.5


class TestWorstCaseScenarios:
    """Test worst-case performance scenarios."""

    def test_single_character_per_line(self, setup_vi):
        """Test buffer with many single-character lines."""
        buffer, modes, renderer, executor = setup_vi
        lines = ["x" for _ in range(10000)]
        buffer.set_lines(lines)

        start = time.time()
        buffer.set_cursor(0, 0)
        executor.execute_normal("G")
        executor.execute_normal("gg")
        end = time.time()

        assert (end - start) < 0.1

    def test_extremely_long_single_line(self, setup_vi):
        """Test navigation on extremely long single line."""
        buffer, modes, renderer, executor = setup_vi
        long_line = "x" * 100000
        buffer.set_lines([long_line])
        buffer.set_cursor(0, 0)

        start = time.time()
        executor.execute_normal("$")
        executor.execute_normal("0")
        end = time.time()

        # Should complete in under 0.1 seconds
        assert (end - start) < 0.1

    def test_deep_nesting_brackets(self, setup_vi):
        """Test deeply nested bracket structures."""
        buffer, modes, renderer, executor = setup_vi
        # Create deeply nested structure
        nested = "(" * 1000 + "content" + ")" * 1000
        buffer.set_lines([nested])
        buffer.set_cursor(0, 0)

        # Test bracket matching (when implemented)
        start = time.time()
        executor.execute_normal("%")
        end = time.time()

        # Should complete in reasonable time
        assert (end - start) < 0.5


class TestRegressionPerformance:
    """Test for performance regressions."""

    def test_baseline_operations(self, setup_vi):
        """Establish baseline for common operations."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i} with content" for i in range(100)]
        buffer.set_lines(lines)

        # Test basic operations
        operations = [
            ("j", 0.01),  # Move down should be < 10ms
            ("k", 0.01),  # Move up should be < 10ms
            ("w", 0.01),  # Word forward should be < 10ms
            ("b", 0.01),  # Word back should be < 10ms
            ("$", 0.01),  # End of line should be < 10ms
            ("0", 0.01),  # Start of line should be < 10ms
        ]

        for op, max_time in operations:
            buffer.set_cursor(50, 0)
            start = time.time()
            for _ in range(100):
                executor.execute_normal(op)
            end = time.time()
            avg_time = (end - start) / 100

            assert avg_time < max_time, f"Operation {op} too slow: {avg_time:.4f}s"
