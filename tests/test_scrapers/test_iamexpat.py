import pytest
from unittest.mock import patch, MagicMock
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
