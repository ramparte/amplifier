"""
YAML storage layer with defensive file I/O patterns.

Handles atomic saves, backup creation, and retry logic for cloud sync issues.
Following the single source of truth pattern with robust error handling.
"""

import shutil
import time
from pathlib import Path

import yaml
from filelock import FileLock

from amplifier.ideas.models import IdeasDocument


class IdeasStorage:
    """
    Storage layer for ideas documents with defensive patterns.

    Handles the "brick" of data persistence with atomic operations,
    cloud sync resilience, and backup management.
    """

    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        self.lockfile = Path(f"{filepath}.lock")
        self.backup_dir = self.filepath.parent / "backups"

        # Ensure directories exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(exist_ok=True)

    def load(self) -> IdeasDocument:
        """
        Load ideas document from YAML file with retry logic.

        Returns empty document if file doesn't exist.
        Retries on cloud sync delays (OneDrive, Dropbox, etc.)
        """
        if not self.filepath.exists():
            return IdeasDocument()

        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                with open(self.filepath, encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                if data is None:  # Empty file
                    return IdeasDocument()

                return IdeasDocument(**data)

            except OSError as e:
                if e.errno == 5 and attempt < max_retries - 1:  # I/O error, likely cloud sync
                    if attempt == 0:
                        print(f"⚠️  File I/O delay loading {self.filepath} - retrying...")
                        print("    This may be due to cloud sync (OneDrive, Dropbox, etc.)")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                raise
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in {self.filepath}: {e}")
            except Exception as e:
                raise RuntimeError(f"Failed to load ideas from {self.filepath}: {e}")

        raise RuntimeError(f"Failed to load after {max_retries} attempts")

    def save(self, doc: IdeasDocument, user: str = "system") -> None:
        """
        Atomic save with backup and retry logic.

        Creates backup of existing file before writing.
        Uses temp file + rename for atomicity.
        Retries on cloud sync issues.
        """
        # Update metadata
        doc.update_metadata(user)

        max_retries = 3
        retry_delay = 1.0

        with FileLock(self.lockfile, timeout=10):
            # Create backup of existing file
            if self.filepath.exists():
                backup_path = self._create_backup()
                if backup_path:
                    print(f"💾 Backed up to {backup_path.name}")

            # Atomic write with retry
            temp_file = self.filepath.with_suffix(".tmp")

            for attempt in range(max_retries):
                try:
                    # Convert to dict and write to temp file
                    data = doc.model_dump(mode="json")

                    with open(temp_file, "w", encoding="utf-8") as f:
                        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True, indent=2)
                        f.flush()

                    # Atomic rename
                    temp_file.replace(self.filepath)
                    return

                except OSError as e:
                    if e.errno == 5 and attempt < max_retries - 1:  # I/O error
                        if attempt == 0:
                            print(f"⚠️  File I/O delay saving {self.filepath} - retrying...")
                            print("    This may be due to cloud sync (OneDrive, Dropbox, etc.)")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    # Clean up temp file on error
                    if temp_file.exists():
                        temp_file.unlink()
                    raise
                except Exception as e:
                    # Clean up temp file on error
                    if temp_file.exists():
                        temp_file.unlink()
                    raise RuntimeError(f"Failed to save ideas to {self.filepath}: {e}")

        raise RuntimeError(f"Failed to save after {max_retries} attempts")

    def backup(self) -> Path | None:
        """Create a timestamped backup of the current file"""
        return self._create_backup()

    def _create_backup(self) -> Path | None:
        """Create backup with timestamp"""
        if not self.filepath.exists():
            return None

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"{self.filepath.stem}_{timestamp}.yaml"

        try:
            shutil.copy2(self.filepath, backup_path)
            # Keep only last 10 backups
            self._cleanup_old_backups()
            return backup_path
        except Exception as e:
            print(f"⚠️  Warning: Failed to create backup: {e}")
            return None

    def _cleanup_old_backups(self, keep: int = 10) -> None:
        """Remove old backup files, keeping only the most recent"""
        try:
            backups = list(self.backup_dir.glob(f"{self.filepath.stem}_*.yaml"))
            if len(backups) > keep:
                # Sort by modification time, remove oldest
                backups.sort(key=lambda p: p.stat().st_mtime)
                for old_backup in backups[:-keep]:
                    old_backup.unlink()
        except Exception:
            pass  # Backup cleanup is not critical

    def exists(self) -> bool:
        """Check if the ideas file exists"""
        return self.filepath.exists()

    def get_filepath(self) -> Path:
        """Get the full file path"""
        return self.filepath

    def get_backup_dir(self) -> Path:
        """Get the backup directory path"""
        return self.backup_dir


