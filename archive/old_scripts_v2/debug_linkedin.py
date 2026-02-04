"""
LinkedIn 页面调试工具
=====================

用于检查 LinkedIn Jobs 页面的实际 HTML 结构
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path("job-hunter/config/linkedin_cookies.json")

async def debug_linkedin():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        
        # 加载 cookies
        if COOKIES_FILE.exists():
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 访问 Jobs 页面
        print("访问 LinkedIn Jobs...")
        await page.goto(
            "https://www.linkedin.com/jobs/search?keywords=data+engineer&location=Netherlands&f_TPR=r86400&f_WT=2,3",
            wait_until="networkidle"
        )
        
        await asyncio.sleep(5)
        
        # 获取页面 HTML
        html = await page.content()
        
        # 保存 HTML 用于分析
        with open("linkedin_debug.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("HTML 已保存到 linkedin_debug.html")
        
        # 尝试多种选择器
        selectors = [
            ".jobs-search-results__list-item",
            "li[data-occludable-job-id]",
            ".job-card-container",
            "[data-job-id]",
            ".jobs-search-results__list > li",
            "[class*='job-card']",
            "[class*='search-result']"
        ]
        
        print("\n测试选择器:")
        for selector in selectors:
            elements = await page.query_selector_all(selector)
            print(f"  {selector}: {len(elements)} 个元素")
        
        # 获取第一个职位卡片的 HTML
        first_card = await page.query_selector(".jobs-search-results__list-item")
        if first_card:
            card_html = await first_card.inner_html()
            with open("linkedin_card_debug.html", "w", encoding="utf-8") as f:
                f.write(card_html)
            print("\n第一个职位卡片 HTML 已保存到 linkedin_card_debug.html")
        
        print("\n按回车关闭浏览器...")
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_linkedin())
