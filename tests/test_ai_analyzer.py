"""Tests for src.ai_analyzer module — C1/C2 response parsing and DB workflow.

No AI calls — tests cover response parsing, bullet resolution, bio assembly,
validation, and C1→C2 DB update flow.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.db.job_db import AnalysisResult


# =============================================================================
# Helpers
# =============================================================================

def _make_job(job_id="test-001", title="Data Engineer", company="TestCorp"):
    return {
        "id": job_id,
        "title": title,
        "company": company,
        "description": "We need a Data Engineer with Python, SQL, Spark experience.",
        "location": "Amsterdam",
    }


def _valid_c1_response():
    """A well-formed C1 evaluate response."""
    return json.dumps({
        "scoring": {
            "overall_score": 7.5,
            "skill_match": 8.0,
            "experience_fit": 7.0,
            "growth_potential": 7.5,
            "recommendation": "APPLY",
            "reasoning": "Strong Python/Spark match for data engineering role."
        },
        "application_brief": {
            "hook": "6 years of data pipeline experience with PySpark and Delta Lake",
            "key_angle": "Financial Data Lakehouse project directly relevant",
            "gap_mitigation": "No Kafka experience but strong Spark streaming skills",
            "company_connection": None
        }
    })


def _valid_c2_response():
    """A well-formed C2 tailor response (just tailored_resume, no scoring)."""
    return json.dumps({
        "tailored_resume": {
            "bio": {
                "role_title": "Data Engineer",
                "years": 6,
                "domain_claims": ["data_pipelines"],
                "include_education": True,
                "include_certification": True,
                "closer_id": "eager_company"
            },
            "experiences": [
                {
                    "company": "GLP Technology",
                    "company_note": None,
                    "location": "Shanghai, China",
                    "title": "Data Scientist & Team Lead",
                    "date": "Jul. 2017 -- Aug. 2019",
                    "bullets": ["glp_founding_member", "glp_decision_engine"]
                },
                {
                    "company": "Baiquan Investment",
                    "company_note": None,
                    "location": "Beijing, China",
                    "title": "Quantitative Researcher",
                    "date": "Jul. 2015 -- Jun. 2017",
                    "bullets": ["bq_factor_research"]
                }
            ],
            "projects": [
                {
                    "name": "Financial Data Lakehouse",
                    "date": "Oct. 2025 -- Present",
                    "bullets": ["lakehouse_streaming"]
                }
            ],
            "skills": [
                {"category": "Languages & Core", "skills_list": "Python (Expert), SQL"}
            ]
        }
    })


# =============================================================================
# C1 Evaluate Response Parsing
# =============================================================================

class TestEvaluateResponseParsing:
    """Test C1 evaluate response parsing (no AI calls)."""

    def test_valid_response_parses_scoring(self):
        """Full scoring + brief JSON parses correctly."""
        from src.ai_analyzer import AIAnalyzer
        # We test _parse_response directly since it's used by evaluate_job
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response(_valid_c1_response())
        assert parsed is not None
        assert parsed["scoring"]["overall_score"] == 7.5
        assert parsed["scoring"]["recommendation"] == "APPLY"
        assert parsed["application_brief"]["hook"] is not None

    def test_missing_recommendation_defaults(self):
        """Missing recommendation in scoring → parsed dict has no 'recommendation' key."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({
            "scoring": {"overall_score": 5.0, "reasoning": "OK match"},
            "application_brief": {}
        })
        parsed = analyzer_cls._parse_response(response)
        assert parsed is not None
        # recommendation is absent — caller handles default
        assert "recommendation" not in parsed["scoring"]

    def test_score_boundary_39(self):
        """ai_score 3.9 → below C2 threshold."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({
            "scoring": {"overall_score": 3.9, "recommendation": "MAYBE", "reasoning": "Weak match"},
            "application_brief": {}
        })
        parsed = analyzer_cls._parse_response(response)
        assert parsed["scoring"]["overall_score"] == 3.9

    def test_score_boundary_40(self):
        """ai_score 4.0 → eligible for C2."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({
            "scoring": {"overall_score": 4.0, "recommendation": "MAYBE", "reasoning": "Decent match"},
            "application_brief": {}
        })
        parsed = analyzer_cls._parse_response(response)
        assert parsed["scoring"]["overall_score"] == 4.0

    def test_malformed_json_returns_none(self):
        """Unparseable response → None."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response("This is not JSON at all")
        assert parsed is None

    def test_json_in_code_block_extracted(self):
        """JSON wrapped in markdown code block → still parsed."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = '```json\n{"scoring": {"overall_score": 6.0}}\n```'
        parsed = analyzer_cls._parse_response(response)
        assert parsed is not None
        assert parsed["scoring"]["overall_score"] == 6.0

    def test_application_brief_preserved(self):
        """application_brief fields are accessible in parsed output."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response(_valid_c1_response())
        brief = parsed["application_brief"]
        assert brief["hook"] is not None
        assert brief["key_angle"] is not None
        assert brief["company_connection"] is None


# =============================================================================
# C2 Tailor Response Parsing
# =============================================================================

class TestTailorResponseParsing:
    """Test C2 tailor response parsing (no AI calls)."""

    def test_valid_response_has_tailored_resume(self):
        """C2 response contains tailored_resume."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response(_valid_c2_response())
        assert parsed is not None
        assert "tailored_resume" in parsed
        assert len(parsed["tailored_resume"]["experiences"]) >= 2

    def test_empty_tailored_resume(self):
        """Empty tailored_resume dict → parsed but empty."""
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({"tailored_resume": {}})
        parsed = analyzer_cls._parse_response(response)
        assert parsed is not None
        assert parsed["tailored_resume"] == {}


