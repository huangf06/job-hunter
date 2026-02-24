# Cover Letter Quality Improvement — Phase 0+1 Design

## Problem

AI-generated cover letters are detectable by experienced recruiters (Jorrit/ENPICOM incident).
Root causes: uniform structure, JD-only company knowledge, absence of genuine human signals,
lack of candidate's authentic voice.

## Solution: Seed & Amplify Architecture

Instead of making AI write like a human, inject genuinely human content and let AI amplify it.

### Phase 0: Prompt Improvement (zero extra effort per job)

Changes to `cover_letter_generator.py` `_build_prompt()`:

1. **Voice examples** — Load `assets/voice_examples/*.txt`, inject as few-shot style reference
2. **Knowledge base fragments** — Load `assets/cl_knowledge_base.yaml`, inject relevant fragments
   filtered by role_type match against the job's AI analysis
3. **Anti-detection structural rules** — Ban AI-typical patterns (uniform paragraphs, "Furthermore",
   balanced constructions, etc.)
4. **Visa context** — Standard background about Zoekjaar → Kennismigrant transition
5. **Selective depth** — Instruct AI to focus on 2-3 JD requirements deeply, not all shallowly

### Phase 1: Knowledge Base Bootstrap

Create `assets/cl_knowledge_base.yaml` with fragments extracted from:
- Picnic CL (handwritten)
- Eneco CL (handwritten)
- Voice examples (voice_example origin)

Fragment types: company_observation, company_connection, personal_why, career_narrative,
philosophical_insight, honest_limitation, genuine_curiosity, growth_motivation, visa_context,
education_narrative

Each fragment tagged with: id, source_company, origin (handwritten/ai_edited/voice_example),
type, role_types, text.

## Files Changed

- `src/cover_letter_generator.py` — New methods: `_load_voice_examples()`,
  `_load_knowledge_base()`, `_select_relevant_fragments()`. Rewritten `_build_prompt()`.
- `assets/cl_knowledge_base.yaml` — New file, bootstrapped fragments
- `assets/cover_letter_config.yaml` — Add anti-detection rules section
- `assets/voice_examples/` — Already created (2 examples)

## What Does NOT Change

- `--prepare` flow unchanged — still fully automated
- `cover_letter_renderer.py` — no changes
- DB schema — no changes
- Resume generation — no changes
