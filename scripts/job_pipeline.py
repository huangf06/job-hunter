"""
Job Pipeline - 完整的职位处理流程
==================================

功能：
1. 从 inbox 导入新职位到数据库
2. 硬规则筛选
3. AI 评分
4. 生成定制简历
5. 申请状态跟踪

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
    from src.db.job_db import JobDatabase, FilterResult, ScoreResult, Resume
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("[Warning] 数据库模块不可用，使用 JSON 追踪器")


## Legacy JobAnalyzer removed in v2.0 cleanup — use JobPipeline + AI Analyzer instead


## Legacy ResumeTailor removed in v2.0 cleanup — use ResumeRenderer (src/resume_renderer.py) instead


def _keyword_boundary_pattern(kw: str) -> str:
    """Build regex pattern with proper word boundaries for keywords with non-word chars at edges.

    Standard \\b fails for keywords like '.net' (leading dot) or 'c#' (trailing hash).
    For leading non-word chars: skip boundary (the char itself is discriminating).
    For trailing non-word chars: use (?!\\w) lookahead.
    """
    escaped = re.escape(kw)
    prefix = '' if kw and not kw[0].isalnum() and kw[0] != '_' else r'\b'
    suffix = r'(?!\w)' if kw and not kw[-1].isalnum() and kw[-1] != '_' else r'\b'
    return prefix + escaped + suffix


class JobTracker:
    """职位追踪器"""
    
    TRACKER_FILE = DATA_DIR / "job_tracker.json"
    
    def __init__(self):
        self.data = self._load()
    
    def _load(self) -> Dict:
        """加载追踪数据"""
        default_data = {
            "jobs": [],
            "stats": {
                "total_analyzed": 0,
                "total_applied": 0,
                "responses": 0,
                "interviews": 0,
                "offers": 0
            }
        }
        
        if self.TRACKER_FILE.exists():
            with open(self.TRACKER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 确保所有必要字段存在
                for key, value in default_data.items():
                    if key not in data:
                        data[key] = value
                return data
        
        return default_data
    
    def _save(self):
        """保存追踪数据"""
        with open(self.TRACKER_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)
    
    def add_job(self, job: Dict, analysis: Dict):
        """添加职位到追踪器"""
        job_id = self._generate_id(job)
        
        # 检查是否已存在
        if any(j['id'] == job_id for j in self.data['jobs']):
            return False
        
        entry = {
            "id": job_id,
            "title": job.get('title'),
            "company": job.get('company'),
            "location": job.get('location'),
            "url": job.get('url'),
            "score": analysis.get('score'),
            "recommendation": analysis.get('recommendation'),
            "status": "new",
            "added_at": datetime.now().isoformat(),
            "applied_at": None,
            "resume_path": None,
            "notes": []
        }
        
        self.data['jobs'].append(entry)
        self.data['stats']['total_analyzed'] += 1
        self._save()
        return True
    
    def _generate_id(self, job: Dict) -> str:
        """生成唯一 ID"""
        import hashlib
        key = f"{job.get('title', '')}-{job.get('company', '')}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
    
    def get_high_priority_jobs(self, min_score: float = 6.0) -> List[Dict]:
        """获取高优先级职位"""
        return [
            j for j in self.data['jobs']
            if j.get('score', 0) >= min_score and j['status'] == 'new'
        ]
    
    def mark_applied(self, job_id: str, resume_path: str = None):
        """标记为已申请"""
        for job in self.data['jobs']:
            if job['id'] == job_id:
                job['status'] = 'applied'
                job['applied_at'] = datetime.now().isoformat()
                if resume_path:
                    job['resume_path'] = str(resume_path)
                self.data['stats']['total_applied'] += 1
                self._save()
                return True
        return False
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.data['stats']


def print_analysis_report(jobs: List[Dict], top_n: int = 10):
    """打印分析报告"""
    print("\n" + "=" * 80)
    print("JOB ANALYSIS REPORT")
    print("=" * 80)
    print(f"Total jobs analyzed: {len(jobs)}")
    print(f"Top {top_n} by match score:\n")

    for i, job in enumerate(jobs[:top_n], 1):
        score = job.get('score', 0)
        rec = job.get('recommendation', 'UNKNOWN')
        title = job.get('title', 'N/A')
        company = job.get('company', 'N/A')
        location = job.get('location', 'N/A')

        # 颜色代码 (仅支持终端)
        if score >= 7:
            color = "\033[92m"  # Green
        elif score >= 5:
            color = "\033[93m"  # Yellow
        else:
            color = "\033[91m"  # Red
        reset = "\033[0m"

        print(f"{i}. [{color}{score:.1f}{reset}] {rec}")
        print(f"   {title} @ {company}")
        print(f"   Location: {location}")

        # 打印正面原因
        reasons = job.get('reasons', {})
        if reasons.get('positive'):
            print(f"   + {', '.join(reasons['positive'][:3])}")
        print()


# =============================================================================
# 新版数据库集成流水线
# =============================================================================

class JobPipeline:
    """Job processing pipeline - Database version"""

    def __init__(self):
        """Initialize pipeline"""
        if not DB_AVAILABLE:
            raise RuntimeError("Database module not available")

        self.db = JobDatabase()
        self.filter_config = self._load_config("base/filters.yaml")
        self.score_config = self._load_config("base/scoring.yaml")
        self.ai_config = self._load_config("ai_config.yaml")

        # Cache company and title blacklists (avoid reloading per-job)
        search_profiles = self._load_config("search_profiles.yaml")
        self.company_blacklist = [c.lower() for c in search_profiles.get('company_blacklist', [])]
        self.title_blacklist = [t.lower() for t in search_profiles.get('title_blacklist', [])]

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
                    result = self._apply_filter(job)
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

    def _apply_filter(self, job: Dict) -> FilterResult:
        """应用筛选规则 v2.0

        支持多种检测类型:
        - word_count: 荷兰语词频检测
        - title_check: 标题白名单/黑名单检查
        - tech_stack: 技术栈检查 (标题 + 正文)
        - regex: 正则表达式匹配
        """
        job_id = job['id']
        title = (job.get('title') or '').lower()
        description = (job.get('description') or '').lower()
        company = (job.get('company') or '').lower()
        location = (job.get('location') or '').lower()
        full_text = f"{title} {company} {description} {location}"

        # Reject jobs with insufficient data (empty JDs waste AI tokens)
        if not title.strip() or not description.strip() or len(description) < 50:
            return FilterResult(
                job_id=job_id, passed=False,
                reject_reason="insufficient_data",
                filter_version="2.0",
                matched_rules=json.dumps({"title_len": len(title), "desc_len": len(description)})
            )

        hard_rules = self.filter_config.get('hard_reject_rules', {})

        # Sort rules by priority
        sorted_rules = sorted(
            hard_rules.items(),
            key=lambda x: x[1].get('priority', 99)
        )

        for rule_name, rule_config in sorted_rules:
            if not rule_config.get('enabled', True):
                continue

            rule_type = rule_config.get('type', 'regex')

            # --- Dutch language word count detection ---
            if rule_type == 'word_count':
                indicators = rule_config.get('dutch_indicators', [])
                threshold = rule_config.get('threshold', 8)
                # Count how many Dutch indicator words appear in the text
                # Use word boundary matching to avoid partial matches
                count = 0
                for word in indicators:
                    # Use _keyword_boundary_pattern for consistency with rest of pipeline
                    if re.search(_keyword_boundary_pattern(word), full_text):
                        count += 1
                if count >= threshold:
                    return FilterResult(
                        job_id=job_id, passed=False,
                        reject_reason=rule_name,
                        filter_version="2.0",
                        matched_rules=json.dumps({"dutch_word_count": count})
                    )

            # --- Title-based role check ---
            elif rule_type == 'title_check':
                # Check exceptions first (against title, not body)
                exceptions = rule_config.get('exceptions', [])
                if any(
                    re.search(_keyword_boundary_pattern(exc.lower().strip()), title)
                    for exc in exceptions if exc.strip()
                ):
                    continue

                # Check reject patterns (blacklist has priority)
                reject_patterns = rule_config.get('title_reject_patterns', [])
                rejected = False
                for pattern in reject_patterns:
                    try:
                        if re.search(pattern, title, re.IGNORECASE):
                            return FilterResult(
                                job_id=job_id, passed=False,
                                reject_reason=rule_name,
                                filter_version="2.0",
                                matched_rules=json.dumps({"rejected_pattern": pattern})
                            )
                    except re.error:
                        continue

                # Then check whitelist - title must contain at least one target keyword
                must_contain = rule_config.get('title_must_contain_one_of', [])
                if must_contain:
                    found = any(
                        re.search(_keyword_boundary_pattern(kw.lower().strip()), title)
                        for kw in must_contain if kw.strip()
                    )
                    if not found:
                        return FilterResult(
                            job_id=job_id, passed=False,
                            reject_reason=rule_name,
                            filter_version="2.0",
                            matched_rules=json.dumps({"no_target_keyword_in_title": title})
                        )

            # --- Tech stack check (title + body) ---
            elif rule_type == 'tech_stack':
                exceptions = [e.lower().strip() for e in rule_config.get('exceptions', [])]

                # Skip if title contains an exception keyword (word-boundary match)
                title_has_exception = any(
                    re.search(_keyword_boundary_pattern(exc), title) for exc in exceptions if exc
                )

                if not title_has_exception:
                    # Check title patterns
                    title_patterns = rule_config.get('title_patterns', [])
                    for pattern in title_patterns:
                        try:
                            if re.search(pattern, title, re.IGNORECASE):
                                return FilterResult(
                                    job_id=job_id, passed=False,
                                    reject_reason=rule_name,
                                    filter_version="2.0",
                                    matched_rules=json.dumps({"title_pattern": pattern})
                                )
                        except re.error:
                            continue

                    # Check body irrelevant keyword count
                    body_keywords = rule_config.get('body_irrelevant_keywords', [])
                    body_threshold = rule_config.get('body_irrelevant_threshold', 5)
                    body_count = sum(1 for kw in body_keywords if re.search(_keyword_boundary_pattern(kw.lower()), description))
                    if body_count >= body_threshold:
                        return FilterResult(
                            job_id=job_id, passed=False,
                            reject_reason=rule_name,
                            filter_version="2.0",
                            matched_rules=json.dumps({"body_irrelevant_count": body_count})
                        )

            # --- Standard regex check ---
            elif rule_type == 'regex':
                patterns = rule_config.get('patterns', [])
                exceptions = rule_config.get('exceptions', [])

                # Check exceptions against title only (not full_text) to prevent
                # casual keyword mentions in JD body from bypassing experience filters
                if any(
                    re.search(_keyword_boundary_pattern(exc.lower().strip()), title)
                    for exc in exceptions if exc.strip()
                ):
                    continue

                for pattern in patterns:
                    try:
                        if re.search(pattern, full_text, re.IGNORECASE):
                            return FilterResult(
                                job_id=job_id, passed=False,
                                reject_reason=rule_name,
                                filter_version="2.0",
                                matched_rules=json.dumps({"pattern": pattern})
                            )
                    except re.error:
                        continue

        # 公司黑名单 (cached in __init__)
        for blacklisted in self.company_blacklist:
            if re.search(_keyword_boundary_pattern(blacklisted), company):
                return FilterResult(
                    job_id=job_id, passed=False,
                    reject_reason="company_blacklist",
                    filter_version="2.0"
                )

        # 标题黑名单 (cached in __init__) — reject intern/trainee/student titles
        for blacklisted in self.title_blacklist:
            if re.search(_keyword_boundary_pattern(blacklisted), title):
                return FilterResult(
                    job_id=job_id, passed=False,
                    reject_reason="title_blacklist",
                    filter_version="2.0",
                    matched_rules=json.dumps({"blocked_title_keyword": blacklisted})
                )

        return FilterResult(job_id=job_id, passed=True, filter_version="2.0")

    def score_jobs(self, limit: int = 500) -> int:
        """Score all unscored jobs"""
        unscored = self.db.get_unscored_jobs(limit=limit)
        if not unscored:
            print("[Score] No jobs to score")
            return 0

        print(f"\n[Score] Scoring {len(unscored)} jobs...")
        scored = 0
        with self.db.batch_mode():
            for job in unscored:
                try:
                    result = self._calculate_score(job)
                    self.db.save_score(result)
                    scored += 1
                    apply_now_threshold = self.score_config.get('thresholds', {}).get('apply_now', 7.0)
                    if result.score >= apply_now_threshold:
                        print(f"  * [{result.score:.1f}] {job['title'][:40]} @ {job['company'][:20]}")
                except Exception as e:
                    print(f"  x Score error for {job.get('id', '?')}: {e}")
                    continue

        print(f"[Score] Done: {scored}/{len(unscored)} jobs scored")
        return scored

    def _calculate_score(self, job: Dict) -> ScoreResult:
        """计算职位评分 v2.0

        算法:
        1. 基础分 3.0
        2. 标题关键词匹配 (高权重，按类别只取一次)
        3. 正文关键词匹配 (按类别，有上限)
        4. 目标公司加分 (分层)
        5. 非核心技术惩罚
        6. 限制到 0-10 范围
        """
        job_id = job['id']
        title = (job.get('title') or '').lower()
        description = (job.get('description') or '').lower()
        company = (job.get('company') or '').lower()
        location = (job.get('location') or '').lower()
        full_text = f"{title} {company} {description} {location}"

        base_score = self.score_config.get('base_score', {}).get('starting_score', 3.0)
        score = base_score
        score_breakdown = {}
        matched_keywords = []

        # Penalize very short descriptions (keeps empty-JD jobs below AI threshold)
        short_jd = self.score_config.get('body_scoring', {}).get('short_jd', {})
        short_jd_threshold = short_jd.get('threshold', 100)
        short_jd_penalty = short_jd.get('penalty', -2.0)
        if len(description) < short_jd_threshold:
            score += short_jd_penalty
            score_breakdown["short_jd_penalty"] = short_jd_penalty

        # === Title scoring ===
        title_config = self.score_config.get('title_scoring', {})

        # Positive title categories (only match once per category)
        for category, cat_config in title_config.items():
            if category == 'negative_title':
                continue
            if not isinstance(cat_config, dict) or 'keywords' not in cat_config:
                continue
            keywords = cat_config.get('keywords', [])
            weight = cat_config.get('weight', 0)
            for kw in keywords:
                if re.search(_keyword_boundary_pattern(kw.lower()), title):
                    score += weight
                    score_breakdown[f"title_{category}"] = weight
                    matched_keywords.append(f"title:{kw}")
                    break  # Only count once per category

        # Negative title keywords
        negative_title = title_config.get('negative_title', {})
        for neg_name, neg_config in negative_title.items():
            if not isinstance(neg_config, dict):
                continue
            keywords = neg_config.get('keywords', [])
            weight = neg_config.get('weight', 0)
            for kw in keywords:
                if re.search(_keyword_boundary_pattern(kw.lower()), title):
                    score += weight
                    score_breakdown[f"title_neg_{neg_name}"] = weight
                    matched_keywords.append(f"title_neg:{kw}")
                    break  # Only count once per sub-category

        # === Body scoring (capped per category) ===
        body_config = self.score_config.get('body_scoring', {})
        for category, cat_config in body_config.items():
            if not isinstance(cat_config, dict):
                continue

            # Handle simple keyword list categories (python, ml_frameworks, etc.)
            keywords = cat_config.get('keywords', [])
            weight = cat_config.get('weight', 0)
            max_total = cat_config.get('max_total', None)

            if keywords:
                cat_score = 0
                for kw in keywords:
                    if re.search(_keyword_boundary_pattern(kw.lower()), description):
                        cat_score += weight
                        matched_keywords.append(kw)

                # Apply cap
                if max_total is not None:
                    if max_total >= 0:
                        cat_score = min(cat_score, max_total)
                    else:
                        cat_score = max(cat_score, max_total)

                if cat_score != 0:
                    score += cat_score
                    score_breakdown[f"body_{category}"] = cat_score
            else:
                # Handle inline key-value categories (high_experience)
                cat_score = 0
                _SKIP_KEYS = {'max_total', 'keywords', 'weight', 'description'}
                for kw, kw_config in cat_config.items():
                    if kw in _SKIP_KEYS:
                        continue
                    if isinstance(kw_config, dict) and 'weight' in kw_config:
                        if re.search(_keyword_boundary_pattern(kw.lower()), description):
                            cat_score += kw_config['weight']
                            matched_keywords.append(kw)

                # Apply cap for inline categories too
                inline_max = cat_config.get('max_total', None)
                if inline_max is not None:
                    if inline_max >= 0:
                        cat_score = min(cat_score, inline_max)
                    else:
                        cat_score = max(cat_score, inline_max)

                if cat_score != 0:
                    score += cat_score
                    score_breakdown[f"body_{category}"] = cat_score

        # === Non-core tech penalty ===
        penalty_config = self.score_config.get('non_core_tech_penalty', {})
        if penalty_config:
            non_core_kws = penalty_config.get('non_core_keywords', [])
            core_kws = penalty_config.get('core_keywords', [])
            threshold = penalty_config.get('threshold', 3)
            min_core = penalty_config.get('min_core_keywords', 2)
            penalty = penalty_config.get('penalty', -2.0)

            non_core_count = sum(1 for kw in non_core_kws if re.search(_keyword_boundary_pattern(kw.lower()), full_text))
            core_count = sum(1 for kw in core_kws if re.search(_keyword_boundary_pattern(kw.lower()), full_text))

            if non_core_count >= threshold and core_count < min_core:
                score += penalty
                score_breakdown["non_core_penalty"] = penalty
                matched_keywords.append(f"non_core_dominance({non_core_count}nc/{core_count}c)")

        # === Target company bonus ===
        target_companies = self.score_config.get('target_companies', {})
        for tier, companies in [('tier_1', target_companies.get('tier_1', [])),
                                 ('tier_2', target_companies.get('tier_2', [])),
                                 ('tier_3', target_companies.get('tier_3', []))]:
            for target in companies:
                if re.search(_keyword_boundary_pattern(target.lower()), company):
                    bonus = target_companies.get('bonus_scores', {}).get(tier, 0)
                    score += bonus
                    score_breakdown[f"company_{tier}"] = bonus
                    matched_keywords.append(f"company:{target}")
                    break
            else:
                continue
            break  # Only match one tier

        # === Clamp score ===
        score = max(0.0, min(10.0, score))

        # === Determine recommendation ===
        thresholds = self.score_config.get('thresholds', {})
        apply_now_th = thresholds.get('apply_now', 7.0)
        apply_th = thresholds.get('apply', 5.5)
        maybe_th = thresholds.get('maybe', 4.0)

        if not (maybe_th <= apply_th <= apply_now_th):
            raise ValueError(f"Invalid threshold order in scoring.yaml: maybe={maybe_th}, apply={apply_th}, apply_now={apply_now_th}")

        if score >= apply_now_th:
            recommendation = "APPLY_NOW"
        elif score >= apply_th:
            recommendation = "APPLY"
        elif score >= maybe_th:
            recommendation = "MAYBE"
        else:
            recommendation = "SKIP"

        return ScoreResult(
            job_id=job_id, score=round(score, 1), model="rule_based_v2",
            score_breakdown=json.dumps(score_breakdown),
            matched_keywords=json.dumps(matched_keywords),
            recommendation=recommendation
        )

    def show_stats(self):
        """Show statistics"""
        stats = self.db.get_funnel_stats()
        print("\n=== Funnel Stats ===")
        print(f"Total scraped:    {stats.get('total_scraped', 0)}")
        print(f"Passed filter:    {stats.get('passed_filter', 0)}")
        print(f"High score (>=5.5): {stats.get('scored_high', 0)}")
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
            print(f"{i:2}. [{job.get('score', 0):.1f}] {job['title'][:50]} @ {job['company'][:25]}")
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

            score_color = '#2e7d32' if score >= 7.0 else '#e65100' if score >= 6.0 else '#555'
            rows_html.append(f"""<tr>
  <td><input type="checkbox"></td>
  <td><span style="color:{score_color};font-weight:bold">{score:.1f}</span> {escape(rec)}</td>
  <td>{company}</td>
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

    def ai_analyze_jobs(self, min_rule_score: float = None, limit: int = None,
                        model: str = None) -> int:
        """AI 分析通过预筛选的职位"""
        try:
            from src.ai_analyzer import AIAnalyzer
        except ImportError:
            # Try alternative import path
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "ai_analyzer", PROJECT_ROOT / "src" / "ai_analyzer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find ai_analyzer.py at {PROJECT_ROOT / 'src' / 'ai_analyzer.py'}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            AIAnalyzer = module.AIAnalyzer

        analyzer = AIAnalyzer(model_override=model)
        return analyzer.analyze_batch(min_rule_score=min_rule_score, limit=limit)

    def generate_resumes(self, min_ai_score: float = None, limit: int = None) -> int:
        """为高分职位生成简历"""
        try:
            from src.resume_renderer import ResumeRenderer
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "resume_renderer", PROJECT_ROOT / "src" / "resume_renderer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find resume_renderer.py at {PROJECT_ROOT / 'src' / 'resume_renderer.py'}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            ResumeRenderer = module.ResumeRenderer

        renderer = ResumeRenderer()
        return renderer.render_batch(min_ai_score=min_ai_score, limit=limit)

    def generate_cover_letter(self, job_id: str, custom_requirements: str = None,
                              force: bool = False):
        """Generate + render cover letter for a single job"""
        try:
            from src.cover_letter_generator import CoverLetterGenerator
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_generator", PROJECT_ROOT / "src" / "cover_letter_generator.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_generator.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterGenerator = module.CoverLetterGenerator

        try:
            from src.cover_letter_renderer import CoverLetterRenderer
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_renderer", PROJECT_ROOT / "src" / "cover_letter_renderer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_renderer.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterRenderer = module.CoverLetterRenderer

        generator = CoverLetterGenerator()
        result = generator.generate(job_id, custom_requirements=custom_requirements, force=force)
        if result:
            renderer = CoverLetterRenderer()
            renderer.render(job_id)

    def generate_cover_letters_batch(self, min_ai_score: float = None, limit: int = 50):
        """Batch generate + render cover letters"""
        try:
            from src.cover_letter_generator import CoverLetterGenerator
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_generator", PROJECT_ROOT / "src" / "cover_letter_generator.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_generator.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterGenerator = module.CoverLetterGenerator

        try:
            from src.cover_letter_renderer import CoverLetterRenderer
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_renderer", PROJECT_ROOT / "src" / "cover_letter_renderer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_renderer.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterRenderer = module.CoverLetterRenderer

        generator = CoverLetterGenerator()
        generated = generator.generate_batch(min_ai_score=min_ai_score, limit=limit)

        if generated > 0:
            renderer = CoverLetterRenderer()
            renderer.render_batch(min_ai_score=min_ai_score, limit=limit)

    def cmd_prepare(self, min_ai_score: float = None, limit: int = None):
        """One-command: generate all materials + launch checklist server."""
        from src.checklist_server import generate_checklist, start_server
        from src.resume_renderer import ResumeRenderer
        from src.cover_letter_generator import CoverLetterGenerator
        from src.cover_letter_renderer import CoverLetterRenderer

        threshold = min_ai_score or self.config.get('thresholds', {}).get(
            'ai_score_generate_resume', 5.0)
        limit = limit or 50

        # Step 1: Sync from Turso
        print("Syncing database...")
        try:
            self.db.sync()
        except Exception as e:
            print(f"Warning: Turso sync failed ({e}), using local data")

        # Step 2: Generate resumes for jobs that need them
        renderer = ResumeRenderer()
        jobs = self.db.get_analyzed_jobs_for_resume(
            min_ai_score=threshold, limit=limit)

        results = {"success": [], "failed": [], "cl_failed": []}

        if jobs:
            print(f"\nGenerating materials for {len(jobs)} jobs...")
            cl_gen = CoverLetterGenerator()
            cl_renderer = CoverLetterRenderer()

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

                # Cover letter (non-blocking: resume is saved even if CL fails)
                try:
                    cl_spec = cl_gen.generate(job_id)
                    if cl_spec:
                        cl_renderer.render(job_id)
                except Exception as e:
                    results["cl_failed"].append((label, str(e)))
        else:
            print("No new jobs need resume generation.")

        # Step 3: Collect ALL ready-to-apply jobs (new + existing)
        all_ready = self.db.get_ready_to_apply()

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
        if results["cl_failed"]:
            print(f"  CL warnings: {len(results['cl_failed'])}")
            for label, err in results["cl_failed"]:
                print(f"    ! {label}: {err[:80]}")
        print(f"  Total ready: {len(all_ready)}")
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

        # Process applied jobs
        for job_id, info in applied.items():
            self.db.update_application_status(job_id, "applied", applied_at=now)
            src = ready_dir / info["submit_dir"]
            if src.exists() and src.is_dir():
                dest = applied_dir / src.name
                shutil.move(str(src), str(dest))

        # Process skipped jobs
        for job_id, info in skipped.items():
            self.db.update_application_status(job_id, "skipped")
            src = ready_dir / info["submit_dir"]
            if src.exists() and src.is_dir():
                shutil.rmtree(src)

        # Clean up state files
        state_path.unlink(missing_ok=True)
        checklist_path = ready_dir / "apply_checklist.html"
        if checklist_path.exists():
            checklist_path.unlink()

        # Sync to Turso
        print("Syncing to cloud...")
        try:
            self.db.sync()
        except Exception as e:
            print(f"Warning: Turso sync failed ({e}), changes saved locally")

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

    def analyze_single_job(self, job_id: str, model: str = None):
        """分析单个职位"""
        try:
            from src.ai_analyzer import AIAnalyzer
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "ai_analyzer", PROJECT_ROOT / "src" / "ai_analyzer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find ai_analyzer.py at {PROJECT_ROOT / 'src' / 'ai_analyzer.py'}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            AIAnalyzer = module.AIAnalyzer

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
        scored = self.score_jobs(limit=limit)

        print("\n" + "-" * 70)
        print("Stage 1 Complete: imported {}, filtered {}/{}, scored {}".format(
            imported, passed, passed+rejected, scored))
        print("-" * 70)

        # AI Analysis (optional - only if high-score jobs exist)
        ai_thresholds = self.ai_config.get('thresholds', {})
        rule_score_threshold = ai_thresholds.get('rule_score_for_ai', 3.0)
        ai_score_threshold = ai_thresholds.get('ai_score_generate_resume', 5.0)

        jobs_for_ai = self.db.get_jobs_needing_analysis(min_rule_score=rule_score_threshold, limit=limit)
        if jobs_for_ai:
            print(f"\nFound {len(jobs_for_ai)} jobs ready for AI analysis")
            try:
                user_input = input("Run AI analysis? (y/n, default: n): ").strip().lower()
            except EOFError:
                user_input = 'n'
            if user_input == 'y':
                analyzed = self.ai_analyze_jobs(min_rule_score=rule_score_threshold, limit=limit)
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


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='Job Pipeline')
    parser.add_argument('--analyze', help='Analyze jobs from JSON file (legacy)')
    parser.add_argument('--process', action='store_true', help='Run full pipeline (DB)')
    parser.add_argument('--import-only', action='store_true', help='Only import inbox')
    parser.add_argument('--filter', action='store_true', help='Only run filter')
    parser.add_argument('--score', action='store_true', help='Only run scoring')
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

    args = parser.parse_args()

    # 重新处理所有职位 (清除旧结果)
    if args.reprocess:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        from src.db.job_db import JobDatabase as _JDB
        db = _JDB()
        print("[Reprocess] Clearing old filter, score, and analysis results...")
        filter_count = db.clear_filter_results()
        score_count = db.clear_scores()
        analysis_count = db.clear_rejected_analyses()
        print(f"  Cleared {filter_count} filter results, {score_count} score results, {analysis_count} rejected analyses")

        pipeline = JobPipeline()
        # Reprocess all jobs (ignore --limit to avoid data loss from partial reprocessing)
        pipeline.filter_jobs()
        pipeline.score_jobs()
        pipeline.show_stats()
        return

    # 新版数据库流水线
    if args.process or args.import_only or args.filter or args.score or args.ready \
       or args.ai_analyze or args.generate or args.analyze_job \
       or args.stats or args.mark_applied or args.mark_all_applied \
       or args.update_status or args.tracker \
       or args.cover_letter or args.cover_letters \
       or args.prepare or args.finalize:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        pipeline = JobPipeline()
        if args.prepare:
            pipeline.cmd_prepare(min_ai_score=args.min_score, limit=args.limit)
        elif args.finalize:
            pipeline.cmd_finalize()
        elif args.process:
            pipeline.process_all(limit=args.limit)
        elif args.import_only:
            pipeline.import_inbox()
        elif args.filter:
            pipeline.filter_jobs(limit=args.limit)
        elif args.score:
            pipeline.score_jobs(limit=args.limit)
        elif args.ready:
            pipeline.show_ready()
        elif args.ai_analyze:
            pipeline.ai_analyze_jobs(min_rule_score=args.min_score, limit=args.limit,
                                     model=args.model)
        elif args.generate:
            pipeline.generate_resumes(min_ai_score=args.min_score, limit=args.limit)
            pipeline.generate_cover_letters_batch(min_ai_score=args.min_score, limit=args.limit)
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
            db = JobDatabase()
            job_id = args.mark_applied
            db.update_application_status(job_id, "applied", applied_at=datetime.now().isoformat())
            # Archive the ready_to_send folder
            resume = db.get_resume(job_id)
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
            db = JobDatabase()
            ready = db.get_ready_to_apply()
            if not ready:
                print("[Mark All] No ready-to-apply jobs to mark")
            else:
                now = datetime.now().isoformat()
                archived = 0
                for job in ready:
                    job_id = job['id']
                    db.update_application_status(job_id, "applied", applied_at=now)
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
            db = JobDatabase()
            job_id, status = args.update_status
            valid = {'rejected', 'interview', 'offer'}
            if status not in valid:
                print(f"Invalid status '{status}'. Must be one of: {', '.join(sorted(valid))}")
                sys.exit(1)
            kwargs = {}
            if status == 'rejected':
                kwargs['response_at'] = datetime.now().isoformat()
            elif status == 'interview':
                kwargs['interview_at'] = datetime.now().isoformat()
            elif status == 'offer':
                kwargs['response_at'] = datetime.now().isoformat()
            db.update_application_status(job_id, status, **kwargs)
            job = db.get_job(job_id)
            name = f"{job['title'][:40]} @ {job['company']}" if job else job_id
            print(f"[Status] {name} -> {status}")
        elif args.tracker:
            db = JobDatabase()
            tracker = db.get_application_tracker()
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
        return

    # 旧版 JSON 分析 (已废弃)
    if args.analyze:
        print("[DEPRECATED] --analyze is removed in v2.0. Use --ai-analyze instead.")
        sys.exit(1)

    # Help message
    print("Job Pipeline v2.0 - Commands:")
    print()
    print("  Basic:")
    print("  --process          Run full pipeline (import/filter/score)")
    print("  --import-only      Only import from inbox")
    print("  --filter           Only run hard filter")
    print("  --score            Only run rule-based scoring")
    print("  --ready            Show ready-to-apply jobs")
    print("  --stats            Show funnel stats")
    print("  --reprocess        Clear and reprocess all jobs")
    print("  --mark-applied ID  Mark job as applied")
    print("  --mark-all-applied Mark ALL ready jobs as applied + archive")
    print("  --update-status ID STATUS  Update status (rejected/interview/offer)")
    print("  --tracker          Show application tracker")
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
    print("  Options:")
    print("  --min-score N      Minimum score threshold")
    print("  --limit N          Max jobs to process (default: no limit)")
    print()
    print("  Legacy:")
    print("  --analyze FILE     Analyze JSON file")


if __name__ == "__main__":
    main()
