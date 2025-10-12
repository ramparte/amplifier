"""Undo/redo system implementation for the vi editor."""

from dataclasses import dataclass


@dataclass
class UndoState:
    """Represents a state that can be undone/redone."""

    buffer_lines: list[str]
    cursor_pos: tuple[int, int]
    description: str
    yank_buffer: str | None = None
    yank_is_line: bool = False


class UndoRedoManager:
    """Manages undo and redo operations for the vi editor."""

    def __init__(self, editor, max_history: int = 100):
        """Initialize the undo/redo manager.

        Args:
            editor: Reference to the main editor instance
            max_history: Maximum number of undo states to keep
        """
        self.editor = editor
        self.max_history = max_history
        self.undo_stack: list[UndoState] = []
        self.redo_stack: list[UndoState] = []
        self.is_recording = True
        self.batch_mode = False
        self.batch_states: list[UndoState] = []

    def save_state(self, description: str = "edit") -> None:
        """Save the current editor state to the undo stack.

        Args:
            description: Description of the operation being saved
        """
        if not self.is_recording:
            return

        # Create snapshot of current state
        state = UndoState(
            buffer_lines=self.editor.buffer.get_lines().copy(),
            cursor_pos=self.editor.cursor_pos,
            description=description,
            yank_buffer=getattr(self.editor, "yank_buffer", None),
            yank_is_line=getattr(self.editor, "yank_is_line", False),
        )

        if self.batch_mode:
            # In batch mode, accumulate states
            self.batch_states.append(state)
        else:
            # Normal mode: add to undo stack
            self._add_to_undo_stack(state)
            # Clear redo stack when new change is made
            self.redo_stack.clear()

    def _add_to_undo_stack(self, state: UndoState) -> None:
        """Add a state to the undo stack, maintaining size limit.

        Args:
            state: The state to add
        """
        self.undo_stack.append(state)

        # Maintain maximum history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)

    def begin_batch(self) -> None:
        """Begin a batch operation (multiple changes treated as one undo)."""
        self.batch_mode = True
        self.batch_states = []
        # Save initial state before batch
        self.save_state("batch_start")

    def end_batch(self, description: str = "batch_operation") -> None:
        """End a batch operation and combine all changes into one undo state.

        Args:
            description: Description of the batch operation
        """
        if not self.batch_mode:
            return

        self.batch_mode = False

        if self.batch_states:
            # Use the first state as the undo point
            first_state = self.batch_states[0]
            first_state.description = description
            self._add_to_undo_stack(first_state)

            # Clear redo stack
            self.redo_stack.clear()

        self.batch_states = []

    def undo(self) -> bool:
        """Perform an undo operation.

        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self.undo_stack:
            return False

        # Save current state to redo stack
        current_state = UndoState(
            buffer_lines=self.editor.buffer.get_lines().copy(),
            cursor_pos=self.editor.cursor_pos,
            description="current",
            yank_buffer=getattr(self.editor, "yank_buffer", None),
            yank_is_line=getattr(self.editor, "yank_is_line", False),
        )
        self.redo_stack.append(current_state)

        # Restore previous state
        previous_state = self.undo_stack.pop()
        self._restore_state(previous_state)

        return True

    def redo(self) -> bool:
        """Perform a redo operation.

        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self.redo_stack:
            return False

        # Save current state to undo stack
        current_state = UndoState(
            buffer_lines=self.editor.buffer.get_lines().copy(),
            cursor_pos=self.editor.cursor_pos,
            description="current",
            yank_buffer=getattr(self.editor, "yank_buffer", None),
            yank_is_line=getattr(self.editor, "yank_is_line", False),
        )
        self.undo_stack.append(current_state)

        # Restore next state
        next_state = self.redo_stack.pop()
        self._restore_state(next_state)

        return True

    def _restore_state(self, state: UndoState) -> None:
        """Restore the editor to a given state.

        Args:
            state: The state to restore
        """
        # Temporarily disable recording while restoring
        old_recording = self.is_recording
        self.is_recording = False

        # Restore buffer content
        self.editor.buffer.lines = state.buffer_lines.copy()

        # Restore cursor position
        self.editor.cursor_pos = state.cursor_pos

        # Restore yank buffer if it exists
        if hasattr(self.editor, "yank_buffer"):
            self.editor.yank_buffer = state.yank_buffer
            self.editor.yank_is_line = state.yank_is_line

        # Re-enable recording
        self.is_recording = old_recording

    def clear_history(self) -> None:
        """Clear all undo/redo history."""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.batch_states.clear()

    def can_undo(self) -> bool:
        """Check if undo is possible.

        Returns:
            True if there are states to undo
        """
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is possible.

        Returns:
            True if there are states to redo
        """
        return len(self.redo_stack) > 0

    def get_undo_count(self) -> int:
        """Get the number of undo operations available.

        Returns:
            Number of states in the undo stack
        """
        return len(self.undo_stack)

    def get_redo_count(self) -> int:
        """Get the number of redo operations available.

        Returns:
            Number of states in the redo stack
        """
        return len(self.redo_stack)

    def disable_recording(self) -> None:
        """Temporarily disable undo recording."""
        self.is_recording = False

    def enable_recording(self) -> None:
        """Re-enable undo recording."""
        self.is_recording = True

    def get_last_description(self) -> str | None:
        """Get the description of the last undo state.

        Returns:
            Description string or None if no undo states
        """
        if self.undo_stack:
            return self.undo_stack[-1].description
        return None
