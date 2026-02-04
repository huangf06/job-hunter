"""
简历生成器 v4.1 - 支持 YAML 配置
从 config/resume_generation.yaml 读取配置
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import asyncio
from jinja2 import Template


@dataclass
class JobDescription:
    """职位描述"""
    title: str
    company: str
    description: str = ""
    
    def get_keywords(self, keyword_mappings: Dict) -> List[str]:
        """提取关键词 - 使用配置文件的映射"""
        text = f"{self.title} {self.description}".lower()
        found = []
        for category, keywords in keyword_mappings.items():
            if any(kw.lower() in text for kw in keywords):
                found.append(category)
        return found


@dataclass
class ResumeConfig:
    """简历配置"""
    target_role: str
    company: str
    job_description: JobDescription
    max_bullets_per_exp: int = 3
    include_projects: bool = True
    include_career_note: bool = True


class ConfigDrivenGenerator:
    """配置驱动的简历生成器"""
    
    def __init__(self, 
                 template_path: str = "templates/resume_toni_v4.html",
                 library_path: str = "assets/bullet_library_simple.yaml",
                 config_path: str = "config/resume_generation.yaml"):
        
        self.template_path = Path(template_path)
        self.library_path = Path(library_path)
        self.config_path = Path(config_path)
        
        # 加载所有配置
        self.library = self._load_yaml(self.library_path)
        self.config = self._load_yaml(self.config_path)
        
        # 加载模板
        self.template = self._load_template()
    
    def _load_yaml(self, path: Path) -> Dict:
        """加载 YAML 文件"""
        if not path.exists():
            # 尝试其他路径
            alt_paths = [
                Path("job-hunter") / path,
                Path("workspace/job-hunter") / path,
            ]
            for p in alt_paths:
                if p.exists():
                    path = p
                    break
        
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}
    
    def _load_template(self) -> Template:
        """加载 Jinja2 模板"""
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
    
    def generate(self, resume_config: ResumeConfig) -> str:
        """生成简历"""
        # 获取关键词映射
        keyword_mappings = self.config.get('keyword_mappings', {})
        job_keywords = resume_config.job_description.get_keywords(keyword_mappings)
        print(f"Detected keywords: {job_keywords}")
        
        # 构建数据
        data = self._build_data(resume_config, job_keywords)
        
        # 渲染
        return self.template.render(**data)
    
    def _build_data(self, config: ResumeConfig, job_keywords: List[str]) -> Dict:
        """构建模板数据"""
        personal_info = self.library.get('personal_info', {})
        
        return {
            'name': personal_info.get('name', 'Fei Huang'),
            'location': personal_info.get('resume_location', 'Amsterdam, Netherlands'),
            'phone': personal_info.get('phone', '+31 645 038 614'),
            'email': personal_info.get('email', 'huangf06@gmail.com'),
            'linkedin': personal_info.get('linkedin', 'https://linkedin.com/in/huangf06'),
            'linkedin_display': 'linkedin.com/in/huangf06',
            'github': personal_info.get('github', 'https://github.com/huangf06'),
            'github_display': 'github.com/huangf06',
            'bio': self._generate_bio(config, job_keywords),
            **self._build_education(),
            'experiences': self._build_experiences(config, job_keywords),
            'career_note': self._get_career_note(config),
            'projects': self._build_projects(config, job_keywords),
            'skills': self._build_skills(config),
            'languages': self.library.get('languages', []),
        }
    
    def _generate_bio(self, config: ResumeConfig, job_keywords: List[str]) -> str:
        """生成 Bio - 从配置文件读取"""
        role = config.target_role
        company = config.job_description.company
        
        # 从配置获取角色模板
        roles_config = self.config.get('roles', {})
        role_config = roles_config.get(role, {})
        template = role_config.get('bio_template', {})
        
        if not template:
            # 默认
            template = {
                'core': f"{role.replace('_', ' ').title()} with strong technical background",
                'skills': "Python, SQL, and data tools",
                'highlight': "Experience delivering impactful results"
            }
        
        skills = template.get('skills', "Python, SQL")
        
        # 处理 Databricks/PySpark
        if 'databricks' in job_keywords:
            skills = skills.replace('PySpark', 'Databricks/PySpark')
            skills = skills.replace('Databricks/PySpark, Databricks', 'Databricks/PySpark')
        
        # 处理 cloud
        if any(k in job_keywords for k in ['aws', 'azure', 'gcp']):
            if 'cloud' not in skills:
                skills += " in cloud environments"
        
        bio = f"{template.get('core', '')}. Skilled in {skills}. {template.get('highlight', '')}. M.Sc. in AI from VU Amsterdam. Seeking to contribute to {company}."
        
        # 长度限制
        max_len = self.config.get('generation', {}).get('bio_max_length', 300)
        if len(bio) > max_len:
            bio = bio[:max_len-3] + "..."
        
        return bio
    
    def _build_education(self) -> Dict:
        """构建教育数据"""
        edu = self.library.get('education', {})
        master = edu.get('master', {})
        bachelor = edu.get('bachelor', {})
        
        return {
            'edu_master_school': master.get('school', ''),
            'edu_master_location': master.get('location', ''),
            'edu_master_degree': master.get('degree', ''),
            'edu_master_date': master.get('date', ''),
            'edu_master_note': master.get('note', ''),
            'edu_bachelor_school': bachelor.get('school', ''),
            'edu_bachelor_location': bachelor.get('location', ''),
            'edu_bachelor_degree': bachelor.get('degree', ''),
            'edu_bachelor_date': bachelor.get('date', ''),
            'certification': edu.get('certification', ''),
        }
    
    def _build_experiences(self, config: ResumeConfig, job_keywords: List[str]) -> List[Dict]:
        """构建工作经历"""
        experiences = []
        all_exps = self.library.get('experiences', [])
        
        # 获取角色配置
        roles_config = self.config.get('roles', {})
        role_config = roles_config.get(config.target_role, {})
        title_mapping = role_config.get('title_mapping', {})
        
        for idx, exp in enumerate(all_exps):
            # 获取 title
            default_title = exp.get('titles', {}).get('default', 'Data Scientist')
            title = title_mapping.get(exp.get('company', '').lower().replace(' ', '_').replace('.', ''), default_title)
            
            # 选择 bullets
            bullets = self._select_bullets(exp, job_keywords, config.target_role, 
                                          config.max_bullets_per_exp)
            
            if bullets:
                experiences.append({
                    'company': exp.get('company', ''),
                    'location': exp.get('location', ''),
                    'title': title,
                    'date': exp.get('period', ''),
                    'bullets': bullets,
                })
        
        return experiences
    
    def _select_bullets(self, exp: Dict, job_keywords: List[str], target_role: str, max_bullets: int) -> List[str]:
        """选择最相关的 bullets"""
        bullets = exp.get('bullets', [])
        if not bullets:
            return []
        
        scored = []
        for bullet in bullets:
            score = 0.0
            role_fit = bullet.get('role_fit', [])
            tech = bullet.get('tech', [])
            content = bullet.get('content', '').lower()
            
            # 角色匹配
            if target_role in role_fit:
                score += 3.0
            elif any(r in role_fit for r in ['data_scientist', 'data_engineer', 'ml_engineer']):
                score += 1.5
            
            # 技术匹配
            matching_tech = sum(1 for t in job_keywords if t.lower() in [x.lower() for x in tech])
            score += min(3.0, matching_tech * 1.0)
            
            # 关键词匹配
            keyword_matches = sum(1 for kw in job_keywords if kw.lower() in content)
            score += min(2.0, keyword_matches * 0.5)
            
            scored.append((score, bullet['content']))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for score, content in scored[:max_bullets]]
    
    def _get_career_note(self, config: ResumeConfig) -> Optional[str]:
        """获取 career note"""
        if not config.include_career_note:
            return None
        return self.library.get('career_note', '')
    
    def _build_projects(self, config: ResumeConfig, job_keywords: List[str]) -> List[Dict]:
        """构建项目"""
        if not config.include_projects:
            return []
        
        projects = []
        all_projects = self.library.get('projects', [])
        max_projects = self.config.get('generation', {}).get('max_projects', 3)
        max_bullets = self.config.get('generation', {}).get('max_bullets_per_project', 2)
        
        for proj in all_projects[:max_projects]:
            proj_bullets = proj.get('bullets', [])
            
            scored = []
            for bullet in proj_bullets:
                score = 0.0
                role_fit = bullet.get('role_fit', [])
                
                if config.target_role in role_fit:
                    score += 3.0
                
                content = bullet.get('content', '').lower()
                keyword_matches = sum(1 for kw in job_keywords if kw.lower() in content)
                score += min(2.0, keyword_matches * 0.5)
                
                scored.append((score, bullet['content']))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            selected = [content for score, content in scored[:max_bullets]]
            
            if selected:
                projects.append({
                    'name': proj.get('name', ''),
                    'date': proj.get('date', ''),
                    'bullets': selected,
                })
        
        return projects
    
    def _build_skills(self, config: ResumeConfig) -> List[Dict]:
        """构建技能列表"""
        skills = self.library.get('skills', [])
        
        # 应用角色特定的调整
        roles_config = self.config.get('roles', {})
        role_config = roles_config.get(config.target_role, {})
        adjustments = role_config.get('skill_adjustments', {})
        
        for skill in skills:
            category = skill.get('category', '').replace(' ', '_').replace('&', '_')
            if category in adjustments:
                skill['skills_list'] = adjustments[category]
        
        return skills
    
    def save(self, html: str, company: str, title: str, output_dir: str = 'output') -> Path:
        """保存 HTML"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        safe_company = re.sub(r'[^\w\-]', '_', company.lower())[:20]
        safe_title = re.sub(r'[^\w\-]', '_', title.lower())[:20]
        
        filename = f"Fei_Huang_{safe_title}_{safe_company}.html"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"Saved HTML to: {filepath}")
        return filepath
    
    async def to_pdf(self, html_path: Path, output_path: Path = None) -> Path:
        """转换为 PDF"""
        from playwright.async_api import async_playwright
        
        if output_path is None:
            output_path = html_path.with_suffix('.pdf')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file:///{html_path.resolve()}")
            await page.wait_for_load_state("networkidle")
            
            # 使用配置中的样式
            style = self.config.get('template_style', {})
            margin = style.get('margin', '0.55in')
            
            await page.pdf(
                path=str(output_path),
                format=style.get('page_size', 'A4'),
                margin={"top": margin, "right": margin, "bottom": margin, "left": margin},
                print_background=True
            )
            await browser.close()
        
        print(f"Saved PDF to: {output_path}")
        return output_path


# ============== 使用示例 ==============

async def main():
    """测试"""
    generator = ConfigDrivenGenerator()
    
    job = JobDescription(
        title="Data Engineer",
        company="Picnic",
        description="Python, PySpark, Databricks, SQL, AWS"
    )
    
    config = ResumeConfig(
        target_role="data_engineer",
        company="Picnic",
        job_description=job,
        max_bullets_per_exp=3,
    )
    
    html = generator.generate(config)
    html_path = generator.save(html, "Picnic", "Data_Engineer")
    pdf_path = await generator.to_pdf(html_path)
    
    print(f"\nGenerated:")
    print(f"  HTML: {html_path}")
    print(f"  PDF:  {pdf_path}")


if __name__ == "__main__":
    asyncio.run(main())
