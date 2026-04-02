import json
from pathlib import Path
import uuid

from jinja2 import Environment, FileSystemLoader

from src.resume_renderer import ResumeRenderer


def _local_tmp_dir(name: str) -> Path:
    path = Path("_tmp_test_artifacts") / f"{name}_{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


class _ValidationPass:
    passed = True
    warnings = []
    fixes = {}
    errors = []


class _ValidatorStub:
    def validate(self, tailored, job, tier=None):
        return _ValidationPass()

    def validate_adapt_zones(self, context):
        return _ValidationPass()


class _DBStub:
    def __init__(self, analysis, job):
        self._analysis = analysis
        self._job = job
        self.saved_resume = None
        self.jobs_for_resume = []

    def get_analysis(self, job_id):
        return self._analysis

    def get_job(self, job_id):
        return self._job

    def save_resume(self, resume):
        self.saved_resume = resume

    def get_analyzed_jobs_for_resume(self, min_ai_score=None, limit=None):
        return self.jobs_for_resume


def _make_renderer(tmp_dir: Path, analysis: dict):
    renderer = ResumeRenderer.__new__(ResumeRenderer)
    renderer.config = {"resume": {"candidate": {"name": "Fei Huang"}}}
    renderer.template_dir = Path("templates")
    renderer.output_dir = tmp_dir / "output"
    renderer.ready_dir = tmp_dir / "ready"
    renderer.output_dir.mkdir(parents=True, exist_ok=True)
    renderer.ready_dir.mkdir(parents=True, exist_ok=True)
    renderer.jinja_env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    renderer.candidate = {"name": "Fei Huang"}
    renderer.base_context = {
        "name": "Fei Huang",
        "email": "huangf06@gmail.com",
        "phone": "+31 645 038 614",
        "location": "Amsterdam, Netherlands",
    }
    renderer.validator = _ValidatorStub()
    renderer.registry = {
        "templates": {
            "DE": {
                "pdf": str((tmp_dir / "source_de.pdf").resolve()),
                "slot_schema": {
                    "bio": {
                        "slot_id": "bio",
                        "bio_1": {"default": "Default bio line one."},
                        "bio_2": {"default": "Default bio line two."},
                        "bio_3": {"default": "Default bio line three."},
                    },
                    "sections": [
                        {
                            "section_id": "experience",
                            "entries": [
                                {
                                    "entry_id": "glp",
                                    "company": "GLP",
                                    "title": "Lead",
                                    "date": "2017-2019",
                                    "bullets": [{"slot_id": "glp_1", "default": "Default bullet"}],
                                }
                            ],
                        },
                        {
                            "section_id": "skills",
                            "categories": [{"cat_id": "programming", "default": "Python, SQL"}],
                        },
                    ],
                },
            }
        }
    }
    (tmp_dir / "source_de.pdf").write_bytes(b"template-pdf-bytes")
    renderer.db = _DBStub(
        analysis,
        {
            "id": "job-1",
            "title": "Data Engineer",
            "company": "TestCorp",
            "location": "Amsterdam",
            "description": "desc",
        },
    )
    renderer._html_to_pdf = lambda html_path, pdf_path, margin_override=None: pdf_path.write_bytes(b"rendered-pdf") or True
    return renderer


def test_render_resume_use_template_copies_pdf_byte_identically():
    tmp_dir = _local_tmp_dir("renderer_test_workspace_use")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "USE_TEMPLATE",
            "template_id_final": "DE",
            "tailored_resume": "{}",
        },
    )

    result = renderer.render_resume("job-1")

    assert result is not None
    copied = Path(result["pdf_path"]).read_bytes()
    assert copied == b"template-pdf-bytes"


def test_render_resume_adapt_template_pass_generates_files():
    tmp_dir = _local_tmp_dir("renderer_test_workspace_adapt")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "ADAPT_TEMPLATE",
            "template_id_final": "DE",
            "c3_decision": "PASS",
            "tailored_resume": json.dumps(
                {
                    "slot_overrides": {"bio_1": "Adapted bio line one.", "bio_2": "Adapted line two.", "bio_3": "Adapted line three.", "glp_1": "Adapted bullet"},
                    "skills_override": {"programming": "Python, SQL, Scala"},
                    "entry_visibility": {"glp": True},
                    "change_summary": "Changed bio and bullet",
                }
            ),
        },
    )

    result = renderer.render_resume("job-1")

    assert result is not None
    assert Path(result["html_path"]).exists()
    assert Path(result["pdf_path"]).exists()


