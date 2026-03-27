# Codex Review Prompt: Block A Scraper Rebuild (v3 — Final)

## Your Role

You are reviewing **revision v3** of a design document for the scraping layer rebuild. The design is at `docs/plans/2026-03-26-block-a-scraper-rebuild.md`.

## Context

Two prior review rounds:
- v1 → Codex: "Request revision" (4 blocking + 5 should-fix). All resolved in v2.
- v2 → Codex: "Request revision" (2 remaining should-fix + 2 minor). All resolved in v3.

Prior reviews: `docs/plans/2026-03-26-block-a-scraper-rebuild-codex-review.md` and `docs/plans/2026-03-26-block-a-scraper-rebuild-codex-review-v2.md`.

## What to Verify

This is a third-pass review. The core architecture was approved in v2. Only two items remained open:

1. **#5 Profile compatibility (was should-fix, still open in v2):**
   - v3 decision: delete legacy profiles (`ml_data`, `backend_data`, `quick_test`) from config, update CI workflow inputs in the same change. No backward-compatible aliases.
   - Verify: is this clean-break approach explicitly stated and internally consistent across CLI examples, migration checklist, and config changes?

2. **#6 Metrics JSON contract (was should-fix, still open in v2):**
   - v3 decision: top-level `new_jobs` shim for Phase 1 compatibility, two-phase migration plan.
   - Verify: does the exact JSON example include all `ScrapeReport` fields (including `targets_failed`)? Is the consumer contract for `notify.py` and CI workflow unambiguous?

3. **Two minor concerns from v2:**
   - `targets_failed` missing from metrics example → should now be present
   - Repost detection intentionally absent from scrape-time metrics → should be explicitly stated

4. **Overall implementation readiness:**
   - Can a developer implement this design without asking clarifying questions?
   - Are there any remaining gaps or ambiguities?

## How to Review

- Read the "Revision History" section first to see what changed
- Verify the specific sections that were revised (§3 CLI, §6 Dedup, §7b Metrics, Migration Checklist, Config Changes)
- Cross-check against: `scripts/notify.py`, `.github/workflows/job-pipeline-optimized.yml`, `config/search_profiles.yaml`
- This should be a fast review — the scope is narrow

## Output Format

- **Verdict**: Approve / Approve with minor notes / Request revision
- **#5 resolved?** Yes/No + rationale
- **#6 resolved?** Yes/No + rationale
- **Minor concerns addressed?** Yes/No
- **Implementation readiness**: Ready / Not ready + what's missing