def get_default_ideas_file() -> Path:
    """
    Get the default ideas file path.

    Uses environment variable AMPLIFIER_IDEAS_FILE if set,
    otherwise defaults to ~/amplifier/ideas.yaml
    """
    import os

    # Check environment variable first
    env_path = os.getenv("AMPLIFIER_IDEAS_FILE")
    if env_path:
        return Path(env_path).expanduser()

    # Default to home directory
    return Path.home() / "amplifier" / "ideas.yaml"


def get_ideas_sources() -> list[Path]:
    """
    Get all configured ideas sources.

    Checks AMPLIFIER_IDEAS_DIRS environment variable for additional sources.
    Format: colon-separated paths, each should be a directory containing ideas.yaml

    Returns:
        List of paths to ideas files. First is primary (writable), rest are read-only.
    """
    import os

    sources = []

    # Primary source - always writable
    primary = get_default_ideas_file()
    sources.append(primary)

    # Check for additional sources
    env_dirs = os.getenv("AMPLIFIER_IDEAS_DIRS")
    if env_dirs:
        for dir_path in env_dirs.split(":"):
            dir_path = dir_path.strip()
            if not dir_path:
                continue

            try:
                # Security: prevent directory traversal BEFORE expansion
                if ".." in dir_path or dir_path.startswith("/etc"):
                    print(f"⚠️  Skipping potentially unsafe path: {dir_path}")
                    continue

                # Validate and expand path
                ideas_dir = Path(dir_path).expanduser().resolve()

                # Look for ideas.yaml in the directory
                ideas_file = ideas_dir / "ideas.yaml"

                # Skip if same as primary
                if ideas_file.resolve() == primary.resolve():
                    continue

                # Check if readable
                if ideas_file.exists() and ideas_file.is_file():
                    try:
                        ideas_file.read_text(encoding="utf-8")[:1]  # Test readability
                        sources.append(ideas_file)
                    except (OSError, PermissionError) as e:
                        print(f"⚠️  Cannot read {ideas_file}: {e}")
                elif ideas_dir.exists() and ideas_dir.is_dir():
                    # Directory exists but no ideas.yaml yet - still add it
                    sources.append(ideas_file)

            except Exception as e:
                print(f"⚠️  Invalid path in AMPLIFIER_IDEAS_DIRS: {dir_path} - {e}")

    return sources


