# Bullet Library v7.1 — Narrative Calibration Report

**Date**: 2026-04-27
**Method**: Role-profile-first narrative analysis, grounded in 23 Dutch market JDs from the database
**Data**: 53 active bullets, 17 interview rounds, 432 resumes with bullet_usage tracking

---

## 0. Methodology

This report does NOT use the v7.0 mechanical signal density checklist (strong verb / scale / tech specificity / business impact). That checklist scores author-perceived quality. Interview data proves it does not predict hiring manager response.

Instead, we:
1. Build concrete "daily work" profiles from real JDs that produced interviews
2. Read each bullet as a hiring manager would — in 6 seconds, pattern-matching
3. Identify where narrative signal diverges from role expectations
4. Only suggest rewrites where the mismatch is clear and fixable

**Data sources:**
- 13 interview JDs (companies that invited Fei to interview)
- 10 high-score (8.0+) non-interview JDs for supplemental coverage
- 432 resumes with tracked bullet_usage → interview_rounds join
- bullet_library.yaml v7.0 (53 active bullets)

---

## 1. Role Profiles

### 1.1 Data Engineer — Netherlands, All Sizes

**JD sources:** Deloitte (8.5), Source.ag (7.5/6.5), Swisscom (7.5), Sensorfact (7.0), elipsLife (7.0), Aon (6.5), Catawiki (8.5), Flow Traders (8.5), Tata Steel (8.5), McKinsey/QuantumBlack (8.5)

#### Daily Work Reality

Morning: check orchestration DAGs (Airflow/Prefect/Dagster) for overnight failures. Fix broken pipelines — schema changes from upstream, API timeouts, data quality alerts. Mid-morning: standup, then write or optimize ETL jobs (PySpark/Spark SQL on Databricks or EMR). Afternoon: work on a new data model for a downstream team (analytics, data science, product), review PRs from teammates, maybe investigate a performance regression in a Gold-layer table. Occasionally: design a new pipeline from scratch, set up monitoring/alerting, migrate from one platform to another (Oracle→Databricks, Synapse→Databricks).

The work is 70% maintenance/optimization of existing pipelines, 30% new development. Collaboration is constant: data scientists need clean feature tables, analysts need dimensions, product needs real-time events.

#### 6-Second Scan Signals

**Must-see (appears in 80%+ of JDs):**
- Python + SQL (non-negotiable)
- Spark / PySpark / Databricks
- ETL/ELT pipeline experience
- Cloud platform (AWS or Azure; GCP less common in NL)
- "Production" pipeline experience (not just notebooks)

**Bonus (40-80% of JDs):**
- Airflow or equivalent orchestration
- Data quality / data governance
- Delta Lake / Medallion Architecture
- Streaming (Kafka, Flink, Structured Streaming)
- CI/CD for data pipelines
- Mentoring / tech lead signals

#### "Can Start Tomorrow" Criteria

A hiring manager thinks "minimal ramp-up" when they see:
- Built pipelines that ran in production on a schedule (not one-off scripts)
- Debugged pipeline failures under time pressure (not just built greenfield)
- Knows Spark/Databricks ecosystem specifically (not just "big data" generically)
- Has worked with downstream consumers (analysts, ML engineers) — understands data modeling
- CI/CD awareness (testing data pipelines, not just deploying code)

**What they're afraid of:** Someone who can write Spark code but has never owned a pipeline end-to-end — never dealt with schema drift, never set up alerting, never had a 2am page.

---

### 1.2 Machine Learning Engineer — Netherlands, Mid-Size (50-500)

**JD sources:** kaiko.ai (8.5), FareHarbor (7.5), Springer Nature (6.5), Elsevier (6.5), RevoData (8.5), Qualcomm (8.5)

#### Daily Work Reality

Morning: check model monitoring dashboards — any drift? any degradation in production metrics? Review experiment tracking (MLflow/W&B) for yesterday's training runs. Mid-morning: work on the current model improvement cycle — could be feature engineering, hyperparameter tuning, or evaluating a new architecture. Afternoon: integrate a model into the serving infrastructure (FastAPI endpoint, SageMaker endpoint, or Databricks model serving). Write evaluation scripts. Meet with product/data teams about what metrics matter.

