# Job Hunter v3.0 Refactor — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refactor job-hunter into a data-driven, streaming system with optimized search keywords, SVG template resumes, and decoupled cover letter generation.

**Architecture:** Four independent workstreams: (1) config-driven search optimization, (2) CL decoupling from pipeline, (3) streaming daemon with Single HWM incremental scraping, (4) SVG template resumes with AI routing. Each workstream is independently deployable.

**Tech Stack:** Python 3.11, APScheduler, Playwright, SQLite/Turso, Jinja2, Claude API

**Design Doc:** `docs/plans/2026-03-08-v3-refactor-design.md`

---

## Task 1: Search Keyword Optimization

**Files:**
- Modify: `config/search_profiles.yaml`
- Modify: `config/base/scoring.yaml` (AI score calibration)

**Step 1: Update search_profiles.yaml — disable data_science**

In `config/search_profiles.yaml`, change `data_science` profile:

```yaml
  data_science:
    name: "Data Science & Analytics"
    enabled: false    # DISABLED: 0 interviews from 16 applied
    priority: 99
```

**Step 2: Update search_profiles.yaml — add priority tiers + daemon frequency**

Add `daemon_interval_minutes` field to defaults and each profile. Update priority values based on interview data (DE=7, ML=4, SE-AI=2, Quant=2):

```yaml
defaults:
  location: "Netherlands"
  date_posted: "r86400"
  job_type: "F"
  sort_by: "DD"
  max_jobs: 999
  daemon_interval_minutes: 360   # Default: P2 = every 6 hours
```

Per-profile updates:

```yaml
  data_engineering:
    priority: 0                      # P0: 7 interviews
    daemon_interval_minutes: 60      # Every 1 hour

  ml_engineering:
    priority: 0                      # P0: 4 interviews
    daemon_interval_minutes: 60      # Every 1 hour

  ml_research:
    priority: 1                      # P1: 2 interviews (66.7% rate!)
    daemon_interval_minutes: 120     # Every 2 hours

  backend_engineering:
    priority: 2                      # P2: 0 interviews (legacy had 3)
    daemon_interval_minutes: 360     # Every 6 hours
    # Also: remove "Full Stack Engineer" from queries

  quant:
    priority: 2                      # P2: 2 interviews (not primary focus)
    daemon_interval_minutes: 360     # Every 6 hours
```

**Step 3: Narrow backend_engineering keywords**

Replace the query in `backend_engineering`:

```yaml
  backend_engineering:
    queries:
      - keywords: '"Backend Engineer" OR "Python Developer" OR "Software Engineer"'
        description: "Backend & Python roles (narrowed, no Full Stack)"
    iamexpat:
      queries:
        - keywords: "python developer"
        - keywords: "backend engineer"
        - keywords: "software engineer"
        # Removed: full stack engineer
```

**Step 4: Create backend_ai_data profile**

Add new profile after `ml_research`:

```yaml
  # ============================================================
  # Group 5: Backend + AI/Data Context (INTERVIEW-PROVEN)
  # ============================================================
  backend_ai_data:
    name: "Software Engineer - AI/Data Focus"
    enabled: true
    priority: 1                      # P1: 2 interviews (Source.ag, TomTom)
    daemon_interval_minutes: 120     # Every 2 hours
    queries:
      - keywords: '"Software Engineer" AND ("Data" OR "AI" OR "Machine Learning" OR "Platform")'
        description: "Software engineer roles with data/AI context"
    iamexpat:
      queries:
        - keywords: "software engineer data"
        - keywords: "software engineer ai"
```

**Step 5: Verify config loads correctly**

Run:
```bash
python -c "import yaml; c=yaml.safe_load(open('config/search_profiles.yaml')); profiles={k:v for k,v in c['profiles'].items() if v.get('enabled',True)}; print(f'Enabled profiles: {len(profiles)}'); [print(f'  {k}: P{v.get(\"priority\",99)}, every {v.get(\"daemon_interval_minutes\", c[\"defaults\"].get(\"daemon_interval_minutes\",360))}min') for k,v in sorted(profiles.items(), key=lambda x:x[1].get('priority',99))]"
```

Expected: 6 enabled profiles (data_engineering, ml_engineering, ml_research, backend_ai_data, backend_engineering, quant), data_science disabled.

