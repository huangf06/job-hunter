# Phase 2: Application Pipeline — Decisions

**Date**: 2026-03-26
**Status**: Final
**Depends on**: Phase 1 (resume generation must work)

---

## 2.1 Minimal Viable Daily Pipeline

**Decision: Fully automated through "publish", human checkpoint before applying.**

```
CI (cron 3x weekday, 1x weekend)
├── 1. Scrape (LinkedIn + ATS + IamExpat)          ← automated, existing
├── 2. Filter (hard rules)                          ← automated, existing
├── 3. Score (rule-based, >= 3.0 passes)            ← automated, existing
├── 4. AI Analyze (Claude Opus, <= 20 jobs/run)     ← automated, RE-ENABLE
├── 5. Validate (ResumeValidator)                   ← automated, new explicit step
├── 6. Render (HTML → PDF, resume + optional CL)    ← automated, existing code
├── 7. Publish (upload materials to cloud storage)   ← NEW
└── 8. Notify (Telegram summary)                    ← automated, existing
```

**Per-step details:**

| Step | Runs in | Human needed? | Failure mode | Recovery |
|------|---------|---------------|--------------|----------|
| Scrape | CI | No | Partial scrape (some sources fail) | Other sources still proceed; retry next run |
| Filter | CI | No | None (pure logic) | Rerun |
| Score | CI | No | None (pure logic) | Rerun |
| AI Analyze | CI | No | API rate limit / budget | Skip job, retry next run; save sentinel to avoid re-processing |
| Validate | CI | No | Validation failure | Skip job, log warning; fix bullet_library if systematic |
| Render | CI | No | Playwright crash | Retry once; skip job on second failure |
| Publish | CI | No | Upload failure | Retry; materials remain in output/ |
| Notify | CI | No | Telegram API down | Log error, pipeline still succeeds |

**Human checkpoint**: After notification. User reviews the Telegram summary ("5 new resumes ready: Company A (8.2), Company B (7.1), ..."), then decides whether to apply. No human action needed for the pipeline to run.

**Notification content** (Telegram):
```
📊 Pipeline Run 2026-03-26 08:23

Scraped: 42 new jobs
Filtered: 18 passed
Scored: 12 above threshold
AI Analyzed: 8
Resumes Ready: 5

Top matches:
• Company A — Senior DE — 8.2 ⭐
• Company B — MLE — 7.1
• Company C — Data Engineer — 6.8

📁 Materials: [link to cloud folder or checklist URL]
```

---

## 2.2 The "Prepare → Apply → Finalize" Workflow

**Decision: Option B — CI generates + publishes a cloud checklist, user marks status via Telegram or web form.**

**Current flow (local)**:
```
User runs --prepare → generates resumes locally → starts local HTTP server
→ user clicks checkboxes → runs --finalize → archives + syncs DB
```

**New flow (cloud-native)**:
```
CI runs pipeline → renders materials → uploads to Cloudflare R2 (free tier)
→ generates static checklist HTML → uploads to R2
→ sends Telegram link to checklist
→ user opens checklist in browser, marks applied/skipped
→ next CI run reads checklist state → finalizes (archive + DB update)
```

**Why Cloudflare R2**:
- Free: 10 GB storage, 10M reads/month, 1M writes/month (vastly exceeds our needs)
- S3-compatible API (boto3 works out of the box)
- No egress fees
- Simple: no server needed, just object storage + static HTML

**How the user actually applies**: Opens the job posting in browser, uploads the PDF from R2 link (or downloads it first), fills in application form manually. This hasn't changed — the pipeline generates materials, the human submits them.

**Checklist implementation**: Replace the local `checklist_server.py` with a static HTML page that:
- Lists jobs with scores, links to PDF materials on R2
- Has checkboxes (state saved to `state.json` on R2 via simple PUT)
- Works on mobile (user applies from phone sometimes)
- No server needed — pure client-side JS + R2 API

**Finalize**: Next CI run (or `--finalize` locally) reads `state.json` from R2, marks jobs as applied/skipped in DB.

**Action items**:
1. Add Cloudflare R2 bucket (free tier) — store in GitHub secrets
2. Add upload step to CI: upload PDFs + checklist HTML to R2
3. Rewrite `checklist_server.py` → `checklist_generator.py` (static HTML, no server)
4. Add `state.json` read-from-R2 logic to `--finalize`
5. Keep `--prepare` working locally as fallback (for offline use)

---

## 2.3 Database: Keep Turso or Migrate?

**Decision: Turso HTTP-only. Drop embedded replica entirely.**

**Analysis of current pain**:
- `job_db.py` is 1,777 lines, of which ~400-500 lines (~25%) are Turso embedded replica workarounds
- `WalConflict` recovery handler, Windows health checks, connection retry with exponential backoff, batch mode sync suppression, stale replica detection, dead stream masking
- All of this complexity exists because of `libsql` embedded replica mode + Windows bugs

**What Turso HTTP-only means**:
- Both CI and local use Turso's HTTP API (`https://<db>.turso.io`)
- No local `.db` file, no `-wal`, no `-shm`, no `-info`, no `-client_wal_index`
- No sync, no replica, no `WalConflict`, no Windows libsql bugs
- Simple HTTP requests: `POST /v2/pipeline` with SQL statements
- Latency: ~50-100ms per query (fine for batch operations on few thousand rows)
- Free tier: 9 GB storage, 500 databases, 25M row reads/month

**What we delete**:
- All `_try_sync()` / `_sync_to_turso()` / `_sync_from_turso()` code
- `WalConflict` recovery handler
- Windows health check fallback
- `batch_mode()` sync suppression
- `TURSO_SYNC_MODE` config
- Local `.db` file management
- `final_sync()` calls throughout the pipeline

**What we keep**:
- All 103 DB methods (queries, CRUD, views)
- Table schemas
- SQL logic

**New DB client** (~50 lines):
```python
import httpx

class TursoDB:
    def __init__(self, url: str, token: str):
        self.url = url
        self.token = token
        self.client = httpx.Client(...)

    def execute(self, sql: str, params: list = None) -> list[dict]:
        # POST to Turso HTTP API
        ...

    def execute_batch(self, statements: list) -> list:
        # Batch multiple statements in one HTTP call
        ...
```

**Migration path**:
1. Write `TursoHTTPClient` (~50 lines)
2. Adapt `JobDatabase` to use HTTP client instead of `libsql` connection
3. Delete all sync/replica/recovery code (~400 lines)
4. Test with existing CI workflow
5. Remove `libsql-experimental` from `requirements.txt`

**Why not other options**:

| Option | Rejected because |
|--------|-----------------|
| Keep embedded replica | 400 lines of workarounds, Windows bugs, complexity |
| Supabase/Postgres | Over-engineered for few thousand rows; migration risk; new dialect |
| SQLite in git | Binary conflicts; CI needs push access; git history bloat |
| Cloudflare D1 | Another provider to manage; Turso already works |
| Plain local SQLite | Loses cloud sync; CI and local can't share data |

---

## Phase 2 Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Pipeline automation | Full CI automation through render+publish | Human only needed for actual application submission |
| Human checkpoint | Telegram notification + cloud checklist link | No local commands needed for normal daily operation |
| Material hosting | Cloudflare R2 (free tier) | Static file hosting, S3-compatible, no egress fees |
| Checklist | Static HTML on R2 (no server) | Mobile-friendly, works anywhere |
| Database | Turso HTTP-only | Eliminates 400+ lines of sync workaround code |
| Local fallback | Keep `--prepare` working | For offline use or debugging |
| Immediate action | Write `TursoHTTPClient`, delete sync code | Biggest simplification win |
