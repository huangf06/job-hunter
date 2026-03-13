#!/usr/bin/env python3
"""
SVG Resume to PDF Converter
将 SVG 简历转换为 PDF
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def svg_to_pdf(svg_path: Path, pdf_path: Path):
    """将 SVG 转换为 PDF"""
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
            @page {{ size: A4; margin: 0; }}
        </style>
    </head>
    <body>
        {svg_content}
    </body>
    </html>
    """

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # 设置 HTML 内容
        page.set_content(html_content, wait_until='domcontentloaded')

        # 等待渲染
        page.wait_for_timeout(500)

        # 生成 PDF
        page.pdf(
            path=str(pdf_path),
            format='A4',
            print_background=True,
            margin={'top': '0', 'right': '0', 'bottom': '0', 'left': '0'}
        )

        browser.close()
        print(f"PDF generated: {pdf_path}")

if __name__ == "__main__":
    # 支持命令行参数
    if len(sys.argv) >= 3:
        svg_file = Path(sys.argv[1])
        pdf_file = Path(sys.argv[2])
    else:
        svg_file = PROJECT_ROOT / "templates" / "Fei_Huang_DE_Resume.svg"
        pdf_file = PROJECT_ROOT / "output" / "Fei_Huang_DE_Resume.pdf"

    # 确保输出目录存在
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    svg_to_pdf(svg_file, pdf_file)
