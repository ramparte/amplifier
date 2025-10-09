"""Command execution module for vi editor."""

from .executor import CommandExecutor
from .motions import register_motion_commands
from .numeric_handler import NumericPrefixHandler
from .operators import register_operator_commands
from .registry import CommandContext
from .registry import CommandDef
from .registry import CommandDispatcher
from .registry import CommandMode
from .registry import CommandRegistry
from .registry import CommandType
from .text_objects import register_text_objects

__all__ = [
    "CommandExecutor",
    "CommandRegistry",
    "CommandDispatcher",
    "CommandContext",
    "CommandDef",
    "CommandMode",
    "CommandType",
    "NumericPrefixHandler",
    "register_motion_commands",
    "register_operator_commands",
    "register_text_objects",
]
