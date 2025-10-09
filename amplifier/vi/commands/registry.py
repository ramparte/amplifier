"""Enhanced command registry for vi editor.

This module provides a comprehensive command registration and dispatch system
that handles mode-aware command execution, operator-motion combinations,
numeric prefixes, and text object integration.
"""

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from typing import Any


class CommandMode(Enum):
    """Supported vi editor modes."""

    NORMAL = "normal"
    INSERT = "insert"
    VISUAL = "visual"
    VISUAL_LINE = "visual_line"
    VISUAL_BLOCK = "visual_block"
    COMMAND_LINE = "command_line"
    OPERATOR_PENDING = "operator_pending"


class CommandType(Enum):
    """Types of vi commands."""

    MOTION = "motion"
    OPERATOR = "operator"
    TEXT_OBJECT = "text_object"
    ACTION = "action"
    MODE_CHANGE = "mode_change"
    MISC = "misc"


@dataclass
class CommandContext:
    """Context passed to command handlers."""

    buffer: Any  # TextBuffer instance
    modes: Any  # ModeManager instance
    renderer: Any  # Renderer instance
    count: int = 1
    register: str | None = None
    operator: str | None = None
    motion_count: int | None = None
    last_command: str | None = None
    visual_start: tuple[int, int] | None = None
    visual_end: tuple[int, int] | None = None
    extra_args: dict[str, Any] = field(default_factory=dict)


@dataclass
class CommandDef:
    """Definition of a vi command."""

    keys: str  # Key sequence that triggers this command
    name: str  # Human-readable command name
    type: CommandType
    handler: Callable[[CommandContext], bool]
    modes: set[CommandMode] = field(default_factory=set)
    repeatable: bool = True
    motion: bool = False  # True if this can be used as a motion
    takes_count: bool = True
    takes_register: bool = False
    operator_pending: bool = False  # True if puts editor in operator-pending mode
    description: str = ""


class CommandRegistry:
    """Central registry for all vi commands."""

    def __init__(self):
        """Initialize the command registry."""
        self.commands: dict[str, dict[CommandMode, CommandDef]] = {}
        self.partial_matches: dict[str, list[str]] = {}
        self.operators: set[str] = set()
        self.motions: set[str] = set()
        self.text_objects: set[str] = set()
        self._build_lookup_cache()

    def register(self, command: CommandDef) -> None:
        """Register a new command.

        Args:
            command: Command definition to register
        """
        if command.keys not in self.commands:
            self.commands[command.keys] = {}

        # Register for each mode the command supports
        for mode in command.modes:
            self.commands[command.keys][mode] = command

        # Track special command types
        if command.type == CommandType.OPERATOR:
            self.operators.add(command.keys)
        elif command.type == CommandType.MOTION:
            self.motions.add(command.keys)
        elif command.type == CommandType.TEXT_OBJECT:
            self.text_objects.add(command.keys)

        # Rebuild lookup cache
        self._build_lookup_cache()

    def unregister(self, keys: str, mode: CommandMode | None = None) -> None:
        """Unregister a command.

        Args:
            keys: Key sequence of command to unregister
            mode: Specific mode to unregister from, or None for all modes
        """
        if keys in self.commands:
            if mode:
                self.commands[keys].pop(mode, None)
                if not self.commands[keys]:
                    del self.commands[keys]
            else:
                del self.commands[keys]

            # Update special sets
            if keys in self.operators:
                self.operators.discard(keys)
            if keys in self.motions:
                self.motions.discard(keys)
            if keys in self.text_objects:
                self.text_objects.discard(keys)

            self._build_lookup_cache()

    def get_command(self, keys: str, mode: CommandMode) -> CommandDef | None:
        """Get a command definition for given keys and mode.

        Args:
            keys: Key sequence
            mode: Current editor mode

        Returns:
            Command definition if found, None otherwise
        """
        if keys in self.commands:
            return self.commands[keys].get(mode)
        return None

    def has_partial_match(self, keys: str, mode: CommandMode) -> bool:
        """Check if keys could be the start of a valid command.

        Args:
            keys: Partial key sequence
            mode: Current editor mode

        Returns:
            True if keys could lead to a valid command
        """
        # Direct command match
        if keys in self.commands and mode in self.commands[keys]:
            return True

        # Check if it's a prefix of any command
        return any(cmd_keys.startswith(keys) and mode in self.commands[cmd_keys] for cmd_keys in self.commands)

    def get_possible_completions(self, keys: str, mode: CommandMode) -> list[str]:
        """Get list of possible command completions.

        Args:
            keys: Partial key sequence
            mode: Current editor mode

        Returns:
            List of command keys that start with given prefix
        """
        completions = []
        for cmd_keys in self.commands:
            if cmd_keys.startswith(keys) and mode in self.commands[cmd_keys]:
                completions.append(cmd_keys)
        return sorted(completions)

    def is_operator(self, keys: str) -> bool:
        """Check if keys represent an operator command.

        Args:
            keys: Key sequence

        Returns:
            True if keys are an operator
        """
        return keys in self.operators

    def is_motion(self, keys: str) -> bool:
        """Check if keys represent a motion command.

        Args:
            keys: Key sequence

        Returns:
            True if keys are a motion
        """
        return keys in self.motions

    def is_text_object(self, keys: str) -> bool:
        """Check if keys represent a text object.

        Args:
            keys: Key sequence

        Returns:
            True if keys are a text object
        """
        return keys in self.text_objects

    def get_commands_for_mode(self, mode: CommandMode) -> list[CommandDef]:
        """Get all commands available in a specific mode.

        Args:
            mode: Editor mode

        Returns:
            List of command definitions available in the mode
        """
        commands = []
        for cmd_dict in self.commands.values():
            if mode in cmd_dict:
                commands.append(cmd_dict[mode])
        return commands

    def _build_lookup_cache(self) -> None:
        """Build cache for partial match lookups."""
        self.partial_matches.clear()

        for keys in self.commands:
            # Add all prefixes of this command
            for i in range(1, len(keys)):
                prefix = keys[:i]
                if prefix not in self.partial_matches:
                    self.partial_matches[prefix] = []
                if keys not in self.partial_matches[prefix]:
                    self.partial_matches[prefix].append(keys)


