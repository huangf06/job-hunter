"""
Multi-Platform Job Scraper — Orchestrator
==========================================
Runs all non-LinkedIn scrapers (Greenhouse, Lever, IamExpat).

Usage:
    python scripts/multi_scraper.py --all
    python scripts/multi_scraper.py --platform ats
    python scripts/multi_scraper.py --platform iamexpat
    python scripts/multi_scraper.py --platform ats --platform iamexpat
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.greenhouse import GreenhouseScraper
from src.scrapers.lever import LeverScraper
from src.scrapers.iamexpat import IamExpatScraper

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("multi_scraper")


def load_target_companies() -> list:
    path = CONFIG_DIR / "target_companies.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f).get("companies", [])


def load_iamexpat_queries(profile: str = None) -> list:
    path = CONFIG_DIR / "search_profiles.yaml"
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    queries = []
    profiles = config.get("profiles", {})
    for name, prof in profiles.items():
        if profile and name != profile:
            continue
        if not prof.get("enabled", True):
            continue
        ie = prof.get("iamexpat", {})
        queries.extend(ie.get("queries", []))
    return queries


def run_ats_scrapers(companies: list) -> dict:
    """Run Greenhouse + Lever scrapers."""
    gh_companies = [c for c in companies if c["ats"] == "greenhouse"]
    lv_companies = [c for c in companies if c["ats"] == "lever"]
    combined = {}

    if gh_companies:
        logger.info("=== Greenhouse: %d companies ===", len(gh_companies))
        gh = GreenhouseScraper(companies=gh_companies)
        combined["greenhouse"] = gh.run()

    if lv_companies:
        logger.info("=== Lever: %d companies ===", len(lv_companies))
        lv = LeverScraper(companies=lv_companies)
        combined["lever"] = lv.run()

    return combined


def run_iamexpat_scraper(queries: list, headless: bool = True) -> dict:
    """Run IamExpat scraper."""
    if not queries:
        logger.info("No IamExpat queries configured, skipping")
        return {}
    logger.info("=== IamExpat: %d queries ===", len(queries))
    ie = IamExpatScraper(queries=queries, headless=headless)
    return {"iamexpat": ie.run()}


def main():
    parser = argparse.ArgumentParser(description="Multi-platform job scraper")
    parser.add_argument("--all", action="store_true", help="Run all scrapers")
    parser.add_argument("--platform", action="append", choices=["ats", "iamexpat"],
                        help="Run specific platform(s)")
    parser.add_argument("--profile", default=None, help="Search profile for IamExpat queries")
    parser.add_argument("--headless", action="store_true", default=True,
                        help="Run Playwright in headless mode (default)")
    parser.add_argument("--no-headless", dest="headless", action="store_false",
                        help="Show browser window")
    args = parser.parse_args()

    platforms = set(args.platform or [])
    if args.all:
        platforms = {"ats", "iamexpat"}
    if not platforms:
        parser.error("Specify --all or --platform")

    results = {}
    companies = load_target_companies()

    if "ats" in platforms:
        results.update(run_ats_scrapers(companies))

    if "iamexpat" in platforms:
        queries = load_iamexpat_queries(args.profile)
        results.update(run_iamexpat_scraper(queries, headless=args.headless))

    # Save metrics
    total_new = sum(r.get("new", 0) for r in results.values())
    total_found = sum(r.get("found", 0) for r in results.values())
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "platforms": results,
        "total_found": total_found,
        "total_new": total_new,
    }
    metrics_path = DATA_DIR / "multi_scrape_metrics.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    logger.info("=== Done: found %d, new %d ===", total_found, total_new)


if __name__ == "__main__":
    main()
