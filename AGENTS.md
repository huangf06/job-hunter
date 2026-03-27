# Job Hunter v2.0 - Agent Guide

## Project Overview

Job Hunter is an automated job hunting pipeline designed for a data/ML engineer job search. The system scrapes job listings from LinkedIn, Greenhouse, and IamExpat through a unified Block A scraper CLI, applies hard filters and rule-based scoring, uses AI (Claude Opus) to analyze high-quality matches, generates tailored resumes and cover letters, and tracks applications through the entire lifecycle.

### Pipeline Flow

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Scrape  │───▶│ Hard Filter  │───▶│ Rule PreScore│───▶│ AI Analyzer  │───▶│   Generate   │
│  (jobs)  │    │  (v2.0)      │    │   (v2.0)     │    │(Claude Opus) │    │Resume+Cover  │
└──────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
                      │                   │                   │
                 rejected            score>=3.0          score>=5.0
```

## Technology Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.11 |
| Database | SQLite (local) + Turso (cloud sync via embedded replica) |
| Web Scraping | Playwright (LinkedIn, IamExpat), REST APIs (Greenhouse) |
| AI/LLM | Anthropic Claude Opus (via codesome.cn proxy), Kimi k2.5 |
| Templating | Jinja2 |
| PDF Generation | Playwright (HTML → PDF) |
| Configuration | YAML |
| CI/CD | GitHub Actions |
| Testing | pytest |

## Project Structure

```
job-hunter/
├── scripts/                    # CLI entry points
│   ├── job_pipeline.py             # Main pipeline (unified CLI)
│   ├── scrape.py                   # Unified scraper CLI entry point
│   ├── job_parser.py               # JD parser utilities
│   ├── google_auth.py              # Google OAuth setup
│   ├── notify.py                   # Telegram notifications
│   └── job_daemon.py               # Priority-based scrape scheduler
│
├── src/                        # Reusable Python modules
│   ├── ai_analyzer.py              # AI analysis and resume tailoring
│   ├── resume_renderer.py          # Jinja2 → HTML → PDF
│   ├── resume_validator.py         # Bullet/bio/skill validation gates
│   ├── cover_letter_generator.py   # AI-powered CL generation
│   ├── cover_letter_renderer.py    # CL HTML/PDF rendering
│   ├── checklist_server.py         # Local HTTP server for application checklist
│   ├── google_calendar.py          # Google Calendar REST client
│   ├── gmail_client.py             # Gmail IMAP client for reading emails
│   ├── interview_scheduler.py      # Smart interview time suggestion
│   ├── db/
│   │   └── job_db.py               # Database operations (SQLite + Turso)
│   └── scrapers/                   # Platform-specific scrapers
│       ├── base.py                 # BaseScraper abstract class
│       ├── greenhouse.py           # Greenhouse ATS API
│       ├── linkedin.py             # LinkedIn orchestration
│       ├── linkedin_browser.py     # LinkedIn browser/session layer
│       ├── linkedin_parser.py      # LinkedIn parsing helpers
│       └── iamexpat.py             # IamExpat Jobs scraper
│
├── config/                     # Configuration files
│   ├── ai_config.yaml          # AI models, thresholds, prompts
│   ├── search_profiles.yaml    # LinkedIn + IamExpat search profiles
│   ├── target_companies.yaml   # ATS target company configurations
│   ├── base/
│   │   ├── filters.yaml        # Hard filter rules (v2.0)
│   │   └── scoring.yaml        # Rule-based scoring weights
│   └── private/                # Private configs (not in git)
│       └── salary.yaml
│
├── assets/                     # Resume content assets
│   ├── bullet_library.yaml     # Verified experience bullets (v3.0, ~50 entries)
│   ├── cover_letter_config.yaml    # CL templates and phrases
│   ├── cl_knowledge_base.yaml  # Cover letter knowledge base
│   └── voice_examples/         # Voice and tone examples
│
├── templates/                  # Jinja2 templates
│   ├── base_template.html      # Main resume template
│   ├── cover_letter_template.html
│   └── resume_master.html      # Reference layout
│
├── data/                       # Runtime data
│   ├── jobs.db                 # SQLite database
│   ├── inbox/                  # Incoming JSON files to import
│   ├── archive/                # Processed files archive
│   └── leads/                  # Scrape output
│
├── output/                     # Generated resumes (PDF)
├── ready_to_send/              # Application materials + checklist
├── interview_prep/             # Interview preparation folders
│   └── YYYYMMDD_Company_Role/  # Per-interview folder with 8-9 files
├── tests/                      # Unit tests
│   └── test_scrapers/
└── .github/workflows/          # CI/CD automation
    └── job-pipeline-optimized.yml
