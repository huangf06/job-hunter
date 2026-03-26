# Job Hunter v3.0 - Revised Architecture Design

**Date**: 2026-03-26  
**Status**: Revised Final Proposal  
**Scope**: Medium refactor with incremental migration from v2.0

## 1. Executive Decision

1. Keep the Stage Engine direction, but redraw stage boundaries so business evaluation and external side effects are not mixed in the same stage.
2. Do not delete `ai_scores` in v3.0. Treat it as a compatibility table because existing scripts, stats, views, and archive flows still depend on it.
3. Replace the single thin `JobRepository` abstraction with multiple repository protocols plus a `UnitOfWork` boundary.
4. Split `Render`, `Prepare`, and `Auto-Apply` into separate steps. Rendering generates artifacts, publishing prepares operator-facing materials, and auto-apply is an explicit side-effecting operation.
5. Bring interview preparation and interview scheduling into explicit v3 architecture boundaries instead of leaving them as informal preserved modules.
6. Expand ConfigManager into a runtime configuration system with resolved config loading, private config support, integration config support, config fingerprinting, and per-run snapshots.
7. Introduce a real migration contract: compatibility facade for `src.db.job_db`, parity verification, phased rollout, DB backup points, feature flags, and explicit rollback paths.
8. Email Router is in scope for v3.0 only as a minimal safe version: ingestion, dedupe, job matching, thread merge, review queue, and optional high-confidence reconciliation.
9. Defer over-designed features. Tracer Links move to v3.1 experimental scope. Generic LLM-driven auto-apply is postponed beyond v3.1.
10. Replace the overloaded `track` CLI grouping with narrower command domains: `pipeline`, `materials`, `applications`, `inbox`, `interview`, and `admin`.

## 2. Revised Architecture

### Revised directory structure

```text
src/
├── core/
│   ├── models/              # Shared entities, value objects, enums
│   ├── protocols/           # Repository, service, and unit-of-work protocols
│   ├── config/              # Config loading, merge rules, fingerprinting, snapshots
│   └── runtime/             # Run context, feature flags, stage execution policy
│
├── domain/
│   ├── scoring/             # Rule scoring, gate-pass logic, score explanation
│   ├── analysis/            # AI analysis output, resume spec, validation policy
│   ├── applications/        # Application state transitions, outcome rules, repost logic
│   ├── email/               # Email matching, thread merge, review policy
│   └── interviews/          # Interview prep and scheduling rules
│
├── services/
│   ├── orchestration/       # Stage runner, retries, checkpoints
│   ├── materials/           # Resume/CL generation, validation, publish helpers
│   ├── applications/        # Application reconciliation and finalize workflows
│   ├── inbox/               # Email ingest/classify/reconcile workflows
│   └── interviews/          # Interview prep assembly and scheduling workflows
│
├── integrations/
│   ├── db/                  # SQLite/Turso repos, migrations, legacy adapter
│   ├── llm/                 # Claude/Kimi/Ollama implementations
│   ├── browser/             # Playwright renderers and platform-specific apply drivers
│   ├── email/               # Gmail fetchers/adapters
│   ├── calendar/            # Google Calendar adapter
│   └── scrapers/            # Existing scrapers adapted into ingest contracts
│
├── stages/
│   ├── ingest/              # Job ingestion stages
│   ├── evaluate/            # Filter, score, analyze, validate
│   ├── materials/           # Render and publish
│   └── operations/          # Email sync, classification, reconciliation, auto-apply
│
└── cli/
    ├── main.py
    ├── pipeline.py
    ├── materials.py
    ├── applications.py
    ├── inbox.py
    ├── interview.py
    └── admin.py
```

### Layer boundaries

- `core`: Stable technical backbone. Defines contracts, runtime metadata, config resolution, and execution context. No domain logic and no third-party side effects.
- `domain`: Pure business rules. This is where scoring, validation policy, email matching heuristics, application transitions, and interview rules live.
- `services`: Orchestrate domain logic for one use case. They may depend on protocols, but not on concrete DB or browser implementations.
- `integrations`: All IO. SQLite, Gmail, Playwright, Google Calendar, LLM providers, and scraper adapters belong here.
- `stages`: Batch-oriented execution units with checkpointing and rerun semantics. A stage should not hide unrelated side effects.
- `cli`: Command routing only. It constructs the run context, selects services/stages, and prints operator-facing summaries.

### Architectural boundary decisions

