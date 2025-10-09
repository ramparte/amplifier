"""File saver with atomic writes and backup functionality."""

import contextlib
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class FileSaver:
    """Save files with atomic writes and backups."""

    # Retry settings for cloud sync issues
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds

    def save_file(
        self,
        filepath: str | Path,
        content: str,
        encoding: str = "utf-8",
        line_ending: str = "\n",
        create_backup: bool = True,
    ) -> bool:
        """Save content to file atomically.

        Args:
            filepath: Path to save to
            content: Content to write
            encoding: Encoding to use (default utf-8)
            line_ending: Line ending to use (\n, \r\n, or \r)
            create_backup: Whether to create .bak file

        Returns:
            True if save successful, False otherwise
        """
        path = Path(filepath)

        # Convert line endings if needed
        if line_ending != "\n":
            content = self._convert_line_endings(content, line_ending)

        # Create backup if file exists
        if create_backup and path.exists() and not self._create_backup(path):
            logger.warning(f"Failed to create backup for {path}")

        # Atomic write using temp file
        return self._atomic_write(path, content, encoding)

    def _convert_line_endings(self, content: str, line_ending: str) -> str:
        """Convert \n to target line ending.

        Args:
            content: Content with \n line endings
            line_ending: Target line ending

        Returns:
            Content with converted line endings
        """
        if line_ending == "\r\n":
            return content.replace("\n", "\r\n")
        if line_ending == "\r":
            return content.replace("\n", "\r")
        return content

    def _create_backup(self, path: Path) -> bool:
        """Create backup file with .bak extension.

        Args:
            path: Original file path

        Returns:
            True if backup created, False otherwise
        """
        backup_path = path.with_suffix(path.suffix + ".bak")

        try:
            # Preserve permissions and timestamps
            shutil.copy2(path, backup_path)
            return True
        except OSError as e:
            logger.error(f"Failed to create backup {backup_path}: {e}")
            return False

    def _atomic_write(self, path: Path, content: str, encoding: str) -> bool:
        """Write file atomically using temp file and rename.

        Args:
            path: Target file path
            content: Content to write
            encoding: Text encoding

        Returns:
            True if write successful, False otherwise
        """
        # Create temp file in same directory for atomic rename
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create directory {path.parent}: {e}")
            return False

        # Generate temp file
        temp_fd = None
        temp_path = None

        try:
            # Create temp file in same directory as target
            temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")

            # Write content with retry logic
            if not self._write_with_retry(temp_path, content, encoding):
                return False

            # Preserve original file permissions if file exists
            if path.exists():
                try:
                    # Get original file stats
                    stat_info = os.stat(path)
                    # Apply permissions to temp file
                    os.chmod(temp_path, stat_info.st_mode)
                except OSError as e:
                    logger.warning(f"Could not preserve permissions: {e}")

            # Atomic rename
            try:
                # On Windows, need to remove target first
                if os.name == "nt" and path.exists():
                    path.unlink()
                os.rename(temp_path, path)
                return True
            except OSError as e:
                logger.error(f"Failed to rename temp file to {path}: {e}")
                return False

        except Exception as e:
            logger.error(f"Unexpected error during save: {e}")
            return False

        finally:
            # Clean up temp file if still exists
            if temp_fd is not None:
                with contextlib.suppress(OSError):
                    os.close(temp_fd)

            if temp_path and Path(temp_path).exists():
                with contextlib.suppress(OSError):
                    Path(temp_path).unlink()

    def _write_with_retry(self, filepath: str | Path, content: str, encoding: str) -> bool:
        """Write file with retry logic for cloud sync issues.

        Args:
            filepath: Path to write to
            content: Content to write
            encoding: Text encoding

        Returns:
            True if write successful, False otherwise
        """
        path = Path(filepath)
        retry_delay = self.RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                with open(path, "w", encoding=encoding) as f:
                    f.write(content)
                    f.flush()
                    # Force write to disk
                    os.fsync(f.fileno())
                return True

            except OSError as e:
                if e.errno == 5 and attempt < self.MAX_RETRIES - 1:
                    # I/O error, likely cloud sync issue
                    if attempt == 0:
                        logger.warning(
                            f"File I/O error writing to {path} - retrying. This may be due to cloud-synced files."
                        )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                elif e.errno == 13:
                    # Permission denied
                    logger.error(f"Permission denied writing to {path}")
                    return False
                else:
                    # Other error or final attempt
                    logger.error(f"Failed to write to {path}: {e}")
                    return False

        return False

    def can_write(self, filepath: str | Path) -> bool:
        """Check if file can be written to.

        Args:
            filepath: Path to check

        Returns:
            True if file is writable
        """
        path = Path(filepath)

        # Check if new file can be created
        if not path.exists():
            try:
                # Check parent directory is writable
                parent = path.parent
                if not parent.exists():
                    parent.mkdir(parents=True, exist_ok=True)

                # Try to create and immediately delete a test file
                test_file = parent / f".test_{os.getpid()}.tmp"
                test_file.touch()
                test_file.unlink()
                return True
            except OSError:
                return False

        # Check existing file
        return os.access(path, os.W_OK)


# Module-level convenience function
def save_file(
    filepath: str | Path,
    content: str,
    encoding: str = "utf-8",
    line_ending: str = "\n",
    create_backup: bool = True,
) -> bool:
    """Save content to file atomically.

    Args:
        filepath: Path to save to
        content: Content to write
        encoding: Encoding to use
        line_ending: Line ending style
        create_backup: Whether to create backup

    Returns:
        True if successful
    """
    saver = FileSaver()
    return saver.save_file(filepath, content, encoding, line_ending, create_backup)
