"""Tests for cross-platform semantic dedup during import."""
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta

from src.db.job_db import JobDatabase


def _make_test_db() -> JobDatabase:
    """Create an in-memory JobDatabase with full schema for dedup tests."""
    db = JobDatabase.__new__(JobDatabase)
    db._turso_http = None
    db._conn = sqlite3.connect(":memory:")
    db._conn.row_factory = sqlite3.Row
    # Use the real schema initialization
    db._conn.executescript("""
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            source TEXT DEFAULT 'unknown',
            url TEXT UNIQUE,
            title TEXT NOT NULL DEFAULT '',
            company TEXT NOT NULL DEFAULT '',
            location TEXT DEFAULT '',
            description TEXT DEFAULT '',
            posted_date TEXT DEFAULT '',
            scraped_at TEXT DEFAULT '',
            search_profile TEXT DEFAULT '',
            search_query TEXT DEFAULT '',
            raw_data TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            manual_source TEXT DEFAULT ''
        );
    """)

    @contextmanager
    def fake_get_conn(sync_before=True):
        yield db._conn

    db._get_conn = fake_get_conn
    return db


class TestSemanticDedup:
    """Tests for semantic dedup in insert_job."""

    def test_same_company_title_different_url_is_skipped(self):
        """Second job with same company+title but different URL should be skipped."""
        db = _make_test_db()

        job1 = {"url": "http://linkedin.com/jobs/123", "title": "Data Engineer",
                 "company": "Acme Corp", "source": "linkedin", "description": "Great job"}
        job2 = {"url": "http://greenhouse.io/acme/456", "title": "Data Engineer",
                 "company": "Acme Corp", "source": "greenhouse",
                 "description": "Great job description longer"}

        id1, inserted1 = db.insert_job(job1)
        id2, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is False
        assert id2 == id1  # Returns existing job's ID

    def test_same_company_different_title_is_inserted(self):
        """Different title at same company should NOT be skipped."""
        db = _make_test_db()

        job1 = {"url": "http://a.com/1", "title": "Data Engineer", "company": "Acme",
                 "source": "test", "description": "desc"}
        job2 = {"url": "http://b.com/2", "title": "ML Engineer", "company": "Acme",
                 "source": "test", "description": "desc"}

        _, inserted1 = db.insert_job(job1)
        _, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is True

    def test_normalized_title_match(self):
        """Titles that normalize to same words should be treated as duplicates."""
        db = _make_test_db()

        job1 = {"url": "http://a.com/1", "title": "Senior Data Engineer - Enterprise",
                 "company": "Acme", "source": "test", "description": "desc"}
        job2 = {"url": "http://b.com/2", "title": "Enterprise Senior Data Engineer",
                 "company": "Acme", "source": "test", "description": "desc"}

        _, inserted1 = db.insert_job(job1)
        _, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is False

    def test_dedup_updates_description_if_longer(self):
        """Semantic duplicate with longer description should update the original."""
        db = _make_test_db()

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

    def test_case_insensitive_company_match(self):
        """Company match should be case-insensitive."""
        db = _make_test_db()

        job1 = {"url": "http://a.com/1", "title": "Dev", "company": "ACME Corp",
                 "source": "test", "description": "desc"}
        job2 = {"url": "http://b.com/2", "title": "Dev", "company": "acme corp",
                 "source": "test", "description": "desc"}

        _, inserted1 = db.insert_job(job1)
        _, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert inserted2 is False

    def test_same_url_still_uses_url_dedup(self):
        """Same URL should still work via ON CONFLICT (not break)."""
        db = _make_test_db()

        job1 = {"url": "http://a.com/1", "title": "Dev", "company": "Co",
                 "source": "test", "description": "short"}
        job2 = {"url": "http://a.com/1", "title": "Dev", "company": "Co",
                 "source": "test", "description": "longer description here"}

        id1, inserted1 = db.insert_job(job1)
        id2, inserted2 = db.insert_job(job2)

        assert inserted1 is True
        assert id2 == id1
        # Same URL = same job_id, so semantic dedup exclude_id skips it,
        # then ON CONFLICT upserts the longer description
        job = db.get_job(id1)
        assert job['description'] == "longer description here"


