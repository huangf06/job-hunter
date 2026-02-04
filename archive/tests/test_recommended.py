"""
快速测试推荐配置
================
"""

import asyncio
import time
from src.modules.crawler.linkedin import LinkedInScraper

async def test_recommended():
    """测试推荐配置"""
    
    # 推荐配置的3个策略
    strategies = [
        ("quant", "quantitative researcher", 3),      # 只测试3个
        ("ml", "machine learning engineer", 3),
        ("data", "data engineer", 3),
    ]
    
    scraper = LinkedInScraper(headless=False)
    all_jobs = []
    
    print("="*70)
    print("TESTING RECOMMENDED CONFIGURATION")
    print("="*70)
    print(f"Strategies: {len(strategies)}")
    print(f"Jobs per strategy: 3 (reduced for testing)")
    print(f"Delay: 15s between strategies")
    print("="*70)
    
    start_total = time.time()
    
    for i, (name, term, max_jobs) in enumerate(strategies, 1):
        print(f"\n[{i}/{len(strategies)}] Strategy: {name}")
        print(f"  Term: {term}")
        print(f"  Max jobs: {max_jobs}")
        
        start = time.time()
        
        try:
            jobs = await scraper.scrape_search_results(
                search_term=term,
                location="Netherlands",
                max_jobs=max_jobs,
                easy_apply_only=True,
                time_range="r86400"
            )
            
            elapsed = time.time() - start
            
            print(f"  [OK] Found: {len(jobs)} jobs")
            print(f"  [OK] Time: {elapsed:.1f}s")
            
            if jobs:
                print(f"  Sample: {jobs[0]['title'][:50]} @ {jobs[0]['company'][:30]}")
                for job in jobs:
                    job['search_strategy'] = name
                all_jobs.extend(jobs)
            
        except Exception as e:
            print(f"  [ERROR] {e}")
        
        # 策略间延迟
        if i < len(strategies):
            print(f"  Waiting 15s...")
            await asyncio.sleep(15)
    
    total_time = time.time() - start_total
    
    # 汇总
    print(f"\n{'='*70}")
    print("TEST RESULTS")
    print(f"{'='*70}")
    print(f"Total jobs found: {len(all_jobs)}")
    print(f"Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    print(f"Avg time/job: {total_time/len(all_jobs):.1f}s" if all_jobs else "N/A")
    
    # 去重
    unique = {}
    for job in all_jobs:
        key = f"{job['title']}-{job['company']}"
        unique[key] = job
    
    print(f"Unique jobs: {len(unique)}")
    print(f"Duplicates: {len(all_jobs) - len(unique)}")
    
    # 保存
    if all_jobs:
        scraper.save_jobs(all_jobs, "test_recommended_results.json")
    
    print(f"\n{'='*70}")
    print("ASSESSMENT")
    print(f"{'='*70}")
    
    if len(unique) >= 5:
        print("[SUCCESS] Found sufficient jobs")
        print("[SUCCESS] Strategy is working")
    else:
        print("[WARNING] Low job count")
        print("  Consider adjusting keywords")
    
    if total_time < 120:
        print("[GOOD] Fast execution")
    elif total_time < 300:
        print("[GOOD] Normal speed")
    else:
        print("[WARNING] Slow, consider reducing strategies")
    
    print(f"\nRecommendation: {'PROCEED' if len(unique) >= 5 else 'ADJUST'}")

if __name__ == "__main__":
    print("Starting test...")
    print("This will run 3 strategies with 15s delay")
    print("Estimated time: 2-4 minutes\n")
    
    asyncio.run(test_recommended())
