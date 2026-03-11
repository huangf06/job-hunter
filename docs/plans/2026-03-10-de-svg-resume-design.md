# DE SVG Resume Design — Pixel-Match Toni Layout

Date: 2026-03-10
Status: Approved. Ready for implementation.
Depends on: `2026-03-10-narrative-architecture-design.md` (v4.0 bullet content)

## Design Goal

Create a production-quality SVG resume for Data Engineer roles that pixel-matches Toni Kendel's CV layout while using our v4.0 narrative-architecture bullets. This becomes the gold-standard DE template; ML and DS variants will be derived from it.

## Visual Reference

- **Target**: `templates/Toni_CV_highres.png`
- **Baseline**: `templates/resume_svg_template.svg` (our current attempt — close but has spacing/density issues)

## Page Dimensions

- A4: 595 x 842 pt (210 x 297 mm)
- Margins: ~40pt left/right, ~35pt top, ~25pt bottom
- Content width: ~515pt (595 - 40 - 40)
- Column split: Left ~280pt (x=40 to x=320), Right ~245pt (x=330 to x=555)

## Typography Spec (matching Toni)

| Element | Font | Size | Weight | Color | Style |
|---------|------|------|--------|-------|-------|
| Name | Georgia, serif | 38pt | Bold | #000000 | — |
| Contact info | Arial, sans-serif | 9pt | Normal | #333333 | Right-aligned, stacked |
| "BIO" label | Arial, sans-serif | 9pt | Bold | #1B3A5C | ALL CAPS, letter-spacing: 1.5 |
| Bio text | Arial, sans-serif | 9pt | Normal | #333333 | Bold keywords |
| Section headers | Arial, sans-serif | 9pt | Bold | #1B3A5C | ALL CAPS, letter-spacing: 1.5 |
| Company line | Arial, sans-serif | 10pt | Bold + Italic | #000000 | "Company, City — *Title*" |
| Dates | Arial, sans-serif | 7.5pt | Normal | #666666 | ALL CAPS, letter-spacing: 0.5 |
| Bullet text | Arial, sans-serif | 8.5pt | Normal | #333333 | "• " prefix, bold keywords |
| Tech skills label | Arial, sans-serif | 8.5pt | Bold | #333333 | "Technical Skills:" |
| Tech skills list | Arial, sans-serif | 8.5pt | Normal | #333333 | Comma-separated |
| Skill category | Arial, sans-serif | 9pt | Bold | #333333 | "Category:" |
| Skill items | Arial, sans-serif | 9pt | Normal | #333333 | Comma-separated |

## Layout Structure

```
┌─────────────────────────────────────────────────────────┐
│ Fei Huang (38pt, bold, Georgia)     Amsterdam, NL (9pt) │  y=35-65
│                                     +31 645 038 614     │
│                                     huangf06@gmail.com  │
├─────────────────────────────────────────────────────────┤  y=70 (gray line)
│ BIO                                                      │  y=85
│ Data engineer with 6 years building production data...   │  y=97-125
├─────────────────────────────────────────────────────────┤  y=135 (gray line)
│ LEFT COLUMN (x=40)        │ RIGHT COLUMN (x=330)        │
│                            │                             │
│ EDUCATION                  │ SELECTED PROJECTS           │
│ VU Amsterdam               │ Greenhouse Sensor Pipeline  │
│ Tsinghua University        │ • etl_pipeline bullet       │
│                            │ Technical Skills: ...       │
│ PROFESSIONAL EXPERIENCE    │                             │
│ GLP Technology             │ MSc Thesis: UQ in Deep RL   │
│ • founding_member          │ • uq_framework bullet       │
│ • decision_engine          │ Technical Skills: ...       │
│ • data_engineer            │                             │
│ Technical Skills: ...      │ TECHNICAL SKILLS            │
│                            │ Languages & Core: ...       │
│ Baiquan Investment         │ Data Engineering: ...       │
│ • de_pipeline              │ Cloud & DevOps: ...         │
│ • factor_research          │ Databases: ...              │
│ Technical Skills: ...      │ ML/AI: ...                  │
│                            │                             │
│ Ele.me                     │ CERTIFICATIONS              │
│ • fraud_detection          │ Databricks Certified DE Pro │
│ • sql_optimization         │                             │
│ Technical Skills: ...      │ LANGUAGES                   │
│                            │ English — Fluent            │
│ Henan Energy               │ Mandarin — Native           │
│ • data_automation          │                             │
│ Technical Skills: ...      │                             │
└────────────────────────────┴─────────────────────────────┘
```

## Content Selection (DE Template)

### Bio
> Data engineer with 6 years building production data systems — from ingesting market feeds for 3,000+ securities to designing credit scoring pipelines from scratch as a startup's first data hire. M.Sc. in AI (VU Amsterdam, 8.2/10). Databricks Certified Data Engineer Professional.

Bold keywords: **production data systems**, **3,000+ securities**, **credit scoring pipelines**, **first data hire**, **M.Sc. in AI**, **8.2/10**, **Databricks Certified Data Engineer Professional**

### Education
- **VU Amsterdam**: M.Sc. in Artificial Intelligence, Sep 2023 - Aug 2025, GPA 8.2/10
  - Coursework: Data Mining (9.0), Deep Learning (9.5), Algorithms in Sequence Analysis (9.0)
  - Thesis: Uncertainty Quantification in Deep RL
