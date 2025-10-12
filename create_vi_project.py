#!/usr/bin/env python3
"""Create a super-planner project for rewriting vi in Python with TDD."""

import uuid

from amplifier.planner import Project
from amplifier.planner import Task
from amplifier.planner import TaskState
from amplifier.planner import save_project


def create_vi_rewrite_project():
    """Create a comprehensive project plan for vi rewrite with TDD."""

    # Create project
    project_id = str(uuid.uuid4())
    project = Project(id=project_id, name="Vi Editor Python Rewrite with TDD")

    # Track task IDs for dependencies
    task_ids = {}

    # Helper to create and add task
    def add_task(key, title, description, agent, depends_on=None, parent_key=None):
        task_id = f"{project_id}-{key}"
        parent_id = task_ids.get(parent_key) if parent_key else None

        task = Task(
            id=task_id,
            title=title,
            description=description,
            assigned_to=agent,
            parent_id=parent_id,
            depends_on=depends_on or [],
            state=TaskState.PENDING,
        )
        project.add_task(task)
        task_ids[key] = task_id
        return task_id

    # === Phase 1: Architecture & Test Framework ===

    add_task(
        "arch-design",
        "Design modular architecture for vi editor",
        """Design the overall architecture for the vi editor with clear module boundaries:
        - Buffer management module (line storage, cursor)
        - Mode management (command, insert, visual)
        - Command parser and executor
        - File I/O module
        - Display/rendering module
        - Configuration module

        Create architecture document with module interfaces and data flow.""",
        "zen-architect",
    )

    add_task(
        "test-framework",
        "Create file-based test framework",
        """Build a test framework that:
        - Reads input_file.txt, actions.txt, expected_output.txt
        - Executes actions against the editor
        - Compares output with expected using diff
        - Provides clear test reports
        - Supports both unit and integration tests

        Framework must be simple, reliable, and extensible.""",
        "test-coverage",
        depends_on=[task_ids["arch-design"]],
    )

    # === Phase 2: Core Buffer Tests & Implementation ===

    add_task(
        "buffer-tests",
        "Create comprehensive buffer management tests",
        """Create file-based tests for buffer management:
        - Test empty file handling
        - Test single/multi-line files
        - Test cursor movement boundaries
        - Test line insertion/deletion
        - Test large file handling (1000+ lines)
        - Test special characters and unicode

        Minimum 10 test cases with input/action/expected files.""",
        "test-coverage",
        depends_on=[task_ids["test-framework"]],
    )

    add_task(
        "buffer-impl",
        "Implement buffer management module",
        """Implement buffer.py module:
        - Line-based text storage
        - Cursor position tracking
        - Line insertion/deletion/modification
        - Efficient memory usage for large files
        - Boundary checking

        All tests from buffer-tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["buffer-tests"]],
    )

    # === Phase 3: Command Mode Tests & Implementation ===

    add_task(
        "nav-tests",
        "Create navigation command tests",
        """Create file-based tests for navigation:
        - h,j,k,l movement (left,down,up,right)
        - w,b word movement
        - 0,$ line start/end
        - gg,G file start/end
        - Numbered movements (5j, 10l, etc.)

        Test edge cases: empty lines, file boundaries, word boundaries.
        Minimum 15 test cases.""",
        "test-coverage",
        depends_on=[task_ids["buffer-impl"]],
    )

    add_task(
        "nav-impl",
        "Implement navigation commands",
        """Implement navigation in command_mode.py:
        - Parse movement commands
        - Execute cursor movements
        - Handle numeric prefixes
        - Respect file/line boundaries

        All navigation tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["nav-tests"]],
    )

    # === Phase 4: Insert Mode Tests & Implementation ===

    add_task(
        "insert-tests",
        "Create insert mode tests",
        """Create file-based tests for insert mode:
        - i,I insert at cursor/line start
        - a,A append after cursor/line end
        - o,O open line below/above
        - Text insertion and escape
        - Special key handling (backspace, enter)

        Test mode transitions and text insertion.
        Minimum 12 test cases.""",
        "test-coverage",
        depends_on=[task_ids["nav-impl"]],
    )

    add_task(
        "insert-impl",
        "Implement insert mode",
        """Implement insert_mode.py:
        - Mode transition handlers
        - Character insertion at cursor
        - Special key processing
        - Proper cursor positioning after mode change

        All insert mode tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["insert-tests"]],
    )

    # === Phase 5: Delete Operations Tests & Implementation ===

    add_task(
        "delete-tests",
        "Create delete operation tests",
        """Create file-based tests for deletions:
        - x delete character
        - dd delete line
        - dw delete word
        - d$ delete to line end
        - D delete to line end (alternate)
        - Numbered deletes (3dd, 5x)

        Test edge cases and buffer updates.
        Minimum 10 test cases.""",
        "test-coverage",
        depends_on=[task_ids["insert-impl"]],
    )

    add_task(
        "delete-impl",
        "Implement delete operations",
        """Implement delete operations in command_mode.py:
        - Character/word/line deletion
        - Delete with motion commands
        - Numeric repeat handling
        - Buffer cleanup after deletes

        All delete tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["delete-tests"]],
    )

    # === Phase 6: Copy/Paste Tests & Implementation ===

    add_task(
        "yank-tests",
        "Create yank and paste tests",
        """Create file-based tests for copy/paste:
        - yy yank line
        - yw yank word
        - p,P paste after/before
        - Yanking with counts (3yy)
        - Paste multiple times

        Test register storage and retrieval.
        Minimum 8 test cases.""",
        "test-coverage",
        depends_on=[task_ids["delete-impl"]],
    )

    add_task(
        "yank-impl",
        "Implement yank and paste",
        """Implement yank/paste in command_mode.py:
        - Yank operations to register
        - Paste from register
        - Register management
        - Line vs character yanks

        All yank/paste tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["yank-tests"]],
    )

    # === Phase 7: Visual Mode Tests & Implementation ===

    add_task(
        "visual-tests",
        "Create visual mode tests",
        """Create file-based tests for visual mode:
        - v character-wise selection
        - V line-wise selection
        - Selection with movement
        - Operations on selections (d, y)

        Test selection highlighting and operations.
        Minimum 8 test cases.""",
        "test-coverage",
        depends_on=[task_ids["yank-impl"]],
    )

    add_task(
        "visual-impl",
        "Implement visual mode",
        """Implement visual_mode.py:
        - Visual mode activation
        - Selection tracking
        - Movement in visual mode
        - Operations on selections

        All visual mode tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["visual-tests"]],
    )

    # === Phase 8: Undo/Redo Tests & Implementation ===

    add_task(
        "undo-tests",
        "Create undo/redo tests",
        """Create file-based tests for undo/redo:
        - u undo last change
        - Ctrl-r redo
        - Multiple undo levels
        - Undo after various operations

        Test state management and restoration.
        Minimum 6 test cases.""",
        "test-coverage",
        depends_on=[task_ids["visual-impl"]],
    )

    add_task(
        "undo-impl",
        "Implement undo/redo system",
        """Implement undo.py:
        - Command history stack
        - State snapshots
        - Undo/redo operations
        - Memory-efficient storage

        All undo/redo tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["undo-tests"]],
    )

    # === Phase 9: Search Tests & Implementation ===

    add_task(
        "search-tests",
        "Create search tests",
        """Create file-based tests for search:
        - / forward search
        - ? backward search
        - n,N next/previous match
        - Case sensitivity
        - Regex patterns

        Test wraparound and highlighting.
        Minimum 8 test cases.""",
        "test-coverage",
        depends_on=[task_ids["undo-impl"]],
    )

    add_task(
        "search-impl",
        "Implement search functionality",
        """Implement search.py:
        - Pattern search forward/backward
        - Match highlighting
        - Next/previous navigation
        - Basic regex support

        All search tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["search-tests"]],
    )

    # === Phase 10: Replace Tests & Implementation ===

    add_task(
        "replace-tests",
        "Create replace command tests",
        """Create file-based tests for replace:
        - :s/old/new/ single replace
        - :s/old/new/g global replace
        - :%s/old/new/g file-wide replace
        - Regex patterns in replace

        Test various replace scenarios.
        Minimum 6 test cases.""",
        "test-coverage",
        depends_on=[task_ids["search-impl"]],
    )

    add_task(
        "replace-impl",
        "Implement replace commands",
        """Implement replace in ex_commands.py:
        - Parse :s commands
        - Pattern matching and replacement
        - Flags (g, i, c)
        - Range support

        All replace tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["replace-tests"]],
    )

    # === Phase 11: File I/O Tests & Implementation ===

    add_task(
        "file-tests",
        "Create file I/O tests",
        """Create file-based tests for file operations:
        - :w write file
        - :q quit
        - :wq write and quit
        - :q! force quit
        - :e open file
        - Handle permissions and errors

        Test file creation, modification, saving.
        Minimum 8 test cases.""",
        "test-coverage",
        depends_on=[task_ids["replace-impl"]],
    )

    add_task(
        "file-impl",
        "Implement file I/O operations",
        """Implement file_io.py:
        - Read files into buffer
        - Write buffer to file
        - Handle encodings
        - Permission and error handling
        - Backup creation

        All file I/O tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["file-tests"]],
    )

    # === Phase 12: Display & UI Tests & Implementation ===

    add_task(
        "display-tests",
        "Create display and UI tests",
        """Create tests for display features:
        - Line numbers display
        - Status bar (mode, file, position)
        - Command line display
        - Screen refresh and scrolling

        Test terminal output formatting.
        Minimum 5 test cases.""",
        "test-coverage",
        depends_on=[task_ids["file-impl"]],
    )

    add_task(
        "display-impl",
        "Implement display and UI",
        """Implement display.py:
        - Terminal control (curses or similar)
        - Screen rendering
        - Status bar updates
        - Line number display
        - Efficient screen updates

        All display tests must pass.""",
        "modular-builder",
        depends_on=[task_ids["display-tests"]],
    )

    # === Phase 13: Integration & CLI ===

    add_task(
        "integration-tests",
        "Create comprehensive integration tests",
        """Create end-to-end integration tests:
        - Complete editing sessions
        - Multiple mode transitions
        - Complex command sequences
        - Edge cases and error handling
        - Performance with large files

        Minimum 15 integration test scenarios.""",
        "test-coverage",
        depends_on=[task_ids["display-impl"]],
    )

    add_task(
        "cli-impl",
        "Implement CLI interface",
        """Implement main.py CLI:
        - Command-line argument parsing
        - Editor initialization
        - Main event loop
        - Signal handling (Ctrl-C, etc.)
        - Graceful shutdown

        Create executable vi.py script.""",
        "integration-specialist",
        depends_on=[task_ids["integration-tests"]],
    )

    add_task(
        "integration-verify",
        "Verify all integration tests pass",
        """Run all integration tests:
        - Execute full test suite
        - Verify 100% pass rate
        - Document any limitations
        - Performance benchmarks

        Ensure editor is production-ready.""",
        "test-coverage",
        depends_on=[task_ids["cli-impl"]],
    )

    # === Phase 14: Documentation & Polish ===

    add_task(
        "docs",
        "Create user and developer documentation",
        """Create comprehensive documentation:
        - User manual with command reference
        - Developer guide with architecture
        - Test writing guide
        - Installation instructions
        - Known limitations

        Documentation in markdown format.""",
        "zen-architect",
        depends_on=[task_ids["integration-verify"]],
    )

    add_task(
        "polish",
        "Final polish and optimization",
        """Final improvements:
        - Code cleanup and refactoring
        - Performance optimizations
        - Error message improvements
        - Edge case handling
        - Code review and quality checks

        Ensure professional quality.""",
        "refactor-architect",
        depends_on=[task_ids["docs"]],
    )

    # Save the project
    save_project(project)

    return project_id, project


if __name__ == "__main__":
    project_id, project = create_vi_rewrite_project()

    print(f"Created project: {project_id}")
    print(f"Project: {project.name}\n")

    # Display project statistics
    total_tasks = len(project.tasks)
    by_agent = {}
    for task in project.tasks.values():
        agent = task.assigned_to
        by_agent[agent] = by_agent.get(agent, 0) + 1

    print(f"Total tasks: {total_tasks}")
    print("\nTasks by agent:")
    for agent, count in sorted(by_agent.items(), key=lambda x: -x[1]):
        print(f"  • {agent}: {count} tasks")

    # Show initial ready tasks
    completed_ids = set()
    ready_tasks = [t for t in project.tasks.values() if t.state == TaskState.PENDING and t.can_start(completed_ids)]

    print(f"\nReady to execute: {len(ready_tasks)} task(s)")
    for task in ready_tasks:
        print(f"  → {task.title} ({task.assigned_to})")
