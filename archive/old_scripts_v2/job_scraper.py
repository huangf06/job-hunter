"""
Job Scraper - Job scraping module
==================================

Scrape jobs from platforms:
- IamExpat Jobs
- LinkedIn (requires login)
- Indeed NL

Usage:
    python job_scraper.py --platform iamexpat --search "data scientist"
    python job_scraper.py --test
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlencode, quote_plus
import hashlib

# 配置路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
LEADS_DIR = DATA_DIR / "leads"

# 确保目录存在
LEADS_DIR.mkdir(parents=True, exist_ok=True)


class JobLead:
    """职位信息"""
    
    def __init__(self, data: dict):
        self.id = data.get("id") or self._generate_id(data)
        self.title = data.get("title", "").strip()
        self.company = data.get("company", "").strip()
        self.location = data.get("location", "").strip()
        self.url = data.get("url", "").strip()
        self.description = data.get("description", "").strip()
        self.requirements = data.get("requirements", "").strip()
        self.salary = data.get("salary", "").strip()
        self.posted_date = data.get("posted_date", "").strip()
        self.source = data.get("source", "").strip()
        self.scraped_at = data.get("scraped_at") or datetime.now().isoformat()
        self.raw_html = data.get("raw_html", "")
    
    def _generate_id(self, data: dict) -> str:
        """生成唯一 ID"""
        key = f"{data.get('title', '')}-{data.get('company', '')}-{data.get('url', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "url": self.url,
            "description": self.description,
            "requirements": self.requirements,
            "salary": self.salary,
            "posted_date": self.posted_date,
            "source": self.source,
            "scraped_at": self.scraped_at
        }
    
    def save_to_file(self, directory: Path = None) -> Path:
        """保存到文件"""
        if directory is None:
            directory = LEADS_DIR
        
        # 生成文件名
        safe_company = re.sub(r'[^\w\-]', '_', self.company.lower())[:30]
        safe_title = re.sub(r'[^\w\-]', '_', self.title.lower())[:30]
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"{safe_company}_{safe_title}_{date_str}.json"
        
        filepath = directory / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def __repr__(self):
        return f"JobLead({self.title} @ {self.company})"


def build_iamexpat_url(search_term: str, page: int = 1) -> str:
    """构建 IamExpat 搜索 URL"""
    base_url = "https://www.iamexpat.nl/career/jobs-netherlands"
    params = {
        "search": search_term,
        "page": page
    }
    return f"{base_url}?{urlencode(params)}"


def build_linkedin_url(search_term: str, location: str = "Netherlands") -> str:
    """构建 LinkedIn 搜索 URL"""
    base_url = "https://www.linkedin.com/jobs/search"
    params = {
        "keywords": search_term,
        "location": location,
        "f_TPR": "r604800",  # 过去一周
        "sortBy": "DD"  # 按日期排序
    }
    return f"{base_url}?{urlencode(params)}"


def build_indeed_url(search_term: str, location: str = "Netherlands") -> str:
    """构建 Indeed NL 搜索 URL"""
    base_url = "https://nl.indeed.com/jobs"
    params = {
        "q": search_term,
        "l": location,
        "sort": "date"
    }
    return f"{base_url}?{urlencode(params)}"


def parse_iamexpat_listing(html_content: str) -> List[Dict]:
    """
    解析 IamExpat 职位列表页面
    
    返回职位基本信息列表（需要进一步抓取详情页）
    """
    jobs = []
    
    # 简单的正则解析（实际使用时可能需要 BeautifulSoup）
    # 这里返回空列表，实际解析由 browser 工具完成
    
    return jobs


def parse_iamexpat_detail(html_content: str, url: str) -> Optional[JobLead]:
    """
    解析 IamExpat 职位详情页面
    """
    # 实际解析由 browser 工具完成
    return None


# ============================================================
# 以下函数设计为由 OpenClaw 的 browser 工具调用
# ============================================================

def extract_job_from_snapshot(snapshot_text: str, url: str, source: str) -> JobLead:
    """
    从 browser snapshot 提取职位信息
    
    这个函数由 AI 调用，传入 snapshot 文本
    """
    # AI 会解析 snapshot 并提取信息
    # 这里只是一个占位符
    
    data = {
        "url": url,
        "source": source,
        "scraped_at": datetime.now().isoformat()
    }
    
    return JobLead(data)


def analyze_job_match(job: JobLead, target_keywords: List[str] = None) -> Dict:
    """
    分析职位匹配度
    
    返回：
    - score: 0-10 分
    - reasons: 匹配/不匹配的原因
    - recommendation: apply / maybe / skip
    """
    if target_keywords is None:
        target_keywords = [
            "python", "machine learning", "data scientist", "ml engineer",
            "data engineer", "pytorch", "tensorflow", "sql", "quant"
        ]
    
    exclude_keywords = [
        "senior manager", "director", "head of", "vp ", "vice president",
        "10+ years", "dutch required", "dutch native", "german required",
        "principal", "staff engineer"
    ]
    
    score = 5.0  # 基础分
    reasons = {"positive": [], "negative": []}
    
    # 合并文本进行分析
    text = f"{job.title} {job.description} {job.requirements}".lower()
    
    # 正面因素
    keyword_scores = {
        "python": 1.5,
        "machine learning": 2.0,
        "data scientist": 2.0,
        "ml engineer": 2.0,
        "ai engineer": 2.0,
        "data engineer": 1.5,
        "pytorch": 1.0,
        "tensorflow": 1.0,
        "deep learning": 1.5,
        "nlp": 1.0,
        "llm": 1.0,
        "sql": 0.5,
        "quant": 2.0,
        "quantitative": 1.5,
        "fintech": 1.0,
        "trading": 1.5,
        "junior": 1.0,
        "entry level": 1.0,
        "graduate": 0.5,
        "visa sponsor": 2.0,
        "relocation": 1.0
    }
    
    for keyword, points in keyword_scores.items():
        if keyword in text:
            score += points
            reasons["positive"].append(f"'{keyword}' (+{points})")
    
    # 负面因素
    exclude_scores = {
        "senior manager": -3.0,
        "director": -3.0,
        "head of": -3.0,
        "vp ": -3.0,
        "vice president": -3.0,
        "10+ years": -2.0,
        "8+ years": -1.5,
        "dutch required": -5.0,
        "dutch native": -5.0,
        "german required": -3.0,
        "french required": -3.0,
        "principal": -2.0,
        "staff engineer": -1.5,
        "lead": -0.5
    }
    
    for keyword, points in exclude_scores.items():
        if keyword in text:
            score += points
            reasons["negative"].append(f"'{keyword}' ({points})")
    
    # 限制分数范围
    score = max(0, min(10, score))
    
    # 推荐
    if score >= 7:
        recommendation = "apply"
    elif score >= 5:
        recommendation = "maybe"
    else:
        recommendation = "skip"
    
    return {
        "score": round(score, 1),
        "reasons": reasons,
        "recommendation": recommendation
    }


def save_scrape_results(jobs: List[JobLead], search_term: str, source: str) -> Path:
    """
    保存抓取结果到文件
    """
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    safe_term = re.sub(r'[^\w\-]', '_', search_term.lower())[:20]
    filename = f"scrape_{source}_{safe_term}_{date_str}.json"
    
    filepath = DATA_DIR / filename
    
    data = {
        "search_term": search_term,
        "source": source,
        "scraped_at": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "jobs": [job.to_dict() for job in jobs]
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Saved {len(jobs)} jobs to {filepath}")
    return filepath


def load_scrape_results(filepath: Path) -> List[JobLead]:
    """
    从文件加载抓取结果
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return [JobLead(job) for job in data.get("jobs", [])]


# ============================================================
# CLI 入口
# ============================================================

def main():
    """Main function - show usage"""
    print("=" * 60)
    print("Job Scraper - Job Scraping Module")
    print("=" * 60)
    print()
    print("This module is designed to work with OpenClaw's browser tool.")
    print()
    print("Available URL builders:")
    print(f"  IamExpat: {build_iamexpat_url('data scientist')}")
    print(f"  LinkedIn: {build_linkedin_url('data scientist')}")
    print(f"  Indeed:   {build_indeed_url('data scientist')}")
    print()
    print("Workflow:")
    print("  1. Use browser tool to open search URL")
    print("  2. Use browser snapshot to get page content")
    print("  3. AI parses snapshot to extract job info")
    print("  4. Use analyze_job_match() to analyze fit")
    print("  5. Use save_scrape_results() to save results")
    print()
    
    # Test URL generation
    print("Test search terms:")
    for term in ["data scientist", "machine learning engineer", "quant researcher"]:
        print(f"  - {term}")
        print(f"    IamExpat: {build_iamexpat_url(term)}")
    print()


if __name__ == "__main__":
    main()
