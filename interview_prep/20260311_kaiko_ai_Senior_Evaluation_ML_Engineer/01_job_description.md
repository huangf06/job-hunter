# Job Description - kaiko.ai Senior Evaluation ML Engineer

## Metadata

| Field | Value |
|-------|-------|
| Company | kaiko.ai |
| Role | Senior Evaluation ML Engineer |
| Source | LinkedIn snapshot stored in local DB |
| Job ID | `69d2dfb9a403` |
| URL | https://www.linkedin.com/jobs/view/4362094650/ |
| Location | Amsterdam Area (Hybrid) |
| Snapshot date | Stored locally, accessed 2026-03-11 |
| Interview status | `applications.status = interview` |
| Interview time | 2026-03-11 11:30-12:00 |

## Why This Role Exists

kaiko is building an oncology-focused multimodal large language model. The role exists because clinical-grade performance requires an evaluation stack that is not just large-scale, but clinically meaningful, reproducible, and trusted by experts.

The role is therefore not generic model evaluation. It combines:

- evaluation pipeline engineering
- benchmark curation
- synthetic data generation
- clinical rubric design
- release gating
- clinician-in-the-loop review

## Core Responsibilities From JD

- Build and operate evaluation infrastructure at scale using Python and distributed compute such as Ray or Spark.
- Emphasize CI/CD, reproducibility, and observability.
- Source and curate benchmarks from public, licensed, and partner-provided data.
- Generate synthetic cases while controlling for leakage, cohort balance, plausibility, and difficulty.
- Define clinically meaningful tasks and rubrics across:
  - text
  - imaging
  - pathology
  - genomics
  - structured EHR / FHIR
- Automate offline evaluations and also build online evaluation flows:
  - clinician review
  - preference / ranking
  - A/B style comparisons
- Work with clinicians and external partners to turn clinical questions into measurable evaluation tasks.
- Maintain benchmark hygiene:
  - deduplication
  - de-identification awareness
  - leakage audits
  - stratified sampling

## Required Skills From JD

- Excellent Python
- Strong software engineering fundamentals:
  - testing
  - modular design
  - CI/CD
- Deep experience designing and operating evaluation or data-quality pipelines for ML/LLMs at scale
- Comfort with:
  - Ray / Spark
  - Delta / Iceberg style lakehouse paradigms
  - Parquet / ORC
- Working knowledge of oncology workflows and terminology:
  - TNM staging
  - biomarkers
  - lines of therapy
  - RECIST
  - labs and imaging follow-up

## Nice-to-Have Areas

- `lm-eval-harness`, OpenAI Evals, HF Evaluate
- preference modeling
- healthtech / biomed / bioinformatics / medical imaging
- clinical software quality or safety concepts
- medical reports and standards:
  - FHIR / HL7
  - SNOMED CT
  - ICD-10 / ICD-O
  - LOINC
  - DICOM
  - VCF
- Dagster
- monitoring / observability
- medical foundation model evaluation

## Values and Working Style From JD

The job post repeatedly stresses:

- Ownership
- Collaboration
- Ambition

This matters because the first interview is likely to test not only technical depth, but whether you can operate responsibly in a high-autonomy, high-stakes environment.

## Interview Process In JD

The post describes a typical process:

1. Screening call
2. Technical interview
3. Onsite meeting (optional)
4. Final executive conversation

The current invite most likely maps to Step 1.

## Role-Specific Interpretation

This role sits at the intersection of four things:

1. ML evaluation science
2. data platform engineering
3. product quality / release governance
4. clinical translation

That is why your strongest angle is not "I trained models" alone. It is:

`I know how to design reliable evaluation systems and data pipelines where wrong outputs have real consequences.`

## Sources

- Local DB snapshot from `data/jobs.db`
- https://www.linkedin.com/jobs/view/4362094650/
- https://www.kaiko.ai
