# Block B Hard Filter Rebuild — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract Hard Filter into a standalone module, delete Rule Score, and rewire the pipeline so Hard Filter output feeds directly into AI analysis (Block C).

**Architecture:** Move `_apply_filter()` and `_keyword_boundary_pattern()` from the 1300-line `job_pipeline.py` monolith into `src/hard_filter.py`. Delete `_calculate_score()`, `score_jobs()`, and the `scoring.yaml` config dependency. Update `get_jobs_needing_analysis()` to query `filter_results.passed = 1` directly (no `ai_scores` join). Update views to remove `ai_scores` references.

**Tech Stack:** Python, regex, PyYAML, pytest, SQLite

---

## Task 1: Create `src/hard_filter.py` with extracted filter logic

**Files:**
- Create: `src/hard_filter.py`
- Test: `tests/test_hard_filter.py`

### Step 1: Write failing tests

Create `tests/test_hard_filter.py`:

```python
"""Tests for HardFilter — extracted from job_pipeline.py."""
import pytest
from src.hard_filter import HardFilter, keyword_boundary_pattern
from src.db.job_db import FilterResult


@pytest.fixture
def filter_instance(tmp_path):
    """Create a HardFilter with the real config files."""
    return HardFilter()


class TestKeywordBoundaryPattern:
    """Unit tests for the regex helper."""

    def test_normal_word(self):
        import re
        pat = keyword_boundary_pattern("python")
        assert re.search(pat, "uses python for")
        assert not re.search(pat, "uses pythonic for")

    def test_dotnet(self):
        import re
        pat = keyword_boundary_pattern(".net")
        assert re.search(pat, "uses .net framework")

    def test_csharp(self):
        import re
        pat = keyword_boundary_pattern("c#")
        assert re.search(pat, "proficient in c# development")


class TestHardFilter:
    """Integration tests using real config/base/filters.yaml."""

    def test_dutch_jd_rejected(self, filter_instance):
        job = {
            "id": "test-dutch",
            "title": "data engineer",
            "description": "wij zoeken een ervaren data engineer voor ons team in amsterdam "
                           "jij hebt ervaring met python en werken met grote datasets "
                           "kennis van vacature en sollicitatie processen is een plus "
                           "goede beheersing van de nederlandse taal is vereist",
            "company": "TestCo",
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        assert not result.passed
        assert result.reject_reason == "dutch_language_detection"

    def test_valid_de_job_passes(self, filter_instance):
        job = {
            "id": "test-pass",
            "title": "data engineer",
            "description": "We are looking for a data engineer with experience in "
                           "Python, Spark, and AWS. You will build data pipelines "
                           "and work with large datasets. 3+ years of experience required.",
            "company": "Adyen",
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        assert result.passed

    def test_wrong_role_rejected(self, filter_instance):
        job = {
            "id": "test-wrong-role",
            "title": "marketing manager",
            "description": "We need a marketing manager to lead our brand strategy "
                           "across digital channels. Experience with campaigns required.",
            "company": "TestCo",
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        assert not result.passed

    def test_insufficient_data_rejected(self, filter_instance):
        job = {
            "id": "test-empty",
            "title": "data engineer",
            "description": "short",
            "company": "TestCo",
            "location": "",
        }
        result = filter_instance.apply(job)
        assert not result.passed
        assert result.reject_reason == "insufficient_data"

    def test_senior_management_rejected(self, filter_instance):
        job = {
            "id": "test-vp",
            "title": "vp of engineering",
            "description": "We are looking for a VP of Engineering to lead our "
                           "technology organization of 50+ engineers. "
                           "15+ years of experience in software development required.",
            "company": "TestCo",
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        assert not result.passed

    def test_senior_data_scientist_passes_management_filter(self, filter_instance):
        job = {
            "id": "test-senior-ds",
            "title": "senior data scientist",
            "description": "We need a senior data scientist with expertise in "
                           "machine learning, Python, and statistical modeling. "
                           "You will mentor junior team members.",
            "company": "Booking.com",
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        # Should NOT be rejected by senior_management rule (has exception)
        assert result.reject_reason != "senior_management_roles" or result.passed

    def test_company_blacklist(self, filter_instance):
        """If there are companies in the blacklist, they should be rejected."""
        if not filter_instance.company_blacklist:
            pytest.skip("No company blacklist configured")
        blocked = filter_instance.company_blacklist[0]
        job = {
            "id": "test-blacklist",
            "title": "data engineer",
            "description": "Great data engineering role with Python and Spark.",
            "company": blocked,
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        assert not result.passed
        assert result.reject_reason == "company_blacklist"

    def test_returns_filter_result_type(self, filter_instance):
        job = {
            "id": "test-type",
            "title": "ml engineer",
            "description": "Build ML models with PyTorch and deploy to production.",
            "company": "TestCo",
            "location": "Amsterdam",
        }
        result = filter_instance.apply(job)
        assert isinstance(result, FilterResult)
        assert result.filter_version == "2.0"
```

