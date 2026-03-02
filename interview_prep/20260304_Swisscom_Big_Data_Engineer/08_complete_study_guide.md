# Swisscom Big Data Engineer — 完整备考手册

> 面试时间: 2026-03-04 周三 10:00 CET | MS Teams | 1小时
> 面试官: Yannis Klonatos (EPFL PhD), Mani Bastaniparizi, [可能] Deepthi Thachett, Monica Nicoara

---

# ═══════════════════════════════════════════
# 第一章：开场 — 2分钟自我介绍
# ═══════════════════════════════════════════

## 背诵版本（英语，严格控制2分钟）

> Hi, I'm Fei. I'm a data engineer with about 6 years of experience, currently based in Amsterdam.
>
> I recently completed my Master's in AI at VU Amsterdam with a GPA of 8.2, and earned my Databricks Data Engineer Professional certification earlier this year.
>
> My career has spanned three data-intensive domains. At GLP, a consumer lending startup, I was the founding data hire — I built the entire data infrastructure from scratch, including PySpark ETL pipelines and a credit scoring system. At Baiquan Investment, I engineered market data pipelines for 3,000-plus securities, with a strong focus on cross-source data validation. And most recently, I've been building a real-time financial data lakehouse on Databricks, using Structured Streaming, Delta Lake, and a Medallion Architecture.
>
> What excites me about the Polaris team is the scale — transforming billions of network events per day into actionable insights is exactly the kind of data engineering challenge I thrive on. I'm particularly interested in how the team is building data products that directly shape Swisscom's network strategy.

### 自我介绍要点检查

- [x] 姓名 + 地点
- [x] 学历 (硕士 + GPA) + 认证
- [x] 3段工作经历各一句（按时间倒序的逻辑重要性）
- [x] 为什么对这个职位感兴趣
- [x] 具体数字 (6 years, 8.2 GPA, 3000+ securities, billions of events)
- [x] 不超过2分钟

---

# ═══════════════════════════════════════════
# 第二章：项目深度 — 面试官会深挖的每一层
# ═══════════════════════════════════════════

## 项目 1: Financial Data Lakehouse (最重要)

### 一句话概述
> "An end-to-end data lakehouse on Databricks that ingests real-time crypto market feeds, processes them through a Medallion Architecture, and serves clean OHLCV data for downstream analytics."

### 技术点 1: Structured Streaming + Watermarking

**第1层 — 我做了什么**:
使用 Spark Structured Streaming 从 Kafka 消费实时 crypto 市场数据，通过 watermarking 处理延迟数据。

**第2层 — 为什么这么做**:
- Processing-time window 受系统负载影响——如果 Spark 积压了，窗口边界会偏移，聚合结果语义错误
- Event-time window 用数据自带的时间戳，语义正确
- 但 event-time 需要 watermark 来告诉 Spark "多久以前的数据不再等了"

**第3层 — 机制**:
- 每个 Kafka partition 独立维护 watermark = `max(event_time) - threshold`
- 全局 watermark = `min(所有 partition 的 watermark)` — 最慢的 partition 决定全局进度
- 当全局 watermark 超过某个窗口的结束时间 → 窗口关闭 → 输出结果
- 关闭后到达的数据 → 丢弃（trade-off：completeness vs latency）

**第4层 — 我的决策与 trade-off**:
- 我选择 10 分钟 watermark，因为观察到 crypto 交易所 API 的 99th percentile 延迟约 8 分钟
- 更大的 watermark (30min) → 更完整但下游等待更久，不适合准实时仪表板
- 更小的 watermark (1min) → 丢弃 15-20% 的延迟数据，聚合不准
- **关联 Swisscom**: 网络事件在信号弱时也会延迟上报，同样需要 watermarking

### 技术点 2: Medallion Architecture (Bronze/Silver/Gold)

**第1层**: 三层架构：Raw → Cleaned → Aggregated

**第2层 — 每层的职责**:
| 层 | 存储 | Schema | 数据质量 | 用途 |
|----|------|--------|---------|------|
| Bronze | 原始 JSON (as-is) | Schema-on-read | 不做验证 | 保真、审计、replay |
| Silver | Parquet (typed) | Schema-on-write enforced | 验证+清洗+去重 | 分析基础 |
| Gold | Parquet (aggregated) | 业务视图 | 业务规则验证 | 直接服务查询/BI |

**第3层 — Quarantine-and-Replay 模式**:
```
Bronze 原始数据
    ↓ schema validation (pyspark StructType 校验)
    ├─ 通过 → Silver 层
    └─ 失败 → Quarantine 表 (记录: 原始数据, 错误原因, 时间戳)
               ↓ 修复逻辑后
               Replay → 重新推入 Silver pipeline
```
- 核心原则: **永不丢弃数据**。Bronze 收一切，Quarantine 允许事后修复

