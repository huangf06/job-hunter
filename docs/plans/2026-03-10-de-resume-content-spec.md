# Data Engineer Resume Content Spec

Date: 2026-03-10
Status: Approved content baseline

## Goal

Finalize the canonical content for the Data Engineer resume before layout work. This document defines what the DE template should include, what should remain optional, and what should be excluded by default.

## Target Positioning

This resume targets:

- Data Engineer
- Analytics Engineer
- Data Platform Engineer
- ETL / Pipeline / Data Quality roles

This resume does not primarily target:

- ML Engineer
- Research Scientist
- Quant Trader

The positioning should stay centered on production data systems, pipeline ownership, data quality, and analytical depth.

## Core Narrative

The candidate should read as a first-principles builder: someone who understands problems from the ground up, designs systems deliberately, and implements them end-to-end.

The DE narrative arc is:

1. Early data automation and reporting system design before modern tooling
2. Large-scale analytical problem solving in a high-growth environment
3. Engineering data pipelines that support real research and production decisions
4. Owning a full credit-risk data platform from scratch as the first technical data hire
5. Adding methodological rigor through an M.Sc. in AI without shifting the core identity away from Data Engineer

The main impression after reading should be:

> This is a technically rigorous builder who can design and own production data systems, not just operate tools.

## Final Bio

Use this as the canonical DE bio:

> Data engineer with 6 years building production data systems, from ingesting market feeds for 3,000+ securities to designing credit risk pipelines from scratch as a startup's first data hire. M.Sc. in Artificial Intelligence from VU Amsterdam (8.2/10) brings rigorous thinking to pipeline design, data quality, and system reliability. Databricks Certified Data Engineer Professional.

### Bio principles

- Keep `6 years`, but scope it to production data systems
- Keep `3,000+ securities` as the scale marker
- Keep `first data hire` as the ownership marker
- Keep `M.Sc. in Artificial Intelligence`, but use it to signal rigor rather than ML-first positioning
- Keep the Databricks certification as a DE market signal
- Do not add company-specific closers in the baseline template
- Do not stuff the bio with extra cloud or buzzword keywords

## Education

### Keep

#### Vrije Universiteit Amsterdam

- M.Sc. in Artificial Intelligence
- Sep. 2023 - Aug. 2025
- GPA: 8.2/10
- Relevant Coursework:
  - Data Mining Techniques (9.0)
  - Deep Learning (9.5)
  - Algorithms in Sequence Analysis (9.0)
- Thesis: Uncertainty Quantification in Deep Reinforcement Learning

#### Tsinghua University

- B.Eng. in Industrial Engineering
- Sep. 2006 - Jul. 2010
- School note: #1 in China, Top 20 globally

### Principles

- Education remains visible and credible, but should not dominate the resume
- Course selection in the DE version should lean data / algorithms, not broad ML showcase
- Thesis should stay as one concise line in Education
- Tsinghua brand value should be explicit

## Experience

The DE baseline includes five work experiences in hybrid chronological order: GLP Technology (most recent professional role) at top, followed by Independent Quantitative Researcher (2019-2023 gap explanation), then remaining roles in reverse chronological order.

**Experience ordering (updated 2026-03-11):**
1. GLP Technology (Jul 2017 - Aug 2019)
2. Independent Quantitative Researcher (Sep 2019 - Aug 2023)
3. BQ Investment (Jul 2015 - Jun 2017)
4. Ele.me (Sep 2013 - Jul 2015)
5. Henan Energy (Jul 2010 - Aug 2013)

### 1. GLP Technology, Shanghai

Final title:

- Lead Data Engineer

Keep these bullets:

- `glp_founding_member`
- `glp_decision_engine`
- `glp_data_engineer`

Role of this section:

- Primary ownership proof
- Strongest from-scratch platform story
- Main production data systems evidence

Selection rationale:

- `glp_founding_member` establishes first-hire ownership and full-platform scope
- `glp_decision_engine` proves system design depth and business logic understanding
- `glp_data_engineer` provides direct DE language: ETL, Redshift, parser, structured analytical tables

Default exclusions:

- `glp_portfolio_monitoring`
- `glp_generalist`

### 2. BQ Investment, Beijing

Final title:

- Quantitative Developer

Keep company note:

- Quantitative hedge fund, 5-person team

Keep these bullets:

- `bq_de_pipeline`
- `bq_factor_research`

Role of this section:

- Demonstrates engineering in a high-complexity data environment
- Shows that the data pipeline supported downstream research and live trading

Selection rationale:

- `bq_de_pipeline` is the strongest DE-relevant bullet in the section
- `bq_factor_research` shows the pipeline was connected to real production use, not isolated data plumbing

Default exclusions:

- `bq_de_backtest_infra`
- `bq_futures_strategy`

### 3. Ele.me, Shanghai

Final title:

- Data Analyst

Keep company note:

- (acquired by Alibaba)

Keep these bullets:

- `eleme_fraud_detection`
- `eleme_sql_optimization`

Role of this section:

- Shows large-scale operational data work in a hyper-growth business
- Strengthens the analytics plus data systems bridge

Selection rationale:

- `eleme_fraud_detection` adds business-critical scale and analytical problem-solving
- `eleme_sql_optimization` adds warehouse and performance optimization credibility

Default exclusions:

- `eleme_user_segmentation`
- `eleme_bi_dashboards`

### 4. Henan Energy, Zhengzhou

Final title:

- Business Analyst

Keep company note:

