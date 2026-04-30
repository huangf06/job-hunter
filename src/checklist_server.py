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
            "status": "pending",
            "effort": None,
            "repost_applied_at": job.get("repost_applied_at", ""),
            "rejection_rejected_at": job.get("rejection_rejected_at", ""),
            "prev_app_status": job.get("prev_app_status", ""),
            "prev_app_date": job.get("prev_app_date", ""),
        }

    state_path = ready_dir / "state.json"
    state_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

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
        submit_path = Path(submit_dir)
        abs_path = str((submit_path if submit_path.is_absolute() else ready_dir / submit_path.name).resolve())
        repost = info.get("repost_applied_at", "")
        repost_badge = f' <span style="color:#dc2626;font-weight:bold" title="Applied {_esc(repost)}">REPOST</span>' if repost else ''
        rejected = info.get("rejection_rejected_at", "")
        rejected_badge = f' <span style="color:#ea580c;font-weight:bold" title="Rejected {_esc(rejected)}">REJECTED</span>' if rejected else ''
        prev_status = info.get("prev_app_status", "")
        prev_date = info.get("prev_app_date", "")
        prev_badge = ""
        if prev_status and not repost_badge:
            label = prev_status.upper()
            color = "#9333ea" if prev_status == "skipped" else "#ea580c" if prev_status == "rejected" else "#2563eb"
            prev_badge = f' <span style="color:{color};font-weight:bold" title="Previously {label} on {_esc(prev_date)}">PREV:{label}</span>'

        esc_id = _esc(job_id)

        status = info.get("status", "pending")
        effort = info.get("effort") or ""
        rows.append(f"""
        <tr data-job-id="{esc_id}" data-status="{_esc(status)}" data-effort="{_esc(effort)}">
          <td class="effort-cell">
            <button class="ef-btn{' active' if effort == 'focused' else ''}" onclick="toggleEffort(this)">精投</button>
          </td>
          <td class="status-cell">
            <div class="status-toggle">
              <button class="st-btn st-applied{' active' if status == 'applied' else ''}" onclick="setStatus(this, 'applied')">Applied</button>
              <button class="st-btn st-defer{' active' if status == 'deferred' else ''}" onclick="setStatus(this, 'deferred')">Defer</button>
            </div>
          </td>
          <td><span style="color:{score_color};font-weight:bold">{score:.1f}</span></td>
          <td><code class="job-id" onclick="copyJobId(this)" title="Click to copy">{_esc(job_id[:12])}</code></td>
          <td>{_esc(info['company'])}{repost_badge}{rejected_badge}{prev_badge}</td>
          <td>{_esc(info['title'])}</td>
          <td>
            <button class="btn" data-path="{_esc(abs_path)}" onclick="openFolder(this.dataset.path)">Open Folder</button>
            <button class="btn" data-path="{_esc(abs_path)}" onclick="copyPath(this.dataset.path, this)">Copy Path</button>
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
  .status-toggle {{ display: flex; gap: 4px; }}
  .st-btn {{ padding: 3px 8px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; cursor: pointer; font-size: 0.75rem; font-weight: 500; color: #64748b; }}
  .st-btn:hover {{ opacity: 0.85; }}
  .st-btn.st-applied.active {{ background: #22c55e; color: white; border-color: #22c55e; }}
  .st-btn.st-defer.active {{ background: #f59e0b; color: white; border-color: #f59e0b; }}
  tr[data-status="deferred"] {{ background: #fffbeb; }}
  tr[data-status="applied"] {{ background: #f0fdf4; }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .btn {{ padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; cursor: pointer; font-size: 0.8rem; margin-right: 4px; }}
  .btn:hover {{ background: #f1f5f9; }}
  .btn.copied {{ background: #22c55e; color: white; border-color: #22c55e; }}
  .job-id {{ font-size: 0.75rem; color: #64748b; cursor: pointer; padding: 2px 4px; border-radius: 3px; }}
  .job-id:hover {{ background: #e2e8f0; }}
  .job-id.copied {{ background: #22c55e; color: white; }}
  .ef-btn {{ padding: 3px 8px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; cursor: pointer; font-size: 0.75rem; font-weight: 500; color: #64748b; }}
  .ef-btn:hover {{ opacity: 0.85; }}
  .ef-btn.active {{ background: #2563eb; color: white; border-color: #2563eb; }}
  tr[data-effort="focused"] {{ border-left: 4px solid #2563eb; }}
  tr[data-effort="focused"] td:first-child {{ padding-left: 12px; }}
  .summary {{ margin-top: 1rem; color: #475569; }}
</style>
</head>
<body>
<h1>Application Checklist</h1>
<p class="meta">Generated: {generated} | Total: {len(jobs_sorted)} jobs</p>
<table>
  <thead>
    <tr><th></th><th></th><th>Score</th><th>ID</th><th>Company</th><th>Title</th><th>Actions</th><th>Link</th></tr>
  </thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>
<p class="summary" id="summary"></p>

<script>
let state = JSON.parse({json.dumps(json.dumps(state)).replace("</", "<\\\\/")});

// Migrate old boolean 'applied' to 'status' field
Object.entries(state.jobs).forEach(([id, j]) => {{
  if (!j.status) {{
    j.status = j.applied ? 'applied' : 'pending';
    delete j.applied;
  }}
}});

function updateSummary() {{
  const jobs = Object.values(state.jobs);
  const applied = jobs.filter(j => j.status === 'applied').length;
  const deferred = jobs.filter(j => j.status === 'deferred').length;
  const focused = jobs.filter(j => j.effort === 'focused').length;
  const skip = jobs.length - applied - deferred;
  document.getElementById('summary').textContent =
    focused + ' focused, ' + applied + ' applied, ' + deferred + ' deferred, ' + skip + ' skip  (total: ' + jobs.length + ')';
}}

function saveState() {{
  fetch('/state', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(state)
  }}).then(r => {{
    if (!r.ok) showSaveError('Server returned ' + r.status);
  }}).catch(e => showSaveError(e.message));
}}

function showSaveError(msg) {{
  let el = document.getElementById('save-error');
  if (!el) {{
    el = document.createElement('div');
    el.id = 'save-error';
    el.style.cssText = 'position:fixed;top:0;left:0;right:0;padding:10px;background:#dc2626;color:white;text-align:center;font-weight:bold;z-index:9999;';
    document.body.prepend(el);
  }}
  el.textContent = 'Save failed: ' + msg;
  el.style.display = 'block';
  setTimeout(() => {{ el.style.display = 'none'; }}, 5000);
}}

function toggleEffort(btn) {{
  const tr = btn.closest('tr');
  const jobId = tr.dataset.jobId;
  const current = state.jobs[jobId].effort;
  const newEffort = (current === 'focused') ? null : 'focused';
  state.jobs[jobId].effort = newEffort;
  tr.dataset.effort = newEffort || '';
  btn.classList.toggle('active', newEffort === 'focused');
  saveState();
  updateSummary();
  sortTable();
}}

function sortTable() {{
  const tbody = document.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));
  rows.sort((a, b) => {{
    const ae = a.dataset.effort === 'focused' ? 0 : 1;
    const be = b.dataset.effort === 'focused' ? 0 : 1;
    if (ae !== be) return ae - be;
    const as = parseFloat(a.querySelector('td:nth-child(3)').textContent) || 0;
    const bs = parseFloat(b.querySelector('td:nth-child(3)').textContent) || 0;
    return bs - as;
  }});
  rows.forEach(r => tbody.appendChild(r));
}}

function setStatus(btn, status) {{
  const tr = btn.closest('tr');
  const jobId = tr.dataset.jobId;
  const current = state.jobs[jobId].status;
  // Toggle: click active button to deselect (back to pending/skip)
  const newStatus = (current === status) ? 'pending' : status;
  state.jobs[jobId].status = newStatus;
  tr.dataset.status = newStatus;
  // Update button active states
  tr.querySelector('.st-applied').classList.toggle('active', newStatus === 'applied');
  tr.querySelector('.st-defer').classList.toggle('active', newStatus === 'deferred');
  saveState();
  updateSummary();
}}

function openFolder(path) {{
  fetch('/open-folder', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{folder: path}})
  }});
}}

function copyPath(path, btn) {{
  navigator.clipboard.writeText(path).then(() => {{
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copy Path'; btn.classList.remove('copied'); }}, 1500);
  }});
}}

function copyJobId(el) {{
  const jobId = el.closest('tr').dataset.jobId;
  navigator.clipboard.writeText(jobId).then(() => {{
    el.classList.add('copied');
    setTimeout(() => {{ el.classList.remove('copied'); }}, 1000);
  }});
}}

updateSummary();

// Restore latest state from state.json (survives page reload)
fetch('/state.json').then(r => r.json()).then(saved => {{
  if (!saved || !saved.jobs) return;
  state = saved;
  // Migrate old boolean format
  Object.entries(state.jobs).forEach(([id, j]) => {{
    if (!j.status) {{
      j.status = j.applied ? 'applied' : 'pending';
      delete j.applied;
    }}
  }});
  document.querySelectorAll('tr[data-job-id]').forEach(tr => {{
    const jobId = tr.dataset.jobId;
    if (!state.jobs[jobId]) return;
    const s = state.jobs[jobId].status;
    const e = state.jobs[jobId].effort;
    tr.dataset.status = s;
    tr.dataset.effort = e || '';
    tr.querySelector('.st-applied').classList.toggle('active', s === 'applied');
    tr.querySelector('.st-defer').classList.toggle('active', s === 'deferred');
    tr.querySelector('.ef-btn').classList.toggle('active', e === 'focused');
  }});
  updateSummary();
  sortTable();
}}).catch(() => {{}});
</script>
</body>
</html>"""


def _esc(text: str) -> str:
    """HTML-escape a string (covers attribute and text contexts)."""
    return (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&#39;"))



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
            if content_length > 1_000_000:  # 1MB limit
                self.send_error(413, "Request body too large")
                return
            body = self.rfile.read(content_length)

            if self.path == "/state":
                try:
                    data = json.loads(body)
                except (json.JSONDecodeError, ValueError):
                    self.send_response(400)
                    self.end_headers()
                    return
                if not isinstance(data, dict) or "jobs" not in data:
                    self.send_response(400)
                    self.end_headers()
                    return
                tmp = state_path.with_suffix(".tmp")
                tmp.write_bytes(body)
                tmp.replace(state_path)  # atomic on both POSIX & Windows
                self.send_response(200)
                self.end_headers()
                return

            if self.path == "/open-folder":
                try:
                    data = json.loads(body)
                    folder = data.get("folder", "")
                    folder_path = Path(folder).resolve()
                    # Only allow opening directories within ready_dir
                    if (folder and folder_path.is_dir()
                            and folder_path.is_relative_to(ready_dir.resolve())):
                        os.startfile(str(folder_path))
                    self.send_response(200)
                except Exception:
                    self.send_response(400)
                self.end_headers()
                return

            self.send_response(404)
            self.end_headers()

        def log_message(self, format, *args):
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
