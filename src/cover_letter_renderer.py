#!/usr/bin/env python3
"""
Cover Letter Renderer — 求职信渲染器
=====================================

从 cover_letters 表获取 spec，渲染为 HTML/PDF + 纯文本。

流程:
1. 从 cover_letters 表获取 spec + assembled text
2. 使用 Jinja2 渲染 cover_letter_template.html
3. 使用 Playwright 转换为 PDF
4. 生成纯文本版本 (TXT)
5. 复制到 ready_to_send/ 目录
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

from src.db.job_db import JobDatabase, CoverLetter


class CoverLetterRenderer:
    """Cover letter 渲染器"""

    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()
        self.template_dir = PROJECT_ROOT / "templates"
        self.output_dir = PROJECT_ROOT / self.config.get('resume', {}).get('output_dir', 'output')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ready_dir = PROJECT_ROOT / "ready_to_send"
        self.ready_dir.mkdir(parents=True, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        self.candidate = self.config.get('resume', {}).get('candidate', {})

    def _load_config(self, config_path: Path = None) -> dict:
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    @staticmethod
    def _safe_filename(text: str) -> str:
        """Convert text to safe filename"""
        safe = re.sub(r'[^\w\s-]', '', text).strip()
        safe = re.sub(r'[\s]+', '_', safe)
        return safe

    def render(self, job_id: str) -> Optional[Dict[str, str]]:
        """Render cover letter for a job (HTML/PDF + TXT)"""
        # Load cover letter record
        cl_record = self.db.get_cover_letter(job_id)
        if not cl_record:
            print(f"[CLRenderer] No cover letter found for job: {job_id}")
            return None

        standard_text = cl_record.get('standard_text', '')
        short_text = cl_record.get('short_text', '')
        if not standard_text:
            print(f"[CLRenderer] Empty standard text for job: {job_id}")
            return None

        # Get job details
        job = self.db.get_job(job_id)
        if not job:
            print(f"[CLRenderer] Job not found: {job_id}")
            return None

        company = job.get('company', 'the company')

        # Build template context
        context = {
            'name': self.candidate.get('name', ''),
            'email': self.candidate.get('email', ''),
            'phone': self.candidate.get('phone', ''),
            'location': self.candidate.get('location', ''),
            'linkedin': self.candidate.get('linkedin', ''),
            'linkedin_display': self.candidate.get('linkedin_display', ''),
            'github': self.candidate.get('github', ''),
            'github_display': self.candidate.get('github_display', ''),
            'date': datetime.now().strftime('%B %d, %Y'),
            'greeting': f'{company} Hiring Team',
            'paragraphs': [p.strip() for p in standard_text.split('\n\n') if p.strip()],
        }

        # Render HTML
        from jinja2 import TemplateNotFound
        try:
            template = self.jinja_env.get_template('cover_letter_template.html')
        except TemplateNotFound:
            print(f"[CLRenderer] Template not found: cover_letter_template.html")
            return None

        html_content = template.render(**context)

        # Generate file paths
        candidate_name = self._safe_filename(self.candidate.get('name', 'Cover_Letter'))
        company_safe = self._safe_filename(company)[:20].rstrip('_')
        job_id_short = job.get('id', 'unknown')[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        tracking_name = f"{candidate_name}_{company_safe}_{job_id_short}_{timestamp}_CL"
        submit_name = f"{candidate_name}_Cover_Letter"

        html_path = self.output_dir / f"{tracking_name}.html"
        pdf_path = self.output_dir / f"{tracking_name}.pdf"
        txt_path = self.output_dir / f"{tracking_name}.txt"

        # Find the resume's submit_dir for this job (place cover letter alongside resume)
        resume_record = self.db.get_resume(job_id)
        if resume_record and resume_record.get('submit_dir'):
            submit_dir = Path(resume_record['submit_dir'])
            # Check if already archived to _applied/ (prefer archived location)
            applied_dir = submit_dir.parent / "_applied" / submit_dir.name
            if applied_dir.exists():
                submit_dir = applied_dir
            elif not submit_dir.exists():
                submit_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Fallback: create new submit folder
            date_prefix = datetime.now().strftime("%Y%m%d")
            base_folder = f"{date_prefix}_{company_safe}"
            submit_dir = self.ready_dir / base_folder
            submit_dir.mkdir(parents=True, exist_ok=True)

        submit_pdf_path = submit_dir / f"{submit_name}.pdf"
        submit_txt_path = submit_dir / f"{submit_name}.txt"

        # Save HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Save TXT (short version for paste)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(short_text)

        # Convert to PDF
        pdf_success = self._html_to_pdf(html_path, pdf_path)

        if pdf_success:
            import shutil
            shutil.copy2(pdf_path, submit_pdf_path)
            shutil.copy2(txt_path, submit_txt_path)
            print(f"  -> CL HTML: {html_path.name}")
            print(f"  -> CL PDF:  {pdf_path.name}")
            print(f"  -> CL TXT:  {txt_path.name}")
            print(f"  -> Send: {submit_dir.name}/{submit_name}.pdf + .txt")
        else:
            import shutil
            shutil.copy2(txt_path, submit_txt_path)
            print(f"  -> CL HTML: {html_path.name} (PDF generation failed)")
            print(f"  -> CL TXT:  {txt_path.name}")
            print(f"  -> Send: {submit_dir.name}/{submit_name}.txt")

        # Update DB record with file paths
        cl = CoverLetter(
            job_id=job_id,
            spec_json=cl_record.get('spec_json', ''),
            custom_requirements=cl_record.get('custom_requirements', ''),
            standard_text=standard_text,
            short_text=short_text,
            html_path=str(html_path),
            pdf_path=str(pdf_path) if pdf_success else '',
            tokens_used=cl_record.get('tokens_used', 0),
        )
        self.db.save_cover_letter(cl)

        return {
            'html_path': str(html_path),
            'pdf_path': str(pdf_path) if pdf_success else None,
            'txt_path': str(txt_path),
            'submit_dir': str(submit_dir),
        }

    def _html_to_pdf(self, html_path: Path, pdf_path: Path) -> bool:
        """Convert HTML to PDF via Playwright"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  [WARN] Playwright not installed. PDF generation skipped.")
            return False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                try:
                    page = browser.new_page()
                    page.goto(html_path.absolute().as_uri())
                    page.pdf(
                        path=str(pdf_path),
                        format='A4',
                        margin={
                            'top': '0.75in',
                            'right': '0.75in',
                            'bottom': '0.75in',
                            'left': '0.75in',
                        },
                        print_background=True
                    )
                finally:
                    browser.close()
            return True

        except Exception as e:
            err_str = str(e)
            if "Executable doesn't exist" in err_str or 'browserType.launch' in err_str:
                print(f"  [WARN] Chromium not installed. Run: playwright install chromium")
            else:
                print(f"  [ERROR] PDF generation failed: {e}")
            return False

    def render_batch(self, min_ai_score: float = None, limit: int = 50) -> int:
        """Batch render cover letters that have specs but no PDF"""
        threshold = min_ai_score
        if threshold is None:
            threshold = self.config.get('thresholds', {}).get('ai_score_generate_resume', 5.0)

        # Find cover letters that need rendering (have spec but no pdf_path)
        with self.db._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.*, cl.spec_json, a.ai_score
                FROM jobs j
                JOIN cover_letters cl ON j.id = cl.job_id
                JOIN job_analysis a ON j.id = a.job_id AND a.ai_score >= ?
                WHERE (cl.pdf_path IS NULL OR cl.pdf_path = '')
                  AND cl.standard_text IS NOT NULL
                  AND cl.standard_text != ''
                ORDER BY a.ai_score DESC
                LIMIT ?
            """, (threshold, limit))
            jobs_with_cl = [dict(row) for row in cursor.fetchall()]

        if not jobs_with_cl:
            print("[CLRenderer] No cover letters need rendering")
            return 0

        print(f"\n[CLRenderer] Rendering {len(jobs_with_cl)} cover letters...")
        rendered = 0

        for i, job in enumerate(jobs_with_cl):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            ai_score = job.get('ai_score', 0)
            print(f"  [{i+1}/{len(jobs_with_cl)}] [{ai_score:.1f}] {title} @ {company}")

            result = self.render(job['id'])
            if result:
                rendered += 1

        print(f"\n[CLRenderer] Done: {rendered}/{len(jobs_with_cl)} cover letters rendered")
        return rendered
