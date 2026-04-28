# Bullet Library v7.0 Audit Prompt

Copy everything below the line into a new Claude Code session (working directory: `job-hunter/`).

---

## Task: Bullet Library v7.0 — 逐经历审阅重建

我们要对 `assets/bullet_library.yaml` 做一次从头审阅，产出 v7.0。所有历史版本已提取到 `assets/bullet_library_versions/`，你需要逐个经历对比所有版本，挑出最佳 bullet 写入新版。

### 背景

Bullet library 经历了 7 个版本，面试转化数据如下：

| 版本 | 日期 | Bullets | 面试邀请 | 重大变更 |
|------|------|---------|---------|---------|
| v1.0 | 02-04 | 36 | 0 | 初版 |
| v2.0 | 02-07 | 40 | 0 | 加 bullet ID |
| **v3.0** | **02-08** | **50** | **11** | **5-pass proofread, 赢得 nebius/Deloitte/FareHarbor/Source.ag/Sensorfact/TomTom/Elsevier/Eneco/Swisscom 等面试** |
| v3.2 | 03-09 | 53 | (并入v4.0) | 加 GitHub 项目 bullets |
| v4.0 | 03-10 | 50 | 3 | 叙事重写 (kaiko.ai/ENPICOM/ABN AMRO) |
| v5.0 | 03-31 | 42 | 1 | 清理删除 — **删掉了多个面试验证过的 bullet** (glp_pyspark, glp_data_quality, glp_data_compliance, bq_de_factor_engine, bq_data_quality, eleme_ab_testing, deribit 整个项目) |
| v6.0 | 04-22 | 51 | 0 | 恢复 v3.0 bullets，但 pipeline 暂停没批量跑过 |
| v6.1 | 04-27 | 54 | — | 当前版本 |

**关键事实：v3.0 是经过验证的赢家 — 11/15 面试来自 v3.0 时期。**

### Bullet 使用频次 (来自 bullet_usage 数据库，430 份简历数据)

```
430x  glp_founding_member        (v3.0 原版)
414x  glp_pyspark                (v3.0 原版，v5.0 被删)
409x  bq_de_factor_engine        (v3.0 原版，v5.0 被删)
364x  glp_data_quality           (v3.0 原版，v5.0 被删)
363x  lakehouse_streaming        (v3.2 新增)
359x  glp_portfolio_monitoring   (v3.0 原版)
344x  bq_de_pipeline             (v3.0 原版)
330x  lakehouse_quality          (v3.2 新增)
320x  eleme_ab_testing           (v3.0 原版，v5.0 被删)
191x  lakehouse_orchestration
184x  thesis_noise_paradox
184x  thesis_uq_framework
170x  eleme_sql_optimization
167x  greenhouse_etl_pipeline
161x  bq_data_quality            (v3.0 原版，v5.0 被删)
143x  bq_factor_research
119x  bq_de_backtest_infra
119x  greenhouse_data_quality
110x  eleme_kmeans
103x  expedia_ltr
 92x  lakehouse_optimization
 68x  eleme_fraud_detection
 64x  glp_decision_engine        (v3.2 新增，替代旧 GLP bullets)
 58x  job_hunter_system
 51x  bq_futures_strategy
 42x  nlp_poem_generator
 36x  obama_tts_voice_cloning
 34x  deribit_options_system     (v4.0 废弃，v6.0 恢复)
```

### 各版本每段经历的 Bullet ID 变迁

**GLP Technology:**
- v2.0: glp_founding_member, glp_portfolio_monitoring, glp_pyspark, glp_data_engineer, glp_data_compliance
- v3.0: +glp_payment_collections, +glp_generalist (7 total)
- v3.2/v4.0/v5.0: glp_founding_member, glp_decision_engine(新), glp_data_engineer, glp_portfolio_monitoring, glp_generalist — 删掉了 pyspark/data_quality/data_compliance
- v6.1: 恢复 pyspark/data_quality/data_compliance/payment_collections, 废弃 glp_data_engineer, 新增 glp_decision_engine (9 total, 1 deprecated)

