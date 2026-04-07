# Company Deep Dive — Aon plc

---

## Company at a Glance

| Dimension | Detail |
|-----------|--------|
| Full Name | Aon plc |
| HQ | Dublin, Ireland (incorporated 1979) |
| Type | British-American professional services |
| Revenue | **$17.2B (FY2025)** — 9% YoY growth, 6% organic |
| Employees | **~60,000** in 120 countries (up 20% after NFP acquisition) |
| Market Position | #2 insurance broker globally |
| NYSE | AON |
| CEO | Greg Case |

## Business Divisions

### Risk Capital (67% of 2024 revenue)
- Insurance brokerage
- Reinsurance
- Risk management consulting
- Cyber risk solutions

### Human Capital (33% of 2024 revenue)
- Health insurance solutions
- Retirement/pension plans
- Talent advisory
- Outsourcing services

## Netherlands Operations

| Dimension | Detail |
|-----------|--------|
| Entity | Aon Nederland C.V. |
| HQ | Admiraliteitskade 62, 3063 ED Rotterdam |
| NL Employees | ~1,900 across 10 offices |
| Registration | Chamber of Commerce Rotterdam #24061634 |
| Licensed | AFM Wft register #12009529 (broker + adviser) |
| Marine | ~60 staff in Rotterdam for marine insurance |
| Phone | +31 (0)10 - 448 8200 |

Rotterdam is Aon's NL headquarters — not just a branch office. This is where strategic decisions for NL operations are made.

## The Data Intelligence Team

The Lead Data Engineer role sits in the **Data Intelligence Team**, which focuses on:
- Customer interaction and digitalization
- "Hands-on, entrepreneurial spirit" (their words)
- Warehouse architecture consolidation
- GenAI, NLP, and ML applications
- Data governance and compliance

This is NOT a pure infrastructure team — they explicitly mention innovation with GenAI/NLP/ML, which is where your MSc AI background becomes a differentiator.

## Strategic Context: Accelerating Aon United (AAU)

Aon is executing a **3-year transformation** called the **Accelerating Aon United (AAU) Program** (initiated Q3 2023):
1. Address complex risk through Risk Capital + Human Capital integration
2. Deliver next-generation client experiences
3. Scale AI through **Aon Business Services (ABS)** — the technology backbone

**$1 billion committed to digital transformation** with "AI and real-time data at the core."

### NFP Acquisition (April 2024, $13B)
- 7,700 employees, middle-market risk/benefits/wealth
- Created massive **data integration challenges** (fragmented systems, siloed data)
- Sold wealth management arm to Madison Dearborn Partners for ~$2.7B (Sep 2025)

### AI Products Already Launched
- **Aon Broker Copilot** (June 2025): Patent-pending LLM + predictive analytics for insurance placement
- **Claims Copilot** (Nov 2025): AI-enabled claims processing
- **AonGPT**: Internal AI platform on Azure (Azure AI Foundry + Container Apps + Cosmos DB)
  - **62,000+ users onboarded, 31,000 monthly active, 6.4M+ messages**
  - Policy checker replaces 40 hours of manual document comparison
  - Expanding into domain-specific agents (HR, finance, TA)
- These products demonstrate Aon's commitment to AI — the data platform you'd build feeds these

### Key Technology Leaders
- **Abdul Razack** — Chief Technology and Product Officer (**ex-Google VP**)
- **Sudipto Dasgupta** — Global Head of Data and AI Platforms (**ex-Google Director**)
- **Magnus Roe** — Global Chief Data and Analytics Officer (appointed Nov 2024, Singapore)
- **Boby Azarbod** — Data Services Lead, Aon Reinsurance Solutions
- **Amit Gawali** — Head of Engineering (led AonGPT build)

### Related Open Roles in Rotterdam (Signals: Greenfield Build)
| Role | URL |
|------|-----|
| **Lead Data Engineer** (your role) | jobs.aon.com/jobs/95516 |
| **Data Architect** | jobs.aon.nl/jobs/71820 |
| **Senior Consultant Data, AI & Analytics** | jobs.aon.com/jobs/95050 |

Hiring Lead DE + Data Architect + Senior Consultant simultaneously = **building/rebuilding the data platform from scratch**, not filling one vacancy.

## Technology Landscape

### Current State (Migration Source)
- **Oracle** databases (legacy)
- **Azure Synapse** (intermediate)
- **AWS Databricks** (some workloads)

### Target State (Migration Destination)
- **Azure Databricks** (unified platform)
- Unity Catalog for governance
- Delta Lake for storage
- **Delta Sharing** for cross-team data access (already used by Reinsurance team!)
- DABs (Databricks Asset Bundles) for deployment
- Genie for natural language queries
- Workflows for orchestration
- Azure DevOps for CI/CD
- **Reltio** for cloud-native Master Data Management (50%+ data already migrated)

