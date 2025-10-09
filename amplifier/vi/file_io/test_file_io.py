"""Unit tests for file I/O system."""

import os
import time

import pytest

from amplifier.vi.file_io import FileLoader
from amplifier.vi.file_io import FileSaver
from amplifier.vi.file_io import FileState
from amplifier.vi.file_io import FileStateManager
from amplifier.vi.file_io import load_file
from amplifier.vi.file_io import save_file


class TestFileLoader:
    """Test file loading with encoding detection."""

    def test_load_nonexistent_file(self, tmp_path):
        """Test loading a file that doesn't exist."""
        loader = FileLoader()
        content, encoding, line_ending = loader.load_file(tmp_path / "nonexistent.txt")

        assert content == ""
        assert encoding == "utf-8"
        assert line_ending == "\n"

    def test_load_utf8_file(self, tmp_path):
        """Test loading UTF-8 encoded file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, 世界! 🌍"
        test_file.write_text(test_content, encoding="utf-8")

        loader = FileLoader()
        content, encoding, line_ending = loader.load_file(test_file)

        assert content == test_content
        assert encoding == "utf-8"
        assert line_ending == "\n"

    def test_load_ascii_file(self, tmp_path):
        """Test loading ASCII file."""
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_bytes(test_content.encode("ascii"))

        loader = FileLoader()
        content, encoding, _ = loader.load_file(test_file)

        assert content == test_content
        assert encoding in ["utf-8", "ascii"]  # UTF-8 is superset of ASCII

    def test_detect_crlf_endings(self, tmp_path):
        """Test detection of CRLF line endings."""
        test_file = tmp_path / "test.txt"
        test_content = "Line 1\r\nLine 2\r\nLine 3"
        test_file.write_text(test_content, encoding="utf-8")

        loader = FileLoader()
        content, _, line_ending = loader.load_file(test_file)

        assert line_ending == "\r\n"
        assert content == "Line 1\nLine 2\nLine 3"  # Normalized

    def test_detect_cr_endings(self, tmp_path):
        """Test detection of CR line endings."""
        test_file = tmp_path / "test.txt"
        test_content = "Line 1\rLine 2\rLine 3"
        test_file.write_text(test_content, encoding="utf-8")

        loader = FileLoader()
        content, _, line_ending = loader.load_file(test_file)

        assert line_ending == "\r"
        assert content == "Line 1\nLine 2\nLine 3"  # Normalized

    def test_load_large_file(self, tmp_path):
        """Test loading large file efficiently."""
        test_file = tmp_path / "large.txt"
        # Create a 2MB file
        large_content = "x" * 1024 * 1024 * 2
        test_file.write_text(large_content, encoding="utf-8")

        loader = FileLoader()
        content, encoding, _ = loader.load_large_file(test_file)

        assert content == large_content
        assert encoding == "utf-8"

    def test_module_function(self, tmp_path):
        """Test module-level convenience function."""
        test_file = tmp_path / "test.txt"
        test_content = "Test content"
        test_file.write_text(test_content)

        content, encoding, line_ending = load_file(test_file)

        assert content == test_content
        assert encoding == "utf-8"
        assert line_ending == "\n"


class TestFileSaver:
    """Test file saving with atomic writes."""

    def test_save_new_file(self, tmp_path):
        """Test saving a new file."""
        saver = FileSaver()
        test_file = tmp_path / "new_file.txt"
        test_content = "New content"

        result = saver.save_file(test_file, test_content)

        assert result is True
        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == test_content

    def test_save_with_backup(self, tmp_path):
        """Test saving with backup creation."""
        saver = FileSaver()
        test_file = tmp_path / "test.txt"
        original_content = "Original"
        new_content = "Updated"

        # Create original file
        test_file.write_text(original_content)

        # Save with backup
        result = saver.save_file(test_file, new_content, create_backup=True)

        assert result is True
        assert test_file.read_text() == new_content
        assert (test_file.with_suffix(".txt.bak")).exists()
        assert (test_file.with_suffix(".txt.bak")).read_text() == original_content

    def test_save_without_backup(self, tmp_path):
        """Test saving without creating backup."""
        saver = FileSaver()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Original")

        result = saver.save_file(test_file, "Updated", create_backup=False)

        assert result is True
        assert test_file.read_text() == "Updated"
        assert not (test_file.with_suffix(".txt.bak")).exists()

    def test_save_with_crlf(self, tmp_path):
        """Test saving with CRLF line endings."""
        saver = FileSaver()
        test_file = tmp_path / "test.txt"
        content = "Line 1\nLine 2\nLine 3"

        result = saver.save_file(test_file, content, line_ending="\r\n")

        assert result is True
        raw_content = test_file.read_bytes().decode("utf-8")
        assert raw_content == "Line 1\r\nLine 2\r\nLine 3"

    def test_atomic_write(self, tmp_path):
        """Test atomic write behavior."""
        saver = FileSaver()
        test_file = tmp_path / "test.txt"

        # Write initial content
        test_file.write_text("Initial")

        # During save, temp file should be created
        result = saver.save_file(test_file, "Final")

        assert result is True
        assert test_file.read_text() == "Final"
        # No temp files should remain
        temp_files = list(tmp_path.glob(".test.txt.*.tmp"))
        assert len(temp_files) == 0

    def test_preserve_permissions(self, tmp_path):
        """Test preservation of file permissions."""
        if os.name == "nt":
            pytest.skip("Permission test not applicable on Windows")

        saver = FileSaver()
        test_file = tmp_path / "test.txt"
        test_file.write_text("Content")

        # Set specific permissions
        test_file.chmod(0o644)
        original_mode = test_file.stat().st_mode

        # Save and check permissions preserved
        saver.save_file(test_file, "Updated")

        assert test_file.stat().st_mode == original_mode

    def test_can_write_check(self, tmp_path):
        """Test write permission checking."""
        saver = FileSaver()

        # New file in writable directory
        assert saver.can_write(tmp_path / "newfile.txt") is True

        # Existing writable file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")
        assert saver.can_write(test_file) is True

    def test_module_function(self, tmp_path):
        """Test module-level convenience function."""
        test_file = tmp_path / "test.txt"
        result = save_file(test_file, "Test content")

        assert result is True
        assert test_file.read_text() == "Test content"


class TestFileState:
    """Test file state tracking."""

    def test_new_file_state(self):
        """Test state for new file."""
        state = FileState()

        assert state.filepath is None
        assert state.is_new_file is True
        assert state.is_modified is False
        assert state.is_readonly is False
        assert state.get_display_path() == "[No Name]"
        assert state.get_status_string() == "[New]"

    def test_existing_file_state(self, tmp_path):
        """Test state for existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        state = FileState(filepath=test_file)

        assert state.filepath == test_file
        assert state.is_new_file is False
        assert state.is_readonly is False
        assert state.file_size > 0

    def test_mark_modified(self):
        """Test marking file as modified."""
        state = FileState()
        state.mark_modified()

        assert state.is_modified is True
        assert "Modified" in state.get_status_string()

    def test_mark_saved(self, tmp_path):
        """Test marking file as saved."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        state = FileState(filepath=test_file)
        state.mark_modified()
        state.mark_saved()

        assert state.is_modified is False
        assert state.is_new_file is False
        assert state.last_saved_time is not None

    def test_external_change_detection(self, tmp_path):
        """Test detection of external file changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("original")

        state = FileState(filepath=test_file)
        state.update_from_disk()

        # No changes initially
        assert state.check_external_changes() is False

        # Modify file externally
        time.sleep(0.01)  # Ensure different mtime
        test_file.write_text("modified")

        # Should detect change
        assert state.check_external_changes() is True

    def test_readonly_detection(self, tmp_path):
        """Test read-only file detection."""
        if os.name == "nt":
            pytest.skip("Read-only test not reliable on Windows")

        test_file = tmp_path / "readonly.txt"
        test_file.write_text("content")
        test_file.chmod(0o444)  # Read-only

        state = FileState(filepath=test_file)

        assert state.is_readonly is True
        assert state.can_write() is False
        assert "Read Only" in state.get_status_string()

    def test_display_path(self, tmp_path):
        """Test display path generation."""
        test_file = tmp_path / "subdir" / "test.txt"
        test_file.parent.mkdir()
        test_file.write_text("content")

        state = FileState(filepath=test_file)
        display = state.get_display_path()

        # Should be absolute or relative path
        assert "test.txt" in display


