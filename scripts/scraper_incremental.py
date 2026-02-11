#!/usr/bin/env python3
"""
LinkedIn 增量爬取器 - 智能去重 + 快速更新
============================================

核心优化：
1. 数据库预检查：爬取前批量查询已有职位，避免重复抓取
2. URL级去重：同一职位多个搜索词只抓一次JD
3. 时间窗口：只抓取最近N小时的职位（默认4小时）
4. 快速失败：LinkedIn反爬时快速退出，不浪费时间

Usage:
    python scraper_incremental.py --profile all --max-age-hours 4
    python scraper_incremental.py --profile ml_data --force-refresh
"""

import asyncio
import hashlib
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set
from urllib.parse import urlencode

import yaml
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase

DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
COOKIES_FILE = CONFIG_DIR / "linkedin_cookies.json"
PROFILES_FILE = CONFIG_DIR / "search_profiles.yaml"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# 资源拦截（加速页面加载）
BLOCKED_RESOURCES = ['image', 'media', 'font', 'stylesheet']
BLOCKED_URL_PATTERNS = ['analytics', 'tracking', 'ads', 'beacon', 'pixel', 'telemetry', 'metrics']

# LinkedIn 每页职位数
JOBS_PER_PAGE = 25
# 最大重试次数
MAX_RETRIES = 2
# 请求间隔（秒）
REQUEST_DELAY = 2


