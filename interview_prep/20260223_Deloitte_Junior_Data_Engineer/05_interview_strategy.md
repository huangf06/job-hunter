# Interview Strategy — Deloitte Junior Data Engineer

**Date:** 2026-02-23 (Monday) 13:30-14:00 CET
**Platform:** Microsoft Teams
**Interviewer:** Anna Slootman (Campus Recruiter)
**Format:** 30-min first round — likely behavioral + background match

---

## Interview Nature

This is the **third step** of Deloitte's process (after CV screening + online assessment). Anna is a Campus Recruiter, so expect a culture-fit / motivation / background screening round. Not a deep technical interview. 30 minutes means you need to be concise.

## Deloitte Interview Process (Full)

1. ~~CV Screening~~ (done)
2. ~~Online Assessment~~ (done — personality, skills, SQL/Python)
3. **First Interview (THIS ONE)** — Online, recruiter/hiring manager
4. Second Interview — On-site, Partner/Director round

---

## Three Key Narratives (Pick the best 2-3 for 30 min)

### Narrative 1: "Perfect Technical Match"

> JD asks for Spark, Delta Lake, PySpark, AWS, Airflow — I don't just know them, I have a **Databricks Certified Data Engineer Professional** certification. At GLP, I built PySpark ETL pipelines from scratch for consumer credit data. My recent Financial Data Lakehouse project uses Databricks + Delta Lake + Medallion Architecture + AWS — exactly the work you describe.

**Use when:** "Tell me about your technical background" / "Why are you a good fit?"

### Narrative 2: "Consulting-Ready Communicator"

> At GLP I was the **first data hire** — not just writing code, but coordinating with risk, product, operations, legal, and external vendors. At Henan Energy (Fortune Global 500), I managed stakeholder relationships across **12 subsidiary companies** and presented to senior management. This cross-functional communication is exactly what consulting requires.

**Use when:** "Tell me about teamwork" / "Can you work with clients?" / "Why consulting?"

### Narrative 3: "Why Junior at Deloitte"

> I have 6 years of data experience in China, but I just completed my M.Sc. in AI in the Netherlands. I want to build my European consulting career from a solid foundation. Deloitte offers something product companies can't — **exposure to diverse industries and data challenges**. My experience means I can deliver value faster while learning the European data governance and compliance landscape.

**Use when:** "Why this role?" / "Aren't you overqualified?" / "Where do you see yourself in 3 years?"

---

## Critical Questions & Prepared Responses

### "How is your Dutch?"

> "I'm actively learning — I've lived in Amsterdam for 2.5 years and my daily Dutch is improving. In my experience, most technical work and international client engagements are conducted in English. I'm committed to reaching professional-level Dutch and happy to take language courses. My Mandarin is also an asset for Deloitte's APAC clients."

**Key:** Don't dodge. Be honest but frame it positively.

### "Why apply for a Junior position with 6 years of experience?"

> "I see it as my entry point into European consulting. My China experience gives me a strong technical foundation, but the consulting business model, European regulatory landscape, and client-facing dynamics are new territory I want to master properly. Deloitte's professional development structure is a big draw — and frankly, my experience should help me grow to the next level faster."

### "What's your visa situation?"

> "I'm on a Zoekjaar (Orientation Year) visa, valid until November 2026. To continue working, I'll need to transition to a Kennismigrant (Highly Skilled Migrant) permit. Deloitte is an erkend referent (recognized sponsor), so the process is straightforward. The salary threshold for my situation is the reduced rate of €3,122/month."

**Key:** Show you've done your homework. Deloitte sponsors regularly.

### "Why Deloitte specifically?"

> "Your Platform Development & Integration team does exactly what I'm passionate about — helping organizations modernize their data infrastructure. What excites me is the variety: one quarter you might be building a lakehouse for a bank, the next a streaming pipeline for a retailer. That breadth is unique to consulting. Plus, Deloitte has one of the largest data practices globally — the learning opportunities are unmatched."

### "Tell me about a challenging project."

> **(STAR — GLP Data Infrastructure)**
> **S:** First data hire at a consumer lending startup. No data infrastructure existed.
> **T:** Build the entire data platform — ingestion, ETL, quality checks, ML models, monitoring.
> **A:** Chose PySpark for scalability, implemented schema validation frameworks, built credit scoring models end-to-end, set up portfolio risk monitoring.
> **R:** Enabled automated credit decisions for the business. Mentored a junior analyst. The system processed millions of loan records reliably.

---

## Questions to Ask Anna (Pick 2)

1. "What does the typical project engagement look like for a data engineer? How long do projects usually last?"
2. "What does the next step in the interview process look like — is it a technical assessment or a partner round?"
3. "How does the team balance between cloud platforms? Is it mostly AWS, or do you see Azure and GCP equally?"
4. "What's the typical career progression from Junior to Consultant in the data engineering track?"

---

## Company Research Quick Facts

- Deloitte Netherlands: 3.7/5 work-life balance, 4.1/5 career opportunities
- Data Engineer employees: 91% recommendation rate
- 75+ experts in Data & Responsible Insights team
- Focus areas: data architecture, pipelines, quality, governance
- Junior Consultant salary: ~36-40K EUR/year base
- Culture: learning-oriented, structured, Big 4 pace

---

## Technical Quick Review (In case of surprise questions)

| Topic | 30-Second Answer |
|-------|-----------------|
| **Medallion Architecture** | Bronze (raw ingest) → Silver (cleaned, validated, conformed) → Gold (business aggregates, ready for analytics/ML) |
| **Delta Lake vs Parquet** | Delta adds ACID transactions, time travel, schema evolution, merge/upsert on top of Parquet |
| **Why Airflow** | DAG-based orchestration, dependency management, retry logic, monitoring UI, industry standard |
| **PySpark vs Pandas** | PySpark for distributed/big data (cluster), Pandas for single-node; PySpark lazy evaluation + catalyst optimizer |
| **Schema Evolution** | Adding/changing columns without breaking downstream; Delta Lake handles mergeSchema automatically |
