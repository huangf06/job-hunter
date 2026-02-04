#!/usr/bin/env python3
"""
Picnic Data Engineer 简历 - 多视觉风格版本
内容保持一致，只改变视觉呈现
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from resume_generator_v41 import ConfigDrivenGenerator, ResumeConfig, JobDescription


# =============================================================================
# 不同视觉风格的 CSS 模板
# =============================================================================

# 风格1: 经典 Toni 风格 (当前默认)
STYLE_TONI_CLASSIC = """
:root {
    --primary-color: #1a1a1a;
    --secondary-color: #4a4a4a;
    --accent-color: #2c5282;
    --border-color: #1a1a1a;
    --text-main: #1a1a1a;
    --text-muted: #555555;
    --link-color: #2c5282;
    --bg-color: white;
}
body { font-family: Georgia, 'Times New Roman', serif; font-size: 10pt; line-height: 1.35; }
.header { text-align: center; border-bottom: 2pt solid var(--border-color); }
.name { font-size: 24pt; font-weight: bold; letter-spacing: 1pt; }
.section-title { text-transform: uppercase; letter-spacing: 0.5pt; border-bottom: 1.5pt solid var(--border-color); }
"""

# 风格2: 现代极简 - 无衬线字体，大量留白
STYLE_MODERN_MINIMAL = """
:root {
    --primary-color: #0f172a;
    --secondary-color: #475569;
    --accent-color: #3b82f6;
    --border-color: #e2e8f0;
    --text-main: #1e293b;
    --text-muted: #64748b;
    --link-color: #2563eb;
    --bg-color: white;
}
body { 
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
    font-size: 9.5pt; 
    line-height: 1.5;
    color: var(--text-main);
}
.header { 
    text-align: left; 
    border-bottom: none;
    margin-bottom: 16pt;
}
.name { 
    font-size: 28pt; 
    font-weight: 700; 
    letter-spacing: -0.5pt;
    color: var(--primary-color);
    margin-bottom: 8pt;
}
.contact-row { 
    font-size: 9pt; 
    color: var(--text-muted);
    font-weight: 400;
}
.contact-row a { color: var(--link-color); }
.contact-divider { margin: 0 8pt; color: var(--border-color); }
.bio { 
    font-size: 10pt; 
    line-height: 1.6;
    color: var(--secondary-color);
    margin-bottom: 16pt;
    padding-bottom: 12pt;
    border-bottom: 1pt solid var(--border-color);
}
.section { margin-bottom: 16pt; }
.section-title { 
    font-size: 10pt; 
    font-weight: 600;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-bottom: 10pt;
    padding-bottom: 4pt;
    border-bottom: 1pt solid var(--border-color);
}
.edu-school, .exp-company, .project-name { font-weight: 600; font-size: 10pt; }
.edu-degree, .exp-title { font-style: normal; font-weight: 500; color: var(--secondary-color); }
.edu-date, .exp-date, .exp-location, .edu-location { 
    font-size: 9pt; 
    color: var(--text-muted);
    font-style: normal;
    font-weight: 400;
}
.exp-bullets li, .project-bullets li { 
    font-size: 9.5pt; 
    line-height: 1.5;
    margin-bottom: 3pt;
}
.skills-container { 
    grid-template-columns: 90pt 1fr;
    gap: 4pt 12pt;
    font-size: 9pt;
}
.skill-category { font-weight: 600; color: var(--primary-color); }
.career-note { 
    font-size: 9pt; 
    color: var(--text-muted);
    font-style: normal;
    padding-left: 14pt;
}
"""

# 风格3: 专业商务 - 深蓝色调，稳重
STYLE_PROFESSIONAL = """
:root {
    --primary-color: #1e3a5f;
    --secondary-color: #4a6fa5;
    --accent-color: #2e5c8a;
    --border-color: #1e3a5f;
    --text-main: #2d3748;
    --text-muted: #5a6c7d;
    --link-color: #1e3a5f;
    --bg-color: white;
}
body { 
    font-family: 'Calibri', 'Segoe UI', Arial, sans-serif; 
    font-size: 10.5pt; 
    line-height: 1.4;
}
.header { 
    text-align: center; 
    background: linear-gradient(to bottom, #f8fafc, white);
    padding: 12pt 0;
    border-bottom: 2.5pt solid var(--primary-color);
    margin-bottom: 14pt;
}
.name { 
    font-size: 26pt; 
    font-weight: 700; 
    color: var(--primary-color);
    letter-spacing: 0.5pt;
    text-transform: uppercase;
}
.contact-row { 
    font-size: 9.5pt; 
    color: var(--text-muted);
    margin-top: 6pt;
}
.contact-row a { 
    color: var(--link-color); 
    font-weight: 500;
}
.section { margin-bottom: 14pt; }
.section-title { 
    font-size: 11pt; 
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 1pt;
    margin-bottom: 8pt;
    padding: 4pt 0;
    border-bottom: 1.5pt solid var(--secondary-color);
    background: #f8fafc;
    padding-left: 6pt;
}
.edu-school, .exp-company, .project-name { 
    font-weight: 700; 
    font-size: 10.5pt;
    color: var(--primary-color);
}
.edu-degree, .exp-title { 
    font-style: italic; 
    font-weight: 600;
    color: var(--secondary-color);
}
.edu-date, .exp-date { 
    font-size: 9.5pt; 
    color: var(--text-muted);
    font-weight: 500;
}
.exp-bullets li { 
    font-size: 10pt; 
    line-height: 1.4;
    margin-bottom: 2pt;
}
.skills-container { 
    grid-template-columns: 100pt 1fr;
    gap: 3pt 10pt;
    font-size: 10pt;
}
.skill-category { 
    font-weight: 700; 
    color: var(--primary-color);
}
"""

# 风格4: 创意现代 - 左侧边栏，两栏布局
STYLE_CREATIVE_SIDEBAR = """
:root {
    --primary-color: #111827;
    --secondary-color: #374151;
    --accent-color: #059669;
    --sidebar-bg: #f3f4f6;
    --text-main: #1f2937;
    --text-muted: #6b7280;
    --link-color: #059669;
}
body { 
    font-family: 'Segoe UI', system-ui, sans-serif; 
    font-size: 9.5pt; 
    line-height: 1.45;
    display: grid;
    grid-template-columns: 140pt 1fr;
    gap: 16pt;
    padding: 0.4in;
}
.header { 
    grid-column: 1 / -1;
    text-align: left; 
    border-bottom: 2pt solid var(--accent-color);
    padding-bottom: 10pt;
    margin-bottom: 0;
}
.name { 
    font-size: 24pt; 
    font-weight: 800; 
    color: var(--primary-color);
    letter-spacing: -0.5pt;
}
.contact-row { 
    font-size: 8.5pt; 
    color: var(--text-muted);
    margin-top: 4pt;
}
.contact-row a { color: var(--link-color); }
.bio { 
    grid-column: 1 / -1;
    font-size: 10pt; 
    line-height: 1.5;
    margin-bottom: 12pt;
    padding: 10pt;
    background: var(--sidebar-bg);
    border-left: 3pt solid var(--accent-color);
}
.sidebar {
    grid-column: 1;
    background: var(--sidebar-bg);
    padding: 10pt;
    border-radius: 4pt;
}
.main-content {
    grid-column: 2;
}
.section { margin-bottom: 12pt; }
.section-title { 
    font-size: 10pt; 
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    margin-bottom: 8pt;
    padding-bottom: 3pt;
    border-bottom: 1pt solid var(--accent-color);
}
.edu-school, .exp-company, .project-name { font-weight: 700; font-size: 10pt; }
.edu-degree, .exp-title { font-weight: 500; color: var(--secondary-color); }
.edu-date, .exp-date { font-size: 8.5pt; color: var(--text-muted); }
.exp-bullets li { font-size: 9pt; line-height: 1.45; margin-bottom: 2pt; }
.skills-container { 
    display: block;
    font-size: 9pt;
}
.skill-category { 
    font-weight: 700; 
    color: var(--primary-color);
    margin-top: 6pt;
    margin-bottom: 2pt;
}
.skill-list { display: block; margin-bottom: 4pt; }
@page { size: A4; margin: 0.4in; }
"""

# 风格5: 优雅精致 - 细边框，精致排版
STYLE_ELEGANT = """
:root {
    --primary-color: #2c1810;
    --secondary-color: #5c4a42;
    --accent-color: #8b6914;
    --border-color: #d4c4b0;
    --text-main: #3d2817;
    --text-muted: #7a6b5a;
    --link-color: #8b6914;
    --bg-color: #fefefe;
}
body { 
    font-family: 'Garamond', 'Times New Roman', Georgia, serif; 
    font-size: 10.5pt; 
    line-height: 1.45;
    color: var(--text-main);
    background: var(--bg-color);
}
.header { 
    text-align: center; 
    border-bottom: 1pt solid var(--border-color);
    padding-bottom: 12pt;
    margin-bottom: 14pt;
}
.name { 
    font-size: 26pt; 
    font-weight: normal;
    color: var(--primary-color);
    letter-spacing: 2pt;
    text-transform: uppercase;
    font-variant: small-caps;
}
.contact-row { 
    font-size: 9.5pt; 
    color: var(--text-muted);
    font-style: italic;
    margin-top: 6pt;
}
.contact-row a { 
    color: var(--link-color); 
    text-decoration: none;
    font-style: normal;
}
.bio { 
    font-size: 10.5pt; 
    line-height: 1.5;
    text-align: center;
    font-style: italic;
    color: var(--secondary-color);
    margin-bottom: 16pt;
    padding: 0 20pt;
}
.section { margin-bottom: 16pt; }
.section-title { 
    font-size: 11pt; 
    font-weight: normal;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 2pt;
    text-align: center;
    margin-bottom: 10pt;
    padding-bottom: 4pt;
    border-bottom: 0.5pt solid var(--border-color);
    font-variant: small-caps;
}
.edu-school, .exp-company, .project-name { 
    font-weight: bold; 
    font-size: 10.5pt;
    color: var(--primary-color);
}
.edu-degree, .exp-title { 
    font-style: italic;
    color: var(--secondary-color);
}
.edu-date, .exp-date { 
    font-size: 9.5pt; 
    color: var(--text-muted);
    font-style: italic;
}
.exp-bullets li { 
    font-size: 10pt; 
    line-height: 1.45;
    margin-bottom: 3pt;
}
.skills-container { 
    grid-template-columns: 100pt 1fr;
    gap: 4pt 10pt;
    font-size: 10pt;
}
.skill-category { 
    font-weight: bold; 
    color: var(--primary-color);
    font-variant: small-caps;
}
.career-note {
    font-style: italic;
    color: var(--text-muted);
    text-align: center;
    padding-left: 0;
    margin-top: 8pt;
}
"""

# 风格6: 科技风 - 等宽字体，代码感
STYLE_TECH = """
:root {
    --primary-color: #00d4aa;
    --secondary-color: #7dd3fc;
    --accent-color: #00d4aa;
    --bg-color: #0f172a;
    --text-main: #e2e8f0;
    --text-muted: #94a3b8;
    --link-color: #38bdf8;
}
body { 
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace; 
    font-size: 9pt; 
    line-height: 1.5;
    color: var(--text-main);
    background: var(--bg-color);
}
.header { 
    text-align: left; 
    border-bottom: 1pt solid var(--primary-color);
    padding-bottom: 10pt;
    margin-bottom: 12pt;
}
.name { 
    font-size: 22pt; 
    font-weight: bold;
    color: var(--primary-color);
    letter-spacing: 1pt;
}
.name::before { content: "> "; color: var(--secondary-color); }
.contact-row { 
    font-size: 8.5pt; 
    color: var(--text-muted);
    margin-top: 6pt;
}
.contact-row a { color: var(--link-color); }
.contact-divider { color: var(--primary-color); margin: 0 6pt; }
.bio { 
    font-size: 9.5pt; 
    line-height: 1.6;
    color: var(--text-muted);
    margin-bottom: 14pt;
    padding: 10pt;
    background: rgba(0, 212, 170, 0.05);
    border-left: 2pt solid var(--primary-color);
}
.section { margin-bottom: 14pt; }
.section-title { 
    font-size: 10pt; 
    font-weight: bold;
    color: var(--primary-color);
    text-transform: uppercase;
    margin-bottom: 8pt;
    padding-bottom: 3pt;
    border-bottom: 0.5pt dashed var(--secondary-color);
}
.section-title::before { content: "# "; color: var(--secondary-color); }
.edu-school, .exp-company, .project-name { 
    font-weight: bold; 
    font-size: 10pt;
    color: var(--secondary-color);
}
.edu-degree, .exp-title { 
    color: var(--text-main);
}
.edu-date, .exp-date { 
    font-size: 8.5pt; 
    color: var(--primary-color);
}
.exp-bullets { 
    list-style: none;
    padding-left: 0;
}
.exp-bullets li { 
    font-size: 9pt; 
    line-height: 1.5;
    margin-bottom: 3pt;
    padding-left: 12pt;
    position: relative;
}
.exp-bullets li::before {
    content: "→";
    position: absolute;
    left: 0;
    color: var(--primary-color);
}
.skills-container { 
    grid-template-columns: 100pt 1fr;
    gap: 3pt 8pt;
    font-size: 9pt;
}
.skill-category { 
    font-weight: bold; 
    color: var(--primary-color);
}
.skill-list { color: var(--secondary-color); }
@page { 
    size: A4; 
    margin: 0.5in;
    background: var(--bg-color);
}
"""


STYLES = {
    "01_toni_classic": ("Classic Toni Style", STYLE_TONI_CLASSIC),
    "02_modern_minimal": ("Modern Minimal", STYLE_MODERN_MINIMAL),
    "03_professional": ("Professional Business", STYLE_PROFESSIONAL),
    "04_creative_sidebar": ("Creative Sidebar", STYLE_CREATIVE_SIDEBAR),
    "05_elegant": ("Elegant Refined", STYLE_ELEGANT),
    "06_tech": ("Tech Code Style", STYLE_TECH),
}


def apply_style_to_template(base_html: str, style_css: str) -> str:
    """将样式应用到基础模板"""
    # 提取 body 样式
    body_style = ""
    if "body {" in style_css:
        start = style_css.find("body {")
        end = style_css.find("}", start) + 1
        body_style = style_css[start:end]
    
    # 替换 CSS 变量和主要样式
    import re
    
    # 提取 :root 变量
    root_match = re.search(r':root \{([^}]+)\}', style_css)
    root_vars = root_match.group(1) if root_match else ""
    
    # 构建新的样式块
    custom_style = f"""
    <style>
        :root {{{root_vars}}}
        
        {style_css}
        
        /* Override base styles */
        {body_style}
    </style>
    """
    
    # 替换原模板中的 style 标签
    styled_html = re.sub(r'<style>.*?</style>', custom_style, base_html, flags=re.DOTALL)
    
    return styled_html


async def generate_style_variations():
    """生成多种视觉风格的 Picnic 简历"""
    
    generator = ConfigDrivenGenerator()
    
    # 使用 Data Engineer 角色，统一的 JD
    job = JobDescription(
        title="Data Engineer",
        company="Picnic",
        description="Python, PySpark, Databricks, SQL, AWS, data pipelines, ETL, Delta Lake, data warehousing"
    )
    
    config = ResumeConfig(
        target_role="data_engineer",
        company="Picnic",
        job_description=job,
        max_bullets_per_exp=3,
    )
    
    print("=" * 70)
    print("Picnic Data Engineer - Visual Style Comparison")
    print("=" * 70)
    print("\nContent stays consistent, only visual style changes\n")
    
    generated = []
    
    # 先生成基础 HTML
    base_html = generator.generate(config)
    
    for i, (style_key, (style_name, style_css)) in enumerate(STYLES.items(), 1):
        print(f"[{i}/{len(STYLES)}] Generating: {style_name}")
        
        try:
            # 应用样式
            styled_html = apply_style_to_template(base_html, style_css)
            
            # 保存 HTML
            output_dir = Path("output/picnic_style_variations")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            html_path = output_dir / f"Fei_Huang_{style_key}_picnic.html"
            html_path.write_text(styled_html, encoding='utf-8')
            
            # 生成 PDF
            pdf_path = await generator.to_pdf(html_path)
            
            generated.append({
                'key': style_key,
                'name': style_name,
                'pdf': pdf_path,
                'html': html_path
            })
            print(f"    [OK] {pdf_path.name}")
            
        except Exception as e:
            print(f"    [ERROR] {e}")
            import traceback
            traceback.print_exc()
    
    # 打印总结
    print("\n" + "=" * 70)
    print("Generation Complete! All visual styles:")
    print("=" * 70)
    
    for i, g in enumerate(generated, 1):
        print(f"\n{i}. {g['name']}")
        print(f"   File: {g['pdf'].name}")
    
    print("\n" + "=" * 70)
    print("Location: job-hunter/output/picnic_style_variations/")
    print("Pick your favorite style!")
    print("=" * 70)
    
    return generated


if __name__ == '__main__':
    asyncio.run(generate_style_variations())
