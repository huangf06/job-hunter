from contextlib import contextmanager
import sqlite3

from src.db.job_db import JobDatabase
from src.db.job_db import AnalysisResult


class RecordingConn:
    def __init__(self):
        self.statements = []

    def execute(self, statement, params=()):
        self.statements.append(statement.strip())
        return self

    def fetchall(self):
        return []


def test_init_db_runs_migrate_before_recreating_views():
    db = JobDatabase.__new__(JobDatabase)
    db.SCHEMA = "CREATE TABLE alpha (id INTEGER); CREATE TABLE beta (id INTEGER);"
    conn = RecordingConn()

    @contextmanager
    def fake_get_conn():
        yield conn

    def fake_migrate(inner_conn):
        inner_conn.execute("-- migrate marker")

    db._get_conn = fake_get_conn
    db._build_views_sql = lambda: "CREATE VIEW sample_view AS SELECT 1;"
    db._migrate = fake_migrate

    db._init_db()

    migrate_index = conn.statements.index("-- migrate marker")
    drop_view_index = conn.statements.index("DROP VIEW IF EXISTS v_pending_jobs")
    create_view_index = conn.statements.index("CREATE VIEW sample_view AS SELECT 1")

    assert migrate_index < drop_view_index
    assert migrate_index < create_view_index


