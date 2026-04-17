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


def test_load_registry_has_required_templates_and_role_metadata():
    """After 2026-04-17 revert: registry only keeps role-framing metadata
    (target_roles, bio_positioning, key_strengths). slot_schema is retired."""
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
        # slot_schema must be gone
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


def test_apply_tier1_safeguard_is_noop_after_2026_04_17_revert():
    # Post-2026-04-17: USE_TEMPLATE and ADAPT_TEMPLATE are retired; safeguard is pass-through.
    routing = {"resume_tier": "USE_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("ML", 0.5, ["ml engineer"], True),
    )

    assert guarded["resume_tier"] == "USE_TEMPLATE"
    assert "escalation_reason" not in guarded


def test_apply_tier1_safeguard_noop_on_low_confidence_no_match():
    routing = {"resume_tier": "USE_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("DE", 0.3, [], False),
    )

    assert guarded["resume_tier"] == "USE_TEMPLATE"
    assert "escalation_reason" not in guarded


def test_apply_tier1_safeguard_ignores_non_tier1_routing():
    routing = {"resume_tier": "ADAPT_TEMPLATE"}
    guarded = apply_tier1_safeguard(
        routing,
        RoutingDecision("ML", 0.9, ["data scientist"], False),
    )

    assert guarded["resume_tier"] == "ADAPT_TEMPLATE"
    assert "escalation_reason" not in guarded


def test_validate_tier2_output_is_noop_without_schema():
    """After 2026-04-17 revert: validate_tier2_output short-circuits when schema
    is missing or empty. The zone-era behavior (rejecting unknown slot IDs) is
    retired alongside slot_schema itself."""
    errors = validate_tier2_output(
        {
            "slot_overrides": {"unknown_slot": "bad"},
            "skills_override": {"unknown_cat": "bad"},
            "entry_visibility": {"unknown_entry": False},
            "change_summary": "",
        },
        {},  # empty schema — post-revert default
    )
    assert errors == []
