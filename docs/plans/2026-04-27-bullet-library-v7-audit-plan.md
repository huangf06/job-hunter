# Bullet Library v7.0 Audit — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Review all 54+ bullets across 20 experience units, calibrate each to v3.0's proven signal density using the 4-point checklist, and produce v7.0 of `assets/bullet_library.yaml`.

**Architecture:** Per-experience review: read all historical versions of that experience's bullets, compare texts, apply signal density gate (verb / scale / tech specificity / impact), pick or rewrite best version, edit YAML in-place. v3.0 text is the baseline for any bullet that existed in v3.0. Post-v3.0 bullets are evaluated against the same signal standard.

**Tech Stack:** YAML editing, `profiles/Profile2.0.pdf` for fact verification, `assets/bullet_library_versions/v*.yaml` for historical comparison.

**Key files:**
- Edit target: `assets/bullet_library.yaml`
- v3.0 (interview winner): `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml`
- v3.2 (github projects): `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml`
- v4.0 (narrative rewrite): `assets/bullet_library_versions/v4.0_narrative-rewrite_2026-03-10.yaml`
- v5.0 (aggressive cleanup): `assets/bullet_library_versions/v5.0_cleanup-narrative_2026-03-31.yaml`
- v6.0 (restoration): `assets/bullet_library_versions/v6.0_interview-data-rewrite_2026-04-22.yaml`
- v6.1 (current): `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml`
- Facts: `profiles/Profile2.0.pdf`
- Design: `docs/plans/2026-04-27-bullet-library-v7-audit-design.md`

**Signal Density Checklist (apply to every bullet):**

| # | Signal | Pass | Fail |
|---|--------|------|------|
| 1 | **Verb** | Spearheaded/Engineered/Architected/Designed/Built | Implemented/Created/Worked on/Helped |
| 2 | **Scale** | Numbers, scope (3,000+ stocks, 2.2M users, 150+ runs) | No numbers, no scope indicator |
| 3 | **Technical specificity** | Named tools/methods (PySpark, Fama-MacBeth, logistic regression) | Generic ("ML models", "data pipelines") |
| 4 | **Impact** | Business consequence ("enabling automated credit decisions") | Ends at technical description |

**Hard rules:** No em dashes (use commas/semicolons). One achievement per bullet. Verb-first. Concrete numbers required.

---

## Task 1: GLP Technology (8-9 bullets, highest priority)

