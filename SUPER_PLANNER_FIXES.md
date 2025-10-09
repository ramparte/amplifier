# Super-Planner Design Fixes Required

**Date:** 2025-10-09
**Context:** Vi editor project revealed critical gaps in super-planner's ability to track and resume work

## Root Cause Analysis

### Problem: Lost State Across Sessions
When resuming work on the vi editor, I encountered:
1. **Multiple conflicting tracking systems** (3 different JSON files, 1 markdown plan)
2. **No single source of truth** for completion status
3. **Disconnected implementation from tracking** - files were created but tracking wasn't updated
4. **Manual audit required** to determine what was actually complete

### What Happened
- All phases 1-7 were implemented (100% of required files exist)
- Only Phase 8 was marked complete in vi_completion_project.json
- Super-planner data in `ai_working/vi_implementor/` showed all tasks as "pending"
- No way to know what was done without manually auditing codebase

---

## Required Super-Planner Improvements

### 1. Single Source of Truth Architecture

**Current Problem:**
```
vi_completion_plan.md          # Static plan
vi_completion_project.json     # Tracking (outdated)
ai_working/vi_implementor/...  # Different tracking (outdated)
```

**Solution:**
```json
{
  "super_planner_version": "2.0",
  "project_id": "vi_editor",
  "authoritative_state_file": "THIS_FILE",
  "last_updated": "2025-10-09T08:00:00Z",
  "updated_by": "agent_id_or_human",

  "phases": [...],

  "metadata": {
    "plan_file": "vi_completion_plan.md",
    "git_branch": "vi-rewrite-1",
    "last_commit": "a4bbcec",
    "state_sync": "automatic"
  }
}
```

**Design Principle:** ONE JSON file is the authoritative state. All other files reference it.

---

### 2. File-to-Task Mapping

**Current Problem:** No way to know if a task is complete by looking at files.

**Solution:** Track deliverables explicitly and check file existence:

```json
{
  "task_id": "1.1",
  "name": "File Loading Module",
  "deliverables": [
    {
      "path": "amplifier/vi/file_io/loader.py",
      "type": "implementation",
      "exists": true,
      "last_modified": "2025-10-08T17:21:00Z",
      "size_bytes": 6268,
      "checksum": "sha256:..."
    },
    {
      "path": "amplifier/vi/file_io/test_loader.py",
      "type": "test",
      "exists": true,
      "tests_passing": null
    }
  ],
  "completion_criteria": {
    "all_deliverables_exist": true,
    "tests_passing": false,
    "manually_verified": false
  },
  "state": "auto_detected_complete"
}
```

**Implementation:**
- Add `check_deliverables()` function that scans filesystem
- Update task state automatically based on file existence
- Track file checksums to detect changes

---

### 3. Automated State Synchronization

**Current Problem:** Manual updates required. Easy to forget.

**Solution:** Git hook + file watcher pattern:

```python
# .git/hooks/post-commit (or pre-commit)
def sync_super_planner_state():
    """Auto-sync super-planner state after git operations."""

    # 1. Get list of modified files from commit
    changed_files = git.get_changed_files()

    # 2. Find tasks that list these files as deliverables
    affected_tasks = find_tasks_by_files(changed_files)

    # 3. Update task states
    for task in affected_tasks:
        if all_deliverables_exist(task):
            task.state = "complete"
            task.completed_at = now()

    # 4. Save state
    save_project_state()
```

**Alternative:** Agent explicitly calls `sync_state()` after completing work.

---

### 4. Test-Task Integration

**Current Problem:** Tests exist but not linked to tasks. Can't tell if task is "done done."

**Solution:** Embed test requirements in task definition:

