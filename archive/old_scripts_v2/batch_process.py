#!/usr/bin/env python3
"""
全自动职位处理流水线 v2
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

# 职位列表
jobs = [
    {
        "title": "Data Engineer",
        "company": "Talpa Network", 
        "description": "Design, build, and maintain batch and real-time data pipelines in production. Automate ETL workflows. AWS, Python, SQL. Experience with cloud-based data platforms."
    },
    {
        "title": "Data Engineer - QuantumBlack, AI by McKinsey",
        "company": "QuantumBlack",
        "description": "Data Engineer role at McKinsey's AI division. Build data pipelines, work with cloud platforms. ETL/ELT, data warehousing. Python, SQL. High performance culture."
    },
    {
        "title": "Data Engineer",
        "company": "Doghouse Recruitment (Media)",
        "description": "2+ years data engineering experience. ETL pipelines in production. Python, SQL. AWS or other Public Clouds. DataOps team. Salary up to 80k. Hilversum."
    },
    {
        "title": "Data Engineer - Video-on-demand",
        "company": "Doghouse Recruitment (VOD)",
        "description": "AWS, Kafka, Lambda, SQL, Python. 2+ years cloud-based data platform. ETL, Kafka, Spark. Lambda functions. SQL and NoSQL databases. Utrecht Area. Salary up to 90k."
    },
    {
        "title": "Data Engineer - Contract",
        "company": "iO Associates",
        "description": "Contract role. Design and maintain data pipelines, data lakes. AWS, Azure, or Google Cloud. Python. Docker, Kubernetes. CI/CD. The Hague. NATO Secret Clearance required."
    }
]

def process_job(title, description, company):
    """处理单个职位"""
    cmd = [
        sys.executable, "job_hunter_v42.py",
        "--job", f"{title}|{description}|{company}"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, cwd="job-hunter")
    return result.returncode == 0

if __name__ == "__main__":
    print("="*70)
    print("AUTO BATCH PROCESSING")
    print("="*70)
    
    success_count = 0
    
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}/{len(jobs)}] {job['title']} @ {job['company']}")
        print("-"*70)
        
        if process_job(job['title'], job['description'], job['company']):
            success_count += 1
            print("[OK] SUCCESS")
        else:
            print("[FAIL] FAILED")
    
    print(f"\n{'='*70}")
    print(f"COMPLETE: {success_count}/{len(jobs)} jobs processed")
    print("Check output/ directory for generated resumes")
    print("="*70)
