# Block A Scraper Rebuild Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the degraded scraping layer with the v3 clean-rebuild design while preserving DB compatibility, notification compatibility, and CI operability.

**Architecture:** Rebuild Block A in-place inside the existing repo on an isolated worktree. Introduce a synchronous `BaseScraper` contract with unified reporting and dedup, migrate platform scrapers onto that base, then cut over CLI, metrics, workflow, and docs in a controlled final integration phase.

**Tech Stack:** Python 3.11/3.12, pytest, requests, Playwright, SQLite/Turso integration, GitHub Actions, YAML/JSON config

---

## Execution Notes

- Worktree: `C:\Users\huang\github\job-hunter\.worktrees\block-a-rebuild`
- Branch: `feature/block-a-rebuild`
- Single implementation owner: Codex
- Review model: Opus only at stage boundaries, not as parallel code owner
- Known baseline failures before Block A work:
  - `tests/test_svg_auto_optimizer.py` has 6 failures on this machine due to temp directory permission issues
  - These failures are unrelated to Block A and must not block scraper implementation verification

## File Map

**Create**
- `scripts/scrape.py`
- `src/scrapers/registry.py`
- `src/scrapers/linkedin.py`
- `src/scrapers/linkedin_browser.py`
- `src/scrapers/linkedin_parser.py`

**Rewrite**
- `src/scrapers/base.py`
- `src/scrapers/greenhouse.py`
- `src/scrapers/iamexpat.py`
- `src/scrapers/__init__.py`
- `scripts/notify.py`
- `.github/workflows/job-pipeline-optimized.yml`
- `config/search_profiles.yaml`
- `config/target_companies.yaml`
- `docs/architecture-overview.md`
- `AGENTS.md`
- `CLAUDE.md`

**Delete**
- `scripts/linkedin_scraper_v6.py`
- `scripts/multi_scraper.py`
- `scripts/scraper_incremental.py`
- `scripts/scraper_incremental_v32.py`
- `src/scrapers/lever.py`

**Reference / integration points**
- `src/db/job_db.py`
- `scripts/job_pipeline.py`
- `tests/test_scrapers/test_base.py`
- `tests/test_scrapers/test_greenhouse.py`
- `tests/test_scrapers/test_iamexpat.py`

## Chunk 1: Foundation Contracts

### Task 1: Freeze compatibility assumptions in tests

**Files:**
- Modify: `tests/test_scrapers/test_base.py`
- Create: `tests/test_scrapers/test_registry.py`
- Create: `tests/test_scrapers/test_scrape_cli.py`

- [ ] **Step 1: Write failing tests for the new base contract**

Add tests for:
- sync `scrape()` public contract
- `ScrapeReport.is_healthy`
- `ScrapeReport.severity`
- `dry_run=True` meaning `new == would_insert`
- target counters: attempted/succeeded/failed

- [ ] **Step 2: Write failing tests for registry and CLI surface**

Add tests for:
- registry names: `linkedin`, `greenhouse`, `iamexpat`
- aliases: `ats`, `all`
- CLI rejects deleted legacy profiles
- CLI accepts active profile names

- [ ] **Step 3: Run focused tests to verify they fail for the right reasons**

Run:
```bash
pytest tests/test_scrapers/test_base.py tests/test_scrapers/test_registry.py tests/test_scrapers/test_scrape_cli.py -v
```

- [ ] **Step 4: Commit the red test baseline**

```bash
git add tests/test_scrapers/test_base.py tests/test_scrapers/test_registry.py tests/test_scrapers/test_scrape_cli.py
git commit -m "test: define block a rebuild contracts"
```

### Task 2: Implement `BaseScraper`, `ScrapeReport`, and registry

**Files:**
- Modify: `src/scrapers/base.py`
- Modify: `src/scrapers/__init__.py`
- Create: `src/scrapers/registry.py`

- [ ] **Step 1: Rewrite `src/scrapers/base.py` with the new contract**

