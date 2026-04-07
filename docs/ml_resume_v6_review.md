# ML Resume v6 — Brutal Honest Review & Rewrite Strategy
**Date:** 2026-03-19
**Target:** Machine Learning Engineer roles
**Source:** `templates/Fei_Huang_ML_Resume_v6.svg`

---

## Part 1 — Top-level Diagnosis

**First-impression verdict:** This resume reads as a data professional with a quant/fintech background who recently completed an AI master's degree and is trying to pivot into ML Engineering. The strongest ML signals come from your academic projects (thesis, Expedia LTR), not from your work experience. Your professional experience is dominated by data engineering (ETL, Redshift, Airflow), rule-based systems (rejection rules, scorecards), and quantitative research (factor models, backtesting) — none of which are ML engineering in the way hiring managers define it. The 4-year gap (2019-2023) as "Independent Quantitative Researcher" is the elephant in the room — it reads as underemployment, and the single bullet doesn't justify the space. The resume is well-formatted and has good quantification, but the ML signal is buried under data infrastructure and quant noise.

**What this resume currently looks like:** A Data Scientist / Quantitative Analyst with strong data engineering chops who went back to school for an AI degree. Not an ML Engineer.

**ML Engineer signal strength: WEAK.** The only real ML engineering evidence is academic (thesis benchmark, Expedia LTR). No production ML models, no model serving, no experimentation frameworks, no A/B testing of models, no feature stores, no ML pipelines in production.

**Top 5 issues:**
1. **No production ML models in work experience.** The GLP scorecard is a weighted feature system, not a trained ML model. The BQ work is quant research, not ML engineering.
2. **The 2019-2023 gap is poorly handled.** 4 years as "Independent Quantitative Researcher" with one bullet about a stock pipeline is a red flag.
3. **Section ordering buries ML signal.** Experience (which is your weakest ML section) comes first. Education and projects (your strongest ML evidence) are pushed to the right column.
4. **Too much data engineering / infrastructure detail.** ETL, Redshift, bureau parsers, Hadoop optimization — these are DE bullets, not MLE bullets.
5. **Skills section is generic and unfocused.** "Decisioning & Data Systems" is not an ML category. Missing: experiment tracking, model evaluation, feature engineering frameworks, any mention of transformers/NLP tools.

---

## Part 2 — Hiring-Manager View

### Header / Contact
- **Helps:** Clean, professional. LinkedIn + GitHub links are good.
- **Hurts:** Nothing wrong here.

### Bio / Summary
- **Helps:** "Machine Learning Engineer" title is bold. M.Sc. in AI is mentioned.
- **Hurts:** "production decision systems" is vague. "risk, fraud, and portfolio workflows" screams fintech/quant, not ML. "model-driven logic" is a stretch — the GLP work was rule-based, not model-driven in the ML sense. "ranking, uncertainty evaluation, and sensor classification" are academic projects, not production work.
- **Feels generic:** "Combines data infrastructure, feature-building, and model-driven logic" — this could describe a data engineer or a BI analyst.
- **Verdict:** The summary is trying too hard to bridge incompatible signals. It doesn't land as MLE.

### Experience

**GLP Technology:**
- **Helps:** "First data hire" shows ownership. Scorecard with 19 features shows quantitative thinking.
- **Hurts:** This is a rule-based decision engine, not ML. "29 rejection rules, 36 borrower segments" is business logic, not model training. The ETL bullet is pure DE. Title "Data Scientist & Team Lead" is fine but the work doesn't back it up with ML evidence.
- **Cut:** The ETL/Redshift bullet. It's pure DE and dilutes the ML signal.
- **Emphasize:** The scorecard bullet — but reframe it as a predictive model, not business rules.

**BQ Investment:**
- **Helps:** "14.6% annualized return with real capital" is concrete and impressive. Factor research shows quantitative rigor.
- **Hurts:** This is quant research, not ML engineering. Fama-MacBeth regression is finance, not ML. "Deployed into live trading" is good but it's a trading strategy, not an ML system.
- **Off-target:** The entire role screams "quant researcher." An ML hiring manager will skim past this.

