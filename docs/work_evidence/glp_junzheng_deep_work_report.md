# GLP Technology / 君正小贷 — Deep Work Evidence Report

**Created:** 2026-03-09
**Purpose:** Permanent reference for resume bullet writing. Contains ALL technical details extracted from original work files so future sessions never need to re-read the source material.
**Source files:** `C:\Users\huang\Downloads\2017-君正小贷\` (~28,000 files) + `C:\Users\huang\Downloads\GLP\`

---

## Table of Contents

1. [Timeline & Company Context](#1-timeline--company-context)
2. [Team & Organization](#2-team--organization)
3. [Technical Stack](#3-technical-stack)
4. [Project 1: Risk Decision Engine 3.0](#4-project-1-risk-decision-engine-30)
5. [Project 2: PBOC Credit Report Data Mart](#5-project-2-pboc-credit-report-data-mart)
6. [Project 3: AWS S3 Data Pipeline](#6-project-3-aws-s3-data-pipeline)
7. [Project 4: Application Wide Table](#7-project-4-application-wide-table)
8. [Project 5: Airflow Orchestration](#8-project-5-airflow-orchestration)
9. [Project 6: Tongdun First-Repayment Warning](#9-project-6-tongdun-first-repayment-warning)
10. [Project 7: K8s Log Parsing (Face Recognition + Risk Decision)](#10-project-7-k8s-log-parsing)
11. [Project 8: Data Freshness Monitoring](#11-project-8-data-freshness-monitoring)
12. [Project 9: Operator Action Monitoring](#12-project-9-operator-action-monitoring)
13. [Project 10: PBOC Report Validation Engine](#13-project-10-pboc-report-validation-engine)
14. [Project 11: Monte Carlo Portfolio Simulation](#14-project-11-monte-carlo-portfolio-simulation)
15. [Project 12: PBOC Typing Time Tracker](#15-project-12-pboc-typing-time-tracker)
16. [GLP/Prologis Phase](#16-glpprologis-phase)
17. [Resume Integration Notes](#17-resume-integration-notes)
18. [Full Directory Tree](#18-full-directory-tree)

---

## 1. Timeline & Company Context

### Junzheng Microloan (君正小贷/君正网贷)

- **Full name:** 内蒙古君正小贷 (Inner Mongolia Junzheng Microloan)
- **Location:** Shanghai, China (operations)
- **Business:** Consumer lending — personal unsecured credit loans to homeowners
- **Target customer:** Individuals with 1-2 outstanding mortgage loans, credit card history >= 12 months
- **Loan process:** Multi-stage human review pipeline:
  Registration → ID verification → Document check → Risk decision (automated) → Phone check → Branch booking → Site check → Loan disbursement
- **Candidate's tenure:** ~May 2017 - ~end 2018 (~1.5 years)
- **Candidate was the first employee hired**, but the boss brought 4 people: 1 risk control lead (candidate reported to them), 2 risk analysts at same level as candidate

### GLP Technology (普洛斯)

- **Full name:** GLP / Global Logistic Properties
- **Business:** Supply chain finance — providing mortgage and credit loans to companies and individuals in the logistics ecosystem
- **3 loan products:**
  - 普易租 (Pu Yi Zu) — Leasing product (client: 佛朗斯/Frans)
  - 普货贷 (Pu Huo Dai) — Cargo/goods loan (client: 凯东源/Kaidongyuan)
  - 普运贷 (Pu Yun Dai) — Transportation loan (client: 车满满/Chemanman + 运立方/Yunlifang + 域普/Yupu)
- **Candidate's role:** Senior Data Modeling Engineer
- **Main work:** Data modeling and risk rule design (NOT infrastructure — didn't mainly participate in infrastructure)
- **Team:** Managed/directed teams from 3 consulting companies
- **Candidate's tenure:** ~early 2019 - Aug 2019

### Resume Presentation

On resume: merged as **"GLP Technology, Jul 2017 - Aug 2019"** — one entry covering both companies. Bullets primarily reflect 君正小贷 work (the highlight), with GLP work integrated for PySpark and team management aspects.

---

## 2. Team & Organization

### Junzheng Team (from code authorship and deployment docs)

| Person | Email | Role | Evidence |
|--------|-------|------|----------|
| **Huang Fei (黄飞)** | huangfei@junzhengloan.com | Primary risk data engineer/analyst | `@author: huang` on most code; Airflow DAG owner |
| **Zhang Jun (张俊, "Euler")** | zhangjun@junzhengloan.com | Colleague, contributed PBOC parsing & reports | Email recipient on some DAGs; authored `rp_daily_news`, `rp_personal_image` |
| **Yao Wei (姚伟)** | yaowei@junzhengloan.com | Manager/supervisor (CTO?) | Received critical data freshness alerts |
| **Cheng Yue (程樾)** | — | Contributed case analysis | Found in case analysis files |
| **Xiao Lin (小林)** | — | Mentioned in PBOC data mart design | Referenced in design docs |
| **Fujitsu (富士通)** | — | Outsourced development partner | Billing records found |
| **Huadao (华道)** | — | Outsourced data entry operations | PBOC report typing/digitization |

### GLP Team (from weekly report, week of March 11-15, 2019)

| Person | Section Lead | Primary Client | Work |
|--------|-------------|---------------|------|
| **吴邦 (Wu Bang)** | Lead | — | Manager |
| **安琳 (An Lin)** | Under 吴邦 | 凯东源 | Data cleaning for 42-44 companies; whitelist admission rules |
| **陈耀 (Chen Yao)** | Lead | — | Manager |
| **刘新洋 (Liu Xinyang)** | Under 陈耀 | 运立方/域普/车满满 | Shipping data integration; data quality; financial report analysis |
| **冉浩宇 (Ran Haoyu)** | Lead | — | Manager |
| **王天宇 (Wang Tianyu)** | Under 冉浩宇 | 佛朗斯 | Post-loan monitoring rules; overdue behavior rules from GPS + billing data |

The 3 section leads (吴邦, 陈耀, 冉浩宇) likely represent the 3 consulting companies. The candidate (Huang Fei) does not appear in this report — they were the senior engineer directing this work.

---

## 3. Technical Stack

| Category | Tools |
|----------|-------|
| **Languages** | Python (primary), SQL (extensive) |
| **Data Processing** | pandas, numpy, sqlalchemy, pyodbc |
| **Databases** | AWS Redshift (data warehouse), SQL Server (local), SQLite |
| **Cloud** | AWS (S3, Redshift, EC2), boto3 |
| **Orchestration** | Apache Airflow (deployed on EC2, 10+ DAGs) |
| **Third-party APIs** | PBOC credit bureau, Tongdun fraud detection, UnionPay, facial recognition |
| **Visualization** | Power BI (.pbix files) |
| **Infrastructure** | Kubernetes (K8s) for microservices, logs on S3 |
| **Version Control** | SVN (primary), git (PredictService only) |
| **Deployment** | AWS China (cn-north-1 region) |
| **ML/Stats** | sklearn LinearRegression (typing time prediction) |
| **PySpark** | Used at GLP phase only, NOT at 君正小贷 |

---

## 4. Project 1: Risk Decision Engine 3.0

**The crown jewel of the candidate's 君正小贷 work.**

### Source Files

- **Main logic:** `2017-风险控制/2018_决策引擎3.0/jzrisk.py` (author: huang, created 2017-12-18)
- **Orchestrator:** `2017-风险控制/2018_决策引擎3.0/pbcProc.py`
- **Config:** `2017-风险控制/2018_决策引擎3.0/jzconfig.py`
- **Batch processor:** `2017-风险控制/2018_决策引擎3.0/main_analysis.py`
- **Rule reference:** `2017-风险控制/2018_决策引擎3.0/校对字段.txt`
- **Earlier versions:** `2017-风险控制/2017_系统部署/机审决策重构/Version1.0/` through `Version7.0/`

### Architecture

```
Redshift (dm_pboc_*) → pbcProc.py orchestrator → jzrisk.py functions → 29-column rejection matrix (B.csv)
```

Processing flow in `pbcProc.py`:
1. Overdue section → RH001-RH004, RH023, RH027
2. Customer segment section → RH008-RH012, RH029
3. Debt section → RH013-RH015, RH021-RH022, RH025
4. Query section → RH026 (6 sub-conditions)
5. Other section → RH016-RH018, RH020, RH028

### All 29 Rejection Rules

**Section 1: Overdue (逾期部) — 6 active rules**

| Rule | Condition | Description |
|------|-----------|-------------|
| RH001 | `RH001_1 \| RH001_2 \| RH001_3` | Composite bad credit flag |
| RH001_1 | Account status contains 呆账/止付/冻结 | Bad debt, suspended, or frozen accounts |
| RH001_2 | Max overdue duration >= 6 months (loans, cards, or quasi-cards) | Severe delinquency |
| RH001_3 | Total overdue months >= 15 (any category) | Chronic delinquency |
| RH002 | Current period M1+ overdue with deserved_pmt > 500 RMB | Active delinquency |
| RH003 | Last 6 months M1+ count >= 2 | Repeated recent delinquency |
| RH004 | Last 12 months M3+ overdue with deserved_pmt > 500 RMB | Serious recent delinquency |
| RH023 | Last 24 months M4+ overdue (cards with max_use_lmt > 500) | Very serious card delinquency |
| RH027 | Last 24 months total overdue count >= 10 | Pattern of repeated delinquency |

**Section 2: Customer Segment (客群部) — 5 active rules**

| Rule | Condition | Description |
|------|-----------|-------------|
| RH008 | No outstanding (unsettled) housing loans | Not a homeowner = not target customer |
| RH009 | Housing loan issued within last 9 months | Too-new mortgage (risky) |
| RH010 | No loan or card with history >= 12 months | Thin credit file |
| RH011 | Max credit card limit < 3,000 RMB | Very low credit standing |
| RH012 | Max credit card limit > 500,000 RMB | Over-qualified (not target customer) |
| RH029 | Not a "target customer" — no normal housing loan > 12 months AND no normal card > 12 months | Composite target check |

**Section 3: Debt (负债部) — 5 active rules**

| Rule | Condition | Description |
|------|-----------|-------------|
| RH013 | Unsettled unsecured loan balance > 500,000 RMB | Excessive unsecured debt |
| RH014 | Credit utilization >= 70% AND >= 2 suspected cash-out cards AND cash-out card balance >= 100,000 RMB | Cash-out fraud detection (composite) |
| RH015 | Next 3 months' credit loan repayments >= 200,000 RMB | Excessive near-term obligation |
| RH021 | Loan-debt ratio >= 10 | Over-leveraged |
| RH022 | >= 4 loans issued within 30-day windows in last 12 months | Concentrated borrowing pattern |
| RH025 | Card-debt ratio >= 7 | Excessive card debt relative to limits |

**Section 4: Query (查询部) — 1 composite rule with 6 sub-conditions**

| Rule | Condition | Description |
|------|-----------|-------------|
| RH026_1 | >= 5 querying orgs AND high-risk customer segment | Excessive inquiries in risky segment |
| RH026_2 | Bank credit card approval queries > 5 unique orgs (6 months) | Shopping for credit cards |
| RH026_3 | Bank loan approval queries > 5 unique orgs (6 months) | Shopping for loans |
| RH026_4 | Non-bank queries > 5 unique orgs (6 months) | Shopping at non-bank lenders |
| RH026_5 | Bank card inquiry-to-approval rate <= 25% (if >= 3 inquiries) | Low approval rate = risky |
| RH026_6 | Non-bank inquiry-to-approval rate <= 30% (if >= 6 inquiries) | Low approval rate at non-banks |

**Section 5: Other (其他部) — 5 active rules**

| Rule | Condition | Description |
|------|-----------|-------------|
| RH016 | OverdueScore < 665 | Custom scorecard threshold |
| RH017 | InfoScore < 20 | Insufficient personal information |
| RH018 | Non-tier-1 city ID AND housing loan monthly payment <= 1,500 RMB | Low-value property in non-prime city |
| RH020 | Works at competitor company (regex: 金融信息\|载鑫电子\|小赢优贷) | Competitor employee |
| RH028 | PBOC report is 5-30 days old | Stale credit report (PRODUCT mode only) |

**Disabled rules:** RH005, RH006, RH007, RH019, RH024 (permanently `False`)

**High-risk customer segments** (from `jzconfig.py`):
```
I05, B01, E03, D02, J01, C02, A02, G01, F03, K01, F01
```

### OverdueScore() — Custom Scorecard Model

**Location:** `jzrisk.py` lines 74-106

Weighted dot product of 19 binary indicators across 7 feature groups:

| Group | Variable | Condition | Weight |
|-------|----------|-----------|--------|
| **Mortgage count** | M[0] | n_mortgage <= 1 | 96.8 |
| | M[1] | n_mortgage > 1 | 104.1 |
| **Normal-use accounts** | NU[0] | n_normal_use <= 3 | 92.8 |
| | NU[1] | n_normal_use > 3 | 102.8 |
| **High-money cards** (>= 50K limit) | HM[0] | n_card_high_money <= 1 | 94.4 |
| | HM[1] | n_card_high_money > 1 | 110.4 |
| **Credit type combo** | CT[0] | Has house + mortgage combos (T1) | 110.3 |
| | CT[1] | Mixed credit types (T2) | 100.7 |
| | CT[2] | Minimal/no house loan (T3) | 93.5 |
| **6-month M1+ count** | M1[0] | m1_6 == 0 | 106.8 |
| | M1[1] | m1_6 == 1 | 91.1 |
| | M1[2] | m1_6 >= 2 | 79.7 |
| **Utilization ratio** | UR[0] | used_ratio == 0 | 92.4 |
| | UR[1] | 0 < used_ratio <= 0.6 | 107.9 |
| | UR[2] | 0.6 < used_ratio <= 0.95 | 97.2 |
| | UR[3] | used_ratio > 0.95 | 89.4 |
| **6-month query orgs** | Q[0] | query_n_6 <= 3 | 103.8 |
| | Q[1] | 3 < query_n_6 <= 6 | 87.5 |
| | Q[2] | query_n_6 > 6 | 72.0 |

**Score formula:** `score = round(np.dot(w, features), 0)`
**Score range:** 618.6 (worst) to 746.1 (best)
**Cutoff:** score < 665 → reject (RH016)

**Credit type combo definitions:**
- T1 (best): Has house loan + mortgage/car combinations
- T2 (medium): Mixed credit profiles
- T3 (weakest): No house loan or minimal credit

### GroupClassify() — 36 Customer Segments

**Location:** `jzrisk.py` lines 203-248

Classifies borrowers based on 11 binary conditions into 36 segments (A01-K01, X99 fallback):

**11 Input Conditions:**

| Var | Description |
|-----|-------------|
| C1 | Has housing loan |
| C2 | Has other (non-housing) loan |
| C3 | Has credit card |
| C4 | Most recent housing loan opened within 12 months |
| C5 | Max card age: -1 (<=6mo), 0 (6-24mo), 1 (>24mo) |
| C6 | Has mortgage/pledged housing loan |
| C7 | Has mortgage/pledged other loan |
| C8 | Credit utilization > 50% |
| C9 | Has normal cards AND no risky cards (label 1,4,8) |
| C10 | Has other loan with contract_amt <= 50,000 |
| C11 | All cards have repayment delay >= 20 days or delay == 0 |

**Segment groups (by housing loan status):**
- **A01-A02:** Has house loan + newly opened house loan
- **B01-B02:** Has house loan only (no other loan, no card)
- **C01-C02:** Has house loan + other loan (no card)
- **D01-D06:** Has house loan + card (no other loan) — 6 sub-segments by card age, utilization, card health
- **E01-E04:** Has house loan + other loan + card — 4 sub-segments
- **F01-F05:** No house loan + has card — 5 sub-segments by card age, utilization
- **G01-G03:** No house loan + other loan + card + old cards + small other loan
- **H01-H03:** No house loan + other loan + card + old cards + large other loan
- **I01-I06:** No house loan + no other loan + card + old cards — 6 sub-segments
- **J01:** No house loan + other loan + no card
- **K01:** No house loan + no other loan + no card (thin file)
- **X99:** Fallback (no match)

### CardClassify() — 10 Credit Card Types

**Location:** `jzrisk.py` lines 47-66

| Label | Name | Detection Logic |
|-------|------|----------------|
| 0 | 正常卡 (Normal) | Default — no other condition matches |
| 1 | 循环新卡 (Revolving New) | New card (<=6mo), underpaying minimum, no overdue |
| 2 | 非循环新卡 (Non-revolving New) | Card age <= 6 months |
| 3 | 疑似降额卡 (Suspected Limit-Reduced) | Balance > 2x credit limit AND usage > 2x limit |
| 4 | 超额卡 (Over-limit) | Mature card (>6mo), limit >= 3000, avg balance > 1.1x limit |
| 5 | 卡内分期 (In-card Installment) | High balance relative to payment, all 'N' status, regular payments |
| 6 | 卡外分期 (Out-of-card Installment) | Usage == avg balance == payment (fixed installment pattern) |
| 7 | 循环卡 (Revolving) | Consistently paying less than 90% of minimum |
| 8 | **疑似套现卡 (Suspected Cash-Out)** | Avg balance > 80% of limit, stable utilization (80-120%), meeting minimum payments |
| 9 | 无用卡 (Unused) | Never used (all zeros) |
| 10 | 不活跃卡 (Inactive) | No overdue, mostly inactive history (>50% of months marked '*') |

**Cash-out detection (label 8) is particularly sophisticated** — it identifies cards being used to extract cash through high stable utilization with minimum payments, a common fraud pattern in Chinese consumer credit.

### Other Functions in jzrisk.py

| Function | Lines | Description |
|----------|-------|-------------|
| `InfoScore()` | 110-139 | Information completeness score (0-69). Checks 9 personal fields + account age + payment history depth. Cutoff: < 20 → reject |
| `adjMthPmt()` | 143-169 | Adjusted monthly housing payment. Commercial rate 5%, provident fund rate 3.25%. Age-based decay weights: [4, 2.5, 1.5, 1] for loan ages >=120, 84-119, 48-83, <48 months |
| `adjDsvPmt()` | 173-187 | Adjusts deserved payment for non-monthly loans (1.1x contract/period) |
| `LoanDebt()` | 265-269 | adj_deserved_pmt / adj_monthly_pmt, returns -1 if no housing loan |
| `CardDebt()` | 273-276 | cr_avg_6mth_bal / avg_credit_lmt |
| `Label1stLoan()` | 280-337 | 8 first-loan lifecycle labels: 首贷, 首贷结清, 复贷在还, 周期性续贷, 边还边续, 高债续贷, 非典型客群, 非目标客群 |
| `CompCom()` | 258-261 | Competitor company regex: `金融信息\|载鑫电子\|小赢优贷` |
| `QryOrgNum()` | 252-254 | Deduplicates querying organizations by extracting name before '/' |

### Version History

7+ versions of the decision engine were iterated:
- Version 1.0-6.0: `2017-风险控制/2017_系统部署/机审决策重构/Version{X}.0/`
- Version 3.0 (final, refactored): `2017-风险控制/2018_决策引擎3.0/`
- Key evolution: v6.0 had RH021 and RH026 hardcoded `False`; v3.0 activated them with refined thresholds

---

## 5. Project 2: PBOC Credit Report Data Mart

### Source Files

- **Main parser:** `2017-风险控制/1710_人行数据集市/pbocToDataframe.py` (~530 lines)
- **Data extraction:** `2017-风险控制/1710_人行数据集市/AbstractData.py`
- **Schema design:** `2017-风险控制/1710_人行数据集市/20171016数据集市/人行征信表结构设计.xlsx`
- **Airflow version:** `2017-风险控制/2017_Airflow_Tasks/dm_pboc_mart/pbocToDataframe.py`
- **Earlier versions:** `Version1.0/` through multiple iterations

### Output Tables (5 DataFrames → Redshift `datamart.dm_pboc_*`)

| Function | Table | Columns | Content |
|----------|-------|---------|---------|
| `PersonalToDf()` | `dm_pboc_personal` | 78 | Demographics, employment (5 records), residence (5 records), spouse info |
| `SummaryToDf()` | `dm_pboc_summary` | 59 | Credit cue (10), overdue summary (12), fallback summary (6), share/debt (24), query summary (6) |
| `CardinfoToDf()` | `dm_pboc_card_info` | 24 | Per-card: org, open date, credit limit, usage, payments, overdue status, 6-month history |
| `LoaninfoToDf()` | `dm_pboc_loan_info` | 29 | Per-loan: type, amount, collateral, payment schedule, overdue status, classification |
| `DetailqryToDf()` | `dm_pboc_detail_qry` | 5 | Per-inquiry: operator, date, reason |

### Parsing Architecture

PBOC credit report JSON structure (People's Bank of China):
```
ReportMessage
├── Header
│   ├── MessageHeader → report number, timestamps
│   └── QueryReq → name, ID, query reason/format/org
├── PersonalInfo
│   ├── Identity → gender, birthday, marital status, phones, education
│   ├── Spouse → spouse name, ID, employer, phone
│   ├── Residence → array of up to 5 addresses (flattened to _1..._5 suffix columns)
│   └── Professional → array of up to 5 employment records (flattened to _1..._5)
├── InfoSummary
│   ├── CreditCue → housing/other loan counts, card counts, first open dates
│   ├── OverdueAndFellback
│   │   ├── OverdueSummary → LoanSum, LoancardSum, StandardLoancardSum
│   │   └── FellbackSummary → AssetDisposition, AssureerRepay, FellbackDebt
│   └── ShareAndDebt → UndestoryLoancard, UndestoryStandardLoancard, UnpaidLoan
├── CreditDetail
│   ├── Loan → array of loan records
│   ├── Loancard → array of credit card records
│   └── StandardLoancard → array of quasi-credit card records
└── QueryRecord
    └── RecordInfo[0].RecordDetail → array of inquiry records
