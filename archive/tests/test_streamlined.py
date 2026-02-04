#!/usr/bin/env python3
"""Test streamlined pipeline with real job"""

import sys
sys.path.insert(0, 'C:\\Users\\huang\\.openclaw\\workspace\\job-hunter')

from streamlined_pipeline import process_job, HardFilters

# 第一个职位：Xccelerated Data Engineer
job = {
    'id': '4351614328',
    'title': 'Data Engineer',
    'company': 'Xccelerated | Part of Xebia',
    'location': 'Utrecht, Netherlands',
    'url': 'https://nl.linkedin.com/jobs/view/data-engineer-at-xccelerated-part-of-xebia-4351614328',
    'description': '''
    Xccelerated is hiring a Data Engineer in Utrecht.
    We are looking for someone with experience in Python, SQL, and cloud platforms.
    This is a full-time position.
    ''',
    'discovered_at': '2026-02-03T18:47:00Z'
}

print('='*60)
print('TESTING: Xccelerated Data Engineer')
print('='*60)

# Step 1: Hard filter
passed, details = HardFilters.check(job)
print(f'\n[STEP 1] Hard Filter: {"PASSED" if passed else "REJECTED"}')
if details["reject_reasons"]:
    print(f'  Reject reasons: {details["reject_reasons"]}')
if details["warnings"]:
    print(f'  Warnings: {details["warnings"]}')
print(f'  Penalty score: {details["penalty_score"]}')

# Full process
print('\n' + '='*60)
print('[FULL PROCESS]')
print('='*60)
result = process_job(job, auto_apply=False, min_score=6.0)

print('\n' + '='*60)
print('RESULT:')
print('='*60)
for k, v in result.items():
    print(f'  {k}: {v}')
