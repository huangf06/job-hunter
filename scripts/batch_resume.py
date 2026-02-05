#!/usr/bin/env python3
"""
批量简历生成脚本 - 连接筛选评分和简历生成

从数据库读取高分职位，自动生成定制简历

Usage:
    python scripts/batch_resume.py                    # 显示待处理职位
    python scripts/batch_resume.py --generate         # 生成所有待处理简历
    python scripts/batch_resume.py --generate --top 5 # 只处理前5个高分职位
    python scripts/batch_resume.py --job-id abc123    # 为指定职位生成简历
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase
from job_hunter_v42 import JobHunterV42


class BatchResumeGenerator:
    """批量简历生成器"""

    def __init__(self, min_score: float = 6.0):
        self.db = JobDatabase()
        self.min_score = min_score
        self.hunter = None  # 延迟初始化

    def _init_hunter(self):
        """延迟初始化 JobHunter"""
        if self.hunter is None:
            self.hunter = JobHunterV42()

    def get_pending_jobs(self, limit: int = None) -> list:
        """
        获取待生成简历的职位
        条件：通过筛选 + 评分>=min_score + 未生成简历
        """
        with self.db._get_conn() as conn:
            query = """
                SELECT
                    j.id, j.title, j.company, j.location, j.url, j.description,
                    s.score, s.recommendation, s.matched_keywords
                FROM jobs j
                JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
                JOIN ai_scores s ON j.id = s.job_id AND s.score >= ?
                LEFT JOIN resumes r ON j.id = r.job_id
                WHERE r.job_id IS NULL
                ORDER BY s.score DESC
            """
            if limit:
                query += f" LIMIT {limit}"

            cursor = conn.execute(query, (self.min_score,))
            return [dict(row) for row in cursor.fetchall()]

    def list_pending(self):
        """列出待处理的职位"""
        jobs = self.get_pending_jobs()

        if not jobs:
            print(f"\nNo pending jobs (score >= {self.min_score})")
            return

        print(f"\n=== Jobs Pending Resume Generation ({len(jobs)}) ===\n")
        print(f"{'Score':<6} {'Title':<40} {'Company':<20}")
        print("-" * 70)

        for job in jobs:
            title = job['title'][:38] if len(job['title']) > 38 else job['title']
            company = job['company'][:18] if len(job['company']) > 18 else job['company']
            print(f"{job['score']:<6.1f} {title:<40} {company:<20}")

        print(f"\nUse --generate to create resumes")

    def generate_for_job(self, job: dict) -> dict:
        """Generate resume for a single job"""
        self._init_hunter()

        try:
            result = self.hunter.process_job(
                title=job['title'],
                description=job['description'] or '',
                company=job['company']
            )

            # Save to database
            self._save_resume_record(job['id'], result)

            return {
                'success': True,
                'job_id': job['id'],
                'pdf_path': result['pdf_path']
            }
        except Exception as e:
            print(f"\n[ERROR] Generation failed: {job['title']} @ {job['company']}")
            print(f"  Reason: {e}")
            return {
                'success': False,
                'job_id': job['id'],
                'error': str(e)
            }

    def _save_resume_record(self, job_id: str, result: dict):
        """Save resume record to database"""
        with self.db._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO resumes
                (job_id, role_type, template_version, pdf_path, html_path, generated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                result['role'],
                f"templates/{result['role']}.html",
                result['pdf_path'],
                result['html_path'],
                datetime.now().isoformat()
            ))

    def generate_all(self, limit: int = None, dry_run: bool = False):
        """Batch generate resumes"""
        jobs = self.get_pending_jobs(limit)

        if not jobs:
            print(f"\nNo pending jobs (score >= {self.min_score})")
            return

        print(f"\n=== Batch Resume Generation ===")
        print(f"Pending: {len(jobs)} jobs")

        if dry_run:
            print("\n[DRY RUN] Jobs to be processed:")
            for job in jobs:
                print(f"  - {job['title']} @ {job['company']} (Score: {job['score']})")
            return

        # Start generation
        results = {'success': 0, 'failed': 0}

        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] Processing...")
            result = self.generate_for_job(job)

            if result['success']:
                results['success'] += 1
            else:
                results['failed'] += 1

        # Summary
        print(f"\n{'='*70}")
        print(f"[Done] Success: {results['success']}, Failed: {results['failed']}")

    def generate_by_id(self, job_id: str):
        """Generate resume for a specific job"""
        job = self.db.get_job(job_id)

        if not job:
            print(f"[ERROR] Job not found: {job_id}")
            return

        # Get score info
        with self.db._get_conn() as conn:
            cursor = conn.execute(
                "SELECT score FROM ai_scores WHERE job_id = ?", (job_id,)
            )
            row = cursor.fetchone()
            job['score'] = row['score'] if row else 0

        print(f"\nGenerating resume for: {job['title']} @ {job['company']}")
        self.generate_for_job(job)


def main():
    parser = argparse.ArgumentParser(description='批量简历生成')
    parser.add_argument('--generate', action='store_true', help='生成简历')
    parser.add_argument('--top', type=int, help='只处理前N个高分职位')
    parser.add_argument('--job-id', type=str, help='为指定职位ID生成简历')
    parser.add_argument('--min-score', type=float, default=6.0, help='最低评分阈值')
    parser.add_argument('--dry-run', action='store_true', help='只显示将处理的职位')

    args = parser.parse_args()

    generator = BatchResumeGenerator(min_score=args.min_score)

    if args.job_id:
        generator.generate_by_id(args.job_id)
    elif args.generate:
        generator.generate_all(limit=args.top, dry_run=args.dry_run)
    else:
        generator.list_pending()


if __name__ == "__main__":
    main()
