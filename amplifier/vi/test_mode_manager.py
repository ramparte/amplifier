#!/usr/bin/env python3
"""Comprehensive tests for mode management system."""

import json
import sys
from pathlib import Path
from typing import Any

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from amplifier.vi.buffer import TextBuffer
from amplifier.vi.modes.buffer_adapter import BufferAdapter
from amplifier.vi.modes.insert import InsertMode
from amplifier.vi.modes.replace import ReplaceMode
from amplifier.vi.modes.selection import SelectionManager
from amplifier.vi.modes.state import ModeManager
from amplifier.vi.modes.transitions import ModeTransitions
from amplifier.vi.modes.visual import VisualMode


class ModeTestSuite:
    """Test suite for mode management."""

    def __init__(self):
        """Initialize test suite."""
        self.results: dict[str, Any] = {
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "test_results": {},
        }

    def assert_equal(self, actual: Any, expected: Any, test_name: str) -> bool:
        """Assert equality and record result."""
        self.results["tests_run"] += 1
        if actual == expected:
            self.results["tests_passed"] += 1
            self.results["test_results"][test_name] = "PASS"
            return True
        self.results["tests_failed"] += 1
        self.results["failures"].append({"test": test_name, "expected": str(expected), "actual": str(actual)})
        self.results["test_results"][test_name] = f"FAIL: expected {expected}, got {actual}"
        return False

    def test_basic_mode_transitions(self) -> None:
        """Test basic mode transitions."""
        manager = ModeManager()

        # Test initial state
        self.assert_equal(manager.get_mode(), "normal", "initial_mode")

        # Test transition to insert
        self.assert_equal(manager.to_insert(), True, "to_insert_success")
        self.assert_equal(manager.get_mode(), "insert", "insert_mode")

        # Test transition to normal
        self.assert_equal(manager.to_normal(), True, "to_normal_success")
        self.assert_equal(manager.get_mode(), "normal", "back_to_normal")

        # Test transition to visual
        self.assert_equal(manager.to_visual(), True, "to_visual_success")
        self.assert_equal(manager.get_mode(), "visual", "visual_mode")

        # Test visual line mode
        self.assert_equal(manager.to_visual(line_mode=True), True, "to_visual_line_success")
        self.assert_equal(manager.get_mode(), "visual_line", "visual_line_mode")

        # Test visual block mode
        self.assert_equal(manager.to_visual(block_mode=True), True, "to_visual_block_success")
        self.assert_equal(manager.get_mode(), "visual_block", "visual_block_mode")

        # Test command mode
        manager.to_normal()
        self.assert_equal(manager.to_command(), True, "to_command_success")
        self.assert_equal(manager.get_mode(), "command", "command_mode")

        # Test replace mode
        manager.to_normal()
        self.assert_equal(manager.to_replace(), True, "to_replace_success")
        self.assert_equal(manager.get_mode(), "replace", "replace_mode")

        # Test single replace mode
        manager.to_normal()
        self.assert_equal(manager.to_replace(single=True), True, "to_replace_single_success")
        self.assert_equal(manager.get_mode(), "replace_single", "replace_single_mode")

    def test_insert_variations(self) -> None:
        """Test insert mode variations."""
        text_buffer = TextBuffer("Hello World\nSecond Line\nThird Line")
        buffer = BufferAdapter(text_buffer)
        insert = InsertMode(buffer)

        # Test 'i' - insert before cursor
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("i")
        self.assert_equal(insert.get_variation(), "before_cursor", "insert_i_variation")
        self.assert_equal(buffer.get_cursor_position(), (0, 5), "insert_i_position")

        # Test 'I' - insert at line start
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("I")
        self.assert_equal(insert.get_variation(), "line_start", "insert_I_variation")
        self.assert_equal(buffer.get_cursor_position(), (0, 0), "insert_I_position")

        # Test 'a' - insert after cursor
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("a")
        self.assert_equal(insert.get_variation(), "after_cursor", "insert_a_variation")
        self.assert_equal(buffer.get_cursor_position(), (0, 6), "insert_a_position")

        # Test 'A' - insert at line end
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("A")
        self.assert_equal(insert.get_variation(), "line_end", "insert_A_variation")
        self.assert_equal(buffer.get_cursor_position(), (0, 11), "insert_A_position")

        # Test 'o' - open line below
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("o")
        self.assert_equal(insert.get_variation(), "open_below", "insert_o_variation")
        self.assert_equal(buffer.get_cursor_position(), (1, 0), "insert_o_position")
        self.assert_equal(len(buffer.get_lines()), 4, "insert_o_lines_added")

        # Test 'O' - open line above
        buffer.set_lines(["Hello World", "Second Line", "Third Line"])
        buffer.set_cursor_position(1, 5)
        insert.enter_insert("O")
        self.assert_equal(insert.get_variation(), "open_above", "insert_O_variation")
        self.assert_equal(buffer.get_cursor_position(), (1, 0), "insert_O_position")

        # Test 's' - substitute character
        buffer.set_lines(["Hello World", "Second Line", "Third Line"])
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("s")
        self.assert_equal(insert.get_variation(), "substitute_char", "insert_s_variation")
        self.assert_equal(buffer.get_lines()[0], "HelloWorld", "insert_s_char_deleted")

        # Test 'S' - substitute line
        buffer.set_lines(["    Hello World", "Second Line", "Third Line"])
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("S")
        self.assert_equal(insert.get_variation(), "substitute_line", "insert_S_variation")
        self.assert_equal(buffer.get_lines()[0], "    ", "insert_S_line_cleared")

        # Test 'C' - change to end of line
        buffer.set_lines(["Hello World", "Second Line", "Third Line"])
        buffer.set_cursor_position(0, 5)
        insert.enter_insert("C")
        self.assert_equal(insert.get_variation(), "change_to_eol", "insert_C_variation")
        self.assert_equal(buffer.get_lines()[0], "Hello", "insert_C_text_deleted")

    def test_visual_mode_selections(self) -> None:
        """Test visual mode selection operations."""
        text_buffer = TextBuffer("Hello World\nSecond Line\nThird Line")
        buffer = BufferAdapter(text_buffer)
        visual = VisualMode(buffer)

        # Test character visual mode
        buffer.set_cursor_position(0, 0)
        visual.enter_visual("character")
        buffer.set_cursor_position(0, 4)
        visual.update_selection((0, 4))
        selected = visual.get_selected_text()
        self.assert_equal(selected, "Hello", "visual_char_selection")

        # Test line visual mode
        buffer.set_cursor_position(0, 0)
        visual.enter_visual("line")
        buffer.set_cursor_position(1, 0)
        visual.update_selection((1, 0))
        selected = visual.get_selected_text()
        self.assert_equal(selected, "Hello World\nSecond Line", "visual_line_selection")

        # Test block visual mode
        buffer.set_cursor_position(0, 0)
        visual.enter_visual("block")
        visual.start_pos = (0, 0)
        visual.end_pos = (2, 4)
        selected = visual.get_selected_text()
        expected_block = "Hello\nSecon\nThird"
        self.assert_equal(selected, expected_block, "visual_block_selection")

        # Test delete selection
        buffer.set_lines(["Hello World", "Second Line", "Third Line"])
        visual.enter_visual("character")
        visual.start_pos = (0, 0)
        visual.end_pos = (0, 4)
        deleted = visual.delete_selection()
        self.assert_equal(deleted, "Hello", "visual_delete_text")
        self.assert_equal(buffer.get_lines()[0], " World", "visual_delete_result")

        # Test yank selection
        buffer.set_lines(["Hello World", "Second Line", "Third Line"])
        visual.enter_visual("character")
        visual.start_pos = (0, 6)
        visual.end_pos = (0, 10)
        yanked = visual.yank_selection()
        self.assert_equal(yanked, "World", "visual_yank_text")
        self.assert_equal(buffer.get_lines()[0], "Hello World", "visual_yank_unchanged")

    def test_replace_mode(self) -> None:
        """Test replace mode functionality."""
        text_buffer = TextBuffer("Hello World\nSecond Line")
        buffer = BufferAdapter(text_buffer)
        replace = ReplaceMode(buffer)

        # Test single character replace
        buffer.set_cursor_position(0, 0)
        replace.enter_replace(single_char=True)
        self.assert_equal(replace.is_single_char(), True, "replace_single_mode")
        should_exit = replace.handle_character("X")
        self.assert_equal(should_exit, True, "replace_single_exits")
        self.assert_equal(buffer.get_lines()[0], "Xello World", "replace_single_result")

        # Test multi-character replace mode
        buffer.set_lines(["Hello World", "Second Line"])
        buffer.set_cursor_position(0, 0)
        replace.enter_replace(single_char=False)
        self.assert_equal(replace.is_single_char(), False, "replace_multi_mode")
        should_exit = replace.handle_character("A")
        self.assert_equal(should_exit, False, "replace_multi_continues")
        self.assert_equal(buffer.get_lines()[0], "Aello World", "replace_multi_first")
        replace.handle_character("B")
        self.assert_equal(buffer.get_lines()[0], "ABllo World", "replace_multi_second")

    def test_mode_transition_validation(self) -> None:
        """Test mode transition validation."""
        manager = ModeManager()

        # Test valid transitions from normal
        manager.set_mode("normal")
        valid_from_normal = ModeTransitions.get_valid_transitions("normal")
        expected_from_normal = {
            "insert",
            "visual",
            "visual_line",
            "visual_block",
            "command",
            "replace",
            "replace_single",
            "normal",
        }
        self.assert_equal(valid_from_normal, expected_from_normal, "transitions_from_normal")

        # Test valid transitions from insert
        valid_from_insert = ModeTransitions.get_valid_transitions("insert")
        expected_from_insert = {"normal", "replace", "insert"}
        self.assert_equal(valid_from_insert, expected_from_insert, "transitions_from_insert")

        # Test valid transitions from visual
        valid_from_visual = ModeTransitions.get_valid_transitions("visual")
        expected_from_visual = {"normal", "visual_line", "visual_block", "insert", "replace", "command", "visual"}
        self.assert_equal(valid_from_visual, expected_from_visual, "transitions_from_visual")

        # Test invalid transition
        manager.set_mode("command")
        can_transition = ModeTransitions.can_transition("command", "visual")
        self.assert_equal(can_transition, False, "invalid_transition_command_to_visual")

    def test_mode_history(self) -> None:
        """Test mode history tracking."""
        manager = ModeManager()

        # Perform several mode changes
        manager.to_insert()
        manager.to_normal()
        manager.to_visual()
        manager.to_normal()
        manager.to_command()
        manager.to_normal()

        history = manager.get_mode_history()
        # Initial normal + 6 transitions
        self.assert_equal(len(history), 7, "history_length")
        self.assert_equal(history[-1], "normal", "history_last")
        self.assert_equal(history[-2], "command", "history_previous")

    def test_operator_pending(self) -> None:
        """Test operator-pending state."""
        manager = ModeManager()

        # Test setting pending operator
        manager.set_pending_operator("d")
        self.assert_equal(manager.has_pending_operator(), True, "has_pending_operator")
        self.assert_equal(manager.get_pending_operator(), "d", "get_pending_operator")

        # Test mode indicator with pending operator
        indicator = manager.get_mode_indicator()
        self.assert_equal("OPERATOR PENDING" in indicator, True, "operator_pending_indicator")

        # Test clearing pending operator
        manager.clear_pending_operator()
        self.assert_equal(manager.has_pending_operator(), False, "operator_cleared")

    def test_selection_manager(self) -> None:
        """Test selection manager functionality."""
        text_buffer = TextBuffer("First Line\nSecond Line\nThird Line")
        buffer = BufferAdapter(text_buffer)
        selection = SelectionManager(buffer)

        # Test character selection
        buffer.set_cursor_position(0, 0)
        selection.start_selection("character")
        buffer.set_cursor_position(0, 4)
        selection.update_selection()
        bounds = selection.get_selection_bounds()
        self.assert_equal(bounds, ((0, 0), (0, 4)), "selection_character_bounds")

        # Test line selection
        selection.start_selection("line")
        buffer.set_cursor_position(2, 0)
        selection.update_selection()
        selected_lines = selection.get_selected_lines()
        self.assert_equal(selected_lines, [0, 1, 2], "selection_lines")

        # Test position checking
        selection.start_selection("character")
        selection.anchor = (0, 2)
        selection.cursor = (0, 7)
        is_selected = selection.is_position_selected(0, 5)
        self.assert_equal(is_selected, True, "position_is_selected")
        not_selected = selection.is_position_selected(1, 5)
        self.assert_equal(not_selected, False, "position_not_selected")

    def test_mode_callbacks(self) -> None:
        """Test mode change callbacks."""
        manager = ModeManager()
        callback_triggered = {"value": False}

        def test_callback():
            callback_triggered["value"] = True

        # Register callback for insert mode
        manager.register_mode_change_callback("insert", test_callback)

        # Trigger callback
        manager.to_insert()
        self.assert_equal(callback_triggered["value"], True, "mode_callback_triggered")

        # Test transition callback
        transition_triggered = {"value": False}

        def transition_callback():
            transition_triggered["value"] = True

        manager.register_transition_callback("insert", "normal", transition_callback)
        manager.to_normal()
        self.assert_equal(transition_triggered["value"], True, "transition_callback_triggered")

    def run_all_tests(self) -> dict[str, Any]:
        """Run all tests and return results."""
        print("Running Mode Management Tests...")

        self.test_basic_mode_transitions()
        self.test_insert_variations()
        self.test_visual_mode_selections()
        self.test_replace_mode()
        self.test_mode_transition_validation()
        self.test_mode_history()
        self.test_operator_pending()
        self.test_selection_manager()
        self.test_mode_callbacks()

        # Calculate summary
        self.results["summary"] = {
            "total_tests": self.results["tests_run"],
            "passed": self.results["tests_passed"],
            "failed": self.results["tests_failed"],
            "success_rate": f"{(self.results['tests_passed'] / self.results['tests_run'] * 100):.1f}%"
            if self.results["tests_run"] > 0
            else "0%",
        }

        return self.results


def main():
    """Run tests and save results."""
    suite = ModeTestSuite()
    results = suite.run_all_tests()

    # Save results to JSON
    output_path = Path("/tmp/vi_mode_test_results.json")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    # Print summary
    print(f"\n{'=' * 50}")
    print("TEST RESULTS SUMMARY")
    print(f"{'=' * 50}")
    print(f"Total Tests: {results['summary']['total_tests']}")
    print(f"Passed: {results['summary']['passed']}")
    print(f"Failed: {results['summary']['failed']}")
    print(f"Success Rate: {results['summary']['success_rate']}")

    if results["failures"]:
        print(f"\n{'=' * 50}")
        print("FAILURES:")
        for failure in results["failures"]:
            print(f"  - {failure['test']}: expected {failure['expected']}, got {failure['actual']}")

    print(f"\nResults saved to: {output_path}")
    return 0 if results["tests_failed"] == 0 else 1


if __name__ == "__main__":
    exit(main())
