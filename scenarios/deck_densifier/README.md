# Deck Densifier

Compress presentation slides to "storyteller mode" using LLM intelligence - minimal on-slide content with rich speaker notes.

## Purpose

Transform verbose presentation slides into minimalist visual aids where:
- **Titles**: Maximum 5 words capturing the essence
- **Content**: Maximum 10 words total across all bullets
- **Speaker Notes**: Preserve all original content for verbal delivery

Perfect for presenters who want slides as visual anchors while delivering rich content verbally.

## Installation

```bash
cd scenarios/deck_densifier
uv add -e .
```

## Usage

### Basic Usage

```bash
# Compress a deck (creates input_compressed.json)
python -m scenarios.deck_densifier slides.json

# Specify output file
python -m scenarios.deck_densifier slides.json -o storyteller.json

# Use different LLM model
python -m scenarios.deck_densifier slides.json --model gpt-4

# Verbose mode (shows compression statistics)
python -m scenarios.deck_densifier slides.json -v
```

### Input Format

Expects JSON from deck-parse or deck_builder:

```json
[
  {
    "slide_type": "content",
    "title": "The Core Problem We Face Today",
    "content_blocks": [
      {"text": "I have more ideas than time", "is_bullet": true},
      {"text": "The constraint is execution speed", "is_bullet": true},
      {"text": "We need to amplify our capabilities", "is_bullet": true}
    ],
    "speaker_notes": "Existing notes here",
    "slide_number": 1
  }
]
```

### Output Format

Compressed slides with original content preserved:

```json
[
  {
    "slide_type": "content",
    "title": "Core Problem",
    "content_blocks": [
      {"text": "Ideas exceed time", "is_bullet": true}
    ],
    "speaker_notes": "Existing notes here\n\nOriginal slide content:\n• I have more ideas than time\n• The constraint is execution speed\n• We need to amplify our capabilities",
    "slide_number": 1
  }
]
```

## Module Contract

### Public Interface

```python
from scenarios.deck_densifier import compress_slide, densify_deck, Slide

# Compress a single slide
async def compress_slide(slide: Slide, model: str = "claude-3-5-sonnet-20241022") -> Slide:
    """Compress a single slide to storyteller mode."""

# Compress entire deck
async def densify_deck(
    input_file: Path,
    output_file: Optional[Path] = None,
    model: str = "claude-3-5-sonnet-20241022"
) -> Path:
    """Compress an entire deck to storyteller mode."""
```

### Compression Rules

1. **Title Slides**: Skipped (already minimal)
2. **Blank Slides**: Skipped
3. **Content/Section Slides**: Compressed with these rules:
   - Title: Max 5 words, preserve key meaning
   - Content: Max 10 words total across all blocks
   - Original content appended to speaker notes

### Error Handling

- Invalid JSON: Clear error message with abort
- LLM failures: Retries with fallback to word truncation
- Already compressed: Skip if within word limits

## Examples

### Example 1: Technical Presentation

**Before:**
```
Title: "Understanding the Architecture of Modern Microservices"
Content:
• Services communicate through well-defined APIs
• Each service has its own database
• Deployment is independent and scalable
```

**After:**
```
Title: "Microservices Architecture"
Content: "APIs, databases, independent deployment"
Speaker Notes: [Original content preserved here]
```

### Example 2: Business Strategy

**Before:**
```
Title: "Our Three-Year Strategic Growth Initiative"
Content:
• Expand into Asian markets by Q3 2025
• Double our engineering team size
• Launch AI-powered product features
```

**After:**
```
Title: "Three-Year Growth"
Content: "Asia expansion, team doubling"
Speaker Notes: [Original content preserved here]
```

## Performance Characteristics

- Processing time: ~2-5 seconds per slide (LLM dependent)
- Memory usage: Minimal (streaming processing)
- Concurrent slides: Processes sequentially (can be parallelized)
- Rate limits: Depends on LLM provider

## Testing

```bash
# Run tests
cd scenarios/deck_densifier
pytest tests/

# Test with sample data
python -m scenarios.deck_densifier tests/fixtures/sample_deck.json -v
```

## Regeneration Specification

This module can be fully regenerated from this README specification:

### Key Invariants
- 5-word title limit enforced
- 10-word content limit enforced
- Original content always preserved in speaker notes
- Slide structure and types maintained
- JSON input/output format unchanged

### Dependencies
- pydantic>=2.0.0 (data models)
- pydantic-ai (LLM integration)
- click>=8.0.0 (CLI interface)

### Files
- `densifier.py`: Core compression logic with PydanticAI
- `main.py`: Click CLI interface
- `models.py`: Reuses deck_builder models
- `__init__.py`: Public exports

## Philosophy Alignment

Follows Amplifier's ruthless simplicity:
- **Single purpose**: Compress slides to storyteller mode
- **Clear contract**: 5 words title, 10 words content
- **No complexity**: Direct LLM integration, simple fallbacks
- **Regeneratable**: This README contains full specification