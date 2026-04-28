import json

from src.cover_letter_generator import get_resume_context_for_cl
from src.template_registry import load_registry


def test_get_resume_context_for_cl_full_customize_returns_raw_resume():
    registry = load_registry()
    row = {
        "resume_tier": "FULL_CUSTOMIZE",
        "template_id_final": None,
        "tailored_resume": json.dumps({"bio": "Full custom bio", "experiences": [{"company": "GLP"}]}),
        "reasoning": json.dumps({"application_brief": {"key_angle": "Custom narrative"}}),
    }

    context = get_resume_context_for_cl(row, registry)

    assert '"bio": "Full custom bio"' in context
    assert "Application Brief: Custom narrative" in context


def test_get_resume_context_for_cl_legacy_keeps_existing_behavior():
    registry = load_registry()
    row = {
        "resume_tier": None,
        "tailored_resume": json.dumps({"bio": "Legacy bio"}),
        "reasoning": json.dumps({"application_brief": {"key_angle": "Legacy brief"}}),
    }

    context = get_resume_context_for_cl(row, registry)

    assert context.startswith('{"bio": "Legacy bio"}')
