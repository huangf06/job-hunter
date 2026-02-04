"""
LinkedIn Job Scraper V6 - Multi-Profile Search with Boolean Queries
====================================================================

Features:
1. Read search profiles from YAML config
2. Support boolean search queries (OR combinations)
3. Company/title blacklist filtering
4. Auto-fetch job descriptions (JD)
5. Deduplication and merging
6. Optional SQLite database integration

Usage:
    # Run all enabled profiles
    python linkedin_scraper_v6.py

    # Run specific profile
    python linkedin_scraper_v6.py --profile ml_data

    # Save to database
    python linkedin_scraper_v6.py --profile ml_data --save-to-db

    # Save to database only (no JSON)
    python linkedin_scraper_v6.py --profile ml_data --save-to-db --no-json

    # Run with CDP (connect to existing browser)
    python linkedin_scraper_v6.py --profile quant --cdp

    # List all profiles
    python linkedin_scraper_v6.py --list

    # Skip JD fetching (fast mode)
    python linkedin_scraper_v6.py --no-jd
"""

import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from urllib.parse import urlencode

import yaml
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Optional database support
try:
    from src.db.job_db import JobDatabase
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
DATA_DIR = PROJECT_ROOT / "data"
CONFIG_DIR = PROJECT_ROOT / "config"
COOKIES_FILE = CONFIG_DIR / "linkedin_cookies.json"
PROFILES_FILE = CONFIG_DIR / "search_profiles.yaml"

DATA_DIR.mkdir(parents=True, exist_ok=True)

# Blocked resource types (speed up page loading)
BLOCKED_RESOURCES = ['image', 'media', 'font', 'stylesheet']
BLOCKED_URL_PATTERNS = ['analytics', 'tracking', 'ads', 'beacon', 'pixel', 'telemetry', 'metrics']


class SearchConfig:
    """Search configuration manager"""

    def __init__(self, config_path: Path = PROFILES_FILE):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> dict:
        """Load configuration file"""
        if not self.config_path.exists():
            print(f"[Config] Config file not found: {self.config_path}")
            return self._default_config()

        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"[Config] Loaded config: {self.config_path}")
        return config

    def _default_config(self) -> dict:
        """Default configuration"""
        return {
            "defaults": {
                "location": "Netherlands",
                "date_posted": "r86400",
                "workplace_type": "2,3",
                "sort_by": "DD",
                "max_jobs": 50
            },
            "profiles": {
                "default": {
                    "name": "Default Search",
                    "enabled": True,
                    "queries": [{"keywords": "data engineer", "description": "Default search"}]
                }
            },
            "company_blacklist": [],
            "title_blacklist": []
        }

    @property
    def defaults(self) -> dict:
        return self.config.get("defaults", {})

    @property
    def profiles(self) -> dict:
        return self.config.get("profiles", {})

    @property
    def company_blacklist(self) -> List[str]:
        return [c.lower() for c in self.config.get("company_blacklist", [])]

    @property
    def title_blacklist(self) -> List[str]:
        return [t.lower() for t in self.config.get("title_blacklist", [])]

    def get_enabled_profiles(self) -> List[str]:
        """Get all enabled profile names"""
        return [
            name for name, profile in self.profiles.items()
            if profile.get("enabled", True)
        ]

    def get_profile(self, name: str) -> Optional[dict]:
        """Get specific profile"""
        return self.profiles.get(name)

    def list_profiles(self):
        """List all profiles"""
        print("\nAvailable Search Profiles:")
        print("-" * 60)
        for name, profile in self.profiles.items():
            status = "Y" if profile.get("enabled", True) else "N"
            queries_count = len(profile.get("queries", []))
            print(f"  [{status}] {name}")
            print(f"      Name: {profile.get('name', 'N/A')}")
            print(f"      Queries: {queries_count}")
            for q in profile.get("queries", []):
                print(f"        - {q.get('description', q.get('keywords', '')[:40])}")
        print("-" * 60)


