#!/usr/bin/env python3
"""
LinkedIn 增量爬取器 v3.2 - 基于 v6 的增量版本
===========================================

直接用 v6 的成熟逻辑，只添加：
1. 页数限制（避免抓太多旧职位）
2. 数据库预检查去重

Usage:
    python scraper_incremental_v32.py --profile all --max-pages 4
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

# 直接导入 v6 的类
sys.path.insert(0, str(Path(__file__).parent))
from linkedin_scraper_v6 import LinkedInScraperV6, SearchConfig, PROJECT_ROOT, DATA_DIR, CONFIG_DIR, COOKIES_FILE, PROFILES_FILE

# 导入数据库
sys.path.insert(0, str(PROJECT_ROOT))
from src.db.job_db import JobDatabase


class IncrementalScraperV32(LinkedInScraperV6):
    """基于 v6 的增量爬取器"""
    
    def __init__(self, config: SearchConfig, headless: bool = False, use_cdp: bool = False, 
                 max_pages_per_profile: int = 4):
        # 调用父类初始化
        super().__init__(config, headless, use_cdp)
        self.max_pages_per_profile = max_pages_per_profile
        self.db = JobDatabase()
        
        # 统计
        self.stats = {
            'scraped': 0,
            'new_jobs': 0,
            'duplicates_skipped': 0,
            'jd_fetched': 0,
            'jd_skipped': 0,
            'start_time': datetime.now().isoformat(),
        }
        
    def _preload_existing_jobs(self, urls: List[str]) -> Set[str]:
        """预加载数据库中已存在的职位ID"""
        if not urls:
            return set()
            
        from src.db.job_db import JobDatabase
        db = JobDatabase()
        
        # 批量查询
        job_ids = [db.generate_job_id(url) for url in urls if url]
        existing = set()
        
        # 分块查询避免SQL变量限制
        CHUNK_SIZE = 900
        for i in range(0, len(job_ids), CHUNK_SIZE):
            chunk = job_ids[i:i+CHUNK_SIZE]
            placeholders = ','.join(['?'] * len(chunk))
            try:
                rows = db.execute(
                    f"SELECT id FROM jobs WHERE id IN ({placeholders})",
                    chunk
                )
                existing.update(row['id'] for row in rows)
            except Exception as e:
                print(f"  [WARN] DB query failed: {e}")
                
        return existing
        
    async def run_profile_incremental(self, profile_name: str, fetch_jd: bool = True, 
                                     save_to_db: bool = False) -> List[Dict]:
        """增量运行单个 profile"""
        profile = self.config.get_profile(profile_name)
        if not profile:
            print(f"[Error] Profile not found: {profile_name}")
            return []

        print(f"\n{'='*70}")
        print(f"[Profile] {profile.get('name', profile_name)} (Incremental Mode)")
        print(f"{'='*70}")

        queries = profile.get("queries", [])
        location = profile.get("location_override", self.config.defaults.get("location", "Netherlands"))
        max_jobs = profile.get("max_jobs_override", self.config.defaults.get("max_jobs", 50))
        
        # 限制最大页数
        max_jobs = min(max_jobs, self.max_pages_per_profile * 25)

        profile_jobs = []

        for i, query in enumerate(queries, 1):
            keywords = query.get("keywords", "")
            description = query.get("description", keywords[:30])

            print(f"\n[Query {i}/{len(queries)}] {description}")
            print(f"  Keywords: {keywords[:60]}{'...' if len(keywords) > 60 else ''}")

            # 调用父类方法爬取
            jobs = await self._scrape_single_query(keywords, location, max(1, max_jobs // len(queries)))

            # 黑名单过滤
            filtered_jobs = self._filter_blacklist(jobs)
            
            # 增量去重：检查数据库
            urls = [j['url'] for j in filtered_jobs]
            existing_ids = self._preload_existing_jobs(urls)
            
            new_jobs = []
            for job in filtered_jobs:
                job_id = self.db.generate_job_id(job['url'])
                if job_id in existing_ids:
                    self.stats['duplicates_skipped'] += 1
                else:
                    new_jobs.append(job)
                    
            print(f"  -> Found: {len(filtered_jobs)} jobs, New: {len(new_jobs)} (skipped {self.stats['duplicates_skipped']} duplicates)")
            
            profile_jobs.extend(new_jobs)

            # 延迟
            if i < len(queries):
                print("  -> Waiting 5s before next query...")
                await asyncio.sleep(5)

        # 只抓新职位的 JD
        if fetch_jd and new_jobs:
            print(f"\n[JD] Fetching descriptions for {len(new_jobs)} new jobs...")
            await self.fetch_job_descriptions(new_jobs)
            self.stats['jd_fetched'] = len(new_jobs)

        # 保存到数据库
        if save_to_db and new_jobs:
            print(f"\n[Database] Saving {len(new_jobs)} new jobs...")
            for job in new_jobs:
                if not job.get('search_profile'):
                    job['search_profile'] = profile_name
                try:
                    _, was_inserted = self.db.insert_job(job)
                    if was_inserted:
                        self.stats['new_jobs'] += 1
                except Exception as e:
                    print(f"  ! Failed: {e}")

        self.stats['scraped'] += len(profile_jobs)
        return profile_jobs

    async def run(self, profile: str = 'all') -> Dict:
        """主运行函数"""
        print(f"\n{'='*70}")
        print(f"LinkedIn Incremental Scraper v3.2 (Based on v6)")
        print(f"Max pages per profile: {self.max_pages_per_profile}")
        print(f"{'='*70}\n")
        
        # 登录（父类方法）
        if not await self.login_with_cookies():
            print("[FATAL] Login failed")
            return self.stats
            
        # 确定 profiles
        if profile == 'all':
            profiles_to_run = self.config.get_enabled_profiles()
        else:
            profiles_to_run = [profile]
            
        print(f"[Profiles] Running: {', '.join(profiles_to_run)}\n")
        
        # 运行
        for profile_name in profiles_to_run:
            await self.run_profile_incremental(profile_name, fetch_jd=True, save_to_db=True)
            
        # 统计
        self.stats['end_time'] = datetime.now().isoformat()
        print(f"\n{'='*70}")
        print(f"Complete: {self.stats['new_jobs']} new jobs")
        print(f"{'='*70}")
        
        return self.stats


def main():
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', default='all')
    parser.add_argument('--max-pages', type=int, default=4)
    parser.add_argument('--headless', action='store_true', default=True)
    parser.add_argument('--output', default='stats.json')
    
    args = parser.parse_args()
    
    async def run():
        config = SearchConfig()
        scraper = IncrementalScraperV32(config, headless=args.headless, 
                                       max_pages_per_profile=args.max_pages)
        async with scraper:
            stats = await scraper.run(profile=args.profile)
            with open(args.output, 'w') as f:
                json.dump(stats, f, indent=2)
                
    asyncio.run(run())


if __name__ == '__main__':
    main()
