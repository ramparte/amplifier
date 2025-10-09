"""Operator command implementations for vi editor.

Operators are commands that act on text objects or motions.
Examples: d (delete), c (change), y (yank), = (indent), > (indent right), < (indent left)
"""

from typing import TYPE_CHECKING

from .registry import CommandContext
from .registry import CommandDef
from .registry import CommandMode
from .registry import CommandType

if TYPE_CHECKING:
    from ..buffer.core import TextBuffer


def register_operator_commands(registry):
    """Register all operator commands with the registry.

    Args:
        registry: CommandRegistry instance to register commands with
    """
    # Delete operator
    registry.register(
        CommandDef(
            keys="d",
            name="delete",
            type=CommandType.OPERATOR,
            handler=delete_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            takes_register=True,
            description="Delete text",
        )
    )

    # Delete line (dd)
    registry.register(
        CommandDef(
            keys="dd",
            name="delete_line",
            type=CommandType.ACTION,
            handler=delete_line,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Delete entire line",
        )
    )

    # Delete to end of line (D)
    registry.register(
        CommandDef(
            keys="D",
            name="delete_to_eol",
            type=CommandType.ACTION,
            handler=delete_to_eol,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Delete to end of line",
        )
    )

    # Change operator
    registry.register(
        CommandDef(
            keys="c",
            name="change",
            type=CommandType.OPERATOR,
            handler=change_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            takes_register=True,
            description="Change text",
        )
    )

    # Change line (cc)
    registry.register(
        CommandDef(
            keys="cc",
            name="change_line",
            type=CommandType.ACTION,
            handler=change_line,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Change entire line",
        )
    )

    # Change to end of line (C)
    registry.register(
        CommandDef(
            keys="C",
            name="change_to_eol",
            type=CommandType.ACTION,
            handler=change_to_eol,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Change to end of line",
        )
    )

    # Yank operator
    registry.register(
        CommandDef(
            keys="y",
            name="yank",
            type=CommandType.OPERATOR,
            handler=yank_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            takes_register=True,
            description="Yank (copy) text",
        )
    )

    # Yank line (yy)
    registry.register(
        CommandDef(
            keys="yy",
            name="yank_line",
            type=CommandType.ACTION,
            handler=yank_line,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Yank entire line",
        )
    )

    # Yank to end of line (Y)
    registry.register(
        CommandDef(
            keys="Y",
            name="yank_line_alt",
            type=CommandType.ACTION,
            handler=yank_line,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Yank entire line (same as yy)",
        )
    )

    # Indent operators
    registry.register(
        CommandDef(
            keys=">",
            name="indent_right",
            type=CommandType.OPERATOR,
            handler=indent_right_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            description="Indent right",
        )
    )

    registry.register(
        CommandDef(
            keys="<",
            name="indent_left",
            type=CommandType.OPERATOR,
            handler=indent_left_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            description="Indent left",
        )
    )

    # Format operator
    registry.register(
        CommandDef(
            keys="=",
            name="format",
            type=CommandType.OPERATOR,
            handler=format_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            description="Format text",
        )
    )

    # Case operators
    registry.register(
        CommandDef(
            keys="~",
            name="toggle_case",
            type=CommandType.ACTION,
            handler=toggle_case,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            description="Toggle case",
        )
    )

    registry.register(
        CommandDef(
            keys="gu",
            name="lowercase",
            type=CommandType.OPERATOR,
            handler=lowercase_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            description="Make lowercase",
        )
    )

    registry.register(
        CommandDef(
            keys="gU",
            name="uppercase",
            type=CommandType.OPERATOR,
            handler=uppercase_operator,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            operator_pending=True,
            description="Make uppercase",
        )
    )

    # Join lines
    registry.register(
        CommandDef(
            keys="J",
            name="join_lines",
            type=CommandType.ACTION,
            handler=join_lines,
            modes={CommandMode.NORMAL},
            description="Join lines",
        )
    )

    # Replace character
    registry.register(
        CommandDef(
            keys="r",
            name="replace_char",
            type=CommandType.ACTION,
            handler=replace_char,
            modes={CommandMode.NORMAL},
            description="Replace character",
        )
    )

    # Delete character
    registry.register(
        CommandDef(
            keys="x",
            name="delete_char",
            type=CommandType.ACTION,
            handler=delete_char,
            modes={CommandMode.NORMAL, CommandMode.VISUAL},
            takes_register=True,
            description="Delete character",
        )
    )

    # Delete character before cursor
    registry.register(
        CommandDef(
            keys="X",
            name="delete_char_before",
            type=CommandType.ACTION,
            handler=delete_char_before,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Delete character before cursor",
        )
    )

    # Substitute character
    registry.register(
        CommandDef(
            keys="s",
            name="substitute_char",
            type=CommandType.ACTION,
            handler=substitute_char,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Substitute character",
        )
    )

    # Substitute line
    registry.register(
        CommandDef(
            keys="S",
            name="substitute_line",
            type=CommandType.ACTION,
            handler=substitute_line,
            modes={CommandMode.NORMAL},
            takes_register=True,
            description="Substitute entire line",
        )
    )