### Step 2: Run tests to verify they fail

Run: `python -m pytest tests/test_hard_filter.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'src.hard_filter'`

### Step 3: Implement `src/hard_filter.py`

Extract from `scripts/job_pipeline.py`:
- `_keyword_boundary_pattern()` → `keyword_boundary_pattern()` (public)
- `_apply_filter()` → `HardFilter.apply()`
- Company/title blacklist loading from `search_profiles.yaml`

```python
"""Hard Filter — binary pass/reject for scraped jobs.

Block B in the pipeline architecture. Pure rules, CPU-only, zero AI cost.
Config: config/base/filters.yaml + config/search_profiles.yaml (blacklists).
"""
import json
import re
from pathlib import Path
from typing import Dict

import yaml

from src.db.job_db import FilterResult

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def keyword_boundary_pattern(kw: str) -> str:
    """Build regex with proper word boundaries for keywords with non-word chars.

    Standard \\b fails for '.net' (leading dot) or 'c#' (trailing hash).
    """
    escaped = re.escape(kw)
    prefix = '' if kw and not kw[0].isalnum() and kw[0] != '_' else r'\b'
    suffix = r'(?!\w)' if kw and not kw[-1].isalnum() and kw[-1] != '_' else r'\b'
    return prefix + escaped + suffix


class HardFilter:
    """Applies hard reject rules to jobs. Returns FilterResult (pass/reject)."""

    def __init__(self, config_dir: Path = None):
        config_dir = config_dir or CONFIG_DIR
        self.filter_config = self._load(config_dir / "base" / "filters.yaml")
        search_profiles = self._load(config_dir / "search_profiles.yaml")
        self.company_blacklist = [c.lower() for c in search_profiles.get('company_blacklist', [])]
        self.title_blacklist = [t.lower() for t in search_profiles.get('title_blacklist', [])]

    @staticmethod
    def _load(path: Path) -> dict:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def apply(self, job: Dict) -> FilterResult:
        """Apply hard filter rules. Returns FilterResult with passed=True/False."""
        # --- PASTE the full _apply_filter logic from job_pipeline.py lines 174-352 ---
        # Replace _keyword_boundary_pattern with keyword_boundary_pattern
        # Replace self.filter_config references (already correct)
        # Replace self.company_blacklist/title_blacklist references (already correct)
        ...
```

The `apply()` body is a direct copy of `JobPipeline._apply_filter()` (lines 174-352 in job_pipeline.py), with `_keyword_boundary_pattern` replaced by `keyword_boundary_pattern`.

### Step 4: Run tests to verify they pass

Run: `python -m pytest tests/test_hard_filter.py -v`
Expected: All PASS

### Step 5: Commit

```bash
git add src/hard_filter.py tests/test_hard_filter.py
git commit -m "feat(block-b): extract HardFilter into standalone module with tests"
```

---

## Task 2: Rewire `job_pipeline.py` to use `HardFilter`

**Files:**
- Modify: `scripts/job_pipeline.py`

### Step 1: Replace inline filter with import

In `job_pipeline.py`:

1. Add import at top:
```python
from src.hard_filter import HardFilter, keyword_boundary_pattern
```

2. In `JobPipeline.__init__()`:
   - Remove: `self.filter_config = self._load_config("base/filters.yaml")`
   - Remove: company/title blacklist loading (lines 98-101)
   - Add: `self.hard_filter = HardFilter()`

3. In `filter_jobs()` (line 148-172):
   - Replace `result = self._apply_filter(job)` with `result = self.hard_filter.apply(job)`

4. Delete methods:
   - `_apply_filter()` (lines 174-352) — now in `src/hard_filter.py`

5. Delete the module-level `_keyword_boundary_pattern()` function (lines 67-77) — now in `src/hard_filter.py`

### Step 2: Run existing filter tests

Run: `python -m pytest tests/test_hard_filter.py -v`
Expected: All PASS (module still works identically)

### Step 3: Smoke test the pipeline

Run: `python scripts/job_pipeline.py --filter --limit 5`
Expected: Same output as before (passes/rejects printed)

### Step 4: Commit

