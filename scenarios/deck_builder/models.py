"""Data models for deck builder."""

from enum import Enum

from pydantic import BaseModel
from pydantic import Field


class SlideType(Enum):
    """Types of slides."""

    TITLE = "title"
    CONTENT = "content"
    SECTION = "section"
    BLANK = "blank"


class ContentBlock(BaseModel):
    """A block of content within a slide."""

    text: str = Field(description="The text content")
    is_bullet: bool = Field(default=False, description="Whether this is a bullet point")
    indent_level: int = Field(default=0, description="Indentation level for bullets")


class Slide(BaseModel):
    """A single slide in the presentation."""

    slide_type: SlideType = Field(description="Type of slide")
    title: str = Field(description="Slide title")
    content_blocks: list[ContentBlock] = Field(default_factory=list, description="Content blocks")
    speaker_notes: str = Field(default="", description="Speaker notes for the slide")
    slide_number: int = Field(description="Slide number in the deck")


class Theme(BaseModel):
    """Theme configuration for the presentation."""

    primary_color: str = Field(default="#2C3E50", description="Primary color (hex)")
    accent_color: str = Field(default="#3498DB", description="Accent color (hex)")
    text_color: str = Field(default="#34495E", description="Text color (hex)")
    background_color: str = Field(default="#FFFFFF", description="Background color (hex)")
    font_title: str = Field(default="Calibri", description="Title font")
    font_body: str = Field(default="Calibri", description="Body font")
    font_size_title: int = Field(default=44, description="Title font size")
    font_size_body: int = Field(default=18, description="Body font size")
