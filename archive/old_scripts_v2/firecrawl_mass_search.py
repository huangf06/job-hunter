#!/usr/bin/env python3
"""
快速职位搜索 - Firecrawl + 多平台
"""
import json
import os
import sys
import urllib.request
from urllib.error import HTTPError
from datetime import datetime

FIRECRAWL_API_KEY = "fc-985a28c84caf4eb3a1e2a60e2618d757"

# 更多关键词，更高limit
JOB_QUERIES = [
    ("Data Engineer Amsterdam", 20),
    ("Data Engineer Netherlands", 20),
    ("Machine Learning Engineer Amsterdam", 20),
    ("ML Engineer Netherlands", 20),
    ("Data Scientist Amsterdam", 20),
    ("AI Engineer Netherlands", 20),
    ("Quantitative Researcher Amsterdam", 15),
    ("Python Data Engineer Netherlands", 15),
    ("AWS Data Engineer Amsterdam", 15),
    ("Spark Data Engineer Netherlands", 15),
]


def search_firecrawl(query: str, limit: int = 10):
    """Search using Firecrawl API."""
    url = "https://api.firecrawl.dev/v1/search"
    
    data = json.dumps({
        "query": query,
        "limit": limit,
        "lang": "en",
        "country": "nl"
    }).encode()
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"  Error: {e}")
        return None


def run_mass_search():
    """Run comprehensive job search."""
    print("=" * 70)
    print("MASS JOB SEARCH - Firecrawl")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Queries: {len(JOB_QUERIES)}")
    print("=" * 70)
    
    all_results = []
    
    for query, limit in JOB_QUERIES:
        print(f"\nSearching: {query} (limit: {limit})...")
        result = search_firecrawl(query, limit=limit)
        
        if result and result.get("success") and "data" in result:
            items = result["data"]
            print(f"  Found {len(items)} results")
            for item in items:
                all_results.append({
                    'title': item.get('title', 'N/A'),
                    'url': item.get('url', 'N/A'),
                    'description': item.get('description', '')[:500]
                })
        else:
            print("  No results")
    
    # 去重
    unique_results = []
    seen_urls = set()
    for r in all_results:
        url = r['url']
        if url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)
    
    # 保存
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_found': len(all_results),
        'unique_jobs': len(unique_results),
        'jobs': unique_results
    }
    
    output_file = 'data/leads/firecrawl_mass_jobs.json'
    os.makedirs('data/leads', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'=' * 70}")
    print(f"RESULTS:")
    print(f"  Total found: {len(all_results)}")
    print(f"  Unique jobs: {len(unique_results)}")
    print(f"  Saved to: {output_file}")
    print(f"{'=' * 70}")
    
    # 显示前10个
    print(f"\nTop 10 jobs:")
    for i, job in enumerate(unique_results[:10], 1):
        print(f"{i}. {job['title'][:60]}")
    
    return output


if __name__ == "__main__":
    run_mass_search()