def test_render_resume_full_customize_uses_legacy_render_path():
    tmp_dir = _local_tmp_dir("renderer_test_workspace_full")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "FULL_CUSTOMIZE",
            "tailored_resume": json.dumps(
                {
                    "bio": "Full custom bio",
                    "experiences": [{"company": "GLP", "title": "Lead", "date": "2017-2019", "bullets": ["Bullet"]}],
                    "projects": [],
                    "skills": [{"category": "Languages & Core", "skills_list": "Python, SQL"}],
                }
            ),
        },
    )

    result = renderer.render_resume("job-1")

    assert result is not None
    assert Path(result["html_path"]).exists()
    assert Path(result["pdf_path"]).exists()


def test_render_template_copy_unknown_template_returns_none():
    tmp_dir = _local_tmp_dir("renderer_unknown_tpl_copy")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "USE_TEMPLATE",
            "template_id_final": "NONEXISTENT",
            "tailored_resume": "{}",
        },
    )
    result = renderer.render_resume("job-1")
    assert result is None
    assert renderer.db.saved_resume is None


def test_render_adapt_template_unknown_template_returns_none():
    tmp_dir = _local_tmp_dir("renderer_unknown_tpl_adapt")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "ADAPT_TEMPLATE",
            "template_id_final": "NONEXISTENT",
            "c3_decision": "PASS",
            "tailored_resume": "{}",
        },
    )
    result = renderer.render_resume("job-1")
    assert result is None
    assert renderer.db.saved_resume is None


def test_render_adapt_template_invalid_json_falls_back_to_template():
    tmp_dir = _local_tmp_dir("renderer_bad_json_adapt")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "ADAPT_TEMPLATE",
            "template_id_final": "DE",
            "c3_decision": "PASS",
            "tailored_resume": "NOT VALID JSON {{{",
        },
    )
    result = renderer.render_resume("job-1")
    assert result is not None, "Should fall back to USE_TEMPLATE"
    copied = Path(result["pdf_path"]).read_bytes()
    assert copied == b"template-pdf-bytes"
    assert renderer.db.saved_resume is not None
    assert renderer.db.saved_resume.template_version == "template_v1"


def test_render_adapt_template_missing_slot_schema_falls_back_to_template():
    tmp_dir = _local_tmp_dir("renderer_no_schema_adapt")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "ADAPT_TEMPLATE",
            "template_id_final": "DE",
            "c3_decision": "PASS",
            "tailored_resume": json.dumps(
                {"slot_overrides": {"bio": "X"}, "change_summary": "test"}
            ),
        },
    )
    del renderer.registry["templates"]["DE"]["slot_schema"]
    result = renderer.render_resume("job-1")
    assert result is not None, "Should fall back to USE_TEMPLATE"
    copied = Path(result["pdf_path"]).read_bytes()
    assert copied == b"template-pdf-bytes"


def test_render_resume_c3_fail_routes_to_template_copy():
    """ADAPT_TEMPLATE with c3_decision=FAIL should use template copy, not adapt render."""
    tmp_dir = _local_tmp_dir("renderer_c3_fail")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "ADAPT_TEMPLATE",
            "template_id_final": "DE",
            "c3_decision": "FAIL",
            "tailored_resume": json.dumps({"slot_overrides": {"bio": "Ignored"}}),
        },
    )
    result = renderer.render_resume("job-1")
    assert result is not None
    copied = Path(result["pdf_path"]).read_bytes()
    assert copied == b"template-pdf-bytes"
    assert renderer.db.saved_resume is not None
    assert renderer.db.saved_resume.template_version == "template_v1"


