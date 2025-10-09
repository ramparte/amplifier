"""Motion command implementations for vi editor.

This module implements all movement commands that can be used standalone
or as targets for operators (e.g., 'd2w' deletes 2 words).
"""

from typing import TYPE_CHECKING

from .registry import CommandContext
from .registry import CommandDef
from .registry import CommandMode
from .registry import CommandType

if TYPE_CHECKING:
    from ..buffer.core import TextBuffer


def register_motion_commands(registry):
    """Register all motion commands with the registry.

    Args:
        registry: CommandRegistry instance to register commands with
    """
    # Character motions
    registry.register(
        CommandDef(
            keys="h",
            name="move_left",
            type=CommandType.MOTION,
            handler=move_left,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move cursor left",
        )
    )

    registry.register(
        CommandDef(
            keys="l",
            name="move_right",
            type=CommandType.MOTION,
            handler=move_right,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move cursor right",
        )
    )

    # Line motions
    registry.register(
        CommandDef(
            keys="j",
            name="move_down",
            type=CommandType.MOTION,
            handler=move_down,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move cursor down",
        )
    )

    registry.register(
        CommandDef(
            keys="k",
            name="move_up",
            type=CommandType.MOTION,
            handler=move_up,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move cursor up",
        )
    )

    # Line position motions
    registry.register(
        CommandDef(
            keys="0",
            name="move_line_start",
            type=CommandType.MOTION,
            handler=move_line_start,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            takes_count=False,
            description="Move to start of line",
        )
    )

    registry.register(
        CommandDef(
            keys="^",
            name="move_first_non_blank",
            type=CommandType.MOTION,
            handler=move_first_non_blank,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            takes_count=False,
            description="Move to first non-blank character",
        )
    )

    registry.register(
        CommandDef(
            keys="$",
            name="move_line_end",
            type=CommandType.MOTION,
            handler=move_line_end,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move to end of line",
        )
    )

    # Word motions
    registry.register(
        CommandDef(
            keys="w",
            name="word_forward",
            type=CommandType.MOTION,
            handler=word_forward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move forward by word",
        )
    )

    registry.register(
        CommandDef(
            keys="W",
            name="WORD_forward",
            type=CommandType.MOTION,
            handler=word_forward_big,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move forward by WORD",
        )
    )

    registry.register(
        CommandDef(
            keys="b",
            name="word_backward",
            type=CommandType.MOTION,
            handler=word_backward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move backward by word",
        )
    )

    registry.register(
        CommandDef(
            keys="B",
            name="WORD_backward",
            type=CommandType.MOTION,
            handler=word_backward_big,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move backward by WORD",
        )
    )

    registry.register(
        CommandDef(
            keys="e",
            name="word_end",
            type=CommandType.MOTION,
            handler=word_end,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move to end of word",
        )
    )

    registry.register(
        CommandDef(
            keys="E",
            name="WORD_end",
            type=CommandType.MOTION,
            handler=word_end_big,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move to end of WORD",
        )
    )

    # File motions
    registry.register(
        CommandDef(
            keys="G",
            name="goto_line",
            type=CommandType.MOTION,
            handler=goto_line,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Go to line (default: last)",
        )
    )

    registry.register(
        CommandDef(
            keys="gg",
            name="goto_first_line",
            type=CommandType.MOTION,
            handler=goto_first_line,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            takes_count=False,
            description="Go to first line",
        )
    )

    # Paragraph motions
    registry.register(
        CommandDef(
            keys="{",
            name="paragraph_backward",
            type=CommandType.MOTION,
            handler=paragraph_backward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move backward by paragraph",
        )
    )

    registry.register(
        CommandDef(
            keys="}",
            name="paragraph_forward",
            type=CommandType.MOTION,
            handler=paragraph_forward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move forward by paragraph",
        )
    )

    # Search motions
    registry.register(
        CommandDef(
            keys="f",
            name="find_char_forward",
            type=CommandType.MOTION,
            handler=find_char_forward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Find character forward",
        )
    )

    registry.register(
        CommandDef(
            keys="F",
            name="find_char_backward",
            type=CommandType.MOTION,
            handler=find_char_backward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Find character backward",
        )
    )

    registry.register(
        CommandDef(
            keys="t",
            name="till_char_forward",
            type=CommandType.MOTION,
            handler=till_char_forward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move till character forward",
        )
    )

    registry.register(
        CommandDef(
            keys="T",
            name="till_char_backward",
            type=CommandType.MOTION,
            handler=till_char_backward,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            description="Move till character backward",
        )
    )

    # Matching bracket
    registry.register(
        CommandDef(
            keys="%",
            name="match_bracket",
            type=CommandType.MOTION,
            handler=match_bracket,
            modes={CommandMode.NORMAL, CommandMode.VISUAL, CommandMode.OPERATOR_PENDING},
            motion=True,
            takes_count=False,
            description="Jump to matching bracket",
        )
    )


