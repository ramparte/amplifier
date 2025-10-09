"""File loader with encoding detection and defensive I/O."""

import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class FileLoader:
    """Load files with encoding detection and error handling."""

    # Supported encodings in order of preference
    ENCODINGS = ["utf-8", "ascii", "latin-1", "cp1252"]

    # Retry settings for cloud sync issues
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds

    def load_file(self, filepath: str | Path) -> tuple[str, str, str]:
        """Load file content with encoding detection.

        Args:
            filepath: Path to file to load

        Returns:
            Tuple of (content, encoding, line_ending)
            - content: File content as string
            - encoding: Detected encoding
            - line_ending: Detected line ending (\n, \r\n, or \r)

        If file doesn't exist, returns empty content with utf-8 encoding.
        """
        path = Path(filepath)

        # Handle non-existent files
        if not path.exists():
            logger.info(f"File {path} does not exist, returning empty buffer")
            return "", "utf-8", "\n"

        # Try to read with retry logic for cloud sync issues
        raw_content = self._read_with_retry(path)
        if raw_content is None:
            # Failed to read after retries
            return "", "utf-8", "\n"

        # Detect encoding
        content, encoding = self._detect_encoding(raw_content)

        # Detect line endings
        line_ending = self._detect_line_ending(content)

        # Normalize to \n for internal processing
        content = self._normalize_line_endings(content)

        return content, encoding, line_ending

    def _read_with_retry(self, path: Path) -> bytes | None:
        """Read file with retry logic for cloud sync issues.

        Args:
            path: Path to file

        Returns:
            File content as bytes, or None if failed
        """
        retry_delay = self.RETRY_DELAY

        for attempt in range(self.MAX_RETRIES):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except OSError as e:
                if e.errno == 5 and attempt < self.MAX_RETRIES - 1:
                    # I/O error, likely cloud sync issue
                    if attempt == 0:
                        logger.warning(
                            f"File I/O error reading {path} - retrying. "
                            "This may be due to cloud-synced files (OneDrive, Dropbox, etc.). "
                            "Consider enabling 'Always keep on this device' for better performance."
                        )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                elif e.errno == 13:
                    # Permission denied
                    logger.error(f"Permission denied reading {path}")
                    return None
                else:
                    # Other error or final attempt
                    logger.error(f"Failed to read {path}: {e}")
                    return None

        return None

    def _detect_encoding(self, raw_content: bytes) -> tuple[str, str]:
        """Detect file encoding by trying different encodings.

        Args:
            raw_content: Raw file bytes

        Returns:
            Tuple of (decoded content, encoding name)
        """
        for encoding in self.ENCODINGS:
            try:
                content = raw_content.decode(encoding)
                return content, encoding
            except (UnicodeDecodeError, LookupError):
                continue

        # Fallback: decode with errors ignored
        logger.warning("Could not detect encoding, using utf-8 with errors ignored")
        content = raw_content.decode("utf-8", errors="ignore")
        return content, "utf-8"

    def _detect_line_ending(self, content: str) -> str:
        """Detect line ending style.

        Args:
            content: File content

        Returns:
            Line ending string (\n, \r\n, or \r)
        """
        if "\r\n" in content:
            return "\r\n"
        if "\r" in content:
            return "\r"
        return "\n"

    def _normalize_line_endings(self, content: str) -> str:
        """Normalize all line endings to \n.

        Args:
            content: File content with mixed line endings

        Returns:
            Content with normalized \n line endings
        """
        # Replace CRLF first, then CR
        content = content.replace("\r\n", "\n")
        content = content.replace("\r", "\n")
        return content

    def load_large_file(self, filepath: str | Path, chunk_size: int = 1024 * 1024) -> tuple[str, str, str]:
        """Load large file efficiently in chunks.

        Args:
            filepath: Path to file
            chunk_size: Size of chunks to read (default 1MB)

        Returns:
            Same as load_file()
        """
        path = Path(filepath)

        if not path.exists():
            return "", "utf-8", "\n"

        # For large files, try UTF-8 first as it's most common
        try:
            chunks = []
            line_ending = "\n"
            first_chunk = True

            with open(path, encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break

                    # Detect line ending from first chunk
                    if first_chunk:
                        line_ending = self._detect_line_ending(chunk)
                        first_chunk = False

                    chunks.append(chunk)

            content = "".join(chunks)
            content = self._normalize_line_endings(content)
            return content, "utf-8", line_ending

        except UnicodeDecodeError:
            # Fall back to regular load for encoding detection
            return self.load_file(filepath)


# Module-level convenience function
def load_file(filepath: str | Path) -> tuple[str, str, str]:
    """Load file with encoding detection.

    Args:
        filepath: Path to file

    Returns:
        Tuple of (content, encoding, line_ending)
    """
    loader = FileLoader()
    return loader.load_file(filepath)
