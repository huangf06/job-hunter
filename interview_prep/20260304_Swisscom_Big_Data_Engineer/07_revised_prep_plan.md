# Swisscom 技术面试 — 修正版准备计划

## 核心判断：1小时面试 = 技术深度对话，不是 live coding

已过 CoderPad → 编码能力已验证 → 1小时放不下 CV讨论+技术问答+编码
→ **这轮面试考的是：你是否真正理解你做的东西，能否在高级别对话中展示深度**

---

## 修正后时间分配 (40h → 重新分配)

| 模块 | 时长 | 说明 |
|------|------|------|
| **A. 项目深度准备 — 能口头讲透每个项目** | 10h | 最重要！面试 40% 的时间在这 |
| **B. Spark/数据工程概念深度** | 8h | Yannis 会口头深挖的技术概念 |
| **C. 系统设计思维** | 6h | "如何设计一个..."类型的对话 |
| **D. Kafka + 流处理概念** | 4h | Polaris 团队核心，口头讨论 |
| **E. 英语口述反复练习** | 6h | 散布在每个模块中，每学完一个就说出来 |
| **F. 面试官研究 + 战术策略** | 2h | 怎样利用 Yannis 的背景建立共鸣 |
| **G. 你的提问准备** | 2h | 10 分钟的提问环节是展示调研深度的机会 |
| **H. 面试前放松** | 2h | 停止学习，检查设备 |

**砍掉了什么**:
- ~~Python 刷题 5h~~ → 已过 CoderPad，不会再考
- ~~SQL 手写刷题进阶 4h~~ → 保留概念理解(口头能解释)，砍掉手写练习
- ~~AWS 服务速览 2h~~ → 缩减到嵌入在系统设计中顺带覆盖
- ~~模拟编码环节~~ → 改为模拟口头技术对话

---

## 模块 A：项目深度准备 (10h) — 决胜区

### 原则：不是背答案，是真正理解每一个技术决策的 WHY

Yannis 的面试风格（基于他的学术背景推断）是 **Socratic drilling** — 他会追问"为什么"直到你说不出来为止。你的目标是：**让他追问到第 3-4 层还能回答**。

### 深度层级示意

```
第1层: "I used Structured Streaming with watermarking"  ← 任何人都能说
第2层: "Because event-time windows handle late data correctly"  ← 有经验的人
第3层: "The watermark propagates through the plan — Spark tracks
        max(event_time) - threshold per partition to decide when
        to close windows and emit results"  ← 深度理解
第4层: "The trade-off is latency vs completeness — a larger watermark
        means more complete results but higher latency. For our crypto
        feeds with unreliable APIs, we chose 10 minutes based on
        observing the 99th percentile of actual delays"  ← 出彩
```

### A1. Financial Data Lakehouse — 深挖到第 4 层 (3h)

这是你最近的项目，面试官 100% 会深挖。为以下每个技术点准备到第 4 层:

**1. Structured Streaming + Watermarking**

为什么用 event-time 而不是 processing-time？
→ processing-time 受系统负载影响，不可靠
→ event-time 是数据本身的属性，语义正确

watermark 的值怎么选的？
→ 观察了实际延迟的分布，选择了覆盖 99% 的延迟的阈值
→ trade-off: 太大 → 窗口关闭慢，下游等待久；太小 → 丢弃太多 late data

如果面试官问"watermark propagation"的机制？
→ 每个 Kafka partition 维护自己的 watermark = max(event_time) - threshold
→ 全局 watermark = min(所有 partition 的 watermark)
→ 当全局 watermark 超过窗口结束时间 → 窗口关闭并输出结果

**2. Medallion Architecture (Bronze/Silver/Gold)**

为什么三层而不是两层？
→ Bronze = 原始保真层，永不修改，用于 replay 和 audit
→ Silver = 清洗+去重+类型转换，schema enforced
→ Gold = 业务聚合，直接服务查询

