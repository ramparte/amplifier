#!/usr/bin/env python3
"""Demo script showing how to launch the vi editor."""

import os
import sys

# Add amplifier to path if running from vi directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def main():
    """Demo the vi editor."""
    print("VI Editor Demo")
    print("=" * 50)
    print()
    print("The vi editor is now ready to launch!")
    print()
    print("Launch methods:")
    print("-" * 50)
    print()
    print("1. As a Python module:")
    print("   python3 -m amplifier.vi [filename]")
    print()
    print("2. With command-line options:")
    print("   python3 -m amplifier.vi -R file.txt  # Read-only")
    print("   python3 -m amplifier.vi file.txt +10  # Jump to line 10")
    print("   python3 -m amplifier.vi file.txt +/pattern  # Search for pattern")
    print()
    print("3. From Python code:")
    print("   from amplifier.vi.main import main")
    print("   main()")
    print()
    print("Key features implemented:")
    print("-" * 50)
    print("✓ Command-line argument parsing")
    print("✓ File loading and saving")
    print("✓ Terminal raw mode with proper restoration")
    print("✓ Full screen rendering with status line")
    print("✓ Normal, Insert, Visual, Command modes")
    print("✓ Movement commands (hjkl, w, b, e, $, 0, G, gg)")
    print("✓ Editing commands (i, a, o, O, d, c, y, p)")
    print("✓ Ex commands (:w, :q, :wq, :e)")
    print("✓ Search (/, ?, n, N)")
    print("✓ Visual selection and operations")
    print("✓ Macro recording and playback")
    print("✓ Marks and jumps")
    print("✓ Text objects and operators")
    print()
    print("Signal handling:")
    print("-" * 50)
    print("✓ Ctrl-C returns to normal mode")
    print("✓ Ctrl-Z suspends the editor")
    print("✓ Terminal resize handled (SIGWINCH)")
    print()
    print("Would you like to launch the editor now? (y/n): ", end="", flush=True)

    response = input().strip().lower()
    if response == "y":
        print("\nLaunching vi editor...")
        print("Press :q to quit, :w to save, :wq to save and quit")
        print("Press any key to continue...", end="", flush=True)
        input()

        # Launch the editor
        from amplifier.vi.main import main as vi_main

        vi_main()
    else:
        print("\nTo launch later, use: python3 -m amplifier.vi")


if __name__ == "__main__":
    main()