- Interview prep and interview scheduler remain out of the main job scoring pipeline, but become first-class workflows under `domain/interviews`, `services/interviews`, and `cli/interview.py`.
- The old `src.db.job_db` remains present during migration as a facade that can forward to v3 repositories or legacy SQL paths.
- The v3 architecture does not assume all read and write paths migrate at the same time.

## 3. Protocol and Dependency Model

### Design decision

The original `JobRepository` / `LLMClient` / `BrowserClient` contracts are too thin for the real call surface. v3 should split these into narrower contracts aligned to stable responsibilities.

### Recommended protocol set

```python
class UnitOfWork(Protocol):
    jobs: "JobQueryRepo"
    stages: "StageStateRepo"
    applications: "ApplicationRepo"
    materials: "MaterialRepo"
    email: "EmailRepo"
    runs: "RunMetaRepo"

    def __enter__(self) -> "UnitOfWork": ...
    def __exit__(self, exc_type, exc, tb) -> None: ...
    def commit(self) -> None: ...
    def rollback(self) -> None: ...


class JobQueryRepo(Protocol):
    def get_job(self, job_id: int) -> Job | None: ...
    def search_jobs(self, query: JobQuery) -> list[Job]: ...
    def list_for_stage(self, stage_key: str, limit: int, cursor: str | None = None) -> list[Job]: ...


class StageStateRepo(Protocol):
    def get_latest_result(self, job_id: int, stage_key: str) -> StageExecution | None: ...
    def upsert_stage_result(self, record: StageExecutionWrite) -> None: ...
    def save_checkpoint(self, run_id: str, stage_key: str, cursor: str) -> None: ...


class ApplicationRepo(Protocol):
    def get_application(self, job_id: int) -> Application | None: ...
    def upsert_application(self, command: ApplicationStateUpdate) -> None: ...
    def append_event(self, event: ApplicationEvent) -> None: ...
    def append_outcome(self, event: OutcomeEvent) -> None: ...


class MaterialRepo(Protocol):
    def save_resume_spec(self, job_id: int, spec: ResumeSpec) -> None: ...
    def save_cover_letter_spec(self, job_id: int, spec: CoverLetterSpec) -> None: ...
    def save_rendered_material(self, record: RenderedMaterialWrite) -> None: ...
    def get_latest_material_set(self, job_id: int) -> MaterialSet | None: ...


class EmailRepo(Protocol):
    def has_message(self, external_message_id: str, fingerprint: str) -> bool: ...
    def save_message(self, message: EmailMessageRecord) -> int: ...
    def link_thread(self, link: EmailThreadLink) -> None: ...
    def save_classification(self, record: EmailClassificationWrite) -> None: ...
    def queue_review(self, item: ReviewQueueItem) -> None: ...


class CalendarService(Protocol):
    def list_events(self, window: TimeWindow) -> list[CalendarEvent]: ...
    def create_hold(self, request: CalendarHoldRequest) -> str: ...


class LLMService(Protocol):
    def analyze_job(self, payload: AnalysisInput) -> AnalysisOutput: ...
    def classify_email(self, payload: EmailClassificationInput) -> EmailClassificationOutput: ...


class BrowserRenderService(Protocol):
    def render_resume_pdf(self, html: str, output_path: Path) -> Path: ...
    def render_cover_letter_pdf(self, html: str, output_path: Path) -> Path: ...


class AutoApplyDriver(Protocol):
    def dry_run(self, packet: ApplyPacket) -> ApplyAttempt: ...
    def submit(self, packet: ApplyPacket) -> ApplyAttempt: ...


class RunMetaRepo(Protocol):
    def start_run(self, command: RunCommand, config_fingerprint: str) -> str: ...
    def finish_run(self, run_id: str, summary: RunSummary) -> None: ...
    def record_config_snapshot(self, run_id: str, snapshot: ConfigSnapshot) -> None: ...
    def schema_guard(self, min_version: int, max_version: int | None = None) -> None: ...
```

### Boundary notes

- `job query / stage query`: split into `JobQueryRepo` and `StageStateRepo`.
- `application state update`: isolated in `ApplicationRepo`, with append-only event support.
- `resume / cover letter materials`: handled by `MaterialRepo`, not hidden inside job persistence.
- `email ingestion / classification persistence`: handled by `EmailRepo`.
- `calendar access`: explicit service protocol, not a generic integration bucket.
- `run metadata / config fingerprint / migration-safe operations`: `RunMetaRepo` owns run records, schema guards, and config snapshots.
- `transaction / unit-of-work boundary`: DB writes for one job or one chunk should be atomic; browser actions, email fetches, and PDF rendering stay outside the DB transaction.