class TestFileStateManager:
    """Test file state manager for multiple buffers."""

    def test_create_state(self, tmp_path):
        """Test creating state for buffer."""
        manager = FileStateManager()
        test_file = tmp_path / "test.txt"

        state = manager.create_state(1, test_file)

        assert state is not None
        assert state.filepath == test_file
        assert manager.get_state(1) == state

    def test_remove_state(self):
        """Test removing state for buffer."""
        manager = FileStateManager()
        manager.create_state(1)
        manager.remove_state(1)

        assert manager.get_state(1) is None

    def test_get_modified_buffers(self):
        """Test getting list of modified buffers."""
        manager = FileStateManager()

        state1 = manager.create_state(1)
        manager.create_state(2)  # state2 not modified
        state3 = manager.create_state(3)

        state1.mark_modified()
        state3.mark_modified()

        modified = manager.get_modified_buffers()

        assert 1 in modified
        assert 2 not in modified
        assert 3 in modified

    def test_check_all_external_changes(self, tmp_path):
        """Test checking all buffers for external changes."""
        manager = FileStateManager()

        # Create two files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content1")
        file2.write_text("content2")

        # Create states
        manager.create_state(1, file1)
        manager.create_state(2, file2)

        # Initially no changes
        changes = manager.check_all_external_changes()
        assert changes[1] is False
        assert changes[2] is False

        # Modify file2 externally
        time.sleep(0.01)
        file2.write_text("modified")

        # Check again
        changes = manager.check_all_external_changes()
        assert changes[1] is False
        assert changes[2] is True


