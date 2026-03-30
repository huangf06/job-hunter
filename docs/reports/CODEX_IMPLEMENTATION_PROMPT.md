# Implementation Task: Three-Tier Resume Strategy

## What to build

Implement the three-tier resume strategy described in two design documents:
- **Parent design:** `docs/plans/2026-03-29-resume-strategy-redesign.md` — the overall architecture (three tiers, template registry, C1 routing, C2 dual-mode, C3 gate)
- **v2 addendum (rev4):** `docs/plans/2026-03-29-resume-strategy-v2-addendum.md` — the implementation-ready spec with DB state model, routing contract, slot schema, C3 inputs, and safeguard

The addendum is authoritative wherever it differs from the parent. Read both documents fully before starting.

## Branch

Create a new branch `feat/three-tier-resume` off `master`.

## Implementation sequence

Follow the 15-step task sequence in the addendum's "Implementation Task Sequence" section. The order is dependency-aware — do not reorder. Here is a summary with pointers to the relevant spec sections:

### Step 1: Migration order fix
- **What:** Reorder `_init_db()` in `src/db/job_db.py` so `_migrate()` runs BEFORE view creation (currently: tables → views → migrate; must become: tables → migrate → views)
- **Why:** New views will reference columns that don't exist until `_migrate()` adds them
- **Spec:** Addendum P0-1, migration strategy note
- **Test:** Existing tests still pass; `_init_db()` on a fresh DB works; `_init_db()` on an existing DB (without new columns) works

### Step 2: Schema migration
- **What:** Add 10 new nullable columns to `job_analysis` in `_migrate()`. Extend `AnalysisResult` dataclass with 10 new fields. Extend `save_analysis()` INSERT to include all 21 columns.
- **Spec:** Addendum P0-1 (column definitions + AnalysisResult extension + save_analysis SQL)
- **Test:** Write a test that creates an AnalysisResult with routing fields, saves it, reads it back, verifies all fields round-trip. Also test that legacy AnalysisResult (no routing fields) saves with NULLs.

### Step 3: Query updates
- **What:** Update ALL 15 affected queries/methods listed in the addendum's "Affected queries — exhaustive list" table
- **Spec:** Addendum P0-1 (the table with 15 rows)
- **Key queries:**
  - `get_jobs_needing_tailor()` — exclude USE_TEMPLATE rows
  - `clear_rejected_analyses()` — only delete `resume_tier IS NULL` rows
  - `clear_transient_failures()` — only delete `resume_tier IS NULL` rows
  - `get_analyzed_jobs_for_resume()` — replace with tier-aware query from addendum
  - `get_jobs_needing_cover_letter()` — include USE_TEMPLATE and ADAPT_TEMPLATE+FAIL
  - `v_high_score_jobs` view — include USE_TEMPLATE
  - `get_funnel_stats()` — add tier counters
  - `update_analysis_resume()` — add optional c3 params
  - CLI previews in `ai_analyzer.py` and `job_pipeline.py` — branch on `resume_tier`
  - `notify.py` and `pipeline_gaps.py` — add tier-aware filters
- **Test:** For each modified query, write a test with fixture data for each tier (USE_TEMPLATE, ADAPT_TEMPLATE+PASS, ADAPT_TEMPLATE+FAIL, FULL_CUSTOMIZE, legacy NULL) and verify correct inclusion/exclusion.

### Step 4: Template registry
- **What:** Create `config/template_registry.yaml` with DE and ML templates (Backend `enabled: false`). Include full `slot_schema` for each template (bio, experience entries with bullets, skills categories, all with slot IDs and default text).
- **Spec:** Addendum P0-3 (registry extension YAML). The `default` text for each slot must match the actual content of your existing SVG templates — read `templates/Fei_Huang_DE_Resume.svg` and `templates/Fei_Huang_ML_Resume.svg` to extract the real text.
- **Also:** Add a `load_registry()` utility function in a new `src/template_registry.py` module.
- **Test:** Test that registry loads, all slot IDs are unique per template, all required fields present.

### Step 5: Deterministic selector
- **What:** Implement `select_template()` returning `RoutingDecision(template_id, confidence, matched_keywords, ambiguous)` in `src/template_registry.py`
- **Spec:** Addendum P0-2 (Phase 1 code)
- **Test:** Test exact match ("Data Engineer" → DE, 0.9), ambiguous match ("ML Platform Engineer" → ambiguous, 0.5), no match (→ DE default, 0.3), disabled template skipped.

