# Job Hunter v3.0

Automated job hunting pipeline: scrape jobs, hard-filter by rules, AI evaluate + tailor resumes, render PDFs, track applications.

```
┌──────────┐    ┌──────────────┐    ┌──────────────────────────────┐
│ Block A  │───>│   Block B    │───>│         Block C               │
│  Scrape  │    │ Hard Filter  │    │  C1: Evaluate (score + brief) │
│(LinkedIn,│    │ (10 rules)   │    │  C2: Tailor (resume JSON)     │
│Greenhouse)    └──────────────┘    │  score >= 6.0 triggers C2     │
└──────────┘          │             └──────────────────────────────┘
                 rejected                        │
                      v                          v ai_score >= 6.0
                 ┌─────────┐          ┌──────────────────────────────┐
                 │  SKIP   │          │       Block D                │
                 └─────────┘          │  Resume Renderer (Jinja2)    │
                                      │  Three-tier: USE / ADAPT /   │
                                      │  FULL_CUSTOMIZE              │
                                      │  -> HTML -> PDF              │
                                      └──────────────────────────────┘
                                                 │
                                                 v
                                  ┌──────────────────────────────┐
                                  │  output/Fei_Huang_*.pdf      │
                                  └──────────────────────────────┘
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
# 1. Scrape jobs (LinkedIn + Greenhouse)
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --profile data_engineering --save-to-db

# 2. Process (import + hard filter)
python scripts/job_pipeline.py --process

# 3. AI evaluate + tailor (consumes tokens)
python scripts/job_pipeline.py --ai-evaluate           # C1: score + brief
python scripts/job_pipeline.py --ai-tailor             # C2: resume JSON (score >= 6.0)
python scripts/job_pipeline.py --ai-analyze --limit 10 # C1 + C2 together

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

Say "help me prepare for XX company's interview" to trigger the standardized 7-phase workflow. Generates a full dossier (8-9 files, ~40 KB) in `interview_prep/YYYYMMDD_Company_Role/`.

## Architecture

### Pipeline Blocks

| Block | Name | Purpose |
|-------|------|---------|
| A | Scrape | LinkedIn + Greenhouse ATS scraping |
| B | Hard Filter | 10 binary rules (language, role, tech stack, etc.) |
| C1 | Evaluate | AI scoring (1-10) + application brief |
| C2 | Tailor | Resume customization (bullet selection, bio, skills) |
| D | Render | Jinja2 HTML -> Playwright PDF, three-tier routing |

> Full architecture: `docs/plans/2026-03-27-pipeline-block-architecture.md`

### File Structure

```
scripts/                        # CLI entry points
  job_pipeline.py                   # Main pipeline (unified CLI)
  scrape.py                         # Unified scraper entry point
  google_auth.py                    # Google OAuth (Calendar + Gmail)
  notify.py                         # Telegram notifications (CI/CD)
  notify_discord.py                 # Discord notifications

src/                            # Reusable modules
  hard_filter.py                    # Block B: 10 hard reject rules
  ai_analyzer.py                    # Block C: AI scoring + resume tailoring
  resume_renderer.py                # Block D: Jinja2 -> HTML -> PDF
  resume_validator.py               # Validation gates (title/bullet/skill)
  template_registry.py              # Three-tier template routing
  language_guidance.py              # Resume language tone guidance
  cover_letter_generator.py         # AI cover letter generation
  cover_letter_renderer.py          # CL rendering (HTML -> PDF -> TXT)
  checklist_server.py               # Local application checklist UI
  google_calendar.py                # Google Calendar REST client
  gmail_client.py                   # Gmail IMAP client
  interview_scheduler.py            # Smart interview scheduling (3D scoring)
  scrapers/                         # Multi-platform scrapers
    base.py                             # Abstract base class + ScrapeReport
    registry.py                         # Platform registry and aliases
    greenhouse.py                       # Greenhouse ATS API
    linkedin.py                         # LinkedIn orchestration
    linkedin_browser.py                 # LinkedIn browser/session layer
    linkedin_parser.py                  # LinkedIn parser helpers
    iamexpat.py                         # IamExpat (Playwright, backfill only)
  db/
    job_db.py                       # SQLite + Turso cloud sync

config/
  ai_config.yaml                # AI models, thresholds, prompts, budget
  search_profiles.yaml          # Search profiles (LinkedIn keywords + intervals)
  target_companies.yaml         # Target company ATS endpoints (Greenhouse)
  base/filters.yaml             # Hard filter rules (10 active)

assets/
  bullet_library.yaml           # Verified experience bullets + narrative tags (v5.0)
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
| `job_analysis` | AI scores + tailored resume JSON |
| `resumes` | Generated resume records |
| `cover_letters` | Cover letter records |
| `applications` | Application status tracking |

## Key Design Decisions

- **C1/C2 split**: Evaluate (fast, cheap) runs on all filtered jobs. Tailor (expensive) only runs on score >= 6.0.
- **Three-tier rendering**: USE_TEMPLATE (direct), ADAPT_TEMPLATE (minor edits), FULL_CUSTOMIZE (full rewrite).
- **Bullet-by-ID**: AI outputs bullet IDs from `bullet_library.yaml`, not raw text. Deterministic lookup.
- **Bio Builder**: AI outputs structured spec (title, domain claims, closer). Assembled deterministically.
- **Validation Gates**: Invalid titles, unknown bullet IDs, invented skill categories = hard reject.
- **Application Brief**: Replaces traditional cover letters for most applications.
- **Repost Detection**: `--prepare` auto-detects same company+title already applied, warns in checklist.

## CI/CD

GitHub Actions: `.github/workflows/job-pipeline.yml`
- Weekdays: 2 runs (NL time ~10:37 / ~16:37 CEST)
- Weekends: 1 run (~13:23 CEST)

## Notes

- LinkedIn cookies: `config/linkedin_cookies.json`
- Data files (`*.db`, `*.json`) are gitignored
- AI analysis consumes tokens; budget controlled via `config/ai_config.yaml`
- Google Calendar token: `~/.config/google-calendar-mcp/tokens.json` (shared with MCP)
- First-time Google OAuth: `python scripts/google_auth.py`
- Windows: libsql embedded replica has known stack overflow bug; unset Turso env vars to fall back to local SQLite
