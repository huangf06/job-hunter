# Turso DB Archival & Size Management

**Date**: 2026-02-22
**Status**: Approved
**Problem**: Turso cloud DB approaching 3 GB free tier limit; local replica is only 20 MB

## Root Cause

Turso accumulates WAL/replication history. With CI running 3x/day (weekdays) doing dozens of writes+syncs, the internal overhead grows far beyond actual data size (~20 MB data → ~3 GB storage).

## Current Data Profile

| Table | Rows | Notes |
|-------|------|-------|
| jobs | 1,220 | 12.9 MB (raw_data: 6.6 MB, description: 6.1 MB) |
| filter_results | 1,220 | 1:1 with jobs |
| ai_scores | 635 | Rule-based scores (passed filter only) |
| job_analysis | 585 | AI analysis (456 valid, 129 sentinel) |
| resumes | 312 | Generated resume records |
| applications | 361 | 211 applied, 76 rejected, 43 skipped, 19 interview, 12 pending |
| cover_letters | 185 | |
| emails | 340 | Gmail integration |
| processed_emails | 617 | Gmail dedup tracking |

Data range: 2026-02-08 to 2026-02-22 (14 days, since v2.0 launch).

## Design

### Phase 1: Safe Backup

1. Install Turso CLI (`irm get.tur.so/install.ps1 | iex`)
2. Full cloud dump: `turso db shell <db-name> .dump > data/archive/turso_full_dump_2026-02-22.sql`
3. Verify completeness: compare Turso dump row counts against local replica
4. Verified backup becomes ground truth for all subsequent operations

### Phase 2: Archive Command (`--archive`)

New CLI command: `python scripts/job_pipeline.py --archive`

**Cold data definition** (ALL conditions must be met):
- `scraped_at` older than 30 days
- No application with status `applied` / `interview` / `offer`
- Has a filter_result (not in active pipeline)

**Archive flow**:
1. Open/create `data/archive/archive_YYYY-MM.db` (same schema, monthly files)
2. INSERT cold jobs + all related records (filter_results, ai_scores, job_analysis, resumes, cover_letters, emails) using `INSERT OR IGNORE`
3. Verify write success (row count check)
4. DELETE archived records from live DB (cascade through all related tables)
5. Print archive statistics

**Retained in Turso** (never archived):
- All jobs with `applied` / `interview` / `offer` application status (permanent)
- All jobs within the last 30 days (active pipeline)
- `processed_emails` table (lightweight, prevents reprocessing)

**Archive file strategy**:
- Monthly files: `archive_2026-02.db`, `archive_2026-03.db`, etc.
- `INSERT OR IGNORE` for idempotency (safe to re-run)
- Local only — not pushed to Turso, not committed to git
- `data/archive/` added to `.gitignore`

### Phase 3: Cloud DB Compaction (if needed)

If Turso dashboard still shows ~3 GB after archival + deletion:

1. Verify: local archive + current replica = complete dataset (compare against Phase 1 backup)
2. Create new Turso DB: `turso db create job-hunter-v2`
3. Upload clean local replica to new DB
4. Update GitHub Secrets with new `TURSO_DATABASE_URL`
5. Verify new DB works (run `--stats`)
6. Destroy old DB: `turso db destroy job-hunter`

### Phase 4: Ongoing Maintenance

- `--finalize` shows a reminder when cold data exceeds N rows
- 30-day retention is the starting point; can be reduced if needed
- `raw_data` column: kept as-is (archival handles the size problem)

## Implementation Order

1. Install Turso CLI + full backup (manual)
2. Verify local replica completeness (manual)
3. Implement `--archive` command in `job_pipeline.py` + `job_db.py`
4. Run archive, observe Turso dashboard effect
5. If needed: recreate Turso DB (manual)
