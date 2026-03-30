# Block E+F Design: Deliver + Notify Audit & Refinement

## Overview

Combined audit-and-refine pass for Block E (Deliver: `--prepare`, `--finalize`, `--tracker`) and Block F (Notify: CI Telegram notification). Method: review existing code, fix issues found, delete dead code. Not a rewrite.

## Audit Summary

### Files Audited

| File | Block | Lines | Verdict |
|------|-------|-------|---------|
| `scripts/job_pipeline.py` (cmd_prepare, cmd_finalize, --tracker) | E | ~250 | Solid; needs state.json validation |
| `src/checklist_server.py` | E | 268 | XSS in JSON embedding; dead method |
| `scripts/notify.py` | F | ~250 | Dead code; missing generate stats |
| `scripts/notify_discord.py` | F | 120 | Unused; delete |
| `.github/workflows/job-pipeline-optimized.yml` | F | 176 | Clean; no changes needed |
| `src/db/job_db.py` (application methods) | E | ~100 | Clean; no changes needed |

### Key Findings

1. **Three-tier routing compatibility**: No issues. `cmd_prepare`/`cmd_finalize` are tier-agnostic. Resume tier logic lives in `ResumeRenderer.render_resume()`, which is called correctly. `get_funnel_stats()` already tracks all three tiers.
2. **Block D interface**: `--prepare` calls `render_resume()` correctly after Block D refactor. No breakage.
3. **E and F code overlap**: Near-zero. Only shared touchpoint is `get_funnel_stats()` and `get_ready_to_apply()` called by both. Combined into one design doc for efficiency, not because they're coupled.

## Change List

### EF-1: Delete `scripts/notify_discord.py`

- **What**: Remove the file
- **Why**: Not called in CI workflow, no DB integration, `requests` dependency unused elsewhere
- **Risk**: None -- not imported or referenced anywhere
- **Test**: `grep -r notify_discord` confirms zero references

### EF-2: Fix XSS in `src/checklist_server.py`

- **What**: Replace raw JSON string embedding (line 130) with `JSON.parse()` wrapper using `json.dumps()` for proper escaping
- **Why**: Job titles from scraped sites are embedded in `<script>` context without escaping. A title containing `</script>` could break the page.
- **Risk**: Low -- output is the same JS object, just safer encoding
- **Test**: Unit test with title containing `</script><img onerror=alert(1)>`

### EF-3: Remove dead `_send_json()` in `src/checklist_server.py`

- **What**: Delete the `_send_json()` method from ChecklistHandler
- **Why**: Defined but never called
- **Risk**: None
- **Test**: `grep _send_json` confirms no callers

### EF-4: Remove redundant `get_funnel_stats()` call in `scripts/notify.py`

- **What**: Delete lines 59-63 where `get_funnel_stats()` result is fetched, then immediately overwritten by direct SQL on lines 66-79
- **Why**: Dead code -- the extracted values (`applied`, `interview`, `rejected`) are overwritten before first use
- **Risk**: None
- **Test**: `python scripts/notify.py --status success --dry-run` output unchanged

### EF-5: Add `generate` step visibility to `scripts/notify.py`

- **What**: Query `resumes` table for today's generation count (`WHERE created_at >= today`), include in notification message
- **Why**: Block D's `--generate` step runs in CI but results are invisible in notifications
- **Risk**: Low -- additive message change, no logic change
- **Test**: `--dry-run` with jobs that have today's resume records

### ~~EF-6: Fix CI workflow duplicate step check~~ DROPPED

Audit false positive. Lines 169-171 correctly check `ai_evaluate`, `ai_tailor`, and `generate` respectively. No bug.

### EF-7: Add `state.json` schema validation in `cmd_finalize()`

- **What**: After `json.loads()` in cmd_finalize, validate structure: dict with `jobs` key containing dict of records, each with required keys (`applied`, `submit_dir`, `company`, `title`). Raise clear error on malformed input.
- **Why**: Currently a corrupted state.json causes cryptic KeyError deep in the function
- **Risk**: Low -- validation before existing logic
- **Test**: Unit test with malformed state.json

### EF-8: Tests for modified code

- **What**: Tests for EF-2 (XSS escaping), EF-5 (generate stats), EF-7 (state.json validation)
- **Why**: Test what we touch
- **Risk**: None
- **Test**: `NO_TURSO=1 python -m pytest tests/ -v`

## Out of Scope

- Extracting hardcoded values (port, colors, thresholds) to config -- not worth the churn for a single-user local tool
- Tests for untouched DB methods -- stable, battle-tested by daily use
- Discord notification integration -- deleting instead
- Refactoring checklist_server.py architecture -- it works, it's simple

## Implementation Order

Approach A (fix-by-file):

1. `notify_discord.py` -- delete (EF-1)
2. `checklist_server.py` -- XSS fix + dead code removal (EF-2, EF-3)
3. `notify.py` -- dead code removal + generate stats (EF-4, EF-5)
4. `job_pipeline.py` -- state.json validation (EF-7)
5. Tests (EF-8)

## Environment

- Windows 11, bash shell, Python 3.12
- Local testing: `NO_TURSO=1 python -m pytest tests/ -v`
- Current baseline: 182 passed, 1 skipped
