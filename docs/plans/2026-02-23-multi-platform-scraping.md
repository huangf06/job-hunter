# Multi-Platform Job Scraping — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add IamExpat Jobs, Greenhouse API, and Lever API scrapers to the existing LinkedIn-only pipeline.

**Architecture:** Plugin-style scrapers behind a `BaseScraper` ABC. Greenhouse/Lever use pure `requests` (public JSON APIs, no auth). IamExpat uses Playwright (Next.js site). All scrapers output the same job dict format and call `JobDatabase.insert_job()`. An orchestrator CLI (`multi_scraper.py`) runs all scrapers and integrates into CI.

**Tech Stack:** Python 3.11, requests, playwright, pyyaml, sqlite3 (existing DB layer)

**Key files to reference:**
- `src/db/job_db.py` — `JobDatabase.insert_job(job_data: Dict) -> (job_id, was_inserted)`, `batch_mode()`, `generate_job_id(url)`
- `scripts/linkedin_scraper_v6.py` — existing scraper pattern (async Playwright, `SearchConfig` class)
- `config/search_profiles.yaml` — `company_blacklist`, `title_blacklist`, profile structure
- `.github/workflows/job-pipeline-optimized.yml` — CI workflow to extend

---

### Task 1: BaseScraper ABC + package init

**Files:**
- Create: `src/scrapers/__init__.py`
- Create: `src/scrapers/base.py`
- Create: `tests/test_scrapers/__init__.py`
- Create: `tests/test_scrapers/test_base.py`

**Step 1: Create the scraper package**

```python
# src/scrapers/__init__.py
from src.scrapers.base import BaseScraper

__all__ = ["BaseScraper"]
```

**Step 2: Write BaseScraper**

```python
# src/scrapers/base.py
import logging
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import yaml

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase

logger = logging.getLogger(__name__)

CONFIG_DIR = PROJECT_ROOT / "config"
PROFILES_FILE = CONFIG_DIR / "search_profiles.yaml"


def load_blacklists(config_path: Path = PROFILES_FILE) -> dict:
    """Load company and title blacklists from search_profiles.yaml."""
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return {
        "company": [c.lower() for c in config.get("company_blacklist", [])],
        "title": [t.lower() for t in config.get("title_blacklist", [])],
    }


class BaseScraper(ABC):
    """Abstract base for all job scrapers."""

    source_name: str = "unknown"  # Override in subclass

    def __init__(self):
        self.db = JobDatabase()
        self.blacklists = load_blacklists()
        self.stats = {"found": 0, "new": 0, "skipped_blacklist": 0, "skipped_dup": 0}

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Scrape jobs and return list of job dicts (unified format)."""
        pass

    def is_blacklisted(self, job: Dict) -> bool:
        """Check if job matches company or title blacklist."""
        company = job.get("company", "").lower()
        title = job.get("title", "").lower()
        for bl in self.blacklists["company"]:
            if bl in company:
                return True
        for bl in self.blacklists["title"]:
            if bl in title:
                return True
        return False

    def save_jobs(self, jobs: List[Dict]) -> int:
        """Save jobs to DB using batch_mode. Returns count of new jobs."""
        new_count = 0
        with self.db.batch_mode():
            for job in jobs:
                if self.is_blacklisted(job):
                    self.stats["skipped_blacklist"] += 1
                    continue
                _, was_new = self.db.insert_job(job)
                if was_new:
                    new_count += 1
                else:
                    self.stats["skipped_dup"] += 1
        self.stats["new"] = new_count
        return new_count

    def run(self) -> Dict:
        """Scrape + save + return stats."""
        jobs = self.scrape()
        self.stats["found"] = len(jobs)
        self.save_jobs(jobs)
        logger.info(
            "[%s] Found: %d, New: %d, Blacklisted: %d, Dup: %d",
            self.source_name, self.stats["found"], self.stats["new"],
            self.stats["skipped_blacklist"], self.stats["skipped_dup"],
        )
        return self.stats
```

**Step 3: Write test for blacklist logic**

