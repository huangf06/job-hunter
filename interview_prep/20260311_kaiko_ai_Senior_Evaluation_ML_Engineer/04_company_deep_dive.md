# Company Deep Dive - kaiko.ai

## Company Overview

| Detail | Value |
|--------|-------|
| Name | kaiko.ai |
| Domain | Clinical AI / oncology AI |
| Geography | Amsterdam and Zurich |
| Public positioning | AI systems designed for hospital workflows and regulated care environments |
| Flagship product | `kaiko.w` |
| Partner examples on company site | Antoni van Leeuwenhoek-NKI, LUMC, UMCU, REGA |

## What They Actually Sell

kaiko is not selling generic chatbot AI. The company is positioning itself as a clinical AI layer that helps care teams reason across fragmented patient context:

- notes
- pathology
- radiology
- labs
- imaging
- genomics

The product claim is that clinicians should get a continuous, usable patient view instead of reconstructing context manually across systems.

## Why This Matters For Your Interview

The evaluation challenge is central, not peripheral.

If the model is meant to assist oncology reasoning across modalities, then evaluation has to answer questions like:

- Was the answer clinically grounded?
- Did the system use the right evidence?
- Did benchmark construction leak information?
- Are improvements real or metric gaming?
- Is performance consistent across clinically important subgroups?

That is exactly why this role exists.

## Public Facts Worth Knowing

### Team size

Two public numbers appear in current materials:

- the stored March 2, 2026 JD says `80+ people` and `25 nationalities`
- the current company homepage says `120+` people

Interpretation: the company is growing fast and public materials are not perfectly synchronized.

### Partnerships

The public site highlights close collaboration with hospital and research partners, including:

- Antoni van Leeuwenhoek / NKI
- LUMC
- UMCU
- REGA

This is important because it means the evaluation team likely operates close to real clinical stakeholders rather than purely offline research benchmarks.

### Backing

The company page states it is backed by the Hartwig Foundation.

That matters because it reinforces a long-horizon, mission-driven framing rather than pure short-term SaaS optimization.

## Product and Technical Implications

The product promise implies several hard engineering realities:

1. multimodal data is messy and heterogeneous
2. medical context shifts over time
3. evaluation cannot rely on one benchmark or one scalar metric
4. release confidence requires strong data provenance and auditability

This means the team probably values engineers who can think about:

- benchmark lifecycle management
- failure modes
- stratification
- reproducibility
- expert review loops
- operational observability

## Values From The JD

The job post strongly emphasizes:

- Ownership
- Collaboration
- Ambition

In practice, that probably means:

- Ownership: ability to define structure where ambiguity exists
- Collaboration: work with clinicians, annotators, and researchers without ego
- Ambition: willingness to operate at clinical-grade quality instead of "demo-grade AI"

## Public Research / Ecosystem Signals

### Company insights page

Recent public material on `kaiko.ai/insights` reinforces that the company is actively talking about:

- medical foundation models
- evaluation questions around human vs AI differences
- collaboration with healthcare institutions

### GitHub

The public GitHub organization `kaiko-ai` exists and includes repositories such as `eva`.

Inference:

The company likely has a real internal culture around evaluation tooling rather than treating evaluation as ad hoc notebook work.

## What To Ask About

These are high-value company questions because they connect directly to the role:

1. How is evaluation work split today between ML engineers, clinicians, and researchers?
2. What is the hardest unsolved problem right now: benchmark curation, online review flows, release gating, or modality-specific evaluation?
3. How do they decide that an evaluation metric is clinically meaningful rather than just easy to automate?
4. How mature is their eval platform today: prototype, internal toolchain, or productionized release gate?

## Likely Internal Tensions

These are inferred, not confirmed:

- speed of model iteration vs need for rigorous validation
- synthetic data scale vs clinical realism
- research flexibility vs auditable production processes
- single-number reporting vs nuanced clinical performance slices

If you can talk coherently about those tensions, you will sound much closer to the actual problem they are hiring for.

## Sources

- https://www.kaiko.ai
- https://www.kaiko.ai/insights
- https://github.com/kaiko-ai
