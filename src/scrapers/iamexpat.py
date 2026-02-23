import asyncio
import json
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
        """Extract job cards from a listing page."""
        await page.goto(url, wait_until="networkidle", timeout=30000)
        try:
            await page.wait_for_selector("a[href*='/career/jobs-netherlands/']", timeout=10000)
        except Exception:
            return []

        cards = await page.query_selector_all("a[href*='/career/jobs-netherlands/']")
        results = []
        seen_urls = set()
        for card in cards:
            href = await card.get_attribute("href")
            if not href or "/career/jobs-netherlands/" not in href:
                continue
            parts = href.rstrip("/").split("/")
            if len(parts) < 6:
                continue
            full_url = f"https://www.iamexpat.nl{href}" if href.startswith("/") else href
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)

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
            ld_el = await page.query_selector('script[type="application/ld+json"]')
            if ld_el:
                ld_text = await ld_el.inner_text()
                ld = json.loads(ld_text)
                desc = ld.get("description", "")
                if desc:
                    return desc
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
                        break

            await browser.close()
        return all_jobs

    def scrape(self) -> List[Dict]:
        return asyncio.run(self._scrape_async())
