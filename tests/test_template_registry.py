from pathlib import Path

import pytest

from src.template_registry import (
    TIER1_CONFIDENCE_THRESHOLD,
    RoutingDecision,
    apply_tier1_safeguard,
    load_registry,
    resolve_routing,
    select_template,
    validate_tier2_output,
)


def test_load_registry_has_required_templates_and_unique_slot_ids():
    registry = load_registry()

    assert set(registry["templates"]) >= {"DE", "ML", "Backend"}

    for template_id in ("DE", "ML", "Backend"):
        template = registry["templates"][template_id]
        assert "slot_schema" in template
        assert "bio" in template["slot_schema"]
        assert "sections" in template["slot_schema"]

        slot_ids = {"bio"}
        for section in template["slot_schema"]["sections"]:
            for entry in section.get("entries", []):
                assert "entry_id" in entry
                for bullet in entry.get("bullets", []):
                    assert "slot_id" in bullet
                    assert "default" in bullet
                    assert bullet["slot_id"] not in slot_ids
                    slot_ids.add(bullet["slot_id"])
            for category in section.get("categories", []):
                assert "cat_id" in category
                assert "default" in category


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
    """When a template is disabled, its target_roles are ignored."""
    registry = load_registry()
    # Temporarily disable Backend to verify skip behavior
    registry["templates"]["Backend"]["enabled"] = False
    decision = select_template("Backend Platform Engineer", registry)

    # With Backend disabled, no template matches → falls through to DE default
    assert decision.template_id == "DE"
    assert decision.confidence == 0.3


def test_backend_template_disabled_falls_through():
    """Backend template is disabled, so backend titles fall through to DE default."""
    registry = load_registry()
    decision = select_template("Backend Platform Engineer", registry)

    assert decision.template_id == "DE"
    assert decision.confidence == 0.3


def test_resolve_routing_prefers_c1_override_with_reason():
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

    assert resolved["resume_tier"] == "ADAPT_TEMPLATE"
    assert resolved["template_id_initial"] == "DE"
    assert resolved["template_id_final"] == "ML"
    assert resolved["routing_confidence"] == 0.9
    assert resolved["routing_override_reason"] == "JD is model-heavy"
    assert "routing_payload" in resolved


def test_resolve_routing_keeps_code_template_without_valid_override_reason():
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

    assert resolved["template_id_final"] == "DE"
    assert resolved["routing_override_reason"] is None


def test_apply_tier1_safeguard_keeps_high_confidence_template():
    routing = {"resume_tier": "USE_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("DE", 0.9, ["data engineer"], False),
    )

    assert guarded["resume_tier"] == "USE_TEMPLATE"
    assert "escalation_reason" not in guarded


def test_apply_tier1_safeguard_escalates_ambiguous_low_confidence():
    routing = {"resume_tier": "USE_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("ML", 0.5, ["ml engineer"], True),
    )

    assert guarded["resume_tier"] == "ADAPT_TEMPLATE"
    assert f"{TIER1_CONFIDENCE_THRESHOLD}" in guarded["escalation_reason"]


def test_apply_tier1_safeguard_escalates_no_match_default():
    routing = {"resume_tier": "USE_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("DE", 0.3, [], False),
    )

    assert guarded["resume_tier"] == "ADAPT_TEMPLATE"
    assert "Auto-escalated" in guarded["escalation_reason"]


def test_apply_tier1_safeguard_ignores_non_tier1_routing():
    routing = {"resume_tier": "ADAPT_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("ML", 0.9, ["data scientist"], False),
    )

    assert guarded["resume_tier"] == "ADAPT_TEMPLATE"
    assert "escalation_reason" not in guarded


def test_validate_tier2_output_rejects_unknown_ids():
    registry = load_registry()
    schema = registry["templates"]["DE"]["slot_schema"]

    errors = validate_tier2_output(
        {
            "slot_overrides": {"unknown_slot": "bad"},
            "skills_override": {"unknown_cat": "bad"},
            "entry_visibility": {"unknown_entry": False},
            "change_summary": "",
        },
        schema,
    )

    assert any("Unknown slot" in error for error in errors)
    assert any("Unknown skill category" in error for error in errors)
    assert any("Unknown entry" in error for error in errors)
    assert any("Missing change_summary" in error for error in errors)