class TestIntegration:
    """Integration tests for the file I/O system."""

    def test_load_modify_save_cycle(self, tmp_path):
        """Test complete load-modify-save cycle."""
        test_file = tmp_path / "test.txt"
        original_content = "Original content\nLine 2"
        test_file.write_text(original_content, encoding="utf-8")

        # Load file
        loader = FileLoader()
        content, encoding, line_ending = loader.load_file(test_file)

        # Track state
        state = FileState(filepath=test_file)
        assert not state.is_modified

        # Modify content
        modified_content = content + "\nLine 3"
        state.mark_modified()
        assert state.is_modified

        # Save file
        saver = FileSaver()
        result = saver.save_file(test_file, modified_content, encoding, line_ending)
        assert result is True

        # Update state
        state.mark_saved()
        assert not state.is_modified

        # Verify saved content
        saved_content = test_file.read_text(encoding="utf-8")
        assert saved_content == modified_content

        # Verify backup was created
        backup_file = test_file.with_suffix(".txt.bak")
        assert backup_file.exists()
        assert backup_file.read_text(encoding="utf-8") == original_content

    def test_encoding_preservation(self, tmp_path):
        """Test that encoding is preserved through load/save cycle."""
        test_file = tmp_path / "test.txt"

        # Write file with latin-1 encoding
        content_with_special = "Café résumé"
        test_file.write_text(content_with_special, encoding="latin-1")

        # Load with auto-detection
        loader = FileLoader()
        content, encoding, line_ending = loader.load_file(test_file)

        # Save with same encoding
        saver = FileSaver()
        saver.save_file(test_file, content, encoding, line_ending)

        # Verify content preserved
        final_content = test_file.read_text(encoding="latin-1")
        assert final_content == content_with_special
