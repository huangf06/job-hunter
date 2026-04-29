# Portfolio Public Readiness Handoff

> Created: 2026-04-29
> Branch: `portfolio-public-cleanup`
> Status: Paused by user before sensitive files were removed from git tracking.

## Goal

Turn the current personal production workspace into a GitHub portfolio project that is safe to publish, easy to understand, and reproducible without private credentials or personal job-search data.

## Current State

- Test baseline before cleanup: `pytest -q` completed with `227 passed, 1 warning`.
- Current branch was created from `master`: `portfolio-public-cleanup`.
- Existing user work was already present before cleanup and must be preserved:
  - `.env.example`
  - `.github/workflows/job-pipeline.yml`
  - `config/ai_config.yaml`
  - `requirements.txt`
  - `src/ai_analyzer.py`
  - `src/cover_letter_generator.py`
  - `tests/test_ai_analyzer.py`
  - `tests/test_call_claude.py`
  - `assets/prompts/`
  - `docs/plans/2026-04-29-certification-link-design.md`
  - `docs/plans/2026-04-29-certification-link-plan.md`
- The only completed portfolio-cleanup edit so far is `.gitignore`.
- The attempted `git rm -r --cached ...` step was interrupted before completion. At the time of this handoff, `git status --short` did not show the expected bulk `D` entries, so no sensitive-file untracking should be assumed complete.

## Completed Work

`.gitignore` was tightened to prevent future accidental tracking of private files and generated artifacts:

- Unignored-to-ignored:
  - `config/private/`
  - `materials/`
  - `interview_prep/`
- Added generated/personal output ignores:
  - `data/*.txt`
  - `templates/pdf/`
  - `docs/interview_winning_resumes/`
  - `docs/work_evidence/`
  - `docs/personal-brand-optimization*.md`
  - `docs/career-strategy-*.md`
  - `docs/interview_strategy_*.md`
  - `docs/ml_resume_*_review.md`
  - `aon_query_results.txt`

## Sensitive/Private Tracked Files Identified

These should be removed from git tracking before any public release. Keep local files on disk unless explicitly archiving elsewhere.

- `config/private/salary.yaml`
- `materials/`
- `interview_prep/`
- `docs/interview_winning_resumes/`
- `docs/work_evidence/`
- `templates/pdf/`
- `data/resume_v18_series_extracted.txt`
- `docs/personal-brand-optimization-cn.md`
- `docs/personal-brand-optimization.md`
- `docs/career-strategy-2026-04.md`
- `docs/ml_resume_v6_review.md`
- `docs/interview_strategy_2026.md`
- `aon_query_results.txt`

## Recommended Next Execution Steps

1. Confirm current branch and status.

```powershell
git branch --show-current
git status --short
```

2. Remove private/generated files from git tracking while preserving local files.

```powershell
git rm -r --cached -- config/private materials interview_prep docs/interview_winning_resumes templates/pdf docs/work_evidence data/resume_v18_series_extracted.txt docs/personal-brand-optimization-cn.md docs/personal-brand-optimization.md docs/career-strategy-2026-04.md docs/ml_resume_v6_review.md docs/interview_strategy_2026.md aon_query_results.txt
```

3. Add public-safe replacements.

- `data/sample_jobs.json`
- `config/search_profiles.example.yaml`
- `config/ai_config.example.yaml` or sanitize `config/ai_config.yaml`
- `assets/sample_bullet_library.yaml` if `assets/bullet_library.yaml` remains too personal
- `docs/SECURITY.md`
- `docs/SETUP.md`
- `docs/DEMO.md`
- `docs/DATA_MODEL.md`
- refreshed `README.md`

4. Convert production GitHub Actions to public-safe examples.

- Keep `.github/workflows/test.yml`.
- Move or rename `.github/workflows/job-pipeline.yml` to an example path, or disable scheduled production scraping in public mode.
- Public CI should not require LinkedIn cookies, Telegram secrets, Claude CLI, Turso credentials, or real LLM keys.

5. Verify.

```powershell
pytest -q
git status --short
git diff --stat
```

## Public Repo Release Notes

- Removing files from the index is not enough if the existing repository history will become public.
- For a truly public release, either create a fresh clean public repository or rewrite history with `git filter-repo`.
- If any private version was already pushed to a public remote, rotate all related secrets:
  - LLM API keys
  - Turso tokens
  - LinkedIn cookies
  - Telegram tokens
  - Gmail app password
  - OAuth credentials

## Suggested Public Narrative

Position the project as:

> An end-to-end AI-assisted job application pipeline that scrapes postings, applies deterministic filters, uses LLM evaluation and tailoring with validation gates, renders tailored PDFs, and tracks applications through the lifecycle.

Emphasize engineering decisions:

- multi-source scraper abstraction
- hard filters before expensive AI work
- C1 evaluation and C2 tailoring split
- bullet-by-ID resume generation to avoid hallucinated experience
- deterministic validation gates
- SQLite-first design with optional cloud sync
- test coverage for scraper contracts, filters, AI routing, rendering, and tracker behavior

## Pause Point

Resume from the "Recommended Next Execution Steps" section when the user asks to continue. Do not assume the sensitive-file untracking has already happened.
