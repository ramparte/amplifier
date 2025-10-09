"""Text object implementations for vi editor.

Text objects define regions of text that operators can act upon.
Examples: iw (inner word), aw (a word), i" (inner quotes), a( (a parentheses block)
"""

from typing import TYPE_CHECKING

from .registry import CommandContext
from .registry import CommandDef
from .registry import CommandMode
from .registry import CommandType

if TYPE_CHECKING:
    from ..buffer.core import TextBuffer


def register_text_objects(registry):
    """Register all text object commands with the registry.

    Args:
        registry: CommandRegistry instance to register commands with
    """
    # Word text objects
    registry.register(
        CommandDef(
            keys="iw",
            name="inner_word",
            type=CommandType.TEXT_OBJECT,
            handler=inner_word,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner word",
        )
    )

    registry.register(
        CommandDef(
            keys="aw",
            name="a_word",
            type=CommandType.TEXT_OBJECT,
            handler=a_word,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A word (includes whitespace)",
        )
    )

    registry.register(
        CommandDef(
            keys="iW",
            name="inner_WORD",
            type=CommandType.TEXT_OBJECT,
            handler=inner_word_big,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner WORD",
        )
    )

    registry.register(
        CommandDef(
            keys="aW",
            name="a_WORD",
            type=CommandType.TEXT_OBJECT,
            handler=a_word_big,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A WORD (includes whitespace)",
        )
    )

    # Sentence text objects
    registry.register(
        CommandDef(
            keys="is",
            name="inner_sentence",
            type=CommandType.TEXT_OBJECT,
            handler=inner_sentence,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner sentence",
        )
    )

    registry.register(
        CommandDef(
            keys="as",
            name="a_sentence",
            type=CommandType.TEXT_OBJECT,
            handler=a_sentence,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A sentence",
        )
    )

    # Paragraph text objects
    registry.register(
        CommandDef(
            keys="ip",
            name="inner_paragraph",
            type=CommandType.TEXT_OBJECT,
            handler=inner_paragraph,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner paragraph",
        )
    )

    registry.register(
        CommandDef(
            keys="ap",
            name="a_paragraph",
            type=CommandType.TEXT_OBJECT,
            handler=a_paragraph,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A paragraph",
        )
    )

    # Quote text objects
    registry.register(
        CommandDef(
            keys='i"',
            name="inner_double_quotes",
            type=CommandType.TEXT_OBJECT,
            handler=inner_double_quotes,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner double quotes",
        )
    )

    registry.register(
        CommandDef(
            keys='a"',
            name="a_double_quotes",
            type=CommandType.TEXT_OBJECT,
            handler=a_double_quotes,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A double quotes (includes quotes)",
        )
    )

    registry.register(
        CommandDef(
            keys="i'",
            name="inner_single_quotes",
            type=CommandType.TEXT_OBJECT,
            handler=inner_single_quotes,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner single quotes",
        )
    )

    registry.register(
        CommandDef(
            keys="a'",
            name="a_single_quotes",
            type=CommandType.TEXT_OBJECT,
            handler=a_single_quotes,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A single quotes (includes quotes)",
        )
    )

    registry.register(
        CommandDef(
            keys="i`",
            name="inner_backticks",
            type=CommandType.TEXT_OBJECT,
            handler=inner_backticks,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner backticks",
        )
    )

    registry.register(
        CommandDef(
            keys="a`",
            name="a_backticks",
            type=CommandType.TEXT_OBJECT,
            handler=a_backticks,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A backticks (includes backticks)",
        )
    )

    # Bracket/parentheses text objects
    registry.register(
        CommandDef(
            keys="i(",
            name="inner_parens",
            type=CommandType.TEXT_OBJECT,
            handler=inner_parens,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner parentheses",
        )
    )

    registry.register(
        CommandDef(
            keys="a(",
            name="a_parens",
            type=CommandType.TEXT_OBJECT,
            handler=a_parens,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A parentheses (includes parens)",
        )
    )

    registry.register(
        CommandDef(
            keys="i)",
            name="inner_parens_alt",
            type=CommandType.TEXT_OBJECT,
            handler=inner_parens,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner parentheses",
        )
    )

    registry.register(
        CommandDef(
            keys="a)",
            name="a_parens_alt",
            type=CommandType.TEXT_OBJECT,
            handler=a_parens,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A parentheses (includes parens)",
        )
    )

    # Square brackets
    registry.register(
        CommandDef(
            keys="i[",
            name="inner_brackets",
            type=CommandType.TEXT_OBJECT,
            handler=inner_brackets,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner brackets",
        )
    )

    registry.register(
        CommandDef(
            keys="a[",
            name="a_brackets",
            type=CommandType.TEXT_OBJECT,
            handler=a_brackets,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A brackets (includes brackets)",
        )
    )

    # Curly braces
    registry.register(
        CommandDef(
            keys="i{",
            name="inner_braces",
            type=CommandType.TEXT_OBJECT,
            handler=inner_braces,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner braces",
        )
    )

    registry.register(
        CommandDef(
            keys="a{",
            name="a_braces",
            type=CommandType.TEXT_OBJECT,
            handler=a_braces,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A braces (includes braces)",
        )
    )

    # Angle brackets
    registry.register(
        CommandDef(
            keys="i<",
            name="inner_angle",
            type=CommandType.TEXT_OBJECT,
            handler=inner_angle,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner angle brackets",
        )
    )

    registry.register(
        CommandDef(
            keys="a<",
            name="a_angle",
            type=CommandType.TEXT_OBJECT,
            handler=a_angle,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A angle brackets (includes brackets)",
        )
    )

    # Tag text objects (HTML/XML)
    registry.register(
        CommandDef(
            keys="it",
            name="inner_tag",
            type=CommandType.TEXT_OBJECT,
            handler=inner_tag,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="Inner tag",
        )
    )

    registry.register(
        CommandDef(
            keys="at",
            name="a_tag",
            type=CommandType.TEXT_OBJECT,
            handler=a_tag,
            modes={CommandMode.OPERATOR_PENDING, CommandMode.VISUAL},
            motion=True,
            description="A tag (includes tags)",
        )
    )


