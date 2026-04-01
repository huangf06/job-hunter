# Prepare Diagnostics Fixes

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 4 issues diagnosed from `--prepare` output: DB-disk desync, CL batch limit, AI score clustering, cross-platform dedup.

**Architecture:** Targeted fixes across pipeline CLI, DB layer, AI scoring prompt, and job import logic. Each fix is independent.

**Tech Stack:** Python, SQLite, argparse, pytest

---

## Task 1: `--repair` command to fix DB-disk desync

**Problem:** Resume records exist in DB with `pdf_path` set, but actual PDF files are gone from disk. `get_analyzed_jobs_for_resume()` thinks resumes exist (skips regeneration), but `get_ready_to_apply()` can't find files (skips 99 jobs).

**Files:**
- Modify: `src/db/job_db.py` (add `clear_orphan_resumes` method)
- Modify: `scripts/job_pipeline.py` (add `--repair` flag + `cmd_repair()`)
- Create: `tests/test_repair.py`

### Step 1: Write the failing test

```python
# tests/test_repair.py
"""Tests for --repair: clearing orphan resume records."""
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


class TestClearOrphanResumes:
    """Tests for JobDatabase.clear_orphan_resumes()."""

    def test_clears_resume_with_missing_pdf(self, tmp_path):
        """Resume record whose pdf_path file doesn't exist should be cleared."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        # Insert a job + analysis + resume with a non-existent pdf_path
        db.execute("INSERT INTO jobs (id, source, url, title, company) VALUES ('j1', 'test', 'http://x', 'Dev', 'Co')")
        db.execute("INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model) VALUES ('j1', 8.0, 'APPLY', '{}', '{}', 'test')")
        fake_pdf = str(tmp_path / "nonexistent.pdf")
        db.execute("INSERT INTO resumes (job_id, role_type, template_version, pdf_path) VALUES ('j1', 'de', '1.0', ?)", (fake_pdf,))

        cleared = db.clear_orphan_resumes()
        assert cleared == 1

        # Resume record should be gone
        rows = db.execute("SELECT * FROM resumes WHERE job_id = 'j1'")
        assert len(rows) == 0

    def test_keeps_resume_with_existing_pdf(self, tmp_path):
        """Resume record whose pdf_path file exists should NOT be cleared."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        db.execute("INSERT INTO jobs (id, source, url, title, company) VALUES ('j2', 'test', 'http://y', 'Dev', 'Co')")
        real_pdf = tmp_path / "real.pdf"
        real_pdf.write_text("fake pdf")
        db.execute("INSERT INTO resumes (job_id, role_type, template_version, pdf_path) VALUES ('j2', 'de', '1.0', ?)", (str(real_pdf),))

        cleared = db.clear_orphan_resumes()
        assert cleared == 0

        rows = db.execute("SELECT * FROM resumes WHERE job_id = 'j2'")
        assert len(rows) == 1

    def test_also_clears_orphan_cover_letters(self, tmp_path):
        """When a resume is cleared, its cover letter should also be cleared."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        db.execute("INSERT INTO jobs (id, source, url, title, company) VALUES ('j3', 'test', 'http://z', 'Dev', 'Co')")
        db.execute("INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model) VALUES ('j3', 8.0, 'APPLY', '{}', '{}', 'test')")
        fake_pdf = str(tmp_path / "gone.pdf")
        db.execute("INSERT INTO resumes (job_id, role_type, template_version, pdf_path) VALUES ('j3', 'de', '1.0', ?)", (fake_pdf,))
        db.execute("INSERT INTO cover_letters (job_id, spec_json, standard_text, tokens_used) VALUES ('j3', '{}', 'text', 0)")

        cleared = db.clear_orphan_resumes()
        assert cleared == 1

        cl_rows = db.execute("SELECT * FROM cover_letters WHERE job_id = 'j3'")
        assert len(cl_rows) == 0
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_repair.py -v`
Expected: FAIL (no `clear_orphan_resumes` method)

### Step 3: Implement `clear_orphan_resumes` in job_db.py

Add after the `get_resume()` method (~line 942):

