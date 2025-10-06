"""
Unit tests for amplifier.ideas.models module.

Tests Pydantic validation, idea/goal operations, document structure,
and business logic methods.
"""

from datetime import UTC
from datetime import datetime

import pytest
from pydantic import ValidationError

from amplifier.ideas.models import Goal
from amplifier.ideas.models import HistoryEntry
from amplifier.ideas.models import Idea
from amplifier.ideas.models import IdeasDocument
from amplifier.ideas.models import Metadata


class TestGoal:
    """Test the Goal model"""

    def test_goal_creation_with_defaults(self):
        """Test creating a Goal with default values"""
        goal = Goal(description="Improve user experience")

        assert goal.description == "Improve user experience"
        assert goal.priority == 1
        assert goal.active is True
        assert goal.id.startswith("goal_")
        assert isinstance(goal.created, datetime)

    def test_goal_validation_description_length(self):
        """Test goal description validation"""
        # Too short
        with pytest.raises(ValidationError, match="at least 10 characters"):
            Goal(description="short")

        # Too long
        long_desc = "x" * 501
        with pytest.raises(ValidationError, match="at most 500 characters"):
            Goal(description=long_desc)

        # Just right
        goal = Goal(description="This is exactly long enough")
        assert goal.description == "This is exactly long enough"

    def test_goal_priority_validation(self):
        """Test goal priority must be >= 1"""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            Goal(description="Test goal", priority=0)

        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            Goal(description="Test goal", priority=-1)

        # Valid priority
        goal = Goal(description="Test goal", priority=5)
        assert goal.priority == 5

    def test_goal_custom_values(self):
        """Test creating goal with custom values"""
        custom_time = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        goal = Goal(description="Custom goal description", priority=3, created=custom_time, active=False)

        assert goal.priority == 3
        assert goal.created == custom_time
        assert goal.active is False


class TestIdea:
    """Test the Idea model"""

    def test_idea_creation_with_defaults(self):
        """Test creating an Idea with minimal required fields"""
        idea = Idea(title="Test Idea")

        assert idea.title == "Test Idea"
        assert idea.description == ""
        assert idea.assignee is None
        assert idea.rank is None
        assert idea.themes == []
        assert idea.priority == "medium"
        assert idea.notes is None
        assert idea.id.startswith("idea_")
        assert isinstance(idea.created, datetime)
        assert isinstance(idea.modified, datetime)

    def test_idea_title_validation(self):
        """Test idea title validation"""
        # Too short
        with pytest.raises(ValidationError, match="at least 3 characters"):
            Idea(title="ab")

        # Too long
        long_title = "x" * 201
        with pytest.raises(ValidationError, match="at most 200 characters"):
            Idea(title=long_title)

        # Just right
        idea = Idea(title="Good Title")
        assert idea.title == "Good Title"

    def test_idea_description_validation(self):
        """Test idea description validation"""
        # Too long
        long_desc = "x" * 2001
        with pytest.raises(ValidationError, match="at most 2000 characters"):
            Idea(title="Test", description=long_desc)

        # Valid description
        desc = "This is a valid description"
        idea = Idea(title="Test", description=desc)
        assert idea.description == desc

    def test_idea_priority_validation(self):
        """Test idea priority validation"""
        # Valid priorities
        for priority in ["high", "medium", "low"]:
            idea = Idea(title="Test", priority=priority)  # type: ignore
            assert idea.priority == priority

        # Invalid priority should raise ValidationError
        with pytest.raises(ValidationError):
            Idea(title="Test", priority="urgent")  # type: ignore

    def test_idea_is_assigned(self):
        """Test is_assigned method"""
        unassigned = Idea(title="Unassigned")
        assert not unassigned.is_assigned()

        assigned = Idea(title="Assigned", assignee="alice")
        assert assigned.is_assigned()

    def test_idea_update_modified(self):
        """Test update_modified method"""
        idea = Idea(title="Test")
        original_time = idea.modified

        # Small delay to ensure time difference
        import time

        time.sleep(0.001)

        idea.update_modified()
        assert idea.modified > original_time

    def test_idea_with_custom_values(self):
        """Test creating idea with all custom values"""
        custom_created = datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC)
        custom_modified = datetime(2024, 1, 1, 11, 0, 0, tzinfo=UTC)

        idea = Idea(
            title="Custom Idea",
            description="Custom description",
            assignee="bob",
            rank=2,
            themes=["ui", "performance"],
            priority="high",
            created=custom_created,
            modified=custom_modified,
            notes="Some notes",
        )

        assert idea.title == "Custom Idea"
        assert idea.assignee == "bob"
        assert idea.rank == 2
        assert idea.themes == ["ui", "performance"]
        assert idea.priority == "high"
        assert idea.created == custom_created
        assert idea.modified == custom_modified
        assert idea.notes == "Some notes"


