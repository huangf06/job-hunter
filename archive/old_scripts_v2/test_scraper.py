"""
爬虫诊断测试脚本
================

测试 Playwright 是否能正确抓取 LinkedIn 和 IamExpat
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


async def test_linkedin():
    """测试 LinkedIn 抓取"""
    print("=" * 60)
    print("Testing LinkedIn Scraper")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            url = "https://www.linkedin.com/jobs/search?keywords=data%20scientist&location=Netherlands"
            print(f"Navigating to: {url}")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(8)  # 等待动态内容加载
            
            # 保存页面内容用于分析
            html_content = await page.content()
            debug_file = Path(__file__).parent.parent / "data" / "linkedin_debug.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Page saved to: {debug_file}")
            
            # 尝试多种选择器
            selectors = [
                "[data-job-id]",
                ".jobs-search__results-list li",
                ".job-card-container",
                ".base-card",
                "[class*='job-card']",
                "[class*='job-search-card']",
                ".jobs-search-results__list-item"
            ]
            
            print("\nTesting selectors:")
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  {selector}: {len(elements)} elements found")
                    
                    if elements:
                        # 尝试提取第一个元素的信息
                        first = elements[0]
                        text = await first.inner_text()
                        print(f"    First element text (first 100 chars): {text[:100]}...")
                        
                        # 尝试提取标题
                        title_el = await first.query_selector("h3, h2, .job-card-list__title, [class*='title']")
                        if title_el:
                            title = await title_el.inner_text()
                            print(f"    Title found: {title}")
                        
                        break  # 找到有效选择器就停止
                        
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # 截图
            screenshot_file = Path(__file__).parent.parent / "data" / "linkedin_screenshot.png"
            await page.screenshot(path=str(screenshot_file), full_page=True)
            print(f"\nScreenshot saved to: {screenshot_file}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await browser.close()


async def test_iamexpat():
    """测试 IamExpat 抓取"""
    print("\n" + "=" * 60)
    print("Testing IamExpat Scraper")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        try:
            url = "https://www.iamexpat.nl/career/jobs-netherlands/data-scientist"
            print(f"Navigating to: {url}")
            
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(5)
            
            # 保存页面内容
            html_content = await page.content()
            debug_file = Path(__file__).parent.parent / "data" / "iamexpat_debug.html"
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            print(f"Page saved to: {debug_file}")
            
            # 尝试多种选择器
            selectors = [
                ".job-item",
                ".views-row",
                "[class*='job']",
                ".node-job",
                ".job-listing"
            ]
            
            print("\nTesting selectors:")
            for selector in selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    print(f"  {selector}: {len(elements)} elements found")
                    
                    if elements:
                        first = elements[0]
                        text = await first.inner_text()
                        print(f"    First element text (first 100 chars): {text[:100]}...")
                        break
                        
                except Exception as e:
                    print(f"  {selector}: Error - {e}")
            
            # 截图
            screenshot_file = Path(__file__).parent.parent / "data" / "iamexpat_screenshot.png"
            await page.screenshot(path=str(screenshot_file), full_page=True)
            print(f"\nScreenshot saved to: {screenshot_file}")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await browser.close()


async def main():
    await test_linkedin()
    await test_iamexpat()
    print("\n" + "=" * 60)
    print("Testing completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
