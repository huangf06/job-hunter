"""
Content Engine - 内容引擎
根据角色模板智能选择和定制简历内容
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ResumeContent:
    """简历内容数据类"""
    bio: str
    experiences: List[Dict]
    projects: List[Dict]
    skills: List[Dict]
    education: Dict
    personal_info: Dict
    career_note: Optional[str]


class ContentEngine:
    """内容引擎 - 基于角色模板智能选择内容"""
    
    def __init__(self, 
                 library_path: str = "assets/bullet_library_simple.yaml",
                 config_path: str = "config/role_templates.yaml"):
        """初始化内容引擎"""
        self.library_path = Path(library_path)
        self.config_path = Path(config_path)
        
        # 加载内容库和配置
        self.library = self._load_yaml(self.library_path)
        self.config = self._load_yaml(self.config_path)
        
        # 模板配置
        self.templates = self.config.get('templates', {})
        self.bullet_scoring = self.config.get('bullet_scoring', {})
    
    def _load_yaml(self, path: Path) -> Dict:
        """加载 YAML 文件"""
        if not path.exists():
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
    
    def generate_content(self, role: str, company: str, jd_keywords: List[str]) -> ResumeContent:
        """
        生成简历内容
        
        Args:
            role: 角色代码 (ml_engineer, data_engineer, etc.)
            company: 目标公司
            jd_keywords: JD 中提取的关键词
            
        Returns:
            ResumeContent: 完整的简历内容
        """
        template_config = self.templates.get(role, {})
        
        return ResumeContent(
            bio=self._generate_bio(role, company, template_config),
            experiences=self._select_experiences(role, template_config, jd_keywords),
            projects=self._select_projects(role, template_config, jd_keywords),
            skills=self._build_skills(role, template_config),
            education=self._build_education(),
            personal_info=self._build_personal_info(),
            career_note=self._get_career_note(role)
        )
    
    def _generate_bio(self, role: str, company: str, template_config: Dict) -> str:
        """生成 Bio"""
        bio_template = template_config.get('bio_template', {})
        
        core = bio_template.get('core', f"{role.replace('_', ' ').title()} with strong technical background")
        skills = bio_template.get('skills', "Python, SQL, and data tools")
        highlight = bio_template.get('highlight', "Experience delivering impactful results")
        
        bio = f"{core}. Skilled in {skills}. {highlight}. M.Sc. in AI from VU Amsterdam. Seeking to contribute to {company}."
        
        # 长度限制
        max_len = self.config.get('generation', {}).get('bio_max_length', 300)
        if len(bio) > max_len:
            bio = bio[:max_len-3] + "..."
        
        return bio
    
    def _select_experiences(self, role: str, template_config: Dict, jd_keywords: List[str]) -> List[Dict]:
        """选择并排序工作经历"""
        # 获取经历顺序
        exp_order = template_config.get('experience_order', ['glp', 'baiquan', 'eleme'])
        title_mapping = template_config.get('title_mapping', {})
        max_bullets = template_config.get('max_bullets_per_exp', 3)
        highlight_keywords = template_config.get('highlight_keywords', [])
        
        # 从内容库获取所有经历
        all_exps = self.library.get('experiences', [])
        exp_map = {}
        for exp in all_exps:
            company = exp.get('company', '').lower()
            # 生成多个可能的 key
            keys = [
                company.replace(' ', '_').replace('.', '').replace('(', '').replace(')', ''),
                company.split()[0] if ' ' in company else company,  # 首单词
            ]
            for key in keys:
                exp_map[key] = exp
        
        selected_exps = []
        
        for exp_key in exp_order:
            if exp_key not in exp_map:
                continue
                
            exp = exp_map[exp_key]
            company_name = exp.get('company', '')
            location = exp.get('location', '')
            
            # 获取该经历的标题
            title = title_mapping.get(exp_key, exp.get('titles', {}).get('default', 'Data Scientist'))
            
            # 选择 bullets
            bullets = self._select_bullets(
                exp.get('bullets', []),
                role,
                jd_keywords,
                highlight_keywords,
                max_bullets
            )
            
            if bullets:
                selected_exps.append({
                    'company': company_name,
                    'location': location,
                    'title': title,
                    'date': exp.get('period', ''),
                    'bullets': bullets
                })
        
        return selected_exps
    
    def _select_bullets(self, bullets: List[Dict], role: str, jd_keywords: List[str], 
                       highlight_keywords: List[str], max_bullets: int) -> List[str]:
        """智能选择 bullets"""
        if not bullets:
            return []
        
        scored = []
        
        for bullet in bullets:
            score = 0.0
            content = bullet.get('content', '').lower()
            
            # 1. 角色匹配
            role_fit = bullet.get('role_fit', [])
            if role in role_fit:
                score += self.bullet_scoring.get('role_match_weight', 5.0)
            elif any(r in role_fit for r in self._get_related_roles(role)):
                score += 2.5
            
            # 2. 高亮关键词匹配 (模板特定)
            for kw in highlight_keywords:
                if kw.lower() in content:
                    score += 1.0
            
            # 3. JD 关键词匹配
            for kw in jd_keywords:
                if kw.lower() in content:
                    score += self.bullet_scoring.get('keyword_match_weight', 0.5)
            
            # 4. 技术栈匹配
            tech_stack = bullet.get('tech', [])
            for tech in tech_stack:
                if tech.lower() in [k.lower() for k in jd_keywords]:
                    score += self.bullet_scoring.get('tech_match_weight', 0.5)
            
            scored.append((score, bullet.get('content', '')))
        
        # 按分数排序并选择前 N 个
        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for score, content in scored[:max_bullets]]
    
    def _select_projects(self, role: str, template_config: Dict, jd_keywords: List[str]) -> List[Dict]:
        """选择项目"""
        project_selection = template_config.get('project_selection', [])
        max_projects = self.config.get('generation', {}).get('max_projects', 2)
        max_bullets = self.config.get('generation', {}).get('max_bullets_per_project', 2)
        
        all_projects = self.library.get('projects', [])
        project_map = {proj.get('id', proj.get('name', '').lower().replace(' ', '_')): proj 
                      for proj in all_projects}
        
        selected_projects = []
        
        for proj_id in project_selection[:max_projects]:
            if proj_id not in project_map:
                continue
                
            proj = project_map[proj_id]
            proj_bullets = proj.get('bullets', [])
            
            # 评分并选择 bullets
            scored = []
            for bullet in proj_bullets:
                score = 0.0
                role_fit = bullet.get('role_fit', [])
                
                if role in role_fit:
                    score += 3.0
                
                content = bullet.get('content', '').lower()
                for kw in jd_keywords:
                    if kw.lower() in content:
                        score += 0.5
                
                scored.append((score, bullet.get('content', '')))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            selected_bullets = [content for score, content in scored[:max_bullets]]
            
            if selected_bullets:
                selected_projects.append({
                    'name': proj.get('name', ''),
                    'date': proj.get('date', ''),
                    'bullets': selected_bullets
                })
        
        return selected_projects
    
    def _build_skills(self, role: str, template_config: Dict) -> List[Dict]:
        """构建技能列表"""
        skills_structure = template_config.get('skills_structure', [])
        
        # 如果配置中有预定义的技能结构，转换为正确格式
        if skills_structure:
            formatted_skills = []
            for skill in skills_structure:
                formatted_skills.append({
                    'category': skill.get('category', ''),
                    'skills_list': skill.get('items', '')
                })
            return formatted_skills
        
        # 否则从内容库加载并转换格式
        library_skills = self.library.get('skills', [])
        formatted_skills = []
        for skill in library_skills:
            formatted_skills.append({
                'category': skill.get('category', ''),
                'items': skill.get('skills_list', '')
            })
        return formatted_skills
    
    def _build_education(self) -> Dict:
        """构建教育信息"""
        edu = self.library.get('education', {})
        master = edu.get('master', {})
        bachelor = edu.get('bachelor', {})
        
        return {
            'master': master,
            'bachelor': bachelor,
            'certification': edu.get('certification', '')
        }
    
    def _build_personal_info(self) -> Dict:
        """构建个人信息"""
        return self.library.get('personal_info', {})
    
    def _get_career_note(self, role: str) -> Optional[str]:
        """获取 career note"""
        # Quant 角色可能需要不同的 career note
        return self.library.get('career_note', '')
    
    def _get_related_roles(self, role: str) -> List[str]:
        """获取相关角色 (用于 bullet 匹配)"""
        role_relations = {
            'ml_engineer': ['data_scientist', 'data_engineer'],
            'data_engineer': ['ml_engineer', 'data_scientist'],
            'data_scientist': ['ml_engineer', 'data_engineer', 'data_analyst'],
            'quant': ['data_scientist'],
            'data_analyst': ['data_scientist']
        }
        return role_relations.get(role, [])


# ============== 测试 ==============

def test_content_engine():
    """测试内容引擎"""
    engine = ContentEngine()
    
    print("="*70)
    print("Content Engine Test")
    print("="*70)
    
    test_cases = [
        ("ml_engineer", "Picnic", ["pytorch", "mlops", "docker"]),
        ("data_engineer", "ABN AMRO", ["spark", "databricks", "etl"]),
        ("data_scientist", "Booking.com", ["statistics", "a/b testing"]),
        ("quant", "Optiver", ["backtesting", "alpha"]),
    ]
    
    for role, company, keywords in test_cases:
        print(f"\n{'='*70}")
        print(f"Role: {role} | Company: {company}")
        print(f"Keywords: {', '.join(keywords)}")
        print("="*70)
        
        content = engine.generate_content(role, company, keywords)
        
        print(f"\nBio:\n  {content.bio[:100]}...")
        
        print(f"\nExperiences ({len(content.experiences)}):")
        for exp in content.experiences:
            print(f"  • {exp['title']} @ {exp['company']}")
            print(f"    Bullets: {len(exp['bullets'])}")
        
        print(f"\nProjects ({len(content.projects)}):")
        for proj in content.projects:
            print(f"  • {proj['name']}")
        
        print(f"\nSkills ({len(content.skills)} categories):")
        for skill in content.skills:
            print(f"  • {skill.get('category', 'N/A')}")


if __name__ == "__main__":
    test_content_engine()
