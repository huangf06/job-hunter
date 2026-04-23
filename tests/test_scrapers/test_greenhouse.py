import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.greenhouse import GreenhouseScraper
from src.scrapers.utils import strip_html

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


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.greenhouse.requests.get")
def test_scrape_with_location_filter(mock_get, mock_bl, mock_db):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
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


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.greenhouse.requests.get")
def test_scrape_no_location_filter(mock_get, mock_bl, mock_db):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_RESPONSE
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    company = {"name": "Acme", "ats": "greenhouse", "board_token": "acme"}
    scraper = GreenhouseScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 2


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.greenhouse.requests.get")
def test_scrape_skips_non_greenhouse(mock_get, mock_bl, mock_db):
    company = {"name": "Acme", "ats": "icims", "board_token": "acme"}
    scraper = GreenhouseScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 0
    mock_get.assert_not_called()


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.greenhouse.requests.get")
def test_scrape_handles_api_error(mock_get, mock_bl, mock_db):
    mock_get.side_effect = Exception("Connection timeout")

    company = {"name": "Acme", "ats": "greenhouse", "board_token": "acme"}
    scraper = GreenhouseScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 0


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
@patch.object(GreenhouseScraper, "_fetch_jobs")
def test_run_tracks_per_board_target_counts_and_partial_failure(mock_fetch_jobs, mock_db_cls, mock_bl):
    db = MagicMock()
    db.job_exists.return_value = False
    mock_db_cls.return_value = db

    mock_fetch_jobs.side_effect = [
        [
            {
                "id": 123,
                "title": "Data Engineer",
                "location": {"name": "Amsterdam"},
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
                "updated_at": "2026-02-20T10:00:00-05:00",
                "content": "<p>Build data pipelines...</p>",
            }
        ],
        Exception("Connection timeout"),
    ]

    scraper = GreenhouseScraper(
        companies=[
            {"name": "Acme", "ats": "greenhouse", "board_token": "acme"},
            {"name": "Beta", "ats": "greenhouse", "board_token": "beta"},
        ]
    )
    report = scraper.run(dry_run=True)

    assert report.targets_attempted == 2
    assert report.targets_succeeded == 1
    assert report.targets_failed == 1
    assert report.severity == "warning"
    assert report.target_errors == [{"target": "Beta", "error": "Connection timeout"}]


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.greenhouse.requests.get")
def test_run_deduplicates_and_persists_new_jobs(mock_get, mock_db_cls, mock_bl):
    db = MagicMock()
    db.job_exists.return_value = False
    db.batch_mode.return_value.__enter__.return_value = db
    db.batch_mode.return_value.__exit__.return_value = False
    db.insert_job.return_value = ("abc123", True)
    mock_db_cls.return_value = db

    duplicate_response = {
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
                "id": 124,
                "title": "Data Engineer II",
                "location": {"name": "Amsterdam"},
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/123",
                "updated_at": "2026-02-20T11:00:00-05:00",
                "content": "<p>Build more data pipelines...</p>",
            },
        ],
        "meta": {"total": 2},
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = duplicate_response
    mock_resp.raise_for_status = MagicMock()
    mock_get.return_value = mock_resp

    scraper = GreenhouseScraper(companies=[{"name": "Acme", "ats": "greenhouse", "board_token": "acme"}])
    report = scraper.run()

    assert report.found == 2
    assert report.would_insert == 1
    assert report.new == 1
    assert report.skipped_duplicates == 1
    db.insert_job.assert_called_once()


def test_html_to_text():
    raw = "<p>Hello &amp; <b>world</b></p><br/><li>item one</li>"
    text = strip_html(raw)
    assert "Hello & world" in text
    assert "- item one" in text
    assert "<" not in text