- Fortune Global 500

Keep this bullet:

- `he_data_automation`

Optional second bullet if space allows:

- `he_supply_chain_analytics`

Role of this section:

- Establishes the origin story: data engineering mindset before modern tooling

Selection rationale:

- `he_data_automation` most directly supports the DE narrative through ingest / validate / consolidate / automation language
- `he_supply_chain_analytics` is strong, but secondary in the standard one-page DE baseline

Default exclusions:

- `he_data_quality`
- `he_data_standardization`

### 5. Independent Quantitative Researcher

Content library status:

- Keep in the content baseline
- **Include by default** in the standard one-page DE template (updated 2026-03-11 based on reviewer feedback)

Available bullet:

- `indie_quant_research` (primary, use this one)

Optional supporting bullet:

- `indie_skill_development` (omit in DE template)

Usage rule:

- Include this section with single `indie_quant_research` bullet by default
- Position immediately after GLP Technology to maintain chronological continuity
- Omit only when space is critically constrained

Rationale:

- Addresses the 2019-2023 timeline gap that reviewers flagged as problematic
- The `indie_quant_research` bullet demonstrates real DE skills (83K+ daily records, 3,600+ stocks, Tushare API, MySQL)
- Positioned after GLP (not at bottom) maintains narrative flow and keeps strongest DE experience at top
- Single bullet keeps it concise without overcompensating

## Projects

The DE baseline should include two primary projects. A third project slot may exist for customization, but should be off by default.

### 1. Greenhouse Sensor Data Pipeline (PySpark + Delta Lake)

Keep this bullet:

- `greenhouse_etl_pipeline`

Role of this project:

- Modern DE proof point
- Best single project for PySpark, Delta Lake, Medallion Architecture, and idempotent processing

Default exclusions:

- `greenhouse_data_quality`
- `greenhouse_aggregations`

### 2. M.Sc. Thesis: Uncertainty Quantification in Deep RL

Keep this bullet:

- `thesis_uq_framework`

Role of this project:

- Adds rigor, experimentation discipline, and scale management
- Supports the narrative that the candidate is methodical, not just tool-driven

Default exclusions:

- `thesis_noise_paradox`
- Other thesis secondary bullets

### 3. Optional third project slot

Not enabled in the default DE baseline.

Candidate:

- `lakehouse_streaming`

Usage rule:

- Only include a third project when a JD strongly rewards additional systems-building evidence and the page can still remain disciplined

**Excluded projects:**

- `job_hunter_system` / Multi-Source Application Tracking — removed based on reviewer feedback (2026-03-11) as it reads as job-hunt automation rather than production DE work

## Skills

Use these five categories in the DE baseline:

### Languages & Core

- Python (Expert)
- SQL (Expert)
- Bash

### Data Engineering

- PySpark
- Spark
- Delta Lake
- Databricks
- ETL/ELT
- Medallion Architecture

### Cloud & DevOps

- AWS
- Docker
- Airflow
- CI/CD
- Git

### Databases

- PostgreSQL
- MySQL
- Hadoop
- Hive

### ML/AI

- Pandas
- NumPy
- PyTorch
- XGBoost
- LightGBM
- scikit-learn

### Skills principles

- The first four categories define the DE identity
- The ML/AI category stays last and acts as supporting breadth, not the primary story
- Do not add broad transferable skills by default
- Do not include a soft-skills section

## Certification

Keep:

- Databricks Certified Data Engineer Professional (February 2026)

Rationale:

- Strong market signal for DE roles
- Helps modernize the profile alongside older experience

## Languages

Keep:

- English - Fluent
- Mandarin - Native

## Default Exclusions

The DE content baseline should explicitly exclude these items from the standard one-page template:

- `indie_skill_development` bullet (keep only `indie_quant_research`)
- `job_hunter_system` / Multi-Source Application Tracking project
- `Deribit options` project
- `bq_futures_strategy`
- `bq_de_backtest_infra`
- `eleme_user_segmentation`
- `eleme_bi_dashboards`
- `glp_generalist`
- `glp_portfolio_monitoring`
- `he_data_quality`
- `he_data_standardization`
- Soft-skills lines
- Company-specific closing sentences
- Excessive transferable skills
- Any bullet that is vague, hard to defend, or shifts the narrative toward ML Engineer or Quant Trader

## One-Page Priority Rules

If content exceeds one page, trim in this order:

1. Reduce `Independent Quantitative Researcher` to zero bullets (omit section entirely)
2. Keep only one thesis bullet
3. Keep only one Henan Energy bullet
4. Do not expand project count beyond two
5. Preserve GLP, Baiquan, and Ele.me before trimming anything else

Priority order from highest to lowest:

1. Final Bio
2. GLP three bullets
3. Independent Quantitative Researcher (one bullet)
4. Baiquan two bullets
5. Ele.me two bullets
6. Greenhouse project
7. Education
8. Skills
9. Thesis project
10. Henan Energy

## Canonical DE Baseline Summary

The standard DE template should contain:

- One canonical DE bio
- Two education entries
- Five work experiences:
  - GLP Technology
  - Independent Quantitative Researcher (one bullet)
  - BQ Investment
  - Ele.me
  - Henan Energy
- Two projects:
  - Greenhouse Sensor Data Pipeline
  - M.Sc. Thesis: UQ in Deep RL
- Five skill categories
- One certification line
- One languages line

The default version should not attempt to tell every part of the story. It should tell the strongest DE story with disciplined narrative focus.
