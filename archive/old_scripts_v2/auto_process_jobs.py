#!/usr/bin/env python3
"""
全自动职位处理流水线
- 读取所有抓取的职位
- 自动分类角色
- 生成定制简历
- 输出申请清单
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from job_hunter_v42 import JobHunterV42

def process_all_jobs():
    """处理所有抓取的职位"""
    hunter = JobHunterV42()
    
    leads_dir = Path("data/leads")
    output_dir = Path("output") / datetime.now().strftime("%Y%m%d_%H%M")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_jobs = []
    
    # 读取 LinkedIn 职位
    linkedin_file = leads_dir / "linkedin_jobs_20260204_1310.json"
    if linkedin_file.exists():
        with open(linkedin_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            all_jobs.extend(data.get('jobs', []))
        print(f"[LOAD] LinkedIn: {len(data.get('jobs', []))} jobs")
    
    print(f"\n{'='*70}")
    print(f"AUTO PROCESSING {len(all_jobs)} JOBS")
    print(f"{'='*70}\n")
    
    results = []
    
    for i, job in enumerate(all_jobs, 1):
        print(f"\n[{i}/{len(all_jobs)}] Processing: {job['title']} @ {job['company']}")
        print("-" * 70)
        
        try:
            result = hunter.process_job(
                title=job['title'],
                description=job.get('description', ''),
                company=job['company'],
                output_dir=str(output_dir)
            )
            
            result['original_url'] = job.get('url', '')
            results.append(result)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            continue
    
    # 生成申请清单
    manifest = {
        'generated_at': datetime.now().isoformat(),
        'total_jobs': len(all_jobs),
        'successful': len(results),
        'applications': results
    }
    
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    print(f"\n{'='*70}")
    print("PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"\nTotal jobs: {len(all_jobs)}")
    print(f"Successful: {len(results)}")
    print(f"Failed: {len(all_jobs) - len(results)}")
    print(f"\nOutput directory: {output_dir}")
    print(f"Manifest: {manifest_file}")
    
    # 按角色分组
    by_role = {}
    for r in results:
        role = r['role']
        by_role.setdefault(role, []).append(r)
    
    print(f"\nBy Role:")
    for role, jobs in by_role.items():
        print(f"  {role}: {len(jobs)} jobs")
        for j in jobs[:3]:
            print(f"    - {j['title']} @ {j['company']}")
    
    return results

if __name__ == "__main__":
    process_all_jobs()