**第4层 — 为什么不在入口就拒绝坏数据？**:
- 如果在 Kafka consumer 层就拒绝 → 数据永久丢失，无法 replay
- Bronze 层的成本很低（S3 存储便宜），但数据丢失的成本很高（可能需要重新从交易所拉历史数据）
- Quarantine 还提供了**可观测性** — 可以监控每天 quarantine 的比例，作为上游数据质量的指标

### 技术点 3: Delta Lake 优化

**Z-ordering — 原理**:
- 不是简单排序，而是**多维空间填充曲线**（类似 Z-curve / Hilbert curve）
- 将多列的值交错编码，使得在多维空间中相近的点在物理存储上也相近
- Parquet 文件记录每个 row group 的 min/max statistics
- 查询时，Spark 读取 statistics → 判断这个文件是否可能包含目标数据 → data skipping

**为什么选 Z-ordering 而不是 partitionBy？**:
- `partitionBy(symbol)` → 10,000+ symbols = 10,000+ 目录 → **small file problem**
- Z-ordering 在合理文件大小 (128MB-1GB) 的基础上实现数据局部性
- 我选择 Z-order by `(symbol, timestamp)` → 覆盖 90% 的查询模式

**Compaction**:
- Structured Streaming 每个 micro-batch 写一个小文件 → 大量小文件 → 读取慢
- `OPTIMIZE` 命令合并小文件为大文件
- 我的策略: 每小时对活跃分区运行 OPTIMIZE，每天对所有分区运行一次

### 技术点 4: Schema Evolution

**向后兼容变更**（新增列）:
- `mergeSchema=true` → Delta Lake 自动将新列加入 schema
- 旧数据中该列为 NULL

**不兼容变更**（类型变更、删除列）:
- 写入时 schema enforcement 会拒绝 → 数据进入 Quarantine
- 人工审查决定: 迁移 schema 或修复上游

**Schema-on-write vs Schema-on-read**:
- Schema-on-read (data lake 传统做法): 读取时才检查 → 问题发现太晚
- Schema-on-write (Delta Lake): 写入时就验证 → **fail fast**，问题在入口就被发现
- 我选择 schema-on-write 因为: 下游消费者不应该需要处理 schema 异常

### 技术点 5: Auto Loader vs spark.read

| | spark.read | Auto Loader |
|---|---|---|
| 文件发现 | 每次扫描整个目录 O(n) | 增量发现新文件 O(1) |
| Exactly-once | 需要自己管理 | 通过 checkpoint 自动保证 |
| Schema inference | 每次重新推断 | 一次推断 + evolution |
| 适用 | 一次性加载 | 持续增量加载 |

---

## 项目 2: GLP Technology (从零构建)

### 一句话概述
> "As the founding data hire at a consumer lending startup, I built the entire data infrastructure — PySpark ETL pipelines, credit scoring system, and data quality framework — from scratch."

### 面试官最好奇的: 如何从零开始？

**决策过程（背诵）**:

> "My first week, I didn't write any code. I sat with the business team to understand the core metrics — default rate, collection rate, customer acquisition cost, and loan lifetime value. Then I mapped out all data sources and their relationships.
>
> My priority order was: first, data ingestion — because without data, nothing else matters. Second, analytics capability — so the team could make data-driven decisions. Third, automation — credit scoring models and monitoring.
>
> In the first month, I built the PySpark ETL pipeline to ingest loan data from MySQL, external credit bureau APIs, and user behavior logs. By month two, I had the feature engineering pipeline and a first version of the credit scoring model. By month three, we had automated credit decisions in production."

### PySpark ETL 管道技术深度

**数据源**:
- MySQL (贷款系统): 申请、审批、放款、还款、逾期
- 外部征信 API: 征信报告、黑名单查询
- 用户行为日志: App 内行为、停留时间、点击模式

**Transform 流程**:
1. 清洗: 去重（同一申请多次提交）、类型转换、缺失值标记
2. 特征工程:
   - 申请特征: 年龄、收入、地区、申请渠道
   - 行为特征: App 停留时间、页面跳转模式
   - 征信特征: 历史违约次数、当前负债率
   - 贷款特征: 金额、期限、利率
3. 全生命周期聚合: 每笔贷款从申请到结清的完整视图

**为什么 PySpark 而不是 Pandas?**:
- 数据量: 百万级贷款记录 × 数百特征 → 超出单机内存
- 可扩展: 随业务增长无需重写
- 与 Hive/HDFS 集成: 公司已有 Hadoop 基础设施