Implement:
- sync `scrape()`
- sync `run()`
- `ScrapeReport` fields from design
- `is_healthy` and `severity`
- MD5 URL dedup via `JobDatabase.generate_job_id()`
- blacklist filtering hook
- dry-run-aware save path
- structured target/error reporting

- [ ] **Step 2: Implement registry and exports**

Add:
- `SCRAPERS`
- `ALIASES`
- helper resolution function(s)

- [ ] **Step 3: Run focused contract tests**

Run:
```bash
pytest tests/test_scrapers/test_base.py tests/test_scrapers/test_registry.py -v
```

- [ ] **Step 4: Commit the foundation layer**

```bash
git add src/scrapers/base.py src/scrapers/__init__.py src/scrapers/registry.py tests/test_scrapers/test_base.py tests/test_scrapers/test_registry.py
git commit -m "feat: add unified scraper foundation"
```

## Chunk 2: CLI and Greenhouse

### Task 3: Build `scripts/scrape.py`

**Files:**
- Create: `scripts/scrape.py`
- Modify: `tests/test_scrapers/test_scrape_cli.py`

- [ ] **Step 1: Implement the new CLI entry point**

Support:
- `--platform linkedin|greenhouse|iamexpat`
- alias handling for `ats` and `all`
- `--profile`
- `--save-to-db`
- `--dry-run`
- structured summary output
- metrics file emission to `data/scrape_metrics.json`

- [ ] **Step 2: Enforce profile contract**

Implement:
- active profiles only
- clean-break rejection of `ml_data`, `backend_data`, `quick_test`

- [ ] **Step 3: Run focused CLI tests**

Run:
```bash
pytest tests/test_scrapers/test_scrape_cli.py -v
```

- [ ] **Step 4: Commit the CLI**

```bash
git add scripts/scrape.py tests/test_scrapers/test_scrape_cli.py
git commit -m "feat: add unified scrape cli"
```

### Task 4: Rebuild Greenhouse on the new base

**Files:**
- Modify: `src/scrapers/greenhouse.py`
- Modify: `tests/test_scrapers/test_greenhouse.py`

- [ ] **Step 1: Write/adjust tests for the new report shape**

Cover:
- per-board target counting
- partial board failure reporting
- dedup/save behavior through `BaseScraper.run()`

- [ ] **Step 2: Rewrite Greenhouse scraper**

Keep:
- HTTP API approach
- current parsing behavior

Add:
- target-level retries
- target-level failure recording
- `ScrapeReport` integration

- [ ] **Step 3: Run Greenhouse tests**

Run:
```bash
pytest tests/test_scrapers/test_greenhouse.py tests/test_scrapers/test_base.py -v
```

- [ ] **Step 4: Commit Greenhouse migration**

```bash
git add src/scrapers/greenhouse.py tests/test_scrapers/test_greenhouse.py
git commit -m "feat: migrate greenhouse scraper to new base"
```

## Chunk 3: LinkedIn Rebuild

### Task 5: Characterize current LinkedIn behavior before extraction

**Files:**
- Reference: `scripts/linkedin_scraper_v6.py`
- Create: `tests/test_scrapers/test_linkedin_parser.py`
- Create: `tests/test_scrapers/test_linkedin_orchestration.py`

- [ ] **Step 1: Extract a minimal behavior inventory from the old script**

Capture in test names and comments:
- profile/query orchestration
- pagination expectations
- JD fetch behavior
- cookie/session validation
- CAPTCHA failure path

- [ ] **Step 2: Add failing tests for parser/orchestration boundaries**

Focus on:
- browser lifecycle isolated from parser logic
- parser handles card/detail extraction from provided inputs
- orchestrator maps failures to scraper-level vs target-level errors

- [ ] **Step 3: Run LinkedIn-focused tests to verify failures are contract-driven**

Run:
```bash
pytest tests/test_scrapers/test_linkedin_parser.py tests/test_scrapers/test_linkedin_orchestration.py -v
```

- [ ] **Step 4: Commit the LinkedIn test scaffold**

