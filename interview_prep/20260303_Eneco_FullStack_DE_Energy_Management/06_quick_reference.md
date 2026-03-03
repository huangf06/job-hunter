# Eneco Screening Call — Quick Reference

**Date:** 2026-03-03 11:00 CET (30 min)
**Format:** Microsoft Teams screening call
**Interviewer:** Venetia de Wit (Senior Recruiter, Tech)
**Role:** Full-Stack Data Engineer — Energy Management
**Location:** Rotterdam (Hybrid: 40% office / 40% home / 20% flex)
**Salary:** €83,000 – €117,000 + 8% holiday allowance + FlexBudget + profit sharing

---

## Teams Meeting Link
https://teams.microsoft.com/meet/39389948647491?p=hjaiegnN5UYfSh85Wg
Meeting ID: 393 899 486 474 91 | Passcode: BQ9yE7ju

---

## The Role in 30 Seconds

Build and own the **cloud-based data platform** powering Eneco's IoT consumer products:
- **Toon** smart thermostat (100K+ users, ~10% energy reduction)
- **Energy Insight** dashboards (consumption patterns, cost calc)
- **Smart Charging** (EV load shifting to off-peak)

Team: Data Engineers + ML Engineers + Data Scientists + Data Analysts
Autonomy: High — you lead technical decisions end-to-end

---

## Must-Have Skills (from JD) → My Match

| Requirement | My Evidence |
|------------|-------------|
| REST API development (Spring/FastAPI) | FastAPI (voice cloning project), API design experience |
| Streaming data ingestion & processing | Spark Structured Streaming (Lakehouse project), real-time market data (Baiquan) |
| MPP data platforms (Spark) | PySpark ETL (GLP), Databricks Lakehouse (personal project) |
| Databricks + Unity Catalog | Databricks Certified Data Engineer Professional, Lakehouse project uses Unity Catalog |
| Programming: Java, Scala, Python | Python (primary, 6+ years), Scala/Java (learning, transferable from Spark) |
| Software engineering best practices | CI/CD, code reviews, version control, testing — all daily practices |
| DevOps/SRE interest | Docker, CI/CD pipelines, monitoring experience |

## Nice-to-Have → My Match

| Nice-to-Have | My Evidence |
|-------------|-------------|
| High volume time series data | Market data pipelines (3,000+ securities daily at Baiquan) |
| Data modeling & architecture | Medallion architecture (Lakehouse), dimensional modeling (GLP) |
| Kubernetes + monitoring (Grafana) | Exposure, not deep production experience — honest gap |
| Cloud provider (AWS) + IaC | AWS (Lakehouse project), basic IaC |
| NoSQL (DynamoDB) + RDBMS (Postgres) | PostgreSQL, SQLite, various DB experience |
| SQL + dbt + Snowflake | Strong SQL, no dbt/Snowflake — can learn quickly |
| MLOps / data science | ML lifecycle (GLP credit scoring), thesis (UQ for neural networks) |

---

## About Eneco — Key Facts

- **Dutch energy company**, HQ Rotterdam, ~4,100 employees, ~€11.8B revenue
- **Owned by Mitsubishi Corp (80%) + Chubu Electric (20%)** since 2020 (€4.1B acquisition)
- **One Planet Plan**: Climate neutral by 2035 (Scope 1+2+3), SBTi validated
- **New CEO**: Martijn Hagens started March 1, 2026
- **Recent restructuring**: 350 FTE reduction announced Dec 2024 (cost pressures) — via attrition, not layoffs
- **Strategic pivot**: Divesting district heating (Oct 2025) → focusing on digital/IoT/renewables
- **Eneco Ventures**: CVC arm investing in cleantech startups (suena, Ostrom, Gradyent)

### Recent Developments
- **Wallbox partnership** (Jan 2026): Commercial EV charging in Benelux
- **Grid congestion crisis**: Dutch national issue — Eneco working on load shifting solutions
- **Battery storage**: 50 MW/200 MWh BESS facility operational
- **Gulf Gas + Power acquisition** (2025)

### Tech Stack (Energy Management team)
Databricks, Spark (Scala), Unity Catalog, Snowflake, dbt, Airflow, Kafka, Kubernetes, AWS, Azure, Grafana, FastAPI/Spring, Python, SQL

---

## Interviewer: Venetia de Wit

- **Senior Recruiter (Tech)** at Eneco, Team Recruitment Tech
- Known for thorough candidate assessment, quality-focused
- Empathetic, relationship-builder — cares about career goals
- Prompt and efficient communicator

**What she'll likely ask:**
1. Walk me through your background
2. Why Eneco / why this role?
3. Visa/work permit status
4. Salary expectations
5. Availability / notice period
6. What's your experience with [specific tech]?
7. What are you looking for in your next role?

---

## My Pitch (2 minutes)

"I'm a Data Engineer with 6 years of experience building data pipelines and analytics platforms. I started at Ele.me — China's largest food delivery platform acquired by Alibaba — doing user segmentation on Hadoop at massive scale. Then I moved to Baiquan Investment as a Quantitative Developer, where I built real-time market data pipelines processing 3,000+ securities daily — this is very relevant to your time-series IoT data challenge.

