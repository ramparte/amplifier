"""Macro state management for vi editor."""

from dataclasses import dataclass
from dataclasses import field


@dataclass
class MacroState:
    """Manages the state of macro recording and playback."""

    # Recording state
    is_recording: bool = False
    recording_register: str | None = None
    recorded_keys: list[str] = field(default_factory=list)

    # Playback state
    is_playing: bool = False
    last_played_register: str | None = None
    playback_depth: int = 0  # Track nested macro playback

    # Configuration
    stop_on_error: bool = True  # Whether to stop playback on first error
    max_playback_depth: int = 100  # Maximum nested macro depth to prevent infinite loops

    def start_recording(self, register: str) -> None:
        """Start recording a macro to the specified register.

        Args:
            register: Register name (a-z) to record into
        """
        self.is_recording = True
        self.recording_register = register
        self.recorded_keys = []

    def stop_recording(self) -> tuple[str, list[str]]:
        """Stop recording and return the recorded data.

        Returns:
            Tuple of (register, keys) that were recorded
        """
        register = self.recording_register
        keys = self.recorded_keys.copy()

        self.is_recording = False
        self.recording_register = None
        self.recorded_keys = []

        return register, keys

    def add_recorded_key(self, key: str) -> None:
        """Add a key to the current recording.

        Args:
            key: Key to record
        """
        if self.is_recording:
            self.recorded_keys.append(key)

    def start_playback(self, register: str) -> bool:
        """Start playing back a macro.

        Args:
            register: Register to play back

        Returns:
            True if playback can start, False if max depth exceeded
        """
        if self.playback_depth >= self.max_playback_depth:
            return False

        self.is_playing = True
        self.last_played_register = register
        self.playback_depth += 1
        return True

    def end_playback(self) -> None:
        """End the current playback session."""
        if self.playback_depth > 0:
            self.playback_depth -= 1

        if self.playback_depth == 0:
            self.is_playing = False

    def reset(self) -> None:
        """Reset all macro state."""
        self.is_recording = False
        self.recording_register = None
        self.recorded_keys = []
        self.is_playing = False
        self.playback_depth = 0

    def can_record(self) -> bool:
        """Check if recording can start.

        Returns:
            True if not currently recording
        """
        return not self.is_recording

    def can_playback(self) -> bool:
        """Check if playback can start.

        Returns:
            True if depth limit not exceeded
        """
        return self.playback_depth < self.max_playback_depth
