# Scraper Dedup Window Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Change scraper dedup from all-history to a configurable N-day window (default 30), so stale jobs re-enter the pipeline when they reappear in search results.

**Architecture:** Add `dedup_window_days` config to `search_profiles.yaml`. Propagate to `find_existing_job_ids()` (time-bounded SQL), `find_semantic_duplicate()` (same), and `insert_job()` (UPSERT updates more fields + clears pipeline records for resurfaced jobs). Three call sites: `linkedin.py`, `base.py`, `iamexpat.py`.

**Tech Stack:** Python, SQLite, existing JobDatabase/BaseScraper classes.

---

### Task 1: Add config

**Files:**
- Modify: `config/search_profiles.yaml:9-15`

**Step 1: Add dedup_window_days to defaults**

```yaml
defaults:
  location: "Netherlands"
  date_posted: "r86400"
  dedup_window_days: 30   # Only dedup against last N days. 0 = all-history (old behavior)
  job_type: "F"
  sort_by: "DD"
  language: "en"
  max_jobs: 999
```

**Step 2: Commit**

```bash
git add config/search_profiles.yaml
git commit -m "config: add dedup_window_days (default 30)"
```

---

### Task 2: `find_existing_job_ids()` with time window

**Files:**
- Modify: `src/db/job_db.py:844-861`
- Test: `tests/test_dedup.py`

**Step 1: Write failing tests**

Add to `tests/test_dedup.py`:

```python
from datetime import datetime, timedelta

class TestDedupWindow:
    """Tests for time-windowed dedup in find_existing_job_ids."""

    def test_recent_job_is_deduped(self):
        """Job scraped 5 days ago should be found when window is 30 days."""
        db = _make_test_db()
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "DE", "company": "Co",
                        "source": "test", "description": "d", "scraped_at": recent})
        result = db.find_existing_job_ids(["http://a.com/1"], since_days=30)
        assert len(result) == 1

    def test_stale_job_not_deduped(self):
        """Job scraped 45 days ago should NOT be found when window is 30 days."""
        db = _make_test_db()
        stale = (datetime.now() - timedelta(days=45)).isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "DE", "company": "Co",
                        "source": "test", "description": "d", "scraped_at": stale})
        result = db.find_existing_job_ids(["http://a.com/1"], since_days=30)
        assert len(result) == 0

    def test_zero_window_means_all_history(self):
        """since_days=0 should behave like all-history (original behavior)."""
        db = _make_test_db()
        old = (datetime.now() - timedelta(days=200)).isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "DE", "company": "Co",
                        "source": "test", "description": "d", "scraped_at": old})
        result = db.find_existing_job_ids(["http://a.com/1"], since_days=0)
        assert len(result) == 1
```

**Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_dedup.py::TestDedupWindow -v`
Expected: FAIL — `find_existing_job_ids()` doesn't accept `since_days`

**Step 3: Implement**

In `src/db/job_db.py`, modify `find_existing_job_ids`:

```python
def find_existing_job_ids(self, urls: List[str], since_days: int = 0) -> set[str]:
    """Batch-check which scraped URLs already exist in jobs.

    Args:
        since_days: Only consider jobs scraped within this many days.
                    0 means all history (original behavior).
    """
    job_ids = [self.generate_job_id(url) for url in urls if url]
    if not job_ids:
        return set()

    since_clause = ""
    params_prefix: list = []
    if since_days > 0:
        cutoff = (datetime.now() - timedelta(days=since_days)).isoformat()
        since_clause = "AND scraped_at >= ?"
        params_prefix = [cutoff]

    existing_ids: set[str] = set()
    chunk_size = 900
    with self._get_conn() as conn:
        for i in range(0, len(job_ids), chunk_size):
            chunk = job_ids[i:i + chunk_size]
            placeholders = ",".join(["?"] * len(chunk))
            cursor = conn.execute(
                f"SELECT id FROM jobs WHERE id IN ({placeholders}) {since_clause}",
                chunk + params_prefix,
            )
            existing_ids.update(row[0] for row in cursor.fetchall())
    return existing_ids
