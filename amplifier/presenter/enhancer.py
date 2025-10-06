"""AI-powered enrichment module for enhancing outlines with suggestions."""

import asyncio
import json
from typing import Any

from anthropic import AsyncAnthropic
from presenter.models import Concept
from presenter.models import EnrichedOutline
from presenter.models import NodeType
from presenter.models import OutlineNode
from presenter.models import ParsedOutline
from presenter.models import SlideSuggestion
from presenter.models import SlideType


class OutlineEnhancer:
    """Enhances outlines with AI-powered suggestions and analysis."""

    def __init__(self, api_key: str | None = None):
        """Initialize the enhancer with Anthropic client.

        Args:
            api_key: Anthropic API key. If None, will use ANTHROPIC_API_KEY env var.
        """
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = "claude-3-haiku-20240307"  # Fast model for quick enrichment

    async def enhance(self, outline: ParsedOutline) -> EnrichedOutline:
        """Enhance outline with AI suggestions and concept extraction.

        Args:
            outline: ParsedOutline to enhance

        Returns:
            EnrichedOutline with suggestions and extracted concepts
        """
        # Run analysis tasks in parallel
        suggestions_task = self._suggest_slide_types(outline)
        concepts_task = self._extract_concepts(outline)
        recommendations_task = self._generate_recommendations(outline)

        suggestions, concepts, recommendations = await asyncio.gather(
            suggestions_task,
            concepts_task,
            recommendations_task,
        )

        return EnrichedOutline(
            outline=outline,
            suggestions=suggestions,
            concepts=concepts,
            recommendations=recommendations,
        )

    async def _suggest_slide_types(self, outline: ParsedOutline) -> dict[str, SlideSuggestion]:
        """Suggest slide types for each major section."""
        suggestions = {}

        # Process top-level nodes
        for i, node in enumerate(outline.nodes):
            node_id = f"node_{i}"
            suggestion = await self._analyze_node_for_slide_type(node)
            suggestions[node_id] = suggestion

            # Process significant children
            for j, child in enumerate(node.children):
                if child.node_type == NodeType.HEADING:
                    child_id = f"node_{i}_{j}"
                    child_suggestion = await self._analyze_node_for_slide_type(child)
                    suggestions[child_id] = child_suggestion

        return suggestions

    async def _analyze_node_for_slide_type(self, node: OutlineNode) -> SlideSuggestion:
        """Analyze a single node to suggest slide type."""
        # Simple heuristic-based analysis (can be enhanced with LLM)
        text_lower = node.text.lower()

        # Detect comparison patterns
        if any(word in text_lower for word in ["vs", "versus", "compare", "comparison"]):
            return SlideSuggestion(
                slide_type=SlideType.COMPARISON,
                visual_suggestion="Two-column layout",
                emphasis=[node.text],
            )

        # Detect timeline patterns
        if any(word in text_lower for word in ["timeline", "roadmap", "phases", "steps"]):
            return SlideSuggestion(
                slide_type=SlideType.TIMELINE,
                visual_suggestion="Horizontal timeline",
                emphasis=[],
            )

        # Detect conclusion patterns
        if any(word in text_lower for word in ["conclusion", "summary", "takeaway", "next steps"]):
            return SlideSuggestion(
                slide_type=SlideType.CONCLUSION,
                visual_suggestion="Key points emphasis",
                emphasis=[],
            )

        # Default to bullet for nodes with children
        if node.children:
            return SlideSuggestion(
                slide_type=SlideType.BULLET,
                layout="standard",
                emphasis=[],
            )

        # Default to section for headings
        if node.node_type == NodeType.HEADING:
            return SlideSuggestion(
                slide_type=SlideType.SECTION,
                visual_suggestion="Section divider",
                emphasis=[node.text],
            )

        return SlideSuggestion(slide_type=SlideType.BULLET)

    async def _extract_concepts(self, outline: ParsedOutline) -> list[Concept]:
        """Extract key concepts from the outline using LLM."""
        # Build context from outline
        context = self._build_context(outline)

        if not context:
            return []

        prompt = f"""Extract 3-5 key concepts from this presentation outline.
For each concept, provide:
1. The concept text (2-4 words)
2. A type (technology, metric, process, principle, or general)
3. Importance (0.0-1.0)

Outline:
{context}

Return as JSON array with objects containing: text, type, importance"""

        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}],
            )

            # Parse response - handle anthropic response structure
            content = "[]"
            if response.content and len(response.content) > 0:
                first_block = response.content[0]
                if hasattr(first_block, "text"):
                    content = first_block.text
            concepts_data = self._parse_json_response(content)

            return [
                Concept(
                    text=c.get("text", ""),
                    type=c.get("type"),
                    importance=c.get("importance", 0.5),
                )
                for c in concepts_data
                if c.get("text")
            ][:5]  # Limit to 5 concepts

        except Exception:
            # Return empty list on error - simple fallback
            return []

    async def _generate_recommendations(self, outline: ParsedOutline) -> list[str]:
        """Generate presentation improvement recommendations."""
        # Simple heuristic recommendations
        recommendations = []

        # Check structure
        if len(outline.nodes) < 3:
            recommendations.append("Consider adding more sections for better flow")
        elif len(outline.nodes) > 10:
            recommendations.append("Consider consolidating sections for clarity")

        # Check for introduction
        first_node = outline.nodes[0] if outline.nodes else None
        if first_node and "introduction" not in first_node.text.lower():
            recommendations.append("Add an introduction slide to set context")

        # Check for conclusion
        last_node = outline.nodes[-1] if outline.nodes else None
        if last_node and not any(word in last_node.text.lower() for word in ["conclusion", "summary", "next"]):
            recommendations.append("Add a conclusion slide to summarize key points")

        return recommendations

    def _build_context(self, outline: ParsedOutline) -> str:
        """Build text context from outline."""
        lines = []

        if outline.title:
            lines.append(f"Title: {outline.title}")

        def process_node(node: OutlineNode, indent: int = 0):
            prefix = "  " * indent
            lines.append(f"{prefix}- {node.text}")
            for child in node.children:
                process_node(child, indent + 1)

        for node in outline.nodes:
            process_node(node)

        return "\n".join(lines)

    def _parse_json_response(self, text: str) -> list[dict[str, Any]]:
        """Parse JSON from LLM response, handling common issues."""
        # Try to extract JSON from markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]

        # Clean up common issues
        text = text.strip()

        try:
            result = json.loads(text)
            if isinstance(result, list):
                return result
            return []
        except json.JSONDecodeError:
            return []
