#!/usr/bin/env python3
"""
AI Job Analyzer — Claude Code CLI
==================================

Evaluates jobs and tailors resumes via Claude Code CLI (`claude -p`).
No Anthropic SDK dependency — flat subscription model.
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src import TRANSFERABLE_SKIP_WORDS
from src.db.job_db import JobDatabase, AnalysisResult, Resume
from src.language_guidance import format_language_guidance_for_prompt
from src.resume_validator import ResumeValidator
from src.template_registry import (
    apply_tier1_safeguard,
    load_registry,
    resolve_routing,
    select_template,
    validate_tier2_output,
)


class AIAnalyzer:
    """AI 驱动的职位分析和简历定制"""

    DEFAULT_EXPERIENCE_KEYS = ['glp_technology', 'baiquan_investment', 'eleme', 'henan_energy']
    DEFAULT_PROJECT_KEYS = [
        'financial_data_lakehouse', 'thesis_uq_rl', 'nlp_projects',
        'expedia_recommendation', 'ml4qs', 'deribit_options',
        'graphsage_gnn', 'obama_tts', 'lifeos', 'job_hunter_automation',
    ]

    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()
        self.registry = load_registry()
        self.bullet_library = self._load_bullet_library()
        self.valid_bullets = self._extract_valid_bullets()
        self.bullet_id_lookup = self._build_bullet_id_lookup()
        self.validator = ResumeValidator()
        print(f"[AI Analyzer] Claude Code CLI mode")
        print(f"[AI Analyzer] Loaded {len(self.bullet_id_lookup)} bullet IDs")

    def _load_config(self, config_path: Path = None) -> dict:
        """加载 AI 配置"""
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_bullet_library(self) -> str:
        """加载 bullet library，通过 YAML 解析提取结构化信息供 AI 参考"""
        lib_path = PROJECT_ROOT / "assets" / "bullet_library.yaml"
        if not lib_path.exists():
            self._parsed_bullets = {}
            self._skill_tiers = {}
            self._title_options = {}
            self._bio_constraints = {}
            self._bio_builder = {}
            self._allowed_categories = []
            return ""

        try:
            with open(lib_path, 'r', encoding='utf-8') as f:
                self._parsed_bullets = yaml.safe_load(f) or {}

            prompt_settings = self.config.get('prompt_settings', {})
            experience_keys = prompt_settings.get('experience_keys', self.DEFAULT_EXPERIENCE_KEYS)
            project_keys = prompt_settings.get('project_keys', self.DEFAULT_PROJECT_KEYS)

            sections = []
            work_exp = self._parsed_bullets.get('work_experience', {})
            projects_data = self._parsed_bullets.get('projects', {})

            # Log unconfigured sections for discoverability
            unconfigured_exp = set(work_exp.keys()) - set(experience_keys)
            unconfigured_proj = set(projects_data.keys()) - set(project_keys)
            if unconfigured_exp:
                print(f"  [INFO] Skipping unconfigured experience sections: {sorted(unconfigured_exp)}")
            if unconfigured_proj:
                print(f"  [INFO] Skipping unconfigured project sections: {sorted(unconfigured_proj)}")

            # Work experiences
            sections.append("## WORK EXPERIENCE (you MUST select 2-3 experiences)")
            for key in experience_keys:
                exp_data = work_exp.get(key, {})
                if not isinstance(exp_data, dict):
                    continue

                company = exp_data.get('company', key)
                location = exp_data.get('location', '')
                period = exp_data.get('period', '')
                title = exp_data.get('titles', {}).get('default', '')

                sections.append(f"\n### {company}")
                sections.append(f"Location: {location} | Period: {period} | Title: {title}")

                # Recommended sequences (if defined)
                rec_seqs = exp_data.get('recommended_sequences', {})
                if rec_seqs:
                    seq_lines = []
                    for role_type, seq in rec_seqs.items():
                        short_ids = [s.split('_', 1)[-1] if '_' in s else s for s in seq]
                        seq_lines.append(f"  {role_type}: {' → '.join(short_ids)}")
                    sections.append("Recommended bullet sequences (follow ordering when applicable):")
                    sections.extend(seq_lines)

                sections.append("Available bullets:")

                for bullet in exp_data.get('verified_bullets', []):
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bid = bullet.get('id', '')
                        prefix = f"[{bid}] " if bid else ""
                        role = bullet.get('narrative_role', '')
                        role_tag = f"({role}) " if role else ""
                        sections.append(f"  - {prefix}{role_tag}{bullet['content']}")

            # Projects
            sections.append("\n## PROJECTS (you MUST select 1-3 projects)")
            for key in project_keys:
                proj_data = projects_data.get(key, {})
                if not isinstance(proj_data, dict):
                    continue

                title = proj_data.get('title', key)
                period = proj_data.get('period', '')

                sections.append(f"\n### {title}")
                sections.append(f"Period: {period}")
                sections.append("Available bullets:")

                for bullet in proj_data.get('verified_bullets', []):
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bid = bullet.get('id', '')
                        prefix = f"[{bid}] " if bid else ""
                        role = bullet.get('narrative_role', '')
                        role_tag = f"({role}) " if role else ""
                        sections.append(f"  - {prefix}{role_tag}{bullet['content']}")

            # Extract v3.0 config blocks for dynamic prompt construction
            self._skill_tiers = self._parsed_bullets.get('skill_tiers', {})
            self._title_options = self._parsed_bullets.get('title_options', {})
            self._bio_constraints = self._parsed_bullets.get('bio_constraints', {})
            self._bio_builder = self._parsed_bullets.get('bio_builder', {})
            self._allowed_categories = self._parsed_bullets.get('allowed_skill_categories', [])

            return '\n'.join(sections)

        except Exception as e:
            print(f"[CRITICAL] Failed to load bullet library: {e}")
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"Cannot start AI Analyzer: bullet library failed to load: {e}") from e

    def _extract_valid_bullets(self) -> set:
        """Extract all valid bullets from parsed bullet library YAML (configured keys only)."""
        if not hasattr(self, '_parsed_bullets') or not self._parsed_bullets:
            return set()

        prompt_settings = self.config.get('prompt_settings', {})
        exp_keys = set(prompt_settings.get('experience_keys', self.DEFAULT_EXPERIENCE_KEYS))
        proj_keys = set(prompt_settings.get('project_keys', self.DEFAULT_PROJECT_KEYS))

        bullets = set()

        # From work experiences (configured keys only)
        for key, value in self._parsed_bullets.get('work_experience', {}).items():
            if key not in exp_keys:
                continue
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bullets.add(bullet['content'])

        # From projects (configured keys only)
        for key, value in self._parsed_bullets.get('projects', {}).items():
            if key not in proj_keys:
                continue
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bullets.add(bullet['content'])

        return bullets

    def _build_bullet_id_lookup(self) -> Dict[str, str]:
        """Build mapping of bullet ID -> verified text from parsed YAML.

        Only indexes bullets from configured experience_keys and project_keys,
        preventing phantom bullets (unconfigured sections) from passing validation.
        """
        lookup = {}
        if not hasattr(self, '_parsed_bullets') or not self._parsed_bullets:
            return lookup

        # Restrict to configured keys only
        prompt_settings = self.config.get('prompt_settings', {})
        exp_keys = set(prompt_settings.get('experience_keys', self.DEFAULT_EXPERIENCE_KEYS))
        proj_keys = set(prompt_settings.get('project_keys', self.DEFAULT_PROJECT_KEYS))

        for key, value in self._parsed_bullets.get('work_experience', {}).items():
            if key not in exp_keys:
                continue
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                        if bullet['id'] in lookup:
                            print(f"  [WARN] Duplicate bullet ID '{bullet['id']}' in {key} — overwriting previous")
                        lookup[bullet['id']] = bullet['content']

        for key, value in self._parsed_bullets.get('projects', {}).items():
            if key not in proj_keys:
                continue
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                        if bullet['id'] in lookup:
                            print(f"  [WARN] Duplicate bullet ID '{bullet['id']}' in {key} — overwriting previous")
                        lookup[bullet['id']] = bullet['content']

        return lookup

    def _build_skill_context(self, job_description: str) -> str:
        """Build dynamic skill context for the AI prompt based on JD."""
        if not self._skill_tiers:
            return "ONLY list skills the candidate actually has."

        lines = ["ONLY list skills the candidate actually has.\n"]
        lines.append("VERIFIED skills (can always include):")

        verified = self._skill_tiers.get('verified', {})
        if not isinstance(verified, dict):
            print(f"    [WARN] skill_tiers.verified is not a dict — skipping skill context")
            return '\n'.join(lines)
        for category, skills in verified.items():
            if not isinstance(skills, list):
                continue
            lines.append(f"  - {category}: {', '.join(skills)}")

        # Scan JD to activate transferable skills
        jd_lower = job_description.lower()
        transferable = self._skill_tiers.get('transferable', [])
        activated = []
        for item in transferable:
            if not isinstance(item, dict):
                continue
            skill = item.get('skill', '')
            write_when = item.get('write_when', '').lower()
            # Extract meaningful keywords from write_when
            keywords = re.findall(r'\b\w+\b', write_when)
            for kw in keywords:
                if kw in TRANSFERABLE_SKIP_WORDS:
                    continue
                if re.search(r'\b' + re.escape(kw) + r'\b', jd_lower):
                    activated.append(f"{skill} (basis: {item.get('basis', '')})")
                    break

        if activated:
            lines.append("\nTRANSFERABLE skills (include ONLY if JD mentions them):")
            for a in activated:
                lines.append(f"  - {a}")
        else:
            lines.append("\nNo transferable skills activated for this JD.")

        excluded = self._skill_tiers.get('excluded', [])
        if excluded and isinstance(excluded, list):
            lines.append(f"\nEXCLUDED (NEVER include): {', '.join(excluded)}")

        return '\n'.join(lines)

    def _build_title_context(self) -> str:
        """Build dynamic title options context for the AI prompt."""
        if not self._title_options:
            return "Choose the most relevant title for each experience."

        lines = ["Choose the title for each experience that BEST matches the JD:"]
        for company_key, titles in self._title_options.items():
            if not isinstance(titles, dict):
                print(f"    [WARN] title_options['{company_key}'] is not a dict — skipping")
                continue
            company_name = company_key.replace('_', ' ').title()
            unique_titles = list(dict.fromkeys(titles.values()))  # deduplicate preserving order
            title_list = [f'"{t}"' for t in unique_titles]
            lines.append(f"  - {company_name}: {', '.join(title_list)}")

        return '\n'.join(lines)

    def _build_bio_constraints(self) -> str:
        """Build dynamic bio constraint text for the AI prompt."""
        if not self._bio_constraints:
            return ""

        lines = []
        max_years = self._bio_constraints.get('max_years_claim', 6)
        scope = self._bio_constraints.get('years_claim_scope', 'working with data systems')
        lines.append(f"- Max years claim: {max_years} years of {scope}")

        banned = self._bio_constraints.get('banned_phrases') or []
        if not isinstance(banned, list):
            banned = [banned] if isinstance(banned, str) else []
        if banned:
            lines.append(f"- BANNED phrases in bio: {', '.join(banned)}")

        extra_rules = self._bio_constraints.get('extra_rules') or []
        if not isinstance(extra_rules, list):
            extra_rules = [extra_rules] if isinstance(extra_rules, str) else []
        for rule in extra_rules:
            lines.append(f"- {rule}")

        return '\n'.join(lines)

    def _resolve_bullet_ids(self, tailored: Dict) -> tuple:
        """Resolve bullet IDs to verified text from library.

        Returns (tailored_with_text, errors). Unknown IDs are skipped (not
        included in resolved bullets) and reported as errors. Downstream
        validator checks minimum bullet counts.
        Also accepts exact text matches for backward compatibility.
        """
        errors = []

        for exp in (tailored.get('experiences') or []):
            company = exp.get('company', 'Unknown')
            resolved = []
            bullets = exp.get('bullets') or []
            if not isinstance(bullets, list):
                errors.append(f"[{company}] 'bullets' must be a list, got {type(bullets).__name__}")
                exp['bullets'] = []
                continue
            for bullet in bullets:
                if not isinstance(bullet, str):
                    errors.append(f"[{company}] Bullet must be string, got {type(bullet).__name__}")
                    continue
                if bullet in self.bullet_id_lookup:
                    text = self.bullet_id_lookup[bullet]
                    if text not in resolved:
                        resolved.append(text)
                elif bullet in self.valid_bullets:
                    # Backward compat: AI returned exact text from library
                    if bullet not in resolved:
                        resolved.append(bullet)
                else:
                    errors.append(f"[{company}] Unknown bullet ID or text: '{bullet[:80]}'")
            exp['bullets'] = resolved

        for proj in (tailored.get('projects') or []):
            name = proj.get('name', 'Unknown')
            resolved = []
            bullets = proj.get('bullets') or []
            if not isinstance(bullets, list):
                errors.append(f"[{name}] 'bullets' must be a list, got {type(bullets).__name__}")
                proj['bullets'] = []
                continue
            for bullet in bullets:
                if not isinstance(bullet, str):
                    errors.append(f"[{name}] Bullet must be string, got {type(bullet).__name__}")
                    continue
                if bullet in self.bullet_id_lookup:
                    text = self.bullet_id_lookup[bullet]
                    if text not in resolved:
                        resolved.append(text)
                elif bullet in self.valid_bullets:
                    if bullet not in resolved:
                        resolved.append(bullet)
                else:
                    errors.append(f"[{name}] Unknown bullet ID or text: '{bullet[:80]}'")
            proj['bullets'] = resolved

        return tailored, errors

    def _inject_technical_skills(self, tailored: Dict):
        """Inject per-experience technical_skills from bullet library (static data).

        Looks up each experience's company name in the bullet library and adds
        the technical_skills field if defined. This is NOT AI-generated — it comes
        directly from bullet_library.yaml to ensure accuracy.
        """
        work_exp = self._parsed_bullets.get('work_experience', {})
        # Build company name → technical_skills lookup
        company_tech = {}
        for key, data in work_exp.items():
            if isinstance(data, dict) and 'technical_skills' in data:
                company_name = data.get('company', '')
                if company_name:
                    company_tech[company_name.lower()] = data['technical_skills']

        for exp in (tailored.get('experiences') or []):
            company = (exp.get('company') or '').lower()
            if company in company_tech:
                exp['technical_skills'] = company_tech[company]

    def _assemble_bio(self, bio_spec, job: Dict) -> tuple:
        """Assemble bio text from structured specification.

        Returns (bio_string, errors). If bio_spec is already a string (backward
        compat) or None, returns it as-is.
        """
        # null bio = no bio
        if bio_spec is None:
            return None, []

        # Backward compat: AI returned a freeform string
        if isinstance(bio_spec, str):
            return bio_spec, []

        # Structured bio: assemble from components
        if not isinstance(bio_spec, dict):
            return None, [f"Bio must be null, string, or dict — got {type(bio_spec).__name__}"]

        errors = []
        builder = self._bio_builder
        domain_claims_config = builder.get('domain_claims', {})
        closer_options = builder.get('closer_options', {})
        allowed_titles = builder.get('allowed_titles', [])

        # Validate role_title
        role_title = bio_spec.get('role_title', '')
        if not allowed_titles:
            print("    [WARN] bio_builder.allowed_titles is empty — title validation skipped")
        elif role_title not in allowed_titles:
            errors.append(f"Bio role_title '{role_title}' not in allowed: {allowed_titles}")

        # Validate & resolve domain claims
        claim_ids = bio_spec.get('domain_claims') or []
        if isinstance(claim_ids, str):
            claim_ids = [claim_ids]
        if not isinstance(claim_ids, list):
            errors.append(f"Bio domain_claims must be a list or string, got {type(claim_ids).__name__}")
            claim_ids = []
        claim_texts = []
        for cid in claim_ids:
            if cid in domain_claims_config:
                claim_data = domain_claims_config[cid]
                if isinstance(claim_data, dict) and 'text' in claim_data:
                    claim_texts.append(claim_data['text'])
                else:
                    errors.append(f"Bio domain_claim '{cid}' missing 'text' field in config")
            else:
                errors.append(f"Bio domain_claim '{cid}' not in whitelist: {list(domain_claims_config.keys())}")

        # Validate closer
        closer_id = bio_spec.get('closer_id')
        # Normalize: treat string "null" same as Python None
        if closer_id == 'null':
            closer_id = None
        closer_text = ''
        if closer_id is not None:
            if closer_id in closer_options:
                closer_data = closer_options[closer_id]
                if closer_data:
                    if isinstance(closer_data, dict):
                        closer_text = closer_data.get('text', '')
                    else:
                        closer_text = str(closer_data)
            else:
                errors.append(f"Bio closer_id '{closer_id}' not in options: {list(closer_options.keys())}")

        if errors:
            return None, errors

        # Assemble bio text
        years = bio_spec.get('years', 6)
        if isinstance(years, str):
            try:
                years = int(years)
            except (ValueError, TypeError):
                years = 6
        elif not isinstance(years, (int, float)):
            years = 6  # fallback to default if AI returned null/other
        max_years = self._bio_constraints.get('max_years_claim', 6)
        min_years = self._bio_constraints.get('min_years_claim', 4)
        if years > max_years:
            print(f"    [BIO] Auto-capped years from {years} to {max_years}")
            years = max_years
        if years < min_years:
            print(f"    [BIO] Auto-floored years from {years} to {min_years}")
            years = min_years

        parts = []

        # Opening: "{Role} with {N} years of experience in {domain1} and {domain2}."
        if claim_texts:
            domain_str = ' and '.join(claim_texts)
            parts.append(f"{role_title} with {years} years of experience in {domain_str}.")
        else:
            parts.append(f"{role_title} with {years} years of experience.")

        # Education
        include_edu = bio_spec.get('include_education', True)
        if isinstance(include_edu, str):
            include_edu = include_edu.lower() not in ('false', '0', 'no', 'none')
        if include_edu:
            edu = self.config.get('resume', {}).get('education', {}).get('master', {})
            edu_text = f"{edu.get('degree', 'M.Sc. in Artificial Intelligence')} from {edu.get('school', 'VU Amsterdam')} ({edu.get('date', '2025').split('--')[-1].strip()}, GPA {edu.get('gpa', '8.2/10')})."
            parts.append(edu_text)

        # Certification
        include_cert = bio_spec.get('include_certification', True)
        if isinstance(include_cert, str):
            include_cert = include_cert.lower() not in ('false', '0', 'no', 'none')
        if include_cert:
            cert = self.config.get('resume', {}).get('education', {}).get('certification', 'Databricks Certified Data Engineer Professional (2026)')
            # Strip year suffix if present for cleaner bio
            cert_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', cert)
            parts.append(f"{cert_clean}.")

        # Closer
        if closer_text:
            company = job.get('company', 'the company')
            closer_text = closer_text.replace('{company}', company)
            parts.append(closer_text)

        return ' '.join(parts), []

    # NOTE: legacy _build_prompt() removed — C1/C2 now use _build_evaluate_prompt / _build_tailor_prompt

    def _build_scoring_guidelines(self) -> str:
        """Build scoring guidelines text for C1 evaluator prompt."""
        return """Use the FULL 1-10 scale. INTEGERS ONLY — no decimals (not 7.5, not 8.5).

