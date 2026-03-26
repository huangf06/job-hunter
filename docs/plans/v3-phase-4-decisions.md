# Phase 4: Code Architecture — Decisions

**Date**: 2026-03-26
**Status**: Final
**Depends on**: Phase 1-3 decisions (architecture serves the pipeline, not the other way around)

---

## 4.1 What Refactoring Is Actually Needed Now?

**Method: Walk through Phase 1-3 changes and identify what the current code structure blocks.**

### Phase 1 changes (resume generation):
- Re-enable AI analysis in CI → **Not blocked** (just uncomment env var)
- Update HTML template CSS → **Not blocked** (edit `base_template.html`)
- Make CL optional → **Minor change** in `job_pipeline.py` prepare flow
- Add cleanup command → **Not blocked** (add method to `JobDatabase` + CLI flag)

### Phase 2 changes (pipeline):
- Write `TursoHTTPClient` → **Blocked by DB coupling**: 5 modules hardcode `from src.db.job_db import JobDatabase`. Replacing the DB layer means touching all of them.
- Upload materials to R2 → **Not blocked** (add new step in CI)
- Static checklist generator → **Not blocked** (rewrite `checklist_server.py`)
- Read checklist state from R2 → **Minor change** in `--finalize` flow

### Phase 3 changes (feedback loop):
- Add `application_events` table → **Not blocked** (add migration + methods to `JobDatabase`)
- Telegram command for status update → **Not blocked** (new handler)
- Weekly/monthly digest → **Not blocked** (new CI step + Telegram)
- Auto-transitions → **Not blocked** (add cron logic in CI)

### Verdict

**Only one thing is actually blocked**: The Turso HTTP migration requires changing how `JobDatabase` connects to the database. Since 5 modules import it directly, we need to ensure the interface doesn't break.

**Everything else — the monolithic CLI, scattered config, duplicate validation — is annoying but not blocking.** The CLI is big but each `--flag` works independently. Config loading is scattered but each module loads what it needs correctly. Validation runs twice but doesn't produce incorrect results.

---

## 4.2 Minimal Architectural Changes

**Decision: Three targeted changes, not a full rewrite.**

### Change 1: Replace DB connection layer (serves Phase 2)

**What**: Replace `libsql` embedded replica with `TursoHTTPClient` inside `JobDatabase`.

**How**: `JobDatabase.__init__()` currently creates a `libsql` connection with sync. Change it to create a `TursoHTTPClient` that uses HTTP API. All 103 methods keep their signatures — they just call `self.client.execute(sql, params)` instead of `self.conn.execute(sql, params)`.

**Scope**: Only `src/db/job_db.py` changes. All 5 importing modules see the same `JobDatabase` interface.

**Testing**: Run existing `--stats`, `--process`, `--prepare` against Turso HTTP. Compare output to current behavior. This is the "golden master" test.

**Lines deleted**: ~400 (sync/replica/recovery code)
**Lines added**: ~50 (HTTP client)
**Risk**: Low — interface unchanged, only transport layer swapped

### Change 2: Extract `ApplicationTracker` (serves Phase 3)

**What**: New class that owns application state transitions, event recording, and digest generation.

```python
# src/application_tracker.py (~150 lines)
class ApplicationTracker:
    def __init__(self, db: JobDatabase):
        self.db = db

    def update_status(self, job_id: int, state: str, source: str = "manual", note: str = None):
        """Validate state transition, record event, update current state."""

    def run_auto_transitions(self):
        """Move stale applications through timeout states."""

    def weekly_digest(self) -> str:
        """Generate weekly summary text."""

    def monthly_report(self) -> str:
        """Generate monthly conversion report text."""

    def get_current_state(self, job_id: int) -> str:
        """Derive current state from latest event."""
```

**Why extract?** The existing `applications` table is managed by scattered methods in `JobDatabase` (`mark_applied`, `update_application_status`, `get_application_status`). Phase 3 adds state machine logic, auto-transitions, and reporting — this doesn't belong in the DB layer.

