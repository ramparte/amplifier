"""Main CLI entry point for the presenter pipeline."""

import asyncio
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from presenter.enhancer import OutlineEnhancer
from presenter.exporter import PowerPointExporter
from presenter.generator import SlideGenerator
from presenter.parser import OutlineParser

console = Console()


@click.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    help="Output PowerPoint file path",
)
@click.option(
    "--api-key",
    envvar="ANTHROPIC_API_KEY",
    help="Anthropic API key for AI enhancement",
)
@click.option(
    "--no-enhance",
    is_flag=True,
    help="Skip AI enhancement step",
)
@click.option(
    "--theme",
    type=str,
    default=None,
    help="Presentation theme (not yet implemented)",
)
def main(
    input_file: Path,
    output: Path | None,
    api_key: str | None,
    no_enhance: bool,
    theme: str | None,
):
    """Convert text outlines to PowerPoint presentations.

    INPUT_FILE: Path to markdown or text outline file
    """
    # Determine output path
    if output is None:
        output = input_file.with_suffix(".pptx")

    try:
        # Run the async pipeline
        asyncio.run(
            process_outline(
                input_file,
                output,
                api_key,
                skip_enhance=no_enhance,
            )
        )
        console.print(f"[green]✓[/green] Presentation saved to: {output}")

    except FileNotFoundError:
        console.print(f"[red]Error:[/red] Input file not found: {input_file}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        sys.exit(1)


async def process_outline(
    input_file: Path,
    output_file: Path,
    api_key: str | None,
    skip_enhance: bool = False,
):
    """Process an outline through the full pipeline.

    Args:
        input_file: Input outline file path
        output_file: Output PowerPoint file path
        api_key: Optional Anthropic API key
        skip_enhance: Skip AI enhancement if True
    """
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Parse outline
        task = progress.add_task("Parsing outline...", total=None)
        parser = OutlineParser()

        with open(input_file, encoding="utf-8") as f:
            text = f.read()

        outline = parser.parse(text)
        progress.update(task, completed=True)

        # Validate outline
        if not parser.validate(outline):
            raise ValueError("Invalid outline structure")

        # Enhance with AI (optional)
        if not skip_enhance and api_key:
            task = progress.add_task("Enhancing with AI...", total=None)
            enhancer = OutlineEnhancer(api_key)
            enriched = await enhancer.enhance(outline)
            progress.update(task, completed=True)
        else:
            # Create minimal enriched outline without AI
            from presenter.models import EnrichedOutline

            enriched = EnrichedOutline(
                outline=outline,
                suggestions={},
                concepts=[],
                recommendations=[],
            )

            if not skip_enhance and not api_key:
                console.print(
                    "[yellow]Warning:[/yellow] Skipping AI enhancement (no API key provided)"
                )

        # Generate slides
        task = progress.add_task("Generating slides...", total=None)
        generator = SlideGenerator()
        presentation = generator.generate(enriched)
        progress.update(task, completed=True)

        # Export to PowerPoint
        task = progress.add_task("Exporting to PowerPoint...", total=None)
        exporter = PowerPointExporter()
        exporter.export(presentation, output_file)
        progress.update(task, completed=True)


if __name__ == "__main__":
    main()