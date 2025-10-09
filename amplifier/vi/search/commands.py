"""Search command implementations for vi editor.

This module provides command handlers for all search operations including
forward/backward search, repeat search, and word search.
"""

from amplifier.vi.commands.registry import CommandContext
from amplifier.vi.commands.registry import CommandDef
from amplifier.vi.commands.registry import CommandMode
from amplifier.vi.commands.registry import CommandRegistry
from amplifier.vi.commands.registry import CommandType
from amplifier.vi.search.engine import SearchDirection
from amplifier.vi.search.state import SearchManager

# Global search manager instance
_search_manager = SearchManager()


def get_search_manager() -> SearchManager:
    """Get the global search manager instance.

    Returns:
        The search manager
    """
    return _search_manager


def handle_forward_search(context: CommandContext) -> bool:
    """Handle forward search command (/).

    Args:
        context: Command execution context

    Returns:
        True if search initiated, False otherwise
    """
    # Get search pattern from command line input
    # For now, we'll use a placeholder - in real implementation,
    # this would trigger command line mode for pattern input
    pattern = context.extra_args.get("pattern", "")

    if not pattern:
        # In real implementation, switch to command line mode for pattern input
        # For testing, we can get pattern from buffer's search state
        if hasattr(context.buffer, "_search_pattern"):
            pattern = context.buffer._search_pattern
        else:
            return False

    # Get current position
    row, col = context.buffer.get_cursor()
    lines = context.buffer.get_lines()

    # Perform search
    match = _search_manager.search(pattern, lines, row, col, SearchDirection.FORWARD)

    if match:
        # Move cursor to match
        context.buffer.push_jump_position()  # Save position for jump list
        context.buffer.set_cursor(match.row, match.start_col)

        # Store pattern in buffer for compatibility
        context.buffer._search_pattern = pattern
        context.buffer._search_direction = "forward"
        return True

    return False


def handle_backward_search(context: CommandContext) -> bool:
    """Handle backward search command (?).

    Args:
        context: Command execution context

    Returns:
        True if search initiated, False otherwise
    """
    # Get search pattern from command line input
    pattern = context.extra_args.get("pattern", "")

    if not pattern:
        # In real implementation, switch to command line mode for pattern input
        if hasattr(context.buffer, "_search_pattern"):
            pattern = context.buffer._search_pattern
        else:
            return False

    # Get current position
    row, col = context.buffer.get_cursor()
    lines = context.buffer.get_lines()

    # Perform search
    match = _search_manager.search(pattern, lines, row, col, SearchDirection.BACKWARD)

    if match:
        # Move cursor to match
        context.buffer.push_jump_position()
        context.buffer.set_cursor(match.row, match.start_col)

        # Store pattern in buffer for compatibility
        context.buffer._search_pattern = pattern
        context.buffer._search_direction = "backward"
        return True

    return False


def handle_next_match(context: CommandContext) -> bool:
    """Handle next match command (n).

    Args:
        context: Command execution context

    Returns:
        True if moved to next match, False otherwise
    """
    # Get current position
    row, col = context.buffer.get_cursor()
    lines = context.buffer.get_lines()

    # Repeat search in same direction
    match = _search_manager.repeat_search(lines, row, col, reverse=False)

    if match:
        # Move cursor to match
        context.buffer.push_jump_position()
        context.buffer.set_cursor(match.row, match.start_col)
        return True

    return False


def handle_previous_match(context: CommandContext) -> bool:
    """Handle previous match command (N).

    Args:
        context: Command execution context

    Returns:
        True if moved to previous match, False otherwise
    """
    # Get current position
    row, col = context.buffer.get_cursor()
    lines = context.buffer.get_lines()

    # Repeat search in opposite direction
    match = _search_manager.repeat_search(lines, row, col, reverse=True)

    if match:
        # Move cursor to match
        context.buffer.push_jump_position()
        context.buffer.set_cursor(match.row, match.start_col)
        return True

    return False


def handle_word_search_forward(context: CommandContext) -> bool:
    """Handle word search forward command (*).

    Args:
        context: Command execution context

    Returns:
        True if word found, False otherwise
    """
    # Get current position
    row, col = context.buffer.get_cursor()
    lines = context.buffer.get_lines()

    # Search for word under cursor forward
    match = _search_manager.search_word_under_cursor(lines, row, col, forward=True)

    if match:
        # Move cursor to match
        context.buffer.push_jump_position()
        context.buffer.set_cursor(match.row, match.start_col)

        # Store pattern in buffer for compatibility
        context.buffer._search_pattern = _search_manager.state.pattern
        context.buffer._search_direction = "forward"
        return True

    return False


def handle_word_search_backward(context: CommandContext) -> bool:
    """Handle word search backward command (#).

    Args:
        context: Command execution context

    Returns:
        True if word found, False otherwise
    """
    # Get current position
    row, col = context.buffer.get_cursor()
    lines = context.buffer.get_lines()

    # Search for word under cursor backward
    match = _search_manager.search_word_under_cursor(lines, row, col, forward=False)

    if match:
        # Move cursor to match
        context.buffer.push_jump_position()
        context.buffer.set_cursor(match.row, match.start_col)

        # Store pattern in buffer for compatibility
        context.buffer._search_pattern = _search_manager.state.pattern
        context.buffer._search_direction = "backward"
        return True

    return False


def handle_clear_highlights(context: CommandContext) -> bool:
    """Handle clear search highlights command (:noh).

    Args:
        context: Command execution context

    Returns:
        Always returns True
    """
    _search_manager.clear_highlights()
    return True


