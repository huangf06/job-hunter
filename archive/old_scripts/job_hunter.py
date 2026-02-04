"""
Job Hunter - 完整求职流程
==========================

流程: 爬虫 → 硬性筛选 → AI评分(≥6分) → 生成简历 → 记录

Usage:
    python job_hunter.py --scrape "data scientist" --max 10    # 爬取+处理
    python job_hunter.py --process <file.json>                  # 处理已有数据
    python job_hunter.py --daily                                 # 每日自动运行
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
    status: str  # rejected | scored | generated | error
    score: Optional[float] = None
    reject_reason: Optional[str] = None
    resume_path: Optional[str] = None
    ai_analysis: Optional[str] = None
    error_msg: Optional[str] = None
    processed_at: str = None
    
    def __post_init__(self):
        if self.processed_at is None:
            self.processed_at = datetime.now().isoformat()


class HardFilter:
    """硬性筛选 - 一票否决（零token）"""
    
    REJECT_PATTERNS = {
        "dutch_required": [
            r"dutch\s*(required|mandatory|essential|native|fluent)",
            r"nederlands\s*(verplicht|vereist|moeder.*taal)",
            r"fluency\s+in\s+dutch",
        ],
        "experience_too_high": [
            r"(10|15|20)\+?\s*years?\s*(of\s*)?experience",
            r"minimum\s*(8|9)\+?\s*years",
            r"senior.*with\s*\d{2}\+?\s*years",
        ],
        "senior_level": [
            r"\b(principal|staff|director|vp|vice president|head of)\b",
            r"\bsenior\b.*\b(manager|director|lead|architect)\b",
        ],
        "wrong_role": [
            r"\b(frontend|backend|fullstack|devops|sre|security)\b",
            r"\b(android|ios|mobile)\s*(developer|engineer)",
            r"\b(frontend|ui|ux)\s*(developer|designer)",
        ],
    }
    
    @classmethod
    def check(cls, job: Dict) -> Tuple[bool, Optional[str]]:
        """硬性筛选检查"""
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        
        for rule_name, patterns in cls.REJECT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return False, rule_name
        
        return True, None


class ResumeGenerator:
    """简历生成器"""
    
    def __init__(self):
        self.template = self._load_template()
    
    def _load_template(self) -> str:
        """加载HTML模板"""
        template_path = TEMPLATES_DIR / "resume.html"
        if not template_path.exists():
            raise FileNotFoundError(f"Template not found: {template_path}")
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate(self, job: Dict, ai_analysis: str) -> str:
        """生成定制简历HTML"""
        html = self.template
        company = job.get('company', 'the company')
        title = job.get('title', '').lower()
        
        # 根据AI分析确定角色类型
        role_type = "data_scientist"
        if 'machine learning' in title or 'ml' in title:
            role_type = "ml_engineer"
        elif 'data engineer' in title:
            role_type = "data_engineer"
        elif 'quant' in title:
            role_type = "quantitative"
        elif 'analyst' in title:
            role_type = "data_analyst"
        
        # 生成Summary
        summaries = {
            "ml_engineer": f"Machine Learning Engineer with expertise in developing and deploying ML models at scale. M.Sc. in AI from VU Amsterdam with thesis on Uncertainty Quantification in Deep RL. Experienced in PyTorch, TensorFlow, and production ML systems. Eager to contribute to {company}'s ML initiatives.",
            
            "data_engineer": f"Data Engineer with strong background in building scalable data pipelines, ETL processes, and ML infrastructure. M.Sc. in AI from VU Amsterdam. Experienced in Python, SQL, PySpark, and cloud platforms. Seeking to leverage data engineering skills at {company}.",
            
            "quantitative": f"Quantitative Researcher with hands-on experience in factor research, backtesting, and live trading systems. Background in multi-factor alpha models and futures strategies with proven track record. M.Sc. in AI from VU Amsterdam. Seeking quantitative role at {company}.",
            
            "data_analyst": f"Data Analyst with strong foundation in statistical analysis, data visualization, and business intelligence. M.Sc. in AI from VU Amsterdam. Experienced in SQL, Python, and data-driven decision making. Excited to bring analytical skills to {company}.",
            
            "data_scientist": f"Data Scientist with expertise in machine learning, statistical modeling, and data-driven decision making. M.Sc. in AI from VU Amsterdam. Experienced in building end-to-end ML pipelines, credit risk modeling, and quantitative analysis. Excited to bring analytical skills to {company}."
        }
        
        summary = summaries.get(role_type, summaries["data_scientist"])
        
        # 替换summary
        html = re.sub(
            r'(<div class="tailored-summary"[^\u003e]*\u003e)(.*?)(\u003c/div\u003e)',
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
    """职位追踪器"""
    
    TRACKER_FILE = DATA_DIR / "applications.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载追踪数据"""
        default_data = {"applications": [], "stats": {"total": 0, "generated": 0, "rejected": 0}}
        if self.TRACKER_FILE.exists():
            try:
                with open(self.TRACKER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
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
        if result.status == "generated":
            self.data["stats"]["generated"] += 1
        elif result.status == "rejected":
            self.data["stats"]["rejected"] += 1
        self._save()
    
    def exists(self, job_id: str) -> bool:
        """检查是否已处理过"""
        return any(a["job_id"] == job_id for a in self.data["applications"])
    
    def get_pending_review(self) -> List[Dict]:
        """获取待审核的简历（已生成PDF但未投递）"""
        return [
            a for a in self.data["applications"]
            if a["status"] == "generated" and a.get("resume_path")
        ]


class JobHunter:
    """求职主控"""
    
    def __init__(self):
        self.tracker = JobTracker()
        self.resume_gen = ResumeGenerator()
    
    def _generate_job_id(self, job: Dict) -> str:
        """生成职位唯一ID"""
        key = f"{job.get('title', '')}-{job.get('company', '')}-{job.get('url', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    async def process_job(self, job: Dict, ai_scorer=None) -> JobResult:
        """
        处理单个职位
        
        Args:
            job: 职位信息
            ai_scorer: AI评分函数（外部传入）
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
            # ========== 第一层：硬性筛选 ==========
            passed, reject_reason = HardFilter.check(job)
            if not passed:
                result.status = "rejected"
                result.reject_reason = reject_reason
                self.tracker.add(result)
                print(f"  ❌ REJECTED - {reject_reason}")
                return result
            
            # ========== 第二层：AI评分 ==========
            if ai_scorer:
                score, analysis = await ai_scorer(job)
                result.score = score
                result.ai_analysis = analysis
                
                if score < 6.0:
                    result.status = "scored"
                    result.reject_reason = f"score_too_low({score:.1f})"
                    self.tracker.add(result)
                    print(f"  ⚠️  LOW SCORE - {score:.1f}")
                    return result
            
            # ========== 第三层：生成简历 ==========
            print(f"  📝 GENERATING...")
            
            html = self.resume_gen.generate(job, result.ai_analysis or "")
            html_path = self.resume_gen.save_html(html, job)
            pdf_path = await self.resume_gen.generate_pdf(html_path)
            result.resume_path = str(pdf_path)
            result.status = "generated"
            
            self.tracker.add(result)
            print(f"  ✅ DONE - {pdf_path.name}")
            
        except Exception as e:
            result.status = "error"
            result.error_msg = str(e)
            self.tracker.add(result)
            print(f"  💥 ERROR - {e}")
        
        return result
    
    async def process_jobs(self, jobs: List[Dict], ai_scorer=None) -> List[JobResult]:
        """批量处理职位"""
        results = []
        print(f"\n{'='*70}")
        print(f"Processing {len(jobs)} jobs...")
        print(f"{'='*70}\n")
        
        for i, job in enumerate(jobs, 1):
            company = job.get('company', 'Unknown')
            title = job.get('title', 'Unknown')[:40]
            print(f"[{i}/{len(jobs)}] {company} - {title}...")
            result = await self.process_job(job, ai_scorer)
            results.append(result)
        
        self._print_stats(results)
        return results
    
    def _print_stats(self, results: List[JobResult]):
        """打印统计"""
        total = len(results)
        rejected = sum(1 for r in results if r.status == "rejected")
        low_score = sum(1 for r in results if r.status == "scored")
        generated = sum(1 for r in results if r.status == "generated")
        errors = sum(1 for r in results if r.status == "error")
        skipped = sum(1 for r in results if r.status == "skipped")
        
        print(f"\n{'='*70}")
        print("PROCESSING COMPLETE")
        print(f"{'='*70}")
        print(f"Total:      {total}")
        print(f"Generated:  {generated} ✅")
        print(f"Rejected:   {rejected} ❌")
        print(f"Low score:  {low_score} ⚠️")
        print(f"Skipped:    {skipped} ⏭️")
        print(f"Errors:     {errors} 💥")
        print(f"{'='*70}\n")
        
        if generated > 0:
            print(f"📄 Generated resumes are in: {OUTPUT_DIR}")
            print(f"📊 Tracker saved to: {self.tracker.TRACKER_FILE}")
            print(f"\n👉 Next step: Review generated PDFs and apply manually\n")


# ============== CLI ==============

def load_jobs_from_file(filepath: str) -> List[Dict]:
    """从文件加载职位"""
    path = Path(filepath)
    if not path.exists():
        path = LEADS_DIR / filepath
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get('jobs', [])


async def scrape_linkedin(search_term: str, max_jobs: int = 10) -> List[Dict]:
    """爬取LinkedIn职位"""
    # 导入爬虫
    import sys
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from linkedin_scraper import LinkedInJobScraper
    
    scraper = LinkedInJobScraper(headless=True)
    jobs = await scraper.scrape_search_results(
        search_term=search_term,
        location="Netherlands",
        max_jobs=max_jobs
    )
    
    # 保存原始数据
    if jobs:
        scraper.save_jobs(jobs)
    
    return jobs


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Job Hunter')
    parser.add_argument('--scrape', metavar='TERM', help='Scrape LinkedIn for term')
    parser.add_argument('--max', type=int, default=10, help='Max jobs to scrape')
    parser.add_argument('--process', metavar='FILE', help='Process jobs from file')
    parser.add_argument('--all', action='store_true', help='Process all pending jobs')
    parser.add_argument('--list', action='store_true', help='List pending reviews')
    
    args = parser.parse_args()
    
    hunter = JobHunter()
    
    if args.list:
        pending = hunter.tracker.get_pending_review()
        print(f"\n📋 Pending Reviews: {len(pending)}")
        for p in pending:
            print(f"  - {p['company']}: {p['title'][:50]}")
            print(f"    Resume: {p.get('resume_path', 'N/A')}")
        return
    
    if args.scrape:
        print(f"🔍 Scraping LinkedIn for: {args.scrape}")
        jobs = await scrape_linkedin(args.scrape, args.max)
        if jobs:
            print(f"\n🤖 Now processing with AI scoring...")
            # AI评分函数（外部传入，这里用模拟）
            async def mock_ai_scorer(job):
                # 实际使用时，这里调用真实的AI评分
                return 7.5, "AI analysis placeholder"
            
            await hunter.process_jobs(jobs, mock_ai_scorer)
    
    elif args.process:
        print(f"📂 Loading jobs from: {args.process}")
        jobs = load_jobs_from_file(args.process)
        print(f"Found {len(jobs)} jobs")
        
        async def mock_ai_scorer(job):
            return 7.5, "AI analysis placeholder"
        
        await hunter.process_jobs(jobs, mock_ai_scorer)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