def _make_test_db_with_pipeline_tables() -> JobDatabase:
    """Create an in-memory JobDatabase with jobs + all pipeline tables."""
    db = _make_test_db()
    db._conn.executescript("""
        CREATE TABLE filter_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            passed INTEGER DEFAULT 0,
            rule_results TEXT DEFAULT '',
            filtered_at TEXT DEFAULT ''
        );
        CREATE TABLE job_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            ai_score REAL DEFAULT 0,
            reasoning TEXT DEFAULT '',
            analyzed_at TEXT DEFAULT ''
        );
        CREATE TABLE applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            applied_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            notes TEXT DEFAULT ''
        );
        CREATE TABLE resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            pdf_path TEXT DEFAULT '',
            template_version TEXT DEFAULT '',
            submit_dir TEXT DEFAULT ''
        );
    """)
    return db


def _insert_job_with_scraped_at(db: JobDatabase, url: str, title: str, company: str,
                                 scraped_at: str, description: str = "desc") -> str:
    """Insert a job directly with a specific scraped_at timestamp. Returns job_id."""
    job_id = db.generate_job_id(url)
    db._conn.execute(
        "INSERT INTO jobs (id, source, url, title, company, description, scraped_at) "
        "VALUES (?, 'test', ?, ?, ?, ?, ?)",
        (job_id, url, title, company, description, scraped_at),
    )
    return job_id


class TestDedupWindow:
    """Tests for find_existing_job_ids with since_days time window."""

    def test_recent_job_found_within_window(self):
        """A job scraped 5 days ago should be found when window is 30 days."""
        db = _make_test_db()
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        url = "http://a.com/recent"
        _insert_job_with_scraped_at(db, url, "Dev", "Co", recent)

        found = db.find_existing_job_ids([url], since_days=30)
        assert db.generate_job_id(url) in found

    def test_stale_job_not_found_within_window(self):
        """A job scraped 60 days ago should NOT be found when window is 30 days."""
        db = _make_test_db()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        url = "http://a.com/old"
        _insert_job_with_scraped_at(db, url, "Dev", "Co", old)

        found = db.find_existing_job_ids([url], since_days=30)
        assert db.generate_job_id(url) not in found

    def test_zero_since_days_returns_all(self):
        """since_days=0 should return all existing jobs (backward compat)."""
        db = _make_test_db()
        old = (datetime.now() - timedelta(days=365)).isoformat()
        url = "http://a.com/ancient"
        _insert_job_with_scraped_at(db, url, "Dev", "Co", old)

        found = db.find_existing_job_ids([url], since_days=0)
        assert db.generate_job_id(url) in found

    def test_mixed_recent_and_stale(self):
        """With two jobs, only the recent one should be found within the window."""
        db = _make_test_db()
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        url_new = "http://a.com/new"
        url_old = "http://a.com/old"
        _insert_job_with_scraped_at(db, url_new, "Dev", "Co", recent)
        _insert_job_with_scraped_at(db, url_old, "Dev2", "Co", old)

        found = db.find_existing_job_ids([url_new, url_old], since_days=30)
        assert db.generate_job_id(url_new) in found
        assert db.generate_job_id(url_old) not in found


class TestSemanticDedupWindow:
    """Tests for find_semantic_duplicate with since_days time window."""

    def test_recent_duplicate_found(self):
        """A semantic duplicate scraped recently should be detected."""
        db = _make_test_db()
        recent = (datetime.now() - timedelta(days=5)).isoformat()
        _insert_job_with_scraped_at(db, "http://a.com/1", "Data Engineer", "Acme", recent)

        dup_id = db.find_semantic_duplicate("Data Engineer", "Acme", since_days=30)
        assert dup_id is not None

    def test_stale_duplicate_not_found(self):
        """A semantic duplicate scraped 60 days ago should NOT be detected with 30-day window."""
        db = _make_test_db()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        _insert_job_with_scraped_at(db, "http://a.com/1", "Data Engineer", "Acme", old)

        dup_id = db.find_semantic_duplicate("Data Engineer", "Acme", since_days=30)
        assert dup_id is None

    def test_zero_since_days_finds_all(self):
        """since_days=0 should find duplicates regardless of age."""
        db = _make_test_db()
        old = (datetime.now() - timedelta(days=365)).isoformat()
        _insert_job_with_scraped_at(db, "http://a.com/1", "Data Engineer", "Acme", old)

        dup_id = db.find_semantic_duplicate("Data Engineer", "Acme", since_days=0)
        assert dup_id is not None


