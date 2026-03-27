# Deployment Decision: Job-Hunter Pipeline Runtime

**Date:** 2026-03-27
**Status:** Final
**Scope:** Block A runtime placement and long-term pipeline hosting model

---

## Final Decision

**Do not migrate to VPS or self-hosted runners now.**

The pipeline will remain on **GitHub-hosted Actions runners** for the current phase.

This is a deliberate decision, not a default or temporary placeholder.

## Final Deployment Model

- **Primary runtime:** GitHub Actions hosted runners (`ubuntu-latest`)
- **Primary scheduler/control plane:** GitHub Actions
- **Primary daily scrape path:** unchanged
  - LinkedIn + Greenhouse on the existing hosted workflow
- **IamExpat:** remains manual/backfill only
- **No VPS**
- **No self-hosted GitHub runner**
- **No hybrid split**

---

## Why This Is The Final Decision

The earlier infrastructure discussion correctly identified a real tradeoff:

- **Architecture-optimal answer:** isolate LinkedIn onto a more stable environment
- **Operationally practical answer:** avoid introducing machine administration unless the current hosted setup is clearly insufficient

After reviewing the tradeoffs, the deciding factor is **maintainability**.

This project is a personal job-hunting pipeline, not a production multi-service platform. A VPS or hybrid deployment would add:

- Linux machine maintenance
- runner service maintenance
- browser/profile persistence management
- remote debugging overhead
- extra failure modes unrelated to the job search itself

That additional operational burden is not justified yet.

The current system already has:

- working GitHub Actions schedules
- a merged Block A rebuild
- structured LinkedIn diagnostics
- runbooks/checklists for scraper failures
- a stable and simple control plane

So the correct decision for now is:

- **keep the system simple**
- **accept GitHub-hosted runner limitations**
- **only revisit migration if hosted execution proves materially inadequate**

---

## Why We Are Not Choosing The Other Options

### Linux VPS + self-hosted runner

Rejected for now because:

- it increases operational surface area too much for a personal pipeline
- it turns a code-maintenance problem into a code-plus-infrastructure problem
- it makes debugging and recovery more manual

This remains a valid future option, but not the current decision.

### Hybrid deployment

Rejected for now because:

- it is architecturally elegant but operationally split-brained
- it would require managing two runtime models
- it adds complexity without enough evidence that the hosted path is failing badly enough

Hybrid remains the most targeted architecture, but not the best practical choice at this stage.

### AWS EC2 Free Tier / Lightsail / small VPS providers

Not chosen because:

- the current decision is **not to migrate at all**
- provider selection is premature until migration is actually justified

If migration is reopened later, provider comparison can be revisited then.

### Local Windows machine

Rejected because:

- it is the least reliable automation runtime
- it depends on personal machine availability and state

---

## Current Operating Principle

For this project, **simplicity beats theoretical runtime optimality**.

The system should remain:

- easy to understand
- easy to maintain
- easy to recover

Even if that means accepting some LinkedIn-hosted-runner fragility.

---

## When To Reopen This Decision

Revisit deployment only if one or more of these become true:

1. **LinkedIn hosted-runner instability becomes persistent**
   - repeated session/challenge failures
   - materially lower usefulness of the pipeline

2. **Hosted runner limitations begin blocking operations**
   - schedule reliability becomes unacceptable
   - runtime or environment volatility becomes a recurring problem

3. **The operational value clearly exceeds the maintenance cost**
   - there is strong evidence that moving runtimes would improve scraper yield enough to justify new infra

Until then, the answer remains:

- **stay on GitHub Actions**

---

## Fallback Position

If GitHub-hosted execution becomes unacceptable in the future, the next option to evaluate is:

- **single Linux VPS running the whole main pipeline**

Not hybrid.

Reason:

- one runtime is simpler to maintain than a split runtime
- if migration is necessary, operational simplicity should win over architectural purity

---

## Open Strategic Option

If hosted execution remains insufficient and private infrastructure is still not worth the maintenance burden, an alternative strategic direction is:

- **open-source the project**

This is not a current deployment action. It is a future escape hatch if the operational model stops being worth maintaining privately.

---

## Bottom Line

The final decision is:

- **do not migrate**
- **continue running on GitHub Actions**
- **do not introduce VPS or hybrid deployment now**
- **reopen only if hosted execution proves clearly inadequate**