```python
# tests/test_scrapers/test_base.py
import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    source_name = "Test"
    def scrape(self):
        return []


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={
    "company": ["hays", "randstad"],
    "title": ["intern", "student"],
})
def test_blacklist_filters(mock_bl, mock_db):
    s = DummyScraper()
    assert s.is_blacklisted({"company": "Hays Netherlands", "title": "Data Engineer"})
    assert s.is_blacklisted({"company": "Google", "title": "ML Intern"})
    assert not s.is_blacklisted({"company": "Booking.com", "title": "Data Engineer"})
```

**Step 4: Run test**

Run: `pytest tests/test_scrapers/test_base.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/scrapers/ tests/test_scrapers/
git commit -m "feat: add BaseScraper ABC with blacklist filtering"
```

---

### Task 2: GreenhouseScraper

**Files:**
- Create: `src/scrapers/greenhouse.py`
- Create: `tests/test_scrapers/test_greenhouse.py`

**Step 1: Write test with mocked API response**

```python
# tests/test_scrapers/test_greenhouse.py
import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.greenhouse import GreenhouseScraper

MOCK_RESPONSE = {
    "jobs": [
        {
            "id": 123,
            "title": "Data Engineer",
            "location": {"name": "Amsterdam"},
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
            "updated_at": "2026-02-20T10:00:00-05:00",
            "content": "<p>Build data pipelines...</p>",
        },
        {
            "id": 456,
            "title": "Frontend Developer",
            "location": {"name": "New York"},
            "absolute_url": "https://boards.greenhouse.io/acme/jobs/456",
            "updated_at": "2026-02-19T10:00:00-05:00",
            "content": "<p>Build UIs...</p>",
        },
    ],
    "meta": {"total": 2},
}


@patch("src.scrapers.greenhouse.JobDatabase")
@patch("src.scrapers.greenhouse.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.greenhouse.requests.get")
def test_scrape_with_location_filter(mock_get, mock_bl, mock_db):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    company = {"name": "Acme", "ats": "greenhouse", "board_token": "acme", "location_filter": "Amsterdam"}
    scraper = GreenhouseScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Data Engineer"
    assert jobs[0]["company"] == "Acme"
    assert jobs[0]["source"] == "Greenhouse"
    assert "Build data pipelines" in jobs[0]["description"]


@patch("src.scrapers.greenhouse.JobDatabase")
@patch("src.scrapers.greenhouse.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.greenhouse.requests.get")
def test_scrape_no_location_filter(mock_get, mock_bl, mock_db):
    mock_resp = MagicMock()
    mock_resp.json.return_value = MOCK_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    company = {"name": "Acme", "ats": "greenhouse", "board_token": "acme"}
    scraper = GreenhouseScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 2  # No filter = all jobs
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrapers/test_greenhouse.py -v`
Expected: FAIL (module not found)

**Step 3: Implement GreenhouseScraper**

```python
# src/scrapers/greenhouse.py
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional

import requests

from src.scrapers.base import BaseScraper, load_blacklists

logger = logging.getLogger(__name__)

API_BASE = "https://boards-api.greenhouse.io/v1/boards"


def _html_to_text(html: str) -> str:
    """Strip HTML tags, decode entities, collapse whitespace."""
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"<li>", "\n- ", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&#\d+;", "", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


class GreenhouseScraper(BaseScraper):
    source_name = "Greenhouse"

    def __init__(self, companies: List[Dict]):
        super().__init__()
        self.companies = companies

    def _fetch_jobs(self, board_token: str) -> List[Dict]:
        """Fetch all jobs from a Greenhouse board."""
        url = f"{API_BASE}/{board_token}/jobs?content=true"
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json().get("jobs", [])

    def _matches_location(self, job: Dict, location_filter: Optional[str]) -> bool:
        if not location_filter:
            return True
        loc = job.get("location", {}).get("name", "")
        return location_filter.lower() in loc.lower()

    def _to_job_dict(self, raw: Dict, company_name: str) -> Dict:
        return {
            "title": raw.get("title", ""),
            "company": company_name,
            "location": raw.get("location", {}).get("name", ""),
            "url": raw.get("absolute_url", ""),
            "description": _html_to_text(raw.get("content", "")),
            "source": "Greenhouse",
            "scraped_at": datetime.now().isoformat(),
            "posted_date": raw.get("updated_at", ""),
            "search_profile": "ats",
            "search_query": f"greenhouse:{company_name}",
        }

    def scrape(self) -> List[Dict]:
        all_jobs = []
        for company in self.companies:
            if company.get("ats") != "greenhouse":
                continue
            token = company["board_token"]
            name = company["name"]
            loc_filter = company.get("location_filter")
            try:
                raw_jobs = self._fetch_jobs(token)
                for raw in raw_jobs:
                    if self._matches_location(raw, loc_filter):
                        all_jobs.append(self._to_job_dict(raw, name))
                logger.info("[Greenhouse] %s: %d jobs (filtered from %d)", name, len(all_jobs), len(raw_jobs))
            except Exception as e:
                logger.error("[Greenhouse] %s failed: %s", name, e)
        return all_jobs
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_scrapers/test_greenhouse.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/scrapers/greenhouse.py tests/test_scrapers/test_greenhouse.py
git commit -m "feat: add GreenhouseScraper with location filtering"
```

