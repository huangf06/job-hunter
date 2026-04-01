# Architecture Overview

> **Full pipeline block architecture**: See `docs/plans/2026-03-27-pipeline-block-architecture.md` for the complete design, data flow, DB schema, and rebuild priority.

## Block A: Scraper Layer

Unified scraper entry point with per-platform reporting.

```bash
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --profile data_engineering --save-to-db
python scripts/scrape.py --platform greenhouse --dry-run
```

Organized around a synchronous `BaseScraper.run()` contract that returns a `ScrapeReport`.

- `src/scrapers/base.py`: shared run contract, blacklist filtering, URL-hash dedup, dry-run handling, structured reporting
- `src/scrapers/registry.py`: platform registry and aliases (`ats`, `all`)
- `src/scrapers/greenhouse.py`: Greenhouse board scraper with per-target reporting
- `src/scrapers/iamexpat.py`: IamExpat two-phase listing/detail scraper (backfill only)
- `src/scrapers/linkedin.py`: LinkedIn orchestration
- `src/scrapers/linkedin_browser.py`: LinkedIn browser/session layer
- `src/scrapers/linkedin_parser.py`: LinkedIn parsing helpers

### Diagnostics Model

`ScrapeReport` carries a `diagnostics` object in addition to counts and error lists.

- CLI runtime adds `elapsed_seconds`
- LinkedIn emits structured browser/session diagnostics (`session_status`, `last_stage`, `last_url`, `challenge_marker`, per-query summaries)
- Metrics consumers should prefer `diagnostics` over log scraping when determining scraper health

Operational guidance: `docs/runbooks/block-a-operations.md`

## Block B: Hard Filter

Binary pass/reject rules applied to scraped jobs. Pure CPU, zero AI cost.

```bash
python scripts/job_pipeline.py --filter
python scripts/job_pipeline.py --process   # runs import + filter
```

- `src/hard_filter.py`: `HardFilter` class with `apply(job) -> FilterResult`
- `config/base/filters.yaml`: 10 hard reject rules (Dutch/French/German language, wrong role, wrong tech stack, freelance, low comp, PhD required, senior management)
- Company/title blacklists loaded from `config/search_profiles.yaml`

Rule Score (the old keyword-based scoring step) has been deleted. With flat AI subscription, the "save tokens" gate is unnecessary. Jobs that pass Hard Filter go directly to Block C.

## Block C: AI Analysis (C1 Evaluate + C2 Tailor)

Two-phase AI analysis using Claude.

```bash
python scripts/job_pipeline.py --ai-evaluate   # C1 only
python scripts/job_pipeline.py --ai-tailor     # C2 only (score >= 6.0)
python scripts/job_pipeline.py --ai-analyze    # C1 + C2 together
```

### C1: Evaluate

Runs on all jobs that pass Hard Filter. Produces:
- AI score (1-10)
- Application brief (structured summary for the candidate)
- Recommendation (apply_now / apply / maybe / skip)

### C2: Tailor

Runs only on jobs with `ai_score >= 6.0`. Produces:
- Selected bullet IDs from `assets/bullet_library.yaml`
- Bio spec (title, domain claims, closer)
- Skills categorization
- Resume tier decision (USE_TEMPLATE / ADAPT_TEMPLATE / FULL_CUSTOMIZE)

Key modules:
- `src/ai_analyzer.py`: C1 + C2 prompt construction, response parsing, validation
- `src/resume_validator.py`: Validates C2 output (unknown bullet IDs, invalid titles, invented categories = hard reject)
- `src/language_guidance.py`: Resume language tone guidance injected into prompts

## Block D: Resume Renderer

Converts C2 tailored JSON into PDF resumes.

```bash
python scripts/job_pipeline.py --generate      # render all pending
python scripts/job_pipeline.py --prepare       # render + checklist server
```

Three-tier rendering:
- **USE_TEMPLATE**: Direct template fill, no AI customization needed
- **ADAPT_TEMPLATE**: Minor template adaptations
- **FULL_CUSTOMIZE**: Full AI-driven resume rewrite

Key modules:
- `src/resume_renderer.py`: Jinja2 HTML generation + Playwright PDF rendering
- `src/template_registry.py`: Template selection and tier routing logic
- `templates/base_template.html`: Main Jinja2 template

## Block E/F: Delivery and Notification

Application delivery and status tracking.

```bash
python scripts/job_pipeline.py --prepare       # generate materials + checklist server
python scripts/job_pipeline.py --finalize      # archive applied, clean skipped
python scripts/job_pipeline.py --tracker       # application status board
```

- `src/checklist_server.py`: Local HTTP server for application checklist UI
- `src/cover_letter_generator.py` + `src/cover_letter_renderer.py`: Cover letter generation (when needed)
- Repost detection: `--prepare` auto-detects same company+title already applied

## Compatibility Notes

- `data/scrape_metrics.json` remains the scraper metrics artifact
- Top-level `new_jobs` is preserved for notifications and workflow compatibility
- Job dedup uses `JobDatabase.generate_job_id()` on normalized URLs
