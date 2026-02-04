#!/usr/bin/env python3
"""
测试自动投递 - Otrium Data Engineer
"""

import sys
sys.path.insert(0, 'C:\\Users\\huang\\.openclaw\\workspace\\job-hunter')

from streamlined_pipeline import process_job

# Otrium Data Engineer 职位
job = {
    'id': '4368611599',
    'title': 'Data Engineer',
    'company': 'Otrium',
    'location': 'Amsterdam, North Holland, Netherlands',
    'url': 'https://www.linkedin.com/jobs/view/4368611599',
    'description': '''
    Otrium is hiring a Data Engineer in Amsterdam.
    
    About Otrium:
    - Fashion outlet marketplace
    - Mid-Senior level position
    - Full-time
    - Engineering and Information Technology
    
    Requirements:
    - Experience with data engineering
    - Knowledge of cloud platforms
    - Experience with data pipelines
    ''',
    'discovered_at': '2026-02-03T19:20:00Z'
}

print('='*60)
print('TESTING: Auto-apply for Otrium Data Engineer')
print('='*60)
print(f"Job URL: {job['url']}")
print()

# 运行完整流程（包括自动投递）
result = process_job(job, auto_apply=True, min_score=6.0)

print('\n' + '='*60)
print('FINAL RESULT:')
print('='*60)
for k, v in result.items():
    print(f'  {k}: {v}')

if result['status'] == 'applied':
    print('\n[OK] Application auto-submitted!')
elif result['status'] == 'ready_to_apply':
    print('\n[PENDING] Resume generated, manual apply needed')
elif result['status'] == 'auto_apply_failed':
    print('\n[FAIL] Auto-apply failed')
