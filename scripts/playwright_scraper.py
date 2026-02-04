"""
Playwright 职位爬虫 - 实际抓取实现
=====================================

使用 Playwright 自动化浏览器抓取职位信息。
支持：LinkedIn, IamExpat, Indeed NL

Usage:
    python playwright_scraper.py --platform linkedin --search "data scientist"
    python playwright_scraper.py --platform iamexpat --search "machine learning"
    python playwright_scraper.py --daily
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright, Page

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LEADS_DIR = DATA_DIR / "leads"

# 确保目录存在
LEADS_DIR.mkdir(parents=True, exist_ok=True)


class PlaywrightJobScraper:
    """Playwright 职位爬虫"""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
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
    
    # ============================================================
    # LinkedIn 爬虫
    # ============================================================
    
    async def scrape_linkedin(self, search_term: str, location: str = "Netherlands", max_jobs: int = 25) -> List[Dict]:
        """抓取 LinkedIn 职位"""
        print(f"[LinkedIn] Searching for '{search_term}' in {location}...")
        
        # 构建搜索 URL
        params = {
            "keywords": search_term,
            "location": location,
            "f_TPR": "r604800",  # 过去一周
            "sortBy": "DD"  # 按日期排序
        }
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
        
        jobs = []
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)  # 等待页面加载
            
            # 滚动页面加载更多职位
            for _ in range(5):
                await self.page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(1)
            
            # 尝试多种选择器
            selectors = [
                "[data-job-id]",
                ".jobs-search__results-list > li",
                ".job-card-container",
                ".base-card",
                ".jobs-search-results__list-item"
            ]
            
            job_cards = []
            for selector in selectors:
                job_cards = await self.page.query_selector_all(selector)
                if job_cards:
                    print(f"[LinkedIn] Using selector: {selector}")
                    break
            print(f"[LinkedIn] Found {len(job_cards)} job cards")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job = await self._parse_linkedin_job_card(card)
                    if job:
                        jobs.append(job)
                        print(f"  [{i+1}] {job['title']} @ {job['company']}")
                except Exception as e:
                    print(f"  Error parsing card {i+1}: {e}")
                    continue
                
                await asyncio.sleep(0.5)  # 避免请求过快
            
        except Exception as e:
            print(f"[LinkedIn] Error: {e}")
        
        print(f"[LinkedIn] Successfully scraped {len(jobs)} jobs")
        return jobs
    
    async def _parse_linkedin_job_card(self, card) -> Optional[Dict]:
        """解析 LinkedIn 职位卡片"""
        try:
            # 尝试多种选择器获取标题
            title = ""
            for title_selector in ["h3", "h2", ".job-card-list__title", ".base-card__title", "[class*='title']"]:
                title_el = await card.query_selector(title_selector)
                if title_el:
                    title = await title_el.inner_text()
                    if title.strip():
                        break
            
            # 尝试多种选择器获取公司
            company = ""
            for company_selector in [".job-card-container__company-name", ".base-card__subtitle", ".company-name", "[class*='company']", "[class*='subtitle']"]:
                company_el = await card.query_selector(company_selector)
                if company_el:
                    company = await company_el.inner_text()
                    if company.strip():
                        break
            
            # 尝试多种选择器获取地点
            location = ""
            for loc_selector in [".job-card-container__metadata-item", ".base-card__metadata", "[class*='location']", "[class*='metadata']"]:
                location_el = await card.query_selector(loc_selector)
                if location_el:
                    location = await location_el.inner_text()
                    if location.strip():
                        break
            
            # 链接
            link_el = await card.query_selector("a")
            href = await link_el.get_attribute("href") if link_el else ""
            url = f"https://linkedin.com{href}" if href.startswith("/") else href
            
            # 发布时间
            posted = ""
            for time_selector in ["time", "[class*='date']", "[class*='time']"]:
                time_el = await card.query_selector(time_selector)
                if time_el:
                    posted = await time_el.get_attribute("datetime") or await time_el.inner_text()
                    if posted:
                        break
            
            return {
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "url": url,
                "posted_date": posted,
                "source": "LinkedIn",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    async def scrape_linkedin_job_detail(self, url: str) -> Optional[Dict]:
        """抓取 LinkedIn 职位详情"""
        print(f"[LinkedIn] Fetching job detail: {url}")
        
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # 获取详细描述
            description_el = await self.page.query_selector(".description__text")
            description = await description_el.inner_text() if description_el else ""
            
            # 获取要求
            requirements_el = await self.page.query_selector("[data-test-id='job-requirements']")
            requirements = await requirements_el.inner_text() if requirements_el else ""
            
            return {
                "description": description.strip(),
                "requirements": requirements.strip(),
                "detail_url": url
            }
        except Exception as e:
            print(f"[LinkedIn] Error fetching detail: {e}")
            return None
    
    # ============================================================
    # IamExpat 爬虫
    # ============================================================
    
    async def scrape_iamexpat(self, search_term: str, max_jobs: int = 25) -> List[Dict]:
        """抓取 IamExpat 职位"""
        print(f"[IamExpat] Searching for '{search_term}'...")
        
        # 构建搜索 URL
        search_slug = search_term.replace(" ", "-").lower()
        url = f"https://www.iamexpat.nl/career/jobs-netherlands/{search_slug}"
        
        jobs = []
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # 尝试多种选择器
            selectors = [
                ".job-item",
                ".views-row",
                ".node-job",
                ".job-listing",
                "[class*='job']"
            ]
            
            job_cards = []
            for selector in selectors:
                job_cards = await self.page.query_selector_all(selector)
                if job_cards:
                    print(f"[IamExpat] Using selector: {selector}")
                    break
            
            print(f"[IamExpat] Found {len(job_cards)} job cards")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job = await self._parse_iamexpat_job_card(card)
                    if job:
                        jobs.append(job)
                        print(f"  [{i+1}] {job['title']} @ {job['company']}")
                except Exception as e:
                    print(f"  Error parsing card {i+1}: {e}")
                    continue
                
                await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"[IamExpat] Error: {e}")
        
        print(f"[IamExpat] Successfully scraped {len(jobs)} jobs")
        return jobs
    
    async def _parse_iamexpat_job_card(self, card) -> Optional[Dict]:
        """解析 IamExpat 职位卡片"""
        try:
            # 标题 - 尝试多种选择器
            title = ""
            url = ""
            for title_selector in ["h2 a", "h3 a", ".job-title a", "a[href*='job']", "a"]:
                title_el = await card.query_selector(title_selector)
                if title_el:
                    title = await title_el.inner_text()
                    href = await title_el.get_attribute("href")
                    if href:
                        url = f"https://www.iamexpat.nl{href}" if href.startswith("/") else href
                    if title.strip():
                        break
            
            # 公司
            company = ""
            for company_selector in [".company-name", ".field-name-field-company", "[class*='company']"]:
                company_el = await card.query_selector(company_selector)
                if company_el:
                    company = await company_el.inner_text()
                    if company.strip():
                        break
            
            # 地点
            location = ""
            for loc_selector in [".location", ".field-name-field-location", "[class*='location']"]:
                location_el = await card.query_selector(loc_selector)
                if location_el:
                    location = await location_el.inner_text()
                    if location.strip():
                        break
            
            return {
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "url": url,
                "posted_date": "",
                "source": "IamExpat",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            return None
    
    async def scrape_iamexpat_job_detail(self, url: str) -> Optional[Dict]:
        """抓取 IamExpat 职位详情"""
        print(f"[IamExpat] Fetching job detail: {url}")
        
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)
            await asyncio.sleep(2)
            
            # 获取详细描述
            description_el = await self.page.query_selector(".job-description, .field-name-body")
            description = await description_el.inner_text() if description_el else ""
            
            # 获取要求
            requirements_el = await self.page.query_selector(".requirements, .field-name-field-requirements")
            requirements = await requirements_el.inner_text() if requirements_el else ""
            
            return {
                "description": description.strip(),
                "requirements": requirements.strip(),
                "detail_url": url
            }
        except Exception as e:
            print(f"[IamExpat] Error fetching detail: {e}")
            return None
    
    # ============================================================
    # Indeed NL 爬虫
    # ============================================================
    
    async def scrape_indeed(self, search_term: str, location: str = "Netherlands", max_jobs: int = 25) -> List[Dict]:
        """抓取 Indeed NL 职位"""
        print(f"[Indeed] Searching for '{search_term}' in {location}...")
        
        # 构建搜索 URL
        params = {
            "q": search_term,
            "l": location,
            "sort": "date"
        }
        url = f"https://nl.indeed.com/jobs?{urlencode(params)}"
        
        jobs = []
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # 尝试多种选择器
            selectors = [
                "[data-jk]",
                ".slider_container",
                ".job_seen_beacon",
                ".result",
                "[class*='job']"
            ]
            
            job_cards = []
            for selector in selectors:
                job_cards = await self.page.query_selector_all(selector)
                if job_cards:
                    print(f"[Indeed] Using selector: {selector}")
                    break
            
            print(f"[Indeed] Found {len(job_cards)} job cards")
            
            for i, card in enumerate(job_cards[:max_jobs]):
                try:
                    job = await self._parse_indeed_job_card(card)
                    if job:
                        jobs.append(job)
                        print(f"  [{i+1}] {job['title']} @ {job['company']}")
                except Exception as e:
                    print(f"  Error parsing card {i+1}: {e}")
                    continue
                
                await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"[Indeed] Error: {e}")
        
        print(f"[Indeed] Successfully scraped {len(jobs)} jobs")
        return jobs
    
    async def _parse_indeed_job_card(self, card) -> Optional[Dict]:
        """解析 Indeed 职位卡片"""
        try:
            # 标题
            title = ""
            for title_selector in ["h2 a", ".jobTitle a", "a[href*='job']", "a"]:
                title_el = await card.query_selector(title_selector)
                if title_el:
                    title = await title_el.get_attribute("title")
                    if not title:
                        title = await title_el.inner_text()
                    if title.strip():
                        break
            
            # 公司
            company = ""
            for company_selector in [".companyName", "[data-testid='company-name']", ".company", "[class*='company']"]:
                company_el = await card.query_selector(company_selector)
                if company_el:
                    company = await company_el.inner_text()
                    if company.strip():
                        break
            
            # 地点
            location = ""
            for loc_selector in [".companyLocation", "[data-testid='text-location']", ".location", "[class*='location']"]:
                location_el = await card.query_selector(loc_selector)
                if location_el:
                    location = await location_el.inner_text()
                    if location.strip():
                        break
            
            # 链接
            url = ""
            for link_selector in ["h2 a", ".jobTitle a", "a[href*='job']", "a"]:
                link_el = await card.query_selector(link_selector)
                if link_el:
                    href = await link_el.get_attribute("href")
                    if href:
                        url = f"https://nl.indeed.com{href}" if href.startswith("/") else href
                        break
            
            return {
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "url": url,
                "posted_date": "",
                "source": "Indeed",
                "scraped_at": datetime.now().isoformat()
            }
        except Exception as e:
            return None


# ============================================================
# 工具函数
# ============================================================

def save_scrape_results(jobs: List[Dict], platform: str, search_term: str) -> Path:
    """保存抓取结果"""
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_term = re.sub(r'[^\w\-]', '_', search_term.lower())[:20]
    filename = f"{platform}_{safe_term}_{date_str}.json"
    
    filepath = DATA_DIR / filename
    
    data = {
        "source": platform,
        "search": search_term,
        "scraped_at": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "jobs": jobs
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Saved {len(jobs)} jobs to {filepath}")
    return filepath


def load_scrape_results(filepath: Path) -> List[Dict]:
    """加载抓取结果"""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("jobs", [])


# ============================================================
# CLI 入口
# ============================================================

async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Playwright Job Scraper")
    parser.add_argument("--platform", choices=["linkedin", "iamexpat", "indeed"], help="Platform to scrape")
    parser.add_argument("--search", default="data scientist", help="Search term")
    parser.add_argument("--location", default="Netherlands", help="Location")
    parser.add_argument("--max-jobs", type=int, default=25, help="Maximum jobs to scrape")
    parser.add_argument("--visible", action="store_true", help="Show browser window")
    parser.add_argument("--daily", action="store_true", help="Run daily scrape for all searches")
    
    args = parser.parse_args()
    
    if args.daily:
        # 每日全量抓取
        search_terms = [
            "data scientist",
            "machine learning engineer",
            "data engineer",
            "quantitative researcher",
            "AI engineer"
        ]
        
        all_jobs = []
        async with PlaywrightJobScraper(headless=not args.visible) as scraper:
            for term in search_terms:
                # LinkedIn
                jobs = await scraper.scrape_linkedin(term, args.location, args.max_jobs)
                all_jobs.extend(jobs)
                await asyncio.sleep(2)
                
                # IamExpat
                jobs = await scraper.scrape_iamexpat(term, args.max_jobs)
                all_jobs.extend(jobs)
                await asyncio.sleep(2)
        
        # 去重
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job.get('title', '')}-{job.get('company', '')}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        save_scrape_results(unique_jobs, "daily", "all_terms")
        print(f"\n[Daily] Total unique jobs: {len(unique_jobs)}")
    
    elif args.platform:
        async with PlaywrightJobScraper(headless=not args.visible) as scraper:
            if args.platform == "linkedin":
                jobs = await scraper.scrape_linkedin(args.search, args.location, args.max_jobs)
            elif args.platform == "iamexpat":
                jobs = await scraper.scrape_iamexpat(args.search, args.max_jobs)
            elif args.platform == "indeed":
                jobs = await scraper.scrape_indeed(args.search, args.location, args.max_jobs)
            
            save_scrape_results(jobs, args.platform, args.search)
    
    else:
        print("Playwright Job Scraper")
        print("=" * 50)
        print("Usage examples:")
        print("  python playwright_scraper.py --platform linkedin --search 'data scientist'")
        print("  python playwright_scraper.py --platform iamexpat --search 'machine learning'")
        print("  python playwright_scraper.py --daily")
        print()
        print("Options:")
        print("  --platform {linkedin,iamexpat,indeed}  选择平台")
        print("  --search <term>                        搜索关键词")
        print("  --location <location>                  地点 (默认: Netherlands)")
        print("  --max-jobs <n>                         最大抓取数量")
        print("  --visible                              显示浏览器窗口")
        print("  --daily                                运行每日全量抓取")


if __name__ == "__main__":
    asyncio.run(main())
