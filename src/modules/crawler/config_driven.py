"""
多平台爬虫 - 配置驱动版（支持无限制）
======================================
从YAML配置读取平台设置，不人为限制职位数量
"""

import asyncio
from typing import List, Dict, Optional
from pathlib import Path

from .linkedin import LinkedInScraper
from .iamexpat import IamExpatScraper


class ConfigDrivenScraper:
    """配置驱动的多平台爬虫"""
    
    SCRAPER_CLASSES = {
        "linkedin": LinkedInScraper,
        "iamexpat": IamExpatScraper,
    }
    
    def __init__(self, crawler_config: Dict):
        self.config = crawler_config
        self.platforms_config = crawler_config.get('platforms', {})
        self.global_config = crawler_config.get('global', {})
    
    def get_enabled_platforms(self) -> List[str]:
        """获取启用的平台列表"""
        enabled = []
        for name, config in self.platforms_config.items():
            if config.get('enabled', False):
                enabled.append(name)
        enabled.sort(key=lambda x: self.platforms_config[x].get('priority', 999))
        return enabled
    
    async def scrape_platform(self, platform: str, search_term: str = None) -> List[Dict]:
        """爬取单个平台"""
        if platform not in self.SCRAPER_CLASSES:
            print(f"[Scraper] Unknown platform: {platform}")
            return []
        
        platform_config = self.platforms_config.get(platform, {})
        if not platform_config.get('enabled', False):
            print(f"[Scraper] Platform {platform} is disabled")
            return []
        
        print(f"\n{'='*60}")
        print(f"Scraping {platform.upper()}")
        print(f"{'='*60}")
        
        try:
            scraper_class = self.SCRAPER_CLASSES[platform]
            behavior = platform_config.get('behavior', {})
            headless = behavior.get('headless', True)
            
            scraper = scraper_class(headless=headless)
            
            if platform == 'linkedin':
                all_jobs = await scraper.scrape_with_config(platform_config)
            else:
                search_config = platform_config.get('search', [])
                all_jobs = []
                for strategy in search_config:
                    name = strategy.get('name', 'unknown')
                    term = strategy.get('term', '')
                    location = strategy.get('location', 'Netherlands')
                    # 不设置max_jobs则爬取所有
                    max_jobs = strategy.get('max_jobs')
                    
                    print(f"\n  Strategy: {name}")
                    print(f"    Term: {term}")
                    print(f"    Max: {max_jobs if max_jobs else 'unlimited'}")
                    
                    jobs = await scraper.scrape_search_results(
                        search_term=term,
                        location=location,
                        max_jobs=max_jobs
                    )
                    
                    for job in jobs:
                        job['search_strategy'] = name
                    all_jobs.extend(jobs)
                    
                    # 策略间延迟
                    delay = behavior.get('strategy_delay', 10)
                    await asyncio.sleep(delay)
            
            if all_jobs:
                scraper.save_jobs(all_jobs)
            
            return all_jobs
            
        except Exception as e:
            print(f"[Scraper] Error scraping {platform}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def scrape_all(self, search_term: str = None) -> Dict[str, List[Dict]]:
        """爬取所有启用的平台"""
        platforms = self.get_enabled_platforms()
        
        if not platforms:
            print("[Scraper] No platforms enabled!")
            return {}
        
        print(f"[Scraper] Enabled platforms: {', '.join(platforms)}")
        
        results = {}
        for platform in platforms:
            jobs = await self.scrape_platform(platform, search_term)
            results[platform] = jobs
            
            # 平台间延迟
            if platform != platforms[-1]:
                delay = self.global_config.get('concurrency', {}).get('delay_between_platforms', 30)
                print(f"Waiting {delay}s before next platform...")
                await asyncio.sleep(delay)
        
        return results
    
    def print_summary(self, results: Dict[str, List[Dict]]):
        """打印汇总"""
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        
        total = 0
        for platform, jobs in results.items():
            print(f"  {platform:15s}: {len(jobs):3d} jobs")
            total += len(jobs)
        
        print(f"  {'TOTAL':15s}: {total:3d} jobs")
        print(f"{'='*60}\n")
    
    def get_all_jobs(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """合并所有平台的职位"""
        all_jobs = []
        for platform, jobs in results.items():
            for job in jobs:
                job['source_platform'] = platform
            all_jobs.extend(jobs)
        
        # 去重
        if self.global_config.get('deduplication', {}).get('enabled', True):
            all_jobs = self._deduplicate(all_jobs)
        
        return all_jobs
    
    def _deduplicate(self, jobs: List[Dict]) -> List[Dict]:
        """去重"""
        seen = set()
        unique = []
        
        for job in jobs:
            key = f"{job.get('title', '')}-{job.get('company', '')}"
            key_hash = hash(key.lower())
            
            if key_hash not in seen:
                seen.add(key_hash)
                unique.append(job)
        
        removed = len(jobs) - len(unique)
        if removed > 0:
            print(f"[Scraper] Removed {removed} duplicate jobs")
        
        return unique
