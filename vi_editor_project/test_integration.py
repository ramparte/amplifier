#!/usr/bin/env python3
"""
Comprehensive integration tests for vi editor.

These tests verify complete editing workflows including:
- Complex command sequences across multiple modes
- File operations (open, edit, save, quit)
- Multi-step editing scenarios
- Error handling and edge cases
- Performance with large files
"""

from pathlib import Path

from editor import create_editor
from test_framework import TestRunner


def main():
    """Run all integration tests."""
    test_root = Path(__file__).parent / "tests" / "integration"

    if not test_root.exists():
        print(f"Integration test directory not found: {test_root}")
        print("Creating test directory...")
        test_root.mkdir(parents=True, exist_ok=True)

    runner = TestRunner(test_root)
    passed, failed = runner.run_tests(create_editor, verbose=True)

    # Exit with error code if any tests failed
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