### Why this is preferable

- It supports incremental migration because old code can keep using a facade while new code moves to narrower protocols.
- It reflects actual coupling. Rendering, applications, email, and run metadata are separate persistence concerns.
- It makes parity testing easier because query-side and write-side behavior can be compared independently.

## 4. Stage Redesign

### Revised stage list

1. `ingest_jobs`
2. `evaluate_filters`
3. `evaluate_scoring`
4. `analyze_job_fit`
5. `validate_material_spec`
6. `render_materials`
7. `publish_materials`
8. `sync_email`
9. `classify_email`
10. `reconcile_application_state`
11. `execute_auto_apply`

### Stage rationale

- Split `Render` and `Prepare` because artifact generation and operator-facing publication are different concerns.
- Split email operations into sync, classify, and reconcile because they have different failure paths and idempotency characteristics.
- Keep validation as its own stage between analysis and rendering. Validation remains the blocking gate.
- Keep auto-apply separate from material publication. Publishing makes files ready; auto-apply is an optional operator-triggered action.

### Stage definitions

#### `ingest_jobs`
- Input: scraper output, inbox JSON, source metadata
- Output: `jobs`, `job_sources`
- Idempotent: yes, by `source + external_id` or normalized URL
- Rerunnable: yes
- Recovery: rerun from cursor or source checkpoint

#### `evaluate_filters`
- Input: jobs lacking current filter result for active config fingerprint
- Output: `filter_results`
- Idempotent: yes
- Rerunnable: yes
- Recovery: rerun for affected jobs under new config fingerprint

#### `evaluate_scoring`
- Input: filter-passed jobs
- Output: `stage_scores` and compatibility projection to `ai_scores`
- Idempotent: yes within the same scoring version and config fingerprint
- Rerunnable: yes
- Recovery: overwrite current stage score record; do not delete historical score revisions

#### `analyze_job_fit`
- Input: jobs above rule-score threshold
- Output: `job_analysis`, resume spec draft, cover letter spec draft
- Idempotent: no, because model output may vary
- Rerunnable: yes, but save as new revision instead of destructive overwrite
- Recovery: previous successful revision remains active until a newer revision is promoted

#### `validate_material_spec`
- Input: latest analysis revision
- Output: `material_validations`
- Idempotent: yes
- Rerunnable: yes
- Recovery: rerun after rule, bullet library, or validator updates

#### `render_materials`
- Input: validated material specs
- Output: `rendered_materials`, PDF/HTML file records
- Idempotent: conditionally, based on spec hash
- Rerunnable: yes
- Recovery: delete incomplete artifacts and rerender the same hash

#### `publish_materials`
- Input: latest rendered material set
- Output: `ready_to_send` files, checklist state, publish record
- Idempotent: yes
- Rerunnable: yes
- Recovery: regenerate target folder and state entry from the stored material set

#### `sync_email`
- Input: Gmail cursor or lookback window
- Output: `email_messages`, `email_threads`
- Idempotent: yes, via external message id plus content fingerprint
- Rerunnable: yes
- Recovery: resume from last cursor or rerun lookback scan

#### `classify_email`
- Input: unclassified or stale-classification threads
- Output: `email_classifications`, `review_queue`
- Idempotent: yes under the same classifier version
- Rerunnable: yes
- Recovery: reclassify low-confidence or manually rejected items

#### `reconcile_application_state`
- Input: classified threads plus existing application state
- Output: `application_events`, `outcome_events`, optional application status update
- Idempotent: yes, via message/thread event key
- Rerunnable: yes
- Recovery: conflicting matches are routed to manual review; append-only events prevent destructive rollback

#### `execute_auto_apply`
- Input: published materials plus an explicit target application
- Output: `apply_attempts`, screenshots, submitted state if approved
- Idempotent: no
- Rerunnable: only through explicit retry command
- Recovery: use stored screenshots, field packet, and attempt record; default to dry-run in v3.1

### Special handling

- `Render / Prepare / Auto-Apply`: three distinct stages/commands. Do not collapse them.
- `Email sync / classification / application update`: three distinct operations with separate checkpoints.
- `Validate`: one canonical blocking stage between analysis and render. It should not also run inside analyzer or renderer.

## 5. Schema Strategy

### Keep

- `jobs`
- `filter_results`
- `job_analysis`
- `resumes`
- `cover_letters`
- `applications`

### Add

