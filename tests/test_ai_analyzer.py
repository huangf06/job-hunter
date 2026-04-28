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


def _valid_c1_routing_response(*, tier="FULL_CUSTOMIZE", template_id="DE", override=False, override_reason=None):
    return json.dumps({
        "scoring": {
            "overall_score": 7.5,
            "skill_match": 8.0,
            "experience_fit": 7.0,
            "growth_potential": 7.5,
            "recommendation": "APPLY",
            "reasoning": "Strong overall fit."
        },
        "application_brief": {
            "hook": "Relevant track record",
            "key_angle": "Best fit angle",
            "gap_mitigation": None,
            "company_connection": None
        },
        "resume_routing": {
            "tier": tier,
            "template_id": template_id,
            "override": override,
            "override_reason": override_reason,
            "gaps": ["gap a"],
            "adapt_instructions": None
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
                    "company": "BQ Investment",
                    "company_note": "quant hedge fund",
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
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response(_valid_c1_response())
        assert parsed is not None
        assert parsed["scoring"]["overall_score"] == 7.5
        assert parsed["scoring"]["recommendation"] == "APPLY"
        assert parsed["application_brief"]["hook"] is not None

    def test_missing_recommendation_defaults(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({
            "scoring": {"overall_score": 5.0, "reasoning": "OK match"},
            "application_brief": {}
        })
        parsed = analyzer_cls._parse_response(response)
        assert parsed is not None
        assert "recommendation" not in parsed["scoring"]

    def test_score_boundary_39(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({
            "scoring": {"overall_score": 3.9, "recommendation": "MAYBE", "reasoning": "Weak match"},
            "application_brief": {}
        })
        parsed = analyzer_cls._parse_response(response)
        assert parsed["scoring"]["overall_score"] == 3.9

    def test_score_boundary_40(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({
            "scoring": {"overall_score": 4.0, "recommendation": "MAYBE", "reasoning": "Decent match"},
            "application_brief": {}
        })
        parsed = analyzer_cls._parse_response(response)
        assert parsed["scoring"]["overall_score"] == 4.0

    def test_malformed_json_returns_none(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response("This is not JSON at all")
        assert parsed is None

    def test_json_in_code_block_extracted(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = '```json\n{"scoring": {"overall_score": 6.0}}\n```'
        parsed = analyzer_cls._parse_response(response)
        assert parsed is not None
        assert parsed["scoring"]["overall_score"] == 6.0

    def test_application_brief_preserved(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response(_valid_c1_response())
        brief = parsed["application_brief"]
        assert brief["hook"] is not None
        assert brief["key_angle"] is not None
        assert brief["company_connection"] is None

    def test_evaluate_job_resolves_routing_with_c1_override(self):
        from src.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.config = {
            "prompts": {
                "evaluator": (
                    "Title: {job_title}\nCompany: {job_company}\n"
                    "Templates:\n{available_templates}\n"
                    "Preselected: {preselected_template_id} {preselected_confidence} {ambiguous_warning}\n"
                    "{job_description}"
                )
            },
            "ai_recommendation_thresholds": {"apply_now": 7, "apply": 5, "maybe": 3},
            "prompt_settings": {"job_description_max_chars": 10000},
        }
        from src.template_registry import load_registry
        analyzer.registry = load_registry()
        analyzer._call_claude = lambda prompt: _valid_c1_routing_response(
            tier="ADAPT_TEMPLATE",
            template_id="ML",
            override=True,
            override_reason="JD is ML-heavy",
        )

        result = analyzer.evaluate_job(_make_job(title="Data Engineer"))

        assert result.resume_tier == "FULL_CUSTOMIZE"
        assert result.template_id_initial == "DE"
        assert result.template_id_final == "ML"
        assert result.routing_confidence == 0.9
        assert result.routing_override_reason == "JD is ML-heavy"
        assert result.escalation_reason is None
        assert json.loads(result.routing_payload)["template_id"] == "ML"

    def test_evaluate_job_keeps_code_template_without_override(self):
        from src.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.config = {
            "prompts": {
                "evaluator": (
                    "Title: {job_title}\nCompany: {job_company}\n"
                    "Templates:\n{available_templates}\n"
                    "Preselected: {preselected_template_id} {preselected_confidence} {ambiguous_warning}\n"
                    "{job_description}"
                )
            },
            "ai_recommendation_thresholds": {"apply_now": 7, "apply": 5, "maybe": 3},
            "prompt_settings": {"job_description_max_chars": 10000},
        }
        from src.template_registry import load_registry
        analyzer.registry = load_registry()
        analyzer._call_claude = lambda prompt: _valid_c1_routing_response(
            tier="USE_TEMPLATE",
            template_id="ML",
            override=False,
        )

        result = analyzer.evaluate_job(_make_job(title="Data Engineer"))

        assert result.resume_tier == "FULL_CUSTOMIZE"
        assert result.template_id_initial == "DE"
        assert result.template_id_final == "DE"
        assert result.routing_override_reason is None


# =============================================================================
# C2 Tailor Response Parsing
# =============================================================================

class TestTailorResponseParsing:
    """Test C2 tailor response parsing (no AI calls)."""

    def test_valid_response_has_tailored_resume(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        parsed = analyzer_cls._parse_response(_valid_c2_response())
        assert parsed is not None
        assert "tailored_resume" in parsed
        assert len(parsed["tailored_resume"]["experiences"]) >= 2

    def test_empty_tailored_resume(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer_cls = AIAnalyzer.__new__(AIAnalyzer)
        response = json.dumps({"tailored_resume": {}})
        parsed = analyzer_cls._parse_response(response)
        assert parsed is not None
        assert parsed["tailored_resume"] == {}


class TestBioAssemblyCompanyHook:
    """Lock down interview-winning signal #1: bio last sentence names the target company."""

    def _make_analyzer(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._bio_builder = {
            "allowed_titles": ["Data Engineer", "ML Engineer"],
            "domain_claims": {
                "data_pipelines": {"text": "scalable data pipelines and ETL systems"},
            },
            "closer_options": {
                "eager_company": {"text": "Eager to bring these skills to {company}."},
                "seeking_impact": {"text": "Looking forward to delivering data-driven impact at {company}."},
                "generic": {"text": "Eager to contribute to a team where data engineering drives real impact."},
            },
        }
        analyzer._bio_constraints = {"max_years_claim": 6, "min_years_claim": 4}
        analyzer._parsed_bullets = {
            "education": {
                "master": {"degree": "M.Sc. in AI", "school": "VU Amsterdam", "date": "-- Aug. 2025", "gpa": "8.2/10"},
                "certification": "Databricks Certified Data Engineer Professional (2026)",
            }
        }
        return analyzer

    def test_eager_company_closer_substitutes_company_name(self):
        analyzer = self._make_analyzer()
        bio_spec = {
            "role_title": "Data Engineer",
            "years": 6,
            "domain_claims": ["data_pipelines"],
            "include_education": True,
            "include_certification": True,
            "closer_id": "eager_company",
        }
        bio, errors = analyzer._assemble_bio(bio_spec, {"company": "Source.ag"})

        assert errors == []
        assert bio.endswith("Eager to bring these skills to Source.ag.")
        assert "{company}" not in bio

    def test_generic_closer_omits_company_name(self):
        analyzer = self._make_analyzer()
        bio_spec = {
            "role_title": "Data Engineer",
            "years": 6,
            "domain_claims": ["data_pipelines"],
            "include_education": False,
            "include_certification": False,
            "closer_id": "generic",
        }
        bio, errors = analyzer._assemble_bio(bio_spec, {"company": "Hays"})

        assert errors == []
        assert "Hays" not in bio
        assert bio.endswith("real impact.")

    def test_null_closer_produces_no_closing_sentence(self):
        analyzer = self._make_analyzer()
        bio_spec = {
            "role_title": "Data Engineer",
            "years": 6,
            "domain_claims": ["data_pipelines"],
            "include_education": False,
            "include_certification": False,
            "closer_id": None,
        }
        bio, errors = analyzer._assemble_bio(bio_spec, {"company": "Acme"})

        assert errors == []
        assert "Eager" not in bio
        assert "Looking forward" not in bio


class TestTitleContextPerSection:
    """Title context reads from work_experience[key].titles (single source of truth)."""

    def test_title_context_reads_from_work_experience(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._parsed_bullets = {
            'active_sections': {
                'experience_keys': ['glp_technology', 'baiquan_investment'],
            },
            'work_experience': {
                'glp_technology': {
                    'company': 'GLP Technology',
                    'titles': {
                        'default': 'Senior Data Engineer',
                        'data_scientist': 'Senior Data Scientist',
                        'ml_engineer': 'Senior Data Scientist',
                    },
                },
                'baiquan_investment': {
                    'company': 'BQ Investment',
                    'titles': {
                        'default': 'Quantitative Researcher',
                        'data_engineer': 'Quantitative Developer',
                    },
                },
            },
        }

        context = analyzer._build_title_context()

        assert "GLP Technology" in context
        assert "Senior Data Engineer" in context
        assert "Senior Data Scientist" in context
        assert "BQ Investment" in context
        assert "Quantitative Developer" in context

    def test_title_context_empty_when_no_titles(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._parsed_bullets = {
            'active_sections': {'experience_keys': []},
            'work_experience': {},
        }

        context = analyzer._build_title_context()

        assert "most relevant title" in context.lower()


class TestCandidateSummary:
    """C2 candidate summary is generated from bullet_library, not hardcoded."""

    def test_summary_includes_education_and_core_skills(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._parsed_bullets = {
            'education': {
                'master': {
                    'degree': 'M.Sc. in Artificial Intelligence',
                    'school': 'VU Amsterdam',
                    'thesis': 'Uncertainty Quantification in Deep RL',
                },
                'certification': 'Databricks Certified Data Engineer Professional (2026)',
            },
            'active_sections': {
                'experience_keys': ['glp_technology'],
            },
            'work_experience': {
                'glp_technology': {
                    'company': 'GLP Technology',
                    'titles': {'default': 'Senior Data Engineer'},
                    'verified_bullets': [
                        {'id': 'glp_founding_member', 'content': 'Joined as founding data engineer...', 'status': 'active'},
                    ],
                },
            },
            'skill_tiers': {
                'verified': {
                    'languages': ['Python (Expert)', 'SQL (Expert)', 'Bash'],
                    'data_engineering': ['PySpark', 'Spark', 'Delta Lake', 'Databricks'],
                    'cloud': ['AWS (Redshift, S3, EC2)', 'Docker', 'Airflow'],
                    'ml': ['PyTorch', 'XGBoost', 'scikit-learn'],
                },
            },
        }

        summary = analyzer._build_candidate_summary()

        assert 'M.Sc. in Artificial Intelligence' in summary
        assert 'VU Amsterdam' in summary
        assert 'Databricks Certified' in summary
        assert 'GLP Technology' in summary
        assert 'Senior Data Engineer' in summary
        assert 'Python' in summary
        assert 'PySpark' in summary
        assert 'PyTorch' in summary


class TestAnalyzeJobFlow:
    def test_analyze_job_full_customize_runs_c2(self):
        from src.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.registry = {"templates": {}}
        analyzer.config = {"thresholds": {"ai_score_generate_resume": 4.0}}

        saved_results = []

        class DBStub:
            def save_analysis(self, result):
                saved_results.append(result)

        analyzer.db = DBStub()
        analyzer.evaluate_job = lambda job: AnalysisResult(
            job_id=job["id"],
            ai_score=8.0,
            recommendation="APPLY_NOW",
            reasoning=json.dumps({"reasoning": "ok", "application_brief": {}}),
            tailored_resume="{}",
            model="claude_code",
            resume_tier="FULL_CUSTOMIZE",
            template_id_initial="DE",
            template_id_final="DE",
            routing_confidence=0.3,
            routing_payload=json.dumps({"tier": "FULL_CUSTOMIZE"}),
        )
        analyzer.tailor_resume = lambda job, analysis, c1_routing=None: json.dumps({"bio": "Full custom bio"})

        result = analyzer.analyze_job(_make_job(title="Research Engineer"))

        assert result.resume_tier == "FULL_CUSTOMIZE"
        assert json.loads(result.tailored_resume)["bio"] == "Full custom bio"
        assert len(saved_results) == 1


def test_analyze_batch_does_not_double_save_analysis():
    from src.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    analyzer.db = type("DBStub", (), {"batch_mode": lambda self: __import__("contextlib").nullcontext()})()
    save_calls = []

    class DBStub:
        def get_jobs_needing_analysis(self, limit=None):
            return [_make_job()]

        def save_analysis(self, result):
            save_calls.append(result.job_id)

        def batch_mode(self):
            return __import__("contextlib").nullcontext()

    analyzer.db = DBStub()
    analyzer.analyze_job = lambda job: AnalysisResult(
        job_id=job["id"],
        ai_score=7.0,
        recommendation="APPLY",
        reasoning=json.dumps({"reasoning": "ok", "application_brief": {}}),
        tailored_resume="{}",
        model="claude_code",
        resume_tier="FULL_CUSTOMIZE",
    )

    analyzed = analyzer.analyze_batch()

    assert analyzed == 1
    assert save_calls == []


def test_analyze_single_does_not_double_save_analysis():
    from src.ai_analyzer import AIAnalyzer

    analyzer = AIAnalyzer.__new__(AIAnalyzer)

    class DBStub:
        def get_job(self, job_id):
            return _make_job(job_id=job_id)

        def save_analysis(self, result):
            pytest.fail("analyze_single should not save again after analyze_job")

    analyzer.db = DBStub()
    analyzer.analyze_job = lambda job: AnalysisResult(
        job_id=job["id"],
        ai_score=7.0,
        recommendation="APPLY",
        reasoning=json.dumps({"reasoning": "ok", "application_brief": {}}),
        tailored_resume="{}",
        model="claude_code",
        resume_tier="FULL_CUSTOMIZE",
        template_id_final="DE",
    )

    result = analyzer.analyze_single("job-1")

    assert result is not None
    assert result.job_id == "job-1"


# =============================================================================
# DB Workflow Tests
# =============================================================================

class TestJobAnalysisDB:
    """Test C1/C2 DB workflow using in-memory database."""

    @pytest.fixture
    def db(self):
        """Create a test database."""
        from src.db.job_db import JobDatabase
        test_db = JobDatabase.__new__(JobDatabase)
        import sqlite3
        test_db._local_db_path = ":memory:"
        test_db._turso_url = None
        test_db._turso_token = None
        test_db._conn = sqlite3.connect(":memory:")
        test_db._conn.row_factory = sqlite3.Row
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
                resume_tier TEXT,
                template_id_initial TEXT,
                template_id_final TEXT,
                routing_confidence REAL,
                routing_override_reason TEXT,
                escalation_reason TEXT,
                routing_payload TEXT,
                c3_decision TEXT,
                c3_confidence REAL,
                c3_reason TEXT,
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
        from contextlib import contextmanager
        @contextmanager
        def _get_conn(sync_before=True):
            yield test_db._conn
        test_db._get_conn = _get_conn

        @contextmanager
        def batch_mode():
            yield
        test_db.batch_mode = batch_mode
        return test_db

    def test_save_then_update_resume(self, db):
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

        analysis = db.get_analysis("test-001")
        assert analysis is not None
        assert analysis["ai_score"] == 7.5
        assert analysis["tailored_resume"] == "{}"

        resume_json = json.dumps({"bio": "Test bio", "experiences": []})
        db.update_analysis_resume("test-001", resume_json)

        analysis = db.get_analysis("test-001")
        assert analysis["ai_score"] == 7.5
        assert analysis["recommendation"] == "APPLY"
        assert json.loads(analysis["tailored_resume"])["bio"] == "Test bio"

    def test_get_jobs_needing_tailor(self, db):
        db._conn.execute(
            "INSERT INTO jobs (id, title, company, description, location) VALUES (?, ?, ?, ?, ?)",
            ("job-1", "Data Engineer", "TestCorp", "Description here", "Amsterdam")
        )
        db._conn.execute(
            """INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            ("job-1", 6.0, "APPLY", "Good match", "{}", "claude_code", 0, "2026-03-28")
        )

        jobs = db.get_jobs_needing_tailor(min_score=4.0)
        assert len(jobs) == 1
        assert jobs[0]["id"] == "job-1"
        assert jobs[0]["ai_score"] == 6.0

        jobs = db.get_jobs_needing_tailor(min_score=7.0)
        assert len(jobs) == 0

    def test_get_jobs_needing_tailor_excludes_tailored(self, db):
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
