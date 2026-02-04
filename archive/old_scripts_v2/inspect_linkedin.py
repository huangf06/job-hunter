"""
LinkedIn 页面结构检查工具
==========================

用于检查 LinkedIn Jobs 页面的元素选择器
"""

import asyncio
from playwright.async_api import async_playwright

async def inspect_linkedin():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        print("请手动登录 LinkedIn，然后按回车继续...")
        await page.goto("https://www.linkedin.com/login")
        
        # 等待用户登录
        input("登录完成后请按回车...")
        
        # 检查当前页面
        print(f"\n当前URL: {page.url}")
        
        # 进入 Jobs 页面
        print("\n正在进入 Jobs 页面...")
        await page.goto("https://www.linkedin.com/jobs/")
        await asyncio.sleep(3)
        
        print(f"Jobs 页面 URL: {page.url}")
        
        # 检查搜索框
        print("\n=== 搜索框元素 ===")
        search_selectors = [
            "input[aria-label*='Search']",
            "input[placeholder*='Search']",
            ".jobs-search-box__text-input",
            "[data-test-id='jobs-search-keywords-input']",
            "input[type='text']",
        ]
        
        for selector in search_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    print(f"  [FOUND] {selector}")
                    placeholder = await el.get_attribute("placeholder")
                    aria_label = await el.get_attribute("aria-label")
                    print(f"    placeholder: {placeholder}")
                    print(f"    aria-label: {aria_label}")
            except:
                pass
        
        # 检查筛选按钮
        print("\n=== 筛选按钮 ===")
        filter_keywords = ["Date posted", "Remote", "Experience level", "Salary"]
        for keyword in filter_keywords:
            selectors = [
                f"button:has-text('{keyword}')",
                f"[aria-label*='{keyword}']",
            ]
            for selector in selectors:
                try:
                    el = await page.query_selector(selector)
                    if el:
                        print(f"  [FOUND] {keyword}: {selector}")
                        break
                except:
                    pass
        
        # 检查职位卡片
        print("\n=== 职位卡片 ===")
        card_selectors = [
            "[data-job-id]",
            ".jobs-search-results__list-item",
            ".job-card-container",
            ".scaffold-layout__list-item"
        ]
        for selector in card_selectors:
            try:
                cards = await page.query_selector_all(selector)
                if cards:
                    print(f"  [FOUND] {selector}: {len(cards)} 个")
            except:
                pass
        
        print("\n检查完成，请关闭浏览器...")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(inspect_linkedin())
