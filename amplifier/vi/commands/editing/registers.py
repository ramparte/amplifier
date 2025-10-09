"""Register management system for vi editor.

Provides support for named registers (a-z, A-Z), numbered registers (0-9),
and special registers (", *, +, etc.).
"""

from dataclasses import dataclass
from dataclasses import field
from enum import Enum


class RegisterType(Enum):
    """Types of vi registers."""

    UNNAMED = '"'  # Default register
    NUMBERED = "0-9"  # Numbered registers for recent deletions/yanks
    NAMED_LOWER = "a-z"  # Named registers (lowercase)
    NAMED_UPPER = "A-Z"  # Named registers (uppercase - append)
    CLIPBOARD_PRIMARY = "*"  # System clipboard (primary selection)
    CLIPBOARD_SYSTEM = "+"  # System clipboard
    BLACK_HOLE = "_"  # Black hole register (discards content)
    LAST_SEARCH = "/"  # Last search pattern
    LAST_COMMAND = ":"  # Last command-line command
    LAST_INSERTED = "."  # Last inserted text
    FILENAME = "%"  # Current filename
    EXPRESSION = "="  # Expression register


@dataclass
class RegisterContent:
    """Content stored in a register."""

    text: str
    is_linewise: bool = False  # True for line-based operations (dd, yy)
    is_blockwise: bool = False  # True for visual block operations


@dataclass
class RegisterState:
    """State of all registers in the system."""

    unnamed: RegisterContent | None = None
    named: dict[str, RegisterContent] = field(default_factory=dict)
    numbered: list[RegisterContent | None] = field(default_factory=lambda: [None] * 10)
    clipboard_primary: RegisterContent | None = None
    clipboard_system: RegisterContent | None = None
    last_search: str = ""
    last_command: str = ""
    last_inserted: str = ""
    filename: str = ""
    black_hole_count: int = 0  # Track black hole usage for testing


