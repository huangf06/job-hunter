# Checklist Defer Status Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a "defer" status to the checklist so jobs needing more prep time survive finalize and reappear in the next --prepare cycle.

**Architecture:** Add `status` field ("pending"/"applied"/"deferred") to state.json, replacing the boolean `applied`. UI gets 3-state toggle buttons. Finalize ignores deferred jobs entirely (no DB update, no folder move). No DB schema changes needed.

**Tech Stack:** Python, HTML/CSS/JS (inline in checklist_server.py)

---

### Task 1: Update state.json schema (checklist_server.py)

**Files:**
- Modify: `src/checklist_server.py:24-43` (generate_checklist)

**Change:** Replace `"applied": False` with `"status": "pending"` in the state dict.

---

### Task 2: Update checklist HTML UI (checklist_server.py)

**Files:**
- Modify: `src/checklist_server.py:55-211` (_build_checklist_html)

**Changes:**
- Replace checkbox column with 3 toggle buttons: Skip (default) / Applied / Defer
- Style: Applied=green, Defer=amber, Skip=gray (default)
- JS: toggle `state.jobs[jobId].status` between "pending"/"applied"/"deferred"
- Summary: show "N applied, M deferred, K skip"
- Page reload: restore button states from state.json `status` field
- Backward compat in reload: if old state has `applied` boolean, convert to status

---

### Task 3: Update finalize (job_pipeline.py)

**Files:**
- Modify: `scripts/job_pipeline.py:515-657` (cmd_finalize)

**Changes:**
- Add migration: if job has `applied` key but no `status`, convert (`applied=true` → "applied", else "pending")
- Split jobs into 3 groups: applied (status=="applied"), skipped (status=="pending"), deferred (status=="deferred")
- Deferred jobs: skip entirely (no DB update, no folder move)
- Validation: accept both old and new schema (`applied` or `status` required, not both)
- Summary: report deferred count

---

### Task 4: Test manually

Run `--prepare`, verify 3-state buttons work in browser, mark some as deferred, run `--finalize`, verify deferred jobs are untouched, run `--prepare` again, verify they reappear.
