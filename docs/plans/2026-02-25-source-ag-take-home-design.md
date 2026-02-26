# Source.ag Data Engineering Take-Home — Design Plan

**Date**: 2026-02-25
**Assignment**: Greenhouse Sensor Data Pipeline (ETL/ELT)
**Source**: https://github.com/source-ag/assignment-data-engineering/blob/main/assignment.md
**Sample Data**: https://drive.google.com/drive/folders/1TV20EVuxcmaqro7e0HfmX2j6HtILNwXB?usp=sharing
**Timebox**: ~4 hours (deadline: 1 week)
**Deliverable**: `.git bundle` via email
**Status**: Design approved, ready to execute

---

## Assignment Summary

Build an ETL/ELT pipeline for greenhouse sensor monitoring data. Input is JSON files with sensor readings (timestamps, sensor IDs, parameter types: temperature/humidity/CO2/light, measured values).

### 6 Core Requirements

1. **Data Ingestion** — JSON batch loading, idempotent, incremental
2. **Data Quality & Validation** — Completeness, validity, consistency, duplicates, anomalies
3. **Transformation & Aggregation** — Raw layer + 15-min/hourly aggregations + daily derived metrics
4. **Data Modeling** — Dimensional modeling with justification, partitioning, indexing, extensibility
5. **Analytical Queries** — 5 specific SQL/DataFrame queries
6. **Pipeline Orchestration & Testing** — Single command E2E, comprehensive tests

### Deliverable: README.md with
- Setup + runtime instructions
- Testing procedures
- Architecture overview
- Data quality approach
- Assumptions and trade-offs
- 3-month roadmap (SCD, retention, monitoring, billion-row optimization)

### Scale Design Target
1,000 greenhouses x 50 sensors @ 1-minute resolution = 72M readings/day

---

## Strategic Advantage (Experience Mapping)

| Assignment Need | Direct Experience |
|---|---|
| JSON ingestion + idempotency | Auto Loader in Financial Data Lakehouse |
| Data quality framework | GLP quarantine-and-replay pattern |
| Medallion Architecture | Financial Data Lakehouse project |
| Time-series aggregations | Baiquan 3,000+ securities pipeline |
| Sensor data domain | Financial tick data (structurally identical) |
| Scale design (72M rows/day) | PySpark processing millions of records |

---

## Architecture Decision: DuckDB + Python CLI

**Chosen over**: Dagster, dbt + Dagster (over-engineering risk for a 4-hour timebox)

**Why DuckDB**:
- Columnar engine = fast aggregations on sensor data
- SQL-native, reads JSON/Parquet natively
- Zero infrastructure (no Docker/server needed)
- Handles 72M rows/day on a single machine
- Perfect for analytical workload

**Why Medallion naming**: Aligns with resume (Financial Data Lakehouse) AND Source.ag's Databricks stack.

---

## Architecture: Medallion Pattern

```
JSON files
    |
+---------------------------------------------+
|  BRONZE (Raw)                               |
|  fact_raw_readings - minimal transform      |
|  processing_log - idempotency tracking      |
+----------------------+----------------------+
                       | validate
+---------------------------------------------+
|  SILVER (Validated)                         |
|  fact_readings - cleaned, deduplicated,     |
|                  quality_flag attached       |
|  data_quality_log - all check results       |
+----------------------+----------------------+
                       | aggregate
+---------------------------------------------+
|  GOLD (Analytics-Ready)                     |
|  agg_readings_15min - min/max/avg/stddev    |
|  agg_readings_hourly - min/max/avg/stddev   |
|  agg_daily_metrics - derived (temp range)   |
|  dim_sensor - sensor metadata               |
|  dim_greenhouse - greenhouse metadata       |
+---------------------------------------------+
```

---

## Data Model (Star Schema)

