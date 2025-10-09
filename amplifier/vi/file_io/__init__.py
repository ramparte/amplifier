"""File I/O System for vi editor.

This module provides file loading, saving, and state tracking
with encoding detection, atomic writes, and cloud sync compatibility.
"""

from .loader import FileLoader
from .loader import load_file
from .saver import FileSaver
from .saver import save_file
from .state import FileState
from .state import FileStateManager

__all__ = [
    # Loader
    "FileLoader",
    "load_file",
    # Saver
    "FileSaver",
    "save_file",
    # State
    "FileState",
    "FileStateManager",
]
