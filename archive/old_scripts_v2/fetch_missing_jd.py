"""
补充数据库中职位的 JD 描述
==============================

遍历数据库中所有无 JD 的职位，抓取并更新 JD。

Usage:
    # 补充所有无 JD 的职位
    python fetch_missing_jd.py

    # 只补充前 10 个（测试）
    python fetch_missing_jd.py --limit 10

    # 补充特定职位
    python fetch_missing_jd.py --job-id <job_id>
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.db.job_db import JobDatabase

# 要阻止的资源类型（加速页面加载）
BLOCKED_RESOURCES = ['image', 'media', 'font', 'stylesheet']
BLOCKED_URL_PATTERNS = ['analytics', 'tracking', 'ads', 'beacon', 'pixel', 'telemetry', 'metrics']


class JDFetcher:
    """JD 获取器 - 为现有职位补充描述"""

    def __init__(self, headless: bool = False, use_cdp: bool = False, cdp_url: str = "http://localhost:9222"):
        self.headless = headless
        self.use_cdp = use_cdp
        self.cdp_url = cdp_url
        self.db = JobDatabase()
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()

        if self.use_cdp:
            print(f"[Browser] Connecting to CDP: {self.cdp_url}")
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
                print("  [OK] CDP connected")
            except Exception as e:
                print(f"  [FAIL] CDP connection failed: {e}")
                print("  -> Falling back to built-in browser")
                self.use_cdp = False

        if not self.use_cdp:
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--disable-blink-features=AutomationControlled']
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            self.page = await self.context.new_page()
            await self._setup_request_interception()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if not self.use_cdp:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _setup_request_interception(self):
        """设置请求拦截"""
        async def handle_route(route):
            request = route.request
            if request.resource_type in BLOCKED_RESOURCES:
                await route.abort()
                return
            if any(p in request.url.lower() for p in BLOCKED_URL_PATTERNS):
                await route.abort()
                return
            await route.continue_()
        await self.page.route("**/*", handle_route)

    def get_jobs_without_jd(self, limit: int = None) -> List[Dict]:
        """获取所有无 JD 的职位"""
        with self.db._get_conn() as conn:
            sql = """
                SELECT id, title, company, location, url, scraped_at
                FROM jobs
                WHERE description IS NULL OR description = ''
                ORDER BY scraped_at DESC
            """
            if limit:
                sql += f" LIMIT {limit}"

            cursor = conn.execute(sql)
            rows = cursor.fetchall()

        jobs = []
        for row in rows:
            jobs.append({
                'id': row[0],
                'title': row[1],
                'company': row[2],
                'location': row[3],
                'url': row[4],
                'scraped_at': row[5]
            })

        return jobs

    async def fetch_jd(self, url: str) -> Optional[str]:
        """获取单个职位的 JD"""
        try:
            await self.page.goto(url, wait_until="commit", timeout=30000)
            await asyncio.sleep(2)

            # 尝试多种选择器获取 JD
            jd_selectors = [
                ".jobs-description__content",
                ".jobs-box__html-content",
                ".jobs-description-content__text",
                "[class*='description']",
                ".job-view-layout",
                "[data-test-id='job-description']",
                ".show-more-less-html__markup",
            ]

            for selector in jd_selectors:
                try:
                    el = await self.page.query_selector(selector)
                    if el:
                        text = await el.inner_text()
                        if text and len(text.strip()) > 100:
                            # 清理文本
                            description = text.strip()
                            description = description.replace('\r\n', '\n')
                            description = description.replace('\r', '\n')
                            # 限制长度
                            return description[:8000]
                except:
                    continue

            return None

        except Exception as e:
            print(f"    Error fetching JD: {e}")
            return None

    async def update_job_jd(self, job_id: str, description: str):
        """更新数据库中的 JD"""
        with self.db._get_conn() as conn:
            conn.execute(
                "UPDATE jobs SET description = ? WHERE id = ?",
                (description, job_id)
            )

            # 同时更新 raw_data
            cursor = conn.execute("SELECT raw_data FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                try:
                    raw_data = json.loads(row[0])
                    raw_data['description'] = description
                    conn.execute(
                        "UPDATE jobs SET raw_data = ? WHERE id = ?",
                        (json.dumps(raw_data, ensure_ascii=False), job_id)
                    )
                except:
                    pass

    async def run(self, limit: int = None, job_id: str = None):
        """运行 JD 补充流程"""
        if job_id:
            # 补充特定职位
            job = self.db.get_job(job_id)
            if not job:
                print(f"Job not found: {job_id}")
                return
            jobs = [job]
        else:
            # 获取所有无 JD 的职位
            jobs = self.get_jobs_without_jd(limit)

        if not jobs:
            print("No jobs without JD found!")
            return

        print(f"\nFound {len(jobs)} jobs without JD")
        print("=" * 70)

        success_count = 0
        fail_count = 0

        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] {job['title'][:45]} @ {job['company'][:20]}")
            print(f"  URL: {job['url'][:70]}...")

            description = await self.fetch_jd(job['url'])

            if description:
                await self.update_job_jd(job['id'], description)
                print(f"  [OK] JD fetched: {len(description)} chars")
                success_count += 1
            else:
                print(f"  [FAIL] Could not fetch JD")
                fail_count += 1

            # 延迟避免被检测
            if i < len(jobs):
                delay = 1.5 + (i % 2) * 0.5
                await asyncio.sleep(delay)

        print("\n" + "=" * 70)
        print(f"Done: {success_count} success, {fail_count} failed")
        print("=" * 70)

        return success_count, fail_count


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch missing JD for jobs in database")
    parser.add_argument("--limit", type=int, help="Limit number of jobs to process")
    parser.add_argument("--job-id", type=str, help="Process specific job ID")
    parser.add_argument("--headless", action="store_true", help="Headless mode")
    parser.add_argument("--cdp", action="store_true", help="Use CDP")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="CDP URL")
    args = parser.parse_args()

    print("=" * 70)
    print("Fetch Missing JD for Database Jobs")
    print("=" * 70)

    async with JDFetcher(
        headless=args.headless,
        use_cdp=args.cdp,
        cdp_url=args.cdp_url
    ) as fetcher:
        await fetcher.run(limit=args.limit, job_id=args.job_id)


if __name__ == "__main__":
    asyncio.run(main())
