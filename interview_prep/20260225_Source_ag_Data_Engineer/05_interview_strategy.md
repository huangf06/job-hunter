# Interview Strategy — Source.ag Data Engineer

**Date:** 2026-02-25 (Tuesday) 10:30-11:00 CET
**Platform:** Google Meet — https://meet.google.com/ctz-ifdz-snv
**ATS Platform:** Recruitee
**Interviewer:** James Godlonton (Engineering Manager)
**Format:** 30-min video interview — first round
**Reschedule link:** https://careers.source.ag/v/i/s/tpr1975h6tg7/ou9d7tr81d41/reschedule

---

## Interviewer Profile — James Godlonton

| Detail | Value |
|--------|-------|
| **Role** | Software Engineering Manager (since Aug 2025, promoted from SE) |
| **At Source.ag since** | May 2023 (~2.8 years) |
| **Previous** | Senior Backend Developer at Helin Data (Mar 2022 – Apr 2023, edge-to-cloud IoT for maritime/energy: Shell, BP, Boskalis) |
| **Before that** | ML Consultant (Sep 2021 – Mar 2022), Pre-Doctoral Fellow at University of Zurich Economics (Nov 2020 – Aug 2021) |
| **Education** | BSc Math & CS (First Class w/ Distinction) + BSc Honours CS (fake news detection thesis), **University of Cape Town**; **MSc Artificial Intelligence, Utrecht University** (2018-2020); Douglas Smith Scholar (Cambridge) |
| **Early career** | AWS intern (Cape Town), NEC Research intern, CS Tutor at UCT |
| **Origin** | South Africa (St. Andrews College, Grahamstown) |
| **Team** | Product Development (~16 people) |

### What This Means For You
- He has an **MSc in AI from Utrecht** — he's not just a backend dev, he deeply understands ML/data. He'll appreciate your AI background.
- His **Helin Data experience** was edge-to-cloud IoT (sensor data from ships/offshore rigs) — directly analogous to Source.ag's greenhouse sensor data. He personally built this kind of pipeline before.
- His **economics pre-doc** background means he values rigorous data quality, statistical thinking, and reproducibility.
- He's a **recently promoted engineering manager** — actively building his team, cares about cultural fit AND technical depth.
- He's an **expat himself** (South Africa → Netherlands via Cambridge/Zurich) — understands international hiring, visa sponsorship context.
- You share a **parallel path**: both international professionals with AI master's degrees in NL, both pivoting from different domains into data engineering. Natural rapport point.
- His Honours thesis was on **NLP / fake news detection** — he appreciates applied ML research. Your thesis on uncertainty quantification in RL will resonate.

---

## Interview Nature Assessment

This is **Round 1 of 3** — the personal introductory round:
1. **Round 1 (THIS ONE):** Personal introductory, 30 min, video call — culture fit + motivation + background
2. **Round 2:** Technical, based on a take-home assignment
3. **Round 3:** Final discussion with senior staff

Each round has 2+ interviewers. James as Engineering Manager is the hiring manager.
- 30 minutes means you need to be concise — 2-3 key stories max
- He'll be evaluating: Can this person operate independently? Do they take ownership? Will they mesh with the team?
- Since he has an **MSc in AI**, he may probe deeper on your ML/data engineering overlap than a typical backend manager would

---

## Additional Intel (from careers page research)

- **Salary range:** €75,000 — €90,000
- **Additional tools in stack** (not in LinkedIn JD): dbt, Dagster (may complement/replace Airflow)
- **Role mission:** Build "one of the biggest agricultural datasets in the world"
- **Requirements (careers page version):** 4+ years production systems, Databricks/Snowflake expertise, Python and/or Golang, AWS
- **Founders:** Both ex-BCG/McKinsey data science leads — consulting DNA in the culture
- **Aspiration:** NL's first AgTech unicorn

---

## Three Key Narratives

### Narrative 1: "Data Platform Builder From Scratch" (LEAD WITH THIS)

