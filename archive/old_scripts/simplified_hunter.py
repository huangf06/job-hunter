"""
Simplified Job Hunter - 90%自动化系统
=====================================

核心理念: 自动化能自动化的，人工处理关键的

流程:
1. 爬取职位 (自动)
2. 硬性筛选 (自动) 
3. AI评分 (自动)
4. 生成简历 (自动)
5. 人工审阅 (5-10分钟/天)
6. 辅助投递 (半自动)

Usage:
    python simplified_hunter.py daily      # 运行每日流程
    python simplified_hunter.py review     # 审阅待处理职位
    python simplified_hunter.py stats      # 查看统计
"""

import json
import re
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 项目路径
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
ASSETS_DIR = PROJECT_ROOT / "assets"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))

# 确保目录存在
for d in [DATA_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================================
# 配置
# ============================================================================

class Config:
    """系统配置"""
    
    # 评分阈值
    MIN_SCORE_TO_GENERATE = 6.0  # 生成简历的最低分数
    MIN_SCORE_TO_REVIEW = 7.0    # 推荐审阅的最低分数
    
    # 每日限制
    MAX_JOBS_TO_REVIEW = 10      # 每天最多审阅数量
    
    # 文件路径
    PENDING_FILE = DATA_DIR / "jobs_pending.json"
    APPLIED_FILE = DATA_DIR / "jobs_applied.json"
    BULLET_LIBRARY = ASSETS_DIR / "bullet_library.yaml"
    RESUME_TEMPLATE = TEMPLATES_DIR / "resume_master.html"


# ============================================================================
# 数据模型
# ============================================================================

class Job:
    """职位数据模型"""
    
    def __init__(self, data: Dict):
        self.id = data.get('id', '')
        self.title = data.get('title', '')
        self.company = data.get('company', '')
        self.location = data.get('location', '')
        self.url = data.get('url', '')
        self.description = data.get('description', '')
        self.source = data.get('source', '')
        self.discovered_at = data.get('discovered_at', datetime.now().isoformat())
        
        # 分析结果
        self.score = data.get('score', 0)
        self.recommendation = data.get('recommendation', '')
        self.reject_reason = data.get('reject_reason', '')
        self.resume_path = data.get('resume_path', '')
        
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'title': self.title,
            'company': self.company,
            'location': self.location,
            'url': self.url,
            'description': self.description,
            'source': self.source,
            'discovered_at': self.discovered_at,
            'score': self.score,
            'recommendation': self.recommendation,
            'reject_reason': self.reject_reason,
            'resume_path': self.resume_path,
        }


# ============================================================================
# 硬性筛选
# ============================================================================

class HardFilter:
    """硬性筛选 - 0 token消耗"""
    
    # 绝对否决规则
    REJECT_PATTERNS = {
        'dutch_required': [
            r'dutch\s*(is\s*)?required',
            r'dutch\s*native',
            r'fluent\s*in\s*dutch',
            r'nederlands\s*vereist',
            r'nederlands\s*moeder.*taal',
        ],
        'german_required': [
            r'german\s*(is\s*)?required',
            r'fluent\s*in\s*german',
        ],
        'french_required': [
            r'french\s*(is\s*)?required',
            r'fluent\s*in\s*french',
        ],
        'too_senior': [
            r'10\+?\s*years?',
            r'8\+?\s*years?',
            r'15\+?\s*years?',
        ],
        'leadership_role': [
            r'^lead\s+',
            r'^principal\s+',
            r'^staff\s+',
            r'director',
            r'head\s+of',
            r'vp\s+',
            r'vice\s+president',
            r'chief\s+',
            r'c-level',
        ],
    }
    
    # 警告但不否决
    WARNING_PATTERNS = {
        'senior_title': [
            r'^senior\s+',
        ],
        'mid_experience': [
            r'5\+?\s*years?',
            r'6\+?\s*years?',
            r'7\+?\s*years?',
        ],
    }
    
    @classmethod
    def check(cls, job: Job) -> Tuple[bool, str, float]:
        """
        检查职位是否通过硬性筛选
        
        Returns:
            (passed, reason, penalty)
            passed: True = 通过
            reason: 否决原因 (如果未通过)
            penalty: 分数惩罚 (0-2)
        """
        text = f"{job.title} {job.description}".lower()
        title = job.title.lower()
        
        # 检查否决规则
        for category, patterns in cls.REJECT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False, f"{category}: {pattern}", 0
        
        # 检查警告规则 (扣分但不否决)
        penalty = 0
        for category, patterns in cls.WARNING_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    if category == 'senior_title':
                        penalty += 1  # Senior扣1分
                    else:
                        penalty += 0.5
        
        return True, "", min(penalty, 2)