# Helper functions


def find_word_boundaries(buffer: "TextBuffer", row: int, col: int) -> tuple[int, int]:
    """Find the start and end of a word at given position."""
    lines = buffer.get_lines()
    if row >= len(lines):
        return col, col

    line = lines[row]
    if col >= len(line):
        return col, col

    # Find word start
    start = col
    while start > 0 and line[start - 1].isalnum():
        start -= 1

    # Find word end
    end = col
    while end < len(line) and line[end].isalnum():
        end += 1

    return start, end


def find_word_boundaries_big(buffer: "TextBuffer", row: int, col: int) -> tuple[int, int]:
    """Find the start and end of a WORD (whitespace-delimited) at given position."""
    lines = buffer.get_lines()
    if row >= len(lines):
        return col, col

    line = lines[row]
    if col >= len(line):
        return col, col

    # Find WORD start
    start = col
    while start > 0 and not line[start - 1].isspace():
        start -= 1

    # Find WORD end
    end = col
    while end < len(line) and not line[end].isspace():
        end += 1

    return start, end


def find_matching_quote(buffer: "TextBuffer", row: int, col: int, quote: str) -> tuple[int, int] | None:
    """Find matching quote boundaries."""
    lines = buffer.get_lines()
    if row >= len(lines):
        return None

    line = lines[row]

    # Search backward for opening quote
    start = col
    while start >= 0:
        if line[start] == quote:
            break
        start -= 1
    else:
        return None

    # Search forward for closing quote
    end = col
    if end == start:
        end += 1  # Skip the opening quote
    while end < len(line):
        if line[end] == quote:
            break
        end += 1
    else:
        return None

    return start, end + 1


def find_matching_bracket(
    buffer: "TextBuffer", row: int, col: int, open_b: str, close_b: str
) -> tuple[tuple[int, int], tuple[int, int]] | None:
    """Find matching bracket boundaries, returns ((start_row, start_col), (end_row, end_col))."""
    lines = buffer.get_lines()
    if row >= len(lines):
        return None

    # Search for opening bracket
    count = 0
    start_row, start_col = row, col

    # First, check if we're inside brackets
    for r in range(row, -1, -1):
        line = lines[r]
        c = len(line) - 1 if r < row else col
        while c >= 0:
            if line[c] == close_b:
                count += 1
            elif line[c] == open_b:
                if count == 0:
                    start_row, start_col = r, c
                    break
                count -= 1
            c -= 1
        if start_row != row or start_col != col:
            break

    if start_row == row and start_col == col:
        return None  # No opening bracket found

    # Now find the closing bracket
    count = 1
    end_row, end_col = start_row, start_col + 1

    for r in range(start_row, len(lines)):
        line = lines[r]
        c = start_col + 1 if r == start_row else 0
        while c < len(line):
            if line[c] == open_b:
                count += 1
            elif line[c] == close_b:
                count -= 1
                if count == 0:
                    end_row, end_col = r, c
                    return ((start_row, start_col), (end_row, end_col))
            c += 1

    return None


