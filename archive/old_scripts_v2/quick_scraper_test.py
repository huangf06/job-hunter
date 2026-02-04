"""
Quick test of the scraper with actual crawling
===============================================
"""

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.linkedin_scraper_v6 import SearchConfig
from src.db.job_db import JobDatabase

COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

async def quick_test():
    print("Quick Scraper Test")
    print("=" * 70)
    
    # Load config
    config = SearchConfig()
    profile = config.get_profile('ml_data')
    
    print(f"Profile: {profile['name']}")
    query = profile['queries'][0]
    keywords = query['keywords']
    print(f"Keywords: {keywords[:60]}...")
    
    # Build URL
    from urllib.parse import urlencode
    params = {
        "keywords": keywords,
        "location": "Netherlands",
        "f_TPR": "r604800",
        "f_WT": "2,3",
        "sortBy": "DD"
    }
    url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
    print(f"URL: {url[:80]}...")
    
    # Load cookies
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    
    print("\nStarting browser...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        await context.add_cookies(cookies)
        page = await context.new_page()
        
        print("-> Navigating to search page...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        print(f"Current URL: {page.url}")
        
        # Try to find job cards
        selectors = [
            ".jobs-search-results__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
        ]
        
        for selector in selectors:
            cards = await page.query_selector_all(selector)
            if cards:
                print(f"[OK] Found {len(cards)} job cards with selector: {selector}")
                
                # Parse first card
                if cards:
                    card = cards[0]
                    title_elem = await card.query_selector(".job-card-list__title strong, .job-card-list__title")
                    if title_elem:
                        title = await title_elem.inner_text()
                        print(f"\nFirst job: {title[:50]}")
                
                break
        else:
            print("[FAIL] No job cards found")
            content = await page.content()
            print(f"Page content length: {len(content)}")
        
        await browser.close()
    
    print("\n" + "=" * 70)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(quick_test())
