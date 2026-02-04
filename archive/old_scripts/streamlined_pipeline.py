"""
Streamlined Job Pipeline - 流式职位处理
=======================================

流程: 发现 → 硬性筛选 → AI评分 → 生成简历 → 投递

Usage:
    from streamlined_pipeline import process_job
    process_job(job_data, auto_apply=True)
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple

# 项目路径
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# 确保目录存在
for d in [DATA_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class HardFilters:
    """硬性筛选规则 - 0 token消耗"""
    
    # 绝对否决（除非其他条件优秀）
    ABSOLUTE_REJECT = {
        "dutch_required": [
            r"dutch\s*(is\s*)?required",
            r"dutch\s*native",
            r"fluent\s*in\s*dutch",
            r"nederlands\s*vereist",
        ],
        "other_language": [
            r"german\s*(is\s*)?required",
            r"french\s*(is\s*)?required",
        ],
        "experience": [
            r"10\+?\s*years?",
            r"8\+?\s*years?",
        ],
        "location": [
            # 可添加特定排除地点
        ]
    }
    
    # 警告信号（扣分但不否决）
    WARNING_SIGNALS = {
        "leadership_title": [
            r"^lead\s+",
            r"^principal\s+",
            r"^staff\s+",
            r"director",
            r"head\s+of",
            r"vp\s+",
            r"vice\s+president",
        ],
        "senior_title": [
            r"^senior\s+",
        ],
        "experience_mid": [
            r"5\+?\s*years?",
            r"6\+?\s*years?",
            r"7\+?\s*years?",
        ]
    }
    
    @classmethod
    def check(cls, job: Dict) -> Tuple[bool, Dict]:
        """
        硬性筛选
        
        Returns:
            (passed, details)
            passed: True = 通过，False = 否决
            details: 筛选详情
        """
        text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        title = job.get('title', '').lower()
        
        details = {
            "passed": True,
            "reject_reasons": [],
            "warnings": [],
            "penalty_score": 0
        }
        
        # 检查绝对否决项
        for category, patterns in cls.ABSOLUTE_REJECT.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    details["reject_reasons"].append(f"{category}: {pattern}")
                    details["passed"] = False
        
        # 检查警告信号
        for category, patterns in cls.WARNING_SIGNALS.items():
            for pattern in patterns:
                if re.search(pattern, title, re.IGNORECASE):
                    details["warnings"].append(category)
                    if category == "senior_title":
                        # Senior 职位扣1分，但不否决
                        details["penalty_score"] += 1
                    else:
                        details["penalty_score"] += 2
        
        return details["passed"], details


class AIAnalyzer:
    """AI评分和简历建议 - 单次调用"""
    
    SYSTEM_PROMPT = """You are a job application assistant. Analyze the job posting and output JSON only.

Input: Job title, company, description

Output format:
{
    "score": 0-10,
    "recommendation": "APPLY_NOW|APPLY|MAYBE|SKIP",
    "reason": "brief explanation",
    "resume_focus": "what to emphasize in resume",
    "key_skills": ["skill1", "skill2", "skill3"],
    "tailoring_notes": "specific changes for this application"
}

Scoring criteria:
- 8-10: Perfect match, visa-friendly, strong fit
- 6-7: Good match, worth applying
- 4-5: Marginal, apply if time permits
- 0-3: Poor match, skip

Resume focus guidelines:
- For ML Engineer: emphasize PyTorch, model deployment, ML systems
- For Data Engineer: emphasize pipelines, ETL, SQL, cloud
- For Data Scientist: emphasize analysis, modeling, business impact
- For Quant: emphasize trading, backtesting, alpha research"""

    @classmethod
    def analyze(cls, job: Dict) -> Dict:
        """
        AI分析职位 - 返回评分和简历建议
        
        Returns analysis dict with score and tailoring info
        """
        # 构建输入
        job_text = f"""Job Title: {job.get('title', 'N/A')}
Company: {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}

