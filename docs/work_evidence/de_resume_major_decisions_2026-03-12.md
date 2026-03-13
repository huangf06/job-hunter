# Data Engineer Resume Major Decisions

Date: 2026-03-12
Status: Active reference

## Purpose

This document records the major decisions made so far for the Data Engineer resume line, especially the Toni SVG series up to `templates/de_resume_toni_v18.svg`.

It is intended to prevent re-opening settled questions and to preserve the reasoning behind current resume choices.

## 1. Positioning

The canonical resume identity is:

> A first-principles data engineer who understands problems from the ground up, designs systems deliberately, and implements them end-to-end.

This means the resume should read as:

- production data systems first
- ownership and system design second
- analytical rigor as a credibility layer
- ML/AI as supporting breadth, not the main story

This resume is primarily for:

- Data Engineer
- Analytics Engineer
- Data Platform Engineer
- ETL / Pipeline / Data Quality roles

It is not primarily optimized for:

- ML Engineer
- Research Scientist
- Quant Trader

## 2. Narrative Strategy

The core narrative decision was that the "story" should live in structure and selection, not in overly theatrical bullet writing.

Implications:

- ATS keywords must remain explicit and efficient.
- The recruiter scan layer must stay clean and fast.
- The deeper narrative should come from section order, bullet choice, and flagship proof points.
- The resume should not try to sound profound line by line.

The desired impression is:

> technically rigorous builder, not tool operator

## 3. Canonical Data Engineer Content Baseline

The approved DE baseline is:

- one DE bio
- two education entries: VU Amsterdam, Tsinghua University
- five work experiences:
  - GLP Technology
  - Independent Quantitative Researcher
  - BQ Investment
  - Ele.me
  - Henan Energy
- selected projects focused on real engineering proof
- certification
- skills
- languages

The one-page priority order is:

1. Bio
2. GLP
3. Independent Quantitative Researcher
4. BQ Investment
5. Ele.me
6. Greenhouse project
7. Education
8. Skills
9. Thesis project
10. Henan Energy

## 4. Experience Selection Decisions

The strongest experience proof should come from:

- GLP as the primary ownership / from-scratch platform story
- BQ as engineering in a complex data environment
- Ele.me as business-critical analytical scale
- Henan as origin story, but compressed
- Independent Quantitative Researcher as timeline continuity plus real technical work

Related settled decisions:

- `Aoshen Business` is omitted entirely.
- `Independent Quantitative Researcher` should be included by default in the DE narrative when space permits.
- The resume should avoid weak, vague, or hard-to-defend bullets even if they sound more impressive.

## 5. Project Selection Decisions

The resume should prioritize projects that strengthen the production-data-engineering identity.

Current project logic:

- keep `Greenhouse Sensor Data Pipeline` as the strongest modern DE proof point
- keep `Financial Data Lakehouse` as practical modern systems evidence in the current Toni v18 line
- keep thesis material concise and subordinate to the DE story
- exclude the `job_hunter_system` project from the standard DE resume

The project section is not meant to become a portfolio gallery. It exists to reinforce current-market DE relevance.

## 6. Skills Strategy

The skills section should support the DE identity without turning into a keyword dump.

Settled principles:

- Python and SQL remain front-loaded
- Spark / Delta Lake / Databricks / Airflow / ETL stay central
- AWS / Docker / Git stay as practical infrastructure signals
- ML/AI tools remain supporting breadth, not front-stage identity
- no soft-skills section

The skills block should feel disciplined, not exhaustive.

## 7. Languages and Interests

Current decisions:

- `LANGUAGES` stays as its own section
- it should not be merged into `SKILLS`
- default resume should not add an `INTERESTS` section

Reasoning:

- languages are scan-relevant and deserve separate visibility
- merging them into skills weakens category clarity
- adding interests increases information volume more than decision-making value
- the current resume should stay mature, restrained, and professionally neutral

If an interests line is ever added for a tailored version, it should be minimal and only for a company where personality signaling has clear value.

## 8. Toni Layout Decisions

The Toni series should preserve Toni Kendel's visual language rather than redesign it.

Settled layout rules:

- preserve the two-column structure
- preserve the restrained typography hierarchy
- preserve high information density
- do not add decorative sections
- do not introduce design gestures that reduce readability

This resume should feel like a refined final-send document, not a stylized portfolio artifact.

## 9. Final Layout QA Decisions for v18

The v18 layout pass was explicitly constrained to visual refinement only.

Allowed edits:

- section spacing
- block spacing
- alignment
- small coordinate adjustments
- manual line-break cleanup

Disallowed edits:

- content rewrites
- wording optimization for style alone
- structural redesign
- adding new sections

The main corrections applied in v18:

- normalized right-column section rhythm
- tightened the left-column mid-section gap
- improved project block spacing consistency
- kept header and bio unchanged because they were already visually stable

Final QA conclusion for `templates/de_resume_toni_v18.svg`:

- ready to send

## 10. Default Style Guardrails

When revising this resume in the future, keep these guardrails:

- Do not trade credibility for cleverness.
- Do not trade readability for design.
- Do not trade density for empty visual polish.
- Do not add personality sections unless they clearly help the target application.
- Do not reopen settled baseline choices without a role-specific reason.

## 11. Current Canonical File

Current final DE Toni file:

- `templates/de_resume_toni_v18.svg`

Current exported PDF:

- `output/Fei_Huang_DE_toni_v18.pdf`

## 12. When to Reopen Decisions

Only reopen a major decision if one of these is true:

- the target role is clearly ML-first rather than DE-first
- a specific company version benefits from personality signaling
- a real-space constraint forces content reprioritization
- repeated recruiter or interviewer feedback shows a current choice is underperforming

Otherwise, treat the current baseline as stable.
