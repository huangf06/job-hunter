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
sys.stdout.reconfigure(encoding="utf-8")
from src.db.job_db import JobDatabase


def load_known_bullets() -> dict:
    """Load bullet texts from v3.0 (hardcoded) + current YAML.

    Returns dict mapping content_text -> (bullet_id, library_version).
    """
    bullets = {}

    v3_bullets = {
        "glp_founding_member": "Spearheaded credit scoring infrastructure as the first data hire at a consumer lending startup — owned the full ML lifecycle from data ingestion through feature engineering, model deployment (logistic regression scorecards), and portfolio monitoring, enabling automated credit decisions.",
        "glp_pyspark": "Designed and implemented PySpark ETL pipelines processing consumer credit data across the full loan lifecycle — from application ingestion through repayment tracking; provided technical mentorship to junior analyst on distributed data processing patterns.",
        "glp_data_quality": "Engineered automated data pipeline and quality framework for consumer lending operations, implementing schema validation and integrity checks across loan origination and repayment flows — ensuring clean inputs for credit scoring models.",
        "glp_portfolio_monitoring": "Built portfolio risk monitoring system tracking delinquency rates, repayment trends, and early warning indicators across the consumer loan book; insights directly informed collection strategy adjustments, reducing exposure to deteriorating segments.",
        "glp_data_compliance": "Established compliance reporting framework for consumer lending operations, automating regulatory submissions and audit trail generation for credit decisioning outputs.",
        "glp_payment_collections": "Integrated payment gateway APIs for automated repayment processing; designed tiered collection policies based on delinquency severity, bridging data insights with operational execution.",
        "glp_decision_engine": "Engineered the core decision engine: 29 rejection rules across 4 risk dimensions, 36-segment borrower classification, and an early-delinquency scorecard combining 19 weighted features for first-payment default prediction.",
        "glp_data_engineer": "Built the complete data infrastructure: daily ETL of 30+ production tables into AWS Redshift, credit bureau report parser transforming nested JSON into analytical tables, and compliance reporting automation.",
        "glp_generalist": "Collaborated across risk, product, and operations teams; managed outsourced development partners and coordinated third-party vendor integrations.",
        "bq_de_pipeline": "Built automated market data ingestion pipeline integrating multiple vendor feeds (Wind, Tushare) for 3,000+ A-share securities; implemented corporate action adjustments (splits, dividends, suspensions) ensuring clean inputs for downstream factor research.",
        "bq_de_factor_engine": "Engineered high-performance factor computation engine using vectorized NumPy/Pandas operations, computing technical and fundamental indicators across 3,000+ stocks daily — enabling rapid iteration cycles in alpha research.",
        "bq_de_backtest_infra": "Architected event-driven backtesting framework supporting strategy simulation, walk-forward validation, and performance attribution — adopted as core research infrastructure by the investment team.",
        "bq_factor_research": "Built systematic alpha research pipeline covering 3,000+ A-share equities; applied Fama-MacBeth regression to validate multi-factor models (value, momentum, money flow, event-driven) — validated factors integrated into the fund's live portfolio.",
        "bq_futures_strategy": "Developed and deployed R-Breaker intraday trading strategy for CSI index futures from research through live production — achieved 14.6% annualized return with real capital.",
        "bq_data_quality": "Designed cross-source data validation framework detecting vendor data gaps and inconsistencies in market feeds; built automated alerting for missing trading days and stale prices, safeguarding research pipeline integrity.",
        "eleme_ab_testing": "Developed user segmentation model achieving 2x improvement in churned-user reactivation rate via A/B testing; optimized Hadoop/Hive SQL queries for cross-functional reporting, cutting turnaround time by 30% during the platform’s hyper-growth phase.",
        "eleme_user_segmentation": "Engineered K-means clustering pipeline on Hadoop/Hive to segment millions of users by behavioral patterns (order frequency, recency, category preferences); delivered actionable customer profiles adopted by product and marketing teams for personalized campaign targeting.",
        "eleme_sql_reporting": "Optimized complex SQL queries on Hadoop/Hive for cross-functional stakeholders, cutting reporting turnaround time by 30%.",
        "eleme_fraud_detection": "Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern algorithms (same-phone, high-frequency, repeat-order matching), preventing fraudulent subsidy claims during hyper-growth.",
        "he_data_automation": "Built automated pipeline to ingest, validate, and consolidate non-standardized Excel reports from 20+ business units into unified operational reporting, reducing monthly processing from 2 days to under 2 hours.",
        "he_supply_chain_analytics": "Designed the group's supply chain analytics framework from scratch, tracking daily sales and inventory to guide procurement and sales timing; optimization guided by this framework contributed to €32M in documented profit improvements across business units over 3 years.",
        "he_data_quality": "Established data quality framework and validation rules for multi-source data ingestion, implementing anomaly detection to catch errors, non-standard formats, and data fabrication — built feedback loops to production teams for continuous improvement.",
        "indie_quant_research": "Built automated equity research pipeline processing 83K+ daily records across 3,600+ stocks via Tushare API and MySQL; implemented institutional flow tracking and momentum signal detection for systematic market analysis.",
        "indie_skill_development": "Self-directed study in data science and machine learning, pivoting to AI after the emergence of large language models; admitted to M.Sc. AI program at VU Amsterdam in 2023.",
    }

    v3_projects = {
        "lakehouse_streaming": "Architected end-to-end data lakehouse on Databricks processing real-time financial market feeds via Auto Loader and Structured Streaming; implemented schema evolution and checkpoint-based fault tolerance ensuring zero data loss during upstream changes.",
        "lakehouse_quality": "Engineered data quality framework with quarantine-and-replay pattern isolating malformed records across Bronze/Silver/Gold Medallion Architecture layers — achieving automated recovery without manual intervention.",
        "lakehouse_optimization": "Optimized Delta Lake storage via Z-ordering and compaction, reducing query latency for downstream analysis.",
        "lakehouse_orchestration": "Integrated Airflow for orchestration and Docker for consistent deployment across environments.",
        "thesis_uq_framework": "Developed RL-UQ-Bench, a benchmarking framework evaluating 5 uncertainty quantification methods for Deep RL across 150+ training runs on HPC (SLURM); demonstrated QR-DQN superiority with 31% lower CRPS (p < 0.001) over ensemble and dropout baselines.",
        "thesis_noise_paradox": "Discovered a 'noise paradox' where moderate observation noise unexpectedly improves ensemble-based uncertainty estimates; designed 6-stage reproducible evaluation pipeline with automated calibration benchmarking across multiple RL environments.",
        "thesis_calibration": "Applied temperature scaling and Bayesian methods to calibrate agent confidence; evaluated post-hoc calibration impact across distributional, ensemble, and dropout-based UQ approaches with rigorous statistical testing.",
        "deribit_options_system": "Architected automated options trading system featuring self-implemented Black-Scholes pricing engine (full Greeks, IV solver), edge-based market-making strategy, and multi-layered risk management (position limits, Greeks constraints, drawdown control); currently in paper-trading validation.",
        "deribit_risk_management": "Designed risk management framework enforcing portfolio-level constraints (delta, gamma, vega limits), per-trade stop-loss, daily loss caps, and maximum drawdown controls; implemented Kelly-inspired position sizing adjusted for implied volatility.",
        "expedia_ltr": "Developed hotel recommendation system using learning-to-rank models (LightGBM, XGBoost+SVD) on 4.9M search records; engineered temporal, behavioral, and user-preference features for ranking optimization; achieved NDCG@5 = 0.392, placing top 5% in Kaggle competition.",
        "lifeos_system": "Architected personal productivity platform orchestrating 5 external services (Todoist, Notion, Eudic, Telegram, Logseq) with automated daily workflows via GitHub Actions; built end-to-end vocabulary pipeline: dictionary sync, flashcard generation (genanki), and mobile delivery via Telegram Bot API.",
        "job_hunter_system": "Built end-to-end job application pipeline leveraging LLM APIs (Claude) for resume personalization; designed multi-stage processing (web scraping via Playwright, rule-based filtering, AI scoring, Jinja2 template rendering to PDF) with SQLite backend, YAML-driven configuration, and configurable quality gates.",
        "nlp_poem_generator": "Developed LLM-powered text generation application leveraging GPT-2 and Hugging Face Transformers; implemented prompt engineering with controllable style parameters and deployed as interactive web application via Flask.",
    }

    for bid, content in {**v3_bullets, **v3_projects}.items():
        bullets[content] = (bid, "v3.0")

    # Also load current v6.0 bullets from YAML
    lib_path = Path(__file__).parent.parent / "assets" / "bullet_library.yaml"
    with open(lib_path, encoding="utf-8") as f:
        lib = yaml.safe_load(f)

    for section_key in ("work_experience", "projects"):
        section = lib.get(section_key, {})
        if not isinstance(section, dict):
            continue
        for entry in section.values():
            if not isinstance(entry, dict):
                continue
            for b in entry.get("verified_bullets", []):
                content = b.get("content", "")
                bid = b.get("id", "")
                if content and bid and content not in bullets:
                    bullets[content] = (bid, "v6.0")

    return bullets


