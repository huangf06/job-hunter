"""
查找 Easy Apply 职位
===================

LinkedIn Easy Apply 职位可以直接自动申请
外部申请需要跳转到公司网站
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

async def check_easy_apply_jobs():
    """检查哪些职位有 Easy Apply"""
    
    # 加载职位
    tracker_file = DATA_DIR / "job_tracker.json"
    with open(tracker_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    jobs = [j for j in data.get("jobs", []) if j.get("status") == "new" and j.get("score", 0) >= 6.0]
    
    print(f"Checking {len(jobs)} high-priority jobs for Easy Apply...\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        
        easy_apply_jobs = []
        external_jobs = []
        
        for job in jobs[:10]:  # 检查前10个
            url = job.get("url", "")
            if not url or "linkedin" not in url:
                continue
            
            try:
                await page.goto(url, timeout=30000)
                await asyncio.sleep(3)
                
                # 检查是否有 Easy Apply 按钮
                easy_apply_btn = await page.query_selector(
                    "button[data-control-name='jobdetails_topcard_inapply'], .jobs-apply-button"
                )
                
                if easy_apply_btn:
                    print(f"[EASY APPLY] {job['title'][:50]}... @ {job['company']}")
                    easy_apply_jobs.append(job)
                else:
                    print(f"[EXTERNAL]   {job['title'][:50]}... @ {job['company']}")
                    external_jobs.append(job)
                    
            except Exception as e:
                print(f"[ERROR] {job['title'][:30]}... - {e}")
        
        await browser.close()
    
    print(f"\n{'='*60}")
    print(f"Easy Apply jobs: {len(easy_apply_jobs)}")
    print(f"External apply jobs: {len(external_jobs)}")
    print(f"{'='*60}")
    
    # 保存 Easy Apply 职位
    if easy_apply_jobs:
        with open(DATA_DIR / "easy_apply_jobs.json", "w", encoding="utf-8") as f:
            json.dump(easy_apply_jobs, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(easy_apply_jobs)} Easy Apply jobs to easy_apply_jobs.json")
    
    return easy_apply_jobs

if __name__ == "__main__":
    asyncio.run(check_easy_apply_jobs())
