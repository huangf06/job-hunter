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

    # Save to database (opt-in)
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
import random
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from urllib.parse import urlencode

# Fix Windows console encoding — emoji/CJK in job titles would crash print()
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, 'reconfigure') and getattr(_stream, 'encoding', 'utf-8').lower() not in ('utf-8', 'utf8'):
        _stream.reconfigure(errors='replace')

import yaml
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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

# LinkedIn returns this many jobs per page (used for URL-based pagination)
JOBS_PER_PAGE = 25


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
                "workplace_type": "1,3",
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
        # Database support (lazy init — only connect when save_to_db is used)
        self._db = None
        self.saved_to_db = 0
        self.skipped_duplicates = 0
        self._saved_job_urls: Set[str] = set()  # Track URLs already saved to DB

    @property
    def db(self):
        """Lazy database initialization."""
        if self._db is None and DB_AVAILABLE:
            self._db = JobDatabase()
        return self._db

    async def __aenter__(self):
        self.playwright = await async_playwright().start()

        if self.use_cdp:
            print(f"[Browser] Connecting to CDP: {self.cdp_url}")
            # Quick port check before attempting CDP (avoids 10s timeout)
            import socket
            from urllib.parse import urlparse
            parsed = urlparse(self.cdp_url)
            host = parsed.hostname or "localhost"
            port = parsed.port or 9222
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((host, port))
                sock.close()
                cdp_reachable = True
            except (ConnectionRefusedError, OSError):
                sock.close()
                cdp_reachable = False

            if not cdp_reachable:
                print(f"  [SKIP] CDP port {port} not reachable — no Chrome with --remote-debugging-port?")
                print("  -> Falling back to built-in browser")
                self.use_cdp = False
            else:
                try:
                    self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url, timeout=10000)
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
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
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
            if not isinstance(cookies, list) or len(cookies) == 0:
                print("  [NO] Cookies file is empty or malformed (expected non-empty list)")
                return await self._manual_login()
            # Validate individual cookie objects (must have name, value, domain)
            valid_cookies = []
            for c in cookies:
                if not isinstance(c, dict):
                    continue
                if not all(c.get(k) for k in ('name', 'value', 'domain')):
                    continue
                valid_cookies.append(c)
            if not valid_cookies:
                print("  [NO] No valid cookies found (each needs name, value, domain)")
                return await self._manual_login()
            if len(valid_cookies) < len(cookies):
                print(f"  [WARN] Skipped {len(cookies) - len(valid_cookies)} malformed cookie(s)")
            # Verify session cookie exists (li_at is required for LinkedIn auth)
            has_session = any(c.get('name') == 'li_at' for c in valid_cookies)
            if not has_session:
                print("  [WARN] No 'li_at' session cookie found — login may fail")
            await self.context.add_cookies(valid_cookies)

            print("  -> Verifying login...")
            await self._safe_goto("https://www.linkedin.com/feed/", timeout=30000)
            await asyncio.sleep(2)

            expired_markers = ["/login", "/checkpoint", "/authwall", "/uas/"]
            if any(marker in self.page.url for marker in expired_markers):
                print("  [NO] Cookies expired")
                return await self._manual_login()
            else:
                print("  [OK] Login successful")
                return True

        except Exception as e:
            print(f"  [NO] Login failed: {e}")
            return await self._manual_login()

    async def _manual_login(self) -> bool:
        """Manual login"""
        if not sys.stdin.isatty():
            print("  [FATAL] Cannot prompt for login in non-interactive mode — aborting")
            return False
        print("  -> Please login to LinkedIn manually...")
        await self._safe_goto("https://www.linkedin.com/login", timeout=30000)
        input("Press Enter after login...")

        try:
            cookies = await self.context.cookies()
            COOKIES_FILE.parent.mkdir(parents=True, exist_ok=True)
            # Atomic write: temp file + rename to prevent corruption on crash
            tmp_path = COOKIES_FILE.with_suffix('.tmp')
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2)
            tmp_path.replace(COOKIES_FILE)
            print("  [OK] Cookies saved")
            return True
        except Exception as e:
            print(f"  [WARN] Cookies NOT saved — you will need to login again next time: {e}")
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
                    # Check for CAPTCHA on non-OK responses too
                    try:
                        content = await self.page.content()
                        content_lower = content.lower()
                        captcha_markers = ['captcha', 'challenge', 'verify you are human', 'security check']
                        if any(m in content_lower for m in captcha_markers):
                            print(f"  [!] CAPTCHA/challenge page detected")
                            if sys.stdin.isatty():
                                input("  -> Solve the CAPTCHA in the browser, then press Enter...")
                                return True
                            else:
                                print(f"  [!] Non-interactive mode, cannot solve CAPTCHA — aborting")
                                return False
                    except Exception:
                        pass
            except PlaywrightTimeout:
                print(f"  [!] Timeout, checking page content...")
                await asyncio.sleep(2)
                try:
                    content = await self.page.content()
                    content_lower = content.lower()
                    # Detect CAPTCHA / challenge pages
                    captcha_markers = ['captcha', 'challenge', 'verify you are human', 'security check']
                    if any(m in content_lower for m in captcha_markers):
                        print(f"  [!] CAPTCHA/challenge page detected — pausing for manual solve")
                        if sys.stdin.isatty():
                            input("  -> Solve the CAPTCHA in the browser, then press Enter...")
                            return True
                        else:
                            print(f"  [!] Non-interactive mode, cannot solve CAPTCHA — aborting")
                            return False
                    # Validate page has actual job content, not an error page
                    elif len(content) > 1000 and ('jobs' in content_lower or 'linkedin' in content_lower):
                        print(f"  -> Page partially loaded ({len(content)} bytes), continuing")
                        return True
                    else:
                        print(f"  [!] Page content too short or missing expected elements ({len(content)} bytes)")
                except Exception:
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

            jobs = await self._scrape_single_query(keywords, location, max(1, -(-max_jobs // len(queries))), db=self.db if save_to_db else None)

            # Blacklist filter
            filtered_jobs = self._filter_blacklist(jobs)
            profile_jobs.extend(filtered_jobs)

            # Add to global dedup set
            for job in filtered_jobs:
                key = f"{job['title']}-{job['company']}-{job.get('location', '')}"
                if key not in self.seen_keys:
                    self.seen_keys.add(key)
                    self.all_jobs.append(job)

            print(f"  -> Added: {len(filtered_jobs)} jobs (after filter)")

            # Delay between queries
            if i < len(queries):
                delay = random.uniform(3, 8)
                print(f"  -> Waiting {delay:.1f}s before next query...")
                await asyncio.sleep(delay)

        # Fetch JD for all jobs
        if fetch_jd and self.all_jobs:
            jobs_without_jd = [j for j in self.all_jobs if not j.get('description') and j.get('url')]

            # 如果有数据库且用户请求了DB模式，过滤掉已有完整JD的职位
            if jobs_without_jd and save_to_db and self.db:
                urls = [j['url'] for j in jobs_without_jd]
                urls_needing_jd = set(self.db.filter_urls_needing_jd(urls))
                skipped_count = len(jobs_without_jd) - len(urls_needing_jd)
                jobs_without_jd = [j for j in jobs_without_jd if j['url'] in urls_needing_jd]
                if skipped_count > 0:
                    print(f"  -> Skipped {skipped_count} jobs (JD already in DB)")

            if jobs_without_jd:
                await self.fetch_job_descriptions(jobs_without_jd)

        # Save to database if requested (only save jobs not yet saved in this session)
        if save_to_db and self.db:
            unsaved = [j for j in self.all_jobs if j.get('url') not in self._saved_job_urls]
            if unsaved:
                print(f"\n[Database] Saving {len(unsaved)} new jobs to database...")
                for job in unsaved:
                    if not job.get('search_profile'):
                        job['search_profile'] = profile_name
                    if not job.get('search_query'):
                        job['search_query'] = profile_name
                    try:
                        _, was_inserted = self.db.insert_job(job)
                        if was_inserted:
                            self.saved_to_db += 1
                        else:
                            self.skipped_duplicates += 1
                        self._saved_job_urls.add(job.get('url', ''))
                    except Exception as e:
                        print(f"  ! Failed to save job: {e}")
                print(f"[Database] Saved: {self.saved_to_db}, Duplicates skipped: {self.skipped_duplicates}")

        return profile_jobs

    async def _scrape_single_query(self, keywords: str, location: str, max_jobs: int, db=None) -> List[Dict]:
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

        return await self._extract_jobs(max_jobs, base_url=url, db=db)

    async def _wait_for_jobs_list(self, timeout: int = 15000):
        """Wait for job cards to appear on the page"""
        elapsed = 0
        while elapsed < timeout:
            cards = await self._get_job_cards()
            if cards:
                print(f"  [OK] Found {len(cards)} job cards")
                return True
            await asyncio.sleep(1)
            elapsed += 1000
        print("  [!] No job cards found within timeout")
        return False

    async def _extract_jobs(self, max_jobs: int, base_url: str = "", db=None) -> List[Dict]:
        """Extract jobs across all pages (LinkedIn paginates ~25 per page)"""
        jobs = []
        seen = set()
        page = 1
        max_pages = 20  # safety limit

        print(f"  -> Starting job extraction (max {max_jobs})...")

        while page <= max_pages and len(jobs) < max_jobs:
            # Get all card elements on current page
            cards = await self._get_job_cards()
            if not cards:
                print(f"    Page {page}: no cards found")
                break

            # Scroll each card into viewport to un-occlude its content
            page_new = 0
            page_urls = []
            for card in cards:
                if len(jobs) >= max_jobs:
                    break

                try:
                    await card.scroll_into_view_if_needed(timeout=2000)
                    await asyncio.sleep(0.15)
                except Exception:
                    pass

                job = await self._parse_card(card)
                if job:
                    key = f"{job['title']}-{job['company']}-{job.get('location', '')}"
                    if key not in seen:
                        seen.add(key)
                        jobs.append(job)
                        page_new += 1
                        if job.get('url'):
                            page_urls.append(job['url'])
                        print(f"    [{len(jobs)}] {job['title'][:35]} @ {job['company'][:20]}")

            print(f"    Page {page}: {page_new} jobs extracted (total: {len(jobs)})")

            if len(jobs) >= max_jobs:
                break

            # If this page yielded 0 new jobs, no point continuing
            if page_new == 0:
                print(f"  -> Page {page} had 0 new jobs, stopping pagination")
                break

            # Smart stop: if most jobs on this page are already in DB, stop
            if db and page_urls:
                new_urls = set(db.filter_urls_needing_jd(page_urls))
                known_ratio = 1 - (len(new_urls) / len(page_urls))
                if known_ratio >= 0.8:
                    print(f"  -> Smart stop: {known_ratio:.0%} of page {page} already in DB, stopping")
                    break

            # Try to go to next page
            has_next = await self._goto_next_page(page, base_url)
            if not has_next:
                print(f"  -> No more pages after page {page}")
                break

            page += 1
            await asyncio.sleep(random.uniform(2, 5))  # randomized page delay

            # Wait for new page's job list to load
            await self._wait_for_jobs_list(timeout=10000)
            await asyncio.sleep(2)

            # Scroll to top for fresh extraction
            await self._scroll_job_list_to_top()

        print(f"  [OK] Extracted {len(jobs)} jobs across {page} page(s)")
        return jobs

    async def _goto_next_page(self, current_page: int, base_url: str = "") -> bool:
        """Navigate to the next page of results. Returns True if successful."""
        next_page = current_page + 1
        print(f"  -> Attempting pagination to page {next_page}...")

        # Strategy 1: Click button with specific page number aria-label
        try:
            for label_pattern in [
                f'button[aria-label="Page {next_page}"]',
                f'li[data-test-pagination-page-btn="{next_page}"] button',
            ]:
                btn = await self.page.query_selector(label_pattern)
                if btn and await btn.is_visible():
                    await btn.click()
                    print(f"  [OK] Clicked page {next_page} button (aria-label)")
                    return True
        except Exception as e:
            print(f"  [WARN] Strategy 1 (aria-label) error: {e}")

        # Strategy 2: Find pagination container buttons by page number text
        try:
            for sel in [
                ".jobs-search-pagination",
                ".artdeco-pagination",
                "ul.artdeco-pagination__pages",
            ]:
                container = await self.page.query_selector(sel)
                if not container:
                    continue
                buttons = await container.query_selector_all("button")
                for btn in buttons:
                    text = (await btn.inner_text()).strip()
                    if text == str(next_page):
                        await btn.click()
                        print(f"  [OK] Clicked page {next_page} button (text match in {sel})")
                        return True
        except Exception as e:
            print(f"  [WARN] Strategy 2 (text match) error: {e}")

        # Strategy 3: "Next" / arrow button
        try:
            for sel in [
                'button[aria-label="Next"]',
                'button[aria-label="View next page"]',
                '.artdeco-pagination__button--next',
            ]:
                btn = await self.page.query_selector(sel)
                if btn and await btn.is_visible():
                    disabled = await btn.get_attribute("disabled")
                    if not disabled:
                        await btn.click()
                        print(f"  [OK] Clicked 'Next' button ({sel})")
                        return True
        except Exception as e:
            print(f"  [WARN] Strategy 3 (Next button) error: {e}")

        # Strategy 4: URL-based navigation (most reliable fallback)
        if base_url:
            start = (next_page - 1) * JOBS_PER_PAGE
            if '&start=' in base_url or '?start=' in base_url:
                paginated_url = re.sub(r'([?&])start=\d+', f'\\1start={start}', base_url)
            else:
                paginated_url = f"{base_url}&start={start}"
            print(f"  -> Falling back to URL pagination (start={start})")
            if await self._safe_goto(paginated_url, timeout=30000):
                print(f"  [OK] Navigated to page {next_page} via URL")
                return True
            else:
                print(f"  [FAIL] URL navigation failed")
                return False

        print(f"  [WARN] All pagination strategies failed for page {next_page}")
        return False

    async def fetch_job_descriptions(self, jobs: List[Dict]) -> List[Dict]:
        """Fetch job descriptions with consecutive failure bail-out"""
        if not jobs:
            return jobs

        jobs_to_fetch = [j for j in jobs if j.get('url')]

        if not jobs_to_fetch:
            return jobs

        print(f"\n  [JD] Fetching descriptions for {len(jobs_to_fetch)} jobs...")

        fetched_count = 0
        consecutive_failures = 0
        max_consecutive_failures = 5  # bail out if 5 in a row fail

        for i, job in enumerate(jobs_to_fetch):
            url = job.get('url', '')
            if not url:
                continue

            try:
                description = await self._fetch_single_jd(url)
                if description:
                    job['description'] = description
                    fetched_count += 1
                    consecutive_failures = 0
                    print(f"    [{i+1}/{len(jobs_to_fetch)}] {job['title'][:30]} - {len(description)} chars")
                else:
                    consecutive_failures += 1
                    print(f"    [{i+1}/{len(jobs_to_fetch)}] {job['title'][:30]} - no description found")

                    if consecutive_failures >= max_consecutive_failures:
                        remaining = len(jobs_to_fetch) - i - 1
                        print(f"  [JD] Bail out: {max_consecutive_failures} consecutive failures, skipping {remaining} remaining jobs")
                        break

                # 更保守的间隔避免被限流
                await asyncio.sleep(2.0 + (1.0 * (i % 3)))

            except Exception as e:
                consecutive_failures += 1
                print(f"    [{i+1}/{len(jobs_to_fetch)}] {job['title'][:30]} - error: {str(e)[:30]}")
                if consecutive_failures >= max_consecutive_failures:
                    remaining = len(jobs_to_fetch) - i - 1
                    print(f"  [JD] Bail out: {max_consecutive_failures} consecutive failures, skipping {remaining} remaining jobs")
                    break
                continue

        print(f"  [JD] Fetched {fetched_count}/{len(jobs_to_fetch)} descriptions")
        return jobs

    def _clean_jd_text(self, text: str) -> Optional[str]:
        """Clean and validate JD text"""
        if not text or len(text.strip()) < 100:
            return None
        description = text.strip()
        description = re.sub(r'\n{3,}', '\n\n', description)
        description = re.sub(r' {2,}', ' ', description)
        if len(description) > 15000:
            print(f"      [WARN] JD truncated from {len(description)} to 15000 chars")
        return description[:15000]

    async def _fetch_single_jd(self, url: str) -> Optional[str]:
        """Fetch single job description with multiple fallback strategies"""
        try:
            # 使用 domcontentloaded 确保基本DOM已加载
            await self.page.goto(url, wait_until="domcontentloaded", timeout=30000)

            # 检查是否被重定向到登录/auth页面
            current_url = self.page.url
            auth_markers = ["/login", "/checkpoint", "/authwall", "/uas/"]
            if any(marker in current_url for marker in auth_markers):
                print(f"      [AUTH] Redirected to auth page: {current_url[:80]}")
                return None

            # 等待页面稳定
            await asyncio.sleep(3)

            # === Strategy 1: CSS selectors (按优先级排列) ===
            jd_selectors = [
                ".jobs-description__content",
                ".jobs-box__html-content",
                ".jobs-description-content__text",
                "#job-details",
                ".show-more-less-html__markup",
                "article[class*='jobs-description']",
                ".jobs-description",
                "[class*='description']",
                ".job-view-layout",
            ]

            # 先尝试等待JD元素出现 (2s per selector)
            found_selector = False
            for selector in jd_selectors[:5]:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    found_selector = True
                    break
                except Exception:
                    continue

            # 尝试点击 "Show more" / "See more" 按钮展开完整JD
            if found_selector:
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
                    except Exception:
                        continue

            # 提取JD文本
            for selector in jd_selectors:
                try:
                    el = await self.page.query_selector(selector)
                    if el:
                        text = await el.inner_text()
                        result = self._clean_jd_text(text)
                        if result:
                            return result
                except Exception:
                    continue

            # === Strategy 2: JSON-LD structured data ===
            try:
                jsonld = await self.page.evaluate("""() => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const s of scripts) {
                        try {
                            const data = JSON.parse(s.textContent);
                            if (data.description) return data.description;
                            if (data['@type'] === 'JobPosting' && data.description) return data.description;
                        } catch(e) {}
                    }
                    return null;
                }""")
                if jsonld:
                    # JSON-LD description may contain HTML, strip tags
                    clean = re.sub(r'<[^>]+>', ' ', jsonld)
                    result = self._clean_jd_text(clean)
                    if result:
                        print(f"      [JSON-LD] Extracted via structured data")
                        return result
            except Exception:
                pass

            # === Strategy 3: Page body text fallback ===
            try:
                # 从 main 或 body 提取最长的文本块
                body_text = await self.page.evaluate("""() => {
                    const main = document.querySelector('main') || document.body;
                    if (!main) return '';
                    return main.innerText || '';
                }""")
                # 只在有足够内容时使用 body fallback
                result = self._clean_jd_text(body_text)
                if result and len(result) > 300:
                    print(f"      [BODY] Extracted via body text fallback")
                    return result
            except Exception:
                pass

            # === 所有策略都失败，打印诊断信息 ===
            try:
                title = await self.page.title()
                diag_text = await self.page.evaluate("() => document.body?.innerText?.substring(0, 300) || 'empty'")
                print(f"      [DIAG] title='{title[:60]}' body='{diag_text[:120]}...'")
            except Exception:
                pass

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
            except Exception:
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
            href = (await link_el.get_attribute("href") or "") if link_el else ""
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
            elif title and company:
                print(f"  [WARN] No URL found for: {title[:35]} @ {company[:20]}")
        except Exception as e:
            print(f"  [WARN] _parse_card error: {e}")
        return None

    def _clean_title(self, title: str) -> str:
        """Clean title - remove duplicates and 'with verification' suffix"""
        if not title:
            return ""

        title = title.strip().replace("\n", " ")
        title = re.sub(r'\s*with verification\s*$', '', title, flags=re.IGNORECASE)

        # Handle whitespace-separated duplicates: "Foo Bar  Foo Bar"
        parts = re.split(r'\s{2,}', title)
        if len(parts) >= 2:
            first_part = parts[0].strip()
            second_part = parts[1].strip() if len(parts) > 1 else ""

            if second_part and second_part == first_part:
                title = first_part

        # Handle concatenated duplicates (no separator):
        # "Senior Data EngineerSenior Data Engineer" or "Data Engineer (senior)Data Engineer"
        length = len(title)
        if length >= 10:
            mid = length // 2
            for pos in range(max(4, mid - 5), min(length - 3, mid + 6)):
                first = title[:pos]
                second = title[pos:]
                if first == second:
                    title = first
                    break
                # Second half is prefix of first (shorter variant repeat)
                if len(second) >= 5 and first.startswith(second):
                    title = first
                    break

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
            except Exception:
                continue
        return ""

    async def _scroll_job_list_to_top(self):
        """Scroll back to top (for fresh extraction after page transition)"""
        await self.page.evaluate("""
            (() => {
                const container = document.querySelector('.jobs-search-results-list')
                    || document.querySelector('.scaffold-layout__list')
                    || document.querySelector('.jobs-search__results-list');
                if (container && container.scrollHeight > container.clientHeight + 10) {
                    container.scrollTop = 0;
                } else {
                    window.scrollTo(0, 0);
                }
            })()
        """)
        await asyncio.sleep(0.5)

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

            key = f"{job['title']}-{job['company']}-{job.get('location', '')}"
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

        with open(filepath.with_suffix('.tmp'), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        filepath.with_suffix('.tmp').replace(filepath)

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

        # Database summary (use _db directly to avoid triggering lazy init)
        if self._db is not None and self.saved_to_db > 0:
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
    parser.add_argument("--save-to-db", action="store_true", help="Save results to database")
    parser.add_argument("--no-json", action="store_true", help="Don't save JSON file")
    args = parser.parse_args()

    config = SearchConfig()

    if args.list:
        config.list_profiles()
        return

    save_to_db = args.save_to_db
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
            sys.exit(1)

        try:
            for profile_name in profiles_to_run:
                await scraper.run_profile(
                    profile_name,
                    fetch_jd=not args.no_jd,
                    save_to_db=save_to_db
                )

                if profile_name != profiles_to_run[-1]:
                    print("\n-> Waiting 10s before next profile...")
                    await asyncio.sleep(10)

            print("\n" + "=" * 70)
            print(f"Done! Total {len(scraper.all_jobs)} jobs")
            if save_to_db:
                print(f"  Database new: {scraper.saved_to_db}")
            print("=" * 70)

            # Exit with non-zero code if zero jobs scraped (alerts CI)
            if len(scraper.all_jobs) == 0:
                print("[WARN] Zero jobs scraped — exiting with code 1")
                scraper.save_results(
                    args.profile if args.profile else "all",
                    save_json=not args.no_json
                )
                scraper.print_summary()
                sys.exit(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            print("\n\n[INTERRUPTED] Saving scraped data before exit...")
        finally:
            profile_label = args.profile if args.profile else "all"
            scraper.save_results(profile_label, save_json=not args.no_json)
            scraper.print_summary()

            # Write metrics for CI notification
            metrics = {
                "new_jobs": scraper.saved_to_db,
                "skipped_duplicates": scraper.skipped_duplicates,
                "total_scraped": len(scraper.all_jobs),
                "with_jd": len([j for j in scraper.all_jobs if j.get("description")])
            }
            metrics_path = Path(__file__).resolve().parent.parent / "data" / "scrape_metrics.json"
            metrics_path.parent.mkdir(parents=True, exist_ok=True)
            with open(metrics_path, "w") as f:
                json.dump(metrics, f)
            print(f"[Metrics] Written to {metrics_path}")


if __name__ == "__main__":
    asyncio.run(main())
