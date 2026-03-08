# Resume Narrative Strategy — Design Document

Date: 2026-03-09
Status: Strategy complete. Ready for bullet audit.

## Core Insight

A resume that stacks bullets without a unifying narrative lacks soul. But the narrative doesn't belong in every bullet — it belongs in the **structure, selection, and strategic placement** across four layers.

## Narrative Core: First-Principles Builder

> "I'm a first-principles thinker who understands problems from the ground up, designs solutions, and implements them. Can think AND can do."

This identity runs through the entire career:
- Henan Energy (2010): Automated cross-subsidiary reporting with VBA before modern data tools existed
- Ele.me (2013): Built user segmentation on Hadoop during hyper-growth
- Baiquan (2015): Designed factor computation engine and backtesting infrastructure from scratch
- GLP (2017): Joined as first data hire, defined credit scoring data architecture from zero
- Independent (2019): Self-directed quantitative research on A-share market
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
- MSc or higher (9/15), 3+ years experience (10/15), English fluent (11/15)

### Common Soft Themes

- Problem-solver in ambiguity (9/15) — aligns with first-principles narrative
- Cross-functional communicator (10/15)
- Ownership mentality (7/15) — aligns with "first data hire" story
- Continuous learner (6/15)

---

## Template 1: Data Engineer

### Bio

> Data engineer with 6 years building production data systems — from ingesting market feeds for 3,000+ securities to designing credit scoring pipelines from scratch as a startup's first data hire. M.Sc. in AI (VU Amsterdam, 8.2/10) brings rigorous approach to pipeline design, data quality, and system reliability. Databricks Certified Data Engineer Professional.

### Skills Section Priority

Row 1: Python (Expert), SQL (Expert), PySpark, Spark, Delta Lake
Row 2: Airflow, AWS, Docker, CI/CD, Git, Bash
Row 3: PostgreSQL, Hadoop, Hive, ETL/ELT, Medallion Architecture
Row 4: Pandas, NumPy, Statistics, A/B Testing

### Education — Course Selection

Data Mining Techniques (9.0), Algorithms in Sequence Analysis (9.0), Deep Learning (9.5)

### Job Titles (from title_options)

- GLP: "Data Engineer & Team Lead"
- Baiquan: "Quantitative Developer"
- Ele.me: "Data Analyst"
- Independent: "Independent Quantitative Researcher"
- Henan Energy: "Business Supervisor"

### Bullet Selection & Ordering

Experience ordered chronologically within relevance groups.

**GLP Technology — Data Engineer & Team Lead (3 bullets)**
1. `glp_founding_member` [FLAGSHIP] — "first data hire, from scratch" = ownership
2. `glp_pyspark` — PySpark + ETL keywords
3. `glp_data_engineer` — Data quality framework

**Independent Quantitative Researcher (2 bullets)**
1. `pt_personal_trading` — Event-driven backtesting, walk-forward validation
2. NEW: `pt_market_analysis` — Python equity screening, 3,000+ A-share stocks, systematic signal extraction

**Baiquan Investment — Quantitative Developer (3 bullets)**
1. `bq_de_pipeline` [FLAGSHIP] — 3,000+ securities, scale
2. `bq_de_factor_engine` — Vectorized NumPy/Pandas, performance
3. `bq_data_quality` — Cross-source validation

**Ele.me — Data Analyst (1-2 bullets)**
1. `eleme_ab_testing` — 2x + 30% quantified impact
2. `eleme_user_segmentation` [optional] — Hadoop/Hive, millions of users

**Henan Energy — Business Supervisor (1 bullet)**
1. NEW: `he_vba_automation` — VBA automated reporting, cross-subsidiary data consolidation, data quality/fraud detection

**Projects (3-4 bullets)**
1. `greenhouse_etl_pipeline` [FLAGSHIP] — Medallion Architecture, PySpark, Delta Lake
2. `lakehouse_streaming` — Structured Streaming, Auto Loader
3. `thesis_uq_framework` — 150+ HPC runs (shows large-scale experiment management)

### Flagship Hooks (interviewer will ask about)

1. `glp_founding_member` → "How did you define the data architecture from zero?"
2. `bq_de_pipeline` → "How did you handle corporate actions across 3,000+ securities?"
3. `greenhouse_etl_pipeline` → "Walk me through your Medallion Architecture design."

---

## Template 2: ML Engineer

### Bio

> ML engineer bridging research and production, with M.Sc. in AI (VU Amsterdam, 8.2/10) and 6 years building data-intensive systems. Thesis on uncertainty quantification in deep RL — benchmarking 5 methods across 150+ experiments with rigorous statistical evaluation. Hands-on PyTorch, experiment design, and end-to-end model deployment from credit scoring to NLP.

Key difference from DE Bio: MSc AI is the lead credential, thesis content in Bio, no Databricks cert.

### Skills Section Priority

Row 1: Python (Expert), PyTorch, scikit-learn, NumPy, Pandas
Row 2: Experiment Design, A/B Testing, Statistical Testing, Bayesian Methods
Row 3: Hugging Face Transformers, LLM APIs, XGBoost, LightGBM
Row 4: Docker, FastAPI, AWS, SQL, Git, CI/CD

