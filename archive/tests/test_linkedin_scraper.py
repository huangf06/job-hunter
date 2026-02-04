# Test LinkedIn scraper
import asyncio
from src.modules.crawler.linkedin import LinkedInScraper

async def test():
    print("Starting LinkedIn scraper test...")
    print("This will open a browser and scrape real jobs from LinkedIn")
    print("="*60)
    
    scraper = LinkedInScraper(headless=False)  # headless=False 可以看到浏览器
    
    jobs = await scraper.scrape_search_results(
        search_term="data scientist",
        location="Netherlands",
        max_jobs=5
    )
    
    print(f"\n{'='*60}")
    print(f"SCRAPED {len(jobs)} JOBS")
    print(f"{'='*60}\n")
    
    for i, job in enumerate(jobs, 1):
        easy_apply = "[EASY APPLY]" if job.get('has_easy_apply') else "[EXTERNAL]"
        print(f"{i}. {easy_apply} {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   URL: {job['url'][:80]}...")
        if job.get('description'):
            desc = job['description'][:150].replace('\n', ' ')
            print(f"   Desc: {desc}...")
        print()
    
    # 保存
    if jobs:
        filepath = scraper.save_jobs(jobs)
        print(f"Saved to: {filepath}")

asyncio.run(test())