class TestHistoryEntry:
    """Test the HistoryEntry model"""

    def test_history_entry_creation(self):
        """Test creating history entries"""
        entry = HistoryEntry(action="create", details="Created new idea")

        assert entry.action == "create"
        assert entry.user == "system"  # default
        assert entry.details == "Created new idea"
        assert isinstance(entry.timestamp, datetime)

    def test_history_entry_actions_validation(self):
        """Test valid history actions"""
        valid_actions = ["create", "update", "assign", "unassign", "reorder", "delete"]

        for action in valid_actions:
            entry = HistoryEntry(action=action, details="Test action")  # type: ignore
            assert entry.action == action

        # Invalid action
        with pytest.raises(ValidationError):
            HistoryEntry(action="invalid", details="Test")  # type: ignore

    def test_history_entry_custom_user(self):
        """Test history entry with custom user"""
        entry = HistoryEntry(action="update", user="alice", details="Updated idea title")

        assert entry.user == "alice"


class TestMetadata:
    """Test the Metadata model"""

    def test_metadata_creation(self):
        """Test creating metadata with defaults"""
        meta = Metadata()

        assert meta.total_ideas == 0
        assert meta.total_goals == 0
        assert meta.last_modified_by == "system"
        assert isinstance(meta.last_modified, datetime)

    def test_metadata_validation(self):
        """Test metadata validation"""
        # Negative counts should fail
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Metadata(total_ideas=-1)

        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            Metadata(total_goals=-1)

        # Valid counts
        meta = Metadata(total_ideas=5, total_goals=2)
        assert meta.total_ideas == 5
        assert meta.total_goals == 2


