# Job Hunter v3.0 Architecture — Review Brief

**Date**: 2026-03-26
**Author**: Claude Opus 4.6 + Fei Huang (collaborative design session)
**Purpose**: Complete context for external review before implementation begins
**Design Doc**: `docs/plans/2026-03-26-v3-architecture-design.md`

---

## Situation

### The Current System (Job Hunter v2.0)

Job Hunter is a Python-based job automation system built for a single user (Fei Huang, M.Sc. AI, targeting DE/MLE roles in the Netherlands). It implements a full pipeline: scrape LinkedIn/ATS boards → hard-filter → rule-score → AI analyze (Claude Opus) → generate tailored resume + cover letter → track applications.

**Production stats**: ~11,600 lines of Python, 8 DB tables + 4 views, SQLite + Turso cloud sync, GitHub Actions CI/CD (2-3x daily), 50+ verified resume bullets with narrative role tags.

**Key strengths we must preserve**:
- Bullet Library system (v4.0): 50+ experience bullets with narrative roles (context_setter, depth_prover, foundation) — more sophisticated than either competitor
- Resume Validator: 5 categories of blocking rules preventing AI hallucination in resumes
- 7-stage interview preparation workflow with company GitHub org search, interviewer paper analysis
- Interview scheduling with 3D energy model (candidate state + interviewer state + strategy bonus)
- Strict AI scoring calibration (explicit distribution targets: 9-10 rare <5%, 5-6 most common 30-40%)
- CI/CD pipeline running scrape+filter+score automatically

**Key weaknesses driving the refactor**:

| Problem | Evidence | Impact |
|---------|----------|--------|
| Tight DB coupling | 5 modules hardcode `from src.db.job_db import JobDatabase` | Cannot unit test any module in isolation |
| Duplicate validation | ResumeValidator instantiated in both ai_analyzer.py AND resume_renderer.py | Inconsistent validation, wasted CPU |
| Monolithic CLI | `main()` in job_pipeline.py is 150+ lines, 30+ argparse options | Cannot test individual commands |
| Scattered config | 5 modules each implement `_load_config()` with independent `yaml.safe_load()` | No config validation, no versioning, inconsistent error handling |
| No post-application automation | Gmail client exists but not integrated into pipeline | Manual email checking, manual status updates |
| No web UI | Only CLI + basic HTML checklist server | No visual analytics, no kanban, no real-time progress |
| Dead schema | 3 unused tables (ai_scores, feedback, config_snapshots) | Technical debt, confusion |

### Two Competing Systems Analyzed

We conducted deep research on two external job automation projects to inform our strategy.

#### 1. Job-Ops (github.com/DaKheera47/job-ops)

**Profile**: Full-stack TypeScript web app. 2,312 GitHub stars. React 18 + Express + SQLite. Docker deployment. AGPL v3 + Commons Clause license. 3.5 months old, actively maintained.

**Architecture**: Monorepo (orchestrator, shared, extractors, docs-site). 7 job board extractors. LLM abstraction supporting 7 providers (OpenAI, Gemini, Ollama, etc.). RxResume v4 integration for PDF generation. SSE for real-time pipeline progress.

**Standout features**:
- **Tracer Links**: Injects tracking redirects into resume PDF links. Knows if recruiters clicked your GitHub/portfolio. Privacy-safe (hashed IPs, bot filtering). Analytics dashboard. *No other job tool does this.*
- **Email Smart Router**: Gmail OAuth + AI classifies recruiter emails (interview/rejection/offer) → auto-matches to applied jobs → auto-updates application status.
- **Ghostwriter**: Per-job AI chat assistant with branch-aware conversation threading. Cover letters, interview prep, outreach drafts.
- **Web Dashboard**: Full analytics (apps/day, conversion funnel, response rate by source), kanban board, settings panel, keyboard shortcuts.
- **LLM Provider Abstraction**: 7 providers with fallback chains, retry policies, structured JSON output. Can use local models.

