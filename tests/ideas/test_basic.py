"""
Basic tests to verify ideas system functionality
"""

import tempfile
from pathlib import Path

import yaml

from amplifier.ideas.models import Goal
from amplifier.ideas.models import Idea
from amplifier.ideas.models import IdeasDocument
from amplifier.ideas.storage import IdeasStorage


def test_idea_creation():
    """Test creating an idea with all fields"""
    idea = Idea(
        title="Test Idea",
        description="Test description",
        themes=["test", "example"],
        priority="high",
        notes="Test notes",
    )

    assert idea.title == "Test Idea"
    assert idea.description == "Test description"
    assert "test" in idea.themes
    assert idea.priority == "high"
    assert idea.assignee is None  # Default
    assert idea.id.startswith("idea_")


def test_ideas_document():
    """Test IdeasDocument operations"""
    doc = IdeasDocument()

    # Add idea
    idea = Idea(title="Test", description="Desc")
    doc.add_idea(idea)

    assert len(doc.ideas) == 1
    assert doc.ideas[0].title == "Test"

    # Add goal
    goal = Goal(description="Improve performance by 50%")
    doc.add_goal(goal)

    assert len(doc.goals) == 1
    assert doc.goals[0].description == "Improve performance by 50%"


def test_storage_save_and_load():
    """Test saving and loading ideas via storage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.yaml"
        storage = IdeasStorage(str(file_path))

        # Create and save document
        doc = IdeasDocument()
        idea = Idea(title="Storage Test", description="Testing storage")
        doc.add_idea(idea)
        storage.save(doc)

        # Verify file exists and contains data
        assert file_path.exists()

        # Load and verify
        loaded_doc = storage.load()
        assert len(loaded_doc.ideas) == 1
        assert loaded_doc.ideas[0].title == "Storage Test"


def test_yaml_format():
    """Test that saved file has correct YAML format"""
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "test.yaml"
        storage = IdeasStorage(str(file_path))

        doc = IdeasDocument()
        doc.add_idea(Idea(title="YAML Test", description="Test"))
        storage.save(doc)

        # Load as raw YAML
        data = yaml.safe_load(file_path.read_text())

        assert data["version"] == "1.0"
        assert "ideas" in data
        assert len(data["ideas"]) == 1
        assert data["ideas"][0]["title"] == "YAML Test"
        assert "metadata" in data
        assert "history" in data