def _insert_job(db: JobDatabase, job_id: str) -> None:
    db.execute(
        """
        INSERT INTO jobs (id, source, url, title, company, location, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            job_id,
            "test",
            f"https://example.com/{job_id}",
            "Data Engineer",
            "TestCorp",
            "Amsterdam",
            "Test description",
        ),
    )


def _make_in_memory_db() -> JobDatabase:
    db = JobDatabase.__new__(JobDatabase)
    db._turso_http = None
    db._conn = sqlite3.connect(":memory:")
    db._conn.row_factory = sqlite3.Row
    db._conn.executescript(
        """
        CREATE TABLE jobs (
            id TEXT PRIMARY KEY,
            source TEXT,
            url TEXT,
            title TEXT,
            company TEXT,
            location TEXT,
            description TEXT
        );

        CREATE TABLE job_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            ai_score REAL,
            skill_match REAL,
            experience_fit REAL,
            growth_potential REAL,
            recommendation TEXT,
            reasoning TEXT,
            tailored_resume TEXT,
            model TEXT,
            tokens_used INTEGER,
            analyzed_at TEXT
        );

        CREATE TABLE resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            role_type TEXT,
            template_version TEXT,
            html_path TEXT,
            pdf_path TEXT,
            generated_at TEXT
        );

        CREATE TABLE cover_letters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL UNIQUE,
            spec_json TEXT,
            custom_requirements TEXT,
            standard_text TEXT,
            short_text TEXT,
            html_path TEXT,
            pdf_path TEXT,
            tokens_used INTEGER,
            created_at TEXT
        );
        """
    )

    @contextmanager
    def fake_get_conn(sync_before=True):
        yield db._conn

    db._get_conn = fake_get_conn
    return db


def test_save_analysis_round_trips_routing_fields():
    db = _make_in_memory_db()
    db._migrate(db._conn)
    _insert_job(db, "job-routing")

    result = AnalysisResult(
        job_id="job-routing",
        ai_score=7.2,
        skill_match=7.5,
        experience_fit=6.8,
        growth_potential=7.1,
        recommendation="APPLY",
        reasoning="routing-aware reasoning",
        tailored_resume='{"slot_overrides":{"bio":"Updated bio"}}',
        model="claude_code",
        tokens_used=321,
        resume_tier="ADAPT_TEMPLATE",
        template_id_initial="DE",
        template_id_final="ML",
        routing_confidence=0.55,
        routing_override_reason="C1 found stronger ML fit",
        escalation_reason="Auto-escalated due to ambiguity",
        routing_payload='{"tier":"ADAPT_TEMPLATE","template_id":"ML"}',
        c3_decision="PASS",
        c3_confidence=0.84,
        c3_reason="Adaptation materially improves fit",
    )

    db.save_analysis(result)

    saved = db.get_analysis("job-routing")

    assert saved is not None
    assert saved["resume_tier"] == "ADAPT_TEMPLATE"
    assert saved["template_id_initial"] == "DE"
    assert saved["template_id_final"] == "ML"
    assert saved["routing_confidence"] == 0.55
    assert saved["routing_override_reason"] == "C1 found stronger ML fit"
    assert saved["escalation_reason"] == "Auto-escalated due to ambiguity"
    assert saved["routing_payload"] == '{"tier":"ADAPT_TEMPLATE","template_id":"ML"}'
    assert saved["c3_decision"] == "PASS"
    assert saved["c3_confidence"] == 0.84
    assert saved["c3_reason"] == "Adaptation materially improves fit"


def test_save_analysis_legacy_result_stores_null_routing_fields():
    db = _make_in_memory_db()
    db._migrate(db._conn)
    _insert_job(db, "job-legacy")

    legacy = AnalysisResult(
        job_id="job-legacy",
        ai_score=6.0,
        skill_match=6.0,
        experience_fit=6.0,
        growth_potential=6.0,
        recommendation="APPLY",
        reasoning="legacy result",
        tailored_resume='{"bio":"Legacy bio"}',
        model="claude_code",
        tokens_used=111,
    )

    db.save_analysis(legacy)

    saved = db.get_analysis("job-legacy")

    assert saved is not None
    assert saved["resume_tier"] is None
    assert saved["template_id_initial"] is None
    assert saved["template_id_final"] is None
    assert saved["routing_confidence"] is None
    assert saved["routing_override_reason"] is None
    assert saved["escalation_reason"] is None
    assert saved["routing_payload"] is None
    assert saved["c3_decision"] is None
    assert saved["c3_confidence"] is None
    assert saved["c3_reason"] is None


def test_save_analysis_empty_string_routing_fields_store_as_null():
    db = _make_in_memory_db()
    db._migrate(db._conn)
    _insert_job(db, "job-empty")

    result = AnalysisResult(
        job_id="job-empty",
        ai_score=6.5,
        recommendation="APPLY",
        reasoning="empty string routing fields",
        tailored_resume="{}",
        model="claude_code",
        resume_tier="",
        template_id_initial="",
        template_id_final="",
        routing_override_reason="",
        escalation_reason="",
        routing_payload="",
        c3_decision="",
        c3_reason="",
    )

    db.save_analysis(result)
    saved = db.get_analysis("job-empty")

    assert saved["resume_tier"] is None
    assert saved["template_id_initial"] is None
    assert saved["template_id_final"] is None
    assert saved["routing_override_reason"] is None
    assert saved["escalation_reason"] is None
    assert saved["routing_payload"] is None
    assert saved["c3_decision"] is None
    assert saved["c3_reason"] is None


def test_clear_rejected_analyses_keeps_routed_rows():
    db = _make_in_memory_db()
    db._migrate(db._conn)
    _insert_job(db, "job-routed")
    _insert_job(db, "job-legacy-rejected")

    db.execute(
        "INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, resume_tier, model, tokens_used, analyzed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        ("job-routed", 7.0, "APPLY", "tier1", "{}", "USE_TEMPLATE", "claude_code", 0),
    )
    db.execute(
        "INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        ("job-legacy-rejected", 0.0, "REJECTED", "legacy reject", "{}", "claude_code", 0),
    )

    deleted = db.clear_rejected_analyses()

    assert deleted == 1
    assert db.get_analysis("job-routed") is not None
    assert db.get_analysis("job-legacy-rejected") is None


def test_clear_transient_failures_keeps_routed_rows():
    db = _make_in_memory_db()
    db._migrate(db._conn)
    _insert_job(db, "job-routed-fail")
    _insert_job(db, "job-legacy-fail")

    db.execute(
        "INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, resume_tier, model, tokens_used, analyzed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        ("job-routed-fail", 7.0, "APPLY", "Claude Code CLI returned empty response", "{}", "USE_TEMPLATE", "claude_code", 0),
    )
    db.execute(
        "INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
        ("job-legacy-fail", 0.0, "REJECTED", "Claude Code CLI returned empty response", "{}", "claude_code", 0),
    )

    deleted = db.clear_transient_failures()

    assert deleted == 1
    assert db.get_analysis("job-routed-fail") is not None
    assert db.get_analysis("job-legacy-fail") is None


def test_get_jobs_needing_cover_letter_includes_tier_aware_cases():
    db = _make_in_memory_db()
    db._migrate(db._conn)
    for job_id in ["job-use", "job-adapt-fail", "job-full", "job-legacy", "job-adapt-pass"]:
        _insert_job(db, job_id)

    analyses = [
        ("job-use", 6.0, "USE_TEMPLATE", "{}", None),
        ("job-adapt-fail", 6.0, "ADAPT_TEMPLATE", '{"slot_overrides":{"bio":"x"}}', "FAIL"),
        ("job-full", 6.0, "FULL_CUSTOMIZE", '{"bio":"custom"}', None),
        ("job-legacy", 6.0, None, '{"bio":"legacy"}', None),
        ("job-adapt-pass", 6.0, "ADAPT_TEMPLATE", '{"slot_overrides":{"bio":"x"}}', "PASS"),
    ]
    for job_id, score, tier, tailored_resume, c3_decision in analyses:
        db.execute(
            "INSERT INTO job_analysis (job_id, ai_score, recommendation, reasoning, tailored_resume, resume_tier, c3_decision, model, tokens_used, analyzed_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (job_id, score, "APPLY", "reason", tailored_resume, tier, c3_decision, "claude_code", 0),
        )
        db.execute(
            "INSERT INTO resumes (job_id, role_type, template_version, html_path, pdf_path, generated_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            (job_id, "DE", "v1", "", f"/tmp/{job_id}.pdf"),
        )

    jobs = db.get_jobs_needing_cover_letter(min_ai_score=5.0)
    job_ids = {job["id"] for job in jobs}

    assert "job-use" in job_ids
    assert "job-adapt-fail" in job_ids
    assert "job-full" in job_ids
    assert "job-legacy" in job_ids
    assert "job-adapt-pass" in job_ids


def test_build_views_sql_contains_required_tier_counters():
    db = JobDatabase.__new__(JobDatabase)
    sql = db._build_views_sql()

    assert "tier_2_pass" in sql
    assert "tier_2_fail" in sql
    assert "override_count" in sql
    assert "escalation_count" in sql
    assert "legacy_analysis_count" in sql
