# Block B+C Redesign — Work Report

**Date:** 2026-03-28
**Branch:** `feat/block-bc-redesign` (pushed to origin)
**Base:** `master` @ `a41058c`
**Status:** All tasks complete, Codex reviewed, e2e verified. **Ready to merge.**

---

## Summary

Block B (hard filter) simplified from complex 3-layer reject logic to whitelist-only.
Block C (AI analysis) split into C1 (evaluate) + C2 (tailor), Anthropic SDK removed.
11 planned tasks + 1 Codex review fix commit = 11 total commits.

**Stats:** 11 files changed, +946 / -807 lines. 127 tests pass (1 skipped).

---

## Commits

| # | Hash | Message |
|---|------|---------|
| 1 | `9d01bca` | feat(block-b): simplify filters.yaml to whitelist-only design |
| 2 | `60a21df` | feat(block-b): simplify hard_filter.py to match whitelist-only design |
| 3 | `f879a02` | test(block-b): rewrite tests for whitelist-only design |
| 4 | `95c4b39` | chore: remove SDK model configs, budget tracking, --model CLI flag |
| 5 | `3da7839` | refactor(block-c): remove Anthropic SDK, keep Claude Code CLI only |
| 6 | `a454fe0` | feat(block-c): split AI into C1 (evaluate) + C2 (tailor) |
| 7 | `6eb9b77` | feat(cli): add --ai-evaluate and --ai-tailor commands |
| 8 | `27dc29a` | ci: split AI step into C1 (evaluate) + C2 (tailor) |
| 9 | `1e0099d` | docs: update architecture doc and CLAUDE.md for B+C redesign |
| 10 | `0f11a6f` | test(block-c): add C1/C2 response parsing and DB workflow tests |
| 11 | `c734189` | fix: address Codex review — broken --analyze-job, retry matching, threshold config |

---

## What Changed

### Block B — Hard Filter (Tasks 1-3)

| Before | After |
|--------|-------|
| `non_target_role`: 3-layer (hard reject patterns, soft reject + exceptions, whitelist) | Whitelist-only — title must contain 1 of 27 target keywords |
| `wrong_tech_stack`: title patterns + body keyword counting | Title patterns only |
| 8+ rules including `specific_tech_experience`, `location_restricted`, `experience_too_high` | 6 rules remaining (semantic judgment moved to AI) |

**Files:** `config/base/filters.yaml`, `src/hard_filter.py`, `tests/test_hard_filter.py`

### Block C — AI Analysis (Tasks 4-8)

| Before | After |
|--------|-------|
| Single `analyze_job()` call (scoring + resume in one prompt) | C1 `evaluate_job()` + C2 `tailor_resume()` |
| Anthropic SDK + Claude Code CLI dual path | Claude Code CLI only (`claude -p`) |
| Cover Letter (free-form text) | Application Brief (structured JSON: hook, key_angle, gap_mitigation, company_connection) |
| All jobs get full prompt with bullet library | C1: short prompt (no bullets), C2: full prompt (only for score >= 4.0) |

**New CLI commands:**
- `--ai-evaluate` — C1 only (scoring + brief)
- `--ai-tailor` — C2 only (resume tailoring)
- `--ai-analyze` — C1 + C2 sequential (backward compat)
- `--analyze-job ID` — single job C1+C2

**New DB methods:**
- `update_analysis_resume(job_id, tailored_resume)` — C2 writes to C1's row
- `get_jobs_needing_tailor(min_score, limit)` — find C1-evaluated but not yet tailored

**Files:** `src/ai_analyzer.py`, `src/db/job_db.py`, `config/ai_config.yaml`, `scripts/job_pipeline.py`, `.github/workflows/job-pipeline-optimized.yml`

### Docs & Tests (Tasks 9-10)

- Architecture doc updated for whitelist-only + C1/C2 design
- CLAUDE.md updated with new commands
- 13 new tests in `tests/test_ai_analyzer.py` (C1/C2 parse + DB workflow)

---

## Codex Review (Task 11)

External review by Codex found 1 P0, 1 P1, 2 P2 issues. All fixed in commit `c734189`:

| Priority | Issue | Fix |
|----------|-------|-----|
| **P0** | `--analyze-job` broken — `_build_prompt()` references deleted `prompts.analyzer` | Rewrote `analyze_job()` to use C1+C2 flow; deleted dead `_build_prompt()` |
| **P1** | `--retry-failures` doesn't match new error string `'Claude Code CLI returned empty response'` | Added new LIKE pattern to `clear_transient_failures()` |
| **P2** | C2 threshold 4.0 hardcoded in 4 places | Now reads from `config.thresholds.ai_score_generate_resume` |
| **P2** | CLI help missing `--ai-evaluate` / `--ai-tailor` | Updated help text |

---

## E2E Verification

Tested against real production database with live Claude Code CLI calls:

| Command | Result |
|---------|--------|
| `--analyze-job b9925da58d27` | C1: 7.5 APPLY_NOW, C2: 3 experiences tailored (Big Data Engineer @ Swisscom) |
| `--ai-evaluate --limit 1` | C1: 4.5 MAYBE (Quantitative Developer @ Zanders) |
| `--ai-tailor --limit 1` | C2: tailored a previously evaluated job successfully |

---

## Test Results

```
127 passed, 1 skipped in 8.10s
```

- `tests/test_hard_filter.py`: 61 tests (whitelist-only + title patterns)
- `tests/test_ai_analyzer.py`: 13 tests (C1/C2 parse + DB workflow)
- All other test files: unchanged, still passing

---

## Next Step

**Merge to master.** Three options:

1. **Merge locally:** `git checkout master && git merge feat/block-bc-redesign`
2. **Create PR:** `git push -u origin feat/block-bc-redesign && gh pr create`
3. **Keep as-is:** branch is pushed, resume later

Branch is already pushed to `origin/feat/block-bc-redesign`.

---

## Design References

- Design doc: `docs/plans/2026-03-28-block-bc-unified-design.md`
- Implementation plan: `docs/plans/2026-03-28-block-bc-implementation.md`
- Architecture: `docs/plans/2026-03-27-pipeline-block-architecture.md`
