# Deck Builder Module

A self-contained PowerPoint deck builder that converts markdown slide decks to PPTX format.

## Purpose

Transform markdown-formatted slide decks into editable PowerPoint presentations, preserving structure, content, and speaker notes while using native PowerPoint features for maximum editability.

## Module Contract

### Input
- **Type**: Markdown file
- **Format**: Slides separated by `---`, with title (##), content (bullets/text), and speaker notes sections
- **Example**: `docs/AMPLIFIER_WALKING_DECK.md`

### Output
- **Type**: PowerPoint PPTX file
- **Format**: Native PowerPoint presentation with editable text placeholders
- **Features**: Preserved speaker notes, consistent styling, native layouts

### Side Effects
- Writes PPTX file to specified output path
- No network calls or external dependencies

### Dependencies
- python-pptx: PowerPoint generation
- click: CLI interface
- pydantic: Data validation

## Public Interface

```python
from scenarios.deck_builder import parse_markdown, generate_presentation

# Parse markdown to structured slides
slides = parse_markdown(markdown_content)

# Generate PowerPoint presentation
generate_presentation(slides, output_path="deck.pptx")
```

## CLI Usage

```bash
# Generate presentation
python -m scenarios.deck_builder.main docs/AMPLIFIER_WALKING_DECK.md --output deck.pptx

# Or via make command
make deck-build INPUT=docs/AMPLIFIER_WALKING_DECK.md OUTPUT=deck.pptx
```

## Architecture

### Modules

- **parser.py**: Parse markdown → structured Slide objects
- **models.py**: Data models (Slide, SlideType, ContentBlock, Theme)
- **layouts.py**: Map slide intent → PowerPoint layout selection
- **generator.py**: Generate PPTX using python-pptx library
- **themes.py**: Theme/styling system
- **main.py**: CLI interface

### Design Principles

1. **Native PowerPoint Features**: Use placeholders and layouts, not absolute positioning
2. **Editability First**: All content remains fully editable
3. **Simple Theme**: Clean professional default
4. **Ruthless Simplicity**: MVP that works, enhanced later if needed

## Performance Characteristics

- Processing time: ~1-2 seconds per 20 slides
- Memory usage: Minimal (< 50MB for typical decks)
- No concurrent processing needed

## Testing

Run tests:
```bash
pytest scenarios/deck_builder/tests/
```

## Regeneration Specification

This module can be regenerated from this specification. Key invariants:
- Markdown parsing logic for slide separation
- Speaker notes preservation
- Native PowerPoint layout usage
- CLI interface signatures