"""One-time repair: fix follow_up emails that are actually rejections.

Scans the emails table for follow_up entries containing definitive
rejection keywords, updates their category and the corresponding
application status to 'rejected'.

Usage:
    python scripts/fix_misclassified_rejections.py          # dry run
    python scripts/fix_misclassified_rejections.py --apply  # apply fixes
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase

REJECTION_PHRASES = [
    'unfortunately',
    'not moving forward',
    'will not be proceeding',
    'decided not to proceed',
    'not selected',
    'regret to inform',
    'moved forward with other candidates',
    'not be able to offer you',
    'position has been filled',
    'chosen not to progress',
    'decided to move forward with other',
    'will not be moving forward',
    'unable to move forward',
    'not to progress your application',
]


def main():
    apply = '--apply' in sys.argv
    db = JobDatabase()

    with db._get_conn() as conn:
        followups = conn.execute(
            "SELECT id, message_id, job_id, subject, body, snippet "
            "FROM emails WHERE category = 'follow_up'"
        ).fetchall()

        to_fix = []
        for row in followups:
            r = dict(row)
            body = (r.get('body') or '').lower()[:3000]
            snippet = (r.get('snippet') or '').lower()
            text = body + ' ' + snippet

            matched = [p for p in REJECTION_PHRASES if p in text]
            if matched:
                to_fix.append((r, matched))

        print(f"Found {len(to_fix)} misclassified follow_up emails "
              f"(out of {len(followups)} total follow_ups)")
        print()

        for r, keywords in to_fix:
            subject = (r.get('subject') or '')[:70]
            job_id = r.get('job_id')
            print(f"  Email #{r['id']}: {subject}")
            print(f"    job_id={job_id}, keywords={keywords[:2]}")

            if apply and job_id:
                # Fix email category
                conn.execute(
                    "UPDATE emails SET category = 'rejection' WHERE id = ?",
                    (r['id'],)
                )
                # Fix application status (only if not already offer/interview)
                app = conn.execute(
                    "SELECT status FROM applications WHERE job_id = ?",
                    (job_id,)
                ).fetchone()
                if app:
                    old_status = dict(app).get('status', 'pending')
                    if old_status not in ('offer', 'interview', 'rejected'):
                        now = datetime.now().isoformat()
                        conn.execute(
                            "UPDATE applications SET status = 'rejected', "
                            "response_at = ? WHERE job_id = ?",
                            (now, job_id)
                        )
                        print(f"    -> Updated: {old_status} -> rejected")
                    else:
                        print(f"    -> Skipped: status already {old_status}")
                else:
                    print(f"    -> No application record found")

        if apply and to_fix:
            conn.execute("COMMIT")
            print(f"\nApplied {len(to_fix)} fixes.")
        elif to_fix:
            print(f"\nDry run -- use --apply to fix these.")
        else:
            print("Nothing to fix.")


if __name__ == '__main__':
    main()