def test_render_resume_legacy_null_tier_skips_job():
    """Legacy records with resume_tier=NULL should be skipped (need re-analysis)."""
    tmp_dir = _local_tmp_dir("renderer_legacy_null")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": None,
            "template_id_final": None,
            "tailored_resume": json.dumps(
                {
                    "bio": "Legacy bio",
                    "experiences": [
                        {"company": "Corp", "title": "Eng", "date": "2020", "bullets": ["Did X"]}
                    ],
                    "projects": [],
                    "skills": [{"category": "Languages", "skills_list": "Python, SQL"}],
                }
            ),
        },
    )
    result = renderer.render_resume("job-1")
    assert result is None, "Legacy jobs without resume_tier should be skipped"


def test_render_resume_validator_failure_falls_back_to_template():
    """ResumeValidator.validate() failure should fall back to USE_TEMPLATE."""
    tmp_dir = _local_tmp_dir("renderer_validator_runs")

    class _FailingValidator:
        def validate(self, tailored, job, tier=None):
            return type(
                "R",
                (),
                {"passed": False, "errors": ["Forced fail"], "warnings": [], "fixes": {}},
            )()

    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "FULL_CUSTOMIZE",
            "template_id_final": "DE",
            "tailored_resume": json.dumps(
                {
                    "bio": "Bio",
                    "experiences": [
                        {"company": "C", "title": "T", "date": "D", "bullets": ["B"]}
                    ],
                    "projects": [],
                    "skills": [{"category": "Cat", "skills_list": "Python"}],
                }
            ),
        },
    )
    renderer.validator = _FailingValidator()
    result = renderer.render_resume("job-1")
    assert result is not None, "Validator failure should fall back to USE_TEMPLATE"
    copied = Path(result["pdf_path"]).read_bytes()
    assert copied == b"template-pdf-bytes"


def test_post_render_qa_blocking_prevents_save():
    """A blocking QA issue should prevent PDF generation and DB save."""
    tmp_dir = _local_tmp_dir("renderer_qa_block")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "FULL_CUSTOMIZE",
            "template_id_final": "DE",
            "tailored_resume": json.dumps(
                {
                    "bio": "Bio",
                    "experiences": [
                        {"company": "C", "title": "T", "date": "D", "bullets": ["B"]}
                    ],
                    "projects": [],
                    "skills": [{"category": "Cat", "skills_list": "Python"}],
                }
            ),
        },
    )
    renderer._post_render_qa = lambda html: [("Too long ~5.0 pages", True)]
    result = renderer.render_resume("job-1")
    assert result is None


def test_render_full_customize_role_type_uses_template_id():
    """After Change 5, role_type should come from template_id_final, not _detect_role_type."""
    tmp_dir = _local_tmp_dir("renderer_role_type")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "FULL_CUSTOMIZE",
            "template_id_final": "ML",
            "tailored_resume": json.dumps(
                {
                    "bio": "Bio",
                    "experiences": [
                        {"company": "C", "title": "T", "date": "D", "bullets": ["B"]}
                    ],
                    "projects": [],
                    "skills": [{"category": "Cat", "skills_list": "Python"}],
                }
            ),
        },
    )
    result = renderer.render_resume("job-1")
    assert result is not None
    assert renderer.db.saved_resume.role_type == "ML"


def test_render_full_customize_uses_build_output_paths():
    """FULL_CUSTOMIZE path should use _build_output_paths(), producing ready_to_send output."""
    tmp_dir = _local_tmp_dir("renderer_output_paths")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "FULL_CUSTOMIZE",
            "template_id_final": "DE",
            "tailored_resume": json.dumps(
                {
                    "bio": "Bio",
                    "experiences": [
                        {"company": "C", "title": "T", "date": "D", "bullets": ["B"]}
                    ],
                    "projects": [],
                    "skills": [{"category": "Cat", "skills_list": "Python"}],
                }
            ),
        },
    )
    result = renderer.render_resume("job-1")
    assert result is not None
    assert Path(result["pdf_path"]).exists()
    # _build_output_paths creates submit_dir under ready_dir; saved via DB stub
    saved = renderer.db.saved_resume
    assert saved is not None
    assert str(renderer.ready_dir) in saved.submit_dir


