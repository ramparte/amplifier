"""Text objects module for vi editor."""

from amplifier.vi.text_objects.base import TextObject
from amplifier.vi.text_objects.base import TextObjectRange
from amplifier.vi.text_objects.brackets import create_around_angle_brackets_handler
from amplifier.vi.text_objects.brackets import create_around_curly_braces_handler
from amplifier.vi.text_objects.brackets import create_around_parentheses_handler
from amplifier.vi.text_objects.brackets import create_around_square_brackets_handler
from amplifier.vi.text_objects.brackets import create_inner_angle_brackets_handler
from amplifier.vi.text_objects.brackets import create_inner_curly_braces_handler
from amplifier.vi.text_objects.brackets import create_inner_parentheses_handler
from amplifier.vi.text_objects.brackets import create_inner_square_brackets_handler
from amplifier.vi.text_objects.quotes import create_around_backticks_handler
from amplifier.vi.text_objects.quotes import create_around_double_quotes_handler
from amplifier.vi.text_objects.quotes import create_around_single_quotes_handler
from amplifier.vi.text_objects.quotes import create_inner_backticks_handler
from amplifier.vi.text_objects.quotes import create_inner_double_quotes_handler
from amplifier.vi.text_objects.quotes import create_inner_single_quotes_handler
from amplifier.vi.text_objects.tags import create_around_tag_handler
from amplifier.vi.text_objects.tags import create_inner_tag_handler

__all__ = [
    # Base classes
    "TextObject",
    "TextObjectRange",
    # Bracket handlers
    "create_inner_parentheses_handler",
    "create_around_parentheses_handler",
    "create_inner_square_brackets_handler",
    "create_around_square_brackets_handler",
    "create_inner_curly_braces_handler",
    "create_around_curly_braces_handler",
    "create_inner_angle_brackets_handler",
    "create_around_angle_brackets_handler",
    # Quote handlers
    "create_inner_double_quotes_handler",
    "create_around_double_quotes_handler",
    "create_inner_single_quotes_handler",
    "create_around_single_quotes_handler",
    "create_inner_backticks_handler",
    "create_around_backticks_handler",
    # Tag handlers
    "create_inner_tag_handler",
    "create_around_tag_handler",
]