- `stage_executions`
- `stage_scores`
- `run_metadata`
- `config_run_snapshots`
- `job_sources`
- `material_validations`
- `rendered_materials`
- `application_events`
- `outcome_events`
- `email_messages`
- `email_threads`
- `email_classifications`
- `email_job_links`
- `review_queue`
- `apply_attempts`

### Keep for compatibility first, retire later

- `ai_scores`
- `feedback`
- `config_snapshots`

### Tables that should not be deleted immediately

#### `ai_scores`

Do not delete in v3.0. Existing scripts and views still depend on it. Recommended strategy:

- New scoring logic writes to `stage_scores`
- A compatibility projection writes the latest rule score into `ai_scores`, or exposes `v_ai_scores_compat`
- Legacy stats and archive scripts continue to work during migration

#### `feedback`

Do not treat as safe-to-drop until actual usage is confirmed. If unused, freeze it as `legacy_feedback` semantics and build new feedback tracking on `outcome_events`.

#### `config_snapshots`

Do not drop immediately. Leave legacy reads intact and add `config_run_snapshots` for resolved config, config fingerprint, source paths, and sensitive-source markers.

### Email-related schema

The minimal v3.0 email model should support:

- message dedupe
- thread merge
- classifier revision tracking
- job matching evidence
- manual review queue

Recommended tables:

- `email_messages`
- `email_threads`
- `email_classifications`
- `email_job_links`
- `review_queue`

### Outcome / source / audit trail

All automated state changes must be traceable:

- `application_events` stores state transitions
- `outcome_events` stores interview/rejection/offer/withdrawn/ghosted style outcomes
- each auto-generated event includes `source`, `confidence`, and `evidence_ref`

### Compatibility views and backfills

- Add `v_ai_scores_compat` if old queries are hard to rewrite quickly
- Backfill `application_events` from current `applications` where feasible
- Backfill recent emails only if needed for near-term automation; do not require full historical migration for v3.0

## 6. Migration Contract

### Migration principles

- v2 must remain usable during migration
- old scripts are wrappers until parity is proven
- every schema-changing phase starts with a backup point
- every new write path is gated by a feature flag

### Phase 0: Schema safety foundation

- Goal: add schema version tracking, ordered migrations, backup script, compatibility tables/views
- Code scope: `integrations/db/migrations`, backup tooling, schema guard helpers
- Compatibility strategy: no behavior change to old runtime
- Verification: migration dry-run on copied DB, restore test from backup
- Rollback: restore SQLite backup and keep running old entry points

### Phase 1: Legacy facade and adapter

- Goal: preserve `src.db.job_db` while introducing v3 repository adapters
- Code scope: new DB adapters plus legacy facade
- Compatibility strategy: `JobDatabase` remains importable and forwards to old or new implementation by flag
- Verification: smoke-test existing commands and unit tests against the facade
- Rollback: point facade back to pure legacy code path

### Phase 2: Read-side migration

- Goal: migrate query-side code first: stats, job selection, config loading
- Code scope: query repos, ConfigManager rewrite, CLI read commands
- Compatibility strategy: writes still use v2 paths
- Verification: parity harness for `--stats`, `--ready`, `--analyze-job`
- Rollback: disable read-path flags and revert CLI wrappers to old queries

### Phase 3: Stage-by-stage write migration

- Goal: migrate filter, score, analyze, validate, render, publish one stage at a time
- Code scope: new stages, services, stage persistence
- Compatibility strategy: dual-write where needed, especially for `ai_scores`
- Verification: golden-master comparison on selected job sets and rendered output metadata
- Rollback: disable the specific stage flag and continue through v2 implementation

### Phase 4: Inbox and application reconciliation

- Goal: introduce email ingestion, classification, and application reconciliation
- Code scope: inbox services, email schema, application event model, CLI commands
- Compatibility strategy: default to ingest plus review queue; auto-update disabled by default
- Verification: golden set of recruiter emails, dedupe checks, thread merge checks, manual review acceptance tests
- Rollback: stop reconciliation and keep email data read-only

### Phase 5: CLI migration and default path switch

- Goal: move operators and CI/CD to the new CLI structure
- Code scope: `src/cli/*`, wrappers in `scripts/job_pipeline.py`
- Compatibility strategy: old args still map to new commands, with deprecation warnings
- Verification: CI smoke matrix using both old and new invocations
- Rollback: point workflows back to the old wrapper behavior

### Required migration mechanisms

#### Facade/adapter strategy for old `src.db.job_db`

