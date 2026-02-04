"""
LinkedIn 职位爬虫 - 完善版
===========================

基于人工验证的页面结构，使用正确的选择器抓取职位

Usage:
    python linkedin_scraper_pro.py --search "data engineer"
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


class LinkedInScraperPro:
    """LinkedIn 职位爬虫 - 完善版"""
    
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
    
    async def search_jobs(self, keyword: str, location: str = "Netherlands", max_jobs: int = 50):
        """搜索职位"""
        print(f"\n[LinkedIn] 搜索: '{keyword}' in {location}")
        print("  筛选: Past 24 hours + Hybrid/On-site")
        
        # 构建 URL
        base_url = "https://www.linkedin.com/jobs/search"
        params = f"?keywords={keyword.replace(' ', '%20')}"
        params += f"&location={location.replace(' ', '%20')}"
        params += "&f_TPR=r86400"  # Past 24 hours
        params += "&f_WT=2%2C3"     # Hybrid + On-site
        params += "&sortBy=DD"      # 按日期排序
        
        url = base_url + params
        print(f"  URL: {url[:80]}...")
        
        await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        print("  → 等待页面加载...")
        await asyncio.sleep(5)
        
        # 等待职位列表
        try:
            await self.page.wait_for_selector(".jobs-search-results__list-item", timeout=15000)
            print("  ✓ 职位列表已加载")
        except:
            print("  ! 等待超时，继续尝试...")
        
        # 抓取职位
        jobs = await self._extract_jobs(max_jobs)
        return jobs
    
    async def _extract_jobs(self, max_jobs: int) -> List[Dict]:
        """提取职位信息 - 支持翻页"""
        jobs = []
        seen_urls = set()
        no_new_count = 0
        
        print("\n  开始抓取职位...")
        
        for scroll in range(30):  # 最多滚动30次
            # 使用人工验证的选择器
            cards = await self.page.query_selector_all(".jobs-search-results__list-item")
            
            if not cards:
                cards = await self.page.query_selector_all("li.occludable-update")
            
            if not cards:
                cards = await self.page.query_selector_all(".job-card-container")
            
            print(f"    滚动 {scroll+1}: 找到 {len(cards)} 个卡片")
            
            new_in_this_scroll = 0
            for card in cards:
                if len(jobs) >= max_jobs:
                    break
                
                try:
                    job = await self._parse_job_card(card)
                    if job:
                        # 去重
                        url_clean = job['url'].split('?')[0]
                        if url_clean not in seen_urls:
                            seen_urls.add(url_clean)
                            jobs.append(job)
                            new_in_this_scroll += 1
                            print(f"  [{len(jobs)}] {job['title'][:45]} @ {job['company'][:25]}")
                except Exception as e:
                    continue
            
            if len(jobs) >= max_jobs:
                break
            
            # 检查是否有新职位加载
            if new_in_this_scroll == 0:
                no_new_count += 1
                # 尝试点击 "Show more" 或 "See more jobs" 按钮
                if no_new_count >= 2:
                    clicked = await self._click_show_more()
                    if clicked:
                        no_new_count = 0
                        await asyncio.sleep(3)
                        continue
                    # 如果没有按钮可点击，且连续3次没有新内容，结束
                    if no_new_count >= 3:
                        print(f"    没有更多新职位，结束抓取")
                        break
            else:
                no_new_count = 0
            
            # 滚动加载更多
            await self.page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)
            
            # 每5次滚动尝试点击一次"Show more"
            if scroll > 0 and scroll % 5 == 0:
                await self._click_show_more()
                await asyncio.sleep(2)
        
        print(f"\n  ✓ 共抓取 {len(jobs)} 个职位")
        return jobs
    
    async def _click_show_more(self) -> bool:
        """点击 'Show more' 或 'See more jobs' 按钮加载更多"""
        try:
            # 尝试多种可能的按钮文本
            button_selectors = [
                "button:has-text('Show more')",
                "button:has-text('See more jobs')",
                "button:has-text('Load more')",
                "button:has-text('More jobs')",
                "[aria-label*='Show more']",
                "[aria-label*='See more']",
                ".jobs-search-results__pagination-button",
                "button.artdeco-button--secondary"
            ]
            
            for selector in button_selectors:
                try:
                    button = await self.page.query_selector(selector)
                    if button:
                        # 检查按钮是否可见
                        is_visible = await button.is_visible()
                        if is_visible:
                            await button.click()
                            print(f"    点击了 'Show more' 按钮")
                            return True
                except:
                    continue
            
            return False
        except:
            return False
    
    async def _parse_job_card(self, card) -> Optional[Dict]:
        """解析职位卡片 - 基于人工验证的结构"""
        try:
            # 标题 - 使用人工验证的选择器
            title = ""
            for selector in [
                ".job-card-list__title",
                ".artdeco-entity-lockup__title",
                ".job-card-container__link"
            ]:
                el = await card.query_selector(selector)
                if el:
                    title = await el.inner_text()
                    if title.strip():
                        break
            
            # 公司
            company = ""
            for selector in [
                ".job-card-container__company-name",
                ".artdeco-entity-lockup__subtitle",
                ".job-card-container__company-link"
            ]:
                el = await card.query_selector(selector)
                if el:
                    company = await el.inner_text()
                    if company.strip():
                        break
            
            # 地点
            location = ""
            for selector in [
                ".job-card-container__metadata-item",
                ".artdeco-entity-lockup__caption"
            ]:
                el = await card.query_selector(selector)
                if el:
                    location = await el.inner_text()
                    if location.strip():
                        break
            
            # 链接
            url = ""
            for selector in [
                "a.job-card-list__title",
                "a.artdeco-entity-lockup__title",
                "a.job-card-container__link"
            ]:
                el = await card.query_selector(selector)
                if el:
                    href = await el.get_attribute("href")
                    if href:
                        url = href.split('?')[0]  # 清理参数
                        break
            
            # 发布时间
            posted = ""
            time_el = await card.query_selector("time")
            if time_el:
                posted = await time_el.get_attribute("datetime") or ""
            
            # 清理数据
            title = title.strip().replace("\n", " ")
            company = company.strip().replace("\n", " ")
            location = location.strip().replace("\n", " ").replace("  ", " ")
            
            # 过滤无效数据
            if title and company and url:
                # 排除 "with verification" 混入公司名的情况
                if "with verification" in company and company.startswith(title.split()[0]):
                    company = company.replace(title, "").replace("with verification", "").strip()
                
                return {
                    "title": title,
                    "company": company,
                    "location": location,
                    "url": url,
                    "posted_date": posted,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except Exception as e:
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
    parser.add_argument("--max-jobs", type=int, default=50)
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位爬虫 - 完善版")
    print("="*70)
    
    async with LinkedInScraperPro(headless=args.headless) as scraper:
        await scraper.ensure_login()
        jobs = await scraper.search_jobs(args.search, args.location, args.max_jobs)
        scraper.save_jobs(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"✓ 完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