```

### Key Helper Functions

| Function | Purpose |
|----------|---------|
| `dict_str()` | Recursively converts all int/float values to strings in nested dicts |
| `DictToDataframe()` | Flattens 2-level dict into single-row DataFrame |
| `StrToFloat()` / `StrToInt()` | Locale-aware numeric parsing (handles Chinese and English commas) |
| `StrToDate1/2/3()` | Date format conversions (xxxx.xx.xx, xxxx年xx月, xxxx年xx月xx日) |

### Data Pipeline

```
S3 (api_pboc daily dumps) → Download JSON → pbocToDataframe.py parse → 5 DataFrames → Upload to Redshift (dataframe2redshift.py)
```

Upload method: DataFrame → CSV with `+` delimiter → S3 bucket `jz-redshift-tmp` → Redshift `COPY` command

---

## 6. Project 3: AWS S3 Data Pipeline

### Source Files

- **Download script:** `2017-风险控制/1709_S3数据解析/1获取S3数据.bat`
- **Parser:** `2017-风险控制/1709_S3数据解析/2S3数据解析.py`
- **Earlier versions:** `Version1.0/`, `Version2.0/`, `Version3.0/`

### Architecture

```
S3 (jz-database-backup) → aws s3 cp (batch) → local data/{YYYYMMDD}/ → Python parse (pipe-delimited "|+|") → CSV + SQL Server/Redshift
```

### All 46 Tables Synced

**Business tables (26):**
1. `customer_apply` — Loan applications
2. `customer_apply_end` — Final application results
3. `customer_applyconfirm_result` — Application confirmations
4. `customer_application_info` — Detailed applicant info
5. `customer_branchbook` — Branch bookings
6. `customer_check_file` — Document check records
7. `customer_check_file_result` — Document check results
8. `customer_check_file_result_info` — Document check details
9. `customer_contract` — Loan contracts
10. `customer_final_result` — Final decisions
11. `customer_id_card` — ID card records
12. `customer_no_his` — Customer number history
13. `customer_overtime_result` — Overtime processing results
14. `customer_phcheck_result` — Phone check results
15. `customer_phcheck_result_info` — Phone check details
16. `customer_register` — Customer registrations
17. `customer_riskdecision_question` — Risk decision questions
18. `customer_riskdecision_question_option` — Risk decision options
19. `customer_riskdecision_result` — Risk decision results
20. `customer_salesman` — Salesperson records
21. `customer_sitecheck_question` — Site check questions
22. `customer_sitecheck_question_option` — Site check options
23. `customer_sitecheck_result` — Site check results
24. `customer_sitecheck_result_evaluation` — Site check evaluations
25. `customer_unionpaydata_account_create` — UnionPay account creation
26. `api_pboc` — PBOC credit report API records

**Log/audit tables (11):**
27-37. `log_application_info`, `log_applyconfirm`, `log_branchbook`, `log_check_file_result`, `log_customer_register`, `log_id_card`, `log_loan`, `log_login`, `log_phcheck_result`, `log_sitecheck`, `log_upload_file`

**System/config tables (9):**
38-46. `manage_base_meta`, `manage_sitecheck_refuse_reason`, `manage_user`, `organ`, `organ_sitecheck_info`, `organ_user`, `work_equipment`, `work_station_channel`, `work_station_sitecheck`

### Processing Logic

- Daily S3 snapshots: Each date directory contains pipe-delimited flat files (`|+|` separator)
- File naming: `{table_name}_{YYYYMMDD}_{n}` (n=1 or 2 for different snapshot times)
- Filter: Only processes data from Sept 27, 2017 onward
- Full reload: No incremental/CDC logic — each run re-processes all historical files
- Data range in evidence: directories from 20170801 to 20171023+

---

## 7. Project 4: Application Wide Table

### Source File

- `2017-风险控制/2017_Airflow_Tasks/dm_application_wide/dm_application_wide.py`

### 18 Source Tables (all LEFT JOINed)

| Alias | Source Table | Join Key | Content |
|-------|-------------|----------|---------|
| a01 | `customer_register` | Base table | Registration info |
| a02 | `organ` | organ_id | Organization name |
| a03 | `organ` | net_id | Branch/network name |
| a04 | `customer_salesman` | saleman_id | Salesperson name |
| a05 | `customer_apply` | register_code | Application info |
| a06 | `customer_id_card` | apply_id | Customer name, ID number |
| a07 | `customer_check_file_result` | apply_id | Document review result |
| a08 | `organ_user` (id>64) | organ_user_id | Document reviewer name |
| a09 | `customer_riskdecision_result` | apply_id | Risk decision result |
| a10 | `customer_applyconfirm_result` | apply_id | Customer confirmation |
| a11 | `customer_phcheck_result` | apply_id | Phone check result |
| a12 | `organ_user` (id>64) | organ_user_id | Phone checker name |
| a13 | `customer_sitecheck_result` | apply_id | Site check result |
| a14 | `organ_user` (id>64) | organ_id | Site checker name |
| a15 | `customer_apply_end` | apply_id | Final application result |
| a16 | `customer_application_info` | apply_id | Detailed application info |
| a17 | `customer_branchbook` | apply_id | Branch booking |
| a18 | `organ_user` (id>64) | organ_user_id | Branch booker name |

### Output: 62+ Columns

Covers the full loan lifecycle: registration → organization → salesperson → application → ID verification → document check → risk decision → customer confirmation → phone check → branch booking → site check → final result → detailed application info (education, marriage, income, employment, contacts, address).

### Scheduling

Airflow DAG: runs 2x daily at 01:15 and 13:15 (UTC). `DROP TABLE IF EXISTS` + `SELECT INTO` pattern (full refresh).

---

## 8. Project 5: Airflow Orchestration

### Source Files

- DAGs: `2017-风险控制/2017_Airflow_Tasks/dags/`
- Task scripts: `2017-风险控制/2017_Airflow_Tasks/{task_name}/`
- Config: `2017-风险控制/2017_Airflow_Tasks/airflow.cfg`

### All 10 DAGs

| # | DAG ID | Schedule | Owner | Purpose |
|---|--------|----------|-------|---------|
| 1 | `dm_application_wide` | 2x daily (01:15, 13:15) | huangfei | Application lifecycle wide table |
| 2 | `dm_pboc_mart` | Daily 06:00 (or every 15 min) | huangfei | PBOC credit report data mart |
| 3 | `rp_daily_news` | 2x daily (08:30, 13:30) | huangfei | Daily application status report |
| 4 | `rp_personal_image` | Daily 07:00 | huangfei | Customer credit profile generation |
| 5 | `rp_tongdun_warning` | Monthly (10th, 00:00) | huangfei | Tongdun first-repayment blacklist check |
| 6 | `log_api_face_check` | Daily 05:30 | huangfei | Face recognition K8s log parsing |
| 7 | `log_decision` | Daily 05:00 | huangfei | Risk decision K8s log parsing |
| 8 | `mail_test` | Every 15 min (11:00-15:00) | huangfei | Email alert health check |
| 9 | `mail_important_update_check` | Daily 10:00 | huangfei | Data freshness monitoring (6 tables) |
| 10 | `get_pcauto_index_03` | Every 2 hours | xjy | Web scraping (different team member) |

All DAGs use BashOperator calling Python scripts. All owned by `huangfei` except #10.

---

## 9. Project 6: Tongdun First-Repayment Warning

### Source File

- `2017-风险控制/2017_Airflow_Tasks/rp_tongdun_warning/rp_tongdun_warning.py`

### API Integration

- **Endpoint:** `http://54.223.117.30:32018/query?applyId={}&idNo={}&name={}&mobile={}`
- **Method:** HTTP GET
- **Response:** JSON with nested `report.unofficialCredit.risk_items`