**Baiquan Investment:**
- v2.0: bq_de_pipeline, bq_de_factor_engine, bq_de_backtest_infra, bq_factor_research, bq_futures_strategy, bq_data_processing, bq_data_quality (7)
- v3.0: 去掉 bq_data_processing (6)
- v3.2/v4.0/v5.0: 去掉 bq_de_factor_engine, bq_data_quality (4)
- v6.1: 恢复 bq_de_factor_engine, bq_data_quality (6)

**Ele.me:**
- v2.0: eleme_ab_testing, eleme_sql_reporting (2)
- v3.0: eleme_ab_testing, eleme_sql_reporting, +eleme_user_segmentation (3)
- v3.2/v4.0: eleme_fraud_detection(新), eleme_sql_optimization(新), eleme_user_segmentation, eleme_bi_dashboards(新) — 完全重写 (4)
- v5.0: 去掉 eleme_bi_dashboards (3)
- v6.1: 恢复 eleme_ab_testing, +eleme_kmeans, +eleme_sql_simple (6)

**Henan Energy:**
- v2.0/v3.0: he_operations_management, he_demand_forecasting, he_performance_evaluation (+he_stakeholder_reporting in v3.0)
- v3.2+: 完全重写为 he_data_automation, he_supply_chain_analytics, he_data_quality, he_data_standardization
- v5.0+: 去掉 he_data_standardization

**Projects (变化较大的):**
- deribit_options: v3.0 有, v4.0 废弃, v6.0 恢复
- bsc_thesis_oa: v2.0-v3.0 有 5 bullets, v3.2+ 完全删除
- greenhouse_sensor_pipeline: v3.2 新增 3 bullets
- obama_tts: v3.0 新增
- sequence_analysis, deep_learning_fundamentals: v3.2 新增
- lifeos, job_hunter_automation: v3.0 新增

### 审阅方法

**逐经历执行，每段经历按以下步骤：**

1. **读取所有版本的该经历 bullets** — 打开 `assets/bullet_library_versions/` 下的对应段落做逐行对比
2. **以 v3.0 文本为基准** — 11 次面试验证过的版本。只在有明确改进理由时偏离 v3.0 文本
3. **参考使用频次** — 被 AI 高频选入简历的 bullet 说明其适用面广
4. **评估后续版本的改写** — v3.2/v4.0 的重写有些有价值（如 eleme_fraud_detection），有些是退步
5. **产出决策** — 每个 bullet 给出：保留（哪个版本的文本）/ 合并 / 废弃 / 新写，附理由

**审阅顺序（按重要性）：**
1. GLP Technology (最多 bullets，最高使用频次)
2. Baiquan Investment
3. Ele.me
4. Henan Energy
5. Projects: Thesis → Lakehouse → Greenhouse → Deribit → 其他
6. Independent Investor (career gap period)
7. 决定是否保留/删除: bsc_thesis_oa, aoshen_business, evolutionary_robotics legacy vs research

**质量标准：**
- 每个 bullet 必须有具体数字或可验证的技术细节
- 不用 em dash (—)，用逗号/分号
- 动词开头 (Engineered/Built/Designed/Developed...)
- 一个 bullet 聚焦一个成就，不要塞两件事
- 参考 `profiles/Profile2.0.pdf` 验证时间线和事实

**输出格式：** 每段经历审阅完后，直接修改 `assets/bullet_library.yaml` 的对应段落。全部完成后更新版本号为 v7.0。

### 文件位置

- 当前版本: `assets/bullet_library.yaml`
- 历史版本: `assets/bullet_library_versions/v*.yaml`
- 版本概览: `assets/bullet_library_versions/README.md`
- 事实参考: `profiles/Profile2.0.pdf`
- 简历模板: `templates/resume_master.html`
- AI 配置 (prompt 模板): `config/ai_config.yaml`

从 GLP Technology 开始。对每个 bullet，展示所有版本的文本对比，然后给出你的决策和理由。