def test_base_template_de_renders_with_standard_context():
    """Zone-based base_template_DE.html should render with bio, skills, and per-entry skills."""
    env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    template = env.get_template("base_template_DE.html")

    html = template.render(
        bio_1='Data Engineer with 6+ years of experience building data platforms across e-commerce and credit risk.',
        bio_2='Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up.',
        bio_3='M.Sc. in Artificial Intelligence. Certified Data Engineer with hands-on Spark and Delta Lake.',
        glp_skills="Python, SQL, AWS, Redshift, Airflow, Docker",
        bq_skills="Python, SQL, MATLAB, Data Quality",
        ele_skills="Python, SQL, Hadoop, Hive, Tableau",
        skills=[
            {"category": "Programming", "skills_list": "Python, SQL, Bash"},
            {"category": "Data Engineering", "skills_list": "PySpark, Spark, Delta Lake"},
        ],
    )
    assert "Fei Huang" in html
    assert "GLP Technology" in html
    assert "Vrije Universiteit Amsterdam" in html
    assert "Data Engineer with 6+ years" in html
    assert "M.Sc. in Artificial Intelligence" in html
    assert "Python, SQL, AWS" in html
    assert "PySpark, Spark, Delta Lake" in html


def test_base_template_ml_renders_with_standard_context():
    """Zone-based base_template_ML.html should render with bio, skills, and per-entry skills."""
    env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    template = env.get_template("base_template_ML.html")

    html = template.render(
        bio_1='Machine Learning Engineer with an M.Sc. in AI (GPA 8.2) and 6 years building prediction.',
        bio_2='Strengths in feature engineering, model evaluation, and end-to-end ML pipelines.',
        bio_3='From raw data through production deployment.',
        glp_skills="Python, SQL, PySpark, Feature Engineering",
        bq_skills="Python, SQL, NumPy, pandas, Statistical Modeling",
        ele_skills="Python, SQL, Clustering, Anomaly Detection",
        skills=[
            {"category": "ML & Modeling", "skills_list": "PyTorch, scikit-learn"},
            {"category": "Programming", "skills_list": "Python, SQL, Bash"},
        ],
    )
    assert "Fei Huang" in html
    assert "GLP Technology" in html
    assert "Uncertainty Quantification" in html
    assert "Machine Learning Engineer" in html
    assert "Python, SQL, PySpark" in html
    assert "PyTorch, scikit-learn" in html


def test_render_batch_mixed_tiers():
    """render_batch should handle a mix of USE_TEMPLATE and FULL_CUSTOMIZE jobs."""
    import sqlite3

    tmp_dir = _local_tmp_dir("renderer_batch_mixed")
    renderer = _make_renderer(tmp_dir, {})

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY, title TEXT, company TEXT, location TEXT, description TEXT)")
    conn.execute(
        "CREATE TABLE job_analysis (id INTEGER PRIMARY KEY, job_id TEXT, ai_score REAL, recommendation TEXT, tailored_resume TEXT, reasoning TEXT, resume_tier TEXT, template_id_final TEXT, c3_decision TEXT)"
    )
    conn.execute(
        "CREATE TABLE resumes (id INTEGER PRIMARY KEY, job_id TEXT, role_type TEXT, template_version TEXT, html_path TEXT, pdf_path TEXT, submit_dir TEXT, UNIQUE(job_id, role_type))"
    )
    conn.execute("CREATE TABLE applications (id INTEGER PRIMARY KEY, job_id TEXT)")

    conn.execute("INSERT INTO jobs VALUES ('j1', 'Data Engineer', 'Co1', 'AMS', 'desc')")
    conn.execute("INSERT INTO jobs VALUES ('j2', 'ML Engineer', 'Co2', 'AMS', 'desc')")
    conn.execute(
        "INSERT INTO job_analysis (job_id, ai_score, recommendation, tailored_resume, resume_tier, template_id_final) VALUES ('j1', 7.0, 'APPLY', '{}', 'USE_TEMPLATE', 'DE')"
    )
    conn.execute(
        """INSERT INTO job_analysis (job_id, ai_score, recommendation, tailored_resume, resume_tier, template_id_final) VALUES ('j2', 7.0, 'APPLY', '{"bio":"B","experiences":[{"company":"C","title":"T","date":"D","bullets":["X"]}],"projects":[],"skills":[{"category":"Cat","skills_list":"Python"}]}', 'FULL_CUSTOMIZE', 'ML')"""
    )
    conn.commit()

    count = renderer.render_batch(min_ai_score=5.0)
    assert callable(renderer.render_batch)


