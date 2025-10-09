"""Unit tests for the macro recording and playback system."""

import pytest

from ...buffer.core import TextBuffer
from ..editing.registers import RegisterManager
from ..registry import CommandContext
from ..registry import CommandDispatcher
from ..registry import CommandRegistry
from .player import MacroPlayer
from .recorder import MacroRecorder
from .state import MacroState


@pytest.fixture
def setup():
    """Set up test environment."""
    buffer = TextBuffer("Hello world\nSecond line\nThird line")

    register_manager = RegisterManager()
    macro_state = MacroState()
    recorder = MacroRecorder(register_manager, macro_state)
    player = MacroPlayer(register_manager, macro_state)

    # Create a mock dispatcher
    registry = CommandRegistry()
    dispatcher = CommandDispatcher(registry)
    player.set_dispatcher(dispatcher)

    # Create context
    context = CommandContext(
        buffer=buffer,
        modes=None,
        renderer=None,
    )

    return {
        "buffer": buffer,
        "register_manager": register_manager,
        "macro_state": macro_state,
        "recorder": recorder,
        "player": player,
        "dispatcher": dispatcher,
        "context": context,
    }


class TestMacroRecording:
    """Test macro recording functionality."""

    def test_start_recording(self, setup):
        """Test starting macro recording."""
        recorder = setup["recorder"]

        # Start recording to register 'a'
        success, error = recorder.start_recording("a")
        assert success
        assert error is None
        assert recorder.is_recording()
        assert recorder.get_recording_register() == "a"

    def test_invalid_register(self, setup):
        """Test recording with invalid register."""
        recorder = setup["recorder"]

        # Try invalid registers
        success, error = recorder.start_recording("1")
        assert not success
        assert "Invalid macro register" in error

        success, error = recorder.start_recording("A")
        assert not success
        assert "Invalid macro register" in error

    def test_already_recording(self, setup):
        """Test trying to start recording when already recording."""
        recorder = setup["recorder"]

        # Start first recording
        recorder.start_recording("a")

        # Try to start another
        success, error = recorder.start_recording("b")
        assert not success
        assert "Already recording" in error

    def test_record_keys(self, setup):
        """Test recording keystrokes."""
        recorder = setup["recorder"]
        macro_state = setup["macro_state"]

        # Start recording
        recorder.start_recording("a")

        # Record some keys
        recorder.record_key("d")
        recorder.record_key("d")
        recorder.record_key("j")
        recorder.record_key("p")

        # Check keys are being recorded
        assert macro_state.recorded_keys == ["d", "d", "j", "p"]

    def test_stop_recording(self, setup):
        """Test stopping macro recording."""
        recorder = setup["recorder"]
        register_manager = setup["register_manager"]

        # Start recording
        recorder.start_recording("a")

        # Record some keys
        recorder.record_key("d")
        recorder.record_key("w")
        recorder.record_key("q")  # The 'q' to stop recording

        # Stop recording
        success, error = recorder.stop_recording()
        assert success
        assert error is None
        assert not recorder.is_recording()

        # Check macro was stored (without the final 'q')
        content = register_manager.get("a")
        assert content is not None
        assert content.text == "dw"

    def test_stop_without_recording(self, setup):
        """Test stopping when not recording."""
        recorder = setup["recorder"]

        success, error = recorder.stop_recording()
        assert not success
        assert "Not recording" in error

    def test_empty_macro(self, setup):
        """Test recording an empty macro."""
        recorder = setup["recorder"]

        # Start and immediately stop
        recorder.start_recording("a")
        success, error = recorder.stop_recording()

        assert not success
        assert "No keys recorded" in error


