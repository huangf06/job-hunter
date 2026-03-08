# Resume Narrative Strategy — Design Document

Date: 2026-03-09
Status: In Progress (DE template designed, ML template TODO)

## Core Insight

A resume that stacks bullets without a unifying narrative lacks soul. But the narrative doesn't belong in every bullet — it belongs in the **structure, selection, and strategic placement** across four layers.

## Narrative Core: First-Principles Builder

> "I'm a first-principles thinker who understands problems from the ground up, designs solutions, and implements them. Can think AND can do."

This identity runs through the entire career:
- Henan Energy (2010): Automated cross-subsidiary reporting with VBA before modern data tools existed
- Ele.me (2013): Built user segmentation on Hadoop during hyper-growth
- Baiquan (2015): Designed factor computation engine and backtesting infrastructure from scratch
- GLP (2017): Joined as first data hire, defined credit scoring data architecture from zero
- Independent (2019): Self-directed quantitative analysis, intellectual rebuilding
- MSc AI (2023): Chose uncertainty quantification — "how do we know what we don't know?"

The candidate's deepest strengths are in **understanding and analysis**, not technical tool proficiency. The resume must reflect this without sacrificing keyword effectiveness.

## Four-Layer Strategy

| Layer | Audience | Time | What They Need | How Narrative Shows |
|-------|----------|------|---------------|-------------------|
| **1. Keywords** | ATS | 0s | Exact keyword matches | Skills section, bullet nouns |
| **2. Scan** | Recruiter | 6s | Company names, titles, years, education | Job titles matched to target role |
| **3. Read** | Hiring Manager | 30-60s | Relevance, impact, seniority | Bio (2-3 sentences) + bullet selection & ordering |
| **4. Analyze** | Tech Interviewer | 2-5min | Depth, things to ask about | 2-3 flagship "hook" bullets per template |

**Key principle:** Layers 1-2 are pure efficiency (keywords, structure). Layers 3-4 are where narrative lives — through Bio, bullet selection, and flagship hooks. NOT through rewriting every bullet in a narrative format.

## Interview Data Foundation

15 interviews cluster into 3 archetypes:

| Archetype | Count | Companies | Core Question |
|-----------|-------|-----------|--------------|
| **A: Data Platform Builder** | 7 | Sensorfact, Deloitte, elipsLife, Source.ag (x2), Swisscom, Nebius | "Can this person build reliable pipelines and own production data systems?" |
| **B: ML/AI Systems Engineer** | 5 | FareHarbor, kaiko.ai, Elsevier, Springer Nature, Chikara HR | "Can this person take ML from research to production?" |
| **C: Quantitative Problem Solver** | 3 | Supergrads, Maisha Mazuri, (Chikara HR) | "Does this person have the mathematical horsepower?" |

Two SVG templates (DE, ML) cover ~80% of interview-generating roles. Quant handled by AI customization.

### Common Hard Requirements (from 15 interview JDs)

- Python (13/15), Data pipeline/ETL (10/15), Cloud/AWS (10/15)
- Spark/PySpark (8/15), SQL (8/15), CI/CD (9/15), Docker (7/15)
- MSc or higher (9/15), 3+ years experience (10/15)
- English fluent (11/15)

### Common Soft Themes

- Problem-solver in ambiguity (9/15) — aligns with first-principles narrative
- Cross-functional communicator (10/15)
- Ownership mentality (7/15) — aligns with "first data hire" story
- Continuous learner (6/15)

## Template 1: Data Engineer

### Bio

> Data engineer with 6 years building production data systems — from ingesting market feeds for 3,000+ securities to designing credit scoring pipelines from scratch as a startup's first data hire. M.Sc. in AI (VU Amsterdam, 8.2/10) brings rigorous approach to pipeline design, data quality, and system reliability. Databricks Certified Data Engineer Professional.

### Bullet Selection & Ordering

Ordered by relevance, not chronology. Each section: 1 flagship + 1-2 standard.

**GLP Technology — Data Engineer & Team Lead (3 bullets)**
1. `glp_founding_member` [FLAGSHIP] — "first data hire, from scratch" = ownership
2. `glp_pyspark` — PySpark + ETL keywords
3. `glp_data_engineer` — Data quality framework

**Baiquan Investment — Quantitative Developer (3 bullets)**
1. `bq_de_pipeline` [FLAGSHIP] — 3,000+ securities, scale
2. `bq_de_factor_engine` — Vectorized NumPy/Pandas, performance
3. `bq_data_quality` — Cross-source validation

**Ele.me — Data Analyst (1-2 bullets)**
1. `eleme_ab_testing` — 2x + 30% quantified impact
2. `eleme_user_segmentation` [optional] — Hadoop/Hive, millions of users

**Projects (3-4 bullets)**
1. `greenhouse_etl_pipeline` [FLAGSHIP] — Medallion Architecture, PySpark, Delta Lake
2. `lakehouse_streaming` — Structured Streaming, Auto Loader
3. `thesis_uq_framework` — 150+ HPC runs (shows large-scale experiment management)

### Flagship Hooks (interviewer will ask about)

1. `glp_founding_member` → "How did you define the data architecture from zero?"
2. `bq_de_pipeline` → "How did you handle corporate actions across 3,000+ securities?"
3. `greenhouse_etl_pipeline` → "Walk me through your Medallion Architecture design."

### Early Career Treatment

**Henan Energy (1 bullet, compressed):**
- REWRITE NEEDED: Current bullets don't capture the Excel/VBA automation, cross-subsidiary data consolidation, and data quality/fraud detection work.
- New bullet should frame pre-modern-tools data pipeline work honestly.

**Independent Investor (1 bullet):**
- Use existing `pt_personal_trading` (event-driven backtesting, walk-forward validation)
- Keep restrained. Deep value of this period shows in interviews, not resume.

**Aoshen Business:** Omit entirely (4 months, weak bullet).

## Template 2: ML Engineer

**Status: TODO** — Same framework, different bullet selection emphasizing:
- Thesis (UQ/RL) as flagship
- Model deployment and evaluation
- PyTorch, experiment design, MLOps
- GLP framed as "ML lifecycle" not "data pipeline"

## Bullet Audit Principles

When rewriting individual bullets:

1. **Fact-check against real experience** — eliminate "feeling of fakeness"
2. **Frame as understanding, not just execution** — "designed X because Y" not just "built X with Z"
3. **Keep ATS keywords in first 8 words** — strong verb + technical noun
4. **Quantify where honest** — don't fabricate numbers
5. **One flagship per job section** — the hook that makes interviewer curious
6. **Standard bullets: clean and efficient** — keyword-rich, impact-oriented, no narrative overhead

## Open Items

- [ ] ML Engineer template: Bio + bullet selection + flagships
- [ ] Henan Energy: New bullets based on actual VBA/Excel/data quality work
- [ ] Bullet-by-bullet audit of all ~50 bullets
- [ ] SVG template visual design
- [ ] AI routing integration (ai_analyzer.py + resume_renderer.py)
