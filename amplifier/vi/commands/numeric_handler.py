"""Numeric prefix handler for vi commands.

Handles parsing and processing of numeric prefixes (counts) for commands.
Examples: 5j (move down 5 lines), 3dd (delete 3 lines), 10w (move 10 words)
"""


class NumericPrefixHandler:
    """Handles numeric prefix parsing and state management."""

    def __init__(self):
        """Initialize the numeric prefix handler."""
        self.pending_count = ""
        self.operator_count = ""
        self.motion_count = ""
        self.in_operator_pending = False

    def process_digit(self, digit: str) -> bool:
        """Process a digit character.

        Args:
            digit: Single digit character ('0'-'9')

        Returns:
            True if digit was processed, False if it should be treated as a command
        """
        if not digit.isdigit():
            return False

        # '0' is only a count if we already have digits
        if digit == "0" and not self.pending_count and not self.in_operator_pending:
            return False  # '0' is a command (move to start of line)

        # Add to appropriate count buffer
        if self.in_operator_pending:
            self.motion_count += digit
        else:
            self.pending_count += digit

        return True

    def get_count(self, default: int = 1) -> int:
        """Get the current count value.

        Args:
            default: Default value if no count is set

        Returns:
            The numeric count or default
        """
        if self.pending_count:
            return int(self.pending_count)
        return default

    def get_motion_count(self, default: int = 1) -> int:
        """Get the motion count for operator-pending mode.

        Args:
            default: Default value if no count is set

        Returns:
            The motion count or default
        """
        if self.motion_count:
            return int(self.motion_count)
        return default

    def get_total_count(self, default: int = 1) -> int:
        """Get the total count (operator count * motion count).

        Args:
            default: Default value if no counts are set

        Returns:
            The product of operator and motion counts
        """
        op_count = int(self.operator_count) if self.operator_count else 1
        mot_count = int(self.motion_count) if self.motion_count else 1

        if self.operator_count or self.motion_count:
            return op_count * mot_count
        if self.pending_count:
            return int(self.pending_count)
        return default

    def enter_operator_pending(self) -> None:
        """Enter operator-pending mode, saving current count as operator count."""
        self.in_operator_pending = True
        self.operator_count = self.pending_count
        self.pending_count = ""
        self.motion_count = ""

    def exit_operator_pending(self) -> None:
        """Exit operator-pending mode."""
        self.in_operator_pending = False

    def reset(self) -> None:
        """Reset all counts and state."""
        self.pending_count = ""
        self.operator_count = ""
        self.motion_count = ""
        self.in_operator_pending = False

    def reset_counts_only(self) -> None:
        """Reset counts but preserve operator-pending state."""
        self.pending_count = ""
        self.motion_count = ""
        if not self.in_operator_pending:
            self.operator_count = ""

    def has_count(self) -> bool:
        """Check if any count is set.

        Returns:
            True if any count is present
        """
        return bool(self.pending_count or self.operator_count or self.motion_count)

    def get_state_string(self) -> str:
        """Get a string representation of current state.

        Returns:
            Human-readable state string for debugging/display
        """
        parts = []

        if self.pending_count:
            parts.append(f"count:{self.pending_count}")

        if self.operator_count:
            parts.append(f"op_count:{self.operator_count}")

        if self.motion_count:
            parts.append(f"motion_count:{self.motion_count}")

        if self.in_operator_pending:
            parts.append("operator_pending")

        return " ".join(parts) if parts else "no_count"


def parse_count_from_keys(keys: str) -> tuple[int, str]:
    """Parse a numeric count from the beginning of a key sequence.

    Args:
        keys: String of keys that may start with digits

    Returns:
        Tuple of (count, remaining_keys)
    """
    count_str = ""
    i = 0

    # Extract leading digits
    while i < len(keys) and keys[i].isdigit():
        # Skip leading zeros unless it's the only digit
        # If '0' is at the start and there are more keys, it might be a command
        if keys[i] == "0" and not count_str and i + 1 < len(keys):
            break
        count_str += keys[i]
        i += 1

    # Convert to count
    count = int(count_str) if count_str else 1
    remaining = keys[i:]

    return count, remaining


def apply_count_to_motion(motion_result: tuple[int, int], count: int) -> tuple[int, int]:
    """Apply a count to a motion result.

    Args:
        motion_result: (row, col) position after single motion
        count: Number of times to repeat the motion

    Returns:
        Final (row, col) position after applying count
    """
    # For most motions, we'd need to know the specific motion type
    # to correctly apply the count. This is a simplified version.
    row, col = motion_result

    # This would need motion-specific logic in a real implementation
    # For now, just return the result as-is
    return row, col


def format_count_display(count: int) -> str:
    """Format a count for display in status line or command display.

    Args:
        count: Numeric count value

    Returns:
        Formatted string for display
    """
    if count <= 1:
        return ""
    return str(count)