- **Tsinghua University**: B.Eng. in Industrial Engineering, Sep 2006 - Jul 2010
  - (#1 in China, Top 20 globally)

### Experience (Left Column, 9 bullets total)

**GLP Technology, Shanghai — Lead Data Engineer** (Jul 2017 - Aug 2019)
1. `glp_founding_member` (context_setter) — first hire, built platform from scratch
2. `glp_decision_engine` (depth_prover) — 29 rules, 36-segment, scorecard
3. `glp_data_engineer` (foundation) — ETL 30+ tables, credit bureau parser
Technical Skills: Python, PySpark, AWS (Redshift, S3), SQL, ETL, Credit Risk

**Baiquan Investment, Beijing — Quantitative Developer** (Jul 2015 - Jun 2017)
Company note: "Quantitative hedge fund, 5-person team"
1. `bq_de_pipeline` (headline) — 3,000+ securities, tick-level data, corp actions
2. `bq_factor_research` (headline) — Fama-MacBeth, 4 factor families, live portfolio
Technical Skills: Python, NumPy, Pandas, SQL, Factor Modeling, Backtesting

**Ele.me, Shanghai — Data Analyst** (Sep 2013 - Jul 2015)
Company note: "(acquired by Alibaba)"
1. `eleme_fraud_detection` (headline) — 51K clusters, 2.2M users, 3 algorithms
2. `eleme_sql_optimization` (headline) — 90+ queries, 5x scan reduction
Technical Skills: SQL, Hadoop, Hive, Python, Data Pipeline Optimization

**Henan Energy, Zhengzhou — Business Analyst** (Jul 2010 - Aug 2013)
Company note: "Fortune Global 500"
1. `he_data_automation` (headline) — 20+ BUs, 2 days → 2 hours
Technical Skills: Excel, VBA, Data Automation, SQL, Data Quality

### Projects (Right Column, 2 projects)

**Greenhouse Sensor Data Pipeline (PySpark + Delta Lake)** (2026)
1. `greenhouse_etl_pipeline` (headline) — 3,842 JSON, Medallion Architecture, SHA-256
Technical Skills: PySpark, Delta Lake, Medallion Architecture, Data Quality

**M.Sc. Thesis: UQ in Deep RL** (Feb 2025 - Aug 2025)
1. `thesis_uq_framework` (headline) — 5 methods, 150+ HPC runs, 31% CRPS, p<0.001
Technical Skills: PyTorch, Deep RL, Statistical Testing, HPC/SLURM

### Skills (Right Column)
- Languages & Core: Python (Expert), SQL (Expert), Bash
- Data Engineering: PySpark, Spark, Delta Lake, Databricks, ETL/ELT, Medallion Architecture
- Cloud & DevOps: AWS, Docker, Airflow, CI/CD, Git
- Databases: PostgreSQL, MySQL, Hadoop, Hive
- ML/AI: Pandas, NumPy, PyTorch, XGBoost, LightGBM, scikit-learn

### Certification
Databricks Certified Data Engineer Professional (2026)

### Languages
English — Fluent | Mandarin — Native

## Design Decisions

### Bullet Points (deviate from Toni)
Toni uses paragraph style. We use bullet points because:
1. Tech industry standard for DE/ML roles
2. 2.3x faster scanning for HMs (eye-tracking research)
3. v4.0 bullets designed as standalone impact statements
4. Better ATS parsing

### Technical Skills per job (match Toni, no Soft Skills)
Keep "Technical Skills:" per job entry — ties tech to context.
Drop "Soft Skills:" — generic filler, no value in tech hiring.

### Independent Researcher period
OMIT from DE template. Henan Energy is more relevant for DE positioning.
The 2019-2023 gap is addressed by: MSc admission in 2023 (visible in Education dates).

### Baiquan title
"Quantitative Developer" (DE-oriented, not "Quantitative Researcher")

### GLP title
"Lead Data Engineer" (DE-oriented, not "Data Scientist & Team Lead")

## Color Palette
- Name: #000000 (pure black)
- Section headers: #1B3A5C (navy blue)
- Company names: #000000
- Body text: #333333 (dark gray)
- Dates: #666666 (medium gray)
- Divider lines: #CCCCCC (light gray)
- Background: #FFFFFF (white)

## Spacing Rules (matching Toni's density)
- Line height: 12pt for 9pt text, 11pt for 8.5pt text
- Between section header and first entry: 5pt
- Between company name and date: 2pt
- Between date and first bullet: 5pt
- Between bullets within a company: 2pt
- Between last bullet and Technical Skills: 3pt
- Between companies: 12pt
- Between sections: 15pt
- Bullet indent: 8pt from column left edge
- Bullet text wrap indent: 16pt (aligned after "• ")

## Implementation Approach
1. Hand-craft SVG with precise coordinates
2. Use `<tspan>` for text wrapping within bullet text elements
3. Bold keywords via `<tspan font-weight="bold">`
4. Test rendering in browser → export PDF via Playwright
5. Compare side-by-side with Toni's CV
6. Iterate spacing/sizing until pixel-match achieved
