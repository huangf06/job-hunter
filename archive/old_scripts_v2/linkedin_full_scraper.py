"""
LinkedIn 职位爬虫 - 完整人工流程模拟
======================================

完整模拟人工操作流程：
1. 登录 LinkedIn (使用已保存的 cookies 或手动登录)
2. 点击 Jobs 标签
3. 搜索关键词 + Netherlands
4. 应用筛选：Past 24 hours + Hybrid/On-site
5. 抓取所有结果并保存

Usage:
    python linkedin_full_scraper.py --search "data engineer"
    python linkedin_full_scraper.py --search "machine learning engineer" --max-jobs 50
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, Page

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

# 确保目录存在
DATA_DIR.mkdir(parents=True, exist_ok=True)


class LinkedInFullScraper:
    """LinkedIn 完整流程爬虫"""
    
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
            args=['--disable-blink-features=AutomationControlled']
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        # 注入脚本隐藏自动化特征
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
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
        """登录 LinkedIn - 使用 cookies 或手动登录"""
        print("[LinkedIn] 正在登录...")
        
        # 尝试加载已保存的 cookies
        if COOKIES_FILE.exists():
            print("  [INFO] 发现已保存的 cookies，尝试恢复会话...")
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)
            
            # 验证登录状态
            await self.page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # 检查是否已登录
            if await self._is_logged_in():
                print("  [OK] 使用 cookies 登录成功！")
                return True
            else:
                print("  [WARN] Cookies 已过期，需要重新登录")
        
        # 手动登录流程
        print("  [INFO] 请手动登录 LinkedIn...")
        await self.page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
        
        # 等待用户登录完成（检测到跳转到 feed 页面）
        print("  [WAIT] 等待登录完成（请在浏览器中完成登录）...")
        max_wait = 120  # 最多等待2分钟
        for i in range(max_wait):
            await asyncio.sleep(1)
            if await self._is_logged_in():
                print("  [OK] 登录成功！")
                # 保存 cookies
                cookies = await self.context.cookies()
                COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, indent=2)
                print(f"  [OK] Cookies 已保存到 {COOKIES_FILE}")
                return True
            if i % 10 == 0:
                print(f"  ... 等待中 ({i}s)")
        
        print("  [ERROR] 登录超时")
        return False
    
    async def _is_logged_in(self) -> bool:
        """检查是否已登录"""
        try:
            # 检查是否存在 feed 页面的特征元素
            feed_indicators = [
                "[data-test-id='feed-tab']",
                ".feed-identity-module",
                "[data-control-name='identity_welcome_message']",
                "a[href='/jobs/']"  # 有 Jobs 链接
            ]
            for selector in feed_indicators:
                element = await self.page.query_selector(selector)
                if element:
                    return True
            
            # 检查 URL
            url = self.page.url
            if '/feed' in url or '/in/' in url:
                return True
                
            return False
        except:
            return False
    
    async def navigate_to_jobs(self):
        """点击 Jobs 标签进入职位页面"""
        print("[LinkedIn] 正在进入 Jobs 页面...")
        
        # 点击 Jobs 链接
        jobs_link_selectors = [
            "a[href='/jobs/']",
            "a[href*='jobs']",
            "[data-test-id='jobs-tab']",
            "[aria-label*='Jobs']",
            "[aria-label*='职位']",
            "span:has-text('Jobs')",
            "span:has-text('职位')"
        ]
        
        for selector in jobs_link_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(2)
                    await self.page.wait_for_load_state("networkidle")
                    print("  [OK] 已点击 Jobs 标签")
                    return True
            except:
                continue
        
        # 如果点击失败，直接导航到 URL
        print("  [INFO] 直接导航到 Jobs 页面...")
        await self.page.goto("https://www.linkedin.com/jobs/", wait_until="networkidle")
        await asyncio.sleep(2)
        return True
    
    async def search_jobs(self, keyword: str, location: str = "Netherlands"):
        """搜索职位"""
        print(f"[LinkedIn] 搜索: '{keyword}' in {location}...")
        
        # 等待搜索框出现
        search_selectors = [
            "input[aria-label*='Search']",
            "input[placeholder*='Search']",
            "input[type='text']",
            ".jobs-search-box__text-input",
            "[data-test-id='jobs-search-keywords-input']"
        ]
        
        search_box = None
        for selector in search_selectors:
            try:
                search_box = await self.page.wait_for_selector(selector, timeout=5000)
                if search_box:
                    break
            except:
                continue
        
        if not search_box:
            print("  [ERROR] 找不到搜索框")
            return False
        
        # 输入关键词
        await search_box.fill("")
        await search_box.fill(keyword)
        await asyncio.sleep(0.5)
        
        # 查找位置输入框
        location_selectors = [
            "input[aria-label*='Location']",
            "input[placeholder*='Location']",
            ".jobs-search-box__text-input[aria-label*='location']"
        ]
        
        for selector in location_selectors:
            try:
                location_box = await self.page.query_selector(selector)
                if location_box:
                    await location_box.fill("")
                    await location_box.fill(location)
                    await asyncio.sleep(0.5)
                    break
            except:
                continue
        
        # 按回车搜索
        await search_box.press("Enter")
        await asyncio.sleep(3)
        await self.page.wait_for_load_state("networkidle")
        print("  [OK] 搜索已提交")
        return True
    
    async def apply_filters(self):
        """应用筛选条件：Past 24 hours + Hybrid/On-site"""
        print("[LinkedIn] 正在应用筛选条件...")
        
        # 1. 点击 "Date posted" 筛选
        await self._click_filter_button("Date posted", "发布时间")
        await asyncio.sleep(1)
        
        # 选择 "Past 24 hours"
        await self._select_filter_option("Past 24 hours", "24 小时")
        await asyncio.sleep(2)
        
        # 2. 点击 "Remote" 筛选
        await self._click_filter_button("Remote", "远程")
        await asyncio.sleep(1)
        
        # 选择 "Hybrid" 和 "On-site"
        await self._select_filter_option("Hybrid", "混合")
        await self._select_filter_option("On-site", "现场")
        await asyncio.sleep(2)
        
        # 点击 "Show results" 或关闭筛选面板
        await self._click_show_results()
        await asyncio.sleep(3)
        
        print("  [OK] 筛选条件已应用: Past 24 hours + Hybrid/On-site")
        return True
    
    async def _click_filter_button(self, en_text: str, zh_text: str):
        """点击筛选按钮"""
        selectors = [
            f"button:has-text('{en_text}')",
            f"button:has-text('{zh_text}')",
            f"[aria-label*='{en_text}']",
            f"span:has-text('{en_text}')",
            ".artdeco-dropdown__trigger"
        ]
        
        for selector in selectors:
            try:
                button = await self.page.query_selector(selector)
                if button:
                    await button.click()
                    print(f"    [OK] 点击了 {en_text} 筛选")
                    return True
            except:
                continue
        return False
    
    async def _select_filter_option(self, en_text: str, zh_text: str = ""):
        """选择筛选选项"""
        selectors = [
            f"label:has-text('{en_text}')",
            f"span:has-text('{en_text}')",
            f"[data-test-id*='{en_text.lower().replace(' ', '-')}']",
            f"input[value*='{en_text}']",
        ]
        
        if zh_text:
            selectors.extend([
                f"label:has-text('{zh_text}')",
                f"span:has-text('{zh_text}')",
            ])
        
        for selector in selectors:
            try:
                option = await self.page.query_selector(selector)
                if option:
                    await option.click()
                    print(f"    [OK] 选择了 {en_text}")
                    return True
            except:
                continue
        return False
    
    async def _click_show_results(self):
        """点击显示结果按钮"""
        selectors = [
            "button:has-text('Show results')",
            "button:has-text('显示结果')",
            "[aria-label*='Apply']",
            ".artdeco-button--primary"
        ]
        
        for selector in selectors:
            try:
                button = await self.page.query_selector(selector)
                if button:
                    await button.click()
                    return True
            except:
                continue
        
        # 如果没有找到按钮，按 Escape 关闭面板
        await self.page.keyboard.press("Escape")
        return True
    
    async def scrape_all_jobs(self, max_jobs: int = 100) -> List[Dict]:
        """抓取所有职位"""
        print(f"[LinkedIn] 开始抓取职位 (最多 {max_jobs} 个)...")
        
        jobs = []
        previous_count = 0
        no_change_count = 0
        
        while len(jobs) < max_jobs and no_change_count < 3:
            # 获取当前页面上的所有职位卡片
            job_cards = await self._get_job_cards()
            
            for card in job_cards:
                if len(jobs) >= max_jobs:
                    break
                
                job = await self._parse_job_card(card)
                if job and not self._is_duplicate(jobs, job):
                    jobs.append(job)
                    print(f"  [{len(jobs)}] {job['title']} @ {job['company']}")
            
            # 检查是否有新职位加载
            if len(jobs) == previous_count:
                no_change_count += 1
            else:
                no_change_count = 0
            previous_count = len(jobs)
            
            # 滚动加载更多
            if len(jobs) < max_jobs:
                await self._scroll_down()
                await asyncio.sleep(2)
        
        print(f"[LinkedIn] 成功抓取 {len(jobs)} 个职位")
        return jobs
    
    async def _get_job_cards(self) -> List:
        """获取所有职位卡片元素"""
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
            title = await self._get_text_from_selectors(card, [
                "h3", "h2", ".job-card-list__title", "[class*='title']"
            ])
            
            # 公司
            company = await self._get_text_from_selectors(card, [
                ".job-card-container__company-name", ".company-name", "[class*='company']"
            ])
            
            # 地点
            location = await self._get_text_from_selectors(card, [
                ".job-card-container__metadata-item", ".location", "[class*='location']"
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
            
            # 工作类型 (Remote/Hybrid/On-site)
            workplace = await self._get_text_from_selectors(card, [
                "[class*='workplace']", "[class*='remote']", "[class*='hybrid']"
            ])
            
            if title and company:
                return {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip(),
                    "workplace_type": workplace.strip(),
                    "url": url,
                    "posted_date": posted,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None
    
    async def _get_text_from_selectors(self, parent, selectors: List[str]) -> str:
        """从多个选择器中获取文本"""
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
        """检查是否重复"""
        key = f"{new_job.get('title', '')}-{new_job.get('company', '')}"
        for job in jobs:
            existing_key = f"{job.get('title', '')}-{job.get('company', '')}"
            if key == existing_key:
                return True
        return False
    
    async def _scroll_down(self):
        """向下滚动加载更多"""
        await self.page.evaluate("window.scrollBy(0, 800)")
    
    def save_results(self, jobs: List[Dict], keyword: str) -> Path:
        """保存结果到文件"""
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
                "remote": ["Hybrid", "On-site"]
            },
            "scraped_at": datetime.now().isoformat(),
            "total_jobs": len(jobs),
            "jobs": jobs
        }
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"\n[OK] 结果已保存到: {filepath}")
        return filepath


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="LinkedIn 完整流程职位爬虫")
    parser.add_argument("--search", default="data engineer", help="搜索关键词")
    parser.add_argument("--location", default="Netherlands", help="地点")
    parser.add_argument("--max-jobs", type=int, default=50, help="最大抓取数量")
    parser.add_argument("--headless", action="store_true", help="无头模式（不显示浏览器）")
    
    args = parser.parse_args()
    
    print("="*70)
    print("LinkedIn 职位爬虫 - 完整流程模拟")
    print("="*70)
    print(f"搜索: {args.search}")
    print(f"地点: {args.location}")
    print(f"筛选: Past 24 hours + Hybrid/On-site")
    print("="*70)
    
    async with LinkedInFullScraper(headless=args.headless) as scraper:
        # 1. 登录
        if not await scraper.login():
            print("[ERROR] 登录失败，退出")
            return
        
        # 2. 进入 Jobs 页面
        await scraper.navigate_to_jobs()
        
        # 3. 搜索
        await scraper.search_jobs(args.search, args.location)
        
        # 4. 应用筛选
        await scraper.apply_filters()
        
        # 5. 抓取所有职位
        jobs = await scraper.scrape_all_jobs(args.max_jobs)
        
        # 6. 保存结果
        scraper.save_results(jobs, args.search)
        
        print("\n" + "="*70)
        print(f"完成！共抓取 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
