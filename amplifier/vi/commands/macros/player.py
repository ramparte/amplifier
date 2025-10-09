"""Macro playback functionality for vi editor."""

from typing import TYPE_CHECKING

from ..editing.registers import RegisterManager
from ..registry import CommandContext
from ..registry import CommandDef
from ..registry import CommandMode
from ..registry import CommandType
from .state import MacroState

if TYPE_CHECKING:
    from ..registry import CommandDispatcher


class MacroPlayer:
    """Handles macro playback operations."""

    def __init__(self, register_manager: RegisterManager, macro_state: MacroState):
        """Initialize the macro player.

        Args:
            register_manager: Register manager for retrieving macros
            macro_state: Shared macro state
        """
        self.register_manager = register_manager
        self.state = macro_state
        self.dispatcher: CommandDispatcher | None = None

    def set_dispatcher(self, dispatcher: "CommandDispatcher") -> None:
        """Set the command dispatcher for playback.

        Args:
            dispatcher: Command dispatcher to use for executing macro commands
        """
        self.dispatcher = dispatcher

    def play_macro(self, register: str, context: CommandContext, count: int = 1) -> tuple[bool, str | None]:
        """Play a macro from a register.

        Args:
            register: Register containing the macro
            context: Command context for execution
            count: Number of times to repeat the macro

        Returns:
            Tuple of (success, error_message)
        """
        if not self.dispatcher:
            return False, "No command dispatcher configured"

        # Check if we can start playback
        if not self.state.can_playback():
            return False, f"Maximum macro depth ({self.state.max_playback_depth}) exceeded"

        # Get macro content from register
        content = self.register_manager.get(register)
        if not content or not content.text:
            return False, f"No macro recorded in register {register}"

        # Start playback
        if not self.state.start_playback(register):
            return False, "Cannot start macro playback"

        macro_keys = content.text
        success = True
        error_msg = None

        try:
            # Execute macro 'count' times
            for iteration in range(count):
                # Process each key in the macro
                for key in macro_keys:
                    # Skip if we're trying to record during playback
                    if key == "q" and self.state.is_playing:
                        continue

                    # Process the key through the dispatcher
                    executed, error = self.dispatcher.process_key(key, CommandMode.NORMAL, context)

                    if error and self.state.stop_on_error:
                        success = False
                        error_msg = f"Macro playback error at iteration {iteration + 1}: {error}"
                        break

                if not success and self.state.stop_on_error:
                    break

        finally:
            # End playback
            self.state.end_playback()

        return success, error_msg

    def repeat_last_macro(self, context: CommandContext, count: int = 1) -> tuple[bool, str | None]:
        """Repeat the last played macro.

        Args:
            context: Command context for execution
            count: Number of times to repeat

        Returns:
            Tuple of (success, error_message)
        """
        if not self.state.last_played_register:
            return False, "No previous macro to repeat"

        return self.play_macro(self.state.last_played_register, context, count)

    def is_playing(self) -> bool:
        """Check if currently playing a macro.

        Returns:
            True if playback is active
        """
        return self.state.is_playing

    def create_playback_commands(self) -> list[CommandDef]:
        """Create command definitions for macro playback.

        Returns:
            List of command definitions
        """
        commands = []

        # @{register} - Execute macro from register
        def handle_play_macro(context: CommandContext) -> bool:
            # This is handled by the dispatcher with special state
            return True

        commands.append(
            CommandDef(
                keys="@",
                name="play_macro",
                type=CommandType.ACTION,
                handler=handle_play_macro,
                modes={CommandMode.NORMAL},
                repeatable=True,
                takes_count=True,
                takes_register=False,
                description="Execute macro from register (@{register})",
            )
        )

        # @@ - Repeat last macro
        def handle_repeat_macro(context: CommandContext) -> bool:
            success, error = self.repeat_last_macro(context, context.count)
            if error:
                # Log error but return True to indicate command was handled
                print(f"Macro error: {error}")
            return success

        commands.append(
            CommandDef(
                keys="@@",
                name="repeat_last_macro",
                type=CommandType.ACTION,
                handler=handle_repeat_macro,
                modes={CommandMode.NORMAL},
                repeatable=True,
                takes_count=True,
                description="Repeat last executed macro",
            )
        )

        return commands

    def handle_playback_prefix(self, context: CommandContext, next_key: str) -> tuple[bool, str | None]:
        """Handle the @{register} command to play a macro.

        Args:
            context: Command context
            next_key: The register key following '@'

        Returns:
            Tuple of (success, error_message)
        """
        # Handle @@ for repeat
        if next_key == "@":
            return self.repeat_last_macro(context, context.count)

        # Validate register
        if not next_key or (not next_key.islower() and not next_key.isupper()):
            return False, f"Invalid macro register: {next_key}. Use a-z or A-Z"

        # Play the macro
        return self.play_macro(next_key.lower(), context, context.count)
