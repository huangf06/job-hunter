# Post-Upgrade Zero-Interview Diagnostic — 2026-04-17

> **For Claude:** This memo captures the root cause analysis that informs Phase 4 of
> `docs/plans/2026-04-17-resume-template-revert-plan.md`. Read this before auditing the C2 prompt.

## Trigger

After the 2026-04-01/02 pipeline upgrade (3-tier routing: `USE_TEMPLATE` / `ADAPT_TEMPLATE` / `FULL_CUSTOMIZE`), 77 applications produced **0 interview invitations** — vs ~14 interviews from ~400 applications pre-upgrade (~3.5% baseline).

## Hard Data (from `job_analysis` + `applications`)

**Post-2026-04-02 tier distribution (74 applications with analysis):**

| tier | template | n | % |
|------|----------|---|---|
| USE_TEMPLATE | DE | 35 | 47% |
| USE_TEMPLATE | ML | 21 | 28% |
| USE_TEMPLATE | DS | 5 | 7% |
| ADAPT_TEMPLATE | DE/ML | 12 | 16% |
| **FULL_CUSTOMIZE** | DE | **1** | **1%** |

**`USE_TEMPLATE` reality:** `tailored_resume = "{}"`. Same static PDF (`templates/pdf/Fei_Huang_DE.pdf` etc.) sent byte-identical to 35 DE companies, 21 ML companies, 5 DS companies. **Zero per-job customization.**

## Pre-Upgrade Interview Sample (8 resumes read)

Sources: `interview_prep/20260225_Source_ag`, `20260226_Sensorfact`, `20260227_TomTom`, `20260302_Elsevier`, `20260304_Swisscom`, `20260305_FareHarbor`, `20260311_kaiko_ai`, `20260316_ENPICOM`, `20260320_ABN_AMRO`.

All 8 are 2-page flow-layout, AI per-job tailored. They share three signals that the static template lacks:

### Signal 1 — Bio last sentence names the target company

| Resume | Bio closing |
|---|---|
| Sensorfact | `...Eager to bring these skills to Sensorfact.` |
| Source.ag | `...Eager to bring these skills to Source.ag.` |
| Elsevier | `...Eager to bring these skills to Elsevier.` |
| kaiko.ai | `...Eager to bring these skills to kaiko.ai.` |
| ABN AMRO | `...Eager to bring these skills to ABN AMRO Bank N.V.` |

Static `Fei_Huang_DE_Resume.html` bio has **no company mention**.

### Signal 2 — Bio first sentence tailored to JD vocabulary

Role framing and domain-second-clause are JD-adapted:

| Resume | Bio opening (second clause after "X years of experience in") |
|---|---|
| Sensorfact | `...scalable data pipelines and ETL systems **and anomaly detection and monitoring systems**` (matches their IoT monitoring JD) |
| Source.ag | `...scalable data pipelines and ETL systems **and credit scoring and risk analytics**` (matches their commercial analytics JD) |
| Catawiki | `...scalable data pipelines and ETL systems **and data quality and governance frameworks**` |
| ABN AMRO (ML) | `**ML Engineer** with 6 years of experience in ML model development and deployment and scalable data pipelines` |
| kaiko.ai (ML) | `**ML Engineer** with 6 years of experience in ML model development and deployment and scalable data pipelines` |

Static DE resume has one fixed bio: `"Data Engineer with 6+ years of experience building data platforms across e-commerce, market data, and credit risk."` — used for all 35 DE apps regardless of JD.

### Signal 3 — Role title switches by template_id (DE/ML/DS)

Same GLP role, different title by application:

| Application | GLP job title in resume |
|---|---|
| Source.ag (DE) | `Data Engineer & Team Lead` |
| Sensorfact (DE) | `Data Engineer & Team Lead` |
| Elsevier (ML) | `ML Engineer & Team Lead` |
| kaiko.ai (ML) | `ML Engineer and Team Lead` |
| ABN AMRO (ML) | `ML Engineer & Team Lead` |

### Signal 4 — Projects reordered by JD priority

Pre-upgrade resumes promote the most JD-relevant project to position #1:

| Application | Top project |
|---|---|
| kaiko.ai (Evaluation ML) | **UQ Benchmark** (thesis, evaluation-heavy) ← first |
| Source.ag (DE) | **Financial Data Lakehouse** ← first |
| Sensorfact (DE, monitoring) | **Financial Data Lakehouse** ← first |
| Elsevier (MLOps) | **Financial Data Lakehouse** ← first, then **Expedia Ranking** |
| ABN AMRO (ML) | **Financial Data Lakehouse**, then **Thesis** |