```

Add `from datetime import datetime, timedelta` to imports if not already present.

**Step 4: Run tests**

Run: `python -m pytest tests/test_dedup.py::TestDedupWindow -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/db/job_db.py tests/test_dedup.py
git commit -m "feat: add time window to find_existing_job_ids"
```

---

### Task 3: `find_semantic_duplicate()` with time window

**Files:**
- Modify: `src/db/job_db.py:899-914`
- Test: `tests/test_dedup.py`

**Step 1: Write failing test**

```python
class TestSemanticDedupWindow:

    def test_stale_semantic_dup_not_blocked(self):
        """Semantic duplicate scraped 45 days ago should not block re-insertion."""
        db = _make_test_db()
        stale = (datetime.now() - timedelta(days=45)).isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "Data Engineer",
                        "company": "Acme", "source": "test", "description": "d",
                        "scraped_at": stale})
        result = db.find_semantic_duplicate("Data Engineer", "Acme", since_days=30)
        assert result is None

    def test_recent_semantic_dup_still_blocked(self):
        """Semantic duplicate scraped 5 days ago should still block."""
        db = _make_test_db()
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "Data Engineer",
                        "company": "Acme", "source": "test", "description": "d",
                        "scraped_at": recent})
        result = db.find_semantic_duplicate("Data Engineer", "Acme", since_days=30)
        assert result is not None
```

**Step 2: Run to verify fail**

Run: `python -m pytest tests/test_dedup.py::TestSemanticDedupWindow -v`

**Step 3: Implement**

```python
def find_semantic_duplicate(self, title: str, company: str,
                            exclude_id: str = None,
                            since_days: int = 0) -> Optional[str]:
    """Find existing job with same company + normalized title. Returns job_id or None."""
    norm_title = self._normalize_title(title)
    if not norm_title:
        return None

    since_clause = ""
    params: list = [company.lower()]
    if since_days > 0:
        cutoff = (datetime.now() - timedelta(days=since_days)).isoformat()
        since_clause = "AND scraped_at >= ?"
        params.append(cutoff)

    with self._get_conn() as conn:
        cursor = conn.execute(
            f"SELECT id, title FROM jobs WHERE LOWER(company) = ? {since_clause}",
            params,
        )
        for row in cursor.fetchall():
            if exclude_id and row['id'] == exclude_id:
                continue
            if self._normalize_title(row['title']) == norm_title:
                return row['id']
    return None
```

**Step 4: Run tests, verify pass**

**Step 5: Commit**

```bash
git add src/db/job_db.py tests/test_dedup.py
git commit -m "feat: add time window to find_semantic_duplicate"
```

---

### Task 4: `insert_job()` UPSERT enhancement + pipeline reset

**Files:**
- Modify: `src/db/job_db.py:916-973`
- Test: `tests/test_dedup.py`

**Step 1: Write failing test**

```python
class TestResurfaceJob:

    def test_resurfaced_job_updates_scraped_at(self):
        """Stale job re-inserted should have updated scraped_at."""
        db = _make_test_db()
        db._conn.executescript("""
            CREATE TABLE IF NOT EXISTS filter_results (
                id INTEGER PRIMARY KEY, job_id TEXT, passed INTEGER,
                reject_reason TEXT DEFAULT '', filter_version TEXT DEFAULT '', created_at TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS job_analysis (
                id INTEGER PRIMARY KEY, job_id TEXT, ai_score REAL,
                skill_match TEXT DEFAULT '', experience_fit TEXT DEFAULT '',
                growth_potential TEXT DEFAULT '', recommendation TEXT DEFAULT '',
                reasoning TEXT DEFAULT '', tailored_resume TEXT DEFAULT '',
                model TEXT DEFAULT '', tokens_used INTEGER DEFAULT 0,
                analyzed_at TEXT DEFAULT '', resume_tier TEXT DEFAULT '',
                template_id_initial TEXT DEFAULT '', template_id_final TEXT DEFAULT '',
                routing_confidence REAL DEFAULT 0, routing_override_reason TEXT DEFAULT '',
                escalation_reason TEXT DEFAULT '', routing_payload TEXT DEFAULT '',
                c3_decision TEXT DEFAULT '', c3_confidence REAL DEFAULT 0, c3_reason TEXT DEFAULT ''
            );
        """)
        stale = (datetime.now() - timedelta(days=45)).isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "DE", "company": "Co",
                        "source": "test", "description": "old desc", "scraped_at": stale})
        job_id = db.generate_job_id("http://a.com/1")

        # Add pipeline records
        db._conn.execute("INSERT INTO filter_results (job_id, passed) VALUES (?, 1)", (job_id,))
        db._conn.execute("INSERT INTO job_analysis (job_id, ai_score) VALUES (?, 7.0)", (job_id,))

        # Re-insert (resurface)
        now = datetime.now().isoformat()
        db.insert_job({"url": "http://a.com/1", "title": "DE", "company": "Co",
                        "source": "test", "description": "new longer desc here",
                        "scraped_at": now}, dedup_window_days=30)

        job = db.get_job(job_id)
        assert job['scraped_at'] == now
        assert job['description'] == "new longer desc here"

        # Pipeline records should be cleared
        fr = db._conn.execute("SELECT * FROM filter_results WHERE job_id = ?", (job_id,)).fetchone()
        ja = db._conn.execute("SELECT * FROM job_analysis WHERE job_id = ?", (job_id,)).fetchone()
        assert fr is None
        assert ja is None
