"""
LinkedIn 爬虫 V6 + 数据库集成补丁
=================================

为 linkedin_scraper_v6.py 添加直接写入数据库的功能

Usage:
    # 爬取并直接保存到数据库
    python linkedin_scraper_v6_db.py --profile ml_data --save-to-db

    # 只保存到数据库（不生成JSON）
    python linkedin_scraper_v6_db.py --profile ml_data --save-to-db --no-json
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# 导入 V6 爬虫
from scripts.linkedin_scraper_v6 import LinkedInScraperV6, SearchConfig, DATA_DIR, CONFIG_DIR, COOKIES_FILE, PROFILES_FILE

# 导入数据库模块
try:
    from src.db.job_db import JobDatabase
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[Warning] Database module not available")


class LinkedInScraperV6DB(LinkedInScraperV6):
    """LinkedIn 爬虫 V6 - 支持直接写入数据库"""

    def __init__(self, config: SearchConfig, headless: bool = False, use_cdp: bool = False, cdp_url: str = "http://localhost:9222"):
        super().__init__(config, headless, use_cdp, cdp_url)
        self.db = JobDatabase() if DB_AVAILABLE else None
        self.saved_to_db = 0
        self.skipped_duplicates = 0

    async def run_profile(self, profile_name: str, fetch_jd: bool = True, save_to_db: bool = False) -> List[Dict]:
        """
        Run all queries for a profile

        Args:
            profile_name: Profile name
            fetch_jd: Whether to fetch job descriptions
            save_to_db: Whether to save directly to database
        """
        jobs = await super().run_profile(profile_name, fetch_jd)

        if save_to_db and self.db:
            print(f"\n[Database] Saving {len(jobs)} jobs to database...")
            for job in jobs:
                # 添加 profile 信息
                job['search_profile'] = profile_name
                job['search_query'] = profile_name

                # 检查是否已存在
                if self.db.job_exists(job.get('url', '')):
                    self.skipped_duplicates += 1
                    continue

                # 插入数据库
                try:
                    self.db.insert_job(job)
                    self.saved_to_db += 1
                except Exception as e:
                    print(f"  ! Failed to save job: {e}")

            print(f"[Database] Saved: {self.saved_to_db}, Duplicates skipped: {self.skipped_duplicates}")

        return jobs

    def save_results(self, profile_name: str = "all", save_json: bool = True) -> Optional[Path]:
        """
        Save results to file and/or database

        Args:
            profile_name: Profile name for filename
            save_json: Whether to save JSON file

        Returns:
            Path to saved file or None
        """
        if not save_json:
            print(f"\n[Database] {self.saved_to_db} jobs saved to database")
            return None

        return super().save_results(profile_name)

    def print_summary(self):
        """Print summary including database info"""
        super().print_summary()

        if self.db:
            print(f"\n[Database Summary]")
            print(f"  New jobs saved: {self.saved_to_db}")
            print(f"  Duplicates skipped: {self.skipped_duplicates}")

            # 显示数据库统计
            stats = self.db.get_funnel_stats()
            print(f"\n  Database totals:")
            print(f"    Total scraped: {stats.get('total_scraped', 0)}")
            print(f"    Passed filter: {stats.get('passed_filter', 0)}")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn 职位爬虫 V6 + 数据库集成")
    parser.add_argument("--profile", type=str, help="运行指定 profile (默认运行所有启用的)")
    parser.add_argument("--list", action="store_true", help="列出所有 profiles")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--cdp", action="store_true", help="使用 CDP 连接已有浏览器")
    parser.add_argument("--cdp-url", default="http://localhost:9222", help="CDP URL")
    parser.add_argument("--no-jd", action="store_true", help="跳过 JD 获取（快速模式）")
    parser.add_argument("--save-to-db", action="store_true", help="直接保存到数据库")
    parser.add_argument("--no-json", action="store_true", help="不保存 JSON 文件（仅数据库）")
    args = parser.parse_args()

    # 加载配置
    config = SearchConfig()

    if args.list:
        config.list_profiles()
        return

    if args.save_to_db and not DB_AVAILABLE:
        print("Error: Database module not available")
        sys.exit(1)

    print("=" * 70)
    print("LinkedIn Job Scraper V6 + Database Integration")
    print("=" * 70)

    # 确定要运行的 profiles
    if args.profile:
        profiles_to_run = [args.profile]
    else:
        profiles_to_run = config.get_enabled_profiles()

    print(f"Will run {len(profiles_to_run)} profiles: {', '.join(profiles_to_run)}")
    if args.save_to_db:
        print("Mode: Save to database")

    async with LinkedInScraperV6DB(
        config=config,
        headless=args.headless,
        use_cdp=args.cdp,
        cdp_url=args.cdp_url
    ) as scraper:
        # 登录
        if not await scraper.login_with_cookies():
            print("[FAIL] Login failed")
            return

        # 运行每个 profile
        for profile_name in profiles_to_run:
            await scraper.run_profile(
                profile_name,
                fetch_jd=not args.no_jd,
                save_to_db=args.save_to_db
            )

            # profile 间延迟
            if profile_name != profiles_to_run[-1]:
                print("\n-> Waiting 10s before next profile...")
                await asyncio.sleep(10)

        # 保存结果
        profile_label = args.profile if args.profile else "all"
        scraper.save_results(profile_label, save_json=not args.no_json)

        # 打印摘要
        scraper.print_summary()

        print("\n" + "=" * 70)
        print(f"Done! Total {len(scraper.all_jobs)} jobs")
        if args.save_to_db:
            print(f"  Database new: {scraper.saved_to_db}")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
