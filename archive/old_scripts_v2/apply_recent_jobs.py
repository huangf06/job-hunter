"""
申请最近3天发布的职位
======================

只申请3天内发布的新职位，过滤掉过期职位
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 飞哥信息
PROFILE = {
    "first_name": "Fei",
    "last_name": "Huang",
    "email": "huangf06@gmail.com",
    "phone": "+31612345678",
}


class RecentJobApplyBot:
    """申请最近发布的职位"""
    
    def __init__(self, headless: bool = False, max_days: int = 3):
        self.headless = headless
        self.max_days = max_days
        self.browser = None
        self.context = None
        self.page = None
        self.stats = {"success": 0, "failed": 0, "skipped": 0, "too_old": 0}
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(viewport={"width": 1920, "height": 1080})
        self.page = await self.context.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def delay(self, min_sec=1, max_sec=3):
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    def is_recent_job(self, job: dict) -> bool:
        """检查职位是否在3天内发布"""
        try:
            # 尝试从 added_at 判断
            added_at = job.get("added_at", "")
            if added_at:
                added_date = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
                days_old = (datetime.now() - added_date).days
                return days_old <= self.max_days
            
            # 尝试从 posted_date 判断
            posted = job.get("posted_date", "")
            if posted:
                # 处理各种格式
                if "day" in posted.lower():
                    # 如 "2 days ago"
                    import re
                    match = re.search(r'(\d+)', posted)
                    if match:
                        days = int(match.group(1))
                        return days <= self.max_days
                elif "hour" in posted.lower() or "minute" in posted.lower():
                    return True
                elif "today" in posted.lower() or "just now" in posted.lower():
                    return True
            
            # 默认如果无法判断，假设是新的
            return True
            
        except Exception as e:
            print(f"  Date check error: {e}")
            return True
    
    async def apply_job(self, job: dict) -> bool:
        """申请单个职位"""
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        url = job.get("url", "")
        
        print(f"\n[APPLY] {title[:50]}... @ {company}")
        
        # 检查是否最近发布
        if not self.is_recent_job(job):
            print(f"  [SKIP] Posted more than {self.max_days} days ago")
            self.stats["too_old"] += 1
            return False
        
        try:
            # 打开职位页面
            await self.page.goto(url, timeout=30000)
            await self.delay(3, 5)
            
            # 检查页面是否有效
            if "404" in await self.page.title() or "not found" in (await self.page.content()).lower():
                print(f"  [SKIP] Job page not found (404)")
                self.stats["skipped"] += 1
                return False
            
            # 尝试找外部申请链接
            external_selectors = [
                "a[data-control-name='jobdetails_topcard_external_apply']",
                "a:has-text('Apply on company website')",
                "a:has-text('Visit website')",
                "button:has-text('Apply on company website')",
            ]
            
            external_link = None
            for selector in external_selectors:
                link = await self.page.query_selector(selector)
                if link:
                    external_link = link
                    print(f"  Found external apply link")
                    break
            
            if external_link:
                # 获取外部链接URL
                href = await external_link.get_attribute('href')
                if href:
                    print(f"  External URL: {href[:80]}...")
                    # 在新标签页打开
                    new_page = await self.context.new_page()
                    await new_page.goto(href, timeout=60000)
                    await self.delay(5, 8)
                    
                    # 填写并提交
                    result = await self._fill_and_submit(new_page, company)
                    await new_page.close()
                    return result
            
            # 尝试LinkedIn Easy Apply
            easy_apply = await self.page.query_selector(
                "button[data-control-name='jobdetails_topcard_inapply'], .jobs-apply-button"
            )
            if easy_apply:
                print(f"  Found LinkedIn Easy Apply")
                await easy_apply.click()
                await self.delay(2, 4)
                
                # 填写基本信息
                await self._fill_linkedin_form()
                
                # 尝试提交
                submit = await self.page.query_selector("button:has-text('Submit application')")
                if submit:
                    await submit.click()
                    await self.delay(3, 5)
                    print(f"  [OK] Applied via LinkedIn!")
                    self.stats["success"] += 1
                    return True
            
            print(f"  [SKIP] No apply method found")
            self.stats["skipped"] += 1
            return False
            
        except Exception as e:
            print(f"  [FAIL] {e}")
            self.stats["failed"] += 1
            return False
    
    async def _fill_and_submit(self, page, company: str) -> bool:
        """在公司官网填写并提交"""
        try:
            print(f"  Filling form on {company} website...")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 填写基本信息
            fields = {
                "input[name*='first']": PROFILE["first_name"],
                "input[name*='last']": PROFILE["last_name"],
                "input[type='email']": PROFILE["email"],
                "input[type='tel']": PROFILE["phone"],
            }
            
            for selector, value in fields.items():
                try:
                    el = await page.query_selector(selector)
                    if el:
                        await el.fill(value)
                        await asyncio.sleep(0.3)
                except:
                    pass
            
            # 上传简历
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                resumes = list(OUTPUT_DIR.glob("*.pdf"))
                if resumes:
                    await file_input.set_input_files(str(resumes[0]))
                    await asyncio.sleep(2)
            
            # 尝试提交
            submit_btns = [
                "button[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Send')",
                "button:has-text('Apply')",
            ]
            
            for selector in submit_btns:
                btn = await page.query_selector(selector)
                if btn:
                    visible = await btn.is_visible()
                    enabled = await btn.is_enabled()
                    if visible and enabled:
                        await btn.click()
                        await asyncio.sleep(5)
                        print(f"  [OK] Submitted to {company}!")
                        self.stats["success"] += 1
                        return True
            
            print(f"  [PARTIAL] Form filled, submit button not found")
            self.stats["skipped"] += 1
            return False
            
        except Exception as e:
            print(f"  [ERR] {e}")
            return False
    
    async def _fill_linkedin_form(self):
        """填写LinkedIn表单"""
        try:
            for selector, value in [
                ("input[name*='firstName']", PROFILE["first_name"]),
                ("input[name*='lastName']", PROFILE["last_name"]),
                ("input[name*='email']", PROFILE["email"]),
                ("input[name*='phone']", PROFILE["phone"]),
            ]:
                el = await self.page.query_selector(selector)
                if el:
                    await el.fill(value)
                    await asyncio.sleep(0.3)
        except:
            pass
    
    async def run(self, max_jobs: int = 10):
        """批量运行"""
        print("=" * 70)
        print(f"APPLY RECENT JOBS (Last {self.max_days} days only)")
        print("=" * 70)
        
        # 加载职位
        tracker_file = DATA_DIR / "job_tracker.json"
        with open(tracker_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        all_jobs = [j for j in data.get("jobs", [])
                    if j.get("status") == "new" and j.get("score", 0) >= 6.0]
        
        # 筛选最近发布的
        recent_jobs = [j for j in all_jobs if self.is_recent_job(j)]
        
        print(f"Total high-priority jobs: {len(all_jobs)}")
        print(f"Recent jobs (<= {self.max_days} days): {len(recent_jobs)}")
        print(f"Will process max {max_jobs} jobs\n")
        
        if not recent_jobs:
            print("No recent jobs found. Please run scraper first.")
            return
        
        for i, job in enumerate(recent_jobs[:max_jobs], 1):
            print(f"\n[{i}/{min(len(recent_jobs), max_jobs)}] ", end="")
            await self.apply_job(job)
            await self.delay(5, 10)
        
        # 报告
        print("\n" + "=" * 70)
        print("DONE!")
        print(f"  Success: {self.stats['success']}")
        print(f"  Failed: {self.stats['failed']}")
        print(f"  Skipped: {self.stats['skipped']}")
        print(f"  Too old (> {self.max_days} days): {self.stats['too_old']}")
        print("=" * 70)


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=5, help="Max jobs to apply")
    parser.add_argument("--days", type=int, default=3, help="Max days since posting")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()
    
    async with RecentJobApplyBot(headless=args.headless, max_days=args.days) as bot:
        await bot.run(max_jobs=args.max)


if __name__ == "__main__":
    asyncio.run(main())
