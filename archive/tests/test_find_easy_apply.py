#!/usr/bin/env python3
"""
测试自动投递 - 查找并测试 Easy Apply 职位
"""

import sys
sys.path.insert(0, 'C:\\Users\\huang\\.openclaw\\workspace\\job-hunter')

from playwright.sync_api import sync_playwright
from pathlib import Path

# 测试多个职位，查找 Easy Apply
job_urls = [
    "https://www.linkedin.com/jobs/view/4368611599",  # Otrium
    "https://www.linkedin.com/jobs/view/4366831902",  # GeekSoft
    "https://www.linkedin.com/jobs/view/4368227221",  # JDE Peet's
    "https://www.linkedin.com/jobs/view/4368653147",  # Decentralized Masters
]

print("=" * 60)
print("TESTING: Find Easy Apply jobs")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context(viewport={'width': 1280, 'height': 900})
    page = context.new_page()
    
    # 先登录
    print("\n[LOGIN] Checking login status...")
    page.goto("https://www.linkedin.com/feed", timeout=10000)
    page.wait_for_timeout(2000)
    
    if "login" in page.url:
        print("[LOGIN] Please log in manually...")
        page.wait_for_timeout(30000)  # 等待30秒登录
    else:
        print("[LOGIN] Already logged in")
    
    # 测试每个职位
    for i, url in enumerate(job_urls, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{len(job_urls)}] Testing: {url}")
        print('='*60)
        
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(3000)
            
            # 获取职位信息
            title_elem = page.locator('h1, .jobs-unified-top-card__job-title').first
            title = title_elem.inner_text() if title_elem.is_visible() else "Unknown"
            
            company_elem = page.locator('.jobs-unified-top-card__company-name, a[href*="/company/"]').first
            company = company_elem.inner_text() if company_elem.is_visible() else "Unknown"
            
            print(f"Title: {title}")
            print(f"Company: {company}")
            
            # 检查 Easy Apply 按钮
            easy_apply_selectors = [
                'button[data-control-name="jobdetails_topcard_inapply"]',
                '.jobs-apply-button',
                'button:has-text("Easy Apply")',
            ]
            
            has_easy_apply = False
            for selector in easy_apply_selectors:
                try:
                    btn = page.locator(selector).first
                    if btn.is_visible(timeout=2000):
                        print(f"[OK] Easy Apply button found: {selector}")
                        has_easy_apply = True
                        
                        # 尝试点击
                        print("[ACTION] Clicking Easy Apply...")
                        btn.click()
                        page.wait_for_timeout(3000)
                        
                        # 检查是否打开申请表单
                        if page.locator('input[type="email"]').first.is_visible(timeout=2000):
                            print("[OK] Application form opened!")
                            # 不实际提交，只测试到这里
                            page.wait_for_timeout(5000)
                        break
                except:
                    continue
            
            if not has_easy_apply:
                print("[INFO] No Easy Apply button - external application")
                
                # 检查外部 Apply 按钮
                external_btn = page.locator('button:has-text("Apply"), a:has-text("Apply")').first
                if external_btn.is_visible(timeout=2000):
                    print("[INFO] External Apply button found")
                    
        except Exception as e:
            print(f"[ERROR] {e}")
    
    browser.close()

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
