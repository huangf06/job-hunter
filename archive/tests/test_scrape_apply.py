#!/usr/bin/env python3
"""
测试自动投递 - 使用 Playwright 爬取并投递
"""

import asyncio
import sys
sys.path.insert(0, 'C:\\Users\\huang\\.openclaw\\workspace\\job-hunter')

from scripts.linkedin_scraper import LinkedInJobScraper
from streamlined_pipeline import process_job

async def test_scrape_and_apply():
    """爬取职位并自动投递"""
    
    print("=" * 60)
    print("TEST: Scrape LinkedIn + Auto-Apply")
    print("=" * 60)
    
    # Step 1: 爬取职位
    print("\n[STEP 1] Scraping LinkedIn jobs...")
    scraper = LinkedInJobScraper(headless=False)
    
    jobs = await scraper.scrape_search_results(
        search_term="data engineer",
        location="Netherlands", 
        max_jobs=3
    )
    
    if not jobs:
        print("[FAIL] No jobs found")
        return
    
    # 筛选有 Easy Apply 的职位
    easy_apply_jobs = [j for j in jobs if j.get("has_easy_apply")]
    print(f"\n[OK] Found {len(easy_apply_jobs)} Easy Apply jobs out of {len(jobs)}")
    
    if not easy_apply_jobs:
        print("[WARN] No Easy Apply jobs found, saving all jobs for manual review")
        scraper.save_jobs(jobs)
        return
    
    # Step 2: 处理第一个 Easy Apply 职位
    job = easy_apply_jobs[0]
    print(f"\n[STEP 2] Processing: {job['title']} @ {job['company']}")
    
    result = process_job(job, auto_apply=True, min_score=6.0)
    
    # 显示结果
    print("\n" + "=" * 60)
    print("FINAL RESULT:")
    print("=" * 60)
    for k, v in result.items():
        print(f"  {k}: {v}")
    
    if result['status'] == 'applied':
        print("\n[OK] Application auto-submitted!")
    elif result['status'] == 'ready_to_apply':
        print("\n[PENDING] Resume generated, manual apply needed")
    elif result['status'] == 'auto_apply_failed':
        print("\n[FAIL] Auto-apply failed")
    
    # 保存所有爬取的职位
    scraper.save_jobs(jobs)

if __name__ == "__main__":
    asyncio.run(test_scrape_and_apply())
