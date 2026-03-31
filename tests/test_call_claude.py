"""Tests for AIAnalyzer._call_claude — subprocess interaction with Claude CLI.

All tests mock subprocess.run so no real CLI calls are made.
"""

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest


def _make_analyzer():
    """Create a bare AIAnalyzer without __init__ side effects."""
    from src.ai_analyzer import AIAnalyzer
    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    return analyzer


class TestCallClaude:
    """Unit tests for _call_claude subprocess wrapper."""

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_successful_call_returns_json(self, mock_run, mock_which):
        """Valid JSON response from Claude CLI is returned as stripped string."""
        expected = json.dumps({"scoring": {"overall_score": 7.5}})
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=f"  {expected}  \n",
            stderr="",
        )

        analyzer = _make_analyzer()
        result = analyzer._call_claude("test prompt")

        assert result == expected
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs["input"] == "test prompt"
        assert call_kwargs.kwargs["timeout"] == 300

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=300))
    def test_timeout_returns_none(self, mock_run, mock_which):
        """TimeoutExpired from subprocess.run returns None."""
        analyzer = _make_analyzer()
        result = analyzer._call_claude("test prompt")

        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run", side_effect=FileNotFoundError("not found"))
    def test_file_not_found_returns_none(self, mock_run, mock_which):
        """FileNotFoundError returns None."""
        analyzer = _make_analyzer()
        result = analyzer._call_claude("test prompt")

        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run", side_effect=OSError("permission denied"))
    def test_other_exception_returns_none(self, mock_run, mock_which):
        """Other OS-level exceptions are not caught — verify behavior.

        _call_claude only catches TimeoutExpired and FileNotFoundError,
        so other exceptions propagate. This documents the current behavior.
        """
        analyzer = _make_analyzer()
        with pytest.raises(OSError):
            analyzer._call_claude("test prompt")

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_nonzero_returncode_returns_none(self, mock_run, mock_which):
        """Non-zero return code from CLI returns None."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: rate limited",
        )

        analyzer = _make_analyzer()
        result = analyzer._call_claude("test prompt")

        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_invalid_json_response_returned_as_string(self, mock_run, mock_which):
        """_call_claude returns raw text — it does NOT parse JSON itself.

        JSON parsing is the caller's responsibility (_parse_response).
        Invalid JSON is still returned as a string.
        """
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="This is not valid JSON",
            stderr="",
        )

        analyzer = _make_analyzer()
        result = analyzer._call_claude("test prompt")

        assert result == "This is not valid JSON"

    @patch("shutil.which", return_value=None)
    def test_claude_not_in_path_returns_none(self, mock_which):
        """Claude CLI not found in PATH returns None."""
        analyzer = _make_analyzer()
        result = analyzer._call_claude("test prompt")

        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_env_cleaning_strips_anthropic_vars(self, mock_run, mock_which):
        """ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY are stripped from env."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok": true}',
            stderr="",
        )

        analyzer = _make_analyzer()
        with patch.dict("os.environ", {"ANTHROPIC_BASE_URL": "http://x", "ANTHROPIC_API_KEY": "sk-test"}):
            analyzer._call_claude("test prompt")

        call_kwargs = mock_run.call_args.kwargs
        env = call_kwargs["env"]
        assert "ANTHROPIC_BASE_URL" not in env
        assert "ANTHROPIC_API_KEY" not in env


class TestEvaluateJobNoneHandling:
    """Test that evaluate_job returns None when _call_claude fails (P1-1)."""

    def test_evaluate_job_returns_none_on_api_failure(self):
        """When _call_claude returns None, evaluate_job returns None without saving."""
        from src.ai_analyzer import AIAnalyzer
        from src.template_registry import load_registry

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
        analyzer.registry = load_registry()
        analyzer._call_claude = lambda prompt: None

        job = {
            "id": "test-fail",
            "title": "Data Engineer",
            "company": "TestCorp",
            "description": "Python SQL Spark",
            "location": "Amsterdam",
        }
        result = analyzer.evaluate_job(job)
        assert result is None