```sql
-- Tracking
processing_log (
    file_name VARCHAR,
    file_hash VARCHAR,
    processed_at TIMESTAMP,
    batch_id VARCHAR,
    record_count INTEGER
)

-- Dimensions
dim_greenhouse (
    greenhouse_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    location VARCHAR,
    timezone VARCHAR
)

dim_sensor (
    sensor_id VARCHAR PRIMARY KEY,
    greenhouse_id VARCHAR REFERENCES dim_greenhouse,
    parameter_type VARCHAR,
    unit VARCHAR,
    installed_at TIMESTAMP
)

-- Bronze
fact_raw_readings (
    id INTEGER PRIMARY KEY,
    sensor_id VARCHAR,
    greenhouse_id VARCHAR,
    timestamp TIMESTAMP,
    parameter VARCHAR,
    value DOUBLE,
    source_file VARCHAR,
    batch_id VARCHAR
)

-- Silver
fact_readings (
    id INTEGER PRIMARY KEY,
    sensor_id VARCHAR,
    greenhouse_id VARCHAR,
    timestamp TIMESTAMP,
    parameter VARCHAR,
    value DOUBLE,
    quality_flag VARCHAR,  -- NULL=clean, 'anomaly', 'invalid', 'duplicate'
    batch_id VARCHAR
)

-- Quality log
data_quality_log (
    check_id VARCHAR,
    check_type VARCHAR,  -- completeness/validity/consistency/duplicate/anomaly
    sensor_id VARCHAR,
    timestamp TIMESTAMP,
    severity VARCHAR,    -- warning/error
    description VARCHAR,
    batch_id VARCHAR
)

-- Gold: Aggregations
agg_readings_15min (
    sensor_id VARCHAR,
    greenhouse_id VARCHAR,
    parameter VARCHAR,
    period_start TIMESTAMP,
    min_val DOUBLE,
    max_val DOUBLE,
    avg_val DOUBLE,
    stddev_val DOUBLE,
    reading_count INTEGER
)

agg_readings_hourly (same structure as 15min)

agg_daily_metrics (
    greenhouse_id VARCHAR,
    parameter VARCHAR,
    date DATE,
    daily_min DOUBLE,
    daily_max DOUBLE,
    daily_avg DOUBLE,
    daily_range DOUBLE,  -- max - min
    missing_pct DOUBLE,
    anomaly_count INTEGER
)
```

**Schema extensibility**: New sensor types (e.g., soil moisture) = new row in `dim_sensor` with new `parameter_type`. No schema changes needed. EAV-like `parameter` column is intentional.

---

## Data Quality Framework

5 validation classes, each writes to `data_quality_log`:

| Check | Logic | Severity |
|---|---|---|
| **Completeness** | Detect timestamp gaps per sensor (expected 1-min interval) | warning |
| **Validity** | Range checks: temp [-50, 70]C, humidity [0, 100]%, CO2 [0, 5000]ppm, light [0, 200000] lux | error |
| **Consistency** | Rate-of-change: >10C in 1 min = sensor malfunction | warning |
| **Duplicates** | Same sensor + same timestamp -> keep first occurrence | warning |
| **Anomalies** | IQR-based: value outside Q1-1.5*IQR to Q3+1.5*IQR | warning |

**Key principle**: "Mark outliers for review without halting pipeline" — flagged readings get `quality_flag` in Silver but are **never dropped**. Gold aggregations exclude `quality_flag = 'invalid'` but include `'anomaly'` (might be real extreme greenhouse events).

---

## Idempotency & Incremental Processing

- **First run**: Process all files, record file hashes in `processing_log`
- **Re-run same files**: Skip (hash match) = idempotent
- **New files added**: Only process new files (hash not in log) = incremental
- **Reprocess**: `--reprocess` flag = DELETE cascade by batch_id + re-ingest

---

## 5 Analytical Queries

1. **Average temperature per day (past 7 days)** — GROUP BY on fact_readings WHERE quality_flag IS NULL OR quality_flag = 'anomaly'
2. **Days with highest temperature variance** — stddev from agg_daily_metrics ORDER BY daily_range DESC
3. **Percentage of missing sensor readings daily** — expected readings (1440/sensor/day) vs actual count
4. **24-hour time-series of temperature and humidity** — hourly agg with parameter pivot
5. **Top 3 anomalous readings with explanations** — JOIN data_quality_log with fact_readings, include check description