class MultiSourceStorage:
    """
    Storage layer that combines multiple ideas sources.

    First source is primary (writable), additional sources are read-only.
    Merges ideas from all sources with conflict resolution: first-seen ID wins.
    """

    def __init__(self, sources: list[Path] | None = None):
        """
        Initialize multi-source storage.

        Args:
            sources: List of paths to ideas files. If None, uses get_ideas_sources()
        """
        if sources is None:
            sources = get_ideas_sources()

        if not sources:
            raise ValueError("No ideas sources configured")

        # Primary storage is always writable
        self.primary = IdeasStorage(sources[0])

        # Secondary storages are read-only
        self.secondary = []
        for source in sources[1:]:
            try:
                storage = IdeasStorage(source)
                self.secondary.append(storage)
            except Exception as e:
                print(f"⚠️  Could not initialize secondary source {source}: {e}")

    def load(self) -> IdeasDocument:
        """
        Load and merge ideas from all sources.

        Primary source is loaded first, then secondary sources.
        Conflicts resolved by first-seen wins.
        """
        # Start with primary
        doc = self.primary.load()
        seen_ids = {idea.id for idea in doc.ideas}

        # Merge secondary sources
        for storage in self.secondary:
            try:
                secondary_doc = storage.load()

                # Merge goals (append unique ones)
                for goal in secondary_doc.goals:
                    if goal.description not in [g.description for g in doc.goals]:
                        doc.goals.append(goal)

                # Merge ideas (skip duplicates by ID)
                for idea in secondary_doc.ideas:
                    if idea.id not in seen_ids:
                        doc.ideas.append(idea)
                        seen_ids.add(idea.id)

                # Note: Assignments are handled per-idea in the Idea model

            except Exception as e:
                print(f"⚠️  Error loading secondary source {storage.filepath}: {e}")

        # Update metadata counts
        doc.metadata.total_ideas = len(doc.ideas)
        doc.metadata.total_goals = len(doc.goals)

        return doc

    def save(self, doc: IdeasDocument, user: str = "system") -> None:
        """
        Save to primary storage only.

        Secondary sources are read-only for safety.
        Only saves ideas that belong to the primary source.
        """
        # Get IDs from secondary sources to exclude
        secondary_ids = set()
        secondary_goal_ids = set()
        for storage in self.secondary:
            try:
                sec_doc = storage.load()
                secondary_ids.update(idea.id for idea in sec_doc.ideas)
                secondary_goal_ids.update(goal.id for goal in sec_doc.goals)
            except Exception:
                pass

        # Filter out secondary ideas from the document to save
        filtered_ideas = [idea for idea in doc.ideas if idea.id not in secondary_ids]

        # Filter out secondary goals from the document to save
        filtered_goals = [goal for goal in doc.goals if goal.id not in secondary_goal_ids]

        # Create a new document with only primary source data
        save_doc = IdeasDocument(
            version=doc.version,
            metadata=doc.metadata,
            goals=filtered_goals,
            ideas=filtered_ideas,
            history=doc.history,
        )

        # Update counts
        save_doc.metadata.total_ideas = len(filtered_ideas)
        save_doc.metadata.total_goals = len(filtered_goals)

        self.primary.save(save_doc, user)

    def backup(self) -> Path | None:
        """Create backup of primary storage"""
        return self.primary.backup()

    def exists(self) -> bool:
        """Check if primary storage exists"""
        return self.primary.exists()

    def get_filepath(self) -> Path:
        """Get primary storage filepath"""
        return self.primary.get_filepath()

    def get_all_sources(self) -> list[Path]:
        """Get all configured source paths"""
        sources = [self.primary.get_filepath()]
        sources.extend([s.get_filepath() for s in self.secondary])
        return sources

    def is_multi_source(self) -> bool:
        """Check if multiple sources are configured"""
        return len(self.secondary) > 0


def create_sample_document() -> IdeasDocument:
    """Create a sample ideas document for testing"""
    from amplifier.ideas.models import Goal
    from amplifier.ideas.models import Idea

    doc = IdeasDocument()

    # Add sample goals
    doc.add_goal(Goal(description="Focus on improving user experience and onboarding", priority=1))

    doc.add_goal(Goal(description="Reduce technical debt and improve system reliability", priority=2))

    # Add sample ideas
    idea1 = Idea(
        title="Add dark mode toggle",
        description="Implement theme switching with user preference persistence",
        themes=["ui", "ux"],
        priority="high",
    )
    doc.add_idea(idea1)

    idea2 = Idea(
        title="Implement caching layer",
        description="Add Redis caching for frequently accessed data to improve performance",
        themes=["performance", "infrastructure"],
        priority="medium",
    )
    doc.add_idea(idea2)

    idea3 = Idea(
        title="Create user onboarding tutorial",
        description="Step-by-step walkthrough for new users",
        themes=["onboarding", "ux"],
        priority="high",
    )
    doc.add_idea(idea3)

    # Assign some ideas
    doc.assign_idea(idea1.id, "alice")
    doc.assign_idea(idea2.id, "bob")
    # idea3 remains unassigned

    return doc