```

## Build and Development Commands

### Environment Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# Set up environment variables (copy and edit)
copy .env.example .env

# Optional: Set up Gmail IMAP for reading interview emails
# See docs/gmail_setup.md for detailed instructions
```

### Daily Workflow Commands

```bash
# 1. Unified scraping
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --profile data_engineering --save-to-db

# 2. Process pipeline (import → filter → score)
python scripts/job_pipeline.py --process

# 3. AI analyze high-scoring jobs
python scripts/job_pipeline.py --ai-analyze --limit 10

# 4. Prepare application materials (resume + CL + checklist server)
python scripts/job_pipeline.py --prepare

# 5. After applying, finalize and archive
python scripts/job_pipeline.py --finalize
```

### Utility Commands

```bash
# View statistics
python scripts/job_pipeline.py --stats

# View ready-to-apply jobs
python scripts/job_pipeline.py --ready

# Mark a job as applied
python scripts/job_pipeline.py --mark-applied JOB_ID

# Analyze single job
python scripts/job_pipeline.py --analyze-job JOB_ID

# Application tracker
python scripts/job_pipeline.py --tracker

# Interview scheduling
python scripts/job_pipeline.py --schedule-interview COMPANY --duration 45

# Google Calendar auth (first time setup)
python scripts/google_auth.py

# Gmail commands
python scripts/job_pipeline.py --test-gmail
python scripts/job_pipeline.py --read-email "FareHarbor"
python scripts/job_pipeline.py --search-emails "interview" --lookback-days 14
```

### Testing

```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_scrapers/test_base.py
```

## Configuration System

### AI Configuration (`config/ai_config.yaml`)

Key sections:
- `models`: Claude Opus and Kimi model configurations with API endpoints
- `thresholds`: Rule score (3.0) and AI score (5.0) thresholds for processing
- `budget`: Daily token limits and cost tracking
- `prompt_settings`: Character limits for resume/JD content in prompts
- `prompts.analyzer`: Main AI analysis prompt with structured JSON output
- `resume`: Template path, PDF settings, candidate info, education details
- `interview_scheduler`: Working hours, peak hours, personal energy profile

### Hard Filters (`config/base/filters.yaml`)

Rules applied in priority order (first match rejects):
1. **Dutch language detection** - Word count-based Dutch JD detection
2. **Dutch required** - Regex patterns for Dutch language requirements
3. **Non-target role** - Title must contain data/ML/AI keywords
4. **Wrong tech stack** - Mobile, frontend, Java/.NET/Ruby roles
5. **Freelance/ZZP only** - Contract-only positions
6. **Low compensation** - Below-market salary indicators
7. **Specific tech experience** - 5+ years Java/C++/Scala/Azure
8. **Experience too high** - 8+ years general experience
9. **Senior management** - Director/VP/Principal/CTO roles
10. **Location restricted** - Onsite-only, no visa sponsorship

### Scoring Configuration (`config/base/scoring.yaml`)

- **Base score**: 3.0 (jobs start here)
- **Title scoring**: Core ML/AI (+2.5), Data Engineering (+2.0), Quant (+2.5)
- **Body scoring**: Python, ML frameworks, Data tools, Cloud/MLOps, NLP/LLM, etc.
- **Target companies**: Tiered bonus system (Tier 1: +2.0, Tier 2: +1.5, Tier 3: +1.0)
- **Thresholds**: APPLY_NOW (≥7.0), APPLY (≥5.5), MAYBE (≥4.0), SKIP (<4.0)

## Database Schema

The database uses SQLite locally with optional Turso cloud synchronization.

| Table | Purpose |
|-------|---------|
| `jobs` | Scraped positions (id, source, url, title, company, location, description, etc.) |
| `filter_results` | Hard filter pass/reject status with matched rules |
| `ai_scores` | Rule-based pre-scores with breakdown |
| `job_analysis` | AI analysis results + tailored resume JSON |
| `resumes` | Generated resume records (HTML/PDF paths) |
| `cover_letters` | Generated cover letter records |
| `applications` | Application status tracking (pending → applied → interview → offer) |

## Code Style Guidelines

### Python Code Style

