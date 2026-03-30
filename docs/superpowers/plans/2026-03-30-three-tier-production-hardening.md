# Three-Tier Production Hardening Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the first production run of the three-tier resume pipeline, verify the riskiest first-run paths, and check in the design/review artifacts that should live in the repository.

**Architecture:** Keep the scope narrow. Validate the highest-risk first-run paths with targeted tests, implement the minimum code changes needed to make those tests pass, then verify the affected commands and preserve the planning/review documents in git.

**Tech Stack:** Python 3.11, pytest, SQLite/Turso DB layer, Jinja2/Playwright resume rendering, git

---

## Chunk 1: First-Run Risk Validation

### Task 1: Identify the highest-risk first-run path

**Files:**
- Modify: `tests/test_job_pipeline_template_stats.py`
- Modify: `tests/test_resume_renderer_tiers.py`
- Test: `tests/test_job_pipeline_template_stats.py`
- Test: `tests/test_resume_renderer_tiers.py`

- [ ] **Step 1: Write or extend the failing test for the first confirmed production gap**

Add the smallest assertion that captures the breakage in `--template-stats` or tiered rendering fallback behavior.

- [ ] **Step 2: Run the targeted test to verify it fails**

Run: `pytest tests/test_job_pipeline_template_stats.py -v` or `pytest tests/test_resume_renderer_tiers.py -v`
Expected: FAIL on the newly added assertion for the confirmed gap.

- [ ] **Step 3: Write the minimal implementation to satisfy the failing test**

Modify only the production code directly responsible for the failing behavior.

- [ ] **Step 4: Run the targeted test again to verify it passes**

Run the same pytest command as Step 2.
Expected: PASS

## Chunk 2: Regression Guardrails

### Task 2: Verify no three-tier query or fallback regression remains in the touched area

**Files:**
- Modify: `tests/test_job_db_resume_strategy.py`
- Modify: `tests/test_job_pipeline_template_stats.py`
- Modify: `tests/test_resume_renderer_tiers.py`
- Test: `tests/test_job_db_resume_strategy.py`
- Test: `tests/test_job_pipeline_template_stats.py`
- Test: `tests/test_resume_renderer_tiers.py`

- [ ] **Step 1: Add any missing regression test covering the touched query/fallback contract**

Prefer one focused test over broad fixture churn.

- [ ] **Step 2: Run the new regression test to verify red**

Run: `pytest <targeted test selector> -v`
Expected: FAIL for the intended reason before the code change.

- [ ] **Step 3: Apply the minimum code fix**

Keep logic aligned with the three-tier addendum contract and legacy compatibility rules.

- [ ] **Step 4: Run the affected test modules**

Run: `pytest tests/test_job_db_resume_strategy.py tests/test_job_pipeline_template_stats.py tests/test_resume_renderer_tiers.py -v`
Expected: PASS

## Chunk 3: Repository Record

### Task 3: Preserve design and review artifacts in git

**Files:**
- Create: `docs/superpowers/plans/2026-03-30-three-tier-production-hardening.md`
- Add: `docs/plans/2026-03-29-resume-strategy-v2-addendum.md`
- Add: `docs/reports/`

- [ ] **Step 1: Confirm artifact set is intentional**

Inspect `docs/reports/` contents and ensure they are design/review records, not throwaway generated noise.

- [ ] **Step 2: Stage the approved documentation set**

Run: `git status --short`
Expected: the addendum, reports folder, and any code/test changes appear as intended.

- [ ] **Step 3: Run final targeted verification**

Run the affected pytest modules again after docs are staged.
Expected: PASS

- [ ] **Step 4: Summarize ready-to-commit changes**

Include the production-hardening fix, verification evidence, and the document check-in set.
