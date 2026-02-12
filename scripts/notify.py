"""
Telegram notification for Job Pipeline CI.

Reads scrape metrics from data/scrape_metrics.json, queries DB for
funnel stats and ready-to-apply jobs, sends summary via Telegram Bot API.

Usage:
    # Success notification
    python scripts/notify.py --status success

    # Failure notification
    python scripts/notify.py --status failure --failed-step "AI analyze"

    # Test locally (prints message without sending)
    python scripts/notify.py --status success --dry-run
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CET = timezone(timedelta(hours=1))


def load_scrape_metrics() -> dict:
    """Load scrape metrics from JSON file written by scraper."""
    metrics_path = PROJECT_ROOT / "data" / "scrape_metrics.json"
    if metrics_path.exists():
        with open(metrics_path) as f:
            return json.load(f)
    return {}


def get_db_stats() -> tuple:
    """Query DB for funnel stats and ready-to-apply jobs."""
    funnel = {}
    ready = []
    try:
        from src.db.job_db import JobDatabase
        db = JobDatabase()
        funnel = db.get_funnel_stats()
        ready = db.get_ready_to_apply()
    except Exception as e:
        print(f"[notify] DB query failed: {e}")
    return funnel, ready


def format_message(status: str, failed_step: str = "",
                   scrape: dict = None, funnel: dict = None,
                   ready: list = None) -> str:
    """Format Telegram message."""
    now = datetime.now(CET)
    time_str = now.strftime("%H:%M CET")

    lines = []

    if status == "failure":
        lines.append(f"Job Pipeline FAILED ({time_str})")
        lines.append("")
        if failed_step:
            lines.append(f"Failed step: {failed_step}")
        if scrape and scrape.get("new_jobs", 0) > 0:
            lines.append(f"Scraped before failure: {scrape['new_jobs']} new")
        lines.append("")
        lines.append("Check: https://github.com/$REPO/actions")
        return "\n".join(lines)

    # Success or partial
    lines.append(f"Job Pipeline ({time_str})")
    lines.append("")

    if scrape:
        new = scrape.get("new_jobs", 0)
        skipped = scrape.get("skipped_duplicates", 0)
        lines.append(f"Scraped: {new} new / {skipped} skipped")
    else:
        lines.append("Scraped: no metrics available")

    if funnel:
        lines.append(f"Filtered: {funnel.get('passed_filter', '?')} passed")
        lines.append(f"AI analyzed: {funnel.get('ai_analyzed', '?')} | "
                     f"Resumes: {funnel.get('resume_generated', '?')}")

    if ready:
        lines.append("")
        lines.append(f"Ready to apply ({len(ready)}):")
        for job in ready[:5]:
            score = job.get('score', 0)
            title = job.get('title', '?')[:40]
            company = job.get('company', '?')[:20]
            lines.append(f"  {title} @ {company} ({score:.1f})")
        if len(ready) > 5:
            lines.append(f"  ... and {len(ready) - 5} more")
    elif scrape and scrape.get("new_jobs", 0) == 0:
        lines.append("")
        lines.append("No new jobs this run.")

    return "\n".join(lines)


def send_telegram(message: str, bot_token: str, chat_id: str) -> bool:
    """Send message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print("[notify] Telegram message sent")
                return True
            print(f"[notify] Telegram API error: {result}")
            return False
    except urllib.error.URLError as e:
        print(f"[notify] Failed to send: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Pipeline Telegram notification")
    parser.add_argument("--status", required=True, choices=["success", "failure"],
                        help="Pipeline status")
    parser.add_argument("--failed-step", default="", help="Name of failed step")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print message without sending")
    args = parser.parse_args()

    scrape = load_scrape_metrics()
    funnel, ready = get_db_stats()

    message = format_message(
        status=args.status,
        failed_step=args.failed_step,
        scrape=scrape,
        funnel=funnel,
        ready=ready
    )

    print(f"\n--- Notification ---\n{message}\n---\n")

    if args.dry_run:
        print("[notify] Dry run — not sending")
        return

    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        print("[notify] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set, skipping")
        return

    send_telegram(message, bot_token, chat_id)


if __name__ == "__main__":
    main()
