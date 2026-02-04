"""
LinkedIn 职位爬虫 V5 - 解决页面加载卡住问题
=============================================

核心改进：
1. 使用 CDP 连接已有浏览器实例（避免反爬检测）
2. 改用 'commit' 等待策略（不等待所有资源）
3. 添加请求拦截，阻止不必要的资源加载
4. 增加超时处理和重试机制

Usage:
    # 方式1: 使用独立浏览器（需要先启动 Chrome with remote debugging）
    python linkedin_scraper_v5.py --cdp

    # 方式2: 使用 Playwright 内置浏览器
    python linkedin_scraper_v5.py --search "data engineer"
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# 要阻止的资源类型（加速页面加载）
BLOCKED_RESOURCES = ['image', 'media', 'font', 'stylesheet']
# 要阻止的 URL 模式（广告、追踪器等）
BLOCKED_URL_PATTERNS = [
    'analytics', 'tracking', 'ads', 'beacon',
    'pixel', 'telemetry', 'metrics', 'log'
]


class LinkedInScraperV5:
    """LinkedIn 爬虫 V5 - 解决页面加载问题"""

    def __init__(self, headless: bool = False, use_cdp: bool = False, cdp_url: str = "http://localhost:9222"):
        self.headless = headless
        self.use_cdp = use_cdp
        self.cdp_url = cdp_url
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()

        if self.use_cdp:
            # 连接到已运行的 Chrome 实例
            print(f"[Browser] 连接到 CDP: {self.cdp_url}")
            try:
                self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
                contexts = self.browser.contexts
                if contexts:
                    self.context = contexts[0]
                    pages = self.context.pages
                    self.page = pages[0] if pages else await self.context.new_page()
                else:
                    self.context = await self.browser.new_context()
                    self.page = await self.context.new_page()
                print("  ✓ CDP 连接成功")
            except Exception as e:
                print(f"  ✗ CDP 连接失败: {e}")
                print("  → 回退到内置浏览器")
                self.use_cdp = False

        if not self.use_cdp:
            # 使用内置浏览器，添加反检测措施
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Europe/Amsterdam",
            )

            # 注入反检测脚本
            await self.context.add_init_script("""
                // 隐藏 webdriver 标志
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

                // 模拟真实的 plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });

                // 模拟真实的 languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });

                // 覆盖 permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)

            self.page = await self.context.new_page()

            # 设置请求拦截（加速加载）
            await self._setup_request_interception()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.use_cdp:
            # 只有非 CDP 模式才关闭浏览器
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _setup_request_interception(self):
        """设置请求拦截，阻止不必要的资源"""
        async def handle_route(route):
            request = route.request
            resource_type = request.resource_type
            url = request.url.lower()

            # 阻止特定资源类型
            if resource_type in BLOCKED_RESOURCES:
                await route.abort()
                return

            # 阻止追踪/广告请求
            if any(pattern in url for pattern in BLOCKED_URL_PATTERNS):
                await route.abort()
                return

            await route.continue_()

        await self.page.route("**/*", handle_route)

    async def login_with_cookies(self) -> bool:
        """使用 cookies 登录"""
        print("\n[LinkedIn] 检查登录状态...")

        if not COOKIES_FILE.exists():
            print("  ✗ 未找到 cookies 文件")
            return await self._manual_login()

        try:
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)

            # 验证登录 - 使用 'commit' 策略，不等待所有资源
            print("  → 验证登录状态...")
            await self._safe_goto("https://www.linkedin.com/feed/", timeout=30000)
            await asyncio.sleep(2)

            if "/feed" in self.page.url:
                print("  ✓ 登录成功")
                return True
            else:
                print("  ✗ Cookies 已过期")
                return await self._manual_login()

        except Exception as e:
            print(f"  ✗ 登录失败: {e}")
            return await self._manual_login()

    async def _manual_login(self) -> bool:
        """手动登录"""
        print("  → 请手动登录 LinkedIn...")
        await self._safe_goto("https://www.linkedin.com/login", timeout=30000)

        input("登录完成后请按回车继续...")

        try:
            cookies = await self.context.cookies()
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            print("  ✓ Cookies 已保存")
            return True
        except Exception as e:
            print(f"  ! 保存 cookies 失败: {e}")
            return True

    async def _safe_goto(self, url: str, timeout: int = 60000, retries: int = 3) -> bool:
        """
        安全的页面导航，解决 goto 卡住问题

        关键改进：
        1. 使用 'commit' 等待策略（只等待初始响应）
        2. 添加重试机制
        3. 超时后不抛出异常，继续执行
        """
        for attempt in range(retries):
            try:
                print(f"  → 访问页面 (尝试 {attempt + 1}/{retries})...")

                # 使用 'commit' 策略 - 只等待服务器响应，不等待所有资源
                # 这是解决 LinkedIn 页面加载卡住的关键
                response = await self.page.goto(
                    url,
                    wait_until="commit",  # 关键：不等待 networkidle
                    timeout=timeout
                )

                # 等待基本 DOM 加载
                await asyncio.sleep(2)

                # 检查是否成功
                if response and response.ok:
                    print(f"  ✓ 页面响应成功 (status: {response.status})")
                    return True
                else:
                    print(f"  ! 页面响应异常 (status: {response.status if response else 'None'})")

            except PlaywrightTimeout:
                print(f"  ! 超时，但继续尝试...")
                # 超时不一定是失败，页面可能已经部分加载
                await asyncio.sleep(2)

                # 检查页面是否已经有内容
                try:
                    content = await self.page.content()
                    if len(content) > 1000:  # 有足够内容
                        print(f"  → 页面已部分加载，继续执行")
                        return True
                except:
                    pass

            except Exception as e:
                print(f"  ✗ 导航错误: {e}")

            if attempt < retries - 1:
                print(f"  → 等待 3 秒后重试...")
                await asyncio.sleep(3)

        return False

    async def scrape_jobs(self, keyword: str, location: str = "Netherlands", max_jobs: int = 50) -> List[Dict]:
        """抓取职位"""
        print(f"\n[LinkedIn] 搜索: '{keyword}' in {location}")
        print("  筛选: Past 24 hours + Hybrid/On-site")

        # 构建 URL
        params = {
            "keywords": keyword,
            "location": location,
            "f_TPR": "r86400",      # Past 24 hours
            "f_WT": "2,3",          # Hybrid + On-site
            "sortBy": "DD"          # 按日期排序
        }
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"

        print(f"  URL: {url[:70]}...")

        # 使用安全导航
        if not await self._safe_goto(url, timeout=45000):
            print("  ✗ 无法加载搜索页面")
            return []

        # 等待页面稳定
        print("  → 等待页面渲染...")
        await asyncio.sleep(3)

        # 等待职位列表出现
        await self._wait_for_jobs_list()

        # 抓取职位
        jobs = await self._extract_jobs(max_jobs)
        return jobs

    async def _wait_for_jobs_list(self, timeout: int = 15000):
        """等待职位列表出现"""
        selectors = [
            ".jobs-search-results__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
            ".scaffold-layout__list-container"
        ]

        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout // len(selectors))
                print(f"  ✓ 找到职位列表 ({selector})")
                return True
            except:
                continue

        print("  ! 未找到标准职位列表选择器，尝试继续...")
        return False

    async def _extract_jobs(self, max_jobs: int) -> List[Dict]:
        """提取职位信息"""
        jobs = []
        seen = set()
        no_new_count = 0

        print("\n  开始抓取职位...")

        for scroll_round in range(15):  # 最多滚动15次
            # 获取职位卡片
            cards = await self._get_job_cards()

            if not cards:
                print(f"    第 {scroll_round + 1} 轮: 未找到职位卡片")
                no_new_count += 1
                if no_new_count >= 3:
                    break
                await self._scroll_and_wait()
                continue

            # 解析职位
            new_count = 0
            for card in cards:
                if len(jobs) >= max_jobs:
                    break

                job = await self._parse_card(card)
                if job:
                    key = f"{job['title']}-{job['company']}"
                    if key not in seen:
                        seen.add(key)
                        jobs.append(job)
                        new_count += 1
                        print(f"  [{len(jobs)}] {job['title'][:40]} @ {job['company'][:20]}")

            print(f"    第 {scroll_round + 1} 轮: 新增 {new_count} 个，总计 {len(jobs)} 个")

            if new_count == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    print("  → 连续3轮无新职位，停止滚动")
                    break
            else:
                no_new_count = 0

            if len(jobs) >= max_jobs:
                break

            await self._scroll_and_wait()

        print(f"\n  ✓ 共抓取 {len(jobs)} 个职位")
        return jobs

    async def _get_job_cards(self) -> List:
        """获取职位卡片"""
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
                ".job-card-list__title strong",
                ".job-card-list__title",
                "h3 strong",
                "a[class*='title']"
            ])

            # 公司
            company = await self._get_text(card, [
                ".job-card-container__primary-description",
                ".job-card-container__company-name",
                ".artdeco-entity-lockup__subtitle",
            ])

            # 地点
            location = await self._get_text(card, [
                ".job-card-container__metadata-item",
                ".artdeco-entity-lockup__caption",
            ])

            # 链接
            link_el = await card.query_selector("a[href*='/jobs/view/']")
            if not link_el:
                link_el = await card.query_selector("a")
            href = await link_el.get_attribute("href") if link_el else ""
            url = href.split('?')[0] if href else ""
            if url and not url.startswith("http"):
                url = f"https://www.linkedin.com{url}"

            if title and company:
                return {
                    "title": title.strip(),
                    "company": company.strip(),
                    "location": location.strip() if location else "",
                    "url": url,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None

    async def _get_text(self, parent, selectors: List[str]) -> str:
        """获取文本"""
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

    async def _scroll_and_wait(self):
        """滚动并等待"""
        await self.page.evaluate("window.scrollBy(0, 600)")
        await asyncio.sleep(1.5 + (0.5 * (hash(datetime.now().isoformat()) % 10) / 10))  # 随机延迟

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
    parser = argparse.ArgumentParser(description="LinkedIn 职位爬虫 V5")
    parser.add_argument("--search", default="data engineer", help="搜索关键词")
    parser.add_argument("--location", default="Netherlands", help="地点")
    parser.add_argument("--max-jobs", type=int, default=30, help="最大职位数")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--cdp", action="store_true", help="使用 CDP 连接已有浏览器")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="CDP URL")
    args = parser.parse_args()

    print("="*70)
    print("LinkedIn 职位爬虫 V5 - 解决页面加载问题")
    print("="*70)
    print(f"搜索: {args.search}")
    print(f"地点: {args.location}")
    if args.cdp:
        print(f"模式: CDP ({args.cdp_url})")
    else:
        print(f"模式: 内置浏览器 (headless={args.headless})")
    print("="*70)

    async with LinkedInScraperV5(
        headless=args.headless,
        use_cdp=args.cdp,
        cdp_url=args.cdp_url
    ) as scraper:
        # 登录
        if not await scraper.login_with_cookies():
            print("✗ 登录失败")
            return

        # 抓取
        jobs = await scraper.scrape_jobs(args.search, args.location, args.max_jobs)

        if jobs:
            # 保存
            scraper.save(jobs, args.search)

        print("\n" + "="*70)
        print(f"✓ 完成！共 {len(jobs)} 个职位")
        print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