- Keep module path stable
- Replace internals with a compatibility facade
- Support both legacy SQL path and v3 repository-backed path behind flags

#### Parity harness / golden-master comparison

Build a fixed corpus of jobs and expected outputs:

- selected job ids across sources
- filter pass/fail decisions
- rule scores
- analysis existence and key fields
- rendered output metadata
- stats snapshots

The harness should compare old vs new behavior before flipping defaults.

#### DB backup points

Before every migration phase:

- create `data/backups/jobs-YYYYMMDD-HHMMSS.db`
- log backup path in `run_metadata`

#### Feature flags / command gating

Recommended flags:

- `V3_READ_PATH`
- `V3_STAGE_FILTER`
- `V3_STAGE_SCORING`
- `V3_STAGE_ANALYZE`
- `V3_STAGE_RENDER`
- `EMAIL_AUTO_RECONCILE`
- `AUTO_APPLY_ENABLED`

## 7. CLI Revision

### Recommended command tree

```text
jh pipeline ingest
jh pipeline evaluate
jh pipeline analyze

jh materials validate
jh materials render
jh materials publish

jh applications list
jh applications update
jh applications finalize
jh applications auto-apply

jh inbox email-sync
jh inbox email-classify
jh inbox email-review
jh inbox reconcile

jh interview prep COMPANY
jh interview schedule COMPANY

jh admin stats
jh admin migrate
jh admin backfill
jh admin doctor
```

### Grouping rationale

- `pipeline`: scrape/import/filter/score/analyze style processing
- `materials`: validation, render, and publish of resume and cover letter artifacts
- `applications`: post-material application state changes and explicit auto-apply actions
- `inbox`: email ingestion and reconciliation
- `interview`: interview prep and scheduling workflows
- `admin`: migrations, health checks, stats, and backfills

### Solving `track` overload

The old `track` concept mixed four different concerns:

- application board and lifecycle
- email sync
- stats
- outcomes

These are now separated into `applications`, `inbox`, and `admin`.

### Legacy command compatibility

Old commands should continue to work through wrappers:

- `python scripts/job_pipeline.py --process` -> `jh pipeline ingest` plus `jh pipeline evaluate`
- `--ai-analyze` -> `jh pipeline analyze`
- `--prepare` -> `jh materials publish`
- `--stats` -> `jh admin stats`
- `--tracker` -> `jh applications list`

Compatibility wrappers stay until parity is proven in CI and local smoke runs.

## 8. Feature Scope Triage

### v3.0 must do

- Stage boundary rewrite
- Multi-repository protocol layer plus `UnitOfWork`
- Config fingerprinting and run metadata
- `ai_scores` compatibility strategy
- Ordered migration runner with backup points
- CLI regrouping with old-command compatibility
- Email Router minimal version: ingest, dedupe, thread merge, review queue, optional high-confidence reconciliation
- Interview prep and scheduler integration into v3 architecture

### v3.1 can do

- Platform-specific auto-apply for Greenhouse and Lever, default dry-run
- Archetype framing as a bounded enhancement to analysis/material generation
- Feedback loop reports using `outcome_events`
- Tracer Links experimental implementation

### Postpone to later

- Generic LLM-based auto-apply
- Web Dashboard
- Realtime SSE progress UI
- Broad LLM provider mesh with complex fallback graphs
- Fine-grained tracer analytics

### Specific feature decisions

#### Email Router

Priority: high for v3.0, but minimal safe version only.

#### Auto-Apply

Priority: medium. Keep explicit and operator-triggered. Do not put generic auto-apply in v3.0.

#### Tracer Links

Priority: low. Not required to unblock migration or improve correctness.

#### Archetype framing

Priority: medium. Useful, but should not expand scope into a new narrative framework project.

#### Feedback Loop

Priority: medium. Build on top of new outcome/event tables after v3 state tracking stabilizes.

#### Web Dashboard

Priority: low. Useful, but not needed before the data model and CLI stabilize.

## 9. Risk Register

