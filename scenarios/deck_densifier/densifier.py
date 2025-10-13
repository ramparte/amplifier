"""Core densifier logic for compressing slides using LLM."""

import json
from pathlib import Path

from pydantic import BaseModel
from pydantic import Field
from pydantic_ai import Agent

from .models import ContentBlock
from .models import Slide
from .models import SlideType


class CompressedSlide(BaseModel):
    """Compressed version of a slide."""

    title: str = Field(description="Compressed title (max 5 words)")
    content: str = Field(description="Compressed content (max 10 words total)")


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


async def compress_slide(slide: Slide, model: str = "claude-3-5-sonnet-20241022") -> Slide:
    """Compress a single slide to storyteller mode.

    Args:
        slide: Original slide to compress
        model: LLM model to use for compression

    Returns:
        Compressed slide with original content in speaker notes
    """
    # Skip title slides - they're usually already minimal
    if slide.slide_type == SlideType.TITLE:
        return slide

    # Skip blank slides
    if slide.slide_type == SlideType.BLANK:
        return slide

    # Prepare the original content for the prompt
    original_content = []
    for block in slide.content_blocks:
        if block.is_bullet:
            original_content.append(f"• {block.text}")
        else:
            original_content.append(block.text)

    original_content_str = "\n".join(original_content) if original_content else ""

    # Skip if already compressed enough
    title_words = count_words(slide.title)
    content_words = count_words(original_content_str)

    if title_words <= 5 and content_words <= 10:
        return slide

    # Create the compression agent
    agent: Agent[None, CompressedSlide] = Agent(
        model,
        output_type=CompressedSlide,
        system_prompt="""You are compressing presentation slides for "storyteller mode" where the speaker
delivers most content verbally.

Rules:
1. Title: Maximum 5 words, capture essence
2. Content: Maximum 10 words total (across all bullets)
3. Preserve key concepts and flow
4. Make it punchy and memorable
5. Use clear, impactful words

Return a compressed version that fits these constraints.""",
    )

    # Get the compressed version
    prompt = f"""Original slide:
Title: {slide.title}
Content: {original_content_str}

Compress this to:
- Title: max 5 words
- Content: max 10 words total"""

    result = await agent.run(prompt)
    compressed = result.output

    # Verify word counts
    if count_words(compressed.title) > 5:
        # Fallback: take first 5 words
        compressed.title = " ".join(compressed.title.split()[:5])

    if count_words(compressed.content) > 10:
        # Fallback: take first 10 words
        compressed.content = " ".join(compressed.content.split()[:10])

    # Create new content blocks from compressed content
    new_blocks = []
    if compressed.content.strip():
        # Split into bullets if there are multiple sentences or natural breaks
        lines = [line.strip() for line in compressed.content.split(".") if line.strip()]
        if len(lines) > 1:
            for line in lines:
                new_blocks.append(ContentBlock(text=line, is_bullet=True))
        else:
            # Single line - check if it should be a bullet
            is_bullet = len(slide.content_blocks) > 0 and slide.content_blocks[0].is_bullet
            new_blocks.append(ContentBlock(text=compressed.content, is_bullet=is_bullet))

    # Preserve original content in speaker notes
    original_notes = slide.speaker_notes.strip()
    if original_content_str:
        notes_addition = f"\n\nOriginal slide content:\n{original_content_str}"
        if original_notes:
            new_notes = original_notes + notes_addition
        else:
            new_notes = notes_addition.strip()
    else:
        new_notes = original_notes

    # Create the compressed slide
    return Slide(
        slide_type=slide.slide_type,
        title=compressed.title,
        content_blocks=new_blocks,
        speaker_notes=new_notes,
        slide_number=slide.slide_number,
    )


async def densify_deck(
    input_file: Path, output_file: Path | None = None, model: str = "claude-3-5-sonnet-20241022"
) -> Path:
    """Compress an entire deck to storyteller mode.

    Args:
        input_file: Path to input JSON file with slides
        output_file: Path to output JSON file (optional)
        model: LLM model to use for compression

    Returns:
        Path to the output file
    """
    # Load the input slides
    with open(input_file, encoding="utf-8") as f:
        slides_data = json.load(f)

    # Parse into Slide objects
    slides = [Slide(**slide_data) for slide_data in slides_data]

    # Compress each slide
    compressed_slides = []
    for slide in slides:
        compressed = await compress_slide(slide, model)
        compressed_slides.append(compressed)

    # Determine output file
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_compressed.json"

    # Save the compressed slides
    slides_json = [slide.model_dump(mode="json") for slide in compressed_slides]
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(slides_json, f, indent=2, ensure_ascii=False)

    return output_file
