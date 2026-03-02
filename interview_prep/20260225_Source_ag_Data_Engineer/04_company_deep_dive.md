# Company Deep Dive — Source.ag

## Company Overview

| Detail | Value |
|--------|-------|
| **Full Name** | Source.ag B.V. |
| **Founded** | November 2020 |
| **Founders** | Rien Kamman (CEO, ex-BCG/McKinsey, TU Delft + Columbia MBA), Ernst van Bruggen (CPO, similar consulting background) |
| **CTO** | Magnus Hilding (joined Jan 2025, ex-VP Eng at Silo/Ghost Autonomy/Sony Mobile, MSc EE Lund + ETH Zurich) |
| **HQ** | Johan Huizingalaan 763a, Amsterdam |
| **Employees** | ~70+ (Product Dev team = 16) |
| **Total Funding** | >$60M |
| **Latest Round** | Series B, $17.5M (Nov 2025) |
| **Lead Investor** | Astanor Ventures |
| **Strategic Investors** | Enza Zaden (seed breeder), Harvest House (grower cooperative) |
| **Mission** | Empower growers to sustainably feed the world — aspires to be NL's first AgTech unicorn |

## Founding Story — The Narrative You Should Know

Rien Kamman and Ernst van Bruggen first met during **Mechanical Engineering studies at TU Delft**, then reconnected at **Columbia Business School**. Both went on to lead data science teams at top consulting firms — Rien as Associate Director of Data Science at **BCG GAMMA**, Ernst as Engagement Manager at **McKinsey**. They were building custom AI software for the world's largest corporations.

But having grown up in the Netherlands — the world's **second-largest agricultural exporter** from a tiny country — they felt AI could do more. Dutch greenhouses achieve **15x higher yields** with **20x less water** and zero agricultural runoff, weather-independent. The problem: you can't copy-paste decades of Dutch greenhouse expertise globally. **AI could be the vehicle to scale that knowledge.**

CEO quote: *"Food chain innovation requires AI companies to partner closely with industry."*

He calls the product a **"copilot for growers"** — AI doesn't replace the grower, it amplifies them.

---

## Interview Process (from careers page)

| Round | Format | What They Evaluate |
|-------|--------|-------------------|
| **1. Personal introductory** | Video call, 30 min ← **THIS ONE** | Culture fit, motivation, background |
| **2. Technical** | Based on take-home assignment | Technical skills, problem-solving |
| **3. Final discussion** | With senior staff | Overall fit, seniority assessment |

Each interview has 2+ interviewers including a potential team member with technical expertise.

---

## Key Leadership

| Name | Role | Background |
|------|------|------------|
| **Rien Kamman** | CEO & Co-Founder | TU Delft + Columbia MBA, ex-BCG GAMMA (Associate Director Data Science) |
| **Ernst van Bruggen** | CPO & Co-Founder | TU Delft + Columbia MBA, ex-McKinsey (Engagement Manager) |
| **Magnus Hilding** | CTO (Jan 2025) | Lund + ETH Zurich, ex-VP Eng at Silo, Ghost Autonomy (self-driving AI), Sony Mobile |
| **Tomas Geurts** | GM North America | Early employee, now leads Chicago office (opened Oct 2024) |

---

## What They Do

Source.ag builds **AI software for greenhouse agriculture**. Their platform helps greenhouse growers make better decisions about growing crops — from optimizing yield to automating irrigation to predicting harvests.

**Key insight for interview:** This is NOT a typical SaaS company. They deal with **messy, biological systems** where decisions have real physical consequences. A wrong irrigation decision affects actual crops. Data quality literally feeds people.

### Scale of Impact
- **300+** greenhouses connected across **18 countries**
- **2,500 hectares** of greenhouse coverage
- **40 million people** fed daily from produce grown using their system
- Growing rapidly post-Series B

## Product Suite

| Product | What It Does | Data Relevance |
|---------|-------------|----------------|
| **Source Workspace** | Centralized real-time data dashboard | Core data platform — ingests sensor data from greenhouses |
| **Harvest Forecast** | 8-week yield predictions, refreshed daily | ML predictions on biological/climate data |
| **Cultivation Management** | Simulate crop strategies before implementing | Strategy simulation engine |
| **Irrigation Control** | Automated water + nutrient delivery | IoT control systems with real-time data |
| **Source Plant App** | Mobile plant data collection (tomatoes, peppers, cucumbers) | Data collection at the edge |
| **Source Cloud Modules** | Connect to tools like Power BI | Data export/integration layer |
| **Source APIs** | Real-time data exchange with greenhouse sensors | API layer for data ingestion |

## Funding Timeline

| Date | Event | Amount |
|------|-------|--------|
| Nov 2020 | Founded | — |
| Jul 2021 | First greenhouse connected | — |
| Dec 2021 | First international grower | — |
| Mar 2022 | Seed round | $10M |
| Aug 2022 | Source Workspace launched | — |
| Feb 2023 | Series A | $27M |
| Nov 2023 | 1,400 ha / 200 greenhouses | — |
| Nov 2025 | Series B | $17.5M |
| Feb 2026 | Mexico expansion (Alberto Carbajal Rodriguez) | — |

