"""Checklist server for local application workflow."""

import http.server
import json
import os
import re
import webbrowser
from datetime import datetime, timezone
from pathlib import Path


def estimate_cl_scrutiny(job: dict) -> int:
    """Estimate how carefully a company will read cover letters (0-10).

    Heuristic based on application source and JD text signals.
    Higher score = CL matters more.
    """
    score = 5  # neutral baseline

    source = (job.get("source") or "").lower()
    description = (job.get("description") or "").lower()

    # Source signals
    if "easy_apply" in source or "linkedin_easy" in source:
        score -= 2
    if source in ("greenhouse", "lever"):
        score += 1
    if "email" in source or "direct" in source:
        score += 2

    # JD text signals
    if re.search(r"motivation\s+letter|cover\s+letter\s+required", description):
        score += 2
    if re.search(r"tell\s+us\s+why|why\s+do\s+you\s+want", description):
        score += 1
    elif re.search(r"cover\s+letter", description):
        score += 1

    return max(0, min(10, score))


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
            "repost_applied_at": job.get("repost_applied_at", ""),
            "rejection_rejected_at": job.get("rejection_rejected_at", ""),
            "seeds": {
                "company_observation": "",
                "personal_why": "",
                "genuine_curiosity": "",
            },
            "cl_scrutiny": estimate_cl_scrutiny(job),
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
        abs_path = str((ready_dir / submit_dir).resolve())
        repost = info.get("repost_applied_at", "")
        repost_badge = f' <span style="color:#dc2626;font-weight:bold" title="Applied {_esc(repost)}">REPOST</span>' if repost else ''
        rejected = info.get("rejection_rejected_at", "")
        rejected_badge = f' <span style="color:#ea580c;font-weight:bold" title="Rejected {_esc(rejected)}">REJECTED</span>' if rejected else ''

        # CL scrutiny badge
        cl_scrutiny = info.get("cl_scrutiny", 5)
        if cl_scrutiny >= 7:
            scrutiny_badge = ' <span class="badge badge-cl-matters">CL MATTERS</span>'
        elif cl_scrutiny <= 3:
            scrutiny_badge = ' <span class="badge badge-cl-opt">CL OPT</span>'
        else:
            scrutiny_badge = ''

        # Seeds
        seeds = info.get("seeds", {})
        co_val = _esc(seeds.get("company_observation", ""))
        pw_val = _esc(seeds.get("personal_why", ""))
        gc_val = _esc(seeds.get("genuine_curiosity", ""))

        esc_id = _esc(job_id)

        rows.append(f"""
        <tr data-job-id="{esc_id}">
          <td><input type="checkbox" class="apply-cb" {'checked' if info['applied'] else ''} /></td>
          <td><span style="color:{score_color};font-weight:bold">{score:.1f}</span>{scrutiny_badge}</td>
          <td>{_esc(info['company'])}{repost_badge}{rejected_badge}</td>
          <td>{_esc(info['title'])}</td>
          <td>
            <button class="btn" data-path="{_esc(abs_path)}" onclick="openFolder(this.dataset.path)">Open Folder</button>
            <button class="btn" data-path="{_esc(abs_path)}" onclick="copyPath(this.dataset.path, this)">Copy Path</button>
            <button class="btn btn-seeds" onclick="toggleSeeds('{esc_id}')">Seeds</button>
          </td>
          <td><a href="{_esc(info['url'])}" target="_blank">Job Link</a></td>
        </tr>
        <tr class="seed-row" id="seeds-{esc_id}" style="display:none">
          <td colspan="6">
            <div class="seed-panel">
              <label>Company observation <small>(what caught your eye)</small></label>
              <textarea data-job-id="{esc_id}" data-field="company_observation">{co_val}</textarea>
              <label>Personal why <small>(why this role matters to you)</small></label>
              <textarea data-job-id="{esc_id}" data-field="personal_why">{pw_val}</textarea>
              <label>Genuine curiosity <small>(a real question about the role/company)</small></label>
              <textarea data-job-id="{esc_id}" data-field="genuine_curiosity">{gc_val}</textarea>
              <button class="btn btn-regen" onclick="regenCL('{esc_id}', this)">Regen CL</button>
            </div>
          </td>
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
  tr.seed-row:hover {{ background: white; }}
  input[type="checkbox"] {{ width: 18px; height: 18px; cursor: pointer; }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .btn {{ padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 4px; background: white; cursor: pointer; font-size: 0.8rem; margin-right: 4px; }}
  .btn:hover {{ background: #f1f5f9; }}
  .btn.copied {{ background: #22c55e; color: white; border-color: #22c55e; }}
  .btn-seeds {{ border-color: #818cf8; color: #4f46e5; }}
  .btn-seeds:hover {{ background: #eef2ff; }}
  .btn-regen {{ padding: 6px 16px; background: #4f46e5; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.85rem; margin-top: 8px; }}
  .btn-regen:hover {{ background: #4338ca; }}
  .btn-regen:disabled {{ background: #94a3b8; cursor: wait; }}
  .btn-regen.regen-ok {{ background: #22c55e; }}
  .btn-regen.regen-fail {{ background: #ef4444; }}
  .badge {{ display: inline-block; font-size: 0.65rem; padding: 1px 6px; border-radius: 3px; margin-left: 6px; vertical-align: middle; font-weight: 600; }}
  .badge-cl-matters {{ background: #fef2f2; color: #dc2626; border: 1px solid #fca5a5; }}
  .badge-cl-opt {{ background: #f9fafb; color: #9ca3af; border: 1px solid #e5e7eb; }}
  .seed-panel {{ padding: 12px 8px; background: #f8fafc; }}
  .seed-panel label {{ display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-top: 8px; margin-bottom: 2px; }}
  .seed-panel label:first-child {{ margin-top: 0; }}
  .seed-panel label small {{ font-weight: 400; color: #94a3b8; }}
  .seed-panel textarea {{ width: 100%; min-height: 48px; padding: 6px 8px; border: 1px solid #e2e8f0; border-radius: 4px; font-family: inherit; font-size: 0.85rem; resize: vertical; box-sizing: border-box; }}
  .seed-panel textarea:focus {{ outline: none; border-color: #818cf8; box-shadow: 0 0 0 2px rgba(129,140,248,0.2); }}
  .summary {{ margin-top: 1rem; color: #475569; }}
</style>
</head>
<body>
<h1>Application Checklist</h1>
<p class="meta">Generated: {generated} | Total: {len(jobs_sorted)} jobs</p>
<table>
  <thead>
    <tr><th></th><th>Score</th><th>Company</th><th>Title</th><th>Actions</th><th>Link</th></tr>
  </thead>
  <tbody>
    {''.join(rows)}
  </tbody>
</table>
<p class="summary" id="summary"></p>

<script>
let state = {json.dumps(state).replace("</", "<\\\\/")};

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
  navigator.clipboard.writeText(path).then(() => {{
    btn.textContent = 'Copied!';
    btn.classList.add('copied');
    setTimeout(() => {{ btn.textContent = 'Copy Path'; btn.classList.remove('copied'); }}, 1500);
  }});
}}

function toggleSeeds(jobId) {{
  const row = document.getElementById('seeds-' + jobId);
  row.style.display = row.style.display === 'none' ? 'table-row' : 'none';
}}

document.querySelectorAll('.seed-panel textarea').forEach(ta => {{
  ta.addEventListener('blur', function() {{
    const jobId = this.dataset.jobId;
    const field = this.dataset.field;
    if (!state.jobs[jobId].seeds) state.jobs[jobId].seeds = {{}};
    state.jobs[jobId].seeds[field] = this.value;
    saveState();
  }});
}});

function regenCL(jobId, btn) {{
  const seeds = state.jobs[jobId].seeds || {{}};
  btn.disabled = true;
  btn.textContent = 'Generating...';
  fetch('/regen-cl', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{job_id: jobId, seeds: seeds}})
  }})
  .then(r => r.json())
  .then(data => {{
    btn.textContent = data.success ? 'Done!' : 'Failed';
    btn.classList.add(data.success ? 'regen-ok' : 'regen-fail');
    setTimeout(() => {{
      btn.disabled = false;
      btn.textContent = 'Regen CL';
      btn.classList.remove('regen-ok', 'regen-fail');
    }}, 3000);
  }})
  .catch(() => {{
    btn.textContent = 'Error';
    setTimeout(() => {{ btn.disabled = false; btn.textContent = 'Regen CL'; }}, 3000);
  }});
}}

updateSummary();

// Restore latest state from state.json (seeds/checkboxes survive page reload)
fetch('/state.json').then(r => r.json()).then(saved => {{
  if (!saved || !saved.jobs) return;
  state = saved;
  document.querySelectorAll('.apply-cb').forEach(cb => {{
    const jobId = cb.closest('tr').dataset.jobId;
    if (state.jobs[jobId]) cb.checked = state.jobs[jobId].applied;
  }});
  document.querySelectorAll('.seed-panel textarea').forEach(ta => {{
    const jobId = ta.dataset.jobId;
    const field = ta.dataset.field;
    const seeds = (state.jobs[jobId] && state.jobs[jobId].seeds) || {{}};
    ta.value = seeds[field] || '';
  }});
  updateSummary();
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
    POST /regen-cl -> regenerate cover letter with seeds

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
                        os.startfile(folder)
                    self.send_response(200)
                except Exception:
                    self.send_response(400)
                self.end_headers()
                return

            if self.path == "/regen-cl":
                try:
                    data = json.loads(body)
                    job_id = data.get("job_id", "")
                    seeds = data.get("seeds", {})

                    if not job_id:
                        self._send_json(400, {"success": False,
                                              "message": "Missing job_id"})
                        return

                    # Build custom_requirements from seeds
                    parts = []
                    if seeds.get("company_observation"):
                        parts.append(
                            f"Company observation: {seeds['company_observation']}")
                    if seeds.get("personal_why"):
                        parts.append(
                            f"Personal motivation: {seeds['personal_why']}")
                    if seeds.get("genuine_curiosity"):
                        parts.append(
                            f"Genuine curiosity: {seeds['genuine_curiosity']}")
                    custom_req = "\n".join(parts) if parts else None

                    # Lazy import to avoid loading AI deps on server start
                    from src.cover_letter_generator import CoverLetterGenerator
                    from src.cover_letter_renderer import CoverLetterRenderer

                    gen = CoverLetterGenerator()
                    result = gen.generate(
                        job_id, custom_requirements=custom_req, force=True)
                    if result:
                        ren = CoverLetterRenderer()
                        ren.render(job_id)
                        self._send_json(200, {
                            "success": True,
                            "message": "Cover letter regenerated"})
                    else:
                        self._send_json(200, {
                            "success": False,
                            "message": "Generation failed — check console"})
                except Exception as e:
                    print(f"  [REGEN ERROR] {e}")
                    self._send_json(500, {
                        "success": False,
                        "message": "Internal error - check server console"})
                return

            self.send_response(404)
            self.end_headers()

        def _send_json(self, code: int, data: dict):
            """Send a JSON response."""
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())

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
