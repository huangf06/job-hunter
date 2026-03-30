# Block E+F Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Audit-and-refine Block E (Deliver) and Block F (Notify) — fix XSS, remove dead code, add generate stats to notifications, add state.json validation.

**Architecture:** No architectural changes. Six targeted fixes to existing files, plus tests for the three non-trivial changes.

**Tech Stack:** Python 3.12, pytest, json, Jinja2 HTML templates

---

### Task 1: Delete `scripts/notify_discord.py` (EF-1)

**Files:**
- Delete: `scripts/notify_discord.py`

**Step 1: Verify no references exist**

Run: `grep -r notify_discord scripts/ src/ tests/ .github/ --include="*.py" --include="*.yml"`
Expected: No output (zero references)

**Step 2: Delete the file**

```bash
git rm scripts/notify_discord.py
```

**Step 3: Commit**

```bash
git commit -m "refactor(block-ef): delete unused notify_discord.py (EF-1)"
```

---

### Task 2: Fix XSS in `src/checklist_server.py` (EF-2)

**Files:**
- Modify: `src/checklist_server.py:130`
- Test: `tests/test_checklist_server.py` (create)

**Step 1: Write the failing test**

Create `tests/test_checklist_server.py`:

```python
"""Tests for checklist_server (Block E+F audit)."""
import json
from pathlib import Path

from src.checklist_server import generate_checklist


def test_xss_in_job_title_is_escaped(tmp_path):
    """EF-2: Job titles with </script> must not break the HTML page."""
    jobs = [
        {
            "id": "xss-test-1",
            "title": '</script><img onerror="alert(1)">',
            "company": "Evil Corp",
            "score": 7.0,
            "submit_dir": str(tmp_path / "xss-test-1"),
            "url": "https://example.com",
        }
    ]
    (tmp_path / "xss-test-1").mkdir()

    generate_checklist(jobs, tmp_path)

    html = (tmp_path / "apply_checklist.html").read_text(encoding="utf-8")

    # The raw </script> must NOT appear in script context
    # It should be safely encoded inside a JSON string
    script_sections = html.split("<script>")
    assert len(script_sections) == 2, "Expected exactly one <script> block"
    script_body = script_sections[1].split("</script>")[0]
    assert "</script>" not in script_body.replace("</script>", ""), (
        "Raw </script> found inside <script> block"
    )

    # The state should still be valid — parse it back
    state_json = (tmp_path / "state.json").read_text(encoding="utf-8")
    state = json.loads(state_json)
    assert state["jobs"]["xss-test-1"]["title"] == '</script><img onerror="alert(1)">'
```

**Step 2: Run test to verify it fails**

Run: `NO_TURSO=1 python -m pytest tests/test_checklist_server.py::test_xss_in_job_title_is_escaped -v`
Expected: FAIL (raw `</script>` appears in script block)

**Step 3: Fix the XSS**

In `src/checklist_server.py`, change line 130 from:

```python
let state = {json.dumps(state).replace("</", "<\\\\/")};
```

to:

```python
let state = JSON.parse({json.dumps(json.dumps(state))});
```

The inner `json.dumps(state)` serializes the dict to a JSON string. The outer `json.dumps(...)` wraps it in a proper JS string literal with all quotes and special chars escaped. `JSON.parse()` on the JS side recovers the original object. This is the standard safe pattern — no manual escaping needed.

**Step 4: Run test to verify it passes**

Run: `NO_TURSO=1 python -m pytest tests/test_checklist_server.py::test_xss_in_job_title_is_escaped -v`
Expected: PASS

**Step 5: Run full test suite to verify no regression**

Run: `NO_TURSO=1 python -m pytest tests/ -v`
Expected: All pass (182+ passed)

**Step 6: Commit**

```bash
git add src/checklist_server.py tests/test_checklist_server.py
git commit -m "fix(block-ef): escape JSON in checklist script tag to prevent XSS (EF-2)"
```

---

### Task 3: Remove dead `_send_json()` method (EF-3)

**Files:**
- Modify: `src/checklist_server.py:249-254`

**Step 1: Delete lines 249-254**

Remove this method from `ChecklistHandler`:

```python
        def _send_json(self, code: int, data: dict):
            """Send a JSON response."""
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
```

**Step 2: Run tests**

Run: `NO_TURSO=1 python -m pytest tests/ -v`
Expected: All pass

**Step 3: Commit**

```bash
git add src/checklist_server.py
git commit -m "refactor(block-ef): remove unused _send_json() method (EF-3)"
```

---

### Task 4: Remove redundant `get_funnel_stats()` call in `scripts/notify.py` (EF-4)