### 12 Blacklist Rules (QZ001-QZ012)

| Rule | Tongdun item_id | Special Logic |
|------|-----------------|---------------|
| QZ001 | 8156803 | Standard blacklist |
| QZ002 | 8156753 | Standard blacklist |
| QZ003 | 8156773 | Standard blacklist |
| QZ004 | 8157023 | Standard blacklist |
| QZ005 | 8156823 | Standard blacklist |
| QZ006 | 8156813 | Standard blacklist |
| QZ007 | 8156783 | Standard blacklist |
| QZ008 | 8157003 | Standard blacklist |
| QZ009 | 8156993 | Standard blacklist |
| QZ010 | 8157013 | Standard blacklist |
| QZ011 | 8157473 | Triggered when "3-month ID-linked phone count" > 1 (from `frequency_detail_list`) |
| QZ012 | 8157793 | Triggered when `platform_count` >= 6 (appeared on 6+ lending platforms) |

### Alert Logic

1. Query Redshift for approved loans (`result=1`)
2. Calculate first payment date (month after loan, day=15)
3. Filter to customers with first payment in current month
4. Join with historical Tongdun data to get mobile numbers
5. Re-query Tongdun API for each customer
6. Apply 12 blacklist rules
7. Write results to `report.tongdun_warning`

