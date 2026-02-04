"""
多平台爬虫 - 统一入口
===================
支持 LinkedIn, IamExpat 等多个平台
"""

import asyncio
from typing import List, Dict
from pathlib import Path

from .linkedin import LinkedInScraper
from .iamexpat import IamExpatScraper


class MultiPlatformScraper:
    """多平台爬虫管理器"""
    
    # 支持的爬虫
    SCRAPERS = {
        "linkedin": LinkedInScraper,
        "iamexpat": IamExpatScraper,
    }
    
    def __init__(self, platforms: List[str] = None, headless: bool = True):
        """
        初始化
        
        Args:
            platforms: 要使用的平台列表，如 ["linkedin", "iamexpat"]
            headless: 是否使用无头模式
        """
        self.platforms = platforms or ["linkedin"]
        self.headless = headless
        self.results = {}
    
    async def scrape(self,
                     search_term: str,
                     location: str = "Netherlands",
                     max_jobs_per_platform: int = 10) -> Dict[str, List[Dict]]:
        """
        爬取多个平台
        
        Args:
            search_term: 搜索关键词
            location: 地点
            max_jobs_per_platform: 每个平台最大职位数
        
        Returns:
            {平台名: 职位列表}
        """
        all_jobs = {}
        
        for platform in self.platforms:
            if platform not in self.SCRAPERS:
                print(f"[MultiScraper] Unknown platform: {platform}")
                continue
            
            print(f"\n{'='*60}")
            print(f"Scraping {platform.upper()}")
            print(f"{'='*60}")
            
            try:
                scraper_class = self.SCRAPERS[platform]
                scraper = scraper_class(headless=self.headless)
                
                jobs = await scraper.scrape_search_results(
                    search_term=search_term,
                    location=location,
                    max_jobs=max_jobs_per_platform
                )
                
                all_jobs[platform] = jobs
                
                # 保存
                if jobs:
                    scraper.save_jobs(jobs)
                
            except Exception as e:
                print(f"[MultiScraper] Error scraping {platform}: {e}")
                all_jobs[platform] = []
        
        return all_jobs
    
    def get_all_jobs(self, results: Dict[str, List[Dict]]) -> List[Dict]:
        """合并所有平台的职位"""
        all_jobs = []
        for platform, jobs in results.items():
            for job in jobs:
                job['source_platform'] = platform  # 标记来源
            all_jobs.extend(jobs)
        return all_jobs
    
    def print_summary(self, results: Dict[str, List[Dict]]):
        """打印汇总"""
        print(f"\n{'='*60}")
        print("SCRAPING SUMMARY")
        print(f"{'='*60}")
        
        total = 0
        for platform, jobs in results.items():
            print(f"  {platform:12s}: {len(jobs):3d} jobs")
            total += len(jobs)
        
        print(f"  {'TOTAL':12s}: {total:3d} jobs")
        print(f"{'='*60}\n")


# ============== 使用示例 ==============

async def main():
    """测试多平台爬虫"""
    scraper = MultiPlatformScraper(
        platforms=["linkedin", "iamexpat"],
        headless=False
    )
    
    results = await scraper.scrape(
        search_term="data scientist",
        location="Netherlands",
        max_jobs_per_platform=5
    )
    
    scraper.print_summary(results)
    
    # 合并所有职位
    all_jobs = scraper.get_all_jobs(results)
    print(f"Total unique jobs: {len(all_jobs)}")


if __name__ == "__main__":
    asyncio.run(main())
