"""Tests for AIAnalyzer model calling — _call_claude_code (subprocess) and _call_model (routing).

All tests mock subprocess.run / OpenAI client so no real calls are made.
"""

import json
import subprocess
from unittest.mock import patch, MagicMock

import pytest

def _make_analyzer(provider='claude_code'):
    """Create a bare AIAnalyzer without __init__ side effects."""
    from src.ai_analyzer import AIAnalyzer
    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    analyzer.active_provider = provider
    analyzer.config = {'models': {'deepseek': {
        'api_base': 'https://api.deepseek.com',
        'model': 'deepseek-v4-pro',
        'max_tokens': 8192,
        'temperature': 0.1,
        'timeout': 180,
    }}}
    return analyzer


class TestCallClaudeCode:
    """Unit tests for _call_claude_code subprocess wrapper."""

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_successful_call_returns_json(self, mock_run, mock_which):
        expected = json.dumps({"scoring": {"overall_score": 7.5}})
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=f"  {expected}  \n",
            stderr="",
        )

        analyzer = _make_analyzer()
        result = analyzer._call_claude_code("test prompt")

        assert result == expected
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        assert call_kwargs.kwargs["input"] == "test prompt"
        assert call_kwargs.kwargs["timeout"] == 300

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="claude", timeout=300))
    def test_timeout_returns_none(self, mock_run, mock_which):
        analyzer = _make_analyzer()
        result = analyzer._call_claude_code("test prompt")
        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run", side_effect=FileNotFoundError("not found"))
    def test_file_not_found_returns_none(self, mock_run, mock_which):
        analyzer = _make_analyzer()
        result = analyzer._call_claude_code("test prompt")
        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run", side_effect=OSError("permission denied"))
    def test_other_exception_propagates(self, mock_run, mock_which):
        analyzer = _make_analyzer()
        with pytest.raises(OSError):
            analyzer._call_claude_code("test prompt")

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_nonzero_returncode_returns_none(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: unknown failure",
        )

        analyzer = _make_analyzer()
        result = analyzer._call_claude_code("test prompt")
        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_quota_exhausted_raises_on_rate_limit(self, mock_run, mock_which):
        from src.ai_analyzer import QuotaExhaustedError

        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: rate limited",
        )

        analyzer = _make_analyzer()
        with pytest.raises(QuotaExhaustedError):
            analyzer._call_claude_code("test prompt")

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_invalid_json_response_returned_as_string(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="This is not valid JSON",
            stderr="",
        )

        analyzer = _make_analyzer()
        result = analyzer._call_claude_code("test prompt")
        assert result == "This is not valid JSON"

    @patch("shutil.which", return_value=None)
    def test_claude_not_in_path_returns_none(self, mock_which):
        analyzer = _make_analyzer()
        result = analyzer._call_claude_code("test prompt")
        assert result is None

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_env_cleaning_strips_anthropic_vars(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='{"ok": true}',
            stderr="",
        )

        analyzer = _make_analyzer()
        with patch.dict("os.environ", {"ANTHROPIC_BASE_URL": "http://x", "ANTHROPIC_API_KEY": "sk-test"}):
            analyzer._call_claude_code("test prompt")

        call_kwargs = mock_run.call_args.kwargs
        env = call_kwargs["env"]
        assert "ANTHROPIC_BASE_URL" not in env
        assert "ANTHROPIC_API_KEY" not in env


class TestCallModel:
    """Test _call_model routing to the correct provider."""

    @patch("shutil.which", return_value="/usr/bin/claude")
    @patch("subprocess.run")
    def test_routes_to_claude_code(self, mock_run, mock_which):
        mock_run.return_value = MagicMock(returncode=0, stdout='{"ok": true}', stderr="")
        analyzer = _make_analyzer(provider='claude_code')
        result = analyzer._call_model("test")
        assert result == '{"ok": true}'
        mock_run.assert_called_once()

    @patch.dict("os.environ", {"DEEPSEEK_API_KEY": "sk-test"})
    @patch("openai.OpenAI")
    def test_routes_to_deepseek(self, mock_openai_cls):
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='  {"ok": true}  '))]
        mock_client.chat.completions.create.return_value = mock_response

        analyzer = _make_analyzer(provider='deepseek')
        result = analyzer._call_model("test")
        assert result == '{"ok": true}'
        mock_client.chat.completions.create.assert_called_once()

    def test_deepseek_no_api_key_returns_none(self):
        analyzer = _make_analyzer(provider='deepseek')
        with patch.dict("os.environ", {}, clear=True):
            result = analyzer._call_deepseek("test")
        assert result is None


class TestEvaluateJobNoneHandling:
    """Test that evaluate_job returns None when _call_model fails."""

    def test_evaluate_job_returns_none_on_api_failure(self):
        from src.ai_analyzer import AIAnalyzer
        from src.template_registry import load_registry

        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer.active_provider = 'claude_code'
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
        analyzer._call_model = lambda prompt: None

        job = {
            "id": "test-fail",
            "title": "Data Engineer",
            "company": "TestCorp",
            "description": "Python SQL Spark",
            "location": "Amsterdam",
        }
        result = analyzer.evaluate_job(job)
        assert result is None
