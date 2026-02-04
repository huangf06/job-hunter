"""
基于 web_fetch 的职位爬虫
========================

使用 OpenClaw 的 web_fetch 工具爬取职位
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


class FetchJobScraper:
    """使用 web_fetch 的职位爬虫"""
    
    @staticmethod
    def parse_iamexpat_jobs(markdown_text: str) -> List[Dict]:
        """从 IamExpat Markdown 文本解析职位"""
        jobs = []
        
        # 职位格式 (Markdown 链接格式):
        # [FEATUREDJob TitleFEATUREDCategoryLocationTypePosted on Date](URL)
        
        # 使用正则表达式匹配职位条目
        # 匹配模式: [内容](URL)
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, markdown_text)
        
        for content, url in matches:
            # 跳过非职位条目
            if any(skip in content for skip in ['Post a job', 'Learn more about working']):
                continue
            
            # 清理 FEATURED 标记
            content = re.sub(r'FEATURED', '', content)
            
            # 提取 Posted on 日期
            posted_match = re.search(r'Posted on ([^\)]+)', content)
            posted_date = posted_match.group(1) if posted_match else ''
            content = re.sub(r'Posted on [^\)]+', '', content)
            
            # 提取职位类型 (Permanent, Temporary, Internship, etc.)
            job_types = ['Permanent', 'Temporary', 'Internship / Graduate', 'Contract', 'Freelance']
            job_type = ''
            for jt in job_types:
                if jt in content:
                    job_type = jt
                    content = content.replace(jt, '')
                    break
            
            # 提取类别
            categories = [
                'Sales', 'IT & technology', 'Customer service', 'HR / Recruitment',
                'Finance / Accounting', 'Administration / Secretarial',
                'Supply Chain / Logistics', 'Management / Consulting',
                'Editing / Translation', 'Other', 'Marketing', 'Engineering'
            ]
            category = ''
            for cat in categories:
                if cat in content:
                    category = cat
                    content = content.replace(cat, '')
                    break
            
            # 提取地点 (荷兰城市)
            nl_cities = [
                'Amsterdam', 'Rotterdam', 'Utrecht', 'Eindhoven', 'Den Bosch',
                'Groningen', 'Venray', 'Bleiswijk', 'Woerden', 'Noordwijk aan Zee',
                'Middenmeer', 'The Hague', 'Den Haag', 'Leiden', 'Delft',
                'Maastricht', 'Arnhem', 'Nijmegen', 'Tilburg', 'Breda'
            ]
            location = 'Netherlands'
            for city in nl_cities:
                if city in content:
                    location = city
                    content = content.replace(city, '')
                    break
            
            # 剩下的就是职位标题
            title = content.strip()
            
            # 清理标题中的多余空格
            title = re.sub(r'\s+', ' ', title)
            
            if title and len(title) > 3:
                jobs.append({
                    "title": title,
                    "company": "Unknown",  # IamExpat 列表页不显示公司名
                    "location": location,
                    "url": f"https://www.iamexpat.nl{url}" if url.startswith('/') else url,
                    "category": category,
                    "job_type": job_type,
                    "posted_date": posted_date,
                    "source": "IamExpat",
                    "scraped_at": datetime.now().isoformat()
                })
        
        return jobs
    
    @staticmethod
    def scrape_iamexpat(search_term: str) -> List[Dict]:
        """
        爬取 IamExpat 职位
        
        注意：这个函数需要由 OpenClaw 调用 web_fetch 工具
        这里只是一个占位符，实际调用在 auto_pipeline.py 中
        """
        search_slug = search_term.replace(" ", "-").lower()
        url = f"https://www.iamexpat.nl/career/jobs-netherlands/{search_slug}"
        
        print(f"[FETCH] IamExpat URL: {url}")
        print("[FETCH] Use web_fetch tool to get content, then parse with parse_iamexpat_jobs()")
        
        return []


def save_jobs(jobs: List[Dict], source: str, search_term: str):
    """保存职位"""
    if not jobs:
        return None
    
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"{source}_{search_term.replace(' ', '_')}_{date_str}.json"
    filepath = DATA_DIR / filename
    
    data = {
        "source": source,
        "search": search_term,
        "scraped_at": datetime.now().isoformat(),
        "total_jobs": len(jobs),
        "jobs": jobs
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"[SAVE] Saved {len(jobs)} jobs to {filepath}")
    return filepath


# ============================================================
# 测试
# ============================================================

def test_parse():
    """测试解析"""
    # 真实的 markdown 格式样本
    sample_text = """[FEATUREDContent & Social Media Assistant (intern)FEATUREDEditing / TranslationAmsterdamInternship / GraduatePosted on February 1, 2026](/career/jobs-netherlands/editing-translation-positions/content-social-media-assistant-intern/bDyWtzLntjcC7HkHKYfqR5)
[FEATUREDEditor-in-ChiefFEATUREDEditing / TranslationAmsterdamPosted on February 1, 2026](/career/jobs-netherlands/editing-translation-positions/editor-chief/5BybtkrWNvfTHECYurv5oc)
[Account Manager | French & DutchSalesDen BoschPosted on February 1, 2026](/career/jobs-netherlands/sales-positions/account-manager-french-dutch/3Xe4RPwmkukidqTXbQPqYx)
[Frontend EngineerIT & technologyAmsterdamPermanentPosted on February 1, 2026](/career/jobs-netherlands/it-technology-positions/frontend-engineer/rpd6DZbw2dsgwg5D7QfBEp)"""
    
    print("=" * 60)
    print("Testing IamExpat Parser")
    print("=" * 60)
    
    jobs = FetchJobScraper.parse_iamexpat_jobs(sample_text)
    
    print(f"\nFound {len(jobs)} jobs:")
    for job in jobs:
        print(f"  - {job['title']} | {job.get('category', '')} | {job['location']}")
    
    return jobs


if __name__ == "__main__":
    test_parse()
