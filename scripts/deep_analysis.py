#!/usr/bin/env python3
"""
Deep analysis of the job-hunter database.

Produces 9 reports covering the full funnel from scraping through interviews,
with breakdowns by search profile, title pattern, company, time, and query.
"""

import sqlite3
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "jobs.db"


def connect():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def pct(num, denom):
    """Safe percentage formatting."""
    if denom == 0:
        return "  -  "
    return f"{num / denom * 100:5.1f}%"


def divider(title, width=90):
    print()
    print("=" * width)
    print(f"  {title}")
    print("=" * width)


# ---------------------------------------------------------------------------
# Title keyword classifier
# ---------------------------------------------------------------------------
TITLE_BUCKETS = [
    ("Data Engineer", ["data engineer", "big data engineer"]),
    ("ML/AI Engineer", ["machine learning engineer", "ml engineer", "ai engineer",
                        "mlops", "deep learning"]),
    ("Backend/Software Eng", ["software engineer", "backend engineer",
                              "backend developer", "software developer"]),
    ("Quant/Finance", ["quant", "quantitative", "hft", "trading"]),
    ("Data Scientist", ["data scientist", "data science", "data analyst",
                        "data analysis"]),
    ("Research/Evaluation", ["research", "evaluation"]),
    ("DevOps/Infra", ["devops", "infrastructure", "platform engineer", "sre",
                      "cloud engineer"]),
    ("Fullstack", ["fullstack", "full stack", "full-stack"]),
]


def classify_title(title):
    if not title:
        return "Other"
    t = title.lower()
    for bucket, keywords in TITLE_BUCKETS:
        for kw in keywords:
            if kw in t:
                return bucket
    return "Other"


# =========================================================================
# 1. Search Profile -> Interview Conversion
# =========================================================================
def report_profile_conversion(conn):
    divider("1. SEARCH PROFILE -> INTERVIEW CONVERSION")

    cur = conn.cursor()

    # Total scraped per profile
    cur.execute("SELECT search_profile, COUNT(*) FROM jobs GROUP BY search_profile")
    scraped = {r[0] or "(none)": r[1] for r in cur.fetchall()}

    # Passed filter per profile
    cur.execute("""
        SELECT j.search_profile, COUNT(*)
        FROM filter_results f JOIN jobs j ON f.job_id = j.id
        WHERE f.passed = 1
        GROUP BY j.search_profile
    """)
    passed = {r[0] or "(none)": r[1] for r in cur.fetchall()}

    # Applied per profile (status in applied, interview, rejected -- not skipped/pending)
    cur.execute("""
        SELECT j.search_profile, COUNT(*)
        FROM applications a JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interview', 'rejected')
        GROUP BY j.search_profile
    """)
    applied = {r[0] or "(none)": r[1] for r in cur.fetchall()}

    # Interview per profile
    cur.execute("""
        SELECT j.search_profile, COUNT(DISTINCT ir.job_id)
        FROM interview_rounds ir JOIN jobs j ON ir.job_id = j.id
        GROUP BY j.search_profile
    """)
    interviews = {r[0] or "(none)": r[1] for r in cur.fetchall()}

    profiles = sorted(scraped.keys())
    header = f"{'Profile':<22} {'Scraped':>8} {'Filter':>8} {'Filt%':>7} {'Applied':>8} {'Appl%':>7} {'Intrv':>6} {'Intrv%':>7}"
    print(header)
    print("-" * len(header))

    total_s = total_f = total_a = total_i = 0
    for p in profiles:
        s = scraped.get(p, 0)
        f = passed.get(p, 0)
        a = applied.get(p, 0)
        i = interviews.get(p, 0)
        total_s += s
        total_f += f
        total_a += a
        total_i += i
        print(f"{p:<22} {s:>8} {f:>8} {pct(f, s):>7} {a:>8} {pct(a, f):>7} {i:>6} {pct(i, a):>7}")

    print("-" * len(header))
    print(f"{'TOTAL':<22} {total_s:>8} {total_f:>8} {pct(total_f, total_s):>7} {total_a:>8} {pct(total_a, total_f):>7} {total_i:>6} {pct(total_i, total_a):>7}")