Description:
{job.get('description', 'N/A')[:2000]}"""

        # 这里应该调用AI模型，但先返回模拟结果
        # 实际实现需要接入 sessions_spawn 或其他AI调用方式
        return {
            "score": 0,
            "recommendation": "PENDING",
            "reason": "AI analysis not implemented - requires external AI call",
            "resume_focus": "",
            "key_skills": [],
            "tailoring_notes": ""
        }


class ResumeGenerator:
    """简历生成器"""
    
    def __init__(self):
        self.template_path = TEMPLATES_DIR / "resume.html"
    
    def generate(self, job: Dict, analysis: Dict) -> Optional[Path]:
        """
        根据职位和分析结果生成定制简历
        
        Returns:
            PDF路径 或 None
        """
        # 1. 加载模板
        if not self.template_path.exists():
            print(f"[ERROR] Template not found: {self.template_path}")
            return None
        
        with open(self.template_path, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 2. 根据分析结果定制内容
        html = self._tailor_template(template, job, analysis)
        
        # 3. 保存HTML
        safe_company = re.sub(r'[^\w\-]', '_', job.get('company', 'unknown'))
        safe_title = re.sub(r'[^\w\-]', '_', job.get('title', 'position')[:30])
        html_path = OUTPUT_DIR / f"{safe_company}_{safe_title}.html"
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        # 4. 生成PDF
        pdf_path = self._generate_pdf(html_path, job)
        
        return pdf_path
    
    def _tailor_template(self, template: str, job: Dict, analysis: Dict) -> str:
        """根据分析结果定制模板"""
        title = job.get('title', '').lower()
        company = job.get('company', '')
        focus = analysis.get('resume_focus', '')
        
        # 根据职位类型选择摘要
        if 'machine learning' in title or 'ml engineer' in title:
            summary = f"Machine Learning Engineer with expertise in developing and deploying ML models at scale. M.Sc. in AI from VU Amsterdam. Experienced in PyTorch, TensorFlow, and production ML systems."
        elif 'data engineer' in title:
            summary = f"Data Engineer with strong background in building scalable data pipelines and ETL processes. M.Sc. in AI from VU Amsterdam. Experienced in Python, SQL, PySpark, and cloud platforms."
        elif 'quant' in title:
            summary = f"Quantitative Researcher with hands-on experience in factor research, backtesting, and live trading systems. M.Sc. in AI from VU Amsterdam."
        elif 'data scientist' in title:
            summary = f"Data Scientist with expertise in machine learning, statistical modeling, and data-driven decision making. M.Sc. in AI from VU Amsterdam."
        else:
            summary = f"Data professional with expertise in machine learning, data engineering, and quantitative analysis. M.Sc. in AI from VU Amsterdam."
        
        # 替换模板中的变量
        html = template.replace("{{SUMMARY}}", summary)
        html = html.replace("{{COMPANY}}", company)
        
        return html
    
    def _generate_pdf(self, html_path: Path, job: Dict) -> Optional[Path]:
        """使用 Playwright 生成PDF"""
        try:
            from playwright.sync_api import sync_playwright
            
            # 构建文件名
            safe_company = re.sub(r'[^\w\-]', '_', job.get('company', 'unknown'))
            safe_title = re.sub(r'[^\w\-]', '_', job.get('title', 'position')[:30])
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
            
            print(f"[PDF] Generated: {pdf_path}")
            return pdf_path
                
        except Exception as e:
            print(f"[ERROR] PDF generation error: {e}")
            return None


class ApplicationTracker:
    """申请记录追踪"""
    
    TRACKER_FILE = DATA_DIR / "applications.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载申请记录"""
        if self.TRACKER_FILE.exists():
            with open(self.TRACKER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"version": "2.0", "applications": []}
    
    def _save(self):
        """保存申请记录"""
        with open(self.TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add_application(self, job: Dict, analysis: Dict, resume_path: Path, 
                       status: str = "applied") -> str:
        """
        添加申请记录
        
        Returns:
            application_id
        """
        app_id = f"app_{datetime.now().strftime('%Y%m%d%H%M%S')}_{job.get('company', 'unknown')[:10]}"
        
        application = {
            "id": app_id,
            "job_id": job.get('id'),
            "company": job.get('company'),
            "position": job.get('title'),
            "location": job.get('location'),
            "url": job.get('url'),
            "status": status,
            "priority": "high" if analysis.get('score', 0) >= 7 else "normal",
            "score": analysis.get('score'),
            "analysis": analysis,
            "timeline": {
                "discovered_at": job.get('discovered_at', datetime.now().isoformat()),
                "applied_at": datetime.now().isoformat() if status == "applied" else None,
                "last_updated": datetime.now().isoformat()
            },
            "resume": {
                "generated_at": datetime.now().isoformat(),
                "file_path": str(resume_path),
                "version": "pdf"
            },
            "interviews": [],
            "notes": analysis.get('reasoning', []),
            "automation": {
                "auto_scored": True,
                "match_score": analysis.get('score'),
                "last_checked": datetime.now().isoformat()
            }
        }
        
        self.data["applications"].append(application)
        self._save()
        
        return app_id


def process_job(job: Dict, auto_apply: bool = False, 
                min_score: float = 6.0) -> Dict:
    """
    处理单个职位的主流程
    
    Args:
        job: 职位数据
        auto_apply: 是否自动投递
        min_score: 最低通过分数
    
    Returns:
        处理结果
    """
    result = {
        "job_id": job.get('id'),
        "company": job.get('company'),
        "title": job.get('title'),
        "status": "pending",
        "reason": "",
        "score": 0,
        "resume_path": None,
        "application_id": None
    }
    
    print(f"\n{'='*60}")
    print(f"[PROCESS] {job.get('title')} @ {job.get('company')}")
    print(f"{'='*60}")
    
    # Step 1: 硬性筛选
    print("[STEP 1] Hard filter check...")
    passed, filter_details = HardFilters.check(job)
    
    if not passed:
        result["status"] = "rejected"
        result["reason"] = f"Hard filter: {', '.join(filter_details['reject_reasons'])}"
        print(f"[REJECTED] {result['reason']}")
        return result
    
    if filter_details['warnings']:
        print(f"[WARNING] {', '.join(filter_details['warnings'])}")
    
    # Step 2: AI评分
    print("[STEP 2] AI analysis...")
    # TODO: 这里需要调用实际AI模型
    # 暂时使用模拟数据
    analysis = {
        "score": 7.5,  # 模拟分数
        "recommendation": "APPLY",
        "reason": "Good match for skills and experience",
        "resume_focus": "emphasize ML and data engineering",
        "key_skills": ["python", "machine learning", "sql"],
        "tailoring_notes": "highlight thesis work on RL"
    }
    
    # 应用硬性筛选的扣分
    analysis["score"] -= filter_details.get('penalty_score', 0)
    analysis["score"] = max(0, min(10, analysis["score"]))
    
    result["score"] = analysis["score"]
    
    if analysis["score"] < min_score:
        result["status"] = "skipped"
        result["reason"] = f"Score {analysis['score']} below threshold {min_score}"
        print(f"[SKIPPED] {result['reason']}")
        return result
    
    print(f"[SCORE] {analysis['score']}/10 - {analysis['recommendation']}")
    
    # Step 3: 生成简历
    print("[STEP 3] Generating resume...")
    generator = ResumeGenerator()
    resume_path = generator.generate(job, analysis)
    
    if not resume_path:
        result["status"] = "error"
        result["reason"] = "Resume generation failed"
        print(f"[ERROR] {result['reason']}")
        return result
    
    result["resume_path"] = str(resume_path)
    print(f"[RESUME] {resume_path}")
    
    # Step 4: 自动投递
    print("[STEP 4] Application submission...")
    tracker = ApplicationTracker()
    
    if auto_apply:
        # 尝试自动投递
        from auto_applier import LinkedInAutoApplier
        applier = LinkedInAutoApplier()
        success = applier.apply(job, resume_path)
        
        if success:
            status = "applied"
            print("[APPLY] Auto-applied successfully!")
        else:
            status = "auto_apply_failed"
            print("[APPLY] Auto-apply failed, marked for manual review")
    else:
        status = "ready_to_apply"
        print("[READY] Resume ready, awaiting manual apply")
    
    app_id = tracker.add_application(job, analysis, resume_path, status)
    result["application_id"] = app_id
    result["status"] = status
    
    print(f"[DONE] Application ID: {app_id}")
    
    return result


def batch_process(jobs: list, auto_apply: bool = False, 
                  min_score: float = 6.0) -> list:
    """
    批量处理职位列表
    
    Returns:
        所有处理结果
    """
    results = []
    
    print(f"\n{'='*60}")
    print(f"[BATCH] Processing {len(jobs)} jobs")
    print(f"{'='*60}")
    
    for job in jobs:
        result = process_job(job, auto_apply, min_score)
        results.append(result)
    
    # 打印汇总
    print(f"\n{'='*60}")
    print("[SUMMARY]")
    print(f"{'='*60}")
    
    by_status = {}
    for r in results:
        status = r['status']
        by_status[status] = by_status.get(status, 0) + 1
    
    for status, count in by_status.items():
        print(f"  {status}: {count}")
    
    return results


if __name__ == "__main__":
    # 测试
    test_job = {
        "id": "test_001",
        "title": "Machine Learning Engineer",
        "company": "Test Company",
        "location": "Amsterdam",
        "description": "Looking for ML engineer with Python and PyTorch experience. 3+ years experience required.",
        "url": "https://example.com/job",
        "discovered_at": datetime.now().isoformat()
    }
    
    result = process_job(test_job, auto_apply=False)
    print(f"\nResult: {json.dumps(result, indent=2)}")
