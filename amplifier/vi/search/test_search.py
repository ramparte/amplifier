"""Unit tests for vi editor search functionality."""

from amplifier.vi.buffer.core import TextBuffer
from amplifier.vi.commands.registry import CommandContext
from amplifier.vi.commands.registry import CommandRegistry
from amplifier.vi.search.commands import get_search_manager
from amplifier.vi.search.commands import handle_backward_search
from amplifier.vi.search.commands import handle_forward_search
from amplifier.vi.search.commands import handle_next_match
from amplifier.vi.search.commands import handle_previous_match
from amplifier.vi.search.commands import handle_word_search_backward
from amplifier.vi.search.commands import handle_word_search_forward
from amplifier.vi.search.commands import register_search_commands
from amplifier.vi.search.engine import SearchDirection
from amplifier.vi.search.engine import SearchEngine
from amplifier.vi.search.state import SearchManager
from amplifier.vi.search.state import SearchState


class TestSearchEngine:
    """Test the search engine functionality."""

    def test_find_next_basic(self):
        """Test basic forward search."""
        engine = SearchEngine()
        lines = ["hello world", "test hello", "hello again"]

        # Find first occurrence (searches from position after cursor)
        match = engine.find_next(lines, "hello", 0, 0, wrap=False)
        assert match is not None
        assert match.row == 1  # Skips hello at position 0,0
        assert match.start_col == 5
        assert match.text == "hello"

        # Search from before first hello should find it
        match = engine.find_next(lines, "hello", 0, -1, wrap=False)
        assert match is not None
        assert match.row == 0
        assert match.start_col == 0

        # Find next occurrence
        match = engine.find_next(lines, "hello", 0, 5, wrap=False)
        assert match is not None
        assert match.row == 1
        assert match.start_col == 5

        # Find third occurrence
        match = engine.find_next(lines, "hello", 1, 6, wrap=False)
        assert match is not None
        assert match.row == 2
        assert match.start_col == 0

    def test_find_next_wrap(self):
        """Test forward search with wrap around."""
        engine = SearchEngine()
        lines = ["hello world", "test hello", "hello again"]

        # Search from end should wrap to beginning
        match = engine.find_next(lines, "hello", 2, 6, wrap=True)
        assert match is not None
        assert match.row == 0
        assert match.start_col == 0

    def test_find_previous_basic(self):
        """Test basic backward search."""
        engine = SearchEngine()
        lines = ["hello world", "test hello", "hello again"]

        # Find previous from end
        match = engine.find_previous(lines, "hello", 2, 10, wrap=False)
        assert match is not None
        assert match.row == 2
        assert match.start_col == 0

        # Continue backward
        match = engine.find_previous(lines, "hello", 2, 0, wrap=False)
        assert match is not None
        assert match.row == 1
        assert match.start_col == 5

    def test_find_previous_wrap(self):
        """Test backward search with wrap around."""
        engine = SearchEngine()
        lines = ["hello world", "test hello", "hello again"]

        # Search from beginning should wrap to end
        match = engine.find_previous(lines, "hello", 0, 0, wrap=True)
        assert match is not None
        assert match.row == 2
        assert match.start_col == 0

    def test_find_all_matches(self):
        """Test finding all matches in text."""
        engine = SearchEngine()
        text = "hello world\ntest hello\nhello again"

        matches = engine.find_all_matches(text, "hello")
        assert len(matches) == 3
        assert matches[0].row == 0
        assert matches[0].start_col == 0
        assert matches[1].row == 1
        assert matches[1].start_col == 5
        assert matches[2].row == 2
        assert matches[2].start_col == 0

    def test_case_insensitive_search(self):
        """Test case-insensitive search."""
        engine = SearchEngine(case_sensitive=False)
        lines = ["Hello World", "TEST hello", "HELLO again"]

        matches = engine.find_all_matches("\n".join(lines), "hello", case_sensitive=False)
        assert len(matches) == 3

    def test_regex_search(self):
        """Test regex pattern search."""
        engine = SearchEngine(use_regex=True)
        lines = ["test123", "hello456", "world789"]

        # Search for digits
        match = engine.find_next(lines, r"\d+", 0, 0, wrap=False)
        assert match is not None
        assert match.text == "123"

        # Search for word followed by digits
        matches = engine.find_all_matches("\n".join(lines), r"\w+\d+")
        assert len(matches) == 3

    def test_literal_search(self):
        """Test literal (non-regex) search."""
        engine = SearchEngine(use_regex=False)
        lines = ["test.*", "hello.*", ".*world"]

        # Should find literal .* not as regex
        match = engine.find_next(lines, ".*", 0, 0, wrap=False)
        assert match is not None
        assert match.text == ".*"
        assert match.row == 0
        assert match.start_col == 4

    def test_word_boundaries(self):
        """Test finding word boundaries."""
        engine = SearchEngine()

        # Test on word character
        boundaries = engine.find_word_boundaries("hello world", 2)
        assert boundaries == (0, 5)

        # Test at word start
        boundaries = engine.find_word_boundaries("hello world", 0)
        assert boundaries == (0, 5)

        # Test at word end
        boundaries = engine.find_word_boundaries("hello world", 4)
        assert boundaries == (0, 5)

        # Test on space (not a word)
        boundaries = engine.find_word_boundaries("hello world", 5)
        assert boundaries is None

        # Test with underscores (part of word)
        boundaries = engine.find_word_boundaries("test_word_here", 7)
        assert boundaries == (0, 14)


