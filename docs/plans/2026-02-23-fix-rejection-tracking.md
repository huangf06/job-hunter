# Fix Rejection Tracking — 3 Bugs

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix rejection count discrepancy — DB shows 18 rejections but actual count is much higher due to AI misclassification and a notification bug.

**Architecture:** Three independent fixes across two repos: (1) strengthen mail_processor's rejection detection with post-classification validation, (2) fix notify.py fallback bug, (3) one-time DB repair for 8 known misclassified emails.

**Tech Stack:** Python, SQLite/Turso, Anthropic Claude API

---

### Task 1: Fix notify.py fallback bug (job-hunter)

**Files:**
- Modify: `scripts/notify.py:62`

**Step 1: Fix the wrong fallback value**

Line 62 currently reads:
```python
stats["rejected"] = funnel.get("offer", 0)  # will fix below
```

Change to:
```python
stats["rejected"] = funnel.get("rejected", 0)
```

Note: `v_funnel_stats` view doesn't have a `rejected` column, so this will default to 0, which is the correct fallback before lines 65-78 override it. This protects against the case where the query on lines 65-78 fails.

**Step 2: Verify the fix**

Run: `cd C:/Users/huang/github/job-hunter && python scripts/notify.py --status success --dry-run`
Expected: Should print notification with correct rejected count (18), no errors.

**Step 3: Commit**

```bash
git add scripts/notify.py
git commit -m "fix: correct rejected count fallback in notify.py"
```

---

### Task 2: Add post-classification rejection validation (mail_processor)

**Files:**
- Modify: `C:/Users/huang/github/mail_processor/mail_classifier.py:113-160`

The AI prompt already mentions rejection keywords, but the AI sometimes misclassifies rejection emails as `follow_up` when the email starts with "thank you for applying" language. Rather than changing the prompt (which risks other regressions), add a **post-classification validation** that catches false negatives using keyword matching.

**Step 1: Add `_validate_rejection` method after `_fallback_classify`**

After `_extract_company_from_sender` method (after line 348), add:

```python
def _validate_rejection(self, classification: Dict[str, Any],
                        subject: str, body: str) -> Dict[str, Any]:
    """Post-classification check: catch rejections misclassified as follow_up.

    The AI sometimes classifies rejection emails as 'follow_up' when
    the email starts with 'thank you for applying' language. This check
    catches those by scanning for definitive rejection phrases.
    """
    if classification.get('category') != 'follow_up':
        return classification

    body_lower = body.lower()[:3000]
    subject_lower = subject.lower()
    text = subject_lower + " " + body_lower

    # Definitive rejection phrases (high precision — avoid false positives)
    rejection_phrases = [
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

    if any(phrase in text for phrase in rejection_phrases):
        logger.info(f"Post-validation override: follow_up -> rejection "
                    f"(matched rejection phrase in body)")
        classification['category'] = 'rejection'

    return classification
```

**Step 2: Call validation in `classify_email`**

In `classify_email` method, modify the return paths to call validation. There are 3 return paths that need wrapping:

1. Line 143 (successful AI classification):
   Change:
   ```python
   return result
   ```
   To:
   ```python
   return self._validate_rejection(result, subject, body)
   ```

2. Line 145 (AI parse failure, fallback):
   Change:
   ```python
   return self._fallback_classify(subject, sender, body)
   ```
   To:
   ```python
   return self._validate_rejection(
       self._fallback_classify(subject, sender, body), subject, body)
   ```

3. Line 160 (retries exhausted, fallback):
   Change:
   ```python
   return self._fallback_classify(subject, sender, body)
   ```
   To:
   ```python
   return self._validate_rejection(
       self._fallback_classify(subject, sender, body), subject, body)
   ```

**Step 3: Commit**

```bash
cd C:/Users/huang/github/mail_processor
git add mail_classifier.py
git commit -m "fix: add post-classification rejection validation to catch misclassified follow_ups"
```

---

### Task 3: Repair misclassified emails in DB (job-hunter)

**Files:**
- Create: `scripts/fix_misclassified_rejections.py` (one-time repair script)

**Step 1: Write the repair script**

```python
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
            print(f"\nDry run — use --apply to fix these.")
        else:
            print("Nothing to fix.")


if __name__ == '__main__':
    main()
```

**Step 2: Run dry-run first**

Run: `cd C:/Users/huang/github/job-hunter && python scripts/fix_misclassified_rejections.py`
Expected: Lists 8 emails that need fixing, does NOT modify DB.

**Step 3: Apply the fix**

Run: `cd C:/Users/huang/github/job-hunter && python scripts/fix_misclassified_rejections.py --apply`
Expected: Updates 8 email categories and application statuses.

**Step 4: Verify**

Run: `cd C:/Users/huang/github/job-hunter && python scripts/notify.py --status success --dry-run`
Expected: Rejected count should be ~26 (18 + 8).

**Step 5: Commit**

```bash
git add scripts/fix_misclassified_rejections.py
git commit -m "fix: one-time repair of misclassified rejection emails"
```

---

### Task 4: Verify everything end-to-end

**Step 1: Verify job-hunter notification**

Run: `cd C:/Users/huang/github/job-hunter && python scripts/notify.py --status success --dry-run`
Expected: Rejected count = ~26, no errors.

**Step 2: Verify mail_processor classifier**

Test with a known rejection body to confirm post-validation works:
```bash
cd C:/Users/huang/github/mail_processor && python -c "
from mail_classifier import MailClassifier
c = MailClassifier({'model': 'claude-haiku-4-5-20251001'})
# Test the fallback path (no AI) with a tricky rejection
result = c._fallback_classify(
    'Thank you for your application',
    'noreply@company.com',
    'Thank you for applying. Unfortunately, we have decided to move forward with other candidates.'
)
result = c._validate_rejection(result, 'Thank you for your application',
    'Thank you for applying. Unfortunately, we have decided to move forward with other candidates.')
print(f'Category: {result[\"category\"]}')
assert result['category'] == 'rejection', f'Expected rejection, got {result[\"category\"]}'
print('PASS')
"
```
Expected: `Category: rejection` + `PASS`
