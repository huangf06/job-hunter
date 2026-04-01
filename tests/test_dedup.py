"""Tests for cross-platform semantic dedup during import."""
import os
import sqlite3
from contextlib import contextmanager

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
            raw_data TEXT DEFAULT ''
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