# Motion implementations


def move_left(ctx: CommandContext) -> bool:
    """Move cursor left."""
    ctx.buffer.move_cursor_relative("h", ctx.count)
    return True


def move_right(ctx: CommandContext) -> bool:
    """Move cursor right."""
    ctx.buffer.move_cursor_relative("l", ctx.count)
    return True


def move_down(ctx: CommandContext) -> bool:
    """Move cursor down."""
    ctx.buffer.move_cursor_relative("j", ctx.count)
    return True


def move_up(ctx: CommandContext) -> bool:
    """Move cursor up."""
    ctx.buffer.move_cursor_relative("k", ctx.count)
    return True


def move_line_start(ctx: CommandContext) -> bool:
    """Move to start of line."""
    row, _ = ctx.buffer.get_cursor()
    ctx.buffer.set_cursor(row, 0)
    return True


def move_first_non_blank(ctx: CommandContext) -> bool:
    """Move to first non-blank character of line."""
    row, _ = ctx.buffer.get_cursor()
    lines = ctx.buffer.get_lines()
    if row < len(lines):
        line = lines[row]
        col = 0
        for i, char in enumerate(line):
            if not char.isspace():
                col = i
                break
        ctx.buffer.set_cursor(row, col)
    return True


def move_line_end(ctx: CommandContext) -> bool:
    """Move to end of line."""
    row, _ = ctx.buffer.get_cursor()
    lines = ctx.buffer.get_lines()
    if row < len(lines):
        line_len = len(lines[row])
        # Vi behavior: position at last character, not past it
        ctx.buffer.set_cursor(row, max(0, line_len - 1) if ctx.count == 1 else line_len)
    return True


def word_forward(ctx: CommandContext) -> bool:
    """Move forward by words."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, col = buffer.get_cursor()
        lines = buffer.get_lines()

        if row >= len(lines):
            break

        line = lines[row]

        # Skip current word
        while col < len(line) and not line[col].isspace() and line[col].isalnum():
            col += 1

        # Skip punctuation
        while col < len(line) and not line[col].isspace() and not line[col].isalnum():
            col += 1

        # Skip whitespace
        while col < len(line) and line[col].isspace():
            col += 1

        # If at end of line, move to next line
        if col >= len(line) and row < len(lines) - 1:
            row += 1
            col = 0
            # Skip leading whitespace on new line
            if row < len(lines):
                line = lines[row]
                while col < len(line) and line[col].isspace():
                    col += 1

        buffer.set_cursor(row, col)
    return True


def word_forward_big(ctx: CommandContext) -> bool:
    """Move forward by WORDs (whitespace-delimited)."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, col = buffer.get_cursor()
        lines = buffer.get_lines()

        if row >= len(lines):
            break

        line = lines[row]

        # Skip current WORD
        while col < len(line) and not line[col].isspace():
            col += 1

        # Skip whitespace
        while col < len(line) and line[col].isspace():
            col += 1

        # If at end of line, move to next line
        if col >= len(line) and row < len(lines) - 1:
            row += 1
            col = 0
            # Skip leading whitespace on new line
            if row < len(lines):
                line = lines[row]
                while col < len(line) and line[col].isspace():
                    col += 1

        buffer.set_cursor(row, col)
    return True


def word_backward(ctx: CommandContext) -> bool:
    """Move backward by words."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, col = buffer.get_cursor()
        lines = buffer.get_lines()

        if row >= len(lines):
            break

        # Move back one position first
        if col > 0:
            col -= 1
        elif row > 0:
            row -= 1
            col = len(lines[row]) - 1 if row < len(lines) else 0

        if row < len(lines):
            line = lines[row]

            # Skip whitespace backwards
            while col > 0 and line[col].isspace():
                col -= 1

            # Skip word backwards (alphanumeric)
            if line[col].isalnum():
                while col > 0 and line[col - 1].isalnum():
                    col -= 1
            # Skip punctuation backwards
            else:
                while col > 0 and not line[col - 1].isspace() and not line[col - 1].isalnum():
                    col -= 1

        buffer.set_cursor(row, col)
    return True


def word_backward_big(ctx: CommandContext) -> bool:
    """Move backward by WORDs (whitespace-delimited)."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, col = buffer.get_cursor()
        lines = buffer.get_lines()

        if row >= len(lines):
            break

        # Move back one position first
        if col > 0:
            col -= 1
        elif row > 0:
            row -= 1
            col = len(lines[row]) - 1 if row < len(lines) else 0

        if row < len(lines):
            line = lines[row]

            # Skip whitespace backwards
            while col > 0 and line[col].isspace():
                col -= 1

            # Skip WORD backwards
            while col > 0 and not line[col - 1].isspace():
                col -= 1

        buffer.set_cursor(row, col)
    return True


