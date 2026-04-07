"""Backfill empty LinkedIn job descriptions using the guest API."""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from playwright.async_api import async_playwright
from src.db.job_db import JobDatabase
from src.scrapers.linkedin_browser import GUEST_DETAIL_SELECTORS
from src.scrapers.linkedin_parser import extract_job_description

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


async def backfill():
    db = JobDatabase()

    rows = db.execute(
        """SELECT j.id, j.url, j.title, j.company
           FROM jobs j
           JOIN filter_results fr ON j.id = fr.job_id
           WHERE j.source = 'LinkedIn'
             AND (j.description = '' OR j.description IS NULL)
             AND fr.reject_reason = 'insufficient_data'
             AND j.created_at >= '2026-04-03'
           ORDER BY j.created_at DESC"""
    )

    if not rows:
        logger.info("No jobs to backfill")
        return

    logger.info("Backfilling %d LinkedIn jobs via guest API", len(rows))

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page(user_agent=USER_AGENT)

    success = 0
    failed = 0

    for row in rows:
        job_id = row["id"]
        url = row["url"]
        import re
        match = re.search(r"/jobs/view/(\d+)", url)
        if not match:
            logger.warning("Cannot extract job ID from URL: %s", url)
            failed += 1
            continue

        guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{match.group(1)}"
        try:
            resp = await page.goto(guest_url, wait_until="domcontentloaded", timeout=15000)
            if not resp or resp.status != 200:
                logger.warning("Guest API returned %s for %s", resp.status if resp else "None", url)
                failed += 1
                continue

            payload = {"json_ld_description": "", "detail_text": "", "detail_html": ""}
            for selector in GUEST_DETAIL_SELECTORS:
                element = await page.query_selector(selector)
                if not element:
                    continue
                payload["detail_text"] = (await element.inner_text()).strip()
                payload["detail_html"] = (await element.inner_html()).strip()
                if payload["detail_text"] or payload["detail_html"]:
                    break

            description = extract_job_description(payload)
            if not description or len(description) < 50:
                logger.warning("No description found for %s (%s)", row["company"], row["title"])
                failed += 1
                continue

            # Update description in DB
            db.execute(
                "UPDATE jobs SET description = ? WHERE id = ?",
                [description, job_id],
            )
            # Delete old filter_result so --filter can re-evaluate
            db.execute(
                "DELETE FROM filter_results WHERE job_id = ?",
                [job_id],
            )
            success += 1
            logger.info(
                "  [%d/%d] %s @ %s — %d chars",
                success + failed, len(rows), row["title"], row["company"], len(description),
            )

            # Rate limit
            await asyncio.sleep(1)

        except Exception as exc:
            logger.warning("Error fetching %s: %s", url, exc)
            failed += 1

    await browser.close()
    await pw.stop()

    logger.info("Backfill complete: %d success, %d failed out of %d", success, failed, len(rows))
    if success > 0:
        logger.info("Run 'python scripts/job_pipeline.py --filter' to re-evaluate backfilled jobs")


if __name__ == "__main__":
    asyncio.run(backfill())
