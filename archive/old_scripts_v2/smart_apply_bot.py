"""
智能申请机器人 - 全自动填表投递
===========================

自动完成 LinkedIn Easy Apply 完整流程：
1. 访问职位页面
2. 点击 Easy Apply
3. 填写所有表单字段
4. 上传简历
5. 提交申请
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 飞哥的个人信息
PROFILE = {
    "first_name": "Fei",
    "last_name": "Huang",
    "email": "huangf06@gmail.com",
    "phone": "+31612345678",  # 需要更新为真实号码
    "location": "Amsterdam, Netherlands",
    "linkedin": "https://linkedin.com/in/huangf06",
    "github": "https://github.com/huangf06",
    "summary": """Data Scientist and Machine Learning Engineer with expertise in quantitative research, deep learning, and data engineering. 
M.Sc. in AI from VU Amsterdam. Experienced in building ML models, data pipelines, and trading systems.
Proficient in Python, PyTorch, SQL, and cloud platforms."""
}


class SmartApplyBot:
    """智能申请机器人"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.applied = []
        self.failed = []
    
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
    
    async def delay(self, min_sec=1, max_sec=3):
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    async def smart_type(self, selector: str, text: str):
        """智能输入 - 先清除再输入"""
        try:
            await self.page.click(selector, click_count=3)  # 全选
            await self.page.keyboard.press('Delete')  # 删除
            await asyncio.sleep(0.2)
            for char in text:
                await self.page.type(selector, char, delay=random.randint(30, 80))
                await asyncio.sleep(random.uniform(0.01, 0.03))
        except Exception as e:
            print(f"    Type error: {e}")
    
    async def apply_linkedin_job(self, job: Dict) -> bool:
        """申请单个 LinkedIn 职位"""
        job_id = job.get('id', 'unknown')
        title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        url = job.get('url', '')
        
        print(f"\n[APPLY] {title} @ {company}")
        print(f"  URL: {url}")
        
        try:
            # 访问职位页面
            await self.page.goto(url, timeout=60000)
            await self.delay(4, 6)
            
            # 查找并点击 Easy Apply 按钮
            apply_selectors = [
                "button[data-control-name='jobdetails_topcard_inapply']",
                ".jobs-apply-button",
                "button:has-text('Easy Apply')",
                "button:has-text('Apply')"
            ]
            
            apply_btn = None
            for selector in apply_selectors:
                apply_btn = await self.page.query_selector(selector)
                if apply_btn:
                    break
            
            if not apply_btn:
                print("  [SKIP] No Easy Apply button - external application")
                return False
            
            btn_text = await apply_btn.inner_text()
            if 'Easy' not in btn_text and 'Apply' not in btn_text:
                print(f"  [SKIP] Button text: '{btn_text}' - not Easy Apply")
                return False
            
            print(f"  Clicking '{btn_text.strip()}'...")
            await apply_btn.click()
            await self.delay(3, 5)
            
            # 处理多步表单
            step = 1
            max_steps = 8
            
            while step <= max_steps:
                print(f"  Step {step}: Processing form...")
                
                # 1. 填写联系信息
                await self._fill_contact_info()
                
                # 2. 上传简历
                await self._upload_resume()
                
                # 3. 回答其他问题
                await self._answer_questions()
                
                # 4. 查找下一步/提交按钮
                next_btn = await self._find_next_button()
                
                if not next_btn:
                    print("  No next button found, checking completion...")
                    break
                
                btn_text = await next_btn.inner_text()
                print(f"  Clicking: {btn_text.strip()}")
                
                await next_btn.click()
                await self.delay(3, 5)
                
                # 检查是否提交成功
                if 'submit' in btn_text.lower() or 'review' in btn_text.lower():
                    # 检查成功提示
                    success = await self.page.query_selector(
                        "[aria-label*='Application sent'], .jobs-post-apply__success, h2:has-text('Application sent')"
                    )
                    if success:
                        print("  [SUCCESS] Application submitted!")
                        self.applied.append(job)
                        return True
                
                step += 1
            
            # 检查最终状态
            current_url = self.page.url
            if "apply" not in current_url or "jobs/view" in current_url:
                print("  [SUCCESS] Application likely completed!")
                self.applied.append(job)
                return True
            
            print("  [UNCLEAR] Application status unknown")
            return False
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            self.failed.append(job)
            return False
    
    async def _fill_contact_info(self):
        """填写联系信息"""
        fields = {
            "input[name='firstName']": PROFILE["first_name"],
            "input[name='lastName']": PROFILE["last_name"],
            "input[name='email']": PROFILE["email"],
            "input[name='phone']": PROFILE["phone"],
            "input[name='mobilePhone']": PROFILE["phone"],
            "input[name='location']": PROFILE["location"],
        }
        
        for selector, value in fields.items():
            try:
                field = await self.page.query_selector(selector)
                if field:
                    # 检查是否已填写
                    current = await field.get_attribute('value') or ''
                    if not current:
                        print(f"    Filling: {selector}")
                        await self.smart_type(selector, value)
                        await self.delay(0.5, 1)
            except Exception as e:
                pass
    
    async def _upload_resume(self):
        """上传简历"""
        try:
            # 查找文件上传输入
            file_inputs = await self.page.query_selector_all("input[type='file']")
            
            for file_input in file_inputs:
                # 获取接受的文件类型
                accept = await file_input.get_attribute('accept') or ''
                
                if 'pdf' in accept.lower() or '.pdf' in accept:
                    # 查找简历文件
                    resume_files = list(OUTPUT_DIR.glob("*.pdf"))
                    if resume_files:
                        resume_path = str(resume_files[0])
                        print(f"    Uploading resume: {resume_files[0].name}")
                        await file_input.set_input_files(resume_path)
                        await self.delay(2, 3)
                        return True
        except Exception as e:
            print(f"    Resume upload error: {e}")
        
        return False
    
    async def _answer_questions(self):
        """回答申请表单问题"""
        try:
            # 处理单选按钮（默认选第一个）
            radio_groups = await self.page.query_selector_all(
                "fieldset, [role='radiogroup'], .jobs-easy-apply-form-section"
            )
            
            for group in radio_groups:
                radios = await group.query_selector_all("input[type='radio']")
                if radios and len(radios) > 0:
                    # 选第一个（通常是 Yes 或默认选项）
                    await radios[0].click()
                    await self.delay(0.3, 0.6)
            
            # 处理下拉选择
            selects = await self.page.query_selector_all("select")
            for select in selects:
                options = await select.query_selector_all("option")
                if len(options) > 1:
                    # 选第二个（通常第一个是 placeholder）
                    await options[1].click()
                    await self.delay(0.3, 0.6)
            
            # 处理文本输入（通用问题）
            text_inputs = await self.page.query_selector_all(
                "textarea, input[type='text']:not([name='firstName']):not([name='lastName']):not([name='email']):not([name='phone'])"
            )
            
            for text_input in text_inputs:
                try:
                    # 获取 label 或 placeholder 来判断问题
                    label = await self.page.evaluate(
                        "(el) => { const label = document.querySelector(`label[for='${el.id}']`); return label ? label.innerText : el.placeholder; }",
                        text_input
                    )
                    
                    if label:
                        label_lower = label.lower()
                        if any(x in label_lower for x in ['experience', 'years', 'year']):
                            await self.smart_type(text_input, "3")
                        elif any(x in label_lower for x in ['notice', 'period']):
                            await self.smart_type(text_input, "1 month")
                        elif any(x in label_lower for x in ['salary', 'expectation']):
                            await self.smart_type(text_input, "Negotiable")
                        elif any(x in label_lower for x in ['why', 'motivation']):
                            await self.smart_type(text_input, PROFILE["summary"][:200])
                        else:
                            await self.smart_type(text_input, "N/A")
                        
                        await self.delay(0.3, 0.6)
                except:
                    pass
                    
        except Exception as e:
            print(f"    Question answering error: {e}")
    
    async def _find_next_button(self):
        """查找下一步/提交按钮"""
        selectors = [
            "button[aria-label='Continue to next step']",
            "button[aria-label='Review your application']",
            "button[aria-label='Submit application']",
            "footer button:last-child",
            "button:has-text('Next')",
            "button:has-text('Review')",
            "button:has-text('Submit')",
        ]
        
        for selector in selectors:
            btn = await self.page.query_selector(selector)
            if btn:
                # 检查按钮是否可见和可用
                visible = await btn.is_visible()
                if visible:
                    return btn
        
        return None
    
    async def run(self, max_jobs: int = 3):
        """运行申请流程"""
        print("=" * 70)
        print("SMART APPLY BOT - Full Auto Mode")
        print("=" * 70)
        
        # 加载 Easy Apply 职位
        easy_apply_file = DATA_DIR / "easy_apply_jobs.json"
        if easy_apply_file.exists():
            with open(easy_apply_file, "r", encoding="utf-8") as f:
                jobs = json.load(f)
        else:
            # 从 tracker 加载
            tracker_file = DATA_DIR / "job_tracker.json"
            with open(tracker_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            jobs = [j for j in data.get("jobs", []) 
                    if j.get("status") == "new" and j.get("score", 0) >= 6.0]
        
        print(f"Found {len(jobs)} jobs to process\n")
        
        for i, job in enumerate(jobs[:max_jobs], 1):
            print(f"\n[{i}/{min(len(jobs), max_jobs)}] " + "=" * 50)
            success = await self.apply_linkedin_job(job)
            
            if success:
                # 更新 tracker
                await self._mark_applied(job)
            
            # 随机延迟
            await self.delay(5, 10)
        
        # 报告
        print("\n" + "=" * 70)
        print(f"[DONE] Applied: {len(self.applied)}")
        print(f"[DONE] Failed: {len(self.failed)}")
        print("=" * 70)
    
    async def _mark_applied(self, job: Dict):
        """标记为已申请"""
        try:
            tracker_file = DATA_DIR / "job_tracker.json"
            with open(tracker_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for j in data.get("jobs", []):
                if j.get("id") == job.get("id"):
                    j["status"] = "applied"
                    j["applied_at"] = datetime.now().isoformat()
                    break
            
            with open(tracker_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=3, help="Max jobs to apply")
    parser.add_argument("--visible", action="store_true", help="Show browser")
    args = parser.parse_args()
    
    async with SmartApplyBot(headless=not args.visible) as bot:
        await bot.run(max_jobs=args.max)


if __name__ == "__main__":
    asyncio.run(main())
