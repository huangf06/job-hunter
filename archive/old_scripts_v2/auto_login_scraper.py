"""
全自动登录+爬取+投递系统
===========================

模拟人工操作：
1. 登录网站
2. 搜索职位
3. 获取职位列表
4. 分析匹配度
5. 自动投递

Usage:
    python auto_login_scraper.py --platform linkedin --login
    python auto_login_scraper.py --platform linkedin --search "data scientist"
    python auto_login_scraper.py --auto-apply
"""

import asyncio
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, Page

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR.mkdir(exist_ok=True)

# 加载凭据
def load_credentials():
    cred_file = CONFIG_DIR / "credentials.json"
    if cred_file.exists():
        with open(cred_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class AutoJobBot:
    """全自动求职机器人"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.credentials = load_credentials()
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # 启动浏览器（可见模式便于调试）
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        
        self.page = await self.context.new_page()
        
        # 添加 stealth 脚本
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            window.chrome = { runtime: {} };
        """)
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def human_like_delay(self, min_sec: float = 1, max_sec: float = 3):
        """模拟人类延迟"""
        await asyncio.sleep(random.uniform(min_sec, max_sec))
    
    async def human_like_typing(self, selector: str, text: str):
        """模拟人类打字"""
        for char in text:
            await self.page.type(selector, char, delay=random.randint(50, 150))
            await asyncio.sleep(random.uniform(0.01, 0.05))
    
    async def safe_click(self, selector: str):
        """安全点击（等待元素可见）"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            await self.page.click(selector)
            return True
        except:
            return False
    
    # ============================================================
    # LinkedIn 自动化
    # ============================================================
    
    async def save_cookies(self, platform: str):
        """保存 cookies 到文件"""
        cookies = await self.context.cookies()
        cookie_file = DATA_DIR / f"{platform}_cookies.json"
        with open(cookie_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
        print(f"[{platform}] Cookies saved to {cookie_file}")
    
    async def load_cookies(self, platform: str) -> bool:
        """从文件加载 cookies"""
        cookie_file = DATA_DIR / f"{platform}_cookies.json"
        if not cookie_file.exists():
            return False
        
        with open(cookie_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        
        await self.context.add_cookies(cookies)
        print(f"[{platform}] Cookies loaded from {cookie_file}")
        return True
    
    async def check_logged_in(self, platform: str) -> bool:
        """检查是否已登录"""
        if platform == "indeed":
            # 访问 Indeed 个人页面检查
            await self.page.goto("https://my.indeed.com", timeout=30000)
            await asyncio.sleep(3)
            
            # 检查页面内容
            current_url = self.page.url
            if "login" not in current_url and "resume" in current_url or "profile" in current_url:
                print(f"[{platform}] Already logged in!")
                return True
            
            # 检查是否有用户菜单
            user_menu = await self.page.query_selector("[data-gnav-element-name='AccountMenu'], .gnav-AccountMenu, .user-name")
            if user_menu:
                print(f"[{platform}] Already logged in (found user menu)!")
                return True
            
            print(f"[{platform}] Not logged in (URL: {current_url})")
            return False
        
        return False
    
    async def indeed_login_no_password(self) -> bool:
        """尝试无需密码登录 Indeed（使用 cookies 或访问密钥）"""
        print("[Indeed] Attempting login without password...")
        
        # 方法1: 尝试加载已保存的 cookies
        if await self.load_cookies("indeed"):
            print("[Indeed] Cookies loaded, checking login status...")
            if await self.check_logged_in("indeed"):
                return True
        
        # 方法2: 尝试访问密钥登录（如果浏览器支持）
        print("[Indeed] Trying access key login...")
        try:
            await self.page.goto("https://secure.indeed.com/auth", timeout=60000)
            await self.human_like_delay(3, 5)
            
            # 检查是否有访问密钥选项
            access_key_btn = await self.page.query_selector(
                "button:has-text('Access key'), button:has-text('Toegangssleutel'), [data-testid='access-key-button']"
            )
            
            if access_key_btn:
                print("[Indeed] Access key option found, clicking...")
                await access_key_btn.click()
                await self.human_like_delay(5, 10)
                
                # 这里可能需要用户手动验证指纹/PIN
                # 我们等待一段时间让用户完成验证
                print("[Indeed] Waiting for access key verification (fingerprint/PIN)...")
                print("[Indeed] If prompted, please complete the verification on screen...")
                await asyncio.sleep(15)  # 等待用户验证
                
                # 检查是否登录成功
                if await self.check_logged_in("indeed"):
                    await self.save_cookies("indeed")
                    return True
            
            # 方法3: 检查是否已经在登录状态（通过 Google session）
            print("[Indeed] Checking if already logged in via Google session...")
            await self.page.goto("https://nl.indeed.com", timeout=60000)
            await self.human_like_delay(3, 5)
            
            # 查找用户菜单或欢迎信息
            user_indicators = [
                ".gnav-AccountMenu",
                "[data-gnav-element-name='AccountMenu']",
                ".user-name",
                "a[href*='logout']",
                "a[href*='myresume']"
            ]
            
            for selector in user_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    print(f"[Indeed] Found user indicator: {text[:50]}")
                    await self.save_cookies("indeed")
                    return True
            
            print("[Indeed] Not logged in. Access key may require manual browser interaction.")
            print("[Indeed] Suggestion: Try logging in manually once with 'remember me' enabled.")
            
        except Exception as e:
            print(f"[Indeed] Login error: {e}")
        
        return False
    
    async def linkedin_login(self) -> bool:
        """登录 LinkedIn"""
        print("[LinkedIn] Starting login...")
        
        email = self.credentials.get("linkedin", {}).get("email")
        password = self.credentials.get("linkedin", {}).get("password")
        
        if not email or not password:
            print("[LinkedIn] No credentials found. Please set up credentials.json")
            return False
        
        try:
            # 访问登录页
            await self.page.goto("https://www.linkedin.com/login", timeout=60000)
            await self.human_like_delay(2, 4)
            
            # 输入邮箱
            print("[LinkedIn] Entering email...")
            await self.human_like_typing("#username", email)
            await self.human_like_delay(0.5, 1.5)
            
            # 输入密码
            print("[LinkedIn] Entering password...")
            await self.human_like_typing("#password", password)
            await self.human_like_delay(0.5, 1.5)
            
            # 点击登录
            print("[LinkedIn] Clicking login...")
            await self.safe_click("button[type='submit']")
            
            # 等待登录完成
            await self.human_like_delay(5, 8)
            
            # 检查是否登录成功
            current_url = self.page.url
            if "feed" in current_url or "mynetwork" in current_url:
                print("[LinkedIn] Login successful!")
                return True
            else:
                print(f"[LinkedIn] Login may have failed. Current URL: {current_url}")
                # 保存截图调试
                await self.page.screenshot(path=str(DATA_DIR / "linkedin_login_debug.png"))
                return False
                
        except Exception as e:
            print(f"[LinkedIn] Login error: {e}")
            return False
    
    async def linkedin_search_jobs(self, keywords: List[str], location: str = "Netherlands") -> List[Dict]:
        """在 LinkedIn 搜索职位"""
        jobs = []
        
        for keyword in keywords:
            print(f"[LinkedIn] Searching for: {keyword}")
            
            try:
                # 构建搜索 URL
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
                await self.page.goto(search_url, timeout=60000)
                await self.human_like_delay(5, 8)
                
                # 滚动加载更多
                for _ in range(3):
                    await self.page.evaluate("window.scrollBy(0, 800)")
                    await self.human_like_delay(1, 2)
                
                # 提取职位数据
                job_data = await self.page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('[data-job-id]');
                        
                        cards.forEach(card => {
                            const titleEl = card.querySelector('.job-card-list__title, h3');
                            const companyEl = card.querySelector('.job-card-container__company-name, .base-search-card__subtitle');
                            const locationEl = card.querySelector('.job-card-container__metadata-item, .job-search-card__location');
                            const linkEl = card.querySelector('a');
                            
                            if (titleEl) {
                                jobs.push({
                                    title: titleEl.innerText.trim(),
                                    company: companyEl ? companyEl.innerText.trim() : '',
                                    location: locationEl ? locationEl.innerText.trim() : '',
                                    url: linkEl ? linkEl.href : '',
                                    id: card.getAttribute('data-job-id')
                                });
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                for job in job_data[:10]:  # 每个关键词取前10个
                    if job.get('title'):
                        jobs.append({
                            **job,
                            "source": "LinkedIn",
                            "search_term": keyword,
                            "scraped_at": datetime.now().isoformat()
                        })
                
                print(f"[LinkedIn] Found {len(job_data)} jobs for '{keyword}'")
                
                # 随机延迟，避免被封
                await self.human_like_delay(3, 6)
                
            except Exception as e:
                print(f"[LinkedIn] Search error: {e}")
        
        return jobs
    
    async def linkedin_apply(self, job_url: str) -> bool:
        """申请 LinkedIn 职位"""
        print(f"[LinkedIn] Applying to: {job_url}")
        
        try:
            await self.page.goto(job_url, timeout=60000)
            await self.human_like_delay(3, 5)
            
            # 查找申请按钮
            apply_button = await self.page.query_selector(
                "button[data-control-name='jobdetails_topcard_inapply'], .jobs-apply-button, [aria-label*='Apply']"
            )
            
            if apply_button:
                print("[LinkedIn] Clicking apply button...")
                await apply_button.click()
                await self.human_like_delay(2, 4)
                
                # 处理 Easy Apply 流程
                # 这里需要根据具体申请流程实现
                # 可能需要填写表单、上传简历等
                
                print("[LinkedIn] Application started (manual completion may be needed)")
                return True
            else:
                print("[LinkedIn] Apply button not found - may require external application")
                return False
                
        except Exception as e:
            print(f"[LinkedIn] Apply error: {e}")
            return False
    
    async def indeed_interactive_login(self) -> bool:
        """交互式登录 - 用户手动完成登录，系统保存 cookies"""
        print("\n" + "=" * 60)
        print("Indeed Interactive Login")
        print("=" * 60)
        print("1. Browser will open to Indeed login page")
        print("2. Please click 'Sign in with Google' and complete login")
        print("3. After successful login, press Enter in this terminal")
        print("4. System will save cookies for future automatic use")
        print("=" * 60 + "\n")
        
        try:
            # 打开 Indeed 登录页
            await self.page.goto("https://secure.indeed.com/auth", timeout=60000)
            await self.human_like_delay(2, 3)
            
            print("[Indeed] Browser opened. Please complete login manually...")
            print("[Indeed] After login, the system will save cookies for future use.")
            
            # 等待一段时间让用户登录
            await asyncio.sleep(30)  # 给用户30秒时间完成登录
            
            # 检查登录状态
            if await self.check_logged_in("indeed"):
                await self.save_cookies("indeed")
                print("[Indeed] Login successful! Cookies saved for future use.")
                return True
            else:
                print("[Indeed] Login may not be complete. Please try again.")
                return False
                
        except Exception as e:
            print(f"[Indeed] Error: {e}")
            return False
    
    # ============================================================
    # IamExpat 自动化
    # ============================================================
    
    async def iamexpat_search_jobs(self, keywords: List[str]) -> List[Dict]:
        """在 IamExpat 搜索职位（无需登录）"""
        jobs = []
        
        for keyword in keywords:
            print(f"[IamExpat] Searching for: {keyword}")
            
            try:
                # 构建搜索 URL
                search_slug = keyword.replace(" ", "-").lower()
                url = f"https://www.iamexpat.nl/career/jobs-netherlands/{search_slug}"
                
                await self.page.goto(url, timeout=60000)
                await self.human_like_delay(8, 12)  # 等待 React 渲染
                
                # 滚动触发懒加载
                for _ in range(5):
                    await self.page.evaluate("window.scrollBy(0, 1000)")
                    await self.human_like_delay(1, 2)
                
                await self.human_like_delay(3, 5)
                
                # 提取职位数据
                job_data = await self.page.evaluate("""
                    () => {
                        const jobs = [];
                        // 尝试多种选择器
                        const selectors = [
                            'a[href*="/career/jobs-netherlands/"]', 
                            '.job-item a', 
                            'article a',
                            '[class*="job"] a'
                        ];
                        
                        let links = [];
                        for (const sel of selectors) {
                            links = document.querySelectorAll(sel);
                            if (links.length > 0) break;
                        }
                        
                        links.forEach(link => {
                            const text = link.innerText.trim();
                            if (text && text.length > 5 && text.length < 200) {
                                const parent = link.closest('article, .job-item, [class*="job"], div');
                                const companyEl = parent ? parent.querySelector('[class*="company"], [class*="organization"]') : null;
                                
                                jobs.push({
                                    title: text,
                                    url: link.href,
                                    company: companyEl ? companyEl.innerText.trim() : ''
                                });
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                seen = set()
                for job in job_data:
                    if job.get('title') and job['title'] not in seen:
                        seen.add(job['title'])
                        jobs.append({
                            **job,
                            "location": "Netherlands",
                            "source": "IamExpat",
                            "search_term": keyword,
                            "scraped_at": datetime.now().isoformat()
                        })
                
                print(f"[IamExpat] Found {len(job_data)} jobs for '{keyword}'")
                await self.human_like_delay(3, 6)
                
            except Exception as e:
                print(f"[IamExpat] Search error: {e}")
        
        return jobs


def save_jobs(jobs: List[Dict]):
    """保存职位"""
    if not jobs:
        return
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filepath = DATA_DIR / f"auto_scrape_{date_str}.json"
    
    data = {
        "scraped_at": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "jobs": jobs
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[Save] Saved {len(jobs)} jobs to {filepath}")


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", choices=["linkedin", "indeed", "iamexpat", "all"], default="all")
    parser.add_argument("--login", action="store_true", help="Login only")
    parser.add_argument("--search", help="Search term")
    parser.add_argument("--auto", action="store_true", help="Full auto mode")
    parser.add_argument("--visible", action="store_true", help="Show browser window (for debugging)")
    
    args = parser.parse_args()
    
    # 关键词列表
    KEYWORDS = [
        "Quant", "Quantitative", "Algorithmic", "HFT", "Market Maker",
        "Derivatives", "Trading", "Machine Learning", "Deep Learning",
        "Computer Vision", "NLP", "Data Engineer", "LLM",
        "Python Developer", "Backend Engineer", "Software Engineer"
    ]
    
    async with AutoJobBot(headless=not args.visible) as bot:
        if args.login:
            if args.platform in ["linkedin", "all"]:
                await bot.linkedin_login()
            if args.platform in ["indeed", "all"]:
                # 尝试无密码登录
                if not await bot.indeed_login_no_password():
                    # 如果失败，使用交互式登录
                    print("[Indeed] Automatic login failed. Switching to interactive mode...")
                    await bot.indeed_interactive_login()
        
        elif args.search:
            if args.platform in ["linkedin", "all"]:
                # 先登录
                if await bot.linkedin_login():
                    jobs = await bot.linkedin_search_jobs([args.search])
                    save_jobs(jobs)
            
            if args.platform in ["iamexpat", "all"]:
                jobs = await bot.iamexpat_search_jobs([args.search])
                save_jobs(jobs)
        
        elif args.auto:
            print("=" * 60)
            print("FULL AUTO MODE")
            print("=" * 60)
            
            # 1. LinkedIn
            if await bot.linkedin_login():
                linkedin_jobs = await bot.linkedin_search_jobs(KEYWORDS[:5])  # 前5个关键词
                save_jobs(linkedin_jobs)
            
            # 2. IamExpat
            iamexpat_jobs = await bot.iamexpat_search_jobs(KEYWORDS[:5])
            save_jobs(iamexpat_jobs)
            
            print(f"\nTotal jobs found: {len(linkedin_jobs) + len(iamexpat_jobs)}")
        
        else:
            print("Usage:")
            print("  python auto_login_scraper.py --login --platform linkedin")
            print("  python auto_login_scraper.py --search 'data scientist' --platform all")
            print("  python auto_login_scraper.py --auto")


if __name__ == "__main__":
    asyncio.run(main())
