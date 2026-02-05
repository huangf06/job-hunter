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
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import yaml

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

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


class JobAnalyzer:
    """职位匹配度分析器 (Legacy - 兼容旧版 JSON 分析)"""

    # 目标关键词和权重 (与 scoring.yaml v2.0 保持一致)
    POSITIVE_KEYWORDS = {
        # 标题级别关键词 (高权重)
        "machine learning": 2.5,
        "ml engineer": 2.5,
        "ai engineer": 2.5,
        "data scientist": 2.5,
        "deep learning": 2.5,
        "data engineer": 2.0,
        "quant": 2.5,
        "quantitative": 2.5,
        # 正文级别关键词
        "python": 1.0,
        "pytorch": 1.0,
        "tensorflow": 1.0,
        "nlp": 1.0,
        "llm": 1.0,
        "sql": 0.5,
        "spark": 1.0,
        "pyspark": 1.0,
        "trading": 1.0,
        "junior": 1.5,
        "entry level": 1.5,
        "graduate": 1.0,
        "visa sponsor": 2.0,
        "relocation": 1.0,
        "sponsorship": 2.0,
        "kmv": 1.5,
    }

    NEGATIVE_KEYWORDS = {
        "senior manager": -3.0,
        "director": -3.0,
        "head of": -3.0,
        "vp ": -3.0,
        "vice president": -3.0,
        "10+ years": -2.0,
        "8+ years": -1.5,
        "dutch required": -5.0,
        "dutch native": -5.0,
        "german required": -3.0,
        "french required": -3.0,
        "principal": -2.0,
        "staff engineer": -1.5,
        "5+ years": -0.5,
        "6+ years": -1.0,
        "7+ years": -1.0,
        "senior": -0.5,
        "lead": -1.5,
    }

    TARGET_COMPANIES = {
        # Tier 1
        "picnic": 2.0, "adyen": 2.0, "booking.com": 2.0,
        "optiver": 2.0, "imc": 2.0, "flow traders": 2.0, "deepdesk": 2.0,
        # Tier 2
        "abn amro": 1.5, "ing": 1.5, "rabobank": 1.5, "asml": 1.5, "philips": 1.5,
        # Tier 3
        "tomtom": 1.0, "coolblue": 1.0, "bol.com": 1.0, "shell": 1.0, "kpn": 1.0,
    }

    @classmethod
    def analyze(cls, job: Dict) -> Dict:
        """分析单个职位的匹配度"""
        score = 3.0  # 基础分 (v2.0: 从 5.0 降到 3.0)
        reasons = {"positive": [], "negative": []}

        # 合并文本
        title = job.get('title', '').lower()
        text = f"{title} {job.get('company', '')} {job.get('description', '')}".lower()

        # 正面因素
        for keyword, points in cls.POSITIVE_KEYWORDS.items():
            if keyword in text:
                score += points
                reasons["positive"].append(f"{keyword} (+{points})")

        # 负面因素
        for keyword, points in cls.NEGATIVE_KEYWORDS.items():
            if keyword in text:
                score += points
                reasons["negative"].append(f"{keyword} ({points})")

        # 目标公司加分
        company = job.get('company', '').lower()
        for target, bonus in cls.TARGET_COMPANIES.items():
            if target in company:
                score += bonus
                reasons["positive"].append(f"target company: {target} (+{bonus})")
                break

        # 限制分数范围
        score = max(0, min(10, score))

        # 推荐等级 (v2.0 阈值)
        if score >= 7.0:
            recommendation = "APPLY_NOW"
        elif score >= 5.5:
            recommendation = "APPLY"
        elif score >= 4.0:
            recommendation = "MAYBE"
        else:
            recommendation = "SKIP"

        return {
            "score": round(score, 1),
            "recommendation": recommendation,
            "reasons": reasons
        }
    
    @classmethod
    def analyze_file(cls, filepath: Path) -> List[Dict]:
        """分析整个文件的所有职位"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        jobs = data.get('jobs', [])
        results = []
        
        for job in jobs:
            analysis = cls.analyze(job)
            job_with_analysis = {**job, **analysis}
            results.append(job_with_analysis)
        
        # 按分数排序
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results


class ResumeTailor:
    """简历定制器"""
    
    def __init__(self):
        self.base_template = self._load_template()
    
    def _load_template(self) -> str:
        """加载 HTML 模板"""
        template_path = TEMPLATES_DIR / "resume_base.html"
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    def tailor_for_job(self, job: Dict) -> str:
        """根据职位定制简历"""
        html = self.base_template
        
        # 根据职位类型调整摘要
        title = job.get('title', '').lower()
        company = job.get('company', '')
        
        if 'machine learning' in title or 'ml engineer' in title:
            summary = f"Machine Learning Engineer with expertise in developing and deploying ML models at scale. M.Sc. in AI from VU Amsterdam with thesis on Uncertainty Quantification in Deep RL. Experienced in PyTorch, TensorFlow, and production ML systems. Eager to contribute to {company}'s ML initiatives."
        elif 'data engineer' in title:
            summary = f"Data Engineer with strong background in building scalable data pipelines, ETL processes, and ML infrastructure. M.Sc. in AI from VU Amsterdam. Experienced in Python, SQL, PySpark, and cloud platforms. Seeking to leverage data engineering skills at {company}."
        elif 'quant' in title:
            summary = f"Quantitative Researcher with hands-on experience in factor research, backtesting, and live trading systems. Background in multi-factor alpha models and futures strategies with proven track record (14.6% annual return). M.Sc. in AI from VU Amsterdam. Seeking quantitative role at {company}."
        elif 'data scientist' in title:
            summary = f"Data Scientist with expertise in machine learning, statistical modeling, and data-driven decision making. M.Sc. in AI from VU Amsterdam. Experienced in building end-to-end ML pipelines, credit risk modeling, and quantitative analysis. Excited to bring analytical skills to {company}."
        else:
            summary = f"Data professional with expertise in machine learning, data engineering, and quantitative analysis. M.Sc. in AI from VU Amsterdam. Experienced in Python, SQL, and ML frameworks. Seeking to contribute to {company}'s data initiatives."
        
        # 替换摘要
        import re
        html = re.sub(
            r'(<div class="tailored-summary"[^>]*>)(.*?)(</div>)',
            f'\\1{summary}\\3',
            html,
            flags=re.DOTALL
        )
        
        return html
    
    def save_tailored_html(self, job: Dict, output_path: Path = None) -> Path:
        """保存定制后的 HTML"""
        if output_path is None:
            safe_company = re.sub(r'[^\w\-]', '_', job.get('company', 'unknown').lower())[:20]
            safe_title = re.sub(r'[^\w\-]', '_', job.get('title', 'job').lower())[:20]
            output_path = OUTPUT_DIR / f"{safe_company}_{safe_title}.html"
        
        html = self.tailor_for_job(job)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return output_path


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

        print(f"[Pipeline] Database: {self.db.db_path}")

    def _load_config(self, config_name: str) -> dict:
        """加载配置文件"""
        config_path = CONFIG_DIR / config_name
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
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
        file_path.rename(dest)

    def filter_jobs(self) -> tuple:
        """Filter all unfiltered jobs"""
        unfiltered = self.db.get_unfiltered_jobs(limit=500)
        if not unfiltered:
            print("[Filter] No jobs to filter")
            return 0, 0

        print(f"\n[Filter] Filtering {len(unfiltered)} jobs...")
        passed_count, rejected_count = 0, 0

        for job in unfiltered:
            result = self._apply_filter(job)
            self.db.save_filter_result(result)
            if result.passed:
                passed_count += 1
            else:
                rejected_count += 1

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
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        company = job.get('company', '').lower()
        location = job.get('location', '').lower()
        full_text = f"{title} {company} {description} {location}"

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
                    # Use regex word boundary for accurate matching
                    if re.search(r'\b' + re.escape(word) + r'\b', full_text):
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
                # First check reject patterns (blacklist has priority)
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
                    found = any(kw.lower() in title for kw in must_contain)
                    if not found:
                        return FilterResult(
                            job_id=job_id, passed=False,
                            reject_reason=rule_name,
                            filter_version="2.0",
                            matched_rules=json.dumps({"no_target_keyword_in_title": title})
                        )

            # --- Tech stack check (title + body) ---
            elif rule_type == 'tech_stack':
                exceptions = [e.lower() for e in rule_config.get('exceptions', [])]

                # Skip if title contains an exception keyword (e.g., "data", "ml")
                title_has_exception = any(exc in title for exc in exceptions)

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
                    body_count = sum(1 for kw in body_keywords if kw.lower() in description)
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

                # Check exceptions first
                if any(exc.lower() in full_text for exc in exceptions):
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

        # 公司黑名单
        search_profiles = self._load_config("search_profiles.yaml")
        company_blacklist = [c.lower() for c in search_profiles.get('company_blacklist', [])]
        for blacklisted in company_blacklist:
            if blacklisted in company:
                return FilterResult(
                    job_id=job_id, passed=False,
                    reject_reason="company_blacklist",
                    filter_version="2.0"
                )

        return FilterResult(job_id=job_id, passed=True, filter_version="2.0")

    def score_jobs(self) -> int:
        """Score all unscored jobs"""
        unscored = self.db.get_unscored_jobs(limit=500)
        if not unscored:
            print("[Score] No jobs to score")
            return 0

        print(f"\n[Score] Scoring {len(unscored)} jobs...")
        for job in unscored:
            result = self._calculate_score(job)
            self.db.save_score(result)
            if result.score >= 7.0:
                print(f"  * [{result.score:.1f}] {job['title'][:40]} @ {job['company'][:20]}")

        print(f"[Score] Done: {len(unscored)} jobs scored")
        return len(unscored)

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
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        company = job.get('company', '').lower()
        full_text = f"{title} {company} {description}"

        base_score = self.score_config.get('base_score', {}).get('starting_score', 3.0)
        score = base_score
        score_breakdown = {}
        matched_keywords = []

        # === Title scoring ===
        title_config = self.score_config.get('title_scoring', {})

        # Positive title categories (only match once per category)
        for category in ['core_ml_ai', 'data_engineering', 'quant']:
            cat_config = title_config.get(category, {})
            keywords = cat_config.get('keywords', [])
            weight = cat_config.get('weight', 0)
            for kw in keywords:
                if kw.lower() in title:
                    score += weight
                    score_breakdown[f"title_{category}"] = weight
                    matched_keywords.append(f"title:{kw}")
                    break  # Only count once per category

        # Negative title keywords
        negative_title = title_config.get('negative_title', {})
        for neg_name, neg_config in negative_title.items():
            keywords = neg_config.get('keywords', [])
            weight = neg_config.get('weight', 0)
            for kw in keywords:
                if kw.lower() in title:
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
                    if kw.lower() in full_text:
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
                for kw, kw_config in cat_config.items():
                    if isinstance(kw_config, dict) and 'weight' in kw_config:
                        if kw.lower() in full_text:
                            score += kw_config['weight']
                            score_breakdown[f"body_{category}_{kw}"] = kw_config['weight']
                            matched_keywords.append(kw)

        # === Non-core tech penalty ===
        penalty_config = self.score_config.get('non_core_tech_penalty', {})
        if penalty_config:
            non_core_kws = penalty_config.get('non_core_keywords', [])
            core_kws = penalty_config.get('core_keywords', [])
            threshold = penalty_config.get('threshold', 3)
            min_core = penalty_config.get('min_core_keywords', 2)
            penalty = penalty_config.get('penalty', -2.0)

            non_core_count = sum(1 for kw in non_core_kws if kw.lower() in full_text)
            core_count = sum(1 for kw in core_kws if kw.lower() in full_text)

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
                if target.lower() in company:
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
        if score >= thresholds.get('apply_now', 7.0):
            recommendation = "APPLY_NOW"
        elif score >= thresholds.get('apply', 5.5):
            recommendation = "APPLY"
        elif score >= thresholds.get('maybe', 4.0):
            recommendation = "MAYBE"
        else:
            recommendation = "SKIP"

        return ScoreResult(
            job_id=job_id, score=round(score, 1), model="rule_based_v2",
            score_breakdown=json.dumps(score_breakdown),
            matched_keywords=json.dumps(matched_keywords),
            recommendation=recommendation
        )

    def process_all(self):
        """Run full processing pipeline"""
        print("=" * 70)
        print("Job Hunter Pipeline")
        print("=" * 70)

        imported = self.import_inbox()
        passed, rejected = self.filter_jobs()
        scored = self.score_jobs()

        print("\n" + "=" * 70)
        print(f"Done: imported {imported}, filtered {passed}/{passed+rejected}, scored {scored}")
        print("=" * 70)

        ready = self.db.get_ready_to_apply()
        if ready:
            print(f"\nReady to apply ({len(ready)}):")
            for job in ready[:10]:
                print(f"  [{job['score']:.1f}] {job['title'][:40]} @ {job['company'][:20]}")

    def show_stats(self):
        """Show statistics"""
        stats = self.db.get_funnel_stats()
        print("\n=== Funnel Stats ===")
        print(f"Total scraped:    {stats.get('total_scraped', 0)}")
        print(f"Passed filter:    {stats.get('passed_filter', 0)}")
        print(f"High score (>=6): {stats.get('scored_high', 0)}")
        print(f"Resume generated: {stats.get('resume_generated', 0)}")
        print(f"Applied:          {stats.get('applied', 0)}")

        print("\n=== Filter Reject Reasons ===")
        for stat in self.db.get_filter_stats():
            print(f"  {stat['reject_reason']}: {stat['count']} ({stat['percentage']}%)")

    def show_ready(self):
        """Show jobs ready to apply"""
        ready = self.db.get_ready_to_apply()
        if not ready:
            print("No jobs ready to apply")
            return
        print(f"\nReady to apply ({len(ready)}):")
        for i, job in enumerate(ready, 1):
            print(f"{i:2}. [{job['score']:.1f}] {job['title'][:45]} @ {job['company'][:25]}")
            print(f"    ID: {job['id']}")


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
    parser.add_argument('--reprocess', action='store_true',
                        help='Clear old filter/score results and reprocess all jobs with new rules')

    args = parser.parse_args()

    # 重新处理所有职位 (清除旧结果)
    if args.reprocess:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        from src.db.job_db import JobDatabase
        db = JobDatabase()
        print("[Reprocess] Clearing old filter and score results...")
        filter_count = db.clear_filter_results()
        score_count = db.clear_scores()
        print(f"  Cleared {filter_count} filter results, {score_count} score results")

        pipeline = JobPipeline()
        pipeline.filter_jobs()
        pipeline.score_jobs()
        pipeline.show_stats()
        return

    # 新版数据库流水线
    if args.process or args.import_only or args.filter or args.score or args.ready:
        if not DB_AVAILABLE:
            print("错误: 数据库模块不可用")
            sys.exit(1)

        pipeline = JobPipeline()
        if args.process:
            pipeline.process_all()
        elif args.import_only:
            pipeline.import_inbox()
        elif args.filter:
            pipeline.filter_jobs()
        elif args.score:
            pipeline.score_jobs()
        elif args.ready:
            pipeline.show_ready()
        return

    # 旧版 JSON 分析 (兼容)
    if args.analyze:
        filepath = DATA_DIR / args.analyze
        if not filepath.exists():
            print(f"File not found: {filepath}")
            sys.exit(1)

        print(f"Analyzing jobs from {filepath}...")
        jobs = JobAnalyzer.analyze_file(filepath)

        tracker = JobTracker()
        added = 0
        for job in jobs:
            if tracker.add_job(job, {"score": job.get('score'), "recommendation": job.get('recommendation')}):
                added += 1

        print(f"Added {added} new jobs to tracker")
        print_analysis_report(jobs)
        return

    if args.stats:
        if DB_AVAILABLE:
            pipeline = JobPipeline()
            pipeline.show_stats()
        else:
            tracker = JobTracker()
            stats = tracker.get_stats()
            print("\n=== TRACKER STATS ===")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        return

    if args.mark_applied:
        if DB_AVAILABLE:
            db = JobDatabase()
            db.update_application_status(args.mark_applied, "applied", applied_at=datetime.now().isoformat())
            print(f"已标记为申请: {args.mark_applied}")
        else:
            tracker = JobTracker()
            tracker.mark_applied(args.mark_applied)
        return

    # 帮助信息
    print("Job Pipeline - 命令:")
    print("  --process          执行完整流水线 (数据库)")
    print("  --import-only      只导入 inbox")
    print("  --filter           只执行筛选")
    print("  --score            只执行评分")
    print("  --ready            显示待申请职位")
    print("  --stats            显示统计信息")
    print("  --reprocess        清除旧结果，用新规则重新处理所有职位")
    print("  --mark-applied ID  标记已申请")
    print("  --analyze FILE     分析 JSON 文件 (旧版)")


if __name__ == "__main__":
    main()
