# Bullet Library v7.1 Narrative Calibration — Design

**Date**: 2026-04-27
**Status**: Approved
**Goal**: Produce a narrative calibration report that evaluates every bullet from the perspective of 3 target role profiles, grounded in actual Dutch market JDs from the database.

## Problem Statement

v7.0 used a mechanical 4-point signal density checklist (strong verb, scale indicator, technical specificity, business impact). Interview data reveals this score does not predict interview effectiveness:
- `glp_pyspark`: 2/4 signal density, 17/17 interview resumes
- `lakehouse_orchestration`: 1/4 signal density, 14/17 interview resumes
- `glp_decision_engine`: 4/4 signal density, 1/17 interview resumes

Mechanical checklists cannot substitute for narrative judgment. v7.1 takes a different approach: build concrete role profiles from real JDs, then read each bullet through the hiring manager's eyes.

## Method

**Not** mechanical rewriting. Core method: establish a concrete picture of the target role, then reverse-engineer what signals each bullet should carry.

## Data Sources

- 53 active bullets in `assets/bullet_library.yaml` (v7.0)
- 17 interview rounds across 16 companies
- 432 resumes with bullet_usage tracking
- 13 interview JDs + 10 high-score non-interview JDs from the database
- Fact reference: bullet_library.yaml verified timeline + content

## Report Structure

```
docs/plans/2026-04-27-bullet-library-v7.1-narrative-calibration.md

0. Methodology
   - Data sources: 17 interviews, 432 resumes, 23 JDs
   - Definition of "narrative calibration"

1. Role Profiles (3x ~500 words)
   - Machine Learning Engineer (NL, mid-size 50-500)
   - AI Engineer (NL, startup to scale-up)
   - Data Engineer (NL, all sizes)
   Each: daily work / 6-second scan signals / "can start tomorrow" criteria
   All grounded in database JDs with source company attribution

2. Contradiction Resolution
   2.1 Core thesis: signal density != interview effectiveness
   2.2 Three case studies (glp_pyspark, lakehouse_orchestration, glp_decision_engine)
   2.3 Derived framework for narrative effectiveness
   2.4 Rewrite principles for v7.1

3. Bullet Calibration Table
   Grouped by experience (GLP -> BQ -> Ele.me -> ... -> Projects)
   Per bullet: interview data | MLE reading | AI Eng reading | DE reading | disposition | rewrite suggestion
   Dispositions: keep / reframe / demote / promote
   Rewrite suggestions only for "reframe" items

4. Appendix
   - Interview company-role-bullet usage detail
   - High-frequency technical keywords from database JDs
```

## Role Profile JD Sources

| Profile | Interview JDs | Supplementary High-Score JDs |
|---------|--------------|------------------------------|
| MLE | kaiko.ai (8.5), FareHarbor (7.5), Springer Nature (6.5), Elsevier (6.5) | RevoData (8.5), Qualcomm (8.5) |
| AI Engineer | kaiko.ai (8.5), Elsevier (6.5) | Aivory (8.5), Lumenalta (8.5), kaiko.ai Jr (8.5) |
| DE | Deloitte (8.5), Source.ag (7.5/6.5), Swisscom (7.5), Sensorfact (7.0), elipsLife (7.0), Aon (6.5) | Catawiki (8.5), Flow Traders (8.5), Tata Steel (8.5), McKinsey (8.5) |

Caveat: AI Engineer has fewer direct interview samples; profile relies more on supplementary JDs.

## Role Profile Methodology

Each profile answers 3 questions:
1. **Daily work reality** — not JD buzzwords, but what this person does after opening their laptop. Derived from JD responsibility sections, cross-referenced (3+ occurrences required).
2. **6-second scan signals** — what hiring managers look for in first pass. Two tiers: must-see (80%+ JD frequency) and bonus (40-80%). Derived from JD requirements sections.
3. **"Can start tomorrow" criteria** — what makes a hiring manager think the candidate needs minimal ramp-up. Derived from "nice to have" / "you'll thrive if" / "after 6 months" sections.

## Contradiction Resolution Methodology

Per case study:
1. Which interview resumes included it (role type distribution)
2. Same-group bullet interview rate comparison
3. Read the bullet from each role profile's perspective
4. Propose explanation, test against counterexamples

Working hypotheses (to be validated by data):
- **Recognizability > signal density**: recruiters pattern-match ("I know this"), not quality-score
- **Keyword anchoring**: some bullets carry value via ATS/scan keywords (Airflow, Docker, PySpark), not narrative
- **Narrative fit > narrative quality**: a bullet's value for a DE role depends on whether it reads like DE work, not whether it's well-written

## Scope

- Output: narrative calibration report (this design doc + the report itself)
- No direct edits to bullet_library.yaml — user reviews and approves changes manually
- No changes to YAML schema, metadata, or non-bullet sections
- Rewrite suggestions must preserve v3.0 interview-proven text structure where possible

## What Comes Next (after report)

User reviews the report, approves/rejects individual rewrite suggestions, then a separate session applies approved changes to bullet_library.yaml.
