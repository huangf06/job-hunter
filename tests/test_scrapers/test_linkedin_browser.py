import asyncio

import pytest

from src.scrapers.linkedin_browser import LinkedInBrowser, LinkedInCaptchaError


class FakePage:
    def __init__(self, *, url: str, content: str, body_text: str = ""):
        self.url = url
        self._content = content
        self._body_text = body_text

    async def content(self):
        return self._content

    async def inner_text(self, selector: str):
        if selector != "body":
            raise ValueError(selector)
        return self._body_text


def test_challenge_detection_ignores_grecaptcha_script_references():
    browser = LinkedInBrowser()
    browser.page = FakePage(
        url="https://www.linkedin.com/feed/",
        content='<script>window.cfg={"key":"_grecaptcha"}</script>',
        body_text="Welcome back",
    )

    asyncio.run(browser._raise_if_challenge_page())


def test_challenge_detection_raises_on_visible_security_check_text():
    browser = LinkedInBrowser()
    browser.page = FakePage(
        url="https://www.linkedin.com/checkpoint/challenge/",
        content="<html><body>Security check</body></html>",
        body_text="Security check: verify you are human",
    )

    with pytest.raises(LinkedInCaptchaError):
        asyncio.run(browser._raise_if_challenge_page())

    assert browser.diagnostics["session_status"] == "challenge"
    assert browser.diagnostics["last_stage"] == "challenge_check"
    assert browser.diagnostics["last_url"] == "https://www.linkedin.com/checkpoint/challenge/"
    assert browser.diagnostics["challenge_marker"] == "url:/checkpoint/challenge"
