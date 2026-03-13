# ML Resume V6 — Positioning Tighten Design

**Date:** 2026-03-13
**Input:** Codex section-by-section critique of v5 (12 decision points)
**Base file:** `templates/Fei_Huang_ML_Resume_v5.svg`
**Output:** `templates/Fei_Huang_ML_Resume_v6.svg`

---

## Core Strategy

**Main identity:** Production decisioning ML engineer — GLP as the single hero, all other sections serve this axis.

**Problem diagnosed:** v5 wobbles between three identities (production risk builder, quant researcher, recent ML/AI grad). Content is strong but positioning isn't locked.

**Single system-level fix:** Tighten the top third so readers form one clear impression in 8 seconds.

---

## Section-by-Section Changes

### 1. BIO (3 lines → 2 lines)

**Before:**
```
ML Engineer with production experience in credit risk systems and
quantitative research; M.Sc. in AI (VU Amsterdam).
Thesis on uncertainty quantification in Deep RL.
```

**After:**
```
ML Engineer with production credit risk and decisioning systems experience.
M.Sc. in AI (VU Amsterdam); quantitative research background in finance.
```

- Removes thesis (Education handles it)
- Pins GLP axis in first 8 seconds
- Quant becomes background modifier, not co-headline
- Saves 1 line

### 2. GLP — No changes

Hero section stays exactly as-is. Team Lead title retained.

### 3. BQ — Bug fix only

- Fix duplication: `"informed live portfolio informed live portfolio"` → single occurrence
- No ML over-translation (codex decision #3, Option A)

### 4. Independent Period — Light contextual frame

Prepend one clause to bullet:
```
Conducted independent quantitative research ahead of returning to graduate study.
Built automated equity research pipeline processing 83K+ daily records...
```

Anchors the period without being defensive.

### 5. Ele.me — Expand to 2 bullets

**Bullet 1 (fraud, enriched):**
```
Built anti-fraud detection system identifying 51,000+ suspicious order clusters
across 2.2M+ users using 3 pattern algorithms (same-phone, high-frequency,
repeat-order matching), preventing fraudulent subsidy claims during hyper-growth.
```

**Bullet 2 (data systems, new):**
```
Optimized 90+ Hadoop/Hive queries through partition pruning and subquery pushdown,
cutting scan volume 5x (500GB → 100GB) and unlocking real-time analytics on
30+ warehouse tables.
```

### 6. Education — Add Databricks cert

After Tsinghua, add one-line certifications:
```
CERTIFICATIONS
Databricks Certified Data Engineer Professional — February 2026
```

### 7. Projects — Compress ML4QS

**Before (6 body lines):**
```
Built an end-to-end ML pipeline for multi-sensor IMU data using Kalman filtering,
FFT-based feature engineering, LightGBM, and bidirectional LSTM.
Engineered 576+ features across time and frequency domains and achieved 65%
person classification and 94-99% sex classification accuracy.
```

**After (~3 body lines):**
```
Built end-to-end sensor ML pipeline: Kalman filtering, FFT-based feature
extraction (576+ features), LightGBM and bidirectional LSTM
for multi-class IMU classification.
```

Removes weak 65% metric. Keeps method chain and 576+ feature count.

### 8. Skills — Tighten

**Removed:** MATLAB, Docker, Git, Statistical Testing, ETL/ELT
**Rationale per item:**
- MATLAB: old-stack, no target-role value
- Docker/Git: too generic, every engineer has these
- Statistical Testing: abstract, not pinned to evidence
- ETL/ELT: generic label, already demonstrated in GLP body

**Final skills:**
- ML & Evaluation: PyTorch, scikit-learn, LightGBM, Learning to Rank
- Programming: Python, SQL, pandas, NumPy
- Data Systems: PySpark, Airflow, Redshift, Databricks, Hadoop, Hive
- Infrastructure: AWS

---

## Codex Decision Summary

| # | Decision | Choice | Notes |
|---|----------|--------|-------|
| 1 | Bio width | B (narrow) | Pin GLP axis |
| 2 | Thesis in Bio | B (remove) | Education handles it |
| 3 | BQ ML translation | A (keep quant) | Light framing only |
| 4 | Independent framing | B (light) | One clause, not defensive |
| 5 | Ele.me bullets | B (expand to 2) | Space freed from Bio+ML4QS |
| 6 | ML4QS framing | B (compress) | Remove weak metrics |
| 7 | Skills width | B (narrow) | Evidence-backed only |
| 8 | Databricks | **Override: KEEP** | Has Feb 2026 cert! |
| 9 | MATLAB | B (remove) | Old-stack noise |
| 10 | GLP ML language | A (keep real) | Strongest when authentic |
| 11 | Team Lead | A (keep) | Body proves hands-on |
| 12 | Main identity | A (production ML) | System-level anchor |

---

## Space Budget

| Change | Lines saved | Lines added |
|--------|------------|-------------|
| Bio: 3→2 | +1 | |
| ML4QS compress | +2 | |
| Skills tighten | +1 | |
| Ele.me expand | | -3 |
| Certifications | | -1 |
| Independent frame | | 0 (reword) |
| **Net** | **~0** | balanced |