class TestSearchState:
    """Test search state management."""

    def test_search_history(self):
        """Test search history management."""
        state = SearchState()

        # Add patterns to history
        state.add_to_history("pattern1")
        state.add_to_history("pattern2")
        state.add_to_history("pattern3")

        assert len(state.search_history) == 3
        assert state.search_history[-1] == "pattern3"

        # Adding duplicate should move it to end
        state.add_to_history("pattern1")
        assert len(state.search_history) == 3
        assert state.search_history[-1] == "pattern1"
        assert "pattern1" not in state.search_history[:-1]

    def test_history_navigation(self):
        """Test navigating through search history."""
        state = SearchState()
        state.add_to_history("first")
        state.add_to_history("second")
        state.add_to_history("third")

        # Navigate backward
        assert state.get_previous_history() == "second"
        assert state.get_previous_history() == "first"
        assert state.get_previous_history() == "first"  # At start

        # Navigate forward
        assert state.get_next_history() == "second"
        assert state.get_next_history() == "third"
        assert state.get_next_history() is None  # At end

    def test_match_tracking(self):
        """Test tracking search matches."""
        state = SearchState()
        from amplifier.vi.search.engine import SearchMatch

        matches = [
            SearchMatch(row=0, start_col=0, end_col=5, text="hello"),
            SearchMatch(row=1, start_col=6, end_col=11, text="hello"),
            SearchMatch(row=2, start_col=0, end_col=5, text="hello"),
        ]

        # Set matches and find closest to position
        state.set_matches(matches, 0, 3)
        assert state.current_match == matches[1]  # First match after position

        # Test next/previous navigation
        next_match = state.next_match()
        assert next_match == matches[2]

        next_match = state.next_match()
        assert next_match == matches[0]  # Wrapped around

        prev_match = state.previous_match()
        assert prev_match == matches[2]


class TestSearchManager:
    """Test the search manager."""

    def test_basic_search(self):
        """Test basic search operations."""
        manager = SearchManager()
        lines = ["hello world", "test hello", "hello again"]

        # Forward search from 0,0 finds next occurrence
        match = manager.search("hello", lines, 0, 0, SearchDirection.FORWARD)
        assert match is not None
        assert match.row == 1  # Finds next match after cursor
        assert match.start_col == 5

        # Pattern should be in history
        assert "hello" in manager.state.search_history

    def test_repeat_search(self):
        """Test repeating searches."""
        manager = SearchManager()
        lines = ["hello world", "test hello", "hello again"]

        # Initial search from before first hello
        manager.search("hello", lines, 0, -1, SearchDirection.FORWARD)

        # Repeat in same direction from after first hello
        match = manager.repeat_search(lines, 0, 5, reverse=False)
        assert match is not None
        assert match.row == 1

        # Repeat in reverse direction
        match = manager.repeat_search(lines, 1, 5, reverse=True)
        assert match is not None
        assert match.row == 0

    def test_word_under_cursor(self):
        """Test searching for word under cursor."""
        manager = SearchManager()
        lines = ["hello world", "test hello there", "hello again"]

        # Search forward for word "hello"
        match = manager.search_word_under_cursor(lines, 0, 2, forward=True)
        assert match is not None
        assert match.row == 1
        assert match.start_col == 5

        # Pattern should be word-bounded
        assert manager.state.pattern == r"\bhello\b"

    def test_char_search_memory(self):
        """Test character search memory."""
        manager = SearchManager()

        # Store character search
        manager.set_char_search("x", "f")
        assert manager.get_char_search() == ("x", "f")

        # Update character search
        manager.set_char_search("y", "F")
        assert manager.get_char_search() == ("y", "F")