```

**Step 2: Run to verify fail**

**Step 3: Implement**

Add `_reset_pipeline_for_job` method to `JobDatabase`:

```python
def _reset_pipeline_for_job(self, job_id: str) -> None:
    """Clear pipeline records so a resurfaced job re-enters processing."""
    with self._get_conn(sync_before=False) as conn:
        conn.execute("DELETE FROM filter_results WHERE job_id = ?", (job_id,))
        conn.execute("DELETE FROM job_analysis WHERE job_id = ?", (job_id,))
```

Modify `insert_job` signature and UPSERT:

```python
def insert_job(self, job_data: Dict, dedup_window_days: int = 0) -> tuple:
    """Insert or resurface a job."""
    url = job_data.get("url", "")
    job_id = self.generate_job_id(url)

    title = job_data.get("title", "")
    company = job_data.get("company", "")
    if not title.strip() or not company.strip():
        print(f"  [WARN] Skipping job with empty title or company: {url[:60]}")
        return job_id, False

    existing_id = self.find_semantic_duplicate(
        title, company, exclude_id=job_id, since_days=dedup_window_days)
    if existing_id:
        desc = job_data.get("description", "")
        if desc:
            with self._get_conn(sync_before=False) as conn:
                conn.execute("""
                    UPDATE jobs SET description = ?
                    WHERE id = ? AND (description IS NULL OR length(description) < ?)
                """, (desc, existing_id, len(desc)))
        return existing_id, False

    job = Job(
        id=job_id,
        source=job_data.get("source", "unknown"),
        url=url,
        title=title,
        company=company,
        location=job_data.get("location", ""),
        description=job_data.get("description", ""),
        posted_date=job_data.get("posted_date", ""),
        scraped_at=job_data.get("scraped_at", datetime.now().isoformat()),
        search_profile=job_data.get("search_profile", ""),
        search_query=job_data.get("search_query", ""),
        raw_data=""
    )

    with self._get_conn(sync_before=False) as conn:
        cursor = conn.execute("""
            INSERT INTO jobs
            (id, source, url, title, company, location, description,
             posted_date, scraped_at, search_profile, search_query, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                description = excluded.description,
                scraped_at = excluded.scraped_at,
                search_profile = excluded.search_profile,
                search_query = excluded.search_query,
                posted_date = excluded.posted_date
        """, (job.id, job.source, job.url, job.title, job.company,
              job.location, job.description, job.posted_date, job.scraped_at,
              job.search_profile, job.search_query, job.raw_data))
        was_inserted = cursor.rowcount > 0

    if dedup_window_days > 0:
        self._reset_pipeline_for_job(job_id)

    return job_id, was_inserted
```

Note: the UPSERT now unconditionally updates description (not just when longer) because a resurfaced job's JD may have changed. The `_reset_pipeline_for_job` call is a no-op for truly new jobs (no pipeline records exist).

**Step 4: Run tests**

Run: `python -m pytest tests/test_dedup.py -v`
Expected: ALL pass (including old tests — verify UPSERT change doesn't break them)

**Step 5: Commit**

```bash
git add src/db/job_db.py tests/test_dedup.py
git commit -m "feat: insert_job UPSERT updates all fields + resets pipeline for resurfaced jobs"
```

---

### Task 5: Wire config through `BaseScraper`

**Files:**
- Modify: `src/scrapers/base.py:82-88` (init) and `src/scrapers/base.py:154-209` (run)

**Step 1: Load dedup_window_days in BaseScraper.__init__**

```python
def __init__(self):
    self.db = JobDatabase()
    self.blacklists = load_blacklists()
    self._target_errors: List[Dict[str, str]] = []
    self._run_errors: List[str] = []
    self._target_counts = {"attempted": 0, "succeeded": 0, "failed": 0}
    self._diagnostics: Dict = {}
    self.dedup_window_days = self._load_dedup_window()