```bash
git add scripts/job_pipeline.py
git commit -m "refactor(block-b): rewire job_pipeline to use extracted HardFilter"
```

---

## Task 3: Delete Rule Score

**Files:**
- Modify: `scripts/job_pipeline.py`
- Modify: `src/db/job_db.py`

### Step 1: Delete score methods from `job_pipeline.py`

1. Delete `score_jobs()` method (lines 354-377)
2. Delete `_calculate_score()` method (lines 379-553)
3. In `process_all()` (line 1003): remove `scored = self.score_jobs(limit=limit)` and update the summary print
4. Remove `self.score_config = self._load_config("base/scoring.yaml")` from `__init__`
5. Remove `--score` CLI branch (line 1314-1315)
6. In `--reprocess` handler (line 1233): remove `score_count = pipeline.db.clear_scores()` and `pipeline.score_jobs()`
7. Update `show_stats()`: remove the `scored_high` line

### Step 2: Update `get_jobs_needing_analysis()` in `job_db.py`

Current query (line 937-956) joins `ai_scores` to enforce `score >= min_rule_score`. Replace with filter_results join:

```python
def get_jobs_needing_analysis(self, limit: int = None) -> List[Dict]:
    """Get jobs that passed filter but have no AI analysis yet (excludes applied)."""
    with self._get_conn() as conn:
        query = """
            SELECT j.*
            FROM jobs j
            JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
            LEFT JOIN job_analysis a ON j.id = a.job_id
            LEFT JOIN applications app ON j.id = app.job_id
            WHERE a.id IS NULL
              AND app.job_id IS NULL
            ORDER BY j.created_at DESC
        """
        params = []
        if limit is not None:
            query += " LIMIT ?"
            params.append(limit)
        cursor = conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
```

Note: `min_rule_score` parameter removed — no longer needed.

### Step 3: Update callers of `get_jobs_needing_analysis()`

In `job_pipeline.py`:
- `process_all()`: change `self.db.get_jobs_needing_analysis(min_rule_score=...)` to `self.db.get_jobs_needing_analysis(limit=...)`
- `ai_analyze_jobs()`: remove `min_rule_score` parameter forwarding

In `src/ai_analyzer.py`:
- `analyze_batch()`: remove `min_rule_score` parameter, call `self.db.get_jobs_needing_analysis(limit=limit)`
- Line ~1023: remove `rule_score = job.get('rule_score', 0)` display (no longer available)

### Step 4: Update views in `job_db.py`

In `_build_views_sql()`:

**`v_pending_jobs`**: Remove `ai_scores` join and columns:
```sql
CREATE VIEW IF NOT EXISTS v_pending_jobs AS
SELECT
    j.*,
    f.passed as filter_passed,
    f.reject_reason,
    an.ai_score,
    an.recommendation as ai_recommendation,
    r.pdf_path as resume_path,
    a.status as application_status
FROM jobs j
LEFT JOIN filter_results f ON j.id = f.job_id
LEFT JOIN job_analysis an ON j.id = an.job_id
LEFT JOIN resumes r ON j.id = r.job_id
LEFT JOIN applications a ON j.id = a.job_id
WHERE a.id IS NULL OR a.status = 'pending';
```

**`v_funnel_stats`**: Remove `scored_high` metric and `ai_scores` join:
```sql
CREATE VIEW IF NOT EXISTS v_funnel_stats AS
SELECT
    COUNT(DISTINCT j.id) as total_scraped,
    COUNT(DISTINCT CASE WHEN f.passed = 1 THEN j.id END) as passed_filter,
    COUNT(DISTINCT CASE WHEN an.id IS NOT NULL THEN j.id END) as ai_analyzed,
    COUNT(DISTINCT CASE WHEN an.ai_score >= {ai_score_generate_resume} AND an.tailored_resume IS NOT NULL AND an.tailored_resume != '{{}}' THEN j.id END) as ai_scored_high,
    COUNT(DISTINCT CASE WHEN r.id IS NOT NULL THEN j.id END) as resume_generated,
    COUNT(DISTINCT CASE WHEN a.status = 'applied' THEN j.id END) as applied,
    COUNT(DISTINCT CASE WHEN a.status = 'rejected' THEN j.id END) as rejected,
    COUNT(DISTINCT CASE WHEN a.status = 'interview' THEN j.id END) as interview,
    COUNT(DISTINCT CASE WHEN a.status = 'offer' THEN j.id END) as offer
FROM jobs j
LEFT JOIN filter_results f ON j.id = f.job_id
LEFT JOIN job_analysis an ON j.id = an.job_id
LEFT JOIN resumes r ON j.id = r.job_id
LEFT JOIN applications a ON j.id = a.job_id;
```

