# Codex Execution Prompt: Block D Resume Renderer Implementation

## Your Role

You are implementing the Block D (Resume Renderer) redesign. The design is approved and the implementation plan is written. Your job is to execute the plan task-by-task, commit after each task, and verify tests pass.

## Context

- **Implementation plan**: `docs/plans/2026-03-30-block-d-implementation.md` (9 tasks)
- **Design doc**: `docs/plans/2026-03-30-block-d-render-design.md` (Approved, Codex v2)
- **What this does**: 6 targeted changes to an existing 655-line `resume_renderer.py`. No structural redesign. Removes ~95 lines of redundant code, adds ~20 lines of defensive guards, merges 2 duplicate templates into 1, expands tests from 3 to 15, fixes a missing CI step.

## Key Files

| File | Role | Action |
|------|------|--------|
| `src/resume_renderer.py` (655 lines) | Main renderer | Modify: delete 2 methods, add guards, dedup paths |
| `tests/test_resume_renderer_tiers.py` (171 lines) | Tier tests | Modify: add 12 new tests |
| `.github/workflows/job-pipeline-optimized.yml` | CI workflow | Modify: add `--generate` step |
| `templates/adapt_de.html` (~80 lines) | DE adapt template | Delete |
| `templates/adapt_ml.html` (~80 lines) | ML adapt template | Delete |
| `templates/adapt_template.html` | Unified adapt template | Create (from adapt_de.html, change `<title>`) |
| `config/template_registry.yaml` (217 lines) | Template metadata | Modify: remove `adapt_html` lines |
| `src/resume_validator.py` | Validator | **DO NOT TOUCH** |
| `src/template_registry.py` | Template routing | **DO NOT TOUCH** |
| `templates/base_template.html` | Full customize template | **DO NOT TOUCH** |

## Environment

- **Platform**: Windows 11, bash shell
- **Python**: 3.12
- **Test command**: `NO_TURSO=1 python -m pytest <path> -v`
- **Encoding**: Use `PYTHONIOENCODING=utf-8` for any `scripts/job_pipeline.py` commands
- **Local DB only**: Set `NO_TURSO=1` for all commands — do NOT use Turso cloud DB

## Pre-flight

Before starting any task, verify existing tests pass:

```bash
NO_TURSO=1 python -m pytest tests/test_resume_renderer_tiers.py tests/test_template_registry.py tests/test_ai_analyzer.py -v
```

Expected: all pass (41+ tests). **If not, stop and report.**

## Execution Order

Execute these 9 tasks in order. Each task has explicit steps in the implementation plan. Follow them exactly.

### Task 1: Write 4 defensive guard tests (failing)
- Append 4 test functions to `tests/test_resume_renderer_tiers.py`
- Tests: unknown template (copy path), unknown template (adapt path), invalid JSON, missing slot_schema
- Run to verify they FAIL (expected: KeyError or JSONDecodeError)
- Commit: `test(block-d): add defensive guard tests (expected to fail)`

### Task 2: Write 8 routing/behavior tests
- Append 8 test functions to `tests/test_resume_renderer_tiers.py`
- Tests: c3 FAIL routing, legacy NULL tier, validator still runs, QA blocking, role_type from template_id, adapt template title variable, mixed-tier batch, (output paths is implicit)
- Some will fail (guard tests from T1, role_type test, adapt_template.html test) — that's expected
- Commit: `test(block-d): add routing, validator, QA, and batch tests`

### Task 3: CI workflow — add `--generate` step
- In `.github/workflows/job-pipeline-optimized.yml`, insert generate step between ai-tailor and notification
- Add failure detection line in notification step
- **Important**: Find the exact location — look for the ai-tailor step and the notification step, insert between them
- Commit: `ci(block-d): add --generate step between C2 and notification`

### Task 4: Merge adapt templates
- Create `templates/adapt_template.html` from `adapt_de.html`, change `<title>` to `{{ template_title | default("Adapted Resume") }}`
- Delete `templates/adapt_de.html` and `templates/adapt_ml.html`
- Remove `adapt_html` lines from `config/template_registry.yaml` (3 lines: DE, ML, Backend sections)
- Update `_render_adapt_template()` in `src/resume_renderer.py`: load unified template, pass `template_title`
- Run adapt tests to verify
- Commit: `refactor(block-d): merge adapt_de/ml into single adapt_template.html`

### Task 5: Eliminate output path duplication
- In `render_resume()`, replace the inline path generation block (lines 212-235) with a call to `self._build_output_paths(job)`
- The 4 variables (`html_path`, `pdf_path`, `submit_pdf_path`, `submit_dir`) must still be assigned
- Run FULL_CUSTOMIZE test to verify
- Commit: `refactor(block-d): use _build_output_paths() in FULL_CUSTOMIZE path`

### Task 6: Delete `_validate_tailored_structure()`
- Remove the call in `render_resume()` (lines 150-156)
- Delete the entire method definition (lines 427-485)
- **DO NOT delete `self.validator.validate()` or `_post_render_qa()`** — those stay
- Run validator-still-runs test to verify
- Commit: `refactor(block-d): remove redundant _validate_tailored_structure()`

### Task 7: Delete `_detect_role_type()`
- In the `save_resume()` call within FULL_CUSTOMIZE path, change `role_type=self._detect_role_type(job)` to `role_type=analysis.get('template_id_final') or 'general'`
- Delete the entire `_detect_role_type()` method
- Run role_type test to verify
- Commit: `refactor(block-d): replace _detect_role_type() with template_id_final`

### Task 8: Add defensive guards
- Guard `_render_template_copy()`: replace direct dict access with `.get()` + None check
- Guard `_render_adapt_template()`: same + try/except for `json.loads()` + `slot_schema` check
- Run all 4 guard tests from Task 1 — they should now PASS
- Run full test suite
- Commit: `fix(block-d): add defensive guards to template_copy and adapt_template`

### Task 9: Full verification
- Run `NO_TURSO=1 python -m pytest tests/ -v --tb=short` — expect ~182 passed
- Run `wc -l src/resume_renderer.py` — expect ~560 lines
- Run `NO_TURSO=1 PYTHONIOENCODING=utf-8 python scripts/job_pipeline.py --template-stats`
- Commit: `verify(block-d): all tests pass, spot check successful`

## Critical Rules

1. **Read before editing**: Always read the current state of a file before modifying it. Line numbers in the plan are approximate — the file shifts as you make changes.
2. **One task at a time**: Complete and commit each task before moving to the next.
3. **Test after each change**: Run the specified test commands. If tests fail unexpectedly, investigate before proceeding.
4. **Do not touch files marked "DO NOT TOUCH"**: `resume_validator.py`, `template_registry.py`, `base_template.html`.
5. **Exact commit messages**: Use the commit messages specified in each task.
6. **No scope creep**: Do not add features, refactor code, or make improvements beyond what each task specifies.

## How to Report

After completing all 9 tasks, report:

```
## Block D Implementation Report

**Tasks completed**: N/9
**Final test results**: X passed, Y failed, Z skipped
**Line count**: resume_renderer.py = N lines (was 655)
**Commits made**: list each commit hash + message

**Issues encountered**: (if any)
**Deviations from plan**: (if any)
```