```python
def clear_orphan_resumes(self) -> int:
    """Delete resume (+ cover letter) records whose PDF files no longer exist on disk."""
    from pathlib import Path
    with self._get_conn() as conn:
        rows = conn.execute(
            "SELECT job_id, pdf_path FROM resumes WHERE pdf_path IS NOT NULL AND pdf_path != ''"
        ).fetchall()

        orphan_ids = []
        for row in rows:
            if not Path(row['pdf_path']).exists():
                orphan_ids.append(row['job_id'])

        if not orphan_ids:
            return 0

        placeholders = ','.join('?' * len(orphan_ids))
        conn.execute(f"DELETE FROM cover_letters WHERE job_id IN ({placeholders})", orphan_ids)
        conn.execute(f"DELETE FROM resumes WHERE job_id IN ({placeholders})", orphan_ids)
        return len(orphan_ids)
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_repair.py -v`
Expected: PASS

### Step 5: Add `--repair` CLI flag and `cmd_repair()` method

In `scripts/job_pipeline.py`:

**5a.** Add argparse flag after the `--finalize` line (~line 889):
```python
parser.add_argument('--repair', action='store_true',
                    help='Clear orphan resume/CL records whose PDF files are missing from disk')
```

**5b.** Add `--repair` to the big condition on line 965:
```python
or args.repair \
```

**5c.** Add handler after the `args.finalize` block (~line 980):
```python
elif args.repair:
    pipeline.cmd_repair()
```

**5d.** Add `cmd_repair()` method to `JobPipeline` class:
```python
def cmd_repair(self):
    """Clear orphan resume/CL records whose files are missing from disk."""
    cleared = self.db.clear_orphan_resumes()
    if cleared:
        print(f"[Repair] Cleared {cleared} orphan resume/CL records (PDF files missing)")
        print(f"[Repair] Run --prepare to regenerate them")
    else:
        print("[Repair] No orphan records found — all resume PDFs exist on disk")
```

### Step 6: Run all tests

Run: `pytest tests/test_repair.py -v`
Expected: all PASS

### Step 7: Commit

```bash
git add tests/test_repair.py src/db/job_db.py scripts/job_pipeline.py
git commit -m "feat: add --repair to clear orphan resume/CL records with missing PDFs"
```

---

## Task 2: Increase CL batch limit in `--prepare`

**Problem:** `cmd_prepare()` defaults to `limit=50`, so only top-50-by-score jobs get CLs per run. With 429 jobs pending, this requires many manual runs.

**Files:**
- Modify: `scripts/job_pipeline.py:363` (change default limit)

### Step 1: Change the default limit

In `scripts/job_pipeline.py`, line 363, change:
```python
limit = limit or 50
```
to:
```python
# No default cap — process all eligible jobs unless --limit is specified
```
(Remove the line entirely — `limit` stays `None` if not passed, and both `get_analyzed_jobs_for_resume()` and `generate_batch()` already handle `None` as "no limit".)

But `generate_batch()` in `cover_letter_generator.py:734` has `limit: int = 50` as default. We need to also pass `None` through.

In `scripts/job_pipeline.py`, the `generate_cover_letters_batch()` wrapper (~line 345):
```python
def generate_cover_letters_batch(self, min_ai_score: float = None, limit: int = None):
```
Verify it passes `limit` through to `generator.generate_batch(...)`. If it defaults to 50 internally, change the call.

### Step 2: Verify the change

Run: `python scripts/job_pipeline.py --prepare --limit 5` (small test)
Expected: Only processes 5 jobs (limit still works when explicitly set)

### Step 3: Commit

```bash
git add scripts/job_pipeline.py
git commit -m "fix: remove default limit=50 cap from --prepare, process all eligible jobs"
```

---

## Task 3: Fix AI scoring prompt to reduce clustering

**Problem:** 70 jobs score exactly 8.5. The scoring guidelines define 7-8 as one band, and Claude defaults to the midpoint (7.5, 8.5). Requiring integer-only scores forces clear band boundaries.

