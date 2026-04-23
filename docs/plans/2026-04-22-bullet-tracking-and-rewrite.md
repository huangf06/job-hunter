# Bullet Library Tracking System + Interview-Data Rewrite

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a bullet version tracking system that correlates bullet usage with interview outcomes, then rewrite bullet_library.yaml to restore v3.0 interview-proven content.

**Architecture:** Two new DB tables (`bullet_versions`, `bullet_usage`) track which bullet versions are used per resume. `_resolve_bullet_ids` in ai_analyzer.py records usage at resolution time. A backfill script populates historical data from existing tailored_resume JSON. The bullet library YAML is then rewritten to restore v3.0 interview-proven bullets while keeping v5.0 structural improvements.

**Tech Stack:** Python, SQLite/Turso, YAML, pytest

---

### Task 1: Add `bullet_versions` and `bullet_usage` tables to DB schema

**Files:**
- Modify: `src/db/job_db.py:357-507` (SCHEMA constant)
- Modify: `src/db/job_db.py:677-712` (`_migrate` method)
- Test: `tests/test_bullet_tracking.py`

**Step 1: Write the failing test**

```python
# tests/test_bullet_tracking.py
"""Tests for bullet version tracking tables and operations."""

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from src.db.job_db import JobDatabase


@pytest.fixture
def db(tmp_path):
    """Create a fresh in-memory-like DB for testing."""
    db_path = tmp_path / "test.db"
    import os
    os.environ["NO_TURSO"] = "1"
    database = JobDatabase(db_path=db_path)
    return database


class TestBulletTrackingSchema:
    def test_bullet_versions_table_exists(self, db):
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bullet_versions'")
        assert len(rows) == 1

    def test_bullet_usage_table_exists(self, db):
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bullet_usage'")
        assert len(rows) == 1

    def test_insert_bullet_version(self, db):
        content = "Built PySpark ETL pipelines processing credit data."
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        db.execute(
            "INSERT INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("glp_pyspark", content_hash, content, "v3.0"),
        )
        rows = db.execute("SELECT * FROM bullet_versions WHERE bullet_id = ?", ("glp_pyspark",))
        assert len(rows) == 1
        assert rows[0]["content_hash"] == content_hash

    def test_insert_bullet_usage(self, db):
        # Need a job first
        db.execute(
            "INSERT INTO jobs (id, source, url, title, company, scraped_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
            ("j1", "test", "https://example.com/j1", "Data Engineer", "TestCo"),
        )
        db.execute(
            "INSERT INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
            ("u1", "j1", "glp_pyspark", "abc123", "experience", 0),
        )
        rows = db.execute("SELECT * FROM bullet_usage WHERE job_id = ?", ("j1",))
        assert len(rows) == 1
        assert rows[0]["bullet_id"] == "glp_pyspark"

    def test_bullet_version_upsert_idempotent(self, db):
        content = "Some bullet text."
        h = hashlib.sha256(content.encode()).hexdigest()[:16]
        db.execute(
            "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("b1", h, content, "v5.0"),
        )
        db.execute(
            "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("b1", h, content, "v5.0"),
        )
        rows = db.execute("SELECT * FROM bullet_versions WHERE bullet_id = ?", ("b1",))
        assert len(rows) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bullet_tracking.py -v`
Expected: FAIL — tables don't exist yet

**Step 3: Add tables to SCHEMA and _migrate**

In `src/db/job_db.py`, append to the SCHEMA constant (before the index section at line ~497):

```sql
-- Bullet version tracking (append-only history)
CREATE TABLE IF NOT EXISTS bullet_versions (
    bullet_id    TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    content      TEXT NOT NULL,
    library_version TEXT,
    first_seen   TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (bullet_id, content_hash)
);

-- Per-resume bullet usage log
CREATE TABLE IF NOT EXISTS bullet_usage (
    id           TEXT PRIMARY KEY,
    job_id       TEXT NOT NULL REFERENCES jobs(id),
    bullet_id    TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    section      TEXT NOT NULL,
    position     INTEGER,
    created_at   TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_bullet_usage_job ON bullet_usage(job_id);
CREATE INDEX IF NOT EXISTS idx_bullet_usage_bullet ON bullet_usage(bullet_id);
```

