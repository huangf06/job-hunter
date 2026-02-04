"""
Test LinkedIn login with cookies
================================
"""

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

COOKIES_FILE = PROJECT_ROOT / "config" / "linkedin_cookies.json"

async def test_login():
    print("Testing LinkedIn login with cookies...")
    print("=" * 70)
    
    if not COOKIES_FILE.exists():
        print("[FAIL] Cookies file not found")
        return False
    
    with open(COOKIES_FILE, 'r') as f:
        cookies = json.load(f)
    
    print(f"Loaded {len(cookies)} cookies")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Add cookies
        await context.add_cookies(cookies)
        print("[OK] Cookies added to browser")
        
        # Test login
        page = await context.new_page()
        print("-> Navigating to LinkedIn feed...")
        
        try:
            await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            url = page.url
            print(f"Current URL: {url}")
            
            if "/feed" in url:
                print("[OK] Login successful - redirected to feed")
                
                # Check for user name
                try:
                    name_elem = await page.query_selector(".profile-rail-card__actor-link")
                    if name_elem:
                        name = await name_elem.inner_text()
                        print(f"[OK] Logged in as: {name}")
                except:
                    pass
                
                await browser.close()
                return True
            else:
                print(f"[FAIL] Not logged in - URL: {url}")
                await browser.close()
                return False
                
        except Exception as e:
            print(f"[FAIL] Error: {e}")
            await browser.close()
            return False

if __name__ == "__main__":
    result = asyncio.run(test_login())
    print("=" * 70)
    if result:
        print("Cookies are valid! Ready for scraping.")
    else:
        print("Cookies expired or invalid. Need to re-login.")