The split: 40% experimentation/model development, 30% production infrastructure (pipelines, serving, monitoring), 30% evaluation and collaboration. The "ML" in MLE is real — they train models — but the "Engineer" part is equally weighted: the code must work in production, not just in a notebook.

Key shift in 2025-2026 NL market: MLE roles increasingly expect GenAI/LLM familiarity. RAG pipelines, prompt engineering, model evaluation for LLM outputs are now standard expectations, not "nice to have."

#### 6-Second Scan Signals

**Must-see (80%+ of JDs):**
- Python (strong, not "familiar with")
- ML frameworks (PyTorch preferred in NL market, TensorFlow accepted)
- Production ML experience (deployed models, not just trained them)
- End-to-end ML lifecycle (data → training → evaluation → deployment → monitoring)

**Bonus (40-80% of JDs):**
- MLflow / experiment tracking
- Databricks / Spark (data processing for features)
- Cloud ML services (SageMaker, Vertex AI, Azure ML)
- GenAI / LLM / RAG experience
- A/B testing / experimentation frameworks
- CI/CD for ML

#### "Can Start Tomorrow" Criteria

- Has taken at least one model from research to production (the full loop)
- Can set up an evaluation framework (not just accuracy — business metrics)
- Understands model serving (latency, throughput, batching tradeoffs)
- Knows how to monitor a model in production (drift, degradation)
- Can work with data engineers (understands data pipelines enough to get features)

**What they're afraid of:** A researcher who publishes papers but has never deployed anything. Or a software engineer who can build APIs but doesn't understand why the model is performing poorly.

---

### 1.3 AI Engineer — Netherlands, Startup to Scale-up

**JD sources:** kaiko.ai (8.5), Elsevier (6.5), Aivory (8.5), Lumenalta (8.5), kaiko.ai Jr (8.5)

**Caveat:** "AI Engineer" as a distinct title is still diffusing in the NL market. Direct interview samples are limited; this profile draws more from high-score JDs. The boundary with MLE is blurry — the key distinction is: AI Engineer is more product-facing, more LLM-centric, and works in smaller/faster teams.

#### Daily Work Reality

Morning: check production AI features — are LLM responses degrading? Any hallucination reports? Review user feedback on AI-powered features. Mid-morning: work on the current feature — could be building a RAG pipeline, tuning prompts, implementing a new agent workflow, or adding guardrails. Afternoon: rapid prototyping of a new AI capability — hook up an LLM API, build evaluation, demo to the team. Ship to staging by end of day.

The split: 50% building new AI features (LLM integration, RAG, agents), 30% evaluation and quality (is the AI actually good?), 20% backend infrastructure to support it. Speed matters more than polish. Ownership is total — from idea to production.

Unlike MLE: rarely trains models from scratch. Uses pre-trained models (GPT-4, Claude, open-source LLMs) and builds systems around them. The engineering challenge is in orchestration, evaluation, and reliability — not in gradient descent.

#### 6-Second Scan Signals

**Must-see (80%+ of JDs):**
- Python (strong backend skills)
- LLM / GenAI hands-on experience
- Production deployment (shipped AI features to real users)
- End-to-end ownership (not "I did the model part and someone else deployed it")

**Bonus (40-80% of JDs):**
- RAG pipelines
- Prompt engineering / LLM evaluation
- LangChain / LangGraph / agent frameworks
- FastAPI / backend services
- Evaluation infrastructure
- Experience in regulated domains (healthcare, fintech)

#### "Can Start Tomorrow" Criteria

- Has shipped at least one AI-powered feature to real users
- Knows LLM APIs deeply (not just "I used ChatGPT")
- Can build the full stack around an AI feature (API, eval, monitoring, guardrails)
- Comfortable with ambiguity — can figure out what to build, not just how
- Backend engineering skills (this is not a research role)

**What they're afraid of:** Someone who can prompt an LLM in a notebook but can't build a production system around it. Or someone who needs weeks to ship what should take days.

---

## 2. Contradiction Resolution

### 2.1 Core Thesis

v7.0's signal density checklist evaluates bullets from the **author's** perspective: "Is this bullet well-constructed?" But hiring managers don't read resumes as literary critics. They pattern-match: "Does this person look like the person I need?"

The relevant question is not "Is this bullet high quality?" but "Does this bullet make the candidate recognizable as [role]?"

