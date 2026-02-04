"""
批量申请 - 无鸟所谓模式
=======================

直接批量申请所有高优先级职位
成功失败都无所谓，反正不投的也不会自己投
"""

import asyncio
import json
import random
from datetime import datetime
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
    "summary": "M.Sc. AI from VU Amsterdam. Experienced in ML, Data Engineering, and Quantitative Research."
}


class BulkApplyBot:
    """批量申请机器人"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.page = None
        self.stats = {"success": 0, "failed": 0, "skipped": 0}
    
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
    
    async def apply_job(self, job: dict) -> bool:
        """申请单个职位 - 包括外部申请"""
        company = job.get("company", "Unknown")
        title = job.get("title", "Unknown")
        url = job.get("url", "")
        
        print(f"\n[APPLY] {title[:50]}... @ {company}")
        
        try:
            # 打开LinkedIn职位页面
            await self.page.goto(url, timeout=30000)
            await self.delay(3, 5)
            
            # 首先尝试找外部申请链接（公司官网）
            external_selectors = [
                "a[data-control-name='jobdetails_topcard_external_apply']",
                "a:has-text('Apply on company website')",
                "a:has-text('Visit website')",
                "a:has-text('External apply')",
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
                # 点击外部链接，会在新标签页打开
                await external_link.click()
                await self.delay(5, 8)
                
                # 等待新标签页加载
                pages = self.context.pages
                if len(pages) > 1:
                    # 切换到新标签页（通常是最后一个）
                    new_page = pages[-1]
                    await new_page.bring_to_front()
                    await self.delay(3, 5)
                    
                    # 在新页面尝试申请
                    result = await self._apply_on_external_page(new_page, company)
                    
                    # 关闭新标签页，回到主页面
                    await new_page.close()
                    return result
                else:
                    # 如果还是同一页，说明在当前页加载了
                    return await self._apply_on_external_page(self.page, company)
            
            # 如果没有外部链接，尝试LinkedIn Easy Apply
            easy_apply_selectors = [
                "button[data-control-name='jobdetails_topcard_inapply']",
                ".jobs-apply-button",
                "button:has-text('Easy Apply')",
            ]
            
            for selector in easy_apply_selectors:
                btn = await self.page.query_selector(selector)
                if btn:
                    print(f"  Found LinkedIn Easy Apply")
                    await btn.click()
                    await self.delay(2, 4)
                    await self._quick_fill()
                    
                    submit_btn = await self.page.query_selector(
                        "button[type='submit'], button:has-text('Submit'), button:has-text('Send application')"
                    )
                    if submit_btn:
                        await submit_btn.click()
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
    
    async def _apply_on_external_page(self, page, company: str) -> bool:
        """在公司官网申请页面填写"""
        try:
            print(f"  On {company} website, filling form...")
            
            # 等待页面加载
            await asyncio.sleep(3)
            
            # 尝试各种申请按钮
            apply_btns = [
                "button:has-text('Apply')",
                "button:has-text('Apply Now')",
                "button:has-text('Start Application')",
                "a:has-text('Apply')",
                "input[type='submit'][value*='Apply']",
            ]
            
            for selector in apply_btns:
                btn = await page.query_selector(selector)
                if btn:
                    visible = await btn.is_visible()
                    if visible:
                        await btn.click()
                        await asyncio.sleep(3)
                        break
            
            # 填写基本信息
            await self._fill_external_form(page)
            
            # 尝试提交
            submit_btns = [
                "button[type='submit']",
                "button:has-text('Submit')",
                "button:has-text('Send')",
                "button:has-text('Continue')",
                "button:has-text('Next')",
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
            
            print(f"  [PARTIAL] Form filled but couldn't submit")
            self.stats["skipped"] += 1
            return False
            
        except Exception as e:
            print(f"  [ERR on external] {e}")
            return False
    
    async def _fill_external_form(self, page):
        """填写外部申请表单"""
        try:
            # 名字
            for sel in ["input[name*='first']", "input[id*='first']", "input[placeholder*='First']"]:
                el = await page.query_selector(sel)
                if el:
                    await el.fill(PROFILE["first_name"])
                    break
            
            # 姓氏
            for sel in ["input[name*='last']", "input[id*='last']", "input[placeholder*='Last']"]:
                el = await page.query_selector(sel)
                if el:
                    await el.fill(PROFILE["last_name"])
                    break
            
            # 邮箱
            for sel in ["input[type='email']", "input[name*='email']", "input[id*='email']"]:
                el = await page.query_selector(sel)
                if el:
                    await el.fill(PROFILE["email"])
                    break
            
            # 电话
            for sel in ["input[type='tel']", "input[name*='phone']", "input[id*='phone']"]:
                el = await page.query_selector(sel)
                if el:
                    await el.fill(PROFILE["phone"])
                    break
            
            # 上传简历
            file_input = await page.query_selector("input[type='file']")
            if file_input:
                resumes = list(OUTPUT_DIR.glob("*.pdf"))
                if resumes:
                    await file_input.set_input_files(str(resumes[0]))
                    await asyncio.sleep(2)
            
            await asyncio.sleep(1)
            
        except Exception as e:
            print(f"    Fill error: {e}")
    
    async def _quick_fill(self):
        """快速填写基本信息"""
        try:
            # 填名字
            for selector in ["input[name*='firstName']", "input[id*='firstName']"]:
                el = await self.page.query_selector(selector)
                if el:
                    await el.fill(PROFILE["first_name"])
                    break
            
            # 填姓氏
            for selector in ["input[name*='lastName']", "input[id*='lastName']"]:
                el = await self.page.query_selector(selector)
                if el:
                    await el.fill(PROFILE["last_name"])
                    break
            
            # 填邮箱
            for selector in ["input[name*='email']", "input[id*='email']", "input[type='email']"]:
                el = await self.page.query_selector(selector)
                if el:
                    await el.fill(PROFILE["email"])
                    break
            
            # 填电话
            for selector in ["input[name*='phone']", "input[id*='phone']", "input[type='tel']"]:
                el = await self.page.query_selector(selector)
                if el:
                    await el.fill(PROFILE["phone"])
                    break
            
            # 上传简历（如果有文件上传）
            file_input = await self.page.query_selector("input[type='file']")
            if file_input:
                resumes = list(OUTPUT_DIR.glob("*.pdf"))
                if resumes:
                    await file_input.set_input_files(str(resumes[0]))
                    await self.delay(2, 3)
            
            await self.delay(1, 2)
            
        except:
            pass
    
    async def run(self, max_jobs: int = 10):
        """批量运行"""
        print("=" * 70)
        print("BULK APPLY - NO WORRIES MODE")
        print("=" * 70)
        
        # 加载职位
        tracker_file = DATA_DIR / "job_tracker.json"
        with open(tracker_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        jobs = [j for j in data.get("jobs", [])
                if j.get("status") == "new" and j.get("score", 0) >= 6.0]
        
        print(f"Found {len(jobs)} high-priority jobs")
        print(f"Will process max {max_jobs} jobs\n")
        
        for i, job in enumerate(jobs[:max_jobs], 1):
            print(f"\n[{i}/{min(len(jobs), max_jobs)}] ", end="")
            await self.apply_job(job)
            await self.delay(5, 10)  # 延迟避免被封
        
        # 报告
        print("\n" + "=" * 70)
        print(f"DONE!")
        print(f"  Success: {self.stats['success']}")
        print(f"  Failed: {self.stats['failed']}")
        print(f"  Skipped: {self.stats['skipped']}")
        print("=" * 70)


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=5, help="Max jobs to apply")
    parser.add_argument("--headless", action="store_true", help="Run headless")
    args = parser.parse_args()
    
    async with BulkApplyBot(headless=not args.headless) as bot:
        await bot.run(max_jobs=args.max)


if __name__ == "__main__":
    asyncio.run(main())