Static `Fei_Huang_DE_Resume.html` has only **1 project** (`Greenhouse Sensor Data Pipeline`) for all DE apps — no reordering possible, no JD-relevance match.

## Bullet-Strength Is Not the Root Cause

Static template bullets contain concrete numbers (`51,000+ suspicious order clusters`, `2.2M+ users`, `29 rejection rules`, `500GB→100GB scan reduction`, `founding data engineer`). Honesty level is **equivalent** to pre-upgrade interview resumes — no visible "honesty tax" on content.

The structural problem is uniformity: every bullet in every application is identical, because the static PDF has no per-job interpolation. The flow-layout interview resumes have bullet *selection* and *framing* per job, not stronger bullets per se.

## One Caveat — Absolute-Positioning Splits Bullets

Static template uses `position:absolute` with each bullet line as a separate `<div class="line" style="left:42pt; top:176.4pt">`. Example:

```html
<div class="line body" style="top:176.4pt">Built the credit risk data platform from scratch as the</div>
<div class="line body" style="top:189.4pt">founding data engineer, enabling production lending</div>
<div class="line body" style="top:202.4pt">workflows across ingestion, Redshift warehousing,</div>
<div class="line body" style="top:215.4pt">automated decisioning, and post-loan monitoring.</div>
```

One narrative bullet is 4 pixel-positioned divs with no `<li>` / `<ul>`. Visually bulleted, semantically fragments. This compounds the uniformity problem but isn't the primary driver — even a beautifully-formatted uniform resume wouldn't solve zero-interview if it says the same thing to every company.

## Aon Post-Upgrade "Interview" — Not a New-Pipeline Win

`interview_prep/20260415_Aon_Lead_Data_Engineer/03_submitted_resume.md` notes:
- **Applied 2026-02-13** (pre-upgrade)
- Originally rejected in DB
- Interview invitation received 2026-04-07 (delayed reconsideration)

So Aon is a pre-upgrade application that resurfaced, not a post-upgrade new-pipeline outcome.

**Post-upgrade new-pipeline interview count: 0 / 77.**

## Why Revert Rather Than Fuse

The three new-pipeline features (3-tier classifier, zone 1-page templates, `slot_schema`) collectively produced a measurable hiring-signal regression: ~3.5% → 0%. None has evidence of positive contribution to interview rate.

The only salvageable asset from the upgrade is `config/template_registry.yaml`'s `target_roles` / `bio_positioning` / `key_strengths` metadata — useful as a C2 prompt hint to stabilize DE/ML/DS role framing. This is data, not infrastructure; we keep it without keeping the tier classifier or zone renderer.

## Phase 4 C2 Prompt Audit — Required Checks

The revert plan's Phase 4 C2 prompt audit should verify the AI output produces all four signals above, tested with failing tests first:

1. **Bio closing**: Last sentence of `bio` must contain the target company name (exact match against `job.company`)
2. **Bio JD framing**: First sentence's second clause reflects JD vocabulary (harder to unit-test — probably needs rubric + sample job + visual review)
3. **Role title alignment**: When `template_id_final == "DE"`, GLP role title contains "Data Engineer"; when `== "ML"`, contains "ML Engineer" or "Machine Learning"
4. **Projects ordering**: For ML roles, UQ Benchmark or thesis-related project appears in top-2; for DE roles, Financial Data Lakehouse appears in position 1

These are the hiring-signal checks, in addition to the plan's existing checks (3-5 bullets per role, 6 skill categories, etc.).

## Reference Samples for Phase 5 Validation

When validating post-revert renders, diff against these known-good interview resumes:

- **DE reference**: `interview_prep/20260225_Source_ag_Data_Engineer/03_submitted_resume.md`
- **ML reference**: `interview_prep/20260311_kaiko_ai_Senior_Evaluation_ML_Engineer/03_submitted_resume.md`
- **DS reference**: (none in interview_prep — 0 DS interviews pre-upgrade; use pre-upgrade `job_analysis` tailored_resume for a DS application as the positive example)

Commit: 6a1a2f7 retired the renderer dispatch to USE_TEMPLATE/ADAPT_TEMPLATE.