---

### Task 3: LeverScraper

**Files:**
- Create: `src/scrapers/lever.py`
- Create: `tests/test_scrapers/test_lever.py`

**Step 1: Write test with mocked API response**

```python
# tests/test_scrapers/test_lever.py
import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.lever import LeverScraper

MOCK_PAGE_1 = [
    {
        "id": "abc-123",
        "text": "ML Engineer",
        "categories": {"location": "Amsterdam, Netherlands", "commitment": "Full-time"},
        "hostedUrl": "https://jobs.lever.co/acme/abc-123",
        "descriptionPlain": "Build ML models...",
        "createdAt": 1708000000000,
    },
]


@patch("src.scrapers.lever.JobDatabase")
@patch("src.scrapers.lever.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.lever.requests.get")
def test_scrape_lever(mock_get, mock_bl, mock_db):
    # First call returns jobs, second returns empty (end of pagination)
    resp1 = MagicMock()
    resp1.json.return_value = MOCK_PAGE_1
    resp1.raise_for_status = MagicMock()
    resp2 = MagicMock()
    resp2.json.return_value = []
    resp2.raise_for_status = MagicMock()
    mock_get.side_effect = [resp1, resp2]

    company = {"name": "Acme", "ats": "lever", "board_token": "acme"}
    scraper = LeverScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 1
    assert jobs[0]["title"] == "ML Engineer"
    assert jobs[0]["source"] == "Lever"
    assert jobs[0]["location"] == "Amsterdam, Netherlands"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrapers/test_lever.py -v`
Expected: FAIL

**Step 3: Implement LeverScraper**

```python
# src/scrapers/lever.py
import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests

from src.scrapers.base import BaseScraper, load_blacklists

logger = logging.getLogger(__name__)

API_BASE = "https://api.lever.co/v0/postings"
PAGE_SIZE = 100


class LeverScraper(BaseScraper):
    source_name = "Lever"

    def __init__(self, companies: List[Dict]):
        super().__init__()
        self.companies = companies

    def _fetch_all_postings(self, board_token: str) -> List[Dict]:
        """Fetch all postings with pagination."""
        all_postings = []
        skip = 0
        while True:
            url = f"{API_BASE}/{board_token}?mode=json&limit={PAGE_SIZE}&skip={skip}"
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            page = resp.json()
            if not page:
                break
            all_postings.extend(page)
            if len(page) < PAGE_SIZE:
                break
            skip += PAGE_SIZE
        return all_postings

    def _matches_location(self, posting: Dict, location_filter: Optional[str]) -> bool:
        if not location_filter:
            return True
        loc = posting.get("categories", {}).get("location", "")
        return location_filter.lower() in loc.lower()

    def _to_job_dict(self, raw: Dict, company_name: str) -> Dict:
        created_ms = raw.get("createdAt", 0)
        posted_date = datetime.fromtimestamp(created_ms / 1000).isoformat() if created_ms else ""
        return {
            "title": raw.get("text", ""),
            "company": company_name,
            "location": raw.get("categories", {}).get("location", ""),
            "url": raw.get("hostedUrl", ""),
            "description": raw.get("descriptionPlain", ""),
            "source": "Lever",
            "scraped_at": datetime.now().isoformat(),
            "posted_date": posted_date,
            "search_profile": "ats",
            "search_query": f"lever:{company_name}",
        }

    def scrape(self) -> List[Dict]:
        all_jobs = []
        for company in self.companies:
            if company.get("ats") != "lever":
                continue
            token = company["board_token"]
            name = company["name"]
            loc_filter = company.get("location_filter")
            try:
                raw = self._fetch_all_postings(token)
                filtered = [self._to_job_dict(p, name) for p in raw if self._matches_location(p, loc_filter)]
                all_jobs.extend(filtered)
                logger.info("[Lever] %s: %d jobs (filtered from %d)", name, len(filtered), len(raw))
            except Exception as e:
                logger.error("[Lever] %s failed: %s", name, e)
        return all_jobs
```

