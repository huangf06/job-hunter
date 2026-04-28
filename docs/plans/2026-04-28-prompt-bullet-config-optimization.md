# Prompt x Bullet Library x Config Optimization Design

**Date:** 2026-04-28
**Context:** v7.4 refactor completed (ai_config = system behavior, bullet_library = candidate content). This design addresses cross-cutting issues found during deep audit of the C1/C2 prompt pipeline.

## Changes

### 1. Remove artificial content limits from C2 prompt

**File:** `config/ai_config.yaml` (prompts.tailor)

Remove:
- "The resume MUST be exactly 2 pages"
- "Typical total: 8-12 bullets across all experiences"
- Bullet distribution guidance ("Most relevant: 2-4", "Second: 2-3", etc.)

Replace with quality-oriented soft guidance:
```
Include every bullet that strengthens the application for THIS specific role.
Exclude content that doesn't add signal. Quality and relevance over quantity.
```

Remove the `### BULLET DISTRIBUTION (GUIDANCE, NOT HARD LIMITS)` section entirely.

**Why:** Hard page/bullet limits force the AI to make arbitrary cuts. The resume renderer handles multi-page output. Let the AI optimize for interview conversion, not page count.

### 2. Consolidate title_options into work_experience

**Files:** `assets/bullet_library.yaml`, `src/ai_analyzer.py`

Delete the top-level `title_options` block (lines 543-564). Modify `_build_title_context()` to read from `work_experience[key].titles` instead.

Current (two sources):
```yaml
# In work_experience:
glp_technology:
  titles:
    default: "Senior Data Engineer"
    data_engineer: "Senior Data Engineer"
    data_scientist: "Senior Data Scientist"

# In title_options (DUPLICATE):
title_options:
  glp_technology:
    default: "Senior Data Engineer"
    data_engineer: "Senior Data Engineer"
    ...
```

After: only `work_experience[key].titles` exists. `_build_title_context()` iterates `work_experience` keys, `ResumeValidator._validate_titles()` reads from the same source.

### 3. Remove language guidance from C2 prompt

**File:** `src/ai_analyzer.py` (`_build_tailor_prompt`)

Remove line 750: `f"{language_guidance}\n\n{prompt_body}"` → just `prompt_body`.

C2 selects pre-written bullet IDs, not generates text. Language guidance (~400 tokens) has no effect on C2 output quality. Bio is structured spec (domain_claim IDs + closer_id), not freeform text.

### 4. Simplify C1 routing output

**File:** `config/ai_config.yaml` (prompts.evaluator)

Replace the entire "Resume Routing Decision" section and routing output schema with:

```yaml
## Resume Routing
Template hint: {preselected_template_id} (confidence: {preselected_confidence})
Template determines C2 role framing (DE/ML/DS) for bio, titles, project ordering.
If the pre-selected template is wrong for this role, override it.

## Output (JSON only, no markdown)
{{
  "scoring": {{ ... }},
  "application_brief": {{ ... }},
  "resume_routing": {{
    "template_id": "{preselected_template_id}",
    "override": false,
    "override_reason": null
  }}
}}
```

Remove: tier field (always FULL_CUSTOMIZE), gaps field (no consumer), adapt_instructions (retired).

Saves ~150 input tokens + ~50 output tokens per C1 call.

### 5. Keep C1 candidate profile hardcoded (decision: no change)

C1 is a lightweight scoring step that intentionally doesn't load bullet_library. The hardcoded candidate summary (lines 79-88) is acceptable. Review quarterly for drift.

### 6. Elevate C1 brief in C2 prompt

**File:** `config/ai_config.yaml` (prompts.tailor)

Move application brief from "context" to "task" position:

```yaml
## Your Task
**Strategic angle (from C1 evaluation):**
- Hook: {c1_hook}
- Key angle: {c1_key_angle}
- Gap to mitigate: {c1_gap_mitigation}

**Tailor the resume** to execute this angle:
```

Requires `_build_tailor_prompt()` to parse brief fields individually instead of passing as JSON blob.

Add fallback instruction: "If no application brief is available, infer the strongest angle from the JD and C1 score."

### 7. Add course selection to C2

**Files:** `assets/bullet_library.yaml`, `config/ai_config.yaml`, `src/ai_analyzer.py`, `src/resume_renderer.py`

Add courses as selectable items in the C2 prompt:

```
## COURSEWORK (select relevant courses)
Master's courses (all graded 9.0+):
  - [deep_learning] Deep Learning (9.5) — relevance: ml, dl, ai
  - [multi_agent_systems] Multi-Agent Systems (9.5) — relevance: ml, agents, distributed
  - [ml4qs] ML for Quantified Self (9.5) — relevance: ml, timeseries, iot
  - [data_mining] Data Mining (9.0) — relevance: data, ml, analytics
  - [nlp] Natural Language Processing (9.0) — relevance: nlp, ml, ai
```

C2 output adds:
```json
"selected_courses": ["deep_learning", "data_mining", "nlp"],
"show_bachelor_thesis": false
```

Renderer change: `_format_coursework()` filters by selected IDs.

### 8. Make career_note AI-controllable

**Files:** `config/ai_config.yaml`, `src/resume_renderer.py`

C2 output adds: `"show_career_note": true/false`

Instruction: "Set show_career_note to false if the 2019-2023 period is covered by an included experience (e.g., Independent Quantitative Researcher). Only set to true if there's a visible chronological gap."

Renderer: conditionally render career_note based on this flag.

### 9. Generate C2 candidate summary dynamically

**File:** `src/ai_analyzer.py` (`_build_tailor_prompt`)

Replace the hardcoded "Key Background" section (lines 168-179) with auto-generated summary from bullet_library data:
- education.master → degree + thesis title
- education.certification → cert
- work_experience → company + default title (for each active key)
- skill_tiers.verified.languages → core skills

~20 lines of Python. Eliminates drift between bullet_library and C2 prompt.

### 10. Trim domain_claims

**File:** `assets/bullet_library.yaml`

Merge 3 narrow claims into `data_pipelines`:
- `anomaly_detection` → absorbed (not an independent selling point)
- `streaming_data` → absorbed (sub-dimension of DE)
- `data_governance` → absorbed (too narrow)

Update `data_pipelines.text` to: "scalable data pipelines and data platform engineering"

Result: 10 domain_claims (from 13). Each maps to a distinct role archetype.

## Not Changing

- **C1 hard reject signals** — defense-in-depth with Block B hard filter, catches nuanced cases
- **Bio structured spec** — clearly better than freeform (eliminates banned phrases, enforces years cap, handles staffing agencies)
- **Additional section (interests, languages)** — static is correct; career_note becomes AI-controllable per change #8
- **skill_tiers structure** — verified/transferable/excluded split is clean and well-integrated with validator

## Implementation Order

1. Changes 1, 3, 4 (prompt text edits only — zero code)
2. Changes 6, 9 (ai_analyzer.py prompt construction)
3. Changes 2, 10 (bullet_library.yaml structure + ai_analyzer.py readers)
4. Changes 7, 8 (new C2 output fields + renderer changes)
5. Update tests for all changes