| Risk | Trigger | Impact | Detection | Mitigation | Rollback / Fallback |
|------|---------|--------|-----------|------------|---------------------|
| `ai_scores` removed too early | schema cleanup runs before consumer migration | old stats/views/scripts break | smoke failures on old CLI and SQL views | keep compatibility table/view and dual-write | restore old table or disable new scoring path |
| dual-write divergence | field mapping mismatch between `stage_scores` and `ai_scores` | inconsistent stats and thresholds | parity harness mismatch | stage-specific dual-write tests | disable `V3_STAGE_SCORING` |
| analysis overwrite | rerun logic updates rows destructively | loss of previous analysis | unexpected drop in analysis revision count | append-only revisions | reactivate previous revision |
| validation still duplicated | old paths still call validator internally | inconsistent pass/fail behavior | duplicate validation logs or mismatched results | centralize blocking validation in one stage | keep old render path until duplicates are removed |
| render/publish confusion | same stage writes both artifacts and ready-to-send state | hard-to-recover partial outputs | missing or mismatched output files | split stages and record material set hashes | rerun publish from last good render |
| email dedupe miss | Gmail headers vary or message ids missing | duplicate classifications and updates | duplicate message count spike | use message id plus normalized fingerprint | pause reconciliation and keep ingest only |
| wrong email-to-job match | recruiter emails are ambiguous | wrong application updated | review rejection rate spikes | evidence-based matching plus manual review queue | disable auto reconciliation |
| legacy DB facade mismatch | old imports expect methods not implemented by facade | runtime failures in old scripts | wrapper smoke tests | keep path stable and migrate method-by-method | point facade back to legacy implementation |
| config fingerprint instability | merge order or secret source metadata changes | reruns create false changes | same config yields different fingerprints | canonical serialization rules | temporarily fall back to explicit config version tag |
| migration interruption | schema/backfill step fails mid-run | half-upgraded DB | schema guard failure | ordered migrations plus backup points | restore latest backup |
| CI cutover too early | workflow switches before wrappers are stable | automated pipeline outage | GitHub Actions failures | keep old entrypoints until parity | revert workflow to old command |
| auto-apply mis-submission | DOM drift or bad field mapping | unintended application submission | screenshot review mismatch | keep dry-run default and whitelist targets | disable `AUTO_APPLY_ENABLED` |

## 10. Concrete Design Diff

1. Replace `single JobRepository` with `JobQueryRepo + StageStateRepo + ApplicationRepo + MaterialRepo + EmailRepo + RunMetaRepo + UnitOfWork`.
2. Replace direct `src.db.job_db` coupling with a compatibility facade over legacy and v3 adapters.
3. Replace `Import -> Filter -> Score -> Analyze -> Validate -> Render -> Prepare -> Track` with `Ingest -> Filter -> Score -> Analyze -> Validate -> Render -> Publish -> Email Sync -> Email Classify -> Reconcile -> Auto-Apply`.
4. Replace `Prepare stage includes auto-apply` with separate `publish_materials` and `execute_auto_apply`.
5. Replace validator calls inside analyzer and renderer with one canonical blocking `validate_material_spec` stage.
6. Replace `drop ai_scores` with `retain ai_scores as compatibility surface backed by stage_scores dual-write or compatibility view`.
7. Replace `drop feedback/config_snapshots` with `freeze legacy tables and add outcome_events/config_run_snapshots`.
8. Replace `versioned IF NOT EXISTS` schema handling with ordered migrations, schema version tracking, backup points, and backfills.
9. Replace overloaded `track` CLI with `applications`, `inbox`, and `admin`.
10. Replace narrow ConfigManager with resolved config loading for base, private, and integration config plus fingerprinting.
11. Replace generic `LLMClient.analyze/generate` with task-specific `analyze_job` and `classify_email` protocols.
12. Replace generic `BrowserClient` with separate render and auto-apply contracts.
13. Replace implicit stage state in tables with explicit `stage_executions` and checkpoints.
14. Replace destructive application status updates with append-only `application_events` plus current-state projection.
15. Replace email classification as a future extra with a first-class inbox workflow and review queue.
16. Replace "interview prep/scheduler kept unchanged" with explicit v3 architectural ownership under `domain/services/cli`.
17. Replace generic auto-apply ambition in v3.0 with platform-specific dry-run auto-apply in v3.1.
18. Replace Tracer Links as a core v3.0 feature with a deferred v3.1 experimental feature.
19. Replace direct overwrite of analysis/render outputs with revisioned analysis and hash-based material sets.
20. Replace assumption that old scripts can be deleted with a wrapper-based compatibility period until parity and rollback windows close.

## Implementation Notes

- This proposal assumes a single-user system and favors pragmatic migration safety over framework-heavy infrastructure.
- This proposal intentionally does not recommend Alembic. For this project, ordered handwritten migrations plus schema version tracking are sufficient and lower-overhead unless schema churn becomes substantially higher.
- Inference: existing `feedback` and `config_snapshots` tables appear underused, but they should be frozen first and removed only after usage verification.