> At GLP, I was the **first data hire** at a consumer lending startup — no infrastructure existed. I built the entire data platform: ingestion pipelines, PySpark ETL, data quality frameworks, credit scoring models, and portfolio monitoring. I went from zero to production systems processing millions of loan records. That experience of building from first principles in a resource-constrained environment is exactly what a scale-up needs.

**Use when:** "Tell me about yourself" / "Why are you a good fit?" / "Tell me about a challenging project"

**Why it works for Source.ag:** They explicitly want someone who "takes full ownership from first principles to production" — this is exactly that story.

### Narrative 2: "Data Stack Expert With Your Exact Tools"

> My recent Financial Data Lakehouse project uses Databricks + Delta Lake + Medallion Architecture on AWS — the same core data stack Source.ag runs on. I have my Databricks Certified Data Engineer Professional certification. I've worked with PySpark, Structured Streaming, Schema Evolution, Auto Loader — all the Delta Lake primitives. At Baiquan, I built real-time data pipelines ingesting feeds for 3,000+ securities with automated data quality validation. These are directly transferable to greenhouse sensor data processing.

**Use when:** "Tell me about your technical experience" / "How familiar are you with our stack?"

**Why it works:** Databricks + Delta Lake + AWS + Python overlap is their data layer. Drawing the analogy between financial data feeds and greenhouse sensor data is powerful.

### Narrative 3: "Scale-Up Mentality, Not Corporate Process"

> I've worked at multiple stages: Ele.me during hyper-growth (pre-Alibaba acquisition, millions of users), GLP as a startup from zero, Baiquan as a small quantitative fund. I thrive in environments where things are evolving and you need to make decisions without perfect information. My M.Sc. thesis required running 150 training experiments on HPC clusters — that's iterative, self-directed work. I'm someone who ships first and refines later, which matches your culture of "delivering results over excessive debate."

**Use when:** "Why Source.ag?" / "How do you handle ambiguity?" / "Tell me about working in fast-paced environments"

---

## Critical Questions & Prepared Responses

### "How do you feel about the Golang part of the role?"

> "I don't have production Golang experience, but I'm confident in my ability to pick it up quickly. My foundation is in Python, but I've worked across multiple paradigms — from PySpark distributed processing to NumPy vectorized operations to full ML pipelines. Golang's strengths — concurrency, performance, type safety — are exactly what I'd expect for backend microservices in your architecture. I'm excited to add it to my toolkit. And the data layer work — Databricks, Delta Lake, Python, AWS — I can contribute to immediately while ramping up on Go."

**Key:** Don't dodge. Be honest, show learning agility, and immediately pivot to where you can add value day one.

### "What's your experience with backend services / system design?"

> "At GLP I designed the entire data infrastructure end-to-end — not just ETL scripts, but the service architecture around it: ingestion services, quality validation pipelines, monitoring dashboards, model serving. At Baiquan, I built a factor computation engine that had to reliably process 3,000+ securities daily with automated alerting on failures. My Financial Data Lakehouse project uses event-driven patterns with Structured Streaming — which maps directly to event-driven architectures like EventBridge/SNS/SQS. I think in terms of systems, not just pipelines."

### "Why Source.ag?"

> "I grew up in a farming family in China, so when I came across Source.ag, it wasn't just another data engineering role — I immediately understood the problem you're solving. My parents dealt with unpredictable yields and fragmented information every season, except they had no tools at all. Living in the Netherlands for 2.5 years, I've been impressed by how this tiny country became the world's second-largest agricultural exporter — the greenhouse model is something I think about because I've seen the other extreme growing up. Source.ag is scaling that Dutch expertise globally through software, and that mission is personal for me.
>
> From a data engineering perspective, the problem is genuinely harder and more interesting than finance. Biological systems are non-linear — temperature today affects fruit set six weeks from now. Building reliable pipelines for that is exactly the challenge I want. And the stage of the company is perfect — post-Series B, systems growing complex, needing someone to simplify. That's where I do my best work."

