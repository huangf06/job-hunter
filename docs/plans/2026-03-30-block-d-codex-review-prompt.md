# Codex Review Prompt: Block D Resume Renderer Redesign

## Your Role

You are reviewing a design document for the Block D (Resume Renderer) audit+simplify redesign. The design is at `docs/plans/2026-03-30-block-d-render-design.md`.

## Context

This is a block-by-block pipeline rebuild project. Blocks A (Scrape), B (Hard Filter), and C (AI Evaluate+Tailor) are already completed and merged to master. Block D is the next block.

Block D is NOT a from-scratch rewrite. It's an audit+simplify of an existing 655-line `resume_renderer.py` that already has a working three-tier resume routing system (USE_TEMPLATE / ADAPT_TEMPLATE / FULL_CUSTOMIZE). The design proposes 6 targeted changes based on a line-by-line audit.

### Key files to cross-reference

- `src/resume_renderer.py` — the renderer being simplified (655 lines)
- `src/resume_validator.py` — the validator we're NOT changing (406 lines)
- `src/template_registry.py` — template routing we're NOT changing (120 lines)
- `templates/adapt_de.html` and `templates/adapt_ml.html` — the duplicate templates being merged
- `config/template_registry.yaml` — template metadata + slot schemas
- `.github/workflows/job-pipeline-optimized.yml` — CI workflow missing `--generate`
- `tests/test_resume_renderer_tiers.py` — existing tier tests (3 tests)
- `tests/test_ai_analyzer.py` — tests showing ResumeValidator usage in ai_analyzer

## What to Review

### 1. Are the 7 audit findings accurate?

Cross-check each finding against the actual code:

- **#1 (CRITICAL)**: Is `--generate` truly missing from the CI workflow? Verify lines 143-148 of the workflow file.
- **#2 (HIGH)**: Does `_render_template_copy()` line 300 really have an unguarded `registry['templates'][template_id]`?
- **#3 (HIGH)**: Does `_render_adapt_template()` line 324 have the same issue?
- **#4 (MEDIUM)**: Are `adapt_de.html` and `adapt_ml.html` truly identical except `<title>`?
- **#5 (MEDIUM)**: Does `_validate_tailored_structure()` truly overlap with `ResumeValidator`? Is the claim that validator runs upstream (ai_analyzer lines 804, 1014) correct?
- **#6 (MEDIUM)**: Is the output path code truly duplicated between `render_resume()` main path and `_build_output_paths()`?
- **#7 (LOW)**: Is `_detect_role_type()` truly dead code given three-tier routing?

### 2. Are the 6 proposed changes safe?

For each change, evaluate:

- **Change 1 (CI `--generate`)**: Is the proposed YAML correct? Is `continue-on-error: true` the right policy? Should generate failure block notification?
- **Change 2 (merge adapt templates)**: Is it safe to remove per-template `adapt_html` from registry YAML? Does any code besides `_render_adapt_template()` reference this field?
- **Change 3 (output path dedup)**: Will the FULL_CUSTOMIZE path produce identical output when switched to `_build_output_paths()`? Are there any subtle differences between the two implementations?
- **Change 4 (delete `_validate_tailored_structure`)**: Is it truly safe to rely solely on upstream validation? What happens if someone calls `render_resume()` directly (not via pipeline)? Is there a defense-in-depth argument for keeping it?
- **Change 5 (delete `_detect_role_type`)**: Is `analysis.get('template_id_final') or 'general'` a correct replacement in all cases? What about legacy records where `template_id_final` is NULL?
- **Change 6 (defensive guards)**: Are the proposed guards sufficient? Any edge cases missed?

### 3. Are there missing concerns?

Things the design might have overlooked:

- Is `_post_render_qa()` still needed? Is it doing useful work or is it redundant with validator?
- The `_dedup_skills()` method — is it clean or should it be reviewed?
- The `_build_context()` method — any issues with bio handling (the dict-vs-string check at line 373)?
- Are there race conditions with the submit_dir sequence numbering (lines 226-230)?
- Does `render_batch()` handle mixed tiers correctly in a single batch?

### 4. Is the test plan adequate?

- Do the 6 proposed new tests cover all changed code paths?
- Are there missing negative test cases?
- Should there be an integration test that renders a real PDF (even if slow)?

## How to Review

1. Read the design document fully
2. Cross-reference each finding and change against the actual source files listed above
3. Pay special attention to Change 4 (removing validation) — this is the highest-risk change
4. Check for anything the audit missed that should be in scope

## Output Format

- **Verdict**: Approve / Approve with notes / Request revision
- For each of the 6 changes: **Safe / Risky + rationale**
- **Missing concerns**: List anything the design overlooked
- **Test plan**: Adequate / Needs additions
- **Implementation readiness**: Can a developer implement this without asking clarifying questions?
