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
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass  # dotenv not installed, rely on env vars directly

from anthropic import Anthropic
from db.job_db import JobDatabase, AnalysisResult


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

        self.client = self._init_client()
        self.master_resume = self._load_master_resume()
        self.bullet_library = self._load_bullet_library()

        print(f"[AI Analyzer] Using: {active} ({self.model})")

    def _init_client(self):
        """初始化 API client (Anthropic 或 OpenAI compatible)"""
        if self.provider == "anthropic":
            kwargs = {}
            if self.api_key:
                kwargs['api_key'] = self.api_key
            if self.base_url:
                kwargs['base_url'] = self.base_url
            return Anthropic(**kwargs)
        else:
            # OpenAI-compatible client (for Kimi, etc.)
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("openai package required for Kimi. Run: pip install openai")
            return OpenAI(api_key=self.api_key, base_url=self.base_url)

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
        """加载 bullet library 并提取关键内容供 AI 参考"""
        lib_path = PROJECT_ROOT / "assets" / "bullet_library.yaml"
        if not lib_path.exists():
            return ""

        with open(lib_path, 'r', encoding='utf-8') as f:
            lib = yaml.safe_load(f)

        # Extract structured content for the prompt
        sections = []

        # Personal info
        personal = lib.get('personal_info', {})
        if personal:
            sections.append(f"Name: {personal.get('name', '')}")
            sections.append(f"Location: {personal.get('resume_location', '')}")

        # Certifications
        certs = lib.get('certifications', [])
        if certs:
            cert_lines = []
            for cert in certs:
                cert_lines.append(f"- {cert.get('name', '')} ({cert.get('date', '')})")
            sections.append("Certifications:\n" + "\n".join(cert_lines))

        # Work experiences
        experiences = []
        for key in ['glp_technology', 'independent_investor', 'baiquan_investment',
                     'henan_energy', 'eleme']:
            exp = personal.get(key, {}) if key in str(personal) else lib.get(key, {})
            # Check under personal_info first, then root level
            if not exp:
                # Some experiences are nested under personal_info
                exp = lib.get('personal_info', {}).get(key, {})
            if not exp:
                continue

            company = exp.get('company', exp.get('display_name', key))
            location = exp.get('location', '')
            period = exp.get('period', '')
            titles = exp.get('titles', {})
            default_title = titles.get('default', '') if isinstance(titles, dict) else ''

            bullets = []
            for bullet in exp.get('verified_bullets', []):
                bullets.append(f"  - [{bullet.get('id', '')}] {bullet.get('content', '')}")

            exp_text = f"\n{company} | {location} | {period}\nTitle: {default_title}\nBullets:\n"
            exp_text += "\n".join(bullets)
            experiences.append(exp_text)

        if experiences:
            sections.append("Work Experience:" + "\n".join(experiences))

        # Projects
        projects = lib.get('projects', {})
        if projects:
            proj_lines = []
            for proj_key, proj in projects.items():
                if not isinstance(proj, dict):
                    continue
                title = proj.get('title', proj_key)
                period = proj.get('period', '')
                bullets = []
                for b in proj.get('verified_bullets', []):
                    bullets.append(f"    - [{b.get('id', '')}] {b.get('content', '')}")
                proj_lines.append(f"  {title} ({period})\n" + "\n".join(bullets))
            sections.append("Projects:\n" + "\n".join(proj_lines))

        return "\n\n".join(sections)

    def _build_prompt(self, job: Dict) -> str:
        """构建分析 prompt"""
        prompt_template = self.config.get('prompts', {}).get('analyzer', '')
        if not prompt_template:
            raise ValueError("No analyzer prompt template found in config")

        return prompt_template.format(
            master_resume=self.master_resume[:3000],  # Truncate to save tokens
            bullet_library=self.bullet_library[:4000],
            job_title=job.get('title', ''),
            job_company=job.get('company', ''),
            job_description=job.get('description', '')[:4000]
        )

    def analyze_job(self, job: Dict) -> Optional[AnalysisResult]:
        """分析单个职位: 评分 + 简历定制"""
        job_id = job['id']
        prompt = self._build_prompt(job)

        try:
            # Call different API based on provider
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
                tokens_used = (response.usage.input_tokens + response.usage.output_tokens)
            else:
                # OpenAI-compatible API (Kimi, etc.)
                response = self.client.chat.completions.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.choices[0].message.content
                tokens_used = (response.usage.prompt_tokens + response.usage.completion_tokens)

            # Parse JSON from response
            parsed = self._parse_response(text)
            if not parsed:
                print(f"  [WARN] Failed to parse AI response for {job_id}")
                return None

            scoring = parsed.get('scoring', {})
            tailored = parsed.get('tailored_resume', {})

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
            print(f"  [ERROR] AI analysis failed for {job_id}: {e}")
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