class TestIdeasDocument:
    """Test the complete IdeasDocument model and its methods"""

    def test_document_creation_empty(self):
        """Test creating empty ideas document"""
        doc = IdeasDocument()

        assert doc.version == "1.0"
        assert len(doc.goals) == 0
        assert len(doc.ideas) == 0
        assert len(doc.history) == 0
        assert isinstance(doc.metadata, Metadata)

    def test_add_idea(self):
        """Test adding ideas to document"""
        doc = IdeasDocument()
        idea = Idea(title="Test Idea")

        doc.add_idea(idea)

        assert len(doc.ideas) == 1
        assert doc.ideas[0] == idea
        assert doc.metadata.total_ideas == 1
        assert len(doc.history) == 1
        assert doc.history[0].action == "create"

    def test_add_idea_with_custom_user(self):
        """Test adding idea with custom user"""
        doc = IdeasDocument()
        idea = Idea(title="Test Idea")

        doc.add_idea(idea, user="alice")

        assert doc.history[0].user == "alice"
        assert doc.metadata.last_modified_by == "alice"

    def test_remove_idea_success(self):
        """Test successfully removing an idea"""
        doc = IdeasDocument()
        idea = Idea(title="Test Idea")
        doc.add_idea(idea)

        result = doc.remove_idea(idea.id)

        assert result is True
        assert len(doc.ideas) == 0
        assert doc.metadata.total_ideas == 0
        assert len(doc.history) == 2  # create + delete
        assert doc.history[1].action == "delete"

    def test_remove_idea_not_found(self):
        """Test removing non-existent idea"""
        doc = IdeasDocument()

        result = doc.remove_idea("nonexistent_id")

        assert result is False
        assert len(doc.history) == 0  # No history entry for failed removal

    def test_find_idea(self):
        """Test finding ideas by ID"""
        doc = IdeasDocument()
        idea1 = Idea(title="First Idea")
        idea2 = Idea(title="Second Idea")

        doc.add_idea(idea1)
        doc.add_idea(idea2)

        found = doc.find_idea(idea1.id)
        assert found == idea1

        not_found = doc.find_idea("nonexistent")
        assert not_found is None

    def test_assign_idea_success(self):
        """Test successfully assigning an idea"""
        doc = IdeasDocument()
        idea = Idea(title="Test Idea")
        doc.add_idea(idea)

        result = doc.assign_idea(idea.id, "alice")

        assert result is True
        assert idea.assignee == "alice"
        assert idea.rank == 0  # First in alice's queue
        assert len(doc.history) == 2  # create + assign

    def test_assign_idea_to_user_with_existing_queue(self):
        """Test assigning idea to user who already has ideas"""
        doc = IdeasDocument()

        # Create two ideas already assigned to alice
        idea1 = Idea(title="First")
        idea2 = Idea(title="Second")
        doc.add_idea(idea1)
        doc.add_idea(idea2)
        doc.assign_idea(idea1.id, "alice")
        doc.assign_idea(idea2.id, "alice")

        # Add new idea for alice
        idea3 = Idea(title="Third")
        doc.add_idea(idea3)
        doc.assign_idea(idea3.id, "alice")

        assert idea3.rank == 2  # Third in queue (0-indexed)

    def test_assign_idea_reassignment(self):
        """Test reassigning idea from one user to another"""
        doc = IdeasDocument()
        idea = Idea(title="Test Idea")
        doc.add_idea(idea)
        doc.assign_idea(idea.id, "alice")

        # Reassign to bob
        result = doc.assign_idea(idea.id, "bob")

        assert result is True
        assert idea.assignee == "bob"
        # Should have create, assign, and update history entries
        assert len(doc.history) >= 3

    def test_assign_nonexistent_idea(self):
        """Test assigning nonexistent idea"""
        doc = IdeasDocument()

        result = doc.assign_idea("nonexistent", "alice")

        assert result is False

    def test_get_user_queue(self):
        """Test getting user's assigned ideas"""
        doc = IdeasDocument()

        # Create ideas for different users
        idea1 = Idea(title="Alice 1")
        idea2 = Idea(title="Bob 1")
        idea3 = Idea(title="Alice 2")

        doc.add_idea(idea1)
        doc.add_idea(idea2)
        doc.add_idea(idea3)

        doc.assign_idea(idea1.id, "alice")
        doc.assign_idea(idea2.id, "bob")
        doc.assign_idea(idea3.id, "alice")

        alice_queue = doc.get_user_queue("alice")
        bob_queue = doc.get_user_queue("bob")

        assert len(alice_queue) == 2
        assert len(bob_queue) == 1
        assert alice_queue[0].title in ["Alice 1", "Alice 2"]
        assert bob_queue[0].title == "Bob 1"

    def test_get_user_queue_sorted_by_rank(self):
        """Test user queue is sorted by rank"""
        doc = IdeasDocument()

        ideas = []
        for i in range(3):
            idea = Idea(title=f"Idea {i}")
            doc.add_idea(idea)
            doc.assign_idea(idea.id, "alice")
            ideas.append(idea)

        # Manually adjust ranks to test sorting
        ideas[1].rank = 0  # Should be first
        ideas[0].rank = 2  # Should be last
        ideas[2].rank = 1  # Should be middle

        queue = doc.get_user_queue("alice")

        assert queue[0] == ideas[1]  # rank 0
        assert queue[1] == ideas[2]  # rank 1
        assert queue[2] == ideas[0]  # rank 2

    def test_get_unassigned(self):
        """Test getting unassigned ideas"""
        doc = IdeasDocument()

        assigned = Idea(title="Assigned")
        unassigned1 = Idea(title="Unassigned 1")
        unassigned2 = Idea(title="Unassigned 2")

        doc.add_idea(assigned)
        doc.add_idea(unassigned1)
        doc.add_idea(unassigned2)

        doc.assign_idea(assigned.id, "alice")

        unassigned = doc.get_unassigned()

        assert len(unassigned) == 2
        titles = {idea.title for idea in unassigned}
        assert titles == {"Unassigned 1", "Unassigned 2"}

    def test_get_by_theme(self):
        """Test filtering ideas by theme"""
        doc = IdeasDocument()

        ui_idea = Idea(title="UI Idea", themes=["ui", "design"])
        backend_idea = Idea(title="Backend Idea", themes=["backend", "api"])
        mixed_idea = Idea(title="Mixed Idea", themes=["ui", "backend"])

        doc.add_idea(ui_idea)
        doc.add_idea(backend_idea)
        doc.add_idea(mixed_idea)

        ui_ideas = doc.get_by_theme("ui")
        backend_ideas = doc.get_by_theme("backend")

        assert len(ui_ideas) == 2  # ui_idea and mixed_idea
        assert len(backend_ideas) == 2  # backend_idea and mixed_idea

        # Test case insensitive
        ui_ideas_upper = doc.get_by_theme("UI")
        assert len(ui_ideas_upper) == 2

    def test_get_by_priority(self):
        """Test filtering ideas by priority"""
        doc = IdeasDocument()

        high_idea = Idea(title="High Priority", priority="high")
        medium_idea = Idea(title="Medium Priority", priority="medium")
        low_idea = Idea(title="Low Priority", priority="low")

        doc.add_idea(high_idea)
        doc.add_idea(medium_idea)
        doc.add_idea(low_idea)

        high_ideas = doc.get_by_priority("high")
        medium_ideas = doc.get_by_priority("medium")
        low_ideas = doc.get_by_priority("low")

        assert len(high_ideas) == 1
        assert len(medium_ideas) == 1
        assert len(low_ideas) == 1
        assert high_ideas[0].title == "High Priority"

    def test_add_goal(self):
        """Test adding goals to document"""
        doc = IdeasDocument()
        goal = Goal(description="Improve user experience")

        doc.add_goal(goal)

        assert len(doc.goals) == 1
        assert doc.goals[0] == goal
        assert doc.metadata.total_goals == 1
        assert len(doc.history) == 1
        assert doc.history[0].action == "create"

    def test_get_active_goals_sorted(self):
        """Test getting active goals sorted by priority"""
        doc = IdeasDocument()

        goal1 = Goal(description="Low priority goal", priority=3)
        goal2 = Goal(description="High priority goal", priority=1)
        goal3 = Goal(description="Inactive goal", priority=2, active=False)

        doc.add_goal(goal1)
        doc.add_goal(goal2)
        doc.add_goal(goal3)

        active_goals = doc.get_active_goals()

        assert len(active_goals) == 2  # Only active goals
        assert active_goals[0] == goal2  # priority 1 first
        assert active_goals[1] == goal1  # priority 3 second

    def test_update_metadata(self):
        """Test updating document metadata"""
        doc = IdeasDocument()

        # Add some content
        doc.add_idea(Idea(title="Test Idea"))
        doc.add_goal(Goal(description="Test Goal"))

        original_time = doc.metadata.last_modified

        import time

        time.sleep(0.001)

        doc.update_metadata("alice")

        assert doc.metadata.total_ideas == 1
        assert doc.metadata.total_goals == 1
        assert doc.metadata.last_modified_by == "alice"
        assert doc.metadata.last_modified > original_time

    def test_history_size_limit(self):
        """Test history size is limited to prevent unbounded growth"""
        doc = IdeasDocument()

        # Add many ideas to generate history
        for i in range(1005):  # More than the 1000 limit
            idea = Idea(title=f"Idea {i}")
            doc.add_idea(idea)

        # History should be capped
        assert len(doc.history) <= 1000

    def test_version_validation(self):
        """Test document version validation"""
        # Valid version
        doc = IdeasDocument(version="2.1")
        assert doc.version == "2.1"

        # Invalid version format
        with pytest.raises(ValidationError, match="pattern"):
            IdeasDocument(version="invalid")

        with pytest.raises(ValidationError, match="pattern"):
            IdeasDocument(version="1.0.0")  # Too many parts