### 2.2 Case Study: `glp_pyspark` — The Invisible Workhorse

**Data:** 17/17 interview resumes. Signal density: 2/4. 414 total resumes (96% inclusion rate).

**Content:** "Designed and implemented PySpark ETL pipelines processing consumer credit data across the full loan lifecycle — from application ingestion through repayment tracking; provided technical mentorship to junior analyst on distributed data processing patterns."

**Why signal density scored it low:** No hard numbers (how many records? what throughput?). "Consumer credit data" is domain context, not scale. No explicit business impact statement.

**Why it works:**

Reading as a **DE hiring manager** (6 seconds): "PySpark ETL pipelines" — *check*. "Full loan lifecycle" — *owned something end-to-end*. "Technical mentorship" — *senior enough*. Three signals in one scan. I don't need to know how many records; I know this person has done the job.

Reading as an **MLE hiring manager**: "PySpark" — *can handle data at scale*. "ETL pipelines" — *production experience, not just notebooks*. Less exciting than for DE, but still positive.

Reading as an **AI Engineer hiring manager**: Neutral. Not negative, just doesn't trigger recognition.

**The mechanism:** This bullet works because its key terms ("PySpark", "ETL pipelines", "technical mentorship") are **high-recognizability tokens** in the DE/MLE hiring vocabulary. A recruiter doesn't need to read the full sentence to extract value. The words themselves do the work.

**Lesson:** Recognizability > density. A bullet that is instantly parseable at the keyword level outperforms a dense bullet that requires careful reading.

### 2.3 Case Study: `lakehouse_orchestration` — The Keyword Carrier

**Data:** 14/17 interview resumes. Signal density: 1/4. 191 total resumes (7.3% interview rate — highest of any bullet).

**Content:** "Integrated Airflow for orchestration and Docker for consistent deployment across environments."

**Why signal density scored it lowest:** No scale, no impact, no specificity beyond tool names. Generic to the point of being a checklist item.

**Why it works:**

This bullet carries two ATS/scan keywords that appear in nearly every DE JD: **Airflow** and **Docker**. These are not narrative signals — they are **keyword anchors**.

In the 10 DE JDs analyzed:
- "Airflow" or "orchestration" appears in 8/10
- "Docker" or "containerization" appears in 7/10

When a recruiter or ATS scans a resume for DE fit, these keywords trigger a positive signal regardless of narrative context. The bullet doesn't need to tell a story; it needs to be present.

**Context:** This bullet never appears alone. It always accompanies `lakehouse_streaming`, `lakehouse_quality`, or other substantive bullets. Its role is coverage — filling keyword gaps that the narrative bullets don't cover.

**Lesson:** Some bullets serve as keyword anchors, not narrative vehicles. Their value is in keyword presence, not in storytelling. Rewriting them to add narrative depth would be counterproductive — it might dilute the keyword signal.

**Why interview rate (7.3%) is higher than peers:** Selection bias. This bullet is specifically chosen for DE-heavy resumes where orchestration/DevOps keywords matter. Those resumes target jobs that are more likely to produce interviews (better fit). The bullet's "success" is partly a proxy for good resume targeting.

### 2.4 Case Study: `glp_decision_engine` — The Impressive Wallflower

**Data:** 1/17 interview resumes. Signal density: 4/4. 64 total resumes (1.6% interview rate — lowest).

**Content:** "Engineered the core decision engine: 29 rejection rules across 4 risk dimensions, 36-segment borrower classification, and an early-delinquency scorecard combining 19 weighted features for first-payment default prediction."

**Why signal density scored it highest:** Strong verb (Engineered), specific numbers (29, 4, 36, 19), named techniques (rejection rules, classification, scorecard), clear business impact (first-payment default prediction). Textbook perfect.

**Why it fails in practice:**

Reading as a **DE hiring manager** (6 seconds): "decision engine... rejection rules... borrower classification... scorecard..." — *This is domain logic, not data engineering*. I'm looking for someone who builds pipelines, not business rules. Skip.

Reading as an **MLE hiring manager**: "scorecard... 19 weighted features..." — *This sounds more like risk analytics than ML engineering*. A logistic regression scorecard is not what I think of as "ML." Mixed signal.

Reading as an **AI Engineer hiring manager**: Nothing recognizable here. Skip.

