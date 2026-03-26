# Phase 5: Future Features — Prerequisites

**Date**: 2026-03-26
**Status**: Final
**Rule**: Do not build any of these until Phase 1-4 are stable and the pipeline is running daily.

---

## Feature Prerequisites

| Feature | What must be true first | Earliest possible |
|---------|------------------------|-------------------|
| **Email auto-classification** | Phase 3 `application_events` table works. Gmail OAuth scope includes message body read. At least 50 recruiter emails received and manually categorized as training data for prompt engineering. | 4 weeks after Phase 3 |
| **Auto-apply (Greenhouse/Lever)** | Phase 1 resume generation is reliable (zero validation failures in 2 consecutive weeks). Platform-specific form field mapping documented for top 10 target companies. `dry_run=True` mode implemented and tested. | 6 weeks after Phase 1 |
| **Tracer links in resume PDFs** | Resume PDFs are being generated and submitted consistently. A redirect service exists (Cloudflare Worker or similar) to track link clicks. Privacy policy decided (what data to collect, retention). | After pipeline runs stable for 1 month |
| **Archetype-based resume framing** | `bullet_library.yaml` extended with `archetype_affinity` tags per bullet. At least 3 archetypes defined (DE, MLE, Backend). AI prompt updated to accept archetype parameter. Enough application outcome data to evaluate if different framings convert differently. | 8 weeks after Phase 3 |
| **Web dashboard** | Turso HTTP API is the sole DB access method (Phase 2 complete). `application_events` table populated with 2+ months of data. A clear list of 5 specific questions the dashboard should answer that CLI/Telegram cannot. | 3 months after Phase 2 |
| **Interview prep automation** | Already works as a 7-stage manual workflow. To automate: needs a trigger mechanism (calendar event detection or email classification), and the interview prep output format must be stable (no more schema changes to the 00-09 file structure). | After email classification works |

---

## Feature Dependency Graph

```
Phase 1 (Resume Gen)
  └──→ Auto-Apply (needs reliable PDFs)
  └──→ Tracer Links (needs PDFs being submitted)

Phase 2 (Pipeline + Turso HTTP)
  └──→ Web Dashboard (needs HTTP API)

Phase 3 (Feedback Loop)
  └──→ Email Classification (needs state machine)
       └──→ Interview Prep Automation (needs email triggers)
  └──→ Archetype Framing (needs outcome data)
  └──→ Web Dashboard (needs event data)
```

---

## Features Explicitly Deferred Beyond v3.x

| Feature | Why not | Revisit when |
|---------|---------|-------------|
| **Generic LLM auto-apply** | Every job site has different forms; generic form-filling is an unsolved problem | When a reliable open-source form-filling library exists |
| **Web Dashboard with SSE** | Real-time progress adds infrastructure complexity for a single-user system | When batch sizes exceed 100 jobs/run |
| **Multi-LLM provider mesh** | Claude Opus works; adding fallback chains adds complexity without solving a problem | When Anthropic API has reliability issues |
| **Fine-grained tracer analytics** | Need basic tracer links first; analytics is premature optimization | After 100+ tracked link clicks |

---

## Phase 5 Summary

The priority order for future features, once Phase 1-4 are stable:

1. **Email classification** — highest ROI, automates the most tedious manual work (checking email, updating status)
2. **Auto-apply for Greenhouse/Lever** — saves 5-10 minutes per application for structured ATS platforms
3. **Archetype framing** — improves resume quality per-role-type
4. **Tracer links** — provides signal on recruiter engagement (nice-to-have)
5. **Web dashboard** — visualization (lowest priority, Telegram digests cover 80% of the need)