**Weaknesses relative to us**:
- AI scoring is simpler: single 0-100 score vs our multi-stage (rule pre-score + multi-dimensional AI analysis with calibration)
- Resume generation delegates to external RxResume service (dependency risk)
- No interview preparation workflow
- No interview scheduling
- No bullet library or narrative role system
- License is restrictive (AGPL + Commons Clause: cannot sell or host commercially)

#### 2. Career-Ops (santifer.io/career-ops-system)

**Profile**: Personal Claude Code skill-based system. NOT open source. Documented as technical case study. Runs on Claude Max 20x plan ($200/month). 2 months in production. 631 evaluations, 354 PDFs generated, 68 applications sent.

**Architecture**: 12 Claude Code skill files (modes) with flat-file storage (TSV + Markdown). No database. Puppeteer for PDF rendering. tmux for batch parallelism via conductor + worker pattern.

**Standout features**:
- **"CV is an argument, not a document"**: 6 resume archetypes (AI Platform/LLMOps, Agentic Workflows, Technical PM, Solutions Architect, FDE, Transformation Lead). Same truthful content, different narrative framing per role type.
- **Auto-Apply**: Playwright-driven interactive form filling and submission.
- **Gate-Pass Dimensions**: Role Match + Skills Alignment act as hard vetoes — failure overrides other strong scores. Elegant hybrid of hard filter + soft scoring.
- **Modes over Monolith**: 12 focused skill files with isolated context outperform a single large system prompt. Empirically validated.
- **Zero marginal cost**: Flat $200/month regardless of evaluation volume.

**Weaknesses relative to us**:
- Not open source — cannot clone or fork
- No database — flat files (TSV) can't support analytics or complex queries
- No CI/CD — everything runs locally via Claude Code
- No cover letter generation mentioned
- No interview preparation workflow
- Dependent on Claude Code platform for all orchestration

---

## Task

**Strategic question**: Should we (a) clone Job-Ops and customize, (b) clone Career-Ops and customize, or (c) selectively absorb the best ideas into our existing system?

**Architectural question**: If absorbing, what architecture enables both the refactoring of current weaknesses AND the addition of new features?

**Success criteria**:
1. Resolve all 7 identified weaknesses (DB coupling, duplicate validation, monolithic CLI, scattered config, no post-app automation, no web UI, dead schema)
2. Absorb highest-value features from both competitors
3. Preserve all existing competitive advantages (bullet library, resume validator, interview prep, scheduling, CI/CD)
4. Enable incremental migration — system must remain functional throughout refactoring
5. Keep Python stack (no language rewrite)

---

## Actions

### Decision 1: Selective Absorption (not cloning)

**Rejected: Clone Job-Ops**
- Complete tech stack change (Python → TypeScript) = discard 11,600 lines of production code
- Lose bullet library, resume validator, interview prep, scheduling — all deeply integrated
- AGPL + Commons Clause license is restrictive
- Their AI layer is actually simpler than ours
- Would take weeks to port our unique features back in

**Rejected: Clone Career-Ops**
- Not open source — literally cannot clone
- Architecture couples to Claude Code Max subscription
- Flat-file storage is a regression from our SQLite + Turso
- No CI/CD capability

**Chosen: Absorb into Job Hunter v3.0**
- Keep all 11,600 lines of working Python
- Selectively add 5 highest-value features
- Incremental migration, low risk

### Decision 2: Architecture — "Stage Engine" pattern

**Rejected: "Clean Pipeline" (conservative refactor-in-place)**
- Keeps job_pipeline.py as 1300+ line monolith
- Stages still coupled through DB
- Cannot parallelize or pause/resume pipeline

**Rejected: "Hybrid Agent" (Python + Claude Code orchestration)**
- CI/CD cannot run Claude Code (GitHub Actions)
- Loses type safety and unit testability
- Debugging moves from code to prompts

**Chosen: "Stage Engine" (pipeline as composable stages)**
- Each pipeline step is an independent Stage class with clear inputs/outputs
- PipelineRunner orchestrates stages sequentially
- All dependencies injected via Protocol pattern
- New features = new Stages or new Services

