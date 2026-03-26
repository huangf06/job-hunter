# Phase 3: Feedback Loop — Decisions

**Date**: 2026-03-26
**Status**: Final
**Depends on**: Phase 2 (pipeline must be running daily to generate application data)

---

## 3.1 What Outcomes Matter

**Decision: 7-state model with timeout-based auto-transitions.**

```
                    ┌─────────────────────────────────────┐
                    │                                     ▼
applied ──→ no_response_14d ──→ ghosted
   │
   ├──→ rejected
   │
   ├──→ phone_screen ──→ rejected
   │                  ──→ technical ──→ rejected
   │                                ──→ onsite ──→ rejected
   │                                            ──→ offer ──→ accepted
   │                                                      ──→ declined
   └──→ withdrawn (user cancels)
```

**States:**

| State | Trigger | Auto-transition |
|-------|---------|-----------------|
| `applied` | `--mark-applied` or checklist | → `no_response_14d` after 14 days |
| `no_response_14d` | Auto (timer) | → `ghosted` after 30 more days |
| `rejected` | User input or email parse | Terminal |
| `phone_screen` | User input | None |
| `technical` | User input | None |
| `onsite` | User input | None |
| `offer` | User input | None |
| `accepted` | User input | Terminal |
| `declined` | User input | Terminal |
| `withdrawn` | User input | Terminal |
| `ghosted` | Auto (44 days total) | Terminal |

**Where does outcome data come from?**

Phase 3.0 (now): **Manual only**, via two methods:
1. **Telegram command**: `/status COMPANY_NAME phone_screen` — user types this when they get an email
2. **CLI**: `python scripts/job_pipeline.py --update-status JOB_ID phone_screen`

Phase 3.1 (later): Semi-automated email parsing. See Phase 5 for prerequisites.

**Why not auto-parse emails now?** Gmail parsing requires:
- OAuth scope for reading email bodies (privacy-sensitive)
- LLM classification of recruiter emails (cost)
- Job-to-email matching heuristics (complex, error-prone)
- Manual review queue for uncertain matches

This is 2-3 weeks of work. Getting manual status tracking right first gives us the schema and state machine that email parsing will plug into later.

---

## 3.2 Minimum Viable Feedback Loop

**Decision: Telegram command + weekly digest + monthly conversion report.**

### Daily (passive)
Auto-transitions run during each CI pipeline run:
- `applied` → `no_response_14d` after 14 days
- `no_response_14d` → `ghosted` after 30 more days

### On-demand (user-triggered)
Telegram command: `/status COMPANY_NAME STATE`
- Fuzzy-matches company name against DB
- Updates state, records timestamp
- Confirms: "Updated: Picnic → phone_screen (applied 2026-03-10)"

### Weekly digest (Sunday evening, Telegram)
```
📊 Week of 2026-03-20

Active: 23 applications
  • 3 in interview process (Picnic phone_screen, ABN technical, Booking onsite)
  • 5 no response (> 7 days)
  • 2 rejected this week

Pipeline: 12 new resumes generated, 8 submitted

Stale (> 14 days, no update): 7 applications
  → Consider following up or marking as ghosted
```

### Monthly conversion report (1st of month, Telegram)
```
📈 March 2026 Report

Applications: 32 submitted
Screen rate: 12.5% (4/32 got phone screens)
Interview rate: 6.3% (2/32 reached technical)
Offer rate: 0% (0/32)

By AI score bracket:
  • 7.0+: 3 applied → 2 screens (67%) ← high-score jobs convert
  • 5.5-6.9: 18 applied → 2 screens (11%)
  • 4.0-5.4: 11 applied → 0 screens (0%) ← consider raising threshold

Top converting sources: LinkedIn (3/20), Greenhouse (1/8)

Time to first response: median 8 days
```

---

## 3.3 How Feedback Improves the Pipeline

**Decision: Analytics for human decision-making, not automated threshold adjustment.**

After 50+ data points with outcomes:
1. **Score calibration report**: Compare AI score distributions between jobs that got interviews vs. didn't. If 7.0+ jobs convert at 50% but 5.0-6.0 convert at 2%, the user can decide to raise the generation threshold.

2. **Bullet effectiveness signal**: If jobs where bullet `glp_decision_engine` was included get more callbacks than jobs where it wasn't, surface this in the monthly report. The user decides whether to adjust `recommended_sequences`.

3. **Source quality signal**: If Greenhouse jobs convert 3x better than LinkedIn Easy Apply, surface this. The user decides whether to prioritize Greenhouse scraping.

**Why not automate threshold adjustment?**
- Sample size is too small (32 applications/month, 4 screens) for statistically significant conclusions
- Confounding variables everywhere (job market changes, resume quality improvements, seasonal hiring)
- Wrong auto-adjustment could reduce application volume during a critical period
- "Automate analysis, not decisions" — the user is the strategist

**Schema addition** (single table):

```sql
CREATE TABLE application_events (
    id INTEGER PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES jobs(id),
    state TEXT NOT NULL,           -- 'applied', 'phone_screen', 'rejected', etc.
    source TEXT DEFAULT 'manual',  -- 'manual', 'auto_timer', 'email_parse'
    note TEXT,                     -- optional context
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(job_id, state, created_at)
);
```

Current state is derived by: `SELECT state FROM application_events WHERE job_id = ? ORDER BY created_at DESC LIMIT 1`

This is append-only — we never lose history. The existing `applications` table continues to work for backward compatibility; `application_events` adds the event log on top.

---

## Phase 3 Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| State model | 7 states + auto-transitions | Covers real-world application lifecycle |
| Data entry (v3.0) | Manual via Telegram + CLI | Simple, reliable, no OAuth complexity |
| Data entry (v3.1) | Semi-auto email parsing | Requires stable state machine first |
| Weekly digest | Telegram, Sunday evening | Keeps user aware without being noisy |
| Monthly report | Telegram, 1st of month | Conversion analytics by score bracket |
| Feedback → pipeline | Reports for human decision | Sample too small for auto-adjustment |
| Schema | Append-only `application_events` | Never lose history; backward-compatible |