# ============================================================================
# AI分析器
# ============================================================================

class AIAnalyzer:
    """AI职位分析器"""
    
    SYSTEM_PROMPT = """You are a job application assistant for a Master's graduate in AI looking for jobs in the Netherlands.

Analyze the job posting and output JSON only.

Input: Job title, company, description

Output format:
{
    "score": 0-10,
    "recommendation": "APPLY_NOW|APPLY|MAYBE|SKIP",
    "reason": "brief explanation in Chinese",
    "resume_focus": "what to emphasize in resume",
    "key_skills": ["skill1", "skill2"],
    "tailoring_notes": "specific changes for this application"
}

Scoring criteria for Fei Huang (M.Sc. AI, VU Amsterdam):
- 8-10: Perfect match, visa-friendly sponsor, strong fit for ML/Data roles
- 6-7: Good match, worth applying, likely sponsor
- 4-5: Marginal, apply if time permits
- 0-3: Poor match, skip

Important factors:
+ Sponsorship/visa-friendly companies (Booking, Adyen, ASML, banks, etc.)
+ ML/AI/Data roles matching background
+ Amsterdam/Rotterdam/Utrecht locations
+ English-speaking environment
- Dutch language requirements
- 5+ years experience requirements
- Non-technical roles"""

    @classmethod
    def analyze(cls, job: Job) -> Dict:
        """
        使用AI分析职位
        
        实际实现需要调用AI模型，这里先返回模拟结果
        TODO: 接入实际的AI调用
        """
        # 模拟分析逻辑 (基于关键词)
        title = job.title.lower()
        desc = job.description.lower()
        
        score = 5.0  # 基础分
        reasons = []
        
        # 加分项
        if any(k in title for k in ['machine learning', 'ml engineer', 'ai engineer']):
            score += 2
            reasons.append("ML职位匹配背景")
        elif 'data scientist' in title:
            score += 1.5
            reasons.append("Data Scientist匹配")
        elif 'data engineer' in title:
            score += 1.5
            reasons.append("Data Engineer匹配")
        
        if any(k in desc for k in ['python', 'pytorch', 'tensorflow']):
            score += 0.5
            
        if any(k in desc for k in ['visa', 'sponsorship', 'km visa']):
            score += 1
            reasons.append("提到签证支持")
        
        # 减分项
        if '5+' in desc or '5 years' in desc:
            score -= 1
            
        if 'senior' in title:
            score -= 0.5
        
        # 知名公司加分
        top_companies = ['booking', 'adyen', 'asml', 'philips', 'ing', 'abn', 'rabobank', 
                        'optiver', 'imc', 'flow traders', 'picnic', 'coolblue', 'bol.com']
        if any(c in job.company.lower() for c in top_companies):
            score += 0.5
            reasons.append("知名公司")
        
        score = max(0, min(10, score))
        
        recommendation = "SKIP"
        if score >= 8:
            recommendation = "APPLY_NOW"
        elif score >= 6:
            recommendation = "APPLY"
        elif score >= 4:
            recommendation = "MAYBE"
        
        return {
            "score": round(score, 1),
            "recommendation": recommendation,
            "reason": "; ".join(reasons) if reasons else "一般匹配",
            "resume_focus": cls._get_resume_focus(title),
            "key_skills": cls._get_key_skills(title),
            "tailoring_notes": "根据职位调整强调重点"
        }
    
    @classmethod
    def _get_resume_focus(cls, title: str) -> str:
        if 'machine learning' in title or 'ml' in title:
            return "强调ML模型开发和部署经验"
        elif 'data engineer' in title:
            return "强调数据管道和ETL经验"
        elif 'data scientist' in title:
            return "强调数据分析和建模能力"
        elif 'quant' in title:
            return "强调量化研究和交易系统经验"
        return "强调ML和数据工程综合背景"
    
    @classmethod
    def _get_key_skills(cls, title: str) -> List[str]:
        if 'machine learning' in title or 'ml' in title:
            return ["Python", "PyTorch", "ML Systems"]
        elif 'data engineer' in title:
            return ["Python", "SQL", "Spark"]
        elif 'data scientist' in title:
            return ["Python", "Statistics", "ML"]
        return ["Python", "Machine Learning", "SQL"]


# ============================================================================
# 简历生成器
# ============================================================================