quarantine 为什么放在 Bronze→Silver 而不是 ingestion 入口？
→ 如果在入口就拒绝，数据永久丢失
→ Bronze 先收下所有数据（包括坏数据），然后在 Silver 边界做验证
→ quarantine 记录错误原因，修复后可以 replay → 零数据丢失

如何 replay quarantined data？
→ 修复 schema/逻辑后，将 quarantine 表中的数据重新推入 Silver 管道
→ 幂等处理: Silver 层的 MERGE INTO 确保不会重复

**3. Delta Lake 优化 (Z-ordering, Compaction)**

Z-ordering 原理？
→ 多维排序，将多列的值在物理存储上 co-locate
→ Parquet 文件有 min/max statistics → Z-ordering 让 Spark 的 data skipping 更有效
→ 选择 `symbol` + `timestamp` 因为 90% 的查询模式是 "某个 symbol 在某段时间"

为什么不用 partitionBy 而用 Z-ordering？
→ 如果 symbol 有 10000+ 个值，partitionBy 会产生 10000+ 个小目录 → small file problem
→ Z-ordering 在保持合理文件大小的同时实现数据局部性

Compaction 为什么重要？
→ Streaming 写入产生大量小文件 → 读取时 I/O overhead 大
→ OPTIMIZE 命令合并小文件为大文件 (128MB-1GB)
→ 定时运行（例如每小时）平衡写入延迟和读取性能

**4. Schema Evolution**

上游加了新字段怎么办？
→ Delta Lake 的 `mergeSchema=true` 自动处理向后兼容的变更（新增列）
→ 不兼容的变更（类型改变、删除列）→ 写入失败 → quarantine → 人工审查
→ 这是 schema-on-write (不是 schema-on-read)，在写入时就发现问题

**5. Auto Loader**

它比 `spark.read` 好在哪？
→ `spark.read` 每次扫描整个目录 → O(n) 文件
→ Auto Loader 使用 file notification (或 directory listing 模式) → 只处理新文件 → O(1)
→ 自动处理 exactly-once: 通过 checkpoint 记录已处理文件
→ 支持 schema inference 和 schema evolution

### A2. GLP Technology — 深挖创业经历 (2h)

面试官最好奇的: **作为第一个数据员工，你如何从零构建？**

**决策过程 — 第一个月做什么？**
→ "我没有立即开始写代码。第一周我和业务团队坐在一起，理解消费信贷的核心指标：违约率、催收率、获客成本、贷款生命周期价值。
→ 然后我画了一张数据流图，识别出所有数据来源和它们之间的关系。
→ 优先级决策: 先建数据摄取管道（因为没有数据什么都做不了），然后建分析能力，最后自动化。"

**PySpark ETL 管道的技术深度**
→ 源: MySQL (贷款系统) + 外部征信 API + 用户行为日志
→ Transform:
  - 数据清洗（去重、类型转换、缺失值处理）
  - 特征工程: 申请特征(年龄、收入、地区) + 行为特征(还款模式) + 征信特征(历史违约)
  - 全生命周期聚合: 每个贷款从申请到结清的完整视图
→ Target: 分析用数据库 + 模型训练 feature store
→ 调度: 每日增量 + 每周全量

**信贷评分模型的 trade-off**
→ 为什么用传统 ML (XGBoost/LightGBM) 而不是深度学习？
  - 数据量: 初创公司数据量有限（几十万到百万级），不够训练 DNN
  - 可解释性: 监管要求能解释为什么拒绝贷款（GBDT 有 feature importance）
  - 冷启动: 需要快速迭代，GBDT 训练速度远快于 DNN

### A3. Baiquan Investment — 数据质量的深度 (2h)

**跨源验证框架**
→ 核心问题: 同一只证券在不同数据供应商之间的价格不一致
→ 我的方法:
  1. 每天收盘后，比较 N 个供应商的收盘价
  2. 如果 |price_A - price_B| / price_A > 0.5% → 标记为异常
  3. 自动检查每个交易日是否有数据（缺失交易日 = 供应商故障）
  4. 检查价格的统计属性（日波动率 > 20% → 可能是数据错误 vs 真实极端行情）

