# Turso DB Size & Sync Management

**Date**: 2026-02-22
**Status**: Implemented
**Problem**: Turso free tier limits — storage approaching 3 GB, sync volume at 2.78/3 GB

## Root Causes

1. **Sync volume**: 5 separate CI jobs = 5 fresh runners = 5 full DB downloads per workflow.
   ~120 MB/run × 34 runs in 14 days = ~4 GB theoretical (actual: 2.78 GB).
2. **Storage bloat**: Turso WAL/replication history not auto-compacted.

## Solutions Implemented

### 1. Data Archival (`--archive` command)

**Turso = transit station** (CI only), **local = full history**.

```bash
python scripts/job_pipeline.py --archive                  # default 7-day retention
python scripts/job_pipeline.py --archive --retention-days 3  # more aggressive
```

- Cold data → `data/archive/full_history.db` (single file, easy to query)
- Cold = scraped >7 days ago AND not applied/interview/offer AND has filter_result
- `INSERT OR IGNORE` for idempotency (safe to re-run)
- Verified: live 682 + archive 538 = 1,220 total (no data loss)

### 2. CI Workflow Consolidation (v3.0 → v4.0)

Merged 5 separate jobs into 1 job with 5 steps. Same runner = same `data/jobs.db` file = embedded replica downloaded once.

**Before (v3.0)**: 5 jobs × ~15 MB init sync = ~120 MB/run
**After (v4.0)**: 1 init sync + incremental = ~18 MB/run (**-85%**)

Monthly estimate: ~4.2 GB → ~0.6 GB (well within 3 GB limit).

Key changes:
- `continue-on-error: true` on scrape/score/AI steps (non-critical steps don't block pipeline)
- `if: always()` on notify + stats (always run regardless of earlier failures)
- Single `pip install` + `playwright install` (was duplicated 5 times)
- `if-no-files-found: ignore` on artifact upload (scrape may be skipped)

### 3. Cloud DB Compaction (if needed)

If Turso dashboard storage doesn't decrease after archival:

1. Verify: local archive + current replica = complete dataset
2. Create new Turso DB: `turso db create job-hunter-v2`
3. Upload clean local replica to new DB
4. Update GitHub Secrets with new `TURSO_DATABASE_URL`
5. Destroy old DB after verification

## File Layout

```
data/
├── jobs.db                          # Turso embedded replica (active data)
└── archive/
    ├── full_history.db              # All archived cold data
    └── turso_backup_2026-02-22.db   # Pre-archival full backup
```
