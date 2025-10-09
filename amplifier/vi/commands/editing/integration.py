"""Integration module to register all editing commands with the command registry."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..registry import CommandContext
    from ..registry import CommandRegistry

from ..registry import CommandDef
from ..registry import CommandMode
from ..registry import CommandType
from .case import CaseCommand
from .indent import IndentCommand
from .join import JoinCommand
from .repeat import RepeatCommand
from .repeat import RepeatManager


def register_editing_commands(registry: "CommandRegistry", repeat_manager: RepeatManager | None = None) -> None:
    """Register all editing commands with the command registry.

    Args:
        registry: Command registry to register commands with
        repeat_manager: Optional repeat manager for . command
    """
    # Define normal mode set
    normal_modes = {CommandMode.NORMAL}
    visual_modes = {CommandMode.VISUAL, CommandMode.VISUAL_LINE}
    all_modes = normal_modes | visual_modes

    # Join commands
    def join_handler(ctx: "CommandContext") -> bool:
        join_cmd = JoinCommand(ctx.buffer)
        if ctx.modes.current_mode in visual_modes:
            # In visual mode, join selected lines
            if ctx.visual_start and ctx.visual_end:
                return join_cmd.join_lines_visual(ctx.visual_start[0], ctx.visual_end[0], add_space=True)
        else:
            # In normal mode, join with count
            return join_cmd.join_lines(ctx.count, add_space=True)
        return False

    def join_no_space_handler(ctx: "CommandContext") -> bool:
        join_cmd = JoinCommand(ctx.buffer)
        if ctx.modes.current_mode in visual_modes:
            # In visual mode, join selected lines without space
            if ctx.visual_start and ctx.visual_end:
                return join_cmd.join_lines_visual(ctx.visual_start[0], ctx.visual_end[0], add_space=False)
        else:
            # In normal mode, join with count without space
            return join_cmd.join_lines(ctx.count, add_space=False)
        return False

    registry.register(
        CommandDef(
            keys="J",
            name="join_lines",
            type=CommandType.ACTION,
            handler=join_handler,
            modes=all_modes,
            description="Join lines with space",
        )
    )

    registry.register(
        CommandDef(
            keys="gJ",
            name="join_lines_no_space",
            type=CommandType.ACTION,
            handler=join_no_space_handler,
            modes=all_modes,
            description="Join lines without space",
        )
    )

    # Case commands
    def toggle_case_handler(ctx: "CommandContext") -> bool:
        case_cmd = CaseCommand(ctx.buffer)
        return case_cmd.toggle_case_char(ctx.count)

    registry.register(
        CommandDef(
            keys="~",
            name="toggle_case",
            type=CommandType.ACTION,
            handler=toggle_case_handler,
            modes=normal_modes,
            description="Toggle case of character(s)",
        )
    )

    # Case operators (gu, gU, g~)
    def make_case_operator(operation: str):
        def handler(ctx: "CommandContext") -> bool:
            case_cmd = CaseCommand(ctx.buffer)

            # Check if we have a visual selection
            if ctx.visual_start and ctx.visual_end:
                return case_cmd.convert_case_visual(ctx.visual_start, ctx.visual_end, operation)

            # Check if this is linewise operation (guu, gUU, g~~)
            if ctx.extra_args.get("linewise"):
                row = ctx.buffer.get_cursor()[0]
                return case_cmd.convert_case_lines(row, ctx.count, operation)

            # Otherwise wait for motion
            return False

        return handler

    # Register case operators
    for keys, name, operation, desc in [
        ("gu", "lowercase", "lower", "Convert to lowercase"),
        ("gU", "uppercase", "upper", "Convert to uppercase"),
        ("g~", "toggle_case_op", "toggle", "Toggle case"),
    ]:
        registry.register(
            CommandDef(
                keys=keys,
                name=name,
                type=CommandType.OPERATOR,
                handler=make_case_operator(operation),
                modes=normal_modes,
                operator_pending=True,
                description=desc,
            )
        )

        # Also register double versions (guu, gUU, g~~) for linewise
        def make_linewise_handler(op: str):
            def handler(ctx: "CommandContext") -> bool:
                case_cmd = CaseCommand(ctx.buffer)
                row = ctx.buffer.get_cursor()[0]
                return case_cmd.convert_case_lines(row, ctx.count, op)

            return handler

        registry.register(
            CommandDef(
                keys=keys + keys[-1],  # guu, gUU, g~~
                name=f"{name}_line",
                type=CommandType.ACTION,
                handler=make_linewise_handler(operation),
                modes=normal_modes,
                description=f"{desc} (line)",
            )
        )

    # Indent commands
    def make_indent_handler(direction: str):
        def handler(ctx: "CommandContext") -> bool:
            indent_cmd = IndentCommand(ctx.buffer)

            # Check if we have a visual selection
            if ctx.modes.current_mode in visual_modes and ctx.visual_start and ctx.visual_end:
                return indent_cmd.indent_visual(ctx.visual_start[0], ctx.visual_end[0], direction)

            # Check if this is linewise operation (>>, <<)
            if ctx.extra_args.get("linewise"):
                row = ctx.buffer.get_cursor()[0]
                return indent_cmd.indent_lines(row, ctx.count, direction)

            # Otherwise wait for motion
            return False

        return handler

    # Register indent operators
    for keys, name, direction, desc in [
        (">", "indent_right", "right", "Indent right"),
        ("<", "indent_left", "left", "Indent left"),
    ]:
        registry.register(
            CommandDef(
                keys=keys,
                name=name,
                type=CommandType.OPERATOR,
                handler=make_indent_handler(direction),
                modes=normal_modes | visual_modes,
                operator_pending=True,
                description=desc,
            )
        )

        # Also register double versions (>>, <<) for linewise
        def make_linewise_indent_handler(dir: str):
            def handler(ctx: "CommandContext") -> bool:
                indent_cmd = IndentCommand(ctx.buffer)
                row = ctx.buffer.get_cursor()[0]
                return indent_cmd.indent_lines(row, ctx.count, dir)

            return handler

        registry.register(
            CommandDef(
                keys=keys + keys,  # >>, <<
                name=f"{name}_line",
                type=CommandType.ACTION,
                handler=make_linewise_indent_handler(direction),
                modes=normal_modes,
                description=f"{desc} (line)",
            )
        )

    # Auto-indent operator (=)
    def auto_indent_handler(ctx: "CommandContext") -> bool:
        indent_cmd = IndentCommand(ctx.buffer)

        # Check if we have a visual selection
        if ctx.modes.current_mode in visual_modes and ctx.visual_start and ctx.visual_end:
            return indent_cmd.auto_indent_visual(ctx.visual_start[0], ctx.visual_end[0])

        # Check if this is linewise operation (==)
        if ctx.extra_args.get("linewise"):
            row = ctx.buffer.get_cursor()[0]
            return indent_cmd.auto_indent_lines(row, ctx.count)

        # Otherwise wait for motion
        return False

    registry.register(
        CommandDef(
            keys="=",
            name="auto_indent",
            type=CommandType.OPERATOR,
            handler=auto_indent_handler,
            modes=normal_modes | visual_modes,
            operator_pending=True,
            description="Auto-indent",
        )
    )

    # Register == for linewise auto-indent
    def auto_indent_line_handler(ctx: "CommandContext") -> bool:
        indent_cmd = IndentCommand(ctx.buffer)
        row = ctx.buffer.get_cursor()[0]
        return indent_cmd.auto_indent_lines(row, ctx.count)

    registry.register(
        CommandDef(
            keys="==",
            name="auto_indent_line",
            type=CommandType.ACTION,
            handler=auto_indent_line_handler,
            modes=normal_modes,
            description="Auto-indent line",
        )
    )

    # Repeat command (.)
    if repeat_manager:

        def repeat_handler(ctx: "CommandContext") -> bool:
            # Add dispatcher to context if available
            if hasattr(ctx, "extra_args") and "dispatcher" in ctx.extra_args:
                ctx.dispatcher = ctx.extra_args["dispatcher"]

            repeat_cmd = RepeatCommand(ctx.buffer, repeat_manager)
            return repeat_cmd.execute_repeat(ctx)

        registry.register(
            CommandDef(
                keys=".",
                name="repeat",
                type=CommandType.ACTION,
                handler=repeat_handler,
                modes=normal_modes,
                repeatable=False,  # Don't repeat the repeat command itself
                description="Repeat last change",
            )
        )