**Step 6: Commit**

```bash
git add config/search_profiles.yaml
git commit -m "feat: optimize search profiles based on interview data

Data-driven priority: DE(7 interviews)=P0, ML(4)=P0, SE-AI(2)=P1,
ml_research(2)=P1, quant(2)=P2, backend(0)=P2.
Drop data_science (0/16). Add daemon_interval_minutes for streaming.
Add backend_ai_data profile for SE+AI/Data context."
```

---

## Task 2: Pipeline Decoupling — Remove Auto CL

**Files:**
- Modify: `scripts/job_pipeline.py:691-742` (cmd_prepare)
- Modify: `src/checklist_server.py:12-39,76,114-156,269-292,376-422`

### Step 1: Remove CL imports and generation from cmd_prepare

In `scripts/job_pipeline.py`, modify `cmd_prepare()` (line 691+):

Remove these lines:
- Line 695: `from src.cover_letter_generator import CoverLetterGenerator`
- Line 696: `from src.cover_letter_renderer import CoverLetterRenderer`
- Line 711: Remove `"cl_failed": []` from results dict
- Lines 715-716: Remove `cl_gen` and `cl_renderer` instantiation
- Lines 736-742: Remove the entire CL generation block

The function should go directly from successful resume render to `results["success"].append(label)` with no CL step.

### Step 2: Remove CL references from checklist server

In `src/checklist_server.py`:

1. Remove `estimate_cl_scrutiny()` function (lines 12-39) — no longer needed
2. Remove `cl_scrutiny` from state.json seeds (line 76)
3. Remove CL scrutiny badge HTML (lines 114-121)
4. Remove CL seed panel HTML (lines 144-156)
5. Remove "Regen CL" button (line 153)
6. Remove `regenCL()` JavaScript function (lines 269-292)
7. Remove POST `/regen-cl` endpoint handler (lines 376-422)

### Step 3: Keep standalone --cover-letter command

The existing `--cover-letter JOB_ID` command (line 1204) stays as-is. It's already an independent command. No changes needed.

### Step 4: Remove CL from --generate batch

In `scripts/job_pipeline.py` line 1344-1346, remove the CL batch call:

Before:
```python
elif args.generate:
    pipeline.generate_resumes(min_ai_score=args.min_score, limit=args.limit)
    pipeline.generate_cover_letters_batch(min_ai_score=args.min_score, limit=args.limit)
```

After:
```python
elif args.generate:
    pipeline.generate_resumes(min_ai_score=args.min_score, limit=args.limit)
```

### Step 5: Test --prepare without CL

Run:
```bash
python scripts/job_pipeline.py --prepare --limit 1
```

Expected: Generates resume only, no CL generation, checklist UI has no CL fields.

### Step 6: Commit

```bash
git add scripts/job_pipeline.py src/checklist_server.py
git commit -m "refactor: decouple cover letter from automated pipeline

Remove auto CL generation from --prepare and --generate.
CL is now only available via --cover-letter JOB_ID (manual trigger).
Simplify checklist UI: remove CL scrutiny, seeds panel, regen button."
```

---

## Task 3: Streaming Daemon with Single HWM

**Files:**
- Modify: `src/db/job_db.py` (add scrape_watermarks table)
- Modify: `scripts/scraper_incremental.py` (add HWM logic)
- Create: `scripts/job_daemon.py` (APScheduler daemon)
- Create: `tests/test_daemon.py`

### Step 1: Add scrape_watermarks table to DB schema

In `src/db/job_db.py`, add to `SCHEMA` string (after line 341, before indexes):

```sql
    -- 爬取水位标记表 (增量爬取 High-Water Mark)
    CREATE TABLE IF NOT EXISTS scrape_watermarks (
        profile TEXT NOT NULL,
        query TEXT NOT NULL,
        hwm_url TEXT NOT NULL,
        last_scraped_at TEXT NOT NULL,
        jobs_found INTEGER DEFAULT 0,
        PRIMARY KEY (profile, query)
    );
```

### Step 2: Add HWM helper methods to JobDatabase

In `src/db/job_db.py`, add two methods to the `JobDatabase` class:

