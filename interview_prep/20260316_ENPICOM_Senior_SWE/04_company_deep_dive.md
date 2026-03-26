# ENPICOM Company Deep Dive

## 1. Company Overview

**ENPICOM B.V.** is a bioinformatics software engineering company in 's-Hertogenbosch, Netherlands. Founded 2015 as a VU Amsterdam spin-out. Builds cloud-based SaaS tools to help scientists decode the immune system -- specifically managing, analyzing, and interpreting immune repertoire sequencing data (T-cell & B-cell receptors).

**Mission**: Empowering scientists, accelerating R&D in biologics discovery.

## 2. Core Product: IGX Platform (now "ENPICOM Platform")

Cloud-based SaaS for immune repertoire data:
- **No programming required** -- scientists focus on research, not code
- **Key Modules**:
  - **Antibody Discovery Module (ADM)** -- launched early 2021, rapid market uptake. Selects genetic sequences matching desired therapeutic characteristics from databases of millions
  - **Liability Prediction** -- integrates Oxford's SAbPred for structural antibody analysis, 3D modeling (not just sequence-level)
  - **Display Data Analysis** -- analyzes antibody panning data, tracks clones across rounds
  - **Enrichment Analysis** -- identifies highly enriched candidates
- **Performance**: 1.55M+ reads/min; petabyte-scale; queries across 100M+ sequences in seconds; scales 10M-500M clones
- **IGX Platform 7.0**: 1 billion reads in <6.5 hours, comprehensive API, ML model training/deployment built-in
- **ISO/IEC 27001:2022** certified
- **87% NPS** (user satisfaction)

## 3. Domain Context: What is Immunogenomics?

Immunogenomics studies the genetic basis of the immune system. Key concepts:
- **Immune repertoire**: The full collection of T-cell and B-cell receptors in an organism
- **NGS (Next-Gen Sequencing)**: Technology that reads DNA sequences at massive scale
- **Rep-Seq (Repertoire Sequencing)**: Sequencing immune receptors to understand immune responses
- **Antibody discovery**: Finding antibodies that bind specific targets -- critical for drug development
- **Why it matters**: Enables development of immunotherapies, vaccines, and personalized medicine

ENPICOM makes this data usable for lab scientists who don't code.

## 4. Founding & Leadership Timeline

| Period | Event |
|--------|-------|
| 2015 | **Nicola Bonzanni** & **Alvise Trevisan** start at VU Amsterdam doing bespoke bioinformatics consulting |
| 2017 | Incorporated as B.V. when **Jos Lunenberg** (MBA, ex-Genalice COO) joins as CEO → transition from services to product |
| 2017 | Begin building IGX Platform |
| 2019 | Series A: EUR 1.2M (BOM Brabant Ventures, Nextgen Ventures, Arches Capital) |
| 2020 | Series A Extension: EUR 1.1M |
| 2020 | MiLaboratories partnership (MiXCR integration) |
| 2021 | Antibody Discovery Module launch → rapid market uptake |
| 2022 | Series B (undisclosed, led by BOP Capital) |
| ~2023 | Jos Lunenberg steps down as CEO → **Paul van der Velde** takes over |
| 2023 | Extended financing from existing investors |
| 2024 | Growth capital from BOP Impact Ventures + BOM |
| Oct 2024 | **Nicola Bonzanni** becomes CEO (from CPO) |

**Current Leadership:**
| Name | Title | Background |
|------|-------|------------|
| Nicola Bonzanni | Founder & CEO | PhD VU Amsterdam, postdoc NKI-AVL, intern Microsoft Research Cambridge. Python, Java, comp bio |
| Jorrit Posthuma | CTO | MSc Medical Informatics UvA. Node.js, TypeScript, PostgreSQL |
| Pim Fuchs | Chief AI Officer | Bioinformatics background, hackathon winner |
| Piotr van Rijssel | Director of Business Dev | Commercial leadership |
| Dr. Henk-Jan van den Ham | Head of Research | PhD Theoretical Immunology & Bioinformatics |

## 5. Customers & Partners

**Named customers:**
- **Zai Lab** (NASDAQ: ZLAB) -- Chinese/US biopharma, IGX Platform subscription
- **Genovac** -- CRO/CMO for antibody discovery
- **Kite Pharma Europe** -- original inspiration for ENPICOM (T-cell target discovery)
- **Illumina** -- mentioned as partner/customer
- **LifeArc** -- mentioned in customer context

**Claims**: "Multiple Top 25 big pharmaceutical companies" (names undisclosed), "over 50 industry leaders" collaborated on ADM development.

**Technology Partners:**
- **MiLaboratories** -- MiXCR immune profiling software integrated into IGX
- **Oxford's SAbPred** -- structural antibody prediction

## 6. Competitors

- **Adaptive Biotechnologies** -- immunosequencing pioneer (NASDAQ: ADPT)
- **10x Genomics** -- single-cell sequencing
- **Geneious** / **DNASTAR** -- bioinformatics suites
- **In-house teams** at big pharma

ENPICOM's differentiator: cloud-native SaaS, no-code interface for lab scientists, end-to-end workflow.

## 7. Culture & Team

- **~30 people**, 84% in R&D
- No layers of management
- Won **Microsoft Genomics Hackathon 2018** (Jorrit + Jan Blom + Pim Fuchs)
- Engineering values: clean code (clean-code-javascript fork), pragmatism, plain SQL (no ORM)
- **Preferred hiring**: personally written applications, not AI-generated
- Located in 's-Hertogenbosch, hybrid 2 days/week

## 8. Tech Stack (Confirmed)

| Layer | Technology |
|-------|-----------|
| Primary Language | **TypeScript** |
| Backend | **Node.js**, **PostgreSQL** (plain SQL, no ORM) |
| Frontend | **React** |
| Data Warehouse | **Amazon Redshift** (MPP architecture) |
| Cloud | **AWS** (migrated from GCP) |
| Container Orchestration | **Kubernetes (EKS)** |
| Infra | Docker, GitHub Actions |
| Logging/Monitoring | Pino + Sentry |
| Project Management | JIRA |
| Bioinformatics | Python |
| Storage | AWS S3 |
| Security | ISO 27001, SSO, 2FA |

## 9. GCP → AWS Migration (Engineering Blog)

- **Why**: Customer demand for AWS (security/compliance) + AWS Athena had no GCP equivalent
- **How**: K8s cluster portability (GKE → EKS) was the hero
- **Opinion**: GKE is "batteries included"; EKS is "sold without batteries" -- more painful to set up
- **Result**: Called it a "net positive" despite EKS friction

## 10. VU Amsterdam Connection

- CEO Nicola Bonzanni: PhD from VU Amsterdam (2007-2011)
- ENPICOM hired 1 person from VU Amsterdam
- Fei Huang: MSc AI from VU Amsterdam (2025)
- This is a genuine alumni connection worth mentioning naturally