### Decision 3: Priority — C → A → B

**C (Code Quality)**: Dependency injection, Protocol pattern, ConfigManager, Typer CLI, ValidateStage deduplication
**A (Automation)**: Email Smart Router, Auto-Apply, Tracer Links, Feedback Loop
**B (Visualization)**: Web Dashboard (FastAPI + htmx) — future phase

Rationale: Current tight coupling means adding any new feature increases technical debt. Fix the foundation first, then build features safely.

### Design Sections Approved

**Section 1 — Core Infrastructure**:
- `protocols.py`: JobRepository, LLMClient, BrowserClient Protocol classes
- `config.py`: ConfigManager with pydantic validation, replacing 5 independent `_load_config()` calls
- `database.py`: SQLiteJobRepository implementing JobRepository Protocol

**Section 2 — Stage Engine**:
- Stage ABC with `run()`, `can_run()`, `name` interface
- StageResult dataclass for uniform output
- 8 stages: Import → Filter → Score → Analyze → Validate → Render → Prepare → Track
- PipelineRunner with chainable `.add()` and sequential `.run()`
- ValidateStage as standalone stage (resolves duplicate ResumeValidator problem)

**Section 3 — Services Layer**:
- LLM abstraction: ClaudeClient (production) + OllamaClient (dev/cheap tasks)
- Resume services: BulletLibrary (extracted from ai_analyzer), Validator (single instance), Renderer (injected BrowserClient)
- 5 new services: EmailRouter, AutoApplier, TracerLinkService, Archetype framing, FeedbackLoop

**Section 4 — CLI + Data Flow + Migration**:
- Typer CLI with 4 command groups: pipeline, analyze, apply, track
- Backward-compatible wrapper in scripts/job_pipeline.py (CI/CD unchanged during migration)
- Dependency injection centralized in deps.py
- DB schema: drop 3 unused tables, add 2 new tables, 1 column addition
- 4-phase migration: Foundation → Stages → CLI → New Features

**Section 5 — New Features**:
- Email Smart Router: Gmail IMAP + LLM classification → auto-update application status
- Auto-Apply: Playwright form filling, Phase 1 (Greenhouse/Lever) → Phase 2 (Workday) → Phase 3 (generic). dry_run=True default.
- Tracer Links: Redirect URLs in resume PDFs, Cloudflare Worker, privacy-safe analytics
- Archetype Framing: bullet_library.yaml extended with per-archetype bullet_priority + skill_emphasis + bio_angle
- Feedback Loop: Track AI score → actual outcome correlation. After 50+ data points, generate accuracy report for manual threshold adjustment. "Automate analysis, not decisions."

---

## Results (Expected)

### Architecture Comparison: v2.0 → v3.0

| Dimension | v2.0 | v3.0 Target |
|-----------|------|-------------|
| Modularity | 5/10 — tight DB coupling | 9/10 — Protocol injection |
| Testability | 4/10 — cannot mock DB | 9/10 — mock repo/llm/browser |
| Extensibility | 6/10 — config-driven filters good, rest poor | 8/10 — new feature = new Stage or Service |
| CLI | 4/10 — monolithic 150-line main() | 8/10 — Typer command groups |
| Automation | 6/10 — scrape/filter/score auto, rest manual | 8/10 — email tracking, auto-apply |
| AI Sophistication | 8/10 — strong prompts, validation | 9/10 — + LLM abstraction, archetypes, feedback loop |
| UX | 5/10 — CLI only | 5/10 (Phase 3-4 will add dashboard) |

### File Migration Map