```python
    def get_watermark(self, profile: str, query: str) -> Optional[str]:
        """Get the high-water mark URL for a profile+query."""
        row = self.execute(
            "SELECT hwm_url FROM scrape_watermarks WHERE profile = ? AND query = ?",
            (profile, query),
            fetchone=True
        )
        return row['hwm_url'] if row else None

    def set_watermark(self, profile: str, query: str, hwm_url: str, jobs_found: int = 0):
        """Set/update the high-water mark for a profile+query."""
        self.execute(
            """INSERT INTO scrape_watermarks (profile, query, hwm_url, last_scraped_at, jobs_found)
               VALUES (?, ?, ?, datetime('now'), ?)
               ON CONFLICT(profile, query) DO UPDATE SET
                   hwm_url = excluded.hwm_url,
                   last_scraped_at = excluded.last_scraped_at,
                   jobs_found = excluded.jobs_found""",
            (profile, query, hwm_url, jobs_found)
        )
```

### Step 3: Test DB changes

Run:
```bash
python -c "
from src.db.job_db import JobDatabase
db = JobDatabase()
db.set_watermark('test_profile', 'test_query', 'https://linkedin.com/jobs/view/123')
print(db.get_watermark('test_profile', 'test_query'))
db.execute('DELETE FROM scrape_watermarks WHERE profile = ?', ('test_profile',))
print('OK')
"
```

Expected: Prints the URL, then "OK".

### Step 4: Add HWM logic to IncrementalScraper

In `scripts/scraper_incremental.py`, modify `run_profile()` method (line 345+):

Before the scraping loop, load the HWM:

```python
    async def run_profile(self, profile_name: str, profile_config: Dict,
                         search_config: Dict) -> List[Dict]:
        # ... existing setup code ...

        for i, query in enumerate(queries):
            keywords = query.get('keywords', '')
            # Load HWM for this profile+query
            hwm_url = self.db.get_watermark(profile_name, keywords)
            if hwm_url:
                print(f"  [HWM] Will stop at: {hwm_url[:60]}...")

            first_job_url = None  # Track for new HWM
            hwm_hit = False

            for page_num in range(1, self.max_pages_per_profile + 1):
                jobs = await self.scrape_search_page(keywords, location, page_num)

                if not jobs:
                    break

                for job in jobs:
                    job['search_profile'] = profile_name
                    job['search_query'] = keywords

                    # Record first job URL for new HWM
                    if first_job_url is None:
                        first_job_url = job.get('url', '')

                    # HWM check: stop if we've reached last known position
                    if hwm_url and job.get('url', '') == hwm_url:
                        print(f"  [HWM] Hit watermark on page {page_num}, stopping")
                        hwm_hit = True
                        break

                all_jobs.extend(jobs)

                if hwm_hit:
                    break

                # ... existing early-stop logic ...

            # Update HWM with first job from this scrape
            if first_job_url:
                new_count = len([j for j in all_jobs if j.get('search_query') == keywords])
                self.db.set_watermark(profile_name, keywords, first_job_url, new_count)
```

### Step 5: Create streaming daemon

Create `scripts/job_daemon.py`:

