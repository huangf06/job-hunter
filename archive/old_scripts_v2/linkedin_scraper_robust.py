"""
LinkedIn 职位爬虫 - 稳健版
===========================

模拟人工操作，增加等待时间，确保页面完全响应

关键改进：
1. 使用更长的等待时间
2. 逐步滚动，模拟人工浏览
3. 检查元素是否可见
4. 多次重试机制
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class LinkedInScraperRobust:
    """LinkedIn 职位爬虫 - 稳健版"""
    
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
        await asyncio.sleep(3)
        
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
        """搜索职位 - 稳健版"""
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
        
        # 访问页面 - 使用更长的超时
        print("\n  [步骤 1/4] 访问页面...")
        try:
            await self.page.goto(url, wait_until="networkidle", timeout=90000)
            print("  ✓ 页面已加载")
        except PlaywrightTimeout:
            print("  ! 页面加载超时，但继续尝试...")
        
        # 等待初始渲染
        print("\n  [步骤 2/4] 等待初始渲染 (5秒)...")
        await asyncio.sleep(5)
        
        # 检查职位列表是否出现
        print("\n  [步骤 3/4] 检查职位列表...")
        max_retries = 3
        for attempt in range(max_retries):
            items = await self.page.query_selector_all(".jobs-search-results__list-item")
            print(f"    尝试 {attempt + 1}: 找到 {len(items)} 个职位卡片")
            
            if len(items) >= 5:
                print(f"  ✓ 职位列表已就绪")
                break
            
            print(f"    等待 3 秒后重试...")
            await asyncio.sleep(3)
        
        # 关键：逐步滚动触发懒加载
        print("\n  [步骤 4/4] 逐步滚动触发懒加载...")
        await self._gradual_scroll()
        
        # 抓取职位
        jobs = await self._extract_jobs()
        return jobs
    
    async def _gradual_scroll(self):
        """逐步滚动，模拟人工浏览"""
        print("    开始滚动...")
        
        # 分 15 次滚动，每次滚动后等待
        for i in range(15):
            # 滚动一屏
            await self.page.evaluate("window.scrollBy(0, 600)")
            
            # 每 3 次滚动后检查职位数量
            if (i + 1) % 3 == 0:
                items = await self.page.query_selector_all(".jobs-search-results__list-item")
                print(f"      滚动 {i + 1}/15: 当前有 {len(items)} 个职位卡片")
            
            # 等待时间递增，模拟人工浏览速度
            wait_time = 1.5 + (i * 0.1)
            await asyncio.sleep(wait_time)
        
        # 最后再等待一下确保所有内容加载
        print("    等待最终加载 (3秒)...")
        await asyncio.sleep(3)
        
        # 最终检查
        items = await self.page.query_selector_all(".jobs-search-results__list-item")
        print(f"  ✓ 滚动完成，共找到 {len(items)} 个职位卡片")
    
    async def _extract_jobs(self) -> List[Dict]:
        """提取职位信息"""
        jobs = []
        seen_links = set()
        
        print("\n  开始解析职位...")
        
        # 使用飞哥提供的准确选择器
        items = await self.page.query_selector_all(
            ".jobs-search-results__list-item, li.occludable-update, .job-card-container"
        )
        
        print(f"    处理 {len(items)} 个职位卡片...")
        
        success_count = 0
        fail_count = 0
        
        for idx, item in enumerate(items, 1):
            try:
                # 提取职位标题
                title_el = await item.query_selector(
                    ".job-card-list__title, .artdeco-entity-lockup__title, .job-card-container__link"
                )
                if not title_el:
                    fail_count += 1
                    continue
                
                title = await title_el.inner_text()
                title = title.strip() if title else ""
                
                # 提取公司名
                company_el = await item.query_selector(
                    ".job-card-container__company-name, .artdeco-entity-lockup__subtitle, .job-card-container__company-link"
                )
                company = ""
                if company_el:
                    company = await company_el.inner_text()
                    company = company.strip() if company else ""
                
                # 提取地点
                location_el = await item.query_selector(
                    ".job-card-container__metadata-item, .artdeco-entity-lockup__caption"
                )
                location = ""
                if location_el:
                    location = await location_el.inner_text()
                    location = location.strip() if location else ""
                
                # 提取链接
                link = ""
                link_el = await item.query_selector(
                    "a.job-card-list__title, a.artdeco-entity-lockup__title, a.job-card-container__link"
                )
                if link_el:
                    href = await link_el.get_attribute("href")
                    if href:
                        link = href.split('?')[0]
                
                # 验证数据完整性
                if not title or not company or not link:
                    fail_count += 1
                    continue
                
                # 去重
                if link in seen_links:
                    continue
                seen_links.add(link)
                
                # 计算优先级
                priority = "Medium"
                lower_title = title.lower()
                if any(kw in lower_title for kw in ["senior", "lead", "staff", "principal"]):
                    priority = "High"
                if any(kw in lower_title for kw in ["quant", "machine learning", "ai engineer", "ai/ml"]):
                    priority = "High"
                if any(kw in lower_title for kw in ["intern", "junior", "entry"]):
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
                success_count += 1
                
                # 每 5 个职位打印一次进度
                if success_count % 5 == 0:
                    print(f"    已解析 {success_count} 个职位...")
                
            except Exception as e:
                fail_count += 1
                continue
        
        print(f"\n  ✓ 解析完成: {success_count} 成功, {fail_count} 失败")
        return jobs
    
    def save_jobs(self, jobs: List[Dict], keyword: str):
        """保存职位"""
        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        safe_keyword = re.sub(r'[^\w\-]', '_', keyword.lower())[:20]
        filename = f"linkedin_{safe_keyword}_{date_str}.json"
        filepath = DATA_DIR / filename
        
        # 按优先级排序
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        jobs_sorted = sorted(jobs, key=lambda x: priority_order.get(x.get("priority", "Medium"), 1))
        
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
            "jobs": jobs_sorted
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n  ✓ 已保存 {len(jobs)} 个职位到: {filepath}")
        return filepath
    
    def print_summary(self, jobs: List[Dict]):
        """打印摘要"""
        print("\n" + "="*70)
        print("抓取结果摘要")
        print("="*70)
        
        high_priority = [j for j in jobs if j.get("priority") == "High"]
        medium_priority = [j for j in jobs if j.get("priority") == "Medium"]
        low_priority = [j for j in jobs if j.get("priority") == "Low"]
        
        print(f"\n总计: {len(jobs)} 个职位")
        print(f"  🔴 高优先级: {len(high_priority)} 个")
        print(f"  🟡 中优先级: {len(medium_priority)} 个")
        print(f"  🟢 低优先级: {len(low_priority)} 个")
        
        if high_priority:
            print(f"\n高优先级职位:")
            for job in high_priority[:5]:
                print(f"  • {job['title'][:45]} @ {job['company'][:25]}")


async def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--search", default="data engineer")
    parser.add_argument("--location", default="Netherlands")
    parser.add_argument("--headless", action="store_true")
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位爬虫 - 稳健版")
    print("="*70)
    print(f"搜索: {args.search}")
    print(f"地点: {args.location}")
    print("="*70)
    
    async with LinkedInScraperRobust(headless=args.headless) as scraper:
        await scraper.ensure_login()
        jobs = await scraper.search_jobs(args.search, args.location)
        scraper.save_jobs(jobs, args.search)
        scraper.print_summary(jobs)
        
        print("\n" + "="*70)
        print(f"✓ 完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
