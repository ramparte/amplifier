# Vi Macro Recording and Playback System

This module implements macro recording and playback functionality for the vi editor, allowing users to record sequences of keystrokes and replay them.

## Features

### Recording Macros
- **`q{register}`** - Start recording keystrokes to a register (a-z)
- **`q`** - Stop recording the current macro
- All keystrokes are captured during recording
- Macros are stored in the existing register system
- Recording state is tracked to prevent nested recording

### Playing Macros
- **`@{register}`** - Execute a macro from the specified register
- **`@@`** - Repeat the last executed macro
- **`{count}@{register}`** - Execute macro multiple times
- Configurable error handling (stop on first error or continue)
- Protection against infinite recursion with depth limits

## Architecture

### Components

1. **MacroState** (`state.py`)
   - Manages recording and playback state
   - Tracks current recording register
   - Maintains playback depth for recursion prevention
   - Configurable error handling behavior

2. **MacroRecorder** (`recorder.py`)
   - Handles macro recording operations
   - Validates register names (a-z only)
   - Stores recorded keystrokes in registers
   - Prevents recording during playback

3. **MacroPlayer** (`player.py`)
   - Executes macros from registers
   - Integrates with CommandDispatcher for key replay
   - Handles repeat functionality (`@@`)
   - Manages nested playback depth

## Integration

The macro system integrates seamlessly with:
- **Register System**: Uses existing registers for storage
- **Command Dispatcher**: Replays keys through normal command processing
- **Command Registry**: Registers macro commands (`q`, `@`, `@@`)

## Usage Examples

### Record and Play a Simple Macro

```
qa          # Start recording to register 'a'
dd          # Delete current line
j           # Move down
p           # Paste
q           # Stop recording
@a          # Play macro from register 'a'
3@a         # Play macro 3 times
@@          # Repeat last macro
```

### Error Handling

The system handles errors gracefully:
- Invalid register names are rejected
- Empty macros are not stored
- Playback errors can stop execution or continue (configurable)
- Maximum depth prevents infinite recursion

## Configuration

- `stop_on_error`: Whether to halt macro playback on first error (default: True)
- `max_playback_depth`: Maximum nested macro depth (default: 100)

## Testing

Comprehensive unit tests cover:
- Recording functionality
- Playback with counts
- Error handling
- State management
- Integration with registers

Run tests with:
```bash
uv run pytest vi/commands/macros/test_macros.py -v
```