class TestResurfaceJob:
    """Tests for insert_job resurface: updates fields + clears pipeline records."""

    def test_resurface_updates_scraped_at_and_description(self):
        """A resurfaced job (outside dedup window) should update scraped_at and description."""
        db = _make_test_db_with_pipeline_tables()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        url = "http://a.com/resurface"
        job_id = _insert_job_with_scraped_at(db, url, "Dev", "Co", old, description="old desc")

        new_scraped = datetime.now().isoformat()
        job_data = {
            "url": url, "title": "Dev", "company": "Co",
            "source": "test", "description": "new description",
            "scraped_at": new_scraped, "search_profile": "de",
            "search_query": "data engineer",
        }
        returned_id, was_inserted = db.insert_job(job_data, dedup_window_days=30)

        assert returned_id == job_id
        job = db.get_job(job_id)
        assert job['description'] == "new description"
        assert job['scraped_at'] == new_scraped
        assert job['search_profile'] == "de"

    def test_resurface_clears_filter_results(self):
        """A resurfaced job should have its filter_results cleared."""
        db = _make_test_db_with_pipeline_tables()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        url = "http://a.com/resurface"
        job_id = _insert_job_with_scraped_at(db, url, "Dev", "Co", old)

        # Add pipeline records
        db._conn.execute(
            "INSERT INTO filter_results (job_id, passed) VALUES (?, 1)", (job_id,)
        )
        db._conn.execute(
            "INSERT INTO job_analysis (job_id, ai_score) VALUES (?, 7.5)", (job_id,)
        )

        job_data = {
            "url": url, "title": "Dev", "company": "Co",
            "source": "test", "description": "desc",
        }
        db.insert_job(job_data, dedup_window_days=30)

        # Pipeline records should be cleared
        row = db._conn.execute(
            "SELECT COUNT(*) as c FROM filter_results WHERE job_id = ?", (job_id,)
        ).fetchone()
        assert row[0] == 0

    def test_resurface_clears_job_analysis(self):
        """A resurfaced job should have its job_analysis cleared."""
        db = _make_test_db_with_pipeline_tables()
        old = (datetime.now() - timedelta(days=60)).isoformat()
        url = "http://a.com/resurface"
        job_id = _insert_job_with_scraped_at(db, url, "Dev", "Co", old)

        db._conn.execute(
            "INSERT INTO job_analysis (job_id, ai_score) VALUES (?, 6.0)", (job_id,)
        )

        job_data = {
            "url": url, "title": "Dev", "company": "Co",
            "source": "test", "description": "desc",
        }
        db.insert_job(job_data, dedup_window_days=30)

        row = db._conn.execute(
            "SELECT COUNT(*) as c FROM job_analysis WHERE job_id = ?", (job_id,)
        ).fetchone()
        assert row[0] == 0

    def test_no_pipeline_reset_without_dedup_window(self):
        """With dedup_window_days=0, pipeline records should NOT be cleared."""
        db = _make_test_db_with_pipeline_tables()
        url = "http://a.com/normal"
        job_id = _insert_job_with_scraped_at(
            db, url, "Dev", "Co", datetime.now().isoformat()
        )
        db._conn.execute(
            "INSERT INTO filter_results (job_id, passed) VALUES (?, 1)", (job_id,)
        )

        job_data = {
            "url": url, "title": "Dev", "company": "Co",
            "source": "test", "description": "updated desc",
        }
        db.insert_job(job_data, dedup_window_days=0)

        row = db._conn.execute(
            "SELECT COUNT(*) as c FROM filter_results WHERE job_id = ?", (job_id,)
        ).fetchone()
        assert row[0] == 1  # NOT cleared


