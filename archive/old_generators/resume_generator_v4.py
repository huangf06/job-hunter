"""
智能简历生成器 v4.0 - Toni风格 + Bullet Points
深度集成 bullet_library.yaml，根据职位自动筛选最相关的内容
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from jinja2 import Template


@dataclass
class JobDescription:
    """职位描述"""
    title: str
    company: str
    description: str = ""
    requirements: List[str] = field(default_factory=list)
    
    def get_keywords(self) -> List[str]:
        """提取关键词"""
        text = f"{self.title} {self.description}".lower()
        
        # 技术关键词映射
        tech_keywords = {
            'python': ['python'],
            'sql': ['sql', 'hive', 'spark sql'],
            'pyspark': ['pyspark', 'spark'],
            'databricks': ['databricks'],
            'aws': ['aws', 'amazon web services'],
            'azure': ['azure'],
            'gcp': ['gcp', 'google cloud'],
            'docker': ['docker', 'containerization'],
            'kubernetes': ['kubernetes', 'k8s'],
            'airflow': ['airflow', 'apache airflow'],
            'kafka': ['kafka'],
            'ml': ['machine learning', 'ml', 'modeling'],
            'deep_learning': ['deep learning', 'neural networks', 'pytorch', 'tensorflow'],
            'statistics': ['statistics', 'statistical', 'a/b testing', 'hypothesis testing'],
            'quant': ['quantitative', 'quant', 'trading', 'finance'],
            'data_engineering': ['data engineering', 'etl', 'pipeline', 'data warehouse'],
            'credit_risk': ['credit risk', 'risk modeling', 'scoring'],
            'nlp': ['nlp', 'natural language processing', 'llm'],
        }
        
        found = []
        for category, keywords in tech_keywords.items():
            if any(kw in text for kw in keywords):
                found.append(category)
        
        return found


@dataclass
class ResumeConfig:
    """简历配置"""
    target_role: str  # data_engineer, ml_engineer, data_scientist, quant, etc.
    company: str
    job_description: JobDescription
    max_bullets_per_exp: int = 3
    include_projects: bool = True
    include_career_note: bool = True


class BulletLibrary:
    """Bullet 库管理器 - 简化版"""
    
    def __init__(self, library_path: str = "assets/bullet_library_simple.yaml"):
        self.library_path = Path(library_path)
        self.data = self._load_library()
    
    def _load_library(self) -> Dict:
        """加载 bullet library"""
        if not self.library_path.exists():
            # 尝试其他路径
            alt_paths = [
                Path("job-hunter") / self.library_path,
                Path("workspace/job-hunter") / self.library_path,
            ]
            for path in alt_paths:
                if path.exists():
                    self.library_path = path
                    break
        
        with open(self.library_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def get_personal_info(self) -> Dict:
        """获取个人信息"""
        return self.data.get('personal_info', {})
    
    def get_education(self) -> Dict:
        """获取教育信息"""
        return self.data.get('education', {})
    
    def get_experiences(self) -> List[Dict]:
        """获取所有工作经历"""
        return self.data.get('experiences', [])
    
    def get_projects(self) -> List[Dict]:
        """获取所有项目"""
        return self.data.get('projects', [])
    
    def get_skills(self) -> List[Dict]:
        """获取技能列表"""
        return self.data.get('skills', [])
    
    def get_languages(self) -> List[Dict]:
        """获取语言列表"""
        return self.data.get('languages', [])
    
    def get_career_note(self) -> str:
        """获取 career note"""
        return self.data.get('career_note', '')
    
    def score_bullet_relevance(self, bullet: Dict, job_keywords: List[str], target_role: str) -> float:
        """
        计算 bullet 与职位的相关度分数
        
        Returns:
            0-10 的分数，越高越相关
        """
        score = 0.0
        role_fit = bullet.get('role_fit', [])
        tech = bullet.get('tech', [])
        domain = bullet.get('domain', [])
        content = bullet.get('content', '').lower()
        
        # 1. 角色匹配 (0-3分)
        if target_role in role_fit:
            score += 3.0
        elif any(r in role_fit for r in ['data_scientist', 'data_engineer', 'ml_engineer']):
            score += 1.5
        
        # 2. 技术栈匹配 (0-3分)
        matching_tech = sum(1 for t in job_keywords if t.lower() in [x.lower() for x in tech])
        score += min(3.0, matching_tech * 1.0)
        
        # 3. 领域匹配 (0-2分)
        if 'fintech' in domain and 'finance' in job_keywords:
            score += 1.0
        if 'trading' in domain and ('quant' in job_keywords or 'trading' in job_keywords):
            score += 1.0
        if 'credit_risk' in domain and 'credit_risk' in job_keywords:
            score += 1.0
        
        # 4. 关键词匹配 (0-2分)
        keyword_matches = sum(1 for kw in job_keywords if kw.lower() in content)
        score += min(2.0, keyword_matches * 0.5)
        
        return min(10.0, score)
    
    def select_best_bullets(self, exp_index: int, job_keywords: List[str], 
                           target_role: str, max_bullets: int = 3) -> List[str]:
        """
        为指定经历选择最相关的 bullets
        
        Returns:
            排序后的 bullet 内容列表
        """
        experiences = self.get_experiences()
        if exp_index >= len(experiences):
            return []
        
        bullets = experiences[exp_index].get('bullets', [])
        
        # 计算每个 bullet 的分数
        scored_bullets = []
        for bullet in bullets:
            score = self.score_bullet_relevance(bullet, job_keywords, target_role)
            scored_bullets.append((score, bullet['content']))
        
        # 按分数排序，取前 N 个
        scored_bullets.sort(key=lambda x: x[0], reverse=True)
        
        return [content for score, content in scored_bullets[:max_bullets]]


class ResumeGenerator:
    """Toni 风格简历生成器"""
    
    def __init__(self, template_path: str = "templates/resume_toni_v4.html",
                 library_path: str = "assets/bullet_library_simple.yaml",
                 config_path: str = "config/resume_generation.yaml"):
        self.template_path = Path(template_path)
        self.library = BulletLibrary(library_path)
        self.config = self._load_config(config_path)
        self.template = self._load_template()
    
    def _load_config(self, config_path: str) -> Dict:
        """加载生成配置"""
        path = Path(config_path)
        if not path.exists():
            # 尝试其他路径
            alt_paths = [
                Path("job-hunter") / config_path,
                Path("workspace/job-hunter") / config_path,
            ]
            for p in alt_paths:
                if p.exists():
                    path = p
                    break
        
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}
    
    def _load_template(self) -> Template:
        """加载 Jinja2 模板"""
        # 尝试多个路径
        paths_to_try = [
            self.template_path,
            Path("job-hunter") / self.template_path,
            Path("workspace/job-hunter") / self.template_path,
        ]
        
        for path in paths_to_try:
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return Template(f.read())
        
        raise FileNotFoundError(f"Template not found: {self.template_path}")
    
    def generate(self, config: ResumeConfig) -> str:
        """
        生成定制简历
        
        Args:
            config: 简历配置
        
        Returns:
            HTML 字符串
        """
        # 获取个人信息
        personal_info = self.library.get_personal_info()
        
        # 提取职位关键词
        job_keywords = config.job_description.get_keywords()
        print(f"Detected keywords: {job_keywords}")
        
        # 构建模板数据
        template_data = self._build_template_data(
            personal_info, config, job_keywords
        )
        
        # 渲染模板
        html = self.template.render(**template_data)
        
        return html
    
    def _build_template_data(self, personal_info: Dict, config: ResumeConfig,
                            job_keywords: List[str]) -> Dict:
        """构建模板数据"""
        
        # 1. 基本信息
        data = {
            'name': personal_info.get('name', 'Fei Huang'),
            'location': personal_info.get('resume_location', 'Amsterdam, Netherlands'),
            'phone': personal_info.get('phone', '+31 645 038 614'),
            'email': personal_info.get('email', 'huangf06@gmail.com'),
            'linkedin': personal_info.get('linkedin', 'https://linkedin.com/in/huangf06'),
            'linkedin_display': 'linkedin.com/in/huangf06',
            'github': personal_info.get('github', 'https://github.com/huangf06'),
            'github_display': 'github.com/huangf06',
        }
        
        # 2. Bio / Summary
        data['bio'] = self._generate_bio(config, job_keywords)
        
        # 3. 教育背景
        data.update(self._build_education_data())
        
        # 4. 工作经历（智能选择 bullets）
        data['experiences'] = self._build_experiences(config, job_keywords)
        
        # 5. Career Note
        data['career_note'] = self._generate_career_note(config)
        
        # 6. 项目
        data['projects'] = self._build_projects(config, job_keywords)
        
        # 7. 技能
        data['skills'] = self._build_skills(config, job_keywords)
        
        # 8. 语言
        data['languages'] = self._build_languages(personal_info)
        
        return data
    
    def _generate_bio(self, config: ResumeConfig, job_keywords: List[str]) -> str:
        """生成 Bio / Summary"""
        role = config.target_role
        company = config.job_description.company
        
        # 角色模板
        bio_templates = {
            'data_engineer': {
                'core': "Data Engineer with expertise in building scalable data platforms and ETL pipelines",
                'skills': "Python, PySpark, Databricks, and cloud technologies",
                'highlight': "Hands-on experience designing data infrastructure and optimizing pipeline performance"
            },
            'ml_engineer': {
                'core': "Machine Learning Engineer with strong foundation in ML pipeline development and model deployment",
                'skills': "Python, PyTorch, and MLOps tools",
                'highlight': "experience building end-to-end ML systems from research to production"
            },
            'data_scientist': {
                'core': "Data Scientist with expertise in statistical modeling and machine learning",
                'skills': "Python, statistical analysis, and ML frameworks",
                'highlight': "track record of translating complex data into actionable business insights"
            },
            'quant': {
                'core': "Quantitative Researcher with deep expertise in systematic trading strategies and alpha research",
                'skills': "Python, statistical modeling, and backtesting frameworks",
                'highlight': "hands-on experience developing and deploying quantitative trading strategies"
            },
            'data_analyst': {
                'core': "Data Analyst with strong analytical skills and business acumen",
                'skills': "SQL, Python, and data visualization",
                'highlight': "experience driving data-informed decision making across organizations"
            }
        }
        
        template = bio_templates.get(role, bio_templates['data_scientist'])
        
        # 根据关键词调整 - 避免重复
        skills = template['skills']
        
        # 处理 Databricks/PySpark 逻辑
        if 'databricks' in job_keywords:
            # 替换为 Databricks/PySpark（无论是否提到 pyspark）
            skills = skills.replace('PySpark', 'Databricks/PySpark')
            # 移除可能的重复
            skills = skills.replace('Databricks/PySpark, Databricks', 'Databricks/PySpark')
        
        # 处理 cloud environments
        if 'aws' in job_keywords or 'azure' in job_keywords or 'gcp' in job_keywords:
            if 'cloud' not in skills:
                skills += " in cloud environments"
        
        bio = f"{template['core']}. Skilled in {skills}. {template['highlight']}. M.Sc. in AI from VU Amsterdam. Seeking to contribute to {company}."
        
        return bio
    
    def _build_education_data(self) -> Dict:
        """构建教育背景数据"""
        edu = self.library.get_education()
        master = edu.get('master', {})
        bachelor = edu.get('bachelor', {})
        
        return {
            'edu_master_school': master.get('school', 'Vrije Universiteit Amsterdam'),
            'edu_master_location': master.get('location', 'Amsterdam'),
            'edu_master_degree': master.get('degree', 'M.Sc. in Artificial Intelligence'),
            'edu_master_date': master.get('date', 'Sep 2023 – Aug 2025'),
            'edu_master_note': master.get('note', ''),
            
            'edu_bachelor_school': bachelor.get('school', 'Tsinghua University'),
            'edu_bachelor_location': bachelor.get('location', 'Beijing'),
            'edu_bachelor_degree': bachelor.get('degree', 'B.Eng. in Industrial Engineering'),
            'edu_bachelor_date': bachelor.get('date', 'Sep 2006 – Jul 2010'),
            
            'certification': edu.get('certification', ''),
        }
    
    def _build_experiences(self, config: ResumeConfig, job_keywords: List[str]) -> List[Dict]:
        """构建工作经历（智能选择 bullets）"""
        experiences = []
        
        # 获取所有经历
        all_experiences = self.library.get_experiences()
        
        for idx, exp in enumerate(all_experiences):
            # 获取 title（根据角色类型选择）
            titles = exp.get('titles', {})
            title = titles.get(config.target_role, titles.get('default', 'Data Scientist'))
            
            # 智能选择 bullets
            bullets = self.library.select_best_bullets(
                idx, job_keywords, config.target_role, 
                max_bullets=config.max_bullets_per_exp
            )
            
            if bullets:  # 只添加有 bullets 的经历
                experiences.append({
                    'company': exp.get('company', ''),
                    'location': exp.get('location', ''),
                    'title': title,
                    'date': exp.get('period', ''),
                    'bullets': bullets,
                })
        
        return experiences
    
    def _generate_career_note(self, config: ResumeConfig) -> Optional[str]:
        """生成 Career Note"""
        if not config.include_career_note:
            return None
        
        return self.library.get_career_note()
    
    def _build_projects(self, config: ResumeConfig, job_keywords: List[str]) -> List[Dict]:
        """构建项目经历"""
        if not config.include_projects:
            return []
        
        projects = []
        all_projects = self.library.get_projects()
        
        for proj in all_projects:
            proj_bullets = proj.get('bullets', [])
            
            # 根据角色和关键词筛选 bullets
            scored_bullets = []
            for bullet in proj_bullets:
                score = self.library.score_bullet_relevance(bullet, job_keywords, config.target_role)
                scored_bullets.append((score, bullet['content']))
            
            scored_bullets.sort(key=lambda x: x[0], reverse=True)
            selected_bullets = [content for score, content in scored_bullets[:2]]
            
            if selected_bullets:
                projects.append({
                    'name': proj.get('name', ''),
                    'date': proj.get('date', ''),
                    'bullets': selected_bullets,
                })
        
        return projects
    
    def _build_skills(self, config: ResumeConfig, job_keywords: List[str]) -> List[Dict]:
        """构建技能列表"""
        skills = self.library.get_skills()
        
        # 根据角色调整 ML & Statistics
        if config.target_role == 'quant':
            for skill in skills:
                if skill['category'] == 'ML & Statistics':
                    skill['skills_list'] = 'Statistical Modeling, Backtesting, Factor Research, Time Series Analysis, XGBoost, LightGBM'
                    break
        
        return skills
    
    def _build_languages(self, personal_info: Dict) -> List[Dict]:
        """构建语言列表"""
        return self.library.get_languages()
    
    def save(self, html: str, company: str, title: str, output_dir: str = 'output') -> Path:
        """
        保存 HTML 文件
        
        Returns:
            保存的文件路径
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名: Fei_Huang_[Role]_[Company].html
        safe_company = re.sub(r'[^\w\-]', '_', company.lower())[:20]
        safe_title = re.sub(r'[^\w\-]', '_', title.lower())[:20]
        
        filename = f"Fei_Huang_{safe_title}_{safe_company}.html"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Saved HTML to: {filepath}")
        return filepath
    
    async def to_pdf(self, html_path: Path, output_path: Path = None) -> Path:
        """
        HTML 转 PDF
        
        Returns:
            PDF 文件路径
        """
        from playwright.async_api import async_playwright
        
        if output_path is None:
            output_path = html_path.with_suffix('.pdf')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            await page.goto(f"file:///{html_path.resolve()}")
            await page.wait_for_load_state("networkidle")
            
            await page.pdf(
                path=str(output_path),
                format='A4',
                margin={
                    "top": "0.55in",
                    "right": "0.55in",
                    "bottom": "0.55in",
                    "left": "0.55in",
                },
                print_background=True
            )
            
            await browser.close()
        
        print(f"Saved PDF to: {output_path}")
        return output_path


# ============== 使用示例 ==============

async def main():
    """测试生成器"""
    generator = ResumeGenerator()
    
    # 测试职位
    job = JobDescription(
        title="Data Engineer",
        company="Picnic",
        description="""
        We are looking for a Data Engineer to join our team.
        Requirements: Python, PySpark, Databricks, SQL, AWS
        Experience with data pipelines and ETL processes.
        """
    )
    
    config = ResumeConfig(
        target_role="data_engineer",
        company="Picnic",
        job_description=job,
        max_bullets_per_exp=3,
    )
    
    # 生成简历
    html = generator.generate(config)
    
    # 保存 HTML
    html_path = generator.save(html, "Picnic", "Data_Engineer")
    
    # 生成 PDF
    pdf_path = await generator.to_pdf(html_path)
    
    print(f"\nGenerated resume:")
    print(f"  HTML: {html_path}")
    print(f"  PDF:  {pdf_path}")


if __name__ == "__main__":
    asyncio.run(main())
