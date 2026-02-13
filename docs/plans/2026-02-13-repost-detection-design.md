# Repost Detection Design

## Problem
LinkedIn reposts jobs with new URLs. Our system uses URL-based job_id (MD5 hash), so reposts bypass dedup and enter the pipeline as new jobs — even if we already applied to the same company+title.

## Decision
Query-layer detection (Approach A). No schema changes. Warn but don't block.

## Matching Criteria
- company + title exact match (case-insensitive via LOWER())
- Only matches against jobs with application status = 'applied'
- Different job_id (same job_id is just a URL dedup, not a repost)

## Changes

### 1. `src/db/job_db.py` — `find_applied_duplicates(job_id)`
- Input: job_id
- Query: JOIN jobs + applications, find same company+title (LOWER), status='applied', different job_id
- Return: `list[dict]` with `{job_id, title, company, applied_at}`, empty = no duplicates

### 2. `scripts/job_pipeline.py` — `--ready` output
- Check each ready job via `find_applied_duplicates()`
- Console: `[REPOST]` tag + original applied_at date
- HTML checklist: warning badge on repost jobs

### 3. `scripts/job_pipeline.py` — `--generate` output
- Check before rendering, print console warning
- Still generates resume (JD may have changed)

## Not Changed
- No schema migration
- No changes to `insert_job()`
- No blocking of any pipeline stage
- AI analysis proceeds normally (repost JD may differ)