def test_schema_to_context_outputs_per_entry_skills():
    """_schema_to_context should output per-entry skills variables for zone-based templates."""
    tmp_dir = _local_tmp_dir("renderer_zone_skills")
    renderer = _make_renderer(
        tmp_dir,
        {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"},
    )
    schema = {
        "bio": {
            "slot_id": "bio",
            "bio_1": {"default": "Default bio line one."},
            "bio_2": {"default": "Default bio line two."},
            "bio_3": {"default": "Default bio line three."},
        },
        "sections": [
            {
                "section_id": "experience",
                "entries": [
                    {
                        "entry_id": "glp",
                        "company": "GLP Technology (Fintech)",
                        "title": "Senior Data Engineer",
                        "date": "JULY 2017 - AUGUST 2019",
                        "technical_skills": "Python, SQL, AWS",
                        "bullets": [{"slot_id": "glp_1", "default": "Built X"}],
                    },
                    {
                        "entry_id": "bq",
                        "company": "BQ Investment (Hedge Fund)",
                        "title": "Quant Developer",
                        "date": "JULY 2015 - JUNE 2017",
                        "technical_skills": "Python, SQL, MATLAB",
                        "bullets": [{"slot_id": "bq_1", "default": "Built Y"}],
                    },
                ],
            },
            {
                "section_id": "skills",
                "categories": [
                    {"cat_id": "programming", "default": "Python, SQL"},
                ],
            },
        ],
    }
    tailored = {
        "slot_overrides": {"bio_1": "Custom bio"},
        "skills_override": {},
        "entry_visibility": {},
        "change_summary": "test",
    }
    analysis = {"seniority": "mid"}

    context = renderer._schema_to_context(schema, tailored, analysis)

    assert context["bio_1"] == "Custom bio"
    assert context["glp_skills"] == "Python, SQL, AWS"
    assert context["bq_skills"] == "Python, SQL, MATLAB"
    assert len(context["skills"]) == 1
    assert context["skills"][0]["category"] == "Programming"


def test_validate_adapt_zones_bio_too_long():
    """Bio exceeding 280 chars should produce a warning."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({"bio": "A" * 300})
    assert any("bio" in w.lower() for w in result.warnings)


def test_validate_adapt_zones_skills_line_too_long():
    """Skills line exceeding 65 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator
    validator = ResumeValidator()
    result = validator.validate_adapt_zones({"bio_1": "A", "bio_2": "B", "bio_3": "C", "glp_skills": "A" * 70})
    assert not result.passed
    assert any("glp_skills" in e for e in result.errors)


def test_validate_adapt_zones_bio_line_too_long_blocks():
    """Bio line exceeding 105 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator
    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "A" * 110,
        "bio_2": "Short line two.",
        "bio_3": "Short line three.",
    })
    assert not result.passed
    assert any("bio_1" in e for e in result.errors)


def test_validate_adapt_zones_bio_lines_within_limit_passes():
    """Bio lines within 105 chars should pass."""
    from src.resume_validator import ResumeValidator
    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Data Engineer with 6+ years of experience building data platforms across e-commerce and credit risk.",
        "bio_2": "Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up.",
        "bio_3": "M.Sc. in Artificial Intelligence. Certified Data Engineer with hands-on Spark and Delta Lake.",
    })
    assert result.passed
    assert len(result.errors) == 0


def test_validate_adapt_zones_skills_line_blocks():
    """Skills line exceeding 65 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator
    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Short.", "bio_2": "Short.", "bio_3": "Short.",
        "glp_skills": "A" * 70,
    })
    assert not result.passed
    assert any("glp_skills" in e for e in result.errors)


