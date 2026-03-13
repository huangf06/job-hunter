# ML Resume v3 Design Document

**Date:** 2026-03-12
**Version:** 3.0
**Target:** ML Engineer roles in Europe/Netherlands (mixed company types)
**Strategy:** Full-Stack ML Engineer (Approach C)

---

## Design Principles

1. **Balanced impact philosophy** - Claims are defensible in 3-5 minute interviews, using all available evidence
2. **No LLM over-emphasis** - One project shows capability, not a core positioning
3. **Full lifecycle ownership** - Modeling → evaluation → deployment thread throughout
4. **Production + Quant + Applied ML** - Three pillars equally weighted

---

## Key Changes from v2

### Removed:
- "6+ years" from bio (draws attention to gap)
- Independent Researcher bullets (title only, no content)
- "Prompt Engineering" from skills (not deep enough)
- "Deep RL" from skills (too academic)

### Added:
- "14.6% annualized return" in bio (concrete outcome)
- "hundreds of daily applications" (scale quantification)
- "36-segment borrower classification" (more specific than "36 customer segments")
- "Feature Engineering" to skills (highly defensible)
- "Signal Processing" to skills (from ML4QS)

### Reframed:
- "shipped LLM applications" → "delivered ML projects from feature engineering through deployment"
- "quantitative modeling" → "quantitative evaluation rigor"
- GLP expanded to 4 bullets (hero section)
- BQ compressed to 2 bullets (supporting role)
- Ele.me compressed to 1 bullet (supporting evidence)

---

## Section-by-Section Design

### BIO

**Final version:**
> ML Engineer with production credit decisioning experience and quantitative evaluation rigor. Built decision systems processing hundreds of daily applications in fintech, developed live trading strategies achieving 14.6% annualized return with rigorous backtesting, and delivered ML projects from feature engineering through deployment. Combines hands-on modeling, systematic evaluation, and production deployment experience. M.Sc. in AI from VU Amsterdam.

**Rationale:**
- Opens with core value prop: production + quant rigor
- Concrete outcomes: 14.6%, hundreds of applications
- "Full ML lifecycle" thread: feature engineering → deployment
- No LLM over-emphasis
- 62 words, fits in 4 lines

---

### EXPERIENCE

#### GLP Technology (4 bullets - hero section)

**Bullet 1:** Context + scale + full lifecycle
> First technical hire at a consumer lending fintech; built the credit decisioning system from data pipeline through automated approval and post-loan monitoring, processing hundreds of daily applications.

**Bullet 2:** Hero bullet with all key numbers
> Designed the core decision engine: 29 rejection rules across overdue, debt, inquiry, and customer segment dimensions; 36-segment borrower classification; and a 19-feature scorecard model predicting first-payment default risk.

**Bullet 3:** Production monitoring responsibility
> Developed post-loan monitoring systems including delinquency tracking, repayment trend analysis, and first-repayment early warning with third-party fraud API integration.

**Bullet 4:** Skills line
> **Skills:** Python, SQL, AWS (Redshift, S3, EC2), Airflow, pandas, NumPy

**Rationale:**
- Bullet 2 is the standout: 29, 36, 19 all defensible from source code
- Shows full lifecycle: pipeline → decisioning → monitoring
- "First technical hire" establishes ownership
- All claims defensible from glp_junzheng_deep_work_report.md

---

#### BQ Investment (2 bullets - supporting quant rigor)

**Bullet 1:** Live deployment + outcome
> Developed and deployed an R-Breaker intraday trading strategy for CSI index futures from research through live production, achieving 14.6% annualized return with real capital and rigorous backtesting validation.

**Bullet 2:** Factor research + production integration
> Built a factor research pipeline applying Fama-MacBeth regression across 3,000+ securities; validated factors were integrated into the fund's live portfolio construction.

**Bullet 3:** Skills line
> **Skills:** Python, MATLAB, SQL, NumPy, pandas, scipy

**Rationale:**
- 14.6% return is concrete, defensible from work report
- "rigorous backtesting validation" emphasizes evaluation rigor
- Fama-MacBeth shows statistical sophistication
- Research → production pipeline shown in both bullets

---

#### Ele.me (1 bullet - supporting scale evidence)

**Bullet 1:** Fraud detection scale
> Built an anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern algorithms during hyper-growth at Ele.me (Alibaba Group).

**Bullet 2:** Skills line
> **Skills:** SQL, Hadoop, Hive, Python, pandas, A/B Testing

**Rationale:**
- Strong numbers: 51K, 2.2M
- Compressed to 1 bullet to avoid diluting ML narrative
- Alibaba Group adds credibility

---

#### Independent Quantitative Researcher (title only, no bullets)

**Period:** Sep 2019 - Aug 2023

**Rationale:**
- Title explains the gap without taking space
- No bullets per user decision (space better used for GLP expansion)
- Interview defense: "conducted independent quant research, maintained technical skills, prepared for M.Sc."

---

### EDUCATION

#### VU Amsterdam

**Thesis section:**
> **Thesis:** Uncertainty Quantification in Deep RL
>
> Built an evaluation framework across 3 uncertainty quantification methods, 5 environments, and 150 training runs to systematically benchmark ensemble-based approaches.
>
> Discovered a noise paradox: moderate observation noise unexpectedly improved ensemble uncertainty estimates, revealing that data quality and estimate quality don't always align.

