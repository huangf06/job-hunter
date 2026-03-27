# Codex Review Prompt: Block A Scraper Rebuild

## Your Role

You are reviewing a design document for a clean rebuild of the scraping layer (Block A) of a job-hunting automation system. The design is at `docs/plans/2026-03-26-block-a-scraper-rebuild.md`.

## Context

- This is a Python project that scrapes job listings from LinkedIn, Greenhouse, and IamExpat, then runs them through a filter → AI analysis → resume generation pipeline.
- The current scraping code is degraded: CI reports success but no new data has been produced in 6 days. Error handling silently swallows failures.
- Architecture overview is at `docs/architecture-overview.md`.
- Current scraper code is in `scripts/linkedin_scraper_v6.py` (1,207 lines), `scripts/multi_scraper.py`, and `src/scrapers/`.

## What to Review

Please review the design document and provide feedback on:

1. **Completeness** — Are there gaps? Missing edge cases? Anything the design should address but doesn't?
2. **BaseScraper design** — Is the `fetch_jobs() -> list[RawJob]` abstraction right? Does async make sense for all scrapers? Is `ScrapeReport` missing any fields?
3. **LinkedIn split** — Is the 3-file split (scraper / browser / parser) the right decomposition? Too many files? Too few?
4. **Dedup strategy** — Layer 1 (URL hash) + Layer 2 (company+title fuzzy, flag-only). Is this sound? Should Layer 2 be more aggressive?
5. **Error handling** — TransientError vs PermanentError classification. Is the retry strategy (3x exponential backoff) appropriate? Any failure modes not covered?
6. **Observability** — The 4-level severity model (info/critical/success/warning). Is this sufficient for CI?
7. **Migration risk** — We're deleting 2,193 lines and rewriting 930. What could go wrong? What should we test first?
8. **YAGNI violations** — Is anything over-engineered? Should we simplify further?

## How to Review

- Read the design doc thoroughly
- Cross-reference with the actual current code in `scripts/` and `src/scrapers/` to validate claims
- Check `config/search_profiles.yaml` and `config/target_companies.yaml` for config assumptions
- Look at `.github/workflows/job-pipeline-optimized.yml` for CI integration points
- Be direct: if something is wrong or missing, say so. If the design is solid, say that too.

## Output Format

Structure your review as:
- **Verdict**: Approve / Approve with changes / Request revision
- **Strengths**: What's good about this design
- **Issues**: Specific problems (severity: blocking / should-fix / nice-to-have)
- **Questions**: Things that need clarification before implementation
