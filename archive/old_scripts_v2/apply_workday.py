"""
Workday 自动申请系统
====================

自动完成 Workday ATS 申请流程：
1. 访问职位页面
2. 点击 Apply
3. 创建账户/登录
4. 填写所有表单
5. 上传简历
6. 提交申请

支持公司：Rabobank、ABN AMRO、ING 等使用 Workday 的大公司
"""

import asyncio
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 飞哥的完整 profile
PROFILE = {
    "first_name": "Fei",
    "last_name": "Huang",
    "email": "huangf06@gmail.com",
    "phone": "+31612345678",
    "country": "Netherlands",
    "city": "Amsterdam",
    "address": "Amsterdam, Netherlands",
    "linkedin": "linkedin.com/in/huangf06",
    "github": "github.com/huangf06",
    "website": "",
    
    # 教育背景
    "education": [
        {
            "school": "Vrije Universiteit Amsterdam",
            "degree": "Master of Science",
            "field": "Artificial Intelligence",
            "start": "2023",
            "end": "2025"
        },
        {
            "school": "Tsinghua University",
            "degree": "Bachelor",
            "field": "Computer Science",
            "start": "2019",
            "end": "2023"
        }
    ],
    
    # 工作经历
    "experience": [
        {
            "company": "GLP Technology",
            "title": "Founding Data Scientist",
            "start": "2024",
            "end": "Present",
            "description": "Built ML models for trading systems and risk analysis"
        },
        {
            "company": "Baiquan Investment",
            "title": "Quant Researcher",
            "start": "2022",
            "end": "2023",
            "description": "Developed quantitative trading strategies"
        }
    ],
    
    # 技能
    "skills": "Python, Machine Learning, Deep Learning, PyTorch, TensorFlow, SQL, Data Engineering, Quantitative Analysis, NLP, Computer Vision",
    
    # 简介
    "summary": """Data Scientist and Machine Learning Engineer with expertise in quantitative research, deep learning, and data engineering. 

M.Sc. in AI from VU Amsterdam with thesis on Uncertainty Quantification in Deep Reinforcement Learning. 

Experienced in building ML models, data pipelines, and trading systems. Proficient in Python, PyTorch, SQL, and cloud platforms.""",
    
    # 动机信模板
    "cover_letter": """Dear Hiring Manager,

I am writing to express my strong interest in the {position} position at {company}. With my background in AI and quantitative research, I am confident I can contribute significantly to your team.

My experience includes:
- Building ML models for production trading systems at GLP Technology
- Quantitative research and strategy development at Baiquan Investment  
- M.Sc. in AI from VU Amsterdam with focus on Deep Learning
- Strong programming skills in Python, PyTorch, and SQL

I am particularly excited about {company}'s innovative approach and would welcome the opportunity to discuss how my skills align with your needs.

Thank you for your consideration.

Best regards,
Fei Huang"""
}


