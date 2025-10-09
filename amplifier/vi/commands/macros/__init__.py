"""Macro recording and playback system for vi editor.

This module provides the ability to record keystrokes into registers
and play them back, enabling complex repetitive operations.
"""

from .player import MacroPlayer
from .recorder import MacroRecorder
from .state import MacroState

__all__ = ["MacroRecorder", "MacroPlayer", "MacroState"]
