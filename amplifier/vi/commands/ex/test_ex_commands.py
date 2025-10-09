"""Unit tests for Ex command system."""

import tempfile
from pathlib import Path

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.ex.core_commands import ExCoreCommands
from amplifier.vi.commands.ex.parser import ExCommand
from amplifier.vi.commands.ex.parser import ExCommandParser
from amplifier.vi.commands.ex.settings import ExSettings
from amplifier.vi.commands.ex.substitution import ExSubstitution


class TestExCommandParser:
    """Test Ex command parsing."""

    def setup_method(self):
        """Set up test parser."""
        self.parser = ExCommandParser()

    def test_parse_simple_commands(self):
        """Test parsing simple commands without arguments."""
        # Write command
        cmd = self.parser.parse(":w")
        assert cmd.command == "write"
        assert not cmd.force
        assert cmd.args == ""

        # Quit command
        cmd = self.parser.parse(":q")
        assert cmd.command == "quit"
        assert not cmd.force

        # Force quit
        cmd = self.parser.parse(":q!")
        assert cmd.command == "quit"
        assert cmd.force

    def test_parse_commands_with_args(self):
        """Test parsing commands with arguments."""
        # Write with filename
        cmd = self.parser.parse(":w file.txt")
        assert cmd.command == "write"
        assert cmd.args == "file.txt"

        # Edit with filename
        cmd = self.parser.parse(":e another.txt")
        assert cmd.command == "edit"
        assert cmd.args == "another.txt"

    def test_parse_ranges(self):
        """Test parsing range specifications."""
        # Single line number
        cmd = self.parser.parse(":5d")
        assert cmd.range_start == 5
        assert cmd.range_end == 5

        # Range
        cmd = self.parser.parse(":1,10d")
        assert cmd.range_start == 1
        assert cmd.range_end == 10

        # Current line
        cmd = self.parser.parse(":.d")
        assert cmd.range_start == 0  # 0 means current line
        assert cmd.range_end == 0

        # Last line
        cmd = self.parser.parse(":$d")
        assert cmd.range_start == -1  # -1 means last line
        assert cmd.range_end == -1

        # All lines
        cmd = self.parser.parse(":%d")
        assert cmd.range_start == 1
        assert cmd.range_end == -1

    def test_parse_substitution(self):
        """Test parsing substitution commands."""
        # Basic substitution
        cmd = self.parser.parse(":s/old/new/")
        assert cmd.command == "substitute"
        assert cmd.args == "old/new"
        assert cmd.flags == ""

        # With flags
        cmd = self.parser.parse(":s/old/new/gi")
        assert cmd.command == "substitute"
        assert cmd.args == "old/new"
        assert cmd.flags == "gi"

        # With range
        cmd = self.parser.parse(":%s/old/new/g")
        assert cmd.command == "substitute"
        assert cmd.range_start == 1
        assert cmd.range_end == -1
        assert cmd.flags == "g"

    def test_parse_abbreviations(self):
        """Test command abbreviation expansion."""
        cmd = self.parser.parse(":wq")
        assert cmd.command == "writequit"

        cmd = self.parser.parse(":x")
        assert cmd.command == "exit"

    def test_parse_multiple_commands(self):
        """Test parsing multiple piped commands."""
        commands = self.parser.parse_multiple(":w | q")
        assert len(commands) == 2
        assert commands[0].command == "write"
        assert commands[1].command == "quit"


class TestExCoreCommands:
    """Test core Ex commands."""

    def setup_method(self):
        """Set up test environment."""
        self.buffer = TextBuffer("Line 1\nLine 2\nLine 3")
        self.core = ExCoreCommands(self.buffer)
        self.temp_dir = tempfile.mkdtemp()

    def test_write_command(self):
        """Test :w command."""
        # Write to new file
        filepath = Path(self.temp_dir) / "test.txt"
        cmd = ExCommand(command="write", args=str(filepath))
        success, msg = self.core.execute(cmd)

        assert success
        assert filepath.exists()
        assert filepath.read_text() == "Line 1\nLine 2\nLine 3"

    def test_write_range(self):
        """Test writing a range of lines."""
        filepath = Path(self.temp_dir) / "partial.txt"
        cmd = ExCommand(command="write", args=str(filepath), range_start=1, range_end=2)
        success, msg = self.core.execute(cmd)

        assert success
        assert filepath.read_text() == "Line 1\nLine 2"

    def test_quit_command(self):
        """Test :q command."""
        # Quit without changes
        cmd = ExCommand(command="quit")
        success, msg = self.core.execute(cmd)
        assert success
        assert msg == "quit"

        # Try to quit with changes
        self.core.set_modified(True)
        cmd = ExCommand(command="quit")
        success, msg = self.core.execute(cmd)
        assert not success
        assert "No write since last change" in msg

        # Force quit with changes
        cmd = ExCommand(command="quit", force=True)
        success, msg = self.core.execute(cmd)
        assert success

    def test_edit_command(self):
        """Test :e command."""
        # Create a test file
        filepath = Path(self.temp_dir) / "existing.txt"
        filepath.write_text("Existing content")

        # Edit the file
        cmd = ExCommand(command="edit", args=str(filepath))
        success, msg = self.core.execute(cmd)

        assert success
        assert self.buffer.get_content() == "Existing content"
        assert self.core.current_file == filepath

    def test_read_command(self):
        """Test :r command."""
        # Create a file to read
        filepath = Path(self.temp_dir) / "to_read.txt"
        filepath.write_text("Read me")

        # Read file at cursor
        cmd = ExCommand(command="read", args=str(filepath))
        success, msg = self.core.execute(cmd)

        assert success
        lines = self.buffer.get_lines()
        assert "Read me" in lines


