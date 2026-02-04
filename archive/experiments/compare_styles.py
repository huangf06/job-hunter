#!/usr/bin/env python3
"""分析各简历版本的样式差异"""

from pathlib import Path
import re

# 分析各个HTML版本的样式特点
styles = {}
for f in Path('output/picnic_style_variations').glob('*.html'):
    content = f.read_text(encoding='utf-8')
    
    # 提取字体
    font_match = re.search(r'font-family:\s*([^;]+)', content)
    font = font_match.group(1).strip() if font_match else 'unknown'
    
    # 提取标题对齐
    header_match = re.search(r'\.header\s*\{[^}]*text-align:\s*(\w+)', content, re.DOTALL)
    header_align = header_match.group(1) if header_match else 'unknown'
    
    # 提取名字大小
    name_match = re.search(r'\.name\s*\{[^}]*font-size:\s*([\d.]+pt)', content, re.DOTALL)
    name_size = name_match.group(1) if name_match else 'unknown'
    
    # 检查是否有背景色
    has_bg = 'background:' in content or '--bg-color' in content
    
    styles[f.stem] = {
        'font': font[:50],
        'header_align': header_align,
        'name_size': name_size,
        'has_custom_bg': has_bg
    }

# 打印对比
print('=' * 80)
print('Picnic Resume Style Comparison')
print('=' * 80)
for name, s in sorted(styles.items()):
    print(f'\n{name}:')
    print(f"  Font: {s['font']}")
    print(f"  Header: {s['header_align']}")
    print(f"  Name size: {s['name_size']}")
    print(f"  Custom bg: {s['has_custom_bg']}")

# 对比现有的 Adyen 版本
print('\n' + '=' * 80)
print('Reference: Fei_Huang_data_engineer_adyen.pdf')
print('(Uses same Toni Classic style as current picnic version)')
print('=' * 80)
