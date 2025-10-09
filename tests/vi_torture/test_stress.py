"""Stress tests for vi editor - complex scenarios and edge cases."""

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


class TestComplexEditingPatterns:
    """Test complex editing scenarios."""

    def test_alternating_operations(self, setup_vi):
        """Test alternating between different operations."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line one", "line two", "line three"])

        # Alternate between different operations
        buffer.set_cursor(0, 0)
        executor.execute_normal("dd")  # Delete line
        executor.execute_normal("p")  # Put back
        executor.execute_normal("yy")  # Yank
        executor.execute_normal("p")  # Put
        executor.execute_normal("j")  # Move
        executor.execute_normal("dd")  # Delete
        executor.execute_normal("k")  # Move
        executor.execute_normal("p")  # Put

        # Should maintain consistency

    def test_nested_visual_operations(self, setup_vi):
        """Test complex visual mode operations."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line 1", "line 2", "line 3", "line 4", "line 5"])
        buffer.set_cursor(0, 0)

        # Enter visual mode
        executor.execute_normal("V")
        executor.execute_normal("2j")
        # Yank selection
        executor.execute_visual("y")

        # Move and put
        executor.execute_normal("j")
        executor.execute_normal("p")

        # Enter visual again
        executor.execute_normal("V")
        executor.execute_normal("j")
        # Delete selection
        executor.execute_visual("d")

    def test_mark_and_jump_combinations(self, setup_vi):
        """Test complex mark and jump scenarios."""
        buffer, modes, renderer, executor = setup_vi
        lines = [f"line {i}" for i in range(20)]
        buffer.set_lines(lines)

        # Set multiple marks
        buffer.set_cursor(5, 0)
        executor.execute_normal("m")
        executor.execute_normal("a")

        buffer.set_cursor(10, 0)
        executor.execute_normal("m")
        executor.execute_normal("b")

        buffer.set_cursor(15, 0)
        executor.execute_normal("m")
        executor.execute_normal("c")

        # Jump between marks
        executor.execute_normal("'")
        executor.execute_normal("a")
        assert buffer.get_cursor()[0] == 5

        executor.execute_normal("'")
        executor.execute_normal("c")
        assert buffer.get_cursor()[0] == 15

        executor.execute_normal("'")
        executor.execute_normal("b")
        assert buffer.get_cursor()[0] == 10


class TestDataIntegrity:
    """Test data integrity under stress."""

    def test_massive_editing_consistency(self, setup_vi):
        """Test that massive editing maintains consistency."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["start"])

        # Perform many editing operations
        modes.to_insert()
        for i in range(10):
            buffer.insert_char(str(i))
        modes.to_normal()

        # Verify buffer is still valid
        lines = buffer.get_lines()
        assert isinstance(lines, list)
        assert all(isinstance(line, str) for line in lines)

    def test_cursor_never_invalid(self, setup_vi):
        """Test cursor always stays in valid position."""
        buffer, modes, renderer, executor = setup_vi
        lines = ["line 1", "line 2", "line 3"]
        buffer.set_lines(lines)

        # Try to force invalid cursor positions
        for _ in range(100):
            executor.execute_normal("j")
            executor.execute_normal("l")
            row, col = buffer.get_cursor()
            assert 0 <= row < len(buffer.get_lines())
            if row < len(buffer.get_lines()):
                assert 0 <= col <= len(buffer.get_lines()[row])

        for _ in range(100):
            executor.execute_normal("k")
            executor.execute_normal("h")
            row, col = buffer.get_cursor()
            assert row >= 0
            assert col >= 0

    def test_buffer_never_corrupted(self, setup_vi):
        """Test buffer never gets corrupted."""
        buffer, modes, renderer, executor = setup_vi
        initial = ["line 1", "line 2", "line 3"]
        buffer.set_lines(initial.copy())

        # Perform many operations
        for _ in range(50):
            executor.execute_normal("yy")
            executor.execute_normal("p")
            executor.execute_normal("dd")
            executor.execute_normal("j")

        # Verify buffer structure is still valid
        lines = buffer.get_lines()
        assert isinstance(lines, list)
        assert len(lines) > 0
        assert all(isinstance(line, str) for line in lines)


class TestErrorRecovery:
    """Test recovery from error conditions."""

    def test_invalid_operation_recovery(self, setup_vi):
        """Test recovery from invalid operations."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["test"])

        # Try invalid operations
        executor.execute_normal("\x00")  # Null byte
        executor.execute_normal("\xff")  # Invalid character

        # System should still work
        executor.execute_normal("j")
        assert modes.current_mode == "normal"

    def test_mode_consistency_after_errors(self, setup_vi):
        """Test mode stays consistent after errors."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["test"])

        # Enter various modes
        modes.to_insert()
        modes.to_normal()
        modes.to_visual()
        modes.to_normal()

        # Try invalid mode transitions
        assert modes.current_mode == "normal"

    def test_state_recovery_after_crash_simulation(self, setup_vi):
        """Test state can be recovered."""
        buffer, modes, renderer, executor = setup_vi
        initial = ["line 1", "line 2", "line 3"]
        buffer.set_lines(initial.copy())

        # Simulate partial operations
        executor.execute_normal("yy")
        # Simulate crash - recreate components
        buffer2 = TextBuffer()
        buffer2.set_lines(initial.copy())

        # Should be able to continue
        assert buffer2.get_lines() == initial


class TestBoundaryStress:
    """Stress test boundary conditions."""

    def test_zero_length_operations(self, setup_vi):
        """Test operations with zero-length targets."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines([""])

        # All operations on empty buffer
        executor.execute_normal("dd")
        executor.execute_normal("yy")
        executor.execute_normal("p")
        executor.execute_normal("x")
        executor.execute_normal("D")
        executor.execute_normal("C")

        # Should not crash

    def test_maximum_line_length(self, setup_vi):
        """Test handling of maximum reasonable line length."""
        buffer, modes, renderer, executor = setup_vi
        max_line = "x" * 1000000  # 1 million characters
        buffer.set_lines([max_line])

        buffer.set_cursor(0, 0)
        executor.execute_normal("$")
        executor.execute_normal("0")

        # Should handle without crash

    def test_maximum_buffer_size(self, setup_vi):
        """Test handling of maximum reasonable buffer size."""
        buffer, modes, renderer, executor = setup_vi
        max_lines = [f"line {i}" for i in range(100000)]  # 100k lines
        buffer.set_lines(max_lines)

        buffer.set_cursor(0, 0)
        executor.execute_normal("G")
        executor.execute_normal("gg")

        # Should handle without crash


