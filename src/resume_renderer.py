#!/usr/bin/env python3
"""
Resume Renderer - 简历渲染器
============================

使用 AI 分析的 tailored_resume JSON 生成 HTML 和 PDF 简历。

流程:
1. 从 job_analysis 表获取 tailored_resume
2. 使用 Jinja2 渲染 base_template.html
3. 使用 Playwright 转换为 PDF
4. 保存记录到 resumes 表
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase, Resume
from src.resume_validator import ResumeValidator


class ResumeRenderer:
    """简历渲染器"""

    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()
        self.template_dir = PROJECT_ROOT / "templates"
        self.output_dir = PROJECT_ROOT / self.config.get('resume', {}).get('output_dir', 'output')
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # Load candidate info
        self.candidate = self.config.get('resume', {}).get('candidate', {})
        self.base_context = self._build_base_context()

        # Initialize validator (v3.0)
        self.validator = ResumeValidator()

    def _load_config(self, config_path: Path = None) -> dict:
        """加载配置"""
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _build_base_context(self) -> dict:
        """构建基础模板上下文 (不变的部分)"""
        edu = self.config.get('resume', {}).get('education', {})
        master = edu.get('master', {})
        bachelor = edu.get('bachelor', {})

        return {
            # Personal info
            'name': self.candidate.get('name', 'Fei Huang'),
            'email': self.candidate.get('email', 'huangf06@gmail.com'),
            'phone': self.candidate.get('phone', '+31 645 038 614'),
            'location': self.candidate.get('location', 'Amsterdam, Netherlands'),
            'linkedin': self.candidate.get('linkedin', 'https://www.linkedin.com/in/huangf06/'),
            'github': self.candidate.get('github', 'https://github.com/huangf06'),
            'linkedin_display': self.candidate.get('linkedin_display', 'linkedin.com/in/huangf06'),
            'github_display': self.candidate.get('github_display', 'github.com/huangf06'),
            'blog_url': self.candidate.get('blog_url', 'https://huangf06.github.io/FeiThink/en/'),

            # Education - Master
            'edu_master_school': master.get('school', 'Vrije Universiteit Amsterdam'),
            'edu_master_location': master.get('location', 'Amsterdam, Netherlands'),
            'edu_master_degree': master.get('degree', 'M.Sc. in Artificial Intelligence'),
            'edu_master_date': master.get('date', 'Sep. 2023 -- Aug. 2025'),
            'edu_master_gpa': master.get('gpa', ''),
            'edu_master_coursework': master.get('coursework', ''),
            'edu_master_thesis': master.get('thesis', ''),

            # Education - Bachelor
            'edu_bachelor_school': bachelor.get('school', 'Tsinghua University'),
            'edu_bachelor_location': bachelor.get('location', 'Beijing, China'),
            'edu_bachelor_degree': bachelor.get('degree', 'B.Eng. in Industrial Engineering'),
            'edu_bachelor_date': bachelor.get('date', 'Sep. 2006 -- Jul. 2010'),
            'edu_bachelor_school_note': bachelor.get('school_note', ''),
            'edu_bachelor_thesis': bachelor.get('thesis', ''),

            'certification': edu.get('certification', ''),

            # Career note (for gap explanation)
            'career_note': 'Career Note: 2019-2023 included independent investing, language learning (English, German), and graduate preparation.',
        }

    def render_resume(self, job_id: str) -> Optional[Dict[str, str]]:
        """渲染单个职位的简历"""
        # Get analysis result
        analysis = self.db.get_analysis(job_id)
        if not analysis:
            print(f"[Renderer] No analysis found for job: {job_id}")
            return None

        tailored_json = analysis.get('tailored_resume', '')
        if not tailored_json:
            print(f"[Renderer] No tailored resume for job: {job_id}")
            return None

        try:
            tailored = json.loads(tailored_json)
        except json.JSONDecodeError as e:
            print(f"[Renderer] Invalid tailored_resume JSON: {e}")
            return None

        # Validate structure before rendering
        is_valid, validation_errors = self._validate_tailored_structure(tailored)
        if not is_valid:
            print(f"[Renderer] Invalid tailored resume structure for job: {job_id}")
            for err in validation_errors:
                print(f"  - {err}")
            return None

        # Get job details for filename
        job = self.db.get_job(job_id)
        if not job:
            print(f"[Renderer] Job not found: {job_id}")
            return None

        # v3.0: Run post-generation validation
        validation = self.validator.validate(tailored, job)
        if not validation.passed:
            print(f"[Renderer] Validation FAILED for job: {job_id}")
            for err in validation.errors:
                print(f"  [ERROR] {err}")
            return None
        if validation.warnings:
            print(f"[Renderer] Validation warnings for job: {job_id}")
            for warn in validation.warnings:
                print(f"  [WARN] {warn}")
        if validation.fixes:
            print(f"[Renderer] Auto-fixes applied: {list(validation.fixes.keys())}")

        # Build template context
        context = self._build_context(tailored, job)

        # Render HTML
        template_name = self.config.get('resume', {}).get('template', 'base_template.html')
        template_name = Path(template_name).name  # Extract filename only

        try:
            template = self.jinja_env.get_template(template_name)
        except Exception as e:
            print(f"[Renderer] Template not found: {template_name}, using fallback")
            fallback = self.config.get('resume', {}).get('fallback', 'resume_master.html')
            fallback = Path(fallback).name
            template = self.jinja_env.get_template(fallback)

        html_content = template.render(**context)

        # v3.0: Post-render QA checks
        qa_issues = self._post_render_qa(html_content)
        if qa_issues:
            print(f"[Renderer] Post-render QA warnings:")
            for issue in qa_issues:
                print(f"  [QA] {issue}")

        # Generate output paths
        company_safe = self._safe_filename(job.get('company', 'unknown')[:20])
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_name = f"Fei_Huang_{company_safe}_{timestamp}"

        html_path = self.output_dir / f"{base_name}.html"
        pdf_path = self.output_dir / f"{base_name}.pdf"

        # Save HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Convert to PDF
        pdf_success = self._html_to_pdf(html_path, pdf_path)

        if pdf_success:
            # Save to database
            resume_record = Resume(
                job_id=job_id,
                role_type=self._detect_role_type(job),
                template_version="ai_v1",
                html_path=str(html_path),
                pdf_path=str(pdf_path)
            )
            self.db.save_resume(resume_record)

            print(f"  -> HTML: {html_path.name}")
            print(f"  -> PDF:  {pdf_path.name}")

            return {
                'html_path': str(html_path),
                'pdf_path': str(pdf_path)
            }
        else:
            print(f"  -> HTML: {html_path.name} (PDF generation failed)")
            return {
                'html_path': str(html_path),
                'pdf_path': None
            }

    def _build_context(self, tailored: Dict, job: Dict) -> Dict:
        """构建完整的模板上下文"""
        context = dict(self.base_context)

        # Bio - optional (null means omit)
        bio = tailored.get('bio')
        if bio:
            company = job.get('company', 'the company')
            bio = bio.replace('[Company]', company).replace('{company}', company)
            context['bio'] = bio
        else:
            context['bio'] = ''

        # Experiences
        experiences = tailored.get('experiences', [])
        context['experiences'] = experiences

        # Projects
        projects = tailored.get('projects', [])
        context['projects'] = projects

        # Skills — filter certification rows, then dedup
        skills = tailored.get('skills', [])
        skills = [s for s in skills if s.get('category', '').lower() not in ('certifications', 'certification')]
        skills = self._dedup_skills(skills)
        context['skills'] = skills

        return context

    def _dedup_skills(self, skills: list) -> list:
        """Remove duplicate skills across categories, keeping first occurrence."""
        seen = set()
        for group in skills:
            items = [s.strip() for s in group['skills_list'].split(',')]
            unique = []
            for item in items:
                base = re.sub(r'\s*\(.*?\)', '', item).strip().lower()
                if base not in seen:
                    seen.add(base)
                    unique.append(item)
            group['skills_list'] = ', '.join(unique)
        return [g for g in skills if g['skills_list'].strip()]

    def _validate_tailored_structure(self, tailored: Dict) -> tuple:
        """Validate AI-generated tailored resume JSON structure.

        Returns:
            (is_valid, errors): tuple of bool and list of error strings
        """
        errors = []

        # Check bio (optional - null or string are both valid)
        bio = tailored.get('bio')
        if bio is not None and not isinstance(bio, str):
            errors.append("'bio' field must be a string or null")

        # Check experiences
        experiences = tailored.get('experiences')
        if not isinstance(experiences, list) or len(experiences) == 0:
            errors.append("Missing or empty 'experiences' list")
        else:
            for i, exp in enumerate(experiences):
                if not isinstance(exp, dict):
                    errors.append(f"Experience {i} is not a dict")
                    continue
                for field in ['company', 'title', 'date']:
                    if not exp.get(field):
                        errors.append(f"Experience {i} missing '{field}'")
                if not isinstance(exp.get('bullets'), list):
                    errors.append(f"Experience {i} missing or invalid 'bullets'")

        # Check projects
        projects = tailored.get('projects')
        if not isinstance(projects, list):
            errors.append("'projects' is not a list")
        elif projects:
            for i, proj in enumerate(projects):
                if not isinstance(proj, dict):
                    errors.append(f"Project {i} is not a dict")
                    continue
                if not proj.get('name'):
                    errors.append(f"Project {i} missing 'name'")
                if not isinstance(proj.get('bullets'), list):
                    errors.append(f"Project {i} missing or invalid 'bullets'")

        # Check skills
        skills = tailored.get('skills')
        if not isinstance(skills, list):
            errors.append("'skills' is not a list")
        elif skills:
            for i, skill in enumerate(skills):
                if not isinstance(skill, dict):
                    errors.append(f"Skill {i} is not a dict")
                    continue
                if not skill.get('category'):
                    errors.append(f"Skill {i} missing 'category'")
                if not skill.get('skills_list'):
                    errors.append(f"Skill {i} missing 'skills_list'")

        return len(errors) == 0, errors

    def _post_render_qa(self, html_content: str) -> list:
        """Post-render quality assurance checks on generated HTML."""
        issues = []

        # Check for inconsistent blog URLs
        blog_urls = re.findall(r'https?://[^"<>\s]+(?:substack|feithink|github\.io/FeiThink)[^"<>\s]*', html_content)
        unique_urls = set(blog_urls)
        if len(unique_urls) > 1:
            issues.append(f"Inconsistent blog URLs found: {unique_urls}")

        # Check certification appears at most 2 times
        cert_count = html_content.lower().count('databricks certified')
        if cert_count > 2:
            issues.append(f"Certification mentioned {cert_count} times (max 2)")

        # Estimate page count (rough: ~3000 chars per page for A4 with this template)
        text_only = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        text_only = re.sub(r'<script[^>]*>.*?</script>', '', text_only, flags=re.DOTALL)
        text_only = re.sub(r'<[^>]+>', '', text_only)
        text_only = re.sub(r'\s+', ' ', text_only).strip()  # collapse whitespace
        est_pages = len(text_only) / 3000
        if est_pages < 0.8:
            issues.append(f"Resume may be too short (~{est_pages:.1f} pages)")
        elif est_pages > 2.5:
            issues.append(f"Resume may be too long (~{est_pages:.1f} pages)")

        # Check for empty bullets
        empty_bullets = re.findall(r'<li>\s*</li>', html_content)
        if empty_bullets:
            issues.append(f"Found {len(empty_bullets)} empty bullet(s) <li></li>")

        # Check for double HTML escaping
        if '&amp;amp;' in html_content or '&amp;lt;' in html_content:
            issues.append("Double HTML escaping detected (e.g., &amp;amp;)")

        return issues

    def _safe_filename(self, name: str) -> str:
        """将字符串转换为安全的文件名"""
        # Remove special characters
        safe = re.sub(r'[^\w\-]', '_', name)
        # Remove consecutive underscores
        safe = re.sub(r'_+', '_', safe)
        # Remove leading/trailing underscores
        safe = safe.strip('_')
        return safe or 'unknown'

    def _detect_role_type(self, job: Dict) -> str:
        """根据职位标题检测角色类型"""
        title = job.get('title', '').lower()

        if any(kw in title for kw in ['ml', 'machine learning', 'ai ', 'deep learning']):
            return 'ml_engineer'
        elif any(kw in title for kw in ['data engineer', 'pipeline', 'etl']):
            return 'data_engineer'
        elif any(kw in title for kw in ['quant', 'trading', 'alpha']):
            return 'quant'
        elif any(kw in title for kw in ['data scientist', 'analytics']):
            return 'data_scientist'
        else:
            return 'general'

    def _html_to_pdf(self, html_path: Path, pdf_path: Path) -> bool:
        """使用 Playwright 将 HTML 转换为 PDF"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  [WARN] Playwright not installed. PDF generation skipped.")
            print("  Run: pip install playwright && playwright install chromium")
            return False

        try:
            pdf_config = self.config.get('resume', {}).get('pdf', {})
            margin = pdf_config.get('margin', {})

            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()

                # Load HTML file
                page.goto(f'file://{html_path.absolute()}')

                # Generate PDF
                page.pdf(
                    path=str(pdf_path),
                    format=pdf_config.get('format', 'A4'),
                    margin={
                        'top': margin.get('top', '0.55in'),
                        'right': margin.get('right', '0.55in'),
                        'bottom': margin.get('bottom', '0.55in'),
                        'left': margin.get('left', '0.55in'),
                    },
                    print_background=pdf_config.get('print_background', True)
                )

                browser.close()

            return True

        except Exception as e:
            print(f"  [ERROR] PDF generation failed: {e}")
            return False

    def render_batch(self, min_ai_score: float = None, limit: int = 50) -> int:
        """批量渲染简历"""
        threshold = min_ai_score
        if threshold is None:
            threshold = self.config.get('thresholds', {}).get('ai_score_generate_resume', 5.0)

        jobs = self.db.get_analyzed_jobs_for_resume(min_ai_score=threshold, limit=limit)
        if not jobs:
            print("[Renderer] No jobs need resume generation")
            return 0

        print(f"\n[Renderer] Generating resumes for {len(jobs)} jobs...")
        rendered = 0

        for i, job in enumerate(jobs):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            ai_score = job.get('ai_score', 0)
            print(f"  [{i+1}/{len(jobs)}] [{ai_score:.1f}] {title} @ {company}")

            result = self.render_resume(job['id'])
            if result:
                rendered += 1

        print(f"\n[Renderer] Done: {rendered}/{len(jobs)} resumes generated")
        return rendered


def main():
    """CLI 入口"""
    import argparse

    parser = argparse.ArgumentParser(description="Resume Renderer")
    parser.add_argument('--batch', action='store_true', help='Render all pending resumes')
    parser.add_argument('--job', type=str, help='Render resume for a single job ID')
    parser.add_argument('--min-score', type=float, default=None,
                        help='Minimum AI score threshold')
    parser.add_argument('--limit', type=int, default=50,
                        help='Max resumes to render in batch')

    args = parser.parse_args()

    renderer = ResumeRenderer()

    if args.job:
        result = renderer.render_resume(args.job)
        if result:
            print(f"\nGenerated files:")
            print(f"  HTML: {result['html_path']}")
            if result.get('pdf_path'):
                print(f"  PDF:  {result['pdf_path']}")
    elif args.batch:
        renderer.render_batch(min_ai_score=args.min_score, limit=args.limit)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python resume_renderer.py --batch")
        print("  python resume_renderer.py --job abc123def456")
        print("  python resume_renderer.py --batch --min-score 6.0 --limit 10")


if __name__ == "__main__":
    main()