# =========================================================================
# 2. Job Title Pattern Analysis
# =========================================================================
def report_title_patterns(conn):
    divider("2. JOB TITLE PATTERN ANALYSIS")

    cur = conn.cursor()

    # All applied jobs with their titles
    cur.execute("""
        SELECT j.title, a.status
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interview', 'rejected')
    """)
    bucket_applied = defaultdict(int)
    bucket_interview = defaultdict(int)
    bucket_rejected = defaultdict(int)
    bucket_no_response = defaultdict(int)

    for r in cur.fetchall():
        bucket = classify_title(r[0])
        bucket_applied[bucket] += 1
        if r[1] == "interview":
            bucket_interview[bucket] += 1
        elif r[1] == "rejected":
            bucket_rejected[bucket] += 1
        elif r[1] == "applied":
            bucket_no_response[bucket] += 1

    # Also count from interview_rounds for precision
    cur.execute("""
        SELECT j.title
        FROM interview_rounds ir JOIN jobs j ON ir.job_id = j.id
        GROUP BY ir.job_id
    """)
    iv_buckets = defaultdict(int)
    for r in cur.fetchall():
        iv_buckets[classify_title(r[0])] += 1

    all_buckets = sorted(set(bucket_applied.keys()) | set(iv_buckets.keys()))

    print(f"\n{'Title Category':<24} {'Applied':>8} {'Intrv':>6} {'Reject':>7} {'Ghost':>7} {'Intrv%':>7} {'Reject%':>8}")
    print("-" * 75)
    for b in all_buckets:
        a = bucket_applied[b]
        i = bucket_interview[b]
        rej = bucket_rejected[b]
        ghost = bucket_no_response[b]
        print(f"{b:<24} {a:>8} {i:>6} {rej:>7} {ghost:>7} {pct(i, a):>7} {pct(rej, a):>8}")

    # Show actual interview job titles
    cur.execute("""
        SELECT j.title, j.company
        FROM interview_rounds ir JOIN jobs j ON ir.job_id = j.id
        GROUP BY ir.job_id
        ORDER BY j.title
    """)
    print(f"\n  Actual interview titles:")
    for r in cur.fetchall():
        print(f"    - {r[0]}  @  {r[1]}")


# =========================================================================
# 3. Company Size/Type Analysis
# =========================================================================
def report_company_analysis(conn):
    divider("3. COMPANY ANALYSIS (Interview Companies)")

    cur = conn.cursor()

    # Companies that gave interviews
    cur.execute("""
        SELECT j.company, j.title, j.source, j.search_profile,
               ir.round_type, ir.status
        FROM interview_rounds ir
        JOIN jobs j ON ir.job_id = j.id
        ORDER BY j.company
    """)
    print(f"\n{'Company':<22} {'Title':<45} {'Source':<12} {'Profile':<18} {'Round':<8} {'Status'}")
    print("-" * 120)
    for r in cur.fetchall():
        print(f"{r[0]:<22} {str(r[1])[:44]:<45} {r[2]:<12} {str(r[3]):<18} {r[4]:<8} {r[5]}")

    # Top companies by application volume (applied+interview+rejected)
    cur.execute("""
        SELECT j.company, COUNT(*) as cnt,
               SUM(CASE WHEN a.status = 'interview' THEN 1 ELSE 0 END) as iv,
               SUM(CASE WHEN a.status = 'rejected' THEN 1 ELSE 0 END) as rej
        FROM applications a JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interview', 'rejected')
        GROUP BY j.company
        ORDER BY cnt DESC
        LIMIT 20
    """)
    print(f"\n  Top 20 companies by application volume:")
    print(f"  {'Company':<30} {'Applied':>8} {'Intrv':>6} {'Reject':>7}")
    print(f"  {'-' * 55}")
    for r in cur.fetchall():
        print(f"  {r[0]:<30} {r[1]:>8} {r[2]:>6} {r[3]:>7}")


