# Sensorfact — Deep Dive

## The Story
Sensorfact was founded in 2016/2017 by **Pieter Broekema** in Utrecht, Netherlands. Broekema holds an MSc in Energy & Environmental Sciences and a BSc in Physics from the University of Groningen. Before Sensorfact, he co-founded Dexter Energy (2014) and worked as an Associate at SparkOptimus (strategy consulting).

The core insight: **industrial SMEs waste enormous amounts of energy but lack the tools and expertise to measure and fix it.** Large enterprises have energy management teams; SMEs don't. Sensorfact's solution: plug-and-play sensors that attach to machines + a smart software platform that uses AI to identify savings and provide actionable advice.

## Leadership Team
| Name | Role | Notes |
|------|------|-------|
| Pieter Broekema | CEO & Founder | MSc Energy/Env Sciences, Univ Groningen |
| Dennis Ramondt | VP of Technology | 7 direct reports, oversees all tech |
| Hans Beukers | COO | |
| Karel Nanninga | Chief Growth Officer | |
| Senan King | Head of Sales | |
| Niels Dijk | VP Operations | |
| Tatenda Kusena | Head of Finance | |

## Products & Services
Sensorfact offers a **full-stack monitoring SaaS** for industrial companies:

1. **Hardware**: Wireless plug-and-play sensors that measure machine-level consumption
2. **Software**: Cloud platform for monitoring and analytics
3. **AI-powered advice**: Algorithms detect energy-saving opportunities and provide customer-specific recommendations

### Product Verticals
- **Energy Management** (core) — electricity consumption monitoring + optimization
- **Utilities**: Gas, compressed air, water, steam monitoring
- **Predictive Maintenance** — ML-powered fault detection
- **Overall Equipment Effectiveness (OEE)** — production efficiency tracking
- **Environmental monitoring** — temperature, humidity

### How It Works (Data Flow — Critical for Interview!)
```
Sensors → Raw data → Kafka (ingestion) → Kafka Streams/Flink (processing)
  → Clickhouse (time-series storage) → Hasura/GraphQL API → Customer platform
  → ML models (fault detection, energy waste) → Actionable advice
```

Batch processing: Prefect + AWS Fargate
On-demand: AWS Lambda
API: GraphQL via Hasura + TypeScript

## Technology Stack (Confirmed)
- **Streaming**: Kafka, Kafka Streams, Flink
- **Storage**: Clickhouse (time-series), DynamoDB (some services)
- **Batch**: Prefect, AWS ECS/Fargate
- **Serverless**: AWS Lambda
- **API**: GraphQL via Hasura + TypeScript
- **Cloud**: AWS (full stack)
- **Languages**: Python (data), TypeScript (API/backend)
- **Infrastructure as Code**: CloudFormation (from Luka's blog posts)

## Data Team
- **Size**: 5+ data engineers (growing)
- **Key People**:
  - **Luka Sturtewagen, PhD** — Principal Data Engineer (promoted within a year). PhD from Wageningen University (physics/chemistry). Writes on Medium/ITNEXT about AWS CloudFormation, DynamoDB. Led the streaming architecture initiative with Kafka.
  - **Lieke Kools** — Lead Data Scientist
- **Hiring now**: Engineering Manager - Data + Senior Data Engineer (my role)
- The team sits within the Technology department alongside IoT and Platform teams

## Funding & Financials
| Round | Date | Amount | Lead Investor |
|-------|------|--------|--------------|
| Seed | Early | — | — |
| Series A | ~2019 | ~€7M | — |
| Series B | Jan 2022 | €13M | — |
| Series C | Jul 2023 | €25M ($28.1M) | Blume Equity |
| **Total Raised** | | **$48.4M** | |

Investors: Blume Equity, FORWARD.one, Korys, SET Ventures, EIT InnoEnergy

### ABB Acquisition (MAJOR EVENT)
- **Announced**: January 21, 2025
- **Expected close**: Q1 2025
- **Buyer**: ABB (Swiss multinational, global leader in electrification & automation)
- **Division**: Smart Power (led by Massimiliano Cifalitti)
- **Strategic rationale**: ABB expanding digital energy management portfolio; Sensorfact gets global scale
- **What this means**: Sensorfact now has ABB's resources to expand globally while maintaining startup culture

## Revenue & Scale
- **Revenue**: $50M-$100M range
- **Customers**: 2,000+ manufacturers across Europe
- **Employees**: 250-368 (across 3 continents)
- **Offices**: Utrecht (HQ), Amsterdam, Barcelona, Berlin
- **Nationalities**: 50+

## Market & Competition
### Industry
Industrial energy management / IoT for manufacturing. Driven by:
- **EU Energy Efficiency Directive** (EED) — mandatory energy audits for large companies, driving SME adoption
- **Rising energy costs** (post-Ukraine crisis)
- **Carbon reduction mandates** (ESG reporting requirements)
- **Industry 4.0** digitalization trend

### Competitors
- **Verdigris** — AI-powered smart building management (more commercial buildings)
- **Wattics** — Cloud-based energy analytics
- **Landis+Gyr** — Smart metering (more utility-side)
- **Sympower** — Demand response
- **None are directly comparable** — Sensorfact's unique advantage is the **plug-and-play hardware + AI advice** combination specifically for industrial SMEs

### Differentiation
1. **Full-stack**: Hardware + software + consulting (not just software)
2. **SME focus**: Simple enough for companies without energy management teams
3. **Plug-and-play**: No complex integration required
4. **ABB backing**: Now has global scale and distribution
5. **AI-powered advice**: Not just monitoring — actionable recommendations

## Culture & Team
### Glassdoor Insights
- Hiring process is "smooth, transparent, and well-organized"
- Recruiters described as "professional, communicative, genuinely interested"
- "Very critical with hiring" in product and tech roles
- One negative review: "AVOID THIS COMPANY AT ALL COSTS" (single outlier)
- Interview difficulty: 2.7/5 (moderate)

### Work Style
- Scrum, 2-week sprints
- Stand-ups at 9:30
- Morning meetings, quiet afternoons for focused work
- ~70% remote
- Up to 2 months/year working abroad
- Multidisciplinary teams with product managers

### Awards & Recognition
- Techleap's Rise Program (climate tech)
- Deloitte Technology Fast 50 (fastest-growing tech companies)

## What This Means For You
1. **Your streaming experience transfers**: Structured Streaming → Kafka/Flink (same concepts)
2. **Your ML background is a differentiator**: They do ML-powered fault detection + MLOps
3. **Your data quality work is directly relevant**: Sensor data quality is critical
4. **ABB acquisition = stability**: Recognized sponsor potential for Kennismigrant visa
5. **Growing team = high impact**: You'd be one of ~6+ data engineers
6. **They need an Engineering Manager too**: Shows team is growing fast, your leadership experience is valuable
