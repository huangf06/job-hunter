#!/usr/bin/env python3
"""
Resume Validator — 后置验证器
==============================

在 AI 生成 tailored_resume JSON 之后、渲染之前，校验：
1. Bio 禁词/年数声明
2. Title 是否在允许列表内 (BLOCKING)
3. Skills 排除项 + 可转移技能激活逻辑 (BLOCKING)
3b. Skill 分类名是否在白名单内 (BLOCKING)
4. 跨类别重复技能检测
5. 结构完整性 (最少经历/技能/bullets)

自动修复可修复项（bio 禁词替换），阻断不可修复项（排除技能、非法标题、非法分类名）。
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

from src import TRANSFERABLE_SKIP_WORDS

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class ValidationResult:
    passed: bool
    errors: list = field(default_factory=list)      # blocking issues
    warnings: list = field(default_factory=list)     # non-blocking
    fixes: dict = field(default_factory=dict)        # auto-applied fixes


class ResumeValidator:
    """Post-generation validator for AI-tailored resume JSON."""

    def __init__(self, bullet_library_path: Optional[Path] = None):
        self._library_loaded = False
        lib_path = bullet_library_path or PROJECT_ROOT / "assets" / "bullet_library.yaml"
        self._load_config(lib_path)

    def _load_config(self, lib_path: Path):
        """Load skill_tiers, title_options, bio_constraints, allowed categories from bullet_library.yaml."""
        if not lib_path.exists():
            print(f"[CRITICAL] bullet_library.yaml not found at {lib_path} — ALL validation gates disabled!")
            print(f"[CRITICAL] Resumes will pass without title, skill, or category checks.")
            self._skill_tiers = {}
            self._title_options = {}
            self._bio_constraints = {}
            self._allowed_categories = []
            self._library_loaded = False
            return

        with open(lib_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}

        self._skill_tiers = data.get('skill_tiers', {})
        self._title_options = data.get('title_options', {})
        self._bio_constraints = data.get('bio_constraints', {})
        self._allowed_categories = data.get('allowed_skill_categories', [])
        self._library_loaded = True

    def validate(self, tailored: dict, job: dict) -> ValidationResult:
        """Run all validations on tailored resume JSON.

        Args:
            tailored: The tailored_resume dict from AI analysis
            job: The job dict (needs 'description' for skill activation)

        Returns:
            ValidationResult with passed/errors/warnings/fixes
        """
        errors = []
        warnings = []
        fixes = {}
        jd_text = job.get('description', '') or ''

        # If bullet_library was not loaded, reject all resumes
        if not getattr(self, '_library_loaded', True):
            errors.append("bullet_library.yaml not found — cannot validate resume")
            return ValidationResult(passed=False, errors=errors)

        # 1. Bio validation
        bio = tailored.get('bio')
        if bio and isinstance(bio, str):
            fixed_bio, bio_warnings = self._validate_bio(bio)
            if fixed_bio != bio:
                tailored['bio'] = fixed_bio
                fixes['bio'] = fixed_bio
            warnings.extend(bio_warnings)
        elif bio and not isinstance(bio, str):
            warnings.append(f"Bio is {type(bio).__name__}, expected string — bio validation skipped")

        # 2. Title validation (BLOCKING)
        title_errors = self._validate_titles(tailored.get('experiences') or [])
        errors.extend(title_errors)

        # 3. Skills validation (items)
        skills_list = tailored.get('skills') or []
        skill_errors, skill_warnings = self._validate_skills(skills_list, jd_text)
        errors.extend(skill_errors)
        warnings.extend(skill_warnings)

        # 3b. Skill category whitelist validation (BLOCKING)
        category_errors = self._validate_skill_categories(skills_list)
        errors.extend(category_errors)

        # 4. Duplicate detection
        dup_warnings = self._check_duplicates(tailored)
        warnings.extend(dup_warnings)

        # 5. Structure validation
        struct_errors = self._validate_structure(tailored)
        errors.extend(struct_errors)

        passed = len(errors) == 0
        return ValidationResult(
            passed=passed,
            errors=errors,
            warnings=warnings,
            fixes=fixes,
        )

    def _validate_bio(self, bio: str) -> Tuple[str, List[str]]:
        """Check banned phrases and years claims in bio. Auto-replace where possible."""
        warnings = []
        fixed_bio = bio

        # Apply replacements for banned phrases
        replacements = self._bio_constraints.get('replacements', {})
        for banned, replacement in replacements.items():
            if banned.lower() in fixed_bio.lower():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(banned), re.IGNORECASE)
                fixed_bio = pattern.sub(replacement, fixed_bio)
                warnings.append(f"Bio: replaced '{banned}' with '{replacement}'")

        # Check remaining banned phrases (those without a replacement entry)
        banned_phrases = self._bio_constraints.get('banned_phrases', [])
        for phrase in banned_phrases:
            if phrase.lower() in fixed_bio.lower() and phrase not in replacements:
                warnings.append(f"Bio: contains banned phrase '{phrase}' (no auto-replacement)")

        # Check years claims — BLOCKING for string bios (bio builder already caps years)
        max_years = self._bio_constraints.get('max_years_claim', 6)
        # Match patterns like "6+ years", "7 years", "8+ years of"
        years_pattern = re.compile(r'(\d+)\+?\s*years?', re.IGNORECASE)

        def _cap_match(m):
            claimed = int(m.group(1))
            if claimed > max_years:
                warnings.append(
                    f"Bio: auto-capped '{m.group(0)}' to {max_years} years"
                )
                return m.group(0).replace(m.group(1), str(max_years), 1)
            return m.group(0)

        fixed_bio = years_pattern.sub(_cap_match, fixed_bio)

        return fixed_bio, warnings

    def _validate_titles(self, experiences: list) -> List[str]:
        """Check each experience title is in the allowed title_options. Returns ERRORS (blocking)."""
        errors = []
        if not self._title_options:
            return errors

        # Build a lookup: company name (lowercase) -> set of allowed titles
        company_titles = {}
        for company_key, titles in self._title_options.items():
            # Get all allowed titles for this company
            allowed = set()
            for role_key, title in titles.items():
                allowed.add(title)
            company_titles[company_key] = allowed

        for exp in experiences:
            company = exp.get('company', '')
            title = exp.get('title', '')
            if not company or not title:
                continue

            # Find matching company key (normalize to alphanumeric for dot-containing names like Ele.me)
            company_norm = re.sub(r'[^a-z0-9]', '', company.lower())
            matched_key = None
            for key in company_titles:
                key_norm = re.sub(r'[^a-z0-9]', '', key.lower())
                # Require full match or that key fully contains company (or vice versa)
                # with at least 3 chars overlap to avoid short-key false positives
                if company_norm == key_norm:
                    matched_key = key
                    break
                # Prefix match: require at least 4 chars overlap AND >= 60% of longer string
                overlap_len = min(len(key_norm), len(company_norm))
                max_len = max(len(key_norm), len(company_norm))
                if overlap_len >= 4 and overlap_len / max_len >= 0.6 and (
                    company_norm.startswith(key_norm) or key_norm.startswith(company_norm)
                ):
                    matched_key = key
                    break

            if matched_key:
                allowed = company_titles[matched_key]
                # Normalize whitespace for comparison (AI may add/drop spaces)
                title_norm = ' '.join(title.strip().lower().split())
                allowed_norm = {' '.join(t.strip().lower().split()) for t in allowed}
                if title_norm not in allowed_norm:
                    errors.append(
                        f"Title '{title}' for {company} not in allowed list: {sorted(allowed)}"
                    )

        return errors

    def _validate_skills(self, skills: list, jd_text: str) -> Tuple[List[str], List[str]]:
        """Validate skills: no excluded, only verified + activated transferable."""
        errors = []
        warnings = []

        if not self._skill_tiers:
            return errors, warnings

        excluded = [s.lower() for s in self._skill_tiers.get('excluded', [])]
        # Also add individual components of compound excluded skills (e.g. "C/C++" -> "c", "c++")
        excluded_expanded = set(excluded)
        for ex in excluded:
            if '/' in ex:
                for part in ex.split('/'):
                    part = part.strip()
                    if part:
                        excluded_expanded.add(part)
        excluded = list(excluded_expanded)

        # Build set of verified skills (flatten all categories)
        # Strip parenthetical qualifiers so "Python (Expert)" -> "python" matches skill_base
        verified_set = set()
        for category, skill_list in self._skill_tiers.get('verified', {}).items():
            for s in skill_list:
                base = re.sub(r'\s*\(.*?\)', '', s.lower()).strip()
                verified_set.add(base)
                # Also add individual components of compound skills (e.g., "ETL/ELT" -> "etl", "elt")
                if '/' in base:
                    for part in base.split('/'):
                        part = part.strip()
                        if part:
                            verified_set.add(part)

        # Build set of activated transferable skills
        jd_lower = jd_text.lower()
        transferable_activated = set()
        for item in self._skill_tiers.get('transferable', []):
            skill = item.get('skill', '')
            write_when = item.get('write_when', '').lower()
            # Simple keyword extraction from write_when
            # e.g. "JD mentions Azure" -> check if "azure" is in JD
            keywords = re.findall(r'\b\w+\b', write_when)
            for kw in keywords:
                if kw in TRANSFERABLE_SKIP_WORDS:
                    continue
                if re.search(r'\b' + re.escape(kw) + r'\b', jd_lower):
                    transferable_activated.add(re.sub(r'\s*\(.*?\)', '', skill.lower()).strip())
                    break

        # Check each skill in the resume
        for skill_group in skills:
            skills_str = skill_group.get('skills_list', '')
            if not isinstance(skills_str, str):
                errors.append(f"Skill group '{skill_group.get('category', '?')}': skills_list must be a string, got {type(skills_str).__name__}")
                continue
            # Parse individual skills from comma-separated string (also split on slash for compound skills)
            individual_skills = [s.strip() for part in skills_str.split(',') for s in part.split('/')]
            for skill in individual_skills:
                skill_clean = skill.strip()
                if not skill_clean:
                    continue
                skill_lower = skill_clean.lower()

                # Check against excluded list (exact token match to avoid "java" matching "javascript")
                # Strip parenthetical qualifiers like "Python (Expert)" -> "python"
                skill_base = re.sub(r'\s*\(.*?\)', '', skill_lower).strip()
                for ex in excluded:
                    if skill_base == ex or skill_base.startswith(ex + ' '):
                        errors.append(
                            f"Excluded skill '{skill_clean}' found in category "
                            f"'{skill_group.get('category', '?')}'"
                        )

                # Warn if skill is not in verified or activated transferable set
                if skill_base not in verified_set and skill_base not in transferable_activated:
                    warnings.append(
                        f"Unverified skill '{skill_clean}' in category "
                        f"'{skill_group.get('category', '?')}'"
                    )

        return errors, warnings

    def _check_duplicates(self, tailored: dict) -> List[str]:
        """Detect duplicate skills across categories."""
        warnings = []
        seen = {}  # skill_lower -> category

        for skill_group in (tailored.get('skills') or []):
            category = skill_group.get('category', '?')
            skills_str = skill_group.get('skills_list', '')
            if not isinstance(skills_str, str):
                continue
            # Split on comma and slash for consistency with _validate_skills
            individual_skills = [s.strip() for part in skills_str.split(',') for s in part.split('/')]
            for skill in individual_skills:
                skill_clean = skill.strip()
                if not skill_clean:
                    continue
                # Normalize: remove parenthetical notes for comparison
                skill_base = re.sub(r'\s*\(.*?\)', '', skill_clean).strip().lower()
                if skill_base in seen:
                    warnings.append(
                        f"Duplicate skill '{skill_clean}' in '{category}' "
                        f"(also in '{seen[skill_base]}')"
                    )
                else:
                    seen[skill_base] = category

        return warnings

    def _validate_skill_categories(self, skills: list) -> List[str]:
        """Validate that all skill category names are in the allowed whitelist. Returns ERRORS."""
        if not self._allowed_categories:
            return []

        errors = []
        allowed_lower = {c.lower() for c in self._allowed_categories}

        for skill_group in skills:
            category = skill_group.get('category', '')
            if not category:
                continue
            if category.lower() not in allowed_lower:
                errors.append(
                    f"Skill category '{category}' not in allowed list. "
                    f"Allowed: {self._allowed_categories}"
                )

        return errors

    def _validate_structure(self, tailored: dict) -> List[str]:
        """Validate minimum structural requirements."""
        errors = []

        # At least 2 experiences
        experiences = tailored.get('experiences') or []
        if len(experiences) < 2:
            errors.append(f"Need at least 2 experiences, got {len(experiences)}")

        # At least 3 skill categories
        skills = tailored.get('skills') or []
        if len(skills) < 3:
            errors.append(f"Need at least 3 skill categories, got {len(skills)}")

        # At least 1 project
        projects = tailored.get('projects') or []
        if len(projects) < 1:
            errors.append(f"Need at least 1 project, got {len(projects)}")

        # Each experience must have at least 1 bullet (filter empty strings)
        for i, exp in enumerate(experiences):
            bullets = [b for b in (exp.get('bullets') or []) if isinstance(b, str) and b.strip()]
            if len(bullets) == 0:
                errors.append(f"Experience '{exp.get('company', i)}' has no bullets")

        # Each project must have at least 1 bullet
        for i, proj in enumerate(tailored.get('projects') or []):
            bullets = [b for b in (proj.get('bullets') or []) if isinstance(b, str) and b.strip()]
            if len(bullets) == 0:
                errors.append(f"Project '{proj.get('name', i)}' has no bullets")

        return errors
