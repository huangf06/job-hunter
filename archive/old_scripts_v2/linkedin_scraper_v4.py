"""
LinkedIn 职位爬虫 V4 - 简化稳定版
===================================

直接使用 URL 参数完成所有操作:
1. 登录 (使用 cookies)
2. 直接访问带筛选参数的搜索 URL
3. 抓取职位列表

筛选参数:
- f_TPR=r86400: Past 24 hours
- f_WT=2,3: Hybrid + On-site
- sortBy=DD: 按日期排序

Usage:
    python linkedin_scraper_v4.py --search "data engineer"
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class LinkedInScraperV4:
    """LinkedIn 爬虫 V4 - 简化稳定版"""
    
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
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
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
    
    async def login_with_cookies(self) -> bool:
        """使用 cookies 登录"""
        print("[LinkedIn] 正在登录...")
        
        if not COOKIES_FILE.exists():
            print("  ✗ 未找到 cookies 文件，请先手动登录一次")
            return await self.manual_login()
        
        try:
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
            
            # 验证登录
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(2)
            
            # 简单检查
            if "/feed" in self.page.url:
                print("  ✓ 登录成功")
                return True
            else:
                print("  ✗ Cookies 已过期")
                return await self.manual_login()
                
        except Exception as e:
            print(f"  ✗ 登录失败: {e}")
            return await self.manual_login()
    
    async def manual_login(self) -> bool:
        """手动登录"""
        print("  → 请手动登录 LinkedIn...")
        await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        
        input("登录完成后请按回车继续...")
        
        # 保存 cookies
        try:
            cookies = await self.context.cookies()
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            print("  ✓ Cookies 已保存")
            return True
        except Exception as e:
            print(f"  ! 保存 cookies 失败: {e}")
            return True  # 仍然继续
    
    async def scrape_jobs(self, keyword: str, location: str = "Netherlands", max_jobs: int = 50) -> List[Dict]:
        """抓取职位"""
        print(f"\n[LinkedIn] 搜索: '{keyword}' in {location}")
        print("  筛选: Past 24 hours + Hybrid/On-site")
        
        # 构建带筛选的 URL
        params = {
            "keywords": keyword,
            "location": location,
            "f_TPR": "r86400",      # Past 24 hours
            "f_WT": "2,3",          # Hybrid + On-site
            "sortBy": "DD"          # 按日期排序
        }
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
        
        print(f"  URL: {url[:70]}...")
        
        # 访问页面
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print("  → 页面加载中...")
        await asyncio.sleep(5)  # 等待初始加载
        
        jobs = []
        previous_count = 0
        no_change_count = 0
        
        print("\n  开始抓取职位...")
        
        while len(jobs) < max_jobs and no_change_count < 3:
            # 获取职位卡片
            cards = await self._get_job_cards()
            
            if not cards:
                print(f"    未找到职位卡片，尝试滚动...")
                await self._scroll_down()
                await asyncio.sleep(2)
                no_change_count += 1
                continue
            
            new_jobs = 0
            for card in cards:
                if len(jobs) >= max_jobs:
                    break
                
                job = await self._parse_card(card)
                if job and not self._is_duplicate(jobs, job):
                    jobs.append(job)
                    new_jobs += 1
                    print(f"  [{len(jobs)}] {job['title'][:45]} @ {job['company'][:25]}")
            
            # 检查是否有新内容
            if len(jobs) == previous_count:
                no_change_count += 1
            else:
                no_change_count = 0
            previous_count = len(jobs)
            
            # 滚动加载更多
            if len(jobs) < max_jobs:
                await self._scroll_down()
                await asyncio.sleep(2)
        
        print(f"\n  ✓ 共抓取 {len(jobs)} 个职位")
        return jobs
    
    async def _get_job_cards(self) -> List:
        """获取职位卡片"""
        # 尝试多种选择器
        selectors = [
            ".jobs-search-results__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
            "[data-job-id]"
        ]
        
        for selector in selectors:
            try:
                cards = await self.page.query_selector_all(selector)
                if cards and len(cards) > 0:
                    return cards
            except:
                continue
        return []
    
    async def _parse_card(self, card) -> Optional[Dict]:
        """解析职位卡片"""
        try:
            # 标题
            title = await self._get_text(card, [
                "h3 strong",
                ".job-card-list__title",
                "a[class*='title']"
            ])
            
            # 公司
            company = await self._get_text(card, [
                ".job-card-container__company-name",
                "[class*='company-name']"
            ])
            
            # 地点
            location = await self._get_text(card, [
                ".job-card-container__metadata-item",
                "[class*='metadata']"
            ])
            
            # 链接
            link_el = await card.query_selector("a")
            href = await link_el.get_attribute("href") if link_el else ""
            url = f"https://www.linkedin.com{href}" if href.startswith("/") else href
            
            # 发布时间
            posted = ""
            time_el = await card.query_selector("time")
            if time_el:
                posted = await time_el.get_attribute("datetime") or ""
            
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
    
    async def _get_text(self, parent, selectors: List[str]) -> str:
        """获取文本"""
        for selector in selectors:
            try:
                el = await parent.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if text.strip():
                        return text.strip()
            except:
                continue
        return ""
    
    def _is_duplicate(self, jobs: List[Dict], new_job: Dict) -> bool:
        """检查重复"""
        key = f"{new_job.get('title', '')}-{new_job.get('company', '')}"
        for job in jobs:
            if f"{job.get('title', '')}-{job.get('company', '')}" == key:
                return True
        return False
    
    async def _scroll_down(self):
        """滚动"""
        await self.page.evaluate("window.scrollBy(0, 800)")
    
    def save(self, jobs: List[Dict], keyword: str) -> Path:
        """保存结果"""
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        safe = re.sub(r'[^\w\-]', '_', keyword.lower())[:20]
        filename = f"linkedin_{safe}_{date_str}.json"
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
        
        print(f"\n  ✓ 已保存: {filepath}")
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
    print("LinkedIn 职位爬虫 V4")
    print("="*70)
    
    async with LinkedInScraperV4(headless=args.headless) as scraper:
        # 登录
        if not await scraper.login_with_cookies():
            print("✗ 登录失败")
            return
        
        # 抓取
        jobs = await scraper.scrape_jobs(args.search, args.location, args.max_jobs)
        
        # 保存
        scraper.save(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"✓ 完成！共 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