# =========================================================================
# 4. Time Analysis
# =========================================================================
def report_time_analysis(conn):
    divider("4. TIME ANALYSIS")

    cur = conn.cursor()

    # Applications by week
    cur.execute("""
        SELECT
            CASE
                WHEN applied_at IS NULL OR applied_at = '' THEN 'unknown'
                ELSE strftime('%Y-W%W', applied_at)
            END as week,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'interview' THEN 1 ELSE 0 END) as iv,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rej,
            SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as pending
        FROM applications
        WHERE status IN ('applied', 'interview', 'rejected')
        GROUP BY week
        ORDER BY week
    """)
    print(f"\n  Applications by week:")
    print(f"  {'Week':<14} {'Applied':>8} {'Intrv':>6} {'Reject':>7} {'Ghost':>7} {'Intrv%':>7}")
    print(f"  {'-' * 55}")
    for r in cur.fetchall():
        print(f"  {r[0]:<14} {r[1]:>8} {r[2]:>6} {r[3]:>7} {r[4]:>7} {pct(r[2], r[1]):>7}")

    # Time to rejection (days between applied_at and response_at)
    cur.execute("""
        SELECT
            CAST(julianday(response_at) - julianday(applied_at) AS INTEGER) as days
        FROM applications
        WHERE status = 'rejected'
          AND applied_at IS NOT NULL AND applied_at != ''
          AND response_at IS NOT NULL AND response_at != ''
    """)
    days_list = [r[0] for r in cur.fetchall() if r[0] is not None and r[0] >= 0]
    if days_list:
        print(f"\n  Time to rejection (days):")
        print(f"    Min: {min(days_list)}, Max: {max(days_list)}, "
              f"Avg: {sum(days_list)/len(days_list):.1f}, "
              f"Median: {sorted(days_list)[len(days_list)//2]}, "
              f"N={len(days_list)}")

    # Interview timeline
    cur.execute("""
        SELECT j.company, j.title, a.applied_at, ir.created_at
        FROM interview_rounds ir
        JOIN jobs j ON ir.job_id = j.id
        LEFT JOIN applications a ON ir.job_id = a.job_id
        GROUP BY ir.job_id
        ORDER BY a.applied_at
    """)
    print(f"\n  Interview timeline:")
    print(f"  {'Applied':<28} {'Company':<22} {'Title':<40}")
    print(f"  {'-' * 90}")
    for r in cur.fetchall():
        applied = str(r[2] or "")[:10]
        print(f"  {applied:<28} {r[0]:<22} {str(r[1])[:39]:<40}")


# =========================================================================
# 5. Rejection Analysis
# =========================================================================
def report_rejection_analysis(conn):
    divider("5. REJECTION ANALYSIS (65 Rejected Applications)")

    cur = conn.cursor()

    # Rejections by profile
    cur.execute("""
        SELECT j.search_profile, COUNT(*) as rej,
               (SELECT COUNT(*) FROM applications a2
                JOIN jobs j2 ON a2.job_id = j2.id
                WHERE j2.search_profile = j.search_profile
                  AND a2.status IN ('applied', 'interview', 'rejected')) as total_applied
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status = 'rejected'
        GROUP BY j.search_profile
        ORDER BY rej DESC
    """)
    print(f"\n  Rejections by search profile:")
    print(f"  {'Profile':<22} {'Rejected':>9} {'TotalApp':>10} {'Reject%':>9}")
    print(f"  {'-' * 55}")
    for r in cur.fetchall():
        print(f"  {str(r[0]):<22} {r[1]:>9} {r[2]:>10} {pct(r[1], r[2]):>9}")

    # Rejections by title bucket
    cur.execute("""
        SELECT j.title, j.company, j.search_profile
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status = 'rejected'
    """)
    rej_by_bucket = defaultdict(int)
    for r in cur.fetchall():
        rej_by_bucket[classify_title(r[0])] += 1

    print(f"\n  Rejections by title category:")
    print(f"  {'Category':<24} {'Rejected':>9}")
    print(f"  {'-' * 35}")
    for bucket, cnt in sorted(rej_by_bucket.items(), key=lambda x: -x[1]):
        print(f"  {bucket:<24} {cnt:>9}")

    # Specific rejected companies
    cur.execute("""
        SELECT j.company, COUNT(*) as cnt
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status = 'rejected'
        GROUP BY j.company
        ORDER BY cnt DESC
        LIMIT 15
    """)
    print(f"\n  Top rejecting companies:")
    print(f"  {'Company':<30} {'Rejections':>10}")
    print(f"  {'-' * 42}")
    for r in cur.fetchall():
        print(f"  {r[0]:<30} {r[1]:>10}")