### 信贷评分模型 — trade-off

**为什么 XGBoost/LightGBM 而不是 Deep Learning?**:
1. **数据量有限**: 初创公司只有几十万条贷款记录，不够训练 DNN
2. **可解释性**: 中国监管要求能解释拒贷原因 → GBDT 有 feature importance
3. **迭代速度**: GBDT 训练分钟级 vs DNN 小时级，初创需要快速迭代
4. **缺失值处理**: XGBoost 原生处理缺失值（征信数据经常缺失）

---

## 项目 3: Baiquan Investment (数据质量)

### 一句话概述
> "Built market data infrastructure for quantitative research — ingesting feeds from multiple vendors for 3,000+ securities with a cross-source validation framework to ensure data integrity."

### 跨源验证框架 — 深度

**问题**: 同一只股票在不同供应商的数据不一致
- 供应商 A 的收盘价 vs 供应商 B 可能差 0.1-1%
- 某个供应商可能漏掉某个交易日的数据
- 股票停牌/除权除息处理方式不同

**我的解决方案**:
1. **完整性检查**: 每个交易日，每只证券必须有 OHLCV → 缺失 = 告警
2. **一致性检查**: |price_A - price_B| / price_A > 0.5% → 标记
3. **时效性检查**: 最新数据时间戳 vs 当前时间 → 检测陈旧数据
4. **统计异常检测**: 日波动率 > 3σ → 可能是数据错误（或真实极端事件，需人工判断）

**与 Swisscom 的关联**:
> "This is directly transferable to telecom — network metrics from different monitoring systems should be consistent. If cell tower A reports 1000 events but the central system only received 800, that's a data quality issue that could mask a real network problem."

### 因子计算引擎 — 向量化

**为什么 NumPy 向量化而不是 Python 循环?**:
- Python for-loop: 每次迭代有解释器开销
- NumPy: C 底层实现，SIMD 指令，一次操作整个数组
- 实际提升: 100x+ 加速（从分钟级到秒级）

```python
# 慢: Python 循环
for i in range(len(prices)):
    returns[i] = (prices[i] - prices[i-1]) / prices[i-1]

# 快: NumPy 向量化
returns = np.diff(prices) / prices[:-1]
```

---

## 项目 4: Expedia Hotel Recommendation (简短版)

### 30 秒版本（背诵）
> "For the Expedia Hotel Recommendation challenge on Kaggle, I built a ranking model on 4.9 million booking records. The key insight was treating this as a learning-to-rank problem using NDCG as the metric, not binary classification. I engineered features around user search patterns — like destination popularity, time-of-day booking preferences, and hotel cluster affinity. Used XGBoost for its native handling of missing values and achieved top 5% with an NDCG@5 of 0.392."

### 如果追问 NDCG
- NDCG = Normalized Discounted Cumulative Gain
- 衡量排名列表的质量 — 正确答案排在前面得分更高
- DCG 对排名位置做对数折扣: position 1 比 position 5 重要得多
- @5 = 只看前 5 个推荐结果

---

## 项目 5: 硕士论文 (简短版)

### 30 秒版本（背诵）
> "My thesis was on Uncertainty Quantification in Deep Reinforcement Learning under noisy environments. I ran 150 training runs across 5 different UQ methods on an HPC cluster using SLURM. The key finding was a 'noise paradox' — certain UQ methods actually performed better with noise than without, which was statistically significant at p less than 0.001. This challenged the conventional assumption that noise always degrades model performance."

---

# ═══════════════════════════════════════════
# 第三章：Spark 深度概念 — 口头能讲透
# ═══════════════════════════════════════════

## 3.1 Spark 查询执行全流程

### 背诵版（2分钟口述）

> "When you submit a SQL query or DataFrame operation to Spark, it goes through several stages.
>
> First, the **parser** converts SQL into an unresolved logical plan — it's basically a tree of operations without knowing what the column names actually refer to.
>
> Then the **analyzer** resolves column names and types using the catalog — now Spark knows what each column is.
>
> Next, the **Catalyst optimizer** applies rule-based optimizations — predicate pushdown, column pruning, constant folding, join reordering. For example, if you have a filter after a join, Catalyst pushes the filter before the join to reduce the data early.
>
> After logical optimization, the **planner** generates physical plans — choosing between different join strategies like Broadcast Hash Join versus Sort-Merge Join based on table sizes.
>
> Finally, **Tungsten's whole-stage code generation** fuses multiple operators into a single Java method, avoiding virtual function call overhead. This is essentially compiling the query into optimized JVM bytecode."

### 关键优化规则（记忆）

