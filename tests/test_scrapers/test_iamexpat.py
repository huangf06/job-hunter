import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.scrapers.iamexpat import IamExpatScraper


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
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
    assert job["search_profile"] == "iamexpat"
    assert job["url"].startswith("https://")
    assert job["company"] == "Booking.com"


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_scrape_query_joins_listing_cards_with_detail_content(mock_db_cls, mock_bl):
    db = MagicMock()
    db.job_exists.return_value = False
    mock_db_cls.return_value = db
    scraper = IamExpatScraper(queries=[{"keywords": "data engineer"}])
    page = MagicMock()
    detail_page = MagicMock()
    detail_page.close = AsyncMock()
    context = MagicMock()
    context.new_page = AsyncMock(return_value=detail_page)

    with patch.object(
        scraper,
        "_scrape_listing_page",
        AsyncMock(
            return_value=[
                {
                    "title": "Data Engineer",
                    "company": "Acme",
                    "location": "Amsterdam",
                    "url": "https://www.iamexpat.nl/career/jobs-netherlands/it/data-engineer/abc123",
                }
            ]
        ),
    ), patch.object(
        scraper,
        "_scrape_detail_page",
        AsyncMock(return_value="Build pipelines and ML systems."),
    ):
        jobs = asyncio.run(scraper._scrape_query(context, page, {"keywords": "data engineer"}))

    assert len(jobs) == 1
    assert jobs[0]["description"] == "Build pipelines and ML systems."
    assert jobs[0]["search_query"] == "data engineer"
    context.new_page.assert_awaited_once()
    detail_page.close.assert_awaited_once()


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_run_tracks_query_target_counts_and_timeout_failures(mock_db_cls, mock_bl):
    db = MagicMock()
    db.job_exists.return_value = False
    mock_db_cls.return_value = db

    scraper = IamExpatScraper(
        queries=[
            {"keywords": "data engineer"},
            {"keywords": "ml engineer"},
        ]
    )
    fake_page = MagicMock()
    fake_context = MagicMock()
    fake_context.new_page = AsyncMock(return_value=fake_page)
    fake_browser = MagicMock()
    fake_browser.new_context = AsyncMock(return_value=fake_context)
    fake_browser.close = AsyncMock()
    fake_playwright = MagicMock()
    fake_playwright.chromium.launch = AsyncMock(return_value=fake_browser)
    fake_playwright_cm = MagicMock()
    fake_playwright_cm.__aenter__ = AsyncMock(return_value=fake_playwright)
    fake_playwright_cm.__aexit__ = AsyncMock(return_value=False)

    with patch.object(
        scraper,
        "_scrape_query",
        AsyncMock(
            side_effect=[
                [
                    {
                        "title": "Data Engineer",
                        "company": "Acme",
                        "location": "Amsterdam",
                        "url": "https://www.iamexpat.nl/career/jobs-netherlands/it/data-engineer/abc123",
                        "description": "Build pipelines",
                        "source": "IamExpat",
                        "scraped_at": "2026-03-27T10:00:00",
                        "search_profile": "iamexpat",
                        "search_query": "data engineer",
                    }
                ],
                TimeoutError("listing timeout"),
            ]
        ),
    ), patch("src.scrapers.iamexpat.async_playwright", return_value=fake_playwright_cm):
        report = scraper.run(dry_run=True)

    assert report.targets_attempted == 2
    assert report.targets_succeeded == 1
    assert report.targets_failed == 1
    assert report.severity == "warning"
    assert report.target_errors == [{"target": "ml engineer", "error": "listing timeout"}]


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_scrape_listing_page_returns_empty_quickly_when_no_cards_appear(mock_db_cls, mock_bl):
    mock_db_cls.return_value = MagicMock()
    scraper = IamExpatScraper(queries=[{"keywords": "data engineer"}])
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.wait_for_selector = AsyncMock(side_effect=TimeoutError("no cards"))

    jobs = asyncio.run(scraper._scrape_listing_page(page, "https://example.com"))

    assert jobs == []
    page.wait_for_timeout.assert_awaited_once_with(1000)
    page.wait_for_selector.assert_awaited_once_with("a[href*='/career/jobs-netherlands/']", timeout=4000)


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_scrape_query_skips_detail_fetch_for_known_duplicates(mock_db_cls, mock_bl):
    db = MagicMock()
    db.find_existing_job_ids.return_value = {"dup-job-id"}
    db.generate_job_id.return_value = "dup-job-id"
    mock_db_cls.return_value = db
    scraper = IamExpatScraper(queries=[{"keywords": "data engineer"}])
    page = MagicMock()
    context = MagicMock()
    context.new_page = AsyncMock()

    with patch.object(
        scraper,
        "_scrape_listing_page",
        AsyncMock(
            return_value=[
                {
                    "title": "Data Engineer",
                    "company": "Acme",
                    "location": "Amsterdam",
                    "url": "https://www.iamexpat.nl/career/jobs-netherlands/it/data-engineer/abc123",
                }
            ]
        ),
    ), patch.object(
        scraper,
        "_scrape_detail_page",
        AsyncMock(return_value="should not be used"),
    ) as mock_detail:
        jobs = asyncio.run(scraper._scrape_query(context, page, {"keywords": "data engineer"}))

    assert len(jobs) == 1
    assert jobs[0]["description"] == ""
    db.find_existing_job_ids.assert_called_once_with(
        ["https://www.iamexpat.nl/career/jobs-netherlands/it/data-engineer/abc123"]
    )
    db.job_exists.assert_not_called()
    mock_detail.assert_not_awaited()
