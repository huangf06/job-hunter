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


def _valid_c1_routing_response(*, tier="USE_TEMPLATE", template_id="DE", override=False, override_reason=None):
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
            "adapt_instructions": "Adjust positioning" if tier == "ADAPT_TEMPLATE" else None
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

        # Post-2026-04-17 revert: resume_tier is forced to FULL_CUSTOMIZE regardless
        # of what the AI emits. Template override (ML) is still honored.
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

        # Post-2026-04-17 revert: retired USE_TEMPLATE emission is coerced to FULL_CUSTOMIZE.
        assert result.resume_tier == "FULL_CUSTOMIZE"
        assert result.template_id_initial == "DE"
        assert result.template_id_final == "DE"
        assert result.routing_override_reason is None

    def test_evaluate_job_applies_low_confidence_tier1_safeguard(self):
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

        # Post-2026-04-17: safeguard is a no-op, but resolve_routing forces FULL_CUSTOMIZE.
        result = analyzer.evaluate_job(_make_job(title="ML Platform Engineer"))

        assert result.template_id_initial == "ML"
        assert result.routing_confidence == 0.5
        assert result.resume_tier == "FULL_CUSTOMIZE"
        assert result.escalation_reason is None


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


class TestBioAssemblyCompanyHook:
    """Lock down interview-winning signal #1: bio last sentence names the target company.

    All 8 pre-upgrade interview-winning resumes had a company-named closer
    ("Eager to bring these skills to Source.ag.", etc.). This test ensures the
    structured bio assembly preserves that behavior under the FULL_CUSTOMIZE flow.
    """

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
        analyzer.config = {
            "resume": {
                "education": {
                    "master": {"degree": "M.Sc. in AI", "school": "VU Amsterdam", "date": "-- Aug. 2025", "gpa": "8.2/10"},
                    "certification": "Databricks Certified Data Engineer Professional (2026)",
                }
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
    """Lock down interview-winning signal #2: role titles rotate per experience.

    Pre-upgrade interview resumes used different titles per company (e.g., "Data
    Engineer & Team Lead" at GLP for DE roles, "ML Engineer and Team Lead" at GLP
    for ML roles). The title_context feeds the AI a per-company list so it can pick.
    """

    def test_title_context_lists_each_company_with_its_options(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._title_options = {
            "glp_technology": {"de": "Data Engineer & Team Lead", "ml": "ML Engineer and Team Lead"},
            "baiquan_investment": {"de": "Quantitative Developer", "ml": "Quantitative Researcher"},
        }

        context = analyzer._build_title_context()

        assert "Glp Technology" in context
        assert "Data Engineer & Team Lead" in context
        assert "ML Engineer and Team Lead" in context
        assert "Baiquan Investment" in context
        assert "Quantitative Developer" in context

    def test_title_context_empty_when_no_options(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._title_options = {}

        context = analyzer._build_title_context()

        assert "most relevant title" in context.lower()


class TestAnalyzeJobFlow:
    def test_analyze_job_use_template_skips_c2_and_creates_resume_record(self):
        from src.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.registry = {
            "templates": {
                "DE": {"pdf": "templates/pdf/Fei_Huang_DE.pdf"},
            }
        }
        analyzer.config = {"thresholds": {"ai_score_generate_resume": 4.0}}

        saved_results = []
        saved_resumes = []

        class DBStub:
            def save_analysis(self, result):
                saved_results.append(result)

            def save_resume(self, resume):
                saved_resumes.append(resume)

        analyzer.db = DBStub()
        analyzer.evaluate_job = lambda job: AnalysisResult(
            job_id=job["id"],
            ai_score=7.0,
            recommendation="APPLY",
            reasoning=json.dumps({"reasoning": "ok", "application_brief": {}}),
            tailored_resume="{}",
            model="claude_code",
            resume_tier="USE_TEMPLATE",
            template_id_initial="DE",
            template_id_final="DE",
            routing_confidence=0.9,
            routing_payload=json.dumps({"tier": "USE_TEMPLATE"}),
        )
        analyzer.tailor_resume = lambda *args, **kwargs: pytest.fail("Tier 1 should not call C2")
        analyzer.run_c3_gate = lambda *args, **kwargs: pytest.fail("Tier 1 should not call C3")

        result = analyzer.analyze_job(_make_job())

        assert result.resume_tier == "USE_TEMPLATE"
        assert len(saved_results) == 1
        assert len(saved_resumes) == 1
        assert saved_resumes[0].pdf_path == "templates/pdf/Fei_Huang_DE.pdf"

    def test_analyze_job_adapt_template_runs_c2_and_c3(self):
        from src.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.registry = {"templates": {"ML": {"pdf": "templates/pdf/Fei_Huang_ML.pdf"}}}
        analyzer.config = {"thresholds": {"ai_score_generate_resume": 4.0}}

        saved_results = []

        class DBStub:
            def save_analysis(self, result):
                saved_results.append(result)

            def save_resume(self, resume):
                pytest.fail("Tier 2 should not create template resume record here")

        analyzer.db = DBStub()
        analyzer.evaluate_job = lambda job: AnalysisResult(
            job_id=job["id"],
            ai_score=7.5,
            recommendation="APPLY",
            reasoning=json.dumps({"reasoning": "ok", "application_brief": {}}),
            tailored_resume="{}",
            model="claude_code",
            resume_tier="ADAPT_TEMPLATE",
            template_id_initial="ML",
            template_id_final="ML",
            routing_confidence=0.5,
            routing_payload=json.dumps(
                {"tier": "ADAPT_TEMPLATE", "gaps": ["gap"], "adapt_instructions": "adapt"}
            ),
        )
        analyzer.tailor_resume = lambda job, analysis, c1_routing=None: json.dumps(
            {
                "slot_overrides": {"bio": "Adapted bio"},
                "skills_override": {},
                "entry_visibility": {},
                "change_summary": "Changed bio",
            }
        )
        analyzer.run_c3_gate = lambda analysis, c1_routing, job: {
            "decision": "PASS",
            "confidence": 0.88,
            "reason": "Worth adapting",
        }

        result = analyzer.analyze_job(_make_job(title="ML Engineer"))

        assert result.resume_tier == "ADAPT_TEMPLATE"
        assert result.c3_decision == "PASS"
        assert result.c3_confidence == 0.88
        assert json.loads(result.tailored_resume)["slot_overrides"]["bio"] == "Adapted bio"
        assert len(saved_results) == 1

    def test_analyze_job_full_customize_skips_c3(self):
        from src.ai_analyzer import AIAnalyzer

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.registry = {"templates": {}}
        analyzer.config = {"thresholds": {"ai_score_generate_resume": 4.0}}

        saved_results = []

        class DBStub:
            def save_analysis(self, result):
                saved_results.append(result)

            def save_resume(self, resume):
                pytest.fail("Tier 3 should not create template resume record")

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
        analyzer.run_c3_gate = lambda *args, **kwargs: pytest.fail("Tier 3 should not call C3")

        result = analyzer.analyze_job(_make_job(title="Research Engineer"))

        assert result.resume_tier == "FULL_CUSTOMIZE"
        assert json.loads(result.tailored_resume)["bio"] == "Full custom bio"
        assert result.c3_decision is None
        assert len(saved_results) == 1


def test_build_tier2_prompt_raises_after_2026_04_17_revert():
    """After 2026-04-17 revert: slot_schema is removed from the registry and
    _build_tier2_prompt is dead code — it raises with a re-analyze hint. New
    C1 routing always emits tier=FULL_CUSTOMIZE so this function is not called
    in the normal path."""
    import pytest

    from src.ai_analyzer import AIAnalyzer
    from src.template_registry import load_registry

    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    analyzer.config = {
        "prompts": {"tailor_adapt": "SCHEMA:\n{template_schema}"},
        "prompt_settings": {"job_description_max_chars": 10000},
    }
    analyzer.registry = load_registry()

    with pytest.raises(ValueError, match="slot_schema missing"):
        analyzer._build_tier2_prompt(
            _make_job(title="Data Engineer"),
            {"template_id_final": "DE"},
            {"gaps": [], "adapt_instructions": ""},
        )


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
        resume_tier="USE_TEMPLATE",
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
        resume_tier="USE_TEMPLATE",
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
