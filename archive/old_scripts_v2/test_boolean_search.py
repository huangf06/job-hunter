"""
测试布尔搜索配置
==================
验证新的搜索配置是否正确生成 URL
"""

import yaml
from pathlib import Path
from urllib.parse import urlencode, quote

config_path = Path('config/search_profiles.yaml')
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

print("Testing Boolean Search Configuration")
print("=" * 70)

defaults = config['defaults']

for name, profile in config['profiles'].items():
    if not profile.get('enabled'):
        continue
    
    print(f"\nProfile: {name}")
    print(f"Name: {profile['name']}")
    print("Queries:")
    
    for q in profile.get('queries', []):
        keywords = q.get('keywords', '')
        description = q.get('description', '')
        
        # 构建 URL
        params = {
            "keywords": keywords,
            "location": defaults.get("location", "Netherlands"),
            "f_TPR": defaults.get("date_posted", "r604800"),
            "f_WT": defaults.get("workplace_type", "2,3"),
            "sortBy": defaults.get("sort_by", "DD")
        }
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params, quote_via=quote)}"
        
        print(f"  Description: {description}")
        print(f"  Keywords: {keywords}")
        print(f"  URL: {url[:100]}...")
        print()

print("=" * 70)
print("Configuration test complete!")
