# Block A Operations Runbook

## Purpose

Block A is the scraper foundation for the job pipeline. Its job is to collect raw jobs, apply blacklist and duplicate suppression, and emit unified scrape metrics for downstream scoring, AI analysis, and notifications.

## Daily Entry Points

Default daily path:

```bash
python scripts/scrape.py --all --save-to-db
```

Profile-scoped LinkedIn verification:

```bash
python scripts/scrape.py --platform linkedin --profile data_engineering --dry-run
```

Greenhouse verification:

```bash
python scripts/scrape.py --platform greenhouse --dry-run
```

Manual IamExpat backfill only:

```bash
python scripts/scrape.py --platform iamexpat --dry-run
```

## Current Platform Semantics

- `--all` means `linkedin + greenhouse`
- `iamexpat` is frozen out of the daily critical path
- `iamexpat` still exists for manual or low-frequency backfill

The source of truth for this behavior is `src/scrapers/registry.py`.

## Key Artifacts

- Metrics: `data/scrape_metrics.json`
- CLI: `scripts/scrape.py`
- Shared report contract: `src/scrapers/base.py`
- LinkedIn browser/session diagnostics: `src/scrapers/linkedin_browser.py`
- LinkedIn orchestration diagnostics: `src/scrapers/linkedin.py`

## How To Read `scrape_metrics.json`

Top-level:

- `new_jobs`: Phase 1 compatibility field for notifications
- `platforms`: per-platform `ScrapeReport`
- `total`: aggregate summary

Per-platform report:

- `found`: raw jobs returned by the platform scraper
- `new`: jobs actually inserted
- `would_insert`: insert candidates in dry-run mode
- `skipped_blacklist`: filtered by configured blacklist
- `skipped_duplicates`: removed by URL-hash dedup
- `targets_attempted/succeeded/failed`: per-query or per-target execution counts
- `errors`: scraper-level failures
- `target_errors`: target/query-level failures
- `diagnostics`: structured runtime diagnostics

## LinkedIn Diagnostics

LinkedIn now emits structured diagnostics into the platform report.

Important fields:

- `session_status`
  - `unknown`: not enough state captured yet
  - `cookies_loaded`: cookie file loaded successfully
  - `ok`: validated logged-in session
  - `auth_redirect`: redirected to login/auth wall
  - `challenge`: challenge or CAPTCHA page detected
  - `cookies_missing`: cookie file missing
  - `cookies_malformed`: cookie JSON unreadable or empty
  - `cookies_missing_li_at`: login cookie missing
- `last_stage`
  - `load_cookies`
  - `validate_session`
  - `search`
  - `detail_fetch`
  - `challenge_check`
  - `navigation_timeout`
- `last_url`: most recent LinkedIn URL touched by the browser
- `challenge_marker`: exact URL/text marker that triggered challenge detection
- `cards_found`: cards returned by the most recent LinkedIn search
- `detail_fetch_failures`: description fetch fallbacks/failures seen in this browser session
- `query_count`, `query_successes`, `query_failures`: LinkedIn query fanout summary
- `queries`: per-query execution records
- `elapsed_seconds`: total platform runtime added by the CLI layer

## Interpreting Common LinkedIn Failures

`session_status=auth_redirect`
- Cookie is expired or LinkedIn rejected the session.
- First check the local cookie file at `config/linkedin_cookies.json`.

`session_status=challenge`
- LinkedIn showed a visible challenge page or challenge URL.
- Check `challenge_marker` and `last_url` first.

`last_stage=navigation_timeout`
- LinkedIn page load exceeded timeout.
- This is usually network latency, Playwright instability, or page load regression rather than cookie invalidation.

`query_failures>0` with `session_status=ok`
- Session is healthy but one or more queries failed.
- Start with the first item in `diagnostics.queries` whose `status=error`.

## Greenhouse Failure Pattern

Typical failure mode is a stale or removed company board.

What it looks like:

- `targets_failed > 0`
- `target_errors` contains one or more companies
- severity is usually `warning`, not `error`

Example already seen in production:

- Backbase board returns `404`

Remediation:

- update or remove the company in `config/target_companies.yaml`

## IamExpat Policy

IamExpat is intentionally not in `--all`.

Reason:

- runtime cost is high
- recent incremental yield is low
- it is retained only as a supplemental backfill source

Manual workflow:

- `.github/workflows/iamexpat-backfill.yml`

## Recommended Triage Order

1. Open `data/scrape_metrics.json`
2. Check `total.severity`
3. Check failing platform `errors`, `target_errors`, and `diagnostics`
4. For LinkedIn, inspect `session_status`, `last_stage`, `last_url`, `challenge_marker`
5. For Greenhouse, inspect stale targets in `target_errors`
6. Only after metrics review, rerun a platform-specific dry-run locally
