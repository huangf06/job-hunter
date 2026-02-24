# Cover Letter Quality v2 — Micro-Story Anchored Generation

## Problem

Phase 0+1 (voice examples, knowledge base, anti-detection rules) improved CL quality but
the output still reads like a qualification checklist with better phrasing. Specific issues:

1. **All recent CLs are single-paragraph** — violates anti-detection rule about paragraph variation
2. **Opening formula repetitive** — "I'm applying for X because..." across all jobs
3. **Cross-job repetition** — "3,000+ securities" appears in multiple CLs
4. **No thinking shown** — CLs say what the candidate did, not how they think
5. **AI said "I don't have Power BI experience"** — candidate does have it; AI makes false gap claims

## Solution: Micro-Story Anchored Generation

Core insight: instead of "pick a narrative angle and fill with evidence IDs", use a real
micro-story as the anchor point and build the letter around it.

### Component 1: Micro-Stories in Knowledge Base

New fragment type `micro_story` in `cl_knowledge_base.yaml`:

```yaml
- id: glp_first_data_hire_chaos
  origin: handwritten
  type: micro_story
  role_types: [data_engineer, data_scientist]
  themes: [ownership, ambiguity, building_from_zero]
  text: >
    My first week at GLP, someone asked me where the data dictionary was.
    There wasn't one. There wasn't a pipeline either. I spent three months
    building both, and learned that the hardest part of data engineering
    isn't the engineering — it's deciding what to measure when nobody's
    thought about it yet.
```

Key fields:
- `themes`: new field for JD signal matching
- `origin: handwritten`: must be candidate-written
- Length: 2-4 sentences, one specific scene + one insight

Target: 6-10 micro-stories covering themes:
- `ownership` / `building_from_zero` — GLP first hire experience
- `data_quality` — discovering upstream data issues
- `cross_team` — business asking for one metric, needing another
- `scale` — Baiquan 3000+ securities specific challenge
- `learning` / `domain_transfer` — career transitions, "aha" moments
- `production_mindset` — system in production, unexpected lesson

### Component 2: Theme-Based Matching

JD text → theme signal extraction → micro-story selection:

| Theme | JD Signal Words |
|-------|----------------|
| `ownership` | end-to-end, full ownership, first hire, build from scratch |
| `data_quality` | data quality, validation, reliability, trust, governance |
| `scale` | scale, growth, high-volume, millions, performance |
| `cross_team` | stakeholder, cross-functional, collaborate, business |
| `ambiguity` | fast-paced, startup, undefined, greenfield |
| `production_mindset` | production, monitoring, SLA, reliability, on-call |
| `learning` | new domain, diverse, curious, adapt, fast learner |

Logic: JD contains signal word → corresponding theme scores +1 → select micro-story
with highest matching theme score. Fallback to generic story if no match.

### Component 3: Prompt Rewrite

**Remove**: narrative_angle / hook_type / closer_type mechanical selection from JSON output.

**New core instruction**:
```
Your task is NOT to write a cover letter. Your task is to answer in 150-250 words:
"Why would this person be interested in this role, and how do they think?"

Method:
1. Pick the most relevant Micro-Story as your anchor point
2. Use that specific experience to naturally connect to this role
3. At most 2-3 technical details as evidence, don't pile them up
4. End with a genuine curiosity or thought, not "looking forward to interviewing"
```

**Output format change**:
- standard: 2-3 paragraphs, 150-250 words, paragraph lengths MUST differ
- short: 1 paragraph, 100-150 words, same anchor but compressed
- Keep evidence_ids for validation (but not the writing driver)
- Remove narrative_angle, opening_hook, closer_type from JSON spec
- Add `micro_story_id` to track which story was used

**Retained constraints**:
- All anti-detection rules
- All banned phrases
- evidence_ids validation against bullet_library
- Rule #11: never claim candidate lacks a skill

### Component 4: Validation Updates

- Validate `micro_story_id` exists in knowledge base
- Validate standard has 2-3 paragraphs (not 1)
- Validate word count 150-250 for standard
- Validate paragraph lengths differ by at least 20%

## Files Changed

- `assets/cl_knowledge_base.yaml` — Add micro_story fragments (candidate writes these)
- `src/cover_letter_generator.py` — Rewrite `_build_prompt()`, update `_select_relevant_fragments()`
  to support theme matching, update `_validate_spec()`, simplify JSON output schema
- `assets/cover_letter_config.yaml` — Add theme_signals config, remove narrative_angles/hooks/closers
  (or keep as optional fallback)

## What Does NOT Change

- `--prepare` flow — still fully automated
- `cover_letter_renderer.py` — no changes (reads standard paragraphs from spec)
- DB schema — no changes
- Resume generation — no changes
- Voice examples — kept as style reference
- Existing knowledge base fragments — kept, micro-stories are additive

## Dependencies

- **Candidate must write 6-10 micro-stories** before implementation can start
- Template provided to help structure them quickly
