"""CLI tool to parse markdown slides into JSON."""

import json
import sys
from pathlib import Path

import click

from .parser import parse_markdown


@click.command()
@click.argument("input_file", type=click.Path(exists=True), required=False)
@click.option("--output", "-o", type=click.Path(), help="Output JSON file (default: stdout)")
def main(input_file: str | None, output: str | None) -> None:
    """Parse markdown slides into JSON format.

    Reads markdown from INPUT_FILE or stdin, outputs JSON to --output or stdout.

    Example:
        deck-parse input.md > slides.json
        deck-parse input.md -o slides.json
        cat input.md | deck-parse > slides.json
    """
    # Read input
    if input_file:
        with open(input_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()
    else:
        markdown_content = sys.stdin.read()

    # Parse markdown
    slides = parse_markdown(markdown_content)

    # Convert to JSON
    slides_json = [slide.model_dump(mode="json") for slide in slides]
    json_output = json.dumps(slides_json, indent=2, ensure_ascii=False)

    # Write output
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_output)
        click.echo(f"✓ Parsed {len(slides)} slides to: {output}", err=True)
    else:
        click.echo(json_output)


if __name__ == "__main__":
    main()
