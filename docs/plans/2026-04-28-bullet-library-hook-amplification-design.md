# Bullet Library v7.3: Hook Amplification Design

**Date**: 2026-04-28
**Problem**: Interviewer feedback: "nothing stands out; only Python (Expert) made me stop"
**Root cause**: 2 A-hooks out of 47 active bullets (4.3%); recommended sequences front-load C-level bullets; all verbs are construction verbs ("Built/Engineered/Implemented")

## 1. Diagnosis

### Hook Distribution (47 active bullets)
- **A (stops you cold)**: 2 -- `bq_futures_strategy`, `eleme_fraud_detection`
- **B (has merit, needs full reading)**: 19
- **C (competent but forgettable)**: 26

### Structural Problems
1. GLP DE sequence (most-used direction) puts founding_member (B) LAST after 3 C-bullets
2. BQ DE/MLE sequences exclude the only A-hook (futures_strategy)
3. Ele.me DE sequence is broken: uses deprecated bullet + weakest active bullet
4. Verb monotony: "Built... Engineered... Designed... Implemented..." across all bullets
5. Results/outcomes buried at END of sentences; 6-second scan misses them

## 2. Strategy

Three operations, zero fabrication:

1. **Front-load hooks in sentence structure**: put the surprising element (number, result, finding) at the START of the sentence, not the end
2. **Promote A/B+ hooks into more sequences**: `bq_futures_strategy` and `eleme_fraud_detection` should appear in DE/MLE sequences, not just niche ones
3. **Reorder sequences**: strongest hook first, not last

## 3. Bullet Rewrites (7 bullets, sentence restructuring only)

### 3.1 `glp_founding_member` -- identity claim front-loaded

**Before:**
> Spearheaded credit scoring infrastructure as the first data hire at a fintech startup; owned the full ML lifecycle from data ingestion through feature engineering, model deployment, and portfolio monitoring.

**After:**
> Joined as the founding data engineer at a fintech startup; built the credit scoring infrastructure from scratch, owning the full ML lifecycle from data ingestion through feature engineering, model deployment, and portfolio monitoring.

**Why:** "founding data engineer" > "first data hire" (identity vs. fact). "From scratch" makes the scale explicit.

### 3.2 `eleme_sql_optimization` -- 5x front-loaded

**Before:**
> Optimized 90+ Hadoop/Hive queries through partition pruning and subquery pushdown, cutting scan volume 5x (from 500GB to 100GB) and unlocking real-time analytics on 30+ warehouse tables for fraud detection, operations, and marketing teams.

**After:**
> Cut Hadoop/Hive scan volume 5x (500GB to 100GB) by rewriting 90+ queries with partition pruning and subquery pushdown; unlocked real-time analytics across 30+ warehouse tables serving fraud detection, operations, and marketing teams.

**Why:** "5x" becomes the first number in the sentence. "Cut" is a result verb, not a process verb.

### 3.3 `eleme_ab_testing` -- result verb leads

**Before:**
> Developed user segmentation model achieving 2x improvement in churned-user reactivation rate via A/B testing; optimized Hadoop/Hive SQL queries for cross-functional reporting, cutting turnaround time by 30%.

**After:**
> Doubled churned-user reactivation rate through A/B-tested segmentation model; optimized Hadoop/Hive SQL queries for cross-functional reporting, cutting turnaround time by 30%.

**Why:** "Doubled" is one word that communicates both the action and the magnitude. "2x improvement" requires parsing.

### 3.4 `greenhouse_aggregations` -- scale front-loaded

**Before:**
> Implemented multi-granularity time-series aggregations (15-minute, hourly, daily) with quality-aware filtering that propagates upstream anomaly flags into aggregated results; processing 72M rows/day across 1,000 sensor sources at 1-minute ingestion resolution.

**After:**
> Processed 72M rows/day across 1,000 sensor sources at 1-minute ingestion resolution; implemented multi-granularity time-series aggregations (15-minute, hourly, daily) with quality-aware filtering that propagates upstream anomaly flags into aggregated results.

**Why:** "72M rows/day" is the single strongest scale number in any portfolio project bullet. Currently buried at the end.

### 3.5 `docbridge_pipeline` -- F1 score moved to first clause

**Before:**
> Built end-to-end document AI platform for CN-EU trade documents: PaddleOCR text extraction, LiLT layout-aware token classification, spatial post-processing for key-value pairing, and FastAPI REST API with PostgreSQL persistence; achieved 94.8% F1 on receipt extraction and 75.5% F1 on form understanding.

**After:**
> Built end-to-end document AI platform for CN-EU trade documents, achieving 94.8% F1 on receipt extraction and 75.5% F1 on form understanding; integrated PaddleOCR text extraction, LiLT layout-aware token classification, spatial post-processing for key-value pairing, and FastAPI REST API with PostgreSQL persistence.

**Why:** F1 scores move from last clause to first clause. Tech stack details follow as supporting evidence.

### 3.6 `thesis_uq_framework` -- finding leads, method follows

**Before:**
> Designed and implemented a standardized benchmarking framework for uncertainty quantification in Deep RL, orchestrating 150 independent training runs on SLURM-managed HPC under a full-factorial experimental protocol; unified CRPS, ACE, WIS, and coverage evaluation with statistical testing, establishing distributional learning as the strongest UQ approach across all four metrics.

