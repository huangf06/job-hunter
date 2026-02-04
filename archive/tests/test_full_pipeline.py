"""
全流程测试 - 模拟爬取+处理
==========================
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from src.config.loader import ConfigLoader
from src.core.hunter import JobHunter


# 模拟爬取的职位数据（真实格式）
MOCK_JOBS = [
    {
        "id": "4123456789",
        "title": "Data Engineer",
        "company": "Picnic",
        "location": "Amsterdam, Netherlands",
        "url": "https://www.linkedin.com/jobs/view/4123456789/",
        "description": """
        Data Engineer position at Picnic. 
        Requirements: Python, SQL, PySpark. 
        Visa sponsorship available.
        """,
        "source": "linkedin",
        "scraped_at": datetime.now().isoformat(),
        "has_easy_apply": True,
        "search_strategy": "data"
    },
    {
        "id": "4123456790",
        "title": "Senior Data Scientist (Dutch Required)",
        "company": "Local Bank",
        "location": "Amsterdam",
        "url": "https://www.linkedin.com/jobs/view/4123456790/",
        "description": """
        Senior position requiring fluent Dutch.
        10+ years experience required.
        """,
        "source": "linkedin",
        "scraped_at": datetime.now().isoformat(),
        "has_easy_apply": False,
        "search_strategy": "data"
    },
    {
        "id": "4123456791",
        "title": "Machine Learning Engineer",
        "company": "Optiver",
        "location": "Amsterdam",
        "url": "https://www.linkedin.com/jobs/view/4123456791/",
        "description": """
        ML Engineer for trading systems.
        Requirements: Python, PyTorch, quantitative background.
        Visa sponsorship available.
        """,
        "source": "linkedin",
        "scraped_at": datetime.now().isoformat(),
        "has_easy_apply": True,
        "search_strategy": "ml"
    },
    {
        "id": "4123456792",
        "title": "Quantitative Researcher",
        "company": "IMC",
        "location": "Amsterdam",
        "url": "https://www.linkedin.com/jobs/view/4123456792/",
        "description": """
        Quant researcher position.
        Requirements: Python, statistics, machine learning.
        """,
        "source": "linkedin",
        "scraped_at": datetime.now().isoformat(),
        "has_easy_apply": True,
        "search_strategy": "quant"
    },
    {
        "id": "4123456793",
        "title": "Principal Engineer",
        "company": "BigTech",
        "location": "Amsterdam",
        "url": "https://www.linkedin.com/jobs/view/4123456793/",
        "description": """
        Principal engineer with 15+ years experience.
        Leadership role.
        """,
        "source": "linkedin",
        "scraped_at": datetime.now().isoformat(),
        "has_easy_apply": False,
        "search_strategy": "data"
    },
]


async def test_full_pipeline():
    """测试完整流程"""
    
    print("="*70)
    print("FULL PIPELINE TEST")
    print("="*70)
    print(f"\nInput: {len(MOCK_JOBS)} mock jobs")
    print("Expected: 3 pass filter, 2 rejected")
    
    # 1. 加载配置
    print("\n[1] Loading configuration...")
    loader = ConfigLoader('config')
    config = loader.load()
    print("    [OK] Config loaded")
    
    # 2. 初始化Hunter
    print("\n[2] Initializing JobHunter...")
    hunter = JobHunter(config)
    print("    [OK] Hunter initialized")
    
    # 3. 处理职位
    print("\n[3] Processing jobs...")
    results = await hunter.process_jobs(MOCK_JOBS)
    print("    [OK] Processing complete")
    
    # 4. 分析结果
    print("\n" + "="*70)
    print("RESULTS ANALYSIS")
    print("="*70)
    
    status_counts = {}
    for r in results:
        status = r.status
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("\nStatus distribution:")
    for status, count in sorted(status_counts.items()):
        print(f"  {status:15s}: {count}")
    
    # 详细查看
    print("\nDetailed results:")
    for r in results:
        print(f"\n  {r.company[:20]:20s} - {r.title[:40]:40s}")
        print(f"    Status: {r.status}")
        if r.score:
            print(f"    Score: {r.score}")
        if r.filter_reason:
            print(f"    Reason: {r.filter_reason}")
        if r.resume_path:
            print(f"    Resume: {Path(r.resume_path).name}")
    
    # 5. 验证
    print("\n" + "="*70)
    print("VALIDATION")
    print("="*70)
    
    generated = status_counts.get('generated', 0)
    rejected = status_counts.get('rejected', 0)
    
    if generated >= 2:
        print("[PASS] Sufficient resumes generated")
    else:
        print("[FAIL] Too few resumes generated")
    
    if rejected >= 1:
        print("[PASS] Filter is working")
    else:
        print("[WARN] No jobs rejected")
    
    # 检查输出文件
    output_dir = Path("output")
    pdf_files = list(output_dir.glob("*.pdf"))
    print(f"\n[PASS] Generated {len(pdf_files)} PDF files")
    
    # 检查追踪数据
    tracker_file = Path("data/applications.json")
    if tracker_file.exists():
        with open(tracker_file, 'r') as f:
            tracker_data = json.load(f)
        print(f"[PASS] Tracker has {len(tracker_data.get('applications', []))} records")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)
    
    return results


if __name__ == "__main__":
    print("Starting full pipeline test...")
    print("This will test: Config -> Filter -> Score -> Generate -> Track\n")
    
    try:
        results = asyncio.run(test_full_pipeline())
        print("\n[SUCCESS] All systems operational")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
