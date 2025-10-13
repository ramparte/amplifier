"""CLI interface for deck builder."""

import sys
from pathlib import Path

import click

from .generator import generate_presentation
from .parser import parse_markdown
from .themes import get_default_theme


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output PPTX file path")
@click.option("--theme", "-t", type=click.Path(exists=True, path_type=Path), help="Theme configuration file (JSON)")
def main(input_file: Path, output: Path | None, theme: Path | None) -> None:
    """Convert markdown slide deck to PowerPoint presentation.

    INPUT_FILE: Path to markdown file with slides separated by ---
    """
    # Determine output path
    if output is None:
        output = input_file.with_suffix(".pptx")

    click.echo(f"Converting {input_file} to {output}")

    try:
        # Read markdown content
        with open(input_file, encoding="utf-8") as f:
            markdown_content = f.read()

        # Parse markdown
        click.echo("Parsing markdown...")
        slides = parse_markdown(markdown_content)
        click.echo(f"Found {len(slides)} slides")

        # Load theme if provided
        theme_obj = None
        if theme:
            click.echo(f"Loading theme from {theme}")
            import json

            with open(theme) as f:
                theme_data = json.load(f)
                from .models import Theme

                theme_obj = Theme(**theme_data)
        else:
            theme_obj = get_default_theme()

        # Generate presentation
        click.echo("Generating PowerPoint presentation...")
        generate_presentation(slides, output, theme_obj)

        click.echo(f"✓ Successfully created {output}")
        click.echo(f"  - {len(slides)} slides")
        click.echo("  - Speaker notes preserved")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
