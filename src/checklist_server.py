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
            "applied": False,
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
  const realPath = path.replace(/\\\\/g, '\\\\');
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