def word_end(ctx: CommandContext) -> bool:
    """Move to end of word."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, col = buffer.get_cursor()
        lines = buffer.get_lines()

        if row >= len(lines):
            break

        line = lines[row]

        # Move forward one if at start of word
        if col < len(line) - 1:
            col += 1

        # Skip whitespace
        while col < len(line) and line[col].isspace():
            col += 1

        # Skip to end of current word (alphanumeric)
        if col < len(line) and line[col].isalnum():
            while col < len(line) - 1 and line[col + 1].isalnum():
                col += 1
        # Skip to end of punctuation
        elif col < len(line):
            while col < len(line) - 1 and not line[col + 1].isspace() and not line[col + 1].isalnum():
                col += 1

        buffer.set_cursor(row, col)
    return True


def word_end_big(ctx: CommandContext) -> bool:
    """Move to end of WORD (whitespace-delimited)."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, col = buffer.get_cursor()
        lines = buffer.get_lines()

        if row >= len(lines):
            break

        line = lines[row]

        # Move forward one if at start of WORD
        if col < len(line) - 1:
            col += 1

        # Skip whitespace
        while col < len(line) and line[col].isspace():
            col += 1

        # Skip to end of current WORD
        while col < len(line) - 1 and not line[col + 1].isspace():
            col += 1

        buffer.set_cursor(row, col)
    return True


def goto_line(ctx: CommandContext) -> bool:
    """Go to specific line number (G command)."""
    lines = ctx.buffer.get_lines()
    if ctx.count == 1:  # No count means last line
        target_row = len(lines) - 1
    else:
        target_row = min(ctx.count - 1, len(lines) - 1)
    ctx.buffer.set_cursor(max(0, target_row), 0)
    return True


def goto_first_line(ctx: CommandContext) -> bool:
    """Go to first line (gg command)."""
    ctx.buffer.set_cursor(0, 0)
    return True


def paragraph_backward(ctx: CommandContext) -> bool:
    """Move backward by paragraph."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, _ = buffer.get_cursor()
        lines = buffer.get_lines()

        # Skip current paragraph
        while row > 0 and lines[row - 1].strip():
            row -= 1

        # Skip blank lines
        while row > 0 and not lines[row - 1].strip():
            row -= 1

        buffer.set_cursor(row, 0)
    return True


def paragraph_forward(ctx: CommandContext) -> bool:
    """Move forward by paragraph."""
    buffer: TextBuffer = ctx.buffer
    for _ in range(ctx.count):
        row, _ = buffer.get_cursor()
        lines = buffer.get_lines()

        # Skip current paragraph
        while row < len(lines) - 1 and lines[row].strip():
            row += 1

        # Skip blank lines
        while row < len(lines) - 1 and not lines[row].strip():
            row += 1

        buffer.set_cursor(row, 0)
    return True


def find_char_forward(ctx: CommandContext) -> bool:
    """Find character forward (f command)."""
    # This needs additional input - store state for next key
    ctx.extra_args["pending_find"] = "f"
    return True


def find_char_backward(ctx: CommandContext) -> bool:
    """Find character backward (F command)."""
    # This needs additional input - store state for next key
    ctx.extra_args["pending_find"] = "F"
    return True


def till_char_forward(ctx: CommandContext) -> bool:
    """Move till character forward (t command)."""
    # This needs additional input - store state for next key
    ctx.extra_args["pending_find"] = "t"
    return True


def till_char_backward(ctx: CommandContext) -> bool:
    """Move till character backward (T command)."""
    # This needs additional input - store state for next key
    ctx.extra_args["pending_find"] = "T"
    return True


def match_bracket(ctx: CommandContext) -> bool:
    """Jump to matching bracket."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    lines = buffer.get_lines()

    if row >= len(lines):
        return False

    line = lines[row]
    if col >= len(line):
        return False

    char = line[col]

    # Define matching pairs
    brackets = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{"}

    if char not in brackets:
        return False

    match = brackets[char]
    forward = char in "([{"

    # Search for matching bracket
    count = 1
    if forward:
        col += 1
        while row < len(lines):
            while col < len(lines[row]):
                if lines[row][col] == char:
                    count += 1
                elif lines[row][col] == match:
                    count -= 1
                    if count == 0:
                        buffer.set_cursor(row, col)
                        return True
                col += 1
            row += 1
            col = 0
    else:
        col -= 1
        while row >= 0:
            while col >= 0:
                if lines[row][col] == char:
                    count += 1
                elif lines[row][col] == match:
                    count -= 1
                    if count == 0:
                        buffer.set_cursor(row, col)
                        return True
                col -= 1
            row -= 1
            if row >= 0:
                col = len(lines[row]) - 1

    return False