class TestExSubstitution:
    """Test substitution commands."""

    def setup_method(self):
        """Set up test environment."""
        self.buffer = TextBuffer("foo bar\nbar baz\nfoo foo")
        self.subst = ExSubstitution(self.buffer)

    def test_simple_substitution(self):
        """Test basic substitution on current line."""
        cmd = ExCommand(command="substitute", args="foo/FOO", flags="")
        success, msg = self.subst.execute(cmd)

        assert success
        assert self.buffer.get_lines()[0] == "FOO bar"
        assert self.buffer.get_lines()[2] == "foo foo"  # Unchanged

    def test_global_substitution(self):
        """Test global substitution on current line."""
        self.buffer.set_cursor(2, 0)  # Move to third line
        cmd = ExCommand(command="substitute", args="foo/FOO", flags="g")
        success, msg = self.subst.execute(cmd)

        assert success
        assert self.buffer.get_lines()[2] == "FOO FOO"

    def test_range_substitution(self):
        """Test substitution over a range."""
        cmd = ExCommand(command="substitute", args="foo/FOO", range_start=1, range_end=3, flags="g")
        success, msg = self.subst.execute(cmd)

        assert success
        assert self.buffer.get_lines()[0] == "FOO bar"
        assert self.buffer.get_lines()[2] == "FOO FOO"

    def test_all_lines_substitution(self):
        """Test substitution on all lines."""
        cmd = ExCommand(command="substitute", args="bar/BAR", range_start=1, range_end=-1, flags="g")
        success, msg = self.subst.execute(cmd)

        assert success
        assert self.buffer.get_lines()[0] == "foo BAR"
        assert self.buffer.get_lines()[1] == "BAR baz"

    def test_case_insensitive_substitution(self):
        """Test case insensitive substitution."""
        cmd = ExCommand(command="substitute", args="FOO/replaced", flags="i")
        success, msg = self.subst.execute(cmd)

        assert success
        assert self.buffer.get_lines()[0] == "replaced bar"

    def test_repeat_last_substitution(self):
        """Test repeating the last substitution."""
        # First substitution
        cmd = ExCommand(command="substitute", args="foo/FOO", flags="g")
        self.subst.execute(cmd)

        # Move to different line and repeat
        self.buffer.set_cursor(1, 0)
        success, msg = self.subst.repeat_last()

        assert success
        # Should apply the same substitution to current line


class TestExSettings:
    """Test :set commands."""

    def setup_method(self):
        """Set up test environment."""
        self.settings = ExSettings()

    def test_set_boolean_true(self):
        """Test setting boolean options to true."""
        cmd = ExCommand(command="set", args="number")
        success, _ = self.settings.execute(cmd)

        assert success
        assert self.settings.get("number") is True

    def test_set_boolean_false(self):
        """Test setting boolean options to false."""
        # First set to true
        self.settings.execute(ExCommand(command="set", args="number"))

        # Then set to false
        cmd = ExCommand(command="set", args="nonumber")
        success, _ = self.settings.execute(cmd)

        assert success
        assert self.settings.get("number") is False

    def test_set_integer_value(self):
        """Test setting integer values."""
        cmd = ExCommand(command="set", args="tabstop=4")
        success, _ = self.settings.execute(cmd)

        assert success
        assert self.settings.get("tabstop") == 4

    def test_query_setting(self):
        """Test querying setting values."""
        # Set a value
        self.settings.execute(ExCommand(command="set", args="tabstop=4"))

        # Query it
        cmd = ExCommand(command="set", args="tabstop?")
        success, msg = self.settings.execute(cmd)

        assert success
        assert "tabstop=4" in msg

    def test_toggle_setting(self):
        """Test toggling boolean settings."""
        # Set to true
        self.settings.execute(ExCommand(command="set", args="number"))

        # Toggle it
        cmd = ExCommand(command="set", args="invnumber")
        success, _ = self.settings.execute(cmd)

        assert success
        assert self.settings.get("number") is False

    def test_setting_aliases(self):
        """Test setting name aliases."""
        # Use alias
        cmd = ExCommand(command="set", args="nu")
        success, _ = self.settings.execute(cmd)

        assert success
        assert self.settings.get("number") is True

        # Set with full name, query with alias
        cmd = ExCommand(command="set", args="tabstop=4")
        self.settings.execute(cmd)
        assert self.settings.get("ts") == 4

    def test_multiple_settings(self):
        """Test setting multiple options at once."""
        cmd = ExCommand(command="set", args="number tabstop=4 expandtab")
        success, _ = self.settings.execute(cmd)

        assert success
        assert self.settings.get("number") is True
        assert self.settings.get("tabstop") == 4
        assert self.settings.get("expandtab") is True
