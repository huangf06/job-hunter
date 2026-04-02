import json

from src.ai_analyzer import AIAnalyzer
from src.template_registry import load_registry


def test_build_c3_input_includes_diff_and_density():
    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    registry = load_registry()
    schema = registry["templates"]["DE"]["slot_schema"]
    c2_output = {
        "slot_overrides": {"bio_1": "New bio line one.", "bio_2": "New bio line two.", "bio_3": "New bio line three.", "glp_1": "Updated bullet"},
        "skills_override": {"programming": "Python, SQL, Scala"},
        "entry_visibility": {"henan": False},
        "change_summary": "Changed several items",
    }
    c1_routing = {"gaps": ["backend emphasis"]}

    diff = analyzer.build_c3_input(schema, c2_output, c1_routing, "Strong data platform fit")

    assert "## Job Summary" in diff
    assert "backend emphasis" in diff
    assert "BEFORE:" in diff
    assert "AFTER:" in diff
    assert "**Hidden entries:** henan" in diff
    assert "Change density:" in diff


def test_run_c3_gate_parses_model_response():
    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    analyzer.registry = load_registry()
    analyzer.config = {
        "prompts": {
            "c3_gate": "{structured_diff}",
        }
    }
    analyzer._call_claude = lambda prompt: json.dumps(
        {"decision": "PASS", "confidence": 0.82, "reason": "Worth the adaptation"}
    )

    class Result:
        template_id_final = "DE"
        tailored_resume = json.dumps(
            {
                "slot_overrides": {"bio_1": "New bio line one."},
                "skills_override": {},
                "entry_visibility": {},
                "change_summary": "bio only",
            }
        )
        reasoning = json.dumps({"application_brief": {"key_angle": "Data engineering fit"}})

    gate = analyzer.run_c3_gate(Result(), {"gaps": ["fit gap"]}, {"title": "Data Engineer"})

    assert gate["decision"] == "PASS"
    assert gate["confidence"] == 0.82
    assert gate["reason"] == "Worth the adaptation"


def test_run_c3_gate_prompt_preserves_structured_diff_braces():
    analyzer = AIAnalyzer.__new__(AIAnalyzer)
    analyzer.registry = load_registry()
    analyzer.config = {"prompts": {"c3_gate": "DIFF:\n{structured_diff}"}}
    captured = {}

    def _fake_call(prompt):
        captured["prompt"] = prompt
        return json.dumps({"decision": "PASS", "confidence": 0.75, "reason": "ok"})

    analyzer._call_claude = _fake_call

    class Result:
        template_id_final = "DE"
        tailored_resume = json.dumps(
            {
                "slot_overrides": {"bio_1": "Processed {batch_size} records"},
                "skills_override": {},
                "entry_visibility": {},
                "change_summary": "bio only",
            }
        )
        reasoning = json.dumps({"application_brief": {"key_angle": "Data engineering fit"}})

    analyzer.run_c3_gate(Result(), {"gaps": ["fit gap"]}, {"title": "Data Engineer"})

    assert "Processed {batch_size} records" in captured["prompt"]
    assert "Processed {{batch_size}} records" not in captured["prompt"]
