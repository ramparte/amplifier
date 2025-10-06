# Presenter Pipeline Architecture

## Overview
A modular, extensible pipeline for converting text outlines into professional PowerPoint presentations with rich graphics and consistent styling.

## Core Design Principles
1. **Modular Architecture**: Each component has a single responsibility and clear interfaces
2. **Intermediate Representation**: Use JSON/YAML for slide data that is both human and LLM readable
3. **Progressive Enhancement**: Start with basic text, progressively add styling, graphics, animations
4. **Stateless Processing**: Each module can run independently given proper inputs
5. **Version Control Friendly**: All intermediate formats are text-based and diffable

## System Architecture

```
Text Outline → [Parser] → Structured Outline
                ↓
         [Outline Analyzer]
                ↓
         Enriched Outline
                ↓
         [Slide Generator]
                ↓
         Individual Slides (JSON)
                ↓
         [Style Engine] ← [Theme Manager]
                ↓                ↑
         Styled Slides      [Asset Manager]
                ↓
         [Layout Engine]
                ↓
         [Presentation Assembler]
                ↓
         Complete Presentation (JSON)
                ↓
         [Export Engine]
                ↓
         PowerPoint File (.pptx)
```

## Module Definitions

### 1. Input Parser (`presenter/parser/`)
- Parses various outline formats (Markdown, plain text, OPML)
- Detects hierarchy and structure
- Outputs: Structured JSON outline

### 2. Outline Analyzer (`presenter/analyzer/`)
- Uses LLM to understand content intent
- Suggests slide types (title, bullet, comparison, timeline, etc.)
- Identifies key concepts for visualization
- Outputs: Enriched outline with metadata

### 3. Slide Generator (`presenter/generator/`)
- Converts outline nodes to individual slides
- Determines appropriate slide layouts
- Generates speaker notes
- Outputs: Individual slide JSON files

### 4. Style Engine (`presenter/style/`)
- Applies design themes
- Ensures visual consistency
- Manages fonts, colors, spacing
- Outputs: Styled slide JSON

### 5. Asset Manager (`presenter/assets/`)
- Generates/fetches images, icons, charts
- Manages asset library
- Handles caching and optimization
- Outputs: Asset references and files

### 6. Layout Engine (`presenter/layout/`)
- Positions elements on slides
- Handles responsive scaling
- Manages whitespace and alignment
- Outputs: Positioned slide elements

### 7. Presentation Assembler (`presenter/assembler/`)
- Combines individual slides
- Manages transitions and animations
- Handles master slides and templates
- Outputs: Complete presentation JSON

### 8. Export Engine (`presenter/export/`)
- Converts JSON to PowerPoint (python-pptx)
- Supports multiple export formats (PDF, HTML/S5)
- Handles format-specific optimizations
- Outputs: Final presentation files

### 9. CLI Interface (`presenter/cli/`)
- Interactive command-line interface
- Conversation flow with user
- Progress visualization
- Command orchestration

### 10. Storage Manager (`presenter/storage/`)
- Persists presentations and slides
- Manages versioning and history
- Handles merge operations
- Database: SQLite for metadata, filesystem for content

### 11. LLM Integration (`presenter/llm/`)
- Manages LLM connections
- Handles prompts and responses
- Caches responses for efficiency
- Supports multiple providers (OpenAI, Anthropic)

## Data Formats

### Slide JSON Schema
```json
{
  "id": "unique-slide-id",
  "version": "1.0",
  "type": "bullet|title|comparison|timeline|image|chart|custom",
  "title": "Slide Title",
  "content": {
    "main": ["content items"],
    "notes": "Speaker notes"
  },
  "style": {
    "theme": "theme-id",
    "layout": "layout-id",
    "customizations": {}
  },
  "assets": [
    {"type": "image", "src": "path/to/image", "position": {}}
  ],
  "metadata": {
    "created": "timestamp",
    "modified": "timestamp",
    "tags": [],
    "source": "outline-node-id"
  },
  "transitions": {
    "in": "fade|slide|zoom",
    "out": "fade|slide|zoom"
  }
}
```

### Presentation JSON Schema
```json
{
  "id": "presentation-id",
  "version": "1.0",
  "title": "Presentation Title",
  "metadata": {
    "author": "name",
    "created": "timestamp",
    "modified": "timestamp",
    "description": ""
  },
  "theme": {
    "id": "theme-id",
    "overrides": {}
  },
  "slides": [
    {"ref": "slide-id", "order": 1}
  ],
  "settings": {
    "aspectRatio": "16:9|4:3",
    "slideNumbers": true,
    "footer": ""
  }
}
```

## Technology Stack
- **Language**: Python 3.11+
- **CLI Framework**: Click
- **LLM**: Claude API via anthropic-sdk-python
- **PowerPoint**: python-pptx
- **Image Generation**: Pillow, potentially DALL-E API
- **Charts**: matplotlib/plotly for chart generation
- **Storage**: SQLite + filesystem
- **Testing**: pytest with fixtures
- **Config**: TOML/YAML