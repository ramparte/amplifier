"""Tests for deck densifier."""

import json
from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from scenarios.deck_densifier import compress_slide
from scenarios.deck_densifier import densify_deck
from scenarios.deck_densifier.densifier import CompressedSlide
from scenarios.deck_densifier.densifier import count_words
from scenarios.deck_densifier.models import ContentBlock
from scenarios.deck_densifier.models import Slide
from scenarios.deck_densifier.models import SlideType


def test_count_words():
    """Test word counting function."""
    assert count_words("") == 0
    assert count_words("hello") == 1
    assert count_words("hello world") == 2
    assert count_words("  multiple   spaces   between  ") == 3
    assert count_words("one-two-three") == 1  # Hyphenated counts as one


@pytest.mark.asyncio
async def test_skip_title_slides():
    """Test that title slides are skipped."""
    slide = Slide(
        slide_type=SlideType.TITLE,
        title="My Amazing Presentation About Technology",
        content_blocks=[],
        speaker_notes="",
        slide_number=1,
    )

    result = await compress_slide(slide)
    assert result == slide  # Should return unchanged


@pytest.mark.asyncio
async def test_skip_blank_slides():
    """Test that blank slides are skipped."""
    slide = Slide(slide_type=SlideType.BLANK, title="", content_blocks=[], speaker_notes="", slide_number=2)

    result = await compress_slide(slide)
    assert result == slide  # Should return unchanged


@pytest.mark.asyncio
async def test_skip_already_compressed():
    """Test that already compressed slides are skipped."""
    slide = Slide(
        slide_type=SlideType.CONTENT,
        title="Short Title",  # 2 words
        content_blocks=[
            ContentBlock(text="Brief content", is_bullet=True)  # 2 words
        ],
        speaker_notes="Notes",
        slide_number=3,
    )

    result = await compress_slide(slide)
    assert result == slide  # Should return unchanged


@pytest.mark.asyncio
async def test_compress_content_slide():
    """Test compressing a content slide."""
    slide = Slide(
        slide_type=SlideType.CONTENT,
        title="Understanding the Complex Architecture of Modern Microservices",
        content_blocks=[
            ContentBlock(text="Services communicate through well-defined APIs", is_bullet=True),
            ContentBlock(text="Each service has its own database", is_bullet=True),
            ContentBlock(text="Deployment is independent and scalable", is_bullet=True),
        ],
        speaker_notes="Existing notes",
        slide_number=4,
    )

    # Mock the Agent to return a controlled response
    with patch("scenarios.deck_densifier.densifier.Agent") as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        # Create mock result
        mock_result = MagicMock()
        mock_result.output = CompressedSlide(title="Microservices Architecture", content="APIs, databases, deployment")
        mock_agent.run = AsyncMock(return_value=mock_result)

        result = await compress_slide(slide)

        # Check title is compressed
        assert count_words(result.title) <= 5
        assert result.title == "Microservices Architecture"

        # Check content is compressed
        total_content_words = sum(count_words(block.text) for block in result.content_blocks)
        assert total_content_words <= 10

        # Check original content is in speaker notes
        assert "Existing notes" in result.speaker_notes
        assert "Services communicate through well-defined APIs" in result.speaker_notes
        assert "Each service has its own database" in result.speaker_notes


@pytest.mark.asyncio
async def test_word_count_enforcement():
    """Test that word counts are enforced with fallback."""
    slide = Slide(
        slide_type=SlideType.CONTENT,
        title="A Very Long Title That Exceeds The Maximum Word Count Limit",
        content_blocks=[
            ContentBlock(text="This content is way too long and needs to be compressed significantly", is_bullet=True),
        ],
        speaker_notes="",
        slide_number=5,
    )

    # Mock the Agent to return overly long compressed content
    with patch("scenarios.deck_densifier.densifier.Agent") as mock_agent_class:
        mock_agent = MagicMock()
        mock_agent_class.return_value = mock_agent

        mock_result = MagicMock()
        mock_result.output = CompressedSlide(
            title="This Title Is Still Too Long For Our Requirements",
            content="This content also exceeds our maximum word limit by quite a bit",
        )
        mock_agent.run = AsyncMock(return_value=mock_result)

        result = await compress_slide(slide)

        # Check fallback truncation worked
        assert count_words(result.title) <= 5
        assert result.title == "This Title Is Still Too"  # First 5 words

        total_content_words = sum(count_words(block.text) for block in result.content_blocks)
        assert total_content_words <= 10


@pytest.mark.asyncio
async def test_densify_deck(tmp_path):
    """Test densifying an entire deck."""
    # Create test input file
    input_file = tmp_path / "test_deck.json"
    slides_data = [
        {
            "slide_type": "title",
            "title": "Test Presentation",
            "content_blocks": [],
            "speaker_notes": "",
            "slide_number": 1,
        },
        {
            "slide_type": "content",
            "title": "A Very Long Title About Important Topics",
            "content_blocks": [
                {"text": "First point about something important", "is_bullet": True},
                {"text": "Second point with more details", "is_bullet": True},
            ],
            "speaker_notes": "Notes",
            "slide_number": 2,
        },
    ]

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(slides_data, f)

    # Mock the compress_slide function
    with patch("scenarios.deck_densifier.densifier.compress_slide") as mock_compress:

        async def mock_compress_impl(slide, model):  # noqa: ARG001
            if slide.slide_type == SlideType.TITLE:
                return slide
            # Return a compressed version
            return Slide(
                slide_type=slide.slide_type,
                title="Short Title",
                content_blocks=[ContentBlock(text="Brief content", is_bullet=True)],
                speaker_notes=slide.speaker_notes + "\n\nOriginal content...",
                slide_number=slide.slide_number,
            )

        mock_compress.side_effect = mock_compress_impl

        # Run densify_deck
        output_file = await densify_deck(input_file)

        # Check output file was created
        assert output_file.exists()
        assert output_file.name == "test_deck_compressed.json"

        # Load and verify output
        with open(output_file, encoding="utf-8") as f:
            result_data = json.load(f)

        assert len(result_data) == 2
        # First slide unchanged (title slide)
        assert result_data[0]["title"] == "Test Presentation"
        # Second slide compressed
        assert result_data[1]["title"] == "Short Title"
        assert len(result_data[1]["content_blocks"]) == 1


@pytest.mark.asyncio
async def test_densify_deck_with_output_path(tmp_path):
    """Test densifying with specified output path."""
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.json"

    slides_data = [
        {"slide_type": "content", "title": "Test", "content_blocks": [], "speaker_notes": "", "slide_number": 1}
    ]

    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(slides_data, f)

    with patch("scenarios.deck_densifier.densifier.compress_slide") as mock_compress:

        async def mock_impl(slide, model):  # noqa: ARG001
            return slide

        mock_compress.side_effect = mock_impl

        result = await densify_deck(input_file, output_file)

        assert result == output_file
        assert output_file.exists()
