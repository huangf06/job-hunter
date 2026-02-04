# Test config-driven crawler
from src.config.loader import ConfigLoader
from src.modules.crawler.config_driven import ConfigDrivenScraper

loader = ConfigLoader('config')
config = loader.load()

print("="*60)
print("CONFIG TEST")
print("="*60)

scraper = ConfigDrivenScraper(config.crawler)
enabled = scraper.get_enabled_platforms()

print(f"\nEnabled platforms: {enabled}")
print(f"\nPlatform details:")

for platform in enabled:
    pc = config.crawler.get('platforms', {}).get(platform, {})
    search = pc.get('search', {})
    terms = search.get('terms', [])
    location = search.get('location', 'N/A')
    max_jobs = search.get('max_jobs_per_search', 10)
    
    print(f"\n  {platform.upper()}:")
    print(f"    Terms: {terms}")
    print(f"    Location: {location}")
    print(f"    Max jobs: {max_jobs}")
    
    behavior = pc.get('behavior', {})
    print(f"    Headless: {behavior.get('headless', True)}")
    print(f"    Delay: {behavior.get('request_delay', 2)}s")

print("\n" + "="*60)
print("Global config:")
print("="*60)
global_config = config.crawler.get('global', {})
print(f"  Max total jobs: {global_config.get('daily_limits', {}).get('max_total_jobs', 50)}")
print(f"  Deduplication: {global_config.get('deduplication', {}).get('enabled', True)}")