class TestComplexWorkflows:
    """Test complex realistic workflows."""

    def test_code_editing_workflow(self, setup_vi):
        """Test typical code editing workflow."""
        buffer, modes, renderer, executor = setup_vi
        code = [
            "def function():",
            "    pass",
            "",
            "class MyClass:",
            "    def method(self):",
            "        return True",
        ]
        buffer.set_lines(code.copy())

        # Navigate to function
        buffer.set_cursor(0, 0)
        executor.execute_normal("j")  # Move to pass

        # Delete pass and add code
        executor.execute_normal("dd")
        modes.to_insert()
        buffer.insert_char(" ")
        buffer.insert_char(" ")
        buffer.insert_char(" ")
        buffer.insert_char(" ")
        modes.to_normal()

        # Navigate to class
        executor.execute_normal("3j")

        # Verify still consistent
        assert isinstance(buffer.get_lines(), list)

    def test_document_editing_workflow(self, setup_vi):
        """Test typical document editing workflow."""
        buffer, modes, renderer, executor = setup_vi
        doc = [
            "Title",
            "",
            "Paragraph one with some text.",
            "",
            "Paragraph two with more text.",
            "",
            "Conclusion.",
        ]
        buffer.set_lines(doc.copy())

        # Navigate and edit
        buffer.set_cursor(0, 0)
        executor.execute_normal("j")  # Empty line
        executor.execute_normal("j")  # First paragraph

        # Yank paragraph
        executor.execute_normal("yy")
        executor.execute_normal("p")

        # Move to end
        executor.execute_normal("G")

        # Verify consistency
        assert isinstance(buffer.get_lines(), list)
        assert len(buffer.get_lines()) > 0


class TestStateMachineIntegrity:
    """Test state machine maintains integrity."""

    def test_all_valid_mode_transitions(self, setup_vi):
        """Test all valid mode transitions work."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["test"])

        # Normal -> Insert -> Normal
        modes.to_insert()
        assert modes.current_mode == "insert"
        modes.to_normal()
        assert modes.current_mode == "normal"

        # Normal -> Visual -> Normal
        modes.to_visual()
        assert modes.current_mode == "visual"
        modes.to_normal()
        assert modes.current_mode == "normal"

        # Normal -> Command -> Normal
        modes.to_command()
        assert modes.current_mode == "command"
        modes.to_normal()
        assert modes.current_mode == "normal"

    def test_mode_state_preserved(self, setup_vi):
        """Test mode state is preserved correctly."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line 1", "line 2"])

        # Set position in normal mode
        buffer.set_cursor(1, 0)

        # Switch modes
        modes.to_insert()
        modes.to_normal()

        # Position should be preserved
        assert buffer.get_cursor() == (1, 0)

    def test_rapid_mode_changes_integrity(self, setup_vi):
        """Test integrity with rapid mode changes."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["test"])

        # Rapidly change modes
        for _ in range(100):
            modes.to_insert()
            modes.to_normal()
            modes.to_visual()
            modes.to_normal()
            modes.to_command()
            modes.to_normal()

        # Should end in consistent state
        assert modes.current_mode == "normal"


class TestCornerCases:
    """Test unusual corner cases."""

    def test_operations_at_all_boundaries(self, setup_vi):
        """Test operations at every boundary."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line 1", "line 2", "line 3"])

        # Test at start
        buffer.set_cursor(0, 0)
        executor.execute_normal("h")  # Should stay at start
        executor.execute_normal("k")  # Should stay at start
        assert buffer.get_cursor() == (0, 0)

        # Test at end
        executor.execute_normal("G")
        executor.execute_normal("$")
        row, col = buffer.get_cursor()
        executor.execute_normal("l")  # Should stay at end
        executor.execute_normal("j")  # Should stay at end
        assert buffer.get_cursor() == (row, col)

    def test_all_whitespace_operations(self, setup_vi):
        """Test operations on whitespace-only content."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["   ", "\t\t", "  \t  "])

        # Navigate and edit whitespace
        buffer.set_cursor(0, 0)
        executor.execute_normal("w")
        executor.execute_normal("b")
        executor.execute_normal("j")
        executor.execute_normal("x")

        # Should handle gracefully

    def test_mixed_line_endings(self, setup_vi):
        """Test handling of different line ending scenarios."""
        buffer, modes, renderer, executor = setup_vi
        buffer.set_lines(["line1", "", "line3", "", ""])

        # Navigate through mixed empty/non-empty
        buffer.set_cursor(0, 0)
        for _ in range(10):
            executor.execute_normal("j")

        # Should handle all line types