**After:**
> Established distributional learning as the strongest uncertainty quantification approach for Deep RL across four metrics (CRPS, ACE, WIS, coverage) through a full-factorial benchmark of 150 training runs on SLURM-managed HPC; designed standardized evaluation framework with unified statistical testing.

**Why:** "Established X as strongest" is a definitive finding. "Designed and implemented a framework" is a construction verb. For research-MLE roles, the finding IS the hook.

### 3.7 `bq_futures_strategy` -- return front-loaded

**Before:**
> Developed and deployed R-Breaker intraday trading strategy for CSI index futures from research through live production; achieved 14.6% annualized return with real capital.

**After:**
> Delivered 14.6% annualized return with real capital on CSI index futures; developed and deployed R-Breaker intraday trading strategy from research through live production.

**Why:** "Delivered 14.6%" as opening. "Delivered" implies accountability for outcomes. The ONLY A-hook in the library should not have its number in the second clause.

## 4. Sequence Recomposition (8 changes)

### 4.1 GLP Technology
```yaml
# BEFORE
data_engineer: ["glp_pyspark", "glp_data_quality", "glp_portfolio_monitoring", "glp_founding_member"]

# AFTER
data_engineer: ["glp_founding_member", "glp_pyspark", "glp_data_quality", "glp_portfolio_monitoring"]
```
**Why:** founding_member is the only B-hook. Move it first. Already first in MLE/DS/quant.

### 4.2 Baiquan Investment -- DE
```yaml
# BEFORE
data_engineer: ["bq_de_pipeline", "bq_de_factor_engine", "bq_data_quality"]

# AFTER
data_engineer: ["bq_de_pipeline", "bq_de_factor_engine", "bq_futures_strategy"]
```
**Why:** Replace C-hook (data_quality) with A-hook (futures_strategy). "14.6% return" tells DE hiring managers: this person delivers outcomes, not just pipelines.

### 4.3 Baiquan Investment -- MLE
```yaml
# BEFORE
ml_engineer: ["bq_de_pipeline", "bq_de_factor_engine", "bq_de_backtest_infra"]

# AFTER
ml_engineer: ["bq_de_pipeline", "bq_de_factor_engine", "bq_futures_strategy"]
```
**Why:** Same logic. Replace C-hook (backtest_infra) with A-hook.

### 4.4 Baiquan Investment -- Quant
```yaml
# BEFORE
quant: ["bq_factor_research", "bq_de_factor_engine", "bq_de_backtest_infra", "bq_futures_strategy"]

# AFTER
quant: ["bq_factor_research", "bq_futures_strategy", "bq_de_factor_engine", "bq_de_backtest_infra"]
```
**Why:** A-hook moves from 4th to 2nd position. Research -> Result -> Infrastructure -> Infrastructure.

### 4.5 Ele.me -- DE (broken sequence fix)
```yaml
# BEFORE
data_engineer: ["eleme_kmeans", "eleme_sql_simple"]

# AFTER
data_engineer: ["eleme_fraud_detection", "eleme_sql_optimization"]
```
**Why:** Replace deprecated bullet + C-hook with A-hook + B+ hook. Strongest Ele.me combination for DE.

### 4.6 Ele.me -- MLE
```yaml
# BEFORE
ml_engineer: ["eleme_ab_testing"]

# AFTER
ml_engineer: ["eleme_fraud_detection", "eleme_ab_testing"]
```
**Why:** Add A-hook (fraud detection at scale) before the existing B-hook.

### 4.7 Ele.me -- DS
```yaml
# BEFORE
data_scientist: ["eleme_ab_testing", "eleme_kmeans"]

# AFTER
data_scientist: ["eleme_fraud_detection", "eleme_ab_testing", "eleme_kmeans"]
```
**Why:** A-hook leads the sequence.

### 4.8 Ele.me -- Data Analyst
```yaml
# BEFORE
data_analyst: ["eleme_ab_testing", "eleme_kmeans", "eleme_user_segmentation"]

# AFTER
data_analyst: ["eleme_fraud_detection", "eleme_ab_testing", "eleme_kmeans", "eleme_user_segmentation"]
```
**Why:** A-hook added as first bullet.

## 5. Summary of Impact

### Before (typical DE resume scan)
- GLP: C C C B (founding_member last)
- BQ: B C C (no result)
- Ele.me: C deprecated (broken)
- Lakehouse: B C C C
- **Total A-hooks visible: 0**

### After
- GLP: B C C C (founding_member first)
- BQ: B C A (futures_strategy result)
- Ele.me: A B+ (fraud + sql optimization)
- Lakehouse: B C C C (unchanged)
- **Total A-hooks visible: 2**

Going from 0 to 2 visible A-hooks per resume is the minimum viable improvement. Combined with sentence restructuring that front-loads B-level hooks, the resume should produce multiple "stop" moments in a 6-second scan.

## 6. What This Does NOT Fix

- No new facts are added. If real metrics exist (GLP loan volume, Ele.me growth numbers), adding them later would further strengthen hooks.
- The lakehouse/greenhouse portfolio projects remain at B/C level. They serve as keyword anchors (Databricks, Delta Lake) and don't need A-hooks.
- The "pattern finder" narrative thread (fraud detection + noise paradox + factor research + real returns) is now more visible through sequence composition, but is not explicitly called out anywhere. This is correct: the resume should SHOW, not TELL.