No changes needed to `_migrate` — `CREATE TABLE IF NOT EXISTS` handles existing databases.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bullet_tracking.py -v`
Expected: all 5 PASS

**Step 5: Commit**

```bash
git add src/db/job_db.py tests/test_bullet_tracking.py
git commit -m "feat(db): add bullet_versions and bullet_usage tracking tables"
```

---

### Task 2: Add `v_bullet_conversion` analytics view

**Files:**
- Modify: `src/db/job_db.py:509-507` (VIEWS_TEMPLATE) or `_init_db` for a standalone view
- Test: `tests/test_bullet_tracking.py`

**Step 1: Write the failing test**

Append to `tests/test_bullet_tracking.py`:

```python
class TestBulletConversionView:
    def test_view_exists(self, db):
        rows = db.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='v_bullet_conversion'")
        assert len(rows) == 1

    def test_view_computes_conversion(self, db):
        # Setup: 2 jobs, 1 with interview
        for jid, url in [("j1", "https://a.com/1"), ("j2", "https://a.com/2")]:
            db.execute(
                "INSERT INTO jobs (id, source, url, title, company, scraped_at) VALUES (?, 'test', ?, 'DE', 'Co', datetime('now'))",
                (jid, url),
            )
        h = "abc123"
        db.execute(
            "INSERT INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            ("glp_pyspark", h, "text", "v6.0"),
        )
        # Both jobs used glp_pyspark
        db.execute("INSERT INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
                   ("u1", "j1", "glp_pyspark", h, "experience", 0))
        db.execute("INSERT INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
                   ("u2", "j2", "glp_pyspark", h, "experience", 0))
        # j1 got an interview
        db.execute(
            "INSERT INTO interview_rounds (id, job_id, round_number, round_type, status) VALUES (?, ?, ?, ?, ?)",
            ("ir1", "j1", 1, "hr", "completed"),
        )
        rows = db.execute("SELECT * FROM v_bullet_conversion WHERE bullet_id = 'glp_pyspark'")
        assert len(rows) == 1
        assert rows[0]["times_used"] == 2
        assert rows[0]["times_got_interview"] == 1
        assert rows[0]["interview_rate"] == 50.0
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bullet_tracking.py::TestBulletConversionView -v`
Expected: FAIL — view and interview_rounds table don't exist in test DB

**Step 3: Add interview_rounds to SCHEMA and v_bullet_conversion view**

The `interview_rounds` table currently exists only in production (created outside the SCHEMA constant). Add it to SCHEMA so tests can use it:

```sql
-- Interview rounds tracking
CREATE TABLE IF NOT EXISTS interview_rounds (
    id              TEXT PRIMARY KEY,
    job_id          TEXT NOT NULL REFERENCES jobs(id),
    round_number    INTEGER NOT NULL,
    round_type      TEXT NOT NULL,
    scheduled_date  TEXT,
    completed_date  TEXT,
    status          TEXT NOT NULL,
    notes           TEXT,
    interviewer_name TEXT,
    duration_minutes INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    updated_at      TEXT DEFAULT (datetime('now'))
);
```

Add the view creation to `_init_db`, after the existing views block (line ~647):

```python
# Bullet conversion analytics view
conn.execute("DROP VIEW IF EXISTS v_bullet_conversion")
conn.execute("""
    CREATE VIEW IF NOT EXISTS v_bullet_conversion AS
    SELECT
        bu.bullet_id,
        bv.library_version,
        bu.content_hash,
        COUNT(DISTINCT bu.job_id) as times_used,
        COUNT(DISTINCT ir.job_id) as times_got_interview,
        ROUND(
            COUNT(DISTINCT ir.job_id) * 100.0 / MAX(COUNT(DISTINCT bu.job_id), 1),
            1
        ) as interview_rate,
        bv.content
    FROM bullet_usage bu
    JOIN bullet_versions bv
        ON bu.bullet_id = bv.bullet_id AND bu.content_hash = bv.content_hash
    LEFT JOIN interview_rounds ir ON bu.job_id = ir.job_id
    GROUP BY bu.bullet_id, bu.content_hash
    ORDER BY interview_rate DESC, times_used DESC
""")
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_bullet_tracking.py -v`
Expected: all PASS

**Step 5: Commit**

```bash
git add src/db/job_db.py tests/test_bullet_tracking.py
git commit -m "feat(db): add interview_rounds to schema + v_bullet_conversion view"
```

---

### Task 3: Record bullet usage in `_resolve_bullet_ids`

**Files:**
- Modify: `src/ai_analyzer.py:331-388` (`_resolve_bullet_ids`)
- Modify: `src/ai_analyzer.py:205-240` (`_build_bullet_id_lookup` — add hash computation)
- Test: `tests/test_bullet_tracking.py`

**Step 1: Write the failing test**

Append to `tests/test_bullet_tracking.py`:

```python
class TestBulletUsageRecording:
    def test_resolve_records_usage(self, db, tmp_path):
        """When _resolve_bullet_ids runs, it should record bullet_usage rows."""
        import os
        os.environ["NO_TURSO"] = "1"

        # Create a minimal AIAnalyzer with our test DB
        from unittest.mock import patch, MagicMock

        # Insert a job so FK constraint is satisfied
        db.execute(
            "INSERT INTO jobs (id, source, url, title, company, scraped_at) VALUES (?, 'test', 'https://x.com/1', 'DE', 'Co', datetime('now'))",
            ("job-001",),
        )

        # Build a mock analyzer with known bullet lookup
        bullet_content = "Designed and implemented PySpark ETL pipelines processing consumer credit data."
        bullet_hash = hashlib.sha256(bullet_content.encode()).hexdigest()[:16]

        mock_analyzer = MagicMock()
        mock_analyzer.bullet_id_lookup = {"glp_pyspark": bullet_content}
        mock_analyzer.bullet_id_hashes = {"glp_pyspark": bullet_hash}
        mock_analyzer.valid_bullets = {bullet_content}
        mock_analyzer.db = db
        mock_analyzer._current_job_id = "job-001"

        # Import the real method and bind it
        from src.ai_analyzer import AIAnalyzer
        tailored = {
            "experiences": [
                {"company": "GLP", "bullets": ["glp_pyspark"]}
            ],
            "projects": [],
        }

        result, errors = AIAnalyzer._resolve_bullet_ids(mock_analyzer, tailored)

        # Verify bullet_usage was recorded
        rows = db.execute("SELECT * FROM bullet_usage WHERE job_id = 'job-001'")
        assert len(rows) == 1
        assert rows[0]["bullet_id"] == "glp_pyspark"
        assert rows[0]["content_hash"] == bullet_hash
        assert rows[0]["section"] == "experience"

        # Verify bullet_versions was upserted
        vers = db.execute("SELECT * FROM bullet_versions WHERE bullet_id = 'glp_pyspark'")
        assert len(vers) == 1
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_bullet_tracking.py::TestBulletUsageRecording -v`
Expected: FAIL — no `bullet_id_hashes`, no `_current_job_id`, no recording logic

**Step 3: Implement recording**

3a. In `_build_bullet_id_lookup` (line ~205), also build a hash lookup. Add after the method:

```python
def _build_bullet_id_hashes(self) -> Dict[str, str]:
    """Build mapping of bullet ID -> SHA-256 content hash (first 16 chars)."""
    import hashlib
    return {
        bid: hashlib.sha256(content.encode()).hexdigest()[:16]
        for bid, content in self.bullet_id_lookup.items()
    }
