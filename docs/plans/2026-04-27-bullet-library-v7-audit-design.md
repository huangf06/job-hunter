# Bullet Library v7.0 Audit Design

**Date**: 2026-04-27
**Goal**: Comprehensive menu (~54-60 bullets) with every bullet calibrated to v3.0's proven signal density.

## Problem Statement

v3.0 (2026-02-08) produced 11/15 interview invitations. Subsequent versions regressed: v5.0 deleted interview-proven bullets, and rewrites across v4.0-v6.x reduced signal density under the guise of "truthfulness." The result: recruiter-perceived capability dropped below actual capability. This is not honesty; it is miscommunication.

**Root cause**: Author-perceived "truthfulness" strips the contextual signals (scale, scope, impact) that recruiters use to infer seniority. The fix is not inflation but signal calibration: ensuring every bullet sends signals that match the actual capability level.

## Method: v3.0 Baseline + Signal Density Gate (Approach C)

### Decision Framework (per bullet)

```
1. EXISTS in v3.0?
   YES -> Start with v3.0 text
          -> Check if any later version improved a specific signal dimension
          -> If yes: graft that improvement into v3.0 structure
          -> If no: keep v3.0 verbatim
   NO  -> Find best version text
          -> Apply 4-point signal checklist
          -> Rewrite if below 3/4

2. Signal checklist (must score >= 3/4 for headline bullets, >= 3/4 for all active):
   [ ] Strong verb (Engineered/Architected/Designed/Built/Spearheaded)
   [ ] Scale indicator (numbers, scope, users, records, team size)
   [ ] Technical specificity (named tools/methods, not generic)
   [ ] Business impact or "so what" (what it enabled, saved, prevented)

3. Hard rules:
   - No em dashes; use commas/semicolons
   - One achievement per bullet
   - Verb-first
   - Concrete numbers or verifiable tech details required
```

## Review Order (20 units, by importance)

| # | Experience | Est. Bullets | Key Decisions |
|---|-----------|-------------|---------------|
| 1 | GLP Technology | 8-9 | v3.0 restorations vs v3.2 additions |
| 2 | Baiquan Investment | 6 | Restore v3.0 text |
| 3 | Ele.me | 5-6 | v3.0 + v3.2 coexistence |
| 4 | Henan Energy | 3 | Signal-check v3.2 rewrites |
| 5 | Independent Investor | 1-2 | Signal-check (new section) |
| 6 | Thesis UQ/RL | 2-3 | Signal-check |
| 7 | Financial Data Lakehouse | 3-4 | No v3.0 baseline; write to standard |
| 8 | Greenhouse Sensor Pipeline | 2-3 | Same |
| 9 | Deribit Options | 1-2 | Restore v3.0 |
| 10 | Expedia Recommendation | 1 | Signal-check |
| 11 | ML4QS (IMU Sensor) | 1-2 | Signal-check |
| 12 | NLP Projects | 1-2 | Signal-check |
| 13 | GraphSAGE GNN | 1 | Signal-check |
| 14 | Deep Learning Fundamentals | 1-2 | Signal-check |
| 15 | Sequence Analysis (Bioinformatics) | 1-2 | Signal-check |
| 16 | Obama TTS Voice Cloning | 1 | Signal-check |
| 17 | LifeOS | 1 | Signal-check |
| 18 | Job Hunter Automation | 1-2 | Signal-check |
| 19 | Evolutionary Robotics | 1-2 | Signal-check |
| 20 | Strategic cuts | -- | bsc_thesis_oa, aoshen_business: keep/delete? |

## Inputs

- Current version: `assets/bullet_library.yaml` (v6.1, 54 bullets)
- Historical versions: `assets/bullet_library_versions/v*.yaml` (8 versions)
- Version overview: `assets/bullet_library_versions/README.md`
- Fact reference: `profiles/Profile2.0.pdf`
- Usage data: bullet_usage DB table (430 resumes)

## Output

- Direct edits to `assets/bullet_library.yaml`
- Version header updated to v7.0
- Per-experience decision log shown inline during review
- Target: ~54-60 active bullets

## Scope Exclusions

- YAML schema, metadata fields (status/tags/narrative_role) unchanged
- Non-bullet sections (skill_tiers, bio_builder, title_options, education, certifications) untouched
- recommended_sequences updated only if bullet IDs change
