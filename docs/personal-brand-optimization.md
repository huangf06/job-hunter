# Personal Brand Optimization: LinkedIn + GitHub + Blog

Generated: 2026-04-02 | Aligned with career-strategy-2026-04.md

**Strategic framing**: ML/AI Engineer primary, MLOps hedge, DE fallback.
All brand copy leads with ML/AI identity. DE experience is positioned as differentiator ("I can build the whole pipeline, not just the model"), not as primary identity.

---

## Deliverable 1: GitHub Profile README.md

Ready to commit to `huangf06/huangf06` repo.

```markdown
# Fei Huang

ML Engineer based in Amsterdam. M.Sc. in Artificial Intelligence from VU Amsterdam (GPA 8.2/10). 7+ years building data infrastructure and ML systems in production.

Most ML engineers come from either a research background or a software engineering background. I come from neither -- I built data platforms and quantitative trading systems before graduate school in AI. That means I think about models the way an infrastructure person does: how does this thing fail, how does it scale, and who maintains it at 3am.

My thesis investigated uncertainty quantification in deep reinforcement learning -- when models know what they don't know. Before that: credit scoring engines at a fintech startup, systematic alpha research at a quant fund, fraud detection at a hyper-growth food delivery platform. Each role was a step closer to the intersection of data systems and intelligent decision-making.

I also write about philosophy and literature at [FeiThink](https://huangf06.github.io/FeiThink/en/) -- mostly Kant, Dostoevsky, and the question of how to live well.

## Selected Projects

**[job-hunter](https://github.com/huangf06/job-hunter)** -- AI-powered job search pipeline. LLM-based evaluation (Claude API), automated resume generation, rule-based filtering, and application tracking. Python, SQLite/Turso, Playwright, GitHub Actions.

**Financial Data Lakehouse** -- ML feature engineering infrastructure on Databricks. Auto Loader + Structured Streaming for real-time market data ingestion, Medallion Architecture, schema evolution, data quality framework with quarantine-and-replay pattern.

**M.Sc. Thesis: Uncertainty Quantification in Deep RL** -- Benchmarked 5 UQ methods across 150+ HPC training runs. Demonstrated QR-DQN superiority (31% lower CRPS, p < 0.001). Discovered a "noise paradox" where moderate observation noise improves ensemble uncertainty estimates.

**[LifeOS](https://github.com/huangf06/LifeOS)** -- Personal productivity platform orchestrating 5 services (Todoist, Notion, Telegram Bot, Logseq, Eudic) with automated workflows via GitHub Actions.

## Links

- [LinkedIn](https://linkedin.com/in/huangf06)
- [Blog (English)](https://huangf06.github.io/FeiThink/en/)
- [Substack](https://feithink.substack.com)
```

---

## Deliverable 2: LinkedIn Profile Copy

### a) Headline (214 chars)

```
ML Engineer | M.Sc. Artificial Intelligence, VU Amsterdam | 7+ Years Data Infrastructure & ML Systems | Databricks Certified | Python, PyTorch, Spark | Amsterdam
```

Alternative (shorter, 156 chars):
```
ML Engineer | M.Sc. AI, VU Amsterdam | From Data Pipelines to Production ML | Databricks Certified | Amsterdam
```

### b) About Section (~2000 chars)

```
Most ML engineers come from research or software engineering. I come from data infrastructure -- and that turns out to be a useful place to start.

I spent 7 years building systems where data quality and pipeline reliability directly determined whether decisions were good or catastrophic. At a fintech startup (GLP Technology), I was the first technical hire: I built the credit scoring decision engine from scratch -- 29 rejection rules, 36-segment borrower classification, a scorecard model combining 19 weighted features for default prediction. The entire system, from data ingestion through model-driven decisioning to post-loan monitoring.

Before that: systematic alpha research at a quant fund (factor modeling, backtesting with real capital), and fraud detection at Ele.me during hyper-growth (51K suspicious clusters identified across 2.2M users). Each role pushed me deeper into the question of how to make reliable automated decisions from messy, high-stakes data.

In 2023 I entered the M.Sc. AI program at VU Amsterdam (GPA 8.2/10). My thesis tackled uncertainty quantification in deep reinforcement learning -- 150+ training runs on HPC, evaluating when models know what they don't know. I hold the Databricks Certified Data Engineer Professional certification.

What I bring to ML engineering that pure ML graduates don't: I've built the data platforms that feed models. I know what happens upstream. I think about ML systems the way an infrastructure person does -- failure modes, data drift, pipeline reliability, monitoring. Bridging data pipelines and production ML is not an aspiration for me; it's what I've been doing from both sides.

Looking for ML/AI Engineering roles in the Netherlands. Full work authorization (Zoekjaar), eligible for Kennismigrant visa sponsorship.
```