```json
{
  "task_id": "1.1",
  "name": "File Loading Module",
  "deliverables": [...],
  "tests": {
    "unit_tests": {
      "path": "tests/vi/file_io/test_loader.py",
      "test_count": 12,
      "passing": 12,
      "failing": 0,
      "last_run": "2025-10-09T08:00:00Z"
    },
    "integration_tests": {
      "path": "tests/vi_functional/scenarios/test_file_operations.vicmd",
      "passing": true
    }
  },
  "completion_criteria": {
    "files_exist": true,
    "unit_tests_pass": true,
    "integration_tests_pass": true
  },
  "state": "verified_complete"
}
```

**Implementation:**
- `run_task_tests(task_id)` runs all tests for a task
- Updates test results in project state
- State transitions: pending → files_created → tests_passing → verified_complete

---

### 5. Resumption Context Generation

**Current Problem:** Agent must manually audit to understand state.

**Solution:** Auto-generate resumption context:

```python
def generate_resumption_notes():
    """Generate human-readable resumption context."""

    return f"""
# Project Resumption Context
Generated: {now()}

## Quick Status
- Phases Complete: {count_complete_phases()}/10
- Tasks Complete: {count_complete_tasks()}/{total_tasks()}
- Last Work: {last_updated_phase()}
- Next Recommended: {get_next_task()}

## What Was Done Last Session
{summarize_recent_changes()}

## What Needs Work
{list_incomplete_tasks()}

## How to Continue
1. {next_action_1}
2. {next_action_2}

## Testing Status
- Unit Tests: {unit_test_summary()}
- Integration Tests: {integration_test_summary()}
"""
```

**Saved to:** `PROJECT_RESUMPTION.md` (auto-generated on every state update)

---

### 6. Git Integration for State Inference

**Current Problem:** Git knows what was done, but super-planner doesn't use that info.

**Solution:** Infer state from git history:

```python
def infer_completion_from_git():
    """Use git history to infer task completion."""

    for task in project.tasks:
        for deliverable in task.deliverables:
            # Check if file was committed
            if git.file_exists_in_repo(deliverable.path):
                deliverable.exists = True

                # Get last commit that touched this file
                last_commit = git.get_last_commit(deliverable.path)
                deliverable.last_modified = last_commit.date
                deliverable.committed_by = last_commit.author

                # If all deliverables committed, mark complete
                if all_deliverables_committed(task):
                    task.state = "complete"
                    task.completed_at = last_commit.date
```

---

### 7. State Validation & Healing

**Current Problem:** State can drift. No way to detect/fix.

**Solution:** Validation command:

```bash
make planner-validate

# Or
python -m amplifier.planner validate --fix
```

```python
def validate_and_heal_state():
    """Validate state against reality and fix discrepancies."""

    issues = []

    for task in project.tasks:
        # Check deliverables
        for d in task.deliverables:
            actual_exists = Path(d.path).exists()
            if d.exists != actual_exists:
                issues.append(f"Task {task.id}: {d.path} exists={actual_exists} but tracked as {d.exists}")
                d.exists = actual_exists  # FIX

        # Recalculate task state
        expected_state = calculate_task_state(task)
        if task.state != expected_state:
            issues.append(f"Task {task.id}: state={task.state} but should be {expected_state}")
            task.state = expected_state  # FIX

    return issues
```

---

## Implementation Priority

### P0 - Critical for Resumption
1. ✅ Single source of truth (one authoritative JSON)
2. ✅ File-to-task mapping with existence checks
3. ✅ Auto-generate PROJECT_RESUMPTION.md

### P1 - High Value
4. Automated state sync (git hooks or explicit calls)
5. Test-task integration
6. State validation command

### P2 - Nice to Have
7. Git history inference
8. Advanced dependency tracking

---

## Proposed API Changes

### New Super-Planner Commands

```bash
# Create project with new structure
make planner-create PROJECT="vi_editor" PLAN="vi_completion_plan.md"

# Check current state (scans files, doesn't change anything)
make planner-status PROJECT_ID="uuid"

# Sync state with reality (updates state based on files/git)
make planner-sync PROJECT_ID="uuid"

# Validate and fix state
make planner-validate PROJECT_ID="uuid" --fix

# Generate resumption notes
make planner-resumption PROJECT_ID="uuid"

# Run tests for specific task/phase
make planner-test PROJECT_ID="uuid" TASK="1.1"

# Work on project (original functionality)
make planner-work PROJECT_ID="uuid"
```