### Step 6: C1 prompt extension
- **What:** Add routing instructions to the C1 evaluator prompt in `config/ai_config.yaml`. C1 output must now include `resume_routing` object with: `tier`, `template_id`, `override`, `override_reason`, `gaps`, `adapt_instructions`.
- **Spec:** Addendum P0-2 (Phase 2 prompt) + parent design (C1 Prompt Extension section)
- **Also:** Update `evaluate_job()` in `src/ai_analyzer.py` to: (a) run `select_template()` before calling C1, (b) inject pre-selected template info into prompt, (c) parse `resume_routing` from C1 response, (d) call `resolve_routing()`, (e) call `apply_tier1_safeguard()`, (f) persist all routing fields in AnalysisResult.
- **Test:** Mock C1 response with routing output, verify routing fields are correctly resolved and persisted. Test override=true vs override=false precedence.

### Step 7: Routing resolver + safeguard
- **What:** Implement `resolve_routing()` and `apply_tier1_safeguard()` in `src/template_registry.py`
- **Spec:** Addendum P0-2 (resolve_routing code) + P0-5 (safeguard code)
- **Key rules:**
  - `routing_confidence` always stores code selector confidence, never AI confidence
  - Safeguard keys off `code_decision.confidence`, not the merged result
  - `escalation_reason` is separate from `routing_override_reason`
- **Test:** Test all scenarios in the safeguard table (high confidence pass-through, ambiguous escalation, no-match escalation, C1-chose-Tier2-no-safeguard).

### Step 8: Single-job flow
- **What:** Update `analyze_job()` in `src/ai_analyzer.py` to implement the single-job flow contract
- **Spec:** Addendum P0-1 "Single-job vs batch flow contract" (pseudocode)
- **Flow:** C1 → route in-memory → conditional C2 → conditional C3 → single atomic `save_analysis()` → conditional `insert_resume()` for USE_TEMPLATE
- **Test:** Test all three tier paths through `analyze_job()` with mocked AI responses.

### Step 9: Cover letter tier adapter
- **What:** Add `get_resume_context_for_cl(job_analysis_row, registry)` to `src/cover_letter_generator.py` that branches on `resume_tier` and returns normalized context string
- **Spec:** Addendum P1-d (tier-to-context table)
- **Update:** All call sites that currently inject raw `tailored_resume` into CL prompts must use this adapter instead
- **Test:** Test each tier returns appropriate context shape.

### Step 10: C2 Tier 2 mode
- **What:** Add a second C2 prompt mode for ADAPT_TEMPLATE in `config/ai_config.yaml` and `src/ai_analyzer.py`
- **Spec:** Addendum P0-3 (C2 output contract) + parent design (C2 Redesign: Two Modes)
- **Input:** adapt_instructions + gaps from routing_payload + template HTML content from registry
- **Output:** `{slot_overrides, skills_override, entry_visibility, change_summary}`
- **Validation:** `validate_tier2_output()` checks all slot IDs against registry schema
- **Also:** Update `tailor_resume()` / `tailor_batch()` to branch: ADAPT_TEMPLATE uses short Tier 2 prompt (no bullet library), FULL_CUSTOMIZE uses existing full prompt
- **Test:** Mock C2 Tier 2 response, validate output, test validation rejects unknown slot IDs.

### Step 11: C3 structured gate
- **What:** Implement `build_c3_input()` and `run_c3_gate()` in `src/ai_analyzer.py`
- **Spec:** Addendum P0-4 (build_c3_input code + C3 prompt)
- **Key:** C3 input is code-built from actual template defaults vs C2 overrides. Change density counts bio + bullets + skills + entries (denominator = all changeable items from schema).
- **Test:** Test build_c3_input produces correct diff. Test density calculation with various override combinations.

### Step 12: Renderer update
- **What:** Update `src/resume_renderer.py` to support three rendering paths
- **Spec:** Addendum P0-3 (renderer contract) + parent design (Tier 2 HTML Template Design)
- **Paths:**
  - USE_TEMPLATE (or ADAPT_TEMPLATE+FAIL): copy template PDF from registry path to output
  - ADAPT_TEMPLATE+PASS: load `adapt_{tid}.html`, merge slot schema with C2 overrides, render HTML→PDF
  - FULL_CUSTOMIZE: render via `customize_template.html` (or existing `base_template.html` until new template is built)
  - Legacy (NULL): existing behavior unchanged
