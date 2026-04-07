import json
import logging
import re
from pathlib import Path
from urllib.parse import urlencode

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

COOKIES_FILE = Path(__file__).resolve().parents[2] / "config" / "linkedin_cookies.json"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
AUTH_MARKERS = ("/login", "/checkpoint", "/authwall", "/uas/")
CAPTCHA_MARKERS = ("captcha", "challenge", "verify you are human", "security check")
CHALLENGE_URL_MARKERS = ("/checkpoint/challenge", "/challenge/", "/captcha")
VISIBLE_CHALLENGE_MARKERS = (
    "verify you are human",
    "security check",
    "let's do a quick security check",
    "complete a quick captcha",
    "complete the security check",
)
SEARCH_CARD_SELECTORS = (
    ".jobs-search-results__list-item",
    "li[data-occludable-job-id]",
    ".job-card-container",
    ".scaffold-layout__list-item",
    "[data-job-id]",
)
DETAIL_SELECTORS = (
    ".jobs-description__content",
    ".jobs-box__html-content",
    ".jobs-description-content__text",
    "#job-details",
    ".show-more-less-html__markup",
    "article[class*='jobs-description']",
    ".jobs-description",
    "[class*='description']",
    ".job-view-layout",
)
GUEST_DETAIL_SELECTORS = (
    ".show-more-less-html__markup",
    ".description__text--rich",
    ".description__text",
    ".decorated-job-posting__details",
)


class LinkedInBrowserError(Exception):
    """Base browser-layer error for LinkedIn scraping."""


class LinkedInSessionError(LinkedInBrowserError):
    """Raised when cookies/session are invalid."""


class LinkedInCaptchaError(LinkedInBrowserError):
    """Raised when a CAPTCHA or challenge page is detected."""


