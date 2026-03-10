# Narrative Architecture Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply the approved narrative architecture design to `assets/bullet_library.yaml`, transforming disconnected bullets into a coherent career story.

**Architecture:** Direct YAML edits to bullet content, narrative_role tags, and metadata. No code changes — this is pure content work.

**Tech Stack:** YAML editing. Validate with `python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml'))"` after each task.

**Design doc:** `docs/plans/2026-03-10-narrative-architecture-design.md`

---

### Task 1: Henan Energy — Rewrite headlines + update metadata

**Files:**
- Modify: `assets/bullet_library.yaml` (Henan Energy section, lines ~258-302)

**Step 1: Update default title**

Find:
```yaml
    titles:
      default: "Business Supervisor"
      supply_chain: "Supply Chain & Operations Supervisor"
      data_analyst: "Business Analyst"
      data_engineer: "Data Operations Analyst"
```

Replace with:
```yaml
    titles:
      default: "Business Analyst"
      supply_chain: "Supply Chain & Operations Supervisor"
      data_analyst: "Business Analyst"
      data_engineer: "Data Operations Analyst"
```

**Step 2: Rewrite `he_data_automation`**

Find:
```yaml
      - id: he_data_automation
        narrative_role: depth_prover
        content: "Built automated data aggregation pipeline consolidating operational data from 12+ subsidiaries, reducing manual processing time by 92% (2 days → 2 hours) through VBA-based ETL automation — early-stage data engineering using available technology before modern tools existed."
```

Replace with:
```yaml
      - id: he_data_automation
        narrative_role: headline
        content: "Built automated pipeline to ingest, validate, and consolidate non-standardized Excel reports from 20+ business units into unified operational reporting, reducing monthly processing from 2 days to under 2 hours."
```

**Step 3: Rewrite `he_supply_chain_analytics`**

Find:
```yaml
      - id: he_supply_chain_analytics
        narrative_role: foundation
        content: "Designed and implemented supply chain analytics system tracking inventory and sales across Fortune 500 company (200B RMB revenue), generating 261M RMB ($42M) in profit over 3 years through data-driven optimization of procurement timing and product mix."
```

Replace with:
```yaml
      - id: he_supply_chain_analytics
        narrative_role: headline
        content: "Designed the group's supply chain analytics framework from scratch, tracking daily sales and inventory to guide procurement and sales timing; optimization guided by this framework contributed to €32M in documented profit improvements across business units over 3 years."
```

**Step 4: Update narrative_role for optional bullets**

Find and replace `narrative_role: extension` → `narrative_role: optional` for `he_data_quality`.
Find and replace `narrative_role: breadth` → `narrative_role: optional` for `he_data_standardization`.

**Step 5: Update recommended_sequences** (remove references to deprecated bullet IDs)

Find:
```yaml
    recommended_sequences:
      data_engineer: ["he_data_automation", "he_supply_chain_analytics", "he_data_quality"]
      data_analyst: ["he_supply_chain_analytics", "he_performance_evaluation", "he_data_automation"]
      supply_chain: ["he_supply_chain_analytics", "he_operations_management", "he_performance_evaluation"]
      data_governance: ["he_data_quality", "he_data_standardization", "he_data_automation"]
```

Replace with:
```yaml
    recommended_sequences:
      data_engineer: ["he_data_automation", "he_supply_chain_analytics", "he_data_quality"]
      data_analyst: ["he_supply_chain_analytics", "he_data_automation", "he_data_quality"]
      data_governance: ["he_data_quality", "he_data_standardization", "he_data_automation"]
```

