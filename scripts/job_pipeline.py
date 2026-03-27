"""
Job Pipeline - 完整的职位处理流程
==================================

功能：
1. 从 inbox 导入新职位到数据库
2. 硬规则筛选
3. AI 分析 + 生成定制简历
4. 申请状态跟踪

Usage:
    # 完整处理流程
    python job_pipeline.py --process

    # 只导入
    python job_pipeline.py --import-only

    # 分析文件 (旧接口，兼容)
    python job_pipeline.py --analyze linkedin_ds_scrape_20260201.json

    # 查看待申请
    python job_pipeline.py --ready

    # 查看统计
    python job_pipeline.py --stats

    # 标记已申请
    python job_pipeline.py --mark-applied <job_id>
"""

import json
import sys
import re
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

import yaml

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
LEADS_DIR = DATA_DIR / "leads"
INBOX_DIR = DATA_DIR / "inbox"
ARCHIVE_DIR = DATA_DIR / "archive"
OUTPUT_DIR = PROJECT_ROOT / "output"
TEMPLATES_DIR = PROJECT_ROOT / "templates"
CONFIG_DIR = PROJECT_ROOT / "config"

# 确保目录存在
for d in [DATA_DIR, LEADS_DIR, INBOX_DIR, OUTPUT_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# 尝试导入数据库模块
try:
    from src.db.job_db import JobDatabase, FilterResult, Resume
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[Warning] 数据库模块不可用，使用 JSON 追踪器")

from src.hard_filter import HardFilter


# =============================================================================
# 数据库集成流水线
# =============================================================================

class JobPipeline:
    """Job processing pipeline - Database version"""

    def __init__(self):
        """Initialize pipeline"""
        if not DB_AVAILABLE:
            raise RuntimeError("Database module not available")

        self.db = JobDatabase()
        self.ai_config = self._load_config("ai_config.yaml")
        self.hard_filter = HardFilter()

        print(f"[Pipeline] Database: {self.db.db_path}")

    def _load_config(self, config_name: str) -> dict:
        """加载配置文件"""
        config_path = CONFIG_DIR / config_name
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        print(f"[WARN] Config not found: {config_path}")
        return {}

    def import_inbox(self) -> int:
        """Import all JSON files from inbox"""
        if not INBOX_DIR.exists():
            INBOX_DIR.mkdir(parents=True, exist_ok=True)
            return 0

        json_files = list(INBOX_DIR.glob("*.json"))
        if not json_files:
            print("[Import] inbox is empty")
            return 0

        total_imported = 0
        for json_file in json_files:
            print(f"\n[Import] Processing: {json_file.name}")
            try:
                count = self.db.import_from_json(json_file)
                total_imported += count
                print(f"  -> Imported {count} new jobs")
                self._archive_file(json_file)
            except Exception as e:
                print(f"  x Import failed: {e}")

        return total_imported

    def _archive_file(self, file_path: Path):
        """归档已处理的文件"""
        date_str = datetime.now().strftime("%Y-%m")
        archive_subdir = ARCHIVE_DIR / date_str
        archive_subdir.mkdir(parents=True, exist_ok=True)
        dest = archive_subdir / file_path.name
        if dest.exists():
            dest = archive_subdir / f"{file_path.stem}_{datetime.now().strftime('%H%M%S')}{file_path.suffix}"
        shutil.move(str(file_path), str(dest))

    def filter_jobs(self, limit: int = 500) -> tuple:
        """Filter all unfiltered jobs"""
        unfiltered = self.db.get_unfiltered_jobs(limit=limit)
        if not unfiltered:
            print("[Filter] No jobs to filter")
            return 0, 0

        print(f"\n[Filter] Filtering {len(unfiltered)} jobs...")
        passed_count, rejected_count = 0, 0

        with self.db.batch_mode():
            for job in unfiltered:
                try:
                    result = self.hard_filter.apply(job)
                    self.db.save_filter_result(result)
                    if result.passed:
                        passed_count += 1
                    else:
                        rejected_count += 1
                except Exception as e:
                    print(f"  x Filter error for {job.get('id', '?')}: {e}")
                    continue

        print(f"[Filter] Done: {passed_count} passed, {rejected_count} rejected")
        return passed_count, rejected_count

    def show_stats(self):
        """Show statistics"""
        stats = self.db.get_funnel_stats()
        print("\n=== Funnel Stats ===")
        print(f"Total scraped:    {stats.get('total_scraped', 0)}")
        print(f"Passed filter:    {stats.get('passed_filter', 0)}")
        print(f"AI analyzed:      {stats.get('ai_analyzed', 0)}")
        print(f"AI high (>=5):    {stats.get('ai_scored_high', 0)}")
        print(f"Resume generated: {stats.get('resume_generated', 0)}")
        print(f"Applied:          {stats.get('applied', 0)}")

        print("\n=== Filter Reject Reasons ===")
        for stat in self.db.get_filter_stats():
            print(f"  {stat['reject_reason']}: {stat['count']} ({stat['percentage']}%)")

    def show_ready(self):
        """Show jobs ready to apply and generate application checklist"""
        ready = self.db.get_ready_to_apply()
        if not ready:
            print("No jobs ready to apply")
            return
        print(f"\nReady to apply ({len(ready)}):")
        for i, job in enumerate(ready, 1):
            submit_dir = job.get('submit_dir', '')
            submit_pdf = str(Path(submit_dir) / "Fei_Huang_Resume.pdf") if submit_dir else ''
            dupes = self.db.find_applied_duplicates(job['id'])
            repost_tag = f" [REPOST - applied {dupes[0]['applied_at'][:10]}]" if dupes else ""
            print(f"{i:2}. [{job.get('score', 0):.1f}] {job['title'][:50]} @ {job['company'][:25]}{repost_tag}")
            print(f"    URL:  {job.get('url', 'N/A')}")
            if submit_pdf:
                print(f"    Send: {submit_pdf}")
            print(f"    Full: {job.get('resume_path', 'N/A')}")

        # Generate HTML checklist file
        checklist_path = PROJECT_ROOT / "ready_to_send" / "apply_checklist.html"
        checklist_path.parent.mkdir(parents=True, exist_ok=True)
        from datetime import datetime
        from html import escape
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        rows_html = []
        for i, job in enumerate(ready, 1):
            score = job.get('score', 0)
            rec = job.get('recommendation', '')
            title = escape(job.get('title', ''))
            company = escape(job.get('company', ''))
            url = escape(job.get('url', ''))
            pdf = job.get('resume_path', '')
            submit_dir = job.get('submit_dir', '')
            submit_pdf = str(Path(submit_dir) / "Fei_Huang_Resume.pdf") if submit_dir else ''
            dupes = self.db.find_applied_duplicates(job['id'])
            repost_badge = f' <span style="color:#d32f2f;font-weight:bold" title="Applied {escape(dupes[0]["applied_at"][:10])}">REPOST</span>' if dupes else ''

            score_color = '#2e7d32' if score >= 7.0 else '#e65100' if score >= 6.0 else '#555'
            rows_html.append(f"""<tr>
  <td><input type="checkbox"></td>
  <td><span style="color:{score_color};font-weight:bold">{score:.1f}</span> {escape(rec)}</td>
  <td>{company}{repost_badge}</td>
  <td>{title}</td>
  <td><a href="{url}" target="_blank">Open</a></td>
  <td>{f'<a href="file:///{submit_pdf}" target="_blank">Submit PDF</a>' if submit_pdf else ''}</td>
  <td style="font-size:0.8em;color:#888">{escape(pdf)}</td>
</tr>""")

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Application Checklist</title>
<style>
  body {{ font-family: -apple-system, 'Segoe UI', sans-serif; margin: 2em; background: #fafafa; }}
  h1 {{ margin-bottom: 0.2em; }}
  .meta {{ color: #666; margin-bottom: 1.5em; }}
  table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #f5f5f5; font-weight: 600; position: sticky; top: 0; }}
  tr:hover {{ background: #f0f7ff; }}
  input[type=checkbox] {{ transform: scale(1.3); cursor: pointer; }}
  a {{ color: #1a73e8; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  tr:has(input:checked) {{ background: #e8f5e9; opacity: 0.6; }}
</style></head><body>
<h1>Application Checklist</h1>
<p class="meta">Generated: {now} | Total: {len(ready)} jobs</p>
<table>
<tr><th></th><th>Score</th><th>Company</th><th>Title</th><th>Job Link</th><th>Resume</th><th>Tracking Path</th></tr>
{"".join(rows_html)}
</table></body></html>"""

        checklist_path.write_text(html, encoding="utf-8")
        print(f"\nChecklist saved: {checklist_path}")

    # ==================== AI Analysis & Resume Generation ====================

    def ai_analyze_jobs(self, limit: int = None, model: str = None) -> int:
        """AI 分析通过预筛选的职位"""
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer(model_override=model)
        return analyzer.analyze_batch(limit=limit)

    def generate_resumes(self, min_ai_score: float = None, limit: int = None) -> int:
        """为高分职位生成简历"""
        from src.resume_renderer import ResumeRenderer
        renderer = ResumeRenderer()

        # Check for reposts before rendering
        jobs = self.db.get_analyzed_jobs_for_resume(min_ai_score=min_ai_score, limit=limit)
        for job in jobs:
            dupes = self.db.find_applied_duplicates(job['id'])
            if dupes:
                print(f"  ⚠ REPOST: {job.get('title', '')} @ {job.get('company', '')} — applied {dupes[0]['applied_at'][:10]}")

        return renderer.render_batch(min_ai_score=min_ai_score, limit=limit)

    def generate_cover_letter(self, job_id: str, custom_requirements: str = None,
                              force: bool = False):
        """Generate + render cover letter for a single job"""
        from src.cover_letter_generator import CoverLetterGenerator
        from src.cover_letter_renderer import CoverLetterRenderer
        generator = CoverLetterGenerator()
        result = generator.generate(job_id, custom_requirements=custom_requirements, force=force)
        if result:
            renderer = CoverLetterRenderer()
            renderer.render(job_id)

    def generate_cover_letters_batch(self, min_ai_score: float = None, limit: int = 50):
        """Batch generate + render cover letters"""
        from src.cover_letter_generator import CoverLetterGenerator
        from src.cover_letter_renderer import CoverLetterRenderer

        generator = CoverLetterGenerator()
        generated = generator.generate_batch(min_ai_score=min_ai_score, limit=limit)

        if generated > 0:
            renderer = CoverLetterRenderer()
            renderer.render_batch(min_ai_score=min_ai_score, limit=limit)

    def cmd_prepare(self, min_ai_score: float = None, limit: int = None):
        """One-command: generate all materials + launch checklist server."""
        from src.checklist_server import generate_checklist, start_server
        from src.resume_renderer import ResumeRenderer

        threshold = min_ai_score or self.ai_config.get('thresholds', {}).get(
            'ai_score_generate_resume', 5.0)
        limit = limit or 50

        # Step 1: Sync from Turso
        print("Syncing database...")
        self.db.final_sync()

        # Step 2: Generate resumes for jobs that need them
        renderer = ResumeRenderer()
        jobs = self.db.get_analyzed_jobs_for_resume(
            min_ai_score=threshold, limit=limit)

        results = {"success": [], "failed": []}

        if jobs:
            print(f"\nGenerating materials for {len(jobs)} jobs...")

            for job in jobs:
                job_id = job['id']
                company = job.get('company', 'Unknown')
                title = job.get('title', 'Unknown')
                label = f"{company} - {title}"

                # Resume
                try:
                    resume_result = renderer.render_resume(job_id)
                    if not resume_result:
                        results["failed"].append((label, "render returned None"))
                        continue
                except Exception as e:
                    results["failed"].append((label, str(e)))
                    continue

                results["success"].append(label)
        else:
            print("No new jobs need resume generation.")

        # Step 3: Collect ALL ready-to-apply jobs (new + existing)
        all_ready = self.db.get_ready_to_apply()

        # Step 3.1: Restore submit_dirs cleaned by previous --finalize
        candidate_name = renderer._safe_filename(
            renderer.candidate.get('name', 'Resume'))
        restored = 0
        for job in all_ready:
            submit_dir = job.get('submit_dir')
            if submit_dir and Path(submit_dir).is_dir():
                continue  # Already exists on disk

            # Look up source PDF in output/
            resume_rec = self.db.get_resume(job['id'])
            if not resume_rec or not resume_rec.get('pdf_path'):
                continue
            src_pdf = Path(resume_rec['pdf_path'])
            if not src_pdf.exists():
                continue

            # Re-create submit_dir and copy resume PDF
            target_dir = Path(resume_rec['submit_dir']) if resume_rec.get('submit_dir') else None
            if not target_dir:
                continue
            target_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_pdf, target_dir / f"{candidate_name}_Resume.pdf")

            # Restore cover letter files if available
            cl_rec = self.db.get_cover_letter(job['id'])
            if cl_rec:
                cl_pdf = Path(cl_rec['pdf_path']) if cl_rec.get('pdf_path') else None
                if cl_pdf and cl_pdf.exists():
                    shutil.copy2(cl_pdf, target_dir / f"{candidate_name}_Cover_Letter.pdf")
                if cl_rec.get('short_text'):
                    (target_dir / f"{candidate_name}_Cover_Letter.txt").write_text(
                        cl_rec['short_text'], encoding='utf-8')

            job['submit_dir'] = str(target_dir)
            restored += 1

        if restored:
            print(f"  Restored {restored} submit directories from output/")

        # Filter out jobs whose submit_dir still doesn't exist (source PDF gone)
        before_count = len(all_ready)
        all_ready = [j for j in all_ready if j.get('submit_dir') and Path(j['submit_dir']).is_dir()]
        if before_count > len(all_ready):
            print(f"  Skipped {before_count - len(all_ready)} jobs (resume files missing).")

        # Enrich with repost info
        repost_count = 0
        for job in all_ready:
            dupes = self.db.find_applied_duplicates(job['id'])
            if dupes:
                job['repost_applied_at'] = dupes[0]['applied_at'][:10]
                repost_count += 1

        # Enrich with rejection history
        rejection_count = 0
        for job in all_ready:
            rejected = self.db.find_rejected_duplicates(job['id'])
            if rejected:
                job['rejection_rejected_at'] = (rejected[0].get('rejected_at') or '')[:10]
                rejection_count += 1

        if not all_ready:
            print("\nNo jobs ready to apply. All caught up!")
            return

        # Step 4: Generate checklist
        ready_dir = Path(PROJECT_ROOT) / "ready_to_send"
        generate_checklist(all_ready, ready_dir)

        # Step 5: Summary report
        print(f"\n{'='*50}")
        print(f"  PREPARE SUMMARY")
        print(f"{'='*50}")
        if results["success"]:
            print(f"  New resumes: {len(results['success'])}")
        if results["failed"]:
            print(f"  Failed:      {len(results['failed'])}")
            for label, err in results["failed"]:
                print(f"    x {label}: {err[:80]}")
        print(f"  Total ready: {len(all_ready)}")
        if repost_count:
            print(f"  Reposts:     {repost_count} (already applied to same company+title)")
        print(f"{'='*50}\n")

        # Step 6: Start checklist server
        start_server(ready_dir)

    def cmd_finalize(self):
        """Read checklist state, archive applied jobs, clean up skipped."""
        ready_dir = Path(PROJECT_ROOT) / "ready_to_send"
        state_path = ready_dir / "state.json"

        if not state_path.exists():
            print("No state.json found. Run --prepare first.")
            return

        state = json.loads(state_path.read_text(encoding="utf-8"))
        jobs = state.get("jobs", {})

        if not jobs:
            print("No jobs in state. Nothing to finalize.")
            return

        applied = {jid: j for jid, j in jobs.items() if j.get("applied")}
        skipped = {jid: j for jid, j in jobs.items() if not j.get("applied")}

        applied_dir = ready_dir / "_applied"
        if applied:
            applied_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc).isoformat()

        skipped_dir = ready_dir / "_skipped"

        # Process applied jobs
        for job_id, info in applied.items():
            try:
                self.db.update_application_status(job_id, "applied", applied_at=now)
                if not info.get("submit_dir"):
                    continue
                src = ready_dir / info["submit_dir"]
                if src.exists() and src.is_dir():
                    dest = applied_dir / src.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.move(str(src), str(dest))
            except Exception as e:
                print(f"  [WARN] Failed to finalize applied {job_id}: {e}")

        # Process skipped jobs (move to _skipped/ instead of deleting)
        for job_id, info in skipped.items():
            try:
                self.db.update_application_status(job_id, "skipped")
                if not info.get("submit_dir"):
                    continue
                src = ready_dir / info["submit_dir"]
                if src.exists() and src.is_dir():
                    skipped_dir.mkdir(parents=True, exist_ok=True)
                    dest = skipped_dir / src.name
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.move(str(src), str(dest))
            except Exception as e:
                print(f"  [WARN] Failed to finalize skipped {job_id}: {e}")

        # Detect edited cover letters
        edited_cls_dir = ready_dir / "_edited_cls"
        edited_count = 0
        for job_id, info in applied.items():
            submit_dir_name = info.get("submit_dir", "")
            if not submit_dir_name:
                continue
            archived_dir = applied_dir / Path(submit_dir_name).name
            if not archived_dir.exists():
                continue

            # Find CL txt file in archived dir
            cl_files = list(archived_dir.glob("*_Cover_Letter.txt"))
            if not cl_files:
                continue

            file_text = cl_files[0].read_text(encoding="utf-8").strip().replace('\r\n', '\n')
            if not file_text:
                continue

            # Compare with DB short_text (TXT files contain short version)
            cl_record = self.db.get_cover_letter(job_id)
            if not cl_record:
                continue
            db_text = (cl_record.get("short_text") or "").strip().replace('\r\n', '\n')

            if file_text != db_text:
                company = info.get("company", "unknown")
                edited_cls_dir.mkdir(parents=True, exist_ok=True)
                safe_co = re.sub(r'[^\w\s-]', '', company).strip().replace(' ', '_')[:20]
                out_name = f"{safe_co}_{job_id[:8]}_edited_cl.txt"
                (edited_cls_dir / out_name).write_text(file_text, encoding="utf-8")
                edited_count += 1
                print(f"  [EDITED CL] {company} - saved to _edited_cls/{out_name}")

        if edited_count:
            print(f"\n  {edited_count} edited cover letter(s) detected.")
            print(f"  Review in ready_to_send/_edited_cls/ and extract to cl_knowledge_base.yaml")

        # Clean up state files
        state_path.unlink(missing_ok=True)
        checklist_path = ready_dir / "apply_checklist.html"
        if checklist_path.exists():
            checklist_path.unlink()

        # Sync to Turso
        print("Syncing to cloud...")
        self.db.final_sync()

        # Report
        print(f"\n{'='*50}")
        print(f"  FINALIZE SUMMARY")
        print(f"{'='*50}")
        if applied:
            print(f"  Applied ({len(applied)}):")
            for jid, info in applied.items():
                print(f"    -> {info['company']} - {info['title']}")
        if skipped:
            print(f"  Skipped ({len(skipped)}):")
            for jid, info in skipped.items():
                print(f"    -- {info['company']} - {info['title']}")
        print(f"{'='*50}")

    def cmd_archive(self, retention_days: int = 7):
        """Archive cold jobs to local SQLite and delete from live DB."""
        # Preview first
        cold_ids = self.db.get_cold_job_ids(retention_days=retention_days)
        if not cold_ids:
            print(f"[Archive] No cold jobs found (retention: {retention_days} days)")
            return

        print(f"\n[Archive] Found {len(cold_ids)} cold jobs (older than {retention_days} days, not applied/interview/offer)")

        # Confirm
        try:
            confirm = input(f"Archive and delete {len(cold_ids)} jobs from live DB? (y/n): ").strip().lower()
        except EOFError:
            confirm = 'n'
        if confirm != 'y':
            print("[Archive] Cancelled")
            return

        result = self.db.archive_cold_data(retention_days=retention_days)

        print(f"\n{'='*50}")
        print(f"  ARCHIVE SUMMARY")
        print(f"{'='*50}")
        print(f"  Archived: {result['archived_count']} jobs")
        print(f"  Archive:  {result['archive_path']}")
        if result['archive_path']:
            import os
            size_mb = os.path.getsize(result['archive_path']) / (1024 * 1024)
            print(f"  Size:     {size_mb:.1f} MB")
        if result['details']:
            print(f"  Details:")
            for table, count in result['details'].items():
                print(f"    {table}: {count} rows")
        print(f"{'='*50}")

        # Sync to Turso
        print("\nSyncing deletions to Turso...")
        self.db.final_sync()
        print("Turso sync complete.")

    def analyze_single_job(self, job_id: str, model: str = None):
        """分析单个职位"""
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer(model_override=model)
        result = analyzer.analyze_single(job_id)
        if result:
            print(f"\nTailored Resume Preview:")
            tailored = json.loads(result.tailored_resume) if result.tailored_resume else {}
            if tailored.get('bio'):
                print(f"  Bio: {tailored['bio'][:100]}...")
            else:
                print(f"  Bio: (omitted)")
            if 'experiences' in tailored:
                print(f"  Experiences: {len(tailored['experiences'])} selected")
        return result

    def process_all(self, limit: int = 50):
        """Run full processing pipeline (including AI analysis and resume generation)"""
        print("=" * 70)
        print("Job Hunter Pipeline v2.0 (with AI Analysis)")
        print("=" * 70)

        imported = self.import_inbox()
        passed, rejected = self.filter_jobs(limit=limit)

        print("\n" + "-" * 70)
        print("Stage 1 Complete: imported {}, filtered {}/{}".format(
            imported, passed, passed+rejected))
        print("-" * 70)

        # AI Analysis (optional - only if filtered jobs exist without analysis)
        ai_thresholds = self.ai_config.get('thresholds', {})
        ai_score_threshold = ai_thresholds.get('ai_score_generate_resume', 5.0)

        jobs_for_ai = self.db.get_jobs_needing_analysis(limit=limit)
        if jobs_for_ai:
            print(f"\nFound {len(jobs_for_ai)} jobs ready for AI analysis")
            try:
                user_input = input("Run AI analysis? (y/n, default: n): ").strip().lower()
            except EOFError:
                user_input = 'n'
            if user_input == 'y':
                analyzed = self.ai_analyze_jobs(limit=limit)
                print(f"AI analyzed: {analyzed} jobs")

                # Resume generation
                jobs_for_resume = self.db.get_analyzed_jobs_for_resume(min_ai_score=ai_score_threshold, limit=limit)
                if jobs_for_resume:
                    print(f"\nFound {len(jobs_for_resume)} jobs ready for resume generation")
                    try:
                        user_input = input("Generate resumes? (y/n, default: n): ").strip().lower()
                    except EOFError:
                        user_input = 'n'
                    if user_input == 'y':
                        generated = self.generate_resumes(min_ai_score=ai_score_threshold, limit=limit)
                        print(f"Resumes generated: {generated}")
                        # Also generate cover letters
                        self.generate_cover_letters_batch(min_ai_score=ai_score_threshold, limit=limit)

        print("\n" + "=" * 70)
        self.show_stats()
        print("=" * 70)


# =============================================================================
# Gmail Command Handlers
# =============================================================================

def cmd_test_gmail():
    """Test Gmail IMAP connection."""
    try:
        from src.gmail_client import GmailClient
        with GmailClient() as client:
            addr = client.test_connection()
            print(f"\n[OK] Gmail IMAP connection successful: {addr}")
    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        print("  Run: pip install imapclient>=3.0.0")
    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("  Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env file")
    except Exception as e:
        print(f"\n[ERROR] Connection failed: {e}")


def cmd_read_email(subject_pattern: str, lookback_days: int = 7):
    """Read and display a specific email by subject pattern."""
    try:
        from src.gmail_client import GmailClient, format_email_for_display
        
        print(f"\nSearching for email with subject: '{subject_pattern}'...")
        
        with GmailClient() as client:
            email_data = client.get_email_by_subject(subject_pattern, lookback_days)
            
            if email_data:
                print(format_email_for_display(email_data))
            else:
                print(f"\n[NOT FOUND] No email found with subject containing: '{subject_pattern}'")
                print(f"  Try increasing --lookback-days (current: {lookback_days})")
                
    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        print("  Run: pip install imapclient>=3.0.0")
    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("  Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env file")
    except Exception as e:
        print(f"\n[ERROR] Error reading email: {e}")


def cmd_search_emails(keyword: str, lookback_days: int = 7):
    """Search and list emails by keyword."""
    try:
        from src.gmail_client import GmailClient
        
        print(f"\nSearching emails with keyword: '{keyword}'...")
        
        with GmailClient() as client:
            emails = client.search_emails(
                subject_keywords=[keyword],
                lookback_days=lookback_days,
                max_results=20
            )
            
            if not emails:
                print(f"\n[NOT FOUND] No emails found with keyword: '{keyword}'")
                return
            
            print(f"\nFound {len(emails)} email(s):\n")
            print("-" * 80)
            
            for i, email_data in enumerate(emails, 1):
                subject = email_data.get('subject', 'N/A')[:60]
                sender = email_data.get('sender', 'N/A')[:40]
                date = email_data.get('date', 'N/A')[:30]
                
                print(f"{i}. {subject}")
                print(f"   From: {sender}")
                print(f"   Date: {date}")
                print("-" * 80)
                
    except ImportError as e:
        print(f"\n[ERROR] Import error: {e}")
        print("  Run: pip install imapclient>=3.0.0")
    except ValueError as e:
        print(f"\n[ERROR] Configuration error: {e}")
        print("  Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env file")
    except Exception as e:
        print(f"\n[ERROR] Error searching emails: {e}")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Job Pipeline')
    parser.add_argument('--analyze', help='Analyze jobs from JSON file (legacy)')
    parser.add_argument('--process', action='store_true', help='Run full pipeline (DB)')
    parser.add_argument('--import-only', action='store_true', help='Only import inbox')
    parser.add_argument('--filter', action='store_true', help='Only run filter')
    parser.add_argument('--ready', action='store_true', help='Show ready to apply')
    parser.add_argument('--stats', action='store_true', help='Show stats')
    parser.add_argument('--mark-applied', type=str, help='Mark job as applied')
    parser.add_argument('--mark-all-applied', action='store_true',
                        help='Mark ALL ready-to-apply jobs as applied and archive ready_to_send/')
    parser.add_argument('--update-status', nargs=2, metavar=('JOB_ID', 'STATUS'),
                        help='Update application status (rejected/interview/offer)')
    parser.add_argument('--tracker', action='store_true',
                        help='Show application tracker (status breakdown)')
    parser.add_argument('--reprocess', action='store_true',
                        help='Clear old filter/score results and reprocess all jobs with new rules')
    parser.add_argument('--retry-failures', action='store_true',
                        help='Clear transient AI failures (parse/truncation/empty) and re-analyze')

    # New AI-powered commands
    parser.add_argument('--ai-analyze', action='store_true',
                        help='Run AI analysis on scored jobs')
    parser.add_argument('--generate', action='store_true',
                        help='Generate resumes for AI-analyzed jobs')
    parser.add_argument('--analyze-job', type=str,
                        help='Analyze a single job by ID')
    parser.add_argument('--min-score', type=float, default=None,
                        help='Minimum score threshold for AI commands')
    parser.add_argument('--limit', type=int, default=None,
                        help='Max jobs to process (default: no limit)')
    parser.add_argument('--model', type=str, default=None,
                        choices=['opus', 'kimi'],
                        help='AI model: opus (Claude) or kimi')

    # Cover letter commands
    parser.add_argument('--cover-letter', type=str, metavar='JOB_ID',
                        help='Generate cover letter for a specific job')
    parser.add_argument('--cover-letters', action='store_true',
                        help='Batch generate cover letters for jobs with resumes')
    parser.add_argument('--requirements', type=str, default=None,
                        help='Custom requirements from application page (use with --cover-letter)')
    parser.add_argument('--regen', action='store_true',
                        help='Force regenerate (use with --cover-letter)')

    # Local workflow commands
    parser.add_argument('--prepare', action='store_true',
                        help='Generate all application materials and launch checklist')
    parser.add_argument('--finalize', action='store_true',
                        help='Archive applied jobs, clean up skipped, sync to cloud')

    # Archive command
    parser.add_argument('--archive', action='store_true',
                        help='Archive cold jobs to local SQLite and purge from live DB')
    parser.add_argument('--retention-days', type=int, default=7,
                        help='Days to retain in live DB (default: 7, use with --archive)')

    # Interview scheduling commands
    parser.add_argument('--schedule-interview', type=str, metavar='COMPANY',
                        help='Suggest best interview slots for a company')
    parser.add_argument('--suggest-availability', type=str, metavar='COMPANY',
                        help='Show all available interview slots for a company')
    parser.add_argument('--duration', type=int, default=60,
                        help='Interview duration in minutes (default: 60)')
    parser.add_argument('--days', type=int, default=14,
                        help='Days ahead to search for slots (default: 14)')

    # Gmail commands
    parser.add_argument('--read-email', type=str, metavar='SUBJECT',
                        help='Read email by subject pattern (e.g., "FareHarbor")')
    parser.add_argument('--search-emails', type=str, metavar='KEYWORD',
                        help='Search emails by keyword')
    parser.add_argument('--lookback-days', type=int, default=7,
                        help='Days to look back for email search (default: 7)')
    parser.add_argument('--test-gmail', action='store_true',
                        help='Test Gmail IMAP connection')

    args = parser.parse_args()

    # 重新处理所有职位 (清除旧结果)
    if args.reprocess:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        pipeline = JobPipeline()
        print("[Reprocess] Clearing old filter and analysis results...")
        filter_count = pipeline.db.clear_filter_results()
        analysis_count = pipeline.db.clear_rejected_analyses()
        print(f"  Cleared {filter_count} filter results, {analysis_count} rejected analyses")

        # Reprocess all jobs (ignore --limit to avoid data loss from partial reprocessing)
        pipeline.filter_jobs()
        pipeline.show_stats()
        pipeline.db.final_sync()
        return

    # 重试瞬态失败 (parse failure / truncation / empty response)
    if args.retry_failures:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        pipeline = JobPipeline()
        cleared = pipeline.db.clear_transient_failures()
        if cleared == 0:
            print("[Retry] No transient failures found.")
            return
        print(f"[Retry] Cleared {cleared} transient failure(s), re-analyzing...")
        pipeline.ai_analyze_jobs(limit=cleared + 10, model=args.model)
        pipeline.db.final_sync()
        return

    # Gmail commands (standalone, don't require DB)
    if args.test_gmail:
        cmd_test_gmail()
        return
    if args.read_email:
        cmd_read_email(args.read_email, args.lookback_days)
        return
    if args.search_emails:
        cmd_search_emails(args.search_emails, args.lookback_days)
        return

    # 新版数据库流水线
    if args.process or args.import_only or args.filter or args.ready \
       or args.ai_analyze or args.generate or args.analyze_job \
       or args.stats or args.mark_applied or args.mark_all_applied \
       or args.update_status or args.tracker \
       or args.cover_letter or args.cover_letters \
       or args.prepare or args.finalize or args.archive \
       or args.schedule_interview or args.suggest_availability:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        pipeline = JobPipeline()
        if args.prepare:
            pipeline.cmd_prepare(min_ai_score=args.min_score, limit=args.limit)
        elif args.finalize:
            pipeline.cmd_finalize()
        elif args.archive:
            pipeline.cmd_archive(retention_days=args.retention_days)
        elif args.schedule_interview:
            from src.interview_scheduler import InterviewScheduler, format_slots
            scheduler = InterviewScheduler()
            slots = scheduler.suggest_slots(
                company=args.schedule_interview,
                duration_minutes=args.duration,
                days=args.days,
            )
            print(format_slots(slots))
        elif args.suggest_availability:
            from src.interview_scheduler import InterviewScheduler, format_availability
            scheduler = InterviewScheduler()
            by_date = scheduler.suggest_availability(
                company=args.suggest_availability,
                duration_minutes=args.duration,
                days=args.days,
            )
            print(format_availability(by_date))
        elif args.process:
            pipeline.process_all(limit=args.limit)
        elif args.import_only:
            pipeline.import_inbox()
        elif args.filter:
            pipeline.filter_jobs(limit=args.limit)
        elif args.ready:
            pipeline.show_ready()
        elif args.ai_analyze:
            pipeline.ai_analyze_jobs(limit=args.limit, model=args.model)
        elif args.generate:
            pipeline.generate_resumes(min_ai_score=args.min_score, limit=args.limit)
        elif args.cover_letter:
            pipeline.generate_cover_letter(args.cover_letter,
                                           custom_requirements=args.requirements,
                                           force=args.regen)
        elif args.cover_letters:
            pipeline.generate_cover_letters_batch(min_ai_score=args.min_score,
                                                   limit=args.limit)
        elif args.analyze_job:
            pipeline.analyze_single_job(args.analyze_job, model=args.model)
        elif args.stats:
            pipeline.show_stats()
        elif args.mark_applied:
            job_id = args.mark_applied
            pipeline.db.update_application_status(job_id, "applied", applied_at=datetime.now(timezone.utc).isoformat())
            # Archive the ready_to_send folder
            resume = pipeline.db.get_resume(job_id)
            if resume and resume.get('submit_dir'):
                submit_dir = Path(resume['submit_dir'])
                if submit_dir.exists():
                    applied_dir = submit_dir.parent / "_applied"
                    applied_dir.mkdir(parents=True, exist_ok=True)
                    dest = applied_dir / submit_dir.name
                    shutil.move(str(submit_dir), str(dest))
                    print(f"[Applied] {job_id}")
                    print(f"  -> Archived: _applied/{submit_dir.name}/")
                else:
                    print(f"[Applied] {job_id} (submit folder not found)")
            else:
                print(f"[Applied] {job_id}")
        elif args.mark_all_applied:
            ready = pipeline.db.get_ready_to_apply()
            if not ready:
                print("[Mark All] No ready-to-apply jobs to mark")
            else:
                now = datetime.now(timezone.utc).isoformat()
                archived = 0
                for job in ready:
                    job_id = job['id']
                    pipeline.db.update_application_status(job_id, "applied", applied_at=now)
                    submit_dir = Path(job['submit_dir']) if job.get('submit_dir') else None
                    if submit_dir and submit_dir.exists():
                        applied_dir = submit_dir.parent / "_applied"
                        applied_dir.mkdir(parents=True, exist_ok=True)
                        dest = applied_dir / submit_dir.name
                        shutil.move(str(submit_dir), str(dest))
                        archived += 1
                # Also move checklist
                checklist = PROJECT_ROOT / "ready_to_send" / "apply_checklist.html"
                if checklist.exists():
                    applied_dir = checklist.parent / "_applied"
                    applied_dir.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(checklist), str(applied_dir / checklist.name))
                print(f"[Mark All] {len(ready)} jobs marked as applied, {archived} folders archived")
        elif args.update_status:
            job_id, status = args.update_status
            valid = {'rejected', 'interview', 'offer'}
            if status not in valid:
                print(f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid))}")
                sys.exit(1)
            kwargs = {}
            if status == 'rejected':
                kwargs['response_at'] = datetime.now(timezone.utc).isoformat()
            elif status == 'interview':
                kwargs['interview_at'] = datetime.now(timezone.utc).isoformat()
            elif status == 'offer':
                kwargs['response_at'] = datetime.now(timezone.utc).isoformat()
            pipeline.db.update_application_status(job_id, status, **kwargs)
            job = pipeline.db.get_job(job_id)
            name = f"{job['title'][:40]} @ {job['company']}" if job else job_id
            print(f"[Status] {name} -> {status}")
        elif args.tracker:
            tracker = pipeline.db.get_application_tracker()
            # Summary
            print("\n=== Application Tracker ===")
            total = sum(s['count'] for s in tracker['summary'])
            print(f"Total tracked: {total}")
            for s in tracker['summary']:
                print(f"  {s['status']:12s}: {s['count']}")
            # Per-status details
            for status, jobs in tracker['by_status'].items():
                if not jobs:
                    continue
                print(f"\n--- {status.upper()} ({len(jobs)}) ---")
                for j in jobs[:20]:
                    days = j.get('days_since', '?')
                    print(f"  [{j.get('score', 0):.1f}] {j['company']:25s} | {j['title'][:40]}  ({days}d ago)")
                if len(jobs) > 20:
                    print(f"  ... and {len(jobs) - 20} more")
            # Stale applications — likely ghosted
            STALE_DAYS = 30
            stale = [j for j in tracker['by_status'].get('applied', [])
                     if isinstance(j.get('days_since'), (int, float)) and j['days_since'] >= STALE_DAYS]
            if stale:
                print(f"\n--- LIKELY GHOSTED ({len(stale)}, applied {STALE_DAYS}+ days ago) ---")
                for j in stale[:15]:
                    print(f"  [{j.get('score', 0):.1f}] {j['company']:25s} | {j['title'][:40]}  ({j['days_since']}d)")
                if len(stale) > 15:
                    print(f"  ... and {len(stale) - 15} more")

        # Final sync: push all accumulated writes to Turso remote.
        # In "startup_only" mode this is the ONLY push; in "full" mode it's a
        # harmless no-op (data was already synced incrementally).
        pipeline.db.final_sync()
        return

    # 旧版 JSON 分析 (已废弃)
    if args.analyze:
        print("[DEPRECATED] --analyze is removed in v2.0. Use --ai-analyze instead.")
        sys.exit(1)

    # Help message
    print("Job Pipeline v2.0 - Commands:")
    print()
    print("  Basic:")
    print("  --process          Run full pipeline (import/filter)")
    print("  --import-only      Only import from inbox")
    print("  --filter           Only run hard filter")
    print("  --ready            Show ready-to-apply jobs")
    print("  --stats            Show funnel stats")
    print("  --reprocess        Clear and reprocess all jobs")
    print("  --retry-failures   Clear transient AI failures and re-analyze")
    print("  --mark-applied ID  Mark job as applied")
    print("  --mark-all-applied Mark ALL ready jobs as applied + archive")
    print("  --update-status ID STATUS  Update status (rejected/interview/offer)")
    print("  --tracker          Show application tracker")
    print("  --archive          Archive cold jobs to local DB + purge from live DB")
    print("  --retention-days N Days to keep in live DB (default: 7, use with --archive)")
    print()
    print("  AI-powered:")
    print("  --ai-analyze       AI analysis on scored jobs")
    print("  --generate         Generate resumes for AI high-score jobs")
    print("  --analyze-job ID   Analyze a single job")
    print()
    print("  Cover Letters:")
    print("  --cover-letter ID  Generate cover letter for a job")
    print("  --cover-letters    Batch generate cover letters")
    print("  --requirements TXT Custom requirements (with --cover-letter)")
    print("  --regen            Force regenerate (with --cover-letter)")
    print()
    print("  Interview Scheduling:")
    print("  --schedule-interview COMPANY  Suggest best interview slots")
    print("  --suggest-availability COMPANY  Show all available slots")
    print("  --duration N       Interview duration in minutes (default: 60)")
    print("  --days N           Days ahead to search (default: 14)")
    print()
    print("  Gmail:")
    print("  --read-email SUBJECT    Read email by subject pattern")
    print("  --search-emails KEYWORD Search emails by keyword")
    print("  --lookback-days N       Days to search back (default: 7)")
    print("  --test-gmail            Test Gmail IMAP connection")
    print()
    print("  Options:")
    print("  --min-score N      Minimum score threshold")
    print("  --limit N          Max jobs to process (default: no limit)")
    print()
    print("  Legacy:")
    print("  --analyze FILE     Analyze JSON file")


if __name__ == "__main__":
    main()
