"""Tests for bullet version tracking tables and operations."""

import hashlib
import os
import tempfile
from pathlib import Path

import pytest
from src.db.job_db import JobDatabase


@pytest.fixture
def db():
    os.environ["NO_TURSO"] = "1"
    tmpdir = tempfile.mkdtemp()
    return JobDatabase(db_path=Path(tmpdir) / "test.db")


class TestBulletTrackingSchema:
    def test_bullet_versions_table_exists(self, db):
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bullet_versions'")
        assert len(rows) == 1

    def test_bullet_usage_table_exists(self, db):
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bullet_usage'")
        assert len(rows) == 1

    def test_interview_rounds_table_exists(self, db):
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='interview_rounds'")
        assert len(rows) == 1

    def test_insert_bullet_version(self, db):
        content = "Built PySpark ETL pipelines processing credit data."
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        db.execute(
            "INSERT INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("glp_pyspark", content_hash, content, "v3.0"),
        )
        rows = db.execute("SELECT * FROM bullet_versions WHERE bullet_id = ?", ("glp_pyspark",))
        assert len(rows) == 1
        assert rows[0]["content_hash"] == content_hash

    def test_insert_bullet_usage(self, db):
        db.execute(
            "INSERT INTO jobs (id, source, url, title, company, scraped_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            ("j1", "test", "https://example.com/j1", "Data Engineer", "TestCo"),
        )
        db.execute(
            "INSERT INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
            ("u1", "j1", "glp_pyspark", "abc123", "experience", 0),
        )
        rows = db.execute("SELECT * FROM bullet_usage WHERE job_id = ?", ("j1",))
        assert len(rows) == 1
        assert rows[0]["bullet_id"] == "glp_pyspark"

    def test_bullet_version_upsert_idempotent(self, db):
        content = "Some bullet text."
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        db.execute(
            "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("b1", h, content, "v5.0"),
        )
        db.execute(
            "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("b1", h, content, "v5.0"),
        )
        rows = db.execute("SELECT * FROM bullet_versions WHERE bullet_id = ?", ("b1",))
        assert len(rows) == 1