# Text object implementations


def inner_word(ctx: CommandContext) -> bool:
    """Select inner word."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    start, end = find_word_boundaries(buffer, row, col)

    # Set selection
    ctx.visual_start = (row, start)
    ctx.visual_end = (row, end - 1)
    return True


def a_word(ctx: CommandContext) -> bool:
    """Select a word including trailing whitespace."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    start, end = find_word_boundaries(buffer, row, col)

    # Include trailing whitespace
    lines = buffer.get_lines()
    if row < len(lines):
        line = lines[row]
        while end < len(line) and line[end].isspace():
            end += 1

    ctx.visual_start = (row, start)
    ctx.visual_end = (row, end - 1)
    return True


def inner_word_big(ctx: CommandContext) -> bool:
    """Select inner WORD."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    start, end = find_word_boundaries_big(buffer, row, col)

    ctx.visual_start = (row, start)
    ctx.visual_end = (row, end - 1)
    return True


def a_word_big(ctx: CommandContext) -> bool:
    """Select a WORD including trailing whitespace."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    start, end = find_word_boundaries_big(buffer, row, col)

    # Include trailing whitespace
    lines = buffer.get_lines()
    if row < len(lines):
        line = lines[row]
        while end < len(line) and line[end].isspace():
            end += 1

    ctx.visual_start = (row, start)
    ctx.visual_end = (row, end - 1)
    return True


def inner_sentence(ctx: CommandContext) -> bool:
    """Select inner sentence."""
    # Simplified implementation - real vi is more complex
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    lines = buffer.get_lines()

    if row >= len(lines):
        return False

    line = lines[row]

    # Find sentence start (after . ! ?)
    start = col
    while start > 0:
        if line[start - 1] in ".!?":
            break
        start -= 1

    # Skip whitespace at start
    while start < len(line) and line[start].isspace():
        start += 1

    # Find sentence end
    end = col
    while end < len(line):
        if line[end] in ".!?":
            break
        end += 1

    ctx.visual_start = (row, start)
    ctx.visual_end = (row, end - 1)
    return True


def a_sentence(ctx: CommandContext) -> bool:
    """Select a sentence including trailing whitespace."""
    inner_sentence(ctx)

    # Include the punctuation and trailing space
    if ctx.visual_end:
        row, end = ctx.visual_end
        lines = ctx.buffer.get_lines()
        if row < len(lines):
            line = lines[row]
            if end < len(line) - 1 and line[end + 1] in ".!?":
                end += 1
            while end < len(line) - 1 and line[end + 1].isspace():
                end += 1
            ctx.visual_end = (row, end)

    return True


def inner_paragraph(ctx: CommandContext) -> bool:
    """Select inner paragraph."""
    buffer: TextBuffer = ctx.buffer
    row, _ = buffer.get_cursor()
    lines = buffer.get_lines()

    # Find paragraph start
    start_row = row
    while start_row > 0 and lines[start_row - 1].strip():
        start_row -= 1

    # Find paragraph end
    end_row = row
    while end_row < len(lines) - 1 and lines[end_row + 1].strip():
        end_row += 1

    ctx.visual_start = (start_row, 0)
    ctx.visual_end = (end_row, len(lines[end_row]) - 1)
    return True


def a_paragraph(ctx: CommandContext) -> bool:
    """Select a paragraph including trailing blank lines."""
    inner_paragraph(ctx)

    # Include trailing blank lines
    if ctx.visual_end:
        end_row, _ = ctx.visual_end
        lines = ctx.buffer.get_lines()
        while end_row < len(lines) - 1 and not lines[end_row + 1].strip():
            end_row += 1
        ctx.visual_end = (end_row, len(lines[end_row]) - 1 if end_row < len(lines) else 0)

    return True


