# Local Pipeline Redesign

**Date**: 2026-02-13
**Scope**: Local execution only (CI unchanged)

## Problem

The local pipeline requires running 4-5 separate commands (`--generate`, `--ready`, `--cover-letters`, `--mark-applied`, etc.), with unclear state between steps, fragile error recovery, and cover letter generation split from resume generation.

## Solution: Two-Command Flow

### Command 1: `--prepare`

One command to generate all application materials and launch an interactive checklist.

**Flow**:
1. Sync from Turso (pull latest AI analysis results)
2. Query jobs needing resume generation:
   - `ai_score >= 5.0`
   - `tailored_resume != '{}'`
   - No valid PDF yet
   - Not already applied
3. For each job (atomic, independent):
   - Generate Resume PDF
   - Generate Cover Letter PDF
   - Copy both to `ready_to_send/{date}_{company}/`
   - On failure: log error, continue to next job
4. Collect ALL ready-to-apply jobs (new + previously generated)
5. Write `ready_to_send/state.json` + `ready_to_send/apply_checklist.html`
6. Print summary report (success count, failure count with reasons, total ready)
7. Start localhost:8234 HTTP server + open checklist in browser

**Idempotency**: Safe to run multiple times. Jobs with existing valid PDFs are excluded by the DB query.

### Checklist Server (localhost:8234)

Minimal HTTP server (~30 lines) with two responsibilities:
- Serve static files from `ready_to_send/`
- POST `/state` endpoint: write request body to `state.json`
- POST `/open-folder` endpoint: call `os.startfile(folder_path)` to open Windows Explorer

The checklist HTML page:
- Loads `state.json` on page load
- Each job row: `[checkbox] Company - Title (score) [Open Folder] [Copy Path] [Job Link]`
- Checkbox changes trigger `fetch('/state', {method: 'POST', body: updated_json})`
- Open Folder button triggers `fetch('/open-folder', {method: 'POST', body: {folder: path}})`
- Copy Path button uses `navigator.clipboard.writeText(path)`

Server runs in foreground. User presses Ctrl+C when done.

### state.json Format

```json
{
  "generated_at": "2026-02-13T10:30:00",
  "jobs": {
    "abc123def456": {
      "title": "Data Engineer",
      "company": "Google",
      "ai_score": 7.5,
      "submit_dir": "20260213_Google",
      "url": "https://linkedin.com/jobs/view/...",
      "applied": false
    }
  }
}
```

### Command 2: `--finalize`

Read checklist state and batch-process all jobs.

**Flow**:
1. Read `ready_to_send/state.json`
2. For each job:
   - `applied: true` -> DB mark "applied" + move folder to `_applied/`
   - `applied: false` -> DB mark "skipped" + delete folder
3. Clean up: delete `state.json` and `apply_checklist.html`
4. Sync to Turso (push changes to cloud)
5. Print archive report

**Result**: `ready_to_send/` is clean after finalize. Only `_applied/` subdirectory remains with archived materials.

### File Structure After Operations

```
ready_to_send/
├── state.json                      # deleted by --finalize
├── apply_checklist.html            # deleted by --finalize
├── 20260213_Google/                # pending job (deleted or archived by --finalize)
│   ├── Fei_Huang_Resume.pdf
│   └── Fei_Huang_Cover_Letter.pdf
└── _applied/                       # permanent archive
    └── 20260213_Stripe/
        ├── Fei_Huang_Resume.pdf
        └── Fei_Huang_Cover_Letter.pdf
```

## Cover Letter Template Change

Remove LinkedIn and GitHub links from `templates/cover_letter_template.html`.

Before:
```html
<div class="contact-info">
    {{ email }}
    {% if phone %} &middot; {{ phone }}{% endif %}
    {% if location %} &middot; {{ location }}{% endif %}
    <br>
    {% if linkedin_display %}<a href="{{ linkedin }}">{{ linkedin_display }}</a>{% endif %}
    {% if github_display %} &middot; <a href="{{ github }}">{{ github_display }}</a>{% endif %}
</div>
```

After:
```html
<div class="contact-info">
    {{ email }}
    {% if phone %} &middot; {{ phone }}{% endif %}
    {% if location %} &middot; {{ location }}{% endif %}
</div>
```

## Existing Commands

All existing commands (`--stats`, `--tracker`, `--ready`, `--mark-applied JOB_ID`, `--generate`, `--cover-letters`, etc.) are preserved as-is. They serve as escape hatches for edge cases.

## Error Handling

| Scenario | Behavior |
|---|---|
| Single job resume generation fails | Log error, skip, continue. Summary shows failure reason. |
| Single job cover letter fails | Resume still saved. CL skipped. Summary shows warning. |
| Turso sync fails on --prepare | Use local data, log warning (not fatal) |
| Turso sync fails on --finalize | Local DB updated, warn user to retry sync |
| state.json missing on --finalize | Error message: "Run --prepare first" |
| No jobs checked on --finalize | All jobs marked skipped, all folders deleted, clean state |
| PDF renderer (Playwright) unavailable | HTML saved, PDF path empty. Summary shows warning. |
| --prepare run twice | Idempotent. Already-generated jobs excluded by DB query. Checklist regenerated with all ready jobs. |

## Daily Workflow

```bash
# 1. Generate materials + open checklist
python scripts/job_pipeline.py --prepare

# 2. Browse checklist, open folders, submit applications, check boxes
#    (Ctrl+C to stop server when done)

# 3. Archive applied, clean up skipped
python scripts/job_pipeline.py --finalize
```