**Total: >$60M raised since 2020**

## Tech Stack (from JD + GitHub + HackerNews)

```
Backend:        Golang, Python (HN 2021: "Python, TypeScript and a bit of Golang")
Frontend:       TypeScript, React, Next.js, React Native (mobile app)
Communication:  gRPC, GraphQL, REST, AWS EventBridge/SNS/SQS
Data:           Databricks, Delta Lake, S3, dbt, Dagster, PostgreSQL (RDS), TimescaleDB, MongoDB Atlas
Infrastructure: AWS (ECS, Lambda), Docker, Vercel
Monitoring:     Datadog
Dev tools:      Linear (issue tracking, migrated from YouTrack), AWS CodeArtifact (private Python packages), Cursor + OpenAI Codex (AI-assisted dev)
```

### What the data layer likely looks like:
- **Sensor data** flows in real-time from greenhouses → AWS → Databricks/Delta Lake
- **TimescaleDB** for time-series sensor data (temperature, humidity, CO2, light)
- **PostgreSQL** for application/business data
- **MongoDB Atlas** possibly for flexible/unstructured data (plant observations?)
- **Databricks + Delta Lake** for the ML pipeline (Harvest Forecast, Cultivation simulation)
- **S3** for data lake storage
- **EventBridge/SNS/SQS** for event-driven architecture between microservices

## Core Values

1. **All-in for our Growers** — Customer-first, not tech-first
2. **Learn-Adapt-Succeed** — Growth mindset, feedback culture
3. **We Plant Solutions** — Autonomous problem-solving
4. **Strength Through Diversity** — International team
5. **Driven to Deliver** — Results over process

## Competitive Landscape

| Competitor | Focus | Difference |
|-----------|-------|------------|
| **Priva** | Greenhouse automation hardware + software | Source.ag is pure software/AI; Priva is Source's partner, not competitor |
| **LettUs Grow** | Vertical farming automation | Different segment (vertical vs greenhouse) |
| **Hortilux** | Greenhouse lighting | Hardware-focused |
| **Ridder** | Climate control systems | Hardware + basic automation |
| **Blue Radix** | Autonomous greenhouse growing | Closest direct competitor — also AI for greenhouse |

**Source.ag's differentiation:** They combine AI software with deep grower partnerships. CEO quote: "Food chain innovation requires AI companies to partner closely with industry."

## The Greenhouse Industry Context

**Why it matters:**
- Global population growth demands more food production
- Climate change makes outdoor farming less reliable
- Greenhouses provide **Controlled Environment Agriculture (CEA)** — weather-independent
- BUT: Experienced growers are retiring, knowledge is being lost
- Source.ag's AI captures and scales that expertise digitally

**Market size:**
- CEA market valued at **$103 billion** in 2025
- Projected to reach **$175 billion** by 2029 (14.2% CAGR)
- Source Cultivate achieves **90% accuracy** in yield predictions 3-4 weeks out

**Data challenges you should understand:**
- Sensor data is messy (calibration drift, sensor failures, gaps)
- Biological systems are non-linear (plants don't follow neat equations)
- Each greenhouse is different (crop variety, climate zone, grower preferences)
- Real-time decisions matter (irrigation timing, climate adjustments)
- Seasonality creates massive data volume variation

## Marquee Case Study: Harvest House Partnership

**Harvest House** is one of Europe's largest greenhouse vegetable cooperatives — **600 hectares of tomato production**, serving **30 million consumers**. They went from **weekly spreadsheets** to **daily AI-powered forecasts** using Source.ag's Harvest Forecast.

This is your best reference point in the interview. It shows:
- Real enterprise-scale data pipeline challenges
- The value of accurate forecasting (labor savings, better contract prices, less waste)
- Customer trust so deep they became a Series B investor

---

## Glassdoor Reality Check (3.7/5, 54% recommend)

**Positives:** Great colleagues, smart/motivated people, interesting and innovative work, compelling mission, good work-life balance (4.2/5), free lunch

**Negatives:** Some reviews mention post-layoff morale issues (2024), leadership communication concerns, onboarding described as minimal, salary raise difficulties

**Context:** The 3.7 rating is from a small sample (~20 reviews). Negative reviews appear concentrated around 2024 (before Series B and new CTO). The company has since hired Magnus Hilding as CTO and raised $17.5M — suggesting leadership has stabilized.

---

## Sources
- [Source.ag Homepage](https://www.source.ag/)
- [Source.ag About Us](https://www.source.ag/about-us)
- [EU-Startups: Series B announcement](https://www.eu-startups.com/2025/11/dutch-startup-source-ag-raises-e15-2-million-to-scale-ai-software-powering-300-greenhouses-across-18-countries/)
- [Source.ag News: Series B](https://www.source.ag/news/sourceag-raises-175m-for-applied-ai-in-cea-pushing-total-funding-past-60m)
- [Source.ag Careers](https://careers.source.ag)
- [Source.ag Product Tiers](https://www.source.ag/news/source-ag-launches-new-product-tiers-to-accelerate-ai-adoption-in-greenhouse-operations)
