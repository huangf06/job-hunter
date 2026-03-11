# Next-Round Prep - kaiko.ai

## Current Status

No public kaiko-specific take-home assignment was found in this session.

That said, the JD and invite give enough signal to predict the likely shape of the next step.

## Most Likely Technical Round Themes

### 1. Evaluation system design

You may be asked to design an evaluation pipeline for a clinical AI workflow. Prepare to discuss:

- benchmark sourcing
- task taxonomy
- leakage controls
- versioning
- reproducibility
- release gating
- observability

### 2. Dataset and benchmark hygiene

They may ask how you would prevent misleading evaluation results. Be ready on:

- deduplication
- train/test contamination
- stratified sampling
- cohort balance
- synthetic data risks
- de-identification awareness

### 3. Human evaluation flows

The JD explicitly mentions clinician-in-the-loop review and preference / ranking. Prepare to talk about:

- annotation protocol design
- inter-rater disagreement
- rubric clarity
- escalation paths for ambiguous cases

### 4. Healthcare-specific ramp strategy

Even if the round is technical, they may test whether you can learn the domain responsibly. Prepare a concrete ramp plan:

1. core oncology terminology
2. representative care workflows
3. modality-specific data basics
4. standards vocabulary
5. repeated review loops with clinicians

## Mock Prompt You Should Practice

> Design an evaluation stack for a multimodal oncology assistant that summarizes patient context across notes, imaging, genomics, and labs. How would you define tasks, build benchmarks, prevent leakage, involve clinicians, and decide whether a model release is safe to ship?

## Good Whiteboard Structure

1. Define use cases and decisions
2. Define failure modes
3. Build benchmark slices
4. Establish data provenance and split discipline
5. Define automated and human metrics
6. Build reproducible pipelines and dashboards
7. Tie outputs to go / no-go release criteria

## Specific Stories To Rehearse

### Story A - Thesis benchmark

Use for:

- evaluation methodology
- reproducibility
- statistical rigor

### Story B - GLP data quality framework

Use for:

- high-stakes reliability
- data validation
- ownership

### Story C - Databricks lakehouse project

Use for:

- Spark / Delta / streaming
- platform thinking
- data quality operations

## Lightweight Domain Prep Before The Interview

Read enough to be conversant on:

- TNM staging
- biomarkers
- lines of therapy
- RECIST
- FHIR
- DICOM
- pathology vs radiology vs genomics as different evidence sources

You do not need to become a clinician. You need to show disciplined respect for the domain.
