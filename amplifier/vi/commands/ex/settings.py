"""Settings management for ex mode."""

from dataclasses import dataclass
from dataclasses import field

from .parser import ExCommand


@dataclass
class EditorSettings:
    """Container for all editor settings."""

    # Display settings
    number: bool = False  # Show line numbers
    relativenumber: bool = False  # Show relative line numbers
    ruler: bool = True  # Show cursor position
    showcmd: bool = True  # Show partial commands
    showmode: bool = True  # Show current mode
    wrap: bool = True  # Wrap long lines
    list: bool = False  # Show invisible characters

    # Search settings
    ignorecase: bool = False  # Case insensitive search
    smartcase: bool = False  # Smart case (override ignorecase if pattern has uppercase)
    hlsearch: bool = False  # Highlight search results
    incsearch: bool = True  # Incremental search
    wrapscan: bool = True  # Wrap search around file

    # Indentation settings
    tabstop: int = 8  # Width of tab character
    softtabstop: int = 0  # Soft tab stop
    shiftwidth: int = 8  # Width for autoindent
    expandtab: bool = False  # Use spaces instead of tabs
    autoindent: bool = False  # Copy indent from current line
    smartindent: bool = False  # Smart autoindenting

    # File settings
    backup: bool = True  # Create backup files
    writebackup: bool = True  # Make backup before overwriting
    swapfile: bool = True  # Use swap files
    autowrite: bool = False  # Auto write before commands
    autoread: bool = False  # Auto read when file changes

    # Edit settings
    backspace: str = "indent,eol,start"  # Backspace behavior
    scrolloff: int = 0  # Lines to keep above/below cursor
    sidescrolloff: int = 0  # Columns to keep left/right of cursor

    # Misc settings
    history: int = 50  # Command history size
    report: int = 2  # Report changes affecting N+ lines
    laststatus: int = 1  # Status line display (0=never, 1=if split, 2=always)

    # Custom settings dictionary for extensions
    custom: dict = field(default_factory=dict)