### Data Architecture Pattern
Aon Reinsurance Solutions already uses **Databricks Delta Sharing across decentralized lakehouses** — a **data mesh-inspired** approach. Models developed in Databricks on AWS, consumed in Azure Databricks via Delta Sharing. The Rotterdam role is likely part of extending this pattern to NL operations.

### Why This Migration Matters
Aon is consolidating from 3 separate data platforms into 1. This is a massive, multi-year effort touching:
- Data modeling (need to standardize on Data Vault or Dimensional)
- Governance (Unity Catalog as single source of truth)
- Cost optimization (eliminate redundant platforms)
- Skill consolidation (one platform = one skillset to maintain)
- **NFP integration** — merging acquired company's data systems

## Aon Nederland Leadership

| Name | Title | Notes |
|------|-------|-------|
| Leonique van Houwelingen | CEO / Country Leader | — |
| Philip Alliet | CEO Benelux (since Sep 2024) | — |
| **Marnix Zwartbol** | **CTO** (since Jun 2023) | Ex-BNY Mellon COO |
| **Peter de Bruin** | **CIO**, NL & EMEA Infra | 30yr Aon veteran |
| **Hoi Wah Yip** | **MD, Data & Strategy** | Ex-CFO, likely hiring manager |
| Gerben Pasman | CFO | — |
| Jan Steven Kelder / Arjan Bol | CCO | — |

### Data Intelligence Team Structure
- Reports up through **Hoi Wah Yip** (MD Data & Strategy), NOT through CIO
- Previous leader: **Leen Molendijk** (Ad Interim MD, Data Intelligence, 2010-2021) — now gone
- Team appears small/early-stage — no IC-level members found publicly
- **AGRC** (55 specialists) is a separate data/analytics team within Risk Consulting

### EMEA Data Layer
- **Matthew McCann** — Head of Data Analytics, EMEA (possible dotted-line to NL team)
- **Magnus Roe** — Global CDAO (137 reports globally)

## Competitors

| Company | Revenue | Position |
|---------|---------|----------|
| Marsh McLennan | $23.6B | #1 insurance broker |
| **Aon** | **$15.7B** | **#2 insurance broker** |
| Willis Towers Watson | $10.2B | #3 (Aon's 2021 merger attempt failed) |
| Gallagher | $11.3B | Growing fast |

### Failed WTW Merger (2021)
- Aon attempted to acquire Willis Towers Watson for $30B
- DOJ blocked the deal on antitrust grounds
- This is a sensitive topic — don't bring it up unprompted

## Glassdoor Summary

| Metric | Value |
|--------|-------|
| Overall Rating | 3.9/5 |
| Interview Positivity | 72.7% |
| Interview Difficulty | 2.88/5 (moderate) |
| Average Hiring Process | ~29 days |
| Software Engineer Rating | 3.7/5 (below company average) |

### Pros (Common Themes)
- Work-life balance
- International exposure
- Good benefits and pension
- Hybrid work flexibility
- Professional development opportunities

### Cons (Common Themes)
- Bureaucratic processes (large org)
- Below-market tech salaries
- Slow decision-making
- Limited tech innovation culture (insurance company, not tech company)

## Industry Context: Why Data Engineering Matters for Aon

Insurance is undergoing a data revolution:
1. **Actuarial → ML**: Traditional actuarial models being supplemented/replaced by ML
2. **Claims automation**: NLP to process claims documents
3. **Risk assessment**: Real-time data pipelines for dynamic risk pricing
4. **RegTech**: Compliance reporting requires governed, auditable data
5. **Customer 360**: Unified customer view across Risk Capital + Human Capital divisions

Aon's data consolidation project is not just technical debt cleanup — it's enabling the company to compete in an increasingly data-driven insurance market.

## Interview Process Intel (from InterviewQuery)

Typical Aon Data Engineer interview has **4 stages**:
1. HR screening (30 min) — **THIS IS YOUR ROUND 1 WITH CEES**
2. Hiring manager discussion
3. Technical interview (SQL + Python/Scala, data architecture, ETL)
4. Onsite/virtual with multiple 1:1s

**SQL is the most heavily tested topic** (6 questions typical). Technologies tested: Databricks, Spark, S3, Snowflake, Hadoop.

Average process duration: ~29 days. Difficulty: 2.9/5 (moderate).

## GitHub Presence

- **AonCyberLabs** — R&D for Cyber Solutions (repos now private, 139 followers)
- **GDSSecurity** — 36 public repos, security testing tools
- **No data engineering repos found** — all data work is proprietary/internal
- No take-home assignment found on public GitHub (unlike Source.ag)

## Key Numbers to Remember for the Interview
- **$17.2B revenue** (FY2025)
- **~60,000 employees** (after NFP acquisition)
- 120 countries, 426 offices
- #2 insurance broker globally
- **$1B digital transformation** commitment
- **Aon Broker Copilot** — their flagship AI product
- 1,900 NL employees across 10 offices
- Rotterdam = NL headquarters
- **Delta Sharing** already used by Reinsurance team
