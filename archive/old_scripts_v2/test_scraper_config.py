"""
Test scraper without actual crawling
=====================================
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from scripts.linkedin_scraper_v6 import SearchConfig, LinkedInScraperV6
from urllib.parse import urlencode

print("Testing Scraper Configuration")
print("=" * 70)

config = SearchConfig()

print("\nEnabled Profiles:")
for name in config.get_enabled_profiles():
    profile = config.get_profile(name)
    print(f"\n  {name}: {profile['name']}")
    for q in profile.get('queries', []):
        keywords = q.get('keywords', '')
        print(f"    Keywords: {keywords[:80]}...")
        
        # Build URL
        params = {
            "keywords": keywords,
            "location": config.defaults.get("location", "Netherlands"),
            "f_TPR": config.defaults.get("date_posted", "r604800"),
            "f_WT": config.defaults.get("workplace_type", "2,3"),
            "sortBy": config.defaults.get("sort_by", "DD")
        }
        url = f"https://www.linkedin.com/jobs/search?{urlencode(params)}"
        print(f"    URL: {url[:100]}...")

print("\n" + "=" * 70)
print("Configuration test complete!")
print("\nTo run actual scraping:")
print("  1. Make sure you have LinkedIn cookies saved")
print("  2. Or use --cdp to connect to existing browser")
print("  3. Run: python scripts/linkedin_scraper_v6_db.py --profile ml_data --save-to-db")
