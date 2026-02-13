# Local Pipeline Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the multi-command local workflow with two commands (`--prepare` / `--finalize`) backed by a checklist server with JSON state persistence.

**Architecture:** Add `src/checklist_server.py` for the localhost HTTP server + checklist HTML generation. Add `--prepare` and `--finalize` handlers in `scripts/job_pipeline.py` that orchestrate resume+CL generation, state management, and archival. Add `skipped` to valid application statuses.

**Tech Stack:** Python stdlib (`http.server`, `json`, `webbrowser`, `os`, `shutil`), existing `ResumeRenderer`, `CoverLetterGenerator`, `CoverLetterRenderer`, `JobDatabase`.

---

### Task 1: Cover Letter Template — Remove LinkedIn/GitHub

**Files:**
- Modify: `templates/cover_letter_template.html:90-92`

**Step 1: Edit template**

Remove lines 90-92 (the `<br>` and LinkedIn/GitHub links):

```html
<!-- REMOVE these 3 lines -->
            <br>
            {% if linkedin_display %}<a href="{{ linkedin }}">{{ linkedin_display }}</a>{% endif %}
            {% if github_display %} &middot; <a href="{{ github }}">{{ github_display }}</a>{% endif %}
```

The contact-info div should become:
```html
        <div class="contact-info">
            {{ email }}
            {% if phone %} &middot; {{ phone }}{% endif %}
            {% if location %} &middot; {{ location }}{% endif %}
        </div>
```

**Step 2: Commit**

```bash
git add templates/cover_letter_template.html
git commit -m "fix: remove LinkedIn/GitHub links from cover letter template"
```

---

### Task 2: Add `skipped` to Valid Application Statuses

**Files:**
- Modify: `src/db/job_db.py:986`

**Step 1: Update VALID_STATUSES**

In `update_application_status()` at line 986, add `'skipped'`:

```python
# Before:
VALID_STATUSES = {'pending', 'applied', 'rejected', 'interview', 'offer'}

# After:
VALID_STATUSES = {'pending', 'applied', 'skipped', 'rejected', 'interview', 'offer'}
```

**Step 2: Verify `v_ready_to_apply` view excludes skipped jobs**

Read lines 393-404 in `job_db.py`. The view uses `LEFT JOIN applications a ... WHERE a.id IS NULL`. This means only jobs with NO application record show up. Since `--finalize` creates an application record with status `skipped`, these jobs will automatically be excluded. No view change needed.

**Step 3: Commit**

```bash
git add src/db/job_db.py
git commit -m "feat: add 'skipped' to valid application statuses"
```

---

### Task 3: Create Checklist Server Module

**Files:**
- Create: `src/checklist_server.py`

**Step 1: Write the checklist server module**

This module contains three things:
1. `generate_checklist(jobs, ready_dir)` — writes `state.json` + `apply_checklist.html`
2. `ChecklistHandler` — HTTP request handler (static files + POST /state + POST /open-folder)
3. `start_server(ready_dir, port=8234)` — starts server + opens browser