### "The JD says 10+ years — you have ~6. What do you think?"

> "Actually, the careers page lists 4+ years — and I have 6. But more importantly, my experience is directly relevant: at GLP I was the first data hire and defined the entire data platform direction. That's exactly what this role asks for — 'establish foundations and guardrails' and 'define the technical direction for the Databricks platform.' I've done this before in a resource-constrained startup. Add the Databricks certification, and I think I'm well-positioned."

**Note:** Only use the 10-year framing if James brings it up. Don't volunteer a weakness that might not exist in his mind.

### "What's your visa situation?"

> "I'm on a Zoekjaar (Orientation Year) visa, valid until November 2026. To continue working, I need to transition to a Kennismigrant (Highly Skilled Migrant) permit. The process is straightforward if the employer is an erkend referent — is Source.ag a recognized sponsor? The salary threshold for the reduced rate is €3,122/month."

### "Tell me about a time you simplified a complex system."

> **(STAR — GLP Data Quality Framework)**
> **S:** At GLP, as the startup grew, the data pipelines became a tangle of ad-hoc scripts with no validation.
> **T:** I needed to make the system reliable enough for automated credit decisions — bad data could mean lending to the wrong people.
> **A:** I designed a schema validation framework with integrity checks at every stage — ingestion, transformation, output. I implemented a quarantine pattern where malformed records were isolated rather than silently corrupting downstream aggregates.
> **R:** The system processed millions of records reliably. When I left, the junior analyst I mentored could maintain and extend it independently. The pattern I used at GLP is the same quarantine-and-replay pattern I implemented in my Financial Data Lakehouse project.

### "How do you approach making decisions with incomplete information?"

> "In my thesis research, I ran 150 training experiments across 5 uncertainty quantification methods on SLURM HPC clusters. The whole point of the research was literally about dealing with uncertainty — quantifying what you don't know. In practice at GLP, I was the only data person — there was no one to ask. I had to make architecture decisions, choose frameworks, and ship. My approach: make the best decision you can with available information, design for reversibility, and iterate. Don't let perfect be the enemy of good."

---

## Questions to Ask James (Pick 2-3)

### About the Team & Architecture
1. "What does the data platform look like today? Is it one big Databricks workspace or multiple? How do you split between Golang services and Python data pipelines?"
2. "What's the biggest technical pain point right now — where would a new Data Engineer have the most impact in the first 3 months?"
3. "I understand I'd be the first dedicated Data Engineer on the team — how is data engineering work currently handled? By the software engineers? The data science team?"

### About Culture & Working Style
4. "How do you balance autonomy with alignment in a fast-growing team? How does decision-making work when there's disagreement?"
5. "You've been at Source.ag since 2023 and were recently promoted to Engineering Manager — what's kept you here? What surprised you about the company?"

### About the Process
6. "What does the rest of the interview process look like after this round?"

**Recommended picks:** #2 (shows initiative), #3 (demonstrates research + confirms your unique value), #5 (personal connection with James)

---

## Engineering Team Composition (Intelligence)

> **Source:** The Org, LinkedIn, personal websites

### Key People You Might Meet

