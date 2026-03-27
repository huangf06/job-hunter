import asyncio
import copy
from datetime import datetime
from pathlib import Path

import yaml

from src.scrapers.base import BaseScraper
from src.scrapers.linkedin_browser import (
    LinkedInBrowser,
    LinkedInBrowserError,
    LinkedInBrowserStub,
    LinkedInCaptchaError,
    LinkedInSessionError,
)
from src.scrapers.linkedin_parser import extract_job_description, parse_search_cards


class LinkedInScraper(BaseScraper):
    source_name = "LinkedIn"

    def __init__(
        self,
        profile: str | None,
        browser=None,
        config_path: Path | None = None,
    ):
        super().__init__()
        self.profile = profile
        self.browser = browser or LinkedInBrowser()
        self.config_path = (
            Path(config_path)
            if config_path
            else Path(__file__).resolve().parents[2] / "config" / "search_profiles.yaml"
        )
        self.config = self._load_config()

    def _load_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _get_profile(self) -> dict:
        profiles = self.config.get("profiles", {})
        profile = profiles.get(self.profile)
        if not profile or not profile.get("enabled", True):
            raise ValueError(f"Unknown or inactive LinkedIn profile: {self.profile}")
        return profile

    def _iter_active_profiles(self) -> list[tuple[str, dict]]:
        profiles = self.config.get("profiles", {})
        if self.profile:
            return [(self.profile, self._get_profile())]
        return [
            (name, profile)
            for name, profile in profiles.items()
            if profile and profile.get("enabled", True)
        ]

    async def _scrape_async(self) -> list[dict]:
        defaults = self.config.get("defaults", {})
        jobs: list[dict] = []
        query_diagnostics: list[dict] = []
        profile_scope = [name for name, _ in self._iter_active_profiles()]

        async with self.browser as browser:
            try:
                await browser.validate_session()
            except (LinkedInSessionError, LinkedInCaptchaError, LinkedInBrowserError) as exc:
                self.record_error(exc)
                browser_diag = dict(getattr(browser, "diagnostics", {}))
                browser_diag["last_stage"] = "validate_session"
                if isinstance(exc, LinkedInCaptchaError):
                    browser_diag["session_status"] = "challenge"
                elif isinstance(exc, LinkedInSessionError):
                    browser_diag.setdefault("session_status", "auth_redirect")
                self.update_diagnostics(
                    profile_scope=profile_scope,
                    query_count=0,
                    query_successes=0,
                    query_failures=0,
                    queries=[],
                    **browser_diag,
                )
                return []

            for profile_name, profile in self._iter_active_profiles():
                for query in profile.get("queries", []):
                    keywords = query.get("keywords", "")
                    if not keywords:
                        continue
                    try:
                        cards = await browser.search_jobs(
                            keywords,
                            location=defaults.get("location", "Netherlands"),
                            max_jobs=int(defaults.get("max_jobs", 25)),
                            date_posted=defaults.get("date_posted", "r86400"),
                            sort_by=defaults.get("sort_by", "DD"),
                            job_type=defaults.get("job_type"),
                            workplace_type=defaults.get("workplace_type"),
                        )
                        parsed_jobs = parse_search_cards(cards)
                        jobs_enriched = 0
                        for job in parsed_jobs:
                            payload = await browser.fetch_job_description(job["url"])
                            description = extract_job_description(payload)
                            if description:
                                job["description"] = description
                                jobs_enriched += 1
                            job["scraped_at"] = datetime.now().isoformat()
                            job["search_profile"] = profile_name
                            job["search_query"] = keywords
                        jobs.extend(parsed_jobs)
                        browser_diag = copy.deepcopy(getattr(browser, "diagnostics", {}))
                        query_diagnostics.append(
                            {
                                "profile": profile_name,
                                "query": keywords,
                                "status": "ok",
                                "cards_found": len(cards),
                                "jobs_enriched": jobs_enriched,
                                "last_stage": browser_diag.get("last_stage", ""),
                                "last_url": browser_diag.get("last_url", ""),
                                "error": "",
                            }
                        )
                        self.record_target_success(keywords)
                    except Exception as exc:
                        browser_diag = copy.deepcopy(getattr(browser, "diagnostics", {}))
                        query_diagnostics.append(
                            {
                                "profile": profile_name,
                                "query": keywords,
                                "status": "error",
                                "cards_found": browser_diag.get("cards_found", 0),
                                "jobs_enriched": 0,
                                "last_stage": browser_diag.get("last_stage", ""),
                                "last_url": browser_diag.get("last_url", ""),
                                "error": str(exc),
                            }
                        )
                        self.record_target_failure(keywords, exc)
            browser_diag = dict(getattr(browser, "diagnostics", {}))
            self.update_diagnostics(
                profile_scope=profile_scope,
                query_count=len(query_diagnostics),
                query_successes=sum(1 for item in query_diagnostics if item["status"] == "ok"),
                query_failures=sum(1 for item in query_diagnostics if item["status"] == "error"),
                queries=query_diagnostics,
                **browser_diag,
            )
        return jobs

    def scrape(self) -> list[dict]:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(asyncio.run, self._scrape_async()).result()
        return asyncio.run(self._scrape_async())


__all__ = [
    "LinkedInBrowser",
    "LinkedInBrowserStub",
    "LinkedInBrowserError",
    "LinkedInSessionError",
    "LinkedInCaptchaError",
    "LinkedInScraper",
]