def inner_double_quotes(ctx: CommandContext) -> bool:
    """Select inner double quotes."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_quote(buffer, row, col, '"')

    if result:
        start, end = result
        ctx.visual_start = (row, start + 1)  # Exclude opening quote
        ctx.visual_end = (row, end - 2)  # Exclude closing quote
        return True
    return False


def a_double_quotes(ctx: CommandContext) -> bool:
    """Select a double quotes including the quotes."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_quote(buffer, row, col, '"')

    if result:
        start, end = result
        ctx.visual_start = (row, start)
        ctx.visual_end = (row, end - 1)
        return True
    return False


def inner_single_quotes(ctx: CommandContext) -> bool:
    """Select inner single quotes."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_quote(buffer, row, col, "'")

    if result:
        start, end = result
        ctx.visual_start = (row, start + 1)
        ctx.visual_end = (row, end - 2)
        return True
    return False


def a_single_quotes(ctx: CommandContext) -> bool:
    """Select a single quotes including the quotes."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_quote(buffer, row, col, "'")

    if result:
        start, end = result
        ctx.visual_start = (row, start)
        ctx.visual_end = (row, end - 1)
        return True
    return False


def inner_backticks(ctx: CommandContext) -> bool:
    """Select inner backticks."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_quote(buffer, row, col, "`")

    if result:
        start, end = result
        ctx.visual_start = (row, start + 1)
        ctx.visual_end = (row, end - 2)
        return True
    return False


def a_backticks(ctx: CommandContext) -> bool:
    """Select a backticks including the backticks."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_quote(buffer, row, col, "`")

    if result:
        start, end = result
        ctx.visual_start = (row, start)
        ctx.visual_end = (row, end - 1)
        return True
    return False


def inner_parens(ctx: CommandContext) -> bool:
    """Select inner parentheses."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "(", ")")

    if result:
        (start_row, start_col), (end_row, end_col) = result
        ctx.visual_start = (start_row, start_col + 1)
        ctx.visual_end = (end_row, end_col - 1)
        return True
    return False


def a_parens(ctx: CommandContext) -> bool:
    """Select a parentheses including the parentheses."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "(", ")")

    if result:
        ctx.visual_start, ctx.visual_end = result
        return True
    return False


def inner_brackets(ctx: CommandContext) -> bool:
    """Select inner brackets."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "[", "]")

    if result:
        (start_row, start_col), (end_row, end_col) = result
        ctx.visual_start = (start_row, start_col + 1)
        ctx.visual_end = (end_row, end_col - 1)
        return True
    return False


def a_brackets(ctx: CommandContext) -> bool:
    """Select a brackets including the brackets."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "[", "]")

    if result:
        ctx.visual_start, ctx.visual_end = result
        return True
    return False


def inner_braces(ctx: CommandContext) -> bool:
    """Select inner braces."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "{", "}")

    if result:
        (start_row, start_col), (end_row, end_col) = result
        ctx.visual_start = (start_row, start_col + 1)
        ctx.visual_end = (end_row, end_col - 1)
        return True
    return False


def a_braces(ctx: CommandContext) -> bool:
    """Select a braces including the braces."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "{", "}")

    if result:
        ctx.visual_start, ctx.visual_end = result
        return True
    return False


def inner_angle(ctx: CommandContext) -> bool:
    """Select inner angle brackets."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "<", ">")

    if result:
        (start_row, start_col), (end_row, end_col) = result
        ctx.visual_start = (start_row, start_col + 1)
        ctx.visual_end = (end_row, end_col - 1)
        return True
    return False


def a_angle(ctx: CommandContext) -> bool:
    """Select a angle brackets including the brackets."""
    buffer: TextBuffer = ctx.buffer
    row, col = buffer.get_cursor()
    result = find_matching_bracket(buffer, row, col, "<", ">")

    if result:
        ctx.visual_start, ctx.visual_end = result
        return True
    return False


def inner_tag(ctx: CommandContext) -> bool:
    """Select inner tag (HTML/XML)."""
    # Simplified implementation
    ctx.renderer.show_message("Tag text objects not fully implemented")
    return False


def a_tag(ctx: CommandContext) -> bool:
    """Select a tag including the tags."""
    # Simplified implementation
    ctx.renderer.show_message("Tag text objects not fully implemented")
    return False