| 优化 | 做什么 | 为什么重要 |
|------|--------|-----------|
| **Predicate Pushdown** | 把 WHERE 推到数据源层 | 减少读取的数据量。对 Parquet 可跳过整个 row group |
| **Column Pruning** | 只读需要的列 | 列式存储中巨大的 I/O 节省 |
| **Constant Folding** | 编译时计算常量 `2+3→5` | 减少运行时计算 |
| **Join Reordering** | 小表先 join，大表后 join | 减少中间结果大小 |
| **Broadcast Join** | 小表 (<10MB) 广播到所有节点 | 避免 shuffle（最昂贵的操作）|

### Tungsten — 为什么快

传统执行 (Volcano model):
```
每个操作符是一个迭代器
Filter.next() → Project.next() → Scan.next()
每次调用都是虚函数 → CPU 分支预测失败 → 慢
```

Tungsten whole-stage codegen:
```
将 Filter + Project + Scan 融合为一个 Java 方法
编译为 JVM 字节码 → 没有虚函数调用 → CPU 流水线高效
```

**与 Yannis 的联系**: 他的 LegoBase 做的是同样的事 — 将高层查询"编译"为低层代码。Tungsten 是这个理念在工业界的实现。

---

## 3.2 Shuffle — 最昂贵的操作

### 什么触发 Shuffle
- `groupBy()` / `groupByKey()`
- `join()` (除了 broadcast join)
- `repartition()`
- `distinct()`
- `orderBy()` / `sort()`

### Shuffle 的代价
```
Executor A                    Executor B
[partition 0] ──写临时文件──→ [磁盘]
              ──网络传输──→   [partition 0']
              ──反序列化──→  [内存]
```
三重代价: **磁盘 I/O + 网络传输 + 序列化/反序列化**

### 优化策略（记忆）

| 策略 | 适用场景 | 原理 |
|------|---------|------|
| **Broadcast Join** | 一侧 <10MB | 小表广播到所有节点，零 shuffle |
| **调整 partition 数** | shuffle partition 过多/过少 | `spark.sql.shuffle.partitions` 默认 200，需按数据量调 |
| **Pre-partitioning** | 多次 join 同一个 key | 提前 `repartition(key)` 避免重复 shuffle |
| **Coalesce** | 过滤后分区太多 | `coalesce(n)` 减少分区数，不触发 full shuffle |
| **Map-side aggregation** | `reduceByKey` vs `groupByKey` | `reduceByKey` 先在 map 端局部聚合，减少 shuffle 数据量 |

---

## 3.3 Data Skew — 检测与解决

### 什么是 Data Skew
某些 key 的数据量远大于其他 → 一个 task 处理 90% 的数据，其他 task 空闲等待

### 检测方法
1. Spark UI → Stages → 看 task 时间分布
2. 如果 median task time = 5s 但 max task time = 300s → 严重 skew
3. 查看 shuffle read size per task — 不均匀说明有 skew

### 解决方案（记忆）

**方案 1: Salting**
```python
# 原始 join (skewed)
df_a.join(df_b, "user_id")

# Salting: 给热 key 加随机前缀
df_a_salted = df_a.withColumn("salt", F.concat(F.col("user_id"), F.lit("_"), (F.rand() * 10).cast("int")))
df_b_exploded = df_b.crossJoin(spark.range(10).withColumnRenamed("id", "salt_id"))
                     .withColumn("salt", F.concat(F.col("user_id"), F.lit("_"), F.col("salt_id")))

# Join on salted key → 数据分散到 10 个 partition
df_a_salted.join(df_b_exploded, "salt")
```
缺点: 右表膨胀 10x → 只在严重 skew 时使用

**方案 2: Broadcast Join**
- 如果 skewed 的那一侧表足够小 → 广播它 → 完全避免 shuffle

**方案 3: AQE (Adaptive Query Execution)**
- Spark 3.0+: `spark.sql.adaptive.enabled=true`
- 运行时检测 skew → 自动拆分大 partition 为多个 sub-tasks
- **推荐**: 先开 AQE，只有 AQE 不够时才手动 salting

### 我的实际经验
> "In the Financial Lakehouse, BTC and ETH trading volume was orders of magnitude higher than other tokens. When aggregating by symbol, the BTC partition would be 100x larger than most others. I addressed this by Z-ordering the data by symbol — which distributes BTC data across multiple files — and using AQE for dynamic partition splitting."

---

## 3.4 Delta Lake

### Delta Lake vs 普通 Parquet（记忆表）

