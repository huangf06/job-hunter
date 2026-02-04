"""
LinkedIn 职位抓取 - 最终版
============================

使用最可靠的方法抓取 LinkedIn 职位
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


class LinkedInJobScraper:
    """LinkedIn 职位抓取器"""
    
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
        
        # 加载 cookies
        if COOKIES_FILE.exists():
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
        
        # 访问 feed 检查登录状态
        await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
        await asyncio.sleep(2)
        
        if "login" in self.page.url or "signup" in self.page.url:
            print("  → 需要登录，请在浏览器中完成登录")
            await self.page.goto("https://www.linkedin.com/login")
            input("登录完成后按回车...")
            
            # 保存 cookies
            cookies = await self.context.cookies()
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f, indent=2)
            print("  ✓ Cookies 已保存")
        else:
            print("  ✓ 已登录")
    
    async def search_jobs(self, keyword: str, location: str = "Netherlands", max_jobs: int = 50):
        """搜索职位"""
        print(f"\n[LinkedIn] 搜索: '{keyword}' in {location}")
        print("  筛选: Past 24 hours + Hybrid/On-site")
        
        # 构建 URL (使用 LinkedIn 的筛选参数)
        base_url = "https://www.linkedin.com/jobs/search"
        params = f"?keywords={keyword.replace(' ', '%20')}"
        params += f"&location={location.replace(' ', '%20')}"
        params += "&f_TPR=r86400"  # Past 24 hours
        params += "&f_WT=2%2C3"     # Hybrid + On-site
        params += "&sortBy=DD"      # 按日期排序
        
        url = base_url + params
        print(f"  URL: {url[:80]}...")
        
        # 访问页面
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print("  → 等待页面加载...")
        await asyncio.sleep(5)
        
        # 等待职位列表出现
        print("  → 等待职位列表...")
        try:
            await self.page.wait_for_selector(".jobs-search-results__list-item", timeout=15000)
        except:
            print("  ! 等待超时，尝试其他选择器...")
        
        # 抓取职位
        jobs = await self._extract_jobs(max_jobs)
        return jobs
    
    async def _extract_jobs(self, max_jobs: int) -> List[Dict]:
        """提取职位信息"""
        jobs = []
        seen = set()
        
        for scroll in range(10):  # 最多滚动10次
            # 获取当前所有职位卡片
            cards = await self.page.query_selector_all(".jobs-search-results__list-item")
            
            if not cards:
                # 尝试其他选择器
                cards = await self.page.query_selector_all("li[data-occludable-job-id]")
            
            print(f"    滚动 {scroll+1}: 找到 {len(cards)} 个卡片")
            
            for card in cards:
                if len(jobs) >= max_jobs:
                    break
                
                try:
                    # 获取职位 ID (用于去重)
                    job_id = await card.get_attribute("data-occludable-job-id") or ""
                    if job_id in seen:
                        continue
                    seen.add(job_id)
                    
                    # 解析职位信息
                    job = await self._parse_job_card(card)
                    if job:
                        jobs.append(job)
                        print(f"  [{len(jobs)}] {job['title'][:45]} @ {job['company'][:25]}")
                except Exception as e:
                    continue
            
            if len(jobs) >= max_jobs:
                break
            
            # 滚动加载更多
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)
        
        return jobs
    
    async def _parse_job_card(self, card) -> Optional[Dict]:
        """解析单个职位卡片"""
        try:
            # 获取所有文本内容
            full_text = await card.inner_text()
            
            # 使用多种方式提取信息
            # 标题
            title_el = await card.query_selector("h3 strong, .job-card-list__title")
            title = await title_el.inner_text() if title_el else ""
            
            # 公司
            company_el = await card.query_selector(".job-card-container__company-name")
            company = await company_el.inner_text() if company_el else ""
            
            # 如果上面的选择器失败，尝试从文本中提取
            if not title or not company:
                lines = [l.strip() for l in full_text.split('\n') if l.strip()]
                if len(lines) >= 2:
                    if not title:
                        title = lines[0]
                    if not company:
                        company = lines[1]
            
            # 地点
            location_el = await card.query_selector(".job-card-container__metadata-item")
            location = await location_el.inner_text() if location_el else ""
            
            # 链接
            link_el = await card.query_selector("a")
            href = await link_el.get_attribute("href") if link_el else ""
            url = f"https://www.linkedin.com{href}" if href.startswith("/") else href
            
            # 发布时间
            time_el = await card.query_selector("time")
            posted = await time_el.get_attribute("datetime") if time_el else ""
            
            if title and company:
                return {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "url": url,
                    "posted_date": posted,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except:
            pass
        return None
    
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
    parser.add_argument("--max-jobs", type=int, default=30)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位抓取器")
    print("="*70)
    
    async with LinkedInJobScraper(headless=args.headless) as scraper:
        # 确保登录
        await scraper.ensure_login()
        
        # 搜索职位
        jobs = await scraper.search_jobs(args.search, args.location, args.max_jobs)
        
        # 保存
        scraper.save_jobs(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
