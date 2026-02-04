"""
RSS/API 职位爬虫 - 备用数据源
==============================

当 Playwright 爬虫不可用时，使用 RSS feeds 和 APIs

Sources:
- LinkedIn RSS (if available)
- Indeed RSS
- IamExpat RSS
- GitHub Jobs API
- RemoteOK API
"""

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import urllib.request
import urllib.parse

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)


class RSSJobScraper:
    """RSS 职位爬虫"""
    
    RSS_FEEDS = {
        "stackoverflow": "https://stackoverflow.com/jobs/feed?location=amsterdam",
        "indeed_nl": "https://nl.indeed.com/rss?q=data+scientist&l=Netherlands",
    }
    
    @classmethod
    def fetch_rss(cls, url: str) -> Optional[str]:
        """获取 RSS feed"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode("utf-8")
        except Exception as e:
            print(f"Error fetching RSS: {e}")
            return None
    
    @classmethod
    def parse_rss(cls, xml_content: str, source: str) -> List[Dict]:
        """解析 RSS XML"""
        jobs = []
        try:
            root = ET.fromstring(xml_content)
            
            # 查找 item 元素
            items = root.findall(".//item")
            
            for item in items:
                title = item.find("title")
                link = item.find("link")
                description = item.find("description")
                pub_date = item.find("pubDate")
                
                job = {
                    "title": title.text if title is not None else "",
                    "url": link.text if link is not None else "",
                    "description": description.text if description is not None else "",
                    "posted_date": pub_date.text if pub_date is not None else "",
                    "source": source,
                    "scraped_at": datetime.now().isoformat()
                }
                
                # 尝试从标题提取公司和地点
                title_text = job["title"]
                # 常见格式: "Job Title at Company in Location"
                match = re.search(r'at\s+(.+?)(?:\s+in\s+(.+))?$', title_text)
                if match:
                    job["company"] = match.group(1).strip()
                    job["location"] = match.group(2).strip() if match.group(2) else "Netherlands"
                else:
                    job["company"] = "Unknown"
                    job["location"] = "Netherlands"
                
                jobs.append(job)
        
        except Exception as e:
            print(f"Error parsing RSS: {e}")
        
        return jobs
    
    @classmethod
    def scrape(cls, source: str) -> List[Dict]:
        """爬取指定源的职位"""
        if source not in cls.RSS_FEEDS:
            print(f"Unknown source: {source}")
            return []
        
        url = cls.RSS_FEEDS[source]
        print(f"[RSS] Fetching {source} from {url}")
        
        xml_content = cls.fetch_rss(url)
        if not xml_content:
            return []
        
        jobs = cls.parse_rss(xml_content, source)
        print(f"[RSS] Found {len(jobs)} jobs from {source}")
        
        return jobs


class GitHubJobsScraper:
    """GitHub Jobs API 爬虫 (已归档，但可作为参考实现)"""
    
    @classmethod
    def scrape(cls, search: str = "python", location: str = "amsterdam") -> List[Dict]:
        """爬取 GitHub Jobs"""
        # GitHub Jobs API 已关闭，这里作为示例
        print("[GitHub Jobs] API is no longer available")
        return []


class ManualJobImporter:
    """手动导入职位"""
    
    @staticmethod
    def import_from_json(filepath: Path) -> List[Dict]:
        """从 JSON 文件导入职位"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            jobs = data.get("jobs", [])
            print(f"[Import] Loaded {len(jobs)} jobs from {filepath}")
            return jobs
        except Exception as e:
            print(f"[Import] Error: {e}")
            return []
    
    @staticmethod
    def import_from_text(text: str, source: str = "manual") -> List[Dict]:
        """从文本导入职位（每行一个）"""
        jobs = []
        lines = text.strip().split("\n")
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            
            # 简单格式: "Title - Company - Location"
            parts = line.split(" - ")
            if len(parts) >= 2:
                job = {
                    "title": parts[0].strip(),
                    "company": parts[1].strip(),
                    "location": parts[2].strip() if len(parts) > 2 else "Netherlands",
                    "url": "",
                    "source": source,
                    "scraped_at": datetime.now().isoformat()
                }
                jobs.append(job)
        
        print(f"[Import] Parsed {len(jobs)} jobs from text")
        return jobs


def save_jobs(jobs: List[Dict], source: str, search_term: str):
    """保存职位到文件"""
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
    
    print(f"[Save] Saved to {filepath}")
    return filepath


def main():
    """主函数"""
    print("=" * 60)
    print("RSS/API Job Scraper - Alternative Data Sources")
    print("=" * 60)
    print()
    
    # 测试 RSS 源
    for source in ["stackoverflow", "indeed_nl"]:
        jobs = RSSJobScraper.scrape(source)
        if jobs:
            save_jobs(jobs, source, "data_scientist")
        print()
    
    print("=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == "__main__":
    main()
