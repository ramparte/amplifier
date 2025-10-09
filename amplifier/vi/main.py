"""Main entry point for vi editor with complete CLI support."""

import argparse
import os
import re
import signal
import sys

from .buffer.core import TextBuffer
from .commands.executor import CommandExecutor
from .event_loop import EventLoop
from .file_io.operations import FileOperations
from .modes.state import ModeManager
from .terminal.interface import TerminalInterface
from .terminal.renderer import Renderer


class ViEditor:
    """Main vi editor class with full CLI integration."""

    def __init__(
        self,
        filename: str | None = None,
        line_number: int | None = None,
        search_pattern: str | None = None,
        readonly: bool = False,
    ):
        """Initialize vi editor with command-line options.

        Args:
            filename: File to open (optional)
            line_number: Line number to jump to (optional)
            search_pattern: Pattern to search for on open (optional)
            readonly: Open file in read-only mode
        """
        # Core components
        self.buffer = TextBuffer()
        self.modes = ModeManager()
        self.renderer = Renderer()
        self.terminal = TerminalInterface()
        self.file_ops = FileOperations()

        # Create executor with all components
        self.executor = CommandExecutor(
            buffer=self.buffer,
            modes=self.modes,
            renderer=self.renderer,
        )

        # Create event loop
        self.event_loop = EventLoop(
            buffer=self.buffer,
            modes=self.modes,
            renderer=self.renderer,
            executor=self.executor,
            terminal=self.terminal,
            file_ops=self.file_ops,
        )

        # Editor state
        self.filename = filename
        self.readonly = readonly
        self.running = False

        # Load file if specified
        if filename:
            self._load_file(filename)

        # Jump to line if specified
        if line_number is not None:
            self._jump_to_line(line_number)

        # Search for pattern if specified
        if search_pattern:
            self._search_pattern(search_pattern)

    def _load_file(self, filename: str) -> None:
        """Load file content into buffer."""
        try:
            content = self.file_ops.read_file(filename)
            if content is not None:
                self.buffer = TextBuffer(content)
                # Update ALL components with new buffer
                self.executor.buffer = self.buffer
                self.event_loop.buffer = self.buffer
                # Also update visual mode's buffer reference
                if hasattr(self.executor, "visual"):
                    self.executor.visual.buffer = self.buffer
                self.renderer.show_message(f'"{filename}" {len(self.buffer.get_lines())}L')
            else:
                # New file
                self.buffer = TextBuffer()
                self.executor.buffer = self.buffer
                self.event_loop.buffer = self.buffer
                if hasattr(self.executor, "visual"):
                    self.executor.visual.buffer = self.buffer
                self.renderer.show_message(f'"{filename}" [New File]')
        except Exception as e:
            print(f"Error loading file: {e}", file=sys.stderr)
            sys.exit(1)

    def _jump_to_line(self, line_number: int) -> None:
        """Jump to specified line number."""
        # Convert to 0-based index
        target_line = max(0, line_number - 1)
        max_line = len(self.buffer.get_lines()) - 1
        target_line = min(target_line, max_line)

        row, col = self.buffer.get_cursor()
        self.buffer.set_cursor(target_line, col)

    def _search_pattern(self, pattern: str) -> None:
        """Search for pattern and position cursor at first match."""
        lines = self.buffer.get_lines()
        row, col = self.buffer.get_cursor()

        # Search from current position
        for i in range(row, len(lines)):
            line = lines[i]
            start_col = col if i == row else 0

            try:
                match = re.search(pattern, line[start_col:])
                if match:
                    # Found match, position cursor
                    self.buffer.set_cursor(i, start_col + match.start())
                    self.renderer.show_message(f"/{pattern}")
                    return
            except re.error:
                # Invalid regex, treat as literal
                idx = line[start_col:].find(pattern)
                if idx >= 0:
                    self.buffer.set_cursor(i, start_col + idx)
                    self.renderer.show_message(f"/{pattern}")
                    return

        # No match found
        self.renderer.show_message(f"Pattern not found: {pattern}")

    def run(self) -> None:
        """Run the editor main loop."""
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._handle_sigint)
        signal.signal(signal.SIGTSTP, self._handle_sigtstp)
        signal.signal(signal.SIGWINCH, self._handle_sigwinch)

        try:
            # Initialize terminal
            self.terminal.setup()

            # Initial render
            self.renderer.render(
                self.buffer,
                self.modes,
                filename=self.filename,
                readonly=self.readonly,
            )

            # Run event loop
            self.event_loop.run()

        except KeyboardInterrupt:
            # Handle Ctrl-C gracefully
            pass
        except Exception as e:
            # Log error for debugging
            import traceback

            with open("/tmp/vi_error.log", "w") as f:
                f.write(str(e) + "\n")
                f.write(traceback.format_exc())
            raise
        finally:
            # Restore terminal
            self.terminal.restore()

            # Clear screen
            print("\033[2J\033[H", end="")
            sys.stdout.flush()

    def _handle_sigint(self, signum, frame):
        """Handle Ctrl-C signal."""
        # Return to normal mode
        self.modes.to_normal()
        self.renderer.show_message("Type :q to quit")

    def _handle_sigtstp(self, signum, frame):
        """Handle Ctrl-Z signal (suspend)."""
        # Restore terminal before suspending
        self.terminal.restore()

        # Send SIGTSTP to self to actually suspend
        os.kill(os.getpid(), signal.SIGTSTP)

        # When resumed, setup terminal again
        self.terminal.setup()
        self.renderer.render(
            self.buffer,
            self.modes,
            filename=self.filename,
            readonly=self.readonly,
        )

    def _handle_sigwinch(self, signum, frame):
        """Handle terminal resize signal."""
        self.renderer.resize()
        self.renderer.render(
            self.buffer,
            self.modes,
            filename=self.filename,
            readonly=self.readonly,
        )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Vi text editor - a simple and powerful text editor",
        epilog="Examples:\n"
        "  vi file.txt           # Open file.txt\n"
        "  vi +10 file.txt       # Open file.txt at line 10\n"
        "  vi +/pattern file.txt # Open file.txt and search for pattern\n"
        "  vi -R file.txt        # Open file.txt in read-only mode\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "filename",
        nargs="?",
        help="File to edit (optional, creates new file if not exists)",
    )

    parser.add_argument(
        "-R",
        "--readonly",
        action="store_true",
        help="Open file in read-only mode",
    )

    # Handle special vi syntax for line numbers and patterns
    # This requires custom parsing
    args, remaining = parser.parse_known_args()

    # Process remaining arguments for + syntax
    line_number = None
    search_pattern = None

    for arg in remaining:
        if arg.startswith("+"):
            rest = arg[1:]
            if not rest:
                # Just +, go to last line
                line_number = -1
            elif rest.isdigit():
                # +N, go to line N
                line_number = int(rest)
            elif rest.startswith("/"):
                # +/pattern, search for pattern
                search_pattern = rest[1:] if len(rest) > 1 else ""

    return args.filename, line_number, search_pattern, args.readonly


def main():
    """Main entry point for vi editor."""
    # Parse command-line arguments
    filename, line_number, search_pattern, readonly = parse_arguments()

    # Create and run editor
    editor = ViEditor(
        filename=filename,
        line_number=line_number,
        search_pattern=search_pattern,
        readonly=readonly,
    )

    try:
        editor.run()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
