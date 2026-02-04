"""
自动投递模块 - Auto Apply Module
实现完全自动化的职位投递
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, Page, Browser


@dataclass
class ApplyResult:
    """投递结果"""
    success: bool
    job_id: str
    company: str
    position: str
    method: str  # 'linkedin_easy_apply', 'greenhouse', 'manual', etc.
    message: str
    timestamp: str
    screenshot_path: Optional[str] = None


class AutoApplier:
    """自动投递器"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.auto_config = self.config.get("auto_apply", {})
        self.personal_info = self.auto_config.get("personal_info", {})
        self.results: List[ApplyResult] = []
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def _load_config(self, config_path: Optional[Path]) -> Dict:
        """加载配置"""
        if not config_path:
            config_path = Path(__file__).parent.parent / "config.json"
        
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def should_auto_apply(self, job: Dict) -> Tuple[bool, str]:
        """
        判断是否应该自动投递
        返回: (是否应该投递, 原因)
        """
        if not self.auto_config.get("enabled", False):
            return False, "Auto apply disabled"
        
        # 检查分数
        score = job.get("analysis", {}).get("score", 0)
        threshold = self.auto_config.get("score_threshold", 7.5)
        if score < threshold:
            return False, f"Score {score} below threshold {threshold}"
        
        # 检查黑名单
        blacklist = self.auto_config.get("blacklist", {})
        company = job.get("company", "").lower()
        title = job.get("title", "").lower()
        
        # 黑名单公司
        for blocked in blacklist.get("companies", []):
            if blocked.lower() in company:
                return False, f"Company {company} in blacklist"
        
        # 黑名单职位关键词
        for keyword in blacklist.get("titles_containing", []):
            if keyword.lower() in title:
                return False, f"Title contains blacklisted keyword: {keyword}"
        
        # 经验要求
        min_exp = job.get("requirements", {}).get("experience_years", 0)
        if min_exp >= blacklist.get("min_years_experience", 4):
            return False, f"Requires {min_exp}+ years experience"
        
        return True, "Passed all checks"
    
    def detect_platform(self, url: str) -> str:
        """检测申请平台类型"""
        url_lower = url.lower()
        
        if "linkedin.com" in url_lower and "easy-apply" in url_lower:
            return "linkedin_easy_apply"
        elif "greenhouse.io" in url_lower or "boards.greenhouse" in url_lower:
            return "greenhouse"
        elif "lever.co" in url_lower:
            return "lever"
        elif "workday" in url_lower:
            return "workday"
        elif "indeed.com" in url_lower and "apply" in url_lower:
            return "indeed"
        elif "mailto:" in url_lower:
            return "email"
        else:
            return "unknown"
    
    def apply(self, job: Dict, resume_path: Path) -> ApplyResult:
        """
        执行自动投递
        """
        job_id = job.get("id", "unknown")
        company = job.get("company", "Unknown")
        position = job.get("title", "Unknown")
        url = job.get("url", "")
        
        # 检查是否应该自动投递
        should_apply, reason = self.should_auto_apply(job)
        if not should_apply:
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method="skipped",
                message=reason,
                timestamp=datetime.now().isoformat()
            )
        
        # 检测平台
        platform = self.detect_platform(url)
        platform_config = self.auto_config.get("platforms", {}).get(platform, {})
        
        if not platform_config.get("enabled", False):
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method=platform,
                message=f"Platform {platform} not enabled for auto apply",
                timestamp=datetime.now().isoformat()
            )
        
        mode = platform_config.get("mode", "manual")
        
        try:
            if platform == "linkedin_easy_apply" and mode == "full_auto":
                return self._apply_linkedin_easy_apply(job, resume_path)
            elif platform == "greenhouse" and mode in ["full_auto", "semi_auto"]:
                return self._apply_greenhouse(job, resume_path)
            elif platform == "email":
                return self._apply_email(job, resume_path)
            else:
                # 其他平台暂时标记为需要人工处理
                return ApplyResult(
                    success=False,
                    job_id=job_id,
                    company=company,
                    position=position,
                    method=platform,
                    message=f"Platform {platform} mode '{mode}' - requires manual review",
                    timestamp=datetime.now().isoformat()
                )
        except Exception as e:
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method=platform,
                message=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    def _init_browser(self):
        """初始化浏览器"""
        if self.browser is None:
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=False)
            self.page = self.browser.new_page()
    
    def _close_browser(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
            self.browser = None
            self.page = None
    
    def _apply_linkedin_easy_apply(self, job: Dict, resume_path: Path) -> ApplyResult:
        """
        LinkedIn Easy Apply 自动化
        """
        url = job.get("url", "")
        job_id = job.get("id", "unknown")
        company = job.get("company", "Unknown")
        position = job.get("title", "Unknown")
        
        try:
            self._init_browser()
            page = self.page
            
            # 打开职位页面
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # 点击 Easy Apply 按钮
            # LinkedIn 的 Easy Apply 按钮通常有特定属性
            easy_apply_selectors = [
                'button[data-control-name="jobdetails_topcard_inapply"]',
                'button.jobs-apply-button',
                'button:has-text("Easy Apply")',
                '[aria-label*="Apply"]'
            ]
            
            for selector in easy_apply_selectors:
                try:
                    if page.locator(selector).count() > 0:
                        page.click(selector)
                        time.sleep(2)
                        break
                except:
                    continue
            
            # 检查是否打开申请表单
            # 通常是一个 modal 或新页面
            time.sleep(3)
            
            # 填写表单步骤
            # LinkedIn Easy Apply 通常是多步骤表单
            max_steps = 5
            for step in range(max_steps):
                # 检查是否有文件上传
                file_inputs = page.locator('input[type="file"]').all()
                if file_inputs:
                    for file_input in file_inputs:
                        file_input.set_input_files(str(resume_path))
                        time.sleep(1)
                
                # 填写文本字段
                text_fields = {
                    "firstName": self.personal_info.get("first_name", ""),
                    "lastName": self.personal_info.get("last_name", ""),
                    "email": self.personal_info.get("email", ""),
                    "phone": self.personal_info.get("phone", ""),
                }
                
                for field_id, value in text_fields.items():
                    try:
                        field = page.locator(f'input[name="{field_id}"], input[id="{field_id}"], input[autocomplete="{field_id}"]').first
                        if field.count() > 0:
                            field.fill(value)
                            time.sleep(0.5)
                    except:
                        pass
                
                # 检查是否有"Next"或"Submit"按钮
                next_selectors = [
                    'button:has-text("Next")',
                    'button:has-text("Continue")',
                    'button:has-text("Submit")',
                    'button:has-text("Send")',
                    'button[data-control-name="submit_application"]'
                ]
                
                clicked = False
                for selector in next_selectors:
                    try:
                        if page.locator(selector).count() > 0:
                            # 如果是 Submit，点击后结束
                            if "submit" in selector.lower() or "send" in selector.lower():
                                page.click(selector)
                                time.sleep(3)
                                return ApplyResult(
                                    success=True,
                                    job_id=job_id,
                                    company=company,
                                    position=position,
                                    method="linkedin_easy_apply",
                                    message="Application submitted successfully",
                                    timestamp=datetime.now().isoformat()
                                )
                            else:
                                page.click(selector)
                                time.sleep(2)
                                clicked = True
                                break
                    except:
                        continue
                
                if not clicked:
                    # 没有可点击的按钮，可能完成了
                    break
            
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method="linkedin_easy_apply",
                message="Could not complete application - manual review needed",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method="linkedin_easy_apply",
                message=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    def _apply_greenhouse(self, job: Dict, resume_path: Path) -> ApplyResult:
        """
        Greenhouse ATS 自动化
        """
        url = job.get("url", "")
        job_id = job.get("id", "unknown")
        company = job.get("company", "Unknown")
        position = job.get("title", "Unknown")
        
        try:
            self._init_browser()
            page = self.page
            
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            
            # Greenhouse 表单通常有标准字段名
            field_mapping = {
                "first_name": ["first_name", "firstName", "first-name"],
                "last_name": ["last_name", "lastName", "last-name"],
                "email": ["email"],
                "phone": ["phone"],
                "linkedin": ["linkedin_profile", "linkedin", "linkedin_url"],
                "website": ["website", "portfolio", "personal_website"],
            }
            
            # 填写文本字段
            for info_key, field_names in field_mapping.items():
                value = self.personal_info.get(info_key, "")
                if not value:
                    continue
                    
                for field_name in field_names:
                    try:
                        selectors = [
                            f'input[name="{field_name}"]',
                            f'input[id="{field_name}"]',
                            f'textarea[name="{field_name}"]',
                            f'input[autocomplete="{field_name}"]'
                        ]
                        for selector in selectors:
                            field = page.locator(selector).first
                            if field.count() > 0:
                                field.fill(value)
                                time.sleep(0.5)
                                break
                    except:
                        pass
            
            # 上传简历
            try:
                file_input = page.locator('input[type="file"]').first
                if file_input.count() > 0:
                    file_input.set_input_files(str(resume_path))
                    time.sleep(2)
            except:
                pass
            
            # 注意：Greenhouse 通常有自定义问题，这里不做自动提交
            # 只填写标准字段，然后返回需要人工完成
            
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method="greenhouse",
                message="Standard fields filled. Custom questions require manual review.",
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return ApplyResult(
                success=False,
                job_id=job_id,
                company=company,
                position=position,
                method="greenhouse",
                message=f"Error: {str(e)}",
                timestamp=datetime.now().isoformat()
            )
    
    def _apply_email(self, job: Dict, resume_path: Path) -> ApplyResult:
        """
        邮件申请自动化
        """
        job_id = job.get("id", "unknown")
        company = job.get("company", "Unknown")
        position = job.get("title", "Unknown")
        
        # 邮件申请暂时标记为需要手动处理
        # 可以扩展为使用系统邮件客户端或API
        
        return ApplyResult(
            success=False,
            job_id=job_id,
            company=company,
            position=position,
            method="email",
            message="Email applications require manual send - prepared but not sent",
            timestamp=datetime.now().isoformat()
        )
    
    def apply_batch(self, jobs: List[Dict], resume_dir: Path) -> List[ApplyResult]:
        """
        批量投递
        """
        results = []
        daily_limit = self.auto_config.get("daily_limit", 10)
        delay_ms = self.auto_config.get("delay_ms", 30000)
        
        applied_today = 0
        
        for job in jobs:
            if applied_today >= daily_limit:
                results.append(ApplyResult(
                    success=False,
                    job_id=job.get("id", "unknown"),
                    company=job.get("company", "Unknown"),
                    position=job.get("title", "Unknown"),
                    method="skipped",
                    message="Daily limit reached",
                    timestamp=datetime.now().isoformat()
                ))
                continue
            
            # 检查是否有对应的简历
            safe_company = job.get("company", "unknown").replace(" ", "_")
            safe_title = job.get("title", "position").replace(" ", "_")
            resume_name = f"Fei_Huang_{safe_company}_{safe_title}.pdf"
            resume_path = resume_dir / resume_name
            
            if not resume_path.exists():
                # 尝试其他命名格式
                resume_path = resume_dir / f"Fei_Huang_{safe_title}_{safe_company}.pdf"
            
            if not resume_path.exists():
                results.append(ApplyResult(
                    success=False,
                    job_id=job.get("id", "unknown"),
                    company=job.get("company", "Unknown"),
                    position=job.get("title", "Unknown"),
                    method="skipped",
                    message=f"Resume not found: {resume_name}",
                    timestamp=datetime.now().isoformat()
                ))
                continue
            
            # 执行投递
            result = self.apply(job, resume_path)
            results.append(result)
            
            if result.success:
                applied_today += 1
            
            # 延迟
            time.sleep(delay_ms / 1000)
        
        self._close_browser()
        return results
    
    def generate_report(self, results: List[ApplyResult]) -> str:
        """
        生成投递报告
        """
        total = len(results)
        success = sum(1 for r in results if r.success)
        failed = total - success
        
        lines = [
            "=" * 60,
            "Auto Apply Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
            "",
            f"Total Jobs Processed: {total}",
            f"Successfully Applied: {success}",
            f"Failed/Skipped: {failed}",
            "",
            "Details:",
            "-" * 60
        ]
        
        for r in results:
            status = "[OK]" if r.success else "[SKIP]"
            lines.append(f"{status} [{r.method}] {r.position} @ {r.company}")
            lines.append(f"   Message: {r.message}")
            lines.append("")
        
        return "\n".join(lines)