```bash
git add tests/test_scrapers/test_linkedin_parser.py tests/test_scrapers/test_linkedin_orchestration.py
git commit -m "test: characterize linkedin rebuild boundaries"
```

### Task 6: Implement the LinkedIn 3-file split

**Files:**
- Create: `src/scrapers/linkedin.py`
- Create: `src/scrapers/linkedin_browser.py`
- Create: `src/scrapers/linkedin_parser.py`

- [ ] **Step 1: Implement `linkedin_browser.py`**

Own:
- Playwright startup / shutdown
- CDP vs launch selection
- cookie load/save
- session validation
- CAPTCHA detection

- [ ] **Step 2: Implement `linkedin_parser.py`**

Own:
- search results extraction
- pagination parsing helpers
- JD/detail parsing helpers
- selector fallback logic

- [ ] **Step 3: Implement `linkedin.py`**

Own:
- active profile loading
- query orchestration
- internal `asyncio.run()` boundary
- mapping errors into `ScrapeReport`

- [ ] **Step 4: Run focused LinkedIn tests**

Run:
```bash
pytest tests/test_scrapers/test_linkedin_parser.py tests/test_scrapers/test_linkedin_orchestration.py tests/test_scrapers/test_base.py -v
```

- [ ] **Step 5: Commit LinkedIn rebuild**

```bash
git add src/scrapers/linkedin.py src/scrapers/linkedin_browser.py src/scrapers/linkedin_parser.py tests/test_scrapers/test_linkedin_parser.py tests/test_scrapers/test_linkedin_orchestration.py
git commit -m "feat: rebuild linkedin scraper with split architecture"
```

## Chunk 4: IamExpat and Metrics Contract

### Task 7: Rebuild IamExpat on the new base

**Files:**
- Modify: `src/scrapers/iamexpat.py`
- Modify: `tests/test_scrapers/test_iamexpat.py`

- [ ] **Step 1: Update tests for target-level reporting and two-phase scraping**

Cover:
- listing to detail flow
- target counters
- timeout/failure handling

- [ ] **Step 2: Rewrite IamExpat**

Implement:
- internal async Playwright path
- `domcontentloaded` + explicit waits
- target-level error handling
- `ScrapeReport` integration

- [ ] **Step 3: Run IamExpat tests**

Run:
```bash
pytest tests/test_scrapers/test_iamexpat.py tests/test_scrapers/test_base.py -v
```

- [ ] **Step 4: Commit IamExpat migration**

```bash
git add src/scrapers/iamexpat.py tests/test_scrapers/test_iamexpat.py
git commit -m "feat: migrate iamexpat scraper to new base"
```

### Task 8: Implement metrics file compatibility

**Files:**
- Modify: `scripts/scrape.py`
- Modify: `tests/test_scrapers/test_scrape_cli.py`
- Create: `tests/test_scrapers/test_metrics_contract.py`

- [ ] **Step 1: Add tests for the Phase 1 metrics JSON contract**

Verify:
- top-level `new_jobs`
- `total.new`
- per-platform `targets_failed`
- severity fields

- [ ] **Step 2: Implement JSON emission exactly per design**

Write `data/scrape_metrics.json` with:
- `new_jobs` shim
- `platforms`
- `total`

- [ ] **Step 3: Run metrics contract tests**

Run:
```bash
pytest tests/test_scrapers/test_metrics_contract.py tests/test_scrapers/test_scrape_cli.py -v
```

- [ ] **Step 4: Commit metrics contract**

```bash
git add scripts/scrape.py tests/test_scrapers/test_scrape_cli.py tests/test_scrapers/test_metrics_contract.py
git commit -m "feat: add phase one scrape metrics contract"
```

## Chunk 5: Integration Cutover

### Task 9: Cut over workflow, config, and notification compatibility

**Files:**
- Modify: `.github/workflows/job-pipeline-optimized.yml`
- Modify: `scripts/notify.py`
- Modify: `config/search_profiles.yaml`
- Modify: `config/target_companies.yaml`

