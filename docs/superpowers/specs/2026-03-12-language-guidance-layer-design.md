# Language Guidance Layer Design

**Date:** 2026-03-12

**Goal**

Create a reusable language-guidance layer that keeps AI-generated résumé, cover letter, and analysis outputs calm, credible, and engineering-first. The system should improve consistency and reduce repetitive or inflated wording without enforcing brittle hard rules.

**Problem**

Current generation quality varies by output type and prompt. Common failure modes:

- Repetitive verb openings such as `Built` or `Developed` across many bullets
- Tone drift between résumé, cover letter, and analysis outputs
- Over-optimized phrasing that sounds less trustworthy to hiring managers
- Inconsistent mapping between action type and verb choice
- Prompt-level duplication that makes tuning difficult to maintain

**Design Principles**

- `Soft guidance`, not hard enforcement
- `Trust over impressiveness`
- `Centralized policy`, reused by multiple generators
- `Content-type aware` guidance rather than one-size-fits-all instructions
- `Low-friction adoption` in the existing pipeline
- `Human override` always allowed

## Scope

This guidance layer should apply to:

- Résumé summary / bio
- Experience bullets
- Project bullets
- Cover letters
- AI-generated job analysis outputs

This first version does not include automatic rejection or blocking. It only guides generation. Validation can be added later if needed.

## Proposed Structure

Use one centralized configuration file:

- `assets/language_guidance.yaml`

This file should contain four sections:

1. `global_tone`
2. `content_types`
3. `verb_architecture`
4. `anti_patterns`

### 1. Global Tone

Defines cross-output language preferences.

Required qualities:

- Calm
- Credible
- Specific
- Engineering-first
- Moderately concise

Discouraged qualities:

- Salesy
- Inflated
- Over-clever
- Self-congratulatory
- Keyword-stuffed

Priority order:

- Trust
- Clarity
- Relevance
- Sharpness

### 2. Content-Type Guidance

Each output type gets its own style rules.

#### `resume_summary`

Purpose:

- Establish target role quickly
- Anchor strongest factual differentiators
- Keep supporting context subordinate

Guidance:

- 2 to 3 sentences maximum
- Lead with role and domain fit
- Mention academic background only as supporting context
- Avoid abstract self-description such as “deep thinker” or “first-principles”

#### `experience_bullet`

Purpose:

- Show ownership, implementation depth, and production relevance

Guidance:

- Prefer 1 action per bullet
- Use strong but factual verbs
- Emphasize systems, data movement, controls, and downstream use
- Avoid stacking too many claims in one sentence
- Within a role, vary bullet function:
  - ownership / scope
  - implementation
  - controls / optimization / enablement

#### `project_bullet`

Purpose:

- Show current technical depth without sounding like portfolio theater

Guidance:

- Describe implemented mechanisms, not perfect outcomes
- Prefer concrete engineering nouns over promotional claims
- Avoid absolute claims such as `zero data loss`, `100% automated recovery`, unless explicitly verified and worth the risk

#### `cover_letter`

Purpose:

- Connect candidate fit to role needs in a natural tone

Guidance:

- Slightly warmer than résumé language
- Still restrained and factual
- Avoid buzzword stacking
- Reuse the same action hierarchy as résumé bullets

#### `analysis_output`

Purpose:

- Support decision quality in the pipeline

Guidance:

- Direct and diagnostic
- Prioritize signal over polish
- Short sentences preferred
- Avoid decorative language entirely

### 3. Verb Architecture

The guidance layer should map action types to preferred verb pools.

This is not a hard replacement table. It is a preference system.

#### Ownership / platform scope

Use for:

- Foundational platform creation
- End-to-end ownership
- New system establishment

Preferred verbs:

- `Built`
- `Established`
- `Created`

Usage note:

- Keep `Built` rare
- Prefer 1 to 3 uses per résumé page
- Reserve for the highest-value scope statements

#### Data layer / pipeline implementation

Use for:

- ETL / ELT
- Data pipelines
- Streaming jobs
- Core data model implementation

Preferred verbs:

- `Developed`
- `Engineered`
- `Implemented`

Usage note:

- Avoid overusing any one of these in adjacent bullets

#### Controls / mechanisms / quality logic

Use for:

- Validation
- Data quality checks
- Replay / quarantine logic
- Rules engines

Preferred verbs:

- `Implemented`
- `Introduced`
- `Designed`

#### Optimization

Use for:

- Query tuning
- Runtime / scan reduction
- Efficiency improvements

Preferred verbs:

- `Optimized`
- `Improved`
- `Reduced`

#### Enablement / downstream support

Use for:

- Supporting analysts, risk teams, or downstream consumers

Preferred verbs:

- `Enabled`
- `Supported`
- `Provided`

Usage note:

- Often better placed in the second half of a bullet rather than as the opening verb

### 4. Anti-Patterns

The first version should explicitly discourage:

- The same opening verb repeated across many bullets
- Abstract self-branding
- Perfect-outcome language without evidence
- Decorative architecture words without operational detail
- Summary statements that compete with experience for attention

## Recommended Distribution Heuristics

For résumé bullets, guidance should encourage:

- No single opening verb used more than 3 times on one page when alternatives fit
- No repeated opening verb in adjacent bullets within the same role when avoidable
- One role should usually show a sequence like:
  - scope / ownership
  - implementation
  - controls / optimization / enablement

These are heuristics, not constraints.

## Integration Plan

### Phase 1

Use the guidance file as shared prompt context in:

- `src/ai_analyzer.py`
- `src/cover_letter_generator.py`
- résumé generation logic tied to resume tailoring

### Phase 2

Apply content-type slices depending on output being generated.

Examples:

- Résumé summary uses `resume_summary`
- Experience bullets use `experience_bullet`
- Cover letters use `cover_letter`

### Phase 3

Optional future validator:

- warn on verb overuse
- warn on anti-pattern phrases
- warn on tone drift

This validator should start as advisory only.

## Risks

- Too much guidance can flatten style if prompts become overly prescriptive
- Verb diversity can become artificial if pursued mechanically
- Some roles may legitimately need repeated verbs when the work is highly homogeneous

Mitigations:

- Keep guidance preference-based
- Preserve explicit override paths
- Test on multiple existing résumé versions before wider rollout

## Success Criteria

The guidance layer is successful if:

- résumé bullets show lower verb repetition
- cover letters and résumé feel like the same candidate voice
- analysis outputs become cleaner and less ornamental
- prompt maintenance becomes easier because language policy lives in one place

