"""
全自动求职流水线
================

完整的端到端自动化：
1. 登录各平台
2. 搜索职位
3. 分析匹配度
4. 生成定制简历
5. 自动投递
6. 记录追踪

定时运行：每天 9:00-18:00，每3小时一次
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from auto_login_scraper import AutoJobBot, save_jobs
from job_pipeline import JobAnalyzer, ResumeTailor, JobTracker

# 配置
CONFIG = {
    "search_keywords": [
        "Quant Researcher", "Quantitative Analyst", "Algorithmic Trading",
        "Machine Learning Engineer", "Deep Learning Engineer", "Computer Vision",
        "NLP Engineer", "Data Engineer", "LLM Engineer",
        "Python Developer", "Backend Engineer", "Software Engineer"
    ],
    "location": "Netherlands",
    "min_score": 6.0,  # 只投递高匹配度职位
    "max_applications_per_run": 5,  # 每次最多投递5个
    "headless": True,  # 无头模式运行
}


class FullAutoPipeline:
    """全自动流水线"""
    
    def __init__(self):
        self.tracker = JobTracker()
        self.tailor = ResumeTailor()
        self.new_jobs = []
        self.high_priority_jobs = []
    
    async def run(self, dry_run: bool = True):
        """运行完整流程"""
        mode = "[DRY RUN - Test Mode]" if dry_run else "[LIVE MODE - Real Applications]"
        print("=" * 70)
        print(f"🤖 FULL AUTO JOB HUNTER - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"   {mode}")
        print("=" * 70)
        
        # Step 1: 爬取职位
        await self.scrape_jobs()
        
        # Step 2: 分析匹配度
        self.analyze_jobs()
        
        # Step 3: 生成简历
        self.generate_resumes()
        
        # Step 4: 自动投递
        await self.apply_jobs(dry_run=dry_run)
        
        # Step 5: 发送报告
        self.send_report()
        
        print("\n" + "=" * 70)
        print("✅ Pipeline completed!")
        print("=" * 70)
    
    async def scrape_jobs(self):
        """爬取职位"""
        print("\n📡 Step 1: Scraping jobs...")
        
        async with AutoJobBot(headless=CONFIG["headless"]) as bot:
            all_jobs = []
            
            # LinkedIn (需要登录)
            print("\n[LinkedIn] Attempting login...")
            if await bot.linkedin_login():
                print("[LinkedIn] Login successful, searching jobs...")
                jobs = await bot.linkedin_search_jobs(
                    CONFIG["search_keywords"][:4],  # 前4个关键词
                    CONFIG["location"]
                )
                all_jobs.extend(jobs)
            else:
                print("[LinkedIn] Login failed, skipping...")
            
            # IamExpat (无需登录)
            print("\n[IamExpat] Searching jobs...")
            jobs = await bot.iamexpat_search_jobs(CONFIG["search_keywords"][:4])
            all_jobs.extend(jobs)
        
        self.new_jobs = all_jobs
        print(f"\n📊 Total new jobs found: {len(all_jobs)}")
    
    def analyze_jobs(self):
        """分析职位匹配度"""
        print("\n🧠 Step 2: Analyzing job matches...")
        
        added = 0
        high_priority = []
        
        for job in self.new_jobs:
            # 分析匹配度
            analysis = JobAnalyzer.analyze(job)
            
            # 添加到追踪器
            if self.tracker.add_job(job, analysis):
                added += 1
                
                # 收集高优先级职位
                if analysis["score"] >= CONFIG["min_score"]:
                    high_priority.append({
                        **job,
                        "score": analysis["score"],
                        "recommendation": analysis["recommendation"]
                    })
        
        # 按分数排序
        high_priority.sort(key=lambda x: x["score"], reverse=True)
        self.high_priority_jobs = high_priority[:CONFIG["max_applications_per_run"]]
        
        print(f"   Added {added} new jobs to tracker")
        print(f"   High priority jobs (score >= {CONFIG['min_score']}): {len(high_priority)}")
        print(f"   Will apply to top {len(self.high_priority_jobs)}")
    
    def generate_resumes(self):
        """为高优先级职位生成简历"""
        print("\n📄 Step 3: Generating tailored resumes...")
        
        for job in self.high_priority_jobs:
            try:
                html_path = self.tailor.save_tailored_html(job)
                print(f"   ✅ Resume for {job['title'][:40]}... @ {job['company']}")
            except Exception as e:
                print(f"   ❌ Failed: {e}")
    
    async def apply_jobs(self, dry_run: bool = True):
        """自动投递"""
        print("\n🚀 Step 4: Auto-applying to jobs...")
        
        if dry_run:
            print("   [DRY RUN] Applications prepared but not submitted")
            print("   To actually apply, run with --apply flag")
            
            for job in self.high_priority_jobs:
                print(f"\n   📌 {job['title'][:50]}... @ {job['company']}")
                print(f"      Score: {job['score']} | URL: {job['url']}")
                print(f"      [READY] Resume generated, waiting for approval")
        else:
            print("   [LIVE MODE] Submitting real applications!")
            
            from auto_apply_bot import AutoApplyBot
            
            async with AutoApplyBot(headless=False) as bot:
                await bot.apply_jobs(self.high_priority_jobs, max_applications=5)
    
    def send_report(self):
        """发送运行报告"""
        print("\n📧 Step 5: Report")
        
        stats = self.tracker.get_stats()
        
        report = f"""
Job Hunter Auto-Run Report
==========================
Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Stats:
- New jobs found: {len(self.new_jobs)}
- Added to tracker: {len([j for j in self.new_jobs if self.tracker.add_job(j, JobAnalyzer.analyze(j))])}
- High priority: {len(self.high_priority_jobs)}
- Total in tracker: {stats['total_analyzed']}
- Total applied: {stats['total_applied']}

Top Jobs to Apply:
"""
        
        for i, job in enumerate(self.high_priority_jobs[:5], 1):
            report += f"{i}. [{job['score']}] {job['title'][:40]}... @ {job['company']}\n"
        
        print(report)
        
        # 保存报告
        report_file = PROJECT_ROOT / "data" / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n📄 Report saved: {report_file}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Actually submit applications (not dry run)")
    parser.add_argument("--test-apply", action="store_true", help="Test apply bot without submitting")
    args = parser.parse_args()
    
    if args.test_apply:
        # 测试投递功能
        from auto_apply_bot import AutoApplyBot
        
        tracker_file = DATA_DIR / "job_tracker.json"
        with open(tracker_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        jobs_to_apply = [
            j for j in data.get("jobs", [])
            if j.get("score", 0) >= 6.0 and j.get("status") == "new"
        ]
        
        async with AutoApplyBot(headless=False) as bot:
            await bot.apply_jobs(jobs_to_apply[:3], max_applications=3)
    else:
        pipeline = FullAutoPipeline()
        await pipeline.run(dry_run=not args.apply)


if __name__ == "__main__":
    asyncio.run(main())
