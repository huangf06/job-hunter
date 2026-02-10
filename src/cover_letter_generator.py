#!/usr/bin/env python3
"""
Cover Letter Generator — AI 驱动的求职信生成
=============================================

基于已有的 job_analysis 结果，调用 Claude 生成结构化的 cover letter spec。
AI 输出 JSON spec（包含 prose + evidence_ids），验证后存入 cover_letters 表。

不改动 ai_analyzer.py — 独立模块，复用分析结果。
"""

import json
import os
import random
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=True)
except ImportError:
    pass

from anthropic import Anthropic, RateLimitError, APITimeoutError, APIConnectionError
from src.db.job_db import JobDatabase, CoverLetter


class CoverLetterGenerator:
    """AI 驱动的 cover letter 生成器"""

    def __init__(self, config_path: Path = None, model_override: str = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()

        # Model setup (same pattern as AIAnalyzer)
        active = model_override or self.config.get('active_model', 'opus')
        model_cfg = self.config.get('models', {}).get(active, {})
        self.model_name = model_cfg.get('model', 'claude-opus-4-6')
        self.max_tokens = model_cfg.get('max_tokens', 4096)
        self.temperature = model_cfg.get('temperature', 0.3)

        # API credentials
        env_key = model_cfg.get('env_key', 'ANTHROPIC_API_KEY')
        env_url = model_cfg.get('env_url', 'ANTHROPIC_BASE_URL')
        api_key = os.environ.get(env_key, '')
        base_url = os.environ.get(env_url, None)
        auth_type = model_cfg.get('auth_type', 'api_key')

        # Init Anthropic client
        client_kwargs = {}
        if base_url:
            client_kwargs['base_url'] = base_url
        if auth_type == 'bearer':
            client_kwargs['auth_token'] = api_key
        else:
            client_kwargs['api_key'] = api_key
        self.client = Anthropic(**client_kwargs)

        # Load bullet library + cover letter config
        self.bullet_library = self._load_yaml(PROJECT_ROOT / "assets" / "bullet_library.yaml")
        self.cl_config = self._load_yaml(PROJECT_ROOT / "assets" / "cover_letter_config.yaml")
        self.bullet_id_lookup = self._build_bullet_id_lookup()

    def _load_config(self, config_path: Path = None) -> dict:
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_yaml(self, path: Path) -> dict:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _build_bullet_id_lookup(self) -> Dict[str, str]:
        """Map bullet ID -> verified text from bullet_library.yaml"""
        lookup = {}
        if not self.bullet_library:
            return lookup

        prompt_settings = self.config.get('prompt_settings', {})
        exp_keys = prompt_settings.get('experience_keys', [])
        proj_keys = prompt_settings.get('project_keys', [])

        for key in exp_keys:
            section = self.bullet_library.get('work_experience', {}).get(key, {})
            for bullet in section.get('verified_bullets', []):
                if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                    lookup[bullet['id']] = bullet['content']

        for key in proj_keys:
            section = self.bullet_library.get('projects', {}).get(key, {})
            for bullet in section.get('verified_bullets', []):
                if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                    lookup[bullet['id']] = bullet['content']

        return lookup

    def _build_evidence_pool(self) -> str:
        """Format bullet library as [id] text for prompt"""
        lines = []
        for bid, text in self.bullet_id_lookup.items():
            lines.append(f"[{bid}] {text}")
        return "\n".join(lines)

    def _build_prompt(self, job: Dict, analysis: Dict,
                      custom_requirements: str = None) -> str:
        """Build the cover letter generation prompt"""
        company = job.get('company', 'the company')
        title = job.get('title', 'the position')
        description = (job.get('description', '') or '')[:10000]

        ai_score = analysis.get('ai_score', 0)
        reasoning = analysis.get('reasoning', '')
        tailored_resume = analysis.get('tailored_resume', '{}')

        angles = self.cl_config.get('narrative_angles', {})
        hooks = self.cl_config.get('opening_hooks', {})
        closers = self.cl_config.get('closer_types', {})
        tone = self.cl_config.get('tone_guidelines', [])
        banned = self.cl_config.get('banned_phrases', [])

        angles_str = "\n".join(f"  - {k}: {v}" for k, v in angles.items())
        hooks_str = "\n".join(f"  - {k}: {v}" for k, v in hooks.items())
        closers_str = "\n".join(f"  - {k}: {v}" for k, v in closers.items())
        tone_str = "\n".join(f"  - {t}" for t in tone)
        banned_str = "\n".join(f'  - "{b}"' for b in banned)

        evidence_pool = self._build_evidence_pool()

        if custom_requirements:
            requirements_section = f"""
## Custom Requirements (from application page)
The applicant has specific requirements from the application page. Address these directly:
{custom_requirements}
"""
        else:
            requirements_section = """
## Custom Requirements
None — generate a standard cover letter tailored to the job description.
"""

        # Escape braces in user content to prevent format string issues
        description_safe = description.replace('{', '{{').replace('}', '}}')
        reasoning_safe = reasoning.replace('{', '{{').replace('}', '}}')
        tailored_safe = tailored_resume.replace('{', '{{').replace('}', '}}')

        prompt = f"""You are writing a cover letter for a job application. Generate a structured JSON spec.

## Job Context
- Title: {title}
- Company: {company}
- AI Match Score: {ai_score}/10
- AI Reasoning: {reasoning_safe}

## Job Description
{description_safe}

## Tailored Resume (already generated for this job)
{tailored_safe}
{requirements_section}
## Evidence Pool (ONLY use these IDs for evidence_ids)
{evidence_pool}

## Available Narrative Components
Narrative angles (pick ONE that best fits):
{angles_str}

Opening hook styles:
{hooks_str}

Closer types:
{closers_str}

## Tone Rules
{tone_str}

## Banned Phrases (NEVER use these)
{banned_str}

## Output Format
Return a single JSON object with this exact structure:

{{{{
  "standard": {{{{
    "opening_prose": "A compelling 2-3 sentence opening. Reference something specific about the company from the JD. State the role. Hint at why you're a great fit.",
    "body_paragraphs": [
      {{{{
        "prose": "A narrative paragraph connecting your experience to the role's needs. Paraphrase, don't copy bullets verbatim. ~80-120 words.",
        "evidence_ids": ["bullet_id_1", "bullet_id_2"]
      }}}},
      {{{{
        "prose": "A second paragraph with different angle. ~80-120 words.",
        "evidence_ids": ["bullet_id_3"]
      }}}}
    ],
    "closer_prose": "2-3 sentences. Express enthusiasm, forward-looking, call to action.",
    "narrative_angle": "one_of_the_angle_ids"
  }}}},
  "short": {{{{
    "prose": "A concise ~150 word version suitable for email body or text box. Cover the same ground more briefly.",
    "evidence_ids": ["bullet_id_1", "bullet_id_2", "bullet_id_3"]
  }}}}
}}}}

## Rules
1. evidence_ids MUST come from the Evidence Pool above — use exact IDs
2. Do NOT copy bullet text verbatim — paraphrase achievements into narrative
3. Company-specific statements MUST come from the job description — do NOT invent facts about the company
4. Standard cover letter: ~250-300 words total (flexible, not strict)
5. Short version: ~120-150 words (flexible)
6. Standard has exactly 2 body_paragraphs
7. narrative_angle must be one of: {', '.join(angles.keys())}
8. Answer three questions: Why this company? Why you? Why now?
9. Be specific and concrete — generic statements are worthless

Return ONLY the JSON object, no other text."""

        return prompt

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from AI response (same strategy as ai_analyzer.py)"""
        # Attempt 1: Direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Attempt 2: Extract from code blocks
        patterns = [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```']
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        # Attempt 3: Balanced brace extraction
        start = text.find('{')
        if start >= 0:
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                ch = text[i]
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue
                if ch == '"' and not escape:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            break
        return None

    def _validate_spec(self, spec: Dict, job: Dict) -> Tuple[bool, List[str]]:
        """Validate cover letter spec against config constraints"""
        errors = []

        if 'standard' not in spec:
            errors.append("Missing 'standard' section")
            return False, errors
        if 'short' not in spec:
            errors.append("Missing 'short' section")
            return False, errors

        std = spec['standard']

        # Validate narrative_angle
        valid_angles = set(self.cl_config.get('narrative_angles', {}).keys())
        angle = std.get('narrative_angle', '')
        if angle and angle not in valid_angles:
            errors.append(f"Invalid narrative_angle: '{angle}'. Valid: {valid_angles}")

        # Validate evidence_ids in standard
        all_evidence_ids = []
        for para in std.get('body_paragraphs', []):
            for eid in para.get('evidence_ids', []):
                all_evidence_ids.append(eid)
                if eid not in self.bullet_id_lookup:
                    errors.append(f"Unknown evidence_id in standard: '{eid}'")

        # Validate evidence_ids in short
        for eid in spec['short'].get('evidence_ids', []):
            all_evidence_ids.append(eid)
            if eid not in self.bullet_id_lookup:
                errors.append(f"Unknown evidence_id in short: '{eid}'")

        if not all_evidence_ids:
            errors.append("No evidence_ids found in spec — cover letter has no grounded claims")

        # Check banned phrases
        banned = self.cl_config.get('banned_phrases', [])
        all_prose = self._extract_all_prose(spec)
        for phrase in banned:
            if phrase.lower() in all_prose.lower():
                errors.append(f"Banned phrase found: '{phrase}'")

        return len(errors) == 0, errors

    def _extract_all_prose(self, spec: Dict) -> str:
        """Extract all prose text from spec for validation"""
        parts = []
        std = spec.get('standard', {})
        parts.append(std.get('opening_prose', ''))
        for para in std.get('body_paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('closer_prose', ''))
        parts.append(spec.get('short', {}).get('prose', ''))
        return ' '.join(parts)

    def generate(self, job_id: str, custom_requirements: str = None,
                 force: bool = False) -> Optional[Dict]:
        """Generate cover letter spec for a job."""
        # Check existing
        if not force:
            existing = self.db.get_cover_letter(job_id)
            if existing and existing.get('spec_json'):
                print(f"[CoverLetter] Already exists for {job_id}. Use --regen to regenerate.")
                return json.loads(existing['spec_json'])

        # Load job + analysis
        job = self.db.get_job(job_id)
        if not job:
            print(f"[CoverLetter] Job not found: {job_id}")
            return None

        analysis = self.db.get_analysis(job_id)
        if not analysis:
            print(f"[CoverLetter] No AI analysis for job: {job_id}. Run --ai-analyze first.")
            return None

        company = job.get('company', '')[:20]
        title = job.get('title', '')[:45]
        print(f"[CoverLetter] Generating for: {title} @ {company}")

        # Build prompt
        prompt = self._build_prompt(job, analysis, custom_requirements)

        # AI call with retry
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                break
            except RateLimitError:
                wait = 30 * (attempt + 1) + random.uniform(0, 5)
                print(f"  [RATE LIMIT] Waiting {wait:.0f}s...")
                time.sleep(wait)
            except (APITimeoutError, APIConnectionError) as e:
                wait = 2 ** (attempt + 1)
                print(f"  [RETRY] {type(e).__name__}, waiting {wait}s...")
                time.sleep(wait)
        else:
            print(f"[CoverLetter] Failed after 3 attempts")
            return None

        # Extract response
        if not response.content or not response.content[0].text:
            print(f"[CoverLetter] Empty response from AI")
            return None

        raw_text = response.content[0].text
        tokens_used = (response.usage.input_tokens + response.usage.output_tokens
                       if response.usage else 0)

        # Parse JSON
        spec = self._parse_json_response(raw_text)
        if not spec:
            print(f"[CoverLetter] Failed to parse JSON response")
            print(f"  Raw (first 500 chars): {raw_text[:500]}")
            return None

        # Validate
        is_valid, errors = self._validate_spec(spec, job)
        if not is_valid:
            print(f"[CoverLetter] Validation failed:")
            for err in errors:
                print(f"  - {err}")
            return None
        if errors:
            for err in errors:
                print(f"  [WARN] {err}")

        # Assemble prose texts
        standard_text = self._assemble_standard_text(spec)
        short_text = spec.get('short', {}).get('prose', '')

        # Save to DB
        cl = CoverLetter(
            job_id=job_id,
            spec_json=json.dumps(spec, ensure_ascii=False),
            custom_requirements=custom_requirements or '',
            standard_text=standard_text,
            short_text=short_text,
            tokens_used=tokens_used,
        )
        self.db.save_cover_letter(cl)
        print(f"  -> Saved spec ({tokens_used} tokens)")

        return spec

    def _assemble_standard_text(self, spec: Dict) -> str:
        """Assemble full cover letter text from spec"""
        std = spec.get('standard', {})
        parts = []
        parts.append(std.get('opening_prose', ''))
        for para in std.get('body_paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('closer_prose', ''))
        return '\n\n'.join(p for p in parts if p)

    def generate_batch(self, min_ai_score: float = None, limit: int = 50) -> int:
        """Batch generate cover letters for jobs that have resumes but no cover letter"""
        threshold = min_ai_score
        if threshold is None:
            threshold = self.config.get('thresholds', {}).get('ai_score_generate_resume', 5.0)

        jobs = self.db.get_jobs_needing_cover_letter(min_ai_score=threshold, limit=limit)
        if not jobs:
            print("[CoverLetter] No jobs need cover letter generation")
            return 0

        print(f"\n[CoverLetter] Generating cover letters for {len(jobs)} jobs...")
        generated = 0

        for i, job in enumerate(jobs):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            ai_score = job.get('ai_score', 0)
            print(f"  [{i+1}/{len(jobs)}] [{ai_score:.1f}] {title} @ {company}")

            result = self.generate(job['id'])
            if result:
                generated += 1

        print(f"\n[CoverLetter] Done: {generated}/{len(jobs)} cover letters generated")
        return generated
