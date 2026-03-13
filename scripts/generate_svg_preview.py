#!/usr/bin/env python3
"""
SVG Resume Preview Generator
生成 SVG 简历的预览图，用于迭代设计
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def generate_preview(svg_path: Path, output_path: Path):
    """生成 SVG 预览图"""
    # 读取 SVG 内容
    svg_content = svg_path.read_text(encoding='utf-8')

    # 创建 HTML 包装
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ margin: 0; padding: 0; }}
        </style>
    </head>
    <body>
        {svg_content}
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 794, 'height': 1123})

        # 直接设置 HTML 内容
        page.set_content(html_content, wait_until='domcontentloaded')

        # 等待渲染
        page.wait_for_timeout(500)

        # 截图
        page.screenshot(path=str(output_path), full_page=True)

        browser.close()
        print(f"Preview generated: {output_path}")

if __name__ == "__main__":
    svg_file = PROJECT_ROOT / "templates" / "Fei_Huang_DE_Resume.svg"
    preview_file = PROJECT_ROOT / "templates" / "Fei_Huang_DE_Resume_preview.png"

    generate_preview(svg_file, preview_file)
