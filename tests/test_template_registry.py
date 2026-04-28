from pathlib import Path

import pytest

from src.template_registry import (
    RoutingDecision,
    load_registry,
    resolve_routing,
    select_template,
)


def test_load_registry_has_required_templates_and_role_metadata():
    registry = load_registry()

    assert set(registry["templates"]) >= {"DE", "ML", "Backend"}

    for template_id in ("DE", "ML", "Backend"):
        template = registry["templates"][template_id]
        assert "target_roles" in template
        assert isinstance(template["target_roles"], list)
        assert template["target_roles"], f"{template_id} target_roles must be non-empty"
        assert "bio_positioning" in template
        assert isinstance(template["bio_positioning"], str)
        assert "key_strengths" in template
        assert isinstance(template["key_strengths"], list)
        assert "slot_schema" not in template, f"{template_id} still has retired slot_schema"


def test_load_registry_uses_repo_config_file():
    registry = load_registry()
    assert Path(registry["_meta"]["path"]).name == "template_registry.yaml"


@pytest.mark.parametrize(
    ("title", "expected_template", "expected_confidence", "expected_ambiguous"),
    [
        ("Senior Data Engineer", "DE", 0.9, False),
        ("ML Platform Engineer", "ML", 0.5, True),
        ("MLOps Engineer", "ML", 0.9, False),
        ("Business Intelligence Manager", "DE", 0.3, False),
        ("Software Engineer", "DE", 0.3, False),
        ("Backend Engineer", "DE", 0.3, False),
        ("Python Developer", "DE", 0.3, False),
        ("Infrastructure Engineer", "DE", 0.3, False),
    ],
)
def test_select_template_behaviors(title, expected_template, expected_confidence, expected_ambiguous):
    registry = load_registry()
    decision = select_template(title, registry)

    assert decision.template_id == expected_template
    assert decision.confidence == expected_confidence
    assert decision.ambiguous is expected_ambiguous


def test_select_template_skips_disabled_templates():
    registry = load_registry()
    registry["templates"]["Backend"]["enabled"] = False
    decision = select_template("Backend Platform Engineer", registry)

    assert decision.template_id == "DE"
    assert decision.confidence == 0.3


def test_backend_template_disabled_falls_through():
    registry = load_registry()
    decision = select_template("Backend Platform Engineer", registry)

    assert decision.template_id == "DE"
    assert decision.confidence == 0.3


def test_resolve_routing_forces_full_customize_even_when_ai_emits_adapt_template():
    code_decision = RoutingDecision("DE", 0.9, ["data engineer"], False)
    c1_routing = {
        "tier": "ADAPT_TEMPLATE",
        "template_id": "ML",
        "override": True,
        "override_reason": "JD is model-heavy",
        "gaps": ["model deployment depth"],
        "adapt_instructions": "Shift to ML positioning",
    }

    resolved = resolve_routing(code_decision, c1_routing)

    assert resolved["resume_tier"] == "FULL_CUSTOMIZE"
    assert resolved["template_id_initial"] == "DE"
    assert resolved["template_id_final"] == "ML"
    assert resolved["routing_confidence"] == 0.9
    assert resolved["routing_override_reason"] == "JD is model-heavy"
    assert "routing_payload" in resolved


def test_resolve_routing_forces_full_customize_when_ai_emits_use_template():
    code_decision = RoutingDecision("DE", 0.9, ["data engineer"], False)
    c1_routing = {
        "tier": "USE_TEMPLATE",
        "template_id": "ML",
        "override": True,
        "override_reason": None,
        "gaps": [],
        "adapt_instructions": None,
    }

    resolved = resolve_routing(code_decision, c1_routing)

    assert resolved["resume_tier"] == "FULL_CUSTOMIZE"
    assert resolved["template_id_final"] == "DE"
    assert resolved["routing_override_reason"] is None


def test_resolve_routing_forces_full_customize_when_tier_missing():
    code_decision = RoutingDecision("DE", 0.9, ["data engineer"], False)
    c1_routing = {
        "template_id": "DE",
        "override": False,
        "override_reason": None,
        "gaps": [],
        "adapt_instructions": None,
    }

    resolved = resolve_routing(code_decision, c1_routing)

    assert resolved["resume_tier"] == "FULL_CUSTOMIZE"