**Scope**: New file. Existing `JobDatabase` application methods remain (called by `ApplicationTracker`). No other modules change.

**Risk**: None — purely additive

### Change 3: Add `application_events` table (serves Phase 3)

**What**: New table for append-only event log. Added via schema migration in `JobDatabase._init_db()`.

```sql
CREATE TABLE IF NOT EXISTS application_events (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    state TEXT NOT NULL,
    source TEXT DEFAULT 'manual',
    note TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(job_id, state, created_at)
);
```

**Backfill**: On first run, populate from existing `applications` table:
```sql
INSERT OR IGNORE INTO application_events (job_id, state, source, created_at)
SELECT id, status, 'backfill', applied_at FROM applications WHERE status IS NOT NULL;
```

**Risk**: None — new table, no existing data affected

---

## 4.3 What We Explicitly Do NOT Change

| Proposed in v3 design doc | Decision | Why not now |
|---------------------------|----------|-------------|
| 6 repository protocols + UnitOfWork | Skip | Only DB connection transport changes; interface stays the same |
| Stage Engine (11 stages) | Skip | Current `--process` flag-based pipeline works; stages add abstraction without solving a real problem |
| Typer CLI rewrite | Skip | argparse works; 30+ flags is ugly but functional; rewriting CLI is high effort, zero user value |
| ConfigManager with fingerprinting | Skip | 5 independent `_load_config()` calls work correctly; no bugs caused by this |
| Directory restructure (core/domain/services/integrations/stages/cli) | Skip | Moving files doesn't fix any Phase 1-3 blocker |
| ValidateStage deduplication | Skip | Validator runs in both analyzer and renderer, but this causes no bugs — just redundant CPU |
| Email Router | Skip (Phase 5) | Requires stable application tracking first |
| Feature flags | Skip | Three changes are small enough to deploy directly |

**Principle**: Refactor only what blocks Phase 1-3 delivery. The v3 architecture design doc is a vision document — it describes where we might go. But most of those changes don't solve the five current pain points (pipeline offline, CL quality, no feedback, no cloud automation, risky changes).

---

## 4.3 Migration Strategy

**All three changes can be done as "strangler fig":**

### Change 1 (DB transport):
- Add `TursoHTTPClient` alongside existing `libsql` code
- Add env var `DB_TRANSPORT=http|libsql` (default: `libsql`)
- Test with `DB_TRANSPORT=http` locally and in CI
- Once confirmed working, flip default to `http`
- Delete `libsql` code path after 1 week of stable operation

### Change 2 (ApplicationTracker):
- New file, no existing code changes
- Pipeline calls `ApplicationTracker` for new functionality
- Existing `mark_applied` in `JobDatabase` still works (called internally by tracker)

### Change 3 (application_events table):
- `CREATE TABLE IF NOT EXISTS` — safe to run on any DB
- Backfill runs once, idempotent via `INSERT OR IGNORE`

**Testing strategy**:
1. **DB transport**: Golden master — run `--stats` with both transports, diff output
2. **ApplicationTracker**: Unit tests for state transitions (valid/invalid) and auto-transitions
3. **application_events**: Check backfill count matches `applications` table count

**Rollback plan**:
1. **DB transport**: Set `DB_TRANSPORT=libsql` — instant rollback
2. **ApplicationTracker**: Delete import, pipeline falls back to direct `JobDatabase` calls
3. **application_events**: Table is additive; ignore it if needed

---

## Phase 4 Summary

| Change | Scope | Lines changed | Risk | Serves |
|--------|-------|---------------|------|--------|
| TursoHTTPClient | `job_db.py` only | -400, +50 | Low (env flag rollback) | Phase 2 |
| ApplicationTracker | New file | +150 | None (additive) | Phase 3 |
| application_events | Schema addition | +10 SQL | None (additive) | Phase 3 |

**Total refactoring**: ~3 files changed, ~200 net lines removed. No directory restructure, no protocol layer, no stage engine, no CLI rewrite.
