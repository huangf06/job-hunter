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
import logging
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Any, Generator

import yaml

# Load .env if available (for local dev — CI uses env: blocks)
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env", override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path(__file__).parent.parent.parent / "data" / "jobs.db"
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"


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
    submit_dir: str = ""


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


@dataclass
class CoverLetter:
    """Cover letter 记录"""
    job_id: str
    spec_json: str = ""
    custom_requirements: str = ""
    standard_text: str = ""
    short_text: str = ""
    html_path: str = ""
    pdf_path: str = ""
    tokens_used: int = 0


class TursoHTTPClient:
    """Turso HTTP API v2 client using httpx.

    Replaces libsql embedded replica with a simple HTTP transport.
    Uses the Turso pipeline endpoint: POST {url}/v3/pipeline
    """

    def __init__(self, db_url: str, auth_token: str):
        import httpx
        # Convert libsql:// to https://
        self._base_url = db_url.replace('libsql://', 'https://')
        self._headers = {
            'Authorization': f'Bearer {auth_token}',
            'Content-Type': 'application/json',
        }
        self._client = httpx.Client(timeout=30.0)

    def execute(self, sql: str, params: tuple = ()) -> list:
        """Execute a single SQL statement, return list of dicts."""
        results = self.execute_batch([(sql, params)])
        return results[0] if results else []

    def execute_batch(self, statements: list) -> list:
        """Execute multiple statements in one HTTP call.

        Args:
            statements: list of (sql, params) tuples

        Returns:
            list of list-of-dicts, one per statement
        """
        requests = []
        for sql, params in statements:
            args = self._convert_params(params)
            stmt = {'sql': sql}
            if args:
                stmt['args'] = args
            requests.append({'type': 'execute', 'stmt': stmt})
        requests.append({'type': 'close'})

        url = f'{self._base_url}/v3/pipeline'
        resp = self._client.post(url, json={'requests': requests}, headers=self._headers)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get('results', []):
            if item.get('type') == 'ok':
                response = item.get('response', {})
                result = response.get('result', {})
                cols = [c['name'] for c in result.get('cols', [])]
                rows = []
                for row in result.get('rows', []):
                    values = [self._extract_value(cell) for cell in row]
                    rows.append(dict(zip(cols, values)))
                results.append(rows)
            elif item.get('type') == 'error':
                error = item.get('error', {})
                raise RuntimeError(f"Turso HTTP error: {error.get('message', 'unknown')}")
        return results

    @staticmethod
    def _convert_params(params):
        """Convert Python params to Turso HTTP API format."""
        if not params:
            return []
        args = []
        for p in params:
            if p is None:
                args.append({'type': 'null', 'value': None})
            elif isinstance(p, int):
                args.append({'type': 'integer', 'value': str(p)})
            elif isinstance(p, float):
                args.append({'type': 'float', 'value': p})
            elif isinstance(p, bytes):
                import base64
                args.append({'type': 'blob', 'base64': base64.b64encode(p).decode()})
            else:
                args.append({'type': 'text', 'value': str(p)})
        return args

    @staticmethod
    def _extract_value(cell):
        """Extract Python value from Turso HTTP API cell."""
        if cell is None or cell.get('type') == 'null':
            return None
        val = cell.get('value')
        cell_type = cell.get('type', '')
        if cell_type == 'integer':
            return int(val)
        if cell_type == 'float':
            return float(val)
        return val

    def close(self):
        self._client.close()


class _DualAccessRow(dict):
    """Row that supports both dict-style (row['col']) and index-style (row[0]) access."""

    def __init__(self, d: dict):
        super().__init__(d)
        self._values = list(d.values())

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._values[key]
        return super().__getitem__(key)

    def __iter__(self):
        return iter(self._values)

    def keys(self):
        return super().keys()


class _TursoCursor:
    """Minimal cursor adapter for TursoHTTPClient results."""

    def __init__(self, rows: list):
        self._rows = [_DualAccessRow(r) if isinstance(r, dict) else r for r in rows]
        self._iter = iter(self._rows)
        # Mimic sqlite3.Cursor.description for code that checks it
        if rows and isinstance(rows[0], dict):
            self.description = [(k,) for k in rows[0].keys()]
        else:
            self.description = None

    def fetchone(self):
        try:
            return next(self._iter)
        except StopIteration:
            return None

    def fetchall(self):
        return self._rows

    def __iter__(self):
        return iter(self._rows)