**Step 4: Run test**

Run: `pytest tests/test_scrapers/test_lever.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/scrapers/lever.py tests/test_scrapers/test_lever.py
git commit -m "feat: add LeverScraper with pagination"
```

---

### Task 4: IamExpatScraper

**Files:**
- Create: `src/scrapers/iamexpat.py`
- Create: `tests/test_scrapers/test_iamexpat.py`

**Context:** IamExpat is a Next.js site — needs Playwright for rendering. Job listings at `iamexpat.nl/career/jobs-netherlands?search={kw}&page={n}`, 20 per page. Detail pages have full JD. The existing LinkedIn scraper uses async Playwright — follow the same pattern.

**Step 1: Write test for job dict conversion**

```python
# tests/test_scrapers/test_iamexpat.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.scrapers.iamexpat import IamExpatScraper


@patch("src.scrapers.iamexpat.JobDatabase")
@patch("src.scrapers.iamexpat.load_blacklists", return_value={"company": [], "title": []})
def test_to_job_dict(mock_bl, mock_db):
    scraper = IamExpatScraper(queries=[{"keywords": "data engineer"}])
    job = scraper._to_job_dict(
        title="Data Engineer",
        company="Booking.com",
        location="Amsterdam",
        url="https://www.iamexpat.nl/career/jobs-netherlands/it/data-engineer/abc123",
        description="Build pipelines...",
        query="data engineer",
    )
    assert job["title"] == "Data Engineer"
    assert job["source"] == "IamExpat"
    assert job["search_query"] == "data engineer"
    assert job["url"].startswith("https://")
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_scrapers/test_iamexpat.py -v`
Expected: FAIL

**Step 3: Implement IamExpatScraper**

