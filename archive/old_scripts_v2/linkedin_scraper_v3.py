"""
LinkedIn 职位爬虫 V3 - 完整重写版
=====================================

核心改进:
1. 使用正确的 LinkedIn 登录后页面选择器
2. 完整的筛选流程 (Past 24h + Hybrid/On-site)
3. 等待动态内容加载
4. 详细的日志输出

Usage:
    python linkedin_scraper_v3.py --search "data engineer"
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, Page, expect

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)


class LinkedInScraperV3:
    """LinkedIn 爬虫 V3 - 完整重写"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        self.jobs: List[Dict] = []
    
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox'
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        # 隐藏自动化特征
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
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
        print("\n[1/5] 正在登录 LinkedIn...")
        
        # 尝试使用 cookies
        if COOKIES_FILE.exists():
            print("  → 尝试使用已保存的 cookies...")
            try:
                with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                await self.context.add_cookies(cookies)
                
                # 验证
                await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                if await self._check_login_status():
                    print("  ✓ 使用 cookies 登录成功")
                    return True
                else:
                    print("  ✗ Cookies 已过期")
            except Exception as e:
                print(f"  ✗ Cookies 加载失败: {e}")
        
        # 手动登录
        print("  → 请手动登录 LinkedIn...")
        await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        
        # 等待登录完成
        print("  → 等待登录完成（请在浏览器中操作）...")
        for i in range(180):  # 最多3分钟
            await asyncio.sleep(1)
            if await self._check_login_status():
                print("  ✓ 登录成功")
                # 保存 cookies
                try:
                    cookies = await self.context.cookies()
                    COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
                    with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                        json.dump(cookies, f, indent=2)
                    print(f"  ✓ Cookies 已保存")
                except Exception as e:
                    print(f"  ! 保存 cookies 失败: {e}")
                return True
            if i % 15 == 0 and i > 0:
                print(f"    ... 等待中 ({i}s)")
        
        print("  ✗ 登录超时")
        return False
    
    async def _check_login_status(self) -> bool:
        """检查是否已登录"""
        try:
            url = self.page.url
            # 检查是否在 feed 页面或个人资料页
            if '/feed' in url or '/in/' in url:
                return True
            # 检查是否有登录后的元素
            try:
                me_button = await self.page.query_selector("[data-test-id='global-nav__me']")
                if me_button:
                    return True
            except:
                pass
            return False
        except:
            return False
    
    async def navigate_to_jobs(self):
        """导航到 Jobs 页面"""
        print("\n[2/5] 正在进入 Jobs 页面...")
        
        await self.page.goto("https://www.linkedin.com/jobs/", wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(3)
        
        # 等待页面加载完成
        try:
            # 等待搜索框出现
            await self.page.wait_for_selector("input[aria-label*='Search']", timeout=10000)
            print("  ✓ Jobs 页面已加载")
            return True
        except Exception as e:
            print(f"  ! 警告: 页面可能未完全加载: {e}")
            return True  # 继续尝试
    
    async def search_and_filter(self, keyword: str, location: str = "Netherlands") -> bool:
        """搜索并应用筛选"""
        print(f"\n[3/5] 搜索: '{keyword}' in {location}")
        
        try:
            # 1. 输入关键词
            print("  → 输入搜索关键词...")
            keyword_input = await self.page.wait_for_selector(
                "input[aria-label*='Search by title, skill, or company']", 
                timeout=10000
            )
            await keyword_input.fill("")
            await keyword_input.fill(keyword)
            await asyncio.sleep(0.5)
            
            # 2. 输入地点
            print("  → 输入地点...")
            location_input = await self.page.wait_for_selector(
                "input[aria-label*='City, state, or zip code']",
                timeout=10000
            )
            await location_input.fill("")
            await location_input.fill(location)
            await asyncio.sleep(0.5)
            
            # 3. 提交搜索
            print("  → 提交搜索...")
            await keyword_input.press("Enter")
            await asyncio.sleep(4)
            await self.page.wait_for_load_state("networkidle")
            
            print("  ✓ 搜索完成")
            return True
            
        except Exception as e:
            print(f"  ✗ 搜索失败: {e}")
            return False
    
    async def apply_filters(self):
        """应用筛选条件"""
        print("\n[4/5] 应用筛选条件...")
        print("  → Date posted: Past 24 hours")
        print("  → Workplace: Hybrid + On-site")
        
        try:
            # 点击 "Date posted" 按钮
            date_button = await self.page.wait_for_selector(
                "button:has-text('Date posted')",
                timeout=10000
            )
            await date_button.click()
            await asyncio.sleep(1)
            
            # 选择 "Past 24 hours"
            option_24h = await self.page.wait_for_selector(
                "text=Past 24 hours",
                timeout=5000
            )
            await option_24h.click()
            await asyncio.sleep(2)
            
            # 点击 "Remote" 按钮
            remote_button = await self.page.wait_for_selector(
                "button:has-text('Remote')",
                timeout=10000
            )
            await remote_button.click()
            await asyncio.sleep(1)
            
            # 选择 Hybrid
            hybrid_option = await self.page.wait_for_selector(
                "text=Hybrid",
                timeout=5000
            )
            await hybrid_option.click()
            await asyncio.sleep(0.5)
            
            # 选择 On-site
            onsite_option = await self.page.wait_for_selector(
                "text=On-site",
                timeout=5000
            )
            await onsite_option.click()
            await asyncio.sleep(2)
            
            # 点击 "Show results" 按钮
            show_results = await self.page.wait_for_selector(
                "button:has-text('Show results')",
                timeout=5000
            )
            await show_results.click()
            await asyncio.sleep(4)
            
            print("  ✓ 筛选条件已应用")
            return True
            
        except Exception as e:
            print(f"  ! 筛选应用失败: {e}")
            print("  → 尝试使用 URL 参数方式...")
            return await self._apply_filters_via_url()
    
    async def _apply_filters_via_url(self):
        """通过 URL 参数应用筛选"""
        try:
            current_url = self.page.url
            # 添加筛选参数
            if '?' in current_url:
                new_url = current_url + "&f_TPR=r86400&f_WT=2,3&sortBy=DD"
            else:
                new_url = current_url + "?f_TPR=r86400&f_WT=2,3&sortBy=DD"
            
            await self.page.goto(new_url, wait_until="networkidle")
            await asyncio.sleep(4)
            print("  ✓ 通过 URL 应用筛选完成")
            return True
        except Exception as e:
            print(f"  ✗ URL 筛选也失败: {e}")
            return False
    
    async def scrape_jobs(self, max_jobs: int = 50) -> List[Dict]:
        """抓取职位"""
        print(f"\n[5/5] 开始抓取职位 (最多 {max_jobs} 个)...")
        
        jobs = []
        previous_count = 0
        no_change_count = 0
        max_attempts = 15
        
        for attempt in range(max_attempts):
            # 获取当前所有职位卡片
            cards = await self._get_job_cards()
            
            if not cards:
                print(f"    第 {attempt+1} 次尝试: 未找到职位卡片")
                await self._scroll_down()
                await asyncio.sleep(2)
                continue
            
            new_count = 0
            for card in cards:
                if len(jobs) >= max_jobs:
                    break
                
                job = await self._parse_card(card)
                if job and not self._is_duplicate(jobs, job):
                    jobs.append(job)
                    new_count += 1
                    print(f"  [{len(jobs)}] {job['title'][:50]} @ {job['company'][:30]}")
            
            # 检查是否有新内容
            if len(jobs) == previous_count:
                no_change_count += 1
                if no_change_count >= 3:
                    print(f"    没有更多新职位")
                    break
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
        # LinkedIn 登录后的职位列表选择器
        selectors = [
            ".jobs-search-results__list-item",
            "[data-job-id]",
            ".job-card-container",
            ".scaffold-layout__list-item",
            "li[data-occludable-job-id]"
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
            title = await self._get_element_text(card, [
                "h3 strong",
                ".job-card-list__title",
                "a[class*='title']",
                "span[dir='ltr']"
            ])
            
            # 公司
            company = await self._get_element_text(card, [
                ".job-card-container__company-name",
                ".company-name",
                "[class*='company']"
            ])
            
            # 地点
            location = await self._get_element_text(card, [
                ".job-card-container__metadata-item",
                ".location",
                "[class*='metadata']"
            ])
            
            # 工作类型
            workplace = await self._get_element_text(card, [
                "[class*='workplace']",
                ".job-card-container__metadata-item:nth-child(2)"
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
                    "workplace_type": workplace.strip() if workplace else "",
                    "url": url,
                    "posted_date": posted,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None
    
    async def _get_element_text(self, parent, selectors: List[str]) -> str:
        """获取元素文本"""
        for selector in selectors:
            try:
                el = await parent.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    if text and text.strip():
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
        await self.page.evaluate("window.scrollBy(0, 1000)")
    
    def save_results(self, jobs: List[Dict], keyword: str) -> Path:
        """保存结果"""
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
        
        print(f"\n  ✓ 结果已保存: {filepath}")
        return filepath


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn 职位爬虫 V3")
    parser.add_argument("--search", default="data engineer", help="搜索关键词")
    parser.add_argument("--location", default="Netherlands", help="地点")
    parser.add_argument("--max-jobs", type=int, default=30, help="最大数量")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位爬虫 V3")
    print("="*70)
    print(f"关键词: {args.search}")
    print(f"地点: {args.location}")
    print(f"筛选: Past 24 hours + Hybrid/On-site")
    print("="*70)
    
    async with LinkedInScraperV3(headless=args.headless) as scraper:
        # 1. 登录
        if not await scraper.login():
            print("\n✗ 登录失败，退出")
            return
        
        # 2. 进入 Jobs
        await scraper.navigate_to_jobs()
        
        # 3. 搜索
        if not await scraper.search_and_filter(args.search, args.location):
            print("\n✗ 搜索失败，退出")
            return
        
        # 4. 应用筛选
        await scraper.apply_filters()
        
        # 5. 抓取
        jobs = await scraper.scrape_jobs(args.max_jobs)
        
        # 6. 保存
        scraper.save_results(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"✓ 完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