# =========================================================================
# 6. Filter Funnel by Profile
# =========================================================================
def report_filter_funnel(conn):
    divider("6. FILTER FUNNEL BY PROFILE")

    cur = conn.cursor()

    # Filter pass rate per profile
    cur.execute("""
        SELECT j.search_profile,
               COUNT(*) as total,
               SUM(CASE WHEN f.passed = 1 THEN 1 ELSE 0 END) as passed
        FROM filter_results f
        JOIN jobs j ON f.job_id = j.id
        GROUP BY j.search_profile
    """)
    filter_data = {r[0] or "(none)": (r[1], r[2]) for r in cur.fetchall()}

    # Average rule_score per profile
    cur.execute("""
        SELECT j.search_profile, AVG(s.score), MIN(s.score), MAX(s.score), COUNT(*)
        FROM ai_scores s
        JOIN jobs j ON s.job_id = j.id
        GROUP BY j.search_profile
    """)
    score_data = {r[0] or "(none)": (r[1], r[2], r[3], r[4]) for r in cur.fetchall()}

    # AI-analyzed per profile
    cur.execute("""
        SELECT j.search_profile, COUNT(*)
        FROM job_analysis ja
        JOIN jobs j ON ja.job_id = j.id
        GROUP BY j.search_profile
    """)
    ai_data = {r[0] or "(none)": r[1] for r in cur.fetchall()}

    profiles = sorted(set(filter_data.keys()) | set(score_data.keys()))

    print(f"\n{'Profile':<22} {'Total':>7} {'PassFlt':>8} {'Flt%':>6} {'AvgRule':>8} {'#Scored':>8} {'#AIAnal':>8}")
    print("-" * 75)
    for p in profiles:
        total, passed = filter_data.get(p, (0, 0))
        avg_s, min_s, max_s, cnt_s = score_data.get(p, (0, 0, 0, 0))
        ai = ai_data.get(p, 0)
        print(f"{p:<22} {total:>7} {passed:>8} {pct(passed, total):>6} {avg_s:>8.2f} {cnt_s:>8} {ai:>8}")

    # Top reject reasons per profile
    cur.execute("""
        SELECT j.search_profile, f.reject_reason, COUNT(*) as cnt
        FROM filter_results f
        JOIN jobs j ON f.job_id = j.id
        WHERE f.passed = 0
        GROUP BY j.search_profile, f.reject_reason
        ORDER BY j.search_profile, cnt DESC
    """)
    reasons_by_profile = defaultdict(list)
    for r in cur.fetchall():
        reasons_by_profile[r[0] or "(none)"].append((r[1], r[2]))

    print(f"\n  Top filter rejection reasons by profile:")
    for p in sorted(reasons_by_profile.keys()):
        reasons = reasons_by_profile[p][:3]
        reasons_str = ", ".join(f"{r[0]}({r[1]})" for r in reasons)
        print(f"    {p:<20}: {reasons_str}")