```python
"""Checklist server for local application workflow."""

import http.server
import json
import os
import webbrowser
from datetime import datetime, timezone
from pathlib import Path


def generate_checklist(jobs: list[dict], ready_dir: Path) -> Path:
    """Write state.json and apply_checklist.html to ready_dir.

    Args:
        jobs: list of dicts with keys: id, title, company, ai_score/score,
              submit_dir, url
        ready_dir: Path to ready_to_send/ directory

    Returns:
        Path to state.json
    """
    ready_dir.mkdir(parents=True, exist_ok=True)

    # Build state
    state = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "jobs": {}
    }
    for job in jobs:
        job_id = job["id"]
        score = job.get("ai_score") or job.get("score", 0)
        state["jobs"][job_id] = {
            "title": job.get("title", ""),
            "company": job.get("company", ""),
            "ai_score": float(score),
            "submit_dir": job.get("submit_dir", ""),
            "url": job.get("url", ""),
            "applied": False,
        }

    state_path = ready_dir / "state.json"
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    # Generate HTML checklist
    html = _build_checklist_html(state, ready_dir)
    checklist_path = ready_dir / "apply_checklist.html"
    checklist_path.write_text(html, encoding="utf-8")

    return state_path


def _build_checklist_html(state: dict, ready_dir: Path) -> str:
    """Build interactive checklist HTML page."""
    jobs_sorted = sorted(
        state["jobs"].items(),
        key=lambda x: x[1]["ai_score"],
        reverse=True,
    )

    rows = []
    for job_id, info in jobs_sorted:
        score = info["ai_score"]
        if score >= 7.0:
            score_color = "#22c55e"
        elif score >= 6.0:
            score_color = "#f59e0b"
        else:
            score_color = "#6b7280"

        submit_dir = info["submit_dir"]
        # Absolute path for open-folder / copy-path
        abs_dir = str((ready_dir / submit_dir).resolve()).replace("\\", "\\\\")

        rows.append(f"""
        <tr data-job-id="{job_id}">
          <td><input type="checkbox" class="apply-cb" {'checked' if info['applied'] else ''} /></td>
          <td style="color:{score_color};font-weight:bold">{score:.1f}</td>
          <td>{_esc(info['company'])}</td>
          <td>{_esc(info['title'])}</td>
          <td>
            <button class="btn" onclick="openFolder('{abs_dir}')">Open Folder</button>
            <button class="btn" onclick="copyPath('{abs_dir}', this)">Copy Path</button>
          </td>
          <td><a href="{_esc(info['url'])}" target="_blank">Job Link</a></td>
        </tr>""")

    generated = state.get("generated_at", "")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Application Checklist</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; background: #f8fafc; }}
  h1 {{ color: #1e293b; margin-bottom: 0.25rem; }}
  .meta {{ color: #64748b; font-size: 0.85rem; margin-bottom: 1.5rem; }}
  table {{ border-collapse: collapse; width: 100%; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th {{ background: #1e293b; color: white; padding: 12px 16px; text-align: left; font-weight: 500; }}
  td {{ padding: 10px 16px; border-bottom: 1px solid #e2e8f0; }}
  tr:hover {{ background: #f1f5f9; }}
  input[type="checkbox"] {{ width: 18px; height: 18px; cursor: pointer; }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .btn {{ padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; cursor: pointer; font-size: 0.8rem; margin-right: 4px; }}
  .btn:hover {{ background: #f1f5f9; }}
  .btn.copied {{ background: #22c55e; color: white; border-color: #22c55e; }}
  .summary {{ margin-top: 1rem; color: #475569; }}
</style>
</head>
<body>
<h1>Application Checklist</h1>
<p class="meta">Generated: {generated} | Total: {len(jobs_sorted)} jobs</p>
<table>
  <thead>
    <tr><th></th><th>Score</th><th>Company</th><th>Title</th><th>Folder</th><th>Link</th></tr>
  </thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>
<p class="summary" id="summary"></p>

<script>
let state = {json.dumps(state)};

function updateSummary() {{
  const checked = Object.values(state.jobs).filter(j => j.applied).length;
  const total = Object.values(state.jobs).length;
  document.getElementById('summary').textContent = checked + ' / ' + total + ' marked as applied';
}}

function saveState() {{
  fetch('/state', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(state)
  }});
}}

document.querySelectorAll('.apply-cb').forEach(cb => {{
  cb.addEventListener('change', function() {{
    const jobId = this.closest('tr').dataset.jobId;
    state.jobs[jobId].applied = this.checked;
    saveState();
    updateSummary();
  }});
}});

function openFolder(path) {{
  fetch('/open-folder', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{folder: path}})
  }});
}}

function copyPath(path, btn) {{
  // Unescape the double-backslashes back to single for clipboard
  const realPath = path.replace(/\\\\\\\\/g, '\\\\');
  navigator.clipboard.writeText(realPath).then(() => {{
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copy Path'; btn.classList.remove('copied'); }}, 1500);
  }});
}}

updateSummary();
</script>
</body>
</html>"""


def _esc(text: str) -> str:
    """HTML-escape a string."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def start_server(ready_dir: Path, port: int = 8234):
    """Start checklist HTTP server and open browser.

    Serves static files from ready_dir.
    POST /state -> writes state.json
    POST /open-folder -> opens Windows Explorer

    Blocks until Ctrl+C.
    """
    state_path = ready_dir / "state.json"

    class ChecklistHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ready_dir), **kwargs)

        def do_POST(self):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            if self.path == "/state":
                state_path.write_bytes(body)
                self.send_response(200)
                self.end_headers()
                return

            if self.path == "/open-folder":
                try:
                    data = json.loads(body)
                    folder = data.get("folder", "")
                    if folder and Path(folder).is_dir():
                        os.startfile(folder)
                    self.send_response(200)
                except Exception:
                    self.send_response(400)
                self.end_headers()
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
            # Suppress request logging noise
            pass

    server = http.server.HTTPServer(("localhost", port), ChecklistHandler)
    url = f"http://localhost:{port}/apply_checklist.html"
    print(f"\nChecklist server running at {url}")
    print("Press Ctrl+C to stop.\n")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("\nServer stopped.")
```