```python
# src/scrapers/iamexpat.py
import asyncio
import logging
import re
from datetime import datetime
from typing import List, Dict
from playwright.async_api import async_playwright

from src.scrapers.base import BaseScraper, load_blacklists

logger = logging.getLogger(__name__)

BASE_URL = "https://www.iamexpat.nl/career/jobs-netherlands"
JOBS_PER_PAGE = 20


class IamExpatScraper(BaseScraper):
    source_name = "IamExpat"

    def __init__(self, queries: List[Dict], headless: bool = True, max_pages: int = 5):
        super().__init__()
        self.queries = queries
        self.headless = headless
        self.max_pages = max_pages

    def _to_job_dict(self, title: str, company: str, location: str,
                     url: str, description: str, query: str) -> Dict:
        return {
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "description": description,
            "source": "IamExpat",
            "scraped_at": datetime.now().isoformat(),
            "search_profile": "iamexpat",
            "search_query": query,
        }

    async def _scrape_listing_page(self, page, url: str) -> List[Dict]:
        """Extract job cards from a listing page. Returns list of {title, company, location, url}."""
        await page.goto(url, wait_until="networkidle", timeout=30000)
        # Wait for job cards to render
        await page.wait_for_selector("a[href*='/career/jobs-netherlands/']", timeout=10000)

        cards = await page.query_selector_all("a[href*='/career/jobs-netherlands/'][href*='/']")
        results = []
        seen_urls = set()
        for card in cards:
            href = await card.get_attribute("href")
            if not href or "/career/jobs-netherlands/" not in href:
                continue
            # Skip category/filter links (they don't have enough path segments)
            parts = href.rstrip("/").split("/")
            if len(parts) < 6:  # /career/jobs-netherlands/{cat}/{slug}/{id}
                continue
            full_url = f"https://www.iamexpat.nl{href}" if href.startswith("/") else href
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

            # Extract text from card
            text = await card.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            title = lines[0] if lines else ""
            company = lines[1] if len(lines) > 1 else ""
            location = lines[2] if len(lines) > 2 else ""

            if title:
                results.append({"title": title, "company": company,
                                "location": location, "url": full_url})
        return results

    async def _scrape_detail_page(self, page, url: str) -> str:
        """Fetch full JD from detail page."""
        try:
            await page.goto(url, wait_until="networkidle", timeout=20000)
            # Try JSON-LD first
            ld_el = await page.query_selector('script[type="application/ld+json"]')
            if ld_el:
                import json
                ld_text = await ld_el.inner_text()
                ld = json.loads(ld_text)
                desc = ld.get("description", "")
                if desc:
                    return desc
            # Fallback: grab main content area
            content = await page.query_selector("article, .job-description, main")
            if content:
                return await content.inner_text()
            return await page.inner_text("body")
        except Exception as e:
            logger.warning("[IamExpat] Failed to fetch detail %s: %s", url[:60], e)
            return ""

    async def _scrape_async(self) -> List[Dict]:
        all_jobs = []
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()

            for query_cfg in self.queries:
                kw = query_cfg["keywords"]
                logger.info("[IamExpat] Searching: %s", kw)
                for page_num in range(1, self.max_pages + 1):
                    url = f"{BASE_URL}?search={kw.replace(' ', '+')}&page={page_num}"
                    try:
                        cards = await self._scrape_listing_page(page, url)
                    except Exception as e:
                        logger.warning("[IamExpat] Listing page %d failed: %s", page_num, e)
                        break
                    if not cards:
                        break
                    for card in cards:
                        desc = await self._scrape_detail_page(page, card["url"])
                        job = self._to_job_dict(
                            title=card["title"], company=card["company"],
                            location=card["location"], url=card["url"],
                            description=desc, query=kw,
                        )
                        all_jobs.append(job)
                    if len(cards) < JOBS_PER_PAGE:
                        break  # Last page

            await browser.close()
        return all_jobs

    def scrape(self) -> List[Dict]:
        return asyncio.run(self._scrape_async())
```

**Step 4: Run test**

Run: `pytest tests/test_scrapers/test_iamexpat.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/scrapers/iamexpat.py tests/test_scrapers/test_iamexpat.py
git commit -m "feat: add IamExpatScraper with Playwright"
```

---

### Task 5: Configuration files

**Files:**
- Create: `config/target_companies.yaml`
- Modify: `config/search_profiles.yaml` (add iamexpat queries)

**Step 1: Create target_companies.yaml**

Start with a small set of known NL tech companies. The user can expand this list later.

```yaml
# config/target_companies.yaml
# Target companies for direct ATS scraping
# ats: greenhouse | lever
# board_token: company identifier in ATS URL
# location_filter: optional, case-insensitive substring match on job location

companies:
  # === Greenhouse ===
  - name: Booking.com
    ats: greenhouse
    board_token: bookingcom
    location_filter: "Amsterdam"

  - name: Adyen
    ats: greenhouse
    board_token: adyen
    location_filter: "Amsterdam"

  - name: MessageBird
    ats: greenhouse
    board_token: messagebird
    location_filter: "Amsterdam"

  - name: Miro
    ats: greenhouse
    board_token: miro
    location_filter: "Amsterdam"

  - name: Databricks
    ats: greenhouse
    board_token: databricks
    location_filter: "Amsterdam"

  # === Lever ===
  - name: Spotify
    ats: lever
    board_token: spotify
    location_filter: "Netherlands"

  - name: Elastic
    ats: lever
    board_token: elastic
    location_filter: "Netherlands"
```

**Step 2: Add IamExpat queries to search_profiles.yaml**

Add `iamexpat` section under each enabled profile. Append after existing `queries`:

