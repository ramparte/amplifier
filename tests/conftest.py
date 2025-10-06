"""
Pytest configuration and shared fixtures for tests.

This file provides common fixtures and configuration for all tests,
following the modular design philosophy.
"""

import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from amplifier.ideas.models import Goal
from amplifier.ideas.models import Idea


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_ideas_file(temp_dir: Path) -> Path:
    """Create a temporary ideas file"""
    file_path = temp_dir / "test_ideas.json"
    # Create empty YAML structure
    import yaml

    empty_doc = {"version": "1.0", "ideas": [], "goals": [], "metadata": {}, "history": []}
    file_path.write_text(yaml.dump(empty_doc))
    return file_path


@pytest.fixture
def sample_goals() -> list[Goal]:
    """Create sample goals for testing"""
    return [
        Goal(description="Improve system performance by 50% in the next quarter", priority=1),
        Goal(description="Implement AI-powered features for better user experience", priority=2),
        Goal(description="Reduce technical debt and improve code maintainability", priority=3),
    ]


@pytest.fixture
def sample_ideas() -> list[Idea]:
    """Create sample ideas for testing"""
    return [
        Idea(
            title="Implement Event Sourcing",
            description="Add event sourcing pattern to capture all state changes",
            themes=["architecture", "event-driven"],
            priority="high",
        ),
        Idea(
            title="Add NLP Pipeline",
            description="Build natural language processing pipeline for text analysis",
            themes=["AI", "NLP", "machine-learning"],
            priority="medium",
        ),
        Idea(
            title="Optimize Query Performance",
            description="Implement query caching and indexing strategy",
            themes=["performance", "database", "caching"],
            priority="high",
        ),
    ]


@pytest.fixture
def multi_source_env(temp_dir: Path) -> Generator[dict[str, Any], None, None]:
    """Set up multi-source environment variables"""
    # Create test directories
    source1 = temp_dir / "source1"
    source2 = temp_dir / "source2"
    source1.mkdir()
    source2.mkdir()

    # Create ideas files with YAML structure
    import yaml

    empty_doc = {"version": "1.0", "ideas": [], "goals": [], "metadata": {}, "history": []}
    (source1 / "ideas.json").write_text(yaml.dump(empty_doc))
    (source2 / "ideas.json").write_text(yaml.dump(empty_doc))

    old_env = os.environ.copy()

    # Set multi-source environment
    os.environ["IDEAS_FILES"] = f"{source1}/ideas.json,{source2}/ideas.json"
    os.environ["DEFAULT_IDEAS_FILE"] = str(source1 / "ideas.json")

    yield {"source1": source1, "source2": source2, "files": [source1 / "ideas.json", source2 / "ideas.json"]}

    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def mock_llm_client() -> AsyncMock:
    """Create a mock LLM client for operations testing"""
    mock = AsyncMock()

    # Mock response for reorder operation
    mock.complete.return_value = MagicMock(
        parsed=[
            Idea(title="Priority Idea", description="Most important idea", themes=["priority"]),
            Idea(title="Secondary Idea", description="Less important", themes=["secondary"]),
        ]
    )

    return mock


@pytest.fixture
def isolated_env() -> Generator[None, None, None]:
    """Isolate environment variables for testing"""
    old_env = os.environ.copy()

    # Clear ideas-related env vars
    env_vars = ["IDEAS_FILE", "IDEAS_FILES", "DEFAULT_IDEAS_FILE"]
    for var in env_vars:
        os.environ.pop(var, None)

    yield

    # Restore environment
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def cli_runner():
    """Create a Click testing runner"""
    from click.testing import CliRunner

    return CliRunner()
