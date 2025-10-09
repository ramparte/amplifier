"""Integration module to register all movement commands with the command registry."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import CommandContext
    from ..registry import CommandRegistry

from ..registry import CommandDef
from ..registry import CommandMode
from ..registry import CommandType
from .basic import BasicMovements
from .brackets import BracketMovement
from .char_search import CharSearchMovements
from .line import LineMovements
from .screen import ScreenMovements
from .word import WordMovements


def register_movement_commands(registry: "CommandRegistry") -> None:
    """Register all movement commands with the command registry.

    Args:
        registry: Command registry to register commands with
    """
    # Define normal mode set
    normal_modes = {CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.VISUAL_LINE, CommandMode.OPERATOR_PENDING}

    # Basic movements (h, j, k, l)
    def make_basic_handler(direction: str):
        def handler(ctx: "CommandContext") -> bool:
            movements = BasicMovements(ctx.buffer)
            if direction == "h":
                return movements.move_left(ctx.count)
            if direction == "j":
                return movements.move_down(ctx.count)
            if direction == "k":
                return movements.move_up(ctx.count)
            if direction == "l":
                return movements.move_right(ctx.count)
            return False

        return handler

    for key, name in [("h", "left"), ("j", "down"), ("k", "up"), ("l", "right")]:
        registry.register(
            CommandDef(
                keys=key,
                name=f"move_{name}",
                type=CommandType.MOTION,
                handler=make_basic_handler(key),
                modes=normal_modes,
                motion=True,
                description=f"Move cursor {name}",
            )
        )

    # Word movements
    def make_word_handler(movement_type: str, big_word: bool = False):
        def handler(ctx: "CommandContext") -> bool:
            movements = WordMovements(ctx.buffer)
            if movement_type == "forward":
                return movements.word_forward(ctx.count, big_word)
            if movement_type == "backward":
                return movements.word_backward(ctx.count, big_word)
            if movement_type == "end":
                return movements.word_end_forward(ctx.count, big_word)
            return False

        return handler

    word_commands = [
        ("w", "word_forward", "forward", False, "Move forward by word"),
        ("W", "WORD_forward", "forward", True, "Move forward by WORD"),
        ("b", "word_backward", "backward", False, "Move backward by word"),
        ("B", "WORD_backward", "backward", True, "Move backward by WORD"),
        ("e", "word_end", "end", False, "Move to end of word"),
        ("E", "WORD_end", "end", True, "Move to end of WORD"),
    ]

    for key, name, movement_type, big_word, desc in word_commands:
        registry.register(
            CommandDef(
                keys=key,
                name=name,
                type=CommandType.MOTION,
                handler=make_word_handler(movement_type, big_word),
                modes=normal_modes,
                motion=True,
                description=desc,
            )
        )

    # Line movements
    def make_line_handler(movement_type: str):
        def handler(ctx: "CommandContext") -> bool:
            movements = LineMovements(ctx.buffer)
            if movement_type == "start":
                return movements.to_line_start()
            if movement_type == "first_non_blank":
                return movements.to_first_non_blank()
            if movement_type == "end":
                return movements.to_line_end()
            if movement_type == "last_non_blank":
                return movements.to_last_non_blank()
            if movement_type == "same_indent":
                return movements.to_first_non_blank_same_indent()
            return False

        return handler

    line_commands = [
        ("0", "line_start", "start", "Move to start of line"),
        ("^", "first_non_blank", "first_non_blank", "Move to first non-blank character"),
        ("$", "line_end", "end", "Move to end of line"),
        ("g_", "last_non_blank", "last_non_blank", "Move to last non-blank character"),
        ("_", "same_indent", "same_indent", "Move to first non-blank same indent"),
    ]

    for key, name, movement_type, desc in line_commands:
        registry.register(
            CommandDef(
                keys=key,
                name=name,
                type=CommandType.MOTION,
                handler=make_line_handler(movement_type),
                modes=normal_modes,
                motion=True,
                takes_count=(key != "0"),  # 0 doesn't take count
                description=desc,
            )
        )

    # Screen movements
    def make_screen_handler(movement_type: str):
        def handler(ctx: "CommandContext") -> bool:
            # Get viewport info from renderer if available
            viewport_start = getattr(ctx.renderer, "viewport_start", 0)
            viewport_height = getattr(ctx.renderer, "viewport_height", 24)

            movements = ScreenMovements(ctx.buffer, viewport_start, viewport_height)

            if movement_type == "top":
                return movements.to_screen_top(ctx.count - 1 if ctx.count > 1 else 0)
            if movement_type == "middle":
                return movements.to_screen_middle()
            if movement_type == "bottom":
                return movements.to_screen_bottom(ctx.count - 1 if ctx.count > 1 else 0)
            return False

        return handler

    screen_commands = [
        ("H", "screen_top", "top", "Move to top of screen"),
        ("M", "screen_middle", "middle", "Move to middle of screen"),
        ("L", "screen_bottom", "bottom", "Move to bottom of screen"),
    ]

    for key, name, movement_type, desc in screen_commands:
        registry.register(
            CommandDef(
                keys=key,
                name=name,
                type=CommandType.MOTION,
                handler=make_screen_handler(movement_type),
                modes=normal_modes,
                motion=True,
                description=desc,
            )
        )

    # Character search commands
    char_search_state = {"movements": None}

    def make_char_search_handler(search_type: str):
        def handler(ctx: "CommandContext") -> bool:
            # Initialize char search if needed
            if char_search_state["movements"] is None:
                char_search_state["movements"] = CharSearchMovements(ctx.buffer)

            movements = char_search_state["movements"]

            # For f/F/t/T, we need to get the next character
            # This should be handled by the dispatcher putting it in extra_args
            if search_type in ["f", "F", "t", "T"]:
                target_char = ctx.extra_args.get("target_char")
                if not target_char:
                    return False

                till = search_type in ["t", "T"]
                forward = search_type in ["f", "t"]

                if forward:
                    return movements.find_char_forward(target_char, ctx.count, till)
                return movements.find_char_backward(target_char, ctx.count, till)
            if search_type == "repeat":
                return movements.repeat_search(ctx.count)
            if search_type == "repeat_reverse":
                return movements.repeat_search_reverse(ctx.count)
            return False

        return handler

    # Register character search commands - these need special handling
    char_commands = [
        ("f", "find_forward", "f", "Find character forward"),
        ("F", "find_backward", "F", "Find character backward"),
        ("t", "till_forward", "t", "Move till character forward"),
        ("T", "till_backward", "T", "Move till character backward"),
        (";", "repeat_search", "repeat", "Repeat character search"),
        (",", "repeat_search_reverse", "repeat_reverse", "Repeat search in reverse"),
    ]

    for key, name, search_type, desc in char_commands:
        registry.register(
            CommandDef(
                keys=key,
                name=name,
                type=CommandType.MOTION,
                handler=make_char_search_handler(search_type),
                modes=normal_modes,
                motion=True,
                description=desc,
            )
        )

    # Go to line commands
    def goto_line_handler(ctx: "CommandContext") -> bool:
        if ctx.count == 1 and not ctx.extra_args.get("has_count"):
            # No count means last line
            ctx.buffer.move_to_last_line()
        else:
            # Go to specific line
            target_row = min(ctx.count - 1, len(ctx.buffer.lines) - 1)
            ctx.buffer.set_cursor(target_row, 0)
        return True

    registry.register(
        CommandDef(
            keys="G",
            name="goto_line",
            type=CommandType.MOTION,
            handler=goto_line_handler,
            modes=normal_modes,
            motion=True,
            description="Go to line (last line if no count)",
        )
    )

    def goto_first_line_handler(ctx: "CommandContext") -> bool:
        ctx.buffer.move_to_first_line()
        return True

    registry.register(
        CommandDef(
            keys="gg",
            name="goto_first_line",
            type=CommandType.MOTION,
            handler=goto_first_line_handler,
            modes=normal_modes,
            motion=True,
            description="Go to first line",
        )
    )

    # Bracket matching (%)
    def bracket_match_handler(ctx: "CommandContext") -> bool:
        bracket_movement = BracketMovement(ctx.buffer)
        return bracket_movement.find_matching_bracket()

    registry.register(
        CommandDef(
            keys="%",
            name="match_bracket",
            type=CommandType.MOTION,
            handler=bracket_match_handler,
            modes=normal_modes,
            motion=True,
            takes_count=False,  # % doesn't take count
            description="Jump to matching bracket",
        )
    )