**Files:**
- Modify: `assets/bullet_library.yaml:100-181` (glp_technology section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:108-140` (GLP in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:136-165` (GLP in v3.2)
- Read: `assets/bullet_library_versions/v4.0_narrative-rewrite_2026-03-10.yaml:148-175` (GLP in v4.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml:128-180` (GLP current)
- Reference: `profiles/Profile2.0.pdf` for GLP facts

**Bullet ID map across versions:**

| Bullet ID | v3.0 | v3.2 | v4.0 | v5.0 | v6.1 | Usage |
|-----------|------|------|------|------|------|-------|
| glp_founding_member | YES | YES | YES | YES | YES | 430x |
| glp_pyspark | YES | -- | -- | -- | YES (restored) | 414x |
| glp_data_quality | YES* | -- | -- | -- | YES (restored) | 364x |
| glp_portfolio_monitoring | YES | YES | YES | YES | YES | 359x |
| glp_data_compliance | YES | -- | -- | -- | YES (restored) | -- |
| glp_payment_collections | YES | -- | -- | -- | YES (restored) | -- |
| glp_generalist | YES | YES | YES | YES | YES | -- |
| glp_data_engineer | YES | YES | YES | YES | deprecated in v6.1 | -- |
| glp_decision_engine | -- | YES (new) | YES | YES | YES | 64x |

*v3.0 had `glp_data_quality` but under a different name; check actual content.

**Step 1: Read all GLP bullets across versions**

Read v3.0 GLP section (lines ~108-140), v3.2 GLP section (lines ~136-165), v4.0 GLP section (lines ~148-175), and current v6.1 GLP section (lines ~128-180). For each bullet, extract the `content:` text.

**Step 2: Compare per-bullet, apply signal checklist**

For each of the 9 bullets:
1. Show the v3.0 text (if exists) and the current v6.1 text side by side
2. Note any intermediate version that changed the text
3. Score both on the 4-point checklist
4. Decision: keep v3.0 / keep v6.1 / graft improvement / rewrite
5. State reasoning

**Step 3: Edit `assets/bullet_library.yaml` GLP section**

Apply all decisions. Keep metadata (status, tags, narrative_role) unchanged unless a bullet is being deprecated or restored. Update `recommended_sequences` only if bullet IDs changed.

**Step 4: Verify YAML syntax**

Run: `python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml'))" && echo "YAML OK"`
Expected: "YAML OK"

**Step 5: Present decisions to user for approval before moving to next task**

---

## Task 2: Baiquan Investment (6 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:220-281` (baiquan_investment section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:168-200` (BQ in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:233-255` (BQ in v3.2)
- Read: `assets/bullet_library_versions/v4.0_narrative-rewrite_2026-03-10.yaml:245-265` (BQ in v4.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml:246-280` (BQ current)

**Bullet ID map:**

| Bullet ID | v3.0 | v3.2 | v4.0 | v5.0 | v6.1 | Usage |
|-----------|------|------|------|------|------|-------|
| bq_de_pipeline | YES | YES | YES | YES | YES | 344x |
| bq_de_factor_engine | YES | -- | -- | -- | YES (restored) | 409x |
| bq_de_backtest_infra | YES | YES | YES | YES | YES | 119x |
| bq_factor_research | YES | YES | YES | YES | YES | 143x |
| bq_futures_strategy | YES | YES | YES | YES | YES | 51x |
| bq_data_quality | YES | -- | -- | -- | YES (restored) | 161x |

**Steps:** Same as Task 1 — read all versions, compare per-bullet, apply signal checklist, edit, verify YAML, present to user.

---

## Task 3: Ele.me (5-6 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:340-401` (eleme section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:246-270` (Ele.me in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:337-355` (Ele.me in v3.2)
- Read: `assets/bullet_library_versions/v4.0_narrative-rewrite_2026-03-10.yaml:348-367` (Ele.me in v4.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml:364-401` (Ele.me current)

**Bullet ID map:**

| Bullet ID | v3.0 | v3.2 | v4.0 | v5.0 | v6.1 | Usage |
|-----------|------|------|------|------|------|-------|
| eleme_ab_testing | YES | -- (merged) | -- | -- | YES (restored) | 320x |
| eleme_sql_reporting | YES | -- (merged) | -- | -- | -- | -- |
| eleme_user_segmentation | YES | YES | YES | YES | YES | -- |
| eleme_fraud_detection | -- | YES (new) | YES | YES | YES | 68x |
| eleme_sql_optimization | -- | YES (new) | YES | YES | YES | 170x |
| eleme_bi_dashboards | -- | YES (new) | YES | -- | -- | -- |
| eleme_kmeans | -- | -- | -- | -- | YES (new in v6.1) | 110x |
| eleme_sql_simple | -- | -- | -- | -- | YES (new in v6.1) | -- |

**Key decision:** v3.0 had 3 bullets (ab_testing, sql_reporting, user_segmentation). v3.2 replaced them with 4 new ones. v6.1 has 6 bullets (both originals and replacements). Evaluate whether all 6 earn their slot or if some overlap.

**Steps:** Same pattern. Extra attention to overlap between restored originals and their v3.2 replacements.

---

## Task 4: Henan Energy (3 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:283-327` (henan_energy section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:202-228` (HE in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:282-302` (HE in v3.2)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml:310-327` (HE current)

**Bullet ID map:**

| Bullet ID | v3.0 | v3.2+ | v6.1 | Notes |
|-----------|------|-------|------|-------|
| he_operations_management | YES | -- | -- | Replaced by he_data_automation |
| he_demand_forecasting | YES | -- | -- | Replaced by he_supply_chain_analytics |
| he_performance_evaluation | YES | -- | -- | Merged into he_data_standardization |
| he_stakeholder_reporting | YES | -- | -- | Dropped |
| he_data_automation | -- | YES | YES | Replaced he_operations_management |
| he_supply_chain_analytics | -- | YES | YES | Replaced he_demand_forecasting |
| he_data_quality | -- | YES | YES | New |
| he_data_standardization | -- | v3.2-v4.0 | -- | Dropped in v5.0 |

**Key decision:** The v3.2 rewrite repositioned Henan from generic "operations" to "data automation" framing, which is more relevant for data roles. But do the v3.2 texts have sufficient signal density? Compare both framings.

**Steps:** Same pattern.

---

## Task 5: Independent Investor (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:182-218` (independent_investor section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:142-165` (career transition in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:190-206` (indie in v3.2)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml:207-218` (current)

**Notes:** v3.0 had 4 bullets (pt_personal_trading, pt_grad_prep, pt_language_learning, pt_philosophy). v3.2 rewrote to indie_quant_research + indie_skill_development + indie_market_analysis. v6.1 has 2 (indie_quant_research, indie_skill_development). Signal-check the 2 survivors.

**Steps:** Same pattern.

---

## Task 6: Thesis UQ/RL (2-3 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:408-437` (thesis_uq_rl section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:275-292` (thesis in v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (thesis current)

**Bullet IDs:** thesis_uq_framework (184x), thesis_noise_paradox (184x), thesis_calibration. All exist from v3.0. Compare v3.0 vs current text.

**Steps:** Same pattern.

---

## Task 7: Financial Data Lakehouse (3-4 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:586-618` (financial_data_lakehouse section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:397-416` (lakehouse in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:548-560` (lakehouse in v3.2)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** lakehouse_streaming (363x), lakehouse_quality (330x), lakehouse_optimization (92x), lakehouse_orchestration (191x). All exist from v3.0. High usage = high value. Signal-check each.

**Steps:** Same pattern.

---

## Task 8: Greenhouse Sensor Pipeline (2-3 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:619-647` (greenhouse_sensor_pipeline section)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:570-580` (first appeared v3.2)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** greenhouse_etl_pipeline (167x), greenhouse_data_quality (119x), greenhouse_aggregations. New in v3.2, no v3.0 baseline. Apply signal checklist fresh.

**Steps:** Same pattern.

---

## Task 9: Deribit Options (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:648-668` (deribit_options section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:294-308` (deribit in v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** deribit_options_system (34x), deribit_risk_management. Existed in v3.0, deprecated in v4.0, restored in v6.0. Compare v3.0 vs current text.

**Steps:** Same pattern.

---

## Task 10: Expedia Recommendation (1 bullet)

**Files:**
- Modify: `assets/bullet_library.yaml:462-477` (expedia_recommendation section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:326-337` (v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet ID:** expedia_ltr (103x). Existed from v3.0. Compare texts, signal-check.

**Steps:** Same pattern.

---

## Task 11: ML4QS / IMU Sensor (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:478-501` (ml4qs section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:339-353` (v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** ml4qs_pipeline, ml4qs_deep_learning. Both from v3.0. Signal-check.

**Steps:** Same pattern.

---

## Task 12: NLP Projects (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:438-459` (nlp_projects section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:310-324` (v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** nlp_poem_generator (42x), nlp_dependency_parsing. Both from v3.0. Signal-check.

**Steps:** Same pattern.

---

## Task 13: GraphSAGE GNN (1 bullet)

**Files:**
- Modify: `assets/bullet_library.yaml:502-517` (graphsage_gnn section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:355-366` (v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet ID:** graphsage_ppi. From v3.0. Signal-check.

**Steps:** Same pattern.

---

## Task 14: Deep Learning Fundamentals (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:563-584` (deep_learning_fundamentals section)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:513-520` (first appeared v3.2)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** dnn_scratch, dnn_architecture. New in v3.2, no v3.0 baseline. Signal-check.

**Steps:** Same pattern.

---

## Task 15: Sequence Analysis / Bioinformatics (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:541-562` (sequence_analysis section)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:495-502` (first appeared v3.2)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet IDs:** bioinfo_hmm, bioinfo_alignment. New in v3.2. Signal-check.

**Steps:** Same pattern.

---

## Task 16: Obama TTS Voice Cloning (1 bullet)

**Files:**
- Modify: `assets/bullet_library.yaml:670-685` (obama_tts section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:368-379` (v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet ID:** obama_tts_voice_cloning (36x). From v3.0. Signal-check.

**Steps:** Same pattern.

---

## Task 17: LifeOS (1 bullet)

**Files:**
- Modify: `assets/bullet_library.yaml:686-701` (lifeos section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:419-430` (v3.0)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Bullet ID:** lifeos_system. From v3.0. Signal-check.

**Steps:** Same pattern.

---

## Task 18: Job Hunter Automation (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:702-723` (job_hunter_automation section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:432-443` (v3.0 — only job_hunter_system)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current — has job_hunter_system + job_hunter_operations)

**Bullet IDs:** job_hunter_system (58x), job_hunter_operations (new in v6.x). Signal-check both.

**Steps:** Same pattern.

---

## Task 19: Evolutionary Robotics (1-2 bullets)

**Files:**
- Modify: `assets/bullet_library.yaml:518-540` (evolutionary_robotics_research section)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:381-395` (v3.0 — ec_robotics, ec_statistical_analysis)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:477-484` (v3.2 — neuroevo_robotics, neuroevo_system)
- Read: `assets/bullet_library_versions/v6.1_current_2026-04-27.yaml` (current)

**Note:** v3.0 had ec_robotics + ec_statistical_analysis. v3.2 rewrote as neuroevo_robotics + neuroevo_system. Different IDs, same project. Compare both sets.

**Steps:** Same pattern.

---

## Task 20: Strategic Cuts (bsc_thesis_oa, aoshen_business)

**Files:**
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:230-244` (aoshen in v3.0)
- Read: `assets/bullet_library_versions/v3.0_high-impact-rewrite_2026-02-08.yaml:445-468` (bsc_thesis_oa in v3.0)
- Read: `assets/bullet_library_versions/v3.2_github-projects_2026-03-09.yaml:615-630` (bsc in v3.2)
- Read: `assets/bullet_library.yaml:329-340` (aoshen comment block in current)

**Decision framework:**
- **aoshen_business**: 4-month overlap with Ele.me period. Currently deleted with comment block in v6.1. v3.0 had 1 bullet (aoshen_trade_analysis). Evaluate: does it add value as a separate entry, or is it noise?
- **bsc_thesis_oa**: BSc thesis project with 5 bullets in v3.0 (Java production system). Deleted entirely in v3.2+. Evaluate: is a BSc project from 2010 worth resume space when competing with MSc thesis + portfolio projects?

**Steps:**
1. Read all historical versions of these entries
2. Decide keep/delete for each, with reasoning
3. If keeping: apply signal checklist and edit into `assets/bullet_library.yaml`
4. If deleting: ensure they remain absent (verify no orphan references)
5. Present decisions to user

---

## Task 21: Finalize v7.0

**Files:**
- Modify: `assets/bullet_library.yaml:1-28` (header block)

**Step 1: Update version header**

Change the header comment from `v6.0` to `v7.0` with a changelog summarizing all decisions made in Tasks 1-20.

**Step 2: Verify final bullet count**

Run: `grep -c "- id:" assets/bullet_library.yaml`
Expected: 54-60 active bullets

**Step 3: Verify no deprecated bullets are referenced in recommended_sequences**

Run: `python -c "import yaml; data=yaml.safe_load(open('assets/bullet_library.yaml')); [print(f'WARN: {k}') for k,v in {**data.get('work_experience',{}), **data.get('projects',{})}.items() if 'recommended_sequences' in (v or {}) for seq in (v.get('recommended_sequences',{}) or {}).values() for bid in seq if any(b['id']==bid and b.get('status')=='deprecated' for b in (v.get('verified_bullets',[])))]; print('CHECK DONE')"`
Expected: no WARN lines, just "CHECK DONE"

**Step 4: Full YAML validation**

Run: `python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml')); print('YAML OK')"`
Expected: "YAML OK"

**Step 5: Copy to version archive**

Run: `cp assets/bullet_library.yaml assets/bullet_library_versions/v7.0_signal-calibrated_2026-04-27.yaml`

**Step 6: Commit**

```bash
git add assets/bullet_library.yaml assets/bullet_library_versions/v7.0_signal-calibrated_2026-04-27.yaml
git commit -m "feat: bullet library v7.0 — signal-calibrated audit

v3.0 baseline + 4-point signal density gate across all 20 experience
units. Every bullet calibrated for recruiter-perceived signal strength
matching actual capability level.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```