---

## 10. Project 7: K8s Log Parsing

### Face Recognition Log Parser

**Source:** `2017-风险控制/1711_风险决策人脸识别日志解析/log_api_face_check.py`

- **S3 bucket:** `k8s.product.log`, prefix `face-check`
- **Log format:** K8s pod logs with ISO8601 timestamps + JSON payloads
- **Regex extracts 15 fields:** acode, idNumber, Name, PhotoUrl, sign, Score, FaceResult, FaceResultText, CitizenResult, CitizenResultText, Photo, ResponseCode, ResponseText, Result, ResultText
- **Output:** `datamart.log_api_face_check` (Redshift)
- **Schedule:** Daily 05:30 (incremental) + full backfill script available

### Risk Decision Log Parser

**Source:** `2017-风险控制/1711_风险决策人脸识别日志解析/log_decision.py`

- **S3 bucket:** `k8s.product.log`, prefix `predict-service`
- **3 event types parsed via byte-level target matching:**

| Type | Target Pattern | Output Table | Columns |
|------|---------------|-------------|---------|
| Risk Decision Input | `'functionName': 'riskDecision'` | `log_decision` | 14 cols: functionName, version, applyId, idNo, name, timestamp, repCheck, compCheck, blacklistTd, pbcAllowIn, cusAllowIn, loanAmount, loanRate, loanFee |
| Question Decision | `'questionDescription'` | `log_questions` | 11 cols: version, timestamp, applyId, idNo, name, test, result, reasonCodes, questionCode, questionDescription, option |
| Make Loan Decision | `'customerDecisionResult'` | `log_makeloan` | 14 cols: version, timestamp, applyId, questionCode, questionResult, commentResult, commentDescription, riskDecisionResult, customerDecisionResult, systemDecisionResult, phoneCheckResult, test, result, reasonCodes |