```

In `__init__` (line ~57), add after `self.bullet_id_lookup`:

```python
self.bullet_id_hashes = self._build_bullet_id_hashes()
```

3b. Add `_current_job_id` tracking. In `_resolve_bullet_ids`, the method currently doesn't know the job_id. We need to pass it in. Change signature:

```python
def _resolve_bullet_ids(self, tailored: Dict, job_id: str = None) -> tuple:
```

3c. At the end of `_resolve_bullet_ids` (before `return tailored, errors`), add recording logic:

```python
if job_id and hasattr(self, 'db') and usage_log:
    self._record_bullet_usage(job_id, usage_log)
```

Where `usage_log` is built during resolution. Inside the experience loop, when a bullet ID is resolved:

```python
if bullet in self.bullet_id_lookup:
    text = self.bullet_id_lookup[bullet]
    if text not in resolved:
        resolved.append(text)
        usage_log.append({
            'bullet_id': bullet,
            'content_hash': self.bullet_id_hashes.get(bullet, ''),
            'section': 'experience',
            'position': len(resolved) - 1,
        })
```

Similarly for projects with `'section': 'project'`.

Initialize `usage_log = []` at the top of the method.

3d. Add the `_record_bullet_usage` method:

```python
def _record_bullet_usage(self, job_id: str, usage_log: list):
    """Record which bullets were used for a job (append-only)."""
    import hashlib as _hl
    import uuid
    for entry in usage_log:
        bid = entry['bullet_id']
        chash = entry['content_hash']
        content = self.bullet_id_lookup.get(bid, '')
        # Upsert version
        self.db.execute(
            "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
            (bid, chash, content, self._library_version()),
        )
        # Record usage
        self.db.execute(
            "INSERT OR IGNORE INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4())[:8], job_id, bid, chash, entry['section'], entry['position']),
        )

def _library_version(self) -> str:
    """Extract library version from parsed YAML header comment or return 'unknown'."""
    lib_path = PROJECT_ROOT / "assets" / "bullet_library.yaml"
    try:
        with open(lib_path, 'r', encoding='utf-8') as f:
            for line in f:
                if 'VERIFIED BULLET LIBRARY' in line and 'v' in line.lower():
                    import re
                    m = re.search(r'v(\d+\.\d+)', line)
                    if m:
                        return f"v{m.group(1)}"
                if not line.startswith('#'):
                    break
    except Exception:
        pass
    return "unknown"
```

3e. Update both call sites to pass `job_id`:

- Line ~822: `tailored, bullet_errors = self._resolve_bullet_ids(tailored, job_id=job_id)`
- Line ~1062: `tailored, bullet_errors = self._resolve_bullet_ids(tailored, job_id=job_id)`

**Step 4: Run tests**

Run: `python -m pytest tests/test_bullet_tracking.py tests/test_ai_analyzer.py -v`
Expected: all PASS (existing tests unaffected since `job_id` defaults to None)

**Step 5: Commit**

```bash
git add src/ai_analyzer.py tests/test_bullet_tracking.py
git commit -m "feat(tracking): record bullet usage and versions during resume generation"
```

---

### Task 4: Add `status` and `tags` fields to bullet library YAML

**Files:**
- Modify: `assets/bullet_library.yaml`
- Test: manual — verify YAML parses, existing tests pass

This task adds `status` and `tags` to every bullet entry in the YAML. The AI analyzer already ignores unknown fields, so this is purely additive.

**Step 1: Add status/tags to all work_experience bullets**

Add `status: active` to every existing bullet. Add `tags` based on content. Example:

```yaml
- id: glp_founding_member
  status: active
  tags: [ml, leadership, founding, credit-risk]
  narrative_role: context_setter
  content: "..."
