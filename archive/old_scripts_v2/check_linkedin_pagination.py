"""
LinkedIn 职位数量检查
=====================

检查 LinkedIn 搜索结果的实际职位数量
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path("job-hunter/config/linkedin_cookies.json")

async def check_job_count():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1920, "height": 1080})
        
        # 加载 cookies
        if COOKIES_FILE.exists():
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
        
        page = await context.new_page()
        
        # 访问搜索结果页
        url = "https://www.linkedin.com/jobs/search?keywords=data%20engineer&location=Netherlands&f_TPR=r86400&f_WT=2%2C3&sortBy=DD"
        print(f"访问: {url}")
        await page.goto(url, wait_until="networkidle")
        await asyncio.sleep(5)
        
        # 检查页面上的职位数量显示
        print("\n检查页面信息...")
        
        # 尝试找到显示总数量的元素
        count_selectors = [
            "[data-test-id='jobs-search-results-count']",
            ".jobs-search-results__title",
            "[class*='results-count']",
            "[class*='search-results__title']"
        ]
        
        for selector in count_selectors:
            try:
                el = await page.query_selector(selector)
                if el:
                    text = await el.inner_text()
                    print(f"  找到数量信息: {text}")
            except:
                pass
        
        # 统计实际加载的职位卡片
        cards = await page.query_selector_all(".jobs-search-results__list-item")
        print(f"\n当前页面职位卡片数: {len(cards)}")
        
        # 滚动几次看是否有变化
        print("\n滚动测试...")
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 1000)")
            await asyncio.sleep(2)
            cards = await page.query_selector_all(".jobs-search-results__list-item")
            print(f"  滚动 {i+1} 后: {len(cards)} 个卡片")
        
        # 检查是否有 "Show more" 按钮
        print("\n检查翻页按钮...")
        button_selectors = [
            "button:has-text('Show more')",
            "button:has-text('See more jobs')",
            "button:has-text('Load more')",
            ".jobs-search-results__pagination-button"
        ]
        
        for selector in button_selectors:
            try:
                button = await page.query_selector(selector)
                if button:
                    text = await button.inner_text()
                    visible = await button.is_visible()
                    print(f"  找到按钮: '{text}' (可见: {visible})")
            except:
                pass
        
        print("\n按回车关闭浏览器...")
        input()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(check_job_count())
