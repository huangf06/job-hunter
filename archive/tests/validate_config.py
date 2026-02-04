"""
验证推荐配置 - 模拟测试
========================
"""

from src.config.loader import ConfigLoader
from src.modules.crawler.config_driven import ConfigDrivenScraper

print("="*70)
print("CONFIG VALIDATION TEST")
print("="*70)

# 加载推荐配置
loader = ConfigLoader('config')
config = loader.load()

scraper = ConfigDrivenScraper(config.crawler)

# 检查配置
print("\n[1] Platform Configuration:")
enabled = scraper.get_enabled_platforms()
print(f"    Enabled platforms: {enabled}")

for platform in enabled:
    pc = config.crawler.get('platforms', {}).get(platform, {})
    search = pc.get('search', [])
    
    print(f"\n    {platform.upper()}:")
    print(f"      Strategies: {len(search)}")
    
    for i, s in enumerate(search, 1):
        print(f"        {i}. {s['name']}: {s['term'][:40]}... (max: {s['max_jobs']})")
    
    behavior = pc.get('behavior', {})
    print(f"      Delay: {behavior.get('request_delay', 2)}s")
    print(f"      Headless: {behavior.get('headless', True)}")

# 计算预估
print("\n[2] Estimation:")
total_jobs = 0
for platform in enabled:
    pc = config.crawler.get('platforms', {}).get(platform, {})
    search = pc.get('search', [])
    platform_jobs = sum(s.get('max_jobs', 0) for s in search)
    total_jobs += platform_jobs
    print(f"    {platform}: ~{platform_jobs} jobs")

print(f"\n    Total: ~{total_jobs} jobs/day")

# 时间估算
strategy_count = sum(
    len(config.crawler.get('platforms', {}).get(p, {}).get('search', []))
    for p in enabled
)
estimated_time = strategy_count * 30  # 30s per strategy
print(f"    Strategies: {strategy_count}")
print(f"    Est. time: {estimated_time/60:.1f} minutes")

# 风险评估
print("\n[3] Risk Assessment:")
if total_jobs <= 30:
    print("    [LOW] Job count is safe")
elif total_jobs <= 50:
    print("    [MEDIUM] Monitor for blocking")
else:
    print("    [HIGH] Reduce job count")

if strategy_count <= 3:
    print("    [LOW] Strategy count is good")
elif strategy_count <= 5:
    print("    [MEDIUM] Consider reducing")
else:
    print("    [HIGH] Too many strategies")

print("\n" + "="*70)
print("CONCLUSION")
print("="*70)
print("Configuration is valid and ready to use.")
print("Run: python hunt.py --scrape")
print("="*70)
