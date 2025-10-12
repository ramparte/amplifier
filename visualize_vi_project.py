#!/usr/bin/env python3
"""Visualize the vi rewrite project structure."""

from amplifier.planner import TaskState
from amplifier.planner import load_project


def visualize_project(project_id):
    """Display project structure with hierarchy and dependencies."""

    project = load_project(project_id)

    print(f"Project: {project.name}")
    print(f"ID: {project.id}")
    print("=" * 80)

    # Calculate statistics
    total = len(project.tasks)
    completed_ids = {tid for tid, t in project.tasks.items() if t.state == TaskState.COMPLETED}
    completed = len(completed_ids)
    ready_tasks = [t for t in project.tasks.values() if t.state == TaskState.PENDING and t.can_start(completed_ids)]

    print(f"\nProgress: {completed}/{total} tasks completed ({completed / total * 100:.1f}%)")
    print(f"Ready tasks: {len(ready_tasks)}")
    print()

    # Display task tree with phases
    print("Task Hierarchy:")
    print("-" * 80)

    # Group tasks by phase based on their keys
    phases = {
        "Phase 1: Architecture & Test Framework": ["arch-design", "test-framework"],
        "Phase 2: Core Buffer": ["buffer-tests", "buffer-impl"],
        "Phase 3: Command Mode": ["nav-tests", "nav-impl"],
        "Phase 4: Insert Mode": ["insert-tests", "insert-impl"],
        "Phase 5: Delete Operations": ["delete-tests", "delete-impl"],
        "Phase 6: Copy/Paste": ["yank-tests", "yank-impl"],
        "Phase 7: Visual Mode": ["visual-tests", "visual-impl"],
        "Phase 8: Undo/Redo": ["undo-tests", "undo-impl"],
        "Phase 9: Search": ["search-tests", "search-impl"],
        "Phase 10: Replace": ["replace-tests", "replace-impl"],
        "Phase 11: File I/O": ["file-tests", "file-impl"],
        "Phase 12: Display & UI": ["display-tests", "display-impl"],
        "Phase 13: Integration": ["integration-tests", "cli-impl", "integration-verify"],
        "Phase 14: Documentation & Polish": ["docs", "polish"],
    }

    for phase_name, task_keys in phases.items():
        print(f"\n{phase_name}:")

        for key in task_keys:
            task_id = f"{project.id}-{key}"
            if task_id in project.tasks:
                task = project.tasks[task_id]

                # Determine status icon
                if task.state == TaskState.COMPLETED:
                    icon = "✓"
                elif task.state == TaskState.IN_PROGRESS:
                    icon = "→"
                elif task.state == TaskState.BLOCKED:
                    icon = "⏸"
                elif task.can_start(completed_ids):
                    icon = "●"
                else:
                    icon = "○"

                # Show dependencies
                deps = []
                if task.depends_on:
                    for dep_id in task.depends_on:
                        if dep_id in project.tasks:
                            dep_key = dep_id.split("-", 1)[1] if "-" in dep_id else dep_id
                            deps.append(dep_key)

                dep_str = f" [depends on: {', '.join(deps)}]" if deps else ""

                print(f"  {icon} {task.title} ({task.assigned_to}){dep_str}")

    # Show execution order
    print("\n" + "=" * 80)
    print("Execution Order (respecting dependencies):")
    print("-" * 80)

    # Build dependency graph
    executed = set()
    execution_order = []

    while len(executed) < len(project.tasks):
        # Find tasks that can be executed
        can_execute = []
        for task_id, task in project.tasks.items():
            if task_id not in executed and all(dep_id in executed for dep_id in task.depends_on):
                can_execute.append(task)

        if not can_execute:
            print("ERROR: Circular dependency or missing tasks!")
            break

        # Sort by phase for better grouping
        can_execute.sort(key=lambda t: t.id)

        # Add to execution order
        for task in can_execute:
            execution_order.append(task)
            executed.add(task.id)

    # Display execution order grouped by parallel batches
    batch_num = 1
    executed = set()

    while len(executed) < len(project.tasks):
        # Find tasks that can be executed in parallel
        batch = []
        for task_id, task in project.tasks.items():
            if task_id not in executed and all(dep_id in executed for dep_id in task.depends_on):
                batch.append(task)

        if not batch:
            break

        print(f"\nBatch {batch_num} (can run in parallel):")
        for task in batch:
            key = task.id.split("-", 1)[1] if "-" in task.id else task.id
            print(f"  • {task.title} ({task.assigned_to})")
            executed.add(task.id)

        batch_num += 1

    print("\n" + "=" * 80)
    print(f"Total batches: {batch_num - 1}")
    print(
        f"Maximum parallelism: {max([len([t for t in project.tasks.values() if all(d in executed_at_batch for d in t.depends_on)]) for executed_at_batch in [set()] + [executed.copy() for _ in range(batch_num - 1)]], default=1)}"
    )


if __name__ == "__main__":
    project_id = "9d16c244-42ba-4ce9-91bc-cb928c869e75"
    visualize_project(project_id)
