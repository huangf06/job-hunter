import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.greenhouse import GreenhouseScraper, _html_to_text

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
    company = {"name": "Acme", "ats": "lever", "board_token": "acme"}
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


def test_html_to_text():
    html = "<p>Hello &amp; <b>world</b></p><br/><li>item one</li>"
    text = _html_to_text(html)
    assert "Hello & world" in text
    assert "- item one" in text
    assert "<" not in text
