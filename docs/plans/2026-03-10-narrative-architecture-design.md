# Narrative Architecture Design — Bullet Library v4.0

Date: 2026-03-10
Status: Approved. Ready for implementation.
Supersedes: `2026-03-09-resume-narrative-strategy.md` (bullet selection and bio sections still valid; this doc replaces the bullet-level narrative design)

## Design Goal

Transform individually strong but disconnected bullets into a coherent career story. Each section tells its own chapter; together they form a book about a **first-principles builder who understands problems deeply, designs systems, and delivers measurable results**.

## Invisible Narrative Principles

The best resume narrative is one the reader never notices — they just finish reading with a clear impression.

### 1. Recurring Motifs
"from scratch", "end-to-end", "from X through Y to Z" appear across sections. Reader accumulates: "this person always builds complete systems."

### 2. Scale Escalation

| Section | Scale Marker |
|---------|-------------|
| Henan Energy | 20+ business units, Fortune 500, €24B+ revenue |
| Ele.me | 2.2M+ users, hyper-growth startup |
| Baiquan | 3,000+ securities, tick-level data, real capital |
| GLP | First hire, built everything from zero |
| Thesis/Projects | 150+ HPC runs, 5 methods, p<0.001 |

### 3. Consistent Rhythm
Every headline bullet follows: **[What I built] → [Technical specificity] → [Measurable result]**.

### 4. Chapter Progression

| Chapter | Reader Impression | Career Arc Role |
|---------|------------------|----------------|
| Henan Energy | "Born to work with data" | Origin — data thinking before modern tools |
| Ele.me | "Builds order from chaos" | Validation — delivers under hyper-growth |
| Baiquan | "Research that ships" | Deepening — full research-to-production |
| GLP | "Can own a platform solo" | Climax — built everything as first hire |
| Independent | "Deliberate choice, not a gap" | Bridge — self-directed, kept building |
| MSc + Projects | "Theory + first principles" | Elevation — rigorous research + implementation |

---

## Section-by-Section Design

### Henan Energy — "Data engineering before modern tools"

**Company line:** `Henan Energy (Fortune Global 500) | Zhengzhou, China | Jul. 2010 – Aug. 2013`
**Title:** `Business Analyst`

**Bullet 1 (HEADLINE): `he_data_automation`**
> Built automated pipeline to ingest, validate, and consolidate non-standardized Excel reports from 20+ business units into unified operational reporting, reducing monthly processing from 2 days to under 2 hours.

**Bullet 2 (HEADLINE): `he_supply_chain_analytics`**
> Designed the group's supply chain analytics framework from scratch, tracking daily sales and inventory to guide procurement and sales timing; optimization guided by this framework contributed to €32M in documented profit improvements across business units over 3 years.

**Bullet 3 (OPTIONAL): `he_data_quality`** — unchanged
**Bullet 4 (OPTIONAL): `he_data_standardization`** — unchanged

**Section narrative:** Fresh Tsinghua grad enters Fortune 500 SOE, discovers decisions run on manually aggregated spreadsheets. Builds automated systems with available tools, directly contributing to €32M in business impact.

---

### Ele.me — "Analytical products at hyper-scale"

**Company line:** `Ele.me (acquired by Alibaba) | Shanghai, China | Sep. 2013 – Jul. 2015`
**Title:** `Data Analyst`

**Bullet 1 (HEADLINE): `eleme_fraud_detection`**
> Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern algorithms (same-phone, high-frequency, repeat-order matching), preventing fraudulent subsidy claims during hyper-growth.

**Bullet 2 (HEADLINE): `eleme_sql_optimization`**
> Optimized 90+ Hadoop/Hive queries through partition pruning and subquery pushdown, cutting scan volume 5x (500GB → 100GB) and unlocking real-time analytics on 30+ warehouse tables for fraud detection, operations, and marketing teams.

**Bullet 3 (OPTIONAL): `eleme_user_segmentation`** — unchanged
**Bullet 4 (OPTIONAL): `eleme_bi_dashboards`** — unchanged

**Section narrative:** At pre-Alibaba Ele.me, solves most urgent problem first (fraud = revenue protection), then optimizes infrastructure that powers all analytical products.

**Currency note:** Drop €85K (too small for European context); use detection scale (51K clusters, 2.2M users) instead.

---

### Baiquan Investment — "Full lifecycle: data to live trading"

**Company line:** `Baiquan Investment | Beijing, China | Jul. 2015 – Jun. 2017`
**Company descriptor:** `Quantitative hedge fund, 5-person team`
**Title:** per template (Quantitative Researcher / Quantitative Developer)

**Bullet 1 (HEADLINE): `bq_de_pipeline`**
> Built end-to-end market data ingestion pipeline processing 3,000+ A-share securities and 5+ years of tick-level futures data from multiple vendor feeds; implemented corporate action handling and deduplication logic ensuring data integrity for all downstream research and live trading.

Change: "for quantitative research" → "for all downstream research and live trading" (forward-references the full arc).

**Bullet 2 (OPTIONAL): `bq_de_backtest_infra`** — unchanged
**Bullet 3 (HEADLINE): `bq_factor_research`** — unchanged
**Bullet 4 (HEADLINE for ML): `bq_futures_strategy`** — unchanged

**Headline selection by template:**
- DE: bq_de_pipeline + bq_factor_research
- ML: bq_factor_research + bq_futures_strategy
- Quant: all 4