class TestDocumentIntegration:
    """Test complex document operations"""

    def test_complex_workflow(self):
        """Test a complete workflow with multiple operations"""
        doc = IdeasDocument()

        # Add goals
        goal1 = Goal(description="Improve user experience", priority=1)
        goal2 = Goal(description="Increase performance", priority=2)
        doc.add_goal(goal1)
        doc.add_goal(goal2)

        # Add ideas
        ideas = []
        for i in range(5):
            idea = Idea(
                title=f"Idea {i}",
                description=f"Description {i}",
                themes=["ui" if i % 2 == 0 else "backend"],
                priority="high" if i < 2 else "medium",
            )
            doc.add_idea(idea)
            ideas.append(idea)

        # Assign some ideas
        doc.assign_idea(ideas[0].id, "alice")
        doc.assign_idea(ideas[1].id, "alice")
        doc.assign_idea(ideas[2].id, "bob")

        # Verify state
        assert len(doc.ideas) == 5
        assert len(doc.goals) == 2
        assert len(doc.get_user_queue("alice")) == 2
        assert len(doc.get_user_queue("bob")) == 1
        assert len(doc.get_unassigned()) == 2
        assert len(doc.get_by_theme("ui")) == 3
        assert len(doc.get_by_priority("high")) == 2

        # Remove an idea
        doc.remove_idea(ideas[4].id)
        assert len(doc.ideas) == 4

        # Verify metadata updated
        assert doc.metadata.total_ideas == 4
        assert doc.metadata.total_goals == 2

        # Verify substantial history
        assert len(doc.history) > 10  # Goals + ideas + assignments + removal
