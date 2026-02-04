import json
from datetime import datetime

with open('data/job_tracker.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Sort by added_at descending
jobs = sorted(data['jobs'], key=lambda x: x.get('added_at', ''), reverse=True)

# Get high priority jobs (score >= 6.0) added today
today = '2026-02-03'
new_jobs = [j for j in jobs if j.get('added_at', '').startswith(today) and j.get('score', 0) >= 6.0]

print('=' * 60)
print(f'NEW HIGH PRIORITY JOBS TODAY: {len(new_jobs)} found')
print('=' * 60)
for job in new_jobs:
    status = 'APPLIED' if job.get('status') == 'applied' else 'TODO'
    print(f"""
[{job.get('score')}] {job.get('title')} @ {job.get('company')}
    Location: {job.get('location')}
    Rec: {job.get('recommendation')} | {status}
    URL: {job.get('url')}
""")

# Also show all high priority jobs not yet applied
print('\n' + '=' * 60)
print('TOP 10 HIGH PRIORITY JOBS (score >= 6.0, not applied)')
print('=' * 60)
todo_jobs = [j for j in data['jobs'] if j.get('score', 0) >= 6.0 and j.get('status') != 'applied']
for job in sorted(todo_jobs, key=lambda x: x.get('score', 0), reverse=True)[:10]:
    print(f"[{job.get('score')}] {job.get('title')} @ {job.get('company')} ({job.get('location')})")