# Operator implementations


def delete_operator(ctx: CommandContext) -> bool:
    """Delete operator - needs a motion to complete."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        # Operator pending mode - wait for motion
        return True

    # If we have visual range from text object/motion, delete that range
    if ctx.visual_start and ctx.visual_end:
        buffer = ctx.buffer
        start_row, start_col = ctx.visual_start
        end_row, end_col = ctx.visual_end

        # Ensure proper ordering
        if (start_row, start_col) > (end_row, end_col):
            start_row, start_col, end_row, end_col = end_row, end_col, start_row, start_col

        # Delete the selected range
        lines = buffer.get_lines()

        if start_row == end_row:
            # Single line deletion
            if start_row < len(lines):
                line = lines[start_row]
                buffer._lines[start_row] = line[:start_col] + line[end_col + 1 :]
                buffer.set_cursor(start_row, start_col)
        else:
            # Multi-line deletion
            if start_row < len(lines) and end_row < len(lines):
                # Combine first and last lines
                first_part = lines[start_row][:start_col]
                last_part = lines[end_row][end_col + 1 :] if end_col < len(lines[end_row]) - 1 else ""
                buffer._lines[start_row] = first_part + last_part

                # Delete middle lines
                for _ in range(end_row - start_row):
                    del buffer._lines[start_row + 1]

                buffer.set_cursor(start_row, start_col)

        return True

    # Fallback message if no visual range
    ctx.renderer.show_message(f"Delete with motion: {motion}")
    return True


def delete_line(ctx: CommandContext) -> bool:
    """Delete entire line(s)."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        buffer.delete_line()
    return True


def delete_to_eol(ctx: CommandContext) -> bool:
    """Delete from cursor to end of line."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    lines = buffer.get_lines()

    if row < len(lines):
        line = lines[row]
        # Delete from cursor to end
        buffer._lines[row] = line[:col]
    return True


def change_operator(ctx: CommandContext) -> bool:
    """Change operator - deletes text and enters insert mode."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        # Operator pending mode - wait for motion
        return True

    # If we have visual range from text object/motion, delete that range
    if ctx.visual_start and ctx.visual_end:
        # First delete the range (same as delete_operator)
        buffer = ctx.buffer
        start_row, start_col = ctx.visual_start
        end_row, end_col = ctx.visual_end

        # Ensure proper ordering
        if (start_row, start_col) > (end_row, end_col):
            start_row, start_col, end_row, end_col = end_row, end_col, start_row, start_col

        # Delete the selected range
        lines = buffer.get_lines()

        if start_row == end_row:
            # Single line deletion
            if start_row < len(lines):
                line = lines[start_row]
                buffer._lines[start_row] = line[:start_col] + line[end_col + 1 :]
                buffer.set_cursor(start_row, start_col)
        else:
            # Multi-line deletion
            if start_row < len(lines) and end_row < len(lines):
                # Combine first and last lines
                first_part = lines[start_row][:start_col]
                last_part = lines[end_row][end_col + 1 :] if end_col < len(lines[end_row]) - 1 else ""
                buffer._lines[start_row] = first_part + last_part

                # Delete middle lines
                for _ in range(end_row - start_row):
                    del buffer._lines[start_row + 1]

                buffer.set_cursor(start_row, start_col)

        # Enter insert mode
        ctx.modes.to_insert()
        return True

    # Fallback message if no visual range
    ctx.renderer.show_message(f"Change with motion: {motion}")
    ctx.modes.to_insert()
    return True