**Rationale:**
- "150 training runs" shows experimental rigor
- "noise paradox" is concrete finding with practical implication
- "systematically benchmark" emphasizes rigor
- Not too academic, but shows research quality

---

### PROJECTS

**Order:** Expedia → ML4QS → Poem Generator (LLM last, not over-emphasized)

#### Project 1: Expedia Hotel Recommendation

> Built a hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered temporal, behavioral, and aggregation features and achieved NDCG@5 = 0.392 in a 200-person ranking competition.
>
> **Skills:** LightGBM, Learning-to-Rank, Feature Engineering

**Rationale:**
- NDCG@5 = 0.392 verified from course report
- "ranking competition" accurate (VU course project)
- Removed "near the top" (can mention verbally if asked)
- Shows ranking/optimization expertise

---

#### Project 2: ML4QS IMU Sensor Classification

> Built an end-to-end ML pipeline for multi-sensor IMU data using Kalman filtering, FFT-based feature engineering, LightGBM, and Bidirectional LSTM.
>
> Engineered 576+ features across time and frequency domains and achieved 65% person identification (4-class) and 94-99% sex classification accuracy.
>
> **Skills:** Python, LightGBM, PyTorch, Optuna, Kalman Filter, Signal Processing

**Rationale:**
- 576+ features is standout number (defensible: 24 sensors × 8 features × 3 windows)
- "4-class" clarifies 65% context
- Shows signal processing + deep learning + feature engineering
- Split into 2 sentences for readability

---

#### Project 3: Poem Generator

> Built a text generation application using GPT-2 and Hugging Face Transformers with prompt controls for style variation; deployed as an interactive web interface via Flask.
>
> **Skills:** Python, GPT-2, Hugging Face Transformers, Flask

**Rationale:**
- Concise, honest about scope
- Shows LLM familiarity without over-claiming
- Removed "Prompt Engineering" from skills (not deep enough)
- Serves purpose: demonstrate LLM API usage + deployment

---

### TECHNICAL SKILLS

**ML & Deep Learning:** PyTorch, scikit-learn, LightGBM, XGBoost, Hugging Face Transformers, Feature Engineering

**Programming:** Python, SQL, MATLAB, Bash

**Data & Infrastructure:** AWS (Redshift, S3, EC2), Airflow, Hadoop, Hive, Docker, Git

**Modeling & Evaluation:** Learning-to-Rank, Fama-MacBeth Regression, Backtesting, Statistical Testing, Signal Processing

**Rationale:**
- Clear hierarchy: ML first, Programming second, Data/Infra third, Modeling fourth
- Removed "Prompt Engineering" and "Deep RL" (not deep enough / too academic)
- Added "Feature Engineering" and "Signal Processing" (highly defensible)
- All skills defensible from experience/projects

---

## Defensibility Audit

### Strongest Claims (Can defend 5+ minutes):
1. **GLP decision engine** (29 rules, 36 segments, 19 features) - full source code
2. **BQ 14.6% return** - work report + live capital
3. **ML4QS 576+ features** - calculation: 24 × 8 × 3
4. **Expedia NDCG@5 = 0.392** - official course report
5. **Thesis 150 training runs** - can explain experimental design

### Moderate Claims (Can defend 3 minutes):
1. **"hundreds of daily applications"** - reasonable inference from GLP context
2. **"51,000+ suspicious clusters"** - from Ele.me work evidence
3. **"3,000+ securities"** - full A-share market coverage at BQ
4. **"200-person ranking competition"** - VU course project, need to clarify if asked

### Weakest Claims (Prepare talking points):
1. **"near the top" (removed from final)** - can't prove specific rank
2. **"rigorous backtesting"** - need to explain backtesting framework if asked
3. **"systematic evaluation"** - need to explain thesis methodology

---

## Interview Preparation Notes

### If asked about LLM depth:
"I have hands-on experience with Hugging Face Transformers and GPT-2 for text generation, including prompt design and Flask deployment. My focus has been on applied ML and production systems rather than LLM research, but I'm comfortable working with LLM APIs and integrating them into applications."

### If asked about Expedia competition:
"This was a VU Data Mining course project using real Expedia data (4.96M records). 200 students participated, and we used a Kaggle-style leaderboard. While it's a course project, the data scale and techniques (LightGBM LambdaRank, learning-to-rank) are industry-standard."

### If asked about 4-year gap:
"After GLP, I conducted independent quantitative research (2019-2023), maintaining technical skills while deepening my understanding of financial markets. This led me to pursue formal AI education at VU Amsterdam, where I focused on deep RL and uncertainty quantification. Now I'm ready to apply this combination of practical experience and academic rigor to production ML systems."

---

## Success Metrics

This resume succeeds if:
1. ✅ Gets interviews at all 5 company types (tech, AI startups, fintech, scale-ups, mixed)
2. ✅ Every claim can be defended in interviews without hesitation
3. ✅ Positions candidate as "full-stack ML engineer" not "quant researcher" or "data engineer"
4. ✅ LLM capability shown but not over-emphasized
5. ✅ Production + quant + applied ML pillars equally visible

---

**Design approved and ready for implementation.**