---

## 11. Project 8: Data Freshness Monitoring

### Source Files

- **Original (5 tables):** `2017-风险控制/1711_五表更新预警/log_important_update_check.py`
- **Airflow version (6 tables):** `2017-风险控制/2017_Airflow_Tasks/mail_import_update_check/mail_important_update_check.py`

### 6 Monitored Tables

1. `origin_data_schema.api_face_check` — Face recognition API
2. `origin_data_schema.api_pboc` — PBOC credit bureau API
3. `origin_data_schema.api_unofficial_credit` — Unofficial credit check API
4. `origin_data_schema.CCS_ACCT` — Core Credit System accounts
5. `origin_data_schema.CCS_ACCTING_ENTRY` — Core Credit System accounting
6. `origin_data_schema.CCS_LOAN` — Core Credit System loans (added in Airflow version)

### Alert Logic

- **Threshold:** < 5 new records in past 24 hours
- **Recipient:** `yaowei@junzhengloan.com` (Yao Wei)
- **Subject:** "重要表更新异常！" (Critical table update anomaly!)
- **Priority:** Highest (1)
- **SMTP:** `smtp.ym.163.com` from `notify@junzhengloan.com`

---

## 12. Project 9: Operator Action Monitoring

### Source Files

- `2017-风险控制/1709_S3数据解析/用户动作监控1.sql` (wide table assembly)
- `2017-风险控制/1709_S3数据解析/用户动作监控2.sql` (time metric calculation)

