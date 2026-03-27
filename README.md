# Job Hunter v2.0

Automated job hunting pipeline: unified scrape → hard filter → rule score → AI analysis (Claude Opus) → tailored resume + cover letter → application tracking + interview prep.

```
Scrape ──▶ Hard Filter ──▶ Rule Score ──▶ AI Analyze ──▶ Render Resume ──▶ Track
(LinkedIn,     │                          (Claude Opus)   (Jinja2 + PDF)   (checklist
 Greenhouse,  rejected                    + Cover Letter                    + calendar)
 IamExpat)
```

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
```

Set up `.env`:
```
ANTHROPIC_API_KEY=sk-...
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...
```

## Daily Workflow

```bash
# 1. Scrape jobs (default daily path: LinkedIn + Greenhouse)
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --profile data_engineering --save-to-db

# Optional low-frequency backfill
python scripts/scrape.py --platform iamexpat --save-to-db

# 2. Process (import → filter → rule score)
python scripts/job_pipeline.py --process

# 3. AI analyze top candidates (consumes tokens)
python scripts/job_pipeline.py --ai-analyze --limit 10

# 4. Prepare applications (generate resume/CL + checklist server)
python scripts/job_pipeline.py --prepare

# 5. After applying, archive
python scripts/job_pipeline.py --finalize
```

### Interview Scheduling

```bash
# Smart slot recommendation (calendar + AI scores + 3D scoring model)
python scripts/job_pipeline.py --schedule-interview COMPANY --duration 45

# List all available slots
python scripts/job_pipeline.py --suggest-availability COMPANY --duration 30
```

### Interview Prep

Say "帮我准备 XX 公司的面试" to trigger the standardized 7-phase workflow. Generates a full dossier (8-9 files, ~40 KB) in `interview_prep/YYYYMMDD_Company_Role/`.

## Architecture

```
scripts/                        # CLI entry points
  job_pipeline.py                   # Main pipeline (unified CLI)
  scrape.py                         # Unified scraper entry point
  google_auth.py                    # Google OAuth (Calendar + Gmail)
  job_parser.py                     # JD text parser
  notify.py                         # Telegram notifications (CI/CD)
  notify_discord.py                 # Discord notifications
  svg_auto_optimizer.py             # SVG resume auto-optimizer (Vision API)
  generate_svg_preview.py           # SVG → PNG preview
  svg_to_pdf.py                     # SVG → PDF

src/                            # Reusable modules
  ai_analyzer.py                    # AI scoring + resume tailoring (Claude Opus)
  resume_renderer.py                # Jinja2 → HTML → PDF
  resume_validator.py               # Validation gates (title/bullet/skill/category)
  cover_letter_generator.py         # AI cover letter generation
  cover_letter_renderer.py          # CL rendering (HTML → PDF → TXT)
  checklist_server.py               # Local application checklist UI
  google_calendar.py                # Google Calendar REST client
  gmail_client.py                   # Gmail IMAP client
  interview_scheduler.py            # Smart interview scheduling (3D scoring)
  scrapers/                         # Multi-platform scrapers
    base.py                             # Abstract base class
    greenhouse.py                       # Greenhouse ATS API
    linkedin.py                         # LinkedIn orchestration
    linkedin_browser.py                 # LinkedIn browser/session layer
    linkedin_parser.py                  # LinkedIn parser helpers
    iamexpat.py                         # IamExpat (Playwright)
  db/
    job_db.py                       # SQLite + Turso cloud sync

config/
  ai_config.yaml                # AI models, thresholds, prompts, budget
  search_profiles.yaml          # Search profiles (LinkedIn + IamExpat)
  target_companies.yaml         # Target company ATS endpoints
  base/filters.yaml             # Hard filter rules
  base/scoring.yaml             # Rule-based scoring weights

assets/
  bullet_library.yaml           # 50 verified experience bullets + skills + bio builder
  cover_letter_config.yaml      # CL tone, structure, anti-AI rules
  cl_knowledge_base.yaml        # Hand-written CL fragments

templates/
  base_template.html            # Resume template (Jinja2)
  cover_letter_template.html    # Cover letter template
  resume_master.html            # Reference layout

interview_prep/                 # Interview dossiers (per company)
  YYYYMMDD_Company_Role/            # 00-09 standardized files
```

## Database

SQLite locally, synced to Turso cloud for CI/CD (embedded replica pattern).

| Table | Purpose |
|-------|---------|
| `jobs` | All scraped positions |
| `filter_results` | Hard filter pass/reject |
| `ai_scores` | Rule-based pre-scores |
| `job_analysis` | AI scores + tailored resume JSON |
| `resumes` | Generated resume records |
| `cover_letters` | Cover letter records |
| `applications` | Application status tracking |

## Key Design Decisions (v2.0)

- **Bullet-by-ID**: AI outputs bullet IDs, not text. Deterministic lookup from `bullet_library.yaml`.
- **Bio Builder**: AI outputs structured spec (title, domain claims, closer). Assembled deterministically.
- **Validation Gates**: Invalid titles, unknown bullet IDs, invented skill categories = hard reject.
- **Turso Sync**: Embedded replica pattern. Local SQLite for speed, cloud sync for CI/CD.
- **Repost Detection**: `--prepare` auto-detects same company+title already applied, warns in checklist.

## CI/CD

GitHub Actions runs the main pipeline for LinkedIn + Greenhouse on the regular schedule. IamExpat is retained as a separate low-frequency backfill source. See `.github/workflows/job-pipeline-optimized.yml`.

## Notes

- LinkedIn cookies: `config/linkedin_cookies.json`
- Data files (`*.db`, `*.json`) are gitignored
- AI analysis consumes tokens; budget controlled via `config/ai_config.yaml`
- Google Calendar token: `~/.config/google-calendar-mcp/tokens.json` (shared with MCP)
- First-time Google OAuth: `python scripts/google_auth.py`
- Windows: libsql embedded replica has known stack overflow bug; unset Turso env vars to fall back to local SQLite
