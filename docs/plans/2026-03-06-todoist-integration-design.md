# Todoist Integration Design

**Date**: 2026-03-06
**Status**: Approved

## Goal

Add Todoist task management capability to job-hunter, replicating LifeOS's `TodoistManager` as a standalone CLI tool.

## Decision Summary

| Decision | Choice |
|----------|--------|
| Scope | Complete TodoistManager (create/batch/list/export/setup/test) |
| Config | Shared — read LifeOS's `config/todoist_config.json`, fallback to local |
| Module location | `scripts/todoist_manager.py` (single file, CLI + class) |
| CLI style | Independent script with positional action argument |

## Architecture

```
scripts/todoist_manager.py    ← TodoistManager class + CLI entry point
                                 (adapted from LifeOS/scripts/todoist_manager.py)

Config loading order:
  1. LifeOS:  ~/github/LifeOS/config/todoist_config.json
  2. Local:   config/todoist_config.json
  3. Neither: prompt user to run `setup`
```

## Changes from LifeOS Original

1. **Config path resolution**: Instead of only looking at `../config/todoist_config.json` relative to script, first try LifeOS path, then fallback to local.
2. **CLI `add` command**: Add `add "task content"` action (LifeOS doesn't have this as CLI action).
3. **Remove `fitness` action**: LifeOS-specific, not relevant to job-hunter.
4. **Update help text**: Reflect job-hunter context.

## CLI Commands

```bash
python scripts/todoist_manager.py test              # Test connection
python scripts/todoist_manager.py setup             # Interactive API token setup
python scripts/todoist_manager.py add "task text"   # Create a task
python scripts/todoist_manager.py list              # List all tasks
python scripts/todoist_manager.py list --project career  # Filter by project
python scripts/todoist_manager.py export            # Export to JSON
python scripts/todoist_manager.py init-projects     # Initialize projects & labels
```

## Dependencies

- `todoist-api-python` (add to `requirements.txt`)

## Files Modified

- `scripts/todoist_manager.py` — NEW (adapted from LifeOS)
- `requirements.txt` — add `todoist-api-python`
- `.gitignore` — add `config/todoist_config.json`
