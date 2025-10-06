"""Tests for the OutlineEnhancer module."""

import asyncio
import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from presenter.enhancer import OutlineEnhancer
from presenter.models import EnrichedOutline
from presenter.models import NodeType
from presenter.models import OutlineNode
from presenter.models import ParsedOutline
from presenter.models import SlideSuggestion
from presenter.models import SlideType


@pytest.fixture
def sample_outline():
    """Create a sample parsed outline for testing."""
    return ParsedOutline(
        title="Test Presentation",
        nodes=[
            OutlineNode(
                level=1,
                text="Introduction",
                node_type=NodeType.HEADING,
                children=[
                    OutlineNode(level=2, text="Overview", node_type=NodeType.BULLET),
                    OutlineNode(level=2, text="Goals", node_type=NodeType.BULLET),
                ],
            ),
            OutlineNode(
                level=1,
                text="Comparison: Old vs New",
                node_type=NodeType.HEADING,
                children=[
                    OutlineNode(level=2, text="Old System", node_type=NodeType.BULLET),
                    OutlineNode(level=2, text="New System", node_type=NodeType.BULLET),
                ],
            ),
            OutlineNode(
                level=1,
                text="Timeline and Roadmap",
                node_type=NodeType.HEADING,
                children=[
                    OutlineNode(level=2, text="Q1 2024", node_type=NodeType.BULLET),
                    OutlineNode(level=2, text="Q2 2024", node_type=NodeType.BULLET),
                ],
            ),
        ],
        metadata={"author": "Test Author"},
    )


@pytest.fixture
def enhancer():
    """Create an enhancer instance with a mock API key."""
    return OutlineEnhancer(api_key="test_key")