**`v_high_score_jobs`** and **`v_ready_to_apply`**: These already use `job_analysis` not `ai_scores` — no change needed.

### Step 5: Stop writing to `ai_scores` table

In `job_db.py`:
- Keep the `CREATE TABLE IF NOT EXISTS ai_scores` statement (preserve existing data)
- Delete `save_score()` method (line 848-866)
- Delete `get_unscored_jobs()` method (line 869-886)
- Delete `clear_scores()` method (find and remove)
- Keep `ai_scores` table in `_init_db` to avoid dropping existing data

### Step 6: Archive `scoring.yaml`

```bash
mkdir -p config/archive
mv config/base/scoring.yaml config/archive/scoring.yaml.archived
```

### Step 7: Run tests and smoke test

Run: `python -m pytest tests/test_hard_filter.py -v`
Expected: All PASS

Run: `python scripts/job_pipeline.py --stats`
Expected: Stats display without `scored_high` line, no errors

Run: `python scripts/job_pipeline.py --filter --limit 5`
Expected: Filter works as before

### Step 8: Commit

```bash
git add scripts/job_pipeline.py src/db/job_db.py src/ai_analyzer.py config/archive/
git rm config/base/scoring.yaml
git commit -m "feat(block-b): delete Rule Score, rewire AI analysis to use filter_results directly"
```

---

## Task 4: Update CI workflow

**Files:**
- Modify: `.github/workflows/job-pipeline-optimized.yml`

### Step 1: Update the score step

Current CI step runs `python scripts/job_pipeline.py --process` which calls `import_inbox() → filter_jobs() → score_jobs()`.

Since `score_jobs()` is deleted, `--process` now only does `import_inbox() → filter_jobs()`. The step name and command can stay the same, but update the comment:

```yaml
      - name: Step 2 - Filter jobs
        run: |
          python scripts/job_pipeline.py --process
```

No functional change needed — `--process` already works without score_jobs after Task 3.

### Step 2: Commit

```bash
git add .github/workflows/job-pipeline-optimized.yml
git commit -m "chore(ci): update step comments after Rule Score removal"
```

---

## Task 5: Update notification to reflect new funnel

**Files:**
- Modify: `scripts/notify.py`

### Step 1: Check and update funnel display

The notify script reads `v_funnel_stats`. After Task 3, `scored_high` column is removed from this view.

Search for any reference to `scored_high` in `notify.py` and remove/update it. If the script just reads from `get_funnel_stats()` dict, it will silently skip missing keys.

### Step 2: Verify

Run: `python scripts/notify.py --status success --dry-run` (if dry-run exists) or read the code to confirm no crash on missing `scored_high`.

### Step 3: Commit (if changes needed)

```bash
git add scripts/notify.py
git commit -m "fix(notify): remove scored_high reference after Rule Score deletion"
```

---

## Task 6: Update architecture docs and clean up

**Files:**
- Modify: `docs/architecture-overview.md`
- Modify: `docs/plans/2026-03-27-pipeline-block-architecture.md`
- Modify: `CLAUDE.md`

### Step 1: Update `architecture-overview.md`

Add Block B section describing the new standalone `src/hard_filter.py` module, similar to the Block A section.

### Step 2: Update `CLAUDE.md`

- Remove references to `--score` CLI flag
- Update `--process` description: "导入 → 筛选" (no longer includes 规则评分)
- Remove `scoring.yaml` from config file list
- Update pipeline flow diagram to remove Rule Score step

### Step 3: Mark Block B as complete in architecture doc

In `docs/plans/2026-03-27-pipeline-block-architecture.md`, change Block B status from 待重建 to ✅ 完成.

### Step 4: Commit

```bash
git add docs/ CLAUDE.md
git commit -m "docs: update Block B status to complete, remove Rule Score references"
```

---

## Execution Notes

- Tasks 1-2 are the core extraction (low risk, no behavior change)
- Task 3 is the biggest change (deletes Rule Score, rewires DB queries)
- Tasks 4-6 are cleanup
- Total: ~200 lines deleted (score logic), ~180 lines added (hard_filter.py + tests), net reduction ~20 lines
- The `ai_scores` table is NOT dropped — existing data preserved for historical queries
- `deep_analysis.py` and `pipeline_gaps.py` reference `ai_scores` — they will still work for historical data but won't get new entries. These are diagnostic scripts, not pipeline-critical.