- [ ] **Step 1: Update config files**

Implement:
- remove Lever config
- delete legacy profiles from `config/search_profiles.yaml`

- [ ] **Step 2: Update workflow**

Implement:
- replace old scrape steps with `python scripts/scrape.py --all --save-to-db`
- preserve Phase 1 `new_jobs` extraction
- remove scrape-step `continue-on-error: true`
- update workflow input profile options to active names

- [ ] **Step 3: Update `scripts/notify.py` only to remain Phase 1 compatible**

Do not do the richer Phase 2 notification redesign here.
Only ensure:
- `load_scrape_metrics()` still reads the unified file path
- current `scrape.get("new_jobs", 0)` continues to work
- no regression from unified metrics artifact

- [ ] **Step 4: Run integration-targeted tests**

Run:
```bash
pytest tests/test_scrapers -v
```

- [ ] **Step 5: Commit integration cutover**

```bash
git add .github/workflows/job-pipeline-optimized.yml scripts/notify.py config/search_profiles.yaml config/target_companies.yaml
git commit -m "feat: cut over scraper integration points"
```

### Task 10: Delete obsolete scraper code and update docs

**Files:**
- Delete: `scripts/linkedin_scraper_v6.py`
- Delete: `scripts/multi_scraper.py`
- Delete: `scripts/scraper_incremental.py`
- Delete: `scripts/scraper_incremental_v32.py`
- Delete: `src/scrapers/lever.py`
- Modify: `docs/architecture-overview.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Remove dead code only after new paths are passing**

- [ ] **Step 2: Update docs to reference the new scraper architecture and commands**

- [ ] **Step 3: Run repo-wide verification relevant to Block A**

Run:
```bash
pytest tests/test_scrapers -v
python scripts/scrape.py --all --dry-run
python scripts/notify.py --status success --dry-run
```

- [ ] **Step 4: Commit final cleanup**

```bash
git add docs/architecture-overview.md AGENTS.md CLAUDE.md
git add -u scripts src/scrapers
git commit -m "refactor: finalize block a scraper rebuild"
```

## Chunk 6: Final Verification

### Task 11: Execute the design verification gates

**Files:**
- Reference: `docs/plans/2026-03-26-block-a-scraper-rebuild.md`

- [ ] **Step 1: Verify URL hash compatibility**

Run a targeted check against `JobDatabase.generate_job_id()` and confirm the new flow preserves MD5-based IDs for normalized URLs.

- [ ] **Step 2: Verify LinkedIn failure paths**

Exercise:
- expired cookie => permanent error
- CAPTCHA => permanent error without hanging

- [ ] **Step 3: Verify dry-run semantics**

Confirm:
- no DB writes
- `new` means would-insert under dry-run

- [ ] **Step 4: Verify end-to-end compatibility commands**

Run:
```bash
python scripts/scrape.py --platform greenhouse --dry-run
python scripts/scrape.py --platform iamexpat --dry-run
python scripts/scrape.py --all --dry-run
```

- [ ] **Step 5: Record verification results in the final handoff summary**

Include:
- commands run
- pass/fail status
- any remaining non-Block-A baseline failures

- [ ] **Step 6: Commit verification artifacts if any repo files changed**

```bash
git status --short
```

## Recommended Review Gates

- After Chunk 1: review foundation contract only
- After Chunk 3: review LinkedIn boundaries and failure handling
- After Chunk 5: review workflow/config/metrics cutover before deleting old files
- After Chunk 6: final implementation review

## Success Criteria

- New scraper layer exists exactly under the designed file structure
- Legacy profiles are removed from config and workflow
- `scripts/scrape.py` is the only scraper CLI entry point
- Metrics contract matches the v3 design, including Phase 1 `new_jobs` shim
- `scripts/notify.py` and CI continue to work with Phase 1 compatibility
- Repost detection remains downstream via `find_applied_duplicates()`
- Scraper-focused tests pass
- Known unrelated `svg_auto_optimizer` baseline failures remain the only acknowledged non-Block-A failures
