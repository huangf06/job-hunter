"""
自动投递机器人
================

自动完成职位申请流程：
1. 访问职位详情页
2. 检测申请方式
3. 填写申请表单
4. 上传简历
5. 提交申请

支持平台：
- LinkedIn Easy Apply
- Indeed Apply
- IamExpat (外部链接处理)
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

from playwright.async_api import async_playwright, Page

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"


class AutoApplyBot:
    """自动投递机器人"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.applied_count = 0
        self.failed_jobs = []
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        
        # 添加 stealth 脚本
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)
        
        self.page = await self.context.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def human_delay(self, min_sec=1, max_sec=3):
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    async def safe_click(self, selector: str, timeout=10000):
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            await self.page.click(selector)
            return True
        except:
            return False
    
    async def type_slowly(self, selector: str, text: str):
        """模拟人类打字"""
        for char in text:
            await self.page.type(selector, char, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.01, 0.05))
    
    # ============================================================
    # LinkedIn Easy Apply
    # ============================================================
    
    async def apply_linkedin(self, job: Dict, resume_path: str) -> bool:
        """申请 LinkedIn 职位"""
        job_url = job.get('url', '')
        if not job_url:
            print(f"[LinkedIn Apply] No URL for job: {job.get('title')}")
            return False
        
        print(f"\n[LinkedIn Apply] {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
        print(f"  URL: {job_url}")
        
        try:
            # 访问职位页面
            await self.page.goto(job_url, timeout=60000)
            await self.human_delay(3, 5)
            
            # 查找 Easy Apply 按钮
            apply_selectors = [
                "button[data-control-name='jobdetails_topcard_inapply']",
                ".jobs-apply-button",
                "[aria-label*='Apply']",
                "button:has-text('Easy Apply')",
                "button:has-text('Apply')"
            ]
            
            apply_btn = None
            for selector in apply_selectors:
                apply_btn = await self.page.query_selector(selector)
                if apply_btn:
                    break
            
            if not apply_btn:
                print("  [INFO] No Easy Apply button - opening external application page")
                # 保存截图供用户查看
                await self.page.screenshot(path=str(DATA_DIR / f"apply_{job.get('id', 'unknown')}.png"))
                print(f"  [INFO] Screenshot saved to data/apply_{job.get('id', 'unknown')}.png")
                # 对于外部申请，我们标记为需要手动处理
                return False
            
            # 点击申请
            print("  Clicking Apply button...")
            await apply_btn.click()
            await self.human_delay(2, 4)
            
            # 处理多步申请表单
            step = 1
            max_steps = 10
            
            while step <= max_steps:
                print(f"  Processing step {step}...")
                
                # 检查是否有下一步/提交按钮
                next_selectors = [
                    "button[aria-label='Continue to next step']",
                    "button[aria-label='Review your application']",
                    "button[aria-label='Submit application']",
                    "button:has-text('Next')",
                    "button:has-text('Review')",
                    "button:has-text('Submit')"
                ]
                
                # 填写表单字段
                await self._fill_linkedin_form()
                
                # 上传简历（如果需要）
                await self._upload_resume_if_needed(resume_path)
                
                # 查找并点击下一步/提交
                next_btn = None
                for selector in next_selectors:
                    next_btn = await self.page.query_selector(selector)
                    if next_btn:
                        break
                
                if not next_btn:
                    print("  No next button found, checking if application is complete...")
                    break
                
                # 检查是否是提交按钮
                btn_text = await next_btn.inner_text()
                is_submit = 'submit' in btn_text.lower() or 'review' in btn_text.lower()
                
                print(f"  Clicking '{btn_text}'...")
                await next_btn.click()
                await self.human_delay(2, 4)
                
                if is_submit:
                    print("  Application submitted!")
                    self.applied_count += 1
                    return True
                
                step += 1
            
            print("  Application flow completed")
            return True
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            self.failed_jobs.append(job)
            return False
    
    async def _fill_linkedin_form(self):
        """填写 LinkedIn 申请表单"""
        # 常见字段填写
        fields = {
            "input[name='firstName']": "Fei",
            "input[name='lastName']": "Huang",
            "input[name='email']": "huangf06@gmail.com",
            "input[name='phone']": "+31 6 12345678",  # 需要更新为真实号码
        }
        
        for selector, value in fields.items():
            try:
                field = await self.page.query_selector(selector)
                if field:
                    await self.type_slowly(selector, value)
                    await self.human_delay(0.5, 1)
            except:
                pass
        
        # 处理选择题（默认选第一个）
        try:
            radio_groups = await self.page.query_selector_all("fieldset, [role='radiogroup']")
            for group in radio_groups:
                first_radio = await group.query_selector("input[type='radio'], [role='radio']")
                if first_radio:
                    await first_radio.click()
                    await self.human_delay(0.5, 1)
        except:
            pass
    
    async def _upload_resume_if_needed(self, resume_path: str):
        """上传简历（如果需要）"""
        try:
            file_input = await self.page.query_selector("input[type='file']")
            if file_input:
                print("  Uploading resume...")
                await file_input.set_input_files(resume_path)
                await self.human_delay(2, 3)
        except:
            pass
    
    # ============================================================
    # Indeed Apply
    # ============================================================
    
    async def apply_indeed(self, job: Dict, resume_path: str) -> bool:
        """申请 Indeed 职位"""
        job_url = job.get('url', '')
        if not job_url:
            return False
        
        print(f"\n[Indeed Apply] {job.get('title', 'Unknown')} @ {job.get('company', 'Unknown')}")
        
        try:
            await self.page.goto(job_url, timeout=60000)
            await self.human_delay(3, 5)
            
            # 查找申请按钮
            apply_btn = await self.page.query_selector(
                "[data-testid='apply-button'], .indeed-apply-button, button:has-text('Apply')"
            )
            
            if not apply_btn:
                print("  [SKIP] No apply button found")
                return False
            
            await apply_btn.click()
            await self.human_delay(3, 5)
            
            # 处理 Indeed 申请表单
            # 通常是一个弹窗或新页面
            print("  Processing Indeed application...")
            
            # 填写基本信息
            await self._fill_indeed_form()
            
            # 上传简历
            await self._upload_resume_if_needed(resume_path)
            
            # 提交
            submit_btn = await self.page.query_selector(
                "button[type='submit'], button:has-text('Submit'), button:has-text('Send')"
            )
            
            if submit_btn:
                await submit_btn.click()
                await self.human_delay(3, 5)
                print("  Application submitted!")
                self.applied_count += 1
                return True
            
            return False
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            self.failed_jobs.append(job)
            return False
    
    async def _fill_indeed_form(self):
        """填写 Indeed 申请表单"""
        fields = {
            "input[name='name']": "Fei Huang",
            "input[name='email']": "huangf06@gmail.com",
            "input[name='phone']": "+31 6 12345678",
        }
        
        for selector, value in fields.items():
            try:
                field = await self.page.query_selector(selector)
                if field:
                    await self.type_slowly(selector, value)
                    await self.human_delay(0.5, 1)
            except:
                pass
    
    # ============================================================
    # 批量申请
    # ============================================================
    
    async def apply_jobs(self, jobs: List[Dict], max_applications: int = 5):
        """批量申请职位"""
        print("=" * 70)
        print("AUTO APPLY BOT")
        print("=" * 70)
        
        for i, job in enumerate(jobs[:max_applications], 1):
            print(f"\n[{i}/{min(len(jobs), max_applications)}] Processing...")
            
            # 从 URL 推断 source
            url = job.get('url', '').lower()
            if 'linkedin' in url:
                source = 'linkedin'
            elif 'indeed' in url:
                source = 'indeed'
            else:
                source = job.get('source', '').lower()
            
            # 找到对应的简历文件
            resume_path = self._find_resume_for_job(job)
            
            if source == 'linkedin':
                await self.apply_linkedin(job, resume_path)
            elif source == 'indeed':
                await self.apply_indeed(job, resume_path)
            else:
                print(f"  [SKIP] Unsupported source: {source}")
            
            # 随机延迟，避免被封
            await self.human_delay(5, 10)
        
        print("\n" + "=" * 70)
        print(f"[OK] Applied: {self.applied_count}")
        print(f"[FAIL] Failed: {len(self.failed_jobs)}")
        print("=" * 70)
    
    def _find_resume_for_job(self, job: Dict) -> str:
        """找到对应职位的简历文件"""
        company = job.get('company', 'unknown').replace(' ', '_')
        title = job.get('title', 'position').replace(' ', '_')[:30]
        
        # 尝试多种文件名格式
        patterns = [
            f"Fei_Huang_{company}_{title}.pdf",
            f"{company}_{title}.pdf",
            f"*_{company}*.pdf",
            f"*_{title}*.pdf",
        ]
        
        for pattern in patterns:
            matches = list(OUTPUT_DIR.glob(pattern))
            if matches:
                return str(matches[0])
        
        # 返回默认简历
        default_resumes = list(OUTPUT_DIR.glob("*.pdf"))
        if default_resumes:
            return str(default_resumes[0])
        
        return ""


async def main():
    """测试自动投递"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Test mode (no actual application)")
    parser.add_argument("--max", type=int, default=3, help="Max applications")
    args = parser.parse_args()
    
    # 加载待申请职位
    tracker_file = DATA_DIR / "job_tracker.json"
    if not tracker_file.exists():
        print("No jobs to apply. Run analysis first.")
        return
    
    with open(tracker_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 筛选高优先级且未申请的职位
    jobs_to_apply = [
        j for j in data.get("jobs", [])
        if j.get("score", 0) >= 6.0 and j.get("status") == "new"
    ]
    
    if not jobs_to_apply:
        print("No high-priority jobs to apply.")
        return
    
    print(f"Found {len(jobs_to_apply)} jobs to apply")
    
    if args.test:
        print("[TEST MODE] No actual applications will be sent")
        for job in jobs_to_apply[:args.max]:
            print(f"  Would apply: {job['title']} @ {job['company']}")
    else:
        async with AutoApplyBot(headless=False) as bot:
            await bot.apply_jobs(jobs_to_apply, args.max)


if __name__ == "__main__":
    asyncio.run(main())