class LinkedInBrowser:
    def __init__(
        self,
        *,
        headless: bool = True,
        cookies_path: Path | None = None,
        use_cdp: bool = False,
        cdp_url: str = "http://localhost:9222",
    ):
        self.headless = headless
        self.cookies_path = Path(cookies_path) if cookies_path else COOKIES_FILE
        self.use_cdp = use_cdp
        self.cdp_url = cdp_url
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.diagnostics = {
            "session_status": "unknown",
            "last_stage": "init",
            "last_url": "",
            "challenge_marker": "",
            "cards_found": 0,
            "detail_fetch_failures": 0,
            "cookies_path": str(self.cookies_path),
            "cookies_loaded": 0,
        }

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        if self.use_cdp:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.cdp_url)
            self.context = self.browser.contexts[0] if self.browser.contexts else await self.browser.new_context(
                user_agent=USER_AGENT
            )
        else:
            self.browser = await self.playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(user_agent=USER_AGENT)

        await self._load_cookies()
        self.page = await self.context.new_page()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if self.browser:
                await self.browser.close()
        except Exception:
            pass
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass
        return False

    async def _load_cookies(self) -> None:
        self.diagnostics["last_stage"] = "load_cookies"
        if not self.cookies_path.exists():
            self.diagnostics["session_status"] = "cookies_missing"
            raise LinkedInSessionError(f"LinkedIn cookies file not found: {self.cookies_path}")

        with open(self.cookies_path, "r", encoding="utf-8") as f:
            raw_cookies = json.load(f)

        valid_cookies = []
        for cookie in raw_cookies if isinstance(raw_cookies, list) else []:
            if not isinstance(cookie, dict):
                continue
            if all(cookie.get(key) for key in ("name", "value", "domain")):
                valid_cookies.append(cookie)

        if not valid_cookies:
            self.diagnostics["session_status"] = "cookies_malformed"
            raise LinkedInSessionError("LinkedIn cookies file is empty or malformed")

        if not any(cookie.get("name") == "li_at" for cookie in valid_cookies):
            self.diagnostics["session_status"] = "cookies_missing_li_at"
            raise LinkedInSessionError("LinkedIn session cookie li_at is missing")

        await self.context.add_cookies(valid_cookies)
        self.diagnostics["session_status"] = "cookies_loaded"
        self.diagnostics["cookies_loaded"] = len(valid_cookies)

    async def validate_session(self) -> bool:
        self.diagnostics["last_stage"] = "validate_session"
        await self._goto("https://www.linkedin.com/feed/", timeout=30000)
        if self._is_auth_url(self.page.url):
            self.diagnostics["session_status"] = "auth_redirect"
            raise LinkedInSessionError(f"LinkedIn session expired: redirected to {self.page.url}")
        self.diagnostics["session_status"] = "ok"
        await self._raise_if_challenge_page()
        return True

    async def search_jobs(
        self,
        keywords: str,
        *,
        location: str,
        max_jobs: int,
        date_posted: str = "r86400",
        sort_by: str = "DD",
        job_type: str | None = None,
        workplace_type: str | None = None,
        language: str | None = None,
    ) -> list[dict]:
        self.diagnostics["last_stage"] = "search"
        params = {
            "keywords": keywords,
            "location": location,
            "f_TPR": date_posted,
            "sortBy": sort_by,
        }
        if job_type:
            params["f_JT"] = job_type
        if workplace_type:
            params["f_WT"] = workplace_type
        if language:
            params["f_JC"] = language

        await self._goto(f"https://www.linkedin.com/jobs/search?{urlencode(params)}", timeout=45000)
        await self._wait_for_cards()
        cards = await self._extract_cards()
        self.diagnostics["cards_found"] = len(cards)
        return cards[:max_jobs] if max_jobs > 0 else cards

    async def fetch_job_description(self, url: str) -> dict:
        self.diagnostics["last_stage"] = "detail_fetch"
        await self._goto(url, timeout=30000)

        # Wait for SPA to render JD content (LinkedIn loads async in logged-in view)
        for selector in DETAIL_SELECTORS[:5]:
            try:
                await self.page.wait_for_selector(selector, timeout=2000)
                break
            except Exception:
                continue
        else:
            # No selector appeared after waits — give a final grace period
            await self.page.wait_for_timeout(3000)

        # Try expanding truncated JD via "Show more" button
        for btn_selector in (
            "button[aria-label*='Show more']",
            "button[aria-label*='See more']",
            ".jobs-description__footer-button",
            "button.show-more-less-html__button",
        ):
            try:
                btn = await self.page.query_selector(btn_selector)
                if btn:
                    await btn.click()
                    await self.page.wait_for_timeout(500)
                    break
            except Exception:
                continue

        payload = {
            "json_ld_description": await self._extract_json_ld_description(),
            "detail_text": "",
            "detail_html": "",
        }

        for selector in DETAIL_SELECTORS:
            try:
                element = await self.page.query_selector(selector)
                if not element:
                    continue
                payload["detail_text"] = (await element.inner_text()).strip()
                payload["detail_html"] = (await element.inner_html()).strip()
                if payload["detail_text"] or payload["detail_html"]:
                    return payload
            except Exception:
                continue

        # Logged-in selectors failed — try guest API fallback
        guest_payload = await self._fetch_guest_description(url)
        if guest_payload.get("detail_text") or guest_payload.get("detail_html"):
            logger.info("[LinkedIn] Guest API fallback succeeded for %s", url)
            return guest_payload

        self.diagnostics["detail_fetch_failures"] += 1
        logger.warning("[LinkedIn] All selectors failed for %s", url)
        return payload

    async def _fetch_guest_description(self, url: str) -> dict:
        """Fallback: fetch JD from LinkedIn's public guest API (no auth needed)."""
        payload = {"json_ld_description": "", "detail_text": "", "detail_html": ""}
        # Extract job ID from URL like /jobs/view/4398351834/
        match = re.search(r"/jobs/view/(\d+)", url)
        if not match:
            return payload
        job_id = match.group(1)
        guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        try:
            resp = await self.page.goto(guest_url, wait_until="domcontentloaded", timeout=15000)
            if not resp or resp.status != 200:
                return payload
            for selector in GUEST_DETAIL_SELECTORS:
                element = await self.page.query_selector(selector)
                if not element:
                    continue
                payload["detail_text"] = (await element.inner_text()).strip()
                payload["detail_html"] = (await element.inner_html()).strip()
                if payload["detail_text"] or payload["detail_html"]:
                    return payload
        except Exception as exc:
            logger.debug("[LinkedIn] Guest API fallback error: %s", exc)
        return payload

    async def _goto(self, url: str, *, timeout: int) -> None:
        self.diagnostics["last_url"] = url
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
        except PlaywrightTimeout as exc:
            self.diagnostics["last_stage"] = "navigation_timeout"
            raise LinkedInBrowserError(f"Timed out loading LinkedIn page: {url}") from exc

        self.diagnostics["last_url"] = self.page.url
        if self._is_auth_url(self.page.url):
            self.diagnostics["session_status"] = "auth_redirect"
            raise LinkedInSessionError(f"LinkedIn redirected to auth page: {self.page.url}")
        await self._raise_if_challenge_page()

    async def _raise_if_challenge_page(self) -> None:
        self.diagnostics["last_stage"] = "challenge_check"
        self.diagnostics["last_url"] = self.page.url or self.diagnostics.get("last_url", "")
        url = (self.page.url or "").lower()
        if any(marker in url for marker in CHALLENGE_URL_MARKERS):
            matched_marker = next(marker for marker in CHALLENGE_URL_MARKERS if marker in url)
            self.diagnostics["session_status"] = "challenge"
            self.diagnostics["challenge_marker"] = f"url:{matched_marker}"
            logger.warning("[LinkedIn] Challenge URL detected: url=%s", self.page.url)
            raise LinkedInCaptchaError("LinkedIn CAPTCHA or challenge page detected")

        try:
            body_text = (await self.page.inner_text("body")).lower()
        except Exception:
            body_text = ""

        for marker in VISIBLE_CHALLENGE_MARKERS:
            index = body_text.find(marker)
            if index >= 0:
                self.diagnostics["session_status"] = "challenge"
                self.diagnostics["challenge_marker"] = f"text:{marker}"
                snippet_start = max(0, index - 160)
                snippet_end = min(len(body_text), index + 160)
                snippet = body_text[snippet_start:snippet_end].replace("\n", " ")
                logger.warning(
                    "[LinkedIn] Visible challenge marker detected: marker=%s url=%s snippet=%s",
                    marker,
                    self.page.url,
                    snippet,
                )
                raise LinkedInCaptchaError("LinkedIn CAPTCHA or challenge page detected")

    def _is_auth_url(self, url: str) -> bool:
        return any(marker in url for marker in AUTH_MARKERS)

    async def _wait_for_cards(self) -> None:
        for selector in SEARCH_CARD_SELECTORS:
            try:
                await self.page.wait_for_selector(selector, timeout=5000)
                return
            except Exception:
                continue

    async def _extract_cards(self) -> list[dict]:
        script = """
        (selectors) => {
            const items = [];
            for (const selector of selectors) {
                const cards = Array.from(document.querySelectorAll(selector));
                if (!cards.length) {
                    continue;
                }
                for (const card of cards) {
                    const titleEl = card.querySelector('.job-card-list__title strong, .job-card-list__title, h3 strong, a[class*="title"]');
                    const companyEl = card.querySelector('.job-card-container__company-name, .artdeco-entity-lockup__subtitle, .job-card-container__company-link, .job-card-container__primary-description');
                    const locationEl = card.querySelector('.job-card-container__metadata-item, .artdeco-entity-lockup__caption');
                    const linkEl = card.querySelector('a[href*="/jobs/view/"]') || card.querySelector('a.job-card-list__title') || card.querySelector('a');
                    const href = linkEl ? (linkEl.getAttribute('href') || '') : '';
                    items.push({
                        title: titleEl ? (titleEl.textContent || '').trim() : '',
                        company: companyEl ? (companyEl.textContent || '').trim() : '',
                        location: locationEl ? (locationEl.textContent || '').trim() : '',
                        url: href,
                    });
                }
                if (items.length) {
                    break;
                }
            }
            return items;
        }
        """
        cards = await self.page.evaluate(script, list(SEARCH_CARD_SELECTORS))
        normalized = []
        for card in cards or []:
            href = (card.get("url") or "").split("?")[0]
            if href and not href.startswith("http"):
                href = f"https://www.linkedin.com{href}"
            normalized.append(
                {
                    "title": card.get("title", ""),
                    "company": card.get("company", ""),
                    "location": card.get("location", ""),
                    "url": href,
                }
            )
        return normalized

    async def _extract_json_ld_description(self) -> str:
        try:
            script = await self.page.query_selector('script[type="application/ld+json"]')
            if not script:
                return ""
            data = json.loads(await script.inner_text())
            if isinstance(data, dict):
                return str(data.get("description", "") or "")
        except Exception:
            return ""
        return ""