class TestMacroPlayback:
    """Test macro playback functionality."""

    def test_play_macro(self, setup):
        """Test playing back a recorded macro."""
        player = setup["player"]
        register_manager = setup["register_manager"]
        context = setup["context"]

        # Store a macro in register 'a'
        register_manager.set("a", "jjj", is_linewise=False)

        # Create a mock process_key that tracks calls
        calls = []

        def mock_process_key(key, mode, ctx):
            calls.append(key)
            return (True, None)

        player.dispatcher.process_key = mock_process_key

        # Play the macro
        success, error = player.play_macro("a", context)
        assert success
        assert error is None
        assert calls == ["j", "j", "j"]

    def test_play_nonexistent_macro(self, setup):
        """Test playing a macro that doesn't exist."""
        player = setup["player"]
        context = setup["context"]

        success, error = player.play_macro("z", context)
        assert not success
        assert "No macro recorded" in error

    def test_play_with_count(self, setup):
        """Test playing a macro multiple times."""
        player = setup["player"]
        register_manager = setup["register_manager"]
        context = setup["context"]

        # Store a macro
        register_manager.set("a", "x", is_linewise=False)

        # Track calls
        calls = []

        def mock_process_key(key, mode, ctx):
            calls.append(key)
            return (True, None)

        player.dispatcher.process_key = mock_process_key

        # Play 3 times
        success, error = player.play_macro("a", context, count=3)
        assert success
        assert calls == ["x", "x", "x"]

    def test_repeat_last_macro(self, setup):
        """Test repeating the last played macro."""
        player = setup["player"]
        register_manager = setup["register_manager"]
        context = setup["context"]
        macro_state = setup["macro_state"]

        # Store and play a macro
        register_manager.set("b", "dd", is_linewise=False)

        calls = []

        def mock_process_key(key, mode, ctx):
            calls.append(key)
            return (True, None)

        player.dispatcher.process_key = mock_process_key

        # Play macro
        player.play_macro("b", context)
        assert macro_state.last_played_register == "b"

        # Clear calls
        calls.clear()

        # Repeat last macro
        success, error = player.repeat_last_macro(context)
        assert success
        assert calls == ["d", "d"]

    def test_no_macro_to_repeat(self, setup):
        """Test repeating when no macro has been played."""
        player = setup["player"]
        context = setup["context"]

        success, error = player.repeat_last_macro(context)
        assert not success
        assert "No previous macro" in error

    def test_error_during_playback(self, setup):
        """Test handling errors during macro playback."""
        player = setup["player"]
        register_manager = setup["register_manager"]
        context = setup["context"]
        macro_state = setup["macro_state"]

        # Store a macro with multiple commands
        register_manager.set("a", "abc", is_linewise=False)

        # Mock process_key that fails on 'b'
        calls = []

        def mock_process_key(key, mode, ctx):
            calls.append(key)
            if key == "b":
                return (False, "Command failed")
            return (True, None)

        player.dispatcher.process_key = mock_process_key

        # Play macro with stop_on_error=True (default)
        success, error = player.play_macro("a", context)
        assert not success
        assert "Macro playback error" in error
        assert calls == ["a", "b"]  # Stopped at 'b'

        # Play with stop_on_error=False
        calls.clear()
        macro_state.stop_on_error = False
        success, error = player.play_macro("a", context)
        assert success  # Continues despite error
        assert calls == ["a", "b", "c"]  # All commands executed

    def test_nested_macro_depth_limit(self, setup):
        """Test that nested macros respect depth limit."""
        player = setup["player"]
        context = setup["context"]
        macro_state = setup["macro_state"]

        # Set a low depth limit
        macro_state.max_playback_depth = 2

        # Simulate deep nesting
        macro_state.playback_depth = 2

        success, error = player.play_macro("a", context)
        assert not success
        assert "Maximum macro depth" in error

    def test_skip_recording_during_playback(self, setup):
        """Test that 'q' is skipped during macro playback."""
        player = setup["player"]
        register_manager = setup["register_manager"]
        context = setup["context"]

        # Store a macro with 'q' in it
        register_manager.set("a", "qqq", is_linewise=False)

        # Track calls - 'q' should be skipped
        calls = []

        def mock_process_key(key, mode, ctx):
            calls.append(key)
            return (True, None)

        player.dispatcher.process_key = mock_process_key

        # Play the macro
        success, error = player.play_macro("a", context)
        assert success
        assert calls == []  # All 'q's were skipped


class TestMacroState:
    """Test macro state management."""

    def test_start_recording(self, setup):
        """Test state changes when starting recording."""
        state = setup["macro_state"]

        state.start_recording("x")
        assert state.is_recording
        assert state.recording_register == "x"
        assert state.recorded_keys == []

    def test_stop_recording(self, setup):
        """Test state changes when stopping recording."""
        state = setup["macro_state"]

        state.start_recording("y")
        state.add_recorded_key("a")
        state.add_recorded_key("b")

        register, keys = state.stop_recording()
        assert register == "y"
        assert keys == ["a", "b"]
        assert not state.is_recording
        assert state.recording_register is None
        assert state.recorded_keys == []

    def test_playback_state(self, setup):
        """Test playback state management."""
        state = setup["macro_state"]

        # Start playback
        assert state.start_playback("a")
        assert state.is_playing
        assert state.last_played_register == "a"
        assert state.playback_depth == 1

        # Nested playback
        assert state.start_playback("b")
        assert state.playback_depth == 2

        # End nested
        state.end_playback()
        assert state.playback_depth == 1
        assert state.is_playing  # Still playing outer macro

        # End outer
        state.end_playback()
        assert state.playback_depth == 0
        assert not state.is_playing

    def test_reset(self, setup):
        """Test resetting macro state."""
        state = setup["macro_state"]

        # Set various states
        state.start_recording("m")
        state.add_recorded_key("x")
        state.is_playing = True
        state.playback_depth = 5

        # Reset
        state.reset()

        assert not state.is_recording
        assert state.recording_register is None
        assert state.recorded_keys == []
        assert not state.is_playing
        assert state.playback_depth == 0