class WorkdayApplyBot:
    """Workday 自动申请机器人"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.applied_jobs = []
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
    
    async def smart_type(self, selector: str, text: str, clear_first=True):
        """智能输入"""
        try:
            if clear_first:
                await self.page.click(selector, click_count=3)
                await self.page.keyboard.press('Delete')
                await asyncio.sleep(0.2)
            
            for char in text:
                await self.page.type(selector, char, delay=random.randint(30, 80))
                await asyncio.sleep(random.uniform(0.01, 0.03))
        except Exception as e:
            print(f"    Type error on {selector}: {e}")
    
    async def apply_job(self, job_url: str, company: str, position: str) -> bool:
        """申请单个 Workday 职位"""
        print(f"\n{'='*60}")
        print(f"[APPLY] {position} @ {company}")
        print(f"{'='*60}")
        
        try:
            # 1. 访问职位页面
            print("\n[Step 1] Opening job page...")
            await self.page.goto(job_url, timeout=60000)
            await self.delay(4, 6)
            
            # 2. 查找外部申请链接
            print("[Step 2] Looking for external apply link...")
            external_url = await self._find_external_apply_link()
            
            if external_url:
                print(f"  Found external link: {external_url[:80]}...")
                await self.page.goto(external_url, timeout=60000)
                await self.delay(5, 8)
            
            # 3. 点击 Apply 按钮
            print("[Step 3] Looking for Apply button...")
            apply_btn = await self._find_apply_button()
            if not apply_btn:
                print("  [ERROR] Apply button not found")
                # 保存截图调试
                await self.page.screenshot(path=str(DATA_DIR / f"debug_{company}.png"))
                print(f"  Screenshot saved to data/debug_{company}.png")
                return False
            
            await apply_btn.click()
            await self.delay(3, 5)
            
            # 3. 创建账户或登录
            print("[Step 3] Handling account creation...")
            await self._handle_account_creation()
            
            # 4. 填写申请表单（多页）
            print("[Step 4] Filling application form...")
            await self._fill_application_form(company, position)
            
            # 5. 提交
            print("[Step 5] Submitting application...")
            success = await self._submit_application()
            
            if success:
                print(f"\n[SUCCESS] Application submitted for {position} @ {company}")
                self.applied_jobs.append({
                    "company": company,
                    "position": position,
                    "url": job_url,
                    "applied_at": datetime.now().isoformat()
                })
                return True
            else:
                print(f"\n[FAILED] Could not submit application")
                self.failed_jobs.append({"company": company, "position": position, "url": job_url})
                return False
                
        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()
            self.failed_jobs.append({"company": company, "position": position, "url": job_url})
            return False
    
    async def _find_external_apply_link(self) -> Optional[str]:
        """查找外部申请链接（从 LinkedIn 跳转到公司申请系统）"""
        try:
            # 查找 "Apply" 或 "Visit website" 链接
            external_selectors = [
                "a[href*='rabobank.wd3']",
                "a[href*='workday.com']",
                "a[href*='myworkdayjobs.com']",
                "a[href*='careers']",
                "a[data-control-name='jobdetails_topcard_external_apply']",
                "a:has-text('Apply on company website')",
                "a:has-text('Visit website')",
                "a:has-text('External apply')",
            ]
            
            for selector in external_selectors:
                link = await self.page.query_selector(selector)
                if link:
                    href = await link.get_attribute('href')
                    if href:
                        # 处理相对链接
                        if href.startswith('/'):
                            href = f"https://www.linkedin.com{href}"
                        return href
            
            # 如果没找到，检查页面上的所有链接
            all_links = await self.page.query_selector_all("a[href*='apply'], a[href*='careers']")
            for link in all_links:
                href = await link.get_attribute('href')
                if href and ('workday' in href or 'apply' in href.lower()):
                    return href
            
            return None
            
        except Exception as e:
            print(f"  Error finding external link: {e}")
            return None
    
    async def _find_apply_button(self):
        """查找 Apply 按钮"""
        selectors = [
            "button:has-text('Apply')",
            "button:has-text('Apply Now')",
            "button:has-text('Apply for Job')",
            "a:has-text('Apply')",
            "[data-automation-id='applyButton']",
            "button[data-apply-button]",
            "button[aria-label*='Apply']",
        ]
        
        for selector in selectors:
            btn = await self.page.query_selector(selector)
            if btn:
                visible = await btn.is_visible()
                if visible:
                    return btn
        
        # 如果没找到，可能是已经加载了申请页面
        current_url = self.page.url
        if "apply" in current_url.lower():
            print("  Already on application page")
            return None
        
        return None
    
    async def _handle_account_creation(self):
        """处理账户创建/登录"""
        # 检查是否在登录/创建账户页面
        current_url = self.page.url
        
        if "signin" in current_url.lower() or "login" in current_url.lower():
            print("  On login page, creating new account...")
            
            # 查找创建账户链接
            create_account_links = [
                "a:has-text('Create Account')",
                "a:has-text('Sign Up')",
                "a:has-text('Register')",
                "button:has-text('Create Account')",
            ]
            
            for selector in create_account_links:
                link = await self.page.query_selector(selector)
                if link:
                    await link.click()
                    await self.delay(2, 4)
                    break
        
        # 填写账户信息
        await self._fill_account_info()
    
    async def _fill_account_info(self):
        """填写账户基本信息"""
        fields = {
            "input[name*='email']": PROFILE["email"],
            "input[name*='firstName']": PROFILE["first_name"],
            "input[name*='lastName']": PROFILE["last_name"],
            "input[name*='password']": "TempPass123!",  # 临时密码
            "input[name*='confirmPassword']": "TempPass123!",
        }
        
        for selector, value in fields.items():
            try:
                field = await self.page.query_selector(selector)
                if field:
                    print(f"  Filling: {selector}")
                    await self.smart_type(selector, value)
                    await self.delay(0.5, 1)
            except:
                pass
        
        # 点击继续/创建账户
        continue_btn = await self.page.query_selector(
            "button:has-text('Continue'), button:has-text('Create Account'), button:has-text('Next')"
        )
        if continue_btn:
            await continue_btn.click()
            await self.delay(3, 5)
    
    async def _fill_application_form(self, company: str, position: str):
        """填写申请表单（处理多页）"""
        max_pages = 10
        page_num = 1
        
        while page_num <= max_pages:
            print(f"\n  [Page {page_num}] Filling form...")
            
            # 填写联系信息
            await self._fill_contact_info()
            
            # 填写经历
            await self._fill_experience()
            
            # 填写教育
            await self._fill_education()
            
            # 上传简历
            await self._upload_resume()
            
            # 回答问题
            await self._answer_questions(company, position)
            
            # 查找下一步/提交按钮
            next_btn = await self._find_next_or_submit_button()
            
            if not next_btn:
                print("  No next button found, checking if complete...")
                break
            
            btn_text = await next_btn.inner_text()
            print(f"  Clicking: {btn_text.strip()}")
            
            await next_btn.click()
            await self.delay(3, 5)
            
            # 检查是否提交成功或进入新页面
            if "submit" in btn_text.lower() or "review" in btn_text.lower():
                break
            
            page_num += 1
    
    async def _fill_contact_info(self):
        """填写联系信息"""
        fields = {
            "input[name*='firstName']": PROFILE["first_name"],
            "input[name*='lastName']": PROFILE["last_name"],
            "input[name*='email']": PROFILE["email"],
            "input[name*='phone']": PROFILE["phone"],
            "input[name*='address']": PROFILE["address"],
            "input[name*='city']": PROFILE["city"],
            "select[name*='country']": PROFILE["country"],
            "input[name*='linkedin']": PROFILE["linkedin"],
            "input[name*='website']": PROFILE["website"],
        }
        
        for selector, value in fields.items():
            try:
                field = await self.page.query_selector(selector)
                if field:
                    tag = await field.evaluate("el => el.tagName")
                    if tag.lower() == "select":
                        await field.select_option(value)
                    else:
                        await self.smart_type(selector, value)
                    await self.delay(0.3, 0.6)
            except:
                pass
    
    async def _fill_experience(self):
        """填写工作经历"""
        try:
            # 查找添加经历按钮
            add_exp_btn = await self.page.query_selector(
                "button:has-text('Add Experience'), button:has-text('Add Work Experience'), button[aria-label*='Add Experience']"
            )
            
            if add_exp_btn:
                for exp in PROFILE["experience"]:
                    await add_exp_btn.click()
                    await self.delay(1, 2)
                    
                    # 填写经历详情
                    fields = {
                        "input[name*='company']": exp["company"],
                        "input[name*='title']": exp["title"],
                        "input[name*='start']": exp["start"],
                        "input[name*='end']": exp["end"],
                        "textarea[name*='description']": exp["description"],
                    }
                    
                    for selector, value in fields.items():
                        try:
                            field = await self.page.query_selector(selector)
                            if field:
                                await self.smart_type(selector, value, clear_first=False)
                                await self.delay(0.3, 0.6)
                        except:
                            pass
                    
                    # 保存
                    save_btn = await self.page.query_selector("button:has-text('Save'), button:has-text('Add')")
                    if save_btn:
                        await save_btn.click()
                        await self.delay(1, 2)
        except:
            pass
    
    async def _fill_education(self):
        """填写教育背景"""
        try:
            add_edu_btn = await self.page.query_selector(
                "button:has-text('Add Education'), button:has-text('Add School')"
            )
            
            if add_edu_btn:
                for edu in PROFILE["education"]:
                    await add_edu_btn.click()
                    await self.delay(1, 2)
                    
                    fields = {
                        "input[name*='school']": edu["school"],
                        "input[name*='degree']": edu["degree"],
                        "input[name*='field']": edu["field"],
                        "input[name*='start']": edu["start"],
                        "input[name*='end']": edu["end"],
                    }
                    
                    for selector, value in fields.items():
                        try:
                            field = await self.page.query_selector(selector)
                            if field:
                                await self.smart_type(selector, value, clear_first=False)
                                await self.delay(0.3, 0.6)
                        except:
                            pass
                    
                    save_btn = await self.page.query_selector("button:has-text('Save'), button:has-text('Add')")
                    if save_btn:
                        await save_btn.click()
                        await self.delay(1, 2)
        except:
            pass
    
    async def _upload_resume(self):
        """上传简历"""
        try:
            file_input = await self.page.query_selector("input[type='file']")
            if file_input:
                # 查找简历文件
                resume_files = list(OUTPUT_DIR.glob("*.pdf"))
                if resume_files:
                    resume_path = str(resume_files[0])
                    print(f"  Uploading resume: {resume_files[0].name}")
                    await file_input.set_input_files(resume_path)
                    await self.delay(2, 3)
        except Exception as e:
            print(f"  Resume upload error: {e}")
    
    async def _answer_questions(self, company: str, position: str):
        """回答申请问题"""
        try:
            # 查找所有文本输入（不包括已填写的）
            textareas = await self.page.query_selector_all("textarea")
            
            for textarea in textareas:
                try:
                    # 获取 label 或 placeholder
                    label = await self.page.evaluate(
                        """(el) => {
                            const label = document.querySelector(`label[for='${el.id}']`);
                            return label ? label.innerText : el.placeholder;
                        }""",
                        textarea
                    )
                    
                    if label:
                        label_lower = label.lower()
                        
                        if any(x in label_lower for x in ['cover', 'letter', 'motivation']):
                            # 生成动机信
                            cover_letter = PROFILE["cover_letter"].format(
                                company=company,
                                position=position
                            )
                            await self.smart_type(textarea, cover_letter, clear_first=False)
                        
                        elif any(x in label_lower for x in ['why', 'interest', 'reason']):
                            await self.smart_type(textarea, PROFILE["summary"][:300], clear_first=False)
                        
                        elif any(x in label_lower for x in ['experience', 'relevant']):
                            await self.smart_type(textarea, PROFILE["experience"][0]["description"], clear_first=False)
                        
                        await self.delay(0.5, 1)
                except:
                    pass
            
            # 处理单选问题
            radio_groups = await self.page.query_selector_all("fieldset, [role='radiogroup']")
            for group in radio_groups:
                radios = await group.query_selector_all("input[type='radio']")
                if radios:
                    # 选第一个（通常是 Yes 或默认选项）
                    await radios[0].click()
                    await self.delay(0.3, 0.6)
            
            # 处理下拉选择
            selects = await self.page.query_selector_all("select")
            for select in selects:
                options = await select.query_selector_all("option")
                if len(options) > 1:
                    # 选第二个（跳过 placeholder）
                    await options[1].click()
                    await self.delay(0.3, 0.6)
                    
        except Exception as e:
            print(f"  Question answering error: {e}")
    
    async def _find_next_or_submit_button(self):
        """查找下一步或提交按钮"""
        selectors = [
            "button:has-text('Next')",
            "button:has-text('Continue')",
            "button:has-text('Save and Continue')",
            "button:has-text('Review')",
            "button:has-text('Submit')",
            "button:has-text('Submit Application')",
            "button[type='submit']",
        ]
        
        for selector in selectors:
            btn = await self.page.query_selector(selector)
            if btn:
                visible = await btn.is_visible()
                enabled = await btn.is_enabled()
                if visible and enabled:
                    return btn
        
        return None
    
    async def _submit_application(self) -> bool:
        """提交申请"""
        try:
            # 查找提交按钮
            submit_btn = await self.page.query_selector(
                "button:has-text('Submit'), button:has-text('Submit Application'), button[type='submit']"
            )
            
            if submit_btn:
                await submit_btn.click()
                await self.delay(5, 8)
                
                # 检查成功提示
                success_indicators = [
                    "Application submitted",
                    "Thank you for applying",
                    "Application received",
                    "Success",
                    "Confirmation"
                ]
                
                page_text = await self.page.content()
                for indicator in success_indicators:
                    if indicator.lower() in page_text.lower():
                        return True
                
                # 检查 URL 变化
                current_url = self.page.url
                if "confirmation" in current_url.lower() or "success" in current_url.lower():
                    return True
                
                return False
            
            return False
            
        except Exception as e:
            print(f"  Submit error: {e}")
            return False
    
    async def run_test(self):
        """测试运行 - 申请第一个高优先级职位"""
        # 加载职位
        tracker_file = DATA_DIR / "job_tracker.json"
        with open(tracker_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        jobs = [j for j in data.get("jobs", [])
                if j.get("status") == "new" and j.get("score", 0) >= 6.0]
        
        if not jobs:
            print("No jobs to apply")
            return
        
        # 申请第一个
        job = jobs[0]
        await self.apply_job(
            job_url=job["url"],
            company=job["company"],
            position=job["title"]
        )
        
        # 报告
        print(f"\n{'='*60}")
        print(f"Applied: {len(self.applied_jobs)}")
        print(f"Failed: {len(self.failed_jobs)}")
        print(f"{'='*60}")


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", help="Job URL")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--position", help="Position title")
    parser.add_argument("--test", action="store_true", help="Test mode (apply first job in tracker)")
    parser.add_argument("--visible", action="store_true", help="Show browser")
    args = parser.parse_args()
    
    async with WorkdayApplyBot(headless=not args.visible) as bot:
        if args.test:
            await bot.run_test()
        elif args.url and args.company and args.position:
            await bot.apply_job(args.url, args.company, args.position)
        else:
            print("Usage:")
            print("  python apply_workday.py --test --visible")
            print("  python apply_workday.py --url 'https://...' --company 'Rabobank' --position 'Data Scientist'")


if __name__ == "__main__":
    asyncio.run(main())