class TestOutlineEnhancer:
    """Test suite for OutlineEnhancer."""

    @pytest.mark.asyncio
    async def test_enhance_basic(self, enhancer, sample_outline):
        """Test basic enhancement with mocked API responses."""
        # Mock the Anthropic client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text=json.dumps(
                    [
                        {"text": "Digital Transformation", "type": "technology", "importance": 0.9},
                        {"text": "Performance Metrics", "type": "metric", "importance": 0.7},
                    ]
                )
            )
        ]

        with patch.object(enhancer.client.messages, "create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = mock_response

            result = await enhancer.enhance(sample_outline)

            # Verify result structure
            assert isinstance(result, EnrichedOutline)
            assert result.outline == sample_outline
            assert len(result.suggestions) > 0
            assert len(result.concepts) > 0

    @pytest.mark.asyncio
    async def test_enhance_api_failure_graceful_recovery(self, enhancer, sample_outline):
        """Test that enhancement handles API failures gracefully."""
        # Mock API to raise an exception
        with patch.object(enhancer.client.messages, "create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("API connection failed")

            # Should not raise, but return minimal enrichment
            result = await enhancer.enhance(sample_outline)

            assert isinstance(result, EnrichedOutline)
            assert result.outline == sample_outline
            assert len(result.concepts) == 0  # No concepts due to API failure
            assert len(result.suggestions) > 0  # Heuristic suggestions still work

    def test_analyze_node_for_slide_type_comparison(self, enhancer):
        """Test slide type detection for comparison content."""
        node = OutlineNode(
            level=1,
            text="Feature Comparison: Pro vs Standard",
            node_type=NodeType.HEADING,
        )

        # Run synchronously since this method is not async
        import asyncio

        suggestion = asyncio.run(enhancer._analyze_node_for_slide_type(node))

        assert suggestion.slide_type == SlideType.COMPARISON
        assert "column" in suggestion.visual_suggestion.lower()

    def test_analyze_node_for_slide_type_timeline(self, enhancer):
        """Test slide type detection for timeline content."""
        node = OutlineNode(
            level=1,
            text="Project Roadmap 2024",
            node_type=NodeType.HEADING,
        )

        import asyncio

        suggestion = asyncio.run(enhancer._analyze_node_for_slide_type(node))

        assert suggestion.slide_type == SlideType.TIMELINE
        assert "timeline" in suggestion.visual_suggestion.lower()

    def test_analyze_node_for_slide_type_conclusion(self, enhancer):
        """Test slide type detection for conclusion content."""
        node = OutlineNode(
            level=1,
            text="Key Takeaways and Next Steps",
            node_type=NodeType.HEADING,
        )

        import asyncio

        suggestion = asyncio.run(enhancer._analyze_node_for_slide_type(node))

        assert suggestion.slide_type == SlideType.CONCLUSION

    def test_parse_json_response_clean_json(self, enhancer):
        """Test parsing clean JSON response."""
        clean_json = '[{"text": "AI", "type": "tech", "importance": 0.8}]'
        result = enhancer._parse_json_response(clean_json)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["text"] == "AI"

    def test_parse_json_response_markdown_wrapped(self, enhancer):
        """Test parsing JSON wrapped in markdown code blocks."""
        wrapped_json = """```json
[{"text": "ML", "type": "tech", "importance": 0.9}]
```"""
        result = enhancer._parse_json_response(wrapped_json)

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["text"] == "ML"

    def test_parse_json_response_malformed(self, enhancer):
        """Test handling of malformed JSON."""
        malformed = "This is not JSON at all"
        result = enhancer._parse_json_response(malformed)

        assert result == []  # Returns empty list on parse failure

    def test_build_context(self, enhancer, sample_outline):
        """Test context building from outline."""
        context = enhancer._build_context(sample_outline)

        assert "Test Presentation" in context
        assert "Introduction" in context
        assert "Overview" in context
        assert "Comparison: Old vs New" in context

    @pytest.mark.asyncio
    async def test_extract_concepts_empty_outline(self, enhancer):
        """Test concept extraction with empty outline."""
        empty_outline = ParsedOutline(nodes=[])

        with patch.object(enhancer.client.messages, "create", new_callable=AsyncMock):
            concepts = await enhancer._extract_concepts(empty_outline)

            assert concepts == []

    @pytest.mark.asyncio
    async def test_generate_recommendations_short_outline(self, enhancer):
        """Test recommendations for a short outline."""
        short_outline = ParsedOutline(
            title="Brief Update",
            nodes=[
                OutlineNode(level=1, text="Status", node_type=NodeType.HEADING),
            ],
        )

        recommendations = await enhancer._generate_recommendations(short_outline)

        assert any("more sections" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_generate_recommendations_long_outline(self, enhancer):
        """Test recommendations for an overly long outline."""
        long_outline = ParsedOutline(
            title="Comprehensive Review",
            nodes=[OutlineNode(level=1, text=f"Section {i}", node_type=NodeType.HEADING) for i in range(15)],
        )

        recommendations = await enhancer._generate_recommendations(long_outline)

        assert any("consolidating" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_suggest_slide_types_nested_structure(self, enhancer, sample_outline):
        """Test slide type suggestions for nested structure."""
        suggestions = await enhancer._suggest_slide_types(sample_outline)

        # Should have suggestions for main nodes and heading children
        assert len(suggestions) > len(sample_outline.nodes)

        # Check that node IDs are properly formatted
        assert "node_0" in suggestions
        assert "node_1" in suggestions

        # Verify suggestions are SlideSuggestion objects
        for suggestion in suggestions.values():
            assert isinstance(suggestion, SlideSuggestion)

    @pytest.mark.asyncio
    async def test_enhance_with_no_api_key(self, sample_outline):
        """Test enhancement without API key (should use defaults)."""
        enhancer_no_key = OutlineEnhancer(api_key=None)

        # Mock to avoid actual API call
        with patch.object(enhancer_no_key.client.messages, "create", new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = Exception("No API key")

            result = await enhancer_no_key.enhance(sample_outline)

            assert isinstance(result, EnrichedOutline)
            # Should still get heuristic suggestions
            assert len(result.suggestions) > 0

    def test_build_context_with_metadata(self, enhancer):
        """Test context building includes metadata."""
        outline_with_meta = ParsedOutline(
            title="Presentation",
            nodes=[],
            metadata={"author": "John Doe", "date": "2024-01-01"},
        )

        context = enhancer._build_context(outline_with_meta)

        assert "Presentation" in context

    @pytest.mark.asyncio
    async def test_parallel_processing(self, enhancer, sample_outline):
        """Test that enhancement tasks run in parallel."""
        import time

        # Mock each method to take some time
        async def slow_suggest(*args):
            await asyncio.sleep(0.1)
            return {}

        async def slow_extract(*args):
            await asyncio.sleep(0.1)
            return []

        async def slow_recommend(*args):
            await asyncio.sleep(0.1)
            return []

        with (
            patch.object(enhancer, "_suggest_slide_types", new=slow_suggest),
            patch.object(enhancer, "_extract_concepts", new=slow_extract),
            patch.object(enhancer, "_generate_recommendations", new=slow_recommend),
        ):
            start = time.time()
            await enhancer.enhance(sample_outline)
            elapsed = time.time() - start

            # If running in parallel, should take ~0.1s, not 0.3s
            assert elapsed < 0.2
