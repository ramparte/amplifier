"""Search and replace functionality for vi editor.

This module provides comprehensive search and replace operations including:
- Pattern-based forward and backward search
- Search navigation (n, N)
- Word search under cursor (*, #)
- Character and pattern replacement
- Substitution commands (:s)
- Search history management
"""

from .commands import get_match_highlights
from .commands import get_search_manager
from .commands import get_search_status
from .commands import handle_backward_search
from .commands import handle_clear_highlights
from .commands import handle_find_char_backward
from .commands import handle_find_char_forward
from .commands import handle_forward_search
from .commands import handle_next_match
from .commands import handle_previous_match
from .commands import handle_repeat_char_search
from .commands import handle_reverse_char_search
from .commands import handle_till_char_backward
from .commands import handle_till_char_forward
from .commands import handle_word_search_backward
from .commands import handle_word_search_forward
from .commands import register_search_commands
from .engine import SearchDirection
from .engine import SearchEngine
from .engine import SearchMatch
from .engine import SearchState
from .state import SearchManager
from .state import SearchMode
from .state import SearchState as SearchStateManager

__all__ = [
    # Engine components
    "SearchEngine",
    "SearchMatch",
    "SearchState",
    "SearchDirection",
    # State management
    "SearchManager",
    "SearchMode",
    "SearchStateManager",
    # Command handlers
    "handle_forward_search",
    "handle_backward_search",
    "handle_next_match",
    "handle_previous_match",
    "handle_word_search_forward",
    "handle_word_search_backward",
    "handle_clear_highlights",
    "handle_repeat_char_search",
    "handle_reverse_char_search",
    "handle_find_char_forward",
    "handle_find_char_backward",
    "handle_till_char_forward",
    "handle_till_char_backward",
    "register_search_commands",
    # Utility functions
    "get_search_manager",
    "get_search_status",
    "get_match_highlights",
]
