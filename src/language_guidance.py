"""
集中管理跨简历、求职信、分析输出的语言风格 guidance。
"""

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_GUIDANCE_PATH = PROJECT_ROOT / "assets" / "language_guidance.yaml"


def load_language_guidance(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load centralized language guidance config from YAML."""
    guidance_path = path or DEFAULT_GUIDANCE_PATH
    with open(guidance_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_language_guidance(content_type: str, path: Optional[Path] = None) -> Dict[str, Any]:
    """Return global tone plus the requested content-type guidance."""
    guidance = load_language_guidance(path)
    content_types = guidance.get("content_types", {})

    if content_type not in content_types:
        raise KeyError(f"Unknown language guidance content type: {content_type}")

    return {
        "global_tone": guidance.get("global_tone", {}),
        "content_type": {
            "name": content_type,
            **content_types[content_type],
        },
        "verb_architecture": guidance.get("verb_architecture", {}),
        "anti_patterns": guidance.get("anti_patterns", {}),
    }


def format_language_guidance_for_prompt(content_type: str, path: Optional[Path] = None) -> str:
    """Format guidance into a compact prompt block for generation tasks."""
    guidance = get_language_guidance(content_type, path)
    global_tone = guidance.get("global_tone", {})
    content = guidance.get("content_type", {})
    verb_arch = guidance.get("verb_architecture", {})
    anti_patterns = guidance.get("anti_patterns", {}).get("discouraged", [])

    tone_lines = "\n".join(f"- {item}" for item in global_tone.get("style", []))
    priority_lines = "\n".join(f"- {item}" for item in global_tone.get("priorities", []))
    content_lines = "\n".join(f"- {item}" for item in content.get("guidance", []))
    anti_lines = "\n".join(f"- {item}" for item in anti_patterns)

    verb_lines = []
    for name, rule in verb_arch.items():
        label = name.replace("_", " ")
        verbs = ", ".join(rule.get("preferred_verbs", []))
        note = rule.get("usage_note")
        line = f"- {label}: {verbs}"
        if note:
            line += f" ({note})"
        verb_lines.append(line)
    verb_text = "\n".join(verb_lines)

    return (
        "## Language Guidance\n"
        "Use this as soft guidance. Preserve credibility and factual grounding over polish.\n\n"
        "### Global Tone\n"
        f"{tone_lines}\n\n"
        "### Priorities\n"
        f"{priority_lines}\n\n"
        f"### Content-Type Guidance ({content.get('name', content_type)})\n"
        f"{content_lines}\n\n"
        "### Verb Architecture\n"
        f"{verb_text}\n\n"
        "### Avoid\n"
        f"{anti_lines}"
    )