class RegisterManager:
    """Manages all vi registers."""

    def __init__(self):
        """Initialize the register manager."""
        self.state = RegisterState()
        self._system_clipboard: str | None = None  # Mock system clipboard

    def get(self, register: str | None = None) -> RegisterContent | None:
        """Get content from a register.

        Args:
            register: Register name (None for unnamed register)

        Returns:
            Register content or None if empty
        """
        if register is None or register == '"':
            return self.state.unnamed

        # Named registers (a-z, A-Z)
        if len(register) == 1 and register.isalpha():
            lower_reg = register.lower()
            return self.state.named.get(lower_reg)

        # Numbered registers (0-9)
        if register.isdigit():
            idx = int(register)
            if 0 <= idx <= 9:
                return self.state.numbered[idx]

        # Special registers
        if register == "*":
            return self.state.clipboard_primary
        if register == "+":
            return self.state.clipboard_system
        if register == "_":
            return None  # Black hole always returns None
        if register == "/":
            return RegisterContent(self.state.last_search) if self.state.last_search else None
        if register == ":":
            return RegisterContent(self.state.last_command) if self.state.last_command else None
        if register == ".":
            return RegisterContent(self.state.last_inserted) if self.state.last_inserted else None
        if register == "%":
            return RegisterContent(self.state.filename) if self.state.filename else None

        return None

    def set(
        self,
        register: str | None,
        content: str,
        is_linewise: bool = False,
        is_blockwise: bool = False,
        is_delete: bool = False,
    ) -> None:
        """Set content in a register.

        Args:
            register: Register name (None for unnamed register)
            content: Text to store
            is_linewise: Whether operation was line-based
            is_blockwise: Whether operation was visual block
            is_delete: Whether this is from a delete operation
        """
        reg_content = RegisterContent(content, is_linewise, is_blockwise)

        # Handle unnamed register
        if register is None or register == '"':
            self.state.unnamed = reg_content
            # Also update numbered registers
            self._update_numbered_registers(reg_content, is_delete)
            return

        # Named registers (a-z: replace, A-Z: append)
        if len(register) == 1 and register.isalpha():
            if register.islower():
                # Replace content
                self.state.named[register] = reg_content
            else:
                # Append to lowercase version
                lower_reg = register.lower()
                if lower_reg in self.state.named:
                    existing = self.state.named[lower_reg]
                    # Append with appropriate separator
                    if existing.is_linewise and is_linewise:
                        combined_text = existing.text + content
                    else:
                        combined_text = existing.text + "\n" + content if existing.text else content
                    self.state.named[lower_reg] = RegisterContent(
                        combined_text, existing.is_linewise and is_linewise, False
                    )
                else:
                    self.state.named[lower_reg] = reg_content

            # Also update unnamed register
            self.state.unnamed = reg_content
            return

        # Numbered register (0 for yank)
        if register == "0" and not is_delete:
            self.state.numbered[0] = reg_content
            self.state.unnamed = reg_content
            return

        # Special registers
        if register == "*":
            self.state.clipboard_primary = reg_content
            self._system_clipboard = content  # Mock system clipboard
            return
        if register == "+":
            self.state.clipboard_system = reg_content
            self._system_clipboard = content  # Mock system clipboard
            return
        if register == "_":
            # Black hole - discard content
            self.state.black_hole_count += 1
            return
        if register == "/":
            self.state.last_search = content
            return
        if register == ":":
            self.state.last_command = content
            return
        if register == ".":
            self.state.last_inserted = content
            return
        if register == "%":
            self.state.filename = content
            return

    def _update_numbered_registers(self, content: RegisterContent, is_delete: bool) -> None:
        """Update numbered registers for yank/delete operations.

        Register 0: Contains text from most recent yank
        Registers 1-9: Contains text from recent delete/change operations
        """
        if is_delete:
            # Shift registers 1-8 down to 2-9
            for i in range(8, 0, -1):
                self.state.numbered[i] = self.state.numbered[i - 1]
            # Put new deletion in register 1
            self.state.numbered[1] = content
        else:
            # Yank - only update register 0
            self.state.numbered[0] = content

    def clear(self, register: str | None = None) -> None:
        """Clear a register or all registers.

        Args:
            register: Specific register to clear, or None for all
        """
        if register is None:
            # Clear all registers
            self.state = RegisterState()
            self._system_clipboard = None
        elif register == '"':
            self.state.unnamed = None
        elif len(register) == 1 and register.isalpha():
            lower_reg = register.lower()
            self.state.named.pop(lower_reg, None)
        elif register.isdigit():
            idx = int(register)
            if 0 <= idx <= 9:
                self.state.numbered[idx] = None
        elif register == "*":
            self.state.clipboard_primary = None
        elif register == "+":
            self.state.clipboard_system = None
        elif register == "/":
            self.state.last_search = ""
        elif register == ":":
            self.state.last_command = ""
        elif register == ".":
            self.state.last_inserted = ""
        elif register == "%":
            self.state.filename = ""

    def get_register_list(self) -> dict[str, str]:
        """Get a list of all non-empty registers for display.

        Returns:
            Dictionary mapping register names to their content (truncated)
        """
        result = {}

        # Unnamed register
        if self.state.unnamed:
            content = self.state.unnamed.text[:50]
            if len(self.state.unnamed.text) > 50:
                content += "..."
            result['"'] = content

        # Named registers
        for name, reg_content in sorted(self.state.named.items()):
            if reg_content and reg_content.text:
                content = reg_content.text[:50]
                if len(reg_content.text) > 50:
                    content += "..."
                result[name] = content

        # Numbered registers
        for i, reg_content in enumerate(self.state.numbered):
            if reg_content and reg_content.text:
                content = reg_content.text[:50]
                if len(reg_content.text) > 50:
                    content += "..."
                result[str(i)] = content

        # Special registers
        if self.state.clipboard_primary:
            content = self.state.clipboard_primary.text[:50]
            if len(self.state.clipboard_primary.text) > 50:
                content += "..."
            result["*"] = content

        if self.state.clipboard_system:
            content = self.state.clipboard_system.text[:50]
            if len(self.state.clipboard_system.text) > 50:
                content += "..."
            result["+"] = content

        return result

    def get_system_clipboard(self) -> str | None:
        """Get mock system clipboard content (for testing)."""
        return self._system_clipboard

    def set_system_clipboard(self, content: str) -> None:
        """Set mock system clipboard content (for testing)."""
        self._system_clipboard = content
        self.state.clipboard_system = RegisterContent(content)
        self.state.clipboard_primary = RegisterContent(content)
