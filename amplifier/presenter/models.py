"""Data models for the presenter pipeline."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from pydantic import Field


class NodeType(str, Enum):
    """Types of nodes in an outline."""

    HEADING = "heading"
    BULLET = "bullet"
    TEXT = "text"
    CODE = "code"
    NOTE = "note"
    IMAGE = "image"


class SlideType(str, Enum):
    """Types of slides."""

    TITLE = "title"
    BULLET = "bullet"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    IMAGE = "image"
    CHART = "chart"
    CUSTOM = "custom"
    SECTION = "section"
    CONCLUSION = "conclusion"


class TransitionType(str, Enum):
    """Types of slide transitions."""

    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"
    NONE = "none"


class OutlineNode(BaseModel):
    """A node in a hierarchical outline."""

    level: int = Field(ge=0, description="Nesting level (0 = root)")
    text: str = Field(description="Content text")
    node_type: NodeType = Field(default=NodeType.TEXT)
    children: list["OutlineNode"] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ParsedOutline(BaseModel):
    """A parsed outline with hierarchical structure."""

    title: str | None = Field(default=None, description="Main title")
    nodes: list[OutlineNode] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Front matter or metadata")
    source: str | None = Field(default=None, description="Source file path")


class Concept(BaseModel):
    """A key concept extracted from text."""

    text: str = Field(description="Concept text")
    type: str | None = Field(default=None, description="Concept type (e.g., 'technology', 'metric')")
    icon: str | None = Field(default=None, description="Suggested icon name")
    definition: str | None = Field(default=None, description="Brief definition")
    importance: float = Field(default=0.5, ge=0, le=1, description="Importance score")


class SlideSuggestion(BaseModel):
    """LLM suggestion for a slide."""

    slide_type: SlideType = Field(description="Suggested slide type")
    visual_suggestion: str | None = Field(default=None, description="Suggested visual element")
    layout: str | None = Field(default=None, description="Suggested layout")
    emphasis: list[str] = Field(default_factory=list, description="Text to emphasize")
    chart_type: str | None = Field(default=None, description="Chart type if applicable")


class EnrichedOutline(BaseModel):
    """An outline enriched with LLM analysis."""

    outline: ParsedOutline = Field(description="Original parsed outline")
    suggestions: dict[str, SlideSuggestion] = Field(default_factory=dict)
    concepts: list[Concept] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)


class SlideContent(BaseModel):
    """Content for a slide."""

    main: list[Any] = Field(default_factory=list, description="Main content items")
    notes: str | None = Field(default=None, description="Speaker notes")
    bullets: list[str] | None = Field(default=None, description="Bullet points")
    chart_data: dict[str, Any] | None = Field(default=None, description="Chart data if applicable")


class Asset(BaseModel):
    """An asset (image, icon, chart) for a slide."""

    id: str = Field(description="Unique asset ID")
    type: str = Field(description="Asset type (image, icon, chart)")
    path: str | None = Field(default=None, description="File path")
    url: str | None = Field(default=None, description="URL if remote")
    position: dict[str, float] = Field(default_factory=dict, description="Position coordinates")
    size: int | None = Field(default=None, description="Size in pixels")
    metadata: dict[str, Any] = Field(default_factory=dict)


class SlideStyle(BaseModel):
    """Styling information for a slide."""

    theme: str | None = Field(default=None, description="Theme ID")
    layout: str | None = Field(default=None, description="Layout ID")
    background: str | None = Field(default=None, description="Background color or gradient")
    customizations: dict[str, Any] = Field(default_factory=dict)


class SlideTransitions(BaseModel):
    """Transition settings for a slide."""

    entrance: TransitionType = Field(default=TransitionType.FADE)
    exit: TransitionType = Field(default=TransitionType.FADE)
    duration: float = Field(default=0.5, ge=0, description="Duration in seconds")


class Slide(BaseModel):
    """A single presentation slide."""

    id: str = Field(description="Unique slide ID")
    version: str = Field(default="1.0")
    type: SlideType = Field(default=SlideType.BULLET)
    title: str = Field(description="Slide title")
    content: SlideContent = Field(default_factory=SlideContent)
    style: SlideStyle = Field(default_factory=SlideStyle)
    assets: list[Asset] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    transitions: SlideTransitions = Field(default_factory=SlideTransitions)
    order: int | None = Field(default=None, description="Order in presentation")
    source_node_id: str | None = Field(default=None, description="Source outline node ID")


class PresentationSettings(BaseModel):
    """Settings for a presentation."""

    aspect_ratio: str = Field(default="16:9", description="Aspect ratio")
    slide_numbers: bool = Field(default=True, description="Show slide numbers")
    footer: str | None = Field(default=None, description="Footer text")
    author: str | None = Field(default=None, description="Author name")
    date: datetime | None = Field(default=None, description="Presentation date")


class Presentation(BaseModel):
    """A complete presentation."""

    id: str = Field(description="Unique presentation ID")
    version: str = Field(default="1.0")
    title: str = Field(description="Presentation title")
    slides: list[Slide] = Field(default_factory=list, description="List of slides")
    settings: PresentationSettings = Field(default_factory=PresentationSettings)
    theme_id: str | None = Field(default=None, description="Theme ID")
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    modified_at: datetime = Field(default_factory=datetime.now)


# Enable forward references for recursive models
OutlineNode.model_rebuild()
