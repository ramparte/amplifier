# Presenter Pipeline

A modular pipeline for converting text outlines to PowerPoint presentations with optional AI enhancement.

## Features

- **Parse** markdown/text outlines with hierarchical structure
- **Enhance** with AI-powered suggestions (optional, requires Anthropic API key)
- **Generate** slides from structured content
- **Export** to PowerPoint (.pptx) format
- Clean modular architecture following brick-and-stud philosophy

## Installation

```bash
# Install dependencies
make install

# Or using uv directly
uv pip install -e .
```

## Usage

```bash
# Basic usage (no AI enhancement)
presenter input.md --no-enhance

# With AI enhancement
presenter input.md --api-key YOUR_ANTHROPIC_KEY

# Specify output file
presenter input.md -o output.pptx --no-enhance

# Using environment variable for API key
export ANTHROPIC_API_KEY=your_key_here
presenter input.md
```

## Development

```bash
# Run tests
make test

# Run specific test
make test-one TEST=tests/test_parser.py::test_parse_simple

# Run all checks
make check

# Format code
make format
```

## Module Architecture

Following the brick-and-stud philosophy:

1. **parser.py** - Converts text to structured OutlineNode tree
2. **enhancer.py** - AI-powered enrichment with suggestions
3. **generator.py** - Transforms enriched outline to Slide objects
4. **exporter.py** - Creates PowerPoint files from Slide objects
5. **main.py** - CLI orchestrator

Each module is self-contained with clear contracts defined in `models.py`.

## Input Format

Supports markdown with:
- Headers (`#`, `##`, etc.)
- Bullet points (`-`, `*`, `+`)
- Code blocks
- YAML frontmatter
- Plain text paragraphs

## Design Philosophy

Built with ruthless simplicity:
- Each module under 200 lines
- Clear single responsibility
- Minimal dependencies
- Working code over perfect abstractions

## License

MIT