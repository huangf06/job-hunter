# Codex Review Prompt: Block A Scraper Rebuild (v2)

## Your Role

You are reviewing **revision v2** of a design document for a clean rebuild of the scraping layer (Block A). The design is at `docs/plans/2026-03-26-block-a-scraper-rebuild.md`.

## Context

This is a revision that addresses your previous review (`docs/plans/2026-03-26-block-a-scraper-rebuild-codex-review.md`), which returned "Request revision" with 4 blocking issues, 5 should-fix items, and 2 nice-to-haves. All 11 items have been addressed — see the "Revision History" section at the bottom of the design doc for a point-by-point mapping.

## What to Verify

Since this is a second-pass review, focus on:

1. **Were the 4 blocking issues actually resolved?**
   - #1: MD5 hash preserved (not changed to SHA256). Cross-check against `src/db/job_db.py` line 674.
   - #2: Sync public contract (`scrape()` not `async fetch_jobs()`). Is the async-internal pattern coherent?
   - #3: `is_healthy` no longer requires `found > 0`. Does the new `severity` property cover all edge cases?
   - #4: Layer 2 dedup removed. Is the existing `find_applied_duplicates()` in `job_db.py` sufficient for repost detection?

2. **Were the 5 should-fix items addressed adequately?**
   - #5: CI profile compatibility — is the migration checklist complete?
   - #6: Unified metrics schema — is the JSON schema sufficient for `notify.py`? Cross-check with `scripts/notify.py` `load_scrape_metrics()`.
   - #7: ScrapeReport fields — are `targets_attempted/succeeded/failed` and `dry_run` sufficient?
   - #8: `new` vs `would_insert` in dry-run — is this clear and unambiguous now?
   - #9: Two-level error scope — does scraper-level vs target-level cover all real failure modes? Is `Retry-After` handling specified enough?

3. **New risks introduced by the revision?**
   - Did resolving one issue create a new gap?
   - Is anything over-simplified by removing Layer 2 dedup?

4. **Implementation readiness:**
   - Is this design specific enough to hand to a developer for implementation without ambiguity?
   - Are the verification gates (section at bottom) the right ones? Missing any?

## How to Review

- Read the full revised design doc
- Cross-reference with actual code: `src/db/job_db.py`, `scripts/notify.py`, `.github/workflows/job-pipeline-optimized.yml`, `config/search_profiles.yaml`
- Compare v2 against your original review to confirm each item is addressed
- Be direct: approve if ready, request revision if not

## Output Format

- **Verdict**: Approve / Approve with minor notes / Request revision
- **Blocking issues resolved?** Yes/No per item with brief rationale
- **Should-fix items resolved?** Yes/No per item with brief rationale
- **New concerns** (if any)
- **Implementation readiness assessment**