def change_line(ctx: CommandContext) -> bool:
    """Change entire line(s)."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        buffer.delete_line()
    # Open new line and enter insert mode
    buffer.insert_char("\n")
    buffer.move_cursor_up()
    ctx.modes.to_insert()
    return True


def change_to_eol(ctx: CommandContext) -> bool:
    """Change from cursor to end of line."""
    delete_to_eol(ctx)
    ctx.modes.to_insert()
    return True


def yank_operator(ctx: CommandContext) -> bool:
    """Yank operator - copies text to register."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        # Operator pending mode - wait for motion
        return True

    # If we have visual range from text object/motion, yank that range
    if ctx.visual_start and ctx.visual_end:
        buffer = ctx.buffer
        start_row, start_col = ctx.visual_start
        end_row, end_col = ctx.visual_end

        # Ensure proper ordering
        if (start_row, start_col) > (end_row, end_col):
            start_row, start_col, end_row, end_col = end_row, end_col, start_row, start_col

        # Extract the text to yank
        lines = buffer.get_lines()
        yanked_text = ""

        if start_row == end_row:
            # Single line yank
            if start_row < len(lines):
                line = lines[start_row]
                yanked_text = line[start_col : end_col + 1]
        else:
            # Multi-line yank
            if start_row < len(lines) and end_row < len(lines):
                # First line
                yanked_text = lines[start_row][start_col:] + "\n"
                # Middle lines
                for row in range(start_row + 1, end_row):
                    if row < len(lines):
                        yanked_text += lines[row] + "\n"
                # Last line
                yanked_text += lines[end_row][: end_col + 1]

        # Store in register (would need actual register implementation)
        ctx.renderer.show_message(f"Yanked {len(yanked_text)} characters")
        return True

    # Fallback message if no visual range
    ctx.renderer.show_message(f"Yank with motion: {motion}")
    return True


def yank_line(ctx: CommandContext) -> bool:
    """Yank entire line(s)."""
    # Placeholder - real implementation would copy to register
    ctx.renderer.show_message(f"Yanked {ctx.count} line(s)")
    return True


def indent_right_operator(ctx: CommandContext) -> bool:
    """Indent right operator."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        return True

    # Placeholder
    ctx.renderer.show_message(f"Indent right with motion: {motion}")
    return True


def indent_left_operator(ctx: CommandContext) -> bool:
    """Indent left operator."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        return True

    # Placeholder
    ctx.renderer.show_message(f"Indent left with motion: {motion}")
    return True


def format_operator(ctx: CommandContext) -> bool:
    """Format operator."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        return True

    # Placeholder
    ctx.renderer.show_message(f"Format with motion: {motion}")
    return True


def toggle_case(ctx: CommandContext) -> bool:
    """Toggle case of character(s)."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    lines = buffer.get_lines()

    if row < len(lines):
        line = lines[row]
        for i in range(ctx.count):
            if col + i < len(line):
                char = line[col + i]
                if char.isupper():
                    line = line[: col + i] + char.lower() + line[col + i + 1 :]
                elif char.islower():
                    line = line[: col + i] + char.upper() + line[col + i + 1 :]
        buffer._lines[row] = line
        # Move cursor forward
        buffer.move_cursor_right(ctx.count)
    return True


def lowercase_operator(ctx: CommandContext) -> bool:
    """Lowercase operator."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        return True

    # Placeholder
    ctx.renderer.show_message(f"Lowercase with motion: {motion}")
    return True


def uppercase_operator(ctx: CommandContext) -> bool:
    """Uppercase operator."""
    motion = ctx.extra_args.get("motion")
    if not motion:
        return True

    # Placeholder
    ctx.renderer.show_message(f"Uppercase with motion: {motion}")
    return True


def join_lines(ctx: CommandContext) -> bool:
    """Join lines together."""
    buffer: TextBuffer = ctx.buffer
    row, _ = buffer.get_cursor()
    lines = buffer.get_lines()

    for _ in range(ctx.count):
        if row < len(lines) - 1:
            # Join current line with next
            buffer._lines[row] = buffer._lines[row].rstrip() + " " + buffer._lines[row + 1].lstrip()
            del buffer._lines[row + 1]
    return True


def replace_char(ctx: CommandContext) -> bool:
    """Replace character under cursor - needs next key input."""
    # This needs additional input handling
    ctx.extra_args["pending_replace"] = True
    return True


def delete_char(ctx: CommandContext) -> bool:
    """Delete character(s) at cursor."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        buffer.delete_char()
    return True


def delete_char_before(ctx: CommandContext) -> bool:
    """Delete character(s) before cursor."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        buffer.move_cursor_left()
        buffer.delete_char()
    return True


def substitute_char(ctx: CommandContext) -> bool:
    """Substitute character(s) - delete and enter insert mode."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        buffer.delete_char()
    ctx.modes.to_insert()
    return True


def substitute_line(ctx: CommandContext) -> bool:
    """Substitute entire line - delete and enter insert mode."""
    buffer: TextBuffer = ctx.buffer
    row, _ = buffer.get_cursor()
    lines = buffer.get_lines()

    if row < len(lines):
        # Clear the line but keep it
        buffer._lines[row] = ""
        buffer.set_cursor(row, 0)
    ctx.modes.to_insert()
    return True
