# Pipeline Restoration Execution Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore the job pipeline to full local operation with new dual-column resume template, Claude Code as AI provider, and simplified DB layer. Then process 3 weeks of backlogged jobs.

**Architecture:** Keep existing pipeline structure. Three targeted changes: (1) rewrite HTML template to match DE Resume SVG dual-column layout, (2) add `claude_code` provider to ai_analyzer.py, (3) replace libsql embedded replica with Turso HTTP client. No directory restructure, no new abstractions.

**Tech Stack:** Python, Jinja2, Playwright, Claude Code CLI, httpx, Turso HTTP API

---

## Task 1: Rewrite `base_template.html` to dual-column layout

**Files:**
- Modify: `templates/base_template.html`

**Design spec** (match `templates/Fei_Huang_DE_Resume.svg` exactly):

Layout: CSS Grid, two columns
- Left column (~55%): Bio + Experience
- Right column (~45%): Education → Certifications → Recent Project → Technical Skills → Languages

Typography:
- Name: Georgia 24pt bold, left-aligned, #1f1b1b (NO center, NO border-bottom)
- Contact: Arial 10px, #2f2f2f, top-right corner (same row as name)
- Section headers: Arial 8px bold, #33455a, uppercase, letter-spacing 0.4px, NO underline
- Body text: Arial 10px, #4f4f4f (NOT Georgia)
- Company + Title: same line — `Company (Note) - Title`, Georgia bold + italic
- Date: Arial 8px, #6a6a6a, uppercase
- Experience content: paragraph text with bold keywords (NO bullet points)
- Per-experience `Skills:` line at bottom
- No "Additional" section (no interests, no blog)
- Languages as standalone section in right column

Jinja2 interface: preserve all existing `{{ }}` variables. Renderer code does NOT change.

Print/PDF: A4, Playwright-compatible, `@page` margins matching SVG (42pt left, ~42pt top).

**Step 1:** Rewrite the full HTML+CSS template
**Step 2:** Render a test resume locally with sample data to verify layout
**Step 3:** Compare rendered PDF side-by-side with DE Resume SVG
**Step 4:** Commit

---

## Task 2: Add `claude_code` provider to ai_analyzer.py

**Files:**
- Modify: `src/ai_analyzer.py`
- Modify: `config/ai_config.yaml`

**Design:**

Add a new model config in `ai_config.yaml`:
```yaml
claude_code:
  provider: "claude_code"
  model: "claude-sonnet-4-6"  # or opus, controlled by Claude Code's model setting
  max_tokens: 8192
  temperature: 0.3
```

Set `active_model: "claude_code"` for local use.

In `ai_analyzer.py`, add a code path for `provider == "claude_code"`:
- Write the full prompt (system + user) to a temp file
- Call `claude -p <prompt> --output-format text --model claude-sonnet-4-6 --max-tokens 8192`
- Parse JSON from stdout (same format as current API response)
- Handle errors (timeout, invalid JSON, empty response)

Keep existing `anthropic` SDK path for API-based providers (opus, kimi). The `provider` field determines which path runs.

**Step 1:** Add `claude_code` config to `ai_config.yaml`
**Step 2:** Implement `_analyze_via_claude_code()` method in `AIAnalyzer`
**Step 3:** Wire it into the existing `analyze_job()` dispatch
**Step 4:** Test with one job: `python src/ai_analyzer.py --job <ID> --model claude_code`
**Step 5:** Commit

---

## Task 3: Replace DB layer with Turso HTTP client

**Files:**
- Modify: `src/db/job_db.py`
- Modify: `.env` (no new vars needed, existing `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN` are reused)

**Design:**

Write `TursoHTTPClient` class (~50 lines) using `httpx`:
- `execute(sql, params) -> list[dict]` — single statement
- `execute_batch(statements) -> list[list[dict]]` — multiple statements in one HTTP call
- Uses Turso HTTP API v2: `POST {db_url}/v3/pipeline`
- Auth: `Authorization: Bearer {token}`

Replace connection setup in `JobDatabase.__init__()`:
- If `TURSO_DATABASE_URL` is set: use `TursoHTTPClient`
- Else: fall back to local `sqlite3` (for offline use)

Delete all embedded replica code:
- `_try_sync()`, `_sync_to_turso()`, `_sync_from_turso()`
- `WalConflict` recovery handler
- Windows health check fallback
- `batch_mode()` sync suppression
- `TURSO_SYNC_MODE` config
- `final_sync()` calls
- `libsql` import and connection logic

Add `DB_TRANSPORT=http|sqlite` env var as escape hatch.

**Step 1:** Write `TursoHTTPClient` class
**Step 2:** Integrate into `JobDatabase.__init__()`
**Step 3:** Delete sync/replica code
**Step 4:** Test: `python scripts/job_pipeline.py --stats` matches expected output
**Step 5:** Commit

---

## Task 4: End-to-end local test

**Files:** None (testing only)

**Step 1:** Run `python scripts/job_pipeline.py --stats` — verify DB works
**Step 2:** Run `python scripts/job_pipeline.py --process` — verify filter + score on any new jobs
**Step 3:** Run `python scripts/job_pipeline.py --ai-analyze --limit 1` — verify Claude Code provider works
**Step 4:** Check generated PDF in `output/` — verify dual-column template renders correctly
**Step 5:** Fix any issues found

---

## Task 5: Process 3-week backlog

**Step 1:** Run `--process` to filter and score all backlogged jobs
**Step 2:** Query score distribution:
```sql
SELECT
  CASE
    WHEN score >= 7 THEN '7+'
    WHEN score >= 5 THEN '5-6.9'
    WHEN score >= 3 THEN '3-4.9'
    ELSE '<3'
  END as bracket,
  COUNT(*) as count
FROM ai_scores GROUP BY bracket ORDER BY bracket DESC
```
**Step 3:** Based on distribution, set AI analysis threshold (target: ~5.0, adjust to keep batch manageable — under 50 jobs)
**Step 4:** Run AI analysis: `python scripts/job_pipeline.py --ai-analyze --min-score <threshold> --limit 50`
**Step 5:** Run `--stats` to see results
**Step 6:** Commit any config threshold changes

---

## Task 6: CI workflow update

**Files:**
- Modify: `.github/workflows/job-pipeline-optimized.yml`

**Changes:**
- Keep AI analysis step disabled (no API key in CI)
- Ensure scrape → filter → score steps work with Turso HTTP
- Update any env vars if needed
- Remove `ANTHROPIC_BASE_URL` references

**Step 1:** Update workflow file
**Step 2:** Commit and push
**Step 3:** Verify next scheduled run succeeds (or trigger manually)

---

## Execution Notes

- Tasks 1-3 are independent, execute sequentially (fast)
- Task 4 is integration test after 1-3
- Task 5 depends on 4 passing
- Task 6 can be done after 5
- All changes committed individually with descriptive messages
- If any step fails, fix before proceeding
- Full authority granted: code changes, commits, pushes, local commands
