# Pipeline Recovery Design — 2026-04-23

## Background

After the 04-01 zone-based template upgrade caused 0 interviews across 77 applications, a revert was executed (04-17) plus a bullet library v6.0 rewrite (04-22). However, **18 commits were never pushed to remote** — CI ran stale code for 6 days, producing 74 polluted analyses with `USE_TEMPLATE` and empty `tailored_resume = '{}'`.

### Phase 0 (completed)

- Pushed 18 commits to remote
- Patched 74 polluted `resume_tier` values → `FULL_CUSTOMIZE`
- 51 jobs now eligible for C2 tailoring
- 0 jobs were applied with bad resumes (applications stopped 04-10)

---

## Phase 1: Full End-to-End Canary (today)

**Goal:** Validate the entire pipeline from keyword search → scrape → filter → AI analyze → resume generation, using fresh jobs from the last 24 hours.

### Step 1: Verify search configuration

- Review `config/search_profiles.yaml` — confirm active profiles, keywords, locations match current job strategy (ML Engineer primary, MLOps hedge, DE fallback per `project_job_search_strategy_2026_04.md`)
- Review `config/target_companies.yaml` — confirm Greenhouse targets are current
- Review `config/base/filters.yaml` — confirm hard rules are sensible

### Step 2: Fresh scrape

```bash
python scripts/scrape.py --all --save-to-db
```

Run LinkedIn + Greenhouse. Confirm new jobs appear in DB.

### Step 3: Process + filter

```bash
python scripts/job_pipeline.py --process
```

Confirm hard filter pass/reject counts look normal.

### Step 4: AI analyze canary batch

```bash
python scripts/job_pipeline.py --ai-analyze --limit 5
```

Run C1+C2 on ~5 fresh jobs. Verify:
- All get `resume_tier = FULL_CUSTOMIZE`
- `tailored_resume` JSON contains `bio`, `experiences`, `projects`, `skills`
- Bio includes company name (Signal 1 from diagnostic)
- Bio opening is JD-tailored (Signal 2)

### Step 5: Resume generation + visual diff

```bash
python scripts/job_pipeline.py --generate
```

Generate PDFs, then compare against reference interview resume (Source.ag or Sensorfact):
- 2-page flow layout
- 15+ bullets with per-job tailoring
- 6 skill categories
- Keyword surface area comparable to reference
- Company name in bio closing

### Step 6: Go/no-go

If 3+ of 5 resumes pass structural check → Phase 1 passes.

---

## Phase 2: Small Batch (day 2 — 3-day window, score >= 6.0)

1. Re-analyze qualifying jobs from last 3 days
2. Generate + spot-check 2-3 resumes
3. Run `--prepare`, apply via checklist, `--finalize`

## Phase 3: Full Blast (day 3 — 7-day window, score >= 5.0)

1. Full batch on 7-day inventory
2. Run `--prepare`, apply, `--finalize`
3. Monitor for interview invitations over following week

---

## Notes

- Phases 2 and 3 may run in separate sessions
- C1 scores from polluted analyses are still valid — only C2 tailoring needs re-running
- 51 existing jobs are eligible for C2 tailor and can be batch-processed alongside fresh canary jobs
