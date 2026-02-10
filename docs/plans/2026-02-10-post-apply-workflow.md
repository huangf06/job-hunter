# Post-Apply Workflow Improvements

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add bulk mark-applied, auto-cleanup, application tracker, and status update commands to the job pipeline.

**Architecture:** All changes in `scripts/job_pipeline.py` (CLI + pipeline logic) and `src/db/job_db.py` (one new query method). No new files.

**Tech Stack:** Python, SQLite, argparse

---

### Task 1: Add `--mark-all-applied` with auto-cleanup

**Files:**
- Modify: `scripts/job_pipeline.py` (argparse + handler logic)

**What to do:**
1. Add `--mark-all-applied` flag to argparse
2. Handler: query `v_ready_to_apply`, mark each as applied in DB, move each `submit_dir` to `_applied/`, move `apply_checklist.html` to `_applied/`
3. Print summary: how many marked, how many folders archived

**Implementation notes:**
- Reuse existing archive pattern from `--mark-applied` (lines 971-991)
- Use single DB connection for bulk insert (performance)
- The `get_ready_to_apply()` method already returns jobs with `submit_dir`

### Task 2: Add `--update-status JOB_ID STATUS` command

**Files:**
- Modify: `scripts/job_pipeline.py` (argparse + handler)

**What to do:**
1. Add `--update-status` flag that takes 2 args: job_id and status
2. Valid statuses: `rejected`, `interview`, `offer`
3. Auto-set timestamp: `response_at` for rejected, `interview_at` for interview
4. Print confirmation with job title/company

### Task 3: Add `--tracker` command

**Files:**
- Modify: `scripts/job_pipeline.py` (argparse + handler)
- Modify: `src/db/job_db.py` (new query method)

**What to do:**
1. Add `get_application_tracker()` to `JobDatabase` — query applications joined with jobs, grouped by status
2. Add `--tracker` CLI flag
3. Display: summary counts + per-status job lists
4. Show: status, company, title, applied_at, days since applied

### Task 4: Make checklist reflect applied status

**Files:**
- Modify: `scripts/job_pipeline.py` (`show_ready()` method)

**What to do:**
- No change needed to checklist generation itself (it already uses `v_ready_to_apply` which excludes applied jobs)
- The fix is that `--mark-all-applied` moves the checklist to `_applied/` (covered in Task 1)
- When `--ready` is called again, it regenerates a fresh checklist with only unapplied jobs
- This is already correct behavior — the "bug" was only that we weren't running `--mark-all-applied` (which didn't exist)

---

## Execution: Subagent-Driven (this session)