class ResumeGenerator:
    """简历生成器"""
    
    def __init__(self):
        self.template_path = Config.RESUME_TEMPLATE
        self.bullet_path = Config.BULLET_LIBRARY
    
    def generate(self, job: Job, analysis: Dict) -> Optional[Path]:
        """生成定制简历"""
        if not self.template_path.exists():
            print(f"[ERROR] Template not found: {self.template_path}")
            return None
        
        # 读取模板
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 定制内容
        html = self._tailor_content(template, job, analysis)
        
        # 保存HTML
        safe_company = re.sub(r'[^\w\-]', '_', job.company)[:20]
        safe_title = re.sub(r'[^\w\-]', '_', job.title)[:30]
        html_path = OUTPUT_DIR / f"{safe_company}_{safe_title}.html"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # 生成PDF
        pdf_path = self._generate_pdf(html_path, job)
        
        return pdf_path
    
    def _tailor_content(self, template: str, job: Job, analysis: Dict) -> str:
        """根据职位定制模板内容 - 适配 resume_master.html"""
        title = job.title.lower()
        company = job.company
        
        # 根据职位类型选择角色定位和关键词
        if 'machine learning' in title or 'ml engineer' in title:
            role = "Machine Learning Engineer"
            expertise = "developing and deploying ML models at scale, with production experience in recommendation systems and forecasting"
            skills = "PyTorch, TensorFlow, Python, and ML systems"
        elif 'data engineer' in title or 'data platform' in title:
            role = "Data Engineer"
            expertise = "building scalable data platforms and ETL pipelines"
            skills = "Python, SQL, PySpark, Databricks, and cloud technologies"
        elif 'quant' in title or 'quantitative' in title:
            role = "Quantitative Researcher"
            expertise = "quantitative research, factor modeling, and trading systems"
            skills = "Python, statistical modeling, backtesting, and time series analysis"
        elif 'data scientist' in title:
            role = "Data Scientist"
            expertise = "machine learning, statistical modeling, and data-driven decision making"
            skills = "Python, ML/Statistics, A/B testing, and data analysis"
        elif 'software engineer' in title or 'ai engineer' in title:
            role = "AI Software Engineer"
            expertise = "building AI-powered applications and production ML systems"
            skills = "Python, ML frameworks, and software engineering"
        else:
            role = "Data professional"
            expertise = "machine learning, data engineering, and quantitative analysis"
            skills = "Python, Machine Learning, SQL"
        
        # 构建定制化的 Bio
        bio = f"{role} with expertise in {expertise}. Skilled in {skills}. M.Sc. in AI from VU Amsterdam. Seeking to contribute to {company}."
        
        # 替换模板中的 Bio 部分 (resume_master.html 中的 bio div 内容)
        import re
        # 匹配 <div class="bio">...</div> 中的内容
        bio_pattern = r'(<div class="bio">)[^<]*([^<]*(?:<[^/][^>]*>[^<]*</[^>]+>)?[^<]*)*(</div>)'
        
        # 简单的字符串替换方式 - 找到 bio div 并替换内容
        html = template
        
        # 查找 bio div 的开始和结束
        bio_start = html.find('<div class="bio">')
        if bio_start != -1:
            bio_content_start = bio_start + len('<div class="bio">')
            bio_end = html.find('</div>', bio_content_start)
            if bio_end != -1:
                # 替换 bio 内容
                html = html[:bio_content_start] + '\n        ' + bio + '\n    ' + html[bio_end:]
        
        return html
    
    def _generate_pdf(self, html_path: Path, job: Job) -> Optional[Path]:
        """使用Playwright生成PDF"""
        try:
            from playwright.sync_api import sync_playwright
            
            safe_company = re.sub(r'[^\w\-]', '_', job.company)[:20]
            safe_title = re.sub(r'[^\w\-]', '_', job.title)[:30]
            output_name = f"Fei_Huang_{safe_company}_{safe_title}.pdf"
            pdf_path = OUTPUT_DIR / output_name
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.goto(f"file:///{html_path.resolve()}")
                page.pdf(
                    path=str(pdf_path),
                    format="A4",
                    margin={"top": "0.5in", "bottom": "0.5in", "left": "0.5in", "right": "0.5in"}
                )
                browser.close()
            
            return pdf_path
            
        except Exception as e:
            print(f"[ERROR] PDF generation failed: {e}")
            return None


# ============================================================================
# 数据存储
# ============================================================================

