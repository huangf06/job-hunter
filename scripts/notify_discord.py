#!/usr/bin/env python3
"""
Discord 通知脚本 - Pipeline 运行结果通知
==========================================

Usage:
    python notify_discord.py --new-jobs 5 --duration 120 --run-url "..."
"""

import os
import sys
import json
from datetime import datetime
from typing import Optional

import requests

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')


def get_emoji_for_count(count: int) -> str:
    """根据新职位数量返回表情"""
    if count == 0:
        return "😴"
    elif count < 5:
        return "📬"
    elif count < 15:
        return "🔥"
    else:
        return "🚀"


def format_duration(seconds: int) -> str:
    """格式化持续时间"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m {seconds % 60}s"
    else:
        return f"{seconds // 3600}h {(seconds % 3600) // 60}m"


def send_notification(
    new_jobs: int = 0,
    duration: int = 0,
    run_url: str = "",
    high_score_jobs: int = 0,
    message: str = ""
) -> bool:
    """发送 Discord 通知"""
    
    if not DISCORD_WEBHOOK_URL:
        print("[WARN] DISCORD_WEBHOOK_URL not set")
        return False
        
    emoji = get_emoji_for_count(new_jobs)
    duration_str = format_duration(int(duration))
    
    # 构建 embed
    embed = {
        'title': f"{emoji} Job Hunter Pipeline Complete",
        'color': 0x00ff00 if new_jobs > 0 else 0x95a5a6,
        'fields': [
            {
                'name': '🆕 New Jobs',
                'value': str(new_jobs),
                'inline': True
            },
            {
                'name': '⏱️ Duration',
                'value': duration_str,
                'inline': True
            },
        ],
        'timestamp': datetime.utcnow().isoformat(),
    }
    
    if high_score_jobs > 0:
        embed['fields'].append({
            'name': '⭐ High Score Jobs',
            'value': str(high_score_jobs),
            'inline': True
        })
        
    if message:
        embed['description'] = message
        
    if run_url:
        embed['url'] = run_url
        
    # 添加 footer
    embed['footer'] = {
        'text': 'Job Hunter v3.0'
    }
    
    payload = {
        'embeds': [embed]
    }
    
    try:
        resp = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=10
        )
        if resp.status_code == 204:
            print("[OK] Discord notification sent")
            return True
        else:
            print(f"[ERROR] Discord returned {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to send notification: {e}")
        return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Send Discord notification')
    parser.add_argument('--new-jobs', type=int, default=0)
    parser.add_argument('--duration', type=int, default=0)
    parser.add_argument('--run-url', default='')
    parser.add_argument('--high-score-jobs', type=int, default=0)
    parser.add_argument('--message', default='')
    
    args = parser.parse_args()
    
    success = send_notification(
        new_jobs=args.new_jobs,
        duration=args.duration,
        run_url=args.run_url,
        high_score_jobs=args.high_score_jobs,
        message=args.message
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