### Education — Course Selection

Deep Learning (9.5), ML for Quantified Self (9.5), Multi-Agent Systems (9.5), NLP (9.0)

### Job Titles (from title_options)

- GLP: "ML Engineer & Team Lead"
- Baiquan: "Quantitative Researcher"
- Ele.me: "Data Analyst"
- Independent: "Independent Quantitative Researcher"

### Section Order (differs from DE)

**Projects BEFORE Experience** — for ML template, thesis and projects are stronger signals than work history.

```
Education
Projects (4-5 bullets)  ← promoted to top
Experience (6-8 bullets)
```

### Bullet Selection

**Projects (4-5 bullets — primary section)**
1. `thesis_uq_framework` [FLAGSHIP] — 150+ runs, 5 methods, 31% CRPS, p<0.001
2. `thesis_noise_paradox` [HOOK] — counter-intuitive discovery, guaranteed interview question
3. `expedia_ltr` — 4.9M records, top 5% Kaggle, learning-to-rank
4. `obama_tts_voice_cloning` — Fine-tuning + HPC + FastAPI deployment (full MLOps chain)
5. `graphsage_ppi` or `ml4qs_pipeline` [optional] — GNN or time-series breadth

**GLP Technology — ML Engineer & Team Lead (2 bullets)**
1. `glp_founding_member` [FLAGSHIP] — same bullet, ML reader sees "model training and deployment"
2. `glp_portfolio_monitoring` — monitoring, early warning = model monitoring angle

**Independent Quantitative Researcher (2 bullets)**
1. `pt_personal_trading` — Event-driven backtesting (quantitative modeling)
2. NEW: `pt_market_analysis` — Python screening framework (analytical methods)

**Baiquan Investment — Quantitative Researcher (2-3 bullets)**
1. `bq_factor_research` [FLAGSHIP] — Fama-MacBeth → validated → live portfolio = research-to-production
2. `bq_futures_strategy` — 14.6% annualized return = deployed model with real results
3. `bq_de_backtest_infra` [optional] — Evaluation infrastructure

**Ele.me — Data Analyst (1 bullet)**
1. `eleme_ab_testing` — A/B testing, experiment design

**Henan Energy:** Omit or 1-line only (less relevant for ML roles).

### Flagship Hooks

1. `thesis_noise_paradox` → "What is the noise paradox? Why does moderate noise improve uncertainty estimates?"
2. `glp_founding_member` → "Walk me through your credit scoring model — features, training, deployment."
3. `bq_factor_research` → "How did your factor models go from backtest to live?"

---

## Cross-Template Decisions

### Experience Timeline Strategy

Both templates use chronological order within Experience section:
```
GLP Technology (Jul 2017 - Aug 2019)
Independent Quantitative Researcher (Sep 2019 - Aug 2023)
Baiquan Investment (Jul 2015 - Jun 2017)
Ele.me (Sep 2013 - Jul 2015)
Henan Energy (Jul 2010 - Aug 2013)  [DE: 1 bullet, ML: omit/1-line]
```

Independent period positioned after GLP (chronologically correct). Title: "Independent Quantitative Researcher" (NOT "Investor"). 2 bullets — not 1 (looks empty) and not 3+ (overcompensating).

### Aoshen Business (Sep-Dec 2014)

Omit entirely. 4 months, weak bullet, not worth the space.

### AI Routing Logic

```
New job → AI analysis → template_fit evaluation
  ├─ max(de_fit, ml_fit) >= 8 → Use highest-scoring SVG template
  └─ Both < 8                 → AI-customized generation (Jinja2)
```

### What the Resume Does NOT Need to Carry

The resume's job = get the HM to say "I want to talk to this person" (30 seconds).
The candidate's deeper value (intellectual depth, resilience, cross-domain thinking) shows in interviews, not on paper.

---

## Bullet Audit Principles

When rewriting individual bullets:

1. **Fact-check against real experience** — eliminate "feeling of fakeness." Ask: "If the interviewer deep-dives this, can I confidently explain every detail?"
2. **Frame as understanding, not just execution** — "designed X because Y" not just "built X with Z"
3. **Keep ATS keywords in first 8 words** — strong verb + technical noun
4. **Quantify where honest** — don't fabricate numbers
5. **One flagship per job section** — the hook that makes interviewer curious
6. **Standard bullets: clean and efficient** — keyword-rich, impact-oriented, no narrative overhead
7. **Check for inflation** — if a bullet makes the work sound bigger than it was, downgrade the language

## New Bullets Needed

- [ ] `he_vba_automation` — Henan Energy: VBA reporting automation, cross-subsidiary data consolidation, data quality/fraud detection
- [ ] `pt_market_analysis` — Independent period: Python equity screening framework, A-share market analysis

## Open Items

- [x] Narrative core definition
- [x] Four-layer strategy
- [x] DE template: Bio + bullets + flagships + skills
- [x] ML template: Bio + bullets + flagships + skills
- [x] Timeline and gap handling strategy
- [x] Cross-template routing logic
- [ ] Bullet-by-bullet audit of all ~50 bullets (+ 2 new bullets)
- [ ] SVG template visual design
- [ ] AI routing code integration (ai_analyzer.py + resume_renderer.py)