### c) Experience Entries

**GLP Technology | ML & Data Engineering Lead | Jul 2017 - Aug 2019 | Shanghai**

```
First technical hire at a lending fintech. Designed and built the complete credit risk ML platform from scratch -- from raw data ingestion through model-driven automated decisioning to post-loan monitoring.

Core system: engineered the credit scoring decision engine with 29 rejection rules across 4 risk dimensions, a 36-segment borrower classification model, and an early-delinquency scorecard combining 19 weighted features for first-payment default prediction. This was a production ML system making real lending decisions.

Built the underlying data infrastructure: daily ETL of 30+ production tables into AWS Redshift, credit bureau report parser (deeply nested JSON to 5 structured analytical tables), and post-loan monitoring with delinquency tracking and fraud detection API integration.

Tech: Python, SQL, PySpark, AWS (Redshift, S3, EC2), Airflow, scikit-learn, pandas, NumPy
```

**Independent Quantitative Researcher | Sep 2019 - Aug 2023 | Remote**

```
Deliberate career transition: independent research + graduate school preparation.

Built automated equity research pipeline processing 83K+ daily records across 3,600+ stocks. Implemented institutional flow tracking and momentum signal detection for systematic market analysis.

Concurrent: self-directed deep dive into ML/DL (PyTorch, deep learning theory), English and German language acquisition. Admitted to M.Sc. AI at VU Amsterdam (2023).
```

**BQ Investment | Quantitative Researcher | Jul 2015 - Jun 2017 | Beijing**

```
Quantitative hedge fund, 5-person team.

Built systematic alpha research pipeline: Fama-MacBeth regression validating 4 factor families (value, momentum, money flow, event-driven) across 3,000+ securities. Factors integrated into live portfolio. Developed and deployed R-Breaker intraday trading strategy achieving 14.6% annualized return with real capital.

Architected event-driven backtesting framework (Python + MATLAB) with walk-forward validation and 15+ performance metrics -- adopted as core research infrastructure.

Built end-to-end market data pipeline: 3,000+ securities, 5+ years tick-level futures data, corporate action handling, deduplication.

Tech: Python, MATLAB, SAS, SQL, NumPy, pandas, scipy
```

**Ele.me (acquired by Alibaba) | Data Analyst | Sep 2013 - Jul 2015 | Shanghai**

```
Joined during hyper-growth, pre-Alibaba acquisition.

Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern-matching algorithms (same-phone, high-frequency, repeat-order), preventing fraudulent subsidy claims. This was effectively an anomaly detection / classification problem at scale.

Optimized 90+ Hadoop/Hive queries (partition pruning, subquery pushdown), cutting scan volume 5x (500GB to 100GB). Engineered user segmentation pipeline across 4 behavioral cohorts for targeted marketing.

Tech: SQL, Hadoop, Hive, Python, pandas, A/B Testing
```

**Henan Energy | Business Analyst | Jul 2010 - Aug 2013 | Zhengzhou**

```
Fortune Global 500 (#328). Built automated data consolidation pipeline across 20+ business units (2 days to 2 hours). Designed supply chain analytics framework -- EUR 32M documented profit impact over 3 years.
```

### d) Education (LinkedIn section)

**VU Amsterdam | M.Sc. Artificial Intelligence | 2023 - 2025**
```
GPA: 8.2/10

Thesis: Uncertainty Quantification in Deep Reinforcement Learning under Noisy Environments
- Benchmarked 5 UQ methods across 150+ HPC training runs (SLURM)
- QR-DQN superiority: 31% lower CRPS (p < 0.001) over ensemble and dropout baselines
- Discovered "noise paradox": moderate observation noise improves ensemble-based UQ

Selected courses (all 9.0+): Deep Learning (9.5), Multi-Agent Systems (9.5), ML for Quantified Self (9.5), NLP (9.0), Data Mining (9.0), Evolutionary Computing (9.0)
```

