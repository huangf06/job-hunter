"""Tests for checklist_server (Block E+F audit)."""

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from src.checklist_server import generate_checklist


def _local_tmp_dir(name: str) -> Path:
    path = Path("_tmp_test_artifacts") / f"{name}_{uuid.uuid4().hex[:8]}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_xss_in_job_title_is_escaped():
    """EF-2: Checklist HTML must not expose a raw closing script tag in JS state."""
    tmp_path = _local_tmp_dir("checklist_xss")
    jobs = [
        {
            "id": "xss-test-1",
            "title": '</script><img onerror="alert(1)">',
            "company": "Evil Corp",
            "score": 7.0,
            "submit_dir": str(tmp_path / "xss-test-1"),
            "url": "https://example.com",
        }
    ]
    (tmp_path / "xss-test-1").mkdir()

    generate_checklist(jobs, tmp_path)

    html = (tmp_path / "apply_checklist.html").read_text(encoding="utf-8")

    script_sections = html.split("<script>")
    assert len(script_sections) == 2, "Expected exactly one <script> block"
    script_block = script_sections[1].split("</script>")[0]
    assert "let state = JSON.parse(" in script_block
    assert "</script>" not in script_block

    state_json = (tmp_path / "state.json").read_text(encoding="utf-8")
    state = json.loads(state_json)
    assert state["jobs"]["xss-test-1"]["title"] == '</script><img onerror="alert(1)">'


def test_finalize_rejects_malformed_state_json():
    """EF-7: cmd_finalize should raise clear error on malformed state.json."""
    from scripts.job_pipeline import JobPipeline

    tmp_path = _local_tmp_dir("finalize_bad_state")

    with patch.object(JobPipeline, "__init__", lambda self: None):
        pipeline = JobPipeline()
        pipeline.db = MagicMock()

        with patch("scripts.job_pipeline.PROJECT_ROOT", str(tmp_path)):
            ready_dir = tmp_path / "ready_to_send"
            ready_dir.mkdir()
            (ready_dir / "state.json").write_text('{"bad": "data"}', encoding="utf-8")

            with pytest.raises(SystemExit):
                pipeline.cmd_finalize()


def test_finalize_rejects_jobs_missing_required_keys():
    """EF-7: Jobs in state.json must have applied, submit_dir, company, title."""
    from scripts.job_pipeline import JobPipeline

    tmp_path = _local_tmp_dir("finalize_missing_keys")
    state = {
        "generated_at": "2026-03-30T00:00:00",
        "jobs": {
            "job-1": {"applied": True}
        },
    }

    with patch.object(JobPipeline, "__init__", lambda self: None):
        pipeline = JobPipeline()
        pipeline.db = MagicMock()

        with patch("scripts.job_pipeline.PROJECT_ROOT", str(tmp_path)):
            ready_dir = tmp_path / "ready_to_send"
            ready_dir.mkdir()
            (ready_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")

            with pytest.raises(SystemExit):
                pipeline.cmd_finalize()