def _load_dedup_window(self) -> int:
    try:
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        return int(config.get("defaults", {}).get("dedup_window_days", 0))
    except (FileNotFoundError, ValueError):
        return 0
```

**Step 2: Pass to find_existing_job_ids and insert_job in run()**

In `run()`, change line 166:

```python
existing_job_ids = self.db.find_existing_job_ids(
    [job.get("url", "") for job in jobs],
    since_days=self.dedup_window_days,
)
```

And change lines 193-196:

```python
if jobs_to_insert:
    with self.db.batch_mode():
        for job in jobs_to_insert:
            self.db.insert_job(job, dedup_window_days=self.dedup_window_days)
```

**Step 3: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: ALL pass

**Step 4: Commit**

```bash
git add src/scrapers/base.py
git commit -m "feat: BaseScraper loads dedup_window_days and passes to DB methods"
```

---

### Task 6: Wire config through `LinkedInScraper`

**Files:**
- Modify: `src/scrapers/linkedin.py:117`

**Step 1: Pass dedup_window_days to find_existing_job_ids**

In `_scrape_async()`, change line 117:

```python
known_ids = self.db.find_existing_job_ids(
    card_urls, since_days=self.dedup_window_days)
```

`self.dedup_window_days` is inherited from `BaseScraper.__init__()`.

**Step 2: Run LinkedIn-specific tests**

Run: `python -m pytest tests/test_scrapers/test_linkedin_orchestration.py -v`
Expected: PASS

**Step 3: Commit**

```bash
git add src/scrapers/linkedin.py
git commit -m "feat: LinkedInScraper uses dedup window for early DB dedup"
```

---

### Task 7: Wire config through `IamExpatScraper`

**Files:**
- Modify: `src/scrapers/iamexpat.py:135`

**Step 1: Pass dedup_window_days**

Change line 135:

```python
existing_job_ids = self.db.find_existing_job_ids(
    [card["url"] for card in cards],
    since_days=self.dedup_window_days,
)
```

**Step 2: Commit**

```bash
git add src/scrapers/iamexpat.py
git commit -m "feat: IamExpatScraper uses dedup window"
```

---

### Task 8: Update CLAUDE.md

**Files:**
- Modify: `CLAUDE.md`

Add to the "配置说明" section:

```markdown
### 去重窗口 (`config/search_profiles.yaml`)
- `defaults.dedup_window_days`: 去重时间窗口（天）。默认 30 = 只对最近 30 天内抓取过的职位去重。超过 30 天的旧职位会被重新抓取并走完整 pipeline（重新硬规则筛选 + AI 评分 + 简历定制）。设为 0 = 全历史去重（旧行为）。
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: document dedup_window_days config"
```

---

### Task 9: Integration smoke test

**Step 1: Dry-run scrape to verify resurfaced jobs**

```bash
python scripts/scrape.py --all --dry-run
```

Check output for `would_insert` count — should be significantly higher than before (stale jobs now counted as new).

**Step 2: Verify with DB query**

```python
python -c "
from src.db.job_db import JobDatabase
from datetime import datetime, timedelta
db = JobDatabase()
cutoff = (datetime.now() - timedelta(days=30)).isoformat()
rows = db.execute('SELECT COUNT(*) as c FROM jobs WHERE scraped_at < ?', (cutoff,))
print(f'Jobs older than 30 days (eligible for resurface): {rows[0][\"c\"]}')
rows2 = db.execute('SELECT COUNT(*) as c FROM jobs WHERE scraped_at >= ?', (cutoff,))
print(f'Jobs within 30-day window (still deduped): {rows2[0][\"c\"]}')
"
```

**Step 3: Final commit if any adjustments needed**