---

## Data Structure Changes

### Enhanced Task Schema

```json
{
  "task_id": "1.1",
  "title": "File Loading Module",
  "description": "...",

  "deliverables": [
    {
      "path": "amplifier/vi/file_io/loader.py",
      "type": "implementation",
      "required": true,
      "exists": true,
      "size_bytes": 6268,
      "last_modified": "2025-10-08T17:21:00Z",
      "git_committed": true,
      "commit_sha": "a4bbcec"
    }
  ],

  "tests": {
    "unit": {
      "path": "tests/...",
      "count": 12,
      "passing": 12,
      "last_run": "2025-10-09T08:00:00Z"
    }
  },

  "completion_criteria": {
    "all_files_exist": true,
    "all_tests_pass": false,
    "manual_verification": false
  },

  "state": "files_complete",  # pending | files_complete | tests_passing | verified_complete
  "state_auto_detected": true,
  "state_last_checked": "2025-10-09T08:00:00Z",

  "created_at": "2025-10-07T18:00:00Z",
  "completed_at": "2025-10-08T17:21:00Z",
  "dependencies": ["task_id_1", "task_id_2"]
}
```

---

## Testing the Fix

Once implemented, test with vi editor project:

```bash
# 1. Re-initialize super-planner with new design
make planner-create PROJECT="vi_editor_v2" PLAN="vi_completion_plan.md"

# 2. Sync state with current codebase
make planner-sync PROJECT_ID="..."
# Should detect all files exist and mark phases 1-8 complete

# 3. Generate resumption notes
make planner-resumption PROJECT_ID="..."
# Should say "All phases complete, ready for testing"

# 4. Simulate interruption and resume
# ... do some work ...
# ... exit ...
# ... resume in new session ...
make planner-resumption PROJECT_ID="..."
# Should show exactly where we left off

# 5. Validate state
make planner-validate PROJECT_ID="..." --fix
# Should find no issues (or fix what it finds)
```

---

## Success Criteria

Super-planner v2 is successful if:

1. ✅ **Single command gives full context:** `make planner-resumption` tells me everything
2. ✅ **No manual tracking needed:** File creation = task completion (when all files exist)
3. ✅ **Test integration:** Can see which tasks have passing tests
4. ✅ **Git awareness:** Uses git history to infer completion
5. ✅ **Self-healing:** Can detect and fix state drift
6. ✅ **Cross-session continuity:** Any agent can resume from where any other left off

---

## Files to Modify in Super-Planner

```
amplifier/planner/
├── models.py              # Add deliverables, tests fields to Task model
├── storage.py             # Add file existence checking
├── sync.py                # NEW: Auto-sync from filesystem/git
├── validation.py          # NEW: State validation and healing
├── resumption.py          # NEW: Generate resumption context
└── cli.py                 # Add new commands (sync, validate, resumption)
```

---

## Migration Plan for Existing Projects

For vi editor project:

```python
def migrate_vi_project():
    """Migrate vi editor to new super-planner format."""

    # 1. Load old project
    old_project = load_json("vi_completion_project.json")

    # 2. Scan filesystem for all vi files
    files = scan_directory("amplifier/vi/")

    # 3. Map files to tasks
    for task in old_project.tasks:
        task.deliverables = infer_deliverables_from_plan(task)
        for d in task.deliverables:
            d.exists = check_file_exists(d.path)

    # 4. Auto-detect completion
    for task in old_project.tasks:
        if all(d.exists for d in task.deliverables):
            task.state = "files_complete"

    # 5. Save new format
    save_json("vi_project_v2.json", old_project)

    # 6. Generate resumption notes
    generate_resumption_notes()
```

---

_This document should be read by whoever implements super-planner v2 fixes._