def test_validate_adapt_zones_skills_categories_blocks():
    """More than 5 skill categories should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator
    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Short.", "bio_2": "Short.", "bio_3": "Short.",
        "skills": [{"category": f"Cat{i}", "skills_list": "Python"} for i in range(6)],
    })
    assert not result.passed
    assert any("categor" in e.lower() for e in result.errors)


def test_validate_adapt_zones_skills_list_too_long_blocks():
    """A single skills_list exceeding 80 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator
    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Short.", "bio_2": "Short.", "bio_3": "Short.",
        "skills": [{"category": "Programming", "skills_list": "A" * 85}],
    })
    assert not result.passed
    assert any("skills_list" in e.lower() or "programming" in e.lower() for e in result.errors)


def test_schema_to_context_outputs_per_line_bio():
    """_schema_to_context should output bio_1, bio_2, bio_3 from per-line schema."""
    tmp_dir = _local_tmp_dir("renderer_perline_bio")
    renderer = _make_renderer(tmp_dir, {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"})
    schema = {
        "bio": {
            "slot_id": "bio",
            "bio_1": {"default": "Line one default.", "senior": "Line one senior."},
            "bio_2": {"default": "Line two default.", "senior": "Line two senior."},
            "bio_3": {"default": "Line three default.", "senior": "Line three senior."},
        },
        "sections": [
            {"section_id": "experience", "entries": [
                {"entry_id": "glp", "company": "GLP", "title": "Lead", "date": "2017-2019",
                 "technical_skills": "Python, SQL", "bullets": [{"slot_id": "glp_1", "default": "Built X"}]},
            ]},
            {"section_id": "skills", "categories": [{"cat_id": "programming", "default": "Python, SQL"}]},
        ],
    }
    tailored = {"slot_overrides": {}, "skills_override": {}, "entry_visibility": {}, "change_summary": "test"}
    analysis = {"seniority": "mid"}
    context = renderer._schema_to_context(schema, tailored, analysis)
    assert context["bio_1"] == "Line one default."
    assert context["bio_2"] == "Line two default."
    assert context["bio_3"] == "Line three default."
    assert "bio" not in context


def test_schema_to_context_senior_bio_lines():
    """Senior seniority should pick senior bio lines."""
    tmp_dir = _local_tmp_dir("renderer_senior_bio")
    renderer = _make_renderer(tmp_dir, {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"})
    schema = {
        "bio": {"slot_id": "bio",
                "bio_1": {"default": "Mid one.", "senior": "Senior one."},
                "bio_2": {"default": "Mid two.", "senior": "Senior two."},
                "bio_3": {"default": "Mid three.", "senior": "Senior three."}},
        "sections": [],
    }
    tailored = {"slot_overrides": {}, "skills_override": {}, "entry_visibility": {}, "change_summary": "test"}
    analysis = {"seniority": "senior"}
    context = renderer._schema_to_context(schema, tailored, analysis)
    assert context["bio_1"] == "Senior one."
    assert context["bio_2"] == "Senior two."
    assert context["bio_3"] == "Senior three."


def test_schema_to_context_slot_override_bio_lines():
    """AI-generated bio line overrides should take precedence over defaults."""
    tmp_dir = _local_tmp_dir("renderer_override_bio")
    renderer = _make_renderer(tmp_dir, {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"})
    schema = {
        "bio": {"slot_id": "bio",
                "bio_1": {"default": "Default one.", "senior": "Senior one."},
                "bio_2": {"default": "Default two.", "senior": "Senior two."},
                "bio_3": {"default": "Default three.", "senior": "Senior three."}},
        "sections": [],
    }
    tailored = {
        "slot_overrides": {"bio_1": "Custom line one.", "bio_2": "Custom line two.", "bio_3": "Custom line three."},
        "skills_override": {}, "entry_visibility": {}, "change_summary": "Adapted bio",
    }
    analysis = {"seniority": "mid"}
    context = renderer._schema_to_context(schema, tailored, analysis)
    assert context["bio_1"] == "Custom line one."
    assert context["bio_2"] == "Custom line two."
    assert context["bio_3"] == "Custom line three."
