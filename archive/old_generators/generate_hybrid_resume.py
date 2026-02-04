#!/usr/bin/env python3
"""
生成参考了 Corporate Professional 风格的 Picnic 简历
结合 Modern Minimal 和这个模板的优点
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from resume_generator_v41 import ConfigDrivenGenerator, ResumeConfig, JobDescription


# 融合风格：Modern Minimal + Corporate Professional 优点
STYLE_HYBRID = """
:root {
    --primary-color: #111827;
    --secondary-color: #374151;
    --accent-color: #059669;
    --border-color: #d1d5db;
    --text-main: #1f2937;
    --text-muted: #6b7280;
    --link-color: #2563eb;
    --bg-color: #ffffff;
}

body { 
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; 
    font-size: 10pt; 
    line-height: 1.45;
    color: var(--text-main);
    background: var(--bg-color);
}

/* Header - 居中但简洁 */
.header { 
    text-align: center; 
    margin-bottom: 14pt;
    padding-bottom: 10pt;
    border-bottom: 1pt solid var(--border-color);
}

.name { 
    font-size: 26pt; 
    font-weight: 700; 
    color: var(--primary-color);
    letter-spacing: -0.3pt;
    margin-bottom: 4pt;
}

.contact-row { 
    font-size: 9pt; 
    color: var(--text-muted);
    line-height: 1.5;
}

.contact-row a { 
    color: var(--link-color); 
    text-decoration: none;
}

.contact-divider { 
    color: var(--border-color); 
    margin: 0 6pt;
}

/* Bio - 简洁的摘要 */
.bio { 
    font-size: 10pt; 
    line-height: 1.5;
    color: var(--secondary-color);
    margin-bottom: 12pt;
    text-align: justify;
}

/* Section - 大写标题，简洁分隔 */
.section { 
    margin-bottom: 12pt; 
}

.section-title { 
    font-size: 10pt; 
    font-weight: 700;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 1.5pt;
    margin-bottom: 8pt;
    padding-bottom: 3pt;
    border-bottom: 1pt solid var(--border-color);
}

/* Experience - 职位大写，公司信息清晰 */
.experience-item {
    margin-bottom: 10pt;
}

.exp-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1pt;
}

.exp-company {
    font-weight: 700;
    font-size: 10pt;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.3pt;
}

.exp-location {
    font-size: 9pt;
    color: var(--text-muted);
}

.exp-subheader {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 3pt;
}

.exp-title {
    font-weight: 600;
    font-size: 9.5pt;
    color: var(--secondary-color);
}

.exp-date {
    font-size: 9pt;
    color: var(--text-muted);
    font-style: italic;
}

/* Bullets - 紧凑但清晰 */
.exp-bullets {
    list-style: disc;
    padding-left: 14pt;
    margin: 0;
}

.exp-bullets li {
    font-size: 9.5pt;
    line-height: 1.4;
    color: var(--text-main);
    margin-bottom: 1.5pt;
}

/* Education - 两栏布局 */
.edu-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12pt;
}

.education-item {
    margin-bottom: 6pt;
}

.edu-school {
    font-weight: 700;
    font-size: 9.5pt;
    color: var(--primary-color);
}

.edu-degree {
    font-weight: 600;
    font-size: 9pt;
    color: var(--secondary-color);
}

.edu-location, .edu-date {
    font-size: 8.5pt;
    color: var(--text-muted);
}

.edu-note {
    font-size: 8.5pt;
    color: var(--text-muted);
    font-style: italic;
}

/* Skills - 三栏网格 */
.skills-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4pt 12pt;
    font-size: 9pt;
}

.skill-item {
    color: var(--text-main);
}

/* Languages */
.languages-row {
    font-size: 9pt;
    color: var(--text-main);
}

.language-name {
    font-weight: 600;
}

.language-level {
    color: var(--text-muted);
}

/* Career note */
.career-note {
    font-size: 9pt;
    color: var(--text-muted);
    font-style: italic;
    margin-top: 4pt;
}

/* Print optimization */
@media print {
    body {
        padding: 0;
    }
    
    .section {
        break-inside: avoid;
    }
    
    .experience-item {
        break-inside: avoid;
    }
}
"""


def apply_hybrid_style(base_html: str, style_css: str) -> str:
    """应用融合风格到基础模板"""
    import re
    
    # 提取 :root 变量
    root_match = re.search(r':root \{([^}]+)\}', style_css)
    root_vars = root_match.group(1) if root_match else ""
    
    # 构建新的样式块
    custom_style = f"""
    <style>
        :root {{{root_vars}}}
        
        {style_css}
    </style>
    """
    
    # 替换原模板中的 style 标签
    styled_html = re.sub(r'<style>.*?</style>', custom_style, base_html, flags=re.DOTALL)
    
    return styled_html


async def generate_hybrid_resume():
    """生成融合风格的 Picnic 简历"""
    
    generator = ConfigDrivenGenerator()
    
    # Picnic Data Engineer JD
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
    print("Generating Hybrid Style Resume for Picnic")
    print("(Modern Minimal + Corporate Professional)")
    print("=" * 70)
    
    try:
        # 生成基础 HTML
        base_html = generator.generate(config)
        
        # 应用融合风格
        styled_html = apply_hybrid_style(base_html, STYLE_HYBRID)
        
        # 保存 HTML
        output_dir = Path("output/picnic_style_variations")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        html_path = output_dir / "Fei_Huang_07_hybrid_picnic.html"
        html_path.write_text(styled_html, encoding='utf-8')
        
        # 生成 PDF
        pdf_path = await generator.to_pdf(html_path)
        
        print(f"\n[OK] Generated: {pdf_path.name}")
        print(f"\nLocation: {pdf_path}")
        
        return pdf_path
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    asyncio.run(generate_hybrid_resume())