| 特性 | Parquet on S3 | Delta Lake |
|------|--------------|------------|
| ACID 事务 | ❌ 无 | ✅ 有 (transaction log) |
| 并发写入 | 可能数据损坏 | 乐观并发控制 |
| Schema enforcement | ❌ | ✅ 写入时验证 |
| Schema evolution | 手动处理 | mergeSchema=true |
| Time travel | ❌ | ✅ 可查历史版本 |
| MERGE INTO | ❌ | ✅ upsert/SCD |
| 小文件问题 | 严重 | OPTIMIZE 命令 |
| Data skipping | 有限 (row group stats) | Z-ordering 增强 |

### Delta 事务日志
- `_delta_log/` 目录下的 JSON 文件
- 每次写入产生一个新的 commit (00000001.json, 00000002.json, ...)
- 读取时: 重放所有 commits → 知道当前版本有哪些文件
- 每 10 个 commit 自动创建 checkpoint (Parquet 格式) → 加速重放

---

## 3.5 Batch vs Streaming — 选择框架

### 决策树（背诵）

```
延迟要求是什么？
├── 天级 / 小时级 → Batch (Spark batch, Hive, traditional ETL)
├── 分钟级 → Micro-batch (Spark Structured Streaming, default)
├── 秒级 → Micro-batch (Structured Streaming, trigger=1s)
└── 毫秒级 → Event-by-event (Flink, Kafka Streams)
```

### Spark Structured Streaming 三种 trigger

| Trigger | 延迟 | 吞吐量 | 适用 |
|---------|------|--------|------|
| `processingTime="10s"` | ~10s | 高 | 大多数场景 |
| `once=True` | N/A | 最高 | 增量批处理 (每天跑一次) |
| `continuous` (实验性) | ~1ms | 较低 | 超低延迟需求 |

---

# ═══════════════════════════════════════════
# 第四章：Kafka + 流处理概念
# ═══════════════════════════════════════════

## 4.1 Kafka 架构（记忆图）

```
Producer ──→ Broker Cluster ──→ Consumer Group
              │
              ├── Broker 1
              │     ├── Topic A, Partition 0 (Leader)
              │     └── Topic B, Partition 1 (Follower)
              ├── Broker 2
              │     ├── Topic A, Partition 1 (Leader)
              │     └── Topic B, Partition 0 (Follower)
              └── Broker 3
                    └── (replicas)
```

### 核心概念（一句话定义，背诵）

| 概念 | 一句话 |
|------|--------|
| **Topic** | 消息的逻辑分类，类似数据库的表 |
| **Partition** | Topic 的物理分片，是 Kafka 并行的基本单位 |
| **Offset** | 消息在 partition 内的序号，consumer 用它标记读到哪了 |
| **Consumer Group** | 一组 consumer 共同消费一个 topic，每个 partition 只被组内一个 consumer 读 |
| **Replication Factor** | 每个 partition 的副本数 (通常 3)，容错用 |
| **ISR** | In-Sync Replicas，与 leader 保持同步的副本集合 |
| **Producer Acks** | `acks=0` 不等确认; `acks=1` leader 确认; `acks=all` ISR 全部确认 |

### Partition 内保证顺序，跨 Partition 不保证

这是 Kafka 最重要的语义。

**面试回答模板**:
> "Kafka guarantees ordering within a single partition, but not across partitions. So if you need events from the same cell tower to be processed in order, you should partition by cell_tower_id. The trade-off is that if one tower generates much more traffic than others, you'll get a hot partition — which is essentially the data skew problem."

### Exactly-Once 语义（三个组件）

1. **Idempotent Producer**: `enable.idempotence=true` → Kafka 用 (producer_id, sequence_number) 去重
2. **Transactional Producer**: 原子地写入多个 partition（要么全成功，要么全失败）
3. **Consumer read_committed**: 只读已提交的消息

**端到端 exactly-once** = idempotent producer + transactional writes + consumer read_committed + 下游幂等处理

### Consumer Group Rebalancing

**触发条件**: consumer 加入/离开/crash，或 partition 数变化
**问题**: rebalancing 期间，**所有 consumer 暂停**
**优化**: Cooperative rebalancing (Kafka 2.4+) → 只重新分配变化的 partition，不暂停所有

---

## 4.2 Kafka vs 竞品

| | Kafka | Kinesis | Pulsar |
|---|---|---|---|
| 管理方式 | 自管 / Confluent Cloud | AWS 全管 | 自管 / StreamNative |
| 吞吐 | 极高 (MB/s per partition) | 1MB/s per shard | 高 |
| 保留 | 可配置 (天/周/永久) | 7天 (max 365天) | 分层存储 (无限) |
| 分区扩展 | 手动 | 手动 (resharding) | 自动 |
| 适用 | 通用流平台 | AWS 生态 | 多租户 |

---

## 4.3 Schema Registry