**Files:**
- Modify: `src/ai_analyzer.py:531-551` (scoring guidelines)
- Modify: `config/ai_config.yaml:199` (example output)

### Step 1: Update scoring guidelines

In `src/ai_analyzer.py`, replace the `_build_scoring_guidelines()` return string:

```python
return """Use the FULL 1-10 scale. INTEGERS ONLY — no decimals (not 7.5, not 8.5).

**Score Bands (mutually exclusive — pick the ONE that fits best):**
- 10: Unicorn match (<2%) — Every required skill present, exact experience level, domain overlap, candidate would be a top-3 hire
- 9: Near-perfect match (<5%) — ALL required skills present, experience level exact, domain overlap strong
- 8: Strong match, high confidence (10%) — Most required skills, minor gaps only in nice-to-haves, experience within 1 year
- 7: Good match, worth prioritizing (15%) — Core skills present, 1-2 gaps in secondary requirements, experience close
- 6: Solid match, worth applying (20%) — Core skills present, 1-2 secondary gaps, candidate can credibly do the job
- 5: Borderline (15%) — Has relevant foundation but notable gaps; would need to stretch. Apply only if no better options
- 4: Weak match (15%) — Major skill or experience gaps, different specialization but adjacent
- 3: Poor match (10%) — Wrong specialization, significant experience gaps
- 2: Wrong role (5%) — Different domain or tech stack entirely
- 1: Complete mismatch (<3%) — Nothing in common

**The key distinction for 7 vs 8:** Does the candidate match ALL core requirements with at most nice-to-have gaps? → 8. Are there 1-2 gaps in secondary requirements? → 7.

**The key distinction for 5 vs 6:** Would this candidate get past a 30-second resume screen by a hiring manager who knows the role? If yes → 6. If maybe → 5. If unlikely → 4.

**Calibration anchors:**
- JD requires "5+ years Java" but candidate has 0 Java → 3 MAX (wrong primary stack)
- JD requires "PhD in CS" but candidate has M.Sc. → 5 MAX (unless "or equivalent" mentioned → 6)
- JD is 80% frontend but candidate is backend → 2 MAX
- JD says "10+ years" but candidate has 6 → 4 MAX (significant experience gap)
- JD matches candidate's DE stack but wants cloud candidate lacks (GCP vs AWS) → 6-7 (transferable)
- JD is a startup wanting generalist data/ML with Python+SQL → 7-8 (strong fit)"""
```

### Step 2: Update example output in ai_config.yaml

In `config/ai_config.yaml`, line 199, change the example scores to integers:
```yaml
      "overall_score": 7,
      "skill_match": 8,
      "experience_fit": 7,
      "growth_potential": 7,
```

### Step 3: Commit

```bash
git add src/ai_analyzer.py config/ai_config.yaml
git commit -m "fix: require integer-only AI scores to reduce clustering at X.5 boundaries"
```

**Note:** Existing scores in the DB are unaffected. Only new evaluations will use integer scoring. Consider running `--retry-failures` or re-evaluating high-value jobs if needed.

---

## Task 4: Cross-platform semantic dedup during import

**Problem:** Same job posted on different boards (LinkedIn vs Greenhouse) gets different URLs → different job_ids → stored as duplicates. Example: Fractal "Senior Data Scientist - Payment Processing" appears twice.

**Files:**
- Modify: `src/db/job_db.py` (add `find_semantic_duplicate` method, modify `insert_job`)
- Create: `tests/test_dedup.py`

### Step 1: Write the failing test

