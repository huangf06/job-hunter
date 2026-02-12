"""
Pipeline gap report — 查看爬取后各阶段未处理的职位，并和 ready_to_send/ 交叉比对。

Usage:
    python scripts/pipeline_gaps.py              # 完整报告
    python scripts/pipeline_gaps.py --pending    # 只看待处理
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase

READY_DIR = PROJECT_ROOT / "ready_to_send"
APPLIED_DIR = READY_DIR / "_applied"
EMPTY_RESUME = '{}'


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Pipeline gap report')
    parser.add_argument('--pending', action='store_true', help='Only show pending (no resume) jobs')
    args = parser.parse_args()

    db = JobDatabase()

    with db._get_conn() as conn:
        # ── 1. Funnel summary ──────────────────────────────────────────────
        if not args.pending:
            print("=" * 75)
            print("PIPELINE GAP REPORT")
            print("=" * 75)

            row = conn.execute(
                "SELECT COUNT(*) as c, MIN(scraped_at) as earliest, MAX(scraped_at) as latest FROM jobs"
            ).fetchone()
            print(f"\nData range: {row['earliest'][:10]} -> {row['latest'][:10]}  ({row['c']} jobs total)")

            stats = [
                ("Scraped", "SELECT COUNT(*) as c FROM jobs"),
                ("Passed filter", "SELECT COUNT(*) as c FROM filter_results WHERE passed = 1"),
                ("Rejected filter", "SELECT COUNT(*) as c FROM filter_results WHERE passed = 0"),
                ("Rule scored >= 3.0", "SELECT COUNT(*) as c FROM ai_scores WHERE score >= 3.0"),
                ("AI analyzed", "SELECT COUNT(*) as c FROM job_analysis"),
                ("AI score >= 5.0", f"SELECT COUNT(*) as c FROM job_analysis WHERE ai_score >= 5.0 AND tailored_resume != ?"),
                ("Resume generated", "SELECT COUNT(*) as c FROM resumes WHERE pdf_path IS NOT NULL AND pdf_path != ''"),
                ("Applied", "SELECT COUNT(*) as c FROM applications"),
            ]
            print("\n  Stage                   Count")
            print("  " + "-" * 35)
            for label, sql in stats:
                params = (EMPTY_RESUME,) if '?' in sql else ()
                row = conn.execute(sql, params).fetchone()
                print(f"  {label:24s} {row['c']:>5}")

            # Application status breakdown
            rows = conn.execute(
                "SELECT status, COUNT(*) as c FROM applications GROUP BY status ORDER BY c DESC"
            ).fetchall()
            if rows:
                print(f"\n  Application breakdown:")
                for r in rows:
                    print(f"    {r['status']:12s} {r['c']:>5}")

        # ── 2. Gap: AI score ≥ 5.0 but no resume yet ──────────────────────
        print("\n" + "=" * 75)
        print("PENDING: AI Score >= 5.0, no resume generated, not applied")
        print("=" * 75)

        pending = conn.execute("""
            SELECT j.id, j.title, j.company, j.url, j.scraped_at,
                   a.ai_score, a.recommendation
            FROM jobs j
            JOIN job_analysis a ON j.id = a.job_id
            LEFT JOIN resumes r ON j.id = r.job_id
            LEFT JOIN applications app ON j.id = app.job_id
            WHERE (r.id IS NULL OR r.pdf_path IS NULL OR r.pdf_path = '')
              AND a.ai_score >= 5.0
              AND a.tailored_resume != ?
              AND app.job_id IS NULL
            ORDER BY a.ai_score DESC
        """, (EMPTY_RESUME,)).fetchall()

        if not pending:
            print("\n  (none — all high-score jobs have resumes)")
        else:
            print(f"\n  {len(pending)} jobs waiting for resume generation:\n")
            for i, r in enumerate(pending, 1):
                score = r['ai_score']
                marker = '***' if score >= 7.0 else ' * ' if score >= 6.0 else '   '
                print(f"  {marker} {i:2}. [{score:.1f}] {r['recommendation']:10s} | "
                      f"{r['company'][:25]:25s} | {r['title'][:42]}")
            print(f"\n  *** = APPLY_NOW (>=7.0)    * = APPLY (>=6.0)")
            print(f"\n  -> Run: python scripts/job_pipeline.py --generate")

        # ── 3. Gap: Ready to apply (resume done, not applied) ─────────────
        print("\n" + "=" * 75)
        print("READY TO APPLY: Resume generated, not yet applied")
        print("=" * 75)

        ready = conn.execute("""
            SELECT j.id, j.title, j.company, j.url,
                   a.ai_score, a.recommendation,
                   r.pdf_path, r.submit_dir
            FROM jobs j
            JOIN job_analysis a ON j.id = a.job_id
            JOIN resumes r ON j.id = r.job_id
                AND r.pdf_path IS NOT NULL AND r.pdf_path != ''
            LEFT JOIN applications app ON j.id = app.job_id
            WHERE app.job_id IS NULL
            ORDER BY a.ai_score DESC
        """).fetchall()

        if not ready:
            print("\n  (none — all generated resumes have been applied)")
        else:
            print(f"\n  {len(ready)} jobs ready to apply:\n")
            for i, r in enumerate(ready, 1):
                submit = Path(r['submit_dir']) if r['submit_dir'] else None
                exists = submit.exists() if submit else False
                disk = 'OK' if exists else 'MISSING'
                print(f"  {i:2}. [{r['ai_score']:.1f}] {r['company'][:25]:25s} | "
                      f"{r['title'][:38]:38s} [{disk}]")

        # ── 4. Cross-validation: DB vs filesystem ─────────────────────────
        if not args.pending:
            print("\n" + "=" * 75)
            print("CROSS-VALIDATION: DB records vs ready_to_send/ filesystem")
            print("=" * 75)

            # All resume records in DB with submit_dir
            db_resumes = conn.execute("""
                SELECT j.id, j.title, j.company, r.pdf_path, r.submit_dir,
                       CASE WHEN app.job_id IS NOT NULL THEN 1 ELSE 0 END as is_applied
                FROM resumes r
                JOIN jobs j ON j.id = r.job_id
                LEFT JOIN applications app ON j.id = app.job_id
                WHERE r.submit_dir IS NOT NULL AND r.submit_dir != ''
            """).fetchall()

            db_submit_dirs = {}
            for r in db_resumes:
                dirname = Path(r['submit_dir']).name
                db_submit_dirs[dirname] = r

            # Filesystem: ready_to_send/ (non-applied)
            fs_ready = set()
            if READY_DIR.exists():
                for d in READY_DIR.iterdir():
                    if d.is_dir() and d.name != '_applied':
                        fs_ready.add(d.name)

            # Filesystem: ready_to_send/_applied/
            fs_applied = set()
            if APPLIED_DIR.exists():
                for d in APPLIED_DIR.iterdir():
                    if d.is_dir():
                        fs_applied.add(d.name)

            fs_all = fs_ready | fs_applied

            # Check 1: DB says submit_dir exists, but folder is missing on disk
            missing_on_disk = []
            for dirname, rec in db_submit_dirs.items():
                if dirname not in fs_all:
                    missing_on_disk.append((dirname, rec))

            # Check 2: Folder exists on disk but no DB record
            orphan_on_disk = []
            for dirname in sorted(fs_all):
                if dirname not in db_submit_dirs:
                    location = 'ready' if dirname in fs_ready else '_applied'
                    orphan_on_disk.append((dirname, location))

            # Check 3: DB says not applied, but folder is in _applied/
            inconsistent_applied = []
            for dirname in fs_applied:
                if dirname in db_submit_dirs and db_submit_dirs[dirname]['is_applied'] == 0:
                    inconsistent_applied.append((dirname, db_submit_dirs[dirname]))

            # Check 4: DB says applied, but folder still in ready/ (not archived)
            inconsistent_not_archived = []
            for dirname in fs_ready:
                if dirname in db_submit_dirs and db_submit_dirs[dirname]['is_applied'] == 1:
                    inconsistent_not_archived.append((dirname, db_submit_dirs[dirname]))

            print(f"\n  DB resume records with submit_dir: {len(db_submit_dirs)}")
            print(f"  Folders in ready_to_send/:         {len(fs_ready)}")
            print(f"  Folders in _applied/:               {len(fs_applied)}")
            print(f"  Total on disk:                      {len(fs_all)}")

            all_ok = True

            if missing_on_disk:
                all_ok = False
                print(f"\n  [WARN] DB references folder, but MISSING on disk: {len(missing_on_disk)}")
                for dirname, rec in missing_on_disk[:10]:
                    print(f"    - {dirname}  ({rec['company']} | {rec['title'][:35]})")
                if len(missing_on_disk) > 10:
                    print(f"    ... and {len(missing_on_disk) - 10} more")

            if orphan_on_disk:
                all_ok = False
                print(f"\n  [WARN] Folder on disk, but NO DB record: {len(orphan_on_disk)}")
                for dirname, location in orphan_on_disk[:10]:
                    print(f"    - {dirname}  (in {location}/)")
                if len(orphan_on_disk) > 10:
                    print(f"    ... and {len(orphan_on_disk) - 10} more")

            if inconsistent_applied:
                all_ok = False
                print(f"\n  [WARN] In _applied/ but DB says NOT applied: {len(inconsistent_applied)}")
                for dirname, rec in inconsistent_applied:
                    print(f"    - {dirname}  ({rec['company']})")

            if inconsistent_not_archived:
                all_ok = False
                print(f"\n  [WARN] DB says applied, but folder still in ready/: {len(inconsistent_not_archived)}")
                for dirname, rec in inconsistent_not_archived:
                    print(f"    - {dirname}  ({rec['company']})")

            if all_ok:
                print("\n  All checks passed — DB and filesystem are consistent.")

        print()


if __name__ == "__main__":
    main()