---

## Project Structure

```
greenhouse-sensor-pipeline/
├── README.md                  # Setup, architecture, decisions, roadmap
├── pyproject.toml             # Dependencies (duckdb, click, pytest)
├── Makefile                   # make run, make test, make lint
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Validation thresholds, paths, constants
│   ├── database.py            # DuckDB connection, schema creation
│   ├── ingest.py              # Bronze: JSON -> fact_raw_readings
│   ├── validate.py            # Quality checks -> data_quality_log
│   ├── transform.py           # Silver: clean + deduplicate + flag
│   ├── aggregate.py           # Gold: 15-min, hourly, daily
│   └── analytics.py           # 5 analytical queries
│
├── tests/
│   ├── conftest.py            # In-memory DuckDB, synthetic fixtures
│   ├── test_ingest.py
│   ├── test_validate.py
│   ├── test_transform.py
│   ├── test_aggregate.py
│   └── test_analytics.py
│
├── data/
│   └── raw/                   # Input JSON files (gitignored)
│
└── pipeline.py                # CLI entry (click): run/ingest/validate/...
```

---

## CLI Interface

```bash
# Full pipeline (single command - assignment requirement)
python pipeline.py run --data-dir data/raw/

# Individual stages
python pipeline.py ingest --data-dir data/raw/
python pipeline.py validate
python pipeline.py transform
python pipeline.py aggregate

# Analytical queries
python pipeline.py query --all
python pipeline.py query --name avg_temp_7d

# Incremental mode
python pipeline.py run --data-dir data/raw/ --incremental

# Reprocess (force re-run)
python pipeline.py run --data-dir data/raw/ --reprocess
```

---

## Testing Strategy

- **Unit tests**: Each module independently with synthetic data fixtures
- **Integration test**: End-to-end pipeline with sample data
- **Edge cases**: Empty files, duplicate timestamps, all-null readings, extreme values, single-sensor files
- **Isolation**: pytest fixtures create in-memory DuckDB per test

---

## Git Commit Strategy

Clean history telling a story:

1. `chore: project scaffold and DuckDB schema`
2. `feat: JSON ingestion with idempotency tracking`
3. `feat: data quality validation framework (5 checks)`
4. `feat: Silver layer transformation and deduplication`
5. `feat: Gold layer aggregations (15-min, hourly, daily)`
6. `feat: dimensional model and 5 analytical queries`
7. `feat: CLI orchestration with click`
8. `test: comprehensive test suite`
9. `docs: README with architecture, decisions, and roadmap`

---

## 3-Month Roadmap (for README)

1. **SCD Type 2**: Track sensor relocations/recalibrations with effective_from/effective_to in dim_sensor
2. **Data retention**: Hot (30d DuckDB) -> Warm (90d Parquet) -> Cold (S3 Glacier)
3. **Monitoring**: Data freshness alerts, quality score trending, anomaly rate dashboards
4. **Billion-row optimization**: Partitioned Parquet on S3, DuckDB external tables, or migrate to Spark/Databricks

---

## Execution Plan

| Step | Est. Time | Deliverable |
|---|---|---|
| 0. Setup | 15 min | Download data, inspect JSON schema, init project |
| 1. Ingestion | 30 min | Bronze layer + idempotency |
| 2. Quality | 45 min | 5 validators + quality log |
| 3. Transform | 30 min | Silver layer + dedup |
| 4. Aggregate | 30 min | Gold: 15-min, hourly, daily |
| 5. Queries | 30 min | 5 analytical queries |
| 6. CLI | 20 min | click CLI + Makefile |
| 7. Tests | 40 min | Unit + integration |
| 8. README | 30 min | Architecture, decisions, roadmap |
| **Total** | **~4.5h** | |

---

## First Step When Resuming

1. Download sample data from Google Drive
2. Inspect JSON schema (field names, nesting, data types)
3. Adjust data model if needed based on actual schema
4. Begin Step 0 (project scaffold)