```

Use `status: deprecated` for bullets we're about to replace. Use `tags` reflecting the bullet's domain signals.

Tag taxonomy:
- Domain: `credit-risk`, `quant`, `data-pipeline`, `analytics`, `fraud`, `trading`
- Tech: `pyspark`, `sql`, `hadoop`, `numpy`, `pytorch`
- Signal: `leadership`, `founding`, `mentorship`, `compliance`, `data-quality`
- Role: `de`, `ml`, `ds`, `quant-researcher`

**Step 2: Run existing tests to verify no regression**

Run: `python -m pytest tests/ -v --timeout=30`
Expected: all existing tests PASS (new fields are ignored by code)

**Step 3: Commit**

```bash
git add assets/bullet_library.yaml
git commit -m "feat(bullets): add status and tags metadata to all bullet entries"
```

---

### Task 5: Rewrite bullet library — restore v3.0 interview-proven GLP bullets

**Files:**
- Modify: `assets/bullet_library.yaml` (glp_technology section)
- Reference: `git show d819d38:assets/bullet_library.yaml` (v3.0 source)

**Step 1: Restore v3.0 GLP bullets**

Replace current GLP bullets with v3.0 originals. Current v5.0 bullets that are fundamentally different get deprecated.

Specific changes:

| Bullet ID | Action |
|-----------|--------|
| `glp_founding_member` | Restore v3.0 content (14x interview-proven) |
| `glp_decision_engine` | Keep (v5.0 addition, has specific metrics) |
| `glp_data_engineer` | Deprecate v5.0 version. Restore as `glp_pyspark` with v3.0 content (16x proven) |
| `glp_portfolio_monitoring` | Restore v3.0 content (9x proven) |
| `glp_data_compliance` | Restore from v3.0 (3x proven, was deleted) |
| `glp_payment_collections` | Restore from v3.0 (was deleted) |
| `glp_generalist` | Keep as-is (0x selected, but harmless backup) |

v3.0 content to restore:

```yaml
- id: glp_founding_member
  status: active
  tags: [ml, leadership, founding, credit-risk]
  narrative_role: context_setter
  content: "Spearheaded credit scoring infrastructure as the first data hire at a consumer lending startup — owned the full ML lifecycle from data ingestion through feature engineering, model deployment (logistic regression scorecards), and portfolio monitoring, enabling automated credit decisions."

- id: glp_pyspark
  status: active
  tags: [pyspark, etl, mentorship, credit-risk, de]
  narrative_role: headline
  content: "Designed and implemented PySpark ETL pipelines processing consumer credit data across the full loan lifecycle — from application ingestion through repayment tracking; provided technical mentorship to junior analyst on distributed data processing patterns."

- id: glp_data_engineer
  status: deprecated
  tags: [etl, aws, de]
  narrative_role: foundation
  content: "Built the data foundation powering all risk systems: daily ETL of 30+ production tables into AWS Redshift, plus a credit bureau report parser transforming deeply nested JSON into 5 structured analytical tables."

- id: glp_data_quality
  status: active
  tags: [data-quality, schema-validation, credit-risk, de]
  narrative_role: foundation
  content: "Engineered automated data pipeline and quality framework for consumer lending operations, implementing schema validation and integrity checks across loan origination and repayment flows — ensuring clean inputs for credit scoring models."

- id: glp_portfolio_monitoring
  status: active
  tags: [monitoring, risk, analytics, ds]
  narrative_role: extension
  content: "Built portfolio risk monitoring system tracking delinquency rates, repayment trends, and early warning indicators across the consumer loan book; insights directly informed collection strategy adjustments, reducing exposure to deteriorating segments."

- id: glp_data_compliance
  status: active
  tags: [compliance, reporting, regulated-industry]
  narrative_role: optional
  content: "Established compliance reporting framework for consumer lending operations, automating regulatory submissions and audit trail generation for credit decisioning outputs."

- id: glp_payment_collections
  status: active
  tags: [api, operations, payments]
  narrative_role: optional
  content: "Integrated payment gateway APIs for automated repayment processing; designed tiered collection policies based on delinquency severity, bridging data insights with operational execution."
```

**Step 2: Update `recommended_sequences` for GLP**

Update to use restored bullet IDs:

```yaml
recommended_sequences:
  data_engineer: ["glp_founding_member", "glp_pyspark", "glp_data_quality"]
  ml_engineer: ["glp_founding_member", "glp_decision_engine"]
  data_scientist: ["glp_founding_member", "glp_decision_engine", "glp_portfolio_monitoring"]
