from io import StringIO
from contextlib import redirect_stdout

from scripts.job_pipeline import JobPipeline


class _DBStub:
    def execute(self, sql, params=()):
        normalized = " ".join(sql.split())
        assert params == (4.0,)
        if "resume_tier = 'USE_TEMPLATE'" in normalized and "COUNT(*) as c" in normalized:
            return [{"c": 5}]
        if "resume_tier = 'ADAPT_TEMPLATE'" in normalized and "c3_decision = 'PASS'" in normalized:
            return [{"c": 3}]
        if "resume_tier = 'ADAPT_TEMPLATE'" in normalized and "c3_decision = 'FAIL'" in normalized:
            return [{"c": 2}]
        if "resume_tier = 'FULL_CUSTOMIZE'" in normalized:
            return [{"c": 1}]
        if "resume_tier IS NULL" in normalized and "COUNT(*) as c" in normalized:
            return [{"c": 4}]
        if "template_id_initial = template_id_final" in normalized:
            return [{"c": 8}]
        if "routing_override_reason IS NOT NULL" in normalized and "COUNT(*) as c" in normalized:
            return [{"c": 2}]
        if "escalation_reason IS NOT NULL" in normalized:
            return [{"c": 1}]
        if "GROUP BY template_id_final" in normalized:
            return [{"template_id_final": "DE", "c": 6}, {"template_id_final": "ML", "c": 5}]
        if "AVG(c3_confidence)" in normalized and "PASS" in normalized:
            return [{"avg_conf": 0.82}]
        if "AVG(c3_confidence)" in normalized and "FAIL" in normalized:
            return [{"avg_conf": 0.71}]
        return [{"c": 0}]


def test_show_template_stats_outputs_expected_sections():
    pipeline = JobPipeline.__new__(JobPipeline)
    pipeline.db = _DBStub()
    pipeline.ai_config = {"thresholds": {"ai_score_generate_resume": 4.0}}

    stdout = StringIO()
    with redirect_stdout(stdout):
        pipeline.show_template_stats()

    text = stdout.getvalue()
    assert "Resume Tier Distribution" in text
    assert "USE_TEMPLATE:     5" in text
    assert "ADAPT_TEMPLATE:   5" in text
    assert "FULL_CUSTOMIZE:   1" in text
    assert "Legacy:           4" in text
    assert "Code -> C1 agreement:  8" in text
    assert "C1 overrides:          2" in text
    assert "Safeguard escalations: 1" in text
    assert "DE:      6" in text
    assert "ML:      5" in text
    assert "Avg confidence (PASS): 0.82" in text
    assert "Avg confidence (FAIL): 0.71" in text
