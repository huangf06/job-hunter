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

    def get_analysis(self, job_id):
        return self._analysis

    def get_job(self, job_id):
        return self._job

    def save_resume(self, resume):
        self.saved_resume = resume


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
