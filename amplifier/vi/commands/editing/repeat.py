"""Repeat command (.) implementation for vi editor."""

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any

if TYPE_CHECKING:
    from ...buffer.core import TextBuffer


@dataclass
class RepeatableChange:
    """Stores information about the last change made."""

    command: str  # The command that was executed
    count: int  # Count prefix for the command
    register: str | None  # Register used
    text_inserted: str | None  # Text that was inserted (for insert mode)
    operator: str | None  # Operator if this was an operator-motion
    motion: str | None  # Motion if this was an operator-motion
    motion_count: int | None  # Count for the motion
    visual_mode: str | None  # Visual mode type if applicable
    visual_range: tuple[tuple[int, int], tuple[int, int]] | None  # Visual selection range


class RepeatManager:
    """Manages the repeat (.) command functionality."""

    def __init__(self):
        """Initialize the repeat manager."""
        self.last_change: RepeatableChange | None = None
        self.is_recording: bool = False
        self.recording_buffer: list[str] = []

    def start_recording(self) -> None:
        """Start recording a repeatable change."""
        self.is_recording = True
        self.recording_buffer = []

    def stop_recording(self, change: RepeatableChange) -> None:
        """Stop recording and save the change."""
        self.is_recording = False
        self.last_change = change
        self.recording_buffer = []

    def record_key(self, key: str) -> None:
        """Record a key press during change recording."""
        if self.is_recording:
            self.recording_buffer.append(key)

    def get_last_change(self) -> RepeatableChange | None:
        """Get the last recorded change."""
        return self.last_change

    def clear(self) -> None:
        """Clear the last change."""
        self.last_change = None
        self.is_recording = False
        self.recording_buffer = []

    def create_change_from_context(
        self,
        command: str,
        count: int = 1,
        register: str | None = None,
        operator: str | None = None,
        motion: str | None = None,
        motion_count: int | None = None,
        text_inserted: str | None = None,
        visual_mode: str | None = None,
        visual_range: tuple[tuple[int, int], tuple[int, int]] | None = None,
    ) -> RepeatableChange:
        """Create a RepeatableChange from command context."""
        return RepeatableChange(
            command=command,
            count=count,
            register=register,
            text_inserted=text_inserted,
            operator=operator,
            motion=motion,
            motion_count=motion_count,
            visual_mode=visual_mode,
            visual_range=visual_range,
        )


class RepeatCommand:
    """Implementation of the repeat (.) command."""

    def __init__(self, buffer: "TextBuffer", repeat_manager: RepeatManager):
        """Initialize the repeat command handler.

        Args:
            buffer: Text buffer to operate on
            repeat_manager: Manager for repeat functionality
        """
        self.buffer = buffer
        self.repeat_manager = repeat_manager

    def execute_repeat(self, context: Any) -> bool:
        """Execute the last recorded change.

        Args:
            context: Command context containing buffer, modes, etc.

        Returns:
            True if repeat was successful, False otherwise
        """
        change = self.repeat_manager.get_last_change()
        if not change:
            return False

        # Apply count from current context if provided
        count = context.count if context.count > 1 else change.count

        # Save current state for potential undo
        self.buffer.save_state()

        try:
            # Handle different types of changes
            if change.text_inserted is not None:
                # Repeat text insertion
                for _ in range(count):
                    self.buffer.insert_text(change.text_inserted)
                return True

            if change.operator and change.motion:
                # Repeat operator-motion combination
                # This would need to be handled by the command dispatcher
                # For now, return False to indicate we need dispatcher support
                return self._repeat_operator_motion(change, count, context)

            if change.command:
                # Repeat a simple command
                # This also needs dispatcher support
                return self._repeat_simple_command(change, count, context)

            return False

        except Exception:
            # If repeat fails, restore state
            self.buffer.undo()
            return False

    def _repeat_operator_motion(self, change: RepeatableChange, count: int, context: Any) -> bool:
        """Repeat an operator-motion combination.

        This needs to interact with the command dispatcher to properly
        execute the operator and motion.
        """
        # Set up context for dispatcher
        if hasattr(context, "dispatcher"):
            dispatcher = context.dispatcher

            # Store current dispatcher state
            old_operator = dispatcher.pending_operator
            old_count = dispatcher.pending_count
            old_motion_count = dispatcher.motion_count

            # Set up for repeat
            dispatcher.pending_operator = change.operator
            dispatcher.pending_count = str(count) if count > 1 else ""
            dispatcher.motion_count = str(change.motion_count) if change.motion_count else ""

            # Process the motion
            result = False
            if change.motion:
                for key in change.motion:
                    success, error = dispatcher.process_key(key, context.modes.current_mode, context)
                    if error:
                        break
                    if success:
                        result = True

            # Restore dispatcher state
            dispatcher.pending_operator = old_operator
            dispatcher.pending_count = old_count
            dispatcher.motion_count = old_motion_count

            return result

        return False

    def _repeat_simple_command(self, change: RepeatableChange, count: int, context: Any) -> bool:
        """Repeat a simple command.

        This needs dispatcher support to re-execute the command.
        """
        if hasattr(context, "dispatcher"):
            dispatcher = context.dispatcher

            # Store current state
            old_count = dispatcher.pending_count

            # Set count for repeat
            dispatcher.pending_count = str(count) if count > 1 else ""

            # Process the command
            result = False
            for key in change.command:
                success, error = dispatcher.process_key(key, context.modes.current_mode, context)
                if error:
                    break
                if success:
                    result = True

            # Restore state
            dispatcher.pending_count = old_count

            return result

        return False