```python
#!/usr/bin/env python3
"""
Job Hunter Streaming Daemon v1.0
================================
Priority-tiered scheduler with per-job streaming pipeline.
Uses APScheduler to run scrape profiles at different intervals.

Usage:
    python scripts/job_daemon.py                    # Run daemon
    python scripts/job_daemon.py --once              # Single run (all profiles)
    python scripts/job_daemon.py --profile data_engineering  # Single profile
"""
import asyncio
import json
import signal
import sys
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from scripts.scraper_incremental import IncrementalScraper
from src.db.job_db import JobDatabase

CONFIG_DIR = PROJECT_ROOT / "config"
PROFILES_FILE = CONFIG_DIR / "search_profiles.yaml"


def load_config():
    """Load search profiles config."""
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


async def scrape_and_process(profile_name: str, headless: bool = True):
    """Scrape a single profile and stream each new job through the pipeline."""
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Scraping: {profile_name}")

    config = load_config()
    profile_config = config['profiles'].get(profile_name)
    if not profile_config or not profile_config.get('enabled', True):
        print(f"  [SKIP] Profile {profile_name} is disabled")
        return

    try:
        async with IncrementalScraper(headless=headless, max_pages_per_profile=4) as scraper:
            new_jobs = await scraper.run(profile=profile_name)

        if scraper.stats.get('new_jobs', 0) > 0:
            # Stream new jobs through pipeline
            db = JobDatabase()
            from scripts.job_pipeline import JobPipeline
            pipeline = JobPipeline()

            # Process only new jobs: filter + score
            pipeline.process_jobs()

            # Notify about high-score jobs
            notify_high_score_jobs(db, scraper.stats['new_jobs'])

    except Exception as e:
        print(f"  [ERROR] {profile_name}: {e}")


def notify_high_score_jobs(db: JobDatabase, new_count: int):
    """Send Telegram notification for high-score new jobs."""
    try:
        from scripts.notify import send_telegram_message
        msg = f"🔍 {new_count} new jobs found and processed"
        send_telegram_message(msg)
    except Exception:
        pass  # Notification is best-effort


def build_scheduler(config: dict) -> AsyncIOScheduler:
    """Build APScheduler with per-profile intervals from config."""
    scheduler = AsyncIOScheduler()
    defaults = config.get('defaults', {})
    default_interval = defaults.get('daemon_interval_minutes', 360)

    profiles = config.get('profiles', {})
    for name, profile in profiles.items():
        if not profile.get('enabled', True):
            continue

        interval = profile.get('daemon_interval_minutes', default_interval)
        scheduler.add_job(
            scrape_and_process,
            trigger=IntervalTrigger(minutes=interval),
            args=[name],
            id=f"scrape_{name}",
            name=f"Scrape {profile.get('name', name)} (every {interval}min)",
            max_instances=1,
            misfire_grace_time=300,
        )
        print(f"  Scheduled: {name} every {interval}min (P{profile.get('priority', 99)})")

    return scheduler


async def run_daemon():
    """Run the daemon with APScheduler."""
    config = load_config()

    print("=" * 60)
    print("Job Hunter Streaming Daemon v1.0")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    scheduler = build_scheduler(config)
    scheduler.start()

    # Run all profiles once immediately on startup
    profiles = {k: v for k, v in config['profiles'].items() if v.get('enabled', True)}
    for name in sorted(profiles, key=lambda x: profiles[x].get('priority', 99)):
        await scrape_and_process(name)

    # Keep running until interrupted
    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f: stop_event.set())

    print("\nDaemon running. Press Ctrl+C to stop.")
    await stop_event.wait()

    scheduler.shutdown()
    print("\nDaemon stopped.")


async def run_once(profile: str = None):
    """Single run mode."""
    config = load_config()
    profiles = config.get('profiles', {})

    if profile:
        await scrape_and_process(profile)
    else:
        enabled = {k: v for k, v in profiles.items() if v.get('enabled', True)}
        for name in sorted(enabled, key=lambda x: enabled[x].get('priority', 99)):
            await scrape_and_process(name)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Job Hunter Streaming Daemon')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--profile', type=str, help='Run specific profile only')
    parser.add_argument('--headless', action='store_true', default=True)
    args = parser.parse_args()

    if args.once or args.profile:
        asyncio.run(run_once(profile=args.profile))
    else:
        asyncio.run(run_daemon())


if __name__ == '__main__':
    main()
```

### Step 6: Install APScheduler dependency

Run:
```bash
pip install apscheduler
```

Add to `requirements.txt`:
```
apscheduler>=3.10.0
```

### Step 7: Test daemon single-run mode

Run:
```bash
python scripts/job_daemon.py --once --profile data_engineering
```

Expected: Scrapes data_engineering profile, processes new jobs through pipeline, shows HWM status.

### Step 8: Commit

```bash
git add src/db/job_db.py scripts/scraper_incremental.py scripts/job_daemon.py requirements.txt
git commit -m "feat: add streaming daemon with Single HWM incremental scraping

- Add scrape_watermarks table for high-water mark tracking
- Integrate HWM into IncrementalScraper (stop at last known position)
- Create job_daemon.py with APScheduler (priority-tiered intervals)
- Per-job streaming: scrape → filter → score → notify"
```

---

## Task 4: SVG Template Resumes with AI Routing

**Files:**
- Create: `templates/resume_data_engineer.svg`
- Create: `templates/resume_ml_engineer.svg`
- Modify: `src/ai_analyzer.py` (add template_fit output)
- Modify: `src/resume_renderer.py` (add SVG routing)

