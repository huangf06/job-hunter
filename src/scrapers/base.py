import logging
import sys
from abc import ABC, abstractmethod
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

    source_name: str = "unknown"

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
