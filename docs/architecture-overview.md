# Architecture Overview

> **Full pipeline block architecture**: See `docs/plans/2026-03-27-pipeline-block-architecture.md` for the complete 6-block design (A→F), data flow, DB schema, and rebuild priority.

## Block A Scraper Layer

Block A now uses a unified scraper entry point:

```bash
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --profile data_engineering --save-to-db
python scripts/scrape.py --platform greenhouse --dry-run
```

The scraper layer is organized around a synchronous `BaseScraper.run()` contract that returns a `ScrapeReport`.

- `src/scrapers/base.py`: shared run contract, blacklist filtering, URL-hash dedup, dry-run handling, structured reporting
- `src/scrapers/registry.py`: platform registry and aliases (`ats`, `all`)
- `src/scrapers/greenhouse.py`: Greenhouse board scraper with per-target reporting
- `src/scrapers/iamexpat.py`: IamExpat two-phase listing/detail scraper with per-query reporting
- `src/scrapers/linkedin.py`: LinkedIn orchestration
- `src/scrapers/linkedin_browser.py`: LinkedIn browser/session layer
- `src/scrapers/linkedin_parser.py`: LinkedIn parsing helpers

## Diagnostics Model

`ScrapeReport` now carries a `diagnostics` object in addition to counts and error lists.

- CLI runtime adds `elapsed_seconds`
- LinkedIn emits structured browser/session diagnostics such as `session_status`, `last_stage`, `last_url`, `challenge_marker`, and per-query summaries
- Metrics consumers should prefer `diagnostics` over log scraping when determining scraper health

Operational guidance lives in:

- `docs/runbooks/block-a-operations.md`
- `docs/runbooks/block-a-checklist.md`

## Compatibility Notes

- `data/scrape_metrics.json` remains the Phase 1 metrics artifact.
- Top-level `new_jobs` is preserved for notifications and workflow compatibility.
- Job dedup continues to use `JobDatabase.generate_job_id()` on normalized URLs.
- Downstream hard filter, AI analysis, and notification flow are being rebuilt block-by-block (see pipeline block architecture doc).
