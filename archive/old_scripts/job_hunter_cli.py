"""
Job Hunter CLI - 主控制脚本
============================

一站式职位自动爬取投递系统

Commands:
    scrape          爬取职位
    analyze         分析职位匹配度
    generate        生成定制简历
    apply           执行投递
    daily           运行每日完整流程
    stats           查看统计

Usage:
    python job_hunter_cli.py scrape --platform linkedin --search "data scientist"
    python job_hunter_cli.py analyze --file linkedin_data_scientist_20260201.json
    python job_hunter_cli.py generate --job-id <id>
    python job_hunter_cli.py daily
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 项目路径
PROJECT_ROOT = Path(__file__).parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

sys.path.insert(0, str(SCRIPTS_DIR))

from job_pipeline import JobAnalyzer, ResumeTailor, JobTracker, print_analysis_report


class JobHunterCLI:
    """Job Hunter 命令行界面"""
    
    def __init__(self):
        self.tracker = JobTracker()
        self.tailor = ResumeTailor()
    
    def scrape(self, platform: str, search: str, location: str = "Netherlands", max_jobs: int = 25):
        """爬取职位"""
        print("=" * 60)
        print(f"[SCRAPER] Scraping {platform} for '{search}'")
        print("=" * 60)
        
        cmd = [
            sys.executable,
            str(SCRIPTS_DIR / "playwright_scraper.py"),
            "--platform", platform,
            "--search", search,
            "--location", location,
            "--max-jobs", str(max_jobs)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.returncode == 0
    
    def scrape_all(self):
        """爬取所有平台和关键词"""
        print("=" * 60)
        print("[SCRAPER] Running Full Scrape")
        print("=" * 60)
        
        # 首先尝试 RSS 源
        print("\n[1] Trying RSS sources...")
        try:
            from scripts.rss_scraper import RSSJobScraper, save_jobs
            rss_sources = ["stackoverflow", "indeed_nl"]
            for source in rss_sources:
                jobs = RSSJobScraper.scrape(source)
                if jobs:
                    save_jobs(jobs, source, "data_scientist")
        except Exception as e:
            print(f"RSS scraping failed: {e}")
        
        # 然后尝试 Playwright
        print("\n[2] Trying Playwright scraper...")
        searches = [
            ("linkedin", "data scientist"),
            ("linkedin", "machine learning engineer"),
            ("linkedin", "data engineer"),
            ("iamexpat", "data scientist"),
            ("iamexpat", "machine learning"),
        ]
        
        for platform, search in searches:
            self.scrape(platform, search)
            print()
    
    def analyze(self, filepath: Optional[str] = None):
        """分析职位"""
        print("=" * 60)
        print("[ANALYZER] Analyzing Jobs")
        print("=" * 60)
        
        if filepath:
            target_file = DATA_DIR / filepath
        else:
            # 找到最新的抓取文件
            json_files = sorted(DATA_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
            target_file = json_files[0] if json_files else None
        
        if not target_file or not target_file.exists():
            print("❌ No scrape file found. Run scrape first.")
            return False
        
        print(f"Analyzing: {target_file.name}")
        jobs = JobAnalyzer.analyze_file(target_file)
        
        # 添加到追踪器
        added = 0
        for job in jobs:
            analysis = {"score": job.get("score"), "recommendation": job.get("recommendation")}
            if self.tracker.add_job(job, analysis):
                added += 1
        
        print(f"[OK] Added {added} new jobs to tracker")
        print_analysis_report(jobs)
        
        # 保存分析报告
        report_path = DATA_DIR / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(jobs[:20], f, indent=2, ensure_ascii=False)
        print(f"[REPORT] Report saved: {report_path}")
        
        return True
    
    def generate_resume(self, job_id: Optional[str] = None, company: Optional[str] = None):
        """生成定制简历"""
        print("=" * 60)
        print("[RESUME] Generating Tailored Resume")
        print("=" * 60)
        
        # 获取职位信息
        job = None
        if job_id:
            for j in self.tracker.data["jobs"]:
                if j["id"] == job_id:
                    job = j
                    break
        elif company:
            for j in self.tracker.data["jobs"]:
                if company.lower() in j.get("company", "").lower():
                    job = j
                    break
        
        if not job:
            # 显示高优先级职位供选择
            high_priority = self.tracker.get_high_priority_jobs()
            print("Available high-priority jobs:")
            for i, j in enumerate(high_priority[:5], 1):
                print(f"  {i}. [{j['score']}] {j['title']} @ {j['company']} (ID: {j['id']})")
            return False
        
        print(f"Generating resume for: {job['title']} @ {job['company']}")
        
        # 生成 HTML
        html_path = self.tailor.save_tailored_html(job)
        print(f"[OK] HTML generated: {html_path}")
        
        # 生成 PDF (使用 resume_project 的工具)
        pdf_path = self._generate_pdf(html_path, job)
        if pdf_path:
            print(f"[OK] PDF generated: {pdf_path}")
            # 更新追踪器
            self.tracker.mark_applied(job["id"], str(pdf_path))
            return True
        
        return False
    
    def _generate_pdf(self, html_path: Path, job: Dict) -> Optional[Path]:
        """生成 PDF"""
        try:
            # 使用 Playwright 生成 PDF
            from playwright.sync_api import sync_playwright
            
            # 构建文件名
            safe_company = job.get("company", "unknown").replace(" ", "_")
            safe_title = job.get("title", "position").replace(" ", "_")
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
            print(f"Error generating PDF: {e}")
        
        return None
    
    def apply(self, job_id: Optional[str] = None, dry_run: bool = True, auto: bool = False):
        """执行投递"""
        print("=" * 60)
        print("[APPLY] Job Application")
        print("=" * 60)
        
        if dry_run:
            print("[DRY RUN] No actual applications will be sent")
        
        # 获取待投递的高优先级职位
        high_priority = self.tracker.get_high_priority_jobs()
        
        if job_id:
            jobs_to_apply = [j for j in high_priority if j["id"] == job_id]
        else:
            jobs_to_apply = high_priority[:5]  # 默认投递前5个
        
        if not jobs_to_apply:
            print("No jobs to apply for. Run analyze first.")
            return False
        
        print(f"Applying to {len(jobs_to_apply)} jobs:\n")
        
        # 自动投递模式
        if auto and not dry_run:
            print("[AUTO MODE] Running automated application...")
            from scripts.auto_apply import AutoApplier
            
            applier = AutoApplier()
            results = applier.apply_batch(jobs_to_apply, OUTPUT_DIR)
            
            # 打印报告
            report = applier.generate_report(results)
            print(report)
            
            # 保存报告
            report_path = DATA_DIR / f"apply_report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n[REPORT] Saved to: {report_path}")
            
            # 更新追踪器状态
            for result in results:
                if result.success:
                    self.tracker.mark_applied(result.job_id, "auto_applied")
            
            return True
        
        # 手动模式
        for job in jobs_to_apply:
            print(f"  >> {job['title']} @ {job['company']}")
            print(f"     Score: {job['score']} | URL: {job['url']}")
            
            if not dry_run:
                if auto:
                    # 自动模式：已在 batch 中处理
                    pass
                else:
                    # 手动模式：只生成简历
                    success = self.generate_resume(job_id=job["id"])
                    if success:
                        print(f"     [OK] Resume generated and ready to apply")
                    else:
                        print(f"     [FAIL] Failed to generate resume")
            else:
                print(f"     [DRY RUN] Would generate resume and apply")
            print()
        
        return True
    
    def daily(self, auto_apply: bool = False):
        """运行每日完整流程"""
        print("=" * 60)
        print("[DAILY] Job Hunter Pipeline")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"Auto Apply: {'ENABLED' if auto_apply else 'DISABLED (dry run)'}")
        print("=" * 60)
        print()
        
        # 1. 爬取
        print("Step 1: Scraping jobs...")
        self.scrape_all()
        print()
        
        # 2. 分析
        print("Step 2: Analyzing jobs...")
        self.analyze()
        print()
        
        # 3. 生成高优先级职位的简历
        print("Step 3: Generating resumes for high-priority jobs...")
        high_priority = self.tracker.get_high_priority_jobs()
        generated = 0
        for job in high_priority[:10]:  # 只生成前10个
            if self.generate_resume(job_id=job["id"]):
                generated += 1
        print(f"[OK] Generated {generated} tailored resumes")
        print()
        
        # 4. 投递
        print("Step 4: Applying to jobs...")
        if auto_apply:
            print("[AUTO MODE] Running fully automated application...")
            self.apply(dry_run=False, auto=True)
        else:
            print("[DRY RUN] Review and run with --auto-apply to submit")
            self.apply(dry_run=True)
        print()
        
        # 5. 显示统计
        print("Step 5: Final stats...")
        self.stats()
        
        print("=" * 60)
        print("[DONE] Daily pipeline completed!")
        print("=" * 60)
    
    def stats(self):
        """显示统计"""
        stats = self.tracker.get_stats()
        high_priority = self.tracker.get_high_priority_jobs()
        
        print("=" * 40)
        print("Job Hunter Stats")
        print("=" * 40)
        print(f"  Total analyzed: {stats['total_analyzed']}")
        print(f"  Total applied:  {stats['total_applied']}")
        print(f"  Responses:      {stats['responses']}")
        print(f"  Interviews:     {stats['interviews']}")
        print(f"  Offers:         {stats['offers']}")
        print()
        print(f"  High priority jobs (score >= 6.0): {len(high_priority)}")
        
        if high_priority:
            print("\n  Top 5 jobs to apply:")
            for i, job in enumerate(high_priority[:5], 1):
                status = "[DONE]" if job.get("status") == "applied" else "[TODO]"
                print(f"    {status} [{job['score']}] {job['title']} @ {job['company']}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Job Hunter - Automated Job Search & Apply System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 爬取 LinkedIn 数据科学家职位
  python job_hunter_cli.py scrape --platform linkedin --search "data scientist"
  
  # 分析最新抓取结果
  python job_hunter_cli.py analyze
  
  # 生成特定职位的简历
  python job_hunter_cli.py generate --company "Picnic"
  
  # 运行每日完整流程
  python job_hunter_cli.py daily
  
  # 查看统计
  python job_hunter_cli.py stats
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape jobs from platforms")
    scrape_parser.add_argument("--platform", choices=["linkedin", "iamexpat", "indeed", "all"], default="all")
    scrape_parser.add_argument("--search", default="data scientist")
    scrape_parser.add_argument("--location", default="Netherlands")
    scrape_parser.add_argument("--max-jobs", type=int, default=25)
    
    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze job matches")
    analyze_parser.add_argument("--file", help="Specific file to analyze")
    
    # generate command
    generate_parser = subparsers.add_parser("generate", help="Generate tailored resume")
    generate_parser.add_argument("--job-id", help="Job ID from tracker")
    generate_parser.add_argument("--company", help="Company name")
    
    # apply command
    apply_parser = subparsers.add_parser("apply", help="Apply to jobs")
    apply_parser.add_argument("--job-id", help="Specific job ID")
    apply_parser.add_argument("--no-dry-run", action="store_true", help="Actually apply")
    apply_parser.add_argument("--auto", action="store_true", help="Enable auto-apply mode (browser automation)")
    
    # daily command
    daily_parser = subparsers.add_parser("daily", help="Run daily full pipeline")
    daily_parser.add_argument("--auto-apply", action="store_true", help="Enable automatic application submission")
    
    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics")
    
    # import command
    import_parser = subparsers.add_parser("import", help="Import jobs from file")
    import_parser.add_argument("--file", required=True, help="JSON file to import")
    
    # add command - 手动添加职位
    add_parser = subparsers.add_parser("add", help="Add job manually")
    add_parser.add_argument("--text", help="Job description text")
    add_parser.add_argument("--url", default="", help="Job URL")
    add_parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = JobHunterCLI()
    
    if args.command == "scrape":
        if args.platform == "all":
            cli.scrape_all()
        else:
            cli.scrape(args.platform, args.search, args.location, args.max_jobs)
    
    elif args.command == "analyze":
        cli.analyze(args.file)
    
    elif args.command == "generate":
        cli.generate_resume(args.job_id, args.company)
    
    elif args.command == "apply":
        cli.apply(args.job_id, dry_run=not args.no_dry_run, auto=args.auto)
    
    elif args.command == "daily":
        cli.daily(auto_apply=args.auto_apply)
    
    elif args.command == "stats":
        cli.stats()
    
    elif args.command == "import":
        # 导入职位
        from scripts.rss_scraper import ManualJobImporter
        from job_pipeline import JobAnalyzer
        
        import_path = Path(args.file)
        if not import_path.exists():
            # 尝试在 data 目录查找
            import_path = DATA_DIR / args.file
        
        if import_path.exists():
            jobs = ManualJobImporter.import_from_json(import_path)
            if jobs:
                # 分析并添加到追踪器
                for job in jobs:
                    analysis = JobAnalyzer.analyze(job)
                    cli.tracker.add_job(job, analysis)
                print(f"[IMPORT] Added {len(jobs)} jobs to tracker")
        else:
            print(f"[IMPORT] File not found: {args.file}")
    
    elif args.command == "add":
        # 手动添加职位
        from scripts.job_parser import JobParser
        from job_pipeline import JobAnalyzer
        
        if args.interactive:
            print("[ADD] Interactive mode - paste job description (Ctrl+Z then Enter to finish):")
            lines = []
            try:
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                pass
            text = "\n".join(lines)
        else:
            text = args.text or ""
        
        if text:
            job = JobParser.parse_from_text(text, args.url)
            if job:
                analysis = JobAnalyzer.analyze(job)
                cli.tracker.add_job(job, analysis)
                print(f"[ADD] Added job: {job['title']} @ {job['company']}")
                print(f"       Score: {analysis['score']}, Recommendation: {analysis['recommendation']}")
            else:
                print("[ADD] Failed to parse job from text")
        else:
            print("[ADD] No text provided. Use --text or --interactive")


if __name__ == "__main__":
    main()