```yaml
# Under ml_data profile, add:
    iamexpat:
      queries:
        - keywords: "data engineer"
        - keywords: "machine learning"
        - keywords: "MLOps"

# Under backend_data profile, add:
    iamexpat:
      queries:
        - keywords: "python developer"
        - keywords: "backend engineer"
        - keywords: "software engineer"

# Under quant profile, add:
    iamexpat:
      queries:
        - keywords: "quantitative"
```

**Step 3: Commit**

```bash
git add config/target_companies.yaml config/search_profiles.yaml
git commit -m "feat: add target companies config and IamExpat search queries"
```

---

### Task 6: Orchestrator CLI (multi_scraper.py)

**Files:**
- Create: `scripts/multi_scraper.py`

**Step 1: Implement orchestrator**

```python
# scripts/multi_scraper.py
"""
Multi-Platform Job Scraper — Orchestrator
==========================================
Runs all non-LinkedIn scrapers (Greenhouse, Lever, IamExpat).

Usage:
    python scripts/multi_scraper.py --all
    python scripts/multi_scraper.py --platform ats
    python scripts/multi_scraper.py --platform iamexpat
    python scripts/multi_scraper.py --platform ats --platform iamexpat
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.greenhouse import GreenhouseScraper
from src.scrapers.lever import LeverScraper
from src.scrapers.iamexpat import IamExpatScraper

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("multi_scraper")


def load_target_companies() -> list:
    path = CONFIG_DIR / "target_companies.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("companies", [])


def load_iamexpat_queries(profile: str = None) -> list:
    path = CONFIG_DIR / "search_profiles.yaml"
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    queries = []
    profiles = config.get("profiles", {})
    for name, prof in profiles.items():
        if profile and name != profile:
            continue
        if not prof.get("enabled", True):
            continue
        ie = prof.get("iamexpat", {})
        queries.extend(ie.get("queries", []))
    return queries


def run_ats_scrapers(companies: list) -> dict:
    """Run Greenhouse + Lever scrapers."""
    gh_companies = [c for c in companies if c["ats"] == "greenhouse"]
    lv_companies = [c for c in companies if c["ats"] == "lever"]
    combined = {}

    if gh_companies:
        logger.info("=== Greenhouse: %d companies ===", len(gh_companies))
        gh = GreenhouseScraper(companies=gh_companies)
        combined["greenhouse"] = gh.run()

    if lv_companies:
        logger.info("=== Lever: %d companies ===", len(lv_companies))
        lv = LeverScraper(companies=lv_companies)
        combined["lever"] = lv.run()

    return combined


def run_iamexpat_scraper(queries: list, headless: bool = True) -> dict:
    """Run IamExpat scraper."""
    if not queries:
        logger.info("No IamExpat queries configured, skipping")
        return {}
    logger.info("=== IamExpat: %d queries ===", len(queries))
    ie = IamExpatScraper(queries=queries, headless=headless)
    return {"iamexpat": ie.run()}


def main():
    parser = argparse.ArgumentParser(description="Multi-platform job scraper")
    parser.add_argument("--all", action="store_true", help="Run all scrapers")
    parser.add_argument("--platform", action="append", choices=["ats", "iamexpat"],
                        help="Run specific platform(s)")
    parser.add_argument("--profile", default=None, help="Search profile for IamExpat queries")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run Playwright in headless mode (default)")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="Show browser window")
    args = parser.parse_args()

    platforms = set(args.platform or [])
    if args.all:
        platforms = {"ats", "iamexpat"}
    if not platforms:
        parser.error("Specify --all or --platform")

    results = {}
    companies = load_target_companies()

    if "ats" in platforms:
        results.update(run_ats_scrapers(companies))

    if "iamexpat" in platforms:
        queries = load_iamexpat_queries(args.profile)
        results.update(run_iamexpat_scraper(queries, headless=args.headless))

    # Save metrics (same pattern as LinkedIn scraper)
    total_new = sum(r.get("new", 0) for r in results.values())
    total_found = sum(r.get("found", 0) for r in results.values())
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "platforms": results,
        "total_found": total_found,
        "total_new": total_new,
    }
    metrics_path = DATA_DIR / "multi_scrape_metrics.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("=== Done: found %d, new %d ===", total_found, total_new)


if __name__ == "__main__":
    main()
```

