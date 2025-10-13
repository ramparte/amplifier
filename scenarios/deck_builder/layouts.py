"""PowerPoint layout mappings."""

from enum import Enum

from .models import Slide
from .models import SlideType


class LayoutType(Enum):
    """PowerPoint layout types."""

    TITLE_SLIDE = 0
    TITLE_AND_CONTENT = 1
    SECTION_HEADER = 2
    TWO_CONTENT = 3
    COMPARISON = 4
    TITLE_ONLY = 5
    BLANK = 6


def select_layout(slide: Slide) -> LayoutType:
    """Select appropriate PowerPoint layout for a slide.

    Args:
        slide: Slide object to map

    Returns:
        LayoutType to use
    """
    # Map slide types to PowerPoint layouts
    if slide.slide_type == SlideType.TITLE:
        return LayoutType.TITLE_SLIDE
    if slide.slide_type == SlideType.SECTION:
        return LayoutType.SECTION_HEADER
    if slide.slide_type == SlideType.BLANK:
        return LayoutType.BLANK
    # For content slides, use title and content layout
    return LayoutType.TITLE_AND_CONTENT


def get_placeholder_indices(layout_type: LayoutType) -> dict[str, int]:
    """Get placeholder indices for a layout type.

    Args:
        layout_type: The layout type

    Returns:
        Dictionary mapping placeholder types to indices
    """
    # Standard placeholder mappings for common layouts
    mappings = {
        LayoutType.TITLE_SLIDE: {"title": 0, "subtitle": 1},
        LayoutType.TITLE_AND_CONTENT: {"title": 0, "content": 1},
        LayoutType.SECTION_HEADER: {"title": 0, "subtitle": 1},
        LayoutType.TITLE_ONLY: {"title": 0},
        LayoutType.BLANK: {},
    }

    return mappings.get(layout_type, {"title": 0, "content": 1})
