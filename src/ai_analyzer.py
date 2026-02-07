#!/usr/bin/env python3
"""
AI Job Analyzer - 统一评分与简历定制
=====================================

一次 AI 调用同时完成:
1. 职位匹配评分 (skill_match, experience_fit, growth_potential)
2. 简历内容定制 (bio, experiences, projects, skills)

使用 Claude Opus (via proxy) 进行分析，结果保存到 job_analysis 表。

API keys 从 .env 文件加载。
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

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=True)
except ImportError:
    pass  # dotenv not installed, rely on env vars directly

from anthropic import Anthropic
from src.db.job_db import JobDatabase, AnalysisResult


class AIAnalyzer:
    """AI 驱动的职位分析和简历定制"""

    def __init__(self, config_path: Path = None, model_override: str = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()

        # Determine which model to use
        active = model_override or self.config.get('active_model', 'opus')
        model_config = self.config.get('models', {}).get(active, {})

        if not model_config:
            raise ValueError(f"Model config not found: {active}")

        self.provider = model_config.get('provider', 'anthropic')
        self.model = model_config.get('model', 'anthropic/claude-opus-4-5')
        self.max_tokens = model_config.get('max_tokens', 4096)
        self.temperature = model_config.get('temperature', 0.3)

        # Load API credentials from env
        env_key = model_config.get('env_key', 'ANTHROPIC_API_KEY')
        env_url = model_config.get('env_url', 'ANTHROPIC_BASE_URL')
        self.api_key = os.environ.get(env_key)
        self.base_url = os.environ.get(env_url)
        self.auth_type = model_config.get('auth_type', 'api_key')

        self.client = self._init_client()
        self.master_resume = self._load_master_resume()
        self.bullet_library = self._load_bullet_library()
        self.valid_bullets = self._extract_valid_bullets()  # Set of all valid bullet texts
        self.bullet_id_lookup = self._build_bullet_id_lookup()  # ID -> text

        print(f"[AI Analyzer] Using: {active} ({self.model})")
        print(f"[AI Analyzer] Loaded {len(self.bullet_id_lookup)} bullet IDs for resolution")

    def _init_client(self):
        """初始化 API client (统一使用 Anthropic SDK)"""
        kwargs = {}
        if self.api_key:
            kwargs['api_key'] = self.api_key
        if self.base_url:
            kwargs['base_url'] = self.base_url
        # For proxies that require Bearer auth (e.g. codesome.cn)
        if self.auth_type == 'bearer' and self.api_key:
            kwargs['default_headers'] = {"Authorization": f"Bearer {self.api_key}"}
        return Anthropic(**kwargs)

    def _load_config(self, config_path: Path = None) -> dict:
        """加载 AI 配置"""
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _load_master_resume(self) -> str:
        """加载 master resume HTML 作为参考"""
        resume_path = PROJECT_ROOT / "templates" / "resume_master.html"
        if resume_path.exists():
            with open(resume_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def _load_bullet_library(self) -> str:
        """加载 bullet library，通过 YAML 解析提取结构化信息供 AI 参考"""
        lib_path = PROJECT_ROOT / "assets" / "bullet_library.yaml"
        if not lib_path.exists():
            self._parsed_bullets = {}
            return ""

        try:
            with open(lib_path, 'r', encoding='utf-8') as f:
                self._parsed_bullets = yaml.safe_load(f) or {}

            prompt_settings = self.config.get('prompt_settings', {})
            experience_keys = prompt_settings.get('experience_keys',
                ['glp_technology', 'baiquan_investment', 'eleme', 'henan_energy'])
            project_keys = prompt_settings.get('project_keys',
                ['thesis_uq_rl', 'nlp_projects', 'expedia_recommendation', 'ml4qs'])

            sections = []
            work_exp = self._parsed_bullets.get('work_experience', {})
            projects_data = self._parsed_bullets.get('projects', {})

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
                sections.append("Available bullets:")

                for bullet in exp_data.get('verified_bullets', []):
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bid = bullet.get('id', '')
                        prefix = f"[{bid}] " if bid else ""
                        sections.append(f"  - {prefix}{bullet['content']}")

            # Projects
            sections.append("\n## PROJECTS (you MUST select 1-2 projects)")
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
                        sections.append(f"  - {prefix}{bullet['content']}")

            # Extract v3.0 config blocks for dynamic prompt construction
            self._skill_tiers = self._parsed_bullets.get('skill_tiers', {})
            self._title_options = self._parsed_bullets.get('title_options', {})
            self._bio_constraints = self._parsed_bullets.get('bio_constraints', {})
            self._bio_builder = self._parsed_bullets.get('bio_builder', {})

            return '\n'.join(sections)

        except Exception as e:
            print(f"[WARN] Failed to load bullet library: {e}")
            import traceback
            traceback.print_exc()
            self._parsed_bullets = {}
            self._skill_tiers = {}
            self._title_options = {}
            self._bio_constraints = {}
            self._bio_builder = {}
            return ""

    def _extract_valid_bullets(self) -> set:
        """Extract all valid bullets from parsed bullet library YAML"""
        if not hasattr(self, '_parsed_bullets') or not self._parsed_bullets:
            return set()

        bullets = set()

        # From work experiences
        for key, value in self._parsed_bullets.get('work_experience', {}).items():
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bullets.add(bullet['content'])

        # From projects
        for key, value in self._parsed_bullets.get('projects', {}).items():
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'content' in bullet:
                        bullets.add(bullet['content'])

        return bullets

    def _build_bullet_id_lookup(self) -> Dict[str, str]:
        """Build mapping of bullet ID -> verified text from parsed YAML."""
        lookup = {}
        if not hasattr(self, '_parsed_bullets') or not self._parsed_bullets:
            return lookup

        for key, value in self._parsed_bullets.get('work_experience', {}).items():
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                        lookup[bullet['id']] = bullet['content']

        for key, value in self._parsed_bullets.get('projects', {}).items():
            if isinstance(value, dict) and 'verified_bullets' in value:
                for bullet in value['verified_bullets']:
                    if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                        lookup[bullet['id']] = bullet['content']

        return lookup

    def _build_skill_context(self, job_description: str) -> str:
        """Build dynamic skill context for the AI prompt based on JD."""
        if not self._skill_tiers:
            return "ONLY list skills the candidate actually has."

        lines = ["ONLY list skills the candidate actually has.\n"]
        lines.append("VERIFIED skills (can always include):")

        verified = self._skill_tiers.get('verified', {})
        for category, skills in verified.items():
            lines.append(f"  - {category}: {', '.join(skills)}")

        # Scan JD to activate transferable skills
        jd_lower = job_description.lower()
        transferable = self._skill_tiers.get('transferable', [])
        activated = []
        for item in transferable:
            skill = item.get('skill', '')
            write_when = item.get('write_when', '').lower()
            # Extract meaningful keywords from write_when
            keywords = re.findall(r'\b\w+\b', write_when)
            skip_words = {'jd', 'mentions', 'or', 'but', 'not', 'as', 'primary', 'for', 'when'}
            for kw in keywords:
                if kw in skip_words:
                    continue
                if kw in jd_lower:
                    activated.append(f"{skill} (basis: {item.get('basis', '')})")
                    break

        if activated:
            lines.append("\nTRANSFERABLE skills (include ONLY if JD mentions them):")
            for a in activated:
                lines.append(f"  - {a}")
        else:
            lines.append("\nNo transferable skills activated for this JD.")

        excluded = self._skill_tiers.get('excluded', [])
        if excluded:
            lines.append(f"\nEXCLUDED (NEVER include): {', '.join(excluded)}")

        return '\n'.join(lines)

    def _build_title_context(self) -> str:
        """Build dynamic title options context for the AI prompt."""
        if not self._title_options:
            return "Choose the most relevant title for each experience."

        lines = ["Choose the title for each experience that BEST matches the JD:"]
        for company_key, titles in self._title_options.items():
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

        banned = self._bio_constraints.get('banned_phrases', [])
        if banned:
            lines.append(f"- BANNED phrases in bio: {', '.join(banned)}")

        extra_rules = self._bio_constraints.get('extra_rules', [])
        for rule in extra_rules:
            lines.append(f"- {rule}")

        return '\n'.join(lines)

    def _resolve_bullet_ids(self, tailored: Dict) -> tuple:
        """Resolve bullet IDs to verified text from library.

        Returns (tailored_with_text, errors). Unknown IDs = hard error.
        Also accepts exact text matches for backward compatibility.
        """
        errors = []

        for exp in tailored.get('experiences', []):
            company = exp.get('company', 'Unknown')
            resolved = []
            for bullet in exp.get('bullets', []):
                if bullet in self.bullet_id_lookup:
                    resolved.append(self.bullet_id_lookup[bullet])
                elif bullet in self.valid_bullets:
                    # Backward compat: AI returned exact text from library
                    resolved.append(bullet)
                else:
                    errors.append(f"[{company}] Unknown bullet ID or text: '{bullet[:80]}'")
            exp['bullets'] = resolved

        for proj in tailored.get('projects', []):
            name = proj.get('name', 'Unknown')
            resolved = []
            for bullet in proj.get('bullets', []):
                if bullet in self.bullet_id_lookup:
                    resolved.append(self.bullet_id_lookup[bullet])
                elif bullet in self.valid_bullets:
                    resolved.append(bullet)
                else:
                    errors.append(f"[{name}] Unknown bullet ID or text: '{bullet[:80]}'")
            proj['bullets'] = resolved

        return tailored, errors

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
        if allowed_titles and role_title not in allowed_titles:
            errors.append(f"Bio role_title '{role_title}' not in allowed: {allowed_titles}")

        # Validate & resolve domain claims
        claim_ids = bio_spec.get('domain_claims', [])
        claim_texts = []
        for cid in claim_ids:
            if cid in domain_claims_config:
                claim_texts.append(domain_claims_config[cid]['text'])
            else:
                errors.append(f"Bio domain_claim '{cid}' not in whitelist: {list(domain_claims_config.keys())}")

        # Validate closer
        closer_id = bio_spec.get('closer_id')
        closer_text = ''
        if closer_id and closer_id != 'null':
            if closer_id in closer_options:
                closer_data = closer_options[closer_id]
                if closer_data:
                    closer_text = closer_data.get('text', '')
            else:
                errors.append(f"Bio closer_id '{closer_id}' not in options: {list(closer_options.keys())}")

        if errors:
            return None, errors

        # Assemble bio text
        years = bio_spec.get('years', 6)
        max_years = self._bio_constraints.get('max_years_claim', 6)
        if years > max_years:
            years = max_years

        parts = []

        # Opening: "{Role} with {N} years of experience in {domain1} and {domain2}."
        if claim_texts:
            domain_str = ' and '.join(claim_texts)
            parts.append(f"{role_title} with {years} years of experience in {domain_str}.")
        else:
            parts.append(f"{role_title} with {years} years of experience.")

        # Education
        if bio_spec.get('include_education', True):
            parts.append("M.Sc. in Artificial Intelligence from VU Amsterdam (2025, GPA 8.2/10).")

        # Certification
        if bio_spec.get('include_certification', False):
            parts.append("Databricks Certified Data Engineer Professional.")

        # Closer
        if closer_text:
            company = job.get('company', 'the company')
            closer_text = closer_text.replace('{company}', company)
            parts.append(closer_text)

        return ' '.join(parts), []

    def _build_prompt(self, job: Dict) -> str:
        """构建分析 prompt"""
        prompt_template = self.config.get('prompts', {}).get('analyzer', '')
        if not prompt_template:
            raise ValueError("No analyzer prompt template found in config")

        prompt_settings = self.config.get('prompt_settings', {})
        ai_thresholds = self.config.get('ai_recommendation_thresholds', {})

        master_resume_max = prompt_settings.get('master_resume_max_chars', 3000)
        jd_max = prompt_settings.get('job_description_max_chars', 4000)

        jd_text = job.get('description', '')[:jd_max]

        # Build dynamic context blocks (v3.0)
        skill_context = self._build_skill_context(jd_text)
        title_context = self._build_title_context()
        bio_constraints = self._build_bio_constraints()

        return prompt_template.format(
            master_resume=self.master_resume[:master_resume_max],
            bullet_library=self.bullet_library,
            job_title=job.get('title', ''),
            job_company=job.get('company', ''),
            job_description=jd_text,
            apply_now_threshold=ai_thresholds.get('apply_now', 7),
            apply_threshold=ai_thresholds.get('apply', 5),
            maybe_threshold=ai_thresholds.get('maybe', 3),
            skill_context=skill_context,
            title_context=title_context,
            bio_constraints=bio_constraints,
        )

    def analyze_job(self, job: Dict) -> Optional[AnalysisResult]:
        """分析单个职位: 评分 + 简历定制"""
        job_id = job['id']
        prompt = self._build_prompt(job)

        try:
            # Unified Anthropic SDK format (works for Claude and Kimi Coding)
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
            tokens_used = (response.usage.input_tokens + response.usage.output_tokens)

            # Parse JSON from response
            parsed = self._parse_response(text)
            if not parsed:
                print(f"  [WARN] Failed to parse AI response for {job_id}")
                return None

            scoring = parsed.get('scoring', {})
            tailored = parsed.get('tailored_resume', {})

            # Resolve bullet IDs to verified text (hard reject unknown IDs)
            tailored, bullet_errors = self._resolve_bullet_ids(tailored)
            if bullet_errors:
                for err in bullet_errors:
                    print(f"    [BULLET ERROR] {err}")
                print(f"    [REJECTED] {len(bullet_errors)} unknown bullet(s) — resume will not generate")
                tailored = {}

            # Assemble bio from structured spec (or pass through string/null)
            if tailored:
                bio_spec = tailored.get('bio')
                assembled_bio, bio_errors = self._assemble_bio(bio_spec, job)
                if bio_errors:
                    for err in bio_errors:
                        print(f"    [BIO ERROR] {err}")
                    print(f"    [REJECTED] Bio assembly failed — resume will not generate")
                    tailored = {}
                else:
                    tailored['bio'] = assembled_bio

            result = AnalysisResult(
                job_id=job_id,
                ai_score=scoring.get('overall_score', 0),
                skill_match=scoring.get('skill_match', 0),
                experience_fit=scoring.get('experience_fit', 0),
                growth_potential=scoring.get('growth_potential', 0),
                recommendation=scoring.get('recommendation', 'SKIP'),
                reasoning=scoring.get('reasoning', ''),
                tailored_resume=json.dumps(tailored, ensure_ascii=False),
                model=self.model,
                tokens_used=tokens_used
            )

            return result

        except Exception as e:
            print(f"  [ERROR] AI analysis failed for {job_id}: {ascii(str(e))}")
            return None

    def _parse_response(self, text: str) -> Optional[Dict]:
        """解析 AI 的 JSON 响应"""
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find JSON in response
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            try:
                return json.loads(text[start:end])
            except json.JSONDecodeError:
                pass

        # Try to find JSON in code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        return None

    def analyze_batch(self, min_rule_score: float = None, limit: int = 50) -> int:
        """批量分析职位"""
        threshold = min_rule_score
        if threshold is None:
            threshold = self.config.get('thresholds', {}).get('rule_score_for_ai', 3.0)

        jobs = self.db.get_jobs_needing_analysis(min_rule_score=threshold, limit=limit)
        if not jobs:
            print("[AI Analyzer] No jobs to analyze")
            return 0

        print(f"\n[AI Analyzer] Analyzing {len(jobs)} jobs (model: {self.model})...")
        analyzed = 0
        total_tokens = 0

        for i, job in enumerate(jobs):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            rule_score = job.get('rule_score', 0)
            print(f"  [{i+1}/{len(jobs)}] [{rule_score:.1f}] {title} @ {company}...", end=' ')

            result = self.analyze_job(job)
            if result:
                self.db.save_analysis(result)
                analyzed += 1
                total_tokens += result.tokens_used
                print(f"-> {result.recommendation} ({result.ai_score:.1f})")
            else:
                print("-> FAILED")

            # Rate limiting
            if i < len(jobs) - 1:
                time.sleep(1)

            # Token budget check
            budget_limit = self.config.get('budget', {}).get('daily_limit', 100000)
            if total_tokens >= budget_limit:
                print(f"\n[AI Analyzer] Token budget reached ({total_tokens} tokens)")
                break

        print(f"\n[AI Analyzer] Done: {analyzed}/{len(jobs)} analyzed, {total_tokens} tokens used")
        return analyzed

    def analyze_single(self, job_id: str) -> Optional[AnalysisResult]:
        """分析单个职位 (by ID)"""
        job = self.db.get_job(job_id)
        if not job:
            print(f"[AI Analyzer] Job not found: {job_id}")
            return None

        print(f"[AI Analyzer] Analyzing: {job['title']} @ {job['company']}")
        result = self.analyze_job(job)
        if result:
            self.db.save_analysis(result)
            print(f"  Score: {result.ai_score:.1f} | {result.recommendation}")
            print(f"  Reasoning: {result.reasoning}")
            print(f"  Tokens: {result.tokens_used}")
        return result


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="AI Job Analyzer")
    parser.add_argument('--batch', action='store_true', help='Analyze all pending jobs')
    parser.add_argument('--job', type=str, help='Analyze a single job by ID')
    parser.add_argument('--min-score', type=float, default=None,
                        help='Minimum rule score threshold')
    parser.add_argument('--limit', type=int, default=50,
                        help='Max jobs to analyze in batch')
    parser.add_argument('--model', type=str, default=None,
                        choices=['opus', 'kimi'],
                        help='Model to use: opus (Claude) or kimi')

    args = parser.parse_args()

    analyzer = AIAnalyzer(model_override=args.model)

    if args.job:
        analyzer.analyze_single(args.job)
    elif args.batch:
        analyzer.analyze_batch(min_rule_score=args.min_score, limit=args.limit)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python ai_analyzer.py --batch                    # Use default model from config")
        print("  python ai_analyzer.py --batch --model kimi       # Force Kimi")
        print("  python ai_analyzer.py --batch --model opus       # Force Claude Opus")
        print("  python ai_analyzer.py --job abc123 --model kimi")


if __name__ == "__main__":
    main()
