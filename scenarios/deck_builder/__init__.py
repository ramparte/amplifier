"""
Deck Builder Module

A PowerPoint deck builder that converts markdown slide decks to PPTX format.
"""

from .generator import generate_presentation
from .models import ContentBlock
from .models import Slide
from .models import SlideType
from .models import Theme
from .parser import parse_markdown

__all__ = ["parse_markdown", "generate_presentation", "Slide", "SlideType", "ContentBlock", "Theme"]
