"""Example integration of file I/O system with TextBuffer."""

from pathlib import Path

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.file_io import FileLoader
from amplifier.vi.file_io import FileSaver
from amplifier.vi.file_io import FileState


def load_buffer_from_file(filepath: str | Path) -> tuple[TextBuffer, FileState]:
    """Load a file into a TextBuffer with state tracking.

    Args:
        filepath: Path to file to load

    Returns:
        Tuple of (TextBuffer, FileState)
    """
    # Create loader and load file
    loader = FileLoader()
    content, encoding, line_ending = loader.load_file(filepath)

    # Create buffer with content
    buffer = TextBuffer(content)

    # Create file state
    state = FileState(filepath=Path(filepath), encoding=encoding, line_ending=line_ending)

    return buffer, state


def save_buffer_to_file(buffer: TextBuffer, state: FileState) -> bool:
    """Save a TextBuffer to file using state information.

    Args:
        buffer: TextBuffer to save
        state: FileState with file information

    Returns:
        True if save successful
    """
    if not state.filepath:
        raise ValueError("No filepath set in state")

    # Get buffer content
    content = buffer.get_content()

    # Create saver and save
    saver = FileSaver()
    success = saver.save_file(state.filepath, content, encoding=state.encoding, line_ending=state.line_ending)

    if success:
        state.mark_saved()

    return success


def example_workflow():
    """Example workflow showing file I/O integration."""
    # Create a test file
    test_file = Path("test_document.txt")
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    # Load file into buffer
    buffer, state = load_buffer_from_file(test_file)
    print(f"Loaded: {state.get_display_path()}")
    print(f"Content lines: {buffer.get_line_count()}")

    # Make modifications
    buffer.move_to_last_line()
    buffer.insert_text("\nLine 4 - Added content")
    state.mark_modified()
    print(f"Status: {state.get_status_string()}")

    # Save changes
    if save_buffer_to_file(buffer, state):
        print(f"Saved successfully to {state.filepath}")
        print(f"Status: {state.get_status_string()}")

    # Clean up
    test_file.unlink()
    backup = test_file.with_suffix(".txt.bak")
    if backup.exists():
        backup.unlink()


if __name__ == "__main__":
    example_workflow()