**为什么这对 Swisscom 直接相关？**
→ 电信网络数据同样来自多个来源（不同网元、不同协议）
→ 同一基站的指标在不同系统中应该一致 → 不一致 = 潜在问题
→ 数据质量直接影响下游决策（错误的网络指标 → 错误的容量规划）

### A4. Expedia + Thesis — 准备简短版本 (1h)

这两个可能只会被简单提到。准备 1 分钟版本:

**Expedia**: "Learning-to-rank problem, 4.9M records, XGBoost, NDCG@5=0.392, top 5% Kaggle. Key insight: feature engineering on user search patterns was more impactful than model complexity."

**Thesis**: "Uncertainty quantification in Deep RL under noisy environments. 150 training runs across 5 UQ methods. Key finding: noise paradoxically improved certain UQ methods — the 'noise paradox'. Published result with p<0.001."

### A5. 口述练习 (2h) — 分散在 A1-A4 中

每学完一个项目的深度准备，**立即用英语大声讲一遍**:
- 计时: 每个项目控制在 3 分钟以内
- 录音 → 回放 → 检查: 是否清楚？是否有具体数字？是否展示了 trade-off？
- **反复练习你的 2 分钟开场自我介绍**（至少说 5 遍）

---

## 模块 B：Spark/数据工程概念深度 (8h)

### B1. Spark 内部机制 (4h) — 口头能解释，不需要手写代码

**必须能流畅口述的 5 个话题**:

**话题 1: Spark 查询执行全流程 (Catalyst + Tungsten)**
（参考 07_40h_battle_plan.md 中的详细描述）
→ 重点: 能画出 SQL → Logical Plan → Optimized Plan → Physical Plan → Code Gen 的流程
→ 与 Yannis 的 LegoBase 的联系: 都是 "编译" 查询为底层代码

**话题 2: Shuffle 是什么，为什么昂贵，怎么避免**
→ Shuffle = 跨网络重新分配数据
→ 昂贵因为: 磁盘 I/O (写临时文件) + 网络传输 + 序列化/反序列化
→ 避免: broadcast join, pre-partitioning, 减少 groupBy 的 key 粒度

**话题 3: Data Skew — 检测和解决**
→ 检测: Spark UI → Stage 中某个 task 比其他慢 10x+
→ 解决: salting, broadcast join, AQE
→ 你的经验: crypto 数据中 BTC/ETH 交易量 >> 其他 → 某些 partition 过大

**话题 4: Batch vs Streaming 的选择**
→ 不是二选一，而是看用例:
  - 延迟容忍度: 分钟级 → batch; 秒级 → micro-batch; 毫秒级 → event-by-event
  - 你的做法: 在 Financial Lakehouse 中两者都用 — Auto Loader (batch) + Structured Streaming (streaming)

**话题 5: Delta Lake 的价值**
→ ACID on data lake: 解决了 S3/HDFS 上 Parquet 的一致性问题
→ Time travel: 可以查询历史版本，便于审计和 debug
→ Schema enforcement: 写入时验证 schema，防止坏数据进入
→ MERGE INTO: 支持 upsert 操作，SCD Type 2 的基础

### B2. 数据工程模式 (4h) — 概念层面的对话能力

**数据建模**:
- Star schema vs Snowflake: 什么时候用哪个？
- Kimball vs Inmon: 维度建模 vs 企业数据仓库
- SCD Type 2: 能口头解释机制和实现（MERGE INTO）

**数据质量**:
- 你在 3 家公司分别如何处理数据质量
- 能说出一个 data quality 框架的组成部分 (schema validation, completeness, freshness, consistency, accuracy)

**ETL vs ELT**:
- ETL: 传统方式，先转换再加载（适合 RDBMS 目标）
- ELT: 先加载再转换（适合 data lake/warehouse，利用目标系统的计算能力）
- 你的偏好: ELT (Bronze 先加载所有原始数据，然后在 Silver 转换)