class ExSettings:
    """Handle :set commands for editor settings."""

    def __init__(self):
        """Initialize settings manager."""
        self.settings = EditorSettings()

        # Map of setting names to their types for validation
        self.setting_types = {
            # Boolean settings
            "number": bool,
            "nu": bool,  # Alias for number
            "relativenumber": bool,
            "rnu": bool,  # Alias for relativenumber
            "ignorecase": bool,
            "ic": bool,  # Alias for ignorecase
            "smartcase": bool,
            "scs": bool,  # Alias for smartcase
            "hlsearch": bool,
            "hls": bool,  # Alias for hlsearch
            "incsearch": bool,
            "is": bool,  # Alias for incsearch
            "expandtab": bool,
            "et": bool,  # Alias for expandtab
            "autoindent": bool,
            "ai": bool,  # Alias for autoindent
            "smartindent": bool,
            "si": bool,  # Alias for smartindent
            "wrap": bool,
            "list": bool,
            "ruler": bool,
            "showcmd": bool,
            "showmode": bool,
            "backup": bool,
            "writebackup": bool,
            "swapfile": bool,
            "autowrite": bool,
            "autoread": bool,
            "wrapscan": bool,
            "ws": bool,  # Alias for wrapscan
            # Integer settings
            "tabstop": int,
            "ts": int,  # Alias for tabstop
            "softtabstop": int,
            "sts": int,  # Alias for softtabstop
            "shiftwidth": int,
            "sw": int,  # Alias for shiftwidth
            "scrolloff": int,
            "so": int,  # Alias for scrolloff
            "sidescrolloff": int,
            "siso": int,  # Alias for sidescrolloff
            "history": int,
            "report": int,
            "laststatus": int,
            "ls": int,  # Alias for laststatus
            # String settings
            "backspace": str,
            "bs": str,  # Alias for backspace
        }

        # Map aliases to canonical names
        self.aliases = {
            "nu": "number",
            "rnu": "relativenumber",
            "ic": "ignorecase",
            "scs": "smartcase",
            "hls": "hlsearch",
            "is": "incsearch",
            "et": "expandtab",
            "ai": "autoindent",
            "si": "smartindent",
            "ws": "wrapscan",
            "ts": "tabstop",
            "sts": "softtabstop",
            "sw": "shiftwidth",
            "so": "scrolloff",
            "siso": "sidescrolloff",
            "ls": "laststatus",
            "bs": "backspace",
        }

    def execute(self, command: ExCommand) -> tuple[bool, str]:
        """Execute a :set command.

        Args:
            command: Parsed ex command

        Returns:
            Tuple of (success, message)
        """
        if not command.args:
            # :set with no args shows all modified settings
            return self._show_modified_settings()

        # Parse setting arguments
        args = command.args.strip()

        # Handle queries (:set setting?)
        if args.endswith("?"):
            setting_name = args[:-1].strip()
            return self._query_setting(setting_name)

        # Handle toggles (:set invSetting or :set setting!)
        if args.startswith("inv"):
            setting_name = args[3:]
            return self._toggle_setting(setting_name)
        if args.endswith("!"):
            setting_name = args[:-1]
            return self._toggle_setting(setting_name)

        # Handle no/no prefix (:set nosetting)
        if args.startswith("no"):
            setting_name = args[2:]
            return self._set_boolean(setting_name, False)

        # Handle multiple settings separated by space BEFORE checking for assignment
        # (because "number tabstop=4" contains both space and =)
        if " " in args:
            results = []
            for arg in args.split():
                success, msg = self.execute(ExCommand(command="set", args=arg))
                if not success:
                    return (False, msg)
                if msg:  # Only append non-empty messages
                    results.append(msg)
            return (True, "; ".join(results) if results else "")

        # Handle assignment (:set setting=value)
        if "=" in args:
            setting_name, value = args.split("=", 1)
            return self._set_value(setting_name.strip(), value.strip())

        # Default: set boolean to true
        return self._set_boolean(args, True)

    def _show_modified_settings(self) -> tuple[bool, str]:
        """Show all settings that differ from defaults.

        Returns:
            Tuple of (success, message)
        """
        defaults = EditorSettings()
        modified = []

        for attr in dir(self.settings):
            if attr.startswith("_") or attr == "custom":
                continue
            current_value = getattr(self.settings, attr, None)
            default_value = getattr(defaults, attr, None)
            if current_value != default_value:
                if isinstance(current_value, bool):
                    if current_value:
                        modified.append(f"  {attr}")
                    else:
                        modified.append(f"no{attr}")
                else:
                    modified.append(f"  {attr}={current_value}")

        if modified:
            return (True, "\n".join(modified))
        return (True, "All settings at default values")

    def _query_setting(self, setting_name: str) -> tuple[bool, str]:
        """Query a specific setting value.

        Args:
            setting_name: Name of setting to query

        Returns:
            Tuple of (success, message)
        """
        # Resolve alias
        canonical_name = self.aliases.get(setting_name, setting_name)

        if not hasattr(self.settings, canonical_name):
            return (False, f"Unknown option: {setting_name}")

        value = getattr(self.settings, canonical_name)
        if isinstance(value, bool):
            if value:
                return (True, f"  {canonical_name}")
            return (True, f"no{canonical_name}")
        return (True, f"  {canonical_name}={value}")

    def _toggle_setting(self, setting_name: str) -> tuple[bool, str]:
        """Toggle a boolean setting.

        Args:
            setting_name: Name of setting to toggle

        Returns:
            Tuple of (success, message)
        """
        canonical_name = self.aliases.get(setting_name, setting_name)

        if not hasattr(self.settings, canonical_name):
            return (False, f"Unknown option: {setting_name}")

        current_value = getattr(self.settings, canonical_name)
        if not isinstance(current_value, bool):
            return (False, f"Cannot toggle non-boolean option: {setting_name}")

        setattr(self.settings, canonical_name, not current_value)
        return (True, "")

    def _set_boolean(self, setting_name: str, value: bool) -> tuple[bool, str]:
        """Set a boolean setting.

        Args:
            setting_name: Name of setting
            value: Boolean value to set

        Returns:
            Tuple of (success, message)
        """
        canonical_name = self.aliases.get(setting_name, setting_name)

        if not hasattr(self.settings, canonical_name):
            return (False, f"Unknown option: {setting_name}")

        if canonical_name in self.setting_types and self.setting_types[canonical_name] is not bool:
            return (False, f"Not a boolean option: {setting_name}")

        setattr(self.settings, canonical_name, value)
        return (True, "")

    def _set_value(self, setting_name: str, value_str: str) -> tuple[bool, str]:
        """Set a setting to a specific value.

        Args:
            setting_name: Name of setting
            value_str: String representation of value

        Returns:
            Tuple of (success, message)
        """
        canonical_name = self.aliases.get(setting_name, setting_name)

        if not hasattr(self.settings, canonical_name):
            # Allow custom settings
            self.settings.custom[setting_name] = value_str
            return (True, "")

        # Get expected type
        setting_type = self.setting_types.get(canonical_name, str)

        # Convert value
        try:
            if setting_type is bool:
                value = value_str.lower() in ("1", "true", "yes", "on")
            elif setting_type is int:
                value = int(value_str)
            else:
                value = value_str
        except ValueError:
            return (False, f"Invalid value for {setting_name}: {value_str}")

        setattr(self.settings, canonical_name, value)
        return (True, "")

    def get(self, setting_name: str):
        """Get a setting value.

        Args:
            setting_name: Name of setting

        Returns:
            Setting value or None if not found
        """
        canonical_name = self.aliases.get(setting_name, setting_name)

        # Check standard settings
        if hasattr(self.settings, canonical_name):
            return getattr(self.settings, canonical_name)

        # Check custom settings
        return self.settings.custom.get(setting_name)

    def reset_to_defaults(self) -> None:
        """Reset all settings to default values."""
        self.settings = EditorSettings()
