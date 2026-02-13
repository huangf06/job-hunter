# Job Hunter v2.0

Automated job hunting pipeline: scrape LinkedIn → hard filter → rule score → AI analysis (Claude) → tailored resume generation → application tracking.

```
Scrape ──▶ Hard Filter ──▶ Rule Score ──▶ AI Analyze ──▶ Render Resume ──▶ Track
              │                              (Claude Opus)    (Jinja2+PDF)
           rejected                          + Cover Letter
```

## Quick Start

```bash
pip install -r requirements.txt
playwright install chromium
```

Set up `.env` (see `.env.example`):
```
ANTHROPIC_API_KEY=sk-...
TURSO_DATABASE_URL=libsql://...
TURSO_AUTH_TOKEN=...
```

## Daily Workflow

```bash
# 1. Scrape jobs
python scripts/linkedin_scraper_v6.py --profile ml_data --save-to-db --cdp

# 2. Process (import → filter → rule score)
python scripts/job_pipeline.py --process

# 3. AI analyze top candidates
python scripts/job_pipeline.py --ai-analyze

# 4. Generate tailored resumes + cover letters
python scripts/job_pipeline.py --generate

# 5. Check what's ready to apply
python scripts/job_pipeline.py --ready
```

### Local Application Workflow

```bash
# Prepare: generates resume/cover letter, opens checklist server
python scripts/job_pipeline.py --prepare JOB_ID

# Finalize: marks applied, stops server, moves files to ready_to_send/
python scripts/job_pipeline.py --finalize JOB_ID
```

## Architecture

```
scripts/                    # CLI entry points
  job_pipeline.py               # Main pipeline (unified CLI)
  linkedin_scraper_v6.py        # LinkedIn scraper
  job_parser.py                 # JD parser

src/                        # Reusable modules
  ai_analyzer.py                # AI scoring + resume tailoring (Claude Opus)
  resume_renderer.py            # Jinja2 → HTML → PDF
  resume_validator.py           # Bullet/bio/skill validation gates
  checklist_server.py           # Local application checklist UI
  db/job_db.py                  # SQLite + Turso cloud sync

config/
  ai_config.yaml            # AI model, thresholds, prompts
  search_profiles.yaml      # LinkedIn search profiles
  base/filters.yaml         # Hard filter rules
  base/scoring.yaml         # Rule-based scoring weights

assets/
  bullet_library.yaml       # Verified experience bullets, skills, bio builder
  cover_letter_config.yaml  # Cover letter templates

templates/
  base_template.html        # Resume template (Jinja2)
  cover_letter_template.html
  resume_master.html        # Reference layout
```

## Database

SQLite locally, synced to Turso cloud for CI/CD.

| Table | Purpose |
|-------|---------|
| `jobs` | All scraped positions |
| `filter_results` | Hard filter pass/reject |
| `ai_scores` | Rule-based pre-scores |
| `job_analysis` | AI scores + tailored resume JSON |
| `resumes` | Generated resume records |
| `cover_letters` | Generated cover letter records |
| `applications` | Application status tracking |

## Key Design Decisions (v2.0)

- **Bullet-by-ID**: AI outputs bullet IDs, not text. Deterministic lookup from `bullet_library.yaml`.
- **Bio Builder**: AI outputs structured spec (title, domain claims, closer). Assembled deterministically.
- **Validation Gates**: Invalid titles, unknown bullet IDs, invented skill categories = hard reject.
- **Turso Sync**: Embedded replica pattern. Local SQLite for speed, cloud sync for CI/CD.

## CI/CD

GitHub Actions runs the full pipeline on schedule (`.github/workflows/job-pipeline.yml`).

## Notes

- LinkedIn cookies: `config/linkedin_cookies.json`
- Data files (`*.db`, `*.json`) are gitignored
- AI analysis consumes tokens; budget controlled via `config/ai_config.yaml`
- Legacy code archived in `archive/`
