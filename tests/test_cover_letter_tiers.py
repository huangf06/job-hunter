import json

from src.cover_letter_generator import get_resume_context_for_cl
from src.template_registry import load_registry


def test_get_resume_context_for_cl_use_template():
    registry = load_registry()
    row = {
        "resume_tier": "USE_TEMPLATE",
        "template_id_final": "DE",
        "tailored_resume": "{}",
        "reasoning": json.dumps({"application_brief": {"key_angle": "Data platform fit"}}),
    }

    context = get_resume_context_for_cl(row, registry)

    assert "Template Positioning: Data Engineer" in context
    assert "Key Strengths: Spark/Delta Lake, AWS data stack, financial domain, Python" in context
    assert "Application Brief: Data platform fit" in context


def test_get_resume_context_for_cl_adapt_template_pass_falls_back_without_schema():
    """After 2026-04-17 revert: slot_schema is gone from registry, so legacy
    ADAPT_TEMPLATE rows with c3_decision=PASS no longer hydrate slot_overrides.
    They fall through to the lightweight template context instead (same as
    USE_TEMPLATE) — the row should really be re-analyzed as FULL_CUSTOMIZE."""
    registry = load_registry()
    row = {
        "resume_tier": "ADAPT_TEMPLATE",
        "template_id_final": "ML",
        "c3_decision": "PASS",
        "tailored_resume": json.dumps(
            {
                "slot_overrides": {"bio": "Custom ML bio"},
                "change_summary": "Adapted for ML role",
            }
        ),
        "reasoning": json.dumps({"application_brief": {"key_angle": "Applied ML depth"}}),
    }

    context = get_resume_context_for_cl(row, registry)

    # Slot overrides are NOT hydrated — schema is gone
    assert "Custom ML bio" not in context
    # Falls through to template positioning / strengths
    assert "Template Positioning: ML Engineer / Data Scientist" in context
    assert "Application Brief: Applied ML depth" in context


def test_get_resume_context_for_cl_adapt_template_fail_falls_back_to_template():
    registry = load_registry()
    row = {
        "resume_tier": "ADAPT_TEMPLATE",
        "template_id_final": "ML",
        "c3_decision": "FAIL",
        "tailored_resume": json.dumps({"slot_overrides": {"bio": "Ignored"}}),
        "reasoning": json.dumps({"application_brief": {"key_angle": "Fallback brief"}}),
    }

    context = get_resume_context_for_cl(row, registry)

    assert "Template Positioning: ML Engineer / Data Scientist" in context
    assert "Ignored" not in context
    assert "Application Brief: Fallback brief" in context


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
