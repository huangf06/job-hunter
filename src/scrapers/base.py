import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List

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


@dataclass
class ScrapeReport:
    source: str
    found: int = 0
    new: int = 0
    would_insert: int = 0
    skipped_blacklist: int = 0
    skipped_duplicates: int = 0
    targets_attempted: int = 0
    targets_succeeded: int = 0
    targets_failed: int = 0
    errors: List[str] = field(default_factory=list)
    target_errors: List[Dict[str, str]] = field(default_factory=list)
    diagnostics: Dict = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return not self.errors and self.targets_failed == 0

    @property
    def severity(self) -> str:
        if self.errors:
            return "error"
        if self.targets_failed:
            return "warning"
        return "info"

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "found": self.found,
            "new": self.new,
            "would_insert": self.would_insert,
            "skipped_blacklist": self.skipped_blacklist,
            "skipped_duplicates": self.skipped_duplicates,
            "targets_attempted": self.targets_attempted,
            "targets_succeeded": self.targets_succeeded,
            "targets_failed": self.targets_failed,
            "errors": list(self.errors),
            "target_errors": list(self.target_errors),
            "diagnostics": dict(self.diagnostics),
            "is_healthy": self.is_healthy,
            "severity": self.severity,
        }


class BaseScraper(ABC):
    """Abstract base for all job scrapers."""

    source_name: str = "unknown"

    def __init__(self):
        self.db = JobDatabase()
        self.blacklists = load_blacklists()
        self._target_errors: List[Dict[str, str]] = []
        self._run_errors: List[str] = []
        self._target_counts = {"attempted": 0, "succeeded": 0, "failed": 0}
        self._diagnostics: Dict = {}

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """Scrape jobs and return a list of unified job dicts."""

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

    def record_target_success(self, target: str) -> None:
        self._target_counts["attempted"] += 1
        self._target_counts["succeeded"] += 1

    def record_target_failure(self, target: str, error: Exception | str) -> None:
        self._target_counts["attempted"] += 1
        self._target_counts["failed"] += 1
        self._target_errors.append({"target": target, "error": str(error)})

    def record_error(self, error: Exception | str) -> None:
        self._run_errors.append(str(error))

    def _reset_report_state(self) -> None:
        self._target_errors = []
        self._run_errors = []
        self._target_counts = {"attempted": 0, "succeeded": 0, "failed": 0}
        self._diagnostics = {}

    def update_diagnostics(self, **values) -> None:
        self._diagnostics.update(values)

    def _build_report(self, jobs: List[Dict]) -> ScrapeReport:
        counts = self._target_counts.copy()
        if counts["attempted"] == 0:
            if jobs and not self._run_errors:
                logger.warning("[%s] No targets tracked; auto-marking as success (found %d jobs)", self.source_name, len(jobs))
                counts["attempted"] = 1
                counts["succeeded"] = 1
        return ScrapeReport(
            source=self.source_name.lower(),
            found=len(jobs),
            targets_attempted=counts["attempted"],
            targets_succeeded=counts["succeeded"],
            targets_failed=counts["failed"],
            errors=list(self._run_errors),
            target_errors=list(self._target_errors),
            diagnostics=dict(self._diagnostics),
        )

    def _is_known_duplicate(self, job: Dict, seen_job_ids: set[str], existing_job_ids: set[str]) -> bool:
        url = job.get("url", "")
        job_id = JobDatabase.generate_job_id(url)
        if job_id in seen_job_ids:
            return True

        seen_job_ids.add(job_id)
        return job_id in existing_job_ids

    def run(self, dry_run: bool = False) -> ScrapeReport:
        """Scrape, dedup, optionally save, and return a structured report."""
        self._reset_report_state()

        try:
            jobs = list(self.scrape())
        except Exception as exc:
            self.record_error(exc)
            jobs = []

        report = self._build_report(jobs)
        seen_job_ids: set[str] = set()
        existing_job_ids = self.db.find_existing_job_ids([job.get("url", "") for job in jobs])
        jobs_to_insert: List[Dict] = []

        for job in jobs:
            if self.is_blacklisted(job):
                report.skipped_blacklist += 1
                continue

            if not job.get("url", ""):
                self.record_error("Skipping job without URL")
                continue

            if self._is_known_duplicate(job, seen_job_ids, existing_job_ids):
                report.skipped_duplicates += 1
                continue

            report.would_insert += 1
            if dry_run:
                continue
            jobs_to_insert.append(job)

        report.errors = list(self._run_errors)

        if dry_run:
            report.new = report.would_insert
            return report

        if jobs_to_insert:
            with self.db.batch_mode():
                for job in jobs_to_insert:
                    self.db.insert_job(job)
            report.new = len(jobs_to_insert)

        logger.info(
            "[%s] found=%d new=%d would_insert=%d blacklist=%d duplicates=%d severity=%s",
            self.source_name,
            report.found,
            report.new,
            report.would_insert,
            report.skipped_blacklist,
            report.skipped_duplicates,
            report.severity,
        )
        return report
