"""
智能职位解析器
==============

从各种格式的文本中提取职位信息

支持:
- LinkedIn 职位页面文本
- IamExpat 职位页面文本
- Indeed 职位页面文本
- 任意格式的职位描述
"""

import re
import json
from datetime import datetime
from typing import List, Dict, Optional


class JobParser:
    """智能职位解析器"""
    
    @staticmethod
    def parse_from_text(text: str, url: str = "", source: str = "manual") -> Optional[Dict]:
        """
        从任意文本中解析职位信息
        
        使用多种启发式方法提取:
        - 职位标题
        - 公司名称
        - 地点
        - 描述
        - 要求
        """
        if not text or len(text) < 50:
            return None
        
        job = {
            "title": "",
            "company": "",
            "location": "",
            "description": text[:2000],  # 限制长度
            "requirements": "",
            "url": url,
            "source": source,
            "scraped_at": datetime.now().isoformat()
        }
        
        lines = text.split("\n")
        lines = [l.strip() for l in lines if l.strip()]
        
        if not lines:
            return None
        
        # 尝试提取标题（通常是第一行或包含特定关键词的行）
        job["title"] = JobParser._extract_title(lines, text)
        
        # 尝试提取公司
        job["company"] = JobParser._extract_company(lines, text)
        
        # 尝试提取地点
        job["location"] = JobParser._extract_location(lines, text)
        
        # 尝试提取要求部分
        job["requirements"] = JobParser._extract_requirements(text)
        
        return job
    
    @staticmethod
    def _extract_title(lines: List[str], full_text: str) -> str:
        """提取职位标题"""
        # 常见职位关键词
        job_keywords = [
            "data scientist", "machine learning engineer", "ml engineer",
            "data engineer", "ai engineer", "quantitative researcher",
            "data analyst", "software engineer", "python developer",
            "research scientist", "algorithm engineer", "senior data engineer"
        ]
        
        # 方法1: 查找包含职位关键词的行
        for line in lines[:10]:  # 只看前10行
            line_lower = line.lower()
            for keyword in job_keywords:
                if keyword in line_lower and len(line) < 100:
                    # 清理常见前缀后缀
                    title = re.sub(r'^(job|position|role|title)\s*[:\-]?\s*', '', line, flags=re.I)
                    title = re.sub(r'\s*at\s+.*$', '', title, flags=re.I)  # 移除 "at Company"
                    return title.strip()
        
        # 方法2: 第一行通常是标题
        if lines:
            first = lines[0]
            if len(first) < 100 and not any(x in first.lower() for x in ["http", "www", "apply", "save"]):
                # 移除 "at Company" 部分
                first = re.sub(r'\s+at\s+.*$', '', first, flags=re.I)
                return first
        
        # 方法3: 返回未知
        return "Unknown Position"
    
    @staticmethod
    def _extract_company(lines: List[str], full_text: str) -> str:
        """提取公司名称"""
        # 方法1: 查找 "at Company" 模式 (最常见)
        match = re.search(r'at\s+([A-Z][A-Za-z0-9\s&\.]+?)(?:\s+in\s+|\s*$|\s*\.|")', full_text, re.I)
        if match:
            company = match.group(1).strip()
            if len(company) > 2 and len(company) < 50:
                return company
        
        # 方法2: 其他模式
        patterns = [
            r'@\s*([A-Z][A-Za-z0-9\s&\.]+)(?:\s|$|\.|")',
            r'([A-Z][A-Za-z0-9\s&\.]+)\s+is\s+hiring',
            r'([A-Z][A-Za-z0-9\s&\.]+)\s+–\s*',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, full_text)
            if match:
                company = match.group(1).strip()
                if len(company) > 2 and len(company) < 50:
                    return company
        
        # 方法3: 查找 "Company Name" + "Location" 模式
        for i, line in enumerate(lines[:15]):
            if any(loc in line for loc in ["Amsterdam", "Rotterdam", "Utrecht", "Netherlands", "NL", "in"]):
                # 前一行可能是公司名
                if i > 0:
                    prev = lines[i-1]
                    if len(prev) < 50 and not any(x in prev.lower() for x in ["apply", "save", "http"]):
                        return prev
        
        return "Unknown Company"
    
    @staticmethod
    def _extract_location(lines: List[str], full_text: str) -> str:
        """提取地点"""
        # 荷兰常见地点
        nl_cities = [
            "Amsterdam", "Rotterdam", "Utrecht", "The Hague", "Den Haag",
            "Eindhoven", "Groningen", "Maastricht", "Leiden", "Delft",
            "Amersfoort", "Haarlem", "Arnhem", "Nijmegen", "Tilburg",
            "Breda", "Apeldoorn", "Enschede", "Leeuwarden", "Zwolle"
        ]
        
        # 方法1: 直接匹配城市名
        for city in nl_cities:
            if city in full_text:
                # 检查是否有更具体的地点描述
                pattern = rf'{city}(?:\s*,\s*(?:Netherlands|NL|Holland))?(?:\s|$|\.)'
                match = re.search(pattern, full_text)
                if match:
                    return city + ", Netherlands"
        
        # 方法2: 查找 "Location:" 或 "Place:" 模式
        loc_patterns = [
            r'[Ll]ocation\s*[:\-]?\s*([^\n]+)',
            r'[Pp]lace\s*[:\-]?\s*([^\n]+)',
            r'[Cc]ity\s*[:\-]?\s*([^\n]+)',
        ]
        
        for pattern in loc_patterns:
            match = re.search(pattern, full_text)
            if match:
                location = match.group(1).strip()
                if len(location) < 50:
                    return location
        
        # 默认
        if "Netherlands" in full_text:
            return "Netherlands"
        return "Remote / Unknown"
    
    @staticmethod
    def _extract_requirements(text: str) -> str:
        """提取职位要求部分"""
        # 查找要求部分的开始
        req_indicators = [
            "requirements", "qualifications", "what you need", "what we look for",
            "skills required", "must have", "you should have", "we are looking for"
        ]
        
        text_lower = text.lower()
        for indicator in req_indicators:
            idx = text_lower.find(indicator)
            if idx != -1:
                # 提取要求部分（接下来的500字符）
                req_text = text[idx:idx+500]
                return req_text.strip()
        
        return ""
    
    @staticmethod
    def parse_linkedin_share_text(text: str, url: str) -> Optional[Dict]:
        """
        解析 LinkedIn 分享文本
        
        格式通常是:
        Job Title
        Company Name
        Location
        
        Description...
        """
        return JobParser.parse_from_text(text, url, "LinkedIn")
    
    @staticmethod
    def parse_multiple(text: str) -> List[Dict]:
        """
        从长文本中解析多个职位
        
        假设职位之间用空行或特定分隔符分隔
        """
        jobs = []
        
        # 尝试按空行分割
        chunks = re.split(r'\n\s*\n', text)
        
        for chunk in chunks:
            if len(chunk) > 100:  # 至少有一定长度
                job = JobParser.parse_from_text(chunk)
                if job and job["title"] != "Unknown Position":
                    jobs.append(job)
        
        return jobs


def main():
    """测试解析器"""
    # 示例文本
    sample_text = """Machine Learning Engineer
Picnic Technologies
Amsterdam, Netherlands

We are looking for a Machine Learning Engineer to join our team!

Requirements:
- 2+ years experience with Python
- Experience with PyTorch or TensorFlow
- MSc in Computer Science or related field
- Experience with production ML systems

What you'll do:
- Build and deploy ML models
- Work with large datasets
- Collaborate with data scientists and engineers
"""
    
    print("=" * 60)
    print("Job Parser Test")
    print("=" * 60)
    print()
    
    job = JobParser.parse_from_text(sample_text, "https://example.com/job/123")
    
    if job:
        print("Parsed Job:")
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Location: {job['location']}")
        print(f"  URL: {job['url']}")
        print(f"  Requirements: {job['requirements'][:100]}...")
    else:
        print("Failed to parse job")


if __name__ == "__main__":
    main()
