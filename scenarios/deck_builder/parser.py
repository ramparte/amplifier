"""Markdown parser for slide decks."""

import re

from .models import ContentBlock
from .models import Slide
from .models import SlideType


def parse_markdown(markdown_content: str) -> list[Slide]:
    """Parse markdown content into structured slides.

    Args:
        markdown_content: Markdown text with slides separated by ---

    Returns:
        List of Slide objects
    """
    slides = []
    raw_slides = markdown_content.split("\n---\n")

    # Skip the first part if it's a title/header before the first ---
    start_idx = 1 if raw_slides and not raw_slides[0].strip().startswith("##") else 0

    for idx, raw_slide in enumerate(raw_slides[start_idx:], start=1):
        slide = _parse_single_slide(raw_slide.strip(), idx)
        if slide:
            slides.append(slide)

    return slides


def _parse_single_slide(raw_content: str, slide_number: int) -> Slide | None:
    """Parse a single slide from raw markdown.

    Args:
        raw_content: Raw markdown for one slide
        slide_number: The slide number

    Returns:
        Slide object or None if empty
    """
    if not raw_content:
        return None

    lines = raw_content.split("\n")
    title = ""
    content_blocks = []
    speaker_notes = ""
    in_speaker_notes = False
    slide_type = SlideType.CONTENT

    for line in lines:
        # Check for title
        if line.startswith("## "):
            title = line[3:].strip()
            # Detect slide type based on title patterns
            if "slide" in title.lower() and ":" in title:
                # Extract actual title after "Slide N:"
                parts = title.split(":", 1)
                if len(parts) > 1:
                    title = parts[1].strip()
            continue

        # Check for speaker notes section
        if line.strip().startswith("**Speaker Notes:**") or line.strip() == "**Speaker Notes**":
            in_speaker_notes = True
            continue

        # Process content
        if in_speaker_notes:
            speaker_notes += line + "\n"
        else:
            if line.strip():
                # Check if it's a bullet point
                is_bullet, indent_level, text = _parse_bullet(line)
                if is_bullet or line.startswith("**"):
                    content_blocks.append(
                        ContentBlock(text=_clean_text(text), is_bullet=is_bullet, indent_level=indent_level)
                    )

    # Determine slide type
    if slide_number == 1 and not content_blocks:
        slide_type = SlideType.TITLE
    elif title and not content_blocks:
        slide_type = SlideType.SECTION

    return Slide(
        slide_type=slide_type,
        title=title or f"Slide {slide_number}",
        content_blocks=content_blocks,
        speaker_notes=speaker_notes.strip(),
        slide_number=slide_number,
    )


def _parse_bullet(line: str) -> tuple[bool, int, str]:
    """Parse a bullet point line.

    Args:
        line: Line to parse

    Returns:
        Tuple of (is_bullet, indent_level, text)
    """
    # Check for bullet indicators
    bullet_pattern = r"^(\s*)[-*•]\s+(.+)$"
    match = re.match(bullet_pattern, line)

    if match:
        indent = len(match.group(1))
        indent_level = indent // 2  # Convert spaces to indent levels
        text = match.group(2)
        return True, indent_level, text

    # Check for numbered lists
    number_pattern = r"^(\s*)(\d+\.)\s+(.+)$"
    match = re.match(number_pattern, line)

    if match:
        indent = len(match.group(1))
        indent_level = indent // 2
        text = match.group(3)
        return True, indent_level, text

    return False, 0, line


def _clean_text(text: str) -> str:
    """Clean markdown formatting from text.

    Args:
        text: Text to clean

    Returns:
        Cleaned text
    """
    # Remove bold markers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    # Remove italic markers
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    # Remove inline code markers
    text = re.sub(r"`(.*?)`", r"\1", text)

    return text.strip()
