# Job Hunter Architecture Diagnosis

Date: 2026-04-28
Status: Final (Opus independent review)
Scope: Evidence-based architecture audit. Diagnosis and decision only — no code changes.

---

## 1. Executive Summary

The project is a working, tested (253 passing tests), single-user Python pipeline. The Block A-F decomposition is correct and maps to real business value. **The system does not need a rewrite or a large-scale subpackage migration.**

What it does need is **surgical splitting of the 3 largest files**, which together hold 4,640 lines (36% of all source) and concentrate too many responsibilities:

| File | Lines | Core Problem |
|------|-------|--------------|
| `src/db/job_db.py` | 1,938 | Transport + schema + migrations + 7 table repositories + business queries + archival + stats + CLI |
| `src/ai_analyzer.py` | 1,417 | Prompt construction + Claude CLI calls + bullet resolution + bio assembly + skill activation + routing + validation + batch orchestration |
| `scripts/job_pipeline.py` | 1,285 | 30 CLI flags, 26 functions, 12 inline SQL queries, path resolution, analytics formatting, Gmail commands, interview scheduling |

The remaining 25+ files are appropriately sized and scoped. No circular dependencies exist. The dependency graph is clean and acyclic.

**Decision: Partial refactor needed. Scope: split the big 3, extract prompts from config. Do not reorganize the rest.**

---

## 2. Current Architecture Map

### 2.1 Pipeline Flow (verified against code)

```text
Block A: scrape.py → scrapers/{linkedin,greenhouse,iamexpat} → db.insert_job()
Block B: job_pipeline.py --filter → hard_filter.apply() → db.save_filter_result()
Block C1: job_pipeline.py --ai-evaluate → ai_analyzer.batch_evaluate() → db.save_analysis()
Block C2: job_pipeline.py --ai-tailor → ai_analyzer.batch_tailor() → db.update_analysis_resume()
Block D: job_pipeline.py --generate → resume_renderer.render() → output/ + db.save_resume()
Block E: job_pipeline.py --prepare → checklist_server.generate_checklist() → ready_to_send/
Block F: notify.py (Telegram, standalone)
```

### 2.2 Source Code Size Distribution

```text
src/db/job_db.py          ████████████████████  1,938  (15.1%)
src/ai_analyzer.py        ████████████████      1,417  (11.1%)
scripts/job_pipeline.py   █████████████         1,285  (10.0%)
src/cover_letter_gen.py   ████████               792   (6.2%)
scripts/deep_analysis.py  ████████               726   (5.7%)
src/resume_renderer.py    ████████               721   (5.6%)
src/resume_validator.py   █████                  497   (3.9%)
src/scrapers/linkedin_b.  █████                  469   (3.7%)
--- everything else ---   ███████████████████   3,952  (30.9%)
tests/                    ████████████████████   3,998
                                         total: 12,797 src + 3,998 test
```

### 2.3 Import Dependency Graph

```text
                    job_db.py  (hub — imported by 10+ modules)
                   /    |    \
          ai_analyzer  resume_renderer  hard_filter  cover_letter_*  scrapers/*
           /    |          |
  template_registry  resume_validator  language_guidance  (leaf modules)
```

No circular dependencies. No scripts importing other scripts. Clean acyclic graph.

### 2.4 Database Table Ownership

| Table | Primary Writer | Other Writers | Readers |
|-------|---------------|---------------|---------|
| `jobs` | scrapers/base.py | — | pipeline, analyzer, renderer, gaps |
| `filter_results` | hard_filter.py | — | pipeline (stats) |
| `job_analysis` | ai_analyzer.py | — | renderer, CL generator, pipeline, tracker, views |
| `resumes` | resume_renderer.py | ai_analyzer.py (USE_TEMPLATE fallback) | pipeline (prepare), CL renderer |
| `cover_letters` | cover_letter_generator.py | cover_letter_renderer.py | pipeline (finalize) |
| `applications` | job_pipeline.py | — | tracker, stats |
| `bullet_versions` | ai_analyzer.py | — | analytics |
| `bullet_usage` | ai_analyzer.py | — | analytics |
| `scrape_watermarks` | scrapers (via base) | — | scrapers |