- **Docstrings**: Use triple quotes with Chinese comments for module-level documentation
- **Type hints**: Use typing module for function signatures (`List[Dict]`, `Optional[str]`, etc.)
- **Naming**: 
  - Classes: `PascalCase` (e.g., `JobPipeline`, `BaseScraper`)
  - Functions/variables: `snake_case` (e.g., `filter_jobs`, `job_id`)
  - Constants: `UPPER_CASE` (e.g., `DB_PATH`, `CONFIG_DIR`)
- **Comments**: Mixed Chinese and English in codebase; prefer Chinese for business logic explanations
- **Path handling**: Use `pathlib.Path` for all file system operations
- **Error handling**: Use try/except blocks with informative error messages

### Configuration Style

- YAML files with hierarchical structure
- Section headers with `====` separator lines
- Chinese comments for business logic
- English keys for programmatic access

## Key Design Decisions

1. **Bullet-by-ID System**: AI outputs bullet IDs, not text. This ensures only verified content from `bullet_library.yaml` appears in resumes.

2. **Bio Builder**: AI outputs a structured spec (title, years, domain claims, closer) that is assembled deterministically.

3. **Validation Gates**: Invalid titles, unknown bullet IDs, or invented skill categories cause hard rejections.

4. **Turso Sync**: Uses embedded replica pattern - local SQLite for speed, cloud sync for CI/CD.

5. **Template-based Rendering**: Jinja2 HTML templates rendered to PDF via Playwright for pixel-perfect control.

6. **Repost Detection**: `--prepare` automatically detects same company+title combinations that were previously applied to.

## Testing Strategy

- **Unit tests**: Located in `tests/` directory, uses pytest
- **Scraper tests**: Mock-based tests for LinkedIn, Greenhouse, and IamExpat scrapers
- **Integration**: CI/CD pipeline tests the full workflow end-to-end
- **Manual testing**: Local checklist server for application workflow validation

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/job-pipeline-optimized.yml`):
- **Schedule**: 3x daily weekdays (08:23, 12:23, 16:23 CET), 1x on weekends
- **Steps**: Unified scrape → Rule scoring → AI analysis → Notify
- **Caching**: Playwright browsers, Turso embedded replica
- **Secrets**: Turso credentials, Anthropic API key, LinkedIn cookies, Telegram tokens

## Security Considerations

- **API Keys**: Stored in `.env` file (never commit)
- **Cookies**: LinkedIn cookies in `config/linkedin_cookies.json` (gitignored)
- **Database**: Local SQLite + encrypted Turso sync
- **Google OAuth**: Tokens stored in `~/.config/google-calendar-mcp/tokens.json`
- **Gmail IMAP**: App password stored in `.env` file (GMAIL_APP_PASSWORD)
- **Private configs**: Salary information in `config/private/` (gitignored)

## Important File Locations

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Detailed Chinese execution guide with all commands |
| `config/linkedin_cookies.json` | LinkedIn authentication cookies |
| `data/jobs.db` | Main SQLite database |
| `~/.config/google-calendar-mcp/tokens.json` | Google Calendar OAuth tokens |
| `~/.config/gcp-oauth.keys.json` | Google OAuth client credentials |
| `docs/gmail_setup.md` | Gmail IMAP setup instructions |
| `ready_to_send/state.json` | Application checklist state |

## Common Issues and Solutions

1. **Windows libsql crash**: Turso embedded replica has a known stack overflow bug on Windows. Unset `TURSO_DATABASE_URL` to use local-only SQLite.

2. **Playwright browser not found**: Run `playwright install chromium --with-deps`

3. **Google Calendar auth expired**: Run `python scripts/google_auth.py` to refresh tokens.

4. **Repost detection false positives**: Check `ready_to_send/state.json` for duplicate entries.

## Interview Preparation Workflow

When user says "帮我准备 [公司] 的面试", trigger the 7-stage interview prep workflow:

1. **Intelligence gathering**: Query Google Calendar + Database
2. **Base files**: Create folder, write JD, AI analysis, submitted resume
3. **Company research**: Website, funding, products, leadership, Glassdoor, GitHub org
4. **Interviewer research**: LinkedIn, publications, career trajectory
5. **Portfolio assembly**: Write company deep-dive, interview strategy, quick reference
6. **Deep research**: GitHub repos (check for take-home assignments), HN, tech blogs
7. **Enrichment + briefing**: Update files, present key findings to user

Output folder: `interview_prep/YYYYMMDD_Company_Role/` with files 00-09.