class JobStore:
    """职位数据存储"""
    
    def __init__(self):
        self.pending_file = Config.PENDING_FILE
        self.applied_file = Config.APPLIED_FILE
        self.pending = self._load_pending()
        self.applied = self._load_applied()
    
    def _load_pending(self) -> List[Dict]:
        if self.pending_file.exists():
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _load_applied(self) -> List[Dict]:
        if self.applied_file.exists():
            with open(self.applied_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def _save_pending(self):
        with open(self.pending_file, 'w', encoding='utf-8') as f:
            json.dump(self.pending, f, indent=2, ensure_ascii=False)
    
    def _save_applied(self):
        with open(self.applied_file, 'w', encoding='utf-8') as f:
            json.dump(self.applied, f, indent=2, ensure_ascii=False)
    
    def add_pending(self, job: Job):
        """添加待处理职位"""
        # 检查是否已存在
        for existing in self.pending:
            if existing.get('url') == job.url:
                return False
        
        self.pending.append(job.to_dict())
        self._save_pending()
        return True
    
    def get_pending_to_review(self, limit: int = 10) -> List[Job]:
        """获取待审阅职位 (按分数排序)"""
        # 过滤出有分数且未处理的
        to_review = [j for j in self.pending if j.get('score', 0) >= Config.MIN_SCORE_TO_REVIEW]
        # 按分数排序
        to_review.sort(key=lambda x: x.get('score', 0), reverse=True)
        return [Job(j) for j in to_review[:limit]]
    
    def mark_applied(self, job_id: str, resume_path: str = ""):
        """标记为已投递"""
        # 从pending移到applied
        for i, job in enumerate(self.pending):
            if job.get('id') == job_id:
                job['status'] = 'applied'
                job['applied_at'] = datetime.now().isoformat()
                job['resume_path'] = resume_path
                self.applied.append(job)
                self.pending.pop(i)
                self._save_pending()
                self._save_applied()
                return True
        return False
    
    def mark_skipped(self, job_id: str, reason: str = ""):
        """标记为跳过"""
        for i, job in enumerate(self.pending):
            if job.get('id') == job_id:
                job['status'] = 'skipped'
                job['skipped_at'] = datetime.now().isoformat()
                job['skip_reason'] = reason
                self.pending.pop(i)
                self._save_pending()
                return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计"""
        return {
            'pending': len(self.pending),
            'applied': len(self.applied),
            'to_review': len([j for j in self.pending if j.get('score', 0) >= Config.MIN_SCORE_TO_REVIEW]),
        }


# ============================================================================
# 主控制器
# ============================================================================

class JobHunter:
    """主控制器"""
    
    def __init__(self):
        self.store = JobStore()
        self.generator = ResumeGenerator()
    
    def process_new_job(self, job_data: Dict) -> Dict:
        """处理新职位"""
        job = Job(job_data)
        
        print(f"\n[PROCESS] {job.title} @ {job.company}")
        
        # Step 1: 硬性筛选
        passed, reason, penalty = HardFilter.check(job)
        if not passed:
            print(f"  [FILTERED] {reason}")
            return {'status': 'filtered', 'reason': reason}
        
        # Step 2: AI分析
        analysis = AIAnalyzer.analyze(job)
        job.score = analysis['score'] - penalty
        job.recommendation = analysis['recommendation']
        
        print(f"  [SCORE] {job.score}/10")
        
        # Step 3: 如果分数够高，生成简历
        if job.score >= Config.MIN_SCORE_TO_GENERATE:
            print(f"  [GENERATING] Resume...")
            resume_path = self.generator.generate(job, analysis)
            if resume_path:
                job.resume_path = str(resume_path)
                print(f"  [OK] {resume_path.name}")
            else:
                print(f"  [FAIL] Resume generation failed")
        
        # Step 4: 保存到待处理
        self.store.add_pending(job)
        
        return {
            'status': 'pending',
            'score': job.score,
            'resume_generated': bool(job.resume_path)
        }
    
    def review_mode(self):
        """审阅模式 - 人工确认"""
        jobs = self.store.get_pending_to_review(limit=Config.MAX_JOBS_TO_REVIEW)
        
        if not jobs:
            print("\n✅ 没有待审阅的高优先级职位")
            return
        
        print(f"\n{'='*70}")
        print(f"📋 待审阅职位 ({len(jobs)}个)")
        print(f"{'='*70}")
        
        for i, job in enumerate(jobs, 1):
            print(f"\n[{i}/{len(jobs)}] {job.title}")
            print(f"    公司: {job.company}")
            print(f"    地点: {job.location}")
            print(f"    评分: {job.score}/10")
            print(f"    简历: {job.resume_path or '未生成'}")
            
            # 交互式确认
            while True:
                choice = input(f"\n    [Y]投递 [N]跳过 [O]打开链接 [D]详情 [Q]退出: ").strip().lower()
                
                if choice == 'y':
                    self._apply_job(job)
                    break
                elif choice == 'n':
                    reason = input("    跳过原因 (可选): ").strip()
                    self.store.mark_skipped(job.id, reason)
                    print("    [SKIPPED]")
                    break
                elif choice == 'o':
                    webbrowser.open(job.url)
                    print(f"    [OPENED] {job.url}")
                elif choice == 'd':
                    print(f"\n    描述: {job.description[:500]}...")
                elif choice == 'q':
                    print("\n[EXIT]")
                    return
                else:
                    print("    无效输入，请重试")
        
        print(f"\n{'='*70}")
        print("✅ 审阅完成")
        print(f"{'='*70}")
    
    def _apply_job(self, job: Job):
        """执行投递"""
        print(f"\n    [APPLYING] {job.company}...")
        
        # 打开申请页面
        webbrowser.open(job.url)
        
        # 打开简历文件夹
        if job.resume_path:
            resume_path = Path(job.resume_path)
            if resume_path.exists():
                subprocess.run(['explorer', '/select,', str(resume_path)])
        
        # 标记为已投递
        self.store.mark_applied(job.id, job.resume_path)
        
        print("    [OK] 已打开申请页面和简历，请完成投递后按回车继续...")
        input()
    
    def daily_run(self):
        """每日自动运行"""
        print(f"\n{'='*70}")
        print(f"🤖 Job Hunter Daily Run - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}")
        
        # 这里应该调用爬虫获取新职位
        # 现在先用模拟数据演示
        print("\n[TODO] 调用爬虫获取新职位...")
        print("[INFO] 使用示例数据演示流程")
        
        # 示例职位
        sample_jobs = [
            {
                'id': 'test_001',
                'title': 'Machine Learning Engineer',
                'company': 'Picnic',
                'location': 'Amsterdam',
                'url': 'https://picnic.app/careers',
                'description': 'We are looking for a Machine Learning Engineer to join our team. You will work on recommendation systems and demand forecasting. Requirements: Python, PyTorch, 3+ years experience.',
                'source': 'linkedin'
            },
            {
                'id': 'test_002',
                'title': 'Senior Data Scientist',
                'company': 'Booking.com',
                'location': 'Amsterdam',
                'url': 'https://careers.booking.com',
                'description': 'As a Data Scientist, you will analyze user behavior and build ML models. English required. Visa sponsorship available.',
                'source': 'linkedin'
            },
            {
                'id': 'test_003',
                'title': 'Data Engineer',
                'company': 'Random Startup',
                'location': 'Amsterdam',
                'url': 'https://example.com',
                'description': 'Dutch required. Native level Dutch speaker needed for this role.',
                'source': 'indeed'
            }
        ]
        
        results = []
        for job_data in sample_jobs:
            result = self.process_new_job(job_data)
            results.append(result)
        
        # 打印汇总
        print(f"\n{'='*70}")
        print("📊 今日汇总")
        print(f"{'='*70}")
        
        stats = {'filtered': 0, 'pending': 0}
        for r in results:
            stats[r['status']] = stats.get(r['status'], 0) + 1
        
        print(f"  已过滤: {stats.get('filtered', 0)}")
        print(f"  待审阅: {stats.get('pending', 0)}")
        
        # 显示待审阅列表
        to_review = self.store.get_pending_to_review()
        if to_review:
            print(f"\n  高优先级职位 (≥{Config.MIN_SCORE_TO_REVIEW}分):")
            for job in to_review:
                status = "✅ 简历已生成" if job.resume_path else "⏳ 待生成"
                print(f"    [{job.score}] {job.title} @ {job.company} - {status}")
            
            print(f"\n  运行 `python simplified_hunter.py review` 开始审阅")
        
        print(f"\n{'='*70}")
    
    def show_stats(self):
        """显示统计"""
        stats = self.store.get_stats()
        
        print(f"\n{'='*50}")
        print("📈 Job Hunter 统计")
        print(f"{'='*50}")
        print(f"  待处理: {stats['pending']}")
        print(f"  待审阅: {stats['to_review']}")
        print(f"  已投递: {stats['applied']}")
        print(f"{'='*50}")


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Hunter - 90%自动化求职系统')
    parser.add_argument('command', choices=['daily', 'review', 'stats', 'test'])
    
    args = parser.parse_args()
    
    hunter = JobHunter()
    
    if args.command == 'daily':
        hunter.daily_run()
    elif args.command == 'review':
        hunter.review_mode()
    elif args.command == 'stats':
        hunter.show_stats()
    elif args.command == 'test':
        # 测试模式
        print("运行测试...")
        hunter.daily_run()
        print("\n现在进入审阅模式:")
        hunter.review_mode()


if __name__ == '__main__':
    main()