**Step 2: Commit**

```bash
git add src/checklist_server.py
git commit -m "feat: add checklist server module with state.json persistence"
```

---

### Task 4: Add `--prepare` Command

**Files:**
- Modify: `scripts/job_pipeline.py`

**Step 1: Add argparse arguments**

In the argparse setup section (~line 967-1012), add two new arguments:

```python
parser.add_argument('--prepare', action='store_true',
                    help='Generate all application materials and launch checklist')
parser.add_argument('--finalize', action='store_true',
                    help='Archive applied jobs, clean up skipped, sync to cloud')
```

**Step 2: Add import**

At the top imports section (~line 32-52), add:

```python
from src.checklist_server import generate_checklist, start_server
```

**Step 3: Add `cmd_prepare` method to `JobPipeline` class**

Add this method to the `JobPipeline` class (before `generate_resumes`, roughly after line 797):

```python
def cmd_prepare(self, min_ai_score: float = None, limit: int = None):
    """One-command: generate all materials + launch checklist server."""
    from src.cover_letter_generator import CoverLetterGenerator
    from src.cover_letter_renderer import CoverLetterRenderer

    threshold = min_ai_score or self.config.get('thresholds', {}).get(
        'ai_score_generate_resume', 5.0)
    limit = limit or 50

    # Step 1: Sync from Turso
    print("Syncing database...")
    try:
        self.db.sync()
    except Exception as e:
        print(f"Warning: Turso sync failed ({e}), using local data")

    # Step 2: Generate resumes for jobs that need them
    renderer = ResumeRenderer()
    jobs = self.db.get_analyzed_jobs_for_resume(
        min_ai_score=threshold, limit=limit)

    results = {"success": [], "failed": [], "cl_failed": []}

    if jobs:
        print(f"\nGenerating materials for {len(jobs)} jobs...")
        cl_gen = CoverLetterGenerator()
        cl_renderer = CoverLetterRenderer()

        for job in jobs:
            job_id = job['id']
            company = job.get('company', 'Unknown')
            title = job.get('title', 'Unknown')
            label = f"{company} - {title}"

            # Resume
            try:
                resume_result = renderer.render_resume(job_id)
                if not resume_result:
                    results["failed"].append((label, "render returned None"))
                    continue
            except Exception as e:
                results["failed"].append((label, str(e)))
                continue

            results["success"].append(label)

            # Cover letter (non-blocking: resume is saved even if CL fails)
            try:
                cl_spec = cl_gen.generate(job_id)
                if cl_spec:
                    cl_renderer.render(job_id)
            except Exception as e:
                results["cl_failed"].append((label, str(e)))
    else:
        print("No new jobs need resume generation.")

    # Step 3: Collect ALL ready-to-apply jobs (new + existing)
    all_ready = self.db.get_ready_to_apply()

    if not all_ready:
        print("\nNo jobs ready to apply. All caught up!")
        return

    # Step 4: Generate checklist
    ready_dir = Path(PROJECT_ROOT) / "ready_to_send"
    generate_checklist(all_ready, ready_dir)

    # Step 5: Summary report
    print(f"\n{'='*50}")
    print(f"  PREPARE SUMMARY")
    print(f"{'='*50}")
    if results["success"]:
        print(f"  New resumes: {len(results['success'])}")
    if results["failed"]:
        print(f"  Failed:      {len(results['failed'])}")
        for label, err in results["failed"]:
            print(f"    x {label}: {err[:80]}")
    if results["cl_failed"]:
        print(f"  CL warnings: {len(results['cl_failed'])}")
        for label, err in results["cl_failed"]:
            print(f"    ! {label}: {err[:80]}")
    print(f"  Total ready: {len(all_ready)}")
    print(f"{'='*50}\n")

    # Step 6: Start checklist server
    start_server(ready_dir)
```

**Step 4: Add handler in main**

In the main command dispatch section (~line 1040+), add before the existing `elif args.generate:`:

