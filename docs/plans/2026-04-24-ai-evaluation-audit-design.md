# AI Evaluation Pipeline Audit — Design Document

**Date:** 2026-04-24
**Status:** Approved
**Goal:** 恢复 AI 评分管道的面试转化率，重启求职投递

## 问题诊断

### 时间线

- **2026-02 (v3.0 era):** 17 轮面试，来自 2 月投递。单一 prompt (C1+C2 合并)，宽松选择哲学。
- **2026-03~04 (v4.0→v6.0):** Bullet library 多轮重写，C2 prompt 膨胀（加入 narrative composition、page balance 等）。4 月投了 77 份，0 面试。

### 三个根因

1. **Bullet 内容漂移:** 11/35 面试验证 bullet 在 v6.0 中文本不同或被删除
2. **C2 Prompt 过度约束:** 新增 narrative roles、recommended sequences、cross-section strategy、page balance 等规则，把 AI 从"选最相关内容"变成"遵守格式模板"
3. **配置错位:** `deribit_options` 恢复但未加入 `project_keys`；`independent_investor` 未加入 `experience_keys`

## 修改方案

### Part 1: Bullet Library 合并 (v6.0 + v3.0 面试验证内容)

**A. 恢复 3 个 bullet 的 v3.0 面试验证文本:**

| Bullet ID | 操作 |
|---|---|
| `bq_de_backtest_infra` | content 改回 v3.0: "Architected event-driven backtesting framework supporting strategy simulation, walk-forward validation, and performance attribution — adopted as core research infrastructure by the investment team." |
| `expedia_ltr` | content 改回 v3.0: "Developed hotel recommendation system using learning-to-rank models (LightGBM, XGBoost+SVD) on 4.9M search records; engineered temporal, behavioral, and aggregation features achieving NDCG@5 = 0.392 on Kaggle test set." |
| `job_hunter_system` | content 改回 v3.0: "Built end-to-end job application pipeline leveraging LLM APIs (Claude) for resume personalization; designed multi-stage processing (web scraping via Playwright, rule-based filtering, AI analysis) with SQLite persistence and Turso cloud sync." |

**B. 恢复 2 个被删除的面试验证 bullet:**

| Bullet ID | Section | Content |
|---|---|---|
| `eleme_sql_reporting` | eleme | "Optimized complex SQL queries on Hadoop/Hive for cross-functional stakeholders, cutting reporting turnaround time by 30% during hyper-growth." |
| `obama_tts_voice_cloning` | 新建 projects section | "Fine-tuned Coqui XTTS v2 voice cloning model with hybrid deployment architecture: GPU training on Snellius HPC cluster via SLURM, CPU inference server on personal hardware; achieved production-quality voice synthesis across languages." |

**C. 保留 v6.0 强力新增 bullets (不动):**

`glp_decision_engine` (66x), `glp_data_quality` (58x), `eleme_fraud_detection` (56x), `eleme_sql_optimization` (44x), `greenhouse_etl_pipeline` (34x), 及其余所有 v6.0 新增内容。

**D. `glp_data_engineer` 保持 deprecated** — v3.0 原文已由 `glp_data_quality` 承载。

### Part 2: C2 Prompt 简化

**删除:**
- `PAGE BALANCE (CRITICAL)` section
- `NARRATIVE COMPOSITION (CRITICAL FOR RESUME QUALITY)` section (含 Narrative Roles 表格、Composition rules、Cross-Section Strategy)

**修改:**

1. **CONTENT SELECTION PRINCIPLE:**
   ```
   Before: "Quality over quantity — 3 well-chosen bullets that tell a coherent story beat 5 relevant-but-disconnected bullets."
   After: "Include ALL content that is relevant to the JD. Exclude content that doesn't strengthen the application. The resume can be 1-2 pages — do NOT artificially cut content to fit 1 page."
   ```

2. **BULLET DISTRIBUTION:**
   ```
   Before: "Main project: 2-3 bullets / Total project bullets: max 5"
   After: "Main project: 2-4 bullets (include all that are relevant) / Second project: 1-2 bullets / Third project (if relevant): 1 bullet"
   ```

3. **SKILLS FORMAT:** `4-5 categories` → `4-6 categories`

4. **PROJECT SELECTION:**
   ```
   Before: "Select 1-2 projects (max 2 to maintain page balance)"
   After: "Select 1-3 projects based on JD relevance. Include a third project only if it adds clearly different skills."
   保留 THESIS RULE (always include thesis_noise_paradox with thesis_uq_framework)
   ```

5. **OTHER RULES:**
   ```
   Before: "Prefer narrative composition over exhaustive coverage"
   After: "Include ALL relevant bullets for a position — do not cut for space"
   ```

**保留 (不动):**
- Header + Candidate Profile
- C1 Analysis Context (C2 独有增强)
- BIO RULES (增强版: staffing agency 检测、generic closer)
- TITLE SELECTION, COMPANY_NOTE
- SKILLS HONESTY RULE
- BULLET SELECTION RULE

### Part 3: 配置修复

`config/ai_config.yaml` → `prompt_settings`:
- `project_keys`: 加入 `deribit_options`
- `experience_keys`: 加入 `independent_investor`

### Part 4: 不动的部分

- C1 Prompt (evaluator): 不改
- Resume Validator: 不改
- Bullet Library 结构 (skill_tiers, bio_builder, title_options): 不改
- C1/C2 分离架构: 不改
- `tailor_adapt` / `c3_gate` prompts: 已 deprecated，不改

## 预期效果

- C2 prompt 从 ~14 个规则 section 减至 ~10 个，删除所有 narrative 工程规则
- Bullet library 恢复面试验证内容的同时保留 v6.0 新增强力 bullets
- AI 的注意力从"遵守格式模板"回归"选择最相关内容"
