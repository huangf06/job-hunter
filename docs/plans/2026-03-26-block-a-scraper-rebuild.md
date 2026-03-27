# Block A: Scraper Clean Rebuild Design

> Date: 2026-03-26
> Status: Revised (v3, addressing Codex review v2)
> Scope: Complete rewrite of scraping layer (Block A)
> Reviews:
>   - v1 → Codex: "Request revision" (4 blocking + 5 should-fix). All resolved in v2.
>   - v2 → Codex: "Request revision" (2 remaining should-fix + 2 minor). All resolved in v3.

## Context

### Current State (Degraded)

Block A consists of 6 active files (~1,753 lines) + 3 dead files (~761 lines). CI runs succeed
but scrapers have produced zero new data since March 20, masked by `continue-on-error: true`.

| Platform | Total Jobs | Last Scraped | Status |
|----------|-----------|-------------|--------|
| LinkedIn | 2,604 (69%) | Mar 20 | 6 days silent, cookie likely expired |
| Greenhouse | 521 | Mar 20 | 6 days silent |
| IamExpat | 176 | Mar 18 | 8 days silent, Playwright fragile |
| Lever | 0 | Never | Built but never produced data |

Git history shows 23 scraper-related bug fix commits (Jan-Mar 2026), indicating persistent instability.
CI has been running continuously (20 consecutive green runs) — the data drought is not caused by CI being disabled, but by scrapers silently failing or finding only duplicates.

### Decision: Clean Rebuild

Reasons:
1. Scrapers are not producing data despite CI reporting success
2. Repeated patch-fix pattern indicates architectural issues
3. LinkedIn scraper is 1,207 lines in a single file
4. Dedup strategies inconsistent across scrapers
5. Errors silently swallowed, no way to distinguish "no new jobs" from "scraper broken"

### Rejected Alternatives

- **Incremental fix (keep current code):** Preserves the root problems
- **BaseScraper + abstract browser layer:** LinkedIn CDP and IamExpat headless are too different to share meaningfully
- **Welcome to the Jungle platform:** Researched; NL job market coverage is near zero (strong in France/Spain/UK). Technically easy (Algolia public API, pure HTTP), but no data to scrape. Revisit if they expand to NL.
- **Lever scraper:** Zero lifetime output, only one target company (Spotify). Delete. Can rewrite in ~80 lines from new BaseScraper if needed later.

## Architecture

### Approach: Unified BaseScraper + Plugin Scrapers

```
scripts/scrape.py              <- single CLI entry point
src/scrapers/
  __init__.py                  <- exports
  base.py                     <- BaseScraper + ScrapeReport + error types
  registry.py                 <- scraper dict + aliases
  linkedin.py                 <- LinkedInScraper(BaseScraper)
  linkedin_browser.py         <- browser lifecycle + CDP
  linkedin_parser.py          <- page parsing + JD extraction
  greenhouse.py               <- GreenhouseScraper(BaseScraper)
  iamexpat.py                 <- IamExpatScraper(BaseScraper)
```

## Design Details

### 1. BaseScraper

```python
class BaseScraper(ABC):
    @abstractmethod
    def scrape(self) -> list[RawJob]: ...   # synchronous public contract

    def run(self) -> ScrapeReport:          # synchronous entry point
        raw_jobs = self.scrape()
        jobs = self._deduplicate(raw_jobs)
        jobs = self._apply_blacklist(jobs)
        saved = self._save_to_db(jobs)
        return self._build_report()

@dataclass
class ScrapeReport:
    source: str
    found: int              # raw count from platform
    new: int                # actually inserted to DB (or would_insert in dry-run)
    duplicates: int         # skipped by URL dedup
    blacklisted: int        # skipped by blacklist
    errors: int             # failed fetches (target-level)
    error_details: list     # specific error messages with classification
    duration_seconds: float
    targets_attempted: int  # e.g. number of Greenhouse boards, LinkedIn queries
    targets_succeeded: int
    targets_failed: int
    dry_run: bool = False   # when True, `new` means "would have inserted"

    @property
    def is_healthy(self) -> bool:
        """Healthy = no fatal errors. found=0 with no errors is normal (quiet market)."""
        return self.errors == 0

    @property
    def severity(self) -> str:
        """CI notification severity level."""
        if self.errors > 0 and self.found == 0:
            return "critical"   # scraper broken
        if self.errors > 0:
            return "warning"    # partial failure
        if self.found == 0:
            return "info"       # quiet market, all targets succeeded but nothing new
        return "success"        # healthy with data
```

**Key design decisions (revised per Codex review):**

