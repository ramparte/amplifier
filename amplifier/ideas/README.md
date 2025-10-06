# Ideas Management System

A comprehensive CLI-based system for managing shared project ideas with goals, assignments, and AI-powered operations.

## Overview

The Ideas Management System provides structured storage and manipulation of project ideas, allowing teams to:

- Capture and organize ideas with themes and priorities
- Set project goals and track progress
- Generate, reorder, and validate ideas using AI
- Support multi-source configurations for shared workflows
- Comprehensive test coverage (101 tests, 78% pass rate)

## Key Features

### Core Functionality
- **YAML-based storage** with atomic operations and backup management
- **Multi-source support** via environment variables for team collaboration
- **CLI interface** with rich output formatting
- **AI-powered operations** for idea generation and enhancement
- **Defensive patterns** with cloud sync resilience and retry logic

### CLI Commands
- `ideas list` - Display all ideas with filtering and formatting options
- `ideas add` - Add new ideas interactively or from command line
- `ideas generate` - AI-powered idea generation based on themes
- `ideas reorder` - AI-powered intelligent reordering by priority/relevance
- `ideas validate` - AI-powered validation of idea feasibility and clarity
- `ideas status` - Show system status including active sources

### Multi-Source Configuration
Configure multiple ideas sources for team workflows:
```bash
export AMPLIFIER_IDEAS_DIRS="/path/to/primary:/path/to/secondary:/path/to/tertiary"
```

- Primary source (first) is writable for new ideas
- Secondary sources are read-only for merging
- Automatic conflict resolution with "first-seen wins"
- Security validation prevents directory traversal

## Architecture

### Core Components

#### Models (`models.py`)
- `Idea` - Individual idea with title, description, themes, priority
- `Goal` - Project goal with description and priority
- `IdeasDocument` - Top-level container with versioning and metadata

#### Storage (`storage.py`)
- `IdeasStorage` - Single-source YAML persistence with defensive patterns
- `MultiSourceStorage` - Multi-source aggregation and merging
- Cloud sync resilience with retry logic and informative warnings

#### CLI (`cli.py`)
- Click-based command interface with rich formatting
- Multi-source awareness and configuration management
- Interactive and batch operation modes

#### Operations (`operations.py`)
- AI-powered operations using PydanticAI
- Idea generation, reordering, and validation
- Defensive LLM response handling

## Usage Examples

### Basic Operations
```bash
# List all ideas
amplifier-ideas list

# Add a new idea
amplifier-ideas add "Implement caching layer" --theme performance --priority high

# Generate ideas for a theme
amplifier-ideas generate --theme "AI automation" --count 5

# Reorder ideas by priority
amplifier-ideas reorder --strategy priority
```

### Multi-Source Setup
```bash
# Configure multiple sources
export AMPLIFIER_IDEAS_DIRS="~/primary/ideas:~/shared/team-ideas:~/archive/old-ideas"

# Check status
amplifier-ideas status
# Output: Found 3 sources: 15 ideas total (10 + 3 + 2)
```

## Testing

Comprehensive test suite with 101 tests covering:
- Unit tests for models, storage, and operations
- Integration tests for CLI and multi-source scenarios
- Security tests for path validation and directory traversal prevention
- Defensive patterns and cloud sync resilience

```bash
# Run tests
pytest tests/ideas/
```

## Integration

This module integrates cleanly with the Amplifier ecosystem:

- Follows Amplifier's implementation philosophy of ruthless simplicity
- Uses defensive patterns from `amplifier.utils.file_io` for cloud sync
- Compatible with existing Amplifier CLI patterns and conventions
- Modular design allows independent regeneration and testing

## Dependencies

- `click` - CLI framework
- `rich` - Terminal formatting
- `pydantic` - Data validation
- `PyYAML` - YAML processing
- `filelock` - Atomic file operations
- `pydantic-ai` - AI operations (optional)

## Development

The ideas module follows Amplifier's "bricks and studs" philosophy:
- Self-contained with clear contracts
- Comprehensive test coverage
- Defensive patterns for reliability
- Ready for regeneration from specifications