### e) Featured Section Suggestions

Pin in this order:
1. **M.Sc. Thesis** -- link to paper/repo if available. Strongest ML signal.
2. **Databricks Certified Data Engineer Professional** -- credential link
3. **GitHub: job-hunter** -- "AI-powered job search pipeline (Claude API, Python, GitHub Actions)"
4. **Blog post: "What My M.Sc. Thesis Taught Me About Uncertainty"** -- write this first (see Blog Strategy)
5. **Blog post: "Skin in the Game"** -- analytical thinking, Taleb resonates with technical audiences

Avoid featuring: political commentary posts (Li Wenliang, Hong Kong, White Paper Protests). Keep published, don't promote on LinkedIn.

### f) Skills (ordered for ML/AI Engineer positioning)

**Pin these 3:**
1. Machine Learning
2. Python
3. PyTorch

**Remaining 12:**
4. Deep Learning
5. Data Engineering
6. Apache Spark / PySpark
7. SQL
8. Databricks
9. scikit-learn
10. Docker
11. AWS
12. Delta Lake
13. Statistical Modeling
14. CI/CD
15. Airflow

---

## Deliverable 3: Blog Strategy Memo

### Existing Post Assessment

(Unchanged from previous version -- all 48 posts are philosophical/literary. Assessment stands.)

