"""Template registry helpers for three-tier resume routing."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
REGISTRY_PATH = PROJECT_ROOT / "config" / "template_registry.yaml"
TIER1_CONFIDENCE_THRESHOLD = 0.7


@dataclass
class RoutingDecision:
    template_id: str
    confidence: float
    matched_keywords: List[str]
    ambiguous: bool
    seniority: str = "mid"  # "senior" or "mid"


def load_registry(path: Optional[Path] = None) -> Dict:
    registry_path = path or REGISTRY_PATH
    with open(registry_path, "r", encoding="utf-8") as handle:
        registry = yaml.safe_load(handle) or {}

    registry["_meta"] = {"path": str(registry_path)}
    return registry


_SENIOR_KEYWORDS = {"senior", "lead", "staff", "principal", "head"}


def _detect_seniority(title_lower: str) -> str:
    """Detect seniority level from job title."""
    for kw in _SENIOR_KEYWORDS:
        if kw in title_lower.split():
            return "senior"
    return "mid"


def select_template(title: str, registry: Dict) -> RoutingDecision:
    title_lower = (title or "").lower()
    seniority = _detect_seniority(title_lower)
    matches: Dict[str, List[str]] = {}

    for template_id, meta in registry.get("templates", {}).items():
        if not meta.get("enabled", True):
            continue
        matched = [keyword for keyword in meta.get("target_roles", []) if keyword in title_lower]
        if matched:
            matches[template_id] = matched

    if not matches:
        return RoutingDecision("DE", confidence=0.3, matched_keywords=[], ambiguous=False, seniority=seniority)

    if len(matches) == 1:
        template_id = next(iter(matches))
        if template_id == "ML" and "platform engineer" in title_lower:
            return RoutingDecision(template_id, confidence=0.5, matched_keywords=matches[template_id], ambiguous=True, seniority=seniority)
        return RoutingDecision(template_id, confidence=0.9, matched_keywords=matches[template_id], ambiguous=False, seniority=seniority)

    best = max(matches, key=lambda template_id: len(matches[template_id]))
    return RoutingDecision(best, confidence=0.5, matched_keywords=matches[best], ambiguous=True, seniority=seniority)


def resolve_routing(code_decision: RoutingDecision, c1_routing: Dict) -> Dict:
    final_template = code_decision.template_id
    override_reason = None

    if c1_routing.get("override") and c1_routing.get("override_reason"):
        final_template = c1_routing["template_id"]
        override_reason = c1_routing["override_reason"]

    return {
        "resume_tier": c1_routing["tier"],
        "template_id_initial": code_decision.template_id,
        "template_id_final": final_template,
        "routing_confidence": code_decision.confidence,
        "routing_override_reason": override_reason,
        "routing_payload": json.dumps(c1_routing, ensure_ascii=False),
    }


def apply_tier1_safeguard(routing: Dict, code_decision: RoutingDecision) -> Dict:
    # 2026-04-17 revert: USE_TEMPLATE and ADAPT_TEMPLATE retired; every job is
    # FULL_CUSTOMIZE. Kept as a no-op pass-through for backward compatibility.
    return routing


def validate_tier2_output(output: Dict, schema: Dict) -> List[str]:
    errors: List[str] = []
    valid_slots = {"bio", "bio_1", "bio_2", "bio_3"}
    valid_entries = set()
    valid_categories = set()

    for section in schema.get("sections", []):
        for entry in section.get("entries", []):
            valid_entries.add(entry["entry_id"])
            for bullet in entry.get("bullets", []):
                valid_slots.add(bullet["slot_id"])
        for category in section.get("categories", []):
            valid_categories.add(category["cat_id"])

    for slot_id in output.get("slot_overrides", {}):
        if slot_id not in valid_slots:
            errors.append(f"Unknown slot '{slot_id}' in slot_overrides")

    for cat_id in output.get("skills_override", {}):
        if cat_id not in valid_categories:
            errors.append(f"Unknown skill category '{cat_id}'")

    for entry_id in output.get("entry_visibility", {}):
        if entry_id not in valid_entries:
            errors.append(f"Unknown entry '{entry_id}' in entry_visibility")

    if not output.get("change_summary"):
        errors.append("Missing change_summary")

    return errors