At GLP Technology, I was the first data hire and grew into a team lead role, building credit scoring infrastructure end-to-end: data ingestion, ETL with PySpark, ML model deployment, and monitoring dashboards.

I then moved to the Netherlands for my Master's in AI at VU Amsterdam, graduated with an 8.2 GPA, and got my Databricks Certified Data Engineer Professional certification. My thesis was on uncertainty quantification for neural networks — 150 training runs on HPC clusters.

Currently I'm building a Financial Data Lakehouse on Databricks with medallion architecture, real-time streaming, and Unity Catalog — which maps directly to what you're building for IoT data at Eneco.

What excites me about this role is the combination of real-world impact — helping millions of customers use energy more sustainably — with a modern tech stack and high autonomy. The IoT time-series challenge is technically fascinating, and I care about the energy transition."

---

## Why Eneco? (Specific Reasons)

1. **Real-world impact at scale**: IoT products directly help millions use energy sustainably — not just pushing ads or optimizing clicks
2. **Tech stack alignment**: Databricks + Spark + streaming is exactly what I've been building expertise in
3. **Energy transition mission**: One Planet Plan is ambitious and genuine — climate neutral by 2035 including Scope 3
4. **Grid congestion problem**: The Dutch grid crisis makes smart charging/load shifting genuinely important engineering work, not just a feature
5. **Autonomy**: "Own end-to-end technical decisions" — I thrive in high-autonomy environments (was first data hire at GLP, built everything from scratch)
6. **Personal**: My very first job was at Henan Energy Chemical Industry Group — energy has been part of my career from day one

---

## Honest Gaps & How to Frame Them

| Gap | Frame It As |
|-----|-------------|
| No Scala production experience | "Python primary, but I work daily with Spark/PySpark. Scala is a natural extension — I'm actively learning it. The conceptual model (functional programming, distributed compute) is the same." |
| No Kubernetes production | "I use Docker extensively and understand container orchestration concepts. K8s is the logical next step and I'm keen to grow into it." |
| No Java | "My background is Python-first but I've worked with strongly-typed languages and large codebases. Java syntax isn't a barrier." |
| No IoT/energy domain | "My time-series experience from financial markets transfers directly — high-frequency, high-volume, real-time processing. The domain is new but the engineering challenges are familiar." |
| No dbt/Snowflake | "I use Databricks + Delta Lake for similar patterns. dbt is a tool I can pick up quickly." |

---

## Questions I Should Ask

### About the Role
1. "What does the team look like right now? How many engineers, and what's the split between Data Engineers and ML Engineers?"
2. "What's the current state of the IoT data platform? Are you building from scratch or evolving an existing system?"
3. "How much of the work is Scala vs Python vs other languages day-to-day?"
4. "What does 'full-stack' mean in practice here — does it include frontend, or is it backend + infrastructure + data?"

### About the Process
5. "What does the interview process look like after this call? How many rounds?"
6. "Is there a technical assessment or take-home assignment?"
7. "What's the timeline for filling this position?"

### About the Company
8. "How has the recent reorganization affected the Energy Management team specifically?"
9. "I saw the new CEO started March 1st — is there any shift in digital/data strategy expected?"

### About Growth
10. "What does career growth look like for a Data Engineer at Eneco? Is there a path to principal/staff level?"

---

## Visa / Logistics

- **Current visa**: Orientation Year (Zoekjaar), valid until November 2026
- **Need**: Highly Skilled Migrant (Kennismigrant) sponsorship
- **Eneco IS a recognized sponsor** (erkend referent) — this should not be an issue
- **Salary threshold**: Reduced rate €3,122/month for zoekjaar→kennismigrant transition
- **This role's salary (€83K-117K) far exceeds the threshold** — no issue
- **Availability**: Can start relatively quickly (no current employer notice period)

---

## Salary Strategy

- Range: €83,000 – €117,000
- **My target**: €95,000-105,000 (mid-to-upper range)
- **If asked early**: "I've seen the range on the posting and it aligns with my expectations. I'd love to understand more about the role and total compensation package before committing to a specific number."
- **If pressed**: "Based on my experience level and the market, I'd be comfortable in the €95,000-105,000 range, but I'm flexible depending on the full package."
- Total comp includes: 8% holiday allowance, FlexBudget, bonus/profit sharing → effective total is ~10-15% above base

---

## Red Flags to Watch For

- Reorganization impact on team stability
- Whether the 350 FTE cut affected this team
- "We need someone who can also do X, Y, Z" (scope creep beyond data engineering)
- Very short timeline pressure (might indicate someone just left)

---

## Final Checklist Before the Call

- [ ] Teams app installed and tested
- [ ] Camera + mic working
- [ ] Quiet environment
- [ ] This cheat sheet open on second screen
- [ ] Water nearby
- [ ] LinkedIn profile of Venetia open (for rapport)
- [ ] Smile and be genuine
