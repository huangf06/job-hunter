from pathlib import Path

import pytest


from src.language_guidance import (
    format_language_guidance_for_prompt,
    get_language_guidance,
    load_language_guidance,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUIDANCE_PATH = PROJECT_ROOT / "assets" / "language_guidance.yaml"


def test_load_language_guidance_has_required_sections():
    guidance = load_language_guidance(GUIDANCE_PATH)

    assert set(guidance.keys()) >= {
        "global_tone",
        "content_types",
        "verb_architecture",
        "anti_patterns",
    }


def test_get_language_guidance_returns_content_type_with_global_tone():
    guidance = get_language_guidance("experience_bullet", GUIDANCE_PATH)

    assert "global_tone" in guidance
    assert "content_type" in guidance
    assert guidance["content_type"]["name"] == "experience_bullet"
    assert "guidance" in guidance["content_type"]
    assert guidance["content_type"]["guidance"]


def test_get_language_guidance_rejects_unknown_content_type():
    with pytest.raises(KeyError, match="Unknown language guidance content type"):
        get_language_guidance("not_a_real_type", GUIDANCE_PATH)


def test_format_language_guidance_for_prompt_includes_named_sections():
    prompt_block = format_language_guidance_for_prompt("experience_bullet", GUIDANCE_PATH)

    assert "Language Guidance" in prompt_block
    assert "Global Tone" in prompt_block
    assert "Content-Type Guidance" in prompt_block
    assert "Verb Architecture" in prompt_block
    assert "Avoid" in prompt_block