(Removed `he_performance_evaluation` and `he_operations_management` references — these IDs don't exist. Removed `supply_chain` template.)

**Step 6: Validate YAML**

Run: `python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml', encoding='utf-8'))"`
Expected: No errors.

**Step 7: Commit**

```bash
git add assets/bullet_library.yaml
git commit -m "narrative: rewrite Henan Energy headlines + update metadata (v4.0)"
```

---

### Task 2: Ele.me — Rewrite headlines

**Files:**
- Modify: `assets/bullet_library.yaml` (Ele.me section, lines ~317-355)

**Step 1: Rewrite `eleme_fraud_detection`**

Find:
```yaml
      - id: eleme_fraud_detection
        narrative_role: depth_prover
        content: "Built anti-fraud detection system identifying 51,000+ suspicious order clusters using 3 pattern detection algorithms (same-phone matching, high-frequency users, repeat orders) — protected 651K RMB in GMV and prevented fraudulent subsidy claims across 2.2M+ users."
```

Replace with:
```yaml
      - id: eleme_fraud_detection
        narrative_role: headline
        content: "Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern algorithms (same-phone, high-frequency, repeat-order matching), preventing fraudulent subsidy claims during hyper-growth."
```

**Step 2: Rewrite `eleme_sql_optimization`**

Find:
```yaml
      - id: eleme_sql_optimization
        narrative_role: foundation
        content: "Optimized 90+ Hadoop/Hive SQL queries through partition pruning and subquery pushdown, achieving 5x query speedup (500GB → 100GB scanned) — enabled cross-functional teams to access real-time analytics on 30+ data warehouse tables."
```

Replace with:
```yaml
      - id: eleme_sql_optimization
        narrative_role: headline
        content: "Optimized 90+ Hadoop/Hive queries through partition pruning and subquery pushdown, cutting scan volume 5x (500GB → 100GB) and unlocking real-time analytics on 30+ warehouse tables for fraud detection, operations, and marketing teams."
```

**Step 3: Update narrative_role for optional bullets**

Change `eleme_user_segmentation` narrative_role from `extension` to `optional`.
Change `eleme_bi_dashboards` narrative_role from `breadth` to `optional`.

**Step 4: Validate YAML + Commit**

```bash
python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml', encoding='utf-8'))"
git add assets/bullet_library.yaml
git commit -m "narrative: rewrite Ele.me headlines, drop EUR amount (v4.0)"
```

---

### Task 3: Baiquan — Update pipeline bullet + add team context

**Files:**
- Modify: `assets/bullet_library.yaml` (Baiquan section, lines ~209-253)

**Step 1: Add team_size to company metadata**

Find:
```yaml
  baiquan_investment:
    company: "Baiquan Investment"
    company_type: "Quantitative hedge fund"
    location: "Beijing, China"
```

Replace with:
```yaml
  baiquan_investment:
    company: "Baiquan Investment"
    company_type: "Quantitative hedge fund, 5-person team"
    location: "Beijing, China"
```

**Step 2: Update `bq_de_pipeline` ending**

Find:
```yaml
        content: "Built end-to-end market data ingestion pipeline processing 3,000+ A-share securities and 5+ years of tick-level futures data from multiple vendor feeds; implemented corporate action handling and deduplication logic ensuring data integrity for quantitative research."
```

Replace with:
```yaml
        content: "Built end-to-end market data ingestion pipeline processing 3,000+ A-share securities and 5+ years of tick-level futures data from multiple vendor feeds; implemented corporate action handling and deduplication logic ensuring data integrity for all downstream research and live trading."
```

**Step 3: Update narrative_roles**

Change `bq_de_pipeline` from `context_setter` to `headline`.
Change `bq_factor_research` from `foundation` to `headline`.
Keep `bq_de_backtest_infra` as `optional` (was `depth_prover`).
Keep `bq_futures_strategy` as `headline` (was `depth_prover`).

Note: bq_futures_strategy is headline for ML/Quant templates but optional for DE. The `recommended_sequences` already handle this distinction — the narrative_role just needs to be `headline` since it's headline in at least one template.

**Step 4: Validate YAML + Commit**

```bash
python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml', encoding='utf-8'))"
git add assets/bullet_library.yaml
git commit -m "narrative: update Baiquan pipeline bullet + add team context (v4.0)"
```

---

### Task 4: Independent — Rewrite bullets + deprecate market_analysis

**Files:**
- Modify: `assets/bullet_library.yaml` (Independent section, lines ~168-206)

**Step 1: Rewrite `indie_quant_research`**

Find:
```yaml
      - id: indie_quant_research
        narrative_role: context_setter
        content: "Conducted independent quantitative research on Chinese equity markets, building automated data pipeline (83K+ records, 3,600+ stocks) to track institutional flows and high-momentum patterns; developed Python-based analysis tools using Tushare API and MySQL — maintained technical proficiency while deepening market microstructure understanding."
```

Replace with:
```yaml
      - id: indie_quant_research
        narrative_role: headline
        content: "Built automated equity research pipeline processing 83K+ daily records across 3,600+ stocks via Tushare API and MySQL; implemented institutional flow tracking and momentum signal detection for systematic market analysis."
```

**Step 2: Rewrite `indie_skill_development`**

Find:
```yaml
      - id: indie_skill_development
        narrative_role: extension
        content: "Pursued self-directed learning in advanced topics (machine learning, reinforcement learning, German language) while preparing for graduate studies — admitted to M.Sc. AI program at VU Amsterdam in 2023."
```

Replace with:
```yaml
      - id: indie_skill_development
        narrative_role: optional
        content: "Self-directed study in data science and machine learning, pivoting to AI after the emergence of large language models; admitted to M.Sc. AI program at VU Amsterdam in 2023."
```

**Step 3: Deprecate `indie_market_analysis`**

Find:
```yaml
      - id: indie_market_analysis
        narrative_role: breadth
        content: "Analyzed macroeconomic trends, industry dynamics, and company fundamentals through systematic research of investment reports and financial data — developed holistic understanding of market mechanisms and economic cycles."
```

Replace with:
```yaml
      # DEPRECATED (v4.0): Too vague, indefensible in interview
      # - id: indie_market_analysis
      #   content: "Analyzed macroeconomic trends..."
```

**Step 4: Update recommended_sequences** (remove indie_market_analysis)

Find:
```yaml
    recommended_sequences:
      data_engineer: ["indie_quant_research"]  # Single bullet, context only
      data_analyst: ["indie_quant_research", "indie_skill_development"]
      quant_researcher: ["indie_quant_research", "indie_market_analysis"]
```

Replace with:
```yaml
    recommended_sequences:
      data_engineer: ["indie_quant_research"]
      data_analyst: ["indie_quant_research", "indie_skill_development"]
      quant_researcher: ["indie_quant_research", "indie_skill_development"]
```

**Step 5: Validate YAML + Commit**

```bash
python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml', encoding='utf-8'))"
git add assets/bullet_library.yaml
git commit -m "narrative: rewrite Independent bullets, deprecate market_analysis (v4.0)"
```

---

### Task 5: Projects — Expedia rewrite + Deribit deprecation

**Files:**
- Modify: `assets/bullet_library.yaml` (Projects section)

**Step 1: Rewrite `expedia_ltr` (remove self-deprecating labels)**

Find:
```yaml
      - id: expedia_ltr
        narrative_role: depth_prover
        content: "Built hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered temporal, behavioral, and aggregation features (price normalization, competitor rates, estimated position); achieved NDCG@5 = 0.392 on Kaggle evaluation — VU course project, collaborated with 2 teammates."

        # Alternative version with more technical detail (for ML-heavy roles)
        # content: "Developed learning-to-rank hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered 50+ features (temporal, price normalization by search_id, competitor rates, estimated position) and optimized label gains [0,1,5] for click/booking prediction; achieved NDCG@5 = 0.392 on Kaggle test set, outperforming XGBoost+SVD ensemble (0.374) — VU course project, team of 3."
```

Replace with:
```yaml
      - id: expedia_ltr
        narrative_role: headline
        content: "Built hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered temporal, behavioral, and aggregation features (price normalization, competitor rates, estimated position); achieved NDCG@5 = 0.392 on Kaggle evaluation."

        # Alternative version with more technical detail (for ML-heavy roles)
        # content: "Developed learning-to-rank hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered 50+ features (temporal, price normalization by search_id, competitor rates, estimated position) and optimized label gains [0,1,5] for click/booking prediction; achieved NDCG@5 = 0.392 on Kaggle test set, outperforming XGBoost+SVD ensemble (0.374)."
```

**Step 2: Deprecate `deribit_options` (entire project)**

Find the entire deribit_options block and comment it out:

Find:
```yaml
  deribit_options:
    title: "Automated Crypto Options Trading System"
    institution: "Personal Project"
    period: "Oct. 2025 - Present"

    verified_bullets:

      - id: deribit_options_system
        content: "Architected automated options trading system featuring self-implemented Black-Scholes pricing engine (full Greeks, IV solver), edge-based market-making strategy, and multi-layered risk management (position limits, Greeks constraints, drawdown control); currently in paper-trading validation."

      - id: deribit_risk_management
        content: "Designed risk management framework enforcing portfolio-level constraints (delta, gamma, vega limits), per-trade stop-loss, daily loss caps, and maximum drawdown controls; implemented Kelly-inspired position sizing adjusted for implied volatility."
```

Replace with:
```yaml
  # DEPRECATED (v4.0): Candidate cannot recall project details; indefensible in interview
  # deribit_options:
  #   title: "Automated Crypto Options Trading System"
  #   institution: "Personal Project"
  #   period: "Oct. 2025 - Present"
```

**Step 3: Add headline/optional tags to thesis bullets**

Find `thesis_uq_framework` and add `narrative_role: headline`.
Find `thesis_noise_paradox` and add `narrative_role: headline`.
Find `thesis_calibration` and add `narrative_role: optional`.

**Step 4: Add headline/optional tags to other key project bullets**

- `greenhouse_etl_pipeline`: add `narrative_role: headline`
- `greenhouse_data_quality`: add `narrative_role: optional`
- `greenhouse_aggregations`: add `narrative_role: optional`
- `lakehouse_streaming`: add `narrative_role: optional`
- `lakehouse_quality`: add `narrative_role: optional`
- `lakehouse_optimization`: add `narrative_role: optional`
- `lakehouse_orchestration`: add `narrative_role: optional`
- `ml4qs_pipeline`: add `narrative_role: optional`
- `ml4qs_deep_learning`: add `narrative_role: optional`
- `graphsage_ppi`: add `narrative_role: optional`
- `neuroevo_robotics`: add `narrative_role: optional`
- `neuroevo_system`: add `narrative_role: optional`
- `bioinfo_hmm`: add `narrative_role: optional`
- `bioinfo_alignment`: add `narrative_role: optional`
- `dnn_scratch`: add `narrative_role: optional`
- `dnn_architecture`: add `narrative_role: optional`
- `nlp_poem_generator`: add `narrative_role: optional`
- `nlp_dependency_parsing`: add `narrative_role: optional`
- `lifeos_system`: add `narrative_role: optional`
- `job_hunter_system`: add `narrative_role: optional`
- All bsc_thesis bullets: add `narrative_role: optional`

**Step 5: Validate YAML + Commit**

```bash
python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml', encoding='utf-8'))"
git add assets/bullet_library.yaml
git commit -m "narrative: Expedia rewrite, deprecate Deribit, tag all projects (v4.0)"
```

---

### Task 6: Version bump + header update

**Files:**
- Modify: `assets/bullet_library.yaml` (header block, lines 1-27)

**Step 1: Add v4.0 changelog entry**

Add after the v3.2 CHANGES block:

```yaml
#
# v4.0 CHANGES (2026-03-10) — Narrative Architecture:
#   - REWRITTEN Henan Energy headlines (ingest/validate/consolidate + €32M framework)
#   - REWRITTEN Ele.me headlines (drop EUR, use detection scale + cross-team unlocking)
#   - UPDATED Baiquan pipeline ending + added 5-person team context
#   - REWRITTEN Independent bullets (pure technical, removed defensive language)
#   - REWRITTEN Expedia (removed self-deprecating "course project" labels)
#   - DEPRECATED Deribit options (candidate cannot recall project)
#   - DEPRECATED indie_market_analysis (too vague)
#   - ADDED narrative_role: headline/optional tags to ALL bullets
#   - CONVERTED all currency amounts to EUR for European market
#   - Default title for Henan Energy changed to "Business Analyst"
```

**Step 2: Update header version**

Find:
```yaml
# VERIFIED BULLET LIBRARY v3.0 — High-Impact Rewrite (2026-02-08)
```

Replace with:
```yaml
# VERIFIED BULLET LIBRARY v4.0 — Narrative Architecture (2026-03-10)
```

**Step 3: Validate YAML + Commit**

```bash
python -c "import yaml; yaml.safe_load(open('assets/bullet_library.yaml', encoding='utf-8'))"
git add assets/bullet_library.yaml
git commit -m "narrative: bump bullet library to v4.0, update changelog"
```

---

### Task 7: Final validation

**Step 1: Full YAML parse test**

```bash
python -c "
import yaml
with open('assets/bullet_library.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)
# Count active bullets
work_bullets = sum(len(exp.get('verified_bullets', [])) for exp in data.get('work_experience', {}).values())
proj_bullets = sum(len(proj.get('verified_bullets', [])) for proj in data.get('projects', {}).values())
print(f'Work experience bullets: {work_bullets}')
print(f'Project bullets: {proj_bullets}')
print(f'Total active bullets: {work_bullets + proj_bullets}')
# Verify no RMB/USD amounts remain in active bullet content
import re
for section in [data.get('work_experience', {}), data.get('projects', {})]:
    for key, entry in section.items():
        for bullet in entry.get('verified_bullets', []):
            content = bullet.get('content', '')
            if 'RMB' in content or 'USD' in content or '$' in content:
                print(f'WARNING: Currency not converted in {bullet[\"id\"]}: {content[:80]}...')
print('Validation complete.')
"
```

Expected: No warnings about unconverted currencies. Bullet counts should be approximately 18 work + 25 project = ~43 active bullets (after deprecations).

**Step 2: Verify no broken references in recommended_sequences**

```bash
python -c "
import yaml
with open('assets/bullet_library.yaml', encoding='utf-8') as f:
    data = yaml.safe_load(f)
# Collect all valid bullet IDs
valid_ids = set()
for section in [data.get('work_experience', {}), data.get('projects', {})]:
    for key, entry in section.items():
        for bullet in entry.get('verified_bullets', []):
            valid_ids.add(bullet['id'])
# Check recommended_sequences
for section in [data.get('work_experience', {}), data.get('projects', {})]:
    for key, entry in section.items():
        for template, seq in entry.get('recommended_sequences', {}).items():
            for bullet_id in seq:
                if bullet_id not in valid_ids:
                    print(f'BROKEN REF: {key}.{template} references {bullet_id}')
print(f'Total valid bullet IDs: {len(valid_ids)}')
print('Reference check complete.')
"
```

Expected: No broken references.

**Step 3: Final commit if any fixes needed**

```bash
git add assets/bullet_library.yaml
git commit -m "fix: resolve any validation issues from v4.0 narrative update"
```
