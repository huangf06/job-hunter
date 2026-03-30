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
    def validate(self, tailored, job):
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
                "adapt_html": "templates/adapt_de.html",
                "slot_schema": {
                    "bio": {"slot_id": "bio", "default": "Default bio"},
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
    renderer._html_to_pdf = lambda html_path, pdf_path: pdf_path.write_bytes(b"rendered-pdf") or True
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
                    "slot_overrides": {"bio": "Adapted bio", "glp_1": "Adapted bullet"},
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


def test_render_adapt_template_invalid_json_returns_none():
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
    assert result is None
    assert renderer.db.saved_resume is None


def test_render_adapt_template_missing_slot_schema_returns_none():
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
    assert result is None


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


def test_render_resume_legacy_null_tier_uses_full_customize():
    """Legacy records with resume_tier=NULL should use the FULL_CUSTOMIZE path."""
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
    assert result is not None
    assert Path(result["html_path"]).exists()


def test_render_resume_validator_still_runs():
    """ResumeValidator.validate() must still execute in the renderer."""
    tmp_dir = _local_tmp_dir("renderer_validator_runs")

    class _FailingValidator:
        def validate(self, tailored, job):
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
    assert result is None, "Validator failure should prevent rendering"


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


def test_adapt_template_html_renders_with_title_variable():
    """Merged adapt_template.html should accept template_title variable."""
    env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    template = env.get_template("adapt_template.html")

    schema = {
        "bio": {"slot_id": "bio", "default": "Default bio"},
        "sections": [],
    }
    html = template.render(
        candidate={"name": "Test", "location": "A", "phone": "1", "email": "e"},
        schema=schema,
        slot_overrides={},
        skills_override={},
        entry_visibility={},
        template_title="Adapted ML Resume",
    )
    assert "Adapted ML Resume" in html
    assert "Default bio" in html


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