class LinkedInBrowserStub:
    """Async browser double for orchestration tests."""

    def __init__(
        self,
        session_valid: bool = True,
        captcha_detected: bool = False,
        search_results_by_query: dict | None = None,
        failures_by_query: dict | None = None,
        description_payloads_by_url: dict | None = None,
    ):
        self.session_valid = session_valid
        self.captcha_detected = captcha_detected
        self.search_results_by_query = search_results_by_query or {}
        self.failures_by_query = failures_by_query or {}
        self.description_payloads_by_url = description_payloads_by_url or {}
        self.diagnostics = {
            "session_status": "ok" if session_valid and not captcha_detected else "unknown",
            "last_stage": "stub",
            "last_url": "",
            "challenge_marker": "",
            "cards_found": 0,
            "detail_fetch_failures": 0,
            "cookies_path": "stub",
            "cookies_loaded": 0,
        }

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def validate_session(self) -> bool:
        if self.captcha_detected:
            self.diagnostics["session_status"] = "challenge"
            self.diagnostics["last_stage"] = "validate_session"
            raise LinkedInCaptchaError("LinkedIn CAPTCHA or challenge page detected")
        if not self.session_valid:
            self.diagnostics["session_status"] = "auth_redirect"
            self.diagnostics["last_stage"] = "validate_session"
            raise LinkedInSessionError("LinkedIn session expired (stub)")
        self.diagnostics["session_status"] = "ok"
        self.diagnostics["last_stage"] = "validate_session"
        return True

    async def search_jobs(self, keywords: str, **kwargs) -> list[dict]:
        self.diagnostics["last_stage"] = "search"
        failure = self.failures_by_query.get(keywords)
        if failure:
            raise failure
        results = list(self.search_results_by_query.get(keywords, []))
        self.diagnostics["cards_found"] = len(results)
        return results

    async def fetch_job_description(self, url: str) -> dict:
        self.diagnostics["last_stage"] = "detail_fetch"
        self.diagnostics["last_url"] = url
        return dict(self.description_payloads_by_url.get(url, {}))
