"""Mode management for vi editor with robust state transitions."""

from collections.abc import Callable


class ModeManager:
    """Manages vi editor modes with validated state transitions."""

    # Mode constants
    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    COMMAND = "command"
    VISUAL_LINE = "visual_line"
    VISUAL_BLOCK = "visual_block"
    REPLACE = "replace"
    REPLACE_SINGLE = "replace_single"  # For 'r' command

    # Valid modes set
    VALID_MODES = {
        NORMAL,
        INSERT,
        VISUAL,
        COMMAND,
        VISUAL_LINE,
        VISUAL_BLOCK,
        REPLACE,
        REPLACE_SINGLE,
    }

    # Insert mode variations tracking
    INSERT_VARIATIONS = {
        "i": "before_cursor",  # Insert before cursor
        "I": "line_start",  # Insert at line start
        "a": "after_cursor",  # Insert after cursor
        "A": "line_end",  # Insert at line end
        "o": "open_below",  # Open line below
        "O": "open_above",  # Open line above
        "s": "substitute_char",  # Substitute character
        "S": "substitute_line",  # Substitute line
        "c": "change",  # Change (requires motion)
        "C": "change_to_eol",  # Change to end of line
    }

    # Mode transition keys mapping
    TRANSITION_KEYS = {
        ":": COMMAND,  # Colon enters command mode
        "i": INSERT,  # i enters insert mode
        "a": INSERT,  # a enters insert mode (after cursor)
        "I": INSERT,  # I enters insert mode (start of line)
        "A": INSERT,  # A enters insert mode (end of line)
        "o": INSERT,  # o opens line below and enters insert
        "O": INSERT,  # O opens line above and enters insert
        "s": INSERT,  # s substitutes character and enters insert
        "S": INSERT,  # S substitutes line and enters insert
        "c": INSERT,  # c changes text (with motion) and enters insert
        "C": INSERT,  # C changes to end of line and enters insert
        "v": VISUAL,  # v enters visual mode
        "V": VISUAL_LINE,  # V enters visual line mode
        "\x16": VISUAL_BLOCK,  # Ctrl-V enters visual block mode
        "R": REPLACE,  # R enters replace mode
        "r": REPLACE_SINGLE,  # r replaces single character
        "\x1b": NORMAL,  # ESC returns to normal mode
    }

    def __init__(self):
        """Initialize mode manager in normal mode."""
        self._mode = self.NORMAL
        self._previous_mode = self.NORMAL
        self._mode_callbacks: dict[str, list[Callable]] = {}
        self._transition_callbacks: dict[tuple[str, str], list[Callable]] = {}
        self._locked = False  # For preventing invalid transitions
        self._mode_history: list[str] = [self.NORMAL]  # Mode history for undo/redo
        self._insert_variation: str | None = None  # Current insert mode variation
        self._pending_operator: str | None = None  # For operator-pending states
        self._selection_start: tuple[int, int] | None = None  # Visual mode selection start
        self._selection_end: tuple[int, int] | None = None  # Visual mode selection end

    def get_mode(self) -> str:
        """Get the current mode.

        Returns:
            The current mode string
        """
        return self._mode

    @property
    def current_mode(self) -> str:
        """Property alias for get_mode() for test compatibility."""
        return self._mode

    def set_mode(self, mode: str) -> bool:
        """Set the current mode. Alias for switch_to().

        Args:
            mode: The mode to switch to

        Returns:
            True if mode changed successfully, False otherwise
        """
        return self.switch_to(mode)

    def switch_to(self, mode: str) -> bool:
        """Switch to a different mode with validation.

        Args:
            mode: The mode to switch to

        Returns:
            True if mode changed successfully, False otherwise
        """
        # Validate the mode
        if not self._validate_mode(mode):
            return False

        # Check if transition is allowed
        if not self._can_transition(self._mode, mode):
            return False

        # Already in requested mode
        if mode == self._mode:
            return True

        # Perform the transition
        old_mode = self._mode
        self._previous_mode = old_mode
        self._mode = mode

        # Add to history
        self.push_mode_history(mode)

        # Clear insert variation when leaving insert mode
        if old_mode == self.INSERT and mode != self.INSERT:
            self._insert_variation = None

        # Clear selection when leaving visual mode
        if old_mode in {self.VISUAL, self.VISUAL_LINE, self.VISUAL_BLOCK} and not self.is_visual():
            self.clear_selection()

        # Clear pending operator when switching modes
        if mode != self.NORMAL:
            self.clear_pending_operator()

        # Trigger mode change callbacks
        self._trigger_mode_callbacks(mode)

        # Trigger transition callbacks
        self._trigger_transition_callbacks(old_mode, mode)

        return True

    def _validate_mode(self, mode: str) -> bool:
        """Validate that a mode is valid.

        Args:
            mode: The mode to validate

        Returns:
            True if valid, False otherwise
        """
        return mode in self.VALID_MODES

    def _can_transition(self, from_mode: str, to_mode: str) -> bool:
        """Check if a transition between modes is allowed.

        Args:
            from_mode: Current mode
            to_mode: Target mode

        Returns:
            True if transition is allowed, False otherwise
        """
        # If locked, no transitions allowed
        if self._locked:
            return False

        # Allow transition to same mode (no-op)
        if from_mode == to_mode:
            return True

        # Always allow transition to normal mode (via ESC)
        if to_mode == self.NORMAL:
            return True

        # From normal mode, can go anywhere
        if from_mode == self.NORMAL:
            return True

        # From insert mode, can only go to normal or replace
        if from_mode == self.INSERT:
            return to_mode in {self.NORMAL, self.REPLACE}

        # From command mode, can only go to normal
        if from_mode == self.COMMAND:
            return to_mode == self.NORMAL

        # From visual modes, can go to normal, other visual modes, or insert/replace
        if from_mode in {self.VISUAL, self.VISUAL_LINE, self.VISUAL_BLOCK}:
            return to_mode in {self.NORMAL, self.VISUAL, self.VISUAL_LINE, self.VISUAL_BLOCK, self.INSERT, self.REPLACE}

        # From replace mode, can go to normal or insert
        if from_mode == self.REPLACE:
            return to_mode in {self.NORMAL, self.INSERT}

        # From replace single, must return to normal
        if from_mode == self.REPLACE_SINGLE:
            return to_mode == self.NORMAL

        # Default: allow the transition
        return True

    def get_transition_key(self, key: str) -> str | None:
        """Get the mode that a key press would transition to.

        Args:
            key: The key pressed

        Returns:
            The mode to transition to, or None if no transition
        """
        # Handle special case for command mode
        if key == ":" and self._mode == self.NORMAL:
            return self.COMMAND

        # Handle ESC from any mode
        if key == "\x1b" and self._mode != self.NORMAL:
            return self.NORMAL

        # Only process other transitions from normal mode
        if self._mode != self.NORMAL:
            return None

        return self.TRANSITION_KEYS.get(key)

    def is_normal(self) -> bool:
        """Check if in normal mode."""
        return self._mode == self.NORMAL

    def is_insert(self) -> bool:
        """Check if in insert mode."""
        return self._mode == self.INSERT

    def is_visual(self) -> bool:
        """Check if in any visual mode."""
        return self._mode in {self.VISUAL, self.VISUAL_LINE, self.VISUAL_BLOCK}

    def is_replace(self) -> bool:
        """Check if in replace mode."""
        return self._mode in {self.REPLACE, self.REPLACE_SINGLE}

    def is_command(self) -> bool:
        """Check if in command mode."""
        return self._mode == self.COMMAND

    def to_normal(self) -> bool:
        """Switch to normal mode.

        Returns:
            True if switched successfully
        """
        return self.switch_to(self.NORMAL)

    def to_insert(self) -> bool:
        """Switch to insert mode.

        Returns:
            True if switched successfully
        """
        return self.switch_to(self.INSERT)

    def to_visual(self, line_mode: bool = False, block_mode: bool = False) -> bool:
        """Switch to visual mode (character, line, or block).

        Args:
            line_mode: If True, switch to visual line mode
            block_mode: If True, switch to visual block mode

        Returns:
            True if switched successfully
        """
        if block_mode:
            return self.switch_to(self.VISUAL_BLOCK)
        if line_mode:
            return self.switch_to(self.VISUAL_LINE)
        return self.switch_to(self.VISUAL)

    def to_command(self) -> bool:
        """Switch to command mode.

        Returns:
            True if switched successfully
        """
        return self.switch_to(self.COMMAND)

    def to_replace(self, single: bool = False) -> bool:
        """Switch to replace mode.

        Args:
            single: If True, switch to single character replace mode

        Returns:
            True if switched successfully
        """
        if single:
            return self.switch_to(self.REPLACE_SINGLE)
        return self.switch_to(self.REPLACE)

    def escape(self) -> bool:
        """Handle escape key - returns to normal mode.

        Returns:
            True if switched successfully
        """
        return self.to_normal()

    def set_insert_variation(self, variation: str) -> None:
        """Set the current insert mode variation.

        Args:
            variation: The insert variation (e.g., 'before_cursor', 'line_start')
        """
        if variation in self.INSERT_VARIATIONS.values():
            self._insert_variation = variation

    def get_insert_variation(self) -> str | None:
        """Get the current insert mode variation."""
        return self._insert_variation

    def set_pending_operator(self, operator: str | None) -> None:
        """Set a pending operator for operator-pending mode.

        Args:
            operator: The pending operator (e.g., 'd', 'c', 'y')
        """
        self._pending_operator = operator

    def get_pending_operator(self) -> str | None:
        """Get the current pending operator."""
        return self._pending_operator

    def clear_pending_operator(self) -> None:
        """Clear the pending operator."""
        self._pending_operator = None

    def has_pending_operator(self) -> bool:
        """Check if there's a pending operator."""
        return self._pending_operator is not None

    def set_selection(self, start: tuple[int, int] | None, end: tuple[int, int] | None) -> None:
        """Set the visual mode selection range.

        Args:
            start: Selection start position (row, col) or None
            end: Selection end position (row, col) or None
        """
        self._selection_start = start
        self._selection_end = end

    def get_selection(self) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        """Get the visual mode selection range.

        Returns:
            Tuple of (start, end) positions
        """
        return self._selection_start, self._selection_end

    def clear_selection(self) -> None:
        """Clear the visual mode selection."""
        self._selection_start = None
        self._selection_end = None

    def push_mode_history(self, mode: str) -> None:
        """Add a mode to the history stack.

        Args:
            mode: The mode to add to history
        """
        self._mode_history.append(mode)
        # Keep history limited to prevent memory issues
        if len(self._mode_history) > 100:
            self._mode_history = self._mode_history[-50:]

    def get_mode_history(self) -> list[str]:
        """Get the mode history.

        Returns:
            List of modes in chronological order
        """
        return self._mode_history.copy()

    def get_previous_mode(self) -> str:
        """Get the previous mode before the last switch."""
        return self._previous_mode

    def lock(self) -> None:
        """Lock mode transitions (useful during critical operations)."""
        self._locked = True

    def unlock(self) -> None:
        """Unlock mode transitions."""
        self._locked = False

    def is_locked(self) -> bool:
        """Check if mode transitions are locked."""
        return self._locked

    def register_mode_change_callback(self, mode: str, callback: Callable) -> None:
        """Register a callback to be called when entering a specific mode.

        Args:
            mode: The mode to trigger the callback
            callback: The callback function
        """
        if mode not in self.VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}")

        if mode not in self._mode_callbacks:
            self._mode_callbacks[mode] = []
        if callback not in self._mode_callbacks[mode]:
            self._mode_callbacks[mode].append(callback)

    def unregister_mode_change_callback(self, mode: str, callback: Callable) -> None:
        """Unregister a mode change callback.

        Args:
            mode: The mode the callback was registered for
            callback: The callback function to remove
        """
        if mode in self._mode_callbacks and callback in self._mode_callbacks[mode]:
            self._mode_callbacks[mode].remove(callback)

    def register_transition_callback(self, from_mode: str, to_mode: str, callback: Callable) -> None:
        """Register a callback for specific mode transitions.

        Args:
            from_mode: The mode transitioning from
            to_mode: The mode transitioning to
            callback: The callback function
        """
        if from_mode not in self.VALID_MODES or to_mode not in self.VALID_MODES:
            raise ValueError(f"Invalid modes: {from_mode} -> {to_mode}")

        key = (from_mode, to_mode)
        if key not in self._transition_callbacks:
            self._transition_callbacks[key] = []
        if callback not in self._transition_callbacks[key]:
            self._transition_callbacks[key].append(callback)

    def _trigger_mode_callbacks(self, mode: str) -> None:
        """Trigger all callbacks registered for a mode change.

        Args:
            mode: The mode that was entered
        """
        import contextlib

        if mode in self._mode_callbacks:
            for callback in self._mode_callbacks[mode][:]:  # Copy list to avoid modification during iteration
                with contextlib.suppress(Exception):
                    callback()

    def _trigger_transition_callbacks(self, from_mode: str, to_mode: str) -> None:
        """Trigger callbacks for specific mode transitions.

        Args:
            from_mode: The mode transitioned from
            to_mode: The mode transitioned to
        """
        import contextlib

        key = (from_mode, to_mode)
        if key in self._transition_callbacks:
            for callback in self._transition_callbacks[key][:]:  # Copy list
                with contextlib.suppress(Exception):
                    callback()

    def get_mode_indicator(self) -> str:
        """Get a string indicator for the current mode."""
        indicators = {
            self.NORMAL: "-- NORMAL --",
            self.INSERT: "-- INSERT --",
            self.VISUAL: "-- VISUAL --",
            self.VISUAL_LINE: "-- VISUAL LINE --",
            self.VISUAL_BLOCK: "-- VISUAL BLOCK --",
            self.COMMAND: ":",
            self.REPLACE: "-- REPLACE --",
            self.REPLACE_SINGLE: "-- REPLACE CHAR --",
        }

        # Add operator-pending indicator
        if self._pending_operator and self._mode == self.NORMAL:
            return f"-- OPERATOR PENDING ({self._pending_operator}) --"

        # Add insert variation to indicator
        if self._mode == self.INSERT and self._insert_variation:
            variant_map = {
                "before_cursor": "INSERT",
                "after_cursor": "INSERT (after)",
                "line_start": "INSERT (start)",
                "line_end": "INSERT (end)",
                "open_below": "INSERT (new line)",
                "open_above": "INSERT (line above)",
                "substitute_char": "INSERT (substitute)",
                "substitute_line": "INSERT (replace line)",
                "change": "INSERT (change)",
                "change_to_eol": "INSERT (change to end)",
            }
            variant_text = variant_map.get(self._insert_variation, "INSERT")
            return f"-- {variant_text} --"

        return indicators.get(self._mode, "-- UNKNOWN --")

    def get_mode_color(self) -> str:
        """Get ANSI color code for the current mode.

        Returns:
            ANSI color escape sequence for the mode
        """
        colors = {
            self.NORMAL: "\033[37m",  # White
            self.INSERT: "\033[32m",  # Green
            self.VISUAL: "\033[33m",  # Yellow
            self.VISUAL_LINE: "\033[33m",  # Yellow
            self.VISUAL_BLOCK: "\033[33m",  # Yellow
            self.COMMAND: "\033[36m",  # Cyan
            self.REPLACE: "\033[35m",  # Magenta
            self.REPLACE_SINGLE: "\033[35m",  # Magenta
        }

        # Use red for operator-pending
        if self._pending_operator and self._mode == self.NORMAL:
            return "\033[31m"  # Red

        return colors.get(self._mode, "\033[37m")  # Default to white

    def reset(self) -> None:
        """Reset mode manager to initial state."""
        self._mode = self.NORMAL
        self._previous_mode = self.NORMAL
        self._locked = False
        self._mode_history = [self.NORMAL]
        self._insert_variation = None
        self._pending_operator = None
        self._selection_start = None
        self._selection_end = None
        # Keep callbacks intact, just reset state

    def __repr__(self) -> str:
        """String representation of mode manager state."""
        return f"ModeManager(mode={self._mode}, previous={self._previous_mode}, locked={self._locked})"

    def __str__(self) -> str:
        """Human-readable string representation."""
        return self.get_mode_indicator()