class _TursoConnAdapter:
    """Makes TursoHTTPClient quack like a sqlite3 connection.

    Each execute() call is a separate HTTP request (auto-commit).
    commit() and rollback() are no-ops.
    """

    def __init__(self, client: TursoHTTPClient):
        self._client = client

    def execute(self, sql: str, params=()):
        rows = self._client.execute(sql, tuple(params) if params else ())
        return _TursoCursor(rows)

    def executemany(self, sql, params_seq):
        for params in params_seq:
            self._client.execute(sql, tuple(params))
        return _TursoCursor([])

    def commit(self):
        pass  # auto-commit per statement

    def rollback(self):
        pass  # HTTP is stateless, no rollback


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
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 筛选结果表
    CREATE TABLE IF NOT EXISTS filter_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL REFERENCES jobs(id),
        passed BOOLEAN NOT NULL,
        filter_version TEXT,
        reject_reason TEXT,
        matched_rules TEXT,
        processed_at TEXT DEFAULT (datetime('now')),
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
        scored_at TEXT DEFAULT (datetime('now')),
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
        submit_dir TEXT,
        generated_at TEXT DEFAULT (datetime('now')),
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
        updated_at TEXT DEFAULT (datetime('now')),
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
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 配置快照表 (UNUSED — reserved for future config versioning)
    CREATE TABLE IF NOT EXISTS config_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id TEXT NOT NULL,
        config_type TEXT NOT NULL,
        config_data TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
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
        analyzed_at TEXT DEFAULT (datetime('now'))
    );

    -- Cover letter 表
    CREATE TABLE IF NOT EXISTS cover_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL UNIQUE REFERENCES jobs(id),
        spec_json TEXT,
        custom_requirements TEXT,
        standard_text TEXT,
        short_text TEXT,
        html_path TEXT,
        pdf_path TEXT,
        tokens_used INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- 爬取水位标记表 (增量爬取 High-Water Mark)
    CREATE TABLE IF NOT EXISTS scrape_watermarks (
        profile TEXT NOT NULL,
        query TEXT NOT NULL,
        hwm_url TEXT NOT NULL,
        last_scraped_at TEXT NOT NULL,
        jobs_found INTEGER DEFAULT 0,
        PRIMARY KEY (profile, query)
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
    CREATE INDEX IF NOT EXISTS idx_cover_letters_job ON cover_letters(job_id);
    """

    # 视图定义 (template — thresholds filled from config at init time)
    VIEWS_TEMPLATE = """
    -- 待处理职位视图
    CREATE VIEW IF NOT EXISTS v_pending_jobs AS
    SELECT
        j.*,
        f.passed as filter_passed,
        f.reject_reason,
        an.ai_score,
        an.recommendation as ai_recommendation,
        r.pdf_path as resume_path,
        a.status as application_status
    FROM jobs j
    LEFT JOIN filter_results f ON j.id = f.job_id
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
    JOIN job_analysis an ON j.id = an.job_id AND an.ai_score >= {ai_score_apply_now} AND an.tailored_resume != '{{}}'
    LEFT JOIN resumes r ON j.id = r.job_id
    LEFT JOIN applications a ON j.id = a.job_id
    ORDER BY an.ai_score DESC;

    -- 待申请职位视图 (已生成简历但未申请)
    CREATE VIEW IF NOT EXISTS v_ready_to_apply AS
    SELECT
        j.id, j.title, j.company, j.location, j.url,
        an.ai_score as score, an.recommendation,
        r.pdf_path as resume_path,
        r.submit_dir
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
        COUNT(DISTINCT CASE WHEN an.id IS NOT NULL THEN j.id END) as ai_analyzed,
        COUNT(DISTINCT CASE WHEN an.ai_score >= {ai_score_generate_resume} AND an.tailored_resume IS NOT NULL AND an.tailored_resume != '{{}}' THEN j.id END) as ai_scored_high,
        COUNT(DISTINCT CASE WHEN r.id IS NOT NULL THEN j.id END) as resume_generated,
        COUNT(DISTINCT CASE WHEN a.status = 'applied' THEN j.id END) as applied,
        COUNT(DISTINCT CASE WHEN a.status = 'rejected' THEN j.id END) as rejected,
        COUNT(DISTINCT CASE WHEN a.status = 'interview' THEN j.id END) as interview,
        COUNT(DISTINCT CASE WHEN a.status = 'offer' THEN j.id END) as offer
    FROM jobs j
    LEFT JOIN filter_results f ON j.id = f.job_id
    LEFT JOIN job_analysis an ON j.id = an.job_id
    LEFT JOIN resumes r ON j.id = r.job_id
    LEFT JOIN applications a ON j.id = a.job_id;
    """

    def __init__(self, db_path: Path = None):
        """初始化数据库

        Transport selection:
        - DB_TRANSPORT=http or TURSO_DATABASE_URL set: Turso HTTP API
        - DB_TRANSPORT=sqlite or no Turso env vars: local SQLite
        """
        self.db_path = db_path or DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        transport = os.getenv("DB_TRANSPORT", "").lower()
        turso_url = os.getenv("TURSO_DATABASE_URL")
        turso_token = os.getenv("TURSO_AUTH_TOKEN")

        # Determine transport: Turso HTTP or local SQLite
        self._turso_http = None
        if transport == "sqlite" or os.getenv("NO_TURSO"):
            pass  # force local SQLite
        elif transport == "http" or turso_url:
            if not turso_token:
                raise ValueError(
                    "TURSO_DATABASE_URL is set but TURSO_AUTH_TOKEN is missing. "
                    "Set the token or unset the URL to use local SQLite."
                )
            self._turso_http = TursoHTTPClient(turso_url, turso_token)
            logger.info("Using Turso HTTP transport: %s", turso_url)

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
            # Migrations must run before recreating views because newer view
            # definitions may reference columns added during migration.
            self._migrate(conn)
            # Drop and recreate views to ensure they're up-to-date
            conn.execute("DROP VIEW IF EXISTS v_pending_jobs")
            conn.execute("DROP VIEW IF EXISTS v_high_score_jobs")
            conn.execute("DROP VIEW IF EXISTS v_ready_to_apply")
            conn.execute("DROP VIEW IF EXISTS v_funnel_stats")
            views_sql = self._build_views_sql()
            for statement in views_sql.split(';'):
                statement = statement.strip()
                if statement:
                    conn.execute(statement)

    @staticmethod
    def _load_view_thresholds() -> Dict[str, float]:
        """Load thresholds from config files for DB views.

        Returns dict with keys: ai_score_apply_now, ai_score_generate_resume.
        Falls back to hardcoded defaults if config unavailable.
        """
        defaults = {
            'ai_score_apply_now': 7.0,
            'ai_score_generate_resume': 5.0,
        }
        try:
            ai_config_path = CONFIG_DIR / "ai_config.yaml"
            if ai_config_path.exists():
                with open(ai_config_path, 'r', encoding='utf-8') as f:
                    ai_cfg = yaml.safe_load(f) or {}
                thresholds = ai_cfg.get('thresholds', {})
                defaults['ai_score_apply_now'] = float(thresholds.get('ai_score_apply_now', defaults['ai_score_apply_now']))
                defaults['ai_score_generate_resume'] = float(thresholds.get('ai_score_generate_resume', defaults['ai_score_generate_resume']))
        except Exception:
            pass  # Use defaults on any config error
        return defaults

    def _build_views_sql(self) -> str:
        """Build views SQL with thresholds loaded from config."""
        thresholds = self._load_view_thresholds()
        return self.VIEWS_TEMPLATE.format(**thresholds)

    def _migrate(self, conn):
        """Add columns introduced after initial schema."""
        existing = {row[1] for row in conn.execute("PRAGMA table_info(resumes)").fetchall()}
        if 'submit_dir' not in existing:
            conn.execute("ALTER TABLE resumes ADD COLUMN submit_dir TEXT")

    @contextmanager
    def _get_conn(self, *, sync_before=True):
        """获取数据库连接 (Turso HTTP or local SQLite)

        For Turso HTTP: wraps a _TursoConnAdapter that translates
        execute()/commit() to HTTP calls.
        For local SQLite: standard sqlite3 connection.
        """
        if self._turso_http:
            yield _TursoConnAdapter(self._turso_http)
        else:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=5000")
                conn.execute("PRAGMA foreign_keys=ON")
                yield conn
                conn.commit()
            except BaseException as e:
                try:
                    conn.rollback()
                except Exception as rollback_err:
                    logger.warning("Rollback failed: %s", rollback_err)
                raise e
            finally:
                conn.close()

    @contextmanager
    def batch_mode(self):
        """Context manager for batch operations. No-op with HTTP transport."""
        yield

    def final_sync(self):
        """No-op — HTTP transport is always live."""
        pass

    def execute(self, sql: str, params: tuple = ()) -> list:
        """执行 SQL 并返回结果行（用于 ad-hoc 查询和数据修改）"""
        if self._turso_http:
            return self._turso_http.execute(sql, params)
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

    def find_existing_job_ids(self, urls: List[str]) -> set[str]:
        """Batch-check which scraped URLs already exist in jobs."""
        job_ids = [self.generate_job_id(url) for url in urls if url]
        if not job_ids:
            return set()

        existing_ids: set[str] = set()
        chunk_size = 900
        with self._get_conn() as conn:
            for i in range(0, len(job_ids), chunk_size):
                chunk = job_ids[i:i + chunk_size]
                placeholders = ",".join(["?"] * len(chunk))
                cursor = conn.execute(
                    f"SELECT id FROM jobs WHERE id IN ({placeholders})",
                    chunk,
                )
                existing_ids.update(row[0] for row in cursor.fetchall())
        return existing_ids

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
            raw_data=""  # Deprecated: no longer populated (duplicates description)
        )

        with self._get_conn(sync_before=False) as conn:
            cursor = conn.execute("""
                INSERT INTO jobs
                (id, source, url, title, company, location, description,
                 posted_date, scraped_at, search_profile, search_query, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    description = CASE
                        WHEN excluded.description != ''
                             AND length(excluded.description) > length(COALESCE(jobs.description, ''))
                        THEN excluded.description
                        ELSE jobs.description
                    END
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
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO filter_results
                (job_id, passed, filter_version, reject_reason, matched_rules, processed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (result.job_id, result.passed, result.filter_version,
                  result.reject_reason, result.matched_rules, datetime.now(timezone.utc).isoformat()))

    def get_filter_result(self, job_id: str) -> Optional[Dict]:
        """获取筛选结果"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM filter_results WHERE job_id = ? ORDER BY processed_at DESC LIMIT 1",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_unfiltered_jobs(self, limit: int = None) -> List[Dict]:
        """获取未筛选的职位"""
        with self._get_conn() as conn:
            query = """
                SELECT j.* FROM jobs j
                LEFT JOIN filter_results f ON j.id = f.job_id
                WHERE f.id IS NULL
                ORDER BY j.scraped_at DESC
            """
            params = []
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Score 操作 ====================

    def get_score(self, job_id: str) -> Optional[Dict]:
        """获取评分结果"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM ai_scores WHERE job_id = ? ORDER BY scored_at DESC LIMIT 1",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    # ==================== Resume 操作 ====================

    def save_resume(self, resume: Resume):
        """保存简历记录"""
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO resumes
                (job_id, role_type, template_version, html_path, pdf_path, submit_dir, generated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (resume.job_id, resume.role_type, resume.template_version,
                  resume.html_path, resume.pdf_path, resume.submit_dir,
                  datetime.now(timezone.utc).isoformat()))

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
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO job_analysis
                (job_id, ai_score, skill_match, experience_fit, growth_potential,
                 recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (result.job_id, result.ai_score, result.skill_match,
                  result.experience_fit, result.growth_potential,
                  result.recommendation, result.reasoning,
                  result.tailored_resume, result.model, result.tokens_used,
                  datetime.now(timezone.utc).isoformat()))

    def get_analysis(self, job_id: str) -> Optional[Dict]:
        """获取 AI 分析结果"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM job_analysis WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_analysis_resume(self, job_id: str, tailored_resume: str):
        """Update tailored_resume for an existing analysis (C2 writes to C1's row)."""
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                UPDATE job_analysis
                SET tailored_resume = ?
                WHERE job_id = ?
            """, (tailored_resume, job_id))

    def get_jobs_needing_tailor(self, min_score: float = 4.0, limit: int = None) -> List[Dict]:
        """Get jobs with C1 evaluation but no C2 tailored resume yet."""
        with self._get_conn() as conn:
            query = """
                SELECT j.*, a.ai_score, a.recommendation, a.reasoning
                FROM jobs j
                JOIN job_analysis a ON j.id = a.job_id
                LEFT JOIN applications app ON j.id = app.job_id
                WHERE a.ai_score >= ?
                  AND (a.tailored_resume IS NULL OR a.tailored_resume = '{}')
                  AND app.job_id IS NULL
                ORDER BY a.ai_score DESC
            """
            params = [min_score]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_jobs_needing_analysis(self, limit: int = None) -> List[Dict]:
        """Get jobs that passed filter but have no AI analysis yet (excludes applied)."""
        with self._get_conn() as conn:
            query = """
                SELECT j.*
                FROM jobs j
                JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
                LEFT JOIN job_analysis a ON j.id = a.job_id
                LEFT JOIN applications app ON j.id = app.job_id
                WHERE a.id IS NULL
                  AND app.job_id IS NULL
                ORDER BY j.created_at DESC
            """
            params = []
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_analyzed_jobs_for_resume(self, min_ai_score: float = 5.0, limit: int = None) -> List[Dict]:
        """获取 AI 评分达标但未生成简历的职位 (排除已投递; 含 PDF 生成失败重试)"""
        with self._get_conn() as conn:
            query = """
                SELECT j.*, a.ai_score, a.recommendation as ai_recommendation,
                       a.tailored_resume, a.reasoning
                FROM jobs j
                JOIN job_analysis a ON j.id = a.job_id AND a.ai_score >= ?
                LEFT JOIN resumes r ON j.id = r.job_id
                LEFT JOIN applications app ON j.id = app.job_id
                WHERE (r.id IS NULL OR (r.pdf_path IS NULL OR r.pdf_path = ''))
                  AND a.tailored_resume IS NOT NULL
                  AND a.tailored_resume != '{}'
                  AND app.job_id IS NULL
                ORDER BY a.ai_score DESC
            """
            params = [min_ai_score]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def clear_analyses(self, model: str = None) -> int:
        """清除 AI 分析结果"""
        with self._get_conn(sync_before=False) as conn:
            if model:
                cursor = conn.execute(
                    "DELETE FROM job_analysis WHERE model = ?", (model,))
            else:
                cursor = conn.execute("DELETE FROM job_analysis")
            return cursor.rowcount

    def clear_rejected_analyses(self) -> int:
        """清除被拒绝的 AI 分析结果 (tailored_resume = '{}')，允许重新分析"""
        with self._get_conn(sync_before=False) as conn:
            cursor = conn.execute(
                "DELETE FROM job_analysis WHERE tailored_resume = '{}' OR tailored_resume IS NULL"
            )
            return cursor.rowcount

    def clear_transient_failures(self) -> int:
        """清除可重试的瞬态失败 (parse failure / truncation / empty response)，保留正常低分拒绝"""
        with self._get_conn(sync_before=False) as conn:
            cursor = conn.execute("""
                DELETE FROM job_analysis
                WHERE tailored_resume = '{}'
                  AND (reasoning LIKE '[PARSE_FAIL]%'
                       OR reasoning LIKE 'Failed to parse AI response:%'
                       OR reasoning LIKE 'Response truncated%'
                       OR reasoning LIKE 'Empty API response%'
                       OR reasoning LIKE 'Claude Code CLI returned empty response%'
                       OR reasoning LIKE 'Analysis error:%')
            """)
            return cursor.rowcount

    # ==================== Cover Letter 操作 ====================

    def save_cover_letter(self, cl: CoverLetter):
        """保存 cover letter 记录"""
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cover_letters
                (job_id, spec_json, custom_requirements, standard_text, short_text,
                 html_path, pdf_path, tokens_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cl.job_id, cl.spec_json, cl.custom_requirements,
                  cl.standard_text, cl.short_text,
                  cl.html_path, cl.pdf_path, cl.tokens_used,
                  datetime.now(timezone.utc).isoformat()))

    def get_cover_letter(self, job_id: str) -> Optional[Dict]:
        """获取 cover letter 记录"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM cover_letters WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_jobs_needing_cover_letter(self, min_ai_score: float = 5.0, limit: int = None) -> List[Dict]:
        """获取有 AI 分析+简历但无 cover letter 的职位"""
        with self._get_conn() as conn:
            query = """
                SELECT j.*, a.ai_score, a.recommendation as ai_recommendation,
                       a.tailored_resume, a.reasoning
                FROM jobs j
                JOIN job_analysis a ON j.id = a.job_id AND a.ai_score >= ?
                JOIN resumes r ON j.id = r.job_id AND r.pdf_path IS NOT NULL AND r.pdf_path != ''
                LEFT JOIN cover_letters cl ON j.id = cl.job_id
                WHERE cl.id IS NULL
                  AND a.tailored_resume IS NOT NULL
                  AND a.tailored_resume != '{}'
                ORDER BY a.ai_score DESC
            """
            params = [min_ai_score]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    # ==================== Watermark 操作 (增量爬取 HWM) ====================

    def get_watermark(self, profile: str, query: str) -> Optional[str]:
        """Get the high-water mark URL for a profile+query."""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT hwm_url FROM scrape_watermarks WHERE profile = ? AND query = ?",
                (profile, query),
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def set_watermark(self, profile: str, query: str, hwm_url: str, jobs_found: int = 0):
        """Set/update the high-water mark for a profile+query."""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO scrape_watermarks (profile, query, hwm_url, last_scraped_at, jobs_found) "
                "VALUES (?, ?, ?, datetime('now'), ?) "
                "ON CONFLICT(profile, query) DO UPDATE SET "
                "hwm_url = excluded.hwm_url, last_scraped_at = excluded.last_scraped_at, "
                "jobs_found = excluded.jobs_found",
                (profile, query, hwm_url, jobs_found),
            )

    # ==================== Application 操作 (original) ====================

    def save_application(self, app: Application):
        """保存申请状态"""
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO applications
                (job_id, status, applied_at, response_at, interview_at, outcome, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (app.job_id, app.status, app.applied_at, app.response_at,
                  app.interview_at, app.outcome, app.notes, datetime.now(timezone.utc).isoformat()))

    def update_application_status(self, job_id: str, status: str, **kwargs):
        """更新申请状态"""
        VALID_STATUSES = {'pending', 'applied', 'skipped', 'rejected', 'interview', 'offer'}
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
                params = [status, datetime.now(timezone.utc).isoformat()]

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
                      datetime.now(timezone.utc).isoformat()))

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

    def get_application_tracker(self) -> Dict:
        """获取申请跟踪数据：按状态分组，含天数统计"""
        with self._get_conn() as conn:
            # Summary counts
            summary = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM applications
                GROUP BY status
                ORDER BY CASE status
                    WHEN 'applied' THEN 1
                    WHEN 'interview' THEN 2
                    WHEN 'offer' THEN 3
                    WHEN 'rejected' THEN 4
                    ELSE 5
                END
            """).fetchall()

            # Per-status job details
            rows = conn.execute("""
                SELECT
                    a.status, a.applied_at, a.response_at, a.interview_at,
                    j.title, j.company, j.url,
                    an.ai_score as score,
                    CAST(JULIANDAY('now') - JULIANDAY(a.applied_at) AS INTEGER) as days_since
                FROM applications a
                JOIN jobs j ON a.job_id = j.id
                LEFT JOIN job_analysis an ON a.job_id = an.job_id
                ORDER BY a.status, an.ai_score DESC
            """).fetchall()

            by_status = {}
            for row in rows:
                row_dict = dict(row)
                status = row_dict['status']
                if status not in by_status:
                    by_status[status] = []
                by_status[status].append(row_dict)

            return {
                'summary': [dict(r) for r in summary],
                'by_status': by_status
            }

    @staticmethod
    def _normalize_title(title: str) -> str:
        """标准化职位标题为排序词集合，忽略词序和标点"""
        import re
        words = re.findall(r'[a-z0-9+#]+', title.lower())
        return ' '.join(sorted(words))

    def find_applied_duplicates(self, job_id: str) -> List[Dict]:
        """查找同 company+title 已投递的职位 (repost 检测)

        使用词集合比较，忽略词序和标点，例如:
        "Data Engineer - Enterprise" == "Enterprise Data Engineer"
        """
        with self._get_conn() as conn:
            # 先获取目标职位的 company 和 title
            target = conn.execute(
                "SELECT title, company FROM jobs WHERE id = ?", (job_id,)
            ).fetchone()
            if not target:
                return []

            target_company = target['company'].lower()
            target_title_norm = self._normalize_title(target['title'])

            # 查找同公司已投递的职位，在 Python 层做标题词集合比较
            cursor = conn.execute("""
                SELECT j.id as job_id, j.title, j.company, a.applied_at
                FROM jobs j
                JOIN applications a ON j.id = a.job_id AND a.status = 'applied'
                WHERE LOWER(j.company) = ? AND j.id != ?
            """, (target_company, job_id))

            results = []
            for row in cursor.fetchall():
                if self._normalize_title(row['title']) == target_title_norm:
                    results.append(dict(row))
            return results

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

    def get_cold_job_ids(self, retention_days: int = 7) -> List[str]:
        """Get job IDs eligible for archival.

        Cold = scraped_at older than retention_days
               AND no application with status applied/interview/offer
               AND has a filter_result (not in active pipeline)
        """
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.id
                FROM jobs j
                JOIN filter_results f ON j.id = f.job_id
                WHERE j.scraped_at < datetime('now', ? || ' days')
                  AND NOT EXISTS (
                      SELECT 1 FROM applications a
                      WHERE a.job_id = j.id
                        AND a.status IN ('applied', 'interview', 'offer')
                  )
                ORDER BY j.scraped_at ASC
            """, (str(-retention_days),))
            return [row['id'] for row in cursor.fetchall()]

    def archive_cold_data(self, retention_days: int = 7) -> Dict:
        """Archive cold jobs to a local SQLite file and delete from live DB.

        Returns dict with keys: archived_count, archive_path, details (per-table counts).
        """
        cold_ids = self.get_cold_job_ids(retention_days=retention_days)
        if not cold_ids:
            return {"archived_count": 0, "archive_path": None, "details": {}}

        # Determine archive path: data/archive/full_history.db (single file)
        archive_dir = self.db_path.parent / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / "full_history.db"

        # Open archive DB and ensure schema exists
        archive_conn = sqlite3.connect(str(archive_path))
        archive_conn.execute("PRAGMA journal_mode=WAL")
        archive_conn.execute("PRAGMA foreign_keys=OFF")  # We control insert order
        for statement in self.SCHEMA.split(';'):
            statement = statement.strip()
            if statement:
                try:
                    archive_conn.execute(statement)
                except sqlite3.OperationalError:
                    pass  # Table/index already exists

        # Tables to archive (order: parent first, then dependents)
        # For each table, define (table_name, fk_column)
        # NOTE: processed_emails is intentionally excluded — it's email dedup
        # tracking (no job_id FK) and must be retained to prevent re-processing.
        related_tables = [
            ("filter_results", "job_id"),
            ("ai_scores", "job_id"),
            ("job_analysis", "job_id"),
            ("resumes", "job_id"),
            ("cover_letters", "job_id"),
            ("applications", "job_id"),
            ("feedback", "job_id"),
            ("emails", "job_id"),
        ]

        details = {}
        CHUNK_SIZE = 500

        with self._get_conn() as conn:
            # Process in chunks to stay within SQLite variable limit
            for start in range(0, len(cold_ids), CHUNK_SIZE):
                chunk = cold_ids[start:start + CHUNK_SIZE]
                placeholders = ','.join(['?'] * len(chunk))

                # 1. Copy jobs
                rows = conn.execute(
                    f"SELECT * FROM jobs WHERE id IN ({placeholders})", chunk
                ).fetchall()
                if rows:
                    cols = [d[0] for d in conn.execute("SELECT * FROM jobs LIMIT 0").description]
                    insert_sql = f"INSERT OR IGNORE INTO jobs ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
                    archive_conn.executemany(insert_sql, [tuple(r) for r in rows])
                    details["jobs"] = details.get("jobs", 0) + len(rows)

                # 2. Copy related tables
                for table, fk_col in related_tables:
                    try:
                        rows = conn.execute(
                            f"SELECT * FROM {table} WHERE {fk_col} IN ({placeholders})", chunk
                        ).fetchall()
                    except Exception:
                        continue  # Table might not exist in live DB
                    if rows:
                        cols = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
                        # Ensure table exists in archive (may not be in SCHEMA)
                        try:
                            archive_conn.execute(f"SELECT 1 FROM {table} LIMIT 0")
                        except sqlite3.OperationalError:
                            ddl = conn.execute(
                                "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
                                (table,)
                            ).fetchone()
                            if ddl and ddl['sql']:
                                archive_conn.execute(ddl['sql'])
                        insert_sql = f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({','.join(['?'] * len(cols))})"
                        archive_conn.executemany(insert_sql, [tuple(r) for r in rows])
                        details[table] = details.get(table, 0) + len(rows)

            archive_conn.commit()

            # Verify: count jobs in archive that we intended to write
            archived_count = 0
            for chunk_start in range(0, len(cold_ids), CHUNK_SIZE):
                chunk = cold_ids[chunk_start:chunk_start + CHUNK_SIZE]
                placeholders = ','.join(['?'] * len(chunk))
                archived_count += archive_conn.execute(
                    f"SELECT COUNT(*) FROM jobs WHERE id IN ({placeholders})",
                    chunk
                ).fetchone()[0]

            if archived_count != len(cold_ids):
                archive_conn.close()
                raise RuntimeError(
                    f"Archive verification failed: expected {len(cold_ids)}, got {archived_count}"
                )

            # DELETE from live DB (reverse order: dependents first, then jobs)
            for table, fk_col in reversed(related_tables):
                for chunk_start in range(0, len(cold_ids), CHUNK_SIZE):
                    chunk = cold_ids[chunk_start:chunk_start + CHUNK_SIZE]
                    placeholders = ','.join(['?'] * len(chunk))
                    try:
                        conn.execute(
                            f"DELETE FROM {table} WHERE {fk_col} IN ({placeholders})", chunk
                        )
                    except Exception:
                        pass

            for chunk_start in range(0, len(cold_ids), CHUNK_SIZE):
                chunk = cold_ids[chunk_start:chunk_start + CHUNK_SIZE]
                placeholders = ','.join(['?'] * len(chunk))
                conn.execute(
                    f"DELETE FROM jobs WHERE id IN ({placeholders})", chunk
                )

        archive_conn.close()

        return {
            "archived_count": len(cold_ids),
            "archive_path": str(archive_path),
            "details": details,
        }

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
                    AVG(an.ai_score) as avg_ai_score
                FROM jobs j
                LEFT JOIN filter_results f ON j.id = f.job_id
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
                    COUNT(DISTINCT CASE WHEN r.id IS NOT NULL THEN j.id END) as resume_generated
                FROM jobs j
                LEFT JOIN filter_results f ON j.id = f.job_id
                LEFT JOIN resumes r ON j.id = r.job_id
                WHERE j.scraped_at >= DATE('now', ?)
                GROUP BY DATE(j.scraped_at)
                ORDER BY date DESC
            """, (f'-{days} days',))
            return [dict(row) for row in cursor.fetchall()]

    def get_daily_token_usage(self) -> int:
        """Get total tokens used today across AI analyses + cover letters."""
        with self._get_conn() as conn:
            row = conn.execute("""
                SELECT COALESCE(SUM(tokens), 0) as today_tokens FROM (
                    SELECT tokens_used as tokens FROM job_analysis
                    WHERE DATE(analyzed_at) = DATE('now')
                    UNION ALL
                    SELECT tokens_used as tokens FROM cover_letters
                    WHERE DATE(created_at) = DATE('now')
                )
            """).fetchone()
            return row['today_tokens'] if row else 0

    def clear_filter_results(self, filter_version: str = None) -> int:
        """清除筛选结果，以便重新处理

        Args:
            filter_version: 如果指定，只清除该版本的结果；否则清除全部

        Returns:
            删除的记录数
        """
        with self._get_conn(sync_before=False) as conn:
            if filter_version:
                cursor = conn.execute(
                    "DELETE FROM filter_results WHERE filter_version = ?",
                    (filter_version,)
                )
            else:
                cursor = conn.execute("DELETE FROM filter_results")
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
        with self._get_conn(sync_before=False) as conn:
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
                        raw_data=""  # Deprecated: no longer populated (duplicates description)
                    )
                    cursor = conn.execute("""
                        INSERT INTO jobs
                        (id, source, url, title, company, location, description,
                         posted_date, scraped_at, search_profile, search_query, raw_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ON CONFLICT(id) DO UPDATE SET
                            description = CASE
                                WHEN excluded.description != ''
                                     AND length(excluded.description) > length(COALESCE(jobs.description, ''))
                                THEN excluded.description
                                ELSE jobs.description
                            END
                    """, (job.id, job.source, job.url, job.title, job.company,
                          job.location, job.description, job.posted_date, job.scraped_at,
                          job.search_profile, job.search_query, job.raw_data))
                    if cursor.rowcount > 0:
                        imported += 1
                except Exception as e:
                    is_constraint = (
                        isinstance(e, sqlite3.IntegrityError)
                        or "UNIQUE constraint" in str(e)
                    )
                    severity = "WARN" if is_constraint else "ERROR"
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
                query += " AND id IN (SELECT job_id FROM job_analysis WHERE ai_score >= ?)"
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
        print(f"\u603b\u6293\u53d6: {stats.get('total_scraped', 0)}")
        print(f"\u901a\u8fc7\u7b5b\u9009: {stats.get('passed_filter', 0)}")
        print(f"AI 分析: {stats.get('ai_analyzed', 0)}")
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