```
OLD                                 →  NEW
────────────────────────────────────────────────────────
src/db/job_db.py                    →  src/core/database.py
(new)                               →  src/core/protocols.py
(new)                               →  src/core/config.py
src/ai_analyzer.py                  →  src/stages/analyze_stage.py
                                       + src/services/llm/claude.py
                                       + src/services/resume/bullet_library.py
src/resume_renderer.py              →  src/stages/render_stage.py
                                       + src/services/resume/renderer.py
src/resume_validator.py             →  src/stages/validate_stage.py
                                       + src/services/resume/validator.py
src/cover_letter_generator.py       →  src/stages/render_stage.py (merged)
  + src/cover_letter_renderer.py       + src/services/cover_letter.py
src/checklist_server.py             →  src/stages/prepare_stage.py
src/gmail_client.py                 →  src/services/email_router.py (enhanced)
src/google_calendar.py              →  src/services/google_calendar.py (unchanged)
src/interview_scheduler.py          →  src/services/interview_scheduler.py (unchanged)
src/scrapers/*                      →  src/scrapers/* (unchanged)
scripts/job_pipeline.py             →  src/cli/* (split) + scripts/job_pipeline.py (compat)
config/*                            →  config/* (unchanged)
assets/*                            →  assets/* (unchanged, bullet_library extended)
```

### Implementation Phases

```
Phase 0: Foundation                    (no feature change, no risk)
  ├── src/core/protocols.py
  ├── src/core/config.py
  └── src/core/database.py
  └── Validate: old pipeline still works

Phase 1: Stage Migration               (one at a time, validate after each)
  ├── FilterStage
  ├── ScoreStage
  ├── ImportStage
  ├── AnalyzeStage
  ├── ValidateStage
  ├── RenderStage
  └── PrepareStage
  └── Validate: `jh pipeline run` produces same results as old `--process`

Phase 2: CLI Migration
  ├── src/cli/ (Typer)
  ├── scripts/job_pipeline.py → thin compat wrapper
  └── CI/CD workflow updated

Phase 3: New Features
  ├── Email Smart Router (TrackStage)
  ├── Auto-Apply (PrepareStage enhancement)
  ├── Tracer Links (RenderStage enhancement)
  ├── Archetype framing (BulletLibrary enhancement)
  └── Feedback Loop

Phase 4: Web Dashboard (future)
  ├── FastAPI + htmx
  ├── Funnel charts, kanban board
  └── Real-time pipeline progress (SSE)
```

### Features NOT Absorbed (and Why)

| Feature | Source | Rejection Reason |
|---------|--------|-----------------|
| RxResume integration | Job-Ops | External service dependency; our Jinja2 + Validator is more controllable and self-contained |
| Ghostwriter chat | Job-Ops | Claude Code itself serves as our AI assistant; redundant to embed another |
| Visa sponsor matching | Job-Ops | UK-focused; we handle NL visa filtering via hard rules already |
| tmux parallelism | Career-Ops | GitHub Actions + Python asyncio is more appropriate for our CI/CD model |
| Flat-file storage | Career-Ops | Regression from SQLite + Turso; cannot support analytics or complex queries |
| Demo/onboarding mode | Job-Ops | Single-user personal tool; no onboarding needed |
| Docusaurus docs site | Job-Ops | CLAUDE.md + design docs sufficient for personal project |

---

## Review Checklist for Codex

Please evaluate this design against the following criteria:

1. **Completeness**: Does the design address all 7 identified weaknesses?
2. **Preservation**: Are all existing competitive advantages (bullet library, resume validator, interview prep, scheduling, CI/CD) preserved?
3. **Feasibility**: Is the migration strategy realistic? Are there hidden dependencies or ordering issues?
4. **Over-engineering**: Is any part of the design more complex than necessary? (YAGNI check)
5. **Protocol design**: Are the JobRepository, LLMClient, BrowserClient interfaces sufficient? Missing methods?
6. **Stage boundaries**: Are the 8 stages correctly scoped? Should any be merged or split further?
7. **New features**: Are Email Router, Auto-Apply, Tracer Links, Archetypes, Feedback Loop well-designed? Missing edge cases?
8. **Risk**: What could go wrong during migration? What's the rollback plan?
9. **Consistency**: Does the CLI command structure make sense? Any naming conflicts?
10. **Schema changes**: Are the 3 table drops + 2 table adds + 1 column add safe? Data loss risk?