```

**Step 3: Run tests**

Run: `python -m pytest tests/ -v --timeout=30`
Expected: PASS

**Step 4: Commit**

```bash
git add assets/bullet_library.yaml
git commit -m "feat(bullets): restore v3.0 interview-proven GLP bullets, deprecate v5.0 rewrites"
```

---

### Task 6: Rewrite bullet library — restore v3.0 Baiquan bullets

**Files:**
- Modify: `assets/bullet_library.yaml` (baiquan_investment section)

**Step 1: Restore Baiquan v3.0 bullets**

| Bullet ID | Action |
|-----------|--------|
| `bq_de_pipeline` | Keep current (matches v3.0 `bq_de_pipeline`) |
| `bq_de_backtest_infra` | Keep current (matches v3.0) |
| `bq_factor_research` | Keep current (v5.0 version emphasizes Fama-MacBeth) |
| `bq_de_factor_engine` | Restore from v3.0 (15x proven, engineering focus — currently missing) |
| `bq_data_quality` | Restore from v3.0 (9x proven, was deleted) |
| `bq_futures_strategy` | Keep current (matches v3.0) |

Add back:

```yaml
- id: bq_de_factor_engine
  status: active
  tags: [numpy, pandas, vectorized, performance, quant]
  narrative_role: headline
  content: "Engineered high-performance factor computation engine using vectorized NumPy/Pandas operations, computing technical and fundamental indicators across 3,000+ stocks daily — enabling rapid iteration cycles in alpha research."

- id: bq_data_quality
  status: active
  tags: [data-quality, monitoring, alerting, de]
  narrative_role: optional
  content: "Designed cross-source data validation framework detecting vendor data gaps and inconsistencies in market feeds; built automated alerting for missing trading days and stale prices, safeguarding research pipeline integrity."
```

Update `recommended_sequences`:
```yaml
recommended_sequences:
  data_engineer: ["bq_de_pipeline", "bq_de_backtest_infra", "bq_de_factor_engine"]
  ml_engineer: ["bq_futures_strategy", "bq_factor_research", "bq_de_backtest_infra"]
  quant_researcher: ["bq_futures_strategy", "bq_factor_research", "bq_de_backtest_infra", "bq_de_pipeline"]
  data_scientist: ["bq_factor_research", "bq_de_pipeline", "bq_futures_strategy"]
```

**Step 2: Run tests, commit**

```bash
python -m pytest tests/ -v --timeout=30
git add assets/bullet_library.yaml
git commit -m "feat(bullets): restore v3.0 Baiquan factor engine + data quality bullets"
```

---

### Task 7: Rewrite bullet library — restore v3.0 Ele.me bullets + Deribit project

**Files:**
- Modify: `assets/bullet_library.yaml` (eleme + projects sections)

**Step 1: Restore Ele.me combined A/B bullet**

Add back the v3.0 combined bullet (9x proven) alongside existing v5.0 bullets:

```yaml
- id: eleme_ab_testing
  status: active
  tags: [ab-testing, sql, hadoop, analytics, ds]
  narrative_role: headline
  content: "Developed user segmentation model achieving 2x improvement in churned-user reactivation rate via A/B testing; optimized Hadoop/Hive SQL queries for cross-functional reporting, cutting turnaround time by 30% during the platform's hyper-growth phase."
```

Keep `eleme_fraud_detection`, `eleme_sql_optimization`, `eleme_user_segmentation` as active (they're v5.0 additions with real content).

**Step 2: Restore Deribit options project**

Re-add to projects section (was deprecated in v4.0 but 4x interview-proven):

```yaml
deribit_options:
  title: "Automated Crypto Options Trading System"
  institution: "Personal Project"
  period: "Oct. 2025 - Present"

  verified_bullets:
    - id: deribit_options_system
      status: active
      tags: [options, black-scholes, greeks, risk-management, quant, trading]
      narrative_role: headline
      content: "Architected automated options trading system featuring self-implemented Black-Scholes pricing engine (full Greeks, IV solver), edge-based market-making strategy, and multi-layered risk management (position limits, Greeks constraints, drawdown control); currently in paper-trading validation."

    - id: deribit_risk_management
      status: active
      tags: [risk-management, position-sizing, quant]
      narrative_role: optional
      content: "Designed risk management framework enforcing portfolio-level constraints (delta, gamma, vega limits), per-trade stop-loss, daily loss caps, and maximum drawdown controls; implemented Kelly-inspired position sizing adjusted for implied volatility."
```

Also add `deribit_options` back to `DEFAULT_PROJECT_KEYS` in `src/ai_analyzer.py:45-49` (it's already there from the v3.0 era — verify).

**Step 3: Run tests, commit**

```bash
python -m pytest tests/ -v --timeout=30
git add assets/bullet_library.yaml src/ai_analyzer.py
git commit -m "feat(bullets): restore v3.0 Ele.me combined bullet + Deribit options project"
```

---

### Task 8: Backfill historical bullet usage from interview data

**Files:**
- Create: `scripts/backfill_bullet_usage.py`
- Test: run script and verify data

**Step 1: Write the backfill script**

```python
#!/usr/bin/env python3
"""Backfill bullet_usage from historical tailored_resume JSON.

Matches bullet text in stored resumes against known library versions
(v3.0 from git, current from YAML) to reconstruct which bullet IDs
were used for each job that got an interview.
"""