# =========================================================================
# 7. Interview Job Characteristics
# =========================================================================
def report_interview_characteristics(conn):
    divider("7. INTERVIEW JOB CHARACTERISTICS (Scores & Patterns)")

    cur = conn.cursor()

    cur.execute("""
        SELECT j.id, j.title, j.company, j.search_profile,
               s.score as rule_score,
               ja.ai_score, ja.skill_match, ja.experience_fit,
               ja.growth_potential, ja.recommendation
        FROM interview_rounds ir
        JOIN jobs j ON ir.job_id = j.id
        LEFT JOIN ai_scores s ON j.id = s.job_id
        LEFT JOIN job_analysis ja ON j.id = ja.job_id
        GROUP BY ir.job_id
        ORDER BY ja.ai_score DESC
    """)

    rows = cur.fetchall()
    print(f"\n{'Company':<22} {'Title':<36} {'Rule':>6} {'AI':>5} {'Skill':>6} {'ExpFit':>6} {'Growth':>7} {'Rec'}")
    print("-" * 100)

    rule_scores = []
    ai_scores = []
    for r in rows:
        rs = r[4]
        ai = r[5]
        if rs is not None:
            rule_scores.append(rs)
        if ai is not None:
            ai_scores.append(ai)
        print(f"{r[2]:<22} {str(r[1])[:35]:<36} "
              f"{rs if rs is not None else '-':>6} "
              f"{ai if ai is not None else '-':>5} "
              f"{r[6] if r[6] is not None else '-':>6} "
              f"{r[7] if r[7] is not None else '-':>6} "
              f"{r[8] if r[8] is not None else '-':>7} "
              f"{r[9] or '-'}")

    if rule_scores:
        print(f"\n  Rule score stats (interview jobs): "
              f"avg={sum(rule_scores)/len(rule_scores):.2f}, "
              f"min={min(rule_scores):.1f}, max={max(rule_scores):.1f}, n={len(rule_scores)}")
    if ai_scores:
        print(f"  AI score stats (interview jobs):   "
              f"avg={sum(ai_scores)/len(ai_scores):.2f}, "
              f"min={min(ai_scores):.1f}, max={max(ai_scores):.1f}, n={len(ai_scores)}")

    # Compare with overall applied population
    cur.execute("""
        SELECT AVG(s.score), AVG(ja.ai_score)
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        LEFT JOIN ai_scores s ON j.id = s.job_id
        LEFT JOIN job_analysis ja ON j.id = ja.job_id
        WHERE a.status IN ('applied', 'interview', 'rejected')
    """)
    overall = cur.fetchone()
    print(f"\n  Overall applied population: avg_rule={overall[0]:.2f}, avg_ai={overall[1]:.2f}")
    if rule_scores and ai_scores:
        print(f"  Interview uplift:          rule +{sum(rule_scores)/len(rule_scores) - (overall[0] or 0):.2f}, "
              f"ai +{sum(ai_scores)/len(ai_scores) - (overall[1] or 0):.2f}")


