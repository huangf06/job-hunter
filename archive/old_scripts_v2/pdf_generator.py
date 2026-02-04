"""
PDF Generator - 从 HTML 生成 PDF 简历
=====================================

使用 Playwright 将 HTML 简历转换为 PDF

使用方法：
    python pdf_generator.py input.html output.pdf
    python pdf_generator.py --test  # 测试生成
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"
OUTPUT_DIR = PROJECT_ROOT / "output"

# 确保目录存在
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


async def html_to_pdf(html_path: str, pdf_path: str, options: dict = None) -> bool:
    """
    将 HTML 文件转换为 PDF
    
    Args:
        html_path: HTML 文件路径
        pdf_path: 输出 PDF 路径
        options: PDF 选项（页面大小、边距等）
    
    Returns:
        bool: 是否成功
    """
    from playwright.async_api import async_playwright
    
    default_options = {
        "format": "A4",
        "margin": {
            "top": "0.4in",
            "right": "0.4in",
            "bottom": "0.4in",
            "left": "0.4in"
        },
        "print_background": True,
        "prefer_css_page_size": True
    }
    
    if options:
        default_options.update(options)
    
    html_path = Path(html_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    
    if not html_path.exists():
        print(f"[ERROR] HTML file not found: {html_path}")
        return False
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # 加载 HTML 文件
            await page.goto(f"file:///{html_path}")
            
            # 等待页面完全加载
            await page.wait_for_load_state("networkidle")
            
            # 生成 PDF
            await page.pdf(
                path=str(pdf_path),
                format=default_options["format"],
                margin=default_options["margin"],
                print_background=default_options["print_background"],
                prefer_css_page_size=default_options["prefer_css_page_size"]
            )
            
            await browser.close()
            
        print(f"[OK] PDF generated: {pdf_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        return False


async def html_string_to_pdf(html_content: str, pdf_path: str, options: dict = None) -> bool:
    """
    将 HTML 字符串转换为 PDF
    
    Args:
        html_content: HTML 内容字符串
        pdf_path: 输出 PDF 路径
        options: PDF 选项
    
    Returns:
        bool: 是否成功
    """
    from playwright.async_api import async_playwright
    
    default_options = {
        "format": "A4",
        "margin": {
            "top": "0.4in",
            "right": "0.4in",
            "bottom": "0.4in",
            "left": "0.4in"
        },
        "print_background": True
    }
    
    if options:
        default_options.update(options)
    
    pdf_path = Path(pdf_path).resolve()
    
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # 设置 HTML 内容
            await page.set_content(html_content, wait_until="networkidle")
            
            # 生成 PDF
            await page.pdf(
                path=str(pdf_path),
                format=default_options["format"],
                margin=default_options["margin"],
                print_background=default_options["print_background"]
            )
            
            await browser.close()
            
        print(f"[OK] PDF generated: {pdf_path}")
        return True
        
    except Exception as e:
        print(f"[ERROR] PDF generation failed: {e}")
        return False


def generate_pdf(html_path: str, pdf_path: str) -> bool:
    """同步版本的 PDF 生成"""
    return asyncio.run(html_to_pdf(html_path, pdf_path))


def generate_pdf_from_string(html_content: str, pdf_path: str) -> bool:
    """同步版本的 HTML 字符串转 PDF"""
    return asyncio.run(html_string_to_pdf(html_content, pdf_path))


async def test_generation():
    """测试 PDF 生成"""
    print("=" * 50)
    print("[TEST] PDF Generation")
    print("=" * 50)
    
    template_path = TEMPLATES_DIR / "resume_base.html"
    output_path = OUTPUT_DIR / "test_resume_generated.pdf"
    
    if not template_path.exists():
        print(f"[ERROR] Template not found: {template_path}")
        return False
    
    print(f"Input:  {template_path}")
    print(f"Output: {output_path}")
    
    success = await html_to_pdf(str(template_path), str(output_path))
    
    if success:
        # 检查文件大小
        size_kb = output_path.stat().st_size / 1024
        print(f"File size: {size_kb:.1f} KB")
    
    return success


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        asyncio.run(test_generation())
    elif len(sys.argv) == 3:
        html_file = sys.argv[1]
        pdf_file = sys.argv[2]
        generate_pdf(html_file, pdf_file)
    else:
        print("用法:")
        print("  python pdf_generator.py input.html output.pdf")
        print("  python pdf_generator.py --test")
