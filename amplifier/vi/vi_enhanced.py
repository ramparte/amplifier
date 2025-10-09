"""Enhanced vi editor implementation with comprehensive command registry.

This module integrates the new command registry system for better command handling,
supporting operator-motion combinations, numeric prefixes, and text objects.
"""

import sys
import termios
import tty

from .buffer.core import TextBuffer
from .commands import CommandContext
from .commands import CommandDispatcher
from .commands import CommandMode
from .commands import CommandRegistry
from .commands import register_motion_commands
from .commands import register_operator_commands
from .commands import register_text_objects
from .modes.state import ModeManager
from .terminal.render import Renderer


class EnhancedVi:
    """Enhanced vi editor with comprehensive command registry system."""

    def __init__(self, filename: str | None = None):
        """Initialize enhanced vi editor with optional file to open."""
        # Core components
        self.buffer = TextBuffer()
        self.modes = ModeManager()
        self.renderer = Renderer()

        # Command registry system
        self.registry = CommandRegistry()
        self._register_all_commands()

        # Command dispatcher
        self.dispatcher = CommandDispatcher(self.registry)

        # Editor state
        self.filename = filename
        self.running = False
        self._command_buffer = ""
        self._pending_char_command = None

        # Load file if provided
        if filename:
            self._load_file(filename)

    def _register_all_commands(self) -> None:
        """Register all vi commands with the registry."""
        register_motion_commands(self.registry)
        register_operator_commands(self.registry)
        register_text_objects(self.registry)

        # Register additional editor-specific commands here
        self._register_mode_change_commands()
        self._register_file_commands()

    def _register_mode_change_commands(self) -> None:
        """Register mode change commands."""
        from .commands import CommandDef
        from .commands import CommandType

        # Insert mode commands
        self.registry.register(
            CommandDef(
                keys="i",
                name="insert",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._enter_insert_mode(ctx),
                modes={CommandMode.NORMAL},
                description="Enter insert mode",
            )
        )

        self.registry.register(
            CommandDef(
                keys="a",
                name="append",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._enter_insert_after(ctx),
                modes={CommandMode.NORMAL},
                description="Enter insert mode after cursor",
            )
        )

        self.registry.register(
            CommandDef(
                keys="A",
                name="append_line",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._enter_insert_end(ctx),
                modes={CommandMode.NORMAL},
                description="Enter insert mode at end of line",
            )
        )

        self.registry.register(
            CommandDef(
                keys="I",
                name="insert_line",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._enter_insert_start(ctx),
                modes={CommandMode.NORMAL},
                description="Enter insert mode at start of line",
            )
        )

        self.registry.register(
            CommandDef(
                keys="o",
                name="open_below",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._open_line_below(ctx),
                modes={CommandMode.NORMAL},
                description="Open line below and enter insert mode",
            )
        )

        self.registry.register(
            CommandDef(
                keys="O",
                name="open_above",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._open_line_above(ctx),
                modes={CommandMode.NORMAL},
                description="Open line above and enter insert mode",
            )
        )

        # Visual mode commands
        self.registry.register(
            CommandDef(
                keys="v",
                name="visual",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._enter_visual_mode(ctx),
                modes={CommandMode.NORMAL},
                description="Enter visual mode",
            )
        )

        self.registry.register(
            CommandDef(
                keys="V",
                name="visual_line",
                type=CommandType.MODE_CHANGE,
                handler=lambda ctx: self._enter_visual_line_mode(ctx),
                modes={CommandMode.NORMAL},
                description="Enter visual line mode",
            )
        )

    def _register_file_commands(self) -> None:
        """Register file operation commands."""
        from .commands import CommandDef
        from .commands import CommandType

        # Put commands
        self.registry.register(
            CommandDef(
                keys="p",
                name="put_after",
                type=CommandType.ACTION,
                handler=lambda ctx: self._put_after(ctx),
                modes={CommandMode.NORMAL},
                takes_register=True,
                description="Put after cursor",
            )
        )

        self.registry.register(
            CommandDef(
                keys="P",
                name="put_before",
                type=CommandType.ACTION,
                handler=lambda ctx: self._put_before(ctx),
                modes={CommandMode.NORMAL},
                takes_register=True,
                description="Put before cursor",
            )
        )

        # Undo/redo
        self.registry.register(
            CommandDef(
                keys="u",
                name="undo",
                type=CommandType.ACTION,
                handler=lambda ctx: self._undo(ctx),
                modes={CommandMode.NORMAL},
                repeatable=False,
                description="Undo last change",
            )
        )

        # Repeat
        self.registry.register(
            CommandDef(
                keys=".",
                name="repeat",
                type=CommandType.ACTION,
                handler=lambda ctx: self._repeat_last(ctx),
                modes={CommandMode.NORMAL},
                repeatable=False,
                description="Repeat last command",
            )
        )

    def _load_file(self, filename: str) -> None:
        """Load a file into the buffer."""
        try:
            with open(filename, encoding="utf-8") as f:
                content = f.read()
                self.buffer = TextBuffer(content)
        except FileNotFoundError:
            # New file - start with empty buffer
            self.buffer = TextBuffer()
        except Exception as e:
            print(f"Error loading file: {e}")
            sys.exit(1)

    def _save_file(self) -> bool:
        """Save buffer content to file."""
        if not self.filename:
            self.renderer.show_message("No filename")
            return False

        try:
            content = self.buffer.get_content()
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(content)

            lines = len(self.buffer.get_lines())
            chars = len(content)
            self.renderer.show_message(f'"{self.filename}" {lines}L, {chars}C written')
            return True
        except Exception as e:
            self.renderer.show_message(f"Error saving: {e}")
            return False

    def run(self) -> None:
        """Main editor loop."""
        self.running = True

        # Save terminal settings
        old_settings = termios.tcgetattr(sys.stdin)

        try:
            # Set terminal to raw mode
            tty.setraw(sys.stdin)

            # Initial render
            self.renderer.render(self.buffer, self.modes)

            # Main loop
            while self.running:
                # Read keyboard input
                char = sys.stdin.read(1)

                # Handle input based on current mode
                self._handle_input(char)

                # Render updated state
                if self.running:
                    self.renderer.render(self.buffer, self.modes)

        finally:
            # Restore terminal settings
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            # Clear screen on exit
            print("\033[2J\033[H", end="")

    def _handle_input(self, char: str) -> None:
        """Handle keyboard input based on current mode."""
        mode = self.modes.get_mode()

        if mode == ModeManager.NORMAL:
            self._handle_normal_mode(char)
        elif mode == ModeManager.INSERT:
            self._handle_insert_mode(char)
        elif mode == ModeManager.VISUAL:
            self._handle_visual_mode(char)
        elif mode == ModeManager.COMMAND:
            self._handle_command_mode(char)

    def _handle_normal_mode(self, char: str) -> None:
        """Handle input in normal mode using command registry."""
        # Special handling for command mode
        if char == ":":
            self.modes.to_command()
            self.renderer.update_command_line("")
            return

        # Special handling for quit
        if char == "q" and not self.dispatcher.pending_keys:
            self.running = False
            return

        # Escape clears any pending state
        if char == "\x1b":
            self.dispatcher.reset()
            return

        # Handle pending character input (e.g., for 'f' command)
        if self._pending_char_command:
            self._handle_pending_char(char)
            return

        # Process through command dispatcher
        ctx = self._create_context()
        success, error = self.dispatcher.process_key(char, self._get_command_mode(), ctx)

        # Check for pending character commands
        if ctx.extra_args.get("pending_find"):
            self._pending_char_command = ctx.extra_args["pending_find"]
        elif ctx.extra_args.get("pending_replace"):
            self._pending_char_command = "r"

        # Show error if command failed
        if error:
            self.renderer.show_message(error)

    def _handle_insert_mode(self, char: str) -> None:
        """Handle input in insert mode."""
        if char == "\x1b":  # Escape
            self.modes.to_normal()
            # Move cursor back one position if not at start of line
            row, col = self.buffer.get_cursor()
            if col > 0:
                self.buffer.move_cursor_left()
        elif char == "\r" or char == "\n":  # Enter
            self.buffer.insert_char("\n")
        elif char == "\x7f" or char == "\b":  # Backspace
            self.buffer.backspace()
        elif ord(char) >= 32:  # Printable characters
            self.buffer.insert_char(char)

    def _handle_visual_mode(self, char: str) -> None:
        """Handle input in visual mode using command registry."""
        # Escape or v exits visual mode
        if char == "\x1b" or char == "v":
            self.buffer.clear_mark()
            self.modes.to_normal()
            return

        # Process through command dispatcher
        ctx = self._create_context()
        success, error = self.dispatcher.process_key(char, CommandMode.VISUAL, ctx)

        if error:
            self.renderer.show_message(error)

    def _handle_command_mode(self, char: str) -> None:
        """Handle input in command mode."""
        if char == "\x1b":  # Escape
            self._command_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
        elif char == "\r" or char == "\n":  # Enter - execute command
            self._execute_command(self._command_buffer)
            self._command_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
        elif char == "\x7f" or char == "\b":  # Backspace
            if self._command_buffer:
                self._command_buffer = self._command_buffer[:-1]
                self.renderer.update_command_line(self._command_buffer)
        elif ord(char) >= 32:  # Printable characters
            self._command_buffer += char
            self.renderer.update_command_line(self._command_buffer)

    def _handle_pending_char(self, char: str) -> None:
        """Handle pending character input for commands like 'f' or 'r'."""
        if self._pending_char_command == "r":
            # Replace character
            row, col = self.buffer.get_cursor()
            lines = self.buffer.get_lines()
            if row < len(lines) and col < len(lines[row]):
                line = lines[row]
                self.buffer._lines[row] = line[:col] + char + line[col + 1 :]
        elif self._pending_char_command in "fFtT":
            # Find/till character
            self._execute_find_char(self._pending_char_command, char)

        self._pending_char_command = None

    def _execute_find_char(self, cmd: str, target: str) -> None:
        """Execute find character command."""
        row, col = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row >= len(lines):
            return

        line = lines[row]

        if cmd == "f":  # Find forward
            for i in range(col + 1, len(line)):
                if line[i] == target:
                    self.buffer.set_cursor(row, i)
                    break
        elif cmd == "F":  # Find backward
            for i in range(col - 1, -1, -1):
                if line[i] == target:
                    self.buffer.set_cursor(row, i)
                    break
        elif cmd == "t":  # Till forward
            for i in range(col + 1, len(line)):
                if line[i] == target:
                    self.buffer.set_cursor(row, i - 1)
                    break
        elif cmd == "T":  # Till backward
            for i in range(col - 1, -1, -1):
                if line[i] == target:
                    self.buffer.set_cursor(row, i + 1)
                    break

    def _execute_command(self, command: str) -> None:
        """Execute a command line command."""
        if command == "q" or command == "q!":
            self.running = False
        elif command == "w":
            self._save_file()
        elif command == "wq":
            if self._save_file():
                self.running = False
        elif command.startswith("w "):
            self.filename = command[2:].strip()
            self._save_file()
        elif command.startswith("e "):
            filename = command[2:].strip()
            self._load_file(filename)
            self.filename = filename
        else:
            self.renderer.show_message(f"Unknown command: {command}")

    def _create_context(self) -> CommandContext:
        """Create a command context for the current state."""
        return CommandContext(buffer=self.buffer, modes=self.modes, renderer=self.renderer)

    def _get_command_mode(self) -> CommandMode:
        """Get the current command mode enum value."""
        mode = self.modes.get_mode()

        if self.dispatcher.pending_operator:
            return CommandMode.OPERATOR_PENDING
        if mode == ModeManager.NORMAL:
            return CommandMode.NORMAL
        if mode == ModeManager.VISUAL:
            if self.modes.is_line_mode():
                return CommandMode.VISUAL_LINE
            return CommandMode.VISUAL
        if mode == ModeManager.INSERT:
            return CommandMode.INSERT
        if mode == ModeManager.COMMAND:
            return CommandMode.COMMAND_LINE

        return CommandMode.NORMAL

    # Mode change handlers
    def _enter_insert_mode(self, ctx: CommandContext) -> bool:
        """Enter insert mode."""
        self.modes.to_insert()
        return True

    def _enter_insert_after(self, ctx: CommandContext) -> bool:
        """Enter insert mode after cursor."""
        self.buffer.move_cursor_right()
        self.modes.to_insert()
        return True

    def _enter_insert_end(self, ctx: CommandContext) -> bool:
        """Enter insert mode at end of line."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            self.buffer.set_cursor(row, len(lines[row]))
        self.modes.to_insert()
        return True

    def _enter_insert_start(self, ctx: CommandContext) -> bool:
        """Enter insert mode at first non-blank."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            line = lines[row]
            col = 0
            for i, char in enumerate(line):
                if not char.isspace():
                    col = i
                    break
            self.buffer.set_cursor(row, col)
        self.modes.to_insert()
        return True

    def _open_line_below(self, ctx: CommandContext) -> bool:
        """Open new line below and enter insert mode."""
        row, _ = self.buffer.get_cursor()
        lines = self.buffer.get_lines()
        if row < len(lines):
            self.buffer.set_cursor(row, len(lines[row]))
            self.buffer.insert_char("\n")
        self.modes.to_insert()
        return True

    def _open_line_above(self, ctx: CommandContext) -> bool:
        """Open new line above and enter insert mode."""
        row, _ = self.buffer.get_cursor()
        self.buffer.set_cursor(row, 0)
        self.buffer.insert_char("\n")
        self.buffer.move_cursor_up()
        self.modes.to_insert()
        return True

    def _enter_visual_mode(self, ctx: CommandContext) -> bool:
        """Enter visual mode."""
        self.buffer.set_mark()
        self.modes.to_visual()
        return True

    def _enter_visual_line_mode(self, ctx: CommandContext) -> bool:
        """Enter visual line mode."""
        self.buffer.set_mark()
        self.modes.to_visual(line_mode=True)
        return True

    # File operation handlers
    def _put_after(self, ctx: CommandContext) -> bool:
        """Put after cursor (placeholder)."""
        self.renderer.show_message("Put not implemented")
        return True

    def _put_before(self, ctx: CommandContext) -> bool:
        """Put before cursor (placeholder)."""
        self.renderer.show_message("Put not implemented")
        return True

    def _undo(self, ctx: CommandContext) -> bool:
        """Undo last change (placeholder)."""
        self.renderer.show_message("Undo not implemented")
        return True

    def _repeat_last(self, ctx: CommandContext) -> bool:
        """Repeat last command."""
        success, error = self.dispatcher.repeat_last_command(ctx)
        if error:
            self.renderer.show_message(error)
        return success


def main():
    """Main entry point for enhanced vi editor."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Vi-like text editor")
    parser.add_argument("filename", nargs="?", help="File to edit")
    args = parser.parse_args()

    editor = EnhancedVi(args.filename)
    editor.run()


if __name__ == "__main__":
    main()