class IncrementalScraper:
    """增量爬取器 - 智能去重 + 快速更新"""
    
    def __init__(self, headless: bool = True, max_age_hours: int = 4):
        self.headless = headless
        self.max_age_hours = max_age_hours
        self.db = JobDatabase()
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        
        # 统计
        self.stats = {
            'scraped': 0,
            'new_jobs': 0,
            'duplicates_skipped': 0,
            'jd_fetched': 0,
            'jd_skipped': 0,
            'errors': 0,
            'start_time': datetime.now().isoformat(),
        }
        
        # 内存缓存：已存在的职位ID
        self._existing_ids: Set[str] = set()
        # 本次会话已处理的URL
        self._session_urls: Set[str] = set()
        
    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36",
            locale="en-US",
            timezone_id="Europe/Amsterdam",
        )
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        """)
        self.page = await self.context.new_page()
        await self._setup_interception()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def _setup_interception(self):
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
        
    def _generate_job_id(self, url: str) -> str:
        """根据URL生成唯一ID"""
        clean_url = url.split('?')[0].split('#')[0].rstrip('/')
        return hashlib.md5(clean_url.encode()).hexdigest()[:12]
        
    def _preload_existing_jobs(self, urls: List[str]) -> Set[str]:
        """预加载数据库中已存在的职位ID"""
        if not urls:
            return set()
            
        # 批量查询
        job_ids = [self._generate_job_id(url) for url in urls if url]
        existing = set()
        
        # 分块查询避免SQL变量限制
        CHUNK_SIZE = 900
        for i in range(0, len(job_ids), CHUNK_SIZE):
            chunk = job_ids[i:i+CHUNK_SIZE]
            placeholders = ','.join(['?'] * len(chunk))
            try:
                rows = self.db.execute(
                    f"SELECT id FROM jobs WHERE id IN ({placeholders})",
                    chunk
                )
                existing.update(row['id'] for row in rows)
            except Exception as e:
                print(f"  [WARN] DB query failed: {e}")
                
        return existing
        
    async def login_with_cookies(self) -> bool:
        """使用cookie登录"""
        if not COOKIES_FILE.exists():
            print("[Login] No cookies file")
            return False
            
        try:
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
                
            valid_cookies = [c for c in cookies if isinstance(c, dict) and 
                           all(c.get(k) for k in ('name', 'value', 'domain'))]
            
            if not valid_cookies:
                print("[Login] No valid cookies")
                return False
                
            await self.context.add_cookies(valid_cookies)
            
            # 验证登录
            await self.page.goto("https://www.linkedin.com/feed/", timeout=30000)
            await asyncio.sleep(2)
            
            if "/login" in self.page.url or "/checkpoint" in self.page.url:
                print("[Login] Cookies expired")
                return False
                
            print("[Login] OK")
            return True
            
        except Exception as e:
            print(f"[Login] Failed: {e}")
            return False
            
    async def scrape_search_page(self, keywords: str, location: str, max_jobs: int = 50) -> List[Dict]:
        """爬取搜索页面，只获取基本信息（不抓JD）"""
        jobs = []
        
        # 构建搜索URL
        params = {
            'keywords': keywords,
            'location': location,
            'f_TPR': f'r{self.max_age_hours * 3600}',  # 时间过滤
            'f_WT': '1,3',  # On-site + Hybrid
            'sortBy': 'DD',  # 最新发布
        }
        search_url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
        
        print(f"  [Search] {keywords[:50]}...")
        
        for attempt in range(MAX_RETRIES):
            try:
                await self.page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(3)
                
                # 检查是否被拦截
                if "captcha" in (await self.page.content()).lower():
                    print("  [ERROR] CAPTCHA detected, aborting")
                    return []
                    
                # 提取职位列表
                job_cards = await self.page.query_selector_all('[data-job-id]')
                
                for card in job_cards[:max_jobs]:
                    try:
                        # 提取基本信息
                        title_el = await card.query_selector('.job-card-list__title')
                        company_el = await card.query_selector('.job-card-container__company-name')
                        location_el = await card.query_selector('.job-card-container__metadata-item')
                        
                        title = await title_el.inner_text() if title_el else ""
                        company = await company_el.inner_text() if company_el else ""
                        location_text = await location_el.inner_text() if location_el else ""
                        
                        # 获取链接
                        link_el = await card.query_selector('a[href*="/jobs/view/"]')
                        href = await link_el.get_attribute('href') if link_el else ""
                        url = f"https://www.linkedin.com{href}" if href.startswith('/') else href
                        
                        if not title or not company or not url:
                            continue
                            
                        job = {
                            'title': title.strip(),
                            'company': company.strip(),
                            'location': location_text.strip(),
                            'url': url,
                            'source': 'linkedin',
                            'scraped_at': datetime.now().isoformat(),
                        }
                        jobs.append(job)
                        
                    except Exception as e:
                        continue
                        
                print(f"  [OK] Found {len(jobs)} jobs")
                return jobs
                
            except PlaywrightTimeout:
                print(f"  [Timeout] Attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
                self.stats['errors'] += 1
                
        return jobs
        
    async def fetch_job_description(self, job: Dict) -> Optional[str]:
        """抓取单个职位描述"""
        url = job.get('url', '')
        if not url:
            return None
            
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await asyncio.sleep(2)
            
            # 尝试多种选择器
            selectors = [
                '.jobs-description__content',
                '.jobs-box__html-content',
                '[data-test-id="job-description"]',
            ]
            
            for selector in selectors:
                desc_el = await self.page.query_selector(selector)
                if desc_el:
                    description = await desc_el.inner_text()
                    return description.strip()
                    
            return None
            
        except Exception as e:
            print(f"  [JD ERROR] {job.get('title', '')[:30]}: {e}")
            return None
            
    async def run_profile(self, profile_name: str, profile_config: Dict, 
                         search_config: Dict) -> List[Dict]:
        """运行单个profile"""
        print(f"\n{'='*60}")
        print(f"[Profile] {profile_name}")
        print(f"{'='*60}")
        
        queries = profile_config.get('queries', [])
        location = profile_config.get('location_override', search_config.get('location', 'Netherlands'))
        max_jobs = profile_config.get('max_jobs_override', search_config.get('max_jobs', 50))
        
        all_jobs = []
        
        # 第一阶段：快速抓取所有搜索词的职位列表（不抓JD）
        for i, query in enumerate(queries):
            keywords = query.get('keywords', '')
            print(f"\n[Query {i+1}/{len(queries)}] {keywords[:60]}...")
            
            jobs = await self.scrape_search_page(keywords, location, max(1, max_jobs // len(queries)))
            
            for job in jobs:
                job['search_profile'] = profile_name
                job['search_query'] = keywords
                
            all_jobs.extend(jobs)
            
            if i < len(queries) - 1:
                await asyncio.sleep(REQUEST_DELAY)
                
        # 去重：同一职位可能出现在多个搜索词结果中
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            url = job.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_jobs.append(job)
                
        print(f"\n[Phase 1] Total unique jobs: {len(unique_jobs)}")
        
        # 第二阶段：批量检查数据库去重
        urls = [j['url'] for j in unique_jobs]
        existing_ids = self._preload_existing_jobs(urls)
        
        new_jobs = []
        for job in unique_jobs:
            job_id = self._generate_job_id(job['url'])
            if job_id in existing_ids:
                self.stats['duplicates_skipped'] += 1
            else:
                new_jobs.append(job)
                
        print(f"[Phase 2] New jobs to process: {len(new_jobs)} (skipped {self.stats['duplicates_skipped']} duplicates)")
        
        # 第三阶段：只抓新职位的JD
        if new_jobs:
            print(f"\n[Phase 3] Fetching JD for {len(new_jobs)} new jobs...")
            for i, job in enumerate(new_jobs):
                if i > 0 and i % 5 == 0:
                    print(f"  Progress: {i}/{len(new_jobs)}")
                    
                description = await self.fetch_job_description(job)
                if description:
                    job['description'] = description
                    self.stats['jd_fetched'] += 1
                else:
                    self.stats['jd_skipped'] += 1
                    
                # 保存到数据库
                try:
                    _, was_inserted = self.db.insert_job(job)
                    if was_inserted:
                        self.stats['new_jobs'] += 1
                except Exception as e:
                    print(f"  [DB ERROR] {e}")
                    
                await asyncio.sleep(1)  # 礼貌延迟
                
        self.stats['scraped'] += len(unique_jobs)
        return new_jobs
        
    async def run(self, profile: str = 'all', force_refresh: bool = False) -> Dict:
        """主运行函数"""
        print(f"\n{'='*70}")
        print(f"LinkedIn Incremental Scraper v3.0")
        print(f"Max age: {self.max_age_hours} hours | Force refresh: {force_refresh}")
        print(f"{'='*70}\n")
        
        # 登录
        if not await self.login_with_cookies():
            print("[FATAL] Login failed")
            return self.stats
            
        # 加载配置
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        profiles = config.get('profiles', {})
        defaults = config.get('defaults', {})
        
        # 确定要运行的profiles
        if profile == 'all':
            profiles_to_run = [
                name for name, p in profiles.items() 
                if p.get('enabled', True)
            ]
        else:
            profiles_to_run = [profile]
            
        print(f"[Profiles] Running: {', '.join(profiles_to_run)}\n")
        
        # 运行每个profile
        for profile_name in profiles_to_run:
            profile_config = profiles.get(profile_name, {})
            await self.run_profile(profile_name, profile_config, defaults)
            
        # 完成统计
        self.stats['end_time'] = datetime.now().isoformat()
        self.stats['duration_seconds'] = (
            datetime.fromisoformat(self.stats['end_time']) - 
            datetime.fromisoformat(self.stats['start_time'])
        ).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"Scrape Complete")
        print(f"{'='*70}")
        print(f"Total scraped: {self.stats['scraped']}")
        print(f"New jobs: {self.stats['new_jobs']}")
        print(f"Duplicates skipped: {self.stats['duplicates_skipped']}")
        print(f"JD fetched: {self.stats['jd_fetched']}")
        print(f"Duration: {self.stats['duration_seconds']:.1f}s")
        
        return self.stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Incremental Scraper')
    parser.add_argument('--profile', default='all', help='Profile to run')
    parser.add_argument('--max-age-hours', type=int, default=4, help='Max job age in hours')
    parser.add_argument('--headless', action='store_true', default=True, help='Run headless')
    parser.add_argument('--force-refresh', action='store_true', help='Force refresh all jobs')
    parser.add_argument('--save-to-db', action='store_true', help='Save to database')
    parser.add_argument('--output', default='stats.json', help='Output stats file')
    
    args = parser.parse_args()
    
    async def run():
        async with IncrementalScraper(headless=args.headless, max_age_hours=args.max_age_hours) as scraper:
            stats = await scraper.run(profile=args.profile, force_refresh=args.force_refresh)
            
            # 保存统计
            with open(args.output, 'w') as f:
                json.dump(stats, f, indent=2)
                
    asyncio.run(run())


if __name__ == '__main__':
    main()
