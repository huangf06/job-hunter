import importlib
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import yaml


def load_linkedin_module():
    return importlib.import_module("src.scrapers.linkedin")


def write_search_profiles(tmp_path: Path) -> Path:
    config_path = tmp_path / "linkedin_test_profiles.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "defaults": {"location": "Netherlands", "max_jobs": 25},
                "profiles": {
                    "data_engineering": {
                        "enabled": True,
                        "queries": [
                            {"keywords": '"Data Engineer"', "description": "primary"},
                            {"keywords": '"MLOps Engineer"', "description": "platform"},
                        ],
                    },
                    "ml_engineering": {
                        "enabled": True,
                        "queries": [
                            {"keywords": '"ML Engineer"', "description": "ml"},
                        ],
                    },
                    "ml_data": {
                        "enabled": False,
                        "queries": [{"keywords": '"Machine Learning"'}],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    return config_path


class FakeLinkedInBrowser:
    def __init__(
        self,
        *,
        session_error=None,
        search_results_by_query: dict | None = None,
        description_payloads_by_url: dict | None = None,
        failures_by_query: dict | None = None,
    ):
        self.session_error = session_error
        self.search_results_by_query = search_results_by_query or {}
        self.description_payloads_by_url = description_payloads_by_url or {}
        self.failures_by_query = failures_by_query or {}
        self.diagnostics = {}
        self.enter = AsyncMock()
        self.exit = AsyncMock(return_value=False)

    async def __aenter__(self):
        await self.enter()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.exit(exc_type, exc, tb)
        return False

    async def validate_session(self) -> bool:
        if self.session_error:
            raise self.session_error
        return True

    async def search_jobs(self, keywords: str, **kwargs) -> list[dict]:
        failure = self.failures_by_query.get(keywords)
        if failure:
            raise failure
        return list(self.search_results_by_query.get(keywords, []))

    async def fetch_job_description(self, url: str) -> dict:
        return dict(self.description_payloads_by_url.get(url, {}))


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_orchestrator_uses_active_profile_queries_and_maps_query_failure_to_target_failure(mock_db_cls, mock_bl):
    """Inventory from v6: one profile fans out into multiple queries; a single query failure should be target-level, not fatal."""
    linkedin = load_linkedin_module()
    config_path = write_search_profiles(Path(__file__).resolve().parent)
    try:
        db = MagicMock()
        db.find_existing_job_ids.return_value = set()
        mock_db_cls.return_value = db

        browser = FakeLinkedInBrowser(
            search_results_by_query={
                '"Data Engineer"': [
                    {
                        "title": "Data Engineer",
                        "company": "Acme",
                        "location": "Amsterdam",
                        "url": "https://www.linkedin.com/jobs/view/123",
                    }
                ]
            },
            failures_by_query={'"MLOps Engineer"': RuntimeError("search failed")},
            description_payloads_by_url={
                "https://www.linkedin.com/jobs/view/123": {
                    "detail_text": "Build ML systems at scale.",
                }
            },
        )

        scraper = linkedin.LinkedInScraper(profile="data_engineering", browser=browser, config_path=config_path)
        report = scraper.run(dry_run=True)

        assert report.found == 1
        assert report.targets_attempted == 2
        assert report.targets_succeeded == 1
        assert report.targets_failed == 1
        assert report.severity == "warning"
        assert report.target_errors == [{"target": '"MLOps Engineer"', "error": "search failed"}]
        inserted_job = db.insert_job.call_args_list
        assert inserted_job == []
    finally:
        config_path.unlink(missing_ok=True)


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_orchestrator_maps_session_and_captcha_to_scraper_errors(mock_db_cls, mock_bl):
    """Inventory from v6: invalid cookies/session and CAPTCHA are scraper-level failures and should stop cleanly."""
    linkedin = load_linkedin_module()
    config_path = write_search_profiles(Path(__file__).resolve().parent)
    try:
        mock_db_cls.return_value = MagicMock()

        browser = FakeLinkedInBrowser(session_error=linkedin.LinkedInCaptchaError("captcha detected"))
        scraper = linkedin.LinkedInScraper(profile="data_engineering", browser=browser, config_path=config_path)
        report = scraper.run(dry_run=True)

        assert report.found == 0
        assert report.targets_attempted == 0
        assert report.targets_failed == 0
        assert report.severity == "error"
        assert report.errors == ["captcha detected"]
        assert report.diagnostics["session_status"] == "challenge"
        assert report.diagnostics["last_stage"] == "validate_session"
        assert report.diagnostics["queries"] == []
    finally:
        config_path.unlink(missing_ok=True)


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_orchestrator_fetches_descriptions_and_uses_browser_lifecycle(mock_db_cls, mock_bl):
    linkedin = load_linkedin_module()
    config_path = write_search_profiles(Path(__file__).resolve().parent)
    try:
        db = MagicMock()
        db.find_existing_job_ids.return_value = set()
        mock_db_cls.return_value = db

        browser = FakeLinkedInBrowser(
            search_results_by_query={
                '"Data Engineer"': [
                    {
                        "title": "Data Engineer",
                        "company": "Acme",
                        "location": "Amsterdam",
                        "url": "https://www.linkedin.com/jobs/view/123",
                    }
                ],
                '"MLOps Engineer"': [],
            },
            description_payloads_by_url={
                "https://www.linkedin.com/jobs/view/123": {
                    "json_ld_description": "<p>Own the data platform.</p>",
                }
            },
        )

        scraper = linkedin.LinkedInScraper(profile="data_engineering", browser=browser, config_path=config_path)
        jobs = scraper.scrape()

        assert len(jobs) == 1
        assert jobs[0]["description"] == "Own the data platform."
        assert jobs[0]["search_profile"] == "data_engineering"
        assert jobs[0]["search_query"] == '"Data Engineer"'
        browser.enter.assert_awaited_once()
        browser.exit.assert_awaited_once()
    finally:
        config_path.unlink(missing_ok=True)


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_orchestrator_uses_all_active_profiles_when_profile_not_specified(mock_db_cls, mock_bl):
    linkedin = load_linkedin_module()
    config_path = write_search_profiles(Path(__file__).resolve().parent)
    try:
        mock_db_cls.return_value = MagicMock(job_exists=MagicMock(return_value=False))

        browser = FakeLinkedInBrowser(
            search_results_by_query={
                '"Data Engineer"': [],
                '"MLOps Engineer"': [],
                '"ML Engineer"': [],
            }
        )

        scraper = linkedin.LinkedInScraper(profile=None, browser=browser, config_path=config_path)
        jobs = scraper.scrape()

        assert jobs == []
        assert browser.enter.await_count == 1
    finally:
        config_path.unlink(missing_ok=True)


@patch("src.scrapers.base.load_blacklists", return_value={"company": [], "title": []})
@patch("src.scrapers.base.JobDatabase")
def test_orchestrator_emits_structured_linkedin_diagnostics(mock_db_cls, mock_bl):
    linkedin = load_linkedin_module()
    config_path = write_search_profiles(Path(__file__).resolve().parent)
    try:
        mock_db_cls.return_value = MagicMock(find_existing_job_ids=MagicMock(return_value=set()))

        browser = FakeLinkedInBrowser(
            search_results_by_query={
                '"Data Engineer"': [
                    {
                        "title": "Data Engineer",
                        "company": "Acme",
                        "location": "Amsterdam",
                        "url": "https://www.linkedin.com/jobs/view/123",
                    }
                ],
                '"MLOps Engineer"': [],
            },
            description_payloads_by_url={
                "https://www.linkedin.com/jobs/view/123": {
                    "detail_text": "Build ML systems at scale.",
                }
            },
        )
        browser.diagnostics = {
            "session_status": "ok",
            "last_stage": "detail_fetch",
            "last_url": "https://www.linkedin.com/jobs/view/123",
            "challenge_marker": "",
            "cards_found": 1,
            "detail_fetch_failures": 0,
        }

        scraper = linkedin.LinkedInScraper(profile="data_engineering", browser=browser, config_path=config_path)
        report = scraper.run(dry_run=True)

        assert report.diagnostics["session_status"] == "ok"
        assert report.diagnostics["profile_scope"] == ["data_engineering"]
        assert report.diagnostics["query_count"] == 2
        assert report.diagnostics["query_successes"] == 2
        assert report.diagnostics["query_failures"] == 0
        assert report.diagnostics["queries"] == [
            {
                "profile": "data_engineering",
                "query": '"Data Engineer"',
                "status": "ok",
                "cards_found": 1,
                "jobs_enriched": 1,
                "last_stage": "detail_fetch",
                "last_url": "https://www.linkedin.com/jobs/view/123",
                "error": "",
            },
            {
                "profile": "data_engineering",
                "query": '"MLOps Engineer"',
                "status": "ok",
                "cards_found": 0,
                "jobs_enriched": 0,
                "last_stage": "detail_fetch",
                "last_url": "https://www.linkedin.com/jobs/view/123",
                "error": "",
            },
        ]
    finally:
        config_path.unlink(missing_ok=True)
