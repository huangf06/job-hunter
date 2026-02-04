"""
Job Hunter 全自动流程
====================

从爬取到投递的全自动执行
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from fetch_scraper import FetchJobScraper, save_jobs
from job_pipeline import JobAnalyzer, ResumeTailor, JobTracker
from job_parser import JobParser

# 数据目录
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


def scrape_iamexpat_positions():
    """爬取 IamExpat 职位 - 使用 web_fetch"""
    print("=" * 60)
    print("[SCRAPE] Fetching IamExpat jobs via web_fetch")
    print("=" * 60)
    
    search_terms = ["data-scientist", "machine-learning", "data-engineer", "ai-engineer"]
    all_jobs = []
    
    for term in search_terms:
        url = f"https://www.iamexpat.nl/career/jobs-netherlands/{term}"
        print(f"\n[SCRAPE] Fetching: {url}")
        
        # 注意：这里需要使用 web_fetch 工具获取内容
        # 实际调用在下方的主函数中
        print(f"[SCRAPE] Ready to fetch {term}")
    
    return all_jobs


def analyze_and_track_jobs(jobs: list):
    """分析职位并添加到追踪器"""
    print("\n" + "=" * 60)
    print("[ANALYZE] Analyzing job matches")
    print("=" * 60)
    
    tracker = JobTracker()
    added = 0
    
    for job in jobs:
        analysis = JobAnalyzer.analyze(job)
        if tracker.add_job(job, analysis):
            added += 1
            print(f"  [ADDED] {job['title'][:50]}... (Score: {analysis['score']})")
    
    print(f"\n[ANALYZE] Added {added} new jobs to tracker")
    return tracker


def generate_resumes_for_high_priority(tracker: JobTracker, min_score: float = 7.0):
    """为高优先级职位生成简历"""
    print("\n" + "=" * 60)
    print("[GENERATE] Generating tailored resumes")
    print("=" * 60)
    
    high_priority = tracker.get_high_priority_jobs(min_score)
    tailor = ResumeTailor()
    generated = []
    
    print(f"[GENERATE] Found {len(high_priority)} high-priority jobs (score >= {min_score})")
    
    for job in high_priority[:5]:  # 最多生成5个
        if job.get('status') == 'applied':
            continue
            
        print(f"\n  [GENERATE] {job['title']} @ {job['company']}")
        
        try:
            # 生成 HTML
            html_path = tailor.save_tailored_html(job)
            print(f"    HTML: {html_path}")
            
            # 生成 PDF
            pdf_path = generate_pdf(html_path, job)
            if pdf_path:
                print(f"    PDF: {pdf_path}")
                tracker.mark_applied(job['id'], str(pdf_path))
                generated.append({
                    'job': job,
                    'pdf_path': str(pdf_path)
                })
        except Exception as e:
            print(f"    Error: {e}")
    
    print(f"\n[GENERATE] Generated {len(generated)} resumes")
    return generated


def generate_pdf(html_path: Path, job: dict) -> Path:
    """生成 PDF - 使用 Playwright"""
    try:
        from playwright.sync_api import sync_playwright
        
        # 构建文件名
        safe_company = job.get("company", "unknown").replace(" ", "_")
        safe_title = job.get("title", "position").replace(" ", "_")[:30]
        output_name = f"Fei_Huang_{safe_company}_{safe_title}.pdf"
        output_path = OUTPUT_DIR / output_name
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file:///{html_path.resolve()}")
            page.pdf(
                path=str(output_path),
                format="A4",
                margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"}
            )
            browser.close()
        
        return output_path
        
    except Exception as e:
        print(f"    PDF generation error: {e}")
    
    return None


def apply_to_jobs(generated: list, dry_run: bool = True):
    """执行投递"""
    print("\n" + "=" * 60)
    print("[APPLY] Job Application" + (" [DRY RUN]" if dry_run else ""))
    print("=" * 60)
    
    for item in generated:
        job = item['job']
        pdf_path = item['pdf_path']
        
        print(f"\n  [APPLY] {job['title']} @ {job['company']}")
        print(f"    URL: {job.get('url', 'N/A')}")
        print(f"    Resume: {pdf_path}")
        
        if dry_run:
            print(f"    Status: Ready to apply (dry-run mode)")
        else:
            # 实际投递逻辑
            print(f"    Status: Would apply here")
            # TODO: 实现自动投递
    
    print(f"\n[APPLY] Total ready to apply: {len(generated)}")


def run_full_pipeline(dry_run: bool = True):
    """运行完整流程"""
    print("=" * 60)
    print("[PIPELINE] Job Hunter Full Auto Pipeline")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    # 注意：实际爬取需要使用 web_fetch 工具
    # 这里只是流程框架，实际爬取在下面的 main 中处理
    
    print("\n[PIPELINE] Pipeline ready. Use web_fetch to get job data.")
    print("[PIPELINE] Then call analyze_and_track_jobs() with the data.")


def main():
    """主函数 - 用于手动执行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Job Hunter Auto Pipeline")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--min-score", type=float, default=7.0, help="Minimum score for resume generation")
    
    args = parser.parse_args()
    
    run_full_pipeline(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
