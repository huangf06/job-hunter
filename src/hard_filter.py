"""Hard filter module for job pipeline v2.0.

Extracted from scripts/job_pipeline.py to enable standalone testing and reuse.
"""

import json
import re
from pathlib import Path
from typing import Dict

import yaml

from src.db.job_db import FilterResult

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def keyword_boundary_pattern(kw: str) -> str:
    """Build regex pattern with proper word boundaries for keywords with non-word chars at edges.

    Standard \\b fails for keywords like '.net' (leading dot) or 'c#' (trailing hash).
    For leading non-word chars: skip boundary (the char itself is discriminating).
    For trailing non-word chars: use (?!\\w) lookahead.
    """
    escaped = re.escape(kw)
    prefix = '' if kw and not kw[0].isalnum() and kw[0] != '_' else r'\b'
    suffix = r'(?!\w)' if kw and not kw[-1].isalnum() and kw[-1] != '_' else r'\b'
    return prefix + escaped + suffix


class HardFilter:
    """Applies hard reject rules to job postings.

    Loads filter config from config/base/filters.yaml and blacklists from
    config/search_profiles.yaml on init.
    """

    def __init__(self):
        self.filter_config = self._load_config("base/filters.yaml")

        # Cache company and title blacklists (avoid reloading per-job)
        search_profiles = self._load_config("search_profiles.yaml")
        self.company_blacklist = [c.lower() for c in search_profiles.get('company_blacklist', [])]
        self.title_blacklist = [t.lower() for t in search_profiles.get('title_blacklist', [])]

    def _load_config(self, config_name: str) -> dict:
        """Load a YAML config file."""
        config_path = CONFIG_DIR / config_name
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        print(f"[WARN] Config not found: {config_path}")
        return {}

    def apply(self, job: Dict) -> FilterResult:
        """Apply hard filtering rules v2.0 to a single job.

        Supports multiple detection types:
        - word_count: Dutch word frequency detection
        - title_check: Title whitelist/blacklist check
        - tech_stack: Tech stack check (title + body)
        - regex: Regular expression matching
        """
        job_id = job['id']
        title = (job.get('title') or '').lower()
        description = (job.get('description') or '').lower()
        company = (job.get('company') or '').lower()
        location = (job.get('location') or '').lower()
        full_text = f"{title} {company} {description} {location}"

        # Reject jobs with insufficient data (empty JDs waste AI tokens)
        if not title.strip() or not description.strip() or len(description) < 50:
            return FilterResult(
                job_id=job_id, passed=False,
                reject_reason="insufficient_data",
                filter_version="2.0",
                matched_rules=json.dumps({"title_len": len(title), "desc_len": len(description)})
            )

        hard_rules = self.filter_config.get('hard_reject_rules', {})

        # Sort rules by priority
        sorted_rules = sorted(
            hard_rules.items(),
            key=lambda x: x[1].get('priority', 99)
        )

        for rule_name, rule_config in sorted_rules:
            if not rule_config.get('enabled', True):
                continue

            rule_type = rule_config.get('type', 'regex')

            # --- Dutch language word count detection ---
            if rule_type == 'word_count':
                indicators = rule_config.get('dutch_indicators', [])
                threshold = rule_config.get('threshold', 8)
                # Count how many Dutch indicator words appear in the text
                # Use word boundary matching to avoid partial matches
                count = 0
                for word in indicators:
                    # Use keyword_boundary_pattern for consistency with rest of pipeline
                    if re.search(keyword_boundary_pattern(word), full_text):
                        count += 1
                if count >= threshold:
                    return FilterResult(
                        job_id=job_id, passed=False,
                        reject_reason=rule_name,
                        filter_version="2.0",
                        matched_rules=json.dumps({"dutch_word_count": count})
                    )

            # --- Title-based role check ---
            elif rule_type == 'title_check':
                # Check exceptions first (against title, not body)
                exceptions = rule_config.get('exceptions', [])
                if any(
                    re.search(keyword_boundary_pattern(exc.lower().strip()), title)
                    for exc in exceptions if exc.strip()
                ):
                    continue

                # Check reject patterns (blacklist has priority)
                reject_patterns = rule_config.get('title_reject_patterns', [])
                rejected = False
                for pattern in reject_patterns:
                    try:
                        if re.search(pattern, title, re.IGNORECASE):
                            return FilterResult(
                                job_id=job_id, passed=False,
                                reject_reason=rule_name,
                                filter_version="2.0",
                                matched_rules=json.dumps({"rejected_pattern": pattern})
                            )
                    except re.error:
                        continue

                # Then check whitelist - title must contain at least one target keyword
                must_contain = rule_config.get('title_must_contain_one_of', [])
                if must_contain:
                    found = any(
                        re.search(keyword_boundary_pattern(kw.lower().strip()), title)
                        for kw in must_contain if kw.strip()
                    )
                    if not found:
                        return FilterResult(
                            job_id=job_id, passed=False,
                            reject_reason=rule_name,
                            filter_version="2.0",
                            matched_rules=json.dumps({"no_target_keyword_in_title": title})
                        )

            # --- Tech stack check (title + body) ---
            elif rule_type == 'tech_stack':
                exceptions = [e.lower().strip() for e in rule_config.get('exceptions', [])]

                # Skip if title contains an exception keyword (word-boundary match)
                title_has_exception = any(
                    re.search(keyword_boundary_pattern(exc), title) for exc in exceptions if exc
                )

                if not title_has_exception:
                    # Check title patterns
                    title_patterns = rule_config.get('title_patterns', [])
                    for pattern in title_patterns:
                        try:
                            if re.search(pattern, title, re.IGNORECASE):
                                return FilterResult(
                                    job_id=job_id, passed=False,
                                    reject_reason=rule_name,
                                    filter_version="2.0",
                                    matched_rules=json.dumps({"title_pattern": pattern})
                                )
                        except re.error:
                            continue

                    # Check body irrelevant keyword count
                    body_keywords = rule_config.get('body_irrelevant_keywords', [])
                    body_threshold = rule_config.get('body_irrelevant_threshold', 5)
                    body_count = sum(1 for kw in body_keywords if re.search(keyword_boundary_pattern(kw.lower()), description))
                    if body_count >= body_threshold:
                        return FilterResult(
                            job_id=job_id, passed=False,
                            reject_reason=rule_name,
                            filter_version="2.0",
                            matched_rules=json.dumps({"body_irrelevant_count": body_count})
                        )

            # --- Standard regex check ---
            elif rule_type == 'regex':
                patterns = rule_config.get('patterns', [])
                exceptions = rule_config.get('exceptions', [])

                # Check exceptions against title only (not full_text) to prevent
                # casual keyword mentions in JD body from bypassing experience filters
                if any(
                    re.search(keyword_boundary_pattern(exc.lower().strip()), title)
                    for exc in exceptions if exc.strip()
                ):
                    continue

                for pattern in patterns:
                    try:
                        if re.search(pattern, full_text, re.IGNORECASE):
                            return FilterResult(
                                job_id=job_id, passed=False,
                                reject_reason=rule_name,
                                filter_version="2.0",
                                matched_rules=json.dumps({"pattern": pattern})
                            )
                    except re.error:
                        continue

        # Company blacklist (cached in __init__)
        for blacklisted in self.company_blacklist:
            if re.search(keyword_boundary_pattern(blacklisted), company):
                return FilterResult(
                    job_id=job_id, passed=False,
                    reject_reason="company_blacklist",
                    filter_version="2.0"
                )

        # Title blacklist (cached in __init__) — reject intern/trainee/student titles
        for blacklisted in self.title_blacklist:
            if re.search(keyword_boundary_pattern(blacklisted), title):
                return FilterResult(
                    job_id=job_id, passed=False,
                    reject_reason="title_blacklist",
                    filter_version="2.0",
                    matched_rules=json.dumps({"blocked_title_keyword": blacklisted})
                )

        return FilterResult(job_id=job_id, passed=True, filter_version="2.0")
