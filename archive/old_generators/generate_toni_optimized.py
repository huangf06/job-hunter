#!/usr/bin/env python3
"""
Toni 风格优化版 - Georgia 字体 + 双栏 Skills
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from resume_generator_v41 import ConfigDrivenGenerator, ResumeConfig, JobDescription


# Toni 风格优化版 - 保留 Georgia 美感，优化 Skills 布局
STYLE_TONI_OPTIMIZED = """
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

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

@page {
    size: A4;
    margin: 0.55in;
}

body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 10pt;
    line-height: 1.35;
    color: var(--text-main);
    max-width: 8.27in;
    margin: 0 auto;
    padding: 0.55in;
    background: white;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

/* Header - 居中，Toni 风格 */
.header {
    text-align: center;
    margin-bottom: 12pt;
    padding-bottom: 10pt;
    border-bottom: 2pt solid var(--border-color);
}

.name {
    font-size: 24pt;
    font-weight: bold;
    color: var(--primary-color);
    letter-spacing: 1pt;
    margin-bottom: 5pt;
}

.contact-row {
    font-size: 9.5pt;
    color: var(--text-muted);
    line-height: 1.4;
}

.contact-row a {
    color: var(--link-color);
    text-decoration: none;
}

.contact-divider {
    color: var(--text-muted);
    margin: 0 5pt;
}

/* Bio */
.bio {
    font-size: 10pt;
    line-height: 1.4;
    color: var(--text-main);
    margin-bottom: 12pt;
    text-align: left;
}

/* Section */
.section {
    margin-bottom: 12pt;
}

.section-title {
    font-size: 11pt;
    font-weight: bold;
    color: var(--primary-color);
    text-transform: uppercase;
    letter-spacing: 0.5pt;
    margin-bottom: 8pt;
    padding-bottom: 2pt;
    border-bottom: 1.5pt solid var(--border-color);
}

/* Education */
.education-item {
    margin-bottom: 8pt;
}

.edu-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1pt;
}

.edu-school {
    font-weight: bold;
    font-size: 10.5pt;
    color: var(--primary-color);
}

.edu-location {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
}

.edu-details {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
}

.edu-degree {
    font-style: italic;
    font-size: 10pt;
    color: var(--text-main);
}

.edu-date {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
}

.edu-note {
    font-size: 9.5pt;
    color: var(--text-muted);
    margin-top: 1pt;
    font-style: italic;
}

/* Experience */
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
    font-weight: bold;
    font-size: 10.5pt;
    color: var(--primary-color);
}

.exp-location {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
}

.exp-subheader {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 4pt;
}

.exp-title {
    font-style: italic;
    font-size: 10pt;
    color: var(--text-main);
}

.exp-date {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
}

.exp-bullets {
    list-style: disc;
    padding-left: 14pt;
    margin: 0;
}

.exp-bullets li {
    font-size: 9.5pt;
    line-height: 1.35;
    color: var(--text-main);
    margin-bottom: 2pt;
    text-align: left;
}

.career-note {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
    margin-top: 4pt;
    padding-left: 14pt;
}

/* Projects */
.project-item {
    margin-bottom: 8pt;
}

.project-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 2pt;
}

.project-name {
    font-weight: bold;
    font-size: 10.5pt;
    color: var(--primary-color);
}

.project-date {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
}

.project-bullets {
    list-style: disc;
    padding-left: 14pt;
    margin: 0;
}

.project-bullets li {
    font-size: 9.5pt;
    line-height: 1.35;
    color: var(--text-main);
    margin-bottom: 2pt;
}

/* Skills - 双栏布局 */
.skills-container {
    display: grid;
    grid-template-columns: 100pt 1fr;
    gap: 4pt 10pt;
    font-size: 9.5pt;
}

.skill-category {
    font-weight: bold;
    color: var(--primary-color);
    text-align: left;
}

.skill-list {
    color: var(--text-main);
    line-height: 1.35;
}

/* 双栏 Skills 布局 */
.skills-two-column {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6pt 20pt;
    font-size: 9.5pt;
}

.skill-col {
    display: flex;
    flex-direction: column;
    gap: 4pt;
}

.skill-row {
    display: flex;
    gap: 6pt;
}

.skill-label {
    font-weight: bold;
    color: var(--primary-color);
    min-width: 70pt;
}

.skill-items {
    color: var(--text-main);
    flex: 1;
}

/* Languages */
.languages-row {
    font-size: 9.5pt;
    color: var(--text-main);
}

.language-item {
    display: inline;
}

.language-name {
    font-weight: bold;
}

.language-level {
    color: var(--text-muted);
    font-style: italic;
}

.language-divider {
    color: var(--text-muted);
    margin: 0 6pt;
}

/* Print */
@media print {
    body {
        padding: 0;
        max-width: none;
    }
    
    .section {
        break-inside: avoid;
    }
    
    .experience-item {
        break-inside: avoid;
    }
    
    .education-item {
        break-inside: avoid;
    }
    
    a {
        text-decoration: none;
        color: var(--text-main);
    }
    
    a[href]:after {
        content: "";
    }
}
"""


def apply_toni_optimized(base_html: str) -> str:
    """应用 Toni 优化风格"""
    import re
    
    # 替换样式
    styled_html = re.sub(
        r'<style>.*?</style>', 
        f'<style>{STYLE_TONI_OPTIMIZED}</style>', 
        base_html, 
        flags=re.DOTALL
    )
    
    # 修改 Skills 部分为双栏布局
    # 查找 skills-container 并替换为双栏版本
    skills_pattern = r'(<div class="skills-container">)(.*?)(</div>\s*</section>)'
    
    def replace_skills(match):
        # 提取原有的 skills 内容
        original_content = match.group(2)
        
        # 解析技能类别和项目
        skill_items = re.findall(
            r'<span class="skill-category">([^<]+)</span>\s*<span class="skill-list">([^<]+)</span>',
            original_content
        )
        
        # 分成两列
        mid = (len(skill_items) + 1) // 2
        left_col = skill_items[:mid]
        right_col = skill_items[mid:]
        
        # 构建双栏 HTML
        left_html = ''.join([
            f'<div class="skill-row"><span class="skill-label">{cat}</span><span class="skill-items">{items}</span></div>'
            for cat, items in left_col
        ])
        
        right_html = ''.join([
            f'<div class="skill-row"><span class="skill-label">{cat}</span><span class="skill-items">{items}</span></div>'
            for cat, items in right_col
        ]) if right_col else ''
        
        return f'''<div class="skills-two-column">
            <div class="skill-col">{left_html}</div>
            <div class="skill-col">{right_html}</div>
        </div>
        </section>'''
    
    styled_html = re.sub(skills_pattern, replace_skills, styled_html, flags=re.DOTALL)
    
    return styled_html


async def generate_toni_optimized():
    """生成 Toni 优化版简历"""
    
    generator = ConfigDrivenGenerator()
    
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
    print("Generating Toni-Optimized Resume for Picnic")
    print("(Georgia font + Two-column Skills)")
    print("=" * 70)
    
    try:
        base_html = generator.generate(config)
        styled_html = apply_toni_optimized(base_html)
        
        output_dir = Path("output/picnic_style_variations")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        html_path = output_dir / "Fei_Huang_08_toni_optimized_picnic.html"
        html_path.write_text(styled_html, encoding='utf-8')
        
        pdf_path = await generator.to_pdf(html_path)
        
        print(f"\n[OK] Generated: {pdf_path.name}")
        print(f"Location: {pdf_path}")
        
        return pdf_path
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    asyncio.run(generate_toni_optimized())