**Step 2: Test CLI help**

Run: `python scripts/multi_scraper.py --help`
Expected: Shows usage with --all, --platform options

**Step 3: Commit**

```bash
git add scripts/multi_scraper.py
git commit -m "feat: add multi-platform scraper orchestrator CLI"
```

---

### Task 7: CI workflow integration

**Files:**
- Modify: `.github/workflows/job-pipeline-optimized.yml`

**Step 1: Add multi-scraper step after LinkedIn scrape**

Insert between "Scrape LinkedIn" and "Rule-based scoring" steps:

```yaml
      # ==========================================
      # Step 1b: 多平台爬取 (ATS API + IamExpat)
      # ==========================================
      - name: Scrape other platforms
        id: multi_scrape
        continue-on-error: true
        run: |
          echo "=== Scraping Greenhouse + Lever + IamExpat ==="
          python scripts/multi_scraper.py --all
```

**Step 2: Update notification step to include multi-scraper failures**

Add to the FAILED_STEPS collection:
```yaml
          [ "${{ steps.multi_scrape.outcome }}" == "failure" ] && FAILED_STEPS="${FAILED_STEPS:+$FAILED_STEPS, }multi-scrape"
```

**Step 3: Commit**

```bash
git add .github/workflows/job-pipeline-optimized.yml
git commit -m "ci: add multi-platform scraping step to pipeline"
```

---

### Task 8: Update package exports and docs

**Files:**
- Modify: `src/scrapers/__init__.py` (add all scrapers)
- Modify: `CLAUDE.md` (add multi-scraper docs)

**Step 1: Update __init__.py**

```python
# src/scrapers/__init__.py
from src.scrapers.base import BaseScraper
from src.scrapers.greenhouse import GreenhouseScraper
from src.scrapers.lever import LeverScraper
from src.scrapers.iamexpat import IamExpatScraper

__all__ = ["BaseScraper", "GreenhouseScraper", "LeverScraper", "IamExpatScraper"]
```

**Step 2: Add multi-scraper section to CLAUDE.md**

Under "核心命令" section, add after LinkedIn scraper:

```markdown
### 1b. 多平台爬取 (Greenhouse + Lever + IamExpat)
\```bash
# 运行所有非 LinkedIn 平台
python scripts/multi_scraper.py --all

# 只运行 ATS (Greenhouse + Lever)
python scripts/multi_scraper.py --platform ats

# 只运行 IamExpat
python scripts/multi_scraper.py --platform iamexpat

# 指定搜索 profile
python scripts/multi_scraper.py --platform iamexpat --profile ml_data
\```

目标公司配置: `config/target_companies.yaml`
IamExpat 搜索词: `config/search_profiles.yaml` 各 profile 下的 `iamexpat.queries`
```

**Step 3: Commit**

```bash
git add src/scrapers/__init__.py CLAUDE.md
git commit -m "docs: update exports and CLAUDE.md for multi-platform scraping"
```

---

### Task 9: End-to-end smoke test (ATS only)

**Step 1: Run ATS scrapers against real APIs**

Run: `python scripts/multi_scraper.py --platform ats`

Expected:
- Greenhouse and Lever APIs respond successfully
- Jobs are inserted into DB
- `data/multi_scrape_metrics.json` is created with stats
- No errors in output

**Step 2: Verify DB has new jobs**

Run: `python -c "from src.db.job_db import JobDatabase; db=JobDatabase(); print(db.execute(\"SELECT source, COUNT(*) as n FROM jobs WHERE source IN ('Greenhouse','Lever') GROUP BY source\"))"`

Expected: Shows counts for Greenhouse and Lever sources

**Step 3: Run pipeline on new jobs**

Run: `python scripts/job_pipeline.py --process`

Expected: New jobs from Greenhouse/Lever flow through filter → score pipeline normally

**Step 4: Final commit with any fixes**

```bash
git add -A
git commit -m "test: verify multi-platform scraping end-to-end"
```
