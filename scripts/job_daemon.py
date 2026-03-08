#!/usr/bin/env python3
"""
Job Hunter Streaming Daemon v1.0
================================
Priority-tiered scheduler with per-job streaming pipeline.
Scrapes LinkedIn profiles at different intervals based on priority,
processes new jobs immediately through filter -> score pipeline.

Usage:
    python scripts/job_daemon.py              # Run daemon (continuous)
    python scripts/job_daemon.py --once       # Single run, all profiles
    python scripts/job_daemon.py --profile data_engineering  # Single profile
"""
import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

PROFILES_FILE = PROJECT_ROOT / "config" / "search_profiles.yaml"


def load_config():
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


async def scrape_and_process(profile_name: str, headless: bool = True):
    """Scrape a single profile and process new jobs through pipeline."""
    from scripts.scraper_incremental import IncrementalScraper

    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"\n{'='*60}")
    print(f"[{timestamp}] Scraping: {profile_name}")
    print(f"{'='*60}")

    config = load_config()
    profile_config = config['profiles'].get(profile_name)
    if not profile_config or not profile_config.get('enabled', True):
        print(f"  [SKIP] {profile_name} is disabled")
        return

    try:
        async with IncrementalScraper(
            headless=headless, max_pages_per_profile=4
        ) as scraper:
            stats = await scraper.run(profile=profile_name)

        new_count = stats.get('new_jobs', 0)
        if new_count > 0:
            print(f"\n[Pipeline] Processing {new_count} new jobs...")
            from scripts.job_pipeline import JobPipeline
            pipeline = JobPipeline()
            pipeline.process_jobs()
            print(f"[Pipeline] Done processing {new_count} jobs")

            # Best-effort notification
            try:
                from scripts.notify import send_telegram_message
                send_telegram_message(
                    f"[{profile_name}] {new_count} new jobs found and processed"
                )
            except Exception:
                pass
        else:
            print(f"[{profile_name}] No new jobs")

    except Exception as e:
        print(f"[ERROR] {profile_name}: {e}")
        import traceback
        traceback.print_exc()


async def run_once(profile: str = None, headless: bool = True):
    """Run once and exit."""
    config = load_config()
    profiles = config.get('profiles', {})

    if profile:
        targets = [profile]
    else:
        targets = sorted(
            [k for k, v in profiles.items() if v.get('enabled', True)],
            key=lambda x: profiles[x].get('priority', 99)
        )

    print(f"Running {len(targets)} profiles: {', '.join(targets)}")
    for name in targets:
        await scrape_and_process(name, headless=headless)


async def run_daemon(headless: bool = True):
    """Run continuous daemon with APScheduler."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.interval import IntervalTrigger

    config = load_config()
    defaults = config.get('defaults', {})
    default_interval = defaults.get('daemon_interval_minutes', 360)

    print("=" * 60)
    print("Job Hunter Streaming Daemon v1.0")
    print(f"Started: {datetime.now().isoformat()}")
    print("=" * 60)

    scheduler = AsyncIOScheduler()
    profiles = config.get('profiles', {})

    for name, profile in profiles.items():
        if not profile.get('enabled', True):
            continue

        interval = profile.get('daemon_interval_minutes', default_interval)
        scheduler.add_job(
            scrape_and_process,
            trigger=IntervalTrigger(minutes=interval),
            args=[name, headless],
            id=f"scrape_{name}",
            name=f"{name} (P{profile.get('priority', 99)}, every {interval}min)",
            max_instances=1,
            misfire_grace_time=300,
        )
        print(f"  Scheduled: {name} — P{profile.get('priority', 99)}, every {interval}min")

    scheduler.start()

    # Initial run: all profiles once, sorted by priority
    print("\n--- Initial run ---")
    enabled = sorted(
        [k for k, v in profiles.items() if v.get('enabled', True)],
        key=lambda x: profiles[x].get('priority', 99)
    )
    for name in enabled:
        await scrape_and_process(name, headless=headless)

    # Wait for interrupt
    print("\n--- Daemon running. Ctrl+C to stop. ---")
    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, handle_signal)
        except NotImplementedError:
            # Windows
            signal.signal(sig, lambda s, f: handle_signal())

    await stop_event.wait()
    scheduler.shutdown()
    print("\nDaemon stopped.")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Job Hunter Streaming Daemon')
    parser.add_argument('--once', action='store_true',
                        help='Run all profiles once and exit')
    parser.add_argument('--profile', type=str,
                        help='Run specific profile only (implies --once)')
    parser.add_argument('--no-headless', action='store_true',
                        help='Show browser window (debug)')

    args = parser.parse_args()
    headless = not args.no_headless

    if args.once or args.profile:
        asyncio.run(run_once(profile=args.profile, headless=headless))
    else:
        asyncio.run(run_daemon(headless=headless))


if __name__ == '__main__':
    main()
