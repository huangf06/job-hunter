"""
分析页面结构
"""

import asyncio
from playwright.async_api import async_playwright


async def analyze_iamexpat():
    """分析 IamExpat 页面结构"""
    print("=" * 60)
    print("Analyzing IamExpat Job Structure")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            url = "https://www.iamexpat.nl/career/jobs-netherlands/data-scientist"
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(3)
            
            # 查找职位列表容器
            containers = [
                ".view-content",
                ".item-list",
                "[class*='job-list']",
                "[class*='listing']",
                "ul",
                ".content"
            ]
            
            for container_sel in containers:
                container = await page.query_selector(container_sel)
                if container:
                    items = await container.query_selector_all(":scope > li, :scope > div, :scope > article")
                    if len(items) > 3:
                        print(f"\nFound container: {container_sel} with {len(items)} items")
                        
                        # 分析第一个职位项
                        first_item = items[0]
                        html = await first_item.inner_html()
                        text = await first_item.inner_text()
                        
                        print(f"\nFirst item text (first 300 chars):")
                        print(text[:300])
                        
                        # 查找标题、公司、地点
                        title_el = await first_item.query_selector("h2, h3, h4, .title, [class*='title']")
                        if title_el:
                            title_text = await title_el.inner_text()
                            print(f"\nTitle found: {title_text}")
                        
                        company_el = await first_item.query_selector(".company, [class*='company'], [class*='organization']")
                        if company_el:
                            company_text = await company_el.inner_text()
                            print(f"Company found: {company_text}")
                        
                        location_el = await first_item.query_selector(".location, [class*='location'], [class*='place']")
                        if location_el:
                            location_text = await location_el.inner_text()
                            print(f"Location found: {location_text}")
                        
                        break
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await browser.close()


async def main():
    await analyze_iamexpat()


if __name__ == "__main__":
    asyncio.run(main())
