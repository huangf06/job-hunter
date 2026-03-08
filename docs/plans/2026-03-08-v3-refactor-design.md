# Job Hunter v3.0 Refactor Design

Date: 2026-03-08

## Context

Based on deep analysis of 2,433 scraped jobs, 349 applications, and 15 real interviews (from `interview_rounds` table), the system needs optimization across 4 areas.

### Key Data Points

- End-to-end funnel: 2,433 scraped → 1,117 filtered → 429 applied → 15 interviews → 0 offers
- Interview rate: 3.5% of applied (15/429)
- Ghost rate: 81.4% (284/349 applied with no response)
- `data_science` profile: 16 applied, 0 interviews → drop
- `backend_engineering`: 448 scraped, 8 applied (1.8%) → pure noise
- Greenhouse ATS + IamExpat: 611 scraped, 11 applied, 0 interviews
- All 15 interviews came from LinkedIn

### Interview Distribution by Role Type

| Role Type | Interviews | Example Companies |
|-----------|-----------|-------------------|
| Data Engineer | 7 | Sensorfact, elipsLife, Deloitte, Source.ag, Swisscom, Nebius |
| ML/AI Engineer | 4 | FareHarbor, kaiko.ai, Elsevier, Springer Nature |
| Software Engineer (Data/AI) | 2 | Source.ag, TomTom |
| Quant | 2 | Supergrads, Maisha Mazuri |

---

## 1. Search Keyword Optimization

### Priority Tiers (data-driven, by interview count)

| Priority | Profile | Keywords | Daemon Frequency | Interviews |
|----------|---------|----------|-----------------|------------|
| **P0** | `data_engineering` | Data Engineer, Analytics Engineer, Data Platform Engineer, Big Data Engineer | Every 1h | 7 |
| **P0** | `ml_engineering` | ML Engineer, AI Engineer, AI Software Engineer, MLOps Engineer | Every 1h | 4 |
| **P1** | `backend_ai_data` | Software Engineer (AI/Data context), Python Developer | Every 2h | 2 |
| **P1** | `ml_research` | Research Engineer, Applied Scientist | Every 2h | 2 (from 3 applied = 66.7%) |
| **P2** | `quant` | Quantitative Researcher/Developer/Analyst | Every 6h | 2 (can scrape, not primary) |
| **P2** | `backend_engineering` | Backend Engineer, Software Engineer (narrowed, remove "Full Stack") | Every 6h | 0 (but legacy had 3) |
| **Drop** | `data_science` | ~~Data Scientist, Data Analyst, BI Engineer, Data Consultant~~ | - | 0 from 16 applied |
| **Demote** | `ats` / `iamexpat` | Greenhouse + Lever + IamExpat | Daily 1x | 0 from 11 applied |

### Actions

- Disable `data_science` profile in `config/search_profiles.yaml`
- Remove "Full Stack Engineer" from `backend_engineering` queries
- Create or adjust `backend_ai_data` profile: Software Engineer + AI/Data context keywords
- Add priority tier field to each profile in YAML config
- Recalibrate AI scorer: backend/infra roles scored too conservatively (TomTom AI=2.5, Nebius AI=3.0 both got interviews)

---

## 2. SVG Template Resumes

### Templates (priority order)

1. `resume_data_engineer.svg` — Emphasize ETL/Spark/Airflow/data pipeline experience
2. `resume_ml_engineer.svg` — Emphasize PyTorch/model deployment/MLOps
3. `resume_backend.svg` (later) — Emphasize Python/system design/API
4. `resume_quant.svg` (later) — Emphasize quantitative research/financial data/statistics

### Routing Logic

```
New job → AI analysis (existing flow) → template_fit evaluation
  ├─ template_fit >= 8 → Use SVG template (beautiful, zero delay)
  └─ template_fit < 8  → AI-customized generation (current Jinja2 flow)
```

### AI Integration

Add `template_fit` field to existing AI analyzer output (no extra API call):

```json
{
  "template_fit": {
    "score": 8,
    "best_template": "data_engineer",
    "gaps": ["Kafka experience emphasized but not in template"],
    "verdict": "use_template"
  }
}
```

Decision is AI-driven (not rule-based) because the AI already reads the full JD and can assess nuanced fit. The key question AI answers: "Is sacrificing design polish for content customization worth it for this specific JD?"

---

## 3. Streaming Daemon

### Architecture

```
Job Hunter Daemon (Python + APScheduler)

Scheduler Layer:
  P0 (every 1h): data_engineering, ml_engineering
  P1 (every 2h): backend_ai_data, ml_research
  P2 (every 6h): quant, backend_engineering
  Daily:          ats, iamexpat

          │
          ▼

Per-Job Streaming Pipeline (not batch):
  new_job → hard_filter → rule_score → [ai_analyze] → route
                                                         │
                                    ┌────────────────────┤
                                    ▼         ▼          ▼
                               Telegram   SVG template  AI custom
                               instant    (fit >= 8)    (fit < 8)
                               notify
```

### Incremental Scraping: Single High-Water Mark

Each profile+query stores one watermark (the newest job URL from last scrape).

**Table: `scrape_watermarks`**

| Column | Type | Description |
|--------|------|-------------|
| profile | TEXT | Search profile name |
| query | TEXT | Search query keywords |
| hwm_url | TEXT | URL of newest job from last scrape |
| last_scraped_at | TEXT | Timestamp of last scrape |

**Algorithm:**

```
1. Read HWM for this profile+query
2. Scrape page (LinkedIn r86400 + sortBy=DD)
3. For each job on page:
   - URL == HWM? → STOP (reached last known position)
   - URL in DB?  → skip (dedup)
   - New job     → push through streaming pipeline
4. If HWM not found within max_pages → stop (fallback)
5. Update HWM = first job URL from this scrape
```

**Why Single HWM (not Sliding Window):**
- P0/P1 = 80% of scrape volume, every 1-2h. Job delisting within 1-2h is ~0%. Miss probability negligible.
- P2/daily: even if HWM misses, fallback is scanning max_pages (~30s extra). Low-priority profiles, acceptable cost.
- DB dedup guarantees correctness regardless of HWM strategy.
- Cleaner semantics, easier debugging: one URL to trace, not five.

### Foundation

Build on existing `scripts/scraper_incremental.py` (v3.1) which already has:
- Cookie-based LinkedIn auth
- Anti-detection (resource blocking, user-agent spoofing)
- DB dedup with batch checking
- Per-profile execution
- JD fetching for new jobs only

**GitHub Actions retained as fallback** when local daemon is not running.

---

## 4. Pipeline Decoupling (Cover Letter)

### Remove from Pipeline

- Remove auto CL generation from `--prepare` command
- `ready_to_send/` directory contains resume only (no CL)
- `--ai-analyze` no longer triggers CL generation

### New Independent Command

```bash
python scripts/job_pipeline.py --generate-cl JOB_ID
```

- Manual trigger only
- Generates CL draft for editing
- Standalone operation, not part of any automated flow

### Checklist UI Update

- CL column shows "Not generated" instead of auto-generated low-quality CL
- Remove CL-related fields from checklist state.json
- Simplify prepare flow: sync DB → generate resumes → collect ready jobs → generate checklist → start server

---

## Implementation Priority

1. **Search keyword optimization** — Lowest cost, highest immediate impact (config changes + profile adjustments)
2. **Pipeline decoupling** — Remove CL auto-generation (simplification, not new code)
3. **Streaming daemon** — Core architecture change (APScheduler + HWM + per-job streaming)
4. **SVG template resumes** — Requires design work + AI prompt changes (most effort)
