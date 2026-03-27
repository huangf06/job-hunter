import importlib
import inspect
from unittest.mock import MagicMock, patch

import pytest

from src.scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    source_name = "dummy"

    def __init__(self, jobs=None):
        super().__init__()
        self._jobs = jobs or []

    def scrape(self):
        return list(self._jobs)


def load_base_module():
    return importlib.import_module("src.scrapers.base")


@patch(
    "src.scrapers.base.load_blacklists",
    return_value={"company": ["hays", "randstad"], "title": ["intern", "student"]},
)
@patch("src.scrapers.base.JobDatabase")
def test_blacklist_filters(mock_db_cls, mock_blacklists):
    scraper = DummyScraper()

    assert scraper.is_blacklisted({"company": "Hays Netherlands", "title": "Data Engineer"})
    assert scraper.is_blacklisted({"company": "Google", "title": "ML Intern"})
    assert not scraper.is_blacklisted({"company": "Booking.com", "title": "Data Engineer"})


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_scrape_contract_is_synchronous(mock_db_cls, mock_blacklists):
    scraper = DummyScraper()

    assert inspect.iscoroutinefunction(scraper.scrape) is False


def test_scrape_report_health_and_severity():
    base = load_base_module()

    healthy = base.ScrapeReport(source="greenhouse")
    warning = base.ScrapeReport(
        source="greenhouse", targets_attempted=2, targets_succeeded=1, targets_failed=1
    )
    broken = base.ScrapeReport(source="greenhouse", errors=["session expired"])

    assert healthy.is_healthy is True
    assert healthy.severity == "info"
    assert warning.is_healthy is False
    assert warning.severity == "warning"
    assert broken.is_healthy is False
    assert broken.severity == "error"


def test_scrape_report_exposes_target_counters():
    base = load_base_module()
    report = base.ScrapeReport(
        source="iamexpat",
        targets_attempted=3,
        targets_succeeded=2,
        targets_failed=1,
    )

    assert report.targets_attempted == 3
    assert report.targets_succeeded == 2
    assert report.targets_failed == 1


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_run_uses_would_insert_for_new_when_dry_run(mock_db_cls, mock_blacklists):
    db = MagicMock()
    db.job_exists.return_value = False
    mock_db_cls.return_value = db

    scraper = DummyScraper(
        jobs=[
            {
                "title": "Data Engineer",
                "company": "Acme",
                "url": "https://example.com/jobs/123",
                "source": "Dummy",
            }
        ]
    )

    report = scraper.run(dry_run=True)

    assert report.found == 1
    assert report.would_insert == 1
    assert report.new == 1
    db.insert_job.assert_not_called()


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_run_prefetches_existing_job_ids_for_duplicate_checks(mock_db_cls, mock_blacklists):
    url_existing = "https://example.com/jobs/existing"
    url_new = "https://example.com/jobs/new"
    db = MagicMock()
    db.generate_job_id.side_effect = lambda url: f"id:{url.rsplit('/', 1)[-1]}"
    db.find_existing_job_ids.return_value = {"id:existing"}
    mock_db_cls.generate_job_id.side_effect = lambda url: f"id:{url.rsplit('/', 1)[-1]}"
    mock_db_cls.return_value = db

    scraper = DummyScraper(
        jobs=[
            {"title": "Existing", "company": "Acme", "url": url_existing, "source": "Dummy"},
            {"title": "New", "company": "Acme", "url": url_new, "source": "Dummy"},
        ]
    )

    report = scraper.run(dry_run=True)

    assert report.found == 2
    assert report.skipped_duplicates == 1
    assert report.would_insert == 1
    assert report.new == 1
    db.find_existing_job_ids.assert_called_once_with([url_existing, url_new])
    db.job_exists.assert_not_called()
