from contextlib import contextmanager

from src.db.job_db import JobDatabase


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
