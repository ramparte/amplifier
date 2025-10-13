"""CLI for deck densifier tool."""

import asyncio
import json
from pathlib import Path

import click

from .densifier import densify_deck


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output", "-o", type=click.Path(path_type=Path), help="Output file path (default: input_compressed.json)"
)
@click.option("--model", default="claude-3-5-sonnet-20241022", help="LLM model to use for compression")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress information")
def main(input_file: Path, output: Path | None, model: str, verbose: bool) -> None:
    """Compress slides to storyteller mode (5-word title, 10-word content).

    Takes a JSON file with structured slides and compresses them for
    "storyteller mode" where the speaker delivers most content verbally.
    The original content is preserved in speaker notes.

    Example:
        python -m scenarios.deck_densifier slides.json -o compressed.json
    """
    if verbose:
        click.echo(f"Loading slides from: {input_file}")

    # Validate input is JSON
    try:
        with open(input_file, encoding="utf-8") as f:
            slides_data = json.load(f)
        if verbose:
            click.echo(f"Found {len(slides_data)} slides to compress")
    except json.JSONDecodeError as e:
        click.echo(f"Error: Invalid JSON file - {e}", err=True)
        raise click.Abort()
    except Exception as e:
        click.echo(f"Error reading file: {e}", err=True)
        raise click.Abort()

    # Run the async densifier
    try:
        output_path = asyncio.run(densify_deck(input_file, output, model))
        click.echo(f"✓ Compressed deck saved to: {output_path}")

        if verbose:
            # Show compression statistics
            with open(output_path, encoding="utf-8") as f:
                compressed_data = json.load(f)

            click.echo("\nCompression Statistics:")
            for i, (orig, comp) in enumerate(zip(slides_data, compressed_data, strict=False), 1):
                if orig.get("slide_type") not in ["title", "blank"]:
                    orig_title_words = len(orig.get("title", "").split())
                    comp_title_words = len(comp.get("title", "").split())

                    orig_content = " ".join(block.get("text", "") for block in orig.get("content_blocks", []))
                    comp_content = " ".join(block.get("text", "") for block in comp.get("content_blocks", []))

                    orig_content_words = len(orig_content.split()) if orig_content else 0
                    comp_content_words = len(comp_content.split()) if comp_content else 0

                    if orig_title_words > 5 or orig_content_words > 10:
                        click.echo(
                            f"  Slide {i}: Title {orig_title_words}→{comp_title_words} words, "
                            f"Content {orig_content_words}→{comp_content_words} words"
                        )

    except Exception as e:
        click.echo(f"Error during compression: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