---

## 模块 C：系统设计思维 (6h) — 对话式，不是画图

### 核心题: "How would you design a data pipeline for processing network events at Swisscom scale?"

**不需要画完美的架构图，但需要能口头走完整个流程**:

用 5 分钟口述:
1. "First, I'd clarify the requirements — what's the data volume, latency requirement, and what insights do we need?"
2. "For ingestion, I'd use Kafka as the central event bus — it handles the 230K events/second throughput and provides durability."
3. "For processing, I'd use a dual path: Spark Streaming for aggregations and batch analytics, and potentially Flink for ultra-low-latency alerting."
4. "Storage would follow the Medallion pattern on S3 — Bronze for raw events, Silver for cleaned data, Gold for aggregated metrics."
5. "For serving, Redshift or Athena for analytical queries, and a real-time dashboard fed from the streaming layer."
6. "Key trade-offs: partition key selection (region vs tower), watermark size (completeness vs latency), batch interval."

### 附加题: "How would you migrate from on-prem Hadoop to AWS?"

这是 Polaris 团队**正在做**的事情，极可能被问到:

1. "I'd start with a dual-write pattern — new data goes to both HDFS and S3, ensuring we can rollback."
2. "Migrate batch jobs from MapReduce/Hive to Spark on EMR or Glue."
3. "Use AWS DMS or custom scripts for historical data migration."
4. "Validate by running both pipelines in parallel and comparing outputs."
5. "Gradual cutover — one pipeline at a time, monitoring for discrepancies."
6. "Key risk: network egress costs if on-prem cluster is in Switzerland and AWS region is eu-west."

---

## 模块 D：Kafka + 流处理概念 (4h) — 口头对话深度

**只需要能口头解释，不需要写代码。**

核心概念: Topic, Partition, Consumer Group, Offset, Exactly-once
→ 参考 07_40h_battle_plan.md 中的详细描述

重点对话点:
- "How do you choose the partition key?" → 取决于查询模式和 ordering 需求
- "What happens when a consumer crashes?" → rebalancing, offset management
- "Kafka vs Kinesis?" → Kafka 更灵活但需要管理, Kinesis 是 managed 但 shard 限制
- "Schema evolution in streaming?" → Schema Registry + Avro, backward compatibility

---

## 模块 E：英语口述 — 散布在所有模块中 (6h total)

**规则: 每学完一个概念，立即用英语大声说出来**

特别练习:
- 2 分钟自我介绍 → 说 5 遍
- 每个项目 3 分钟深度版 → 每个说 3 遍
- 5 个技术概念的 30 秒解释 → 各说 2 遍
- 2 个系统设计的 5 分钟 walkthrough → 各说 2 遍

---

## 模块 F：面试官策略 (2h)

### 如何利用 Yannis 的背景建立共鸣

**话术准备** — 不要刻意，但如果自然提到:

如果讨论到 Spark Catalyst:
> "I find it fascinating how Spark's Catalyst optimizer essentially compiles SQL into optimized JVM bytecode through whole-stage codegen — it's a practical application of the idea that high-level abstractions don't have to sacrifice performance."
→ 这直接呼应他的 "Abstraction Without Regret" 哲学

如果讨论到查询优化:
> "In our Delta Lake setup, the combination of column statistics and Z-ordering essentially gives the query engine enough metadata to do aggressive data skipping — which is really a form of predicate pushdown at the storage level."
→ 展示你理解底层机制

如果讨论到 Scala vs Python:
> "I've primarily used PySpark for its faster development cycle, but I understand the trade-off — you lose some of the compile-time type safety that Scala's Dataset API provides. For production pipelines where correctness is critical, I can see the value of the stronger type system."
→ 展示你不是 "只会 Python" 而是理解 trade-off

### 其他面试官的应对