**为什么需要**:
- Kafka 只存字节流，不关心 schema
- Producer 和 consumer 必须agree schema → 否则反序列化失败

**工作方式**:
```
Producer → 注册 schema (Avro/Protobuf) → 获得 schema ID
         → 消息 = [schema_id][payload]
Consumer → 读取 schema_id → 从 Registry 获取 schema → 反序列化
```

**兼容性级别**:
- BACKWARD: 新 schema 能读旧数据 (删列OK，加列需默认值)
- FORWARD: 旧 schema 能读新数据 (加列OK，删列需默认值)
- FULL: 双向兼容

---

# ═══════════════════════════════════════════
# 第五章：系统设计 — 口头对话
# ═══════════════════════════════════════════

## 5.1 核心题: "设计 Swisscom 的实时网络事件处理管道"

### 5分钟口述版本（背诵框架，自然表达）

**Step 1 — 需求澄清 (30s)**:
> "Before diving into the design, I'd want to understand:
> - What's the event volume? For a major telco like Swisscom, I'd estimate around 200 billion events per day, roughly 2 TB.
> - What's the latency requirement? Real-time alerts probably need sub-minute, while analytics can tolerate hourly batches.
> - What are the key use cases? I'm guessing anomaly detection, capacity planning, and network optimization."

**Step 2 — 高层架构 (2 min)**:
> "I'd design a dual-path architecture:
>
> For ingestion, Kafka as the central event bus — it handles the throughput, provides durability, and decouples producers from consumers.
>
> For processing, two parallel paths: a streaming path using Spark Structured Streaming for near-real-time aggregations — 5-minute windows of tower activity, signal strength trends. And a fast path using Flink or simple Kafka Streams for sub-second alerting on critical events like tower outages.
>
> For storage, Medallion Architecture on S3: Bronze for raw events, Silver for cleaned and enriched data, Gold for business-level aggregations.
>
> For serving: Redshift for historical analytics, a real-time dashboard fed from the streaming layer, and an alerting service connected to PagerDuty."

**Step 3 — 关键决策 (1.5 min)**:
> "A few key design decisions:
>
> Partition key: I'd partition Kafka by region rather than individual tower. With thousands of towers, per-tower partitioning creates too many partitions. Region gives good data locality for geographic analysis while keeping partition count manageable.
>
> Watermarking: Network events from weak-signal areas can arrive late, so I'd set a watermark of maybe 5-10 minutes based on observed delay distribution.
>
> Schema evolution: Using Avro with Schema Registry, with BACKWARD compatibility — so we can add new event fields without breaking existing consumers."

**Step 4 — 数据质量 (1 min)**:
> "Data quality is critical for network monitoring. I'd implement:
> - Completeness checks: every tower should report every minute — missing data might indicate a real outage versus a data pipeline issue.
> - Cross-source validation: metrics from different monitoring systems should be consistent.
> - Freshness monitoring: alert if the latest event timestamp is more than 5 minutes old.
> - This is very similar to what I built at Baiquan — cross-source validation for market data."

---

## 5.2 附加题: "如何从 on-prem Hadoop 迁移到 AWS"

### 3分钟口述版本

> "I'd approach this as a phased migration, not a big-bang cutover.
>
> **Phase 1: Dual-write.** New data goes to both HDFS and S3 simultaneously. This gives us a safety net — if anything goes wrong on AWS, we still have the Hadoop pipeline.
>
> **Phase 2: Migrate batch jobs.** Convert MapReduce/Hive jobs to Spark on EMR or Glue. The logic stays the same, the execution engine changes. Validate by running both pipelines and comparing outputs — any discrepancy means we have a bug.
>
> **Phase 3: Historical data migration.** Use tools like AWS DataSync or custom Spark jobs to copy historical data from HDFS to S3. This can run in parallel without affecting production.
>
> **Phase 4: Gradual cutover.** Switch one pipeline at a time from Hadoop to AWS. Monitor closely for 2 weeks per pipeline before moving to the next.
>
> **Key risks:** Network egress costs if the Hadoop cluster is in Switzerland and AWS region is in Europe. Data governance — making sure all access controls are replicated. And team upskilling — engineers need to learn AWS services."

---

## 5.3 数据建模概念

### Star Schema vs Snowflake（记忆）

| | Star Schema | Snowflake Schema |
|---|---|---|
| 结构 | Fact 表 + Dimension 表 (一层) | Fact 表 + Dimension 表 (多层 normalized) |
| 查询性能 | 快 (fewer joins) | 慢 (more joins) |
| 存储 | 冗余 (denormalized) | 紧凑 (normalized) |
| 维护 | 简单 | 复杂 |
| 适用 | OLAP, BI 查询 | 严格规范化需求 |

