"""
Streamlined Job Pipeline - 流式职位处理
========================================

流程: 发现职位 → 硬性筛选 → AI评分(≥6分) → 生成简历 → 投递 → 记录

Usage:
    python streamlined_pipeline.py --scrape          # 爬取+处理
    python streamlined_pipeline.py --process <file>  # 处理已有数据
    python streamlined_pipeline.py --test            # 测试模式
"""

import json
import re
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LEADS_DIR = DATA_DIR / "leads"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
ASSETS_DIR = PROJECT_ROOT / "assets"

# 确保目录存在
for d in [DATA_DIR, LEADS_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class JobResult:
    """职位处理结果"""
    job_id: str
    title: str
    company: str
    url: str
    status: str  # rejected | scored | generated | applied | error
    score: Optional[float] = None
    reject_reason: Optional[str] = None
    resume_path: Optional[str] = None
    error_msg: Optional[str] = None
    processed_at: str = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now().isoformat()


class HardFilter:
    """硬性筛选 - 一票否决（零token）"""
    
    # 否决规则（正则匹配）
    REJECT_PATTERNS = {
        "dutch_required": [
            r"dutch\s*(required|mandatory|essential|native)",
            r"nederlands\s*(verplicht|vereist)",
            r"fluent\s+in\s+dutch",
        ],
        "experience_too_high": [
            r"(10|15|20)\+?\s*years?\s*(of\s*)?experience",
            r"minimum\s*8\+?\s*years",
            r"senior.*with\s*\d{2}\+?\s*years",
        ],
        "senior_level": [
            r"\bsenior\b.*\b(manager|director|lead|architect)",
            r"\b(principal|staff|director|vp|vice president|head of)\b",
        ],
        "wrong_role": [
            r"\b(frontend|backend|fullstack|devops|sre|security)\b",
            r"\b(android|ios|mobile)\s*(developer|engineer)",
        ],
        "not_netherlands": [
            r"(onsite|on-site|office).*(only|mandatory)",
            r"no\s*(relocation|visa|sponsorship)",
        ],
    }
    
    @classmethod
    def check(cls, job: Dict) -> Tuple[bool, Optional[str]]:
        """
        硬性筛选检查
        
        Returns:
            (通过?, 否决原因)
        """
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        for rule_name, patterns in cls.REJECT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False, rule_name
        
        return True, None


class JobScorer:
    """职位评分器 - 规则+AI混合"""
    
    # 规则评分（零token）
    KEYWORD_SCORES = {
        # 正面
        "machine learning": 1.5,
        "ml engineer": 2.0,
        "data scientist": 2.0,
        "ai engineer": 2.0,
        "deep learning": 1.5,
        "python": 1.0,
        "pytorch": 1.0,
        "tensorflow": 1.0,
        "nlp": 1.0,
        "llm": 1.0,
        "quantitative": 1.5,
        "quant": 1.5,
        "junior": 1.0,
        "entry level": 1.5,
        "graduate": 1.0,
        "0-3 years": 1.5,
        "1-3 years": 1.0,
        "visa sponsor": 2.0,
        "relocation": 1.0,
        "sponsorship": 2.0,
        # 负面
        "5+ years": -0.5,
        "6+ years": -1.0,
        "7+ years": -1.5,
        "senior": -1.0,
        "lead": -1.5,
    }
    
    TARGET_COMPANIES = [
        "picnic", "adyen", "booking.com", "ing", "abn amro", "rabobank",
        "asml", "philips", "tomtom", "coolblue", "bol.com", "optiver",
        "imc", "flow traders", "shell"
    ]
    
    @classmethod
    def rule_score(cls, job: Dict) -> float:
        """规则评分（快速预估）"""
        score = 5.0  # 基础分
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        for keyword, points in cls.KEYWORD_SCORES.items():
            if keyword in text:
                score += points
        
        # 目标公司加分
        company = job.get('company', '').lower()
        for target in cls.TARGET_COMPANIES:
            if target in company:
                score += 1.5
                break
        
        return max(0, min(10, score))
    
    @classmethod
    async def ai_score(cls, job: Dict) -> Tuple[float, Dict]:
        """
        AI评分（轻量级，1次调用）
        
        Returns:
            (分数, 定制建议)
        """
        # 这里接入实际的AI评分
        # 简化版：先用规则评分
        score = cls.rule_score(job)
        
        # 生成定制建议
        title = job.get('title', '').lower()
        suggestions = {
            "role_type": "data_scientist",
            "keywords": [],
            "summary_focus": ""
        }
        
        if 'machine learning' in title or 'ml' in title:
            suggestions["role_type"] = "ml_engineer"
            suggestions["keywords"] = ["PyTorch", "ML pipelines", "model deployment"]
            suggestions["summary_focus"] = "ML engineering and model deployment"
        elif 'data engineer' in title:
            suggestions["role_type"] = "data_engineer"
            suggestions["keywords"] = ["PySpark", "ETL", "data pipelines"]
            suggestions["summary_focus"] = "data engineering and pipeline development"
        elif 'quant' in title:
            suggestions["role_type"] = "quantitative"
            suggestions["keywords"] = ["factor research", "backtesting", "trading strategies"]
            suggestions["summary_focus"] = "quantitative research and trading systems"
        else:
            suggestions["role_type"] = "data_scientist"
            suggestions["keywords"] = ["Python", "machine learning", "data analysis"]
            suggestions["summary_focus"] = "data science and ML applications"
        
        return score, suggestions


class ResumeGenerator:
    """简历生成器"""
    
    def __init__(self):
        self.template = self._load_template()
        self.bullet_library = self._load_bullets()
    
    def _load_template(self) -> str:
        """加载HTML模板"""
        template_path = TEMPLATES_DIR / "resume.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_bullets(self) -> Dict:
        """加载bullet library"""
        bullets_path = ASSETS_DIR / "bullet_library.yaml"
        if not bullets_path.exists():
            return {}
        # 简化版，实际用yaml解析
        return {}
    
    def generate(self, job: Dict, suggestions: Dict) -> str:
        """
        生成定制简历HTML
        
        Args:
            job: 职位信息
            suggestions: AI评分给出的定制建议
        
        Returns:
            HTML字符串
        """
        html = self.template
        company = job.get('company', 'the company')
        
        # 根据职位类型定制Summary
        role_type = suggestions.get("role_type", "data_scientist")
        keywords = suggestions.get("keywords", [])
        focus = suggestions.get("summary_focus", "data science")
        
        summaries = {
            "ml_engineer": f"Machine Learning Engineer with expertise in developing and deploying ML models at scale. M.Sc. in AI from VU Amsterdam with thesis on Uncertainty Quantification in Deep RL. Experienced in {', '.join(keywords[:3])}. Eager to contribute to {company}'s ML initiatives.",
            
            "data_engineer": f"Data Engineer with strong background in building scalable data pipelines and ML infrastructure. M.Sc. in AI from VU Amsterdam. Experienced in {', '.join(keywords[:3])}. Seeking to leverage data engineering skills at {company}.",
            
            "quantitative": f"Quantitative Researcher with hands-on experience in factor research, backtesting, and live trading systems. Background in multi-factor alpha models with proven track record. M.Sc. in AI from VU Amsterdam. Seeking quantitative role at {company}.",
            
            "data_scientist": f"Data Scientist with expertise in machine learning, statistical modeling, and data-driven decision making. M.Sc. in AI from VU Amsterdam. Experienced in {', '.join(keywords[:3])}. Excited to bring analytical skills to {company}."
        }
        
        summary = summaries.get(role_type, summaries["data_scientist"])
        
        # 替换summary
        html = re.sub(
            r'(<div class="tailored-summary"[^>]*>)(.*?)(</div>)',
            f'\\1{summary}\\3',
            html,
            flags=re.DOTALL
        )
        
        return html
    
    def save_html(self, html: str, job: Dict) -> Path:
        """保存HTML文件"""
        safe_company = re.sub(r'[^\w\-]', '_', job.get('company', 'unknown').lower())[:20]
        safe_title = re.sub(r'[^\w\-]', '_', job.get('title', 'job').lower())[:20]
        filename = f"Fei_Huang_{safe_company}_{safe_title}.html"
        filepath = OUTPUT_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filepath
    
    async def generate_pdf(self, html_path: Path) -> Path:
        """HTML转PDF"""
        from playwright.async_api import async_playwright
        
        pdf_path = html_path.with_suffix('.pdf')
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(f"file:///{html_path.resolve()}")
            await page.wait_for_load_state("networkidle")
            await page.pdf(
                path=str(pdf_path),
                format="A4",
                margin={"top": "0.4in", "right": "0.4in", "bottom": "0.4in", "left": "0.4in"},
                print_background=True
            )
            await browser.close()
        
        return pdf_path


class JobTracker:
    """职位追踪器 - JSON存储"""
    
    TRACKER_FILE = DATA_DIR / "applications.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载追踪数据"""
        default_data = {"applications": [], "stats": {"total": 0, "applied": 0, "rejected": 0}}
        if self.TRACKER_FILE.exists():
            try:
                with open(self.TRACKER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 确保stats存在
                    if "stats" not in data:
                        data["stats"] = default_data["stats"]
                    return data
            except:
                return default_data
        return default_data
    
    def _save(self):
        """保存追踪数据"""
        with open(self.TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add(self, result: JobResult):
        """添加记录"""
        self.data["applications"].append(asdict(result))
        self.data["stats"]["total"] += 1
        if result.status == "applied":
            self.data["stats"]["applied"] += 1
        elif result.status == "rejected":
            self.data["stats"]["rejected"] += 1
        self._save()
    
    def exists(self, job_id: str) -> bool:
        """检查是否已处理过"""
        return any(a["job_id"] == job_id for a in self.data["applications"])


class StreamlinedPipeline:
    """流式处理Pipeline"""
    
    def __init__(self):
        self.tracker = JobTracker()
        self.resume_gen = ResumeGenerator()
    
    def _generate_job_id(self, job: Dict) -> str:
        """生成职位唯一ID"""
        key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('url', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    async def process_job(self, job: Dict) -> JobResult:
        """
        处理单个职位（核心流程）
        
        流程: 发现 → 硬性筛选 → AI评分(≥6分) → 生成简历 → 投递 → 记录
        """
        job_id = self._generate_job_id(job)
        
        # 检查是否已处理
        if self.tracker.exists(job_id):
            return JobResult(
                job_id=job_id,
                title=job.get('title', ''),
                company=job.get('company', ''),
                url=job.get('url', ''),
                status="skipped",
                reject_reason="already_processed"
            )
        
        result = JobResult(
            job_id=job_id,
            title=job.get('title', ''),
            company=job.get('company', ''),
            url=job.get('url', ''),
            status="pending"
        )
        
        try:
            # ========== 第一层：硬性筛选（0 token）==========
            passed, reject_reason = HardFilter.check(job)
            if not passed:
                result.status = "rejected"
                result.reject_reason = reject_reason
                self.tracker.add(result)
                print(f"  [REJECTED] {job.get('title', '')[:50]}... - {reject_reason}")
                return result
            
            # ========== 第二层：AI评分（1次调用）==========
            score, suggestions = await JobScorer.ai_score(job)
            result.score = score
            
            if score < 6.0:
                result.status = "scored"
                result.reject_reason = f"score_too_low({score:.1f})"
                self.tracker.add(result)
                print(f"  [LOW SCORE] {job.get('title', '')[:50]}... - {score:.1f}")
                return result
            
            # ========== 第三层：生成&投递 ==========
            print(f"  [GENERATING] {job.get('title', '')[:50]}... - Score: {score:.1f}")
            
            # 生成简历
            html = self.resume_gen.generate(job, suggestions)
            html_path = self.resume_gen.save_html(html, job)
            pdf_path = await self.resume_gen.generate_pdf(html_path)
            result.resume_path = str(pdf_path)
            
            # TODO: 自动投递
            # await self._apply_to_job(job, pdf_path)
            
            result.status = "applied"
            self.tracker.add(result)
            print(f"  [APPLIED] {job.get('title', '')[:50]}... - PDF: {pdf_path.name}")
            
        except Exception as e:
            result.status = "error"
            result.error_msg = str(e)
            self.tracker.add(result)
            print(f"  [ERROR] {job.get('title', '')[:50]}... - {e}")
        
        return result
    
    async def process_jobs(self, jobs: List[Dict]) -> List[JobResult]:
        """批量处理职位"""
        results = []
        print(f"\n{'='*60}")
        print(f"Processing {len(jobs)} jobs...")
        print(f"{'='*60}\n")
        
        for i, job in enumerate(jobs, 1):
            print(f"[{i}/{len(jobs)}] {job.get('company', 'Unknown')} - {job.get('title', 'Unknown')[:40]}...")
            result = await self.process_job(job)
            results.append(result)
        
        # 打印统计
        self._print_stats(results)
        return results
    
    def _print_stats(self, results: List[JobResult]):
        """打印统计"""
        total = len(results)
        rejected = sum(1 for r in results if r.status == "rejected")
        low_score = sum(1 for r in results if r.status == "scored")
        applied = sum(1 for r in results if r.status == "applied")
        errors = sum(1 for r in results if r.status == "error")
        
        print(f"\n{'='*60}")
        print("PROCESSING COMPLETE")
        print(f"{'='*60}")
        print(f"Total:     {total}")
        print(f"Rejected:  {rejected} (hard filter)")
        print(f"Low score: {low_score} (< 6.0)")
        print(f"Applied:   {applied} (success)")
        print(f"Errors:    {errors}")
        print(f"{'='*60}\n")


# ============== 测试 ==============

async def test_pipeline():
    """测试pipeline"""
    # 模拟职位数据
    test_jobs = [
        {
            "title": "Machine Learning Engineer",
            "company": "Picnic",
            "location": "Amsterdam",
            "url": "https://linkedin.com/jobs/1",
            "description": "Looking for ML engineer with Python, PyTorch experience. 2-4 years experience. Visa sponsorship available."
        },
        {
            "title": "Senior Data Scientist (Dutch Required)",
            "company": "Local Bank",
            "location": "Rotterdam", 
            "url": "https://linkedin.com/jobs/2",
            "description": "Senior role requiring fluent Dutch. 10+ years experience in banking."
        },
        {
            "title": "Junior Data Analyst",
            "company": "Startup",
            "location": "Utrecht",
            "url": "https://linkedin.com/jobs/3",
            "description": "Entry level data analyst. SQL, Python required."
        },
        {
            "title": "Principal Engineer",
            "company": "BigTech",
            "location": "Amsterdam",
            "url": "https://linkedin.com/jobs/4",
            "description": "Principal engineer with 15+ years experience leading teams."
        },
    ]
    
    pipeline = StreamlinedPipeline()
    await pipeline.process_jobs(test_jobs)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(test_pipeline())
    else:
        print("Streamlined Job Pipeline")
        print("Usage:")
        print("  python streamlined_pipeline.py --test    # 测试模式")
