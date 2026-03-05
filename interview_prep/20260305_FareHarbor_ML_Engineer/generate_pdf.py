"""
生成 ML Cheatsheet PDF
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from pathlib import Path

# 读取 Markdown
md_file = Path('ml_cheatsheet_2pages.md')
lines = md_file.read_text(encoding='utf-8').split('\n')

# 创建 PDF
pdf_file = 'ml_cheatsheet_2pages.pdf'
doc = SimpleDocTemplate(
    pdf_file,
    pagesize=A4,
    leftMargin=0.8*cm,
    rightMargin=0.8*cm,
    topMargin=0.8*cm,
    bottomMargin=0.8*cm
)

# 样式
styles = getSampleStyleSheet()

title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=13,
    textColor=colors.HexColor('#2c3e50'),
    spaceAfter=4,
    spaceBefore=0,
    alignment=TA_CENTER,
    fontName='Helvetica-Bold'
)

h2_style = ParagraphStyle(
    'CustomH2',
    parent=styles['Heading2'],
    fontSize=9,
    textColor=colors.HexColor('#2c3e50'),
    spaceAfter=2,
    spaceBefore=6,
    fontName='Helvetica-Bold'
)

h3_style = ParagraphStyle(
    'CustomH3',
    parent=styles['Heading3'],
    fontSize=8,
    textColor=colors.HexColor('#34495e'),
    spaceAfter=2,
    spaceBefore=4,
    fontName='Helvetica-Bold'
)

code_style = ParagraphStyle(
    'Code',
    parent=styles['Code'],
    fontSize=6.5,
    fontName='Courier',
    leftIndent=8,
    spaceAfter=2,
    spaceBefore=2,
    leading=8
)

normal_style = ParagraphStyle(
    'CustomNormal',
    parent=styles['Normal'],
    fontSize=7.5,
    spaceAfter=2,
    leading=9
)

story = []
in_code_block = False
code_lines = []

i = 0
while i < len(lines):
    line = lines[i].rstrip()

    # 标题
    if line.startswith('# '):
        text = line[2:].replace('**', '<b>').replace('**', '</b>')
        story.append(Paragraph(text, title_style))

    elif line.startswith('## '):
        text = line[3:].replace('**', '<b>').replace('**', '</b>')
        story.append(Paragraph(text, h2_style))

    elif line.startswith('### '):
        text = line[4:].replace('**', '<b>').replace('**', '</b>')
        story.append(Paragraph(text, h3_style))

    # 代码块
    elif line.startswith('```'):
        if in_code_block:
            # 结束代码块
            code_text = '\n'.join(code_lines)
            if code_text.strip():
                story.append(Preformatted(code_text, code_style))
            code_lines = []
            in_code_block = False
        else:
            # 开始代码块
            in_code_block = True

    elif in_code_block:
        code_lines.append(line)

    # 分隔线
    elif line.strip() == '---':
        story.append(Spacer(1, 0.15*cm))

    # 表格（简化处理）
    elif line.strip().startswith('|') and not in_code_block:
        # 跳过表格（太复杂，简化处理）
        pass

    # 普通文本
    elif line.strip() and not in_code_block:
        # 处理粗体和代码
        text = line
        text = text.replace('**', '<b>').replace('**', '</b>')
        text = text.replace('`', '<font name="Courier" size="7">')
        text = text.replace('`', '</font>')

        # 处理列表
        if line.strip().startswith('- '):
            text = '• ' + text[2:]

        story.append(Paragraph(text, normal_style))

    i += 1

# 生成 PDF
doc.build(story)
print('✓ PDF 已生成: ml_cheatsheet_2pages.pdf')