**Key finding**: `job_analysis` is the highest-coupling table — read by 5 modules, but only written by `ai_analyzer`. This is acceptable because the write path is singular; the risk is in the JSON blob schema of `tailored_resume`, not in write contention.

### 2.5 Filesystem State Ownership

| Path | Writers | Readers | Risk |
|------|---------|---------|------|
| `output/*.html, *.pdf` | resume_renderer, CL renderer | pipeline (prepare) | Low — append-only |
| `ready_to_send/{date}_{company}/` | resume_renderer, CL renderer | pipeline, checklist | **Medium** — two writers, no coordinator |
| `ready_to_send/state.json` | checklist_server (HTTP POST) | pipeline (finalize) | **Medium** — no DB backup, crash-vulnerable |
| `ready_to_send/apply_checklist.html` | checklist_server | browser (user) | Low |
| archive folders (`_applied/`, `_skipped/`) | job_pipeline.py (finalize) | — | Low |

---

## 3. Evidence-Based Findings

### Finding 1: `job_pipeline.py` is a God CLI

**Evidence:**
- 30 CLI flags across 7 unrelated domains (import, filter, AI, render, prepare/finalize, Gmail, interviews)
- 26 functions in `JobPipeline` class + 3 standalone Gmail functions + 374-line `main()` dispatcher
- 12 inline SQL queries in `show_stats()` and `show_template_stats()` that should be DB methods
- Business logic mixed into CLI: path resolution (`_resolve_submit_dir`), job enrichment with repost history (lines 480-505), orphan folder cleanup (lines 511-521), edited CL detection (lines 637-670), "likely ghosted" calculation
- Gmail commands (`--test-gmail`, `--read-email`, `--search-emails`) have no relationship to the job pipeline

**Severity: High.** Every feature addition touches this file. Impact analysis for any change requires reading the entire 1,285-line dispatcher.

### Finding 2: `job_db.py` conflates 5 layers of abstraction

**Evidence:**
- 65 methods in `JobDatabase` class spanning: transport (`TursoHTTPClient`, 127 lines), connection management, schema creation, 10 ALTER TABLE migrations, 7 SQL views, CRUD for 8 tables, business queries (semantic dedup, resume tier routing), statistics (6 methods), archival (131-line `archive_cold_data`), import/export, and its own CLI
- Longest method: `archive_cold_data()` at 131 lines — handles 14-table migration with chunking, verification, and transactional delete
- `insert_job()` at 69 lines — contains semantic dedup + pipeline reset, which is business logic
- `get_analyzed_jobs_for_resume()` — 4 JOINs with 4-way resume tier routing conditions

**Severity: High.** Any schema migration, new query, or transport change risks breaking unrelated functionality.

### Finding 3: `ai_analyzer.py` does too many things

**Evidence:**
- 1,417 lines, 26 methods in `AIAnalyzer`
- Responsibilities: load bullet library, load config, build skill context, build title context, construct C1 prompt, construct C2 prompt, call Claude CLI subprocess, parse JSON response, resolve bullet IDs, assemble bio from spec, inject technical skills, validate resume structure, track bullet usage (direct SQL INSERT), route resume tiers, run C3 gate, batch orchestrate C1, batch orchestrate C2
- `_call_claude()` is a subprocess wrapper that strips env vars, handles rate limits, and parses output — this is an infrastructure concern mixed with business logic
- Bullet resolution (lines 345-418) and bio assembly (lines 476-597) are content-assembly functions that have nothing to do with AI calling

**Severity: Medium-High.** Prompt changes, bullet library changes, and Claude API changes all require editing the same file. But: the current structure works and has 849 lines of tests.

