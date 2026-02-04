"""
LinkedIn 职位爬虫 - 修复版 (基于飞哥的JS代码)
===============================================

完全按照飞哥提供的JS代码逻辑实现
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class LinkedInScraperFixed:
    """LinkedIn 职位爬虫 - 修复版"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        self.page = await self.context.new_page()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def ensure_login(self):
        """确保已登录"""
        print("[LinkedIn] 检查登录状态...")
        
        if COOKIES_FILE.exists():
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
        
        await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        if "login" in self.page.url or "signup" in self.page.url:
            print("  → 需要登录，请在浏览器中完成")
            await self.page.goto("https://www.linkedin.com/login")
            input("登录完成后按回车...")
            
            cookies = await self.context.cookies()
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            print("  ✓ Cookies 已保存")
        else:
            print("  ✓ 已登录")
    
    async def search_jobs(self, keyword: str, location: str = "Netherlands"):
        """搜索职位 - 完全按照飞哥的流程"""
        print(f"\n[LinkedIn] 搜索: '{keyword}' in {location}")
        print("  筛选: Past 24 hours + Hybrid/On-site")
        
        # 构建 URL
        base_url = "https://www.linkedin.com/jobs/search"
        params = f"?keywords={keyword.replace(' ', '%20')}"
        params += f"&location={location.replace(' ', '%20')}"
        params += "&f_TPR=r86400"  # Past 24 hours
        params += "&f_WT=2%2C3"     # Hybrid + On-site
        
        url = base_url + params
        print(f"  URL: {url}")
        
        await self.page.goto(url, wait_until="networkidle", timeout=60000)
        print("  → 页面加载中...")
        await asyncio.sleep(5)
        
        # 关键：先滚动到底部触发懒加载（像飞哥一样）
        print("  → 滚动触发懒加载...")
        for i in range(10):
            await self.page.evaluate("window.scrollBy(0, 800)")
            await asyncio.sleep(1)
        
        print("  ✓ 准备抓取")
        
        # 抓取职位
        jobs = await self._extract_jobs()
        return jobs
    
    async def _extract_jobs(self) -> List[Dict]:
        """提取职位 - 完全按照飞哥的JS代码逻辑"""
        jobs = []
        seen_links = set()
        
        print("\n  开始抓取职位...")
        
        # 使用飞哥提供的准确选择器
        items = await self.page.query_selector_all(
            ".jobs-search-results__list-item, li.occludable-update, .job-card-container"
        )
        
        print(f"    找到 {len(items)} 个职位卡片")
        
        for item in items:
            try:
                # 提取职位标题 - 飞哥的选择器
                title_el = await item.query_selector(
                    ".job-card-list__title, .artdeco-entity-lockup__title, .job-card-container__link"
                )
                if not title_el:
                    continue
                title = await title_el.inner_text()
                title = title.strip()
                
                # 提取公司名 - 飞哥的选择器
                company_el = await item.query_selector(
                    ".job-card-container__company-name, .artdeco-entity-lockup__subtitle, .job-card-container__company-link"
                )
                company = await company_el.inner_text() if company_el else "Unknown"
                company = company.strip()
                
                # 提取地点 - 飞哥的选择器
                location_el = await item.query_selector(
                    ".job-card-container__metadata-item, .artdeco-entity-lockup__caption"
                )
                location = await location_el.inner_text() if location_el else ""
                location = location.strip().replace("  ", " ")
                
                # 提取链接 - 飞哥的选择器
                link = ""
                link_el = await item.query_selector(
                    "a.job-card-list__title, a.artdeco-entity-lockup__title, a.job-card-container__link"
                )
                if link_el:
                    href = await link_el.get_attribute("href")
                    if href:
                        link = href.split('?')[0]
                
                # 去重判断 - 飞哥的逻辑
                if link and link not in seen_links:
                    seen_links.add(link)
                    
                    # 基础优先级逻辑
                    priority = "Medium"
                    lower_title = title.lower()
                    if any(kw in lower_title for kw in ["senior", "lead", "staff", "principal"]):
                        priority = "High"
                    if any(kw in lower_title for kw in ["quant", "machine learning", "ai"]):
                        priority = "High"
                    if any(kw in lower_title for kw in ["intern", "junior"]):
                        priority = "Low"
                    
                    job = {
                        "title": title,
                        "company": company,
                        "location": location,
                        "url": link,
                        "priority": priority,
                        "source": "LinkedIn",
                        "scraped_at": datetime.now().isoformat()
                    }
                    jobs.append(job)
                    print(f"  [{len(jobs)}] {title[:50]} @ {company[:25]}")
            
            except Exception as e:
                continue
        
        print(f"\n  ✓ 共抓取 {len(jobs)} 个职位")
        return jobs
    
    def save_jobs(self, jobs: List[Dict], keyword: str):
        """保存职位"""
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        safe_keyword = re.sub(r'[^\w\-]', '_', keyword.lower())[:20]
        filename = f"linkedin_{safe_keyword}_{date_str}.json"
        filepath = DATA_DIR / filename
        
        data = {
            "source": "LinkedIn",
            "search": keyword,
            "location": "Netherlands",
            "filters": {
                "date_posted": "Past 24 hours",
                "workplace_type": ["Hybrid", "On-site"]
            },
            "scraped_at": datetime.now().isoformat(),
            "total_jobs": len(jobs),
            "jobs": jobs
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n  ✓ 已保存 {len(jobs)} 个职位到: {filepath}")
        return filepath


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", default="data engineer")
    parser.add_argument("--location", default="Netherlands")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位爬虫 - 修复版")
    print("="*70)
    
    async with LinkedInScraperFixed(headless=args.headless) as scraper:
        await scraper.ensure_login()
        jobs = await scraper.search_jobs(args.search, args.location)
        scraper.save_jobs(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"✓ 完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
