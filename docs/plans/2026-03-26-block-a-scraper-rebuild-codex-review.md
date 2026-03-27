# Block A Scraper Rebuild - Codex Review

> Date: 2026-03-26
> Reviewer: Codex
> Target: `docs/plans/2026-03-26-block-a-scraper-rebuild.md`

## Verdict

Request revision

## Strengths

- The root diagnosis is correct. The current scraping layer does suppress errors locally while CI masks step failure with `continue-on-error: true`, so a rebuild focused on error visibility is justified.
- Moving blacklist, dedup, DB save, and reporting into a common base is the right direction. The current `BaseScraper` is too thin, and the concrete scrapers each implement partial failure handling differently.
- Splitting LinkedIn out of the current 1,200-line script is appropriate. Browser lifecycle, login, pagination, parsing, JD extraction, and DB writes are currently mixed into one file.
- Removing Lever is reasonable. The current config only contains one Lever target (`Spotify`), and the scraper has never produced useful output.

## Issues

### Blocking

1. **Job ID hash migration risk is not addressed**

The design changes Layer 1 dedup from the current MD5-based 12-char ID to SHA256-based 12-char ID. Today, historical identity is generated in [`src/db/job_db.py`](/C:/Users/huang/github/job-hunter/src/db/job_db.py#L674). If the scraper starts writing a different ID for the same normalized URL without a DB migration plan, every historical job becomes "new" from the dedup layer's perspective, and all downstream records keyed by `job_id` become inconsistent in practice.

Required fix:
- Keep the existing hash algorithm for compatibility, or
- Add an explicit migration plan covering existing `jobs.id` and downstream foreign-keyed tables.

2. **`BaseScraper` async contract is inconsistent**

The design defines `async fetch_jobs()` but shows `run()` calling it synchronously. That abstraction is not coherent as written. Also, forcing all scrapers into an async public API is unnecessary here: Greenhouse is simple HTTP, LinkedIn and IamExpat are the only async-heavy cases.

Required fix:
- Keep the public base contract synchronous, for example `scrape() -> list[RawJob]` or `run() -> ScrapeReport`.
- Let individual scrapers use async internally where needed.

3. **`ScrapeReport.is_healthy` conflicts with the observability model**

The design defines:

```python
return self.errors == 0 and self.found > 0
```

But later it says `found=0, errors=0` should be an `info` state rather than a failure. Those two definitions conflict. A quiet market or an all-duplicate run is not automatically unhealthy.

Required fix:
- Define health from fatal errors / contract violations, not from `found > 0`.

4. **Layer-2 dedup flag has no persistence model**

The design says Layer 2 should flag `probable_repost` and let downstream stages decide what to do. The current DB schema has no field for that in `jobs`, and the design does not introduce a new table or schema extension.

Required fix:
- Specify where `probable_repost` is stored.
- If downstream filter / AI is expected to consume it, add a schema change or a durable sidecar table.

### Should-Fix

5. **CI compatibility is under-specified**

The workflow migration section only says "replace scrape commands with `python scripts/scrape.py --all --save-to-db`". That is incomplete.

Current workflow inputs still expose legacy profiles in [`.github/workflows/job-pipeline-optimized.yml`](/C:/Users/huang/github/job-hunter/.github/workflows/job-pipeline-optimized.yml#L17):
- `ml_data`
- `backend_data`
- `quant`

But in [`config/search_profiles.yaml`](/C:/Users/huang/github/job-hunter/config/search_profiles.yaml#L155), `ml_data` and `backend_data` are disabled legacy profiles.

Required fix:
- Either preserve backward-compatible profile aliases in the new CLI, or
- Update workflow inputs and related docs in the same change.

6. **Metrics and notification integration is incomplete**

Today:
- LinkedIn writes `data/scrape_metrics.json`
- Multi-platform writes `data/multi_scrape_metrics.json`
- `scripts/notify.py` only reads `data/scrape_metrics.json`

The rebuild proposes a unified CLI but does not define the unified metrics artifact schema or the corresponding notification change.

Required fix:
- Define one stable scrape metrics file for all platforms.
- Update `scripts/notify.py` to read the new schema.

7. **`ScrapeReport` is missing operationally useful fields**

The current proposal has:
- `found`
- `new`
- `duplicates`
- `blacklisted`
- `errors`
- `error_details`
- `duration_seconds`

That is too small for multi-target scrapers and CI diagnosis. For example, Greenhouse may partially fail across boards; LinkedIn may partially fail across profiles or queries.

Recommended additions:
- `fatal_error`
- `warnings`
- `targets_attempted`
- `targets_succeeded`
- `targets_failed`
- `probable_reposts`
- `would_insert` for dry-run mode

8. **`new` is ambiguous under `--dry-run`**

The CLI promises `--dry-run`, but the report defines `new` as "actually inserted to DB". In dry-run mode there are no inserts, so `new` becomes misleading unless the design also tracks what would have been inserted.

Required fix:
- Add `would_insert`, or
- Redefine `new` and introduce a separate `inserted`.

9. **Error classification needs a scraper-level vs target-level split**

`TransientError` vs `PermanentError` is directionally good, but not enough. One bad Greenhouse board or one failed LinkedIn JD page should not kill the whole scraper. An expired LinkedIn cookie or CAPTCHA probably should.

Required fix:
- Distinguish fatal scraper-level errors from per-page / per-target errors.
- Support `Retry-After` handling for 429s rather than only fixed `2s/4s/8s` backoff.

### Nice-To-Have

10. **The LinkedIn 3-file split is good, but only if boundaries stay strict**

The proposed split is sensible:
- `linkedin.py`: orchestration
- `linkedin_browser.py`: browser/session lifecycle
- `linkedin_parser.py`: DOM parsing and JD extraction

This is the right decomposition as long as pagination control, selector fallbacks, and browser state do not bleed back into one orchestration blob.

11. **Documentation cleanup should be part of the migration plan**

There are existing references to:
- `scripts/linkedin_scraper_v6.py`
- `scripts/multi_scraper.py`

in project docs such as [`AGENTS.md`](/C:/Users/huang/github/job-hunter/AGENTS.md#L38) and `CLAUDE.md`. If the rebuild lands without doc cleanup, operational drift starts immediately.

Recommended fix:
- Add docs update as an explicit migration checklist item.

## Questions

1. Where will `probable_repost` be persisted: new DB column, separate table, or metrics-only artifact?
2. Do you want the new CLI to preserve old command semantics for compatibility, or are you intentionally breaking them and updating all docs/workflows in one shot?
3. Is JD fetching part of the core `fetch_jobs()` path, or should listing fetch and detail enrichment be modeled as separate stages so partial JD failures do not distort scrape health?
4. What are the first verification gates after implementation? The highest-value ones appear to be:
   - URL hash compatibility against the existing DB
   - workflow + metrics + notify compatibility
   - LinkedIn expired-cookie / CAPTCHA failure path
   - dry-run report correctness across all platforms

## Cross-Check Notes

The review above was validated against the current implementation and integration points:

- Design target: [`docs/plans/2026-03-26-block-a-scraper-rebuild.md`](/C:/Users/huang/github/job-hunter/docs/plans/2026-03-26-block-a-scraper-rebuild.md)
- Current base abstraction: [`src/scrapers/base.py`](/C:/Users/huang/github/job-hunter/src/scrapers/base.py#L30)
- Current orchestrator: [`scripts/multi_scraper.py`](/C:/Users/huang/github/job-hunter/scripts/multi_scraper.py#L91)
- Current LinkedIn scraper: [`scripts/linkedin_scraper_v6.py`](/C:/Users/huang/github/job-hunter/scripts/linkedin_scraper_v6.py#L1111)
- Current DB identity logic: [`src/db/job_db.py`](/C:/Users/huang/github/job-hunter/src/db/job_db.py#L674)
- Current workflow integration: [`.github/workflows/job-pipeline-optimized.yml`](/C:/Users/huang/github/job-hunter/.github/workflows/job-pipeline-optimized.yml#L82)
- Current search profile config: [`config/search_profiles.yaml`](/C:/Users/huang/github/job-hunter/config/search_profiles.yaml#L19)
- Current ATS target config: [`config/target_companies.yaml`](/C:/Users/huang/github/job-hunter/config/target_companies.yaml#L1)
