"""
Job Hunter 数据库模块
====================

SQLite 数据库操作，统一管理职位数据的存储和查询。

功能：
- 职位存储和去重
- 筛选结果记录
- AI评分记录
- 简历生成记录
- 申请状态跟踪
- 反馈和分析
"""

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "data" / "jobs.db"


@dataclass
class Job:
    """职位数据"""
    id: str
    source: str
    url: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    posted_date: str = ""
    scraped_at: str = ""
    search_profile: str = ""
    search_query: str = ""
    raw_data: str = ""


@dataclass
class FilterResult:
    """筛选结果"""
    job_id: str
    passed: bool
    filter_version: str = "1.0"
    reject_reason: str = ""
    matched_rules: str = ""  # JSON


@dataclass
class ScoreResult:
    """评分结果"""
    job_id: str
    score: float
    model: str = "rule_based"
    score_breakdown: str = ""  # JSON
    matched_keywords: str = ""  # JSON
    analysis: str = ""
    recommendation: str = ""  # APPLY_NOW, APPLY, MAYBE, SKIP


@dataclass
class Resume:
    """简历记录"""
    job_id: str
    role_type: str
    template_version: str = "1.0"
    html_path: str = ""
    pdf_path: str = ""


@dataclass
class Application:
    """申请状态"""
    job_id: str
    status: str = "pending"  # pending, applied, rejected, interview, offer
    applied_at: str = ""
    response_at: str = ""
    interview_at: str = ""
    outcome: str = ""
    notes: str = ""


@dataclass
class AnalysisResult:
    """AI 分析结果 (评分 + 简历定制)"""
    job_id: str
    ai_score: float = 0.0
    skill_match: float = 0.0
    experience_fit: float = 0.0
    growth_potential: float = 0.0
    recommendation: str = ""
    reasoning: str = ""
    tailored_resume: str = ""  # JSON
    model: str = ""
    tokens_used: int = 0


