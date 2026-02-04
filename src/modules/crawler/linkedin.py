"""
LinkedIn爬虫 - 支持多搜索策略
=============================
从YAML配置读取布尔搜索组合
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright


class LinkedInScraper:
    """LinkedIn职位爬虫 - 支持多搜索策略"""
    
    def __init__(self, headless: bool = True, data_dir: str = "data/leads"):
        self.headless = headless
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.jobs = []
    
    async def scrape_search_results(self, 
                                    search_term: str = None,
                                    location: str = "Netherlands",
                                    max_jobs: int = 10,
                                    easy_apply_only: bool = True,
                                    time_range: str = "r86400") -> List[Dict]:
        """
        爬取LinkedIn搜索结果
        
        Args:
            search_term: 搜索关键词（支持布尔搜索语法）
            location: 地点
            max_jobs: 最大职位数
            easy_apply_only: 只爬Easy Apply职位
            time_range: 时间范围 (r86400=24h, r604800=7d)
        """
        from urllib.parse import urlencode, quote
        
        # 构建搜索URL
        params = {
            "location": location,
            "f_TPR": time_range,  # 过去24小时
            "sortBy": "DD"        # 最新优先
        }
        
        if easy_apply_only:
            params["f_AL"] = "true"  # Easy Apply only
        
        # 添加搜索词
        if search_term:
            params["keywords"] = search_term
        
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params, quote_via=quote)}"
        
        print(f"[LinkedIn] Opening: {url[:120]}...")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
                
                # 滚动加载更多
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(1)
                
                # 提取职位列表
                jobs = await self._extract_jobs_from_page(page)
                print(f"[LinkedIn] Found {len(jobs)} jobs on page")
                
                # 获取详细信息
                detailed_jobs = []
                # 如果不限制数量，处理所有找到的职位
                jobs_to_process = jobs[:max_jobs] if max_jobs else jobs
                total_jobs_str = str(max_jobs) if max_jobs else f"{len(jobs)}"
                for i, job in enumerate(jobs_to_process):
                    print(f"[LinkedIn] Processing {i+1}/{len(jobs_to_process)}: {job.get('title', 'N/A')[:50]}...")
                    detailed = await self._get_job_details(page, job)
                    if detailed:
                        detailed_jobs.append(detailed)
                    await asyncio.sleep(1)
                
                await browser.close()
                return detailed_jobs
                
            except Exception as e:
                print(f"[LinkedIn] Error: {e}")
                await browser.close()
                return []
    
    async def scrape_with_config(self, config: Dict) -> List[Dict]:
        """
        使用配置爬取 - 支持多搜索策略
        
        Args:
            config: 平台配置 (来自crawler.yaml)
        """
        all_jobs = []
        
        # 获取搜索策略
        search_strategies = config.get('search', [])
        if not search_strategies:
            # 兼容旧配置格式
            terms = config.get('search', {}).get('terms', [])
            search_strategies = [{'term': terms[0]}] if terms else []
        
        # 全局设置
        location = config.get('location', 'Netherlands')
        filters = config.get('filters', {})
        time_range = filters.get('time_range', 'r86400')
        # 不设置则默认为False，爬取所有职位
        easy_apply_only = filters.get('easy_apply_only', False)
        behavior = config.get('behavior', {})
        delay = behavior.get('request_delay', 2)
        
        print(f"[LinkedIn] {len(search_strategies)} search strategies configured")
        
        for i, strategy in enumerate(search_strategies, 1):
            name = strategy.get('name', f'strategy_{i}')
            term = strategy.get('term', '')
            max_jobs = strategy.get('max_jobs', 10)
            
            print(f"\n[LinkedIn] Strategy {i}/{len(search_strategies)}: {name}")
            print(f"  Query: {term[:80]}...")
            
            jobs = await self.scrape_search_results(
                search_term=term,
                location=location,
                max_jobs=max_jobs,
                easy_apply_only=easy_apply_only,
                time_range=time_range
            )
            
            # 标记搜索策略
            for job in jobs:
                job['search_strategy'] = name
            
            all_jobs.extend(jobs)
            
            # 策略间延迟
            if i < len(search_strategies):
                print(f"  Waiting {delay}s before next strategy...")
                await asyncio.sleep(delay)
        
        return all_jobs
    
    async def _extract_jobs_from_page(self, page) -> List[Dict]:
        """从页面提取职位列表"""
        jobs = []
        
        selectors = [
            "[data-job-id]",
            ".jobs-search__results-list > li",
            ".job-card-container",
            ".base-card",
        ]
        
        for selector in selectors:
            try:
                cards = await page.query_selector_all(selector)
                if cards:
                    for card in cards[:25]:
                        job = await self._parse_job_card(card)
                        if job:
                            jobs.append(job)
                    break
            except:
                continue
        
        return jobs
    
    async def _parse_job_card(self, card) -> Optional[Dict]:
        """解析单个职位卡片"""
        try:
            title_elem = await card.query_selector("h3, .job-card-list__title, a strong, .base-search-card__title")
            title = await title_elem.inner_text() if title_elem else ""
            
            company_elem = await card.query_selector(".job-card-container__company-name, h4, .base-search-card__subtitle")
            company = await company_elem.inner_text() if company_elem else ""
            
            location_elem = await card.query_selector(".job-card-container__metadata-item, .job-search-card__location")
            location = await location_elem.inner_text() if location_elem else ""
            
            link_elem = await card.query_selector("a[href*='/jobs/view/']")
            href = await link_elem.get_attribute("href") if link_elem else ""
            
            if href and not href.startswith("http"):
                href = f"https://www.linkedin.com{href}"
            
            job_id = ""
            if href:
                match = re.search(r"/jobs/view/[^/]+-?(\d+)", href)
                if match:
                    job_id = match.group(1)
            
            return {
                "id": job_id or f"li_{hash(title + company) % 1000000}",
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "url": href,
                "source": "linkedin",
                "scraped_at": datetime.now().isoformat(),
            }
        except:
            return None
    
    async def _get_job_details(self, page, job: Dict) -> Optional[Dict]:
        """获取职位详细信息"""
        try:
            if not job.get("url"):
                return job
            
            await page.goto(job["url"], wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            description_selectors = [
                ".jobs-description__content",
                ".description__text",
                "[data-test-id='job-description']",
                ".show-more-less-html__markup",
            ]
            
            description = ""
            for selector in description_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        description = await elem.inner_text()
                        if len(description) > 100:
                            break
                except:
                    continue
            
            has_easy_apply = False
            apply_selectors = [
                'button[data-control-name="jobdetails_topcard_inapply"]',
                ".jobs-apply-button",
                'button:has-text("Easy Apply")',
            ]
            
            for selector in apply_selectors:
                try:
                    btn = await page.query_selector(selector)
                    if btn:
                        is_visible = await btn.is_visible()
                        if is_visible:
                            has_easy_apply = True
                            break
                except:
                    continue
            
            job["description"] = description[:3000]
            job["has_easy_apply"] = has_easy_apply
            
            return job
            
        except Exception as e:
            print(f"[LinkedIn] Error getting details: {e}")
            return job
    
    def save_jobs(self, jobs: List[Dict], filename: str = None) -> Path:
        """保存职位到文件"""
        if not filename:
            filename = f"linkedin_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        filepath = self.data_dir / filename
        
        data = {
            "source": "linkedin",
            "scraped_at": datetime.now().isoformat(),
            "total": len(jobs),
            "jobs": jobs
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[LinkedIn] Saved {len(jobs)} jobs to: {filepath}")
        return filepath


# ============== 使用示例 ==============

async def main():
    """测试"""
    # 测试配置
    test_config = {
        "search": [
            {
                "name": "quant_ml",
                "term": '("Quant" OR "Quantitative") AND ("Machine Learning" OR "Deep Learning")',
                "max_jobs": 5
            }
        ],
        "location": "Netherlands",
        "filters": {
            "time_range": "r86400",
            "easy_apply_only": True
        },
        "behavior": {
            "request_delay": 2,
            "headless": False
        }
    }
    
    scraper = LinkedInScraper(headless=False)
    jobs = await scraper.scrape_with_config(test_config)
    
    if jobs:
        scraper.save_jobs(jobs)


if __name__ == "__main__":
    asyncio.run(main())
