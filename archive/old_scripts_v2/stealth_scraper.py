"""
Stealth 爬虫 - 绕过反爬虫检测 (简化版)
======================================

使用手动 stealth 脚本来爬取职位
"""

import asyncio
import json
import random
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

# Stealth 初始化脚本
STEALTH_SCRIPTS = [
    # 覆盖 webdriver
    """Object.defineProperty(navigator, 'webdriver', {get: () => undefined});""",
    # 覆盖 plugins
    """Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});""",
    # 添加 chrome 对象
    """window.chrome = { runtime: {} };""",
    # 覆盖 permissions
    """const originalQuery = window.navigator.permissions.query; window.navigator.permissions.query = (parameters) => (parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters));""",
    # 添加语言
    """Object.defineProperty(navigator, 'language', {get: () => 'en-US'});""",
    """Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});""",
]


class StealthJobScraper:
    """Stealth 职位爬虫"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        
        # 启动浏览器
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
            ]
        )
        
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Europe/Amsterdam",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        # 添加 stealth 脚本
        for script in STEALTH_SCRIPTS:
            await self.context.add_init_script(script)
        
        self.page = await self.context.new_page()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def scrape_with_retry(self, url: str, max_retries: int = 3) -> str:
        """带重试的页面抓取"""
        for attempt in range(max_retries):
            try:
                print(f"  Attempt {attempt + 1}/{max_retries}...")
                
                # 随机延迟
                await asyncio.sleep(random.uniform(2, 5))
                
                # 访问页面
                response = await self.page.goto(
                    url, 
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                
                if response and response.status < 400:
                    # 等待动态内容加载 (React/Next.js 需要更长时间)
                    await asyncio.sleep(random.uniform(8, 12))
                    
                    # 滚动页面模拟真实用户，触发懒加载
                    for _ in range(random.randint(3, 5)):
                        scroll_amount = random.randint(500, 1000)
                        await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                        await asyncio.sleep(random.uniform(1, 2))
                    
                    # 再等待内容加载
                    await asyncio.sleep(random.uniform(3, 5))
                    
                    content = await self.page.content()
                    return content
                else:
                    print(f"  HTTP error: {response.status if response else 'No response'}")
                    
            except Exception as e:
                print(f"  Error: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(random.uniform(5, 10))
        
        return ""
    
    async def scrape_iamexpat(self, search_term: str, max_jobs: int = 25) -> List[Dict]:
        """抓取 IamExpat"""
        print(f"[Stealth] Scraping IamExpat for '{search_term}'...")
        
        search_slug = search_term.replace(" ", "-").lower()
        url = f"https://www.iamexpat.nl/career/jobs-netherlands/{search_slug}"
        
        jobs = []
        
        try:
            content = await self.scrape_with_retry(url)
            if not content:
                print("  Failed to fetch page")
                return jobs
            
            # 保存调试文件
            debug_file = DATA_DIR / "iamexpat_debug.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  Saved debug HTML to {debug_file}")
            
            # 使用 JavaScript 提取职位信息
            job_data = await self.page.evaluate("""
                () => {
                    const jobs = [];
                    // 尝试多种选择器
                    const selectors = [
                        '.views-row', '.job-item', 'article', '.node-job', 
                        '[class*="job"]', '.item-list li', '.content article'
                    ];
                    
                    let items = [];
                    for (const selector of selectors) {
                        items = document.querySelectorAll(selector);
                        if (items.length > 0) break;
                    }
                    
                    items.forEach(item => {
                        const titleEl = item.querySelector('h2 a, h3 a, .title a, a');
                        const companyEl = item.querySelector('.company, [class*="company"], [class*="organization"]');
                        const locationEl = item.querySelector('.location, [class*="location"]');
                        
                        if (titleEl && titleEl.innerText.trim()) {
                            jobs.push({
                                title: titleEl.innerText.trim(),
                                url: titleEl.href,
                                company: companyEl ? companyEl.innerText.trim() : '',
                                location: locationEl ? locationEl.innerText.trim() : ''
                            });
                        }
                    });
                    
                    return jobs;
                }
            """)
            
            print(f"  Raw job data count: {len(job_data)}")
            
            for job in job_data[:max_jobs]:
                if job.get('title') and len(job['title']) > 3:
                    jobs.append({
                        "title": job['title'],
                        "company": job.get('company', 'Unknown') or 'Unknown',
                        "location": job.get('location', 'Netherlands') or 'Netherlands',
                        "url": job.get('url', ''),
                        "source": "IamExpat",
                        "scraped_at": datetime.now().isoformat()
                    })
                    print(f"  - {job['title'][:60]}")
            
            print(f"[Stealth] Found {len(jobs)} jobs")
            
        except Exception as e:
            print(f"[Stealth] Error: {e}")
            import traceback
            traceback.print_exc()
        
        return jobs


def save_jobs(jobs: List[Dict], source: str, search_term: str):
    """保存职位"""
    if not jobs:
        return
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{source}_{search_term.replace(' ', '_')}_{date_str}.json"
    filepath = DATA_DIR / filename
    
    data = {
        "source": source,
        "search": search_term,
        "scraped_at": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "jobs": jobs
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[Save] Saved {len(jobs)} jobs to {filepath}")


async def main():
    """测试"""
    print("=" * 60)
    print("Stealth Job Scraper Test")
    print("=" * 60)
    
    async with StealthJobScraper(headless=True) as scraper:
        # 测试 IamExpat
        jobs = await scraper.scrape_iamexpat("data-scientist")
        if jobs:
            save_jobs(jobs, "iamexpat_stealth", "data_scientist")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