class TestSearchCommands:
    """Test search command handlers."""

    def setup_method(self):
        """Set up test fixtures."""
        self.buffer = TextBuffer("hello world\ntest hello\nhello again")
        self.registry = CommandRegistry()
        self.context = CommandContext(buffer=self.buffer, modes=None, renderer=None)

        # Clear search manager state
        manager = get_search_manager()
        manager.state.reset()

    def test_forward_search_command(self):
        """Test forward search command."""
        # Set up search pattern
        self.context.extra_args["pattern"] = "hello"

        # Execute search from 0,0 (cursor is at start of "hello")
        result = handle_forward_search(self.context)
        assert result is True

        # Should move to next match (skips current position)
        row, col = self.buffer.get_cursor()
        assert row == 1
        assert col == 5

        # Execute again to find next
        self.buffer.set_cursor(1, 6)
        result = handle_forward_search(self.context)
        assert result is True

        row, col = self.buffer.get_cursor()
        assert row == 2
        assert col == 0

    def test_backward_search_command(self):
        """Test backward search command."""
        # Start from end
        self.buffer.set_cursor(2, 10)
        self.context.extra_args["pattern"] = "hello"

        # Execute backward search
        result = handle_backward_search(self.context)
        assert result is True

        # Should find last occurrence
        row, col = self.buffer.get_cursor()
        assert row == 2
        assert col == 0

    def test_next_previous_commands(self):
        """Test n and N commands."""
        # Set up initial search
        self.context.extra_args["pattern"] = "hello"
        handle_forward_search(self.context)
        # Now at row 1, col 5 (second hello)

        # Move to next match (n)
        result = handle_next_match(self.context)
        assert result is True
        row, col = self.buffer.get_cursor()
        assert row == 2  # Third hello

        # Move to previous match (N)
        result = handle_previous_match(self.context)
        assert result is True
        row, col = self.buffer.get_cursor()
        assert row == 1  # Back to second hello

    def test_word_search_commands(self):
        """Test * and # commands."""
        # Position on "hello"
        self.buffer.set_cursor(0, 2)

        # Search forward (*)
        result = handle_word_search_forward(self.context)
        assert result is True
        row, col = self.buffer.get_cursor()
        assert row == 1
        assert col == 5

        # Search backward (#)
        result = handle_word_search_backward(self.context)
        assert result is True
        row, col = self.buffer.get_cursor()
        assert row == 0
        assert col == 0

    def test_command_registration(self):
        """Test that all commands are registered properly."""
        registry = CommandRegistry()
        register_search_commands(registry)

        # Check that key commands are registered
        assert (
            registry.get_command("/", registry.commands["/"][list(registry.commands["/"].keys())[0]].modes.pop())
            is not None
        )
        assert (
            registry.get_command("?", registry.commands["?"][list(registry.commands["?"].keys())[0]].modes.pop())
            is not None
        )
        assert (
            registry.get_command("n", registry.commands["n"][list(registry.commands["n"].keys())[0]].modes.pop())
            is not None
        )
        assert (
            registry.get_command("N", registry.commands["N"][list(registry.commands["N"].keys())[0]].modes.pop())
            is not None
        )
        assert (
            registry.get_command("*", registry.commands["*"][list(registry.commands["*"].keys())[0]].modes.pop())
            is not None
        )
        assert (
            registry.get_command("#", registry.commands["#"][list(registry.commands["#"].keys())[0]].modes.pop())
            is not None
        )


class TestSearchIntegration:
    """Integration tests for search functionality."""

    def test_search_with_count(self):
        """Test search commands with numeric count."""
        buffer = TextBuffer("word1 word2 word3\nword1 word2\nword1")
        context = CommandContext(buffer=buffer, modes=None, renderer=None, count=2)

        # Search with count should find 2nd occurrence
        context.extra_args["pattern"] = "word1"
        manager = get_search_manager()
        manager.state.reset()

        # First search (from 0,0 finds next occurrence)
        handle_forward_search(context)
        row, col = buffer.get_cursor()
        assert row == 1  # Finds second word1 on next line

        # Search with n and count=2 (not implemented in basic version)
        # This would need additional logic to handle count properly

    def test_search_empty_buffer(self):
        """Test search in empty buffer."""
        buffer = TextBuffer("")
        context = CommandContext(buffer=buffer, modes=None, renderer=None)
        context.extra_args["pattern"] = "test"

        result = handle_forward_search(context)
        assert result is False

    def test_search_pattern_not_found(self):
        """Test searching for non-existent pattern."""
        buffer = TextBuffer("hello world")
        context = CommandContext(buffer=buffer, modes=None, renderer=None)
        context.extra_args["pattern"] = "xyz"

        result = handle_forward_search(context)
        assert result is False

        # Cursor should not move
        row, col = buffer.get_cursor()
        assert row == 0
        assert col == 0
