"""Deck densifier - Compress presentation slides to storyteller mode."""

from .densifier import compress_slide
from .densifier import densify_deck
from .models import ContentBlock
from .models import Slide
from .models import SlideType

__all__ = [
    "compress_slide",
    "densify_deck",
    "Slide",
    "ContentBlock",
    "SlideType",
]
