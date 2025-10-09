"""Ex command system for vi editor.

This module provides ex command parsing and execution capabilities including:
- Command parsing with ranges and arguments
- Core file operations (read/write/edit)
- Text substitution with regex
- Editor settings management
"""

from .core_commands import ExCoreCommands
from .parser import ExCommandParser
from .settings import ExSettings
from .substitution import ExSubstitution

__all__ = ["ExCommandParser", "ExCoreCommands", "ExSubstitution", "ExSettings"]