| Name | Title | Why They Matter |
|------|-------|----------------|
| **James Godlonton** | Engineering Manager (your interviewer) | Hiring manager, MSc AI Utrecht, thesis on CCTV anomaly detection |
| **Sven van Dam** | Staff Engineer | MSc Econometrics UvA, leads SW eng team. Likely 2nd interviewer. |
| **Vadim Galaktionov** | Lead Software Engineer | **Ex-ASML Data Engineer**. Most data-eng-relevant person on team. Likely 2nd interviewer. |
| **Federico Ragona** | Lead Engineer | Go/Python/Scala polyglot. Joined Jan 2024, shipped critical backend service in 3 months. |
| **Cedric Canovas** | VP of Data Science | Ex-BCG GAMMA, Columbia MSc OR. Your data eng would serve his DS team. |
| **Magnus Hilding** | CTO | Ex-VP Eng at Ghost Autonomy/Sony Mobile. Joined Jan 2025 from Silicon Valley. Final round interviewer. |
| **David Casper** | Software Engineer | Also from UCT (James's alma mater). South African connection in team. |

### Critical Insight: No Current Data Engineer
There is **no dedicated Data Engineer** on the team. This is a brand new role. Data engineering work is currently handled by software engineers and data scientists ad-hoc. **This means you'd be building the data engineering function from scratch** — exactly like your GLP experience.

---

## James's Thesis — Interview Implications

**Title:** "Increased Interpretability and Performance in CCTV Anomaly Detection" (Utrecht, Nov 2020)
**Supervisor:** Prof. Albert Ali Salah (Social and Affective Computing)

### His Approach
- Combined specialized classifiers instead of one monolithic model
- Scene-based grouping for context-specific detection
- Semantic splitting by anomaly type (fire vs. traffic)
- Critiqued existing evaluation benchmarks as insufficient

### What This Tells You About His Thinking
1. **Modular decomposition** — he breaks complex problems into specialized sub-problems → when discussing your work, show you think in terms of layers/modules, not monoliths
2. **Evaluation rigor** — he literally critiqued evaluation methods → be ready to discuss how you measure pipeline success (SLAs, data freshness, quality metrics)
3. **Interpretability** — he values systems that can explain their decisions → when describing your architecture choices, explain the WHY clearly
4. **Practical impact** — his thesis was about real-world CCTV deployment → frame everything in terms of production impact, not academic metrics

---

## Round 2 Take-Home Preview

> **CRITICAL INTEL:** Source.ag's GitHub has public assignment repos!

The Data Engineering assignment is: **Greenhouse Sensor Data Pipeline**
- Python ETL/ELT, ~4 hours
- JSON sensor data → Data quality → Aggregations → Dimensional modeling
- See `08_take_home_prep.md` for full details and preparation strategy

**This maps almost perfectly to your Financial Data Lakehouse project.**

---

| Concept | 30-Second Explanation |
|---------|----------------------|
| **CEA** | Controlled Environment Agriculture — growing in greenhouses/vertical farms vs open field |
| **Climate control** | Temperature, humidity, CO2, light all controlled — generates massive sensor data |
| **Growing cycle** | Tomatoes: ~4-5 months seed to first harvest, then continuous for 10-11 months |
| **Harvest forecasting** | Predicting when and how much fruit will be ready — critical for logistics and sales |
| **Irrigation** | Water + dissolved nutrients delivered to roots — timing and dosage affect yield and quality |
| **Plant balance** | Vegetative (leaf growth) vs generative (fruit production) — growers steer this daily |
| **Stem density** | How many plant stems per m² — trade-off between individual fruit size and total yield |
| **Priva** | Major greenhouse automation hardware company — Source.ag partner (software on top of Priva hardware) |

---

## Technical Quick Review

| Topic | 30-Second Answer (if asked) |
|-------|---------------------------|
| **Delta Lake** | ACID transactions on data lakes. Schema evolution, time travel, merge/upsert on Parquet. Enables reliable ETL at scale. |
| **Medallion Architecture** | Bronze (raw) → Silver (cleaned/validated) → Gold (business aggregates). Each layer adds quality. |
| **TimescaleDB** | PostgreSQL extension for time-series. Automatic partitioning by time. Perfect for sensor data. |
| **gRPC** | Google's RPC framework using Protocol Buffers. Strongly typed, fast, good for microservice communication. |
| **EventBridge** | AWS serverless event bus. Decouples services. Great for event-driven data pipelines. |
| **ECS** | AWS container orchestration (like K8s but simpler). Runs Docker containers. |
| **Structured Streaming** | Spark's stream processing. Micro-batch or continuous. Checkpointing for exactly-once. |
| **Data quality at scale** | Great Expectations, schema validation, quarantine patterns, data contracts between services. |
