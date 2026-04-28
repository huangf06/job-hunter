#!/usr/bin/env python3
"""Cover Letter Generator — AI-driven cover letter spec generation."""

import json
import os
import re
import sys
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

from src.db.job_db import JobDatabase, CoverLetter
from src.language_guidance import format_language_guidance_for_prompt


def _extract_application_brief_text(analysis: Dict) -> str:
    reasoning = analysis.get("reasoning", "")
    try:
        reasoning_data = json.loads(reasoning)
    except (json.JSONDecodeError, TypeError):
        return ""
    brief = reasoning_data.get("application_brief") or {}
    return brief.get("key_angle") or brief.get("hook") or ""


def get_resume_context_for_cl(job_analysis_row: Dict, registry: Dict) -> str:
    brief_text = _extract_application_brief_text(job_analysis_row)
    context = job_analysis_row.get("tailored_resume", "{}")
    if brief_text:
        context = f"{context}\nApplication Brief: {brief_text}"
    return context


class CoverLetterGenerator:
    """AI 驱动的 cover letter 生成器"""

    def __init__(self, config_path: Path = None, model_override: str = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()
        from src.template_registry import load_registry
        self.registry = load_registry()

        # Load bullet library + cover letter config
        self.bullet_library = self._load_yaml(PROJECT_ROOT / "assets" / "bullet_library.yaml")
        self.cl_config = self._load_yaml(PROJECT_ROOT / "assets" / "cover_letter_config.yaml")
        self.bullet_id_lookup = self._build_bullet_id_lookup()

        # v2.0: Load voice examples and knowledge base
        self.voice_examples = self._load_voice_examples()
        self.knowledge_base = self._load_knowledge_base()

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

        active = self.bullet_library.get('active_sections', {})
        exp_keys = active.get('experience_keys', [])
        proj_keys = active.get('project_keys', [])

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

    # =========================================================================
    # v2.0: Voice examples + Knowledge base loading
    # =========================================================================

    def _load_voice_examples(self) -> List[str]:
        """Load voice example files from assets/voice_examples/"""
        examples = []
        voice_dir = PROJECT_ROOT / "assets" / "voice_examples"
        if not voice_dir.exists():
            return examples
        for path in sorted(voice_dir.glob("*.txt")):
            text = path.read_text(encoding='utf-8').strip()
            if text:
                examples.append(text)
        return examples

    def _load_knowledge_base(self) -> List[Dict]:
        """Load CL knowledge base fragments"""
        kb_path = PROJECT_ROOT / "assets" / "cl_knowledge_base.yaml"
        if not kb_path.exists():
            return []
        data = self._load_yaml(kb_path)
        return data.get('fragments', [])

    def _infer_role_types(self, job: Dict, analysis: Dict) -> List[str]:
        """Infer role types from job title for fragment filtering"""
        title = (job.get('title', '') or '').lower()
        role_types = set()

        mapping = {
            'data_engineer': ['data engineer', 'etl', 'pipeline', 'databricks',
                              'spark', 'data platform', 'data infrastructure'],
            'ml_engineer': ['ml engineer', 'machine learning engineer',
                            'ai engineer', 'deep learning'],
            'data_scientist': ['data scientist', 'data science',
                               'applied scientist'],
            'quant': ['quant', 'trading', 'derivatives', 'risk analyst',
                      'portfolio', 'hedge fund'],
            'data_analyst': ['data analyst', 'analytics', 'business intelligence',
                             'bi developer'],
        }

        for role_type, keywords in mapping.items():
            if any(kw in title for kw in keywords):
                role_types.add(role_type)

        # Fallback: if no specific match, use broad types
        if not role_types:
            role_types = {'data_engineer', 'data_scientist', 'ml_engineer'}

        return list(role_types)

    def _extract_themes_from_jd(self, job: Dict) -> List[str]:
        """Extract themes from JD text using theme_signals config"""
        description = (job.get('description', '') or '').lower()
        theme_signals = self.cl_config.get('theme_signals', {})
        theme_scores = {}
        for theme, signals in theme_signals.items():
            score = sum(1 for s in signals if s.lower() in description)
            if score > 0:
                theme_scores[theme] = score
        # Return themes sorted by score descending
        return [t for t, _ in sorted(theme_scores.items(), key=lambda x: -x[1])]

    def _select_relevant_fragments(self, fragments: List[Dict],
                                   role_types: List[str],
                                   themes: List[str] = None) -> List[Dict]:
        """Select knowledge base fragments relevant to the given role types and themes"""
        relevant = []
        for frag in fragments:
            frag_roles = frag.get('role_types', [])
            if 'all' in frag_roles or any(rt in frag_roles for rt in role_types):
                relevant.append(frag)

        # Sort: micro_stories first (scored by theme match), then handwritten, then others
        origin_order = {
            'handwritten': 0, 'voice_example': 1,
            'ai_edited': 2, 'ai_approved': 3,
        }

        def sort_key(frag):
            is_micro = frag.get('type') == 'micro_story'
            theme_score = 0
            if is_micro and themes:
                frag_themes = frag.get('themes', [])
                theme_score = sum(1 for t in themes if t in frag_themes)
            # micro_stories with theme matches first, then by origin
            return (0 if is_micro and theme_score > 0 else 1,
                    -theme_score,
                    origin_order.get(frag.get('origin', ''), 99))

        relevant.sort(key=sort_key)
        return relevant

    # =========================================================================
    # Claude Code CLI integration
    # =========================================================================

    def _call_claude_code(self, prompt: str) -> Optional[str]:
        """Call Claude Code CLI with prompt and return text output."""
        import shutil
        import subprocess

        claude_bin = shutil.which('claude')
        if not claude_bin:
            print(f"  [CLAUDE_CODE] 'claude' CLI not found in PATH")
            return None

        try:
            cmd = [claude_bin, '-p', '--output-format', 'text', '--max-turns', '2']
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
                print(f"  [CLAUDE_CODE] CLI error (rc={result.returncode}): {stderr} {stdout_preview}")
                return None
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"  [CLAUDE_CODE] CLI timed out after 300s")
            return None
        except FileNotFoundError:
            print(f"  [CLAUDE_CODE] 'claude' CLI not found at {claude_bin}")
            return None

    # =========================================================================
    # Prompt building (v2.0 — completely rewritten)
    # =========================================================================

    def _build_prompt(self, job: Dict, analysis: Dict,
                      custom_requirements: str = None) -> str:
        """Build the cover letter generation prompt (v2.0 — micro-story anchored)"""
        company = job.get('company', 'the company')
        title = job.get('title', 'the position')
        description = (job.get('description', '') or '')[:10000]

        ai_score = analysis.get('ai_score', 0)
        reasoning = analysis.get('reasoning', '')
        tailored_resume = get_resume_context_for_cl(analysis, self.registry)

        # Load config sections
        tone = self.cl_config.get('tone_guidelines', [])
        banned = self.cl_config.get('banned_phrases', [])
        anti_detection = self.cl_config.get('anti_detection_rules', [])

        tone_str = "\n".join(f"  - {t}" for t in tone)
        banned_str = "\n".join(f'  - "{b}"' for b in banned)
        anti_str = "\n".join(f"  - {r}" for r in anti_detection)

        evidence_pool = self._build_evidence_pool()

        # --- Voice examples section ---
        voice_section = ""
        if self.voice_examples:
            voice_parts = []
            for i, ex in enumerate(self.voice_examples[:3], 1):
                voice_parts.append(f"### Example {i}\n{ex}")
            voice_text = "\n\n".join(voice_parts)
            voice_section = f"""
## Candidate's Writing Voice (CRITICAL — match this style)
Below are cover letters that represent the candidate's authentic voice.
Your output MUST match this tone: the sentence rhythm, directness, level
of formality, and personality. Do NOT use generic AI professional voice.

{voice_text}
"""

        # --- Knowledge base fragments section (with theme matching) ---
        kb_section = ""
        anchor_section = ""
        role_types = self._infer_role_types(job, analysis)
        themes = self._extract_themes_from_jd(job)
        relevant_frags = self._select_relevant_fragments(
            self.knowledge_base, role_types, themes)

        # Separate micro-stories from other fragments
        micro_stories = [f for f in relevant_frags if f.get('type') == 'micro_story']
        other_frags = [f for f in relevant_frags if f.get('type') != 'micro_story']

        if micro_stories:
            ms_lines = []
            for frag in micro_stories:
                frag_id = frag.get('id', 'unknown')
                frag_themes = ', '.join(frag.get('themes', []))
                text = frag.get('text', '').strip()
                ms_lines.append(f"  [{frag_id}] (themes: {frag_themes}) {text}")
            ms_text = "\n".join(ms_lines)
            anchor_section = f"""
## Anchor Material (use one as your starting point)
These are micro-stories — real experiences the candidate has reflected on.
Pick the one most connected to this job. Build your letter around it.
Do NOT copy verbatim — adapt, compress, and connect to THIS role.

{ms_text}
"""

        if other_frags:
            frag_lines = []
            for frag in other_frags:
                origin = frag.get('origin', 'unknown')
                ftype = frag.get('type', '')
                text = frag.get('text', '').strip()
                frag_lines.append(f"  [{origin}] ({ftype}) {text}")
            frags_text = "\n".join(frag_lines)
            kb_section = f"""
## Candidate's Own Thoughts (from previous cover letters)
These are real fragments the candidate has written or approved. Use them
as RAW MATERIAL — draw on the ideas, adapt the phrasing, weave in naturally.
Prioritize [handwritten] fragments. Do NOT copy verbatim — adapt to THIS job.

{frags_text}
"""

        # --- Custom requirements / seeds section ---
        req_section = ""
        if custom_requirements:
            # Detect if this is seeds from checklist UI vs actual application requirements
            is_seeds = any(custom_requirements.startswith(p) for p in
                           ("Company observation:", "Personal motivation:", "Genuine curiosity:"))
            if is_seeds:
                req_section = f"""
## Candidate's Seed Ideas (weave these in naturally)
The candidate provided personal notes about this job. Draw on these authentically —
they are raw thoughts, not requirements. Adapt the language, don't copy literally.
{custom_requirements}
"""
            else:
                req_section = f"""
## Custom Requirements (from application page)
Address these directly:
{custom_requirements}
"""

        # Escape braces in user content to prevent format string issues
        description_safe = description.replace('{', '{{').replace('}', '}}')
        reasoning_safe = reasoning.replace('{', '{{').replace('}', '}}')
        tailored_safe = tailored_resume.replace('{', '{{').replace('}', '}}')
        language_guidance = format_language_guidance_for_prompt("cover_letter")

        prompt = f"""{language_guidance}

Your task is NOT to write a cover letter. Your task is to answer in 150-250 words:
"Why would this person find this role interesting, and how do they think about their work?"

Write as Fei Huang — authentic, specific, human. This should read like a thoughtful
person explaining their genuine interest, not a candidate reciting qualifications.

## Candidate Background
- Based in the Netherlands since 2023 (MSc AI, VU Amsterdam, graduated Aug 2025)
- On Zoekjaar (orientation year) visa, building career in NL long-term
- Career path: Industrial Engineering (Tsinghua) -> Energy operations -> Food delivery analytics (Ele.me) -> Quant research (Baiquan) -> Fintech credit scoring (GLP) -> MSc AI -> Job search
- Core philosophy: pragmatic engineer who values systems that work in production
- Databricks Certified Data Engineer Professional (Feb 2026)
{voice_section}{anchor_section}{kb_section}
## Job Context
- Title: {title}
- Company: {company}
- AI Match Score: {ai_score}/10
- AI Reasoning: {reasoning_safe}

## Job Description
{description_safe}

## Tailored Resume (already generated for this job)
{tailored_safe}
{req_section}
## Evidence Pool (ONLY use these IDs for evidence_ids)
{evidence_pool}

## Tone & Voice Rules
{tone_str}

## Anti-Detection Rules (CRITICAL)
{anti_str}

## Banned Phrases (NEVER use)
{banned_str}

## Output Format
Return a single JSON object with this structure:

{{
  "standard": {{
    "paragraphs": [
      {{"prose": "First paragraph — anchor in something specific about THIS role or company.", "evidence_ids": ["bullet_id_1"]}},
      {{"prose": "Second paragraph — go deep on one angle. Show how you think.", "evidence_ids": ["bullet_id_2"]}},
      {{"prose": "Optional third — a genuine curiosity, or understated closer.", "evidence_ids": []}}
    ],
    "micro_story_id": null
  }},
  "short": {{
    "prose": "100-150 word version. Same voice, compressed into one paragraph.",
    "evidence_ids": ["bullet_id_1", "bullet_id_2"]
  }}
}}

## Rules
1. evidence_ids MUST come from the Evidence Pool — use exact IDs
2. Do NOT copy bullet text verbatim — paraphrase into narrative
3. Company-specific statements MUST come from the JD — do NOT invent company facts
4. Standard: 150-250 words, 2-3 paragraphs (flat array, no opening/body/closer separation)
5. Short: 100-150 words, single paragraph
6. Focus on 2-3 JD requirements DEEPLY — do NOT address every requirement
7. If anchor material (micro-stories) is provided, pick ONE and build around it. Set micro_story_id to the ID you used. If none provided, set micro_story_id to null.
8. If knowledge base has relevant fragments, USE them as inspiration
9. Weave in Netherlands context naturally if it fits (not forced)
10. Express ONE genuine curiosity or honest observation
11. NEVER claim the candidate lacks any skill or technology — the resume and evidence pool are NOT exhaustive lists of candidate skills. Phrases like "I don't have X experience" are FORBIDDEN.

Return ONLY the JSON object, no other text."""

        return prompt

    # =========================================================================
    # Response parsing & validation (unchanged from v1)
    # =========================================================================

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

        # Validate paragraphs structure (new format)
        paragraphs = std.get('paragraphs', [])
        if paragraphs:
            if len(paragraphs) < 2:
                errors.append(f"Standard must have 2-3 paragraphs, got {len(paragraphs)}")
            elif len(paragraphs) > 4:
                errors.append(f"Standard has too many paragraphs ({len(paragraphs)}), max 4")
        else:
            # Backward compat: old format
            if not std.get('body_paragraphs'):
                errors.append("Missing paragraphs in standard section")

        # Validate evidence_ids
        all_evidence_ids = []
        source = paragraphs if paragraphs else std.get('body_paragraphs', [])
        for para in source:
            for eid in para.get('evidence_ids', []):
                all_evidence_ids.append(eid)
                if eid not in self.bullet_id_lookup:
                    errors.append(f"Unknown evidence_id: '{eid}'")

        for eid in spec['short'].get('evidence_ids', []):
            all_evidence_ids.append(eid)
            if eid not in self.bullet_id_lookup:
                errors.append(f"Unknown evidence_id in short: '{eid}'")

        if not all_evidence_ids:
            errors.append("No evidence_ids found — cover letter has no grounded claims")

        # Validate micro_story_id if present
        ms_id = std.get('micro_story_id')
        if ms_id:
            valid_ms_ids = {f.get('id') for f in self.knowledge_base
                            if f.get('type') == 'micro_story'}
            if valid_ms_ids and ms_id not in valid_ms_ids:
                errors.append(f"Unknown micro_story_id: '{ms_id}'")

        # Word count check (standard only)
        std_prose = self._extract_standard_prose(spec)
        std_words = len(std_prose.split())
        if std_words < 100:
            errors.append(f"Standard too short ({std_words} words, min 100)")

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
        # New format
        for para in std.get('paragraphs', []):
            parts.append(para.get('prose', ''))
        # Old format fallback
        parts.append(std.get('opening_prose', ''))
        for para in std.get('body_paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('closer_prose', ''))
        parts.append(spec.get('short', {}).get('prose', ''))
        return ' '.join(p for p in parts if p)

    def _extract_standard_prose(self, spec: Dict) -> str:
        """Extract only standard section prose (not short)"""
        std = spec.get('standard', {})
        parts = []
        for para in std.get('paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('opening_prose', ''))
        for para in std.get('body_paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('closer_prose', ''))
        return ' '.join(p for p in parts if p)

    # =========================================================================
    # Generation (core logic unchanged, prompt is new)
    # =========================================================================

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

        # AI call via Claude Code CLI (same pattern as AIAnalyzer)
        raw_text = self._call_claude_code(prompt)
        if not raw_text:
            print(f"[CoverLetter] Failed to get response from Claude Code CLI")
            return None
        tokens_used = 0  # CLI doesn't report token usage

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
        # New format: flat paragraphs array
        paragraphs = std.get('paragraphs', [])
        if paragraphs:
            return '\n\n'.join(p.get('prose', '') for p in paragraphs if p.get('prose'))
        # Backward compat: old format with opening_prose + body_paragraphs + closer_prose
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

        # Token budget check (shared with AI analyzer)
        budget_config = self.config.get('budget', {})
        budget_limit = budget_config.get('daily_limit', 100000)
        try:
            total_tokens = self.db.get_daily_token_usage()
            if total_tokens > 0:
                print(f"  Today's token usage so far: {total_tokens}")
            if total_tokens >= budget_limit:
                print(f"[CoverLetter] Daily token budget reached ({total_tokens}/{budget_limit}). Skipping.")
                return 0
        except Exception as e:
            print(f"  [WARN] Could not query daily token usage: {e}")
            total_tokens = 0

        print(f"\n[CoverLetter] Generating cover letters for {len(jobs)} jobs...")
        generated = 0

        for i, job in enumerate(jobs):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            ai_score = job.get('ai_score', 0)
            print(f"  [{i+1}/{len(jobs)}] [{ai_score:.1f}] {title} @ {company}")

            try:
                result = self.generate(job['id'])
                if result:
                    generated += 1
            except Exception as e:
                print(f"  [ERROR] {type(e).__name__}: {str(e)[:100]}")
                continue

            # Re-check token budget periodically
            if (i + 1) % 5 == 0:
                try:
                    total_tokens = self.db.get_daily_token_usage()
                    if total_tokens >= budget_limit:
                        print(f"\n[CoverLetter] Token budget reached ({total_tokens}/{budget_limit})")
                        break
                except Exception:
                    pass

        print(f"\n[CoverLetter] Done: {generated}/{len(jobs)} cover letters generated")
        return generated
