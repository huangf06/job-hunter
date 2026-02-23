"""
Telegram notification for Job Pipeline CI.

Reads scrape metrics from data/scrape_metrics.json, queries DB for
incremental stats and ready-to-apply jobs, sends summary via Telegram Bot API.

Usage:
    python scripts/notify.py --status success
    python scripts/notify.py --status failure --failed-step "scrape, ai-analyze"
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


def get_db_stats() -> dict:
    """Query DB for incremental + summary stats."""
    stats = {
        "ready": [],
        "today_analyzed": 0,
        "today_tokens": 0,
        "today_new_ready": [],
        "applied": 0,
        "interview": 0,
        "rejected": 0,
        "total_ready": 0,
    }
    try:
        from src.db.job_db import JobDatabase
        db = JobDatabase()

        # Ready-to-apply jobs (have resume, not yet applied)
        ready = db.get_ready_to_apply()
        stats["ready"] = ready
        stats["total_ready"] = len(ready)

        # Application status counts
        funnel = db.get_funnel_stats()
        stats["applied"] = funnel.get("applied", 0)
        stats["interview"] = funnel.get("interview", 0)
        stats["rejected"] = funnel.get("rejected", 0)

        # Get proper counts from applications table
        with db._get_conn() as conn:
            rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM applications
                GROUP BY status
            """).fetchall()
            for row in rows:
                r = dict(row)
                if r["status"] == "applied":
                    stats["applied"] = r["count"]
                elif r["status"] == "interview":
                    stats["interview"] = r["count"]
                elif r["status"] == "rejected":
                    stats["rejected"] = r["count"]

            # Today's AI analysis count
            today_analyzed = conn.execute("""
                SELECT COUNT(*) as cnt
                FROM job_analysis
                WHERE DATE(analyzed_at) = DATE('now')
            """).fetchone()
            stats["today_analyzed"] = today_analyzed["cnt"] if today_analyzed else 0

            # Today's token usage
            today_tokens = conn.execute("""
                SELECT COALESCE(SUM(tokens_used), 0) as total
                FROM job_analysis
                WHERE DATE(analyzed_at) = DATE('now')
            """).fetchone()
            stats["today_tokens"] = today_tokens["total"] if today_tokens else 0

            # Ready jobs that were analyzed today (= new ready)
            today_ready = conn.execute("""
                SELECT j.id, j.title, j.company, an.ai_score as score
                FROM jobs j
                JOIN job_analysis an ON j.id = an.job_id
                JOIN resumes r ON j.id = r.job_id AND r.pdf_path IS NOT NULL AND r.pdf_path != ''
                LEFT JOIN applications a ON j.id = a.job_id
                WHERE a.id IS NULL
                  AND DATE(an.analyzed_at) = DATE('now')
                ORDER BY an.ai_score DESC
            """).fetchall()
            stats["today_new_ready"] = [dict(r) for r in today_ready]

    except Exception as e:
        print(f"[notify] DB query failed: {e}")
    return stats


def format_message(status: str, failed_step: str = "",
                   scrape: dict = None, db_stats: dict = None) -> str:
    """Format Telegram message."""
    now = datetime.now(CET)
    time_str = now.strftime("%H:%M CET")

    if status == "failure":
        lines = [f"Job Pipeline FAILED {time_str}"]
        lines.append("")
        if failed_step:
            lines.append(f"Failed: {failed_step}")
        if scrape and scrape.get("new_jobs", 0) > 0:
            lines.append(f"+{scrape['new_jobs']} scraped before failure")
        lines.append("")
        lines.append("https://github.com/huangf06/job-hunter/actions")
        return "\n".join(lines)

    # --- Success ---
    db = db_stats or {}
    new_jobs = scrape.get("new_jobs", 0) if scrape else 0
    today_analyzed = db.get("today_analyzed", 0)
    today_tokens = db.get("today_tokens", 0)
    total_ready = db.get("total_ready", 0)
    new_ready = db.get("today_new_ready", [])
    ready = db.get("ready", [])
    applied = db.get("applied", 0)
    interview = db.get("interview", 0)
    rejected = db.get("rejected", 0)

    # No new jobs — short message
    if new_jobs == 0 and today_analyzed == 0:
        lines = [f"Job Pipeline {time_str} — No new jobs"]
        lines.append(f"Ready: {total_ready} | Applied: {applied} | Interview: {interview}")
        return "\n".join(lines)

    # Normal run
    lines = [f"Job Pipeline {time_str}"]
    lines.append("")

    # Incremental funnel
    funnel_parts = []
    if new_jobs > 0:
        funnel_parts.append(f"+{new_jobs} new")
    if today_analyzed > 0:
        funnel_parts.append(f"{today_analyzed} analyzed")
    if funnel_parts:
        lines.append(" → ".join(funnel_parts))

    # Token usage
    if today_tokens > 0:
        if today_tokens >= 1000:
            lines.append(f"Tokens: {today_tokens / 1000:.1f}k today")
        else:
            lines.append(f"Tokens: {today_tokens} today")

    # Ready-to-apply list
    if ready:
        lines.append("")
        new_count = len(new_ready)
        new_ids = {r["id"] for r in new_ready}
        if new_count > 0:
            lines.append(f"Ready ({new_count} new / {total_ready} total):")
        else:
            lines.append(f"Ready ({total_ready}):")

        # Show up to 5, new ones first with ✨
        shown = []
        for job in new_ready[:5]:
            score = job.get("score", 0)
            title = job.get("title", "?")[:35]
            company = job.get("company", "?")[:18]
            shown.append(f"  [{score:.1f}] {title} @ {company} ✨")
        remaining_slots = 5 - len(shown)
        if remaining_slots > 0:
            for job in ready:
                if job.get("id") not in new_ids:
                    score = job.get("score", 0)
                    title = job.get("title", "?")[:35]
                    company = job.get("company", "?")[:18]
                    shown.append(f"  [{score:.1f}] {title} @ {company}")
                    if len(shown) >= 5:
                        break
        lines.extend(shown)
        remaining = total_ready - len(shown)
        if remaining > 0:
            lines.append(f"  ... +{remaining} more")

    # Bottom summary line
    lines.append("")
    lines.append(f"Applied: {applied} | Interview: {interview} | Rejected: {rejected}")

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
    parser.add_argument("--failed-step", default="", help="Name of failed step(s)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print message without sending")
    args = parser.parse_args()

    scrape = load_scrape_metrics()
    db_stats = get_db_stats()

    message = format_message(
        status=args.status,
        failed_step=args.failed_step,
        scrape=scrape,
        db_stats=db_stats
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
