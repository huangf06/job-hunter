#!/usr/bin/env python3
"""
处理今日抓取的新职位
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
from simplified_hunter import JobHunter, Job, Config

def load_today_scrape():
    """加载今天抓取的数据"""
    data_dir = Path(__file__).parent / "data"
    today = datetime.now().strftime("%Y%m%d")
    
    all_jobs = []
    
    # 查找今天的所有抓取文件
    for file in data_dir.glob(f"*_{today}_*.json"):
        if file.name.startswith(("linkedin_", "iamexpat_", "indeed_")):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    jobs = data.get('jobs', [])
                    print(f"[LOAD] {file.name}: {len(jobs)} jobs")
                    all_jobs.extend(jobs)
            except Exception as e:
                print(f"[ERROR] Failed to load {file}: {e}")
    
    return all_jobs

def enrich_job_data(job: dict) -> dict:
    """补充职位数据格式"""
    return {
        'id': f"{job.get('source', 'unknown')}_{hash(job.get('url', '')) % 10000000}",
        'title': job.get('title', ''),
        'company': job.get('company', ''),
        'location': job.get('location', ''),
        'url': job.get('url', ''),
        'description': job.get('description', f"Posted: {job.get('posted_date', 'N/A')}"),
        'source': job.get('source', 'unknown'),
        'discovered_at': job.get('scraped_at', datetime.now().isoformat())
    }

def main():
    print("="*70)
    print("[PROCESS] Processing today's scraped jobs")
    print("="*70)
    
    # 加载今日抓取
    scraped_jobs = load_today_scrape()
    print(f"\n[TOTAL] Today's scraped jobs: {len(scraped_jobs)}")
    
    if not scraped_jobs:
        print("\n[EXIT] No new jobs to process")
        return
    
    # 初始化 hunter
    hunter = JobHunter()
    
    # 处理每个职位
    results = []
    for job_data in scraped_jobs:
        enriched = enrich_job_data(job_data)
        result = hunter.process_new_job(enriched)
        results.append(result)
    
    # 统计
    print("\n" + "="*70)
    print("[RESULTS] Processing Results")
    print("="*70)
    
    stats = {}
    for r in results:
        status = r['status']
        stats[status] = stats.get(status, 0) + 1
    
    print(f"  [PASS] Passed filter: {stats.get('pending', 0)}")
    print(f"  [FILTERED] Filtered out: {stats.get('filtered', 0)}")
    
    # 显示高优先级职位
    to_review = hunter.store.get_pending_to_review()
    if to_review:
        print(f"\n  [HIGH PRIORITY] Jobs to review (>= {Config.MIN_SCORE_TO_REVIEW} points):")
        for job in to_review[:5]:  # 只显示前5个
            status = "[OK] Resume ready" if job.resume_path else "[PENDING] Resume pending"
            print(f"    [{job.score}] {job.title} @ {job.company} - {status}")
        
        if len(to_review) > 5:
            print(f"    ... and {len(to_review) - 5} more")
    
    # 最终统计
    final_stats = hunter.store.get_stats()
    print(f"\n  [QUEUE] Current Queue:")
    print(f"     Pending: {final_stats['pending']}")
    print(f"     To Review: {final_stats['to_review']}")
    print(f"     Applied: {final_stats['applied']}")
    
    print("\n" + "="*70)
    print("[DONE] Run `python simplified_hunter.py review` to start reviewing")
    print("="*70)

if __name__ == '__main__':
    main()