def handle_repeat_char_search(context: CommandContext) -> bool:
    """Handle repeat character search command (;).

    Args:
        context: Command execution context

    Returns:
        True if character found, False otherwise
    """
    char_search = _search_manager.get_char_search()
    if not char_search:
        return False

    char, command = char_search

    # Execute the appropriate search
    if command == "f":
        return context.buffer.find_char_forward(char)
    if command == "F":
        return context.buffer.find_char_backward(char)
    if command == "t":
        return context.buffer.find_char_forward(char, till=True)
    if command == "T":
        return context.buffer.find_char_backward(char, till=True)

    return False


def handle_reverse_char_search(context: CommandContext) -> bool:
    """Handle reverse character search command (,).

    Args:
        context: Command execution context

    Returns:
        True if character found, False otherwise
    """
    char_search = _search_manager.get_char_search()
    if not char_search:
        return False

    char, command = char_search

    # Execute the opposite search
    if command == "f":
        return context.buffer.find_char_backward(char)
    if command == "F":
        return context.buffer.find_char_forward(char)
    if command == "t":
        return context.buffer.find_char_backward(char, till=True)
    if command == "T":
        return context.buffer.find_char_forward(char, till=True)

    return False


def register_search_commands(registry: CommandRegistry) -> None:
    """Register all search commands with the command registry.

    Args:
        registry: Command registry to register with
    """
    # Forward search
    registry.register(
        CommandDef(
            keys="/",
            name="search_forward",
            type=CommandType.ACTION,
            handler=handle_forward_search,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            repeatable=True,
            motion=False,
            takes_count=False,
            description="Search forward for pattern",
        )
    )

    # Backward search
    registry.register(
        CommandDef(
            keys="?",
            name="search_backward",
            type=CommandType.ACTION,
            handler=handle_backward_search,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            repeatable=True,
            motion=False,
            takes_count=False,
            description="Search backward for pattern",
        )
    )

    # Next match
    registry.register(
        CommandDef(
            keys="n",
            name="next_match",
            type=CommandType.MOTION,
            handler=handle_next_match,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            repeatable=True,
            motion=True,
            takes_count=True,
            description="Go to next search match",
        )
    )

    # Previous match
    registry.register(
        CommandDef(
            keys="N",
            name="previous_match",
            type=CommandType.MOTION,
            handler=handle_previous_match,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            repeatable=True,
            motion=True,
            takes_count=True,
            description="Go to previous search match",
        )
    )

    # Word search forward
    registry.register(
        CommandDef(
            keys="*",
            name="word_search_forward",
            type=CommandType.ACTION,
            handler=handle_word_search_forward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            repeatable=True,
            motion=False,
            takes_count=False,
            description="Search forward for word under cursor",
        )
    )

    # Word search backward
    registry.register(
        CommandDef(
            keys="#",
            name="word_search_backward",
            type=CommandType.ACTION,
            handler=handle_word_search_backward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            repeatable=True,
            motion=False,
            takes_count=False,
            description="Search backward for word under cursor",
        )
    )

    # Repeat character search
    registry.register(
        CommandDef(
            keys=";",
            name="repeat_char_search",
            type=CommandType.MOTION,
            handler=handle_repeat_char_search,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            repeatable=True,
            motion=True,
            takes_count=True,
            description="Repeat last character search",
        )
    )

    # Reverse character search
    registry.register(
        CommandDef(
            keys=",",
            name="reverse_char_search",
            type=CommandType.MOTION,
            handler=handle_reverse_char_search,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            repeatable=True,
            motion=True,
            takes_count=True,
            description="Reverse last character search",
        )
    )


# Character search handlers that integrate with search manager
def handle_find_char_forward(context: CommandContext) -> bool:
    """Handle find character forward (f).

    Args:
        context: Command execution context

    Returns:
        True if character found, False otherwise
    """
    char = context.extra_args.get("char", "")
    if not char:
        return False

    # Store for repeat
    _search_manager.set_char_search(char, "f")

    # Execute search
    count = context.count
    success = False
    for _ in range(count):
        if context.buffer.find_char_forward(char):
            success = True
        else:
            break

    return success


def handle_find_char_backward(context: CommandContext) -> bool:
    """Handle find character backward (F).

    Args:
        context: Command execution context

    Returns:
        True if character found, False otherwise
    """
    char = context.extra_args.get("char", "")
    if not char:
        return False

    # Store for repeat
    _search_manager.set_char_search(char, "F")

    # Execute search
    count = context.count
    success = False
    for _ in range(count):
        if context.buffer.find_char_backward(char):
            success = True
        else:
            break

    return success


def handle_till_char_forward(context: CommandContext) -> bool:
    """Handle till character forward (t).

    Args:
        context: Command execution context

    Returns:
        True if character found, False otherwise
    """
    char = context.extra_args.get("char", "")
    if not char:
        return False

    # Store for repeat
    _search_manager.set_char_search(char, "t")

    # Execute search
    count = context.count
    success = False
    for _ in range(count):
        if context.buffer.find_char_forward(char, till=True):
            success = True
        else:
            break

    return success


def handle_till_char_backward(context: CommandContext) -> bool:
    """Handle till character backward (T).

    Args:
        context: Command execution context

    Returns:
        True if character found, False otherwise
    """
    char = context.extra_args.get("char", "")
    if not char:
        return False

    # Store for repeat
    _search_manager.set_char_search(char, "T")

    # Execute search
    count = context.count
    success = False
    for _ in range(count):
        if context.buffer.find_char_backward(char, till=True):
            success = True
        else:
            break

    return success


def get_search_status() -> str:
    """Get current search status for display.

    Returns:
        Search status string
    """
    return _search_manager.get_status_string()


def get_match_highlights() -> list[tuple[int, int, int]]:
    """Get match positions for highlighting.

    Returns:
        List of (row, start_col, end_col) tuples
    """
    return _search_manager.get_match_positions()