def _make_test_db_full() -> JobDatabase:
    """Create an in-memory JobDatabase with full pipeline tables and extra columns for queries."""
    db = _make_test_db_with_pipeline_tables()
    # Add missing columns to filter_results/job_analysis that views/queries need
    for col, table, default in [
        ("filter_version", "filter_results", "''"),
        ("reject_reason", "filter_results", "''"),
        ("matched_rules", "filter_results", "''"),
        ("processed_at", "filter_results", "''"),
        ("recommendation", "job_analysis", "''"),
        ("tailored_resume", "job_analysis", "''"),
        ("resume_tier", "job_analysis", "NULL"),
        ("template_id_final", "job_analysis", "NULL"),
    ]:
        try:
            db._conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} TEXT DEFAULT {default}")
        except sqlite3.OperationalError:
            pass
    return db


def _setup_job_through_pipeline(db, url, title, company, ai_score=6.0,
                                 app_status=None, description="desc"):
    """Insert a job and push it through filter + AI analysis + optional application."""
    job_id = _insert_job_with_scraped_at(
        db, url, title, company, datetime.now().isoformat(), description=description,
    )
    db._conn.execute(
        "INSERT INTO filter_results (job_id, passed) VALUES (?, 1)", (job_id,)
    )
    if ai_score is not None:
        db._conn.execute(
            "INSERT INTO job_analysis (job_id, ai_score, recommendation, resume_tier, tailored_resume) "
            "VALUES (?, ?, 'APPLY', 'USE_TEMPLATE', '{}')",
            (job_id, ai_score),
        )
    if app_status:
        db._conn.execute(
            "INSERT INTO applications (job_id, status, applied_at, updated_at) VALUES (?, ?, ?, ?)",
            (job_id, app_status, datetime.now().isoformat(), datetime.now().isoformat()),
        )
    return job_id


class TestResurfacedJobPipeline:
    """Tests that resurfaced jobs (skipped/rejected) flow through the full pipeline."""

    def test_skipped_job_included_in_needing_analysis(self):
        """A job with 'skipped' app status is still included, with status as metadata."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=None, app_status="skipped",
        )
        jobs = db.get_jobs_needing_analysis()
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] == "skipped"

    def test_rejected_job_included_in_needing_analysis(self):
        """A job with 'rejected' app status is still included, with status as metadata."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=None, app_status="rejected",
        )
        jobs = db.get_jobs_needing_analysis()
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] == "rejected"

    def test_applied_job_included_in_needing_analysis(self):
        """A job with 'applied' app status is still included, with status as metadata."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=None, app_status="applied",
        )
        jobs = db.get_jobs_needing_analysis()
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] == "applied"

    def test_interview_job_included_in_needing_analysis(self):
        """A job with 'interview' app status is still included, with status as metadata."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=None, app_status="interview",
        )
        jobs = db.get_jobs_needing_analysis()
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] == "interview"

    def test_no_app_record_included_in_needing_analysis(self):
        """A job with no application record should be picked up (baseline)."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=None, app_status=None,
        )
        jobs = db.get_jobs_needing_analysis()
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] is None

    def test_skipped_job_included_in_needing_tailor(self):
        """A skipped job is still included in C2, with status as metadata."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=6.0, app_status="skipped",
        )
        db._conn.execute(
            "UPDATE job_analysis SET tailored_resume = NULL, resume_tier = 'ADAPT_TEMPLATE' WHERE job_id = ?",
            (job_id,),
        )
        jobs = db.get_jobs_needing_tailor(min_score=5.0)
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] == "skipped"

    def test_applied_job_included_in_needing_tailor(self):
        """An applied job is still included in C2, with status as metadata."""
        db = _make_test_db_full()
        job_id = _setup_job_through_pipeline(
            db, "http://a.com/1", "Dev", "Co", ai_score=6.0, app_status="applied",
        )
        db._conn.execute(
            "UPDATE job_analysis SET tailored_resume = NULL, resume_tier = 'ADAPT_TEMPLATE' WHERE job_id = ?",
            (job_id,),
        )
        jobs = db.get_jobs_needing_tailor(min_score=5.0)
        match = [j for j in jobs if j["id"] == job_id]
        assert len(match) == 1
        assert match[0]["application_status"] == "applied"