def fuzzy_match(text, known_bullets):
    """Try exact match first, then normalized match, then prefix match."""
    if text in known_bullets:
        return known_bullets[text]

    normalized = text.replace("—", "-").replace("–", "-").replace("’", "'").strip()
    for known_text, (bid, ver) in known_bullets.items():
        known_norm = known_text.replace("—", "-").replace("–", "-").replace("’", "'").strip()
        if normalized == known_norm:
            return (bid, ver)

    prefix = text[:80]
    for known_text, (bid, ver) in known_bullets.items():
        if known_text[:80] == prefix:
            return (bid, ver)

    return None


def main():
    db = JobDatabase()
    known = load_known_bullets()
    print(f"Loaded {len(known)} known bullet texts (v3.0 + v6.0)")

    interview_jobs = db.execute("SELECT DISTINCT job_id FROM interview_rounds")
    extra_ids = ["ebf72b62b510", "5f98d1f79e7b"]  # Aon, Barak
    job_ids = list(set([r["job_id"] for r in interview_jobs] + extra_ids))

    # Also add Aon + Barak to interview_rounds if not present
    for jid in extra_ids:
        existing = db.execute(
            "SELECT 1 FROM interview_rounds WHERE job_id = ?", (jid,)
        )
        if not existing:
            db.execute(
                "INSERT INTO interview_rounds (id, job_id, round_number, round_type, status) VALUES (?, ?, 1, 'hr', 'completed')",
                (str(uuid.uuid4())[:8], jid),
            )
            rows = db.execute("SELECT company FROM jobs WHERE id = ?", (jid,))
            name = rows[0]["company"] if rows else jid
            print(f"  Added interview_rounds for {name}")

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

        try:
            resume = json.loads(rows[0]["tailored_resume"])
        except (json.JSONDecodeError, TypeError):
            continue

        if not isinstance(resume, dict):
            continue

        company = rows[0]["company"]
        print(f"\n  {company} ({jid[:8]}):")

        position = 0
        for exp in resume.get("experiences", []):
            for bullet_text in exp.get("bullets", []):
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

    rows = db.execute(
        "SELECT * FROM v_bullet_conversion ORDER BY interview_rate DESC, times_used DESC"
    )
    if rows:
        print("\n=== Bullet Conversion Rates ===")
        print(f"{'Bullet ID':<30} {'Version':<8} {'Used':>5} {'Interview':>10} {'Rate':>6}")
        print("-" * 65)
        for r in rows:
            print(
                f"{r['bullet_id']:<30} {r['library_version'] or '?':<8} {r['times_used']:>5} {r['times_got_interview']:>10} {r['interview_rate']:>5.1f}%"
            )


if __name__ == "__main__":
    main()