```python
elif args.prepare:
    pipeline.cmd_prepare(min_ai_score=args.min_score, limit=args.limit)
elif args.finalize:
    pipeline.cmd_finalize()
```

**Step 5: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat: add --prepare command for one-click material generation"
```

---

### Task 5: Add `--finalize` Command

**Files:**
- Modify: `scripts/job_pipeline.py`

**Step 1: Add `cmd_finalize` method to `JobPipeline` class**

```python
def cmd_finalize(self):
    """Read checklist state, archive applied jobs, clean up skipped."""
    ready_dir = Path(PROJECT_ROOT) / "ready_to_send"
    state_path = ready_dir / "state.json"

    if not state_path.exists():
        print("No state.json found. Run --prepare first.")
        return

    state = json.loads(state_path.read_text(encoding="utf-8"))
    jobs = state.get("jobs", {})

    if not jobs:
        print("No jobs in state. Nothing to finalize.")
        return

    applied = {jid: j for jid, j in jobs.items() if j.get("applied")}
    skipped = {jid: j for jid, j in jobs.items() if not j.get("applied")}

    applied_dir = ready_dir / "_applied"
    if applied:
        applied_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    # Process applied jobs
    for job_id, info in applied.items():
        self.db.update_application_status(job_id, "applied", applied_at=now)
        src = ready_dir / info["submit_dir"]
        if src.exists() and src.is_dir():
            dest = applied_dir / src.name
            shutil.move(str(src), str(dest))

    # Process skipped jobs
    for job_id, info in skipped.items():
        self.db.update_application_status(job_id, "skipped")
        src = ready_dir / info["submit_dir"]
        if src.exists() and src.is_dir():
            shutil.rmtree(src)

    # Clean up state files
    state_path.unlink(missing_ok=True)
    checklist_path = ready_dir / "apply_checklist.html"
    if checklist_path.exists():
        checklist_path.unlink()

    # Sync to Turso
    print("Syncing to cloud...")
    try:
        self.db.sync()
    except Exception as e:
        print(f"Warning: Turso sync failed ({e}), changes saved locally")

    # Report
    print(f"\n{'='*50}")
    print(f"  FINALIZE SUMMARY")
    print(f"{'='*50}")
    if applied:
        print(f"  Applied ({len(applied)}):")
        for jid, info in applied.items():
            print(f"    -> {info['company']} - {info['title']}")
    if skipped:
        print(f"  Skipped ({len(skipped)}):")
        for jid, info in skipped.items():
            print(f"    -- {info['company']} - {info['title']}")
    print(f"{'='*50}")
```

**Step 2: Add `import shutil` and `from datetime import timezone`**

Check the top of `scripts/job_pipeline.py` — if `shutil` and `timezone` are not already imported, add them. (They likely are already used by `--mark-applied`.)

**Step 3: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat: add --finalize command for checklist-driven archival"
```

---

### Task 6: Integration Test — Manual Smoke Test

**Step 1: Run `--prepare` with no pending jobs**

```bash
python scripts/job_pipeline.py --prepare
```

Expected: "No jobs ready to apply. All caught up!" or checklist opens with existing ready jobs.

**Step 2: Run `--prepare` with pending jobs**

If there are analyzed jobs without resumes, they should be generated. Checklist should open in browser showing all ready jobs with checkboxes, Open Folder, Copy Path, and Job Link.

**Step 3: Test checklist interactions**

- Check a box → verify `state.json` updates (the `applied` field should become `true`)
- Click Open Folder → Windows Explorer opens to the submit directory
- Click Copy Path → path copied to clipboard

**Step 4: Run `--finalize`**

```bash
python scripts/job_pipeline.py --finalize
```

Expected:
- Checked jobs: moved to `_applied/`, DB status = "applied"
- Unchecked jobs: folder deleted, DB status = "skipped"
- `state.json` and `apply_checklist.html` deleted
- Summary printed

**Step 5: Verify old commands still work**

```bash
python scripts/job_pipeline.py --stats
python scripts/job_pipeline.py --tracker
python scripts/job_pipeline.py --ready
```

**Step 6: Final commit**

```bash
git add -A
git commit -m "feat: local pipeline redesign — prepare/finalize workflow"
```

---

Plan complete and saved to `docs/plans/2026-02-13-local-pipeline-impl.md`. Two execution options:

**1. Subagent-Driven (this session)** — I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** — Open new session with executing-plans, batch execution with checkpoints

Which approach?