import hashlib
import json
import sys
import uuid
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.db.job_db import JobDatabase


def load_v3_bullets() -> dict:
    """Load v3.0 bullet library from known content."""
    # These are the v3.0 bullet texts verified from git history
    # Maps: content_text -> (bullet_id, library_version)
    bullets = {}

    v3_bullets = {
        "glp_founding_member": "Spearheaded credit scoring infrastructure as the first data hire at a consumer lending startup — owned the full ML lifecycle from data ingestion through feature engineering, model deployment (logistic regression scorecards), and portfolio monitoring, enabling automated credit decisions.",
        "glp_pyspark": "Designed and implemented PySpark ETL pipelines processing consumer credit data across the full loan lifecycle — from application ingestion through repayment tracking; provided technical mentorship to junior analyst on distributed data processing patterns.",
        "glp_data_quality": "Engineered automated data pipeline and quality framework for consumer lending operations, implementing schema validation and integrity checks across loan origination and repayment flows — ensuring clean inputs for credit scoring models.",
        "glp_portfolio_monitoring": "Built portfolio risk monitoring system tracking delinquency rates, repayment trends, and early warning indicators across the consumer loan book; insights directly informed collection strategy adjustments, reducing exposure to deteriorating segments.",
        "glp_data_compliance": "Established compliance reporting framework for consumer lending operations, automating regulatory submissions and audit trail generation for credit decisioning outputs.",
        "glp_payment_collections": "Integrated payment gateway APIs for automated repayment processing; designed tiered collection policies based on delinquency severity, bridging data insights with operational execution.",
        "bq_de_pipeline": "Built automated market data ingestion pipeline integrating multiple vendor feeds (Wind, Tushare) for 3,000+ A-share securities; implemented corporate action adjustments (splits, dividends, suspensions) ensuring clean inputs for downstream factor research.",
        "bq_de_factor_engine": "Engineered high-performance factor computation engine using vectorized NumPy/Pandas operations, computing technical and fundamental indicators across 3,000+ stocks daily — enabling rapid iteration cycles in alpha research.",
        "bq_de_backtest_infra": "Architected event-driven backtesting framework supporting strategy simulation, walk-forward validation, and performance attribution — adopted as core research infrastructure by the investment team.",
        "bq_factor_research": "Built systematic alpha research pipeline covering 3,000+ A-share equities; applied Fama-MacBeth regression to validate multi-factor models (value, momentum, money flow, event-driven) — validated factors integrated into the fund's live portfolio.",
        "bq_futures_strategy": "Developed and deployed R-Breaker intraday trading strategy for CSI index futures from research through live production — achieved 14.6% annualized return with real capital.",
        "bq_data_quality": "Designed cross-source data validation framework detecting vendor data gaps and inconsistencies in market feeds; built automated alerting for missing trading days and stale prices, safeguarding research pipeline integrity.",
        "eleme_ab_testing": "Developed user segmentation model achieving 2x improvement in churned-user reactivation rate via A/B testing; optimized Hadoop/Hive SQL queries for cross-functional reporting, cutting turnaround time by 30% during the platform's hyper-growth phase.",
        "eleme_user_segmentation": "Engineered K-means clustering pipeline on Hadoop/Hive to segment millions of users by behavioral patterns (order frequency, recency, category preferences); delivered actionable customer profiles adopted by product and marketing teams for personalized campaign targeting.",
        "eleme_sql_reporting": "Optimized complex SQL queries on Hadoop/Hive for cross-functional stakeholders, cutting reporting turnaround time by 30%.",
    }

    # Project bullets
    v3_projects = {
        "lakehouse_streaming": "Architected end-to-end data lakehouse on Databricks processing real-time financial market feeds via Auto Loader and Structured Streaming; implemented schema evolution and checkpoint-based fault tolerance ensuring zero data loss during upstream changes.",
        "lakehouse_quality": "Engineered data quality framework with quarantine-and-replay pattern isolating malformed records across Bronze/Silver/Gold Medallion Architecture layers — achieving automated recovery without manual intervention.",
        "lakehouse_optimization": "Optimized Delta Lake storage via Z-ordering and compaction, reducing query latency for downstream analysis.",
        "lakehouse_orchestration": "Integrated Airflow for orchestration and Docker for consistent deployment across environments.",
        "thesis_uq_framework": "Developed RL-UQ-Bench, a benchmarking framework evaluating 5 uncertainty quantification methods for Deep RL across 150+ training runs on HPC (SLURM); demonstrated QR-DQN superiority with 31% lower CRPS (p < 0.001) over ensemble and dropout baselines.",
        "thesis_noise_paradox": "Discovered a 'noise paradox' where moderate observation noise unexpectedly improves ensemble-based uncertainty estimates; designed 6-stage reproducible evaluation pipeline with automated calibration benchmarking across multiple RL environments.",
        "thesis_calibration": "Applied temperature scaling and Bayesian methods to calibrate agent confidence; evaluated post-hoc calibration impact across distributional, ensemble, and dropout-based UQ approaches with rigorous statistical testing.",
        "deribit_options_system": "Architected automated options trading system featuring self-implemented Black-Scholes pricing engine (full Greeks, IV solver), edge-based market-making strategy, and multi-layered risk management (position limits, Greeks constraints, drawdown control); currently in paper-trading validation.",
        "expedia_ltr": "Developed hotel recommendation system using learning-to-rank models (LightGBM, XGBoost+SVD) on 4.9M search records; engineered temporal, behavioral, and user-preference features for ranking optimization; achieved NDCG@5 = 0.392, placing top 5% in Kaggle competition.",
        "lifeos_system": "Architected personal productivity platform orchestrating 5 external services (Todoist, Notion, Eudic, Telegram, Logseq) with automated daily workflows via GitHub Actions; built end-to-end vocabulary pipeline: dictionary sync, flashcard generation (genanki), and mobile delivery via Telegram Bot API.",
        "job_hunter_system": "Built end-to-end job application pipeline leveraging LLM APIs (Claude) for resume personalization; designed multi-stage processing (web scraping via Playwright, rule-based filtering, AI scoring, Jinja2 template rendering to PDF) with SQLite backend, YAML-driven configuration, and configurable quality gates.",
        "obama_tts_voice_cloning": "Fine-tuned Coqui XTTS v2 voice cloning model with hybrid deployment architecture: GPU training on Snellius HPC cluster via SLURM job arrays, CPU inference served through FastAPI REST API and Gradio web UI; implemented 5 configurable speaking styles for text-to-speech generation.",
        "nlp_poem_generator": "Developed LLM-powered text generation application leveraging GPT-2 and Hugging Face Transformers; implemented prompt engineering with controllable style parameters and deployed as interactive web application via Flask.",
    }

    for bid, content in {**v3_bullets, **v3_projects}.items():
        bullets[content] = (bid, "v3.0")

    return bullets


