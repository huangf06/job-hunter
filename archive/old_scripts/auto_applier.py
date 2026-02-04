"""
LinkedIn 自动投递模块 - 使用已保存状态
=========================================

利用 LinkedIn "Remember me" 功能，避免重复登录
"""

import json
import re
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class LinkedInAutoApplier:
    """LinkedIn 自动投递器"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.credentials = self._load_credentials()
        self.state_file = Path(__file__).parent / "linkedin_state.json"
    
    def _load_credentials(self) -> dict:
        """加载 LinkedIn 登录信息"""
        config_paths = [
            Path(__file__).parent / "config" / "credentials.json",
            Path(__file__).parent / "credentials.json",
        ]
        
        for path in config_paths:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        
        raise FileNotFoundError("LinkedIn credentials not found")
    
    def apply(self, job: dict, resume_path: Path) -> bool:
        """自动投递职位"""
        job_url = job.get('url')
        if not job_url:
            print("[AUTO_APPLY] No job URL provided")
            return False
        
        if 'linkedin.com' not in job_url:
            print(f"[AUTO_APPLY] Not a LinkedIn URL: {job_url}")
            return False
        
        print(f"[AUTO_APPLY] Starting application for {job.get('company')}")
        
        try:
            with sync_playwright() as p:
                return self._run_application(p, job_url, resume_path)
        except Exception as e:
            print(f"[AUTO_APPLY] Error: {e}")
            return False
    
    def _run_application(self, p, job_url: str, resume_path: Path) -> bool:
        """执行投递流程"""
        
        # 尝试加载已保存的状态
        context = None
        if self.state_file.exists():
            try:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    storage_state=str(self.state_file),
                    viewport={'width': 1280, 'height': 900}
                )
                print("[AUTO_APPLY] Loaded saved session")
            except Exception as e:
                print(f"[AUTO_APPLY] Could not load saved state: {e}")
                context = None
        
        # 如果没有有效 context，创建新的
        if context is None:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                viewport={'width': 1280, 'height': 900}
            )
        
        page = context.new_page()
        
        try:
            # 检查是否已登录
            if not self._check_login(page):
                print("[AUTO_APPLY] Not logged in, attempting login...")
                if not self._login(page):
                    print("[AUTO_APPLY] Login failed")
                    return False
                # 保存登录状态
                try:
                    context.storage_state(path=str(self.state_file))
                    print("[AUTO_APPLY] Saved login state")
                except Exception as e:
                    print(f"[AUTO_APPLY] Could not save state: {e}")
            
            # 访问职位页面
            print(f"[AUTO_APPLY] Navigating to job page...")
            try:
                page.goto(job_url, wait_until="domcontentloaded", timeout=20000)
            except PlaywrightTimeout:
                page.goto(job_url, wait_until="load", timeout=20000)
            
            page.wait_for_timeout(3000)
            
            # 查找 Easy Apply 按钮
            apply_btn = self._find_apply_button(page)
            
            if apply_btn:
                # Easy Apply 流程
                print("[AUTO_APPLY] Easy Apply button found")
                print("[AUTO_APPLY] Starting application...")
                apply_btn.click()
                page.wait_for_timeout(2000)
                
                # 填写表单
                success = self._fill_application_form(page, resume_path)
                
                if success:
                    print("[AUTO_APPLY] [OK] Application submitted successfully!")
                else:
                    print("[AUTO_APPLY] [FAIL] Could not complete application")
                
                return success
            else:
                # 外部申请流程
                print("[AUTO_APPLY] No Easy Apply button - external application")
                return self._handle_external_application(page, resume_path)
            
        finally:
            browser.close()
    
    def _check_login(self, page) -> bool:
        """检查是否已登录"""
        try:
            page.goto("https://www.linkedin.com/feed", timeout=10000)
            page.wait_for_timeout(2000)
            
            # 检查是否在 feed 页面
            if "feed" in page.url:
                print("[AUTO_APPLY] Already logged in")
                return True
            
            return False
        except:
            return False
    
    def _login(self, page) -> bool:
        """登录 LinkedIn"""
        print("[AUTO_APPLY] Logging in to LinkedIn...")
        
        try:
            page.goto("https://www.linkedin.com/login", 
                     wait_until="domcontentloaded", timeout=15000)
            
            email = self.credentials['linkedin']['email']
            password = self.credentials['linkedin']['password']
            
            page.locator('input#username').fill(email)
            page.locator('input#password').fill(password)
            page.locator('button[type="submit"]').click()
            
            page.wait_for_timeout(5000)
            
            # 检查是否需要验证码
            if page.locator('text=/verify|challenge|captcha/i').first.is_visible(timeout=3000):
                print("[AUTO_APPLY] Security verification required - cannot proceed automatically")
                print("[AUTO_APPLY] Please log in manually once to save the session")
                return False
            
            if "login" in page.url:
                print("[AUTO_APPLY] Login failed - check credentials")
                return False
            
            print("[AUTO_APPLY] [OK] Login successful")
            return True
            
        except Exception as e:
            print(f"[AUTO_APPLY] Login error: {e}")
            return False
    
    def _find_apply_button(self, page):
        """查找申请按钮"""
        selectors = [
            'button[data-control-name="jobdetails_topcard_inapply"]',
            '.jobs-apply-button',
            'button:has-text("Easy Apply")',
            'button:has-text("Apply")',
        ]
        
        for selector in selectors:
            try:
                btn = page.locator(selector).first
                if btn.is_visible(timeout=2000):
                    return btn
            except:
                continue
        
        return None
    
    def _fill_application_form(self, page, resume_path: Path) -> bool:
        """填写申请表单"""
        
        max_pages = 5
        for page_num in range(max_pages):
            print(f"[AUTO_APPLY] Page {page_num + 1}...")
            page.wait_for_timeout(2000)
            
            # 第一页：填写基本信息
            if page_num == 0:
                self._fill_contact_info(page)
                self._upload_resume(page, resume_path)
            
            # 填写其他可见输入框
            self._fill_text_inputs(page)
            
            # 检查按钮
            submit_btn = page.locator(
                'button:has-text("Submit application"):visible, '
                'button:has-text("Submit"):visible'
            ).first
            
            next_btn = page.locator('button:has-text("Next"):visible').first
            review_btn = page.locator('button:has-text("Review"):visible').first
            
            # 优先点击 Submit
            if submit_btn.is_visible(timeout=1000):
                print("[AUTO_APPLY] Submitting application...")
                page.wait_for_timeout(1000)
                submit_btn.click()
                page.wait_for_timeout(3000)
                return True
            
            # 其次点击 Review
            elif review_btn.is_visible(timeout=1000):
                print("[AUTO_APPLY] Going to review...")
                review_btn.click()
                page.wait_for_timeout(2000)
            
            # 最后点击 Next
            elif next_btn.is_visible(timeout=1000):
                print("[AUTO_APPLY] Next page...")
                next_btn.click()
                page.wait_for_timeout(2000)
            
            else:
                print("[AUTO_APPLY] No navigation button found")
                break
        
        return False
    
    def _fill_contact_info(self, page):
        """填写联系信息"""
        try:
            email = self.credentials['linkedin']['email']
            email_field = page.locator('input[type="email"]').first
            if email_field.is_visible(timeout=1000):
                email_field.fill(email)
                print("[AUTO_APPLY]   [OK] Email filled")
        except:
            pass
        
        try:
            phone = self.credentials.get('phone', '+31645038614')
            phone_field = page.locator('input[type="tel"]').first
            if phone_field.is_visible(timeout=1000):
                phone_field.fill(phone)
                print("[AUTO_APPLY]   [OK] Phone filled")
        except:
            pass
    
    def _upload_resume(self, page, resume_path: Path):
        """上传简历"""
        try:
            file_input = page.locator('input[type="file"]').first
            if file_input.is_visible(timeout=1000):
                file_input.set_input_files(str(resume_path.resolve()))
                print(f"[AUTO_APPLY]   [OK] Resume uploaded")
                page.wait_for_timeout(2000)
        except Exception as e:
            print(f"[AUTO_APPLY]   [WARN] Resume upload: {e}")
    
    def _fill_text_inputs(self, page):
        """填写文本输入框"""
        try:
            text_inputs = page.locator('input[type="text"]:visible').all()
            for inp in text_inputs:
                val = inp.input_value()
                if not val:
                    placeholder = inp.get_attribute('placeholder') or ''
                    name = inp.get_attribute('name') or ''
                    
                    if 'city' in placeholder.lower() or 'city' in name.lower():
                        inp.fill("Amsterdam")
                        print("[AUTO_APPLY]   [OK] City filled")
                    elif 'country' in placeholder.lower() or 'country' in name.lower():
                        inp.fill("Netherlands")
                        print("[AUTO_APPLY]   [OK] Country filled")
        except:
            pass
    
    def _handle_external_application(self, page, resume_path: Path) -> bool:
        """处理外部申请"""
        print("[AUTO_APPLY] Handling external application...")
        
        try:
            # 查找外部申请按钮
            external_selectors = [
                'button:has-text("Apply"):visible',
                'a:has-text("Apply"):visible',
                'button[data-control-name="jobdetails_topcard_apply"]',
            ]
            
            apply_btn = None
            for selector in external_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        apply_btn = btn
                        break
                except:
                    continue
            
            if apply_btn:
                print("[AUTO_APPLY] Clicking external Apply button...")
                apply_btn.click()
                page.wait_for_timeout(5000)
                
                # 检查是否跳转到外部网站
                current_url = page.url
                print(f"[AUTO_APPLY] Current URL: {current_url}")
                
                if 'linkedin.com' not in current_url:
                    print("[AUTO_APPLY] Redirected to external site")
                    print("[AUTO_APPLY] [WARN] External application - manual review needed")
                    # 保持浏览器打开30秒供查看
                    page.wait_for_timeout(30000)
                    return False
                else:
                    # 可能是 LinkedIn 的申请表单
                    print("[AUTO_APPLY] LinkedIn application form detected")
                    return self._fill_application_form(page, resume_path)
            else:
                print("[AUTO_APPLY] No apply button found")
                return False
                
        except Exception as e:
            print(f"[AUTO_APPLY] External application error: {e}")
            return False
