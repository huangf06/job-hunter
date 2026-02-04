"""
LinkedIn 职位爬虫 - URL参数版（支持完整筛选）
================================================

通过 URL 参数直接应用所有筛选条件，无需点击 UI 元素：
- Past 24 hours (f_TPR=r86400)
- Hybrid + On-site (f_WT=2,3)

Usage:
    python linkedin_scraper_v2.py --search "data engineer"
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class LinkedInScraperV2:
    """LinkedIn 爬虫 V2 - URL参数版"""
    
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
    
    async def login(self) -> bool:
        """登录 LinkedIn"""
        print("[LinkedIn] 正在登录...")
        
        # 尝试加载 cookies
        if COOKIES_FILE.exists():
            print("  [INFO] 发现已保存的 cookies...")
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
            
            # 验证
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            if await self._is_logged_in():
                print("  [OK] 使用 cookies 登录成功！")
                return True
            else:
                print("  [WARN] Cookies 已过期，需要重新登录")
        
        # 手动登录
        print("  [INFO] 请手动登录 LinkedIn...")
        await self.page.goto("https://www.linkedin.com/login")
        
        print("  [WAIT] 等待登录完成（请在浏览器中完成登录）...")
        max_wait = 180
        for i in range(max_wait):
            await asyncio.sleep(1)
            if await self._is_logged_in():
                print("  [OK] 登录成功！")
                cookies = await self.context.cookies()
                COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
                print(f"  [OK] Cookies 已保存")
                return True
            if i % 10 == 0:
                print(f"  ... 等待中 ({i}s)")
        
        print("  [ERROR] 登录超时")
        return False
    
    async def _is_logged_in(self) -> bool:
        """检查登录状态"""
        try:
            url = self.page.url
            if '/feed' in url or '/in/' in url:
                return True
            # 检查是否有登录后的元素
            indicators = [
                "a[href='/jobs/']",
                ".global-nav__me",
                "[data-test-id='global-nav-search']"
            ]
            for selector in indicators:
                el = await self.page.query_selector(selector)
                if el:
                    return True
            return False
        except:
            return False
    
    async def search_with_filters(self, keyword: str, location: str = "Netherlands") -> List[Dict]:
        """
        使用 URL 参数直接搜索并应用筛选
        
        筛选参数:
        - f_TPR=r86400: Past 24 hours (86400秒 = 24小时)
        - f_WT=2,3: Hybrid (2) + On-site (3)
        - f_WT=1: Remote
        """
        print(f"\n[LinkedIn] 搜索: '{keyword}' in {location}")
        print("  [筛选] Past 24 hours + Hybrid/On-site")
        
        # 构建带筛选参数的 URL
        params = {
            "keywords": keyword,
            "location": location,
            "f_TPR": "r86400",      # Past 24 hours
            "f_WT": "2,3",          # Hybrid + On-site (2=Hybrid, 3=On-site)
            "sortBy": "DD"          # 按日期排序
        }
        
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
        print(f"  [URL] {url[:80]}...")
        
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)  # 等待页面完全加载
        
        print("  [OK] 页面已加载，开始抓取...")
        
        # 抓取所有职位
        jobs = await self._scrape_jobs()
        return jobs
    
    async def _scrape_jobs(self, max_jobs: int = 100) -> List[Dict]:
        """抓取职位列表"""
        jobs = []
        previous_count = 0
        no_change_count = 0
        scroll_attempts = 0
        max_scrolls = 20
        
        while len(jobs) < max_jobs and scroll_attempts < max_scrolls:
            # 获取当前页面上的职位卡片
            job_cards = await self._get_job_cards()
            
            new_jobs = 0
            for card in job_cards:
                if len(jobs) >= max_jobs:
                    break
                
                job = await self._parse_job_card(card)
                if job and not self._is_duplicate(jobs, job):
                    jobs.append(job)
                    new_jobs += 1
                    print(f"  [{len(jobs)}] {job['title']} @ {job['company']} | {job.get('workplace_type', 'N/A')}")
            
            # 检查是否有新内容
            if len(jobs) == previous_count:
                no_change_count += 1
            else:
                no_change_count = 0
            previous_count = len(jobs)
            
            # 如果没有新内容，多尝试几次后退出
            if no_change_count >= 3:
                print(f"  [INFO] 没有更多新职位，共抓取 {len(jobs)} 个")
                break
            
            # 滚动加载更多
            if len(jobs) < max_jobs:
                await self._scroll_down()
                scroll_attempts += 1
                await asyncio.sleep(2)
        
        return jobs
    
    async def _get_job_cards(self) -> List:
        """获取职位卡片元素"""
        selectors = [
            "[data-job-id]",
            ".jobs-search-results__list-item",
            ".job-card-container",
            ".scaffold-layout__list-item"
        ]
        
        for selector in selectors:
            cards = await self.page.query_selector_all(selector)
            if cards:
                return cards
        return []
    
    async def _parse_job_card(self, card) -> Optional[Dict]:
        """解析单个职位卡片"""
        try:
            # 标题
            title = await self._get_text(card, [
                "h3", "h2", ".job-card-list__title",
                "[data-test-id='job-card-title']"
            ])
            
            # 公司
            company = await self._get_text(card, [
                ".job-card-container__company-name",
                ".company-name",
                "[data-test-id='job-card-company']"
            ])
            
            # 地点
            location = await self._get_text(card, [
                ".job-card-container__metadata-item",
                ".location",
                "[data-test-id='job-card-location']"
            ])
            
            # 工作类型
            workplace = await self._get_text(card, [
                "[class*='workplace']",
                ".job-card-container__metadata-item:nth-child(2)"
            ])
            
            # 链接
            link_el = await card.query_selector("a")
            href = await link_el.get_attribute("href") if link_el else ""
            url = f"https://linkedin.com{href}" if href.startswith("/") else href
            
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
                    "workplace_type": workplace.strip() if workplace else "",
                    "url": url,
                    "posted_date": posted,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None
    
    async def _get_text(self, parent, selectors: List[str]) -> str:
        """从多个选择器获取文本"""
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
            existing = f"{job.get('title', '')}-{job.get('company', '')}"
            if key == existing:
                return True
        return False
    
    async def _scroll_down(self):
        """向下滚动"""
        await self.page.evaluate("window.scrollBy(0, 800)")
    
    def save_results(self, jobs: List[Dict], keyword: str) -> Path:
        """保存结果"""
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        safe_keyword = re.sub(r'[^\w\-]', '_', keyword.lower())[:20]
        filename = f"linkedin_filtered_{safe_keyword}_{date_str}.json"
        
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
        
        print(f"\n[OK] 结果已保存: {filepath}")
        return filepath


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn 职位爬虫 V2")
    parser.add_argument("--search", default="data engineer", help="搜索关键词")
    parser.add_argument("--location", default="Netherlands", help="地点")
    parser.add_argument("--max-jobs", type=int, default=50, help="最大数量")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位爬虫 V2 - URL参数版")
    print("="*70)
    print(f"搜索: {args.search}")
    print(f"地点: {args.location}")
    print(f"筛选: Past 24 hours + Hybrid/On-site")
    print("="*70)
    
    async with LinkedInScraperV2(headless=args.headless) as scraper:
        # 登录
        if not await scraper.login():
            print("[ERROR] 登录失败")
            return
        
        # 搜索（带筛选）
        jobs = await scraper.search_with_filters(args.search, args.location)
        
        # 保存
        scraper.save_results(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