def fuzzy_match(text: str, known_bullets: dict, threshold: float = 0.85) -> tuple:
    """Try exact match first, then fuzzy substring match."""
    # Exact match
    if text in known_bullets:
        return known_bullets[text]

    # Normalize whitespace/dashes for near-exact match
    normalized = text.replace('—', '-').replace('–', '-').strip()
    for known_text, (bid, ver) in known_bullets.items():
        known_norm = known_text.replace('—', '-').replace('–', '-').strip()
        if normalized == known_norm:
            return (bid, ver)

    # Prefix match (first 80 chars)
    prefix = text[:80]
    for known_text, (bid, ver) in known_bullets.items():
        if known_text[:80] == prefix:
            return (bid, ver)

    return None


def main():
    db = JobDatabase()
    known = load_v3_bullets()

    # Get all jobs that had interviews (including Aon + Barak)
    interview_jobs = db.execute("SELECT DISTINCT job_id FROM interview_rounds")
    extra_ids = ["ebf72b62b510", "5f98d1f79e7b"]  # Aon, Barak
    job_ids = list(set([r["job_id"] for r in interview_jobs] + extra_ids))

    print(f"Backfilling {len(job_ids)} interview-winning jobs...")

    total_matched = 0
    total_unmatched = 0

    for jid in sorted(job_ids):
        rows = db.execute(
            "SELECT j.company, ja.tailored_resume FROM jobs j JOIN job_analysis ja ON j.id = ja.job_id WHERE j.id = ?",
            (jid,),
        )
        if not rows or not rows[0]["tailored_resume"]:
            continue

        resume = json.loads(rows[0]["tailored_resume"])
        company = rows[0]["company"]
        print(f"\n  {company} ({jid[:8]}):")

        position = 0
        for exp in resume.get("experiences", []):
            for bullet_text in exp.get("bullets", []):
                match = fuzzy_match(bullet_text, known)
                if match:
                    bid, ver = match
                    chash = hashlib.sha256(bullet_text.encode()).hexdigest()[:16]
                    # Upsert version
                    db.execute(
                        "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
                        (bid, chash, bullet_text, ver),
                    )
                    # Record usage
                    db.execute(
                        "INSERT OR IGNORE INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
                        (str(uuid.uuid4())[:8], jid, bid, chash, "experience", position),
                    )
                    print(f"    [MATCH] {bid} ({ver})")
                    total_matched += 1
                else:
                    print(f"    [MISS]  {bullet_text[:70]}...")
                    total_unmatched += 1
                position += 1

        for proj in resume.get("projects", []):
            for bullet_text in proj.get("bullets", []):
                match = fuzzy_match(bullet_text, known)
                if match:
                    bid, ver = match
                    chash = hashlib.sha256(bullet_text.encode()).hexdigest()[:16]
                    db.execute(
                        "INSERT OR IGNORE INTO bullet_versions (bullet_id, content_hash, content, library_version) VALUES (?, ?, ?, ?)",
                        (bid, chash, bullet_text, ver),
                    )
                    db.execute(
                        "INSERT OR IGNORE INTO bullet_usage (id, job_id, bullet_id, content_hash, section, position) VALUES (?, ?, ?, ?, ?, ?)",
                        (str(uuid.uuid4())[:8], jid, bid, chash, "project", position),
                    )
                    print(f"    [MATCH] {bid} ({ver})")
                    total_matched += 1
                else:
                    print(f"    [MISS]  {bullet_text[:70]}...")
                    total_unmatched += 1
                position += 1

    print(f"\n=== Backfill complete: {total_matched} matched, {total_unmatched} unmatched ===")

    # Show conversion view
    print("\n=== Bullet Conversion Rates ===")
    rows = db.execute("SELECT * FROM v_bullet_conversion ORDER BY interview_rate DESC, times_used DESC")
    print(f"{'Bullet ID':<30} {'Version':<8} {'Used':>5} {'Interview':>10} {'Rate':>6}")
    print("-" * 65)
    for r in rows:
        print(f"{r['bullet_id']:<30} {r['library_version'] or '?':<8} {r['times_used']:>5} {r['times_got_interview']:>10} {r['interview_rate']:>5.1f}%")


