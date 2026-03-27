# Block A Scraper Rebuild - Codex Review (v2)

> Date: 2026-03-26
> Reviewer: Codex
> Target: `docs/plans/2026-03-26-block-a-scraper-rebuild.md`
> Review scope: Second-pass review of revision v2 against prior blocking and should-fix feedback

## Verdict

Request revision

## Findings

1. **The CLI/profile compatibility contract is still internally inconsistent**

The revised design still uses the legacy example `--profile ml_data`, but the migration
checklist says workflow inputs should be updated to active profiles. In the current code,
`ml_data` and `backend_data` are disabled legacy profiles in `config/search_profiles.yaml`,
while the workflow still exposes those legacy inputs.

This needs one explicit contract:
- preserve legacy aliases in the new CLI, or
- remove legacy profile names everywhere and update workflow/docs in the same change

2. **The unified metrics migration is still not fully specified against real consumers**

Current consumers read a root-level `new_jobs` field from `data/scrape_metrics.json`:
- `scripts/notify.py`
- `.github/workflows/job-pipeline-optimized.yml`

The revised design switches to `total.new` and says `notify.py` will be updated, but it
does not explicitly define the workflow change for extracting the new count or whether a
temporary compatibility shim will exist.

The metrics schema direction is fine, but the artifact contract is still underspecified
for implementation handoff.

## Blocking Issues Resolved?

1. **#1 MD5 preserved:** Yes
   The design now explicitly keeps MD5 and matches `src/db/job_db.py:674`.

2. **#2 Sync public contract:** Yes
   `scrape()` is synchronous and async is used only internally where needed. That is coherent.

3. **#3 `is_healthy` / severity:** Yes
   `is_healthy` is now error-based, and `severity` distinguishes quiet-market, partial-failure,
   and broken-scraper states well enough.

4. **#4 Layer 2 dedup removed:** Yes
   Keeping repost detection downstream via `find_applied_duplicates()` is sufficient for the
   stated `--prepare`/checklist workflow.

## Should-Fix Items Resolved?

5. **#5 CI profile compatibility:** No
   The migration checklist moves in the right direction, but the design still mixes legacy and
   active profile contracts.

6. **#6 Unified metrics schema for `notify.py`:** No
   The schema is directionally correct, but the actual consumer contract is not pinned down for
   both `notify.py` and workflow output extraction.

7. **#7 `ScrapeReport` fields:** Yes
   `targets_attempted/succeeded/failed` and `dry_run` are sufficient at the report layer.

8. **#8 `new` vs `would_insert` in dry-run:** Yes
   The revised meaning is clear enough: `new` means "would have inserted" when `dry_run=True`.

9. **#9 Two-level error scope / `Retry-After`:** Yes
   Scraper-level fatal vs target-level recoverable failures is specified clearly enough for
   implementation.

## New Concerns

- The metrics example includes `targets_attempted` and `targets_succeeded` but omits
  `targets_failed`, even though the report model includes it. Minor, but it adds ambiguity
  to the metrics contract.
- Removing scraper-side Layer 2 dedup is fine for repost warnings during `--prepare`, but it
  also means repost-like patterns are no longer visible in scrape-time metrics. That is
  acceptable if intentional, but the design should say so explicitly.

## Implementation Readiness Assessment

Not ready to hand off yet.

The core architecture is now coherent, and all 4 previous blocking issues are resolved.
What remains is contract clarity:
- define the exact profile compatibility strategy
- define the exact JSON metrics contract consumed by both `scripts/notify.py` and the workflow

Once those two are pinned down, this should be ready to approve.

## Cross-Check References

- Design doc: `docs/plans/2026-03-26-block-a-scraper-rebuild.md`
- Prior review: `docs/plans/2026-03-26-block-a-scraper-rebuild-codex-review.md`
- DB job ID logic: `src/db/job_db.py:674`
- Repost detection: `src/db/job_db.py:1175`
- Notification consumer: `scripts/notify.py`
- Workflow consumer: `.github/workflows/job-pipeline-optimized.yml`
- Search profile config: `config/search_profiles.yaml`