### 9 Process Nodes Tracked

| Alias | Source Table | Process Node | Key Timestamps |
|-------|-------------|-------------|----------------|
| a | `log_id_card` | Registration | register_time |
| b | `log_upload_file` | File Upload | start_time, head_img_time, video_time |
| c | `log_check_file_result` | Document Check | receive_time, check_start_time, submit_time |
| d | `log_applyconfirm` | Application Confirm | start_time, confirm_1-5_time, print_time |
| e | `log_application_info` | Application Info | education_time through submit_time |
| f | `log_phcheck_result` | Phone Check | receive_time, check_start_time, question_1-6_time |
| g | `log_branchbook` | Branch Booking | customer_phone_time, submit_time |
| h | `log_sitecheck` | Site Check | receive_time, check_start_time, head_img_time |
| i | `log_loan` | Loan Disbursement | bank_debit_card_check_start_time |

### 5 Time Metrics Calculated

| Code | Process | Start → End |
|------|---------|-------------|
| `reg` | Registration + File Upload | register_time → commitment_video_time |
| `chk` | Document Check | check_receive_time → check_submit_time |
| `cfm` | Application Confirm | confirm_start_time → application_time |
| `app` | Application Info Entry | education_time → app_submit_time |
| `phc` | Phone Check | phcheck_receive_time → question_5_time |

