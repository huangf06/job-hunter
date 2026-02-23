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


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
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


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.lever.requests.get")
def test_scrape_lever_location_filter(mock_get, mock_bl, mock_db):
    resp = MagicMock()
    resp.json.return_value = MOCK_PAGE_1
    resp.raise_for_status = MagicMock()
    resp_empty = MagicMock()
    resp_empty.json.return_value = []
    resp_empty.raise_for_status = MagicMock()
    mock_get.side_effect = [resp, resp_empty]

    company = {"name": "Acme", "ats": "lever", "board_token": "acme", "location_filter": "Berlin"}
    scraper = LeverScraper(companies=[company])
    jobs = scraper.scrape()

    assert len(jobs) == 0  # Amsterdam doesn't match Berlin filter
