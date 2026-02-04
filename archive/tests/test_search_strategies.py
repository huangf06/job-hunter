"""
搜索策略测试 - 验证最佳方案
============================
"""

import asyncio
import time
from pathlib import Path
from src.config.loader import ConfigLoader
from src.modules.crawler.linkedin import LinkedInScraper


async def test_single_strategy(scraper, name, term, max_jobs, delay):
    """测试单个搜索策略"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Term: {term}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    jobs = await scraper.scrape_search_results(
        search_term=term,
        location="Netherlands",
        max_jobs=max_jobs,
        easy_apply_only=True,
        time_range="r86400"
    )
    
    elapsed = time.time() - start_time
    
    print(f"\nResults:")
    print(f"  Jobs found: {len(jobs)}")
    print(f"  Time: {elapsed:.1f}s")
    print(f"  Avg time/job: {elapsed/len(jobs):.1f}s" if jobs else "  N/A")
    
    # 显示前3个职位
    if jobs:
        print(f"\n  Sample jobs:")
        for i, job in enumerate(jobs[:3], 1):
            print(f"    {i}. {job['title'][:50]} @ {job['company'][:30]}")
    
    return {
        'name': name,
        'term': term,
        'jobs_found': len(jobs),
        'time': elapsed,
        'jobs': jobs
    }


async def test_strategies():
    """测试多个搜索策略"""
    
    # 测试配置
    test_strategies = [
        ("quant", "quantitative researcher", 5),
        ("ml", "machine learning engineer", 5),
        ("data", "data engineer", 5),
    ]
    
    scraper = LinkedInScraper(headless=False)
    results = []
    
    print("="*60)
    print("LINKEDIN SEARCH STRATEGY TEST")
    print("="*60)
    print(f"\nTesting {len(test_strategies)} strategies")
    print(f"Strategy delay: 30s")
    
    for i, (name, term, max_jobs) in enumerate(test_strategies, 1):
        result = await test_single_strategy(scraper, name, term, max_jobs, 30)
        results.append(result)
        
        # 策略间延迟
        if i < len(test_strategies):
            print(f"\nWaiting 30s before next strategy...")
            await asyncio.sleep(30)
    
    # 汇总
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    total_jobs = sum(r['jobs_found'] for r in results)
    total_time = sum(r['time'] for r in results) + 60  # 加上等待时间
    
    for r in results:
        print(f"{r['name']:10s}: {r['jobs_found']:2d} jobs ({r['time']:.1f}s)")
    
    print(f"{'-'*60}")
    print(f"{'Total':10s}: {total_jobs:2d} jobs ({total_time:.1f}s)")
    print(f"\nEstimated daily time: {total_time/60:.1f} minutes")
    print(f"Estimated daily jobs: {total_jobs}")
    
    # 风险评估
    print(f"\n{'='*60}")
    print("RISK ASSESSMENT")
    print(f"{'='*60}")
    
    if total_jobs > 30:
        print("⚠️  Job count > 30, risk: MEDIUM")
    else:
        print("✓ Job count <= 30, risk: LOW")
    
    if total_time > 300:  # 5分钟
        print("⚠️  Time > 5min, consider reducing strategies")
    else:
        print("✓ Time < 5min, acceptable")
    
    return results


async def main():
    """主测试"""
    try:
        results = await test_strategies()
        
        # 保存结果
        import json
        from datetime import datetime
        
        output = {
            "test_date": datetime.now().isoformat(),
            "results": [
                {
                    "name": r['name'],
                    "term": r['term'],
                    "jobs_found": r['jobs_found'],
                    "time": r['time']
                }
                for r in results
            ]
        }
        
        with open("data/search_test_results.json", "w") as f:
            json.dump(output, f, indent=2)
        
        print(f"\nResults saved to: data/search_test_results.json")
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting search strategy test...")
    print("This will test 3 strategies with 30s delay between them")
    print("Estimated time: 3-5 minutes\n")
    
    asyncio.run(main())
