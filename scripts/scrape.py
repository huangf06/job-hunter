"""
Unified scraper CLI for Block A rebuild.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.registry import resolve_platform_names

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
METRICS_PATH = DATA_DIR / "scrape_metrics.json"
PROFILES_PATH = CONFIG_DIR / "search_profiles.yaml"
TARGET_COMPANIES_PATH = CONFIG_DIR / "target_companies.yaml"
LEGACY_PROFILES = {"ml_data", "backend_data", "quick_test"}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("scrape")


def load_search_profiles() -> dict:
    with open(PROFILES_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def get_active_profile_names() -> list[str]:
    config = load_search_profiles()
    profiles = config.get("profiles", {})
    return sorted(name for name, profile in profiles.items() if profile.get("enabled", True))


def validate_profile_name(value: str) -> str:
    if value in LEGACY_PROFILES:
        raise argparse.ArgumentTypeError(f"Legacy profile is no longer supported: {value}")

    active_profiles = set(get_active_profile_names())
    if value not in active_profiles:
        raise argparse.ArgumentTypeError(
            f"Unknown or inactive profile: {value}. Active profiles: {', '.join(sorted(active_profiles))}"
        )
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified job scraper")
    parser.add_argument(
        "--platform",
        choices=["linkedin", "greenhouse", "iamexpat", "ats", "all"],
        default=None,
        help="Platform or alias to scrape",
    )
    parser.add_argument("--all", action="store_true", help="Run all scraper platforms")
    parser.add_argument("--profile", type=validate_profile_name, default=None, help="Active profile name")
    parser.add_argument("--save-to-db", action="store_true", help="Persist new jobs to the database")
    parser.add_argument("--dry-run", action="store_true", help="Report insert candidates without writing to DB")
    return parser


def load_target_companies() -> list[dict]:
    with open(TARGET_COMPANIES_PATH, "r", encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("companies", [])


def load_iamexpat_queries(profile: str | None = None) -> list[dict]:
    config = load_search_profiles()
    queries: list[dict] = []
    for name, profile_config in config.get("profiles", {}).items():
        if not profile_config.get("enabled", True):
            continue
        if profile and name != profile:
            continue
        queries.extend(profile_config.get("iamexpat", {}).get("queries", []))
    return queries


def build_scraper(platform: str, profile: str | None = None):
    if platform == "greenhouse":
        from src.scrapers.greenhouse import GreenhouseScraper

        companies = [c for c in load_target_companies() if c.get("ats") == "greenhouse"]
        return GreenhouseScraper(companies=companies)

    if platform == "iamexpat":
        from src.scrapers.iamexpat import IamExpatScraper

        return IamExpatScraper(queries=load_iamexpat_queries(profile))

    if platform == "linkedin":
        from src.scrapers.registry import get_scraper_class

        scraper_cls = get_scraper_class("linkedin")
        return scraper_cls(profile=profile)

    raise KeyError(f"Unsupported platform: {platform}")


def serialize_report(report) -> dict:
    if hasattr(report, "to_dict"):
        return report.to_dict()
    return dict(report)


def emit_metrics(platform_reports: dict[str, dict], output_path: Path | None = None) -> dict:
    total_found = sum(report.get("found", 0) for report in platform_reports.values())
    total_new = sum(report.get("new", 0) for report in platform_reports.values())
    total_would_insert = sum(report.get("would_insert", 0) for report in platform_reports.values())
    total_targets_failed = sum(report.get("targets_failed", 0) for report in platform_reports.values())
    severity = "error" if any(r.get("severity") == "error" for r in platform_reports.values()) else (
        "warning" if any(r.get("severity") == "warning" for r in platform_reports.values()) else "info"
    )
    metrics = {
        "timestamp": datetime.now().isoformat(),
        "new_jobs": total_new,
        "platforms": platform_reports,
        "total": {
            "found": total_found,
            "new": total_new,
            "would_insert": total_would_insert,
            "targets_failed": total_targets_failed,
            "severity": severity,
        },
    }
    metrics_path = output_path or METRICS_PATH
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return metrics


def run_platforms(platforms: list[str], profile: str | None, save_to_db: bool, dry_run: bool) -> dict:
    platform_reports: dict[str, dict] = {}
    for platform in platforms:
        started_at = time.perf_counter()
        scraper = build_scraper(platform, profile=profile)
        report = scraper.run(dry_run=(dry_run or not save_to_db))
        serialized_report = serialize_report(report)
        platform_reports[platform] = serialized_report
        elapsed = time.perf_counter() - started_at
        diagnostics = serialized_report.setdefault("diagnostics", {})
        diagnostics["elapsed_seconds"] = round(elapsed, 2)
        logger.info(
            "Platform %s completed in %.2fs severity=%s found=%d new=%d",
            platform,
            elapsed,
            serialized_report.get("severity", "n/a"),
            serialized_report.get("found", 0),
            serialized_report.get("new", 0),
        )
    return platform_reports


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.all:
        platforms = resolve_platform_names("all")
    elif args.platform:
        platforms = resolve_platform_names(args.platform)
    else:
        parser.error("Specify --all or --platform")

    platform_reports = run_platforms(
        platforms=platforms,
        profile=args.profile,
        save_to_db=args.save_to_db,
        dry_run=args.dry_run,
    )
    metrics = emit_metrics(platform_reports)
    print(json.dumps(metrics, indent=2))
    logger.info(
        "Scrape summary: platforms=%s new=%d found=%d",
        ",".join(platforms),
        metrics["total"]["new"],
        metrics["total"]["found"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
