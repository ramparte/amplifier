"""Mode transition validation and management for vi editor."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import ModeManager


class ModeTransitions:
    """Manages and validates mode transitions."""

    # Valid transition matrix
    TRANSITION_MATRIX = {
        "normal": {
            "insert": True,
            "visual": True,
            "visual_line": True,
            "visual_block": True,
            "command": True,
            "replace": True,
            "replace_single": True,
            "normal": True,
        },
        "insert": {
            "normal": True,
            "replace": True,
            "insert": True,
        },
        "visual": {
            "normal": True,
            "visual_line": True,
            "visual_block": True,
            "insert": True,
            "replace": True,
            "command": True,
            "visual": True,
        },
        "visual_line": {
            "normal": True,
            "visual": True,
            "visual_block": True,
            "insert": True,
            "replace": True,
            "command": True,
            "visual_line": True,
        },
        "visual_block": {
            "normal": True,
            "visual": True,
            "visual_line": True,
            "insert": True,
            "replace": True,
            "command": True,
            "visual_block": True,
        },
        "command": {
            "normal": True,
            "command": True,
        },
        "replace": {
            "normal": True,
            "insert": True,
            "replace": True,
        },
        "replace_single": {
            "normal": True,
            "replace_single": True,
        },
    }

    @classmethod
    def can_transition(cls, from_mode: str, to_mode: str) -> bool:
        """Check if a transition between modes is allowed.

        Args:
            from_mode: Current mode
            to_mode: Target mode

        Returns:
            True if transition is allowed
        """
        if from_mode not in cls.TRANSITION_MATRIX:
            return False

        return cls.TRANSITION_MATRIX[from_mode].get(to_mode, False)

    @classmethod
    def get_valid_transitions(cls, from_mode: str) -> set[str]:
        """Get all valid transitions from a given mode.

        Args:
            from_mode: The current mode

        Returns:
            Set of modes that can be transitioned to
        """
        if from_mode not in cls.TRANSITION_MATRIX:
            return set()

        return {mode for mode, allowed in cls.TRANSITION_MATRIX[from_mode].items() if allowed}

    @classmethod
    def validate_transition_key(cls, mode_manager: "ModeManager", key: str) -> str | None:
        """Validate and return target mode for a key press.

        Args:
            mode_manager: The mode manager instance
            key: The key pressed

        Returns:
            Target mode name or None if no transition
        """
        current_mode = mode_manager.get_mode()

        # ESC always returns to normal from any mode
        if key == "\x1b":
            return "normal" if current_mode != "normal" else None

        # Command mode entry
        if key == ":" and current_mode == "normal":
            return "command"

        # Visual mode variations
        if current_mode == "normal":
            if key == "v":
                return "visual"
            if key == "V":
                return "visual_line"
            if key == "\x16":  # Ctrl-V
                return "visual_block"

        # Insert mode variations
        if current_mode in ["normal", "visual", "visual_line", "visual_block"] and key in [
            "i",
            "I",
            "a",
            "A",
            "o",
            "O",
            "s",
            "S",
            "c",
            "C",
        ]:
            # Set the insert variation
            variations = {
                "i": "before_cursor",
                "I": "line_start",
                "a": "after_cursor",
                "A": "line_end",
                "o": "open_below",
                "O": "open_above",
                "s": "substitute_char",
                "S": "substitute_line",
                "c": "change",
                "C": "change_to_eol",
            }
            mode_manager.set_insert_variation(variations.get(key, "before_cursor"))
            return "insert"

        # Replace mode
        if current_mode == "normal":
            if key == "R":
                return "replace"
            if key == "r":
                return "replace_single"

        # Visual mode switching
        if current_mode in ["visual", "visual_line", "visual_block"]:
            if key == "v" and current_mode != "visual":
                return "visual"
            if key == "V" and current_mode != "visual_line":
                return "visual_line"
            if key == "\x16" and current_mode != "visual_block":
                return "visual_block"

        return None

    @classmethod
    def get_transition_description(cls, from_mode: str, to_mode: str) -> str:
        """Get a human-readable description of a mode transition.

        Args:
            from_mode: Starting mode
            to_mode: Target mode

        Returns:
            Description of the transition
        """
        descriptions = {
            ("normal", "insert"): "Entering insert mode",
            ("normal", "visual"): "Entering character-wise visual mode",
            ("normal", "visual_line"): "Entering line-wise visual mode",
            ("normal", "visual_block"): "Entering block-wise visual mode",
            ("normal", "command"): "Entering command mode",
            ("normal", "replace"): "Entering replace mode",
            ("normal", "replace_single"): "Replace single character",
            ("insert", "normal"): "Returning to normal mode",
            ("visual", "normal"): "Exiting visual mode",
            ("visual_line", "normal"): "Exiting visual line mode",
            ("visual_block", "normal"): "Exiting visual block mode",
            ("command", "normal"): "Command executed or cancelled",
            ("replace", "normal"): "Exiting replace mode",
            ("replace_single", "normal"): "Character replaced",
            ("visual", "insert"): "Changing selected text",
            ("visual_line", "insert"): "Changing selected lines",
            ("visual_block", "insert"): "Changing selected block",
        }

        return descriptions.get((from_mode, to_mode), f"Transitioning from {from_mode} to {to_mode}")

    @classmethod
    def handle_operator_pending(cls, mode_manager: "ModeManager", operator: str) -> None:
        """Handle operator-pending state.

        Args:
            mode_manager: The mode manager
            operator: The operator (d, c, y, etc.)
        """
        if mode_manager.get_mode() == "normal":
            mode_manager.set_pending_operator(operator)

    @classmethod
    def complete_operator(cls, mode_manager: "ModeManager") -> str | None:
        """Complete an operator-pending operation.

        Args:
            mode_manager: The mode manager

        Returns:
            The operator that was pending, or None
        """
        operator = mode_manager.get_pending_operator()
        mode_manager.clear_pending_operator()
        return operator