class JobDatabase:
    """职位数据库操作类"""

    # 数据库 Schema
    SCHEMA = """
    -- 职位主表
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        source_id TEXT,  -- reserved, not currently populated
        url TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
        location TEXT,
        description TEXT,
        posted_date TEXT,
        scraped_at TEXT NOT NULL,
        search_profile TEXT,
        search_query TEXT,
        raw_data TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );

    -- 筛选结果表
    CREATE TABLE IF NOT EXISTS filter_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(id),
        passed BOOLEAN NOT NULL,
        filter_version TEXT,
        reject_reason TEXT,
        matched_rules TEXT,
        processed_at TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(job_id, filter_version)
    );

    -- AI评分表
    CREATE TABLE IF NOT EXISTS ai_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(id),
        score REAL NOT NULL,
        model TEXT,
        score_breakdown TEXT,
        matched_keywords TEXT,
        analysis TEXT,
        recommendation TEXT,
        scored_at TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(job_id, model)
    );

    -- 简历生成表
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(id),
        role_type TEXT,
        template_version TEXT,
        html_path TEXT,
        pdf_path TEXT,
        generated_at TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(job_id, role_type)
    );

    -- 申请状态表
    CREATE TABLE IF NOT EXISTS applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(id),
        status TEXT NOT NULL DEFAULT 'pending',
        applied_at TEXT,
        response_at TEXT,
        interview_at TEXT,
        outcome TEXT,
        notes TEXT,
        updated_at TEXT DEFAULT (datetime('now', 'localtime')),
        UNIQUE(job_id)
    );

    -- 反馈记录表 (UNUSED — reserved for future application outcome tracking)
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(id),
        feedback_type TEXT NOT NULL,
        days_to_response INTEGER,
        rejection_stage TEXT,
        rejection_reason TEXT,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );

    -- 配置快照表 (UNUSED — reserved for future config versioning)
    CREATE TABLE IF NOT EXISTS config_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        config_type TEXT NOT NULL,
        config_data TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );

    -- AI 分析表 (整合评分 + 简历定制)
    CREATE TABLE IF NOT EXISTS job_analysis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL UNIQUE REFERENCES jobs(id),

        -- AI 评分
        ai_score REAL,
        skill_match REAL,
        experience_fit REAL,
        growth_potential REAL,
        recommendation TEXT,
        reasoning TEXT,

        -- 定制简历 (JSON)
        tailored_resume TEXT,

        -- 元数据
        model TEXT,
        tokens_used INTEGER,
        analyzed_at TEXT DEFAULT (datetime('now', 'localtime'))
    );

    -- 索引
    CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
    CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
    CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at);
    CREATE INDEX IF NOT EXISTS idx_jobs_search_profile ON jobs(search_profile);
    CREATE INDEX IF NOT EXISTS idx_filter_passed ON filter_results(passed);
    CREATE INDEX IF NOT EXISTS idx_scores_score ON ai_scores(score);
    CREATE INDEX IF NOT EXISTS idx_scores_recommendation ON ai_scores(recommendation);
    CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
    CREATE INDEX IF NOT EXISTS idx_job_analysis_score ON job_analysis(ai_score);
    CREATE INDEX IF NOT EXISTS idx_job_analysis_recommendation ON job_analysis(recommendation);
    """

    # 视图定义
    VIEWS = """
    -- 待处理职位视图
    CREATE VIEW IF NOT EXISTS v_pending_jobs AS
    SELECT
        j.*,
        f.passed as filter_passed,
        f.reject_reason,
        s.score as rule_score,
        s.recommendation as rule_recommendation,
        an.ai_score,
        an.recommendation as ai_recommendation,
        r.pdf_path as resume_path,
        a.status as application_status
    FROM jobs j
    LEFT JOIN filter_results f ON j.id = f.job_id
    LEFT JOIN ai_scores s ON j.id = s.job_id
    LEFT JOIN job_analysis an ON j.id = an.job_id
    LEFT JOIN resumes r ON j.id = r.job_id
    LEFT JOIN applications a ON j.id = a.job_id
    WHERE a.id IS NULL OR a.status = 'pending';

    -- 高分职位视图 (基于 AI 分析)
    CREATE VIEW IF NOT EXISTS v_high_score_jobs AS
    SELECT
        j.id, j.title, j.company, j.location, j.url,
        an.ai_score as score, an.recommendation,
        r.pdf_path as resume_path,
        a.status as application_status
    FROM jobs j
    JOIN job_analysis an ON j.id = an.job_id AND an.ai_score >= 7.0 AND an.tailored_resume != '{}'  -- SYNC: matches ai_config.yaml thresholds.ai_score_apply_now
    LEFT JOIN resumes r ON j.id = r.job_id
    LEFT JOIN applications a ON j.id = a.job_id
    ORDER BY an.ai_score DESC;

    -- 待申请职位视图 (已生成简历但未申请)
    CREATE VIEW IF NOT EXISTS v_ready_to_apply AS
    SELECT
        j.id, j.title, j.company, j.location, j.url,
        an.ai_score as score, an.recommendation,
        r.pdf_path as resume_path
    FROM jobs j
    JOIN job_analysis an ON j.id = an.job_id
    JOIN resumes r ON j.id = r.job_id AND r.pdf_path IS NOT NULL AND r.pdf_path != ''
    LEFT JOIN applications a ON j.id = a.job_id
    WHERE a.id IS NULL
    ORDER BY an.ai_score DESC;

    -- 申请漏斗统计视图
    CREATE VIEW IF NOT EXISTS v_funnel_stats AS
    SELECT
        COUNT(DISTINCT j.id) as total_scraped,
        COUNT(DISTINCT CASE WHEN f.passed = 1 THEN j.id END) as passed_filter,
        COUNT(DISTINCT CASE WHEN s.score >= 5.5 THEN j.id END) as scored_high,  -- SYNC: matches scoring.yaml thresholds.apply
        COUNT(DISTINCT CASE WHEN an.id IS NOT NULL THEN j.id END) as ai_analyzed,
        COUNT(DISTINCT CASE WHEN an.ai_score >= 5.0 THEN j.id END) as ai_scored_high,  -- SYNC: matches ai_config.yaml thresholds.ai_score_generate_resume
        COUNT(DISTINCT CASE WHEN r.id IS NOT NULL THEN j.id END) as resume_generated,
        COUNT(DISTINCT CASE WHEN a.status = 'applied' THEN j.id END) as applied,
        COUNT(DISTINCT CASE WHEN a.status = 'interview' THEN j.id END) as interview,
        COUNT(DISTINCT CASE WHEN a.status = 'offer' THEN j.id END) as offer
    FROM jobs j
    LEFT JOIN filter_results f ON j.id = f.job_id
    LEFT JOIN ai_scores s ON j.id = s.job_id
    LEFT JOIN job_analysis an ON j.id = an.job_id
    LEFT JOIN resumes r ON j.id = r.job_id
    LEFT JOIN applications a ON j.id = a.job_id;
    """

    def __init__(self, db_path: Path = None):
        """初始化数据库"""
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库结构"""
        with self._get_conn() as conn:
            # Use individual execute() calls instead of executescript() so that
            # _get_conn's commit/rollback transaction control works correctly.
            # (executescript() implicitly commits, defeating rollback on error.)
            # WARNING: This split assumes no semicolons appear inside SQL string
            # literals or comments. Keep SCHEMA clean of embedded semicolons.
            for statement in self.SCHEMA.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)
            # Drop and recreate views to ensure they're up-to-date
            conn.execute("DROP VIEW IF EXISTS v_pending_jobs")
            conn.execute("DROP VIEW IF EXISTS v_high_score_jobs")
            conn.execute("DROP VIEW IF EXISTS v_ready_to_apply")
            conn.execute("DROP VIEW IF EXISTS v_funnel_stats")
            for statement in self.VIEWS.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

    @contextmanager
    def _get_conn(self) -> Generator[sqlite3.Connection, None, None]:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.execute("PRAGMA foreign_keys=ON")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def execute(self, sql: str, params: tuple = ()) -> list:
        """执行 SQL 并返回结果行（用于 ad-hoc 查询和数据修改）"""
        with self._get_conn() as conn:
            cur = conn.execute(sql, params)
            if cur.description:
                return [dict(row) for row in cur.fetchall()]
            return []

    # ==================== Job 操作 ====================

    @staticmethod
    def generate_job_id(url: str) -> str:
        """根据 URL 生成唯一 ID"""
        if not url:
            raise ValueError("Cannot generate job_id: URL is empty")
        # 清理 URL，移除查询参数和片段
        clean_url = url.split('?')[0].split('#')[0].rstrip('/')
        return hashlib.md5(clean_url.encode()).hexdigest()[:12]

    def job_exists(self, url: str) -> bool:
        """检查职位是否已存在"""
        job_id = self.generate_job_id(url)
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
            return cursor.fetchone() is not None

    def filter_urls_needing_jd(self, urls: List[str]) -> List[str]:
        """批量过滤，返回需要抓取JD的URL列表

        返回：不存在于数据库 或 存在但description为空 的URL
        """
        if not urls:
            return []

        # Filter out empty URLs to prevent ValueError in generate_job_id
        urls = [u for u in urls if u]
        if not urls:
            return []

        # 生成 job_id -> url 的映射
        url_to_id = {url: self.generate_job_id(url) for url in urls}
        job_ids = list(url_to_id.values())

        # 批量查询已有且JD完整的职位 (chunk to avoid SQLite variable limit)
        complete_ids = set()
        CHUNK_SIZE = 900
        with self._get_conn() as conn:
            for i in range(0, len(job_ids), CHUNK_SIZE):
                chunk = job_ids[i:i+CHUNK_SIZE]
                placeholders = ','.join(['?'] * len(chunk))
                cursor = conn.execute(
                    f"""SELECT id FROM jobs
                        WHERE id IN ({placeholders})
                        AND description IS NOT NULL
                        AND description != ''""",
                    chunk
                )
                complete_ids.update(row[0] for row in cursor.fetchall())

        # 返回不在 complete_ids 中的 URL
        return [url for url, job_id in url_to_id.items() if job_id not in complete_ids]

    def insert_job(self, job_data: Dict) -> tuple:
        """插入新职位"""
        url = job_data.get("url", "")
        job_id = self.generate_job_id(url)

        title = job_data.get("title", "")
        company = job_data.get("company", "")
        if not title.strip() or not company.strip():
            print(f"  [WARN] Skipping job with empty title or company: {url[:60]}")
            return job_id, False

        job = Job(
            id=job_id,
            source=job_data.get("source", "unknown"),
            url=url,
            title=title,
            company=company,
            location=job_data.get("location", ""),
            description=job_data.get("description", ""),
            posted_date=job_data.get("posted_date", ""),
            scraped_at=job_data.get("scraped_at", datetime.now().isoformat()),
            search_profile=job_data.get("search_profile", ""),
            search_query=job_data.get("search_query", ""),
            raw_data=json.dumps(job_data, ensure_ascii=False)
        )

        with self._get_conn() as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO jobs
                (id, source, url, title, company, location, description,
                 posted_date, scraped_at, search_profile, search_query, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (job.id, job.source, job.url, job.title, job.company,
                  job.location, job.description, job.posted_date, job.scraped_at,
                  job.search_profile, job.search_query, job.raw_data))
            was_inserted = cursor.rowcount > 0

        return job_id, was_inserted

    def get_job(self, job_id: str) -> Optional[Dict]:
        """获取职位详情"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_jobs_by_profile(self, profile: str, limit: int = 100) -> List[Dict]:
        """按搜索 profile 获取职位"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT * FROM jobs
                WHERE search_profile = ?
                ORDER BY scraped_at DESC
                LIMIT ?
            """, (profile, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Filter 操作 ====================

    def save_filter_result(self, result: FilterResult):
        """保存筛选结果"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO filter_results
                (job_id, passed, filter_version, reject_reason, matched_rules, processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (result.job_id, result.passed, result.filter_version,
                  result.reject_reason, result.matched_rules, datetime.now().isoformat()))

    def get_filter_result(self, job_id: str) -> Optional[Dict]:
        """获取筛选结果"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM filter_results WHERE job_id = ? ORDER BY processed_at DESC LIMIT 1",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_unfiltered_jobs(self, limit: int = 100) -> List[Dict]:
        """获取未筛选的职位"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.* FROM jobs j
                LEFT JOIN filter_results f ON j.id = f.job_id
                WHERE f.id IS NULL
                ORDER BY j.scraped_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Score 操作 ====================

    def save_score(self, result: ScoreResult):
        """保存评分结果"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO ai_scores
                (job_id, score, model, score_breakdown, matched_keywords, analysis, recommendation, scored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (result.job_id, result.score, result.model, result.score_breakdown,
                  result.matched_keywords, result.analysis, result.recommendation,
                  datetime.now().isoformat()))

    def get_score(self, job_id: str) -> Optional[Dict]:
        """获取评分结果"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM ai_scores WHERE job_id = ? ORDER BY scored_at DESC LIMIT 1",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_unscored_jobs(self, limit: int = 100) -> List[Dict]:
        """获取已通过筛选但未评分的职位"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.* FROM jobs j
                JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
                LEFT JOIN ai_scores s ON j.id = s.job_id
                WHERE s.id IS NULL
                ORDER BY j.scraped_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Resume 操作 ====================

    def save_resume(self, resume: Resume):
        """保存简历记录"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO resumes
                (job_id, role_type, template_version, html_path, pdf_path, generated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (resume.job_id, resume.role_type, resume.template_version,
                  resume.html_path, resume.pdf_path, datetime.now().isoformat()))

    def get_resume(self, job_id: str) -> Optional[Dict]:
        """获取简历记录"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM resumes WHERE job_id = ? ORDER BY generated_at DESC LIMIT 1",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== Application 操作 ====================

    # ==================== Analysis 操作 (AI 分析 + 简历定制) ====================

    def save_analysis(self, result: AnalysisResult):
        """保存 AI 分析结果"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO job_analysis
                (job_id, ai_score, skill_match, experience_fit, growth_potential,
                 recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (result.job_id, result.ai_score, result.skill_match,
                  result.experience_fit, result.growth_potential,
                  result.recommendation, result.reasoning,
                  result.tailored_resume, result.model, result.tokens_used,
                  datetime.now().isoformat()))

    def get_analysis(self, job_id: str) -> Optional[Dict]:
        """获取 AI 分析结果"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM job_analysis WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_jobs_needing_analysis(self, min_rule_score: float = 3.0, limit: int = 50) -> List[Dict]:
        """获取通过筛选、达到规则评分阈值、但未经 AI 分析的职位"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.*, s.score as rule_score, s.recommendation as rule_recommendation
                FROM jobs j
                JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
                JOIN ai_scores s ON j.id = s.job_id AND s.score >= ?
                LEFT JOIN job_analysis a ON j.id = a.job_id
                WHERE a.id IS NULL
                ORDER BY s.score DESC
                LIMIT ?
            """, (min_rule_score, limit))
            return [dict(row) for row in cursor.fetchall()]

    def get_analyzed_jobs_for_resume(self, min_ai_score: float = 5.0, limit: int = 50) -> List[Dict]:
        """获取 AI 评分达标但未生成简历的职位 (or PDF generation previously failed)"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.*, a.ai_score, a.recommendation as ai_recommendation,
                       a.tailored_resume, a.reasoning
                FROM jobs j
                JOIN job_analysis a ON j.id = a.job_id AND a.ai_score >= ?
                LEFT JOIN resumes r ON j.id = r.job_id
                WHERE (r.id IS NULL OR (r.pdf_path IS NULL OR r.pdf_path = ''))
                  AND a.tailored_resume IS NOT NULL
                  AND a.tailored_resume != '{}'
                ORDER BY a.ai_score DESC
                LIMIT ?
            """, (min_ai_score, limit))
            return [dict(row) for row in cursor.fetchall()]

    def clear_analyses(self, model: str = None) -> int:
        """清除 AI 分析结果"""
        with self._get_conn() as conn:
            if model:
                cursor = conn.execute(
                    "DELETE FROM job_analysis WHERE model = ?", (model,))
            else:
                cursor = conn.execute("DELETE FROM job_analysis")
            return cursor.rowcount

    # ==================== Application 操作 (original) ====================

    def save_application(self, app: Application):
        """保存申请状态"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO applications
                (job_id, status, applied_at, response_at, interview_at, outcome, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (app.job_id, app.status, app.applied_at, app.response_at,
                  app.interview_at, app.outcome, app.notes, datetime.now().isoformat()))

    def update_application_status(self, job_id: str, status: str, **kwargs):
        """更新申请状态"""
        VALID_STATUSES = {'pending', 'applied', 'rejected', 'interview', 'offer'}
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}', must be one of {sorted(VALID_STATUSES)}")
        ALLOWED_COLS = ('applied_at', 'response_at', 'interview_at', 'outcome', 'notes')
        with self._get_conn() as conn:
            # 先检查是否存在
            cursor = conn.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,))
            existing = cursor.fetchone()

            if existing:
                # 更新: iterate over known columns, not arbitrary kwargs
                set_clauses = ["status = ?", "updated_at = ?"]
                params = [status, datetime.now().isoformat()]

                for col in ALLOWED_COLS:
                    if col in kwargs:
                        set_clauses.append(f"{col} = ?")
                        params.append(kwargs[col])

                params.append(job_id)
                sql = "UPDATE applications SET " + ", ".join(set_clauses) + " WHERE job_id = ?"
                conn.execute(sql, params)
            else:
                # 插入 (inline to avoid nested _get_conn)
                conn.execute("""
                    INSERT OR REPLACE INTO applications
                    (job_id, status, applied_at, response_at, interview_at, outcome, notes, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (job_id, status, kwargs.get('applied_at', ''),
                      kwargs.get('response_at', ''), kwargs.get('interview_at', ''),
                      kwargs.get('outcome', ''), kwargs.get('notes', ''),
                      datetime.now().isoformat()))

    def get_application(self, job_id: str) -> Optional[Dict]:
        """获取申请状态"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM applications WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_ready_to_apply(self) -> List[Dict]:
        """获取待申请的职位"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM v_ready_to_apply")
            return [dict(row) for row in cursor.fetchall()]

    # ==================== 统计和分析 ====================

    def get_funnel_stats(self) -> Dict:
        """获取漏斗统计"""
        with self._get_conn() as conn:
            cursor = conn.execute("SELECT * FROM v_funnel_stats")
            row = cursor.fetchone()
            return dict(row) if row else {}

    def get_filter_stats(self) -> List[Dict]:
        """获取筛选统计"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT
                    reject_reason,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / MAX((SELECT COUNT(*) FROM filter_results WHERE passed = 0), 1), 1) as percentage
                FROM filter_results
                WHERE passed = 0 AND reject_reason IS NOT NULL AND reject_reason != ''
                GROUP BY reject_reason
                ORDER BY count DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_company_stats(self) -> List[Dict]:
        """获取公司统计"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT
                    j.company,
                    COUNT(DISTINCT j.id) as total_jobs,
                    COUNT(DISTINCT CASE WHEN f.passed = 1 THEN j.id END) as passed_filter,
                    COUNT(DISTINCT CASE WHEN a.status = 'applied' THEN j.id END) as applied,
                    COUNT(DISTINCT CASE WHEN a.status IN ('interview', 'offer') THEN j.id END) as positive_response,
                    AVG(s.score) as avg_rule_score,
                    AVG(an.ai_score) as avg_ai_score
                FROM jobs j
                LEFT JOIN filter_results f ON j.id = f.job_id
                LEFT JOIN ai_scores s ON j.id = s.job_id
                LEFT JOIN job_analysis an ON j.id = an.job_id
                LEFT JOIN applications a ON j.id = a.job_id
                GROUP BY j.company
                HAVING total_jobs >= 2
                ORDER BY total_jobs DESC
                LIMIT 20
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_daily_stats(self, days: int = 7) -> List[Dict]:
        """获取每日统计"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT
                    DATE(j.scraped_at) as date,
                    COUNT(DISTINCT j.id) as scraped,
                    COUNT(DISTINCT CASE WHEN f.passed = 1 THEN j.id END) as passed,
                    COUNT(DISTINCT CASE WHEN s.score >= 5.5 THEN j.id END) as high_score,  -- SYNC: matches scoring.yaml thresholds.apply
                    COUNT(DISTINCT CASE WHEN r.id IS NOT NULL THEN j.id END) as resume_generated
                FROM jobs j
                LEFT JOIN filter_results f ON j.id = f.job_id
                LEFT JOIN ai_scores s ON j.id = s.job_id
                LEFT JOIN resumes r ON j.id = r.job_id
                WHERE j.scraped_at >= DATE('now', 'localtime', ?)
                GROUP BY DATE(j.scraped_at)
                ORDER BY date DESC
            """, (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]

    def get_daily_token_usage(self) -> int:
        """Get total tokens used today across all AI analyses."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(tokens_used), 0) as today_tokens
                FROM job_analysis
                WHERE DATE(analyzed_at) = DATE('now', 'localtime')
            """).fetchone()
            return row['today_tokens'] if row else 0

    def clear_filter_results(self, filter_version: str = None) -> int:
        """清除筛选结果，以便重新处理

        Args:
            filter_version: 如果指定，只清除该版本的结果；否则清除全部

        Returns:
            删除的记录数
        """
        with self._get_conn() as conn:
            if filter_version:
                cursor = conn.execute(
                    "DELETE FROM filter_results WHERE filter_version = ?",
                    (filter_version,)
                )
            else:
                cursor = conn.execute("DELETE FROM filter_results")
            return cursor.rowcount

    def clear_scores(self, model: str = None) -> int:
        """清除评分结果，以便重新处理

        Args:
            model: 如果指定，只清除该模型的结果；否则清除全部

        Returns:
            删除的记录数
        """
        with self._get_conn() as conn:
            if model:
                cursor = conn.execute(
                    "DELETE FROM ai_scores WHERE model = ?",
                    (model,)
                )
            else:
                cursor = conn.execute("DELETE FROM ai_scores")
            return cursor.rowcount

    # ==================== 批量操作 ====================

    def import_from_json(self, json_path: Path, profile: str = "", query: str = "") -> int:
        """从 JSON 文件导入职位 (single connection for entire batch)"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if isinstance(data, list):
            jobs = data
            meta_profile = ""
            meta_search = ""
        else:
            jobs = data.get("jobs", [])
            meta_profile = data.get("profile", "")
            meta_search = data.get("search", "")

        imported = 0
        with self._get_conn() as conn:
            for job_data in jobs:
                url = job_data.get("url", "")
                if not url:
                    continue
                title = job_data.get("title", "")
                company = job_data.get("company", "")
                if not title.strip() or not company.strip():
                    continue
                job_data["search_profile"] = profile or meta_profile
                job_data["search_query"] = query or meta_search
                try:
                    job_id = self.generate_job_id(url)
                    job = Job(
                        id=job_id,
                        source=job_data.get("source", "unknown"),
                        url=url,
                        title=job_data.get("title", ""),
                        company=job_data.get("company", ""),
                        location=job_data.get("location", ""),
                        description=job_data.get("description", ""),
                        posted_date=job_data.get("posted_date", ""),
                        scraped_at=job_data.get("scraped_at", datetime.now().isoformat()),
                        search_profile=job_data.get("search_profile", ""),
                        search_query=job_data.get("search_query", ""),
                        raw_data=json.dumps(job_data, ensure_ascii=False)
                    )
                    cursor = conn.execute("""
                        INSERT OR IGNORE INTO jobs
                        (id, source, url, title, company, location, description,
                         posted_date, scraped_at, search_profile, search_query, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (job.id, job.source, job.url, job.title, job.company,
                          job.location, job.description, job.posted_date, job.scraped_at,
                          job.search_profile, job.search_query, job.raw_data))
                    if cursor.rowcount > 0:
                        imported += 1
                except Exception as e:
                    import sqlite3 as _sqlite3
                    severity = "WARN" if isinstance(e, _sqlite3.IntegrityError) else "ERROR"
                    print(f"  [{severity}] Failed to import job {url[:60]}: {e}")

        return imported

    def export_to_json(self, output_path: Path, **filters) -> int:
        """导出职位到 JSON"""
        with self._get_conn() as conn:
            query = "SELECT * FROM jobs WHERE 1=1"
            params = []

            if filters.get("profile"):
                query += " AND search_profile = ?"
                params.append(filters["profile"])

            if filters.get("min_score"):
                query += " AND id IN (SELECT job_id FROM ai_scores WHERE score >= ?)"
                params.append(filters["min_score"])

            cursor = conn.execute(query, params)
            jobs = [dict(row) for row in cursor.fetchall()]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({"jobs": jobs, "exported_at": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)

        return len(jobs)


# ==================== CLI 接口 ====================

def main():
    """命令行接口"""
    import argparse

    parser = argparse.ArgumentParser(description="Job Hunter 数据库管理")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # init 命令
    subparsers.add_parser("init", help="初始化数据库")

    # import 命令
    import_parser = subparsers.add_parser("import", help="导入 JSON 数据")
    import_parser.add_argument("file", type=Path, help="JSON 文件路径")
    import_parser.add_argument("--profile", default="", help="搜索 profile")

    # stats 命令
    subparsers.add_parser("stats", help="显示统计信息")

    # ready 命令
    subparsers.add_parser("ready", help="显示待申请职位")

    args = parser.parse_args()

    db = JobDatabase()

    if args.command == "init":
        print(f"数据库已初始化: {db.db_path}")

    elif args.command == "import":
        count = db.import_from_json(args.file, profile=args.profile)
        print(f"导入 {count} 个新职位")

    elif args.command == "stats":
        stats = db.get_funnel_stats()
        print("\n=== 漏斗统计 ===")
        print(f"总抓取: {stats.get('total_scraped', 0)}")
        print(f"通过筛选: {stats.get('passed_filter', 0)}")
        print(f"高分 (>=5.5): {stats.get('scored_high', 0)}")
        print(f"已生成简历: {stats.get('resume_generated', 0)}")
        print(f"已申请: {stats.get('applied', 0)}")
        print(f"面试: {stats.get('interview', 0)}")
        print(f"Offer: {stats.get('offer', 0)}")

        print("\n=== 筛选拒绝原因 ===")
        for stat in db.get_filter_stats():
            print(f"  {stat['reject_reason']}: {stat['count']} ({stat['percentage']}%)")

    elif args.command == "ready":
        jobs = db.get_ready_to_apply()
        print(f"\n=== 待申请职位 ({len(jobs)} 个) ===")
        for job in jobs[:20]:
            print(f"  [{job['score']:.1f}] {job['title'][:40]} @ {job['company'][:20]}")
            print(f"       {job['resume_path']}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