**Swisscom 场景**:
- Fact 表: `network_events` (event_id, timestamp, cell_tower_id, event_type, signal_strength, ...)
- Dimension 表: `dim_cell_tower` (tower_id, location, region, technology, capacity, ...)
- Dimension 表: `dim_device_type` (device_id, manufacturer, model, os_version, ...)
- Star schema 更适合: 分析查询模式固定，需要快速聚合

### SCD Type 2（记忆）

**场景**: 基站的配置发生变化（例如从 4G 升级到 5G），需要保留历史

```
| tower_id | technology | valid_from  | valid_to    | is_current |
|----------|-----------|-------------|-------------|------------|
| T001     | 4G        | 2020-01-01  | 2025-06-30  | false      |
| T001     | 5G        | 2025-07-01  | NULL        | true       |
```

实现: `MERGE INTO` (Delta Lake 原生支持)

### ETL vs ELT（记忆）

| | ETL | ELT |
|---|---|---|
| 顺序 | Extract → Transform → Load | Extract → Load → Transform |
| 转换在哪 | 中间系统 (Spark/外部) | 目标系统 (data warehouse) |
| 适用 | 传统 RDBMS 目标 | 现代 data lake / warehouse |
| 优势 | 目标只存干净数据 | 保留原始数据，灵活 |
| 我的做法 | | ✅ Bronze 先加载，Silver 再转换 |

---

# ═══════════════════════════════════════════
# 第六章：面试官策略 — 建立共鸣
# ═══════════════════════════════════════════

## 6.1 与 Yannis 共鸣的话术

**如果讨论到 Spark 优化**:
> "What I find elegant about Spark's Catalyst is that it essentially compiles a declarative SQL query into optimized physical operations — the developer writes what they want, and the optimizer figures out how to do it efficiently. It's a practical example of abstraction without sacrificing performance."

→ 直接呼应他的 "Abstraction Without Regret" 哲学

**如果讨论到 Scala vs Python**:
> "I've primarily used PySpark because of the faster development cycle for data pipelines. But I understand the trade-off — you lose the compile-time type safety that Scala's Dataset API provides. For a production system where correctness is critical, I can see the value of the stronger type system, and that's something I'm keen to learn."

→ 展示你不是 Python 教条主义者

**如果他提到他的研究**:
> "That's really interesting — the idea of generating optimized low-level code from high-level specifications is powerful. In a way, Delta Lake's Z-ordering serves a similar purpose — it's a declarative hint to the storage layer that enables the query engine to do aggressive data skipping without the developer manually partitioning the data."

→ 把他的研究兴趣连接到你的实际经验

### 不要做的事

- ❌ 不要说 "I read your papers" — 太明显在拍马屁
- ❌ 不要假装懂 Scala metaprogramming — 他会深挖
- ✅ 自然地在技术讨论中展示你理解底层机制

---

## 6.2 行为问题准备

### "Why Swisscom?"（背诵）

> "Three things attracted me. First, the scale — processing billions of network events per day is a genuine big data challenge, not just a buzzword. Second, the technical environment — Spark, Kafka, AWS, Delta Lake — it's a modern stack that I'm already experienced with. Third, the culture — I visited the SDC Rotterdam page and it's clear this is an international engineering hub, not just an offshore center. The team is building core data products that directly shape Swisscom's network strategy."

### "Tell me about a technical failure"（背诵）

> "At GLP, early in the credit scoring pipeline, I had a production incident where the feature engineering job silently produced NULL values for a key feature — the customer's historical repayment rate. The credit model still ran, but it was making decisions without critical information, which led to a few bad approvals.
>
> What I learned: I built a data quality gate between the feature engineering step and the model scoring step. It checked for NULL rates, value distributions, and feature coverage — and it would halt the pipeline and alert me if anything looked wrong. This 'fail fast' philosophy is exactly what I later implemented as the quarantine pattern in the Financial Lakehouse."

### "How do you handle disagreements with colleagues?"（背诵）

> "I focus on data, not opinions. At Baiquan, there was a disagreement about whether to use a single-vendor or multi-vendor data feed. I proposed a two-week experiment — run both in parallel and compare data quality metrics. The results clearly showed that the multi-vendor approach caught errors the single-vendor approach missed. By letting the data decide, we avoided a political argument."

### Career gap (2019-2023)（背诵 — 30秒版）

> "During that period, I made a deliberate decision to invest in my long-term career. I did independent investing using quantitative skills, learned English and German, and spent a year preparing for graduate school. It led me to the AI Master's at VU Amsterdam, which gave me both the theoretical depth and the European career foundation I needed."

