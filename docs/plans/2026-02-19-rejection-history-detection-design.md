# Rejection History Detection — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Warn users in the `--prepare` checklist when a job's company+title was previously rejected.

**Architecture:** Mirror the existing REPOST detection. New DB query method → enrich in pipeline → render badge in checklist HTML.

**Tech Stack:** Python, SQLite, HTML

---

### Task 1: Add `find_rejected_duplicates()` to DB

**Files:**
- Modify: `src/db/job_db.py:1133` (insert after `find_applied_duplicates`)

**Step 1: Write the method**

Insert after line 1133 (after `find_applied_duplicates` return), before the `# ==================== 统计和分析` comment:

```python
    def find_rejected_duplicates(self, job_id: str) -> List[Dict]:
        """查找同 company+title 被拒的职位 (rejection history 检测)

        使用词集合比较，忽略词序和标点，例如:
        "Data Engineer - Enterprise" == "Enterprise Data Engineer"
        """
        with self._get_conn() as conn:
            target = conn.execute(
                "SELECT title, company FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            if not target:
                return []

            target_company = target['company'].lower()
            target_title_norm = self._normalize_title(target['title'])

            cursor = conn.execute("""
                SELECT j.id as job_id, j.title, j.company,
                       COALESCE(a.response_at, a.updated_at) as rejected_at
                FROM jobs j
                JOIN applications a ON j.id = a.job_id AND a.status = 'rejected'
                WHERE LOWER(j.company) = ? AND j.id != ?
            """, (target_company, job_id))

            results = []
            for row in cursor.fetchall():
                if self._normalize_title(row['title']) == target_title_norm:
                    results.append(dict(row))
            return results
```

Note: uses `COALESCE(a.response_at, a.updated_at)` because `response_at` may be empty if the user just set status to rejected without providing a date.

**Step 2: Verify no syntax errors**

Run: `python -c "from src.db.job_db import JobDatabase; print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/db/job_db.py
git commit -m "feat: add find_rejected_duplicates() to JobDatabase"
```

---

### Task 2: Enrich ready jobs with rejection history in `--prepare`

**Files:**
- Modify: `scripts/job_pipeline.py:967-973` (the repost enrichment block)

**Step 1: Add rejection enrichment**

After the existing repost enrichment block (lines 967-973), add a parallel block:

```python
        # Enrich with rejection history
        rejection_count = 0
        for job in all_ready:
            rejected = self.db.find_rejected_duplicates(job['id'])
            if rejected:
                job['rejection_rejected_at'] = (rejected[0].get('rejected_at') or '')[:10]
                rejection_count += 1
```

**Step 2: Verify no import errors**

Run: `python -c "import scripts.job_pipeline; print('OK')"` or simply:
`python scripts/job_pipeline.py --stats`
Expected: normal stats output, no errors

**Step 3: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat: enrich ready jobs with rejection history in --prepare"
```

---

### Task 3: Render REJECTED badge in checklist

**Files:**
- Modify: `src/checklist_server.py:38` (state.json generation)
- Modify: `src/checklist_server.py:71-72` (badge rendering)

**Step 1: Add `rejection_rejected_at` to state.json**

In `generate_checklist()`, line 38, add after the `repost_applied_at` line:

```python
            "rejection_rejected_at": job.get("rejection_rejected_at", ""),
```

**Step 2: Render orange REJECTED badge in HTML**

In `_build_checklist_html()`, after line 72 (the repost_badge line), add:

```python
        rejected = info.get("rejection_rejected_at", "")
        rejected_badge = f' <span style="color:#ea580c;font-weight:bold" title="Rejected {_esc(rejected)}">REJECTED</span>' if rejected else ''
```

Then on line 78 where badges are rendered, change:

```python
          <td>{_esc(info['company'])}{repost_badge}</td>
```

to:

```python
          <td>{_esc(info['company'])}{repost_badge}{rejected_badge}</td>
```

**Step 3: Verify no syntax errors**

Run: `python -c "from src.checklist_server import generate_checklist; print('OK')"`
Expected: `OK`

**Step 4: Commit**

```bash
git add src/checklist_server.py
git commit -m "feat: render REJECTED badge in checklist HTML"
```

---

### Task 4: Final verification

**Step 1: Run full import check**

```bash
python -c "from src.db.job_db import JobDatabase; from src.checklist_server import generate_checklist; print('All imports OK')"
```

**Step 2: Run `--stats` to verify pipeline still works**

```bash
python scripts/job_pipeline.py --stats
```

Expected: normal stats output, no errors.