**Section narrative:** In a 5-person fund, owns the full lifecycle — from ingesting tick data through systematic factor research to deploying a live strategy with 14.6% annualized return. The rare person who does both engineering AND research.

---

### GLP Technology — "Platform from zero" (REFERENCE ONLY)

Already has full narrative structure (context_setter → depth_prover → foundation → extension → breadth). No changes needed. This is the benchmark section.

---

### Independent Quantitative Researcher — "Self-directed, not idle"

**Title:** `Independent Quantitative Researcher` (NOT self-employed — avoids ZZP/KvK legal implications in NL)

**Bullet 1 (HEADLINE): `indie_quant_research`**
> Built automated equity research pipeline processing 83K+ daily records across 3,600+ stocks via Tushare API and MySQL; implemented institutional flow tracking and momentum signal detection for systematic market analysis.

Change: Complete rewrite. Removed defensive "maintained technical proficiency" language. Pure technical work — reader infers the person kept coding.

**Bullet 2 (OPTIONAL): `indie_skill_development`**
> Self-directed study in data science and machine learning, pivoting to AI after the emergence of large language models; admitted to M.Sc. AI program at VU Amsterdam in 2023.

Change: Removed "reinforcement learning" (learned during MSc, not this period). Added LLM pivot context.

**Bullet 3: `indie_market_analysis`** — DEPRECATED. Too vague, can't defend in interview.

**Section narrative:** 1 strong bullet showing concrete technical work. Reader sees: "This person built a real data pipeline during this period." The MSc admission in bullet 2 proves the period was purposeful.

---

### Projects — Strategic Selection (no section-level narrative)

Projects don't need a linear arc. They need **strategic selection per template** to complete the capability picture.

**DE template selection (3 bullets):**
1. `greenhouse_etl_pipeline` (HEADLINE) — Medallion Architecture, PySpark, Delta Lake
2. `thesis_uq_framework` (HEADLINE) — 150+ HPC runs (shows scale management)
3. `lakehouse_streaming` or `job_hunter_system` (OPTIONAL) — AI picks based on JD

**ML template selection (3-4 bullets):**
1. `thesis_uq_framework` (HEADLINE) — 5 methods, 31% CRPS, p<0.001
2. `thesis_noise_paradox` (HEADLINE) — original discovery, guaranteed interview hook
3. `expedia_ltr` (HEADLINE) — 4.96M records, LambdaRank, NDCG@5=0.392
4. `ml4qs_pipeline` or `graphsage_ppi` (OPTIONAL) — time-series or GNN breadth

**Expedia bullet — self-deprecating labels removed:**
> Built hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered temporal, behavioral, and aggregation features (price normalization, competitor rates, estimated position); achieved NDCG@5 = 0.392 on Kaggle evaluation.

Removed: "VU course project, collaborated with 2 teammates"

**Deribit options:** DEPRECATED. Candidate cannot recall project details; indefensible in interview.

---

## narrative_role System Update

**New system (all sections except GLP):**

| Tag | Meaning | Position |
|-----|---------|----------|
| `headline` | HM must-read, first 2 bullets | Bullet 1-2 per section |
| `optional` | AI selects based on JD keyword match | Bullet 3+ per section |
| `deprecated` | Retired, never used | Not rendered |

**GLP retains fine-grained tags:** context_setter → depth_prover → foundation → extension → breadth (benchmark section).

---

## Implementation Checklist

Changes needed in `assets/bullet_library.yaml`:

### Henan Energy
- [ ] Rewrite `he_data_automation` content (ingest/validate/consolidate version)
- [ ] Rewrite `he_supply_chain_analytics` content (€32M, procurement/sales timing)
- [ ] Update narrative_role: headline/headline/optional/optional
- [ ] Update default title to "Business Analyst"

### Ele.me
- [ ] Rewrite `eleme_fraud_detection` content (drop €85K, add "during hyper-growth")
- [ ] Rewrite `eleme_sql_optimization` content ("unlocking... for fraud, ops, marketing")
- [ ] Update narrative_role: headline/headline/optional/optional

### Baiquan
- [ ] Update `bq_de_pipeline` ending ("for all downstream research and live trading")
- [ ] Add `team_size: 5` to company metadata
- [ ] Update narrative_role: headline per template (see design)

### Independent
- [ ] Rewrite `indie_quant_research` (technical pipeline version)
- [ ] Rewrite `indie_skill_development` (remove RL, add LLM pivot)
- [ ] Deprecate `indie_market_analysis`

### Projects
- [ ] Rewrite `expedia_ltr` (remove "course project, collaborated with 2 teammates")
- [ ] Deprecate `deribit_options` (both bullets)
- [ ] Add headline/optional tags to all project bullets

### Global
- [ ] Convert all RMB/USD amounts to EUR across bullet library
- [ ] Ensure no em-dash overuse (max 1 per section)
- [ ] Verify all narrative_role tags updated

---

## Currency Conversion Reference

| Original | EUR Equivalent | Used In |
|----------|---------------|---------|
| 261M RMB (Henan Energy) | €32M | he_supply_chain_analytics |
| 651K RMB (Ele.me) | DROPPED | eleme_fraud_detection (use scale metrics instead) |
| 200B RMB (Henan Energy revenue) | €24B+ | company_note only |

Historical rates used: 2011-2013 ~8.25 CNY/EUR, 2014-2015 ~7.5 CNY/EUR.