# =========================================================================
# 8. Applied but Never Heard Back ("Ghost" Analysis)
# =========================================================================
def report_ghost_analysis(conn):
    divider("8. APPLIED BUT NEVER HEARD BACK (Ghost Applications)")

    cur = conn.cursor()

    # Total applied with status still 'applied' (no interview, no rejection)
    cur.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status = 'applied'
    """)
    ghost_total = cur.fetchone()[0]

    cur.execute("""
        SELECT COUNT(*)
        FROM applications
        WHERE status IN ('applied', 'interview', 'rejected')
    """)
    all_applied = cur.fetchone()[0]

    print(f"\n  Total applied (applied+interview+rejected): {all_applied}")
    print(f"  Still waiting / ghosted (status='applied'):  {ghost_total}")
    print(f"  Ghost rate: {pct(ghost_total, all_applied)}")
    print(f"  Got response (interview+rejected):           {all_applied - ghost_total}")

    # Ghost by profile
    cur.execute("""
        SELECT j.search_profile,
               SUM(CASE WHEN a.status = 'applied' THEN 1 ELSE 0 END) as ghost,
               COUNT(*) as total
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interview', 'rejected')
        GROUP BY j.search_profile
        ORDER BY ghost DESC
    """)
    print(f"\n  {'Profile':<22} {'Ghost':>7} {'Total':>7} {'Ghost%':>8}")
    print(f"  {'-' * 48}")
    for r in cur.fetchall():
        print(f"  {str(r[0]):<22} {r[1]:>7} {r[2]:>7} {pct(r[1], r[2]):>8}")

    # Ghost by title category
    cur.execute("""
        SELECT j.title, a.status
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interview', 'rejected')
    """)
    ghost_bucket = defaultdict(int)
    total_bucket = defaultdict(int)
    for r in cur.fetchall():
        b = classify_title(r[0])
        total_bucket[b] += 1
        if r[1] == "applied":
            ghost_bucket[b] += 1

    print(f"\n  {'Title Category':<24} {'Ghost':>7} {'Total':>7} {'Ghost%':>8}")
    print(f"  {'-' * 50}")
    for b in sorted(total_bucket.keys(), key=lambda x: -ghost_bucket.get(x, 0)):
        print(f"  {b:<24} {ghost_bucket.get(b, 0):>7} {total_bucket[b]:>7} {pct(ghost_bucket.get(b, 0), total_bucket[b]):>8}")

    # How old are ghost applications?
    cur.execute("""
        SELECT
            CAST(julianday('now') - julianday(applied_at) AS INTEGER) as days_ago
        FROM applications
        WHERE status = 'applied'
          AND applied_at IS NOT NULL AND applied_at != ''
        ORDER BY applied_at
    """)
    ages = [r[0] for r in cur.fetchall() if r[0] is not None]
    if ages:
        print(f"\n  Ghost application age (days since applied):")
        print(f"    Oldest: {max(ages)} days, Newest: {min(ages)} days, "
              f"Avg: {sum(ages)/len(ages):.0f} days, N={len(ages)}")
        buckets_age = {"< 7 days": 0, "7-14 days": 0, "14-21 days": 0, "21-30 days": 0, "> 30 days": 0}
        for d in ages:
            if d < 7:
                buckets_age["< 7 days"] += 1
            elif d < 14:
                buckets_age["7-14 days"] += 1
            elif d < 21:
                buckets_age["14-21 days"] += 1
            elif d <= 30:
                buckets_age["21-30 days"] += 1
            else:
                buckets_age["> 30 days"] += 1
        print(f"    {'Age Range':<14} {'Count':>6}")
        for k, v in buckets_age.items():
            print(f"    {k:<14} {v:>6}")


# =========================================================================
# 9. Search Query Efficiency
# =========================================================================
def report_query_efficiency(conn):
    divider("9. SEARCH QUERY EFFICIENCY (Signal vs Noise)")

    cur = conn.cursor()

    # For each search_query: scraped, passed filter, applied, interview
    cur.execute("""
        SELECT j.search_query,
               COUNT(DISTINCT j.id) as scraped,
               SUM(CASE WHEN f.passed = 1 THEN 1 ELSE 0 END) as passed,
               0, 0
        FROM jobs j
        LEFT JOIN filter_results f ON j.id = f.job_id
        GROUP BY j.search_query
        ORDER BY scraped DESC
    """)
    query_base = {}
    for r in cur.fetchall():
        q = r[0] or "(none)"
        query_base[q] = {"scraped": r[1], "passed": r[2], "applied": 0, "interview": 0}

    # Applied per query
    cur.execute("""
        SELECT j.search_query, COUNT(*)
        FROM applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status IN ('applied', 'interview', 'rejected')
        GROUP BY j.search_query
    """)
    for r in cur.fetchall():
        q = r[0] or "(none)"
        if q in query_base:
            query_base[q]["applied"] = r[1]

    # Interview per query
    cur.execute("""
        SELECT j.search_query, COUNT(DISTINCT ir.job_id)
        FROM interview_rounds ir
        JOIN jobs j ON ir.job_id = j.id
        GROUP BY j.search_query
    """)
    for r in cur.fetchall():
        q = r[0] or "(none)"
        if q in query_base:
            query_base[q]["interview"] = r[1]

    # Sort by scraped desc
    sorted_queries = sorted(query_base.items(), key=lambda x: -x[1]["scraped"])

    print(f"\n{'Query':<30} {'Scraped':>8} {'PassFlt':>8} {'Flt%':>6} {'Applied':>8} {'Appl%':>7} {'Intrv':>6} {'Signal':>7}")
    print("-" * 95)
    for q, d in sorted_queries:
        label = q[:29]
        signal = pct(d["applied"], d["scraped"])  # apply rate from total scraped
        print(f"{label:<30} {d['scraped']:>8} {d['passed']:>8} {pct(d['passed'], d['scraped']):>6} "
              f"{d['applied']:>8} {pct(d['applied'], d['passed']):>7} {d['interview']:>6} {signal:>7}")

    # Rank by signal (apply rate from scraped)
    print(f"\n  Ranked by Signal (apply rate from total scraped):")
    ranked = [(q, d) for q, d in sorted_queries if d["scraped"] >= 10]
    ranked.sort(key=lambda x: x[1]["applied"] / max(x[1]["scraped"], 1), reverse=True)
    print(f"  {'Query':<30} {'Scraped':>8} {'Applied':>8} {'Signal%':>8}")
    print(f"  {'-' * 58}")
    for q, d in ranked[:15]:
        print(f"  {q[:29]:<30} {d['scraped']:>8} {d['applied']:>8} {pct(d['applied'], d['scraped']):>8}")

    # Noisiest queries (most scraped, fewest applied)
    print(f"\n  Noisiest queries (high scrape, low apply):")
    ranked_noise = [(q, d) for q, d in sorted_queries if d["scraped"] >= 10]
    ranked_noise.sort(key=lambda x: x[1]["applied"] / max(x[1]["scraped"], 1))
    print(f"  {'Query':<30} {'Scraped':>8} {'Applied':>8} {'Signal%':>8}")
    print(f"  {'-' * 58}")
    for q, d in ranked_noise[:10]:
        print(f"  {q[:29]:<30} {d['scraped']:>8} {d['applied']:>8} {pct(d['applied'], d['scraped']):>8}")


# =========================================================================
# Summary
# =========================================================================
def report_summary(conn):
    divider("EXECUTIVE SUMMARY")
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM jobs")
    total_jobs = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM filter_results WHERE passed = 1")
    passed = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status IN ('applied','interview','rejected')")
    applied = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'interview'")
    interviews = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'rejected'")
    rejected = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM applications WHERE status = 'applied'")
    ghost = cur.fetchone()[0]
    cur.execute("SELECT COUNT(DISTINCT job_id) FROM interview_rounds")
    iv_confirmed = cur.fetchone()[0]

    print(f"""
  Total jobs scraped:       {total_jobs:>6}
  Passed hard filter:       {passed:>6}  ({pct(passed, total_jobs).strip()} of scraped)
  Applied (real):           {applied:>6}  ({pct(applied, passed).strip()} of passed)
  Interviews (confirmed):   {iv_confirmed:>6}  ({pct(iv_confirmed, applied).strip()} of applied)
  Rejected:                 {rejected:>6}  ({pct(rejected, applied).strip()} of applied)
  Ghosted (no response):    {ghost:>6}  ({pct(ghost, applied).strip()} of applied)

  Overall funnel:  {total_jobs} scraped -> {passed} filtered -> {applied} applied -> {iv_confirmed} interviews
  End-to-end rate: {pct(iv_confirmed, total_jobs).strip()} (scraped to interview)
""")


# =========================================================================
# Main
# =========================================================================
def main():
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)

    conn = connect()
    try:
        report_summary(conn)
        report_profile_conversion(conn)
        report_title_patterns(conn)
        report_company_analysis(conn)
        report_time_analysis(conn)
        report_rejection_analysis(conn)
        report_filter_funnel(conn)
        report_interview_characteristics(conn)
        report_ghost_analysis(conn)
        report_query_efficiency(conn)
    finally:
        conn.close()

    print(f"\n{'=' * 90}")
    print("  Analysis complete.")
    print(f"{'=' * 90}")


if __name__ == "__main__":
    main()
