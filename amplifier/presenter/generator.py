"""Slide generation module for converting enriched outlines to slides."""

import uuid
from typing import Any

from presenter.models import EnrichedOutline
from presenter.models import NodeType
from presenter.models import OutlineNode
from presenter.models import Presentation
from presenter.models import PresentationSettings
from presenter.models import Slide
from presenter.models import SlideContent
from presenter.models import SlideType


class SlideGenerator:
    """Generates slides from enriched outlines."""

    def generate(self, enriched: EnrichedOutline, settings: PresentationSettings | None = None) -> Presentation:
        """Generate a presentation from an enriched outline.

        Args:
            enriched: EnrichedOutline with suggestions and analysis
            settings: Optional presentation settings

        Returns:
            Complete Presentation object
        """
        slides = []
        order = 0

        # Create title slide
        if enriched.outline.title:
            title_slide = self._create_title_slide(enriched.outline.title, enriched.outline.metadata, order)
            slides.append(title_slide)
            order += 1

        # Process each top-level node
        for i, node in enumerate(enriched.outline.nodes):
            node_id = f"node_{i}"
            suggestion = enriched.suggestions.get(node_id)

            # Create slide for this node
            slide = self._create_slide_from_node(node, suggestion, order, node_id)
            slides.append(slide)
            order += 1

            # Process significant children
            for j, child in enumerate(node.children):
                # Only create slides for heading children or nodes with content
                if child.node_type == NodeType.HEADING or child.children or len(child.text) > 50:
                    child_id = f"node_{i}_{j}"
                    child_suggestion = enriched.suggestions.get(child_id)
                    child_slide = self._create_slide_from_node(child, child_suggestion, order, child_id)
                    slides.append(child_slide)
                    order += 1

        # Add conclusion slide if recommended
        if any("conclusion" in rec.lower() for rec in enriched.recommendations):
            conclusion_slide = self._create_conclusion_slide(enriched, order)
            slides.append(conclusion_slide)

        # Create presentation
        return Presentation(
            id=str(uuid.uuid4()),
            title=enriched.outline.title or "Untitled Presentation",
            slides=slides,
            settings=settings or PresentationSettings(),
            metadata=enriched.outline.metadata,
        )

    def _create_title_slide(self, title: str, metadata: dict[str, Any], order: int) -> Slide:
        """Create a title slide."""
        content = SlideContent(
            main=[title],
            notes="Opening slide - introduce yourself and the topic",
        )

        # Add subtitle from metadata if available
        if metadata.get("subtitle"):
            content.main.append(metadata["subtitle"])

        if metadata.get("author"):
            content.main.append(f"By {metadata['author']}")

        return Slide(
            id=str(uuid.uuid4()),
            type=SlideType.TITLE,
            title=title,
            content=content,
            order=order,
        )

    def _create_slide_from_node(
        self,
        node: OutlineNode,
        suggestion: Any | None,
        order: int,
        source_id: str,
    ) -> Slide:
        """Create a slide from an outline node."""
        # Determine slide type
        slide_type = suggestion.slide_type if suggestion else SlideType.BULLET

        # Build content based on node structure
        content = self._build_slide_content(node, slide_type)

        # Add speaker notes
        if suggestion and suggestion.visual_suggestion:
            content.notes = f"Visual: {suggestion.visual_suggestion}"

        return Slide(
            id=str(uuid.uuid4()),
            type=slide_type,
            title=node.text,
            content=content,
            order=order,
            source_node_id=source_id,
        )

    def _build_slide_content(self, node: OutlineNode, slide_type: SlideType) -> SlideContent:
        """Build slide content from a node."""
        bullets = []
        notes_parts = []

        # Extract bullets from children
        for child in node.children:
            if child.node_type == NodeType.BULLET:
                bullets.append(child.text)
                # Add sub-bullets
                for sub in child.children:
                    bullets.append(f"  • {sub.text}")
            elif child.node_type == NodeType.TEXT:
                # Add text as notes
                notes_parts.append(child.text)
            elif child.node_type == NodeType.CODE:
                # Add code reference in notes
                notes_parts.append(f"Code example: {child.metadata.get('language', 'plain')}")

        # Build speaker notes
        notes = "\n".join(notes_parts) if notes_parts else None

        # Special handling for comparison slides
        if slide_type == SlideType.COMPARISON:
            # Split bullets into two columns if possible
            mid = len(bullets) // 2
            if mid > 0:
                return SlideContent(
                    main=[bullets[:mid], bullets[mid:]],  # Two columns
                    notes=notes,
                )

        # Special handling for timeline slides
        if slide_type == SlideType.TIMELINE:
            # Format bullets as timeline items
            return SlideContent(
                main=[{"phase": i + 1, "text": bullet} for i, bullet in enumerate(bullets)],
                notes=notes,
            )

        # Standard bullet slide
        return SlideContent(
            bullets=bullets if bullets else None,
            notes=notes,
        )

    def _create_conclusion_slide(self, enriched: EnrichedOutline, order: int) -> Slide:
        """Create a conclusion slide with key concepts."""
        # Build key takeaways from concepts
        takeaways = []

        # Add top concepts
        for concept in enriched.concepts[:3]:
            takeaways.append(f"• {concept.text}")

        # Add top recommendations
        for rec in enriched.recommendations[:2]:
            takeaways.append(f"• {rec}")

        content = SlideContent(
            bullets=takeaways if takeaways else ["• Thank you", "• Questions?"],
            notes="Summarize key points and open for questions",
        )

        return Slide(
            id=str(uuid.uuid4()),
            type=SlideType.CONCLUSION,
            title="Key Takeaways",
            content=content,
            order=order,
        )