**Mani Bastaniparizi** — 公开信息少，可能是 Senior Engineer:
→ 可能问更实际的工程问题（生产环境问题排查、运维经验）
→ 准备: "Tell me about a production issue you debugged" 类型的故事

**Deepthi Thachett** (Scrum Master, optional):
→ 如果在场，可能关注: 你如何在 Agile 团队中工作，如何处理优先级变化
→ 准备: "How do you handle competing priorities?" 故事

**Monica Nicoara** (Senior Leader, optional):
→ 如果在场，关注: 大局观、职业目标、为什么选择 Swisscom
→ 准备: "Where do you see yourself in 2-3 years?" 回答

---

## 模块 G：你的提问 (2h)

面试最后 10 分钟的提问环节是你**展示调研深度**和**真诚兴趣**的最佳机会。

### 准备 6 个问题，现场挑 3 个最合适的问

**技术深度** (给 Yannis/Mani):
1. "The Polaris team transforms raw network data into actionable insights — could you walk me through what a typical data pipeline looks like end to end? I'm curious about the scale and whether it's primarily batch, streaming, or hybrid."

2. "I noticed Swisscom's GitHub org has active forks of Calcite and Flink as recently as 2025. Does the team contribute patches back, or are these for internal customization?"

**团队与工作** (给任何人):
3. "What does the team composition look like — how many data engineers, data scientists, and software engineers, and how do they collaborate day to day?"

4. "What would my first 90 days look like? What would be a realistic first project for someone joining the team?"

**战略** (如果 Monica 在):
5. "With the Vodafone Italia integration and the AWS migration happening in parallel, how is that shaping the team's priorities and roadmap?"

6. "What's the biggest technical challenge the Polaris team is facing right now?"

---

## 修正后的执行时间线

```
现在开始:

Phase 1: 项目深度 (0-10h)
  [0-3h]   Financial Lakehouse — 每个技术点深挖到第4层 + 英语口述
  [3-5h]   GLP — 从零构建的决策过程 + 英语口述
  [5-7h]   Baiquan + 数据质量 + 英语口述
  [7-8h]   Expedia/Thesis 简短版 + 2分钟自我介绍反复练
  [8-10h]  所有项目串联口述 + 录音检查

Phase 2: 技术概念 (10-22h)
  [10-14h] Spark 深度 (Catalyst, Shuffle, Skew, Delta Lake)
  [14-18h] 数据工程模式 (建模, 质量, ETL/ELT, SCD)
  [18-22h] Kafka + 流处理 + 系统设计对话

Phase 3: 战术与演练 (22-32h)
  [22-24h] 面试官策略 + 提问准备
  [24-28h] 系统设计口述练习 (2个场景各说3遍)
  [28-32h] 全流程模拟 x2 (计时1小时，口述全部环节)

Phase 4: 收尾 (32-40h)
  [32-36h] 查漏补缺 — 回顾所有笔记中不够流畅的点
  [36-38h] 最后一轮口述: 自我介绍 + 3个项目 + 2个技术概念
  [38-39h] 速查表复习 (数字、Swisscom信息)
  [39-40h] 停止学习 → 检查设备 → 放松

  10:00 CET → 面试开始
```

---

## 与原计划对比

| 原计划 | 修正计划 | 变化 |
|--------|----------|------|
| SQL 手写刷题 8h | SQL 概念理解 (嵌入 B2) 2h | -6h |
| Python 编码 5h | 砍掉 | -5h |
| Spark 8h | Spark 口头深度 8h | 不变，但从写代码改为口述 |
| 系统设计 5h | 系统设计对话 6h | +1h (这是口头面试的核心) |
| Kafka 4h | Kafka 概念 4h | 不变 |
| CV 口述 4h | 项目深度准备 10h | **+6h** (最大变化) |
| AWS 2h | 嵌入系统设计 | -2h |
| 模拟面试 2h | 全流程口述模拟 4h | **+2h** |
| 编码模拟 | 砍掉 | — |

**净效果**: 从 "刷题+写代码" 重心转向 "理解深度+口头表达"。