---

# ═══════════════════════════════════════════
# 第七章：你的提问 — 准备6个，现场选3个
# ═══════════════════════════════════════════

### 技术类（首选 — 展示深度）

**Q1**: "Could you walk me through what a typical data pipeline looks like in the Polaris team — from raw network data to the final data product? I'm curious about the scale and whether the processing is primarily batch, streaming, or a hybrid approach."

**Q2**: "I noticed Swisscom's GitHub org has active forks of Calcite and Flink updated as recently as 2025. Does the team contribute patches back to the upstream projects, or are these customized for internal use?"

### 团队类（展示文化关注）

**Q3**: "What does the team composition look like? How do data engineers, data scientists, and software engineers collaborate on a typical project?"

**Q4**: "What would a realistic first project look like for someone joining the team? What would success look like in the first 90 days?"

### 战略类（给高级领导，如果 Monica 在场）

**Q5**: "With the AWS migration underway and the Vodafone Italia integration, how is the Polaris team's roadmap evolving? Are there new data challenges emerging?"

**Q6**: "What's the biggest technical challenge the team is currently facing?"

---

# ═══════════════════════════════════════════
# 第八章：数字速查表 — 面试时放在旁边
# ═══════════════════════════════════════════

### 你的数字
| 指标 | 数字 |
|------|------|
| 工作经验 | ~6 年 (2013-2019) |
| 硕士 GPA | 8.2/10 |
| Deep Learning 课程 | 9.5/10 |
| GLP 角色 | Founding data hire (第一个数据员工) |
| Baiquan 证券数 | 3,000+ securities |
| Expedia 数据量 | 4.9M booking records |
| Expedia Kaggle 排名 | Top 5% (NDCG@5 = 0.392) |
| 论文实验 | 150 training runs, 5 UQ methods, p<0.001 |
| Ele.me 成果 | 2x reactivation rate, 30% query optimization |
| 认证 | Databricks Data Engineer Professional (2026) |

### Swisscom 数字（展示你做了功课）
| 指标 | 数字 |
|------|------|
| 日网络事件 | 200 亿 / 天 |
| 日数据量 | 2 TB / 天 |
| SIM 卡追踪 | 600 万 |
| 处理吞吐量 | 600,000+ data points/sec |
| Rotterdam 员工 | 400+ 人 |
| 国籍 | 60+ |
| Vodafone Italia 收购 | 80 亿欧元 (2024.12 完成) |
| 平台 | 40 platforms, 2,700 nodes |
| 团队构成 | DE 30-40%, SWE 40%, DS 10-20%, DevOps 10% |

### Spark 关键参数
| 参数 | 默认值 | 用途 |
|------|--------|------|
| `spark.sql.shuffle.partitions` | 200 | shuffle 后的分区数 |
| `spark.sql.autoBroadcastJoinThreshold` | 10MB | 小于此值自动 broadcast |
| `spark.sql.adaptive.enabled` | true (3.0+) | AQE 开关 |
| `spark.executor.memory` | 1g | executor 堆内存 |
| `spark.executor.memoryOverhead` | 10% of executor memory | 堆外内存 |

---

# ═══════════════════════════════════════════
# 第九章：面试当天 Checklist
# ═══════════════════════════════════════════

### 前一晚
- [ ] 测试 MS Teams 音频/视频
- [ ] 准备好耳机（有线优先，避免蓝牙断连）
- [ ] 检查网络稳定性
- [ ] 充好电 / 接好电源

### 面试前 2 小时
- [ ] 停止学新东西
- [ ] 打开此文档的速查表（第八章）
- [ ] 准备水 + 纸笔
- [ ] 关闭所有不必要的程序
- [ ] 穿着: 上半身 smart casual

### 面试前 15 分钟
- [ ] 打开 Teams，进入等待室
- [ ] 把速查表放在屏幕旁边（或第二屏幕）
- [ ] 深呼吸三次
- [ ] 默念一遍 2 分钟自我介绍

### 面试中
- [ ] 面试官说话时，**点头 + 偶尔重述**（"So if I understand correctly, you're asking about..."）
- [ ] 回答每个问题先给 **1 句话总结**，再展开
- [ ] 不会的问题: "That's a great question. I haven't worked with X directly, but let me think about how I'd approach it..." → 说出思考过程
- [ ] 用具体数字和具体项目名称
- [ ] 最后 10 分钟: 问准备好的 3 个问题

### 面试结束
- [ ] "Thank you for the discussion. This has really reinforced my interest in the Polaris team. What are the next steps?"
- [ ] 面试后 24 小时内: 给 Lilla (HR) 发感谢邮件，提及面试中的具体讨论点