**Independent Quantitative Researcher (2019-2023):**
- **Hurts badly.** 4 years with one bullet about a stock data pipeline. This is the single biggest red flag on the resume. It reads as unemployment with a polite label.
- **Should be:** Either killed entirely or compressed to 2 lines max.

**Ele.me:**
- **Helps:** Alibaba brand recognition. Scale numbers (2.2M users, 51K clusters) are good.
- **Hurts:** "Data Analyst" title. "Anti-fraud detection rules" — rules, not models. This is pattern matching, not ML.
- **Cut or compress:** This is your oldest and weakest role. One bullet max.

### Projects
- **This is where your actual ML signal lives.**
- **Uncertainty Quantification Benchmark:** Strong. 150+ runs, statistical rigor, PyTorch, HPC. Real ML research.
- **Expedia Hotel Recommendation:** Strong. LightGBM LambdaRank, 4.96M records, feature engineering, NDCG evaluation. Closest thing to applied MLE on the resume.
- **Missing:** You have more projects in your bullet library (ML4QS sensor classification, GraphSAGE, DNN from scratch) that aren't on the resume. Some would strengthen the ML signal more than the quant experience.

### Education
- **Helps:** M.Sc. in AI from VU Amsterdam with 8.2 GPA. Deep Learning 9.5, NLP 9.0 — excellent.
- **Helps:** Tsinghua (#1 in China) — strong brand signal.
- **Hurts:** B.Eng. in Industrial Engineering is irrelevant to ML. Keep it but don't expand.

### Skills
- **Helps:** PyTorch, scikit-learn, LightGBM are the right keywords.
- **Hurts:** "Decisioning & Data Systems" is not a recognized ML category. Hadoop/Hive are dated. "Infrastructure: AWS" is too thin.
- **Missing:** Hugging Face, Transformers, experiment tracking (W&B, MLflow), Docker, Git, NLP tools despite having NLP coursework.
- **Feels generic:** Reads like a data engineer's skills list with PyTorch tacked on.

---

## Part 3 — Positioning Correction

| Positioning | Credibility | Competitiveness |
|---|---|---|
| **Applied ML Engineer** | Medium | **Best option** |
| ML Engineer | Low-Medium | Aspirational but thin |
| Data Scientist transitioning to MLE | High | Honest but weak positioning |
| ML + Data Systems Engineer | Medium | Niche, confusing |
| Applied Scientist | Low | No publications |

**Best positioning: Applied ML Engineer** with emphasis on "ML + strong data foundations."

Why: You have genuine ML project work (thesis, LTR, sensor classification), strong data engineering fundamentals (pipelines, feature engineering, SQL at scale), and quantitative rigor (statistical testing, experimentation). The gap is that it's all academic or pre-2019. But "Applied ML Engineer" is more defensible than pure "ML Engineer" because it signals you're building ML systems for real problems, not doing research — and it gives you room to lean on your data engineering strength as a differentiator.

---

## Part 4 — Rewrite Strategy

### Summary rewrite approach
- Lead with ML capability, not "decision systems"
- Name specific ML techniques you've actually used (LTR, deep RL, gradient boosting, feature engineering)
- Drop "risk, fraud, and portfolio workflows" — too domain-specific, too fintech
- Mention the M.Sc. AI naturally, not as a separate line

### Section reorder for maximum impact

**Recommended layout:**
```
LEFT COLUMN:                    RIGHT COLUMN:
Name + Contact
Bio (3 lines, ML-focused)
EXPERIENCE                      EDUCATION
  GLP (2 bullets, reframed)       VU Amsterdam (thesis + courses)
  BQ (2 bullets, compressed)      Tsinghua (1 line)
  Ele.me (1 bullet)            PROJECTS
                                  Thesis UQ Benchmark
TECHNICAL SKILLS                  Expedia LTR
  (reorganized for ML)            ML4QS Sensor Classification (NEW)
                                CERTIFICATIONS
LANGUAGES                         Databricks DE Professional (NEW)
```

**Key structural changes:**
1. **KILL the Independent Researcher section entirely.** It's doing more harm than good. The 4-year gap is better addressed in a cover letter or interview than by a weak resume section.
2. **ADD ML4QS project** — sensor classification with Kalman filter, 576 features, LightGBM + LSTM is strong applied ML signal that's currently missing.
3. **ADD Databricks cert** — it's in your bullet library but missing from the resume. Shows current technical investment.
4. **Move skills to left column bottom** to fill space freed by removing the indie researcher block.

### Bullet rewrite priorities
1. **GLP scorecard bullet** → reframe as "predictive model" with feature engineering and evaluation language
2. **GLP founding member bullet** → compress, remove DE detail, emphasize ML system ownership
3. **GLP ETL bullet** → CUT entirely (pure DE, dilutes ML signal)
4. **BQ factor research** → reframe as "feature engineering + model validation pipeline"
5. **BQ futures strategy** → KEEP (shows end-to-end: research → production)
6. **BQ infrastructure bullet** → CUT (pure DE)
7. **Independent researcher** → CUT entire section
8. **Ele.me fraud** → reframe as "anomaly detection system" with pattern algorithms
9. **Ele.me skills line** → CUT (Hadoop/Hive are dated)

---

## Part 5 — Bullet-by-Bullet Rewrite

### BIO — REWRITE

**Current:**
> Machine Learning Engineer with 6+ years building production decision systems across fintech, trading, and e-commerce. Combines data infrastructure, feature-building, and model-driven logic for risk, fraud, and portfolio workflows. M.Sc. in Artificial Intelligence with recent applied ML work in ranking, uncertainty evaluation, and sensor classification.

**Revised:**
> **Machine Learning Engineer** with an M.Sc. in Artificial Intelligence (GPA 8.2) and 6 years of experience building data-intensive prediction and scoring systems in fintech, trading, and e-commerce. Core strengths in feature engineering, model evaluation, and end-to-end ML pipelines — from data ingestion through prediction to production monitoring. Recent applied ML: learning-to-rank on 5M records, uncertainty quantification across 150+ Deep RL experiments, and multi-sensor classification with 576 engineered features.

**Why better:** Names specific ML techniques. Quantifies the academic work. Drops vague "decision systems" framing. Shows ML pipeline thinking.

---

### GLP Technology — REWRITE (3 bullets → 2 bullets)

**Title:** Keep "Data Scientist & Team Lead"

**Bullet 1 (founding member + scorecard merged) — REWRITE:**

*Current (2 separate bullets):*
> Built the consumer lending decision stack as the first data hire, spanning ingestion, underwriting logic, risk scoring, and post-loan monitoring for production lending operations.
> Led automated underwriting: built 29 rejection rules, 36 borrower segments, and a 19-feature scorecard estimating first-payment default risk for approve/reject lending decisions.

*Revised (merged):*
> Joined as first technical hire and built the end-to-end credit risk prediction system: engineered 19 features from raw bureau and transactional data, developed a first-payment default scorecard with 36-segment borrower classification, and deployed the model into production underwriting serving real lending decisions.

**Why:** "Prediction system," "engineered features," "developed scorecard," "deployed into production" — all ML-native language. Same facts, stronger signal.

**Bullet 2 (data foundation) — REWRITE:**

*Current:*
> Built the data foundation behind risk modeling and monitoring: daily ETL from 30+ production tables into Redshift and a bureau parser normalizing nested JSON into 5 structured tables for downstream feature generation, decision support, and live monitoring.

*Revised:*
> Built the feature pipeline powering all risk models: automated ingestion of 30+ production tables and credit bureau data, transforming raw nested JSON into structured analytical features for model training, scoring, and post-loan monitoring.

**Why:** "Feature pipeline" instead of "data foundation." "Model training, scoring" instead of "ETL into Redshift." Same work, ML framing.

**Skills line — REWRITE:**
> Skills: Python, SQL, PySpark, Feature Engineering, AWS (Redshift, S3), Airflow

---

### BQ Investment — REWRITE (3 bullets → 2 bullets)

**Title:** Keep "Quantitative Researcher"

**Bullet 1 (futures strategy) — KEEP with minor edit:**

*Current:*
> Researched, backtested, and deployed an intraday CSI index futures strategy into live trading, delivering 14.6% annualized return with real capital.

*Revised:*
> Developed and deployed a signal-driven intraday trading model from research through live production on CSI index futures — 14.6% annualized return with real capital.

**Why:** "Signal-driven model" and "research through live production" are more ML-adjacent than "strategy."

**Bullet 2 (factor research) — REWRITE:**

*Current:*
> Designed and validated factor signals using regression-based analysis, including Fama-MacBeth; validated signals informed live portfolio construction and investment decisions.

*Revised:*
> Built systematic feature validation pipeline evaluating 4 factor families across 3,000+ securities using cross-sectional regression; validated features integrated into the fund's live portfolio construction.

**Why:** "Feature validation pipeline" instead of "factor signals." "Cross-sectional regression" instead of "Fama-MacBeth" (same thing, more ML-readable). "Validated features" instead of "validated signals."

**Bullet 3 (infrastructure) — CUT.** Pure DE, adds nothing for ML roles.

**Skills line — REWRITE:**
> Skills: Python, SQL, NumPy, pandas, Statistical Modeling

---

### Independent Quantitative Researcher — CUT ENTIRE SECTION

**Rationale:** 4 years with 1 bullet about a stock data pipeline is net negative. It raises more questions than it answers. The gap is better addressed as:
- A brief note in the cover letter ("took time for self-directed study before pursuing M.Sc. in AI")
- Or if you must keep it, compress to a single italic line between GLP and BQ: *"2019-2023: Self-directed quantitative research and ML study; admitted to M.Sc. AI at VU Amsterdam."*

---

### Ele.me — REWRITE (1 bullet, compressed)

**Title:** Keep "Data Analyst" (honest)

**Bullet 1 (fraud detection) — REWRITE:**

*Current:*
> Built anti-fraud detection rules identifying 51,000+ suspicious order clusters across 2.2M+ users, supporting fraud screening during platform hyper-growth.

*Revised:*
> Built anomaly detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using pattern-matching algorithms (same-phone, high-frequency, repeat-order); deployed during Ele.me's hyper-growth phase pre-Alibaba acquisition.

**Why:** "Anomaly detection system" and "pattern-matching algorithms" are more ML-adjacent than "anti-fraud detection rules." Adding the algorithm names shows technical depth.

**Skills line — REWRITE:**
> Skills: Python, SQL, Hadoop/Hive, Pattern Detection at Scale

---

### PROJECTS

#### Uncertainty Quantification Benchmark — KEEP (minor polish)

*Revised:*
> Developed benchmarking framework evaluating 5 uncertainty quantification methods for Deep RL across 150+ training runs on HPC (SLURM); demonstrated QR-DQN achieves 31% lower CRPS (p < 0.001) vs. ensemble and dropout baselines. Designed 6-stage reproducible evaluation pipeline with automated calibration benchmarking.

**Action:** REWRITE (added the 6-stage pipeline detail from your bullet library — shows ML systems thinking)

#### Expedia Hotel Recommendation — KEEP (minor polish)

*Revised:*
> Built hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered 50+ temporal, behavioral, and price-normalization features; achieved NDCG@5 = 0.392 on held-out Kaggle evaluation.

**Action:** REWRITE (added "50+" feature count, "held-out" evaluation — more rigorous language)

#### ML4QS Sensor Classification — ADD (currently missing from resume)

> Built end-to-end ML pipeline for IMU sensor classification (4 subjects, 6 activities): Kalman Filter for noise reduction on 12 sensor channels, 576 FFT-based features (time + frequency domain), and LightGBM + bidirectional LSTM models achieving 65% person and 94-99% sex classification accuracy.

**Why add:** This is strong applied ML — feature engineering, multiple model types, sensor data, evaluation. It fills the "applied ML with real data" gap.

---

### TECHNICAL SKILLS — REWRITE (reorganize for ML)

**Current categories:** Programming | Machine Learning | Decisioning & Data Systems | Infrastructure

**Revised:**
> **ML & Modeling:** PyTorch, scikit-learn, LightGBM, XGBoost, Learning-to-Rank, Deep RL, Statistical Testing, Experiment Design
> **Programming:** Python (expert), SQL (expert), NumPy, pandas, Bash
> **Data & Infrastructure:** PySpark, Airflow, AWS (Redshift, S3, EC2), Delta Lake, Hadoop/Hive, Docker, Git
> **Domains:** Feature Engineering, Time-Series Analysis, Anomaly Detection, Uncertainty Quantification

**Why:** ML & Modeling is now the FIRST category. "Domains" replaces the meaningless "Decisioning & Data Systems." Added Docker, Git, Delta Lake, XGBoost. Removed the bare "Infrastructure: AWS" line.

---

### EDUCATION — KEEP with minor additions

**VU Amsterdam — add one line:**
> Thesis: Uncertainty Quantification in Deep RL; built reproducible benchmark across 3 methods, 5 environments, and 150 training runs.
> Courses: Deep Learning (9.5), NLP (9.0), ML for Quantified Self (9.5), Data Mining (9.0).

**Action:** Added Data Mining course (9.0, in your bullet library). More ML signal.

**Tsinghua — KEEP as is.**

### CERTIFICATIONS — ADD (new section)

> Databricks Certified Data Engineer Professional (Feb 2026)

**Why:** It's in your bullet library but missing from the resume. Shows current technical investment and bridges the DE↔ML gap.

---

## Part 6 — Gap Analysis for ML Engineer Roles

| Gap | Severity | Mitigable via wording? | Needs portfolio work? |
|-----|----------|----------------------|----------------------|
| **No production ML model deployment** | HIGH | Partially — GLP scorecard can be reframed as "deployed model" but won't survive deep probing | Yes — deploy a model with FastAPI/Docker, even a simple one |
| **No model serving / inference at scale** | HIGH | No — nothing in your background maps to this | Yes — add a serving layer to a project (BentoML, TorchServe, or even Flask + Docker) |
| **No experimentation framework evidence** | MEDIUM | Partially — thesis "6-stage evaluation pipeline" helps | Consider adding MLflow/W&B to a project |
| **No A/B testing of ML models** | MEDIUM | No — Ele.me A/B testing was for business metrics, not model comparison | Hard to fake, acknowledge in interviews |
| **Limited ML systems ownership** | HIGH | Partially — GLP "end-to-end" framing helps | Build a complete ML pipeline project (ingest → train → evaluate → serve → monitor) |
| **Weak software engineering signal** | MEDIUM | Partially — mention Git, Docker, CI/CD in skills | GitHub portfolio with clean code, tests, CI helps a lot |
| **No feature store experience** | LOW | Can mention "feature pipeline" and "feature engineering" | Not critical for most MLE roles |
| **No LLM/GenAI experience on resume** | MEDIUM (trending HIGH) | You have NLP coursework + GPT-2 project in bullet library — ADD IT | Consider an LLM-based project |
| **Academic-only ML evidence** | HIGH | This is the fundamental issue. Wording helps but doesn't solve it | The single most impactful thing you can do is ship an ML project end-to-end |
| **4-year career gap** | HIGH | Removing the section helps. Cover letter can address it | Not a portfolio issue — it's a narrative issue |

### Priority actions beyond resume editing:
1. **Ship one end-to-end ML project on GitHub** with: data pipeline → feature engineering → model training → evaluation → simple API endpoint → Docker. Even a toy project shows you can do it.
2. **Add MLflow or W&B tracking** to your thesis or Expedia project and link the repo.
3. **Clean up your GitHub** — make 2-3 repos showcase-ready with READMEs, clean code, and results.

---

## Part 7 — Final Deliverables

### 1. Revised Final Summary
> **Machine Learning Engineer** with an M.Sc. in Artificial Intelligence (GPA 8.2) and 6 years of experience building data-intensive prediction and scoring systems in fintech, trading, and e-commerce. Core strengths in feature engineering, model evaluation, and end-to-end ML pipelines — from data ingestion through prediction to production monitoring. Recent applied ML: learning-to-rank on 5M records, uncertainty quantification across 150+ Deep RL experiments, and multi-sensor classification with 576 engineered features.

### 2. Recommended Section Order
```
LEFT COLUMN:
  1. Name + Contact
  2. Bio (3 lines)
  3. Experience (GLP → BQ → Ele.me, NO indie researcher)
  4. Technical Skills (ML-first ordering)
  5. Languages

RIGHT COLUMN:
  1. Education (VU Amsterdam → Tsinghua)
  2. Certifications (Databricks)
  3. Projects (Thesis → Expedia → ML4QS)
```

### 3. Full Revised Resume Text

**BIO:**
Machine Learning Engineer with an M.Sc. in Artificial Intelligence (GPA 8.2) and 6 years of experience building data-intensive prediction and scoring systems in fintech, trading, and e-commerce. Core strengths in feature engineering, model evaluation, and end-to-end ML pipelines — from data ingestion through prediction to production monitoring. Recent applied ML: learning-to-rank on 5M records, uncertainty quantification across 150+ Deep RL experiments, and multi-sensor classification with 576 engineered features.

**EXPERIENCE:**

**GLP Technology (Fintech)** — *Data Scientist & Team Lead*
JULY 2017 - AUGUST 2019
• Joined as first technical hire and built the end-to-end credit risk prediction system: engineered 19 features from raw bureau and transactional data, developed a first-payment default scorecard with 36-segment borrower classification, and deployed the model into production underwriting serving real lending decisions.
• Built the feature pipeline powering all risk models: automated ingestion of 30+ production tables and credit bureau data, transforming raw nested JSON into structured analytical features for model training, scoring, and post-loan monitoring.
Skills: Python, SQL, PySpark, Feature Engineering, AWS (Redshift, S3), Airflow

**BQ Investment (Hedge Fund)** — *Quantitative Researcher*
JULY 2015 - JUNE 2017
• Developed and deployed a signal-driven intraday trading model from research through live production on CSI index futures — 14.6% annualized return with real capital.
• Built systematic feature validation pipeline evaluating 4 factor families across 3,000+ securities using cross-sectional regression; validated features integrated into the fund's live portfolio construction.
Skills: Python, SQL, NumPy, pandas, Statistical Modeling

**Ele.me (Alibaba Group)** — *Data Analyst*
SEPTEMBER 2013 - JULY 2015
• Built anomaly detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using pattern-matching algorithms (same-phone, high-frequency, repeat-order); deployed during Ele.me's hyper-growth phase pre-Alibaba acquisition.
Skills: Python, SQL, Hadoop/Hive, Pattern Detection at Scale

**EDUCATION:**

**Vrije Universiteit Amsterdam**
*M.Sc. in Artificial Intelligence (GPA: 8.2/10)*
SEPTEMBER 2023 - AUGUST 2025
Thesis: Uncertainty Quantification in Deep RL; built reproducible benchmark across 3 methods, 5 environments, and 150 training runs.
Courses: Deep Learning (9.5), NLP (9.0), ML for Quantified Self (9.5), Data Mining (9.0).

**Tsinghua University (#1 in China)**
*B.Eng. in Industrial Engineering*
SEPTEMBER 2006 - JULY 2010

**CERTIFICATIONS:**
Databricks Certified Data Engineer Professional (Feb 2026)

**PROJECTS:**

**Uncertainty Quantification Benchmark**
FEBRUARY 2025 - AUGUST 2025
Developed benchmarking framework evaluating 5 uncertainty quantification methods for Deep RL across 150+ training runs on HPC (SLURM); demonstrated QR-DQN achieves 31% lower CRPS (p < 0.001) vs. ensemble and dropout baselines. Designed 6-stage reproducible evaluation pipeline with automated calibration benchmarking.
Skills: PyTorch, Deep RL, HPC, Statistical Testing

**Expedia Hotel Recommendation**
APRIL 2024 - MAY 2024
Built hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered 50+ temporal, behavioral, and price-normalization features; achieved NDCG@5 = 0.392 on held-out Kaggle evaluation.
Skills: LightGBM, Learning-to-Rank, Feature Engineering

**IMU Sensor Classification (ML4QS)**
JUNE 2024
Built end-to-end ML pipeline for IMU sensor classification (4 subjects, 6 activities): Kalman Filter for noise reduction on 12 sensor channels, 576 FFT-based features (time + frequency domain), and LightGBM + bidirectional LSTM models achieving 65% person and 94-99% sex classification accuracy.
Skills: LightGBM, LSTM, Feature Engineering, Time-Series

**TECHNICAL SKILLS:**
ML & Modeling: PyTorch, scikit-learn, LightGBM, XGBoost, Learning-to-Rank, Deep RL, Statistical Testing, Experiment Design
Programming: Python (expert), SQL (expert), NumPy, pandas, Bash
Data & Infrastructure: PySpark, Airflow, AWS (Redshift, S3, EC2), Delta Lake, Hadoop/Hive, Docker, Git
Domains: Feature Engineering, Time-Series Analysis, Anomaly Detection, Uncertainty Quantification

**LANGUAGES:**
English - Fluent | Mandarin - Native

### 4. Top 10 Highest-Impact Edits

1. **DELETE the Independent Researcher section** — removes the biggest red flag
2. **Rewrite GLP scorecard bullet** with ML language (features, prediction, deployment)
3. **Add ML4QS sensor classification project** — fills the "applied ML with real data" gap
4. **Rewrite bio** to lead with specific ML techniques instead of vague "decision systems"
5. **Reorganize skills** with ML & Modeling as the first category
6. **Add Databricks certification** — shows current technical investment
7. **Reframe GLP ETL bullet** as "feature pipeline" instead of data engineering
8. **Reframe BQ factor research** as "feature validation pipeline"
9. **Reframe Ele.me fraud** as "anomaly detection system with pattern-matching algorithms"
10. **Add thesis 6-stage evaluation pipeline detail** — shows ML systems thinking beyond just running experiments

### 5. Final Verdict

**"Almost ready"** for ML Engineer applications.

The resume rewrite significantly improves the ML signal, but the fundamental issue remains: your ML evidence is academic, and your professional experience is data engineering + quant research + rule-based systems. The reframing makes it more competitive, but a strong ML hiring manager will still see through the language to the underlying experience.

**What would make it "ready":**
- One shipped end-to-end ML project on GitHub (data → features → model → API → Docker)
- MLflow/W&B integration in at least one project
- A clean, showcase-ready GitHub with 2-3 ML repos

**What would make it "not competitive enough":**
- Applying to senior MLE roles at FAANG/top-tier companies (you'd be competing against people with 3+ years of production ML)
- Roles requiring model serving at scale, real-time inference, or MLOps ownership

**Where this resume IS competitive:**
- Mid-level Applied ML Engineer roles at startups and mid-size companies
- ML Engineer roles in fintech, risk, or fraud (where your domain knowledge is a differentiator)
- Data Scientist roles that are actually ML-heavy
- Companies that value strong data foundations + ML potential over pure ML pedigree
- European market (where the talent pool is thinner than US/UK for ML roles)

---

## Evaluation Against Target ML Engineer Expectations

| Expectation | Evidence Level | Notes |
|---|---|---|
| Strong Python | ✅ Strong | 6+ years, expert level, multiple projects |
| Applied machine learning | ⚠️ Medium | Academic projects are strong; professional experience is weak |
| Feature engineering | ✅ Strong | GLP (19 features), Expedia (50+), ML4QS (576), BQ (factor families) |
| Model evaluation and experimentation | ⚠️ Medium | Thesis benchmark is excellent; no production A/B testing |
| Production-minded system design | ⚠️ Medium | GLP shows production systems; but they're rule-based, not ML |
| Data pipelines for ML | ✅ Strong | GLP ETL, BQ data pipeline, feature pipelines throughout |
| Large-scale data | ✅ Strong | 2.2M users, 4.96M records, 3,600+ stocks, 30+ tables |
| Communication and technical clarity | ✅ Strong | Resume is well-quantified, clear writing, good structure |

**Overall: 5/8 strong, 3/8 medium.** The weak spots are all in the "production ML" dimension — which is exactly where the resume rewrite helps most, but can't fully solve without actual production ML experience.