**Professional assets**: "Skin in the Game", "Why We Read Kant", "IKIRU", "Reason and Emotion", "History of Thought" series
**Neutral**: Literary analyses, personal reflections
**Risk zone**: Political commentary (keep published, don't feature on LinkedIn)

### Technical Blog Posts to Write (5 suggestions, reordered for ML-first strategy)

**1. "What My M.Sc. Thesis Taught Me About Uncertainty" [HIGHEST PRIORITY]**
Why first: This is your strongest ML credential. A practitioner-friendly version establishes you as someone who does real ML research, not just tutorials.
Outline: What is uncertainty quantification? Why production ML needs it (model confidence != accuracy). The noise paradox finding. What 150 HPC runs taught about reproducibility. QR-DQN vs ensembles -- when to use which. Frame for practitioners: "if your model is making decisions, you need to know when it's guessing."
Target: ML engineers, hiring managers evaluating ML depth.

**2. "From Data Pipelines to Production ML: Why Infrastructure Experience Matters"**
Why: This IS your differentiating narrative. This post should be the canonical version of "why my background is an asset, not a liability."
Outline: Factor research is feature engineering. Credit scoring is a production ML system (even if you didn't call it that in 2017). Backtesting is offline evaluation. Data quality is the #1 killer of ML in production. The gap between Jupyter and production is a data engineering problem.
Target: Hiring managers who are wondering "can a DE do ML?" This post answers yes, with receipts.

**3. "Automating Job Search with Python and Claude"**
Why: Viral potential + demonstrates LLM integration in production systems.
Outline: Architecture, the filtering pipeline, LLM-based evaluation (prompt engineering for structured output), resume generation, lessons learned. Honest about what Claude is good/bad at.
Target: Broad developer audience.

**4. "Building a Real-Time Data Lakehouse on Databricks"**
Why: Databricks cert credibility + demonstrates current skills. Also relevant if you pivot to MLOps (feature store infrastructure).
Outline: Medallion Architecture, Auto Loader vs batch, schema evolution, quarantine pattern. Include architecture diagrams.
Target: Data/ML engineers, Databricks community.

**5. "Credit Scoring from Scratch: Building an ML Decision System at a Startup"**
Why: Reframes GLP as ML experience (aligned with resume repackaging in strategy doc).
Outline: First technical hire story. The 29-rule engine. Scorecard methodology as ML. Feature engineering from credit bureau data. What "production ML" looked like before MLOps was a word.
Target: Fintech engineers, ML engineers who think "real ML" only means neural nets.

### Blog Organization

Same as previous version: don't separate, use tags (`technical`, `ml`, `philosophy`, `career`). Add a "Technical Writing" menu item once 3+ posts exist.

### Hugo Config Improvements

Same as previous version, plus:
- Update site description to include ML/AI: "Fei Huang writes about machine learning, data systems, philosophy, and moral thought"
- Update keywords to lead with ML terms: "machine learning, ML engineering, uncertainty quantification, deep reinforcement learning, data infrastructure, philosophy, Kant"

---

## Deliverable 4: Cross-Platform Consistency Audit

### Narrative Alignment (Updated for ML-first strategy)

| Element | Resume (to update) | LinkedIn (proposed) | GitHub (proposed) | Blog (to build) |
|---------|-------------------|--------------------|--------------------|-----------------|
| Primary identity | ML Engineer | ML Engineer | ML Engineer | (needs technical posts) |
| Career arc | IE -> DA -> Quant -> DE -> ML/AI | Same | Same | Post #2 tells this story |
| Differentiator | "bridges data pipelines and production ML" | Same | "thinks about models like an infrastructure person" | Post #2 + #5 |
| Thesis prominence | Projects section, top | Education section, detailed | Selected Projects, with metrics | Post #1 (highest priority) |
| GLP framing | "ML-powered decision system" | "credit risk ML platform" | Not detailed | Post #5 |
| Gap framing | Career note | "Deliberate career transition" | Not mentioned | Not needed |
| Lakehouse framing | "feature engineering infrastructure" | Not in About (too detailed) | "ML feature engineering infrastructure" | Post #4 |

### Key Changes from Previous Version

1. **LinkedIn headline**: "Data Engineer" -> "ML Engineer"
2. **LinkedIn pinned skills**: Spark/DE -> Machine Learning/PyTorch
3. **GitHub README opening**: "Data engineer and AI practitioner" -> "ML Engineer"
4. **GLP title on LinkedIn**: "Data Engineer & Team Lead" -> "ML & Data Engineering Lead"
5. **GLP tech stack**: Added "scikit-learn" (the scorecard was effectively a sklearn pipeline)
6. **About section hook**: Rewritten to frame DE as ML differentiator, not primary identity
7. **Featured section**: Thesis moved to #1 (was not present before)
8. **Blog priorities**: Thesis post is now #1 (was #2), career narrative post reframed from "quant to DE" to "data pipelines to production ML"

### Contradictions to Resolve

1. **Resume master template still says "Data Engineer with expertise in..."** -- needs updating to ML-first framing per strategy doc's recommendation: "ML Engineer with 7+ years in data infrastructure, bridging the gap between data pipelines and production ML systems"

2. **Bullet library GLP title options**: Currently "Senior Data Engineer" (default) or "Data Engineer & Team Lead". Need to add "ML & Data Engineering Lead" as a title option for ML-targeted applications.

3. **Bullet library `skill_tiers`**: ML skills are listed under a generic "ml" category. For ML Engineer positioning, these should be more prominent. Consider reordering so ML appears before data_engineering in the YAML.

4. **LinkedIn vs Resume GLP title**: LinkedIn will show "ML & Data Engineering Lead" permanently. Resume can vary per application. This is fine -- LinkedIn is a fixed profile, resume is tailored.

### Action Items (Prioritized)

| Priority | Action | Where |
|----------|--------|-------|
| P0 | Update LinkedIn headline, About, Experience per this doc | LinkedIn (manual) |
| P0 | Update resume bio_builder default to ML-first framing | bullet_library.yaml |
| P0 | Add "ML & Data Engineering Lead" to GLP title_options | bullet_library.yaml |
| P1 | Write thesis blog post (#1 above) | FeiThink |
| P1 | Create/update GitHub profile README | huangf06/huangf06 repo |
| P1 | Write career narrative post (#2 above) | FeiThink |
| P2 | Write job-hunter post (#3) | FeiThink |
| P2 | Update Hugo config keywords/description | FeiThink config |
| P2 | Update blog About page to connect to professional identity | FeiThink |

### Unified "About Me" Boilerplate (ML-first)

> ML Engineer based in Amsterdam with 7+ years building data infrastructure and ML systems in production. M.Sc. in Artificial Intelligence from VU Amsterdam (GPA 8.2/10), Databricks Certified Data Engineer Professional. Career path from quantitative finance through data engineering to AI -- each step driven by the same question: how do you make reliable automated decisions from messy, high-stakes data. I write about philosophy, literature, and moral thought at FeiThink.

Platform adaptations:
- **LinkedIn**: expand into full About (done above)
- **GitHub**: use as-is with project links
- **Blog About page**: lead with intellectual identity, then professional background
- **Resume**: compress to 1-2 line bio, tailored per application via bio_builder
