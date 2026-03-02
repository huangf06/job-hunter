# Round 2 Take-Home Assignment — Greenhouse Sensor Data Pipeline

> **Source:** Found on Source.ag's public GitHub (github.com/source-ag/assignment-data-engineering)

---

## Assignment Overview

| Detail | Value |
|--------|-------|
| **Type** | ETL/ELT Pipeline |
| **Language** | Python |
| **Time** | ~4 hours |
| **Domain** | Greenhouse sensor data |
| **Input** | JSON sensor readings |
| **Deliverable** | `.git bundle` emailed to them |
| **Deadline** | Final commit 24 hours before Round 2 interview |
| **Scale target** | Design for **1,000 greenhouses × 50 sensors @ 1-min resolution** |
| **LLM allowed** | Yes, explicitly — but you must understand and own every line |

---

## Requirements Breakdown

### 1. Data Ingestion
- Ingest JSON greenhouse sensor data
- Handle idempotent loading (re-running shouldn't create duplicates)
- **Your parallel:** Financial Data Lakehouse Auto Loader with idempotent S3 ingestion

### 2. Data Quality Framework
- **Completeness**: Are all expected fields present?
- **Validity**: Are values within expected ranges? (e.g., temperature, humidity, CO2)
- **Consistency**: Do records align across sources?
- **Deduplication**: Handle duplicate sensor readings
- **Your parallel:** GLP quarantine pattern — malformed records isolated, not silently corrupting downstream

### 3. Aggregations
- 15-minute aggregations (granular)
- Hourly aggregations (summary)
- **Your parallel:** Baiquan factor computation engine — 3,000+ securities with time-based aggregations

### 4. Dimensional Modeling
- Design appropriate fact and dimension tables
- **Your parallel:** Financial Data Lakehouse Medallion Architecture (Bronze → Silver → Gold)

### 5. Analytical Queries (5 specific)
- Daily averages per sensor
- Temperature variance analysis
- Missing data percentage reporting
- Time-series trend queries
- Anomaly detection queries
- **Your parallel:** GLP portfolio monitoring dashboards + Baiquan factor analytics

### 6. Pipeline Orchestration
- Single end-to-end execution command
- Must be reproducible and testable

### 7. Roadmap Discussion (CRITICAL — prepare this!)
You must discuss a **3-month roadmap** covering:
- Slowly-changing dimensions (SCD)
- Data retention policies
- Monitoring & alerting
- Billion-row optimization strategies
- **Your parallel:** GLP data platform evolution, Financial Data Lakehouse scalability design

---

## Assessment Criteria (from assignment)

| Criterion | What They Look For |
|-----------|-------------------|
| **Code structure** | Clean, modular, well-organized |
| **Readability** | Clear naming, logical flow |
| **Documentation** | README with setup, run, test instructions |
| **Testing** | Comprehensive test coverage |
| **Design decisions** | Explain WHY, not just WHAT |
| **Limitations** | Honest about what could be improved |

---

## How Your Experience Maps

| Assignment Need | Your Direct Experience |
|-----------------|----------------------|
| JSON ingestion + idempotency | Auto Loader in Financial Data Lakehouse |
| Data quality framework | GLP quarantine pattern for loan data |
| Time-based aggregations | Baiquan 3,000+ securities daily pipeline |
| Dimensional modeling | Medallion Architecture (Bronze/Silver/Gold) |
| Python ETL | 6+ years production Python |
| Testing | Pytest in job-hunter pipeline |
| Sensor data patterns | Analogous to financial tick data — both are time-series with quality issues |

---

## Other Source.ag Assignments (Context)

| Role | Assignment | Language | Duration |
|------|-----------|----------|----------|
| **Data Engineer** (YOURS) | Greenhouse Sensor Data Pipeline | Python | ~4 hours |
| Software Engineer v2 | Sensor Measurements API | Go 1.22+ or Python 3.12+ | 6-8 hours |
| Cloud Engineer | "Todoozie" TODO App → AWS CDK | AWS CDK (any lang) | N/A |
| Frontend Engineer | Cultivation Team Management | React + TypeScript | 6-8 hours |
| React Native Engineer | Digital Twin Plant Visualization | TypeScript/React Native | 6-8 hours |

**Note:** The SE assignment offers Go OR Python — confirming the careers page framing that Go is "contribute to," not mandatory.

---

## Preparation Strategy

### Before the Assignment (do now)
1. Review Delta Lake / Medallion Architecture patterns
2. Refresh on data quality frameworks (Great Expectations concepts)
3. Review dimensional modeling basics (star schema, slowly changing dimensions)
4. Practice time-series aggregation in PySpark or pandas

### During the Assignment
1. **Start with data exploration** — understand the JSON structure
2. **Design schema first** — don't jump into code
3. **Quality framework early** — don't bolt it on at the end
4. **Test as you go** — pytest for each layer
5. **Document decisions** — README should explain architecture choices
6. **Be honest about limitations** — they value self-awareness over false confidence

### After the Assignment
- The Round 2 interview will discuss your solution
- Be ready to explain every design choice
- Have improvement ideas ready ("if I had more time, I would...")
- Draw the parallel to your real-world experience explicitly
