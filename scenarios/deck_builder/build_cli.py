"""CLI tool to build PowerPoint from JSON slides."""

import json
import sys

import click

from .generator import generate_presentation
from .models import Slide
from .themes import get_default_theme


@click.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.argument("output_file", type=click.Path(), required=True)
def main(input_file: str | None, output_file: str) -> None:
    """Build PowerPoint presentation from JSON slides.

    Reads JSON slides from INPUT_FILE or stdin, outputs PPTX to OUTPUT_FILE.

    Example:
        deck-build slides.json output.pptx
        cat slides.json | deck-build - output.pptx
        deck-parse input.md | deck-build - output.pptx
    """
    # Read input
    if input_file and input_file != "-":
        with open(input_file, "r", encoding="utf-8") as f:
            slides_data = json.load(f)
    else:
        slides_data = json.load(sys.stdin)

    # Parse into Slide objects
    slides = [Slide(**slide_data) for slide_data in slides_data]

    # Get theme
    theme_obj = get_default_theme()

    # Generate presentation
    generate_presentation(slides, output_file, theme_obj)

    click.echo(f"✓ Generated PowerPoint: {output_file}")
    click.echo(f"  - {len(slides)} slides")
    click.echo("  - Speaker notes preserved")


if __name__ == "__main__":
    main()