class LinkedInScraperV6:
    """LinkedIn Scraper V6 - Supports config file and database"""

    def __init__(self, config: SearchConfig, headless: bool = False, use_cdp: bool = False, cdp_url: str = "http://localhost:9222"):
        self.config = config
        self.headless = headless
        self.use_cdp = use_cdp
        self.cdp_url = cdp_url
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.all_jobs: List[Dict] = []
        self.seen_keys: Set[str] = set()
        # Database support
        self.db = JobDatabase() if DB_AVAILABLE else None
        self.saved_to_db = 0
        self.skipped_duplicates = 0

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
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                ]
            )
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="Europe/Amsterdam",
            )

            await self.context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
            """)

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
        """Setup request interception"""
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

    async def login_with_cookies(self) -> bool:
        """Login with cookies"""
        print("\n[LinkedIn] Checking login status...")

        if not COOKIES_FILE.exists():
            print("  [NO] Cookies file not found")
            return await self._manual_login()

        try:
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)
            await self.context.add_cookies(cookies)

            print("  -> Verifying login...")
            await self._safe_goto("https://www.linkedin.com/feed/", timeout=30000)
            await asyncio.sleep(2)

            if "/feed" in self.page.url:
                print("  [OK] Login successful")
                return True
            else:
                print("  [NO] Cookies expired")
                return await self._manual_login()

        except Exception as e:
            print(f"  [NO] Login failed: {e}")
            return await self._manual_login()

    async def _manual_login(self) -> bool:
        """Manual login"""
        print("  -> Please login to LinkedIn manually...")
        await self._safe_goto("https://www.linkedin.com/login", timeout=30000)
        input("Press Enter after login...")

        try:
            cookies = await self.context.cookies()
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            print("  [OK] Cookies saved")
            return True
        except Exception as e:
            print(f"  [!] Failed to save cookies: {e}")
            return True

    async def _safe_goto(self, url: str, timeout: int = 60000, retries: int = 3) -> bool:
        """Safe page navigation"""
        for attempt in range(retries):
            try:
                print(f"  -> Loading page (attempt {attempt + 1}/{retries})...")
                response = await self.page.goto(url, wait_until="commit", timeout=timeout)
                await asyncio.sleep(3)
                if response and response.ok:
                    print(f"  [OK] Page loaded (status: {response.status})")
                    return True
                else:
                    print(f"  [!] Page response error (status: {response.status if response else 'None'})")
            except PlaywrightTimeout:
                print(f"  [!] Timeout, checking page content...")
                await asyncio.sleep(2)
                try:
                    content = await self.page.content()
                    if len(content) > 1000:
                        print(f"  -> Page partially loaded ({len(content)} bytes), continuing")
                        return True
                except:
                    pass
            except Exception as e:
                print(f"  [NO] Navigation error: {e}")

            if attempt < retries - 1:
                print(f"  -> Waiting 3s before retry...")
                await asyncio.sleep(3)
        return False

    async def run_profile(self, profile_name: str, fetch_jd: bool = True, save_to_db: bool = False) -> List[Dict]:
        """Run all queries for a profile

        Args:
            profile_name: Profile name from config
            fetch_jd: Whether to fetch job descriptions
            save_to_db: Whether to save directly to database
        """
        profile = self.config.get_profile(profile_name)
        if not profile:
            print(f"[Error] Profile not found: {profile_name}")
            return []

        print(f"\n{'='*70}")
        print(f"[Profile] {profile.get('name', profile_name)}")
        print(f"{'='*70}")

        queries = profile.get("queries", [])
        location = profile.get("location_override", self.config.defaults.get("location", "Netherlands"))
        max_jobs = profile.get("max_jobs_override", self.config.defaults.get("max_jobs", 50))

        profile_jobs = []

        for i, query in enumerate(queries, 1):
            keywords = query.get("keywords", "")
            description = query.get("description", keywords[:30])

            print(f"\n[Query {i}/{len(queries)}] {description}")
            print(f"  Keywords: {keywords[:60]}{'...' if len(keywords) > 60 else ''}")

            jobs = await self._scrape_single_query(keywords, location, max_jobs // len(queries))

            # Blacklist filter
            filtered_jobs = self._filter_blacklist(jobs)
            profile_jobs.extend(filtered_jobs)

            # Add to global dedup set
            for job in filtered_jobs:
                key = f"{job['title']}-{job['company']}"
                if key not in self.seen_keys:
                    self.seen_keys.add(key)
                    self.all_jobs.append(job)

            print(f"  -> Added: {len(filtered_jobs)} jobs (after filter)")

            # Delay between queries
            if i < len(queries):
                print("  -> Waiting 5s before next query...")
                await asyncio.sleep(5)

        # Fetch JD for all jobs
        if fetch_jd and self.all_jobs:
            jobs_without_jd = [j for j in self.all_jobs if not j.get('description') and j.get('url')]
            if jobs_without_jd:
                await self.fetch_job_descriptions(jobs_without_jd)

        # Save to database if requested
        if save_to_db and self.db:
            print(f"\n[Database] Saving {len(profile_jobs)} jobs to database...")
            for job in profile_jobs:
                job['search_profile'] = profile_name
                job['search_query'] = profile_name
                if self.db.job_exists(job.get('url', '')):
                    self.skipped_duplicates += 1
                    continue
                try:
                    self.db.insert_job(job)
                    self.saved_to_db += 1
                except Exception as e:
                    print(f"  ! Failed to save job: {e}")
            print(f"[Database] Saved: {self.saved_to_db}, Duplicates skipped: {self.skipped_duplicates}")

        return profile_jobs

    async def _scrape_single_query(self, keywords: str, location: str, max_jobs: int) -> List[Dict]:
        """Execute single search query"""
        defaults = self.config.defaults

        params = {
            "keywords": keywords,
            "location": location,
            "f_TPR": defaults.get("date_posted", "r86400"),
            "f_WT": defaults.get("workplace_type", "2,3"),
            "sortBy": defaults.get("sort_by", "DD")
        }
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
        print(f"  URL: {url[:80]}...")

        if not await self._safe_goto(url, timeout=45000):
            print("  [NO] Failed to load search page")
            return []

        # Wait for page render
        print("  -> Waiting for page render...")
        await asyncio.sleep(5)

        # Wait for job list
        found = await self._wait_for_jobs_list()
        if not found:
            print("  [!] Job list not found, continuing...")

        return await self._extract_jobs(max_jobs)

    async def _wait_for_jobs_list(self, timeout: int = 15000):
        """Wait for job list"""
        print("  -> Waiting for job list...")
        selectors = [
            ".jobs-search-results__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
            ".scaffold-layout__list-container",
        ]
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=timeout // len(selectors))
                print(f"  [OK] Found job list ({selector})")
                return True
            except:
                continue
        print("  [!] Standard job list selector not found")
        return False

    async def _extract_jobs(self, max_jobs: int) -> List[Dict]:
        """Extract jobs"""
        jobs = []
        seen = set()
        no_new_count = 0

        print(f"  -> Starting job extraction (max {max_jobs})...")

        for scroll_round in range(15):
            cards = await self._get_job_cards()

            if not cards:
                print(f"    Round {scroll_round + 1}: No job cards found")
                no_new_count += 1
                if no_new_count >= 3:
                    print("  -> No cards for 3 rounds, stopping")
                    break
                await self._scroll_and_wait()
                continue

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
                        print(f"    [{len(jobs)}] {job['title'][:35]} @ {job['company'][:20]}")

            print(f"    Round {scroll_round + 1}: {len(cards)} cards, {new_count} new")

            if new_count == 0:
                no_new_count += 1
                if no_new_count >= 3:
                    print("  -> No new jobs for 3 rounds, stopping scroll")
                    break
            else:
                no_new_count = 0

            if len(jobs) >= max_jobs:
                break

            await self._scroll_and_wait()

        print(f"  [OK] Extracted {len(jobs)} jobs this query")
        return jobs

    async def fetch_job_descriptions(self, jobs: List[Dict]) -> List[Dict]:
        """Fetch job descriptions"""
        if not jobs:
            return jobs

        jobs_to_fetch = [j for j in jobs if j.get('url')]

        if not jobs_to_fetch:
            return jobs

        print(f"\n  [JD] Fetching descriptions for {len(jobs_to_fetch)} jobs...")

        fetched_count = 0
        for i, job in enumerate(jobs_to_fetch):
            url = job.get('url', '')
            if not url:
                continue

            try:
                description = await self._fetch_single_jd(url)
                if description:
                    job['description'] = description
                    fetched_count += 1
                    print(f"    [{i+1}/{len(jobs_to_fetch)}] {job['title'][:30]} - {len(description)} chars")
                else:
                    print(f"    [{i+1}/{len(jobs_to_fetch)}] {job['title'][:30]} - no description found")

                # 更保守的间隔避免被限流
                await asyncio.sleep(2.0 + (1.0 * (i % 3)))

            except Exception as e:
                print(f"    [{i+1}/{len(jobs_to_fetch)}] {job['title'][:30]} - error: {str(e)[:30]}")
                continue

        print(f"  [JD] Fetched {fetched_count}/{len(jobs_to_fetch)} descriptions")
        return jobs

    async def _fetch_single_jd(self, url: str) -> Optional[str]:
        """Fetch single job description"""
        try:
            # 使用 domcontentloaded 确保基本DOM已加载
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 等待页面稳定
            await asyncio.sleep(3)

            # JD选择器 - 按优先级排列
            jd_selectors = [
                ".jobs-description__content",
                ".jobs-box__html-content",
                ".jobs-description-content__text",
                "#job-details",
                "article[class*='jobs-description']",
                ".jobs-description",
                "[class*='description']",
                ".job-view-layout",
            ]

            # 先尝试等待JD元素出现
            for selector in jd_selectors[:4]:
                try:
                    await self.page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue

            # 尝试点击 "Show more" / "See more" 按钮展开完整JD
            show_more_selectors = [
                "button[aria-label*='Show more']",
                "button[aria-label*='See more']",
                ".jobs-description__footer-button",
                "button.show-more-less-html__button",
                "[class*='show-more']",
            ]
            for btn_selector in show_more_selectors:
                try:
                    btn = await self.page.query_selector(btn_selector)
                    if btn:
                        await btn.click()
                        await asyncio.sleep(0.5)
                        break
                except:
                    continue

            # 提取JD文本
            for selector in jd_selectors:
                try:
                    el = await self.page.query_selector(selector)
                    if el:
                        text = await el.inner_text()
                        if text and len(text.strip()) > 100:
                            description = text.strip()
                            description = re.sub(r'\n{3,}', '\n\n', description)
                            description = re.sub(r' {2,}', ' ', description)
                            return description[:5000]
                except:
                    continue

            return None

        except Exception as e:
            return None

    async def _get_job_cards(self) -> List:
        """Get job cards"""
        selectors = [
            ".jobs-search-results__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
            ".scaffold-layout__list-item",
            "[data-job-id]",
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
        """Parse job card"""
        try:
            title = await self._get_text(card, [
                ".job-card-list__title strong",
                ".job-card-list__title",
                "h3 strong",
                "a[class*='title']",
            ])

            company = await self._get_text(card, [
                ".job-card-container__company-name",
                ".artdeco-entity-lockup__subtitle",
                ".job-card-container__company-link",
                ".job-card-container__primary-description",
            ])

            location = await self._get_text(card, [
                ".job-card-container__metadata-item",
                ".artdeco-entity-lockup__caption",
            ])

            link_el = await card.query_selector("a[href*='/jobs/view/']")
            if not link_el:
                link_el = await card.query_selector("a.job-card-list__title")
            if not link_el:
                link_el = await card.query_selector("a")
            href = await link_el.get_attribute("href") if link_el else ""
            url = href.split('?')[0] if href else ""
            if url and not url.startswith("http"):
                url = f"https://www.linkedin.com{url}"

            title = self._clean_title(title) if title else ""
            company = company.strip().replace("\n", " ") if company else ""

            if title and company and url:
                return {
                    "title": title,
                    "company": company,
                    "location": location.strip() if location else "",
                    "url": url,
                    "source": "LinkedIn",
                    "scraped_at": datetime.now().isoformat()
                }
        except Exception as e:
            pass
        return None

    def _clean_title(self, title: str) -> str:
        """Clean title - remove duplicates and 'with verification' suffix"""
        if not title:
            return ""

        title = title.strip().replace("\n", " ")
        title = re.sub(r'\s*with verification\s*$', '', title, flags=re.IGNORECASE)

        parts = re.split(r'\s{2,}', title)
        if len(parts) >= 2:
            first_part = parts[0].strip()
            second_part = parts[1].strip() if len(parts) > 1 else ""

            if second_part and (second_part.startswith(first_part) or first_part.startswith(second_part)):
                title = first_part
            elif second_part == first_part:
                title = first_part

        title = re.sub(r'\s+', ' ', title).strip()

        return title

    async def _get_text(self, parent, selectors: List[str]) -> str:
        """Get text"""
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
        """Scroll and wait"""
        await self.page.evaluate("window.scrollBy(0, 600)")
        await asyncio.sleep(1.5)

    def _filter_blacklist(self, jobs: List[Dict]) -> List[Dict]:
        """Filter blacklist companies and titles"""
        filtered = []
        company_blacklist = self.config.company_blacklist
        title_blacklist = self.config.title_blacklist

        for job in jobs:
            title_lower = job["title"].lower()
            company_lower = job["company"].lower()

            if any(bl in company_lower for bl in company_blacklist):
                continue

            if any(bl in title_lower for bl in title_blacklist):
                continue

            key = f"{job['title']}-{job['company']}"
            if key in self.seen_keys:
                continue

            filtered.append(job)

        return filtered

    def save_results(self, profile_name: str = "all", save_json: bool = True) -> Optional[Path]:
        """Save results to JSON file

        Args:
            profile_name: Profile name for filename
            save_json: Whether to save JSON file

        Returns:
            Path to saved file or None
        """
        if not save_json:
            print(f"\n[Database] {self.saved_to_db} jobs saved to database")
            return None

        date_str = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"linkedin_{profile_name}_{date_str}.json"
        filepath = DATA_DIR / filename

        data = {
            "source": "LinkedIn",
            "profile": profile_name,
            "scraped_at": datetime.now().isoformat(),
            "total_jobs": len(self.all_jobs),
            "with_jd": len([j for j in self.all_jobs if j.get("description")]),
            "jobs": self.all_jobs
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\n[OK] Saved: {filepath}")
        return filepath

    def print_summary(self):
        """Print summary"""
        print("\n" + "=" * 70)
        print("Scraping Results Summary")
        print("=" * 70)

        with_jd = [j for j in self.all_jobs if j.get("description")]

        print(f"\nTotal: {len(self.all_jobs)} jobs (after dedup)")
        print(f"  With JD: {len(with_jd)}")

        if self.all_jobs:
            print(f"\nJob list (top 10):")
            for job in self.all_jobs[:10]:
                jd_mark = "[JD]" if job.get("description") else ""
                print(f"  - {job['title'][:40]} @ {job['company'][:25]} {jd_mark}")

        # Database summary
        if self.db and self.saved_to_db > 0:
            print(f"\n[Database Summary]")
            print(f"  New jobs saved: {self.saved_to_db}")
            print(f"  Duplicates skipped: {self.skipped_duplicates}")
            stats = self.db.get_funnel_stats()
            print(f"\n  Database totals:")
            print(f"    Total scraped: {stats.get('total_scraped', 0)}")
            print(f"    Passed filter: {stats.get('passed_filter', 0)}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn Job Scraper V6 - Multi-Profile Boolean Search")
    parser.add_argument("--profile", type=str, help="Run specific profile (default: all enabled)")
    parser.add_argument("--list", action="store_true", help="List all profiles")
    parser.add_argument("--headless", action="store_true", help="Headless mode")
    parser.add_argument("--cdp", action="store_true", help="Use CDP to connect to existing browser")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="CDP URL")
    parser.add_argument("--no-jd", action="store_true", help="Skip JD fetching (fast mode)")
    parser.add_argument("--no-db", action="store_true", help="Don't save to database")
    parser.add_argument("--no-json", action="store_true", help="Don't save JSON file")
    args = parser.parse_args()

    config = SearchConfig()

    if args.list:
        config.list_profiles()
        return

    save_to_db = not args.no_db
    if save_to_db and not DB_AVAILABLE:
        print("Warning: Database module not available, skipping DB save")
        save_to_db = False

    print("=" * 70)
    print("LinkedIn Job Scraper V6")
    print("=" * 70)

    if args.profile:
        profiles_to_run = [args.profile]
    else:
        profiles_to_run = config.get_enabled_profiles()

    print(f"Will run {len(profiles_to_run)} profiles: {', '.join(profiles_to_run)}")
    if save_to_db:
        print("Mode: Save to database")

    async with LinkedInScraperV6(
        config=config,
        headless=args.headless,
        use_cdp=args.cdp,
        cdp_url=args.cdp_url
    ) as scraper:
        if not await scraper.login_with_cookies():
            print("[FAIL] Login failed")
            return

        for profile_name in profiles_to_run:
            await scraper.run_profile(
                profile_name,
                fetch_jd=not args.no_jd,
                save_to_db=save_to_db
            )

            if profile_name != profiles_to_run[-1]:
                print("\n-> Waiting 10s before next profile...")
                await asyncio.sleep(10)

        profile_label = args.profile if args.profile else "all"
        scraper.save_results(profile_label, save_json=not args.no_json)
        scraper.print_summary()

        print("\n" + "=" * 70)
        print(f"Done! Total {len(scraper.all_jobs)} jobs")
        if save_to_db:
            print(f"  Database new: {scraper.saved_to_db}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
