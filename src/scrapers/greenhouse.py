import logging
import re
from datetime import datetime
from typing import List, Dict, Optional

import requests

from src.scrapers.base import BaseScraper

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
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=30)
                resp.raise_for_status()
                return resp.json().get("jobs", [])
            except (requests.ConnectionError, requests.Timeout) as e:
                if attempt < 2:
                    import time
                    time.sleep(2 ** (attempt + 1))
                else:
                    raise

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
                matched = 0
                for raw in raw_jobs:
                    if self._matches_location(raw, loc_filter):
                        all_jobs.append(self._to_job_dict(raw, name))
                        matched += 1
                self.record_target_success(name)
                logger.info("[Greenhouse] %s: %d jobs (filtered from %d)", name, matched, len(raw_jobs))
            except Exception as e:
                self.record_target_failure(name, e)
                logger.error("[Greenhouse] %s failed: %s", name, e)
        return all_jobs
