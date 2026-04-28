# Bullet Library Version Archive

All historical versions extracted from git for the v7.0 audit.

## Version Timeline & Interview Correlation

```
Version | Date       | Bullets | Interviews Won (from interview_prep/)
--------|------------|---------|--------------------------------------
v1.0    | 2026-02-04 |   36    | 0 (pre-launch)
v2.0    | 2026-02-07 |   40    | 0 (1-day lifespan)
v3.0    | 2026-02-08 |   50    | 11 (nebius, Deloitte, FareHarbor x2, Source.ag,
        |            |         |     MaishaMazuri, Sensorfact, TomTom, Elsevier,
        |            |         |     Eneco, Swisscom)
v3.2    | 2026-03-09 |   53    | (merged into v4.0 next day)
v4.0    | 2026-03-10 |   50    | 3 (kaiko.ai, ENPICOM, ABN AMRO)
v5.0    | 2026-03-31 |   42    | 1 (Aon) — deleted several interview-proven bullets
v6.0    | 2026-04-22 |   51    | 0 (restored v3.0 bullets, but pipeline paused)
v6.1    | 2026-04-27 |   54    | (current, under review)
```

## Key Observation

**v3.0 is the proven winner**: 11 out of 15 interviews came from resumes built with v3.0 bullets.
v5.0 deleted multiple interview-proven bullets and saw a significant drop.
v6.0 attempted to restore v3.0 bullets but hasn't been tested at scale yet.

## Top Bullets by Usage (from bullet_usage DB)

| Uses | Bullet ID                  | Interview-proven? |
|------|----------------------------|--------------------|
| 430x | glp_founding_member       | Yes (v3.0 original) |
| 414x | glp_pyspark               | Yes (v3.0 original) |
| 409x | bq_de_factor_engine       | Yes (v3.0 original) |
| 364x | glp_data_quality          | Yes (v3.0 original) |
| 363x | lakehouse_streaming       | New in v3.2+        |
| 359x | glp_portfolio_monitoring  | Yes (v3.0 original) |
| 344x | bq_de_pipeline            | Yes (v3.0 original) |
| 330x | lakehouse_quality         | New in v3.2+        |
| 320x | eleme_ab_testing          | Yes (v3.0 original) |

## Files

- `v1.0_initial_2026-02-04.yaml` — First version
- `v2.0_bullet-by-id_2026-02-07.yaml` — Added bullet IDs
- `v3.0_high-impact-rewrite_2026-02-08.yaml` — **INTERVIEW-WINNING VERSION**
- `v3.2_github-projects_2026-03-09.yaml` — Added GitHub project bullets
- `v4.0_narrative-rewrite_2026-03-10.yaml` — Narrative restructure
- `v5.0_cleanup-narrative_2026-03-31.yaml` — Cleanup (deleted too aggressively)
- `v6.0_interview-data-rewrite_2026-04-22.yaml` — Restoration attempt
- `v6.1_current_2026-04-27.yaml` — Current state
