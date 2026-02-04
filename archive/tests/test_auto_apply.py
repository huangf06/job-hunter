#!/usr/bin/env python3
"""
测试自动投递 - Xccelerated Data Engineer
"""

import sys
sys.path.insert(0, 'C:\\Users\\huang\\.openclaw\\workspace\\job-hunter')

from streamlined_pipeline import process_job

# Xccelerated Data Engineer 职位
job = {
    'id': '4351614328',
    'title': 'Data Engineer',
    'company': 'Xccelerated',
    'location': 'Utrecht, Netherlands',
    'url': 'https://nl.linkedin.com/jobs/view/data-engineer-at-xccelerated-part-of-xebia-4351614328',
    'description': '''
    Xccelerated is looking for a Data Engineer to join their team in Utrecht.
    
    Requirements:
    - Experience with Python and SQL
    - Knowledge of cloud platforms (AWS, GCP, or Azure)
    - Experience with data pipelines and ETL processes
    - Familiarity with Spark or similar big data technologies
    
    What we offer:
    - Competitive salary
    - Training and development opportunities
    - Work with cutting-edge technologies
    ''',
    'discovered_at': '2026-02-03T19:03:00Z'
}

print('='*60)
print('TESTING: Auto-apply for Xccelerated Data Engineer')
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
    print('\n[SUCCESS] Application auto-submitted!')
elif result['status'] == 'ready_to_apply':
    print('\n[PENDING] Resume generated, manual apply needed')
elif result['status'] == 'auto_apply_failed':
    print('\n[FAIL] Auto-apply failed, check browser automation')
