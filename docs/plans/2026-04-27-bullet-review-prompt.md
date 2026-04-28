# Bullet Library v7.1 — 逐条人工审阅 Prompt

将以下内容粘贴到新对话开头：

---

## 任务

我们要逐条审阅 `assets/bullet_library.yaml` 中所有 45 条 active bullet。目标：确认每条 bullet 的中英文理解一致、事实准确、叙事到位，审阅完成后 bullet library 即可投入 pipeline 使用。

## 流程（每条 bullet）

1. **中文翻译** — 用中文把这条 bullet 的完整意思说给我听。不是逐词翻译，而是确保我们对这条 bullet 传递的信号、强调的重点理解一致。如果有翻译上可能产生歧义的地方，特别标出。

2. **改善讨论** — 基于 v7.1 叙事校准报告的三个原则（可识别性 > 密度、关键词锚定、叙事匹配度），讨论：
   - ��条 bullet 有没有可以增强的地��？
   - 有没有措辞不够精确、可能被误读的地方？
   - 关键词是否到位（对目标岗位的 ATS/recruiter 扫描）？
   
3. **结论** — 三选一：
   - ✅ **通过** — 无需修改
   - ✏️ **微调** — 小幅措辞调整（给出修改建议，我确认后你改）
   - 🔄 **重写** — 叙事方向需要调整（讨论后确定新版本）

## 审阅顺序

按经历分组，从最重要的开始：

1. **GLP Technology** (7 条): glp_founding_member, glp_decision_engine, glp_pyspark, glp_data_quality, glp_data_engineer, glp_portfolio_monitoring, glp_data_compliance
2. **Baiquan Investment** (6 条): bq_de_pipeline, bq_de_factor_engine, bq_de_backtest_infra, bq_factor_research, bq_futures_strategy, bq_data_quality
3. **Ele.me** (5 条): eleme_ab_testing, eleme_fraud_detection, eleme_sql_optimization, eleme_user_segmentation, eleme_kmeans
4. **Henan Energy** (3 条): he_data_automation, he_supply_chain_analytics, he_data_quality
5. **Independent** (1 条): indie_quant_research
6. **Thesis** (3 条): thesis_uq_framework, thesis_noise_paradox, thesis_calibration
7. **Lakehouse** (4 条): lakehouse_streaming, lakehouse_quality, lakehouse_optimization, lakehouse_orchestration
8. **Greenhouse** (3 条): greenhouse_etl_pipeline, greenhouse_data_quality, greenhouse_aggregations
9. **其他项目** (13 条): expedia_ltr, nlp_poem_generator, nlp_dependency_parsing, ml4qs_pipeline, ml4qs_deep_learning, graphsage_ppi, bioinfo_hmm, bioinfo_alignment, deribit_options_system, deribit_risk_management, obama_tts_voice_cloning, lifeos_system, job_hunter_system

## 关键约束

- 所有修改必须基于事实（bullet library 中的 VERIFIED TIMELINE 和内容）
- 不使用 em dash（用逗号或分号）
- 保持 v3.0 interview-proven 文本的核心结构（17/17 面试验证过的 bullet 慎改）
- 改写参考三个原则：可识别性、关键词��定、叙事匹配度
- 每条 bullet 一个成就，verb-first，有具体数字或可验证技术细节

## 背景文件

- 当前 bullet library: `assets/bullet_library.yaml` (v7.1, 45 active)
- 叙事校准报告: `docs/plans/2026-04-27-bullet-library-v7.1-narrative-calibration.md`
- 设计文档: `docs/plans/2026-04-27-bullet-library-v7.1-narrative-calibration-design.md`
- 面试数据: 17 rounds, bullet_usage 表

## 开始

请先读取 `assets/bullet_library.yaml`，然后从 GLP Technology 的第一条 `glp_founding_member` 开始。每次处理一条 bullet，等我确认后再进入下一条。