if __name__ == "__main__":
    main()
```

**Step 2: Run the backfill**

Run: `python scripts/backfill_bullet_usage.py`
Expected: ~80% match rate (some bullets may have minor text differences), conversion rate table displayed

**Step 3: Commit**

```bash
git add scripts/backfill_bullet_usage.py
git commit -m "feat(tracking): add historical bullet usage backfill script"
```

---

### Task 9: Add `--bullet-analytics` CLI command

**Files:**
- Modify: `scripts/job_pipeline.py` (add argument and handler)

**Step 1: Add argument parser entry**

Find the argparse section in `scripts/job_pipeline.py` and add:

```python
parser.add_argument('--bullet-analytics', action='store_true',
                    help='Show bullet library conversion analytics')
```

**Step 2: Add handler**

```python
if args.bullet_analytics:
    from src.db.job_db import JobDatabase
    db = JobDatabase()
    rows = db.execute("SELECT * FROM v_bullet_conversion ORDER BY interview_rate DESC, times_used DESC")
    if not rows:
        print("No bullet usage data. Run backfill first: python scripts/backfill_bullet_usage.py")
    else:
        print(f"\n{'Bullet ID':<30} {'Version':<8} {'Used':>5} {'Interview':>10} {'Rate':>6}")
        print("-" * 65)
        for r in rows:
            print(f"{r['bullet_id']:<30} {r['library_version'] or '?':<8} {r['times_used']:>5} {r['times_got_interview']:>10} {r['interview_rate']:>5.1f}%")

        # Summary
        total_uses = sum(r['times_used'] for r in rows)
        total_interviews = sum(r['times_got_interview'] for r in rows)
        unique_bullets = len(rows)
        print(f"\n  {unique_bullets} unique bullets tracked, {total_uses} total uses, {total_interviews} interview conversions")
    sys.exit(0)
```

**Step 3: Run and verify**

Run: `python scripts/job_pipeline.py --bullet-analytics`
Expected: table of bullet conversion rates (or "run backfill first" message)

**Step 4: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat(cli): add --bullet-analytics command for conversion rate reporting"
```

---

### Task 10: Update CLAUDE.md with bullet tracking documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add bullet tracking section**

Add after the "配置说明" section:

```markdown
### Bullet Library 追踪系统

Bullet library 变更通过 content hash 自动追踪，与面试结果关联。

**管理规则:**
- 修改措辞 → 直接改 YAML 内容，保持同一 ID（hash 自动追踪版本）
- 废弃 bullet → 设 `status: deprecated`
- 讲全新故事 → 新 ID
- 拆分/合并 → 废弃旧 ID，建新 ID

**查看转化率:** `python scripts/job_pipeline.py --bullet-analytics`
**回填历史数据:** `python scripts/backfill_bullet_usage.py`

DB 表: `bullet_versions` (版本历史), `bullet_usage` (每份简历用了哪些 bullet)
视图: `v_bullet_conversion` (按 bullet/版本 统计面试转化率)
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add bullet tracking system documentation to CLAUDE.md"
```

---

## Execution Order Summary

| Task | Description | Depends on |
|------|-------------|------------|
| 1 | DB tables: bullet_versions + bullet_usage | — |
| 2 | Analytics view: v_bullet_conversion | 1 |
| 3 | Recording logic in _resolve_bullet_ids | 1, 2 |
| 4 | Add status/tags fields to YAML | — |
| 5 | Restore v3.0 GLP bullets | 4 |
| 6 | Restore v3.0 Baiquan bullets | 4 |
| 7 | Restore v3.0 Ele.me + Deribit | 4 |
| 8 | Backfill historical data | 1, 2, 5-7 |
| 9 | CLI --bullet-analytics | 2 |
| 10 | Update CLAUDE.md | all |

Tasks 1-3 are sequential (tracking infrastructure). Tasks 4-7 are sequential (YAML changes). Task 8 depends on both chains. Tasks 9-10 can run after their deps.
