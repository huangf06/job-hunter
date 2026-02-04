#!/usr/bin/env python3
"""
Job Hunter v4.2 - 智能岗位路由简历生成器

完整流程:
1. JD输入 → 2. 角色分类 → 3. 内容生成 → 4. 模板渲染 → 5. PDF输出

Usage:
    python job_hunter_v42.py --test          # 测试分类器
    python job_hunter_v42.py --job "JD文本"  # 生成单份简历
    python job_hunter_v42.py --daily         # 处理今日抓取
"""
import asyncio
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from role_classifier import RoleClassifier, ClassificationResult
from content_engine import ContentEngine, ResumeContent

# Add archive path for resume generator
sys.path.insert(0, str(Path(__file__).parent / "archive" / "old_generators"))
from resume_generator_v41 import ConfigDrivenGenerator


class JobHunterV42:
    """Job Hunter v4.2 主控制器"""
    
    def __init__(self):
        """初始化系统组件"""
        print("[INIT] Loading Job Hunter v4.2...")
        
        # 1. 角色分类器
        self.classifier = RoleClassifier()
        print("  [OK] Role Classifier")
        
        # 2. 内容引擎
        self.content_engine = ContentEngine()
        print("  [OK] Content Engine")
        
        # 3. 模板生成器 (按角色缓存)
        self.generators = {}
        print("  [OK] Template Generators")
        
        print("[INIT] System ready!\n")
    
    def get_generator(self, role: str) -> ConfigDrivenGenerator:
        """获取对应角色的生成器"""
        if role not in self.generators:
            template_file = f"templates/{role}.html"
            self.generators[role] = ConfigDrivenGenerator(
                template_path=template_file,
                library_path="assets/bullet_library_simple.yaml",
                config_path="config/role_templates.yaml"
            )
        return self.generators[role]
    
    def process_job(self, title: str, description: str, company: str, 
                   output_dir: str = "output") -> dict:
        """
        处理单个职位，生成简历
        
        Returns:
            dict: 生成结果信息
        """
        print(f"\n{'='*70}")
        print(f"[PROCESS] {title} @ {company}")
        print(f"{'='*70}")
        
        # Step 1: 角色分类
        classification = self.classifier.classify(title, description, company)
        role = classification.role
        
        print(f"\n[CLASSIFICATION]")
        print(f"  Role: {self.classifier.get_role_name(role)}")
        print(f"  Confidence: {classification.confidence:.1%}")
        
        if classification.applied_rules:
            print(f"  Rules: {', '.join(classification.applied_rules)}")
        
        # Step 2: 提取关键词 (简化版，从JD中提取)
        jd_keywords = self._extract_keywords(description)
        print(f"  Keywords: {', '.join(jd_keywords[:5])}")
        
        # Step 3: 生成内容
        content = self.content_engine.generate_content(role, company, jd_keywords)
        print(f"\n[CONTENT]")
        print(f"  Bio: {content.bio[:60]}...")
        print(f"  Experiences: {len(content.experiences)}")
        print(f"  Projects: {len(content.projects)}")
        
        # Step 4: 渲染模板
        generator = self.get_generator(role)
        
        # 构建模板数据
        template_data = self._build_template_data(content)
        
        # 渲染HTML
        from jinja2 import Template
        template_path = Path(f"job-hunter/templates/{role}.html")
        if not template_path.exists():
            template_path = Path(f"templates/{role}.html")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        html = template.render(**template_data)
        
        # Step 5: 保存和转换
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 文件名
        import re
        safe_title = re.sub(r'[^\w\-]', '_', title)[:30]
        safe_company = re.sub(r'[^\w\-]', '_', company)[:20]
        
        html_filename = f"Fei_Huang_{safe_title}_{safe_company}.html"
        pdf_filename = f"Fei_Huang_{safe_title}_{safe_company}.pdf"
        
        html_path = output_path / html_filename
        pdf_path = output_path / pdf_filename
        
        # 保存HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # 转换为PDF
        asyncio.run(self._to_pdf(html_path, pdf_path))
        
        print(f"\n[OUTPUT]")
        print(f"  HTML: {html_path.name}")
        print(f"  PDF: {pdf_path.name}")
        
        return {
            'role': role,
            'company': company,
            'title': title,
            'confidence': classification.confidence,
            'html_path': str(html_path),
            'pdf_path': str(pdf_path)
        }
    
    def _extract_keywords(self, description: str) -> list:
        """从JD中提取关键词"""
        # 简化版：直接返回常见技术关键词
        text = description.lower()
        keywords = []
        
        tech_keywords = [
            'python', 'pytorch', 'tensorflow', 'sql', 'spark', 'pyspark',
            'databricks', 'aws', 'docker', 'kubernetes', 'mlflow',
            'statistics', 'a/b testing', 'backtesting', 'alpha',
            'machine learning', 'deep learning', 'etl', 'pipeline'
        ]
        
        for kw in tech_keywords:
            if kw in text:
                keywords.append(kw)
        
        return keywords
    
    def _build_template_data(self, content: ResumeContent) -> dict:
        """构建模板数据"""
        personal = content.personal_info
        edu_master = content.education.get('master', {})
        edu_bachelor = content.education.get('bachelor', {})
        
        return {
            'name': personal.get('name', 'Fei Huang'),
            'location': personal.get('location', 'Amsterdam, Netherlands'),
            'phone': personal.get('phone', '+31 645 038 614'),
            'email': personal.get('email', 'huangf06@gmail.com'),
            'linkedin': personal.get('linkedin', 'https://linkedin.com/in/huangf06'),
            'linkedin_display': 'linkedin.com/in/huangf06',
            'github': personal.get('github', 'https://github.com/huangf06'),
            'github_display': 'github.com/huangf06',
            'bio': content.bio,
            'edu_master_school': edu_master.get('school', ''),
            'edu_master_location': edu_master.get('location', ''),
            'edu_master_degree': edu_master.get('degree', ''),
            'edu_master_date': edu_master.get('date', ''),
            'edu_master_note': edu_master.get('note', ''),
            'edu_bachelor_school': edu_bachelor.get('school', ''),
            'edu_bachelor_location': edu_bachelor.get('location', ''),
            'edu_bachelor_degree': edu_bachelor.get('degree', ''),
            'edu_bachelor_date': edu_bachelor.get('date', ''),
            'certification': content.education.get('certification', ''),
            'experiences': content.experiences,
            'projects': content.projects,
            'skills': content.skills,
            'career_note': content.career_note,
        }
    
    async def _to_pdf(self, html_path: Path, pdf_path: Path):
        """HTML转PDF"""
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file:///{html_path.resolve()}")
            await page.wait_for_load_state("networkidle")
            
            await page.pdf(
                path=str(pdf_path),
                format="A4",
                margin={"top": "0.55in", "right": "0.55in", "bottom": "0.55in", "left": "0.55in"},
                print_background=True
            )
            await browser.close()
    
    def test_classifier(self):
        """测试分类器"""
        test_cases = [
            ("Machine Learning Engineer", "Build ML pipelines with PyTorch, Docker, Kubernetes", "Picnic"),
            ("Data Engineer", "Design data pipelines with Spark, Databricks, Delta Lake", "ABN AMRO"),
            ("Data Scientist", "Statistical modeling, A/B testing, insights", "Booking.com"),
            ("Quantitative Researcher", "Alpha research, backtesting, factor modeling", "Optiver"),
            ("Senior ML Engineer", "Deep learning, recommendation systems, MLOps", "Unknown"),
        ]
        
        print("="*70)
        print("Role Classifier Test")
        print("="*70)
        
        for title, desc, company in test_cases:
            result = self.classifier.classify(title, desc, company)
            print(f"\n{title} @ {company}")
            print(f"  -> {self.classifier.get_role_name(result.role)} ({result.confidence:.0%})")


def main():
    """主入口"""
    parser = argparse.ArgumentParser(description='Job Hunter v4.2')
    parser.add_argument('--test', action='store_true', help='测试分类器')
    parser.add_argument('--job', type=str, help='JD文本 (标题|描述|公司)')
    parser.add_argument('--daily', action='store_true', help='处理今日抓取')
    
    args = parser.parse_args()
    
    hunter = JobHunterV42()
    
    if args.test:
        hunter.test_classifier()
    
    elif args.job:
        parts = args.job.split('|')
        if len(parts) == 3:
            title, desc, company = parts
            hunter.process_job(title, desc, company)
        else:
            print("[ERROR] Job format: 标题|描述|公司")
    
    elif args.daily:
        print("[TODO] Daily processing not implemented yet")
    
    else:
        # 默认测试
        hunter.test_classifier()


if __name__ == "__main__":
    main()