---

## 13. Project 10: PBOC Report Validation Engine

### Source File

- `2017-风险控制/1709_人行初始化/DataCheck.py`
- **Test cases:** `wrong01.json`, `人行征信_demo.json`
- **Rule spec:** `征信录入校验规则.xlsx`

### Validation Sections

| Section | Fields Checked | Validations |
|---------|---------------|-------------|
| Header (报告头) | ReportSN, QueryTime, ReportCreateTime, Name, Certtype, Certno, QueryReason | Not null, length==22, length==18, datetime format regex |
| PersonalInfo — Professional | 8 fields per record (Duty, Employer, Address, etc.) | Not null |
| PersonalInfo — Spouse | 5 fields (Certno, Name, Employer, etc.) | Not null |
| PersonalInfo — Residence | 3 fields per record (Address, GetTime, Type) | Not null |
| PersonalInfo — Identity | 10 fields (Birthday, Gender, Mobile, etc.) | Not null |
| UndestoryLoancard | 8 summary fields (AccountCount, CreditLimit, etc.) | Consistency: if any non-empty, all must be non-empty; Chinese comma detection |
| RecordInfo | 3 fields per inquiry (Querier, QueryDate, QueryReason) | Not null, date format |

### Error Report Format

```python
{'Name': str, 'Result': '1'/'0', 'Problems': [
    {'TableName': '报告头', 'KeyName': '报告编号', 'Descrption': '内容缺失/位数有误/格式有误', 'Seq': ''}
]}
```

---

## 14. Project 11: Monte Carlo Portfolio Simulation

### Source Files

- **Model:** `W-2017/170808模型成品/IncomeModel7.0-Output.py`
- **Parameters:** `W-2017/170808模型成品/Paras.xlsx`
- **Visualization:** `IncomeDisplay.pbix`, `Stock.pbix`, `Stock2.0.pbix`

### Model Parameters (from Paras.xlsx)

| Parameter | Description |
|-----------|-------------|
| m | Number of Monte Carlo simulations (portfolio count) |
| n | Number of loans per portfolio |
| T | Loan term in months |
| r | Penalty interest rate (÷ 10000) |
| ldes | Loan amount distribution per group: [mean, std, min, max] |
| rdes | Interest rate distribution per group: [mean, std, min, max] |
| w | Customer group weight ratios |
| dr, pr, m1dr, m2dr, m3dr | Monthly default, prepayment, M1/M2/M3 delinquency rate curves per group |

### Simulation Logic

1. **Portfolio generation:** For each of m simulations, generate n loans using truncated normal distributions per customer segment
2. **Payment calculation:** Standard amortization: `Pmt = Loans * (r/12) * (1+r/12)^T / ((1+r/12)^T - 1)`
3. **Event assignment:** Randomly sample abnormal accounts, distribute into Default/Prepay/M1/M2/M3 categories
4. **Cash flow modification:**
   - Default: All future payments zeroed from default month
   - Prepayment: Remaining principal paid, future zeroed
   - M1: Payment shifted +1 month with 30-day penalty interest
   - M2: 2 months shifted +2 months with cumulative penalty
   - M3: 3 months shifted +3 months with cumulative penalty
5. **Output:** Monthly aggregate income per simulation (m rows × T+1 columns) + individual loan detail for first simulation

### Key Functions

| Function | Purpose |
|----------|---------|
| `NormGen(n, m, mu, sigma, mini, maxi)` | Truncated normal distribution RNG (re-samples out-of-range values) |
| `GroupLabel(ng)` | Sequential group label assignment from count array |
| `RatioGen(n, m, w)` | Random group assignment by configured weight ratios |

**Scale:** 5,000 simulation runs mentioned in output filename.

---

## 15. Project 12: PBOC Typing Time Tracker

### Source Files

- `2017-风险控制/1801_华道录入动作监控/TypingMonitor.py`
- `2017-风险控制/1801_华道录入动作监控/LinearModel.py`

### Purpose

Monitors outsourced data entry vendor (华道/Huadao) performance in digitizing PBOC credit reports.

- Reads PDF uploads and XML outputs from S3 bucket `jz-pboc-data`
- Calculates processing time: XML creation time - PDF upload time
- Joins with `api_pboc` table for vendor identification
- `LinearModel.py` fits sklearn `LinearRegression` to predict typing time from PDF file size (MB)
- Filters to 80th percentile of emergency reports for model training

---

## 16. GLP/Prologis Phase

### Source File

- `C:\Users\huang\Downloads\GLP\普洛斯项目周报.xls` (week of March 11-15, 2019)

### Work Overview

The candidate served as **Senior Data Modeling Engineer**, directing teams from 3 consulting companies on a supply chain finance platform. Key aspects:

- **3 loan products:** 普易租 (leasing), 普货贷 (cargo loans), 普运贷 (transport loans)
- **Multiple clients:** 佛朗斯, 凯东源 (42-44 companies pending admission), 车满满, 运立方, 域普
- **Technical scope:**
  - Pre-loan: whitelist rules, product admission rules, credit limit calculation rules
  - Post-loan: monitoring rules using GPS + billing data, overdue behavior rules from repayment history
  - Data quality analysis for companies seeking platform admission