### Finding 4: `ai_config.yaml` mixes 5 concerns in 543 lines

**Evidence:**
- Runtime config: `models.analyzer`, `thresholds.*`, `prompt_settings.*`
- Full multi-line prompts: `prompts.evaluator` (82 lines), `prompts.tailor` (211 lines), `prompts.tailor_adapt` (48 lines), `prompts.c3_gate` (21 lines)
- Static candidate facts: `resume.candidate.*` (name, email, phone, linkedin, github, blog)
- Education data: `resume.education.*` (degrees, GPA, thesis title)
- Interview scheduler config: `interview_scheduler.*`

**Severity: Medium.** This is the highest-frequency edit target. Every prompt iteration, threshold tweak, or personal info update requires editing this one 543-line file. One bad YAML indent breaks the entire pipeline. Prompts especially should be separate files — they're multi-paragraph text blocks, not configuration values.

### Finding 5: Filesystem/DB double-write exists but is manageable

**Evidence:**
- `resumes` table has `pdf_path` and `submit_dir` columns that mirror filesystem state
- `ready_to_send/state.json` tracks application progress with no DB backup
- `--repair` command exists specifically to reconcile filesystem/DB drift
- `clear_orphan_resumes()` validates that PDF files still exist on disk before trusting DB records

**Severity: Low-Medium.** The double-write is real but **already has compensating mechanisms** (repair, orphan cleanup). For a single-user system, this is pragmatic. Centralizing state ownership would be cleaner but carries migration risk disproportionate to the benefit.

### Finding 6: Healthy boundaries that should NOT be refactored

| Module | Lines | Status | Reason to leave alone |
|--------|-------|--------|----------------------|
| `src/hard_filter.py` | 233 | Clean | Single responsibility, config-driven, well-tested (614 test lines) |
| `src/scrapers/` | 856 total | Clean | Good inheritance hierarchy, clear BaseScraper contract |
| `src/checklist_server.py` | 358 | Clean | Standalone, stdlib-only, proper XSS protection |
| `src/resume_validator.py` | 497 | Clean | Pure validation, no side effects |
| `src/template_registry.py` | 137 | Clean | Leaf module, config reader |
| `src/language_guidance.py` | 78 | Clean | Leaf module, config reader |
| `src/google_calendar.py` | 357 | Clean | Standalone REST client |
| `src/gmail_client.py` | 329 | Clean | Standalone IMAP client |
| `src/interview_scheduler.py` | 416 | Clean | Reads DB + Calendar, writes Calendar |
| `scripts/scrape.py` | 198 | Clean | Thin CLI, delegates to scrapers |

**These 10 modules are fine. Touching them would be refactoring for its own sake.**

### Finding 7: Test coverage is strong locally, weak at boundaries

**Evidence:**
- 15 test files, 3,998 lines, 253 tests passing
- Strong coverage: AI analyzer (849 lines), hard filter (614), renderer tiers (574), dedup (492)
- Weak coverage: no test for the full `--prepare` → `--finalize` workflow; no test for `show_stats()` SQL queries; no integration test for scrape → filter → analyze → render chain; `job_pipeline.py` has only 57 lines of test (template stats only)

**Severity: Low for daily work, Medium for refactoring.** Before splitting the big 3, we need contract tests that verify behavior is preserved.

---

## 4. Refactor Decision

```text
Decision:
  Refactor needed: Yes, partial — surgical splitting of the 3 largest files + prompt extraction
  Main reason: The big 3 files concentrate 36% of source and mix abstraction layers,
               making every change high-risk and high-cognitive-load
  Urgency: Medium — the system works, but every prompt/bullet/threshold change
           is harder than it should be
  Biggest risk if not refactored: A prompt change or DB migration breaks something
           unrelated because the blast radius of each file is too wide
  Biggest risk if refactored too aggressively: Breaking the working pipeline and
           253 passing tests for a directory structure that looks cleaner on paper
           but doesn't change runtime behavior
```

