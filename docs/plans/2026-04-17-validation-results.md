# Phase 5 Validation Results — 2026-04-17 Revert

## Scope

Confirm that the post-revert pipeline produces FULL_CUSTOMIZE resumes with the
interview-winning signals preserved: bio company hook, per-section role titles,
project reordering, flow-layout 2-page PDF.

## Rendered Sample: Action — Data Analyst, Commerce

- Job: `c06cc5aafff3` (only post-upgrade row that shipped as FULL_CUSTOMIZE)
- Template: DE (Data Analyst role routed via DE target_roles)
- Tier pre-revert: `FULL_CUSTOMIZE` (passes through guard unchanged)
- Render: succeeded with 2 non-blocking skill warnings (SAP, Data Visualization
  flagged as unverified — acceptable)
- Output: `output/Fei_Huang_Action_c06cc5aa_20260417_163621.pdf`

### Signal checks

| Signal | Expected | Observed |
|--------|----------|----------|
| Bio last sentence names company | "...to Action." | "Eager to bring these skills to Action." — **PASS** |
| Role titles rotate per section | per-company title | GLP = "Senior Data Scientist", BQ = "Quantitative Analyst", Ele.me = "Data Analyst", Henan = "Business Analyst" — **PASS** |
| Projects reorder by relevance | Expedia first (commerce/analytics), Lakehouse second | Expedia listed before Lakehouse — **PASS** |
| Flow-layout 2-page | Not zone single-page | 2-column flow template — **PASS** |

## Why No DE / ML / DS Re-Analysis

The Phase 5 plan originally called for re-analyzing 3 reference jobs (one per
template_id) and rendering each. We did not do this because:

1. Re-analyzing costs AI budget without explicit approval. Per
   `feedback_no_bulk_without_approval`, bulk operations require user go-ahead.
2. Pre-upgrade reference rows (kaiko.ai ML, Source.ag DE) fail current
   validation because `title_options.glp_technology` has tightened since they
   were generated — `Lead Data Engineer` and `ML Engineer and Team Lead` are
   no longer in the allowed list. Re-rendering them is not meaningful.
3. The Action render above already exercises the full FULL_CUSTOMIZE path end-
   to-end and demonstrates the three interview-winning signals are preserved.

## Fixes Discovered During Validation

Two regressions surfaced and were fixed in `536bb4f`:

1. **Silent static-PDF fallback on validation failure.** `render_resume` called
   `_render_template_copy` when the validator rejected output. This is the
   exact mechanism that produced 82% byte-identical PDFs across 77 post-upgrade
   applications (0 interviews). Now refuses to render and surfaces errors.
2. **Legacy pre-v3.0 rows (resume_tier=None) were skipped** instead of treated
   as FULL_CUSTOMIZE. These are the interview-winning baseline — they must
   render, not be rejected.

## Readiness for Phase 6

The pipeline is ready for a controlled rollout on a small batch (top 5
highest-scoring unapplied jobs). Do NOT bulk-run `--prepare` on the full
backlog until at least one Phase 6 batch is manually QA'd against the Action
sample above.

### Open question for user

Most high-score unapplied rows have `resume_tier = USE_TEMPLATE` with
`tailored_resume = "{}"`. These cannot be rendered without re-analysis. The
Phase 6 controlled rollout will require re-analyzing ~5 rows (AI spend ≈ cost
of 5 C2 calls). Requesting explicit approval before spending.
