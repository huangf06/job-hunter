"""
调试申请按钮 - 查看LinkedIn页面结构
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

async def debug_linkedin_job():
    """调试LinkedIn职位页面"""
    
    job_url = "https://nl.linkedin.com/jobs/view/intern-data-scientist-at-rabobank"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("Opening LinkedIn job page...")
        await page.goto(job_url, timeout=60000)
        await asyncio.sleep(5)
        
        # 保存截图
        screenshot_path = DATA_DIR / "debug_linkedin_job.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
        
        # 查找所有按钮
        print("\nAll buttons on page:")
        buttons = await page.query_selector_all("button")
        for i, btn in enumerate(buttons[:10]):
            try:
                text = await btn.inner_text()
                aria = await btn.get_attribute("aria-label")
                data_control = await btn.get_attribute("data-control-name")
                print(f"  [{i}] Text: '{text[:50]}' | aria: '{aria}' | data-control: '{data_control}'")
            except:
                pass
        
        # 查找所有链接
        print("\nAll links containing 'apply':")
        links = await page.query_selector_all("a")
        for i, link in enumerate(links):
            try:
                text = await link.inner_text()
                href = await link.get_attribute("href")
                if "apply" in text.lower() or (href and "apply" in href.lower()):
                    print(f"  [{i}] Text: '{text[:50]}' | href: '{href[:80]}'")
            except:
                pass
        
        # 查找特定的申请区域
        print("\nApply section elements:")
        apply_sections = [
            "[data-test-id='job-details-apply-button']",
            ".jobs-details-top-card__apply-button",
            ".jobs-apply-button--top-card",
            "[data-control-name='jobdetails_topcard']",
        ]
        
        for selector in apply_sections:
            el = await page.query_selector(selector)
            if el:
                print(f"  Found: {selector}")
                html = await el.inner_html()
                print(f"    HTML: {html[:200]}")
        
        print("\nPress Ctrl+C to close...")
        await asyncio.sleep(30)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_linkedin_job())