class CommandDispatcher:
    """Dispatches commands based on current mode and input."""

    def __init__(self, registry: CommandRegistry):
        """Initialize the command dispatcher.

        Args:
            registry: Command registry to use for lookups
        """
        self.registry = registry
        self.pending_keys = ""
        self.pending_operator: str | None = None
        self.pending_count = ""
        self.motion_count = ""
        self.pending_register: str | None = None
        self.last_command: str | None = None
        self.last_context: CommandContext | None = None

    def process_key(self, key: str, mode: CommandMode, context: CommandContext) -> tuple[bool, str | None]:
        """Process a single key input.

        Args:
            key: Input key
            mode: Current editor mode
            context: Command context

        Returns:
            Tuple of (command_executed, error_message)
        """
        # Handle numeric prefix
        if key.isdigit() and (key != "0" or self.pending_count or self.motion_count):
            if self.pending_operator:
                self.motion_count += key
            else:
                self.pending_count += key
            return (False, None)

        # Add key to pending sequence
        self.pending_keys += key

        # Check for exact match
        command = self.registry.get_command(self.pending_keys, mode)
        if command:
            # If we have a pending operator and this is a motion or text object,
            # handle it as an operator-motion combination
            if self.pending_operator and (command.type == CommandType.TEXT_OBJECT or command.motion):
                return self._try_operator_motion(context)
            return self._execute_command(command, context)

        # Check for partial match
        if self.registry.has_partial_match(self.pending_keys, mode):
            # Wait for more input
            return (False, None)

        # No match found - try to parse operator-motion combination
        if self.pending_operator:
            return self._try_operator_motion(context)

        # Clear pending state and return error
        error_msg = f"Unknown command: {self.pending_keys}"
        self.reset()
        return (False, error_msg)

    def _execute_command(self, command: CommandDef, context: CommandContext) -> tuple[bool, str | None]:
        """Execute a command with given context.

        Args:
            command: Command to execute
            context: Execution context

        Returns:
            Tuple of (success, error_message)
        """
        # Update context with dispatcher state
        context.count = int(self.pending_count) if self.pending_count else 1
        context.register = self.pending_register
        context.operator = self.pending_operator
        context.motion_count = int(self.motion_count) if self.motion_count else None
        context.last_command = self.last_command

        # Handle operator-pending mode
        if command.operator_pending:
            self.pending_operator = command.keys
            self.pending_keys = ""
            return (False, None)

        # Execute the command
        try:
            success = command.handler(context)

            if success:
                # Store for repeat
                if command.repeatable:
                    self.last_command = self.pending_keys
                    self.last_context = context

                # Reset state
                self.reset()
                return (True, None)
            self.reset()
            return (False, f"Command failed: {command.name}")

        except Exception as e:
            self.reset()
            return (False, f"Error executing {command.name}: {str(e)}")

    def _try_operator_motion(self, context: CommandContext) -> tuple[bool, str | None]:
        """Try to execute an operator-motion combination.

        Args:
            context: Execution context

        Returns:
            Tuple of (success, error_message)
        """
        # Check if pending_keys is a valid motion or text object
        motion_cmd = self.registry.get_command(self.pending_keys, CommandMode.OPERATOR_PENDING)

        if not motion_cmd:
            # Try in normal mode as fallback
            motion_cmd = self.registry.get_command(self.pending_keys, CommandMode.NORMAL)

        if motion_cmd and (motion_cmd.motion or motion_cmd.type == CommandType.TEXT_OBJECT):
            # First execute the motion/text object to get the range
            # Store current position
            start_row, start_col = context.buffer.get_cursor()

            # Execute motion/text object to set visual_start and visual_end
            motion_success = motion_cmd.handler(context)

            if not motion_success:
                self.reset()
                return (False, "Motion execution failed")

            # Get operator command
            operator_cmd = self.registry.get_command(self.pending_operator, CommandMode.NORMAL)

            if operator_cmd:
                # Set up context for operator execution
                context.count = int(self.pending_count) if self.pending_count else 1
                context.motion_count = int(self.motion_count) if self.motion_count else 1
                context.extra_args["motion"] = self.pending_keys
                context.extra_args["motion_type"] = motion_cmd.type.value

                # If motion set visual_start/visual_end, operator will use those
                # Otherwise, use the cursor movement range
                if not context.visual_start:
                    end_row, end_col = context.buffer.get_cursor()
                    context.visual_start = (start_row, start_col)
                    context.visual_end = (end_row, end_col)

                # Execute operator
                success = operator_cmd.handler(context)

                if success:
                    self.last_command = self.pending_operator + self.pending_keys
                    self.last_context = context

                self.reset()
                return (success, None if success else "Operator execution failed")

        error_msg = f"Invalid motion for operator: {self.pending_keys}"
        self.reset()
        return (False, error_msg)

    def repeat_last_command(self, context: CommandContext) -> tuple[bool, str | None]:
        """Repeat the last executed command.

        Args:
            context: Current command context

        Returns:
            Tuple of (success, error_message)
        """
        if not self.last_command:
            return (False, "No command to repeat")

        # Use saved context but update buffer/modes/renderer
        if self.last_context:
            self.last_context.buffer = context.buffer
            self.last_context.modes = context.modes
            self.last_context.renderer = context.renderer

            # Parse and execute the last command
            for key in self.last_command:
                result, error = self.process_key(key, CommandMode.NORMAL, self.last_context)
                if error:
                    return (False, error)

            return (True, None)

        return (False, "Cannot repeat command")

    def reset(self) -> None:
        """Reset dispatcher state."""
        self.pending_keys = ""
        self.pending_count = ""
        self.motion_count = ""
        self.pending_operator = None
        self.pending_register = None

    def get_state_string(self) -> str:
        """Get a string representation of current dispatcher state.

        Returns:
            Human-readable state string for debugging
        """
        parts = []
        if self.pending_count:
            parts.append(f"count:{self.pending_count}")
        if self.pending_operator:
            parts.append(f"op:{self.pending_operator}")
        if self.motion_count:
            parts.append(f"motion_count:{self.motion_count}")
        if self.pending_keys:
            parts.append(f"keys:{self.pending_keys}")
        if self.pending_register:
            parts.append(f"reg:{self.pending_register}")

        return " ".join(parts) if parts else "idle"