### What to refactor (in priority order)

1. **Extract prompts from `ai_config.yaml` into separate files** — highest frequency benefit, lowest risk
2. **Split `job_db.py`** — extract Turso transport, schema/migrations, and stats into separate files; keep `JobDatabase` as facade
3. **Split `job_pipeline.py`** — extract command handlers for stats, prepare/finalize, Gmail, interviews; keep `main()` as dispatcher
4. **Split `ai_analyzer.py`** — extract Claude client, prompt builder, bullet resolver; keep `AIAnalyzer` as orchestrator

### What NOT to refactor

- Hard filter, scrapers, checklist server, validators, template registry, language guidance, integrations — all appropriately scoped
- DB schema — no normalization of `job_analysis.tailored_resume` JSON blob
- The `ready_to_send/` filesystem workflow — compensating mechanisms (repair, orphan cleanup) already work
- No new CLI framework (click, typer) — argparse works fine for a single-user tool
- No `src/job_hunter/` package rename — import path churn with zero runtime benefit

### What is business complexity, not architecture debt

- Bullet library growth (1,055 lines, 51 bullets) — this is content, not code
- Resume tier routing logic — this is inherent business complexity (3 tiers, legacy compat)
- C1/C2 split with score gating — this is correct domain modeling, not accidental complexity
- Template registry and zone-based rendering history — cleanup is valid but is a product decision, not an architecture one

---

## 5. Target Architecture

**Approach: keep existing `src/` flat structure, split only the 3 overloaded files, extract prompts.**

No new subpackages. No CLI rewrite. No `src/job_hunter/` namespace.

### 5.1 Split `job_db.py` (1,938 → ~4 files)

```text
src/db/
  job_db.py            # JobDatabase facade (keeps all existing method signatures)
  turso_client.py      # TursoHTTPClient, _TursoConnAdapter, _TursoCursor, _DualAccessRow (~170 lines)
  schema.py            # _init_db, _migrate, _build_views_sql, _load_view_thresholds, dataclasses (~250 lines)
  stats.py             # get_funnel_stats, get_filter_stats, get_company_stats, get_daily_stats,
                       #   get_daily_token_usage, archive_cold_data, import/export, CLI (~350 lines)
```

`JobDatabase` stays as the public API — all existing callers (`ai_analyzer`, `resume_renderer`, `job_pipeline`, etc.) keep calling `db.save_analysis()`, `db.get_job()`, etc. No import changes required. The facade delegates internally.

### 5.2 Split `job_pipeline.py` (1,285 → ~4 files)

```text
scripts/
  job_pipeline.py      # main() dispatcher + argparse (slim: ~300 lines)
  _pipeline_commands.py  # Core pipeline: process, filter, AI analyze/tailor, generate (~400 lines)
  _workspace_commands.py # prepare, finalize, repair, archive (~350 lines)
  _reporting_commands.py # stats, template_stats, tracker, bullet_analytics + their SQL (~200 lines)
```