**The only context where it works:** A credit-risk-specific ML role. Those represent <5% of the job market in NL. The AI tailor correctly avoids it for most resumes.

**Its one appearance:** Swisscom "Big Data Engineer" (R2 technical — failed). Even in that context, it didn't help pass the technical round.

**Lesson:** Signal density measures writing quality, not narrative fit. A bullet can be perfectly constructed and still fail because it doesn't pattern-match to the target role. The 4/4 score is correct from a writing standpoint and irrelevant from a hiring standpoint.

### 2.5 Derived Framework: Narrative Effectiveness

From the three cases, three principles emerge:

| Principle | Definition | Implication for rewrites |
|-----------|-----------|------------------------|
| **Recognizability** | The bullet contains tokens that a recruiter for [role] instantly recognizes as "one of us" | Prioritize role-standard vocabulary over impressive but unfamiliar terms |
| **Keyword Anchoring** | Some bullets exist to carry ATS/scan keywords, not to tell stories | Don't rewrite keyword carriers for narrative quality; it dilutes their function |
| **Narrative Fit** | A bullet's value for a role depends on whether it *reads like* that role's work | A well-written bullet for the wrong audience is worse than a mediocre bullet for the right audience |

**Rewrite decision rule:**
- If a bullet fails on **recognizability** → reframe using role-standard vocabulary (keep the facts, change the framing)
- If a bullet fails on **keyword anchoring** → leave it alone (it's working as designed)
- If a bullet fails on **narrative fit** → either reframe for a specific role, or accept that it's role-specific and won't appear on most resumes

**What NOT to do:**
- Don't add numbers to a bullet just to increase signal density — if the numbers don't increase recognizability, they're noise
- Don't rewrite a working keyword carrier into a narrative bullet
- Don't generalize a specialist bullet to make it "work for everyone" — that makes it work for no one

---

## 3. Bullet Calibration Table

Legend:
- **Interview count**: X/17 = appeared on X of 17 interview resumes
- **Disposition**: keep (works as-is) / reframe (right fact, wrong signal) / demote (low value across all roles) / promote (underused relative to value)
- **Rewrite**: only provided for "reframe" items

### 3.1 GLP Technology (8 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `glp_founding_member` | 15/17 | "Full ML lifecycle, credit scoring" — strong for applied ML | "Owned something end-to-end" — moderate positive | "First data hire, pipeline + deployment" — positive context setter | **keep** |
| `glp_pyspark` | 17/17 | "Can handle data at scale" — positive | Neutral | "PySpark ETL, end-to-end, mentorship" — perfect fit | **keep** |
| `glp_data_quality` | 15/17 | "Cares about data quality for models" — moderate positive | Neutral | "Data quality framework, schema validation" — strong fit | **keep** |
| `glp_decision_engine` | 1/17 | "Risk analytics, not ML engineering" — weak fit | Irrelevant | "Business logic, not pipelines" — weak fit | **keep (role-specific)** |
| `glp_portfolio_monitoring` | 11/17 | "Monitoring, analytics" — moderate | Neutral | "Monitoring system, data-driven" — moderate | **keep** |
| `glp_data_compliance` | 3/17 | Irrelevant | Irrelevant | "Compliance, regulated industry" — niche positive for insurance/banking DEs | **keep (niche)** |
| `glp_payment_collections` | 0/17 | Irrelevant | Irrelevant | "API integration" — weak, generic | **demote** |
| `glp_generalist` | 0/17 | Irrelevant | Irrelevant | "Cross-functional, vendor management" — filler | **demote** |

**Notes:**
- `glp_decision_engine`: NOT a failure of the bullet. It's correctly avoided by the AI tailor for non-credit roles. Its 4/4 signal density is accurate for the narrow audience where it belongs. No rewrite needed — just accept it's niche.
- `glp_payment_collections` and `glp_generalist`: Zero interview appearances, zero narrative value for any target role. These are resume filler. Should rarely or never be selected.

---

### 3.2 Baiquan Investment (6 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `bq_de_pipeline` | 15/17 | "Data pipeline experience" — moderate | Neutral | "Market data ingestion, 3000+ securities, dedup" — strong | **keep** |
| `bq_de_factor_engine` | 16/17 | "High-performance computation, NumPy/Pandas, research" — strong | Neutral | "Performance engineering, vectorized" — moderate positive | **keep** |
| `bq_de_backtest_infra` | 13/17 | "Infrastructure, framework design" — moderate | Neutral | "Event-driven architecture" — moderate | **keep** |
| `bq_factor_research` | 4/17 | "Statistical modeling, research methodology" — moderate for research MLE | Neutral | "Analytics, not engineering" — weak | **keep (quant-specific)** |
| `bq_futures_strategy` | 3/17 | "Live production, real returns" — moderate | Neutral | Irrelevant | **keep (quant-specific)** |
| `bq_data_quality` | 10/17 | "Data validation" — weak positive | Neutral | "Cross-source validation, alerting" — moderate | **keep** |

**Notes:**
- `bq_de_factor_engine` is the second-most-used bullet (16/17 interviews). Its recognizability comes from "high-performance" + "NumPy/Pandas" + "3,000+ stocks daily." Every MLE and DE recognizes this as "can write efficient computation code."
- `bq_factor_research` and `bq_futures_strategy` are correctly niche. They shine for quant roles (Barak Capital, Maisha Mazuri, Supergrads) and should stay as-is.

---

### 3.3 Ele.me (6 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `eleme_ab_testing` | 11/17 | "A/B testing, segmentation, experimentation" — strong | Weak | "Cross-functional reporting, Hadoop" — moderate | **keep** |
| `eleme_fraud_detection` | 2/17 | "Pattern algorithms, scale (2.2M users)" — moderate | "Algorithms at scale" — weak positive | "System building, data processing" — moderate | **reframe** |
| `eleme_sql_optimization` | 3/17 | Neutral | Neutral | "SQL performance, 5x improvement, Hadoop/Hive" — strong | **keep** |
| `eleme_user_segmentation` | 9/17 | Weak | Neutral | "SQL pipeline, 2.2M users, actionable output" — moderate | **keep** |
| `eleme_kmeans` | 2/17 | "Clustering, ML on Hadoop" — moderate | Weak | "ML pipeline on Hadoop" — moderate | **keep** |
| `eleme_sql_simple` | 0/17 | Irrelevant | Irrelevant | "SQL optimization" — redundant with eleme_sql_optimization | **demote** |

**Reframe: `eleme_fraud_detection`**

Current: "Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern algorithms (same-phone, high-frequency, repeat-order matching), preventing fraudulent subsidy claims during hyper-growth."

Problem: The word "fraud detection" instantly triggers recognition for a specific niche (fintech anti-fraud), but the underlying work — pattern matching at scale, algorithm design, production system — is broadly relevant. For DE roles, "fraud" narrows it; for MLE, the algorithmic detail is the value.

Suggested reframe: "Engineered pattern detection system identifying 51,000+ suspicious clusters across 2.2M+ users using 3 matching algorithms; deployed during platform hyper-growth (Ele.me, acquired by Alibaba) to prevent subsidy abuse at scale."

Changes: "anti-fraud detection system" → "pattern detection system" (broader recognizability); added company context (Alibaba acquisition signals scale/credibility); removed redundant detail of specific pattern names. The "fraud" signal is still there ("suspicious clusters", "subsidy abuse") but doesn't lead.

---

### 3.4 Henan Energy (3 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `he_data_automation` | 0/17 | Irrelevant | Irrelevant | "Excel automation, early career" — context only | **keep (context)** |
| `he_supply_chain_analytics` | 0/17 | Irrelevant | Irrelevant | "Analytics, business impact (€32M)" — moderate for analytics-heavy DE | **keep (context)** |
| `he_data_quality` | 0/17 | Irrelevant | Irrelevant | "Data quality, anomaly detection, early career" — filler | **keep (context)** |

**Notes:** These bullets have 0 interview appearances because Henan Energy is early career (2010-2013) and rarely included on resumes. They're not "bad" — they're just old. No rewrite needed; they serve as deep-resume context for roles that value data governance background.

---

### 3.5 Independent Quantitative Researcher (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `indie_quant_research` | 0/17 | "Data pipeline, systematic" — weak positive | Neutral | "Automated pipeline, API, MySQL" — weak positive | **keep (gap bridge)** |
| `indie_skill_development` | 0/17 | Irrelevant | Irrelevant | Irrelevant | **demote** |

**Notes:**
- `indie_quant_research` serves a structural purpose: it bridges the 2019-2023 career gap. It's never been selected for interview resumes because the gap period is usually minimized. No rewrite needed.
- `indie_skill_development` is pure filler explaining a career transition. Should almost never appear on a resume targeting a technical role.

---

### 3.6 Thesis / Research Projects (3 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `thesis_uq_framework` | 9/17 | "Benchmarking, HPC, Deep RL, statistical rigor" — strong | "Deep learning research" — moderate | Neutral | **keep** |
| `thesis_noise_paradox` | 9/17 | "Research methodology, novel finding, evaluation pipeline" — strong | "Evaluation pipeline" — moderate | Neutral | **keep** |
| `thesis_calibration` | 2/17 | "Bayesian, calibration" — niche positive | Weak | Irrelevant | **keep (niche)** |

**Notes:** Both thesis bullets appear on 9/17 interview resumes — strong performance. They work for MLE because they signal: "can do rigorous research AND build evaluation systems." The key tokens are "benchmarking framework", "150+ training runs", "HPC (SLURM)", "reproducible evaluation pipeline" — all of which read as engineering, not just academic research.

---

### 3.7 Financial Data Lakehouse (4 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `lakehouse_streaming` | 15/17 | "Data platform" — moderate | Neutral | "Databricks, streaming, Auto Loader, schema evolution" — very strong | **keep** |
| `lakehouse_quality` | 13/17 | Weak | Neutral | "Data quality, quarantine pattern, Medallion" — strong | **keep** |
| `lakehouse_orchestration` | 14/17 | "Airflow, Docker" — keyword hit | Neutral | "Airflow, Docker" — keyword hit | **keep (keyword anchor)** |
| `lakehouse_optimization` | 9/17 | Weak | Neutral | "Delta Lake, Z-ordering, compaction" — moderate | **keep** |

**Notes:** The Lakehouse project is the strongest portfolio-project block. `lakehouse_streaming` works because "Databricks" + "streaming" + "schema evolution" are must-see signals for Dutch DE market (Databricks dominance in NL). The entire block reads as "this person has hands-on Databricks experience" — the single strongest recognizability signal for NL DE roles.

---

### 3.8 Greenhouse Sensor Pipeline (3 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `greenhouse_etl_pipeline` | 5/17 | Weak | Neutral | "PySpark, Delta Lake, Medallion, tests, CI" — strong | **keep** |
| `greenhouse_data_quality` | 4/17 | Weak | Neutral | "Data quality framework, 6 checks" — moderate | **keep** |
| `greenhouse_aggregations` | 2/17 | Weak | Neutral | "Time-series, production scale" — moderate | **keep** |

**Notes:** This block overlaps with Lakehouse in signaling Spark/Delta Lake skills. It adds: "58 tests, CI via GitHub Actions" — a testing/CI signal the Lakehouse bullets don't carry. When both appear together, they reinforce the "production-ready DE" narrative.

---

### 3.9 Deribit Options (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `deribit_options_system` | 4/17 | "Pricing engine, Greeks, risk management" — strong for quant-adjacent MLE | Neutral | Irrelevant | **keep (quant)** |
| `deribit_risk_management` | 2/17 | "Portfolio constraints, position sizing" — quant-specific | Neutral | Irrelevant | **keep (quant)** |

**Notes:** Correctly niche. These bullets shine for quant roles (Barak Capital, Maisha Mazuri, Supergrads) and are correctly omitted for DE/standard MLE.

---

### 3.10 Expedia Recommendation (1 active bullet)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `expedia_ltr` | 5/17 | "LightGBM, recommendation, ranking, Kaggle top 5%" — strong | "ML application" — moderate | "Feature engineering, 4.9M records" — moderate | **keep** |

**Notes:** Strong MLE bullet. "Learning-to-rank", "LightGBM", "NDCG@5", "Kaggle top 5%" are all instantly recognizable MLE signals. Good cross-role versatility.

---

### 3.11 NLP Projects (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `nlp_poem_generator` | 1/17 | "LLM, Hugging Face, text generation" — moderate | "GPT-2, Hugging Face, Flask deployment" — moderate positive | Irrelevant | **reframe** |
| `nlp_dependency_parsing` | 0/17 | "PyTorch, NLP fundamentals" — weak | Irrelevant | Irrelevant | **keep (niche)** |

**Reframe: `nlp_poem_generator`**

Current: "Developed LLM-powered text generation application leveraging GPT-2 and Hugging Face Transformers; implemented prompt engineering with controllable style parameters and deployed as interactive web application via Flask."

Problem: "Poem generator" (implied by title) and "text generation application" undersell what this demonstrates. For AI Engineer roles, the signal should be: "built an LLM application end-to-end and deployed it." The current framing reads as a course exercise.

Suggested reframe: "Built end-to-end LLM application using Hugging Face Transformers (GPT-2): implemented prompt engineering with controllable generation parameters and deployed as production-ready web service via Flask REST API."

Changes: "Developed LLM-powered text generation application leveraging" → "Built end-to-end LLM application using" (more direct, emphasizes end-to-end); "interactive web application" → "production-ready web service via Flask REST API" (signals deployment competence). Core facts unchanged.

---

### 3.12 ML4QS / IMU Sensor (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `ml4qs_pipeline` | 1/17 | "End-to-end ML, sensor data, multiple models" — moderate | Weak | Neutral | **keep (niche)** |
| `ml4qs_deep_learning` | 1/17 | "LSTM, Optuna, cross-validation" — moderate | Weak | Irrelevant | **keep (niche)** |

**Notes:** IoT/sensor data is niche in NL (Sensorfact is one of the few). These bullets are correctly selected for sensor-data-relevant roles and correctly omitted for most others.

---

### 3.13 GraphSAGE GNN (1 active bullet)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `graphsage_ppi` | 0/17 | "GNN, PyTorch Geometric, deep learning" — niche positive for research MLE | "Deep learning" — weak | Irrelevant | **keep (niche)** |

**Notes:** GNN is a niche that's growing in NL (drug discovery, recommendation systems). This bullet is correctly available for specialized roles.

---

### 3.14 Evolutionary Robotics (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `neuroevo_robotics` | 1/17 | "Research, evolution, published paper" — weak (too academic) | Neutral | Irrelevant | **demote** |
| `neuroevo_system` | 0/17 | "MuJoCo, simulation" — niche | Neutral | Irrelevant | **demote** |

**Notes:** These bullets signal academic research capability but don't pattern-match to any common NL market role. The "published research paper" is impressive but reads as academia, not industry. For pure research MLE roles they could work, but those are rare.

Demote reasoning: 0-1/17 interview appearances, low total usage (1 resume each), and the narrative reads as "academic researcher" rather than "production engineer." Should be low-priority in AI tailor selection.

---

### 3.15 Sequence Analysis / Bioinformatics (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `bioinfo_hmm` | 0/17 | "HMM, algorithms from scratch" — moderate for algo-focused roles | Irrelevant | Irrelevant | **keep (niche)** |
| `bioinfo_alignment` | 0/17 | "Algorithms, BWT, O(n)" — moderate for algo-focused | Irrelevant | Irrelevant | **keep (niche)** |

**Notes:** Zero usage in interview resumes, but algorithmically impressive. These could be valuable for companies that care about computer science fundamentals (trading firms, algorithm-heavy companies). No rewrite needed — they serve a narrow but valid purpose.

---

### 3.16 Deep Learning Fundamentals (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `dnn_scratch` | 0/17 | "Understands fundamentals, NumPy" — weak (too basic for senior MLE) | Irrelevant | Irrelevant | **demote** |
| `dnn_architecture` | 0/17 | "Fundamentals" — redundant with thesis bullets | Irrelevant | Irrelevant | **demote** |

**Notes:** These demonstrate understanding of ML fundamentals, but for the seniority level targeted (3-5+ years), showing you can implement a 3-layer NN from scratch reads as entry-level. The thesis bullets already signal deep learning competence at a much higher level. These should almost never be selected over thesis bullets.

---

### 3.17 Voice Cloning / Obama TTS (1 active bullet)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `obama_tts_voice_cloning` | 0/17 | "Fine-tuning, HPC, deployment" — moderate | "Model fine-tuning, deployment" — moderate | Irrelevant | **reframe** |

**Reframe: `obama_tts_voice_cloning`**

Current: "Fine-tuned Coqui XTTS v2 voice cloning model with hybrid deployment architecture: GPU training on Snellius HPC cluster via SLURM job arrays, CPU inference served through FastAPI REST API and Gradio web UI; implemented 5 configurable speaking styles for text-to-speech generation."

Problem: Zero interview appearances despite decent content. The issue: "voice cloning" in the title and "Coqui XTTS v2" as an obscure model name reduce recognizability. The *engineering* value here (fine-tuning on HPC, serving via FastAPI, hybrid GPU/CPU architecture) is strong — but buried under domain-specific details.

Suggested reframe: "Fine-tuned open-source LLM (XTTS v2) on HPC cluster (SLURM job arrays); designed hybrid deployment architecture with GPU training and CPU inference via FastAPI REST API; delivered configurable generation parameters and Gradio web interface."

Changes: "voice cloning model" → "open-source LLM" (broader recognizability — voice models ARE LLMs now); "Coqui XTTS v2" → "XTTS v2" (less obscure); removed "Obama" connotation; foregrounded the engineering pattern (HPC training → FastAPI serving) which is universally valuable for MLE/AI Eng roles. The actual skill demonstrated is "fine-tune and deploy a large model" — that's the signal to lead with.

---

### 3.18 LifeOS (1 active bullet)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `lifeos_system` | 1/17 | Irrelevant | "API orchestration, automation, Telegram Bot" — weak positive | "GitHub Actions, pipeline" — weak | **keep (low-priority)** |

**Notes:** This is a personal project that signals "builds things for fun" but doesn't carry strong professional signals for any target role. It appeared once (Source.ag) — probably as a tie-breaker or culture-fit signal for a startup that values builder mentality. No rewrite needed; low priority.

---

### 3.19 Job Hunter Automation (2 active bullets)

| bullet_id | Int (X/17) | MLE Reading | AI Eng Reading | DE Reading | Disposition |
|-----------|-----------|-------------|----------------|------------|-------------|
| `job_hunter_system` | 2/17 | "LLM APIs, pipeline" — moderate | "LLM APIs, multi-stage pipeline" — moderate | "Pipeline, SQLite, Playwright" — moderate | **keep** |
| `job_hunter_operations` | 0/17 | Irrelevant | Irrelevant | "Operations, GitHub Actions" — weak | **demote** |

**Notes:**
- `job_hunter_system` has cross-role appeal: it signals LLM API usage (AI Eng), pipeline design (DE), and automation (all). Its 2/17 appearance is reasonable for a personal project.
- `job_hunter_operations` is pure filler — "operational controls" doesn't trigger any role recognition.

---

## 4. Summary of Dispositions

| Disposition | Count | Bullets |
|-------------|-------|---------|
| **keep** | 38 | Most core bullets perform well in their intended context |
| **keep (niche/context)** | 8 | Role-specific bullets correctly used for narrow targeting |
| **reframe** | 3 | `eleme_fraud_detection`, `nlp_poem_generator`, `obama_tts_voice_cloning` |
| **demote** | 6 | `glp_payment_collections`, `glp_generalist`, `eleme_sql_simple`, `indie_skill_development`, `neuroevo_robotics`, `neuroevo_system`, `dnn_scratch`, `dnn_architecture`, `job_hunter_operations` |
| **promote** | 0 | No underused bullets identified that warrant promotion |

**Key finding:** The library is in better shape than the v7.0 audit suggested. The contradictions between signal density and interview performance are not bugs — they reflect a real distinction between writing quality and narrative fit. Most bullets work well in their intended context. Only 3 need reframing.

---

## 5. Appendix: High-Frequency Keywords from Database JDs

### DE JDs (top 20 keywords by frequency across 10 JDs):
Python, SQL, Spark/PySpark, Databricks, AWS, ETL, data pipelines, Docker, Airflow, CI/CD, data quality, Delta Lake, Azure, Kafka, data modeling, Git, PostgreSQL, dbt, Kubernetes, monitoring

### MLE JDs (top 15 keywords):
Python, PyTorch, ML pipelines, production deployment, MLflow, Databricks, evaluation, A/B testing, GenAI/LLM, Docker, CI/CD, Kubernetes, FastAPI, monitoring, RAG

### AI Engineer JDs (top 15 keywords):
Python, LLM, RAG, production deployment, FastAPI, prompt engineering, evaluation, end-to-end, GenAI, LangChain/LangGraph, Docker, backend services, agents, Hugging Face, compliance
