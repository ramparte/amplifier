"""Data models for deck densifier - reuses deck_builder models."""

from scenarios.deck_builder.models import ContentBlock
from scenarios.deck_builder.models import Slide
from scenarios.deck_builder.models import SlideType

__all__ = ["Slide", "ContentBlock", "SlideType"]