**Files:**
- Modify: `scripts/notify.py:59-63`

**Step 1: Delete the dead code**

Remove lines 59-63 (the comment + call + three extractions):

```python
        # Application status counts
        funnel = db.get_funnel_stats()
        stats["applied"] = funnel.get("applied", 0)
        stats["interview"] = funnel.get("interview", 0)
        stats["rejected"] = funnel.get("rejected", 0)
```

Keep the blank line before `# Get proper counts from applications table` (line 65).

**Step 2: Run tests**

Run: `NO_TURSO=1 python -m pytest tests/ -v`
Expected: All pass

**Step 3: Commit**

```bash
git add scripts/notify.py
git commit -m "refactor(block-ef): remove redundant get_funnel_stats() call in notify.py (EF-4)"
```

---

### Task 5: Add generate step visibility to `scripts/notify.py` (EF-5)

**Files:**
- Modify: `scripts/notify.py` (get_db_stats + format_message)
- Test: `tests/test_notify.py` (create)

**Step 1: Write the failing test**

Create `tests/test_notify.py`:

```python
"""Tests for notify.py (Block E+F audit)."""
from scripts.notify import format_message


def test_generate_count_in_success_message():
    """EF-5: Today's resume generation count should appear in notification."""
    db_stats = {
        "ready": [{"id": "j1", "score": 7.0, "title": "DE", "company": "Acme"}],
        "today_analyzed": 3,
        "today_high_score": 2,
        "today_tokens": 500,
        "today_new_ready": [],
        "today_generated": 4,
        "applied": 10,
        "interview": 2,
        "rejected": 5,
        "total_ready": 1,
    }
    scrape = {"new_jobs": 5}

    msg = format_message("success", scrape=scrape, db_stats=db_stats)
    assert "4 resumes" in msg or "4 generated" in msg, (
        f"Expected generate count in message, got:\n{msg}"
    )


def test_generate_count_zero_omitted():
    """EF-5: When no resumes generated, don't show generate line."""
    db_stats = {
        "ready": [],
        "today_analyzed": 1,
        "today_high_score": 0,
        "today_tokens": 100,
        "today_new_ready": [],
        "today_generated": 0,
        "applied": 0,
        "interview": 0,
        "rejected": 0,
        "total_ready": 0,
    }
    scrape = {"new_jobs": 2}

    msg = format_message("success", scrape=scrape, db_stats=db_stats)
    assert "generated" not in msg.lower() and "resumes" not in msg.lower(), (
        f"Generate count should be omitted when 0, got:\n{msg}"
    )
```

**Step 2: Run test to verify it fails**

Run: `NO_TURSO=1 python -m pytest tests/test_notify.py -v`
Expected: FAIL (`today_generated` not used in format_message yet)

**Step 3: Add today_generated query to get_db_stats()**

In `scripts/notify.py`, inside `get_db_stats()`, after the `today_ready` query block (around line 120), add:

```python
            # Today's resume generation count
            today_gen = conn.execute("""
                SELECT COUNT(*) as cnt
                FROM resumes
                WHERE DATE(generated_at) = DATE('now')
            """).fetchone()
            stats["today_generated"] = today_gen["cnt"] if today_gen else 0
```

Also add `"today_generated": 0` to the stats dict initialization (around line 40).

**Step 4: Add generate line to format_message()**

In `scripts/notify.py`, in `format_message()`, after extracting existing stats (around line 155), add:

```python
    today_generated = db.get("today_generated", 0)
```

Then after the token usage block (around line 190, after the `lines.append(f"Tokens: ...")` section), add:

```python
    # Resume generation
    if today_generated > 0:
        lines.append(f"Generated: {today_generated} resumes")
```

**Step 5: Run test to verify it passes**

Run: `NO_TURSO=1 python -m pytest tests/test_notify.py -v`
Expected: PASS

**Step 6: Run full test suite**

Run: `NO_TURSO=1 python -m pytest tests/ -v`
Expected: All pass

**Step 7: Commit**

```bash
git add scripts/notify.py tests/test_notify.py
git commit -m "feat(block-ef): add resume generation count to Telegram notification (EF-5)"
```

---

### Task 6: Add state.json schema validation in `cmd_finalize()` (EF-7)

**Files:**
- Modify: `scripts/job_pipeline.py:510-515`
- Test: `tests/test_checklist_server.py` (append)

**Step 1: Write the failing test**

Append to `tests/test_checklist_server.py`:

