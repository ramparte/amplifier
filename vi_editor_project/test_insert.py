#!/usr/bin/env python3
"""Test runner for insert mode tests."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from editor import create_editor
from test_framework import TestRunner


def main():
    """Run insert mode tests."""
    test_dir = Path("tests/insert")

    if not test_dir.exists():
        print(f"Test directory not found: {test_dir}")
        return 1

    runner = TestRunner(test_dir)
    passed, failed = runner.run_tests(create_editor)

    print(f"\n{'=' * 50}")
    print(f"Insert Mode Test Results: {passed} passed, {failed} failed")
    print(f"{'=' * 50}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