All `--flag` names stay identical. The `_` prefix signals these are internal modules, not independent entry points. Gmail and interview commands stay in `job_pipeline.py` for now (they're small enough, ~100 lines each).

### 5.3 Split `ai_analyzer.py` (1,417 → ~3 files)

```text
src/
  ai_analyzer.py       # AIAnalyzer class: batch_evaluate, batch_tailor, analyze_job (orchestrator, ~500 lines)
  claude_client.py     # _call_claude(), QuotaExhaustedError, env stripping (~80 lines)
  resume_builder.py    # resolve_bullets, assemble_bio, inject_technical_skills,
                       #   build_skill_context, build_title_context (~400 lines)
```

Prompt construction stays in `ai_analyzer.py` because it's tightly coupled to the orchestration flow. The split targets the two independently testable concerns: "how to call Claude" and "how to assemble resume content from bullet library."

### 5.4 Extract prompts from `ai_config.yaml`

```text
config/
  ai_config.yaml       # Runtime config only: models, thresholds, prompt_settings,
                        #   candidate info, education, scheduler (~200 lines)
  prompts/
    evaluator.md       # C1 prompt template with {placeholders} (~80 lines)
    tailor.md          # C2 prompt template (~210 lines)
```

`ai_analyzer.py` loads prompts from `config/prompts/*.md` instead of `config['prompts']['evaluator']`. Retired prompts (`tailor_adapt`, `c3_gate`) move to `config/prompts/_retired/` or get deleted if no longer referenced.

### 5.5 Why NOT the full subpackage architecture from the draft

The earlier draft proposed 8 subpackages, 6 repositories, a new CLI framework, and a `src/job_hunter/` namespace. That's too much migration for the actual problem:

| Draft Proposal | My Assessment |
|---------------|---------------|
| 8 bounded-context subpackages | Only 3 files are overloaded. The other 10+ modules already have clear boundaries. |
| 6 DB repositories | Splitting CRUD by table creates 6 tiny files (~50-80 lines each) with high cross-reference overhead. Better: split by abstraction layer (transport, schema, stats) and keep domain queries in facade. |
| New CLI (`job-hunter scrape run`, etc.) | Adds a migration burden with no user-facing benefit for a single-user tool. The current `--flags` work fine. |
| `src/job_hunter/` package rename | Every `from src.` import changes. 100+ lines of churn, zero runtime benefit. |
| Phase 0 "document boundaries" as a separate PR | Documentation without code changes gets stale immediately. Better: document ownership in code comments during the actual splits. |

---

## 6. Recommended Roadmap

### Phase A: Prompt Extraction (1 PR, low risk)

**PR 1: Move prompts out of ai_config.yaml**

- Create `config/prompts/evaluator.md` and `config/prompts/tailor.md`
- Modify `ai_analyzer.py` to load from files instead of config dict
- Delete `prompts.tailor_adapt` and `prompts.c3_gate` if confirmed dead code (grep for references first)
- Shrink `ai_config.yaml` from 543 to ~200 lines

Scope: 3 new files, 1 modified file.
Test strategy: Existing 849 lines of ai_analyzer tests must pass unchanged.
Rollback: Revert 1 commit.
Risk: Near-zero. Prompts are read-once at startup.

### Phase B: Split job_db.py (1-2 PRs, medium risk)

**PR 2: Extract Turso transport + schema/migrations**

- Move `TursoHTTPClient`, `_TursoConnAdapter`, `_TursoCursor`, `_DualAccessRow` → `src/db/turso_client.py`
- Move `_init_db`, `_migrate`, `_build_views_sql`, `_load_view_thresholds`, all dataclasses → `src/db/schema.py`
- `JobDatabase.__init__` imports from these; all public methods stay on `JobDatabase`

Scope: 2 new files, 1 modified file. No import changes for callers.
Test strategy: All 253 existing tests pass. Add 1 test that `JobDatabase` can be instantiated after the split.
Rollback: Revert 1 commit.
Risk: Low. These are pure extractions with no behavior change.

**PR 3: Extract stats + archival + import/export**

- Move `get_funnel_stats`, `get_filter_stats`, `get_company_stats`, `get_daily_stats`, `get_daily_token_usage`, `archive_cold_data`, `import_from_json`, `export_to_json`, `main()` CLI → `src/db/stats.py`
- `JobDatabase` delegates to `stats.py` functions (pass connection)

Scope: 1 new file, 1 modified file.
Test strategy: Existing tests pass. Move the inline SQL from `job_pipeline.py`'s `show_stats()` and `show_template_stats()` into `stats.py` as named functions + add tests.
Rollback: Revert 1 commit.
Risk: Low-Medium. The `archive_cold_data` function is complex (131 lines) but self-contained.

### Phase C: Split job_pipeline.py (1 PR, medium risk)

**PR 4: Extract command handler modules**

- Create `scripts/_pipeline_commands.py` (process, filter, AI commands)
- Create `scripts/_workspace_commands.py` (prepare, finalize, repair, archive)
- Create `scripts/_reporting_commands.py` (stats, template_stats, tracker, bullet_analytics)
- `JobPipeline` class methods move to these files; `main()` dispatcher stays slim
- Move the 12 inline SQL queries from `show_stats()`/`show_template_stats()` into `src/db/stats.py`

Scope: 3 new files, 1 heavily modified file.
Test strategy: All existing tests pass. Add a smoke test that each `--flag` still dispatches correctly.
Rollback: Revert 1 commit, but this is the highest-risk PR because `main()` wiring changes.
Risk: Medium. The dispatcher logic is straightforward but has many branches.

### Phase D: Split ai_analyzer.py (1 PR, medium risk)

**PR 5: Extract Claude client + resume builder**

- Create `src/claude_client.py` (_call_claude, QuotaExhaustedError)
- Create `src/resume_builder.py` (resolve_bullets, assemble_bio, inject_technical_skills, build_skill_context, build_title_context)
- `AIAnalyzer` imports from both; all public methods stay on `AIAnalyzer`

Scope: 2 new files, 1 modified file. No import changes for callers.
Test strategy: Existing 849 lines of tests pass. Add targeted tests for `resume_builder` functions.
Rollback: Revert 1 commit.
Risk: Medium. Bio assembly and bullet resolution have complex validation logic.

### What to defer indefinitely

| Item | Reason |
|------|--------|
| New CLI framework / subcommands | No user-facing benefit for a single-user tool |
| `src/job_hunter/` package rename | Import churn, zero runtime benefit |
| DB repository-per-table split | Over-abstraction for ~65 methods that share a connection |
| Application workspace extraction | `prepare`/`finalize` work; the repair mechanism handles edge cases |
| `state.json` → DB migration | Works for single-user; crash risk is theoretical |
| TypeScript workbench | Python pipeline boundaries should stabilize first |
| `bullet_library.yaml` schema validation | Product quality concern, not architecture |

---

## 7. Open Questions

1. **Are `prompts.tailor_adapt` and `prompts.c3_gate` dead code?** They're in config and have code paths, but template routing was reverted to FULL_CUSTOMIZE only. Need to grep for actual usage before deleting.

2. **Should `resumes` table have a single writer?** Currently both `resume_renderer` and `ai_analyzer` (USE_TEMPLATE fallback) write to it. This hasn't caused bugs, but it's a latent risk. Possible fix: have `ai_analyzer` return the Resume record and let the pipeline decide who calls `db.save_resume()`.

3. **Is `cover_letter_generator.py` (792 lines) the next file to split?** It's the 4th largest, but I haven't done a detailed review. If it has the same pattern (prompt construction + AI calling + content assembly in one file), it would benefit from the same treatment as `ai_analyzer`.

4. **How stable is the bullet library schema?** If it's still evolving rapidly (v7.3 was today), adding schema validation now would create friction. Better to wait until the format stabilizes.

---

## 8. Summary: 5 PRs, Ordered by Value/Risk

| PR | Target | Lines Moved | Risk | Value |
|----|--------|-------------|------|-------|
| 1 | Extract prompts from ai_config.yaml | ~300 | Low | **High** (highest-frequency edit) |
| 2 | Extract Turso transport + schema from job_db.py | ~420 | Low | Medium |
| 3 | Extract stats + archival from job_db.py | ~350 | Low-Med | Medium |
| 4 | Extract command handlers from job_pipeline.py | ~600 | Medium | **High** (reduces blast radius of CLI) |
| 5 | Extract Claude client + resume builder from ai_analyzer.py | ~480 | Medium | Medium |

Total: ~2,150 lines moved into ~11 new files. No import changes for existing callers. No schema changes. No CLI flag changes. All 253 tests must pass at every step.
