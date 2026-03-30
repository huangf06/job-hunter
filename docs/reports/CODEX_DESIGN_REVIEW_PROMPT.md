# Design Review: Three-Tier Resume Strategy Redesign

## Task

Review the design document at `docs/plans/2026-03-29-resume-strategy-redesign.md` for architectural soundness, completeness, and implementability. This is a **design review**, not a code review — no code has been written yet.

## Context

This is a job-hunting automation system. The current pipeline:
- **C1 (evaluate):** AI scores jobs (1-10) and produces an Application Brief
- **C2 (tailor):** AI generates a fully customized resume for each job using a bullet library
- **Renderer:** Jinja2 + Playwright → HTML → PDF

The redesign replaces the "customize every resume" approach with a template-first strategy:
- 3 polished SVG template resumes (DE, ML, Backend) pre-rendered to PDF
- C1 extended with routing logic to classify jobs into 3 tiers
- C2 split into two modes (adapt vs full customize)
- New C3 quality gate for Tier 2

**Key data:** 957 jobs scoring >= 4.0. Distribution: ML 35%, Backend 34%, DE 16%, Analyst 7%, Quant 3%, Other 5%. Two SVG templates exist (DE+ML, covering 52%). Backend template planned (total coverage ~88%).

## Design Document Location

Read the full design: `docs/plans/2026-03-29-resume-strategy-redesign.md`

## Supporting Context (read if needed)

- Current C1/C2 implementation: `src/ai_analyzer.py` (methods: `evaluate_job`, `tailor_resume`, `_build_evaluate_prompt`, `_build_tailor_prompt`)
- Current renderer: `src/resume_renderer.py`
- Bullet library: `assets/bullet_library.yaml`
- C1 prompt: `config/ai_config.yaml` → `prompts.evaluator`
- C2 prompt: `config/ai_config.yaml` → `prompts.tailor`
- SVG templates: `templates/Fei_Huang_DE_Resume.svg`, `templates/Fei_Huang_ML_Resume.svg`
- Current HTML template: `templates/base_template.html` (dual-column, being deprecated)
- SVG optimizer: `scripts/svg_auto_optimizer.py` (Vision-based iterative QA)

## Review Checklist

### 1. Architecture Soundness
- [ ] Does the three-tier split make sense given the data distribution (52% exact, 37% close, 12% none)?
- [ ] Is the "bias toward template" principle well-justified? Could it cause the system to submit poorly-matched resumes for borderline cases?
- [ ] Is the C3 quality gate (Tier 2 only) the right granularity? Should Tier 1 also have a sanity check? Should Tier 3 have one?
- [ ] Is deterministic template selection (title keywords) robust enough? What about "ML Platform Engineer" (ML or Backend?) or "Data Scientist - Software" (ML or DE?)?
- [ ] The design says C1 can override the code's template selection. How should conflicts be handled?

### 2. C1 Routing Extension
- [ ] Adding routing to C1 (scoring + brief + routing in one call) — does this overload C1? Would the prompt be too long or confused?
- [ ] The template summaries injected into C1 are ~5 lines each (15 lines total). Is this enough for C1 to judge "bio positioning is wrong" or ">50% of bullets irrelevant"?
- [ ] The ADAPT_TEMPLATE trigger conditions ("bio wrong OR >50% bullets irrelevant OR skills misrepresent") — are these specific enough for AI to evaluate reliably?
- [ ] What happens when the Backend template doesn't exist yet? The design says "Phase 1 and Phase 2 can parallel" but C1 routing needs to know about all templates.

### 3. Tier 2: Adapt Template
- [ ] The adapt HTML template concept (SVG's HTML clone with Jinja2 override slots) — is this feasible? Can an SVG layout be faithfully reproduced in HTML/CSS?
- [ ] The C2 Tier 2 output format (`bio_override`, `bullet_overrides`, `skills`) — is this the right abstraction? What if C2 needs to reorder experiences or add/remove a section?
- [ ] "AI can only change designated slots" — what if the optimal adaptation requires changing something not in a slot (e.g., experience ordering, project selection)?
- [ ] How does `bullet_overrides` work? Are the bullet IDs from the SVG template matched to Jinja2 slot names? How are they identified?

### 4. C3 Quality Gate
- [ ] The ~300 token lightweight comparison prompt — is this enough to make a meaningful judgment?
- [ ] The gate receives `change_summary` from C2. Can we trust C2 to accurately summarize its own changes?
- [ ] What's the expected fallback rate? If C3 rejects most Tier 2 adaptations, the whole tier becomes wasteful.
- [ ] Should C3 output include a confidence score rather than binary YES/NO?

### 5. Tier 3: Full Customize
- [ ] Switching from dual-column `base_template.html` to a new simple single-column template — what does this template need to look like?
- [ ] The current C2 full-customize prompt references the old template structure. Will it need updating?
- [ ] Is 12% of jobs worth maintaining a completely separate rendering pipeline?

### 6. Operational Concerns
- [ ] Pre-rendered PDFs as "permanent" files — what's the update workflow when the SVG template changes?
- [ ] Template registry in YAML — where does it live? Is it loaded by both C1 (for summaries) and the renderer (for file paths)?
- [ ] The design deprecates `base_template.html` but the current 675 applications were generated with it. How does this affect `--prepare`/`--finalize` for existing analyzed jobs?
- [ ] How does the DB schema accommodate tier info? Does `job_analysis` need a new column?

### 7. Missing Pieces
- [ ] The design mentions Backend SVG template as a dependency but doesn't spec its content (which bullets, which bio, which skills). Is this intentional?
- [ ] No mention of how `--analyze-job` (single job) interacts with the new routing. Does it go through the same tier logic?
- [ ] No mention of how Application Brief interacts with template selection. The brief is personalized but the resume might be generic (Tier 1). Is this dissonant?
- [ ] Cover Letter / Application Brief rendering — how does it work with the new tiers?
- [ ] Metrics/logging — how do we track tier distribution over time to validate the design assumptions?

## Output Format

```
## Summary
<2-3 sentence overall assessment of design quality and readiness>

## Strengths
- Key design decisions that are well-reasoned

## P0 — Design Flaws (must address before implementation)
- Issues that would cause the implementation to fail or produce wrong results

## P1 — Gaps (should address)
- Missing details that implementers will need answers for

## P2 — Suggestions (nice to have)
- Improvements that could enhance the design

## Questions for the Author
- Clarifications needed before proceeding
```
