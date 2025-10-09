"""Main event loop for vi editor that coordinates all components."""

import time


class EventLoop:
    """Main event loop that handles input, dispatches commands, and updates display."""

    def __init__(
        self,
        buffer,
        modes,
        renderer,
        executor,
        terminal,
        file_ops,
    ):
        """Initialize event loop with all required components.

        Args:
            buffer: Text buffer
            modes: Mode manager
            renderer: Display renderer
            executor: Command executor
            terminal: Terminal interface
            file_ops: File operations handler
        """
        self.buffer = buffer
        self.modes = modes
        self.renderer = renderer
        self.executor = executor
        self.terminal = terminal
        self.file_ops = file_ops

        # State management
        self.running = True
        self.filename: str | None = None
        self.readonly = False
        self.modified = False
        self.last_save_content = ""

        # Command buffers
        self.command_buffer = ""
        self.search_buffer = ""
        self.normal_command_buffer = ""
        self.repeat_count = ""

        # Performance
        self.last_render_time = 0
        self.min_render_interval = 1.0 / 60  # 60 FPS max

        # Ex command history
        self.command_history: list[str] = []
        self.history_index = -1

        # Search state
        self.search_pattern = ""
        self.search_direction = "forward"

        # Macro state
        self.recording_macro = False
        self.macro_register = ""
        self.macro_buffer: list[str] = []

    def run(self) -> None:
        """Run the main event loop."""
        self.running = True

        # Store initial content for modification detection
        self.last_save_content = self.buffer.get_content()

        while self.running:
            try:
                # Read key input
                key = self.terminal.read_key()

                # Process input based on current mode
                self._process_input(key)

                # Check if buffer has been modified
                self._update_modified_status()

                # Render if enough time has passed
                current_time = time.time()
                if current_time - self.last_render_time >= self.min_render_interval:
                    self.renderer.render(
                        self.buffer,
                        self.modes,
                        filename=self.filename,
                        readonly=self.readonly,
                        modified=self.modified,
                    )
                    self.last_render_time = current_time

            except KeyboardInterrupt:
                # Handle Ctrl-C
                self._handle_interrupt()
            except Exception as e:
                # Show error and continue
                self.renderer.show_message(f"Error: {str(e)}")

    def _process_input(self, key: str) -> None:
        """Process input based on current mode.

        Args:
            key: The key pressed (may be special key name)
        """
        mode = self.modes.get_mode()

        if mode == "normal":
            self._process_normal_mode(key)
        elif mode == "insert":
            self._process_insert_mode(key)
        elif mode == "visual":
            self._process_visual_mode(key)
        elif mode == "command":
            self._process_command_mode(key)
        elif mode == "replace":
            self._process_replace_mode(key)
        elif mode == "search":
            self._process_search_mode(key)

    def _process_normal_mode(self, key: str) -> None:
        """Process input in normal mode."""
        # Handle special keys
        if key == "ESC":
            # Clear any pending state
            self.normal_command_buffer = ""
            self.repeat_count = ""
            self.renderer.show_message("")
            return

        # Command mode
        if key == ":":
            self.modes.set_mode("command")
            self.command_buffer = ""
            self.renderer.update_command_line("")
            return

        # Search mode
        if key == "/":
            self.modes.set_mode("search")
            self.search_direction = "forward"
            self.search_buffer = ""
            self.renderer.update_command_line("/")
            return

        if key == "?":
            self.modes.set_mode("search")
            self.search_direction = "backward"
            self.search_buffer = ""
            self.renderer.update_command_line("?")
            return

        # Repeat last search
        if key == "n":
            self._repeat_search(same_direction=True)
            return

        if key == "N":
            self._repeat_search(same_direction=False)
            return

        # Mode changes
        if key == "i":
            self.modes.to_insert()
            return

        if key == "I":
            # Insert at beginning of line
            row, _ = self.buffer.get_cursor()
            self.buffer.set_cursor(row, 0)
            self.modes.to_insert()
            return

        if key == "a":
            # Append after cursor
            row, col = self.buffer.get_cursor()
            line = self.buffer.get_lines()[row] if self.buffer.get_lines() else ""
            if col < len(line):
                self.buffer.set_cursor(row, col + 1)
            self.modes.to_insert()
            return

        if key == "A":
            # Append at end of line
            row, _ = self.buffer.get_cursor()
            line = self.buffer.get_lines()[row] if self.buffer.get_lines() else ""
            self.buffer.set_cursor(row, len(line))
            self.modes.to_insert()
            return

        if key == "o":
            # Open line below
            self.executor.execute_normal_command("o")
            self.modes.to_insert()
            return

        if key == "O":
            # Open line above
            self.executor.execute_normal_command("O")
            self.modes.to_insert()
            return

        if key == "v":
            self.modes.to_visual()
            # Set visual start position
            if hasattr(self.buffer, "set_visual_start"):
                row, col = self.buffer.get_cursor()
                self.buffer.set_visual_start(row, col)
            return

        if key == "V":
            self.modes.set_mode("visual_line")
            # Set visual start position
            if hasattr(self.buffer, "set_visual_start"):
                row, col = self.buffer.get_cursor()
                self.buffer.set_visual_start(row, 0)
            return

        if key == "R":
            self.modes.set_mode("replace")
            return

        # Macro recording
        if key == "q":
            if self.recording_macro:
                # Stop recording
                self._stop_macro_recording()
            else:
                # Check for next key to determine register
                self.normal_command_buffer = "q"
                self.renderer.show_message("recording @")
            return

        if self.normal_command_buffer == "q" and key.isalpha():
            # Start recording to register
            self._start_macro_recording(key)
            self.normal_command_buffer = ""
            return

        # Macro playback
        if key == "@":
            self.normal_command_buffer = "@"
            self.renderer.show_message("@")
            return

        if self.normal_command_buffer == "@" and key.isalpha():
            # Play macro from register
            self._play_macro(key)
            self.normal_command_buffer = ""
            return

        # Handle digits for repeat count
        if key.isdigit():
            if key == "0" and not self.repeat_count:
                # 0 is beginning of line command
                self.executor.execute_normal_command("0")
            else:
                self.repeat_count += key
                self.renderer.show_message(self.repeat_count)
            return

        # Arrow key navigation
        if key == "UP":
            self.executor.execute_normal_command("k")
            return
        if key == "DOWN":
            self.executor.execute_normal_command("j")
            return
        if key == "LEFT":
            self.executor.execute_normal_command("h")
            return
        if key == "RIGHT":
            self.executor.execute_normal_command("l")
            return

        # Page navigation
        if key == "PAGEUP" or key == "CTRL-B":
            self.executor.execute_normal_command("\x02")  # Ctrl-B
            return
        if key == "PAGEDOWN" or key == "CTRL-F":
            self.executor.execute_normal_command("\x06")  # Ctrl-F
            return

        # Let executor handle other normal mode commands
        if self.repeat_count:
            # Apply repeat count
            try:
                count = int(self.repeat_count)
                for _ in range(count):
                    self.executor.execute_normal_command(key)
            except ValueError:
                pass
            self.repeat_count = ""
            self.renderer.show_message("")
        else:
            self.executor.execute_normal_command(key)

        # Record macro keystrokes
        if self.recording_macro:
            self.macro_buffer.append(key)

    def _process_insert_mode(self, key: str) -> None:
        """Process input in insert mode."""
        if key == "ESC":
            self.modes.to_normal()
            # Move cursor back one if not at start of line
            row, col = self.buffer.get_cursor()
            if col > 0:
                self.buffer.set_cursor(row, col - 1)
            return

        # Handle special keys
        if key == "BACKSPACE":
            self.executor.execute_insert_command("\b")
        elif key == "DELETE":
            self.executor.execute_insert_command("\x7f")
        elif key == "ENTER":
            self.executor.execute_insert_command("\n")
        elif key == "TAB":
            self.executor.execute_insert_command("\t")
        elif key == "UP":
            row, col = self.buffer.get_cursor()
            if row > 0:
                self.buffer.set_cursor(row - 1, col)
        elif key == "DOWN":
            row, col = self.buffer.get_cursor()
            if row < len(self.buffer.get_lines()) - 1:
                self.buffer.set_cursor(row + 1, col)
        elif key == "LEFT":
            row, col = self.buffer.get_cursor()
            if col > 0:
                self.buffer.set_cursor(row, col - 1)
        elif key == "RIGHT":
            row, col = self.buffer.get_cursor()
            line = self.buffer.get_lines()[row] if self.buffer.get_lines() else ""
            if col < len(line):
                self.buffer.set_cursor(row, col + 1)
        elif not key.startswith("CTRL-") and not key.startswith("ALT-"):
            # Regular character input
            self.executor.execute_insert_command(key)

    def _process_visual_mode(self, key: str) -> None:
        """Process input in visual mode."""
        if key == "ESC":
            self.modes.to_normal()
            if hasattr(self.buffer, "clear_visual"):
                self.buffer.clear_visual()
            return

        # Visual mode operations
        if key == "d" or key == "x":
            # Delete selection
            self.executor.execute_visual_command("d")
            self.modes.to_normal()
            return

        if key == "y":
            # Yank selection
            self.executor.execute_visual_command("y")
            self.modes.to_normal()
            return

        if key == "c":
            # Change selection
            self.executor.execute_visual_command("c")
            self.modes.to_insert()
            return

        # Navigation extends selection
        if key in ["h", "j", "k", "l", "w", "b", "e", "$", "0", "^"]:
            self.executor.execute_visual_command(key)
        elif key == "UP":
            self.executor.execute_visual_command("k")
        elif key == "DOWN":
            self.executor.execute_visual_command("j")
        elif key == "LEFT":
            self.executor.execute_visual_command("h")
        elif key == "RIGHT":
            self.executor.execute_visual_command("l")

    def _process_command_mode(self, key: str) -> None:
        """Process input in command mode."""
        if key == "ESC":
            # Cancel command
            self.command_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
            return

        if key == "ENTER":
            # Execute command
            if self.command_buffer:
                self._execute_ex_command(self.command_buffer)
                # Add to history
                self.command_history.append(self.command_buffer)
                self.history_index = len(self.command_history)

            self.command_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
            return

        if key == "BACKSPACE":
            if self.command_buffer:
                self.command_buffer = self.command_buffer[:-1]
                self.renderer.update_command_line(self.command_buffer)
            else:
                # Empty command, return to normal mode
                self.modes.to_normal()
                self.renderer.clear_command_line()
            return

        if key == "UP":
            # Navigate history up
            if self.history_index > 0:
                self.history_index -= 1
                self.command_buffer = self.command_history[self.history_index]
                self.renderer.update_command_line(self.command_buffer)
            return

        if key == "DOWN":
            # Navigate history down
            if self.history_index < len(self.command_history) - 1:
                self.history_index += 1
                self.command_buffer = self.command_history[self.history_index]
                self.renderer.update_command_line(self.command_buffer)
            elif self.history_index == len(self.command_history) - 1:
                self.history_index = len(self.command_history)
                self.command_buffer = ""
                self.renderer.update_command_line("")
            return

        # Add character to command
        if not key.startswith("CTRL-") and not key.startswith("ALT-"):
            self.command_buffer += key
            self.renderer.update_command_line(self.command_buffer)

    def _process_replace_mode(self, key: str) -> None:
        """Process input in replace mode."""
        if key == "ESC":
            self.modes.to_normal()
            return

        if key == "BACKSPACE":
            # Move cursor back
            row, col = self.buffer.get_cursor()
            if col > 0:
                self.buffer.set_cursor(row, col - 1)
        elif not key.startswith("CTRL-") and not key.startswith("ALT-"):
            # Replace character at cursor
            row, col = self.buffer.get_cursor()
            lines = self.buffer.get_lines()
            if row < len(lines):
                line = lines[row]
                if col < len(line):
                    # Replace character
                    new_line = line[:col] + key + line[col + 1 :]
                    self.buffer.set_line(row, new_line)
                    # Move cursor forward
                    self.buffer.set_cursor(row, col + 1)

    def _process_search_mode(self, key: str) -> None:
        """Process input in search mode."""
        if key == "ESC":
            # Cancel search
            self.search_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
            return

        if key == "ENTER":
            # Execute search
            if self.search_buffer:
                self.search_pattern = self.search_buffer
                self._perform_search()

            self.search_buffer = ""
            self.renderer.clear_command_line()
            self.modes.to_normal()
            return

        if key == "BACKSPACE":
            if self.search_buffer:
                self.search_buffer = self.search_buffer[:-1]
                prefix = "/" if self.search_direction == "forward" else "?"
                self.renderer.update_command_line(prefix + self.search_buffer)
            else:
                # Empty search, return to normal mode
                self.modes.to_normal()
                self.renderer.clear_command_line()
            return

        # Add character to search
        if not key.startswith("CTRL-") and not key.startswith("ALT-"):
            self.search_buffer += key
            prefix = "/" if self.search_direction == "forward" else "?"
            self.renderer.update_command_line(prefix + self.search_buffer)

    def _execute_ex_command(self, command: str) -> None:
        """Execute an ex command."""
        # Basic ex commands
        if command == "q":
            if self.modified and not self.readonly:
                self.renderer.show_message("E37: No write since last change")
            else:
                self.running = False

        elif command == "q!":
            # Force quit
            self.running = False

        elif command == "w":
            # Write file
            self._save_file()

        elif command == "wq" or command == "x":
            # Write and quit
            if self._save_file():
                self.running = False

        elif command.startswith("w "):
            # Write to specific file
            filename = command[2:].strip()
            if filename:
                self._save_file(filename)

        elif command.startswith("e "):
            # Edit file
            filename = command[2:].strip()
            if filename:
                if self.modified:
                    self.renderer.show_message("E37: No write since last change")
                else:
                    self._load_file(filename)

        elif command.startswith("r "):
            # Read file into buffer
            filename = command[2:].strip()
            if filename:
                self._read_file_into_buffer(filename)

        elif command == "set nu" or command == "set number":
            # Enable line numbers
            self.renderer.set_line_numbers(True)

        elif command == "set nonu" or command == "set nonumber":
            # Disable line numbers
            self.renderer.set_line_numbers(False)

        else:
            # Try to execute through executor (for substitute, etc.)
            # This would need to be implemented in the executor
            self.renderer.show_message(f"E492: Not an editor command: {command}")

    def _save_file(self, filename: str | None = None) -> bool:
        """Save buffer to file."""
        if filename:
            self.filename = filename

        if not self.filename:
            self.renderer.show_message("E32: No file name")
            return False

        if self.readonly:
            self.renderer.show_message("E45: 'readonly' option is set")
            return False

        try:
            content = self.buffer.get_content()
            self.file_ops.write_file(self.filename, content)

            # Update saved content
            self.last_save_content = content
            self.modified = False

            # Show success message
            lines = len(self.buffer.get_lines())
            chars = len(content)
            self.renderer.show_message(f'"{self.filename}" {lines}L, {chars}C written')
            return True

        except Exception as e:
            self.renderer.show_message(f"E212: Can't open file for writing: {e}")
            return False

    def _load_file(self, filename: str) -> None:
        """Load a file into the buffer."""
        try:
            content = self.file_ops.read_file(filename)
            if content is not None:
                # Replace buffer content
                from .buffer.core import TextBuffer

                self.buffer = TextBuffer(content)
                self.executor.buffer = self.buffer
                self.filename = filename
                self.last_save_content = content
                self.modified = False

                lines = len(self.buffer.get_lines())
                self.renderer.show_message(f'"{filename}" {lines}L')
            else:
                # New file
                from .buffer.core import TextBuffer

                self.buffer = TextBuffer()
                self.executor.buffer = self.buffer
                self.filename = filename
                self.last_save_content = ""
                self.modified = False
                self.renderer.show_message(f'"{filename}" [New File]')

        except Exception as e:
            self.renderer.show_message(f"E484: Can't open file {filename}: {e}")

    def _read_file_into_buffer(self, filename: str) -> None:
        """Read a file and append to current buffer."""
        try:
            content = self.file_ops.read_file(filename)
            if content:
                row, _ = self.buffer.get_cursor()
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    self.buffer.insert_line(row + i + 1, line)

                self.renderer.show_message(f'"{filename}" {len(lines)}L')

        except Exception as e:
            self.renderer.show_message(f"E484: Can't open file {filename}: {e}")

    def _perform_search(self) -> None:
        """Perform search based on current pattern and direction."""
        if not self.search_pattern:
            return

        import re

        lines = self.buffer.get_lines()
        row, col = self.buffer.get_cursor()

        if self.search_direction == "forward":
            # Search forward from cursor
            for i in range(row, len(lines)):
                line = lines[i]
                start_col = col + 1 if i == row else 0

                try:
                    match = re.search(self.search_pattern, line[start_col:])
                    if match:
                        self.buffer.set_cursor(i, start_col + match.start())
                        return
                except re.error:
                    # Treat as literal search
                    idx = line[start_col:].find(self.search_pattern)
                    if idx >= 0:
                        self.buffer.set_cursor(i, start_col + idx)
                        return

            # Wrap around
            for i in range(0, row + 1):
                line = lines[i]
                end_col = col if i == row else len(line)

                try:
                    match = re.search(self.search_pattern, line[:end_col])
                    if match:
                        self.buffer.set_cursor(i, match.start())
                        self.renderer.show_message("search hit BOTTOM, continuing at TOP")
                        return
                except re.error:
                    idx = line[:end_col].find(self.search_pattern)
                    if idx >= 0:
                        self.buffer.set_cursor(i, idx)
                        self.renderer.show_message("search hit BOTTOM, continuing at TOP")
                        return

        else:  # backward
            # Search backward from cursor
            for i in range(row, -1, -1):
                line = lines[i]
                end_col = col if i == row else len(line)

                # Find last match before cursor
                try:
                    matches = list(re.finditer(self.search_pattern, line[:end_col]))
                    if matches:
                        last_match = matches[-1]
                        self.buffer.set_cursor(i, last_match.start())
                        return
                except re.error:
                    idx = line[:end_col].rfind(self.search_pattern)
                    if idx >= 0:
                        self.buffer.set_cursor(i, idx)
                        return

            # Wrap around
            for i in range(len(lines) - 1, row - 1, -1):
                line = lines[i]
                start_col = col + 1 if i == row else 0

                try:
                    matches = list(re.finditer(self.search_pattern, line[start_col:]))
                    if matches:
                        last_match = matches[-1]
                        self.buffer.set_cursor(i, start_col + last_match.start())
                        self.renderer.show_message("search hit TOP, continuing at BOTTOM")
                        return
                except re.error:
                    idx = line[start_col:].rfind(self.search_pattern)
                    if idx >= 0:
                        self.buffer.set_cursor(i, start_col + idx)
                        self.renderer.show_message("search hit TOP, continuing at BOTTOM")
                        return

        # Pattern not found
        self.renderer.show_message(f"Pattern not found: {self.search_pattern}")
        self.renderer.beep()

    def _repeat_search(self, same_direction: bool) -> None:
        """Repeat the last search."""
        if not self.search_pattern:
            self.renderer.show_message("No previous search pattern")
            return

        # Save original direction
        original_direction = self.search_direction

        # Adjust direction if needed
        if not same_direction:
            self.search_direction = "backward" if self.search_direction == "forward" else "forward"

        # Perform search
        self._perform_search()

        # Restore original direction
        self.search_direction = original_direction

    def _start_macro_recording(self, register: str) -> None:
        """Start recording a macro to the specified register."""
        self.recording_macro = True
        self.macro_register = register
        self.macro_buffer = []
        self.renderer.show_message(f"recording @{register}")

    def _stop_macro_recording(self) -> None:
        """Stop recording the current macro."""
        if self.recording_macro:
            # Store macro in registers or macro system
            # This would need integration with the macro system
            self.recording_macro = False
            self.renderer.show_message(f"Recorded macro @{self.macro_register}")
            self.macro_register = ""

    def _play_macro(self, register: str) -> None:
        """Play a macro from the specified register."""
        # This would need integration with the macro system
        self.renderer.show_message(f"@{register} (not implemented)")

    def _update_modified_status(self) -> None:
        """Update the modified status of the buffer."""
        current_content = self.buffer.get_content()
        self.modified = current_content != self.last_save_content

    def _handle_interrupt(self) -> None:
        """Handle Ctrl-C interrupt."""
        # Return to normal mode
        self.modes.to_normal()

        # Clear any pending state
        self.command_buffer = ""
        self.search_buffer = ""
        self.normal_command_buffer = ""
        self.repeat_count = ""

        # Show message
        self.renderer.show_message("Type :q! to quit without saving")