- **Technology:** PySpark (confirmed by candidate)
- **Candidate's role:** Managed/directed consulting teams (did not appear in the weekly report as an individual contributor — consistent with a supervisory role)
- **Candidate's note:** Infrastructure building was handled by others; candidate's main contribution was data modeling and rule design

---

## 17. Resume Integration Notes

### How Two Companies Merge Into One Narrative

**Resume entry:** "GLP Technology, Jul 2017 - Aug 2019" with title "Lead Data Engineer" (DE) or "Data Scientist & Team Lead" (ML)

**Key decision (2026-03-09):** ALL bullets are based on 君正小贷 work only. GLP/Prologis content is NOT written as bullets — instead, PySpark appears in the per-role "Technical Skills" line (Toni CV format). Rationale:
1. User can defend 君正 work to source-code depth; GLP memory is vague
2. PySpark is already covered in Projects (greenhouse pipeline, lakehouse)
3. "Directed consulting teams" contradicts the "founding startup member" narrative
4. 6 fully defensible bullets > 7 with 1 soft spot

**Narrative arc:** "Joined a lending fintech as the founding technical member, built the entire credit risk data infrastructure from scratch, then progressed to operations and cross-functional leadership."

**Technical Skills line (Toni CV format):**
> Technical Skills: Python, SQL, PySpark, AWS (Redshift, S3, EC2), Airflow, pandas, NumPy, Power BI

PySpark is honestly listed because user used it at GLP phase. No bullet needed to explain it.

### Bullet-to-Evidence Mapping

| Bullet ID | Primary Source | Evidence Strength |
|-----------|---------------|-------------------|
| `glp_founding_member` | 君正: all code @author:huang, first employee | Strong — code evidence |
| `glp_decision_engine` (NEW) | 君正: jzrisk.py, pbcProc.py | Very strong — full source code |
| `glp_data_engineer` | 君正: pbocToDataframe.py, S3 pipeline | Very strong — full source code |
| `glp_pyspark` | GLP: weekly report + candidate confirmation | Medium — one weekly report |
| `glp_portfolio_monitoring` | 君正: rp_tongdun_warning.py, monitoring scripts | Strong — full source code |
| `glp_payment_collections` | Candidate confirmation ("大致准确") | Medium — no direct code evidence |
| `glp_generalist` | GLP: weekly report team structure | Medium — one weekly report |

---

## 18. Full Directory Tree

```
2017-君正小贷/
├── 2017-风险控制/
│   ├── 1707_收入模型/                          # Monte Carlo income model
│   ├── 1709_S3数据解析/                        # S3 data pipeline (V1.0-V3.0)
│   │   ├── 1获取S3数据.bat
│   │   ├── 2S3数据解析.py
│   │   ├── 用户动作监控1.sql, 用户动作监控2.sql
│   │   ├── Version1.0/, Version2.0/, Version3.0/
│   │   └── data/, BackData/data/               # Raw daily snapshots
│   ├── 1709_人行初始化/                        # PBOC report validation
│   │   ├── DataCheck.py
│   │   └── Version1.0/
│   ├── 1709_工号设备号/                        # Employee & device IDs
│   ├── 1709_日志监控/                          # Log monitoring + 40+ CSV exports
│   ├── 1710_人行数据集市/                      # PBOC data mart
│   │   ├── pbocToDataframe.py (~530 lines)
│   │   ├── AbstractData.py
│   │   └── 20171016数据集市/
│   ├── 1711_五表更新预警/                      # Data freshness monitoring
│   ├── 1711_风险决策人脸识别日志解析/          # K8s log parsing
│   │   ├── log_api_face_check.py, log_api_face_check_full.py
│   │   ├── log_decision.py, log_decision_full.py
│   │   └── face-check-*.log                    # 20 sample pod logs
│   ├── 1801_华道录入动作监控/                  # PBOC typing time tracker
│   │   ├── TypingMonitor.py, LinearModel.py
│   ├── 2017_Airflow/                           # Airflow deployment (EC2 keys)
│   ├── 2017_Airflow_Tasks/                     # 10 DAGs + task scripts
│   │   ├── dags/ (10 DAG definitions)
│   │   ├── dm_application_wide/
│   │   ├── dm_pboc_mart/ (+ dataframe2redshift.py)
│   │   ├── log_api_face_check/
│   │   ├── log_riskdecision/
│   │   ├── mail_alert/, mail_import_update_check/
│   │   ├── rp_daily_news/, rp_personal_image/
│   │   └── rp_tongdun_warning/
│   ├── 2017_Redshift权限管理/                  # Redshift permissions
│   ├── 2017_决策规则/                          # Decision rules docs
│   ├── 2017_数据字典/                          # Data dictionary
│   ├── 2017_数据架构/                          # Data architecture docs
│   ├── 2017_系统部署/                          # System deployment
│   │   └── 机审决策重构/Version1.0-7.0/       # Decision engine versions
│   ├── 2018_决策引擎3.0/                      # Decision engine v3.0 (final)
│   │   ├── jzrisk.py (all algorithms)
│   │   ├── pbcProc.py (orchestrator)
│   │   ├── jzconfig.py (configuration)
│   │   └── main_analysis.py (batch processor)
│   ├── 2018_GAN/                               # GAN experiments
│   ├── 2018_动作监控/                          # Action monitoring v2
│   ├── 2018_银联/                              # UnionPay integration
│   ├── PredictService/                         # Risk decision microservice
│   └── 人行报告分析助手/                       # PBOC analysis tool
│
├── W-2017/                                     # Daily working folders
│   ├── 170501 - 180115/                        # Date-organized work journal
│   └── 170808模型成品/                         # Monte Carlo model (v7.0)
│       ├── IncomeModel7.0-Output.py
│       ├── Paras.xlsx
│       └── IncomeDisplay.pbix, Stock*.pbix
```

---

*This document is a permanent reference. If bullets need future revision, consult this report instead of re-reading the 28,000+ source files.*
