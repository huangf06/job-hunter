"""
简历生成器 - 基于配置的动态简历生成
"""

import re
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class ResumeConfig:
    """简历配置"""
    template_path: str
    summary_config: Dict
    bullet_config: Dict
    skills_config: Dict
    pdf_config: Dict


class ResumeGenerator:
    """简历生成器"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.template = self._load_template()
    
    def _load_template(self) -> str:
        """加载HTML模板"""
        template_path = self.config.get('template', {}).get('base_template', 'templates/resume.html')
        
        # 尝试多个路径
        paths_to_try = [
            Path(template_path),
            Path('job-hunter') / template_path,
            Path('workspace/job-hunter') / template_path,
        ]
        
        for path in paths_to_try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    def generate(self, job: Dict, variant_config: Dict = None) -> str:
        """
        生成定制简历
        
        Args:
            job: 职位信息
            variant_config: 实验变体配置（可选）
        
        Returns:
            HTML字符串
        """
        html = self.template
        
        # 合并配置
        config = self.config.copy()
        if variant_config:
            config = self._merge_config(config, variant_config)
        
        # 生成Summary
        summary = self._generate_summary(job, config.get('summary', {}))
        html = self._replace_summary(html, summary)
        
        # 可以扩展：动态调整bullet points、技能顺序等
        
        return html
    
    def _generate_summary(self, job: Dict, summary_config: Dict) -> str:
        """生成Summary"""
        title = job.get('title', '').lower()
        company = job.get('company', 'the company')
        
        # 确定角色类型
        role_type = self._detect_role_type(title)
        
        # 获取模板
        templates = summary_config.get('generation', {}).get('role_based_templates', {})
        template_data = templates.get(role_type, templates.get('data_scientist', {}))
        
        if not template_data:
            # 默认summary
            return f"Data professional with expertise in machine learning and data analysis. M.Sc. in AI from VU Amsterdam. Seeking to contribute to {company}."
        
        # 填充模板
        template = template_data.get('template', '')
        skills = template_data.get('skills', [])
        key_experiences = template_data.get('key_experiences', [])
        thesis_topic = template_data.get('thesis_topic', 'AI research')
        background = template_data.get('background', key_experiences)  # 如果没有background，使用key_experiences
        
        # 构建格式化参数
        format_args = {
            'skills': ', '.join(skills[:3]),
            'key_experiences': ', '.join(key_experiences[:3]),
            'thesis_topic': thesis_topic,
            'company': company,
            'background': ', '.join(background[:2]) if background else ''
        }
        
        summary = template.format(**format_args)
        
        # 应用长度限制
        max_length = summary_config.get('max_length', 300)
        if len(summary) > max_length:
            summary = summary[:max_length-3] + '...'
        
        return summary
    
    def _detect_role_type(self, title: str) -> str:
        """检测角色类型"""
        title_lower = title.lower()
        
        if 'machine learning' in title_lower or 'ml ' in title_lower:
            return 'ml_engineer'
        elif 'data engineer' in title_lower:
            return 'data_engineer'
        elif 'quant' in title_lower:
            return 'quantitative'
        elif 'analyst' in title_lower:
            return 'data_analyst'
        elif 'data scientist' in title_lower:
            return 'data_scientist'
        else:
            return 'data_scientist'  # 默认
    
    def _replace_summary(self, html: str, summary: str) -> str:
        """替换HTML中的summary"""
        # 使用正则替换tailored-summary div的内容
        pattern = r'(<div class="tailored-summary"[^\u003e]*\u003e)(.*?)(</div\u003e)'
        replacement = f'\\1{summary}\\3'
        
        result = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
        
        # 如果没匹配到，尝试其他选择器
        if result == html:
            # 尝试替换id为tailored-summary的元素
            pattern = r'(<div[^\u003e]*id=["\']tailored-summary["\'][^\u003e]*\u003e)(.*?)(</div\u003e)'
            result = re.sub(pattern, replacement, html, flags=re.DOTALL | re.IGNORECASE)
        
        return result
    
    def save(self, html: str, job: Dict, output_dir: str = 'output') -> Path:
        """
        保存HTML文件
        
        Returns:
            保存的文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        safe_company = re.sub(r'[^\w\-]', '_', job.get('company', 'unknown').lower())[:20]
        safe_title = re.sub(r'[^\w\-]', '_', job.get('title', 'job').lower())[:20]
        
        filename = f"Fei_Huang_{safe_company}_{safe_title}.html"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    async def to_pdf(self, html_path: Path, output_path: Path = None) -> Path:
        """
        HTML转PDF
        
        Returns:
            PDF文件路径
        """
        from playwright.async_api import async_playwright
        
        if output_path is None:
            output_path = html_path.with_suffix('.pdf')
        
        pdf_config = self.config.get('pdf', {}).get('page', {})
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            await page.goto(f"file:///{html_path.resolve()}")
            await page.wait_for_load_state("networkidle")
            
            await page.pdf(
                path=str(output_path),
                format=pdf_config.get('format', 'A4'),
                margin={
                    "top": pdf_config.get('margin', {}).get('top', '0.4in'),
                    "right": pdf_config.get('margin', {}).get('right', '0.4in'),
                    "bottom": pdf_config.get('margin', {}).get('bottom', '0.4in'),
                    "left": pdf_config.get('margin', {}).get('left', '0.4in'),
                },
                print_background=pdf_config.get('print_background', True)
            )
            
            await browser.close()
        
        return output_path
    
    def _merge_config(self, base: Dict, override: Dict) -> Dict:
        """递归合并配置"""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value
        
        return result


# ============== 使用示例 ==============

if __name__ == "__main__":
    # 测试配置
    test_config = {
        "template": {
            "base_template": "templates/resume.html"
        },
        "summary": {
            "max_length": 300,
            "generation": {
                "role_based_templates": {
                    "ml_engineer": {
                        "template": "ML Engineer with {skills}. M.Sc. in AI. Experienced in {key_experiences}.",
                        "skills": ["PyTorch", "TensorFlow"],
                        "key_experiences": ["model deployment"]
                    },
                    "data_scientist": {
                        "template": "Data Scientist with {skills}. M.Sc. in AI. Experienced in {key_experiences}.",
                        "skills": ["Python", "machine learning"],
                        "key_experiences": ["data analysis"]
                    }
                }
            }
        },
        "pdf": {
            "page": {
                "format": "A4",
                "margin": {"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"},
                "print_background": True
            }
        }
    }
    
    generator = ResumeGenerator(test_config)
    
    test_job = {
        "title": "Machine Learning Engineer",
        "company": "Picnic"
    }
    
    html = generator.generate(test_job)
    print(f"Generated HTML length: {len(html)}")
    
    # 保存
    # filepath = generator.save(html, test_job)
    # print(f"Saved to: {filepath}")