**Score Bands (mutually exclusive — pick the ONE that fits best):**
- 10: Unicorn match (<2%) — Every required skill present, exact experience level, domain overlap, candidate would be a top-3 hire
- 9: Near-perfect match (<5%) — ALL required skills present, experience level exact, domain overlap strong
- 8: Strong match, high confidence (10%) — Most required skills, minor gaps only in nice-to-haves, experience within 1 year
- 7: Good match, worth prioritizing (15%) — Core skills present, 1-2 gaps in secondary requirements, experience close
- 6: Solid match, worth applying (20%) — Core skills present, 1-2 secondary gaps, candidate can credibly do the job
- 5: Borderline (15%) — Has relevant foundation but notable gaps; would need to stretch. Apply only if no better options
- 4: Weak match (15%) — Major skill or experience gaps, different specialization but adjacent
- 3: Poor match (10%) — Wrong specialization, significant experience gaps
- 2: Wrong role (5%) — Different domain or tech stack entirely
- 1: Complete mismatch (<3%) — Nothing in common

**The key distinction for 7 vs 8:** Does the candidate match ALL core requirements with at most nice-to-have gaps? → 8. Are there 1-2 gaps in secondary requirements? → 7.

**The key distinction for 5 vs 6:** Would this candidate get past a 30-second resume screen by a hiring manager who knows the role? If yes → 6. If maybe → 5. If unlikely → 4.