### Step 1: Create Data Engineer SVG template

Use existing `scripts/svg_auto_optimizer.py` as foundation. Generate a Data Engineer resume SVG emphasizing:
- Work experience bullets focused on ETL, Spark, Airflow, data pipelines
- Skills section: Python, SQL, Spark, Airflow, Kafka, Delta Lake, AWS/GCP
- Projects: Financial Data Lakehouse, data pipeline work

Select specific bullet IDs from `assets/bullet_library.yaml` for the DE template. Save to `templates/resume_data_engineer.svg`.

**Note:** SVG content creation requires manual design iteration with the SVG optimizer. This step may take multiple iterations.

### Step 2: Create ML Engineer SVG template

Same process for ML Engineer, emphasizing:
- PyTorch, TensorFlow, scikit-learn, model deployment
- MLOps, model monitoring, feature engineering
- Thesis UQ/RL project, NLP projects

Save to `templates/resume_ml_engineer.svg`.

### Step 3: Add template_fit to AI analyzer prompt

In `src/ai_analyzer.py`, modify the analysis prompt to include template_fit evaluation. Add to the expected JSON output schema:

```json
{
  "template_fit": {
    "score": 8,
    "best_template": "data_engineer",
    "gaps": ["Kafka experience emphasized but not in template"],
    "verdict": "use_template"
  }
}
```

Add to the prompt instructions:
```
TEMPLATE FIT EVALUATION:
Available templates: data_engineer, ml_engineer
Evaluate how well the best-matching template covers this JD's key requirements.
- score (0-10): How well does the template resume match this JD?
- best_template: Which template is the best fit?
- gaps: What key JD requirements are NOT covered by the template?
- verdict: "use_template" if score >= 8, "customize" if score < 8
```

### Step 4: Add SVG routing to resume renderer

In `src/resume_renderer.py`, add routing logic in the render method:

```python
def render_resume(self, job_id: str) -> dict:
    analysis = self.db.get_job_analysis(job_id)
    template_fit = json.loads(analysis.get('tailored_resume', '{}')).get('template_fit', {})

    if template_fit.get('verdict') == 'use_template':
        # Use pre-built SVG template
        template_name = template_fit.get('best_template', 'data_engineer')
        return self._render_svg_template(job_id, template_name)
    else:
        # Use existing AI-customized Jinja2 flow
        return self._render_customized(job_id)
```

### Step 5: Implement _render_svg_template method

```python
def _render_svg_template(self, job_id: str, template_name: str) -> dict:
    """Copy pre-built SVG template and convert to PDF."""
    svg_path = PROJECT_ROOT / f"templates/resume_{template_name}.svg"
    if not svg_path.exists():
        print(f"  [WARN] SVG template not found: {svg_path}, falling back to custom")
        return self._render_customized(job_id)

    # Use existing svg_to_pdf.py logic
    from scripts.svg_to_pdf import svg_to_pdf
    # ... copy SVG to output dir, convert to PDF, record in DB
```

### Step 6: Test routing logic

Run:
```bash
python -c "
from src.resume_renderer import ResumeRenderer
r = ResumeRenderer()
# Test with a known job that should use template
# Test with a known job that should use custom
"
```

### Step 7: Commit

```bash
git add templates/resume_data_engineer.svg templates/resume_ml_engineer.svg
git add src/ai_analyzer.py src/resume_renderer.py
git commit -m "feat: add SVG template resumes with AI-driven routing

- Create DE and ML Engineer SVG templates
- Add template_fit evaluation to AI analyzer
- Route: template_fit >= 8 → SVG template, < 8 → AI custom Jinja2"
```

---

## Implementation Order

| Order | Task | Effort | Risk | Dependencies |
|-------|------|--------|------|-------------|
| 1 | Search keyword optimization | Low (config only) | None | None |
| 2 | Pipeline CL decoupling | Low (remove code) | Low | None |
| 3 | Streaming daemon + HWM | Medium (new feature) | Medium (LinkedIn) | Task 1 (priorities) |
| 4 | SVG template resumes | High (design work) | Medium (AI prompt) | None |

Tasks 1 & 2 can be done in parallel. Task 3 depends on Task 1 (needs daemon_interval_minutes). Task 4 is independent.
