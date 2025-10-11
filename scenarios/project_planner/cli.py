"""
Project Planner CLI implementation.

Provides commands for initializing, planning, and executing projects with AI coordination.
"""

import argparse
import sys
from pathlib import Path

from amplifier.core.context import create_project_context
from amplifier.core.context import detect_project_context
from amplifier.planner import Project
from amplifier.planner import Task
from amplifier.planner import save_project


def cmd_init(args) -> None:
    """Initialize a new project with planning."""
    project_root = Path(args.path) if args.path else Path.cwd()

    # Check if project already exists
    existing = detect_project_context(project_root)
    if existing:
        print(f"❌ Project already exists: {existing.project_name}")
        print(f"   Located at: {existing.config_file}")
        return

    # Create new project context
    context = create_project_context(project_name=args.name, project_root=project_root, enable_planning=True)

    print(f"✅ Created project: {context.project_name}")
    print(f"   Project ID: {context.project_id}")
    print(f"   Config: {context.config_file}")
    print(f"   Planning: {'Enabled' if context.has_planning else 'Disabled'}")


def cmd_plan(args) -> None:
    """Plan project tasks with AI decomposition."""
    context = detect_project_context()
    if not context:
        print("❌ No project found. Run 'init' first.")
        return

    if not context.has_planning:
        print("❌ Planning not enabled for this project.")
        print("   Enable with: --enable-planning")
        return

    # Create or load planner project
    if not context.planner_project:
        planner_project = Project(id=context.project_id, name=context.project_name)
    else:
        planner_project = context.planner_project

    if args.goals:
        print(f"🧠 Planning tasks for: {args.goals}")

        # Use smart decomposer for AI-driven task breakdown
        import asyncio

        from amplifier.planner.decomposer import ProjectContext
        from amplifier.planner.decomposer import decompose_goal

        # Create context for decomposition
        decomposer_context = ProjectContext(project=planner_project, max_depth=3, min_tasks=2)

        # Run async decomposition
        try:
            tasks = asyncio.run(decompose_goal(args.goals, decomposer_context))

            # Add tasks to project
            for task in tasks:
                planner_project.add_task(task)

            print(f"✅ Generated {len(tasks)} tasks using AI decomposition")

        except Exception as e:
            print(f"⚠️  AI decomposition failed, using simple task: {e}")
            # Fallback to simple task
            main_task = Task(id="main-goal", title=args.goals, description=f"Main project goal: {args.goals}")
            planner_project.add_task(main_task)

        # Save the project
        save_project(planner_project)
        context.planner_project = planner_project

        print(f"✅ Created planning structure with {len(planner_project.tasks)} tasks")
    else:
        print(f"📊 Current project status: {context.project_name}")
        if context.planner_project:
            print(f"   Tasks: {len(context.planner_project.tasks)}")
        else:
            print("   No planning data yet")


def cmd_status(args) -> None:
    """Show project status and progress."""
    context = detect_project_context()
    if not context:
        print("❌ No project found. Run 'init' first.")
        return

    print(f"📊 Project Status: {context.project_name}")
    print(f"   Project ID: {context.project_id}")
    print(f"   Root: {context.project_root}")
    print(f"   Planning: {'Enabled' if context.has_planning else 'Disabled'}")

    if context.has_planning and context.planner_project:
        project = context.planner_project
        print(f"   Tasks: {len(project.tasks)}")

        # Show task breakdown by state
        from collections import Counter

        states = Counter(task.state.value for task in project.tasks.values())
        for state, count in states.items():
            print(f"     {state}: {count}")

        # Show root tasks
        roots = project.get_roots()
        if roots:
            print("   Root tasks:")
            for root in roots[:5]:  # Show first 5
                print(f"     • {root.title}")
    else:
        print("   No planning data")


def cmd_execute(args) -> None:
    """Execute project tasks with agent coordination."""
    context = detect_project_context()
    if not context:
        print("❌ No project found. Run 'init' first.")
        return

    if not context.has_planning or not context.planner_project:
        print("❌ No planning data. Run 'plan' first.")
        return

    print(f"🚀 Executing project: {context.project_name}")

    # Use orchestrator for intelligent task execution
    import asyncio

    from amplifier.planner.orchestrator import orchestrate_execution

    project = context.planner_project

    # Run orchestrated execution
    try:
        results = asyncio.run(orchestrate_execution(project, max_parallel=args.max_parallel or 3))

        print("✅ Execution complete:")
        print(f"  • Total tasks: {results.total_tasks}")
        print(f"  • Completed: {results.completed_tasks}")
        print(f"  • Failed: {results.failed_tasks}")

        # Update project state
        save_project(project)

        return

    except Exception as e:
        print(f"⚠️  Orchestrated execution failed: {e}")

    # Fallback to simple execution
    completed = set()

    # Find tasks that can start
    startable = [t for t in project.tasks.values() if t.can_start(completed)]

    if startable:
        print(f"   Ready to start: {len(startable)} tasks")
        for task in startable[:3]:  # Show first 3
            print(f"     • {task.title}")
    else:
        print("   No tasks ready to start")


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(prog="project-planner", description="AI-driven multi-agent project orchestration")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize new project")
    init_parser.add_argument("--name", required=True, help="Project name")
    init_parser.add_argument("--path", help="Project root path (default: current directory)")
    init_parser.set_defaults(func=cmd_init)

    # Plan command
    plan_parser = subparsers.add_parser("plan", help="Plan project tasks")
    plan_parser.add_argument("--goals", help="Project goals to plan for")
    plan_parser.set_defaults(func=cmd_plan)

    # Status command
    status_parser = subparsers.add_parser("status", help="Show project status")
    status_parser.set_defaults(func=cmd_status)

    # Execute command
    execute_parser = subparsers.add_parser("execute", help="Execute project tasks")
    execute_parser.set_defaults(func=cmd_execute)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        args.func(args)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
