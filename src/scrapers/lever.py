import logging
from datetime import datetime
from typing import List, Dict, Optional

import requests

from src.scrapers.base import BaseScraper

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
