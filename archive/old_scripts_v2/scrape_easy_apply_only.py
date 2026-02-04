"""
专门爬取 LinkedIn Easy Apply 职位
==============================

LinkedIn 搜索时过滤出 Easy Apply 职位
"""

import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# 加载凭据
def load_credentials():
    cred_file = PROJECT_ROOT / "config" / "credentials.json"
    if cred_file.exists():
        with open(cred_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


class EasyApplyScraper:
    """Easy Apply 职位爬虫"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.credentials = load_credentials()
        self.easy_apply_jobs = []
    
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
    
    async def linkedin_login(self) -> bool:
        """登录 LinkedIn"""
        email = self.credentials.get("linkedin", {}).get("email")
        password = self.credentials.get("linkedin", {}).get("password")
        
        if not email or not password:
            print("[LinkedIn] No credentials")
            return False
        
        try:
            await self.page.goto("https://www.linkedin.com/login", timeout=60000)
            await self.delay(2, 4)
            
            await self.page.type("#username", email, delay=50)
            await self.page.type("#password", password, delay=50)
            await self.page.click("button[type='submit']")
            await self.delay(5, 8)
            
            if "feed" in self.page.url or "mynetwork" in self.page.url:
                print("[LinkedIn] Login successful")
                return True
            return False
        except Exception as e:
            print(f"[LinkedIn] Login error: {e}")
            return False
    
    async def search_easy_apply_jobs(self, keywords: list, location: str = "Netherlands"):
        """搜索 Easy Apply 职位"""
        print(f"\n[Search] Looking for Easy Apply jobs...")
        
        for keyword in keywords[:3]:  # 前3个关键词
            print(f"\n  Searching: {keyword}")
            
            # 构建搜索 URL（添加 Easy Apply 过滤器）
            params = {
                "keywords": keyword,
                "location": location,
                "f_AL": "true"  # Easy Apply filter
            }
            url = f"https://www.linkedin.com/jobs/search/?{urlencode(params)}"
            
            try:
                await self.page.goto(url, timeout=60000)
                await self.delay(5, 8)
                
                # 滚动加载
                for _ in range(5):
                    await self.page.evaluate("window.scrollBy(0, 800)")
                    await self.delay(1, 2)
                
                # 提取职位
                jobs = await self.page.evaluate("""
                    () => {
                        const jobs = [];
                        const cards = document.querySelectorAll('[data-job-id]');
                        
                        cards.forEach(card => {
                            // 检查是否有 Easy Apply 按钮
                            const easyApplyBtn = card.querySelector(
                                "button[data-control-name='jobdetails_topcard_inapply'], .jobs-apply-button"
                            );
                            
                            if (easyApplyBtn) {
                                const titleEl = card.querySelector('.job-card-list__title, h3');
                                const companyEl = card.querySelector('.job-card-container__company-name');
                                const locationEl = card.querySelector('.job-card-container__metadata-item');
                                const linkEl = card.querySelector('a');
                                
                                if (titleEl) {
                                    jobs.push({
                                        title: titleEl.innerText.trim(),
                                        company: companyEl ? companyEl.innerText.trim() : 'Unknown',
                                        location: locationEl ? locationEl.innerText.trim() : location,
                                        url: linkEl ? linkEl.href : '',
                                        id: card.getAttribute('data-job-id'),
                                        source: 'LinkedIn',
                                        easy_apply: true
                                    });
                                }
                            }
                        });
                        
                        return jobs;
                    }
                """)
                
                print(f"    Found {len(jobs)} Easy Apply jobs")
                self.easy_apply_jobs.extend(jobs)
                
                await self.delay(3, 6)
                
            except Exception as e:
                print(f"    Error: {e}")
    
    async def run(self):
        """运行爬取"""
        print("=" * 60)
        print("Easy Apply Job Scraper")
        print("=" * 60)
        
        # 登录
        if not await self.linkedin_login():
            print("Login failed, exiting")
            return
        
        # 搜索关键词
        keywords = [
            "Data Scientist",
            "Machine Learning Engineer",
            "Data Engineer",
            "Python Developer",
            "Software Engineer"
        ]
        
        await self.search_easy_apply_jobs(keywords)
        
        # 去重
        seen = set()
        unique_jobs = []
        for job in self.easy_apply_jobs:
            if job['id'] not in seen:
                seen.add(job['id'])
                unique_jobs.append(job)
        
        # 保存
        if unique_jobs:
            output_file = DATA_DIR / f"easy_apply_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump({
                    "scraped_at": datetime.now().isoformat(),
                    "total": len(unique_jobs),
                    "jobs": unique_jobs
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*60}")
            print(f"Total Easy Apply jobs: {len(unique_jobs)}")
            print(f"Saved to: {output_file}")
            print(f"{'='*60}")
            
            # 打印前5个
            print("\nTop 5 jobs:")
            for i, job in enumerate(unique_jobs[:5], 1):
                print(f"{i}. {job['title']} @ {job['company']}")
        else:
            print("\nNo Easy Apply jobs found")


async def main():
    async with EasyApplyScraper(headless=True) as scraper:
        await scraper.run()


if __name__ == "__main__":
    asyncio.run(main())
