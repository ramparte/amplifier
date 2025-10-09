"""Macro recording functionality for vi editor."""

from typing import TYPE_CHECKING

from ..editing.registers import RegisterManager
from ..registry import CommandContext
from ..registry import CommandDef
from ..registry import CommandMode
from ..registry import CommandType
from .state import MacroState

if TYPE_CHECKING:
    pass


class MacroRecorder:
    """Handles macro recording operations."""

    def __init__(self, register_manager: RegisterManager, macro_state: MacroState):
        """Initialize the macro recorder.

        Args:
            register_manager: Register manager for storing macros
            macro_state: Shared macro state
        """
        self.register_manager = register_manager
        self.state = macro_state

    def start_recording(self, register: str) -> tuple[bool, str | None]:
        """Start recording a macro to a register.

        Args:
            register: Register name (a-z)

        Returns:
            Tuple of (success, error_message)
        """
        # Validate register name
        if not register or len(register) != 1 or not register.islower():
            return False, f"Invalid macro register: {register}. Use a-z"

        # Check if already recording
        if self.state.is_recording:
            return False, f"Already recording to register {self.state.recording_register}"

        # Check if in playback mode
        if self.state.is_playing:
            return False, "Cannot record during macro playback"

        # Start recording
        self.state.start_recording(register)
        return True, None

    def stop_recording(self) -> tuple[bool, str | None]:
        """Stop recording the current macro.

        Returns:
            Tuple of (success, error_message)
        """
        if not self.state.is_recording:
            return False, "Not recording a macro"

        # Get the recorded data
        register, keys = self.state.stop_recording()

        # Don't include the final 'q' that stops recording
        if keys and keys[-1] == "q":
            keys = keys[:-1]

        if not keys:
            return False, f"No keys recorded for macro {register}"

        # Store in register as a single string
        macro_content = "".join(keys)
        self.register_manager.set(register, macro_content, is_linewise=False)

        return True, None

    def record_key(self, key: str) -> None:
        """Record a key if currently recording.

        Args:
            key: Key to record
        """
        if self.state.is_recording:
            self.state.add_recorded_key(key)

    def is_recording(self) -> bool:
        """Check if currently recording.

        Returns:
            True if recording is active
        """
        return self.state.is_recording

    def get_recording_register(self) -> str | None:
        """Get the register currently being recorded to.

        Returns:
            Register name or None if not recording
        """
        return self.state.recording_register if self.state.is_recording else None

    def create_recording_commands(self) -> list[CommandDef]:
        """Create command definitions for macro recording.

        Returns:
            List of command definitions
        """
        commands = []

        # q{register} - Start recording
        def handle_start_recording(context: CommandContext) -> bool:
            # The 'q' has been consumed, next char should be the register
            # This will be handled by the dispatcher with a special state
            return True

        commands.append(
            CommandDef(
                keys="q",
                name="start_macro_recording",
                type=CommandType.ACTION,
                handler=handle_start_recording,
                modes={CommandMode.NORMAL},
                repeatable=False,
                takes_register=False,
                description="Start recording a macro (q{register})",
            )
        )

        return commands

    def handle_recording_prefix(self, context: CommandContext, next_key: str) -> tuple[bool, str | None]:
        """Handle the q{register} command to start recording.

        Args:
            context: Command context
            next_key: The register key following 'q'

        Returns:
            Tuple of (success, error_message)
        """
        if next_key == "q":
            # qq means stop recording if currently recording
            if self.state.is_recording:
                return self.stop_recording()
            # Otherwise, start recording in register 'q'
            return self.start_recording("q")
        # Start recording in the specified register
        return self.start_recording(next_key)
