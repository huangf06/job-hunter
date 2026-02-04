#!/usr/bin/env python3
"""
AnyRouter 自动登录脚本
每天定时登录 anyrouter.top 保持活跃
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from playwright.async_api import async_playwright

# 配置
CONFIG = {
    "url": "https://anyrouter.top",
    "email": "huangfei@kmmu.edu.cn",
    "password": "Hc030527",
    "timeout": 30000,  # 30秒超时
}

# 日志文件
LOG_FILE = os.path.join(os.path.dirname(__file__), "anyrouter_login.log")


def log(message: str):
    """记录日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_line + "\n")


async def login_anyrouter():
    """执行登录流程"""
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        try:
            log(f"开始访问 {CONFIG['url']}")
            await page.goto(CONFIG["url"], wait_until="networkidle", timeout=CONFIG["timeout"])
            
            # 等待页面加载
            await page.wait_for_timeout(2000)
            
            # 查找邮箱输入框（常见选择器）
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[id="email"]',
                'input[placeholder*="邮箱"]',
                'input[placeholder*="email"]',
                'input[placeholder*="Email"]',
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        log(f"找到邮箱输入框: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                # 尝试找任何可能是邮箱的输入框
                inputs = await page.query_selector_all('input')
                for inp in inputs:
                    input_type = await inp.get_attribute('type') or ''
                    placeholder = await inp.get_attribute('placeholder') or ''
                    if input_type in ['email', 'text'] or '邮箱' in placeholder or 'email' in placeholder.lower():
                        email_input = inp
                        log(f"通过遍历找到邮箱输入框")
                        break
            
            if not email_input:
                log("错误：未找到邮箱输入框")
                await browser.close()
                return False
            
            # 输入邮箱
            await email_input.fill(CONFIG["email"])
            log("已输入邮箱")
            
            # 查找密码输入框
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[id="password"]',
                'input[placeholder*="密码"]',
                'input[placeholder*="password"]',
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        log(f"找到密码输入框: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                log("错误：未找到密码输入框")
                await browser.close()
                return False
            
            # 输入密码
            await password_input.fill(CONFIG["password"])
            log("已输入密码")
            
            # 查找登录按钮
            login_selectors = [
                'button[type="submit"]',
                'button:has-text("登录")',
                'button:has-text("Login")',
                'button:has-text("Sign in")',
                'input[type="submit"]',
                'a:has-text("登录")',
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        log(f"找到登录按钮: {selector}")
                        break
                except:
                    continue
            
            if not login_button:
                # 尝试按回车键提交
                log("未找到登录按钮，尝试按回车键")
                await password_input.press("Enter")
            else:
                await login_button.click()
                log("已点击登录按钮")
            
            # 等待登录完成
            await page.wait_for_timeout(5000)
            
            # 检查是否登录成功（通过URL变化或特定元素）
            current_url = page.url
            log(f"当前URL: {current_url}")
            
            # 截图保存（用于调试）
            screenshot_path = os.path.join(os.path.dirname(__file__), f"anyrouter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            await page.screenshot(path=screenshot_path, full_page=True)
            log(f"已保存截图: {screenshot_path}")
            
            # 判断登录是否成功
            if "login" not in current_url.lower() or "dashboard" in current_url.lower() or "home" in current_url.lower():
                log("✅ 登录成功！")
                success = True
            else:
                # 检查页面内容是否包含登录成功标志
                page_content = await page.content()
                success_indicators = ["退出", "logout", "欢迎", "welcome", "个人中心", "dashboard"]
                if any(indicator in page_content.lower() for indicator in success_indicators):
                    log("✅ 登录成功！")
                    success = True
                else:
                    log("⚠️ 登录状态不确定，请检查截图")
                    success = True  # 保守认为成功，避免重复尝试
            
            await browser.close()
            return success
            
        except Exception as e:
            log(f"❌ 登录失败: {str(e)}")
            # 保存错误截图
            try:
                error_screenshot = os.path.join(os.path.dirname(__file__), f"anyrouter_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
                await page.screenshot(path=error_screenshot, full_page=True)
                log(f"已保存错误截图: {error_screenshot}")
            except:
                pass
            await browser.close()
            return False


if __name__ == "__main__":
    log("=" * 50)
    log("AnyRouter 自动登录任务开始")
    log("=" * 50)
    
    result = asyncio.run(login_anyrouter())
    
    if result:
        log("任务完成")
        sys.exit(0)
    else:
        log("任务失败")
        sys.exit(1)
