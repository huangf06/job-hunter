"""
测试 JD 获取和数据库写入功能
==============================

Usage:
    python test_jd_pipeline.py
"""

import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.db.job_db import JobDatabase


def test_database_jd():
    """测试数据库中的 JD 数据"""
    print("=" * 70)
    print("Database JD Data Test")
    print("=" * 70)

    db = JobDatabase()

    # 获取所有职位
    with db._get_conn() as conn:
        cursor = conn.execute('''
            SELECT id, title, company, LENGTH(description) as desc_len,
                   LENGTH(raw_data) as raw_len, scraped_at
            FROM jobs
            ORDER BY scraped_at DESC
            LIMIT 20
        ''')
        jobs = cursor.fetchall()

    print(f"\nTotal {len(jobs)} jobs in database (recent 20):")
    print("-" * 70)

    with_jd = 0
    without_jd = 0

    for row in jobs:
        job_id, title, company, desc_len, raw_len, scraped_at = row
        has_jd = "[OK]" if desc_len and desc_len > 0 else "[NO]"
        if desc_len and desc_len > 0:
            with_jd += 1
        else:
            without_jd += 1

        title_short = (title or "")[:35]
        company_short = (company or "")[:20]
        print(f"{has_jd} {job_id} | {title_short:35s} | {company_short:20s} | JD: {desc_len or 0:5d} chars")

    print("-" * 70)
    print(f"With JD: {with_jd}")
    print(f"Without JD: {without_jd}")

    return with_jd, without_jd


def test_json_jd():
    """测试 JSON 文件中的 JD 数据"""
    print("\n" + "=" * 70)
    print("JSON File JD Data Test")
    print("=" * 70)

    data_dir = PROJECT_ROOT / "data"
    json_files = list(data_dir.glob("linkedin_*.json"))

    print(f"\nFound {len(json_files)} JSON files:")

    for json_file in sorted(json_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        jobs = data.get('jobs', [])
        with_jd = sum(1 for j in jobs if j.get('description'))
        total = len(jobs)

        print(f"  {json_file.name:50s} | {with_jd}/{total} with JD")

        # Show first job with JD
        for job in jobs:
            if job.get('description'):
                print(f"    Example: {job['title'][:40]}... | JD: {len(job['description'])} chars")
                break


def test_insert_with_jd():
    """测试插入带 JD 的职位"""
    print("\n" + "=" * 70)
    print("Test Insert Job with JD")
    print("=" * 70)

    db = JobDatabase()

    # 测试数据
    test_job = {
        "title": "Test ML Engineer",
        "company": "Test Company",
        "location": "Amsterdam",
        "url": "https://linkedin.com/jobs/view/test123",
        "description": "This is a test job description. " * 50,  # 长描述
        "source": "test",
        "scraped_at": "2026-02-04T20:00:00",
        "search_profile": "test",
        "search_query": "test"
    }

    # 删除已存在的测试职位
    job_id = db.generate_job_id(test_job['url'])
    with db._get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))

    # 插入测试职位
    inserted_id = db.insert_job(test_job)
    print(f"\nInserted test job ID: {inserted_id}")

    # 验证
    job = db.get_job(inserted_id)
    if job:
        desc_len = len(job.get('description', ''))
        print(f"Read from database:")
        print(f"  Title: {job['title']}")
        print(f"  Company: {job['company']}")
        print(f"  Description length: {desc_len} chars")

        if desc_len > 0:
            print("  [OK] JD saved to database!")
        else:
            print("  [FAIL] JD not saved to database!")

    # 清理
    with db._get_conn() as conn:
        conn.execute("DELETE FROM jobs WHERE id = ?", (inserted_id,))
    print("\nTest data cleaned up")


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("JD Data Integrity Test")
    print("=" * 70)

    # 测试1: 数据库中的 JD
    db_with_jd, db_without_jd = test_database_jd()

    # 测试2: JSON 文件中的 JD
    test_json_jd()

    # 测试3: 插入功能
    test_insert_with_jd()

    # 总结
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    if db_without_jd > 0:
        print(f"\n[WARNING] Found {db_without_jd} jobs without JD data")
        print("\nPossible causes:")
        print("  1. Crawler ran with --no-jd flag")
        print("  2. JD fetch function failed")
        print("  3. Description field lost during JSON import")
        print("\nRecommendations:")
        print("  1. Re-run crawler without --no-jd flag")
        print("  2. Use linkedin_scraper_v6_db.py --save-to-db")
        print("  3. Check crawler logs to verify JD fetch success")
    else:
        print("\n[OK] All jobs have JD data")


if __name__ == "__main__":
    main()