- **Synchronous public contract.** `scrape()` is sync. LinkedIn and IamExpat use `asyncio.run()` internally. Greenhouse uses plain `requests`. No forced async wrapper.
- **`is_healthy` based on errors only**, not `found > 0`. A quiet market or all-duplicate run is not a failure.
- **`severity` property** drives CI notification: 4 levels (critical / warning / info / success).
- **Target-level tracking.** `targets_attempted/succeeded/failed` captures partial failures (e.g., 22 of 23 Greenhouse boards succeeded, 1 returned 404).
- **`dry_run` flag.** When `True`, `new` means "would have inserted" — no ambiguity.

### 2. Error Handling (Two-Level)

```python
class ScraperError(Exception):
    """Base error for all scraper failures."""

class TransientError(ScraperError):
    """Retryable: network timeout, 429 rate limit, page load failure."""

class PermanentError(ScraperError):
    """Not retryable: CAPTCHA, expired cookie, auth failure."""
```

**Two-level error scope (revised per Codex review #9):**

| Scope | Example | Behavior |
|-------|---------|----------|
| **Scraper-level fatal** | LinkedIn CAPTCHA, cookie expired | Stop entire scraper, report as PermanentError |
| **Target-level error** | One Greenhouse board 404, one LinkedIn JD page timeout | Record in `targets_failed`, continue to next target |

**Retry strategy:**
- Target-level TransientError: retry 3x with exponential backoff (2s, 4s, 8s)
- Target-level TransientError with `Retry-After` header: respect server-specified wait time
- Target-level PermanentError (e.g., board 404): skip target, record, continue
- Scraper-level PermanentError: stop scraper immediately, record in report
- No more `except Exception: pass`

### 3. CLI Entry Point

```
python scripts/scrape.py --platform linkedin --profile data_engineering --save-to-db
python scripts/scrape.py --platform ats          # greenhouse only (lever removed)
python scripts/scrape.py --platform iamexpat
python scripts/scrape.py --all                   # all platforms
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --dry-run         # fetch but don't save
```

**Profile compatibility (revised per Codex v2 review #5):**

Legacy profiles (`ml_data`, `backend_data`, `quick_test`) are deleted from `config/search_profiles.yaml`.
The new CLI only accepts active profile names. CI workflow is updated in the same change.
No backward-compatible aliases — clean break.

Active profiles (from `config/search_profiles.yaml`):
- `data_engineering` (P0)
- `ml_engineering` (P0)
- `backend_engineering` (P2)
- `data_science` (P2)
- `quant` (P2)
- `ml_research` (P1)
- `backend_ai_data` (P1)

Registry with aliases:
```python
SCRAPERS = {
    "linkedin": LinkedInScraper,
    "greenhouse": GreenhouseScraper,
    "iamexpat": IamExpatScraper,
}
ALIASES = {
    "ats": ["greenhouse"],
    "all": ["linkedin", "greenhouse", "iamexpat"],
}
```

Output: structured summary table after every run.

```
═══ Scrape Summary ═══
Platform     Found   New   Dup   Skip   Err   Targets   Time
LinkedIn       42    12    28      2     0     5/5       34s
Greenhouse     18     3    15      0     0    23/23       8s
IamExpat        7     2     4      1     0     3/3       22s
────────────────────────────────────────────────────────────
Total          67    17    47      3     0    31/31      66s
```

### 4. LinkedIn Scraper Split

From 1,207 lines in one file to 3 files (~500 lines total):

| File | Responsibility | ~Lines |
|------|---------------|--------|
| `linkedin.py` | `LinkedInScraper(BaseScraper)` — query orchestration, calls `asyncio.run()` internally | 200 |
| `linkedin_browser.py` | Browser lifecycle: CDP connect vs launch, cookie load/save, request interception, session validation | 150 |
| `linkedin_parser.py` | Page parsing: search results -> job cards, detail page -> JD text, multi-strategy fallback | 150 |

Key improvements vs current code:
- CAPTCHA: raise `CaptchaDetectedError` (PermanentError) instead of `input()` hang
- Cookie expiry: validate session after login, raise `PermanentError` on failure
- Pagination: extract to `_paginate()` generator
- JD fetch failure: target-level error, does not kill entire scrape

**Boundary discipline (per Codex #10):** `linkedin_browser.py` owns all Playwright interaction. `linkedin_parser.py` receives page content (HTML strings or Playwright Locators), never manages browser state. `linkedin.py` orchestrates but does not contain selectors or browser logic.

### 5. Greenhouse + IamExpat

**Greenhouse (~80 lines):** Largely unchanged. REST API calls. Retry handled by BaseScraper. Per-board failures are target-level errors (continue to next board).

**IamExpat (~120 lines):** Two-phase scrape preserved (listing -> detail). Change `networkidle` to `domcontentloaded` + explicit element wait. Timeout configurable. Uses `asyncio.run()` internally for Playwright async.

### 6. Dedup Strategy (Unified in BaseScraper)

**URL hash dedup only (revised per Codex review #1 and #4):**
- Use existing `generate_job_id()` from `job_db.py` — **keep MD5, do NOT change to SHA256**
- Normalize URL (strip query params, fragments) → MD5 → 12 char hex → job_id
- DB `ON CONFLICT` as final safety net
- Blacklist applied after dedup (company/title substring match from config)

**Repost detection stays downstream (intentional, per Codex v2 minor concern):**
- `job_db.find_applied_duplicates()` already handles company+title repost detection
- Used by `--prepare` workflow to flag REPOST warnings in checklist
- No new DB schema needed, no Layer 2 in scraper
- Repost-like patterns are intentionally NOT visible in scrape-time metrics — they are a downstream concern. The scraper's job is to collect data; repost detection happens when the user is about to apply.

This is simpler and avoids the persistence problem Codex identified.

### 7. Observability

**7a. CI Notification Severity (ScrapeReport.severity)**

| found | errors | severity | Message |
|-------|--------|----------|---------|
| 0 | 0 | info | "LinkedIn: no new jobs (5/5 targets OK)" |
| 0 | >0 | critical | "LinkedIn: FAILED - CaptchaDetectedError" |
| >0 | 0 | success | "LinkedIn: 12 new / 28 dup" |
| >0 | >0 | warning | "LinkedIn: 8 new, 3 errors (22/25 targets OK)" |

**7b. Unified Metrics File (revised per Codex review #6)**

Single file `data/scrape_metrics.json` replaces both `scrape_metrics.json` and `multi_scrape_metrics.json`.

**Metrics JSON contract (revised per Codex v2 review #6):**

```json
{
  "new_jobs": 17,
  "timestamp": "2026-03-26T08:00:00Z",
  "platforms": {
    "linkedin": {
      "found": 42, "new": 12, "duplicates": 28, "blacklisted": 2,
      "errors": 0, "targets_attempted": 5, "targets_succeeded": 5,
      "targets_failed": 0,
      "duration_seconds": 34.2, "severity": "success"
    },
    "greenhouse": {
      "found": 18, "new": 3, "duplicates": 15, "blacklisted": 0,
      "errors": 0, "targets_attempted": 23, "targets_succeeded": 23,
      "targets_failed": 0,
      "duration_seconds": 8.4, "severity": "success"
    },
    "iamexpat": {
      "found": 7, "new": 2, "duplicates": 4, "blacklisted": 1,
      "errors": 0, "targets_attempted": 3, "targets_succeeded": 3,
      "targets_failed": 0,
      "duration_seconds": 22.1, "severity": "success"
    }
  },
  "total": {
    "found": 67, "new": 17, "duplicates": 47, "blacklisted": 3,
    "errors": 0, "targets_attempted": 31, "targets_succeeded": 31,
    "targets_failed": 0,
    "duration_seconds": 66.1, "severity": "success"
  }
}
```

**Consumer compatibility strategy (two-phase):**

Phase 1 (this rebuild): Top-level `new_jobs` field is a compatibility shim equal to `total.new`.
Existing consumers read it unchanged:
- `scripts/notify.py`: `scrape.get("new_jobs", 0)` — works as-is
- CI workflow: `m.get('new_jobs', 0)` — works as-is

Phase 2 (follow-up): Migrate `notify.py` to read `total.*` and per-platform data for richer
notifications. Then remove the top-level `new_jobs` shim. This is a separate, low-risk change.

## Files to Delete

| File | Lines | Reason |
|------|-------|--------|
| `scripts/linkedin_scraper_v6.py` | 1,207 | Replaced by `src/scrapers/linkedin*.py` |
| `scripts/multi_scraper.py` | 137 | Replaced by `scripts/scrape.py` |
| `scripts/scraper_incremental.py` | 549 | Dead code (v5 legacy) |
| `scripts/scraper_incremental_v32.py` | 212 | Dead code (v3.2 bridge) |
| `src/scrapers/lever.py` | 88 | Never produced data |
| **Total removed** | **2,193** | |

## Files to Create/Rewrite

| File | ~Lines | Action |
|------|--------|--------|
| `scripts/scrape.py` | 100 | New CLI entry point |
| `src/scrapers/__init__.py` | 20 | Rewrite exports |
| `src/scrapers/base.py` | 250 | Rewrite: BaseScraper, ScrapeReport, error types, unified dedup |
| `src/scrapers/registry.py` | 30 | New |
| `src/scrapers/linkedin.py` | 200 | New (from linkedin_scraper_v6.py) |
| `src/scrapers/linkedin_browser.py` | 150 | New (from linkedin_scraper_v6.py) |
| `src/scrapers/linkedin_parser.py` | 150 | New (from linkedin_scraper_v6.py) |
| `src/scrapers/greenhouse.py` | 80 | Rewrite to use BaseScraper |
| `src/scrapers/iamexpat.py` | 120 | Rewrite to use BaseScraper |
| **Total new** | **~1,000** | |

## Config Changes

- `config/target_companies.yaml`: Remove Lever entry (Spotify)
- `config/search_profiles.yaml`: Delete legacy profiles (`ml_data`, `backend_data`, `quick_test`)
- `.github/workflows/job-pipeline-optimized.yml`: Replace scrape commands with `python scripts/scrape.py --all --save-to-db`

## Migration Checklist

Per Codex review #5 and #11, the following must be updated alongside the code:

1. **CI workflow** (`.github/workflows/job-pipeline-optimized.yml`):
   - Replace LinkedIn + multi_scraper steps with single `python scripts/scrape.py --all --save-to-db`
   - Metrics file path stays `data/scrape_metrics.json` — new schema has top-level `new_jobs` shim
   - Workflow extraction line `m.get('new_jobs', 0)` works unchanged (Phase 1 compat)
   - Remove `continue-on-error: true` from scrape step (ScrapeReport handles failure reporting)
   - Update workflow input profiles: replace `ml_data`/`backend_data`/`quant` with active profile names (`data_engineering`, `ml_engineering`, etc.)

2. **Notification script** (`scripts/notify.py`):
   - Phase 1 (this rebuild): No code changes needed — top-level `new_jobs` shim ensures `load_scrape_metrics()` works as-is
   - Phase 2 (follow-up): Migrate to read `total.*` and per-platform data for richer notifications, then remove `new_jobs` shim

3. **Documentation**:
   - `CLAUDE.md`: Update scraper commands and file references
   - `AGENTS.md`: Update file paths referencing deleted scripts
   - `docs/architecture-overview.md`: Update Block A section

## Verification Gates (Post-Implementation)

Per Codex review questions, the first verification checks should be:

1. **URL hash compatibility**: Run new scraper against existing DB, confirm `generate_job_id()` produces identical IDs (MD5, not SHA256)
2. **Metrics + notify compatibility**: Verify `scripts/notify.py` reads new `scrape_metrics.json` correctly
3. **LinkedIn failure paths**: Test expired cookie → PermanentError raised, CAPTCHA → CaptchaDetectedError raised (not hung)
4. **Dry-run correctness**: `--dry-run` produces accurate `would_insert` counts without DB writes
5. **CI end-to-end**: Full workflow run with new `scripts/scrape.py --all --save-to-db`

## Net Impact

| Metric | Before | After |
|--------|--------|-------|
| Active scraper code | 1,753 lines | ~1,000 lines (-43%) |
| Dead code | 761 lines | 0 lines (-100%) |
| Scraper files | 8 + 3 dead | 8 active |
| Dedup strategies | 3 inconsistent | 1 unified (URL hash in base) |
| Error visibility | Silent swallow | Structured ScrapeReport with 2-level error scope |
| CI failure detection | None (continue-on-error) | 4-level severity (critical/warning/info/success) |
| Metrics files | 2 separate | 1 unified |

## Revision History

- **v1 (2026-03-26):** Initial design. Codex review: "Request revision" (4 blocking, 5 should-fix).
- **v2 (2026-03-26):** Addressed all v1 Codex feedback:
  - #1 (blocking): Keep MD5 hash, do not change to SHA256
  - #2 (blocking): Sync public contract (`scrape()`), async internal only
  - #3 (blocking): `is_healthy` based on errors only, added `severity` property
  - #4 (blocking): Removed Layer 2 dedup from scraper; repost detection stays downstream
  - #5 (should-fix): Added migration checklist for CI profile compatibility
  - #6 (should-fix): Defined unified metrics schema, notify.py update plan
  - #7 (should-fix): Added `targets_attempted/succeeded/failed`, `dry_run` flag
  - #8 (should-fix): `new` = `would_insert` when `dry_run=True`
  - #9 (should-fix): Two-level error scope (scraper-level fatal vs target-level), Retry-After support
  - #10 (nice-to-have): Documented boundary discipline for LinkedIn 3-file split
  - #11 (nice-to-have): Added docs update to migration checklist
- **v3 (2026-03-27):** Addressed v2 Codex feedback (2 should-fix + 2 minor):
  - #5 revisited: Explicit profile strategy — delete legacy profiles, clean break, no aliases
  - #6 revisited: Exact metrics JSON contract with `new_jobs` compat shim, two-phase migration plan, full example for all platforms including `targets_failed`
  - Minor: `targets_failed` added to metrics example
  - Minor: Explicitly stated repost patterns are intentionally not in scrape-time metrics
