"""
快速测试爬虫 - 使用更简单的页面
"""

import asyncio
from playwright.async_api import async_playwright


async def test_simple():
    """简单测试"""
    print("Testing basic Playwright functionality...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        # 测试一个简单的页面
        await page.goto("https://httpbin.org/get", timeout=30000)
        content = await page.content()
        print(f"Page loaded successfully, length: {len(content)}")
        
        await browser.close()
        print("Basic test passed!")


async def test_iamexpat_simple():
    """测试 IamExpat - 使用简单方法"""
    print("\nTesting IamExpat...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # 直接访问主页
            url = "https://www.iamexpat.nl/career/jobs-netherlands"
            print(f"Loading: {url}")
            
            await page.goto(url, wait_until="load", timeout=60000)
            await asyncio.sleep(3)
            
            # 获取页面标题
            title = await page.title()
            print(f"Page title: {title}")
            
            # 查找任何包含 "job" 的元素
            elements = await page.query_selector_all("*")
            print(f"Total elements: {len(elements)}")
            
            # 尝试找到职位列表
            job_elements = await page.query_selector_all("a")
            print(f"Links found: {len(job_elements)}")
            
            # 打印前5个链接的文本
            for i, el in enumerate(job_elements[:5]):
                text = await el.inner_text()
                href = await el.get_attribute("href")
                if text and len(text.strip()) > 3:
                    print(f"  Link {i}: {text[:50]}... -> {href[:50] if href else 'N/A'}...")
            
        except Exception as e:
            print(f"Error: {e}")
        
        finally:
            await browser.close()


async def main():
    await test_simple()
    await test_iamexpat_simple()


if __name__ == "__main__":
    asyncio.run(main())