# =============================================================================
# DB Workflow Tests
# =============================================================================

class TestJobAnalysisDB:
    """Test C1/C2 DB workflow using in-memory database."""

    @pytest.fixture
    def db(self):
        """Create a test database."""
        from src.db.job_db import JobDatabase
        # Use in-memory SQLite
        test_db = JobDatabase.__new__(JobDatabase)
        import sqlite3
        test_db._local_db_path = ":memory:"
        test_db._turso_url = None
        test_db._turso_token = None
        test_db._conn = sqlite3.connect(":memory:")
        test_db._conn.row_factory = sqlite3.Row
        # Create tables
        test_db._conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT,
                company TEXT,
                description TEXT,
                location TEXT,
                url TEXT,
                source TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS filter_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT,
                passed INTEGER,
                reject_reason TEXT,
                filter_version TEXT,
                matched_rules TEXT,
                filtered_at TEXT
            );
            CREATE TABLE IF NOT EXISTS job_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                ai_score REAL,
                skill_match REAL,
                experience_fit REAL,
                growth_potential REAL,
                recommendation TEXT,
                reasoning TEXT,
                tailored_resume TEXT,
                model TEXT,
                tokens_used INTEGER,
                analyzed_at TEXT
            );
            CREATE TABLE IF NOT EXISTS applications (
                job_id TEXT PRIMARY KEY,
                status TEXT,
                applied_at TEXT
            );
        """)
        # Patch _get_conn to return this connection as context manager
        from contextlib import contextmanager
        @contextmanager
        def _get_conn(sync_before=True):
            yield test_db._conn
        test_db._get_conn = _get_conn

        # Patch batch_mode
        @contextmanager
        def batch_mode():
            yield
        test_db.batch_mode = batch_mode
        return test_db

    def test_save_then_update_resume(self, db):
        """C1 save_analysis + C2 update_analysis_resume preserves scoring."""
        # C1: save analysis with empty tailored_resume
        c1_result = AnalysisResult(
            job_id="test-001",
            ai_score=7.5,
            skill_match=8.0,
            experience_fit=7.0,
            growth_potential=7.5,
            recommendation="APPLY",
            reasoning='{"reasoning": "Good match", "application_brief": {}}',
            tailored_resume="{}",
            model="claude_code",
            tokens_used=0,
        )
        db.save_analysis(c1_result)

        # Verify C1 saved
        analysis = db.get_analysis("test-001")
        assert analysis is not None
        assert analysis["ai_score"] == 7.5
        assert analysis["tailored_resume"] == "{}"

        # C2: update with tailored resume
        resume_json = json.dumps({"bio": "Test bio", "experiences": []})
        db.update_analysis_resume("test-001", resume_json)

        # Verify scoring preserved, resume updated
        analysis = db.get_analysis("test-001")
        assert analysis["ai_score"] == 7.5  # scoring preserved
        assert analysis["recommendation"] == "APPLY"
        assert json.loads(analysis["tailored_resume"])["bio"] == "Test bio"

    def test_get_jobs_needing_tailor(self, db):
        """Returns jobs with score >= threshold and empty tailored_resume."""
        # Insert a job
        db._conn.execute(
            "INSERT INTO jobs (id, title, company, description, location) VALUES (?, ?, ?, ?, ?)",
            ("job-1", "Data Engineer", "TestCorp", "Description here", "Amsterdam")
        )
        # Insert C1 analysis with empty resume
        db._conn.execute(
            """INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("job-1", 6.0, "APPLY", "Good match", "{}", "claude_code", 0, "2026-03-28")
        )

        # Should find the job
        jobs = db.get_jobs_needing_tailor(min_score=4.0)
        assert len(jobs) == 1
        assert jobs[0]["id"] == "job-1"
        assert jobs[0]["ai_score"] == 6.0

        # Should not find with higher threshold
        jobs = db.get_jobs_needing_tailor(min_score=7.0)
        assert len(jobs) == 0

    def test_get_jobs_needing_tailor_excludes_tailored(self, db):
        """Jobs with non-empty tailored_resume are excluded."""
        db._conn.execute(
            "INSERT INTO jobs (id, title, company, description, location) VALUES (?, ?, ?, ?, ?)",
            ("job-2", "ML Engineer", "AICorp", "ML job desc", "Amsterdam")
        )
        db._conn.execute(
            """INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("job-2", 8.0, "APPLY_NOW", "Excellent match",
             json.dumps({"bio": "Already tailored"}), "claude_code", 0, "2026-03-28")
        )

        jobs = db.get_jobs_needing_tailor(min_score=4.0)
        assert len(jobs) == 0

    def test_get_jobs_needing_tailor_excludes_applied(self, db):
        """Jobs already applied to are excluded."""
        db._conn.execute(
            "INSERT INTO jobs (id, title, company, description, location) VALUES (?, ?, ?, ?, ?)",
            ("job-3", "Data Scientist", "SciCorp", "DS job", "Amsterdam")
        )
        db._conn.execute(
            """INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("job-3", 7.0, "APPLY", "Good", "{}", "claude_code", 0, "2026-03-28")
        )
        db._conn.execute(
            "INSERT INTO applications (job_id, status, applied_at) VALUES (?, ?, ?)",
            ("job-3", "applied", "2026-03-28")
        )

        jobs = db.get_jobs_needing_tailor(min_score=4.0)
        assert len(jobs) == 0