- **Also:** Create `templates/adapt_de.html` and `templates/adapt_ml.html` as HTML faithful clones of the SVG templates, with Jinja2 slots at override positions
- **Test:** Test each rendering path produces a file. Test that USE_TEMPLATE output is byte-identical to the source PDF.

### Step 13: Tier 1 resumes record
- **What:** After C1 routing produces USE_TEMPLATE, create a `resumes` table row with `pdf_path` pointing to the template PDF
- **Spec:** Addendum P1-f
- **Where:** In both `evaluate_batch()` (batch flow) and `analyze_job()` (single-job flow, already added in step 8)
- **Test:** After routing a USE_TEMPLATE job, verify resumes row exists with correct pdf_path.

### Step 14: --template-stats command
- **What:** Add `--template-stats` CLI flag to `scripts/job_pipeline.py`
- **Spec:** Addendum P1-e (sample output format)
- **Output:** Tier distribution, routing agreement/overrides/escalations, template usage, C3 calibration
- **Test:** Test with fixture data produces expected counts.

### Step 15: Legacy compat verification
- **What:** End-to-end verification that legacy rows (resume_tier IS NULL) still work in ALL paths: --ai-tailor, --prepare, --finalize, --stats, --ready, cover letter generation, rendering
- **Test:** Create legacy fixture data (old-format job_analysis rows without routing columns), run each command, verify no errors.

## Testing strategy

- Write tests BEFORE implementation (TDD) where practical
- Each step should have its own test file or test class
- Use the existing test infrastructure (see `tests/` directory)
- Mock AI API calls; test the parsing, routing, and rendering logic
- For step 15 (legacy compat), run existing tests to verify no regression

## Key constraints

1. **Legacy rows must never break.** `resume_tier IS NULL` = old pipeline, always works.
2. **No TIER_1/TIER_2/TIER_3 enum.** Use `USE_TEMPLATE`/`ADAPT_TEMPLATE`/`FULL_CUSTOMIZE` everywhere.
3. **routing_confidence = code selector confidence only.** Never store AI-reported confidence there.
4. **escalation_reason and routing_override_reason are separate columns.** Don't conflate.
5. **Tier 2 FAIL preserves tailored_resume** for debug. `c3_decision='FAIL'` is the authoritative signal; don't reset to `'{}'`.
6. **Every consumer of tailored_resume must branch on resume_tier.** See the polymorphism contract table in the addendum.
7. **_migrate() must run before view creation** in `_init_db()`.

## Files you will modify

- `src/db/job_db.py` — schema, migration, queries, AnalysisResult, save_analysis
- `src/ai_analyzer.py` — C1 routing, C2 dual-mode, C3 gate, analyze_job flow
- `src/resume_renderer.py` — three-path rendering
- `src/cover_letter_generator.py` — tier adapter
- `scripts/job_pipeline.py` — CLI preview, --template-stats
- `scripts/notify.py` — tier-aware stats query
- `scripts/pipeline_gaps.py` — tier-aware gap queries
- `config/ai_config.yaml` — C1 routing prompt, C2 Tier 2 prompt, C3 prompt

## Files you will create

- `src/template_registry.py` — registry loader, select_template, resolve_routing, safeguard
- `config/template_registry.yaml` — template metadata + slot schemas
- `templates/adapt_de.html` — DE template HTML clone with Jinja2 slots
- `templates/adapt_ml.html` — ML template HTML clone with Jinja2 slots
- Test files for each step

## Reference files (read but don't modify unless specified)

- `templates/Fei_Huang_DE_Resume.svg` — source for DE slot defaults and adapt_de.html
- `templates/Fei_Huang_ML_Resume.svg` — source for ML slot defaults and adapt_ml.html
- `templates/base_template.html` — current renderer template (legacy path keeps using it)
- `assets/bullet_library.yaml` — used by FULL_CUSTOMIZE C2 prompt (unchanged)

## Commit strategy

One commit per step. Commit message format: `feat(three-tier): step N — description`

After all 15 steps, open a PR to master with a summary of changes.
