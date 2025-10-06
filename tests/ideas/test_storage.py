"""
Unit tests for amplifier.ideas.storage module.

Tests defensive file I/O patterns, YAML operations, backup/restore functionality,
and cloud sync resilience following DISCOVERIES.md patterns.
"""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import yaml

from amplifier.ideas.models import Idea
from amplifier.ideas.models import IdeasDocument
from amplifier.ideas.storage import IdeasStorage
from amplifier.ideas.storage import get_default_ideas_file
from amplifier.ideas.storage import get_ideas_sources


class TestIdeasStorage:
    """Test the core IdeasStorage class"""

    def test_init_creates_directories(self, temp_dir):
        """Test that IdeasStorage creates necessary directories"""
        storage_path = temp_dir / "subdir" / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        assert storage.filepath == storage_path
        assert storage.backup_dir == storage_path.parent / "backups"
        assert storage.backup_dir.exists()

    def test_load_empty_file_returns_empty_document(self, temp_dir):
        """Test loading non-existent file returns empty IdeasDocument"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = storage.load()

        assert isinstance(doc, IdeasDocument)
        assert len(doc.ideas) == 0
        assert len(doc.goals) == 0

    def test_load_valid_yaml(self, temp_dir):
        """Test loading valid YAML file"""
        storage_path = temp_dir / "ideas.yaml"

        # Create test data
        test_data = {
            "version": "1.0",
            "ideas": [{"id": "test_123", "title": "Test Idea", "description": "Test description", "priority": "high"}],
            "goals": [],
            "history": [],
            "metadata": {"total_ideas": 1, "total_goals": 0},
        }

        with open(storage_path, "w") as f:
            yaml.dump(test_data, f)

        storage = IdeasStorage(storage_path)
        doc = storage.load()

        assert len(doc.ideas) == 1
        assert doc.ideas[0].title == "Test Idea"
        assert doc.ideas[0].priority == "high"

    def test_load_empty_yaml_file(self, temp_dir):
        """Test loading empty YAML file"""
        storage_path = temp_dir / "ideas.yaml"
        storage_path.write_text("")

        storage = IdeasStorage(storage_path)
        doc = storage.load()

        assert isinstance(doc, IdeasDocument)
        assert len(doc.ideas) == 0

    def test_load_invalid_yaml_raises_error(self, temp_dir):
        """Test loading invalid YAML raises ValueError"""
        storage_path = temp_dir / "ideas.yaml"
        storage_path.write_text("invalid: yaml: [unclosed")

        storage = IdeasStorage(storage_path)

        with pytest.raises(ValueError, match="Invalid YAML"):
            storage.load()

    def test_save_creates_backup(self, temp_dir):
        """Test that save creates backup of existing file"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        # Create initial file
        initial_doc = IdeasDocument()
        initial_doc.add_idea(Idea(title="Initial Idea"))
        storage.save(initial_doc)

        # Save updated document
        updated_doc = IdeasDocument()
        updated_doc.add_idea(Idea(title="Updated Idea"))
        storage.save(updated_doc)

        # Check backup was created
        backups = list(storage.backup_dir.glob("ideas_*.yaml"))
        assert len(backups) >= 1

    def test_save_atomic_operation(self, temp_dir):
        """Test that save uses atomic write (temp + rename)"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()
        doc.add_idea(Idea(title="Test Idea"))

        # Mock temp file creation to verify atomic write
        with patch("pathlib.Path.replace") as mock_replace:
            storage.save(doc)
            mock_replace.assert_called_once()

    def test_cloud_sync_retry_logic(self, temp_dir):
        """Test retry logic for cloud sync delays (OneDrive, Dropbox)"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()
        doc.add_idea(Idea(title="Test Idea"))

        # Mock OSError with errno 5 (I/O error) on first attempt
        original_open = open
        call_count = 0

        def mock_open(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise OSError(5, "I/O error")  # Simulate cloud sync delay
            return original_open(*args, **kwargs)

        with patch("builtins.open", side_effect=mock_open):
            storage.save(doc)  # Should succeed on retry
            assert call_count > 1  # Verify retry occurred

    def test_file_lock_prevents_concurrent_access(self, temp_dir):
        """Test file locking prevents concurrent writes"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()

        # Mock FileLock to verify it's used
        with patch("amplifier.ideas.storage.FileLock") as mock_lock:
            mock_lock.return_value.__enter__ = Mock(return_value=None)
            mock_lock.return_value.__exit__ = Mock(return_value=None)

            storage.save(doc)

            mock_lock.assert_called_once()

    def test_backup_cleanup_limits_old_backups(self, temp_dir):
        """Test backup cleanup keeps only specified number of backups"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()

        # Create multiple backups
        for i in range(15):
            doc.add_idea(Idea(title=f"Idea {i}"))
            storage.save(doc)
            time.sleep(0.01)  # Ensure different timestamps

        # Check that only 10 backups remain
        backups = list(storage.backup_dir.glob("ideas_*.yaml"))
        assert len(backups) <= 10

    def test_exists_method(self, temp_dir):
        """Test exists method"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        assert not storage.exists()

        doc = IdeasDocument()
        storage.save(doc)

        assert storage.exists()

    def test_get_paths_methods(self, temp_dir):
        """Test path getter methods"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        assert storage.get_filepath() == storage_path
        assert storage.get_backup_dir() == storage_path.parent / "backups"


class TestEnvironmentConfiguration:
    """Test environment variable configuration functions"""

    def test_get_default_ideas_file_with_env_var(self):
        """Test get_default_ideas_file respects AMPLIFIER_IDEAS_FILE"""
        test_path = "/custom/path/ideas.yaml"

        with patch.dict(os.environ, {"AMPLIFIER_IDEAS_FILE": test_path}):
            result = get_default_ideas_file()
            assert str(result) == test_path

    def test_get_default_ideas_file_without_env_var(self):
        """Test get_default_ideas_file uses default path"""
        with patch.dict(os.environ, {}, clear=True):
            result = get_default_ideas_file()
            assert "amplifier" in str(result)
            assert "ideas.yaml" in str(result)

    def test_get_ideas_sources_single_source(self):
        """Test get_ideas_sources with no additional directories"""
        with patch.dict(os.environ, {}, clear=True):
            sources = get_ideas_sources()
            assert len(sources) == 1
            assert sources[0] == get_default_ideas_file()

    def test_get_ideas_sources_multiple_directories(self):
        """Test get_ideas_sources with AMPLIFIER_IDEAS_DIRS"""
        with tempfile.TemporaryDirectory() as tmpdir1, tempfile.TemporaryDirectory() as tmpdir2:
            # Create ideas files
            (Path(tmpdir1) / "ideas.yaml").write_text("ideas: []")
            (Path(tmpdir2) / "ideas.yaml").write_text("ideas: []")

            env_dirs = f"{tmpdir1}:{tmpdir2}"

            with patch.dict(os.environ, {"AMPLIFIER_IDEAS_DIRS": env_dirs}):
                sources = get_ideas_sources()

                assert len(sources) == 3  # Primary + 2 additional
                assert str(tmpdir1) in str(sources[1])
                assert str(tmpdir2) in str(sources[2])

    def test_get_ideas_sources_security_validation(self):
        """Test security validation prevents directory traversal"""
        malicious_paths = "../etc:/tmp/../root:/etc/passwd"

        with patch.dict(os.environ, {"AMPLIFIER_IDEAS_DIRS": malicious_paths}):
            sources = get_ideas_sources()
            # Should only have primary source, all malicious paths rejected
            assert len(sources) == 1

    def test_get_ideas_sources_handles_unreadable_files(self):
        """Test graceful handling of unreadable files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            ideas_file = Path(tmpdir) / "ideas.yaml"
            ideas_file.write_text("ideas: []")

            # Mock permission error
            def mock_read_text(*args, **kwargs):
                raise PermissionError("Permission denied")

            with (
                patch.dict(os.environ, {"AMPLIFIER_IDEAS_DIRS": tmpdir}),
                patch.object(Path, "read_text", side_effect=mock_read_text),
            ):
                sources = get_ideas_sources()
                # Should only have primary source
                assert len(sources) == 1

    def test_get_ideas_sources_skips_duplicate_paths(self):
        """Test that duplicate paths are skipped"""
        primary_path = get_default_ideas_file()
        primary_dir = str(primary_path.parent)

        with patch.dict(os.environ, {"AMPLIFIER_IDEAS_DIRS": primary_dir}):
            sources = get_ideas_sources()
            # Should not duplicate primary source
            assert len(sources) == 1

    def test_get_ideas_sources_handles_empty_dirs(self):
        """Test handling of empty directory strings"""
        with patch.dict(os.environ, {"AMPLIFIER_IDEAS_DIRS": "::  : :"}):
            sources = get_ideas_sources()
            # Should only have primary source
            assert len(sources) == 1


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_load_permission_error(self, temp_dir):
        """Test handling of permission errors during load"""
        storage_path = temp_dir / "ideas.yaml"
        storage_path.write_text("ideas: []")

        # Mock permission error
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            storage = IdeasStorage(storage_path)

            with pytest.raises(PermissionError):
                storage.load()

    def test_save_disk_full_error(self, temp_dir):
        """Test handling of disk full error during save"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()

        # Mock disk full error
        with patch("builtins.open", side_effect=OSError(28, "No space left on device")), pytest.raises(OSError):
            storage.save(doc)

    def test_backup_failure_continues_save(self, temp_dir):
        """Test that backup failure doesn't prevent save"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        # Create initial file
        doc = IdeasDocument()
        storage.save(doc)

        # Mock backup failure
        with patch("shutil.copy2", side_effect=OSError("Backup failed")):
            doc.add_idea(Idea(title="New Idea"))
            storage.save(doc)  # Should succeed despite backup failure

            # Verify save succeeded
            reloaded = storage.load()
            assert len(reloaded.ideas) == 1

    def test_concurrent_access_handling(self, temp_dir):
        """Test behavior under concurrent access scenarios"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()
        doc.add_idea(Idea(title="Test Idea"))

        # Mock file lock timeout
        with patch("amplifier.ideas.storage.FileLock") as mock_lock:
            mock_lock.return_value.__enter__.side_effect = Exception("Lock timeout")

            with pytest.raises(Exception, match="Lock timeout"):
                storage.save(doc)


@pytest.fixture
def sample_document():
    """Fixture providing a sample IdeasDocument for testing"""
    doc = IdeasDocument()
    doc.add_idea(Idea(title="Sample Idea 1", description="Description 1"))
    doc.add_idea(Idea(title="Sample Idea 2", description="Description 2"))
    return doc


class TestIntegrationScenarios:
    """Test realistic usage scenarios"""

    def test_full_save_load_cycle(self, temp_dir, sample_document):
        """Test complete save/load cycle preserves data integrity"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        # Save document
        storage.save(sample_document)

        # Load and verify
        loaded_doc = storage.load()

        assert len(loaded_doc.ideas) == len(sample_document.ideas)
        assert loaded_doc.ideas[0].title == sample_document.ideas[0].title
        assert loaded_doc.ideas[1].title == sample_document.ideas[1].title

    def test_incremental_updates_preserve_history(self, temp_dir):
        """Test that incremental updates preserve document history"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        # Initial save
        doc = IdeasDocument()
        doc.add_idea(Idea(title="First Idea"))
        storage.save(doc)

        # Load and update
        doc = storage.load()
        doc.add_idea(Idea(title="Second Idea"))
        storage.save(doc)

        # Verify history preserved
        final_doc = storage.load()
        assert len(final_doc.ideas) == 2
        assert len(final_doc.history) >= 2  # At least 2 history entries

    def test_backup_rotation_maintains_recent_versions(self, temp_dir):
        """Test backup rotation keeps recent versions accessible"""
        storage_path = temp_dir / "ideas.yaml"
        storage = IdeasStorage(storage_path)

        doc = IdeasDocument()

        # Create several versions
        for i in range(5):
            doc.add_idea(Idea(title=f"Idea {i}"))
            storage.save(doc)
            time.sleep(0.01)

        # Verify backups exist
        backups = sorted(storage.backup_dir.glob("ideas_*.yaml"))
        assert len(backups) >= 3  # Should have several backups

        # Verify backups are readable
        for backup in backups:
            backup_storage = IdeasStorage(backup)
            backup_doc = backup_storage.load()
            assert isinstance(backup_doc, IdeasDocument)