```python
import pytest
from unittest.mock import patch, MagicMock


def test_finalize_rejects_malformed_state_json(tmp_path):
    """EF-7: cmd_finalize should raise clear error on malformed state.json."""
    from scripts.job_pipeline import JobPipeline

    # Create a malformed state.json (missing 'jobs' key)
    state_path = tmp_path / "state.json"
    state_path.write_text('{"bad": "data"}', encoding="utf-8")

    with patch.object(JobPipeline, '__init__', lambda self: None):
        pipeline = JobPipeline()
        pipeline.db = MagicMock()

        with patch("scripts.job_pipeline.PROJECT_ROOT", str(tmp_path)):
            # Create ready_to_send dir with state.json
            ready_dir = tmp_path / "ready_to_send"
            ready_dir.mkdir()
            (ready_dir / "state.json").write_text('{"bad": "data"}', encoding="utf-8")

            with pytest.raises(SystemExit):
                pipeline.cmd_finalize()


def test_finalize_rejects_jobs_missing_required_keys(tmp_path):
    """EF-7: Jobs in state.json must have applied, submit_dir, company, title."""
    import json
    from scripts.job_pipeline import JobPipeline

    state = {
        "generated_at": "2026-03-30T00:00:00",
        "jobs": {
            "job-1": {"applied": True}  # missing submit_dir, company, title
        }
    }

    with patch.object(JobPipeline, '__init__', lambda self: None):
        pipeline = JobPipeline()
        pipeline.db = MagicMock()

        with patch("scripts.job_pipeline.PROJECT_ROOT", str(tmp_path)):
            ready_dir = tmp_path / "ready_to_send"
            ready_dir.mkdir()
            (ready_dir / "state.json").write_text(
                json.dumps(state), encoding="utf-8"
            )

            with pytest.raises(SystemExit):
                pipeline.cmd_finalize()
```

**Step 2: Run tests to verify they fail**

Run: `NO_TURSO=1 python -m pytest tests/test_checklist_server.py::test_finalize_rejects_malformed_state_json tests/test_checklist_server.py::test_finalize_rejects_jobs_missing_required_keys -v`
Expected: FAIL (no validation exists yet)

**Step 3: Add validation to cmd_finalize()**

In `scripts/job_pipeline.py`, after line 510 (`state = json.loads(...)`), replace the existing block:

```python
        state = json.loads(state_path.read_text(encoding="utf-8"))
        jobs = state.get("jobs", {})

        if not jobs:
            print("No jobs in state. Nothing to finalize.")
            return
```

with:

```python
        state = json.loads(state_path.read_text(encoding="utf-8"))

        # Validate state.json schema (EF-7)
        if not isinstance(state, dict) or "jobs" not in state:
            print("Error: state.json is malformed (missing 'jobs' key). "
                  "Re-run --prepare to regenerate.")
            sys.exit(1)

        jobs = state["jobs"]
        if not isinstance(jobs, dict):
            print("Error: state.json 'jobs' is not a dict. "
                  "Re-run --prepare to regenerate.")
            sys.exit(1)

        required_keys = {"applied", "submit_dir", "company", "title"}
        for jid, info in jobs.items():
            missing = required_keys - set(info.keys())
            if missing:
                print(f"Error: state.json job '{jid}' missing keys: {missing}. "
                      "Re-run --prepare to regenerate.")
                sys.exit(1)

        if not jobs:
            print("No jobs in state. Nothing to finalize.")
            return
```

**Step 4: Run tests to verify they pass**

Run: `NO_TURSO=1 python -m pytest tests/test_checklist_server.py -v`
Expected: PASS

**Step 5: Run full test suite**

Run: `NO_TURSO=1 python -m pytest tests/ -v`
Expected: All pass

**Step 6: Commit**

```bash
git add scripts/job_pipeline.py tests/test_checklist_server.py
git commit -m "fix(block-ef): add state.json schema validation in cmd_finalize (EF-7)"
```

---

### Task 7: Final verification

**Step 1: Run full test suite**

Run: `NO_TURSO=1 python -m pytest tests/ -v`
Expected: All pass (182 + new tests)

**Step 2: Verify no unintended changes**

Run: `git diff HEAD~6 --stat`
Expected: See exactly these files changed:
- `scripts/notify_discord.py` (deleted)
- `src/checklist_server.py` (XSS fix + dead method removed)
- `scripts/notify.py` (dead code removed + generate stats added)
- `scripts/job_pipeline.py` (state.json validation)
- `tests/test_checklist_server.py` (new)
- `tests/test_notify.py` (new)

**Step 3: Verify design doc is up to date**

Run: `git diff docs/plans/2026-03-30-block-ef-design.md`
Expected: EF-6 marked as dropped
