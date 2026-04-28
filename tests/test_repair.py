"""Tests for --repair: clearing orphan resume records."""
import os
import sqlite3
import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

from src.db.job_db import JobDatabase


def _make_test_db() -> JobDatabase:
    """Create an in-memory JobDatabase with minimal schema for repair tests."""
    db = JobDatabase.__new__(JobDatabase)
    db._turso_http = None
    db._conn = sqlite3.connect(":memory:")
    db._conn.row_factory = sqlite3.Row
    db._conn.executescript("""
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            source TEXT,
            url TEXT,
            title TEXT,
            company TEXT
        );

        CREATE TABLE job_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            ai_score REAL,
            recommendation TEXT,
            reasoning TEXT,
            tailored_resume TEXT,
            model TEXT
        );

        CREATE TABLE resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            role_type TEXT,
            template_version TEXT,
            html_path TEXT,
            pdf_path TEXT,
            generated_at TEXT
        );

        CREATE TABLE cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            spec_json TEXT,
            standard_text TEXT,
            tokens_used INTEGER
        );
    """)

    @contextmanager
    def fake_get_conn(sync_before=True):
        yield db._conn

    db._get_conn = fake_get_conn
    return db


class TestClearOrphanResumes:
    """Tests for JobDatabase.clear_orphan_resumes()."""

    def setup_method(self):
        self.tmp_dir = Path("_tmp_test_artifacts") / f"repair_{uuid.uuid4().hex[:8]}"
        self.tmp_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_clears_resume_with_missing_pdf(self):
        """Resume record whose pdf_path file doesn't exist should be cleared."""
        db = _make_test_db()

        db.execute("INSERT INTO jobs (id, source, url, title, company) VALUES ('j1', 'test', 'http://x', 'Dev', 'Co')")
        db.execute("INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model) VALUES ('j1', 8.0, 'APPLY', '{}', '{}', 'test')")
        fake_pdf = os.path.join(self.tmp_dir, "nonexistent.pdf")
        db.execute("INSERT INTO resumes (job_id, role_type, template_version, pdf_path) VALUES ('j1', 'de', '1.0', ?)", (fake_pdf,))

        cleared = db.clear_orphan_resumes()
        assert cleared == 1

        rows = db.execute("SELECT * FROM resumes WHERE job_id = 'j1'")
        assert len(rows) == 0

    def test_keeps_resume_with_existing_pdf(self):
        """Resume record whose pdf_path file exists should NOT be cleared."""
        db = _make_test_db()

        db.execute("INSERT INTO jobs (id, source, url, title, company) VALUES ('j2', 'test', 'http://y', 'Dev', 'Co')")
        real_pdf = os.path.join(self.tmp_dir, "real.pdf")
        with open(real_pdf, 'w') as f:
            f.write("fake pdf")
        db.execute("INSERT INTO resumes (job_id, role_type, template_version, pdf_path) VALUES ('j2', 'de', '1.0', ?)", (str(real_pdf),))

        cleared = db.clear_orphan_resumes()
        assert cleared == 0

        rows = db.execute("SELECT * FROM resumes WHERE job_id = 'j2'")
        assert len(rows) == 1

    def test_also_clears_orphan_cover_letters(self):
        """When a resume is cleared, its cover letter should also be cleared."""
        db = _make_test_db()

        db.execute("INSERT INTO jobs (id, source, url, title, company) VALUES ('j3', 'test', 'http://z', 'Dev', 'Co')")
        db.execute("INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model) VALUES ('j3', 8.0, 'APPLY', '{}', '{}', 'test')")
        fake_pdf = os.path.join(self.tmp_dir, "gone.pdf")
        db.execute("INSERT INTO resumes (job_id, role_type, template_version, pdf_path) VALUES ('j3', 'de', '1.0', ?)", (fake_pdf,))
        db.execute("INSERT INTO cover_letters (job_id, spec_json, standard_text, tokens_used) VALUES ('j3', '{}', 'text', 0)")

        cleared = db.clear_orphan_resumes()
        assert cleared == 1

        cl_rows = db.execute("SELECT * FROM cover_letters WHERE job_id = 'j3'")
        assert len(cl_rows) == 0
