# Interview Strategy — FareHarbor ML Engineer

**Date:** 2026-02-23 (Monday) 15:00-15:30 CET
**Platform:** Google Meet — https://meet.google.com/rii-mume-wpc
**Format:** 30-min first round — likely recruiter/hiring manager intro

---

## Interview Nature

FareHarbor's typical process: Recruiter Call → Technical Round 1 → Technical Round 2 + System Design → Manager Round. This 30-min slot is likely the first screening. Glassdoor rates their interview experience very positively (68.6% positive), described as "the smoothest interview process."

## FareHarbor Interview Process (Expected)

1. **Recruiter Call (THIS ONE)** — Introduction, motivation, background
2. Technical Round 1 — Easy-medium coding (arrays, hashmaps, basic algorithms)
3. Technical Round 2 + System Design — Harder coding + ML pipeline design
4. Manager/Director Round — Behavioral, team fit

---

## Three Key Narratives

### Narrative 1: "End-to-End Production ML"

> At GLP, I owned the **complete ML lifecycle** for credit scoring: data ingestion (PySpark) → feature engineering (500+ features) → model training (XGBoost/LightGBM) → deployment → portfolio monitoring. This wasn't a research project — the model directly drove automated credit decisions with real money. That's exactly the production-grade ML pipeline work your Pricing team needs.

**Use when:** "Tell me about your ML experience" / "Have you built production systems?"

### Narrative 2: "Experimentation & A/B Testing"

> At Ele.me (now part of Alibaba), I designed a user segmentation experiment: clustered millions of users by behavior using K-means, then A/B tested reactivation strategies. Result: **2x improvement in churned-user reactivation rate**. I understand the full experiment lifecycle — hypothesis formation, sample size calculation, randomization, running the test, statistical significance testing, and interpreting results.

**Use when:** "Tell me about A/B testing" / "How do you validate model performance?"

### Narrative 3: "RL + Optimization Background"

> My M.Sc. thesis was literally about **Deep RL + Uncertainty Quantification** — 150+ training runs benchmarking 5 UQ methods. JD mentions multi-armed bandits and contextual bandits as nice-to-haves — that's my research area. Plus, at Baiquan I built a quantitative factor engine and backtesting framework — **optimization under uncertainty** is what I do. The transfer from "financial optimization" to "pricing optimization" is natural.

**Use when:** "Do you have RL experience?" / "How would you approach dynamic pricing?"

---

## Critical Questions & Prepared Responses

### "Why FareHarbor?"

> "Three things: First, the **Pricing & Revenue Management** problem is fascinating — pricing in travel has unique challenges like seasonality, weather, event-driven demand. Second, FareHarbor has the **scale** of Booking Holdings but the **speed** of a smaller team — I can see my work impact 19,000+ clients across 90 countries. Third, I'm based in Amsterdam and this is the kind of hands-on ML engineering role where I can grow."

### "Tell me about your production ML experience."

> **(STAR — GLP Credit Scoring)**
> **S:** First data hire at a consumer lending startup. No ML infrastructure existed.
> **T:** Build a credit scoring system that could automate loan decisions.
> **A:** Built the full pipeline: PySpark ETL for data ingestion, feature engineering (credit history, repayment patterns, application data), trained XGBoost/LightGBM models, deployed to production, built portfolio monitoring dashboards.
> **R:** Enabled automated credit decisions. Monitoring system caught early warning signals that informed collection strategy adjustments.

### "How would you approach pricing optimization for tours/activities?"

> "It's a classic explore/exploit problem. I'd start with **contextual bandits** — using features like location, time of booking, day of week, seasonal demand, and user browsing history to dynamically select price points. **Thompson Sampling** would balance exploration vs exploitation naturally. The key design decisions are:
> 1. Defining the reward signal — pure revenue? Or revenue × conversion trade-off?
> 2. Setting guardrail metrics — conversion rate shouldn't drop below X during exploration
> 3. Building the feedback loop — how quickly can we observe outcomes and update the model?
> I'd instrument everything with proper A/B testing to validate that the ML-driven pricing actually outperforms the baseline."

### "Experience with A/B testing?"

> "At Ele.me: formulated hypothesis (segmented reactivation > uniform), calculated required sample size, set up randomized user groups, ran for 2 weeks, used statistical significance testing to validate. Result: 2x reactivation lift. Key lesson: always define your metrics and guardrails BEFORE running the experiment, and watch for novelty effects."

### "What's your visa situation?"

> "I'm on a Zoekjaar (Orientation Year) permit, valid until November 2026. I need a Kennismigrant (Highly Skilled Migrant) visa through a recognized sponsor. FareHarbor, as part of Booking Holdings, would be a recognized sponsor. The salary threshold is the reduced rate of €3,122/month."

---

## Questions to Ask (Pick 2)

1. "What does the current ML stack look like for the Pricing team? Are you using MLflow/SageMaker, or something custom?"
2. "How does the team run experiments — what's the typical cycle from hypothesis to production deployment?"
3. "How large is the Pricing & Revenue Management ML team? How does it interact with the backend engineering team?"
4. "What's the biggest ML challenge the team is currently working on?"

---

## Company Research Quick Facts

- FareHarbor: largest tour/activity booking platform, 19K+ clients, 90+ countries
- Acquired by Booking Holdings 2018
- Amsterdam = European HQ, engineering hub
- Glassdoor: 3.7/5 WLB, 2.9/5 career opportunities, 2.7/5 compensation
- Interview experience: 68.6% positive, ~18 days average
- Small teams, high impact (e.g., 4 engineers supporting 3K+ client websites)
- Python/Django backend, PostgreSQL, Redis
- "Ohana" culture

---

## Technical Quick Review (For later rounds)

| Topic | 30-Second Answer |
|-------|-----------------|
| **Multi-armed Bandits** | Each arm = a price point. Epsilon-greedy (simple, explore ε% of time), UCB (upper confidence bound, optimistic), Thompson Sampling (Bayesian, sample from posterior — best for pricing) |
| **Contextual Bandits** | Add user/context features to bandit. Model: P(reward | context, action). LinUCB or neural contextual bandits. |
| **A/B Test Design** | Define hypothesis → power analysis (sample size) → randomize → run → test significance (t-test/chi-square) → check for novelty effects |
| **ML Pipeline Design** | Feature store → Training (offline) → Validation (holdout + A/B) → Shadow mode → Canary deployment → Full rollout → Monitoring → Rollback |
| **Model Monitoring** | Track prediction drift (PSI), feature drift, latency, error rates. Alert on degradation. Automated retraining triggers. |
