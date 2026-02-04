"""
IamExpat Jobs 爬虫
==================
https://www.iamexpat.nl/career/jobs-netherlands
"""

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from playwright.async_api import async_playwright


class IamExpatScraper:
    """IamExpat Jobs 爬虫"""
    
    def __init__(self, headless: bool = True, data_dir: str = "data/leads"):
        self.headless = headless
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.jobs = []
    
    async def scrape_search_results(self,
                                    search_term: str = "data scientist",
                                    location: str = "Netherlands",
                                    max_jobs: int = 10) -> List[Dict]:
        """
        爬取 IamExpat 职位
        
        Args:
            search_term: 搜索关键词
            location: 地点（Netherlands/Amsterdam/Rotterdam等）
            max_jobs: 最大职位数
        """
        # IamExpat 搜索 URL
        search_query = search_term.replace(" ", "+")
        url = f"https://www.iamexpat.nl/career/jobs-netherlands?search={search_query}"
        
        if location and location.lower() != "netherlands":
            url += f"&location={location.replace(' ', '+')}"
        
        print(f"[IamExpat] Opening: {url}")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)  # 等待页面加载
                
                # 接受cookie（如果有）
                try:
                    cookie_btn = await page.query_selector('button:has-text("Accept"), button:has-text("I agree")')
                    if cookie_btn:
                        await cookie_btn.click()
                        await asyncio.sleep(2)
                except:
                    pass
                
                # 滚动加载更多
                for _ in range(3):
                    await page.evaluate("window.scrollBy(0, 800)")
                    await asyncio.sleep(1)
                
                # 提取职位列表
                jobs = await self._extract_jobs_from_page(page)
                print(f"[IamExpat] Found {len(jobs)} jobs")
                
                # 获取详细信息
                detailed_jobs = []
                for i, job in enumerate(jobs[:max_jobs]):
                    print(f"[IamExpat] Processing {i+1}/{min(len(jobs), max_jobs)}: {job.get('title', 'N/A')[:50]}...")
                    detailed = await self._get_job_details(page, job)
                    if detailed:
                        detailed_jobs.append(detailed)
                    await asyncio.sleep(1)
                
                await browser.close()
                return detailed_jobs
                
            except Exception as e:
                print(f"[IamExpat] Error: {e}")
                await browser.close()
                return []
    
    async def _extract_jobs_from_page(self, page) -> List[Dict]:
        """从页面提取职位列表"""
        jobs = []
        
        # IamExpat 的选择器
        selectors = [
            ".job-item",
            ".job-listing-item",
            "[data-job-id]",
            ".views-row",  # Drupal常见类
            ".job-card",
        ]
        
        for selector in selectors:
            try:
                cards = await page.query_selector_all(selector)
                if cards:
                    print(f"[IamExpat] Found {len(cards)} cards with selector: {selector}")
                    for card in cards[:25]:
                        job = await self._parse_job_card(card)
                        if job:
                            jobs.append(job)
                    break
            except Exception as e:
                continue
        
        # 如果没找到，尝试通用链接方式
        if not jobs:
            try:
                links = await page.query_selector_all('a[href*="/career/jobs-netherlands/"]')
                print(f"[IamExpat] Trying link-based extraction, found {len(links)} links")
                for link in links[:25]:
                    job = await self._parse_job_link(link)
                    if job:
                        jobs.append(job)
            except Exception as e:
                print(f"[IamExpat] Link extraction error: {e}")
        
        return jobs
    
    async def _parse_job_card(self, card) -> Optional[Dict]:
        """解析职位卡片"""
        try:
            # 标题
            title_elem = await card.query_selector("h2, h3, .job-title, .title")
            title = await title_elem.inner_text() if title_elem else ""
            
            # 公司
            company_elem = await card.query_selector(".company, .employer, .organization")
            company = await company_elem.inner_text() if company_elem else ""
            
            # 地点
            location_elem = await card.query_selector(".location, .job-location")
            location = await location_elem.inner_text() if location_elem else ""
            
            # 链接
            link_elem = await card.query_selector("a")
            href = await link_elem.get_attribute("href") if link_elem else ""
            
            if href and not href.startswith("http"):
                href = f"https://www.iamexpat.nl{href}"
            
            return {
                "id": f"ie_{hash(title + company) % 1000000}",
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip() or "Netherlands",
                "url": href,
                "source": "iamexpat",
                "scraped_at": datetime.now().isoformat(),
            }
        except Exception as e:
            return None
    
    async def _parse_job_link(self, link) -> Optional[Dict]:
        """从链接解析职位"""
        try:
            href = await link.get_attribute("href")
            if not href or "/career/jobs-netherlands/" not in href:
                return None
            
            # 获取文本
            text = await link.inner_text()
            
            # 尝试提取公司（通常在父元素中）
            parent = await link.evaluate("el => el.parentElement")
            company = ""
            
            return {
                "id": f"ie_{hash(text) % 1000000}",
                "title": text.strip()[:100],
                "company": company,
                "location": "Netherlands",
                "url": href if href.startswith("http") else f"https://www.iamexpat.nl{href}",
                "source": "iamexpat",
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
            
            # 提取描述
            description_selectors = [
                ".job-description",
                ".description",
                ".field--name-body",
                "[property='schema:description']",
                ".content .field-item",
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
            
            # 提取公司（如果在详情页有）
            if not job.get("company"):
                company_selectors = [
                    ".company-name",
                    ".employer",
                    ".organization",
                    "h1 + div",
                ]
                for selector in company_selectors:
                    try:
                        elem = await page.query_selector(selector)
                        if elem:
                            company = await elem.inner_text()
                            if company:
                                job["company"] = company.strip()
                                break
                    except:
                        continue
            
            job["description"] = description[:3000]
            
            return job
            
        except Exception as e:
            print(f"[IamExpat] Error getting details: {e}")
            return job
    
    def save_jobs(self, jobs: List[Dict], filename: str = None) -> Path:
        """保存职位到文件"""
        if not filename:
            filename = f"iamexpat_jobs_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        
        filepath = self.data_dir / filename
        
        data = {
            "source": "iamexpat",
            "scraped_at": datetime.now().isoformat(),
            "total": len(jobs),
            "jobs": jobs
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"[IamExpat] Saved {len(jobs)} jobs to: {filepath}")
        return filepath


# ============== 使用示例 ==============

async def main():
    """测试"""
    scraper = IamExpatScraper(headless=False)
    
    jobs = await scraper.scrape_search_results(
        search_term="data scientist",
        location="Netherlands",
        max_jobs=5
    )
    
    if jobs:
        scraper.save_jobs(jobs)
        
        print("\n" + "="*60)
        print("SAMPLE JOBS:")
        print("="*60)
        for i, job in enumerate(jobs[:3], 1):
            print(f"\n{i}. {job['title']}")
            print(f"   Company: {job['company']}")
            print(f"   Location: {job['location']}")
            if job.get('description'):
                print(f"   Description: {job['description'][:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
