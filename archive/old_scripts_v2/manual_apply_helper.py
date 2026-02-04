"""
手动申请助手
打开浏览器让用户手动完成申请
"""

import asyncio
from playwright.async_api import async_playwright

async def open_job_for_manual_apply():
    """打开职位页面供手动申请"""
    
    jobs = [
        {
            "title": "Intern Data Scientist",
            "company": "Rabobank",
            "url": "https://nl.linkedin.com/jobs/view/intern-data-scientist-at-rabobank"
        },
        {
            "title": "Machine Learning Engineer", 
            "company": "ABN AMRO Bank",
            "url": "https://nl.linkedin.com/jobs/view/machine-learning-engineer-at-abn-amro"
        },
        {
            "title": "Data Scientist",
            "company": "BCG X",
            "url": "https://nl.linkedin.com/jobs/view/data-scientist-netherlands-bcg-x"
        }
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        page = await context.new_page()
        
        print("=" * 60)
        print("Manual Apply Helper")
        print("=" * 60)
        print("\nOpening jobs for manual application...")
        print("Please complete the application in the browser window.\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"[{i}] {job['title']} @ {job['company']}")
            print(f"    URL: {job['url']}\n")
            
            # 在新标签页打开
            if i == 1:
                await page.goto(job['url'], timeout=60000)
            else:
                new_page = await context.new_page()
                await new_page.goto(job['url'], timeout=60000)
        
        print("=" * 60)
        print("Browser opened. Please complete applications manually.")
        print("Press Ctrl+C to close when done.")
        print("=" * 60)
        
        # 保持浏览器打开
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            pass
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(open_job_for_manual_apply())
