"""
LinkedIn 职位抓取助手 - 半自动化
==================================

步骤：
1. 自动打开 LinkedIn Jobs 页面
2. 等待你运行 JavaScript 代码
3. 读取结果并保存

Usage:
    python linkedin_helper.py
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright

COOKIES_FILE = Path("job-hunter/config/linkedin_cookies.json")
DATA_DIR = Path("job-hunter/data")
DATA_DIR.mkdir(parents=True, exist_ok=True)


async def open_linkedin():
    """打开 LinkedIn Jobs 页面"""
    print("="*70)
    print("LinkedIn 职位抓取助手")
    print("="*70)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        
        # 加载 cookies
        if COOKIES_FILE.exists():
            with open(COOKIES_FILE, 'r') as f:
                cookies = json.load(f)
            await context.add_cookies(cookies)
            print("✓ 已加载登录状态")
        else:
            print("! 未找到登录状态，可能需要手动登录")
        
        page = await context.new_page()
        
        # 访问 LinkedIn Jobs
        url = "https://www.linkedin.com/jobs/search?keywords=data%20engineer&location=Netherlands&f_TPR=r86400&f_WT=2%2C3"
        print(f"\n正在打开: {url}")
        await page.goto(url, wait_until="domcontentloaded")
        
        print("\n" + "="*70)
        print("请按以下步骤操作:")
        print("="*70)
        print("1. 确保页面已完全加载")
        print("2. 向下滚动几次，触发懒加载")
        print("3. 按 F12 打开开发者工具")
        print("4. 切换到 Console 标签")
        print("5. 粘贴并运行你的 JavaScript 代码")
        print("6. 复制抓取结果")
        print("="*70)
        
        input("\n完成后请按回车关闭浏览器...")
        
        await browser.close()
        print("\n✓ 浏览器已关闭")


if __name__ == "__main__":
    asyncio.run(open_linkedin())