```python
# tests/test_dedup.py
"""Tests for cross-platform semantic dedup during import."""
import pytest


class TestSemanticDedup:
    """Tests for semantic dedup in insert_job."""

    def test_same_company_title_different_url_is_skipped(self, tmp_path):
        """Second job with same company+title but different URL should be skipped."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        job1 = {"url": "http://linkedin.com/jobs/123", "title": "Data Engineer", "company": "Acme Corp",
                 "source": "linkedin", "description": "Great job"}
        job2 = {"url": "http://greenhouse.io/acme/456", "title": "Data Engineer", "company": "Acme Corp",
                 "source": "greenhouse", "description": "Great job description longer"}

        id1, inserted1 = db.insert_job(job1)
        id2, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is False  # Semantic duplicate should be skipped
        assert id2 == id1  # Should return the existing job's ID

    def test_same_company_different_title_is_inserted(self, tmp_path):
        """Different title at same company should NOT be skipped."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        job1 = {"url": "http://a.com/1", "title": "Data Engineer", "company": "Acme",
                 "source": "test", "description": "desc"}
        job2 = {"url": "http://b.com/2", "title": "ML Engineer", "company": "Acme",
                 "source": "test", "description": "desc"}

        _, inserted1 = db.insert_job(job1)
        _, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is True

    def test_normalized_title_match(self, tmp_path):
        """Titles that normalize to same words should be treated as duplicates."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        job1 = {"url": "http://a.com/1", "title": "Senior Data Engineer - Enterprise",
                 "company": "Acme", "source": "test", "description": "desc"}
        job2 = {"url": "http://b.com/2", "title": "Enterprise Senior Data Engineer",
                 "company": "Acme", "source": "test", "description": "desc"}

        _, inserted1 = db.insert_job(job1)
        _, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is False

    def test_dedup_updates_description_if_longer(self, tmp_path):
        """Semantic duplicate with longer description should update the original."""
        from src.db.job_db import JobDatabase
        db = JobDatabase(db_path=str(tmp_path / "test.db"))

        job1 = {"url": "http://a.com/1", "title": "Dev", "company": "Co",
                 "source": "test", "description": "short"}
        job2 = {"url": "http://b.com/2", "title": "Dev", "company": "Co",
                 "source": "test", "description": "much longer description with details"}

        id1, _ = db.insert_job(job1)
        id2, inserted2 = db.insert_job(job2)

        assert inserted2 is False
        assert id2 == id1

        # Description should be updated to the longer one
        job = db.get_job(id1)
        assert job['description'] == "much longer description with details"
```

### Step 2: Run test to verify it fails

Run: `pytest tests/test_dedup.py -v`
Expected: FAIL (insert_job doesn't do semantic dedup)

### Step 3: Add `find_semantic_duplicate` and modify `insert_job`

In `src/db/job_db.py`, add method before `insert_job` (~line 818):

```python
def find_semantic_duplicate(self, title: str, company: str, exclude_id: str = None) -> Optional[str]:
    """Find existing job with same company + normalized title. Returns job_id or None."""
    norm_title = self._normalize_title(title)
    with self._get_conn() as conn:
        cursor = conn.execute(
            "SELECT id, title FROM jobs WHERE LOWER(company) = ?",
            (company.lower(),)
        )
        for row in cursor.fetchall():
            if exclude_id and row['id'] == exclude_id:
                continue
            if self._normalize_title(row['title']) == norm_title:
                return row['id']
    return None
```

Then modify `insert_job()` to check for semantic duplicates before inserting. After the empty title/company check (~line 828), add:

```python
# Semantic dedup: same company + normalized title = same job from different source
existing_id = self.find_semantic_duplicate(title, company, exclude_id=job_id)
if existing_id:
    # Update description if the new one is longer
    with self._get_conn(sync_before=False) as conn:
        conn.execute("""
            UPDATE jobs SET description = ?
            WHERE id = ? AND (description IS NULL OR length(description) < ?)
        """, (job_data.get("description", ""), existing_id, len(job_data.get("description", ""))))
    return existing_id, False
```

### Step 4: Run test to verify it passes

Run: `pytest tests/test_dedup.py -v`
Expected: PASS

### Step 5: Run existing tests to check for regressions

Run: `pytest tests/ -v --timeout=30`
Expected: All existing tests still PASS

### Step 6: Commit

```bash
git add src/db/job_db.py tests/test_dedup.py
git commit -m "feat: add cross-platform semantic dedup (company+normalized title) during import"
```

---

## Execution Order

Tasks are independent. Recommended order: 2 (trivial) → 1 (moderate) → 4 (moderate) → 3 (prompt-only).
