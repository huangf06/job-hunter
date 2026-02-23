import pytest
from unittest.mock import patch, MagicMock
from src.scrapers.base import BaseScraper


class DummyScraper(BaseScraper):
    source_name = "Test"
    def scrape(self):
        return []


@patch("src.scrapers.base.JobDatabase")
@patch("src.scrapers.base.load_blacklists", return_value={
    "company": ["hays", "randstad"],
    "title": ["intern", "student"],
})
def test_blacklist_filters(mock_bl, mock_db):
    s = DummyScraper()
    assert s.is_blacklisted({"company": "Hays Netherlands", "title": "Data Engineer"})
    assert s.is_blacklisted({"company": "Google", "title": "ML Intern"})
    assert not s.is_blacklisted({"company": "Booking.com", "title": "Data Engineer"})
