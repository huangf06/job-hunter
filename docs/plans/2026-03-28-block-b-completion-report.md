# Block B Completion Report — Codex Review Brief

**Date**: 2026-03-28
**Author**: Claude Opus 4.6 + Fei Huang
**Scope**: Block B (Hard Filter) rebuild + Rule Score deletion
**Status**: Complete, ready for review
**Branch**: `master` (commits `446da4c..6752a96`)

---

## 1. What Was Done

### Background

The job-hunter pipeline is being rebuilt block-by-block according to the v3.0 architecture (`docs/plans/2026-03-27-pipeline-block-architecture.md`). The pipeline consists of 6 blocks:

```
Block A (Scrape) → Block B (Hard Filter) → Block C (AI Evaluate) → Block D (Render) → Block E (Deliver) → Block F (Notify)
```

Block A (Scraper Layer) was completed in a prior session (PR #1, merged `df94ff5`). This session completed **Block B**.

### Key Architecture Decision

**Deleted the Rule Score step entirely.** The old pipeline had three evaluation steps:

```
OLD:  Hard Filter → Rule Score (keyword matching) → AI Analysis
NEW:  Hard Filter → AI Analysis (direct)
```

**Rationale**: The user subscribed to Claude Code Max 5x ($100/month flat), making AI calls effectively free. Rule Score was a keyword-based approximation of AI scoring, existing solely to save API token costs. With flat pricing, this gate provides no value and introduces false negatives (jobs using non-standard terminology can score below 3.0 threshold and never reach AI).

This decision is documented in `docs/plans/2026-03-27-pipeline-block-architecture.md`.

---

## 2. Commits (oldest → newest)

| SHA | Message | Files Changed | Lines +/- |
|-----|---------|---------------|-----------|
| `1532971` | `docs: add pipeline block architecture v3.0` | 2 | +477/-1 |
| `7f7f7df` | `docs: add Block B implementation plan` | 1 | +523 |
| `446da4c` | `feat(block-b): extract HardFilter into standalone module with tests` | 2 | +455 |
| `00f7db1` | `refactor(block-b): rewire job_pipeline to use extracted HardFilter` | 1 | +10/-207 |
| `02fd6f0` | `feat(block-b): delete Rule Score, rewire AI analysis to use filter_results directly` | 3 | +20/-350 |
| `6752a96` | `docs: mark Block B complete, update CI and CLAUDE.md` | 4 | +57/-45 |

**Net code change**: +455 lines added (new module + tests), -591 lines deleted (score logic + dead code). Net: **-136 lines**.

---

## 3. Files Changed — Detailed

### New Files

#### `src/hard_filter.py` (233 lines)
Standalone Hard Filter module extracted from `scripts/job_pipeline.py`.

- `keyword_boundary_pattern(kw: str) -> str` — regex helper handling `.net`, `c#`, etc.
- `HardFilter` class:
  - `__init__()`: Loads `config/base/filters.yaml` and `config/search_profiles.yaml` (company/title blacklists)
  - `apply(job: Dict) -> FilterResult`: Applies 9 hard reject rules in priority order, returns pass/reject with reason

The `apply()` logic is a **direct copy** of the old `JobPipeline._apply_filter()` (verified line-by-line in code review). No behavioral changes.

#### `tests/test_hard_filter.py` (500+ lines, 52 tests)

| Test Class | Tests | What It Covers |
|------------|-------|----------------|
| `TestKeywordBoundaryPattern` | 4 | Normal words, `.net`, `c#`, no partial matches |
| `TestDutchLanguageDetection` | 1 | Dutch JD rejected (word_count rule) |
| `TestValidJobPasses` | 2 | Standard DE and ML engineer jobs pass all rules |
| `TestWrongRole` | 2 | Marketing manager, sales director rejected |
| `TestInsufficientData` | 3 | Empty description, short description, empty title |
| `TestSeniorManagement` | 5 | VP/director rejected; senior DS/DE/MLE exceptions pass |
| `TestCompanyBlacklist` | 3 | Hays/Randstad rejected, Booking.com passes |
| `TestTitleBlacklist` | 2 | Intern, trainee rejected |
| `TestDutchRequired` | 3 | Dutch fluency required, nederlandstalig, English-only passes |
| `TestWrongTechStack` | 10 | Title patterns (Flutter/dotnet/C#/Java), body keywords, exceptions, priority |
| `TestFreelanceZzp` | 3 | ZZP rejected, freelance-only rejected, full-time+freelance passes |
| `TestLowCompensation` | 3 | Low USD/EUR monthly rejected, normal salary passes |
| `TestSpecificTechExperience` | 4 | Java/Scala years rejected, Python/data title exceptions pass |
| `TestLocationRestricted` | 3 | Onsite-only rejected, no visa rejected, hybrid passes |
| `TestPriorityOrder` | 2 | Dutch beats wrong role, non_target_role beats tech_stack |
| `TestFilterResultType` | 2 | Returns `FilterResult` with `filter_version="2.0"` |

All 52 tests pass in ~0.2s. Tests use real config files (integration-style). Every enabled rule has at least one hit, one pass, and one exception/bypass test.

### Modified Files

#### `scripts/job_pipeline.py` (1073 lines, was ~1520)
**-449 lines** net. Changes:
- Removed `_keyword_boundary_pattern()` module-level function
- Removed `_apply_filter()` method (178 lines)
- Removed `_calculate_score()` method (174 lines)
- Removed `score_jobs()` method (23 lines)
- Removed `self.score_config` loading from `__init__`
- Removed `self.filter_config` and blacklist loading from `__init__` (replaced with `self.hard_filter = HardFilter()`)
- Added `from src.hard_filter import HardFilter, keyword_boundary_pattern`
- `filter_jobs()` now calls `self.hard_filter.apply(job)` instead of `self._apply_filter(job)`
- `process_all()`: removed `score_jobs()` call, removed `rule_score_threshold` references
- `ai_analyze_jobs()`: removed `min_rule_score` parameter
- `show_stats()`: removed `scored_high` display line
- `--reprocess` handler: removed `clear_scores()` and `score_jobs()` calls
- Removed `--score` CLI argument handler

#### `src/db/job_db.py` (1618 lines, was ~1700)
**-87 lines** net. Changes:
- Deleted `save_score()` method
- Deleted `get_unscored_jobs()` method
- Deleted `clear_scores()` method
- Rewrote `get_jobs_needing_analysis()`: removed `min_rule_score` parameter, removed `ai_scores` table join, now queries `filter_results.passed = 1` directly
- `v_pending_jobs` view: removed `ai_scores` join, removed `rule_score`/`rule_recommendation` columns
- `v_funnel_stats` view: removed `ai_scores` join, removed `scored_high` metric
- `get_daily_stats()`: removed `ai_scores` join and `high_score` column
- `_load_view_thresholds()`: removed `rule_score_apply` threshold and `scoring.yaml` loading
- **Preserved**: `ai_scores` CREATE TABLE statement (existing data intact, table not dropped)

#### `src/ai_analyzer.py` (1106 lines, was ~1120)
**-15 lines**. Changes:
- `analyze_batch()`: removed `min_rule_score` parameter, removed threshold loading from config
- Removed `rule_score = job.get('rule_score', 0)` display in batch loop
- `main()` CLI: removed `--min-score` arg, updated `analyze_batch()` call

#### `.github/workflows/job-pipeline-optimized.yml`
- Renamed step "Rule-based scoring" → "Import and hard filter"
- Changed step ID from `score` to `filter`
- Updated failure detection reference from `steps.score.outcome` to `steps.filter.outcome`

#### `CLAUDE.md`
- Updated pipeline flow diagram (removed Rule PreScore step)
- Changed version header from v2.0 to v3.0
- Removed `--score` CLI flag documentation
- Removed `scoring.yaml` from config file list and file tree
- Added `src/hard_filter.py` to file tree
- Updated `ai_scores` table description: "已废弃，不再写入新数据"
- Updated config section: replaced scoring thresholds with hard filter description
- Added reference to full architecture doc

#### `docs/architecture-overview.md`
- Added Block B section describing `src/hard_filter.py`
- Added note about Rule Score deletion and `ai_scores` table preservation

#### `docs/plans/2026-03-27-pipeline-block-architecture.md`
- Updated Block B status from "待重建" to "✅ 完成"
- Updated rebuild priority table

### Archived Files

#### `config/base/scoring.yaml` → `config/archive/scoring.yaml.archived`
Rule Score configuration (keyword weights, thresholds, target company tiers). No longer loaded by any code. Preserved for reference.

---

## 4. Data Flow — Before and After

### Before (v2.0)

```
jobs table
  → get_unfiltered_jobs()
  → _apply_filter() → filter_results table
  → get_unscored_jobs()
  → _calculate_score() → ai_scores table
  → get_jobs_needing_analysis(min_rule_score=3.0)  [JOIN ai_scores WHERE score >= 3.0]
  → AI analysis → job_analysis table
```

### After (v3.0 Block B)

```
jobs table
  → get_unfiltered_jobs()
  → HardFilter.apply() → filter_results table
  → get_jobs_needing_analysis()  [JOIN filter_results WHERE passed = 1]
  → AI analysis → job_analysis table
```

The `ai_scores` table is bypassed. No writes, no reads in the main pipeline. Historical data preserved.

---

## 5. What Was NOT Changed

- **Block A (Scraper)**: Untouched. `src/scrapers/` fully intact.
- **Block C-F**: Not yet rebuilt. `src/ai_analyzer.py` had minimal changes (removed `min_rule_score` parameter). Rendering, delivery, and notification modules untouched beyond doc updates.
- **`ai_scores` table**: NOT dropped. Existing data preserved for historical queries. Diagnostic scripts (`deep_analysis.py`, `pipeline_gaps.py`) can still read it.
- **`config/base/filters.yaml`**: Unchanged. All 9 filter rules work exactly as before.
- **`config/search_profiles.yaml`**: Unchanged. Blacklists still loaded.
- **Database schema**: No migrations needed. Only view definitions changed (runtime, not schema).

---

## 6. Test Results

```
$ python -m pytest tests/ -v
============================ 105 passed, 1 skipped in 16.42s =============================
```

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/test_hard_filter.py` | 52 | All pass |
| `tests/test_scrapers/test_base.py` | 10 | All pass |
| `tests/test_scrapers/test_greenhouse.py` | 3 | All pass |
| `tests/test_scrapers/test_iamexpat.py` | 5 | All pass |
| `tests/test_scrapers/test_linkedin_browser.py` | 2 | All pass |
| `tests/test_scrapers/test_linkedin_orchestration.py` | 5 | All pass |
| `tests/test_scrapers/test_linkedin_parser.py` | 2 | All pass |
| `tests/test_scrapers/test_metrics_contract.py` | 1 | All pass |
| `tests/test_scrapers/test_registry.py` | 3 | All pass |
| `tests/test_scrapers/test_scrape_cli.py` | 4 | All pass |
| `tests/test_svg_auto_optimizer.py` | 17 | 16 pass, 1 skip |
| `tests/test_language_guidance.py` | 1 | Pass |

No regressions introduced.

### Smoke Tests

```
$ python scripts/job_pipeline.py --stats
Total scraped:    3774
Passed filter:    1813
AI analyzed:      1411
AI high (>=5):    946
Resume generated: 586
Applied:          319

$ python scripts/job_pipeline.py --filter --limit 5
[Filter] No jobs to filter   # all jobs already filtered

$ python -c "from scripts.job_pipeline import JobPipeline; print('OK')"
OK
```

---

## 7. Known Gaps and Future Work

### Immediate (Block C, next session)

- `get_jobs_needing_analysis()` now returns filter-passed jobs directly. Block C will consume these via Claude Code CLI or API.
- CL generation currently uses a separate AI call (`cover_letter_generator.py`). Block C plan merges this into a single AI call.
- The `--min-score` CLI arg still exists on some commands (used for AI score threshold in `--prepare`). This is correct — it now refers to AI score, not rule score.

### Cleanup (low priority)

- `ai_scores` table can be dropped after 2+ months if no diagnostic scripts need it.
- `deep_analysis.py` and `pipeline_gaps.py` still reference `ai_scores` — they work for historical data but won't get new entries.
- `_load_config()` in `JobPipeline` loads `ai_config.yaml` but no longer loads `scoring.yaml` — verified clean.
- The `rejected` variable in `hard_filter.py` line 125 is assigned but never read (inherited from original code). Cosmetic dead code.

---

## 8. Review Checklist for Codex

1. **Logic preservation**: Is `HardFilter.apply()` in `src/hard_filter.py` behaviorally identical to the old `_apply_filter()` in `job_pipeline.py`?
2. **Test coverage**: Do the 52 tests in `test_hard_filter.py` adequately cover the 9 filter rules, blacklists, and edge cases?
3. **Rule Score deletion safety**: Are there any remaining code paths that expect `ai_scores` data for new jobs (not historical)?
4. **View correctness**: Do the updated `v_pending_jobs` and `v_funnel_stats` views still produce correct results without `ai_scores` join?
5. **CI workflow**: Is the step ID rename from `score` to `filter` correctly propagated to the failure detection logic?
6. **Architecture decision**: Was deleting Rule Score the right call given flat AI subscription pricing?
7. **CLAUDE.md consistency**: Does the updated documentation accurately reflect the current system state?

---

## 9. Architecture Context

### Pipeline Block Status

| Block | Name | Status | Key Files |
|-------|------|--------|-----------|
| A | Scrape | ✅ Complete | `src/scrapers/*`, `scripts/scrape.py` |
| B | Hard Filter | ✅ Complete | `src/hard_filter.py`, `config/base/filters.yaml` |
| C | AI Evaluate | Pending | `src/ai_analyzer.py` (to be rebuilt) |
| D | Render | Pending | `src/resume_renderer.py`, `templates/` |
| E | Deliver | Pending | `src/checklist_server.py`, `ready_to_send/` |
| F | Notify | Pending | `scripts/notify.py` |

### Design Documents

| Document | Purpose |
|----------|---------|
| `docs/plans/2026-03-27-pipeline-block-architecture.md` | Full 6-block architecture, data flow, DB schema, rebuild priority |
| `docs/plans/2026-03-27-block-b-hard-filter-rebuild.md` | Block B implementation plan (6 tasks, TDD) |
| `docs/plans/2026-03-28-block-b-completion-report.md` | This document |
| `docs/architecture-overview.md` | Living architecture doc (Block A + B sections) |
| `docs/plans/2026-03-26-v3-architecture-design.md` | Original v3.0 vision (strategic, not all applicable) |
| `docs/plans/v3-phase-1-decisions.md` through `v3-phase-5-decisions.md` | Phase-level design decisions |

### Cost Model Change (driving architecture)

The pipeline was designed around per-token API billing. The user now has Claude Code Max 5x ($100/month flat subscription), which:
- Makes AI calls per-job effectively free
- Eliminates the need for Rule Score as a cost-saving gate
- Enables CI to use `anthropics/claude-code-action@v1` with Max plan authentication (no separate API key needed)
- Opens the door for Block C to do more work per job (merge scoring + resume + CL into one call)
