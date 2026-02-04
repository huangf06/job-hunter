#!/usr/bin/env python3
"""
Job Hunter - 配置驱动版入口
============================
所有参数通过YAML配置管理

使用方法:
    # 使用默认配置爬取
    python hunt.py --scrape
    
    # 指定搜索词（覆盖配置）
    python hunt.py --scrape --term "machine learning engineer"
    
    # 处理已有数据
    python hunt.py --process data/leads/linkedin_jobs_xxx.json
    
    # 使用实验配置
    python hunt.py --scrape --experiment exp_001
"""

import sys
import asyncio
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.core.hunter import JobHunter
from src.config.loader import ConfigLoader
from src.modules.crawler.config_driven import ConfigDrivenScraper


async def scrape_and_process(config_loader: ConfigLoader, 
                             search_term: str = None,
                             experiment: str = None):
    """爬取并处理职位"""
    
    # 加载完整配置
    config = config_loader.load(experiment=experiment)
    
    # 1. 爬取职位（配置驱动）
    print("="*70)
    print("STEP 1: CRAWLING JOBS")
    print("="*70)
    
    scraper = ConfigDrivenScraper(config.crawler)
    results = await scraper.scrape_all(search_term=search_term)
    scraper.print_summary(results)
    
    # 合并所有职位
    all_jobs = scraper.get_all_jobs(results)
    
    if not all_jobs:
        print("No jobs found!")
        return
    
    # 2. 处理职位
    print("\n" + "="*70)
    print("STEP 2: PROCESSING JOBS")
    print("="*70)
    
    hunter = JobHunter(config)
    await hunter.process_jobs(all_jobs)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Job Hunter - Configuration-driven job search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
配置驱动模式 - 所有参数通过 config/base/crawler.yaml 管理:

  # 修改配置文件
  vim config/base/crawler.yaml
  
  # 启用/禁用平台:
  platforms:
    linkedin:
      enabled: true/false
    iamexpat:
      enabled: true/false
  
  # 调整搜索词:
  search:
    terms:
      - "data scientist"
      - "machine learning engineer"
  
  # 调整每平台职位数:
  max_jobs_per_search: 25

使用方法:
  python hunt.py --scrape                    # 使用配置爬取
  python hunt.py --scrape --term "ml engineer" # 覆盖搜索词
  python hunt.py --experiment exp_001         # 使用实验配置
  python hunt.py --stats                      # 查看统计
        """
    )
    
    parser.add_argument('--scrape', action='store_true',
                       help='Scrape jobs using configuration')
    parser.add_argument('--term',
                       help='Override search term from config')
    parser.add_argument('--process', metavar='FILE',
                       help='Process jobs from JSON file')
    parser.add_argument('--experiment', metavar='EXP',
                       help='Experiment configuration to use')
    parser.add_argument('--stats', action='store_true',
                       help='Show statistics')
    parser.add_argument('--config', default='config',
                       help='Configuration directory (default: config)')
    
    args = parser.parse_args()
    
    # 初始化配置加载器
    config_loader = ConfigLoader(args.config)
    
    # 显示统计
    if args.stats:
        from src.modules.tracker.analytics import ReportGenerator
        reporter = ReportGenerator()
        reporter.generate_console_report()
        return
    
    # 爬取+处理模式
    if args.scrape:
        await scrape_and_process(
            config_loader=config_loader,
            search_term=args.term,
            experiment=args.experiment
        )
        return
    
    # 处理模式
    if args.process:
        import json
        jobs_path = Path(args.process)
        if not jobs_path.exists():
            jobs_path = Path("data/leads") / args.process
        
        with open(jobs_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        config = config_loader.load(experiment=args.experiment)
        hunter = JobHunter(config)
        await hunter.process_jobs(jobs)
        return
    
    # 默认显示帮助
    parser.print_help()
    print("\n" + "="*70)
    print("CURRENT CONFIGURATION:")
    print("="*70)
    
    # 显示当前配置
    try:
        config = config_loader.load()
        scraper = ConfigDrivenScraper(config.crawler)
        enabled = scraper.get_enabled_platforms()
        print(f"Enabled platforms: {', '.join(enabled)}")
        
        for platform in enabled:
            pc = config.crawler.get('platforms', {}).get(platform, {})
            search = pc.get('search', {})
            terms = search.get('terms', [])
            max_jobs = search.get('max_jobs_per_search', 10)
            print(f"  {platform}:")
            print(f"    Search terms: {', '.join(terms[:3])}")
            print(f"    Max jobs: {max_jobs}")
    except Exception as e:
        print(f"Could not load config: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