**Calibration anchors:**
- JD requires "5+ years Java" but candidate has 0 Java → 3 MAX (wrong primary stack)
- JD requires "PhD in CS" but candidate has M.Sc. → 5 MAX (unless "or equivalent" mentioned → 6)
- JD is 80% frontend but candidate is backend → 2 MAX
- JD says "10+ years" but candidate has 6 → 4 MAX (significant experience gap)
- JD matches candidate's DE stack but wants cloud candidate lacks (GCP vs AWS) → 6-7 (transferable)
- JD is a startup wanting generalist data/ML with Python+SQL → 7-8 (strong fit)"""

    def _build_evaluate_prompt(self, job: Dict, code_decision) -> str:
        """Build C1 evaluation prompt (scoring + application brief). No bullet library."""
        prompt_template = self.config.get('prompts', {}).get('evaluator', '')
        if not prompt_template:
            raise ValueError("No evaluator prompt template found in config")

        ai_thresholds = self.config.get('ai_recommendation_thresholds', {})
        prompt_settings = self.config.get('prompt_settings', {})
        jd_max = prompt_settings.get('job_description_max_chars', 10000)
        jd_text = (job.get('description') or '')[:jd_max]

        scoring_guidelines = self._build_scoring_guidelines()

        # Escape braces
        jd_safe = jd_text.replace('{', '{{').replace('}', '}}')
        job_title = job.get('title', '').replace('{', '{{').replace('}', '}}')
        job_company = job.get('company', '').replace('{', '{{').replace('}', '}}')
        scoring_safe = scoring_guidelines.replace('{', '{{').replace('}', '}}')
        available_templates = []
        for template_id, meta in self.registry.get('templates', {}).items():
            if not meta.get('enabled', True):
                continue
            strengths = ', '.join(meta.get('key_strengths', []))
            available_templates.append(
                f"- {template_id}: {meta.get('bio_positioning', template_id)}. Strengths: {strengths}"
            )
        available_templates_safe = '\n'.join(available_templates).replace('{', '{{').replace('}', '}}')
        ambiguous_warning = "⚠ AMBIGUOUS: title matched multiple templates" if code_decision.ambiguous else ""

        return prompt_template.format(
            scoring_guidelines=scoring_safe,
            job_title=job_title,
            job_company=job_company,
            job_description=jd_safe,
            available_templates=available_templates_safe,
            preselected_template_id=code_decision.template_id,
            preselected_confidence=code_decision.confidence,
            ambiguous_warning=ambiguous_warning,
            apply_now_threshold=ai_thresholds.get('apply_now', 7),
            apply_threshold=ai_thresholds.get('apply', 5),
            maybe_threshold=ai_thresholds.get('maybe', 3),
        )

    def _build_tailor_prompt(self, job: Dict, analysis: Dict) -> str:
        """Build C2 tailor prompt (resume tailoring). Includes bullet library + C1 context."""
        prompt_template = self.config.get('prompts', {}).get('tailor', '')
        if not prompt_template:
            raise ValueError("No tailor prompt template found in config")
        language_guidance = format_language_guidance_for_prompt("experience_bullet")

        prompt_settings = self.config.get('prompt_settings', {})
        jd_max = prompt_settings.get('job_description_max_chars', 10000)
        jd_text = (job.get('description') or '')[:jd_max]

        # Build dynamic context
        skill_context = self._build_skill_context(jd_text)
        title_context = self._build_title_context()
        bio_constraints = self._build_bio_constraints()

        bio_titles = self._bio_builder.get('allowed_titles', [])
        bio_titles_str = ', '.join(f'"{t}"' for t in bio_titles) if bio_titles else '"Data Engineer"'

        domain_claims = self._bio_builder.get('domain_claims', {})
        if isinstance(domain_claims, dict):
            dc_lines = []
            for dc_id, dc_data in domain_claims.items():
                if isinstance(dc_data, dict):
                    dc_lines.append(f'      "{dc_id}" = {dc_data.get("text", dc_id)}')
                else:
                    dc_lines.append(f'      "{dc_id}" = {dc_data}')
            domain_claims_str = '\n'.join(dc_lines) if dc_lines else '      (none configured)'
        else:
            domain_claims_str = '      (none configured)'

        cat_list = self._allowed_categories if self._allowed_categories else []
        cat_str = ', '.join(f'"{c}"' for c in cat_list) if cat_list else '"Languages & Core"'

        # Extract C1 context
        c1_score = analysis.get('ai_score', 0)
        c1_recommendation = analysis.get('recommendation', 'UNKNOWN')
        c1_reasoning_raw = analysis.get('reasoning', '')
        # Parse reasoning JSON if it contains application_brief
        try:
            reasoning_data = json.loads(c1_reasoning_raw)
            c1_reasoning = reasoning_data.get('reasoning', c1_reasoning_raw)
            c1_brief = json.dumps(reasoning_data.get('application_brief', {}), ensure_ascii=False)
        except (json.JSONDecodeError, TypeError):
            c1_reasoning = c1_reasoning_raw
            c1_brief = '{}'

        # Escape braces
        jd_safe = jd_text.replace('{', '{{').replace('}', '}}')
        job_title = job.get('title', '').replace('{', '{{').replace('}', '}}')
        job_company = job.get('company', '').replace('{', '{{').replace('}', '}}')
        bullet_lib_safe = self.bullet_library.replace('{', '{{').replace('}', '}}')
        skill_ctx_safe = skill_context.replace('{', '{{').replace('}', '}}')
        title_ctx_safe = title_context.replace('{', '{{').replace('}', '}}')
        bio_cstr_safe = bio_constraints.replace('{', '{{').replace('}', '}}')
        c1_reasoning_safe = c1_reasoning.replace('{', '{{').replace('}', '}}')
        c1_brief_safe = c1_brief.replace('{', '{{').replace('}', '}}')

        prompt_body = prompt_template.format(
            bullet_library=bullet_lib_safe,
            job_title=job_title,
            job_company=job_company,
            job_description=jd_safe,
            c1_score=c1_score,
            c1_recommendation=c1_recommendation,
            c1_reasoning=c1_reasoning_safe,
            c1_brief=c1_brief_safe,
            skill_context=skill_ctx_safe,
            title_context=title_ctx_safe,
            bio_constraints=bio_cstr_safe,
            bio_allowed_titles_list=bio_titles_str,
            bio_domain_claims_list=domain_claims_str,
            allowed_skill_categories_list=cat_str,
        )
        return f"{language_guidance}\n\n{prompt_body}"

    def _build_tier2_prompt(self, job: Dict, analysis: Dict, c1_routing: Dict) -> str:
        prompt_template = self.config.get('prompts', {}).get('tailor_adapt', '')
        if not prompt_template:
            raise ValueError("No tailor_adapt prompt template found in config")

        prompt_settings = self.config.get('prompt_settings', {})
        jd_max = prompt_settings.get('job_description_max_chars', 10000)
        jd_text = (job.get('description') or '')[:jd_max]
        template_id = analysis.get('template_id_final')
        schema = self.registry['templates'][template_id]['slot_schema']

        return prompt_template.format(
            job_title=(job.get('title') or '').replace('{', '{{').replace('}', '}}'),
            job_company=(job.get('company') or '').replace('{', '{{').replace('}', '}}'),
            job_description=jd_text.replace('{', '{{').replace('}', '}}'),
            routing_gaps=json.dumps(c1_routing.get('gaps', []), ensure_ascii=False).replace('{', '{{').replace('}', '}}'),
            adapt_instructions=(c1_routing.get('adapt_instructions') or '').replace('{', '{{').replace('}', '}}'),
            template_schema=json.dumps(schema, ensure_ascii=False, indent=2),
        )

    def evaluate_job(self, job: Dict) -> Optional[AnalysisResult]:
        """C1: Score + application brief. Short prompt, fast."""
        job_id = job['id']
        code_decision = select_template(job.get('title', ''), self.registry)
        prompt = self._build_evaluate_prompt(job, code_decision)

        text = self._call_claude(prompt)
        if not text:
            print(f"  [WARN] _call_claude returned None for {job_id}, skipping (will retry later)")
            return None

        parsed = self._parse_response(text)
        if not parsed:
            preview = text[:300].replace('\n', ' ')
            print(f"  [WARN] Failed to parse C1 response for {job_id}")
            return AnalysisResult(
                job_id=job_id, ai_score=0.0,
                recommendation='REJECTED',
                reasoning=f'[PARSE_FAIL] {preview[:200]}',
                tailored_resume='{}',
                model='claude_code', tokens_used=0,
            )

        scoring = parsed.get('scoring', {})
        brief = parsed.get('application_brief', {})
        c1_routing = parsed.get('resume_routing') or {
            'tier': 'USE_TEMPLATE',
            'template_id': code_decision.template_id,
            'override': False,
            'override_reason': None,
            'gaps': [],
            'adapt_instructions': None,
        }
        routing = resolve_routing(code_decision, c1_routing)
        routing = apply_tier1_safeguard(routing, code_decision)

        def _safe_float(val, default=0.0):
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        return AnalysisResult(
            job_id=job_id,
            ai_score=_safe_float(scoring.get('overall_score', 0)),
            skill_match=_safe_float(scoring.get('skill_match', 0)),
            experience_fit=_safe_float(scoring.get('experience_fit', 0)),
            growth_potential=_safe_float(scoring.get('growth_potential', 0)),
            recommendation=scoring.get('recommendation', 'SKIP'),
            reasoning=json.dumps({"reasoning": scoring.get('reasoning', ''),
                                   "application_brief": brief}, ensure_ascii=False),
            tailored_resume='{}',
            model='claude_code',
            tokens_used=0,
            resume_tier=routing.get('resume_tier'),
            template_id_initial=routing.get('template_id_initial'),
            template_id_final=routing.get('template_id_final'),
            routing_confidence=routing.get('routing_confidence'),
            routing_override_reason=routing.get('routing_override_reason'),
            escalation_reason=routing.get('escalation_reason'),
            routing_payload=routing.get('routing_payload'),
        )

    def tailor_resume(self, job: Dict, analysis: Dict, c1_routing: Dict = None) -> Optional[str]:
        """C2: Resume tailoring. Long prompt, only for high-scoring jobs.
        Returns tailored_resume JSON string, or None on failure."""
        job_id = job['id']
        tier = analysis.get('resume_tier')
        if tier == 'ADAPT_TEMPLATE':
            prompt = self._build_tier2_prompt(job, analysis, c1_routing or {})
        else:
            prompt = self._build_tailor_prompt(job, analysis)

        text = self._call_claude(prompt)
        if not text:
            print(f"  [WARN] C2 empty response for {job_id}")
            return None

        parsed = self._parse_response(text)
        if not parsed:
            print(f"  [WARN] C2 parse failed for {job_id}")
            return None

        if tier == 'ADAPT_TEMPLATE':
            errors = validate_tier2_output(parsed, self.registry['templates'][analysis['template_id_final']]['slot_schema'])
            if errors:
                for error in errors:
                    print(f"    [TIER2 VALIDATION] {error}")
                return None
            return json.dumps(parsed, ensure_ascii=False)

        tailored = parsed.get('tailored_resume', {})
        if not tailored:
            print(f"  [WARN] C2 no tailored_resume in response for {job_id}")
            return None

        tailored, bullet_errors = self._resolve_bullet_ids(tailored)
        self._inject_technical_skills(tailored)
        if bullet_errors:
            for err in bullet_errors:
                print(f"    [BULLET WARN] {err}")

        # Bio assembly
        bio_spec = tailored.get('bio')
        assembled_bio, bio_errors = self._assemble_bio(bio_spec, job)
        if bio_errors:
            for err in bio_errors:
                print(f"    [BIO ERROR] {err}")
            return None
        tailored['bio'] = assembled_bio

        # Validation
        validation = self.validator.validate(tailored, job)
        if not validation.passed:
            for err in validation.errors:
                print(f"    [VALIDATION] {err}")
            return None
        if validation.warnings:
            for warn in validation.warnings:
                print(f"    [VALID WARN] {warn}")

        return json.dumps(tailored, ensure_ascii=False)

    def build_c3_input(self, template_schema: Dict, c2_output: Dict, c1_routing: Dict, jd_summary: str) -> str:
        lines = []
        lines.append(f"## Job Summary\n{jd_summary}\n")
        lines.append(f"## Identified Gaps\n{', '.join(c1_routing.get('gaps', []))}\n")
        lines.append("## Changes Made (before -> after)\n")

        change_count = 0
        total_changeable = 1

        if c2_output.get('slot_overrides', {}).get('bio'):
            lines.append("**Bio:**")
            lines.append(f"  BEFORE: {template_schema['bio']['default']}")
            lines.append(f"  AFTER:  {c2_output['slot_overrides']['bio']}\n")
            change_count += 1

        for section in template_schema.get('sections', []):
            for entry in section.get('entries', []):
                for bullet in entry.get('bullets', []):
                    total_changeable += 1
                    override = c2_output.get('slot_overrides', {}).get(bullet['slot_id'])
                    if override:
                        lines.append(f"**{bullet['slot_id']}:**")
                        lines.append(f"  BEFORE: {bullet['default']}")
                        lines.append(f"  AFTER:  {override}\n")
                        change_count += 1
            for category in section.get('categories', []):
                total_changeable += 1
                override = c2_output.get('skills_override', {}).get(category['cat_id'])
                if override:
                    lines.append(f"**skills.{category['cat_id']}:**")
                    lines.append(f"  BEFORE: {category['default']}")
                    lines.append(f"  AFTER:  {override}\n")
                    change_count += 1

        all_entries = set()
        for section in template_schema.get('sections', []):
            for entry in section.get('entries', []):
                all_entries.add(entry['entry_id'])
        total_changeable += len(all_entries)

        hidden = [entry_id for entry_id, visible in c2_output.get('entry_visibility', {}).items() if not visible]
        if hidden:
            lines.append(f"**Hidden entries:** {', '.join(hidden)}")
            change_count += len(hidden)

        density = change_count / max(total_changeable, 1) * 100
        lines.append(
            f"\n**Change density:** {change_count} of {total_changeable} changeable items modified ({density:.0f}%)"
        )
        return "\n".join(lines)

    def run_c3_gate(self, analysis: AnalysisResult, c1_routing: Dict, job: Dict) -> Dict:
        template_id = analysis.template_id_final
        schema = self.registry['templates'][template_id]['slot_schema']
        c2_output = json.loads(analysis.tailored_resume or '{}')
        reasoning_data = json.loads(analysis.reasoning or '{}')
        brief = reasoning_data.get('application_brief', {})
        jd_summary = brief.get('key_angle') or brief.get('hook') or job.get('title', '')
        structured_diff = self.build_c3_input(schema, c2_output, c1_routing, jd_summary)
        prompt = self.config.get('prompts', {}).get('c3_gate', '').format(
            structured_diff=structured_diff
        )
        text = self._call_claude(prompt)
        parsed = self._parse_response(text or '')
        if not parsed:
            return {'decision': 'FAIL', 'confidence': 0.0, 'reason': 'C3 parse failed'}
        return {
            'decision': parsed.get('decision', 'FAIL'),
            'confidence': float(parsed.get('confidence', 0.0) or 0.0),
            'reason': parsed.get('reason', ''),
        }

    def evaluate_batch(self, limit: int = None) -> tuple:
        """C1: Evaluate all jobs needing analysis.

        Returns (attempted, succeeded) tuple.
        """
        jobs = self.db.get_jobs_needing_analysis(limit=limit)
        if not jobs:
            print("[AI C1] No jobs to evaluate")
            return (0, 0)

        print(f"\n[AI C1] Evaluating {len(jobs)} jobs...")
        count = 0
        with self.db.batch_mode():
            for i, job in enumerate(jobs):
                title = job.get('title', '')[:45]
                company = job.get('company', '')[:20]
                print(f"  [{i+1}/{len(jobs)}] {title} @ {company}...", end=' ')
                try:
                    result = self.evaluate_job(job)
                    if result:
                        self.db.save_analysis(result)
                        count += 1
                        print(f"-> {result.recommendation} ({result.ai_score:.1f})")
                    else:
                        print("-> SKIPPED")
                except Exception as e:
                    print(f"-> ERROR: {e}")
                if i < len(jobs) - 1:
                    time.sleep(1)

        print(f"\n[AI C1] Done: {count}/{len(jobs)} evaluated")
        return (len(jobs), count)

    def tailor_batch(self, min_score: float = None, limit: int = None) -> tuple:
        """C2: Tailor resumes for evaluated jobs above threshold.

        Returns (attempted, succeeded) tuple.
        """
        if min_score is None:
            min_score = self.config.get('thresholds', {}).get('ai_score_generate_resume', 4.0)
        jobs = self.db.get_jobs_needing_tailor(min_score=min_score, limit=limit)
        if not jobs:
            print(f"[AI C2] No jobs needing tailoring (min_score={min_score})")
            return (0, 0)

        print(f"\n[AI C2] Tailoring {len(jobs)} jobs (score >= {min_score})...")
        count = 0
        with self.db.batch_mode():
            for i, job in enumerate(jobs):
                title = job.get('title', '')[:45]
                company = job.get('company', '')[:20]
                score = job.get('ai_score', 0)
                print(f"  [{i+1}/{len(jobs)}] {title} @ {company} ({score:.1f})...", end=' ')
                try:
                    analysis = self.db.get_analysis(job['id'])
                    if not analysis:
                        print("-> NO ANALYSIS")
                        continue
                    c1_routing = json.loads(analysis.get('routing_payload') or '{}')
                    resume_json = self.tailor_resume(job, analysis, c1_routing=c1_routing)
                    if resume_json:
                        c3_decision = None
                        c3_confidence = None
                        c3_reason = None
                        if analysis.get('resume_tier') == 'ADAPT_TEMPLATE':
                            temp_result = AnalysisResult(
                                job_id=job['id'],
                                reasoning=analysis.get('reasoning', ''),
                                tailored_resume=resume_json,
                                template_id_final=analysis.get('template_id_final'),
                            )
                            c3 = self.run_c3_gate(temp_result, c1_routing, job)
                            c3_decision = c3['decision']
                            c3_confidence = c3['confidence']
                            c3_reason = c3['reason']
                        self.db.update_analysis_resume(
                            job['id'],
                            resume_json,
                            c3_decision=c3_decision,
                            c3_confidence=c3_confidence,
                            c3_reason=c3_reason,
                        )
                        count += 1
                        print("-> TAILORED")
                    else:
                        print("-> FAILED")
                except Exception as e:
                    print(f"-> ERROR: {e}")
                if i < len(jobs) - 1:
                    time.sleep(1)

        print(f"\n[AI C2] Done: {count}/{len(jobs)} tailored")
        return (len(jobs), count)

    def _post_parse_analysis(self, job_id: str, job: Dict, parsed: Dict,
                              tokens_used: int, prompt: str = '') -> AnalysisResult:
        """Shared post-parse processing for both API and Claude Code paths."""
        scoring = parsed.get('scoring') or {}
        tailored = parsed.get('tailored_resume') or {}

        # Resolve bullet IDs to verified text (skip unknown, keep valid)
        tailored, bullet_errors = self._resolve_bullet_ids(tailored)
        # Inject per-experience technical_skills from bullet library (static, not AI-generated)
        self._inject_technical_skills(tailored)
        rejection_reason = ''
        if bullet_errors:
            for err in bullet_errors:
                print(f"    [BULLET WARN] {err}")
            print(f"    [WARN] {len(bullet_errors)} unknown bullet(s) skipped — validator will check minimums")

        # Assemble bio from structured spec (or pass through string/null)
        if tailored:
            bio_spec = tailored.get('bio')
            assembled_bio, bio_errors = self._assemble_bio(bio_spec, job)
            if bio_errors:
                for err in bio_errors:
                    print(f"    [BIO ERROR] {err}")
                print(f"    [REJECTED] Bio assembly failed — resume will not generate")
                rejection_reason = f"REJECTED: {'; '.join(bio_errors)}"
                tailored = {}
            else:
                tailored['bio'] = assembled_bio

        # v3.0: Early validation — reject before saving to keep counts accurate
        if tailored:
            validation = self.validator.validate(tailored, job)
            if not validation.passed:
                for err in validation.errors:
                    print(f"    [VALIDATION] {err}")
                val_reason = f"REJECTED: validation: {'; '.join(validation.errors[:3])}"
                rejection_reason = f"{rejection_reason} | {val_reason}" if rejection_reason else val_reason
                tailored = {}
            else:
                if validation.warnings:
                    for warn in validation.warnings:
                        print(f"    [VALID WARN] {warn}")
                if validation.fixes:
                    print(f"    [VALIDATION] Auto-fixes applied: {list(validation.fixes.keys())}")

        def _safe_float(val, default=0.0):
            try:
                return float(val)
            except (TypeError, ValueError):
                return default

        reasoning = scoring.get('reasoning', '')
        recommendation = scoring.get('recommendation', 'SKIP')
        if rejection_reason:
            reasoning = f"{reasoning} | {rejection_reason}" if reasoning else rejection_reason
            recommendation = 'REJECTED'

        return AnalysisResult(
            job_id=job_id,
            ai_score=_safe_float(scoring.get('overall_score', 0)),
            skill_match=_safe_float(scoring.get('skill_match', 0)),
            experience_fit=_safe_float(scoring.get('experience_fit', 0)),
            growth_potential=_safe_float(scoring.get('growth_potential', 0)),
            recommendation=recommendation,
            reasoning=reasoning,
            tailored_resume=json.dumps(tailored, ensure_ascii=False),
            model='claude_code',
            tokens_used=tokens_used
        )

    def _call_claude(self, prompt: str) -> Optional[str]:
        """Call Claude Code CLI to analyze a job.

        Pipes the prompt via stdin to `claude -p` and returns the raw text
        output (expected to be JSON).
        """
        import shutil
        import subprocess
        import tempfile

        claude_bin = shutil.which('claude')
        if not claude_bin:
            print(f"    [CLAUDE_CODE] 'claude' CLI not found in PATH")
            return None

        try:
            cmd = [claude_bin, '-p', '--output-format', 'text', '--max-turns', '2']
            # Strip ANTHROPIC_BASE_URL/API_KEY if present — they override
            # Claude Code's native OAuth auth (CLAUDE_CODE_OAUTH_TOKEN).
            clean_env = os.environ.copy()
            clean_env.pop('ANTHROPIC_BASE_URL', None)
            clean_env.pop('ANTHROPIC_API_KEY', None)
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                env=clean_env,
            )
            if result.returncode != 0:
                stderr = (result.stderr or '')[:500]
                stdout_preview = (result.stdout or '')[:200]
                print(f"    [CLAUDE_CODE] CLI error (rc={result.returncode}): {stderr} {stdout_preview}")
                return None
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"    [CLAUDE_CODE] CLI timed out after 300s")
            return None
        except FileNotFoundError:
            print(f"    [CLAUDE_CODE] 'claude' CLI not found at {claude_bin}")
            return None

    def analyze_job(self, job: Dict) -> Optional[AnalysisResult]:
        """分析单个职位: C1 evaluate + route + conditional C2/C3."""
        c1_result = self.evaluate_job(job)
        if not c1_result:
            return None

        c1_routing = json.loads(c1_result.routing_payload) if c1_result.routing_payload else {}
        if c1_result.resume_tier == 'USE_TEMPLATE':
            pass
        elif c1_result.resume_tier in ('ADAPT_TEMPLATE', 'FULL_CUSTOMIZE'):
            analysis = {
                'ai_score': c1_result.ai_score,
                'recommendation': c1_result.recommendation,
                'reasoning': c1_result.reasoning,
                'tailored_resume': c1_result.tailored_resume,
                'resume_tier': c1_result.resume_tier,
                'template_id_final': c1_result.template_id_final,
            }
            resume_json = self.tailor_resume(job, analysis, c1_routing=c1_routing)
            if resume_json:
                c1_result.tailored_resume = resume_json
                if c1_result.resume_tier == 'ADAPT_TEMPLATE':
                    c3 = self.run_c3_gate(c1_result, c1_routing, job)
                    c1_result.c3_decision = c3['decision']
                    c1_result.c3_confidence = c3['confidence']
                    c1_result.c3_reason = c3['reason']

        self.db.save_analysis(c1_result)
        if c1_result.resume_tier == 'USE_TEMPLATE' and c1_result.template_id_final:
            template_pdf = self.registry['templates'][c1_result.template_id_final]['pdf']
            self.db.save_resume(Resume(
                job_id=job['id'],
                role_type=c1_result.template_id_final,
                template_version="template_v1",
                pdf_path=template_pdf,
            ))

        return c1_result

    def _parse_response(self, text: str) -> Optional[Dict]:
        """解析 AI 的 JSON 响应"""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try balanced-brace JSON extraction (string-aware to handle braces in values)
        start = text.find('{')
        if start >= 0:
            depth = 0
            in_string = False
            i = start
            while i < len(text):
                c = text[i]
                if in_string:
                    if c == '\\' and i + 1 < len(text):
                        i += 2  # skip escaped char entirely
                        continue
                    if c == '"':
                        in_string = False
                elif c == '"':
                    in_string = True
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                if depth == 0 and not in_string:
                    try:
                        return json.loads(text[start:i+1])
                    except json.JSONDecodeError:
                        break
                i += 1
            # Fallback: simple first/last brace
            end = text.rfind('}') + 1
            if end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass

        # Try to find JSON in code blocks
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        return None

    def analyze_batch(self, limit: int = None) -> int:
        """批量分析职位: C1 evaluate + C2 tailor combined."""
        jobs = self.db.get_jobs_needing_analysis(limit=limit)
        if not jobs:
            print("[AI Analyzer] No jobs to analyze")
            return 0

        print(f"\n[AI Analyzer] Analyzing {len(jobs)} jobs (C1+C2)...")
        analyzed = 0

        with self.db.batch_mode():
            for i, job in enumerate(jobs):
                title = job.get('title', '')[:45]
                company = job.get('company', '')[:20]
                print(f"  [{i+1}/{len(jobs)}] {title} @ {company}...", end=' ')

                try:
                    result = self.analyze_job(job)
                    if result:
                        analyzed += 1
                        print(f"-> {result.recommendation} ({result.ai_score:.1f})")
                    else:
                        print("-> SKIPPED")
                except Exception as e:
                    print(f"-> ERROR: {e}")

                if i < len(jobs) - 1:
                    time.sleep(1)

        print(f"\n[AI Analyzer] Done: {analyzed}/{len(jobs)} analyzed")
        return analyzed

    def analyze_single(self, job_id: str) -> Optional[AnalysisResult]:
        """分析单个职位 (by ID): C1 evaluate + C2 tailor."""
        job = self.db.get_job(job_id)
        if not job:
            print(f"[AI Analyzer] Job not found: {job_id}")
            return None

        print(f"[AI Analyzer] Analyzing (C1+C2): {job['title']} @ {job['company']}")
        result = self.analyze_job(job)
        if result:
            print(f"  Score: {result.ai_score:.1f} | {result.recommendation}")
            tier = result.resume_tier or ""
            tailored = json.loads(result.tailored_resume) if result.tailored_resume else {}
            if tier == "USE_TEMPLATE":
                print(f"  Resume: template {result.template_id_final} (no adaptation)")
            elif tier == "ADAPT_TEMPLATE":
                slot_count = len((tailored or {}).get("slot_overrides", {}))
                if result.c3_decision == "FAIL":
                    print(f"  Resume: adapted {result.template_id_final} rejected by C3, using template")
                else:
                    print(f"  Resume: adapted {result.template_id_final} ({slot_count} slots overridden)")
            elif tailored and tailored != {}:
                print(f"  Resume: tailored ({len(tailored.get('experiences', []))} experiences)")
            else:
                print(f"  Resume: not tailored (score below threshold or C2 failed)")
        return result


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Job Analyzer (C1/C2)")
    parser.add_argument('--batch', action='store_true', help='C1+C2 for all pending jobs')
    parser.add_argument('--evaluate', action='store_true', help='C1 only: evaluate pending jobs')
    parser.add_argument('--tailor', action='store_true', help='C2 only: tailor evaluated jobs')
    parser.add_argument('--job', type=str, help='C1+C2 for a single job by ID')
    parser.add_argument('--limit', type=int, default=50,
                        help='Max jobs to process in batch')
    args = parser.parse_args()

    analyzer = AIAnalyzer()

    if args.job:
        analyzer.analyze_single(args.job)
    elif args.evaluate:
        analyzer.evaluate_batch(limit=args.limit)
    elif args.tailor:
        analyzer.tailor_batch(limit=args.limit)
    elif args.batch:
        analyzer.analyze_batch(limit=args.limit)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
