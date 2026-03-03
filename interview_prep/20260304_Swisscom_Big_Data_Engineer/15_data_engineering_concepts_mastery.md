# 模块 B：数据工程概念深度掌握手册

> **目标**: 对每个核心概念达到第 4 层理解深度，能够在苏格拉底式追问中自信回答
> **时长**: 8 小时深度学习 + 苏格拉底式对话
> **面试时间**: 2026-03-04 10:00 CET (剩余 22 小时)

---

## 📚 手册结构

本手册分为两大部分：

### Part 1: Spark 内部机制 (4小时)
1. Spark 查询执行全流程 (Catalyst + Tungsten)
2. Shuffle 机制与优化
3. Data Skew 检测与解决
4. Batch vs Streaming 的选择
5. Delta Lake 的核心价值

### Part 2: 数据工程模式 (4小时)
6. 数据建模 (Star Schema, Snowflake, Kimball vs Inmon)
7. 数据质量框架
8. ETL vs ELT
9. SCD (Slowly Changing Dimensions)
10. 流处理模式与保证

---

# Part 1: Spark 内部机制深度掌握

---

## 1. Spark 查询执行全流程 (Catalyst + Tungsten)

### 🎯 核心问题
**面试官会问**: "Explain how Spark executes a SQL query from start to finish."

### 📊 第 1 层：基础概念
Spark 使用 Catalyst 优化器将 SQL 查询转换为优化的执行计划，然后通过 Tungsten 引擎执行。

### 🔍 第 2 层：流程分解
```
SQL/DataFrame API
    ↓
Unresolved Logical Plan (AST)
    ↓
Resolved Logical Plan (catalog lookup)
    ↓
Optimized Logical Plan (rule-based optimization)
    ↓
Physical Plans (multiple candidates)
    ↓
Selected Physical Plan (cost-based optimization)
    ↓
RDDs + Whole-Stage Code Generation
    ↓
Execution
```

### 🧠 第 3 层：每个阶段的机制

#### 3.1 Unresolved Logical Plan
- **输入**: SQL 字符串或 DataFrame API 调用
- **输出**: 抽象语法树 (AST)
- **特点**: 此时还不知道表/列是否存在，只是语法解析

**示例**:
```sql
SELECT name, SUM(amount)
FROM transactions
WHERE date > '2026-01-01'
GROUP BY name
```

转换为:
```
Project(name, SUM(amount))
  └─ Aggregate(groupBy=name, agg=SUM(amount))
      └─ Filter(date > '2026-01-01')
          └─ Scan(transactions)
```

#### 3.2 Resolved Logical Plan
- **操作**: Catalog lookup — 检查表、列是否存在，解析数据类型
- **输出**: 带类型信息的逻辑计划
- **失败点**: 如果表不存在或列名错误，在这里报错

#### 3.3 Optimized Logical Plan
- **操作**: 应用 rule-based optimization rules
- **常见优化规则**:
  1. **Predicate Pushdown**: 将 Filter 尽可能下推到数据源
  2. **Projection Pruning**: 只读取需要的列
  3. **Constant Folding**: 计算常量表达式 (如 `1 + 1` → `2`)
  4. **Boolean Expression Simplification**: 简化逻辑表达式

**示例优化**:
```
原始:
Filter(date > '2026-01-01')
  └─ Scan(transactions)

优化后 (Predicate Pushdown):
Scan(transactions, pushFilters=[date > '2026-01-01'])
```

#### 3.4 Physical Plan Selection
- **操作**: 为每个逻辑操作选择物理实现
- **示例**: `Join` 可以实现为:
  - BroadcastHashJoin (小表 broadcast)
  - SortMergeJoin (大表 shuffle)
  - ShuffledHashJoin (hash-based shuffle)
- **Cost-Based Optimization (CBO)**: 使用统计信息 (表大小、列基数) 选择最优物理计划

#### 3.5 Whole-Stage Code Generation (Tungsten)
- **核心思想**: 将整个 stage 的操作编译为单个 Java 函数，避免虚函数调用和对象创建
- **效果**: 10x+ 性能提升 (相比 Volcano iterator model)

**传统 Volcano Model**:
```java
// 每个操作符是一个 iterator
for (row in filter.next()) {
    for (row in project.next()) {
        emit(row)
    }
}
// 大量虚函数调用，CPU cache miss
```

**Whole-Stage Code Gen**:
```java
// 编译为单个函数
while (scan.hasNext()) {
    row = scan.next()
    if (row.date > threshold) {  // filter
        result.name = row.name    // project
        result.amount = row.amount
        emit(result)
    }
}
// 紧凑的循环，CPU cache 友好
```

### 💡 第 4 层：Trade-offs 与实战经验

#### 4.1 Catalyst 的局限性
**问题**: Rule-based optimization 不考虑数据分布
**示例**:
```sql
SELECT * FROM large_table
WHERE rare_column = 'X'  -- 只有 0.01% 的行满足
```
- Catalyst 会 pushdown filter，但不知道选择性
- 如果 `rare_column` 没有索引/统计信息，可能全表扫描

**解决**:
- 使用 `ANALYZE TABLE` 收集统计信息
- 启用 CBO: `spark.sql.cbo.enabled=true`

#### 4.2 Code Generation 的开销
**问题**: 编译 Java 代码需要时间
**Trade-off**:
- 小查询 (< 1000 rows): code gen 开销 > 收益
- 大查询 (millions of rows): code gen 收益 >> 开销

**配置**: `spark.sql.codegen.wholeStage=true` (默认开启)

#### 4.3 你的实战经验 (Financial Lakehouse)
> "In my Financial Lakehouse project, I noticed that queries on the Gold layer were 6.7x faster after Z-ordering. This is because Catalyst's predicate pushdown combined with Delta Lake's data skipping — the optimizer pushed the filter down to the scan, and Delta's file-level statistics allowed Spark to skip 85% of the files without reading them. This is a perfect example of how logical optimization (pushdown) and physical optimization (data layout) work together."

### 🔗 与 Yannis 的研究联系
Yannis 的 LegoBase 项目也是关于 "编译" 查询为高效代码。你可以说:
> "I find it fascinating how Spark's whole-stage code generation essentially compiles high-level DataFrame operations into tight loops — it's similar to the idea behind LegoBase, where you trade compilation time for runtime performance. The key insight is that abstraction doesn't have to mean overhead."

---

## 2. Shuffle 机制与优化

### 🎯 核心问题
**面试官会问**: "What is shuffle in Spark, why is it expensive, and how do you avoid it?"

### 📊 第 1 层：基础概念
Shuffle 是 Spark 中跨节点重新分配数据的过程，发生在需要按 key 重新分组的操作中 (如 `groupBy`, `join`, `repartition`)。

### 🔍 第 2 层：Shuffle 的机制

#### 2.1 什么操作会触发 Shuffle？
- `groupBy` / `reduceByKey` / `aggregateByKey`
- `join` (除了 broadcast join)
- `repartition` / `coalesce` (增加 partition 数)
- `distinct`
- `sortBy`

#### 2.2 Shuffle 的物理过程
```
Map Side (Shuffle Write):
1. 每个 task 将输出按 partition key hash 到 N 个 bucket
2. 写入本地磁盘 (shuffle files)
3. 通知 Driver: "我的 shuffle 数据在 node X 的 /path/to/shuffle/file"

Reduce Side (Shuffle Read):
1. 每个 reduce task 从所有 map task 拉取属于自己的 partition
2. 通过网络传输
3. 反序列化
4. 可能需要排序 (如果是 sort-based shuffle)
```

### 🧠 第 3 层：为什么 Shuffle 昂贵？

#### 3.1 三大开销
1. **磁盘 I/O**:
   - Map side 写临时文件
   - Reduce side 可能 spill to disk (如果内存不够)

2. **网络传输**:
   - 数据在节点间传输
   - 带宽成为瓶颈

3. **序列化/反序列化**:
   - Map side 序列化后写入
   - Reduce side 读取后反序列化
   - CPU 密集

#### 3.2 Shuffle 的内存管理
Spark 使用 **Unified Memory Management**:
```
Total Memory
├─ Execution Memory (60%)  ← shuffle, join, sort 使用
└─ Storage Memory (40%)    ← cache, broadcast 使用
```

如果 execution memory 不够:
- Spill to disk (写临时文件)
- 性能急剧下降 (磁盘 I/O 比内存慢 100x+)

### 💡 第 4 层：Shuffle 优化策略

#### 4.1 策略 1: Broadcast Join (避免 shuffle)
**适用场景**: 一个表很小 (< 10MB)，另一个表很大

**原理**: 将小表 broadcast 到所有 executor，避免 shuffle 大表

**示例**:
```python
# 默认: SortMergeJoin (两个表都 shuffle)
large_df.join(small_df, "key")

# 优化: BroadcastHashJoin (只 broadcast 小表)
from pyspark.sql.functions import broadcast
large_df.join(broadcast(small_df), "key")
```

**效果**:
- 无 shuffle 开销
- 但如果小表太大 (> executor memory)，会 OOM

**配置**: `spark.sql.autoBroadcastJoinThreshold=10MB` (默认)

#### 4.2 策略 2: Pre-partitioning (减少 shuffle 次数)
**适用场景**: 多次 join 同一个 key

**示例**:
```python
# 坏: 每次 join 都 shuffle
df1.join(df2, "user_id").join(df3, "user_id")
# → shuffle df1, shuffle df2, shuffle result, shuffle df3

# 好: 预先按 user_id partition
df1_part = df1.repartition("user_id")
df2_part = df2.repartition("user_id")
df3_part = df3.repartition("user_id")
df1_part.join(df2_part, "user_id").join(df3_part, "user_id")
# → 只 shuffle 一次 (repartition)，后续 join 无 shuffle
```

**原理**: 如果两个 DataFrame 已经按相同 key partition，Spark 知道相同 key 的数据在同一个 partition，无需 shuffle

#### 4.3 策略 3: 减少 Shuffle 数据量
**方法 1: Filter before shuffle**
```python
# 坏: shuffle 后 filter
df.groupBy("key").count().filter("count > 100")

# 好: filter 后 shuffle (如果可能)
df.filter("some_condition").groupBy("key").count()
```

**方法 2: 只 select 需要的列**
```python
# 坏: shuffle 所有列
df.groupBy("key").agg(sum("amount"))

# 好: 只 shuffle 需要的列
df.select("key", "amount").groupBy("key").agg(sum("amount"))
```

#### 4.4 策略 4: 调整 Shuffle Partition 数
**问题**: 默认 `spark.sql.shuffle.partitions=200`
- 数据量小 → 200 个 partition 太多 → 每个 partition 太小 → overhead 大
- 数据量大 → 200 个 partition 太少 → 每个 partition 太大 → OOM

**解决**: 根据数据量调整
```python
# 经验法则: 每个 partition 128MB-1GB
data_size_gb = 100
partition_size_mb = 512
num_partitions = (data_size_gb * 1024) / partition_size_mb
spark.conf.set("spark.sql.shuffle.partitions", int(num_partitions))
```

**或者使用 AQE (Adaptive Query Execution)**:
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "true")
# Spark 自动合并小 partition
```

### 🔗 你的实战经验
> "In my Financial Lakehouse, I used broadcast join for the crypto metadata table (coin names, symbols) which is only 2MB, joining with the 100GB market data table. This avoided shuffling the large table entirely. I also noticed that the default 200 shuffle partitions was too many for my 10GB daily incremental loads — each partition was only 50MB, causing excessive task scheduling overhead. I reduced it to 20 partitions, and the job time dropped from 8 minutes to 3 minutes."

---

## 3. Data Skew 检测与解决

### 🎯 核心问题
**面试官会问**: "How do you detect and handle data skew in Spark?"

### 📊 第 1 层：基础概念
Data Skew 是指数据在 partition 间分布不均，导致某些 task 处理的数据量远大于其他 task，成为瓶颈。

### 🔍 第 2 层：Skew 的表现

#### 2.1 如何检测 Skew？
**方法 1: Spark UI**
- 打开 Spark UI → Stages → 查看 task 的执行时间
- 如果某个 task 比其他慢 10x+，很可能是 skew

**方法 2: 查看 partition 大小**
```python
df.groupBy(spark_partition_id()).count().show()
# 如果某个 partition 的 count 远大于其他，说明 skew
```

#### 2.2 Skew 的常见原因
1. **Key 分布不均**: 某些 key 的数据量远大于其他 (如 BTC/ETH vs 小币种)
2. **NULL 值**: 所有 NULL 被 hash 到同一个 partition
3. **Hot key**: 某个用户/商品特别活跃

### 🧠 第 3 层：Skew 的解决方案

#### 3.1 方案 1: Salting (加盐)
**原理**: 给 skewed key 添加随机后缀，将其分散到多个 partition

**示例**:
```python
# 原始: BTC 的数据全在一个 partition
df.groupBy("symbol").count()

# Salting: 给 BTC 添加随机后缀 BTC_0, BTC_1, ..., BTC_9
from pyspark.sql.functions import concat, lit, rand
df_salted = df.withColumn(
    "symbol_salted",
    when(col("symbol") == "BTC",
         concat(col("symbol"), lit("_"), (rand() * 10).cast("int")))
    .otherwise(col("symbol"))
)
df_salted.groupBy("symbol_salted").count()

# 最后再聚合
result = df_salted.groupBy("symbol_salted").count() \
    .withColumn("symbol", regexp_replace("symbol_salted", "_\\d+$", "")) \
    .groupBy("symbol").sum("count")
```

**Trade-off**:
- 优点: 简单有效
- 缺点: 需要两次聚合，代码复杂

#### 3.2 方案 2: Broadcast Join (针对 join skew)
**适用场景**: Join 时一个表有 skew，但另一个表很小

**示例**:
```python
# 原始: large_df join small_df，但 large_df 的某些 key 很 skewed
large_df.join(small_df, "key")

# 优化: broadcast small_df
large_df.join(broadcast(small_df), "key")
# 即使 large_df skewed，也不影响 (因为没有 shuffle)
```

#### 3.3 方案 3: AQE Skew Join Optimization
**Spark 3.0+ 的自动优化**:
```python
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes", "256MB")
```

**原理**: Spark 在运行时检测 skewed partition，自动将其拆分为多个 sub-partition

#### 3.4 方案 4: 两阶段聚合 (针对 groupBy skew)
**原理**: 先局部聚合，再全局聚合

**示例**:
```python
# 原始: 直接 groupBy (skewed key 的数据全在一个 partition)
df.groupBy("symbol").agg(sum("amount"))

# 优化: 两阶段聚合
# Stage 1: 局部聚合 (加 random key)
df_local = df.withColumn("random_key", (rand() * 10).cast("int")) \
    .groupBy("symbol", "random_key").agg(sum("amount").alias("local_sum"))

# Stage 2: 全局聚合
df_global = df_local.groupBy("symbol").agg(sum("local_sum").alias("total"))
```

### 💡 第 4 层：你的实战经验

> "In my Financial Lakehouse, I encountered skew when aggregating crypto market data. Bitcoin and Ethereum together accounted for 40% of all records, while the other 98 coins shared the remaining 60%. This caused one partition to take 10x longer than others during hourly aggregations.
>
> I solved it using a hybrid approach:
> 1. For the top 10 coins (BTC, ETH, etc.), I used salting with a factor of 5 — splitting each into 5 sub-keys
> 2. For the remaining coins, I kept them as-is
> 3. After aggregation, I merged the salted results back
>
> This reduced the slowest task from 12 minutes to 2 minutes, bringing it in line with other tasks. The trade-off was slightly more complex code, but the 6x speedup was worth it."

---

## 4. Batch vs Streaming 的选择

### 🎯 核心问题
**面试官会问**: "When would you choose batch processing vs streaming?"

### 📊 第 1 层：基础概念
- **Batch**: 处理有界数据集 (bounded dataset)，一次性处理所有数据
- **Streaming**: 处理无界数据流 (unbounded stream)，持续处理新到达的数据

### 🔍 第 2 层：选择标准

#### 2.1 延迟要求
| 延迟要求 | 推荐方案 | 示例 |
|---------|---------|------|
| 小时级 | Batch (Airflow + Spark) | 每日报表、数据仓库 ETL |
| 分钟级 | Micro-batch (Structured Streaming) | 准实时仪表板、监控 |
| 秒级 | Micro-batch (小 trigger interval) | 实时推荐、欺诈检测 |
| 毫秒级 | Event-by-event (Flink) | 高频交易、网络路由 |

#### 2.2 数据到达模式
- **定期批量**: Batch (如每天凌晨收到一个文件)
- **持续流入**: Streaming (如 Kafka topic)
- **混合**: 两者都用 (如 Lambda Architecture)

#### 2.3 计算复杂度
- **简单聚合** (sum, count): Streaming 友好
- **复杂 join** (多表、多条件): Batch 更容易
- **机器学习训练**: Batch (需要全量数据)
- **机器学习推理**: Streaming (实时预测)

### 🧠 第 3 层：Streaming 的挑战

#### 3.1 状态管理
**问题**: Streaming 需要维护状态 (如 window 聚合、join)
**解决**: Spark Structured Streaming 使用 checkpoint 持久化状态

**示例**:
```python
# Stateful operation: 滑动窗口聚合
df.groupBy(
    window("timestamp", "1 hour", "10 minutes"),
    "symbol"
).agg(avg("price"))
# Spark 需要记住每个窗口的中间结果
```

#### 3.2 Late Data 处理
**问题**: 数据可能延迟到达 (网络延迟、系统故障)
**解决**: Watermarking

**示例**:
```python
df.withWatermark("timestamp", "10 minutes") \
    .groupBy(window("timestamp", "1 hour"), "symbol") \
    .agg(avg("price"))
# 超过 10 分钟的 late data 被丢弃
```

#### 3.3 Exactly-Once 语义
**问题**: 如何保证每条数据恰好处理一次？
**解决**: Checkpoint + Idempotent sink

**Spark Structured Streaming 的保证**:
- Source: Kafka offset 记录在 checkpoint
- Processing: 确定性计算 (相同输入 → 相同输出)
- Sink: 幂等写入 (Delta Lake 的 MERGE INTO)

### 💡 第 4 层：你的实战经验

> "In my Financial Lakehouse, I use both batch and streaming:
>
> **Streaming (Structured Streaming)**:
> - Real-time ingestion from Kafka (crypto market feeds)
> - 30-second micro-batches
> - Writes to Bronze layer (raw data)
> - Use case: Near real-time dashboard showing current prices
>
> **Batch (Auto Loader)**:
> - Daily historical data backfill from S3
> - Processes files that were missed or need reprocessing
> - Writes to the same Bronze layer
> - Use case: Ensuring completeness, handling late-arriving files
>
> The key insight is that Bronze layer doesn't care whether data came from streaming or batch — it's just append-only. This unified architecture (Medallion on Delta Lake) allows me to have both real-time and batch pipelines writing to the same tables without conflicts.
>
> The trade-off is complexity — I need to ensure idempotency (using MERGE INTO in Silver layer) so that if the same data arrives via both paths, it's deduplicated."

---

## 5. Delta Lake 的核心价值

### 🎯 核心问题
**面试官会问**: "What problems does Delta Lake solve?"

### 📊 第 1 层：基础概念
Delta Lake 是一个存储层，在 Parquet 文件之上提供 ACID 事务、Schema enforcement、Time travel 等功能。

### 🔍 第 2 层：解决的核心问题

#### 2.1 问题 1: Parquet 的一致性问题
**场景**: 写入 Parquet 到 S3 时，如果 job 失败，可能留下部分文件
```
s3://bucket/data/
├── part-00000.parquet  ✅ 写入成功
├── part-00001.parquet  ✅ 写入成功
└── part-00002.parquet  ❌ 写入一半，job 失败
```
- 读取时会读到不完整的数据
- 无法回滚

**Delta Lake 的解决**:
- 使用 transaction log (`_delta_log/`)
- 写入是原子的: 要么全部成功，要么全部失败
- 失败的写入不会被读取到

#### 2.2 问题 2: 无法 UPDATE/DELETE
**Parquet 的限制**: 只能 append，不能修改已有数据
**Delta Lake 的解决**: 支持 `UPDATE`, `DELETE`, `MERGE INTO`

**示例**:
```sql
-- GDPR: 删除用户数据
DELETE FROM users WHERE user_id = '12345'

-- SCD Type 2: 更新维度表
MERGE INTO dim_customer AS target
USING updates AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN UPDATE SET *
WHEN NOT MATCHED THEN INSERT *
```

#### 2.3 问题 3: Schema 不一致
**Parquet 的问题**: 不同文件可能有不同 schema
```
part-00000.parquet: {id: int, name: string}
part-00001.parquet: {id: string, name: string}  ← 类型不一致
```
- 读取时报错或返回错误结果

**Delta Lake 的解决**: Schema enforcement
- 写入时验证 schema
- 不兼容的写入被拒绝

**示例**:
```python
# 第一次写入
df1.write.format("delta").save("/path")

# 第二次写入 (schema 不兼容)
df2.write.format("delta").mode("append").save("/path")
# ❌ 报错: Schema mismatch

# 允许 schema evolution (向后兼容的变更)
df2.write.format("delta").mode("append") \
    .option("mergeSchema", "true").save("/path")
# ✅ 成功 (如果只是新增列)
```

#### 2.4 问题 4: 无法查询历史版本
**Parquet 的问题**: 一旦覆盖，旧数据永久丢失
**Delta Lake 的解决**: Time travel

**示例**:
```sql
-- 查询 1 小时前的数据
SELECT * FROM my_table TIMESTAMP AS OF '2026-03-03 10:00:00'

-- 查询版本 5 的数据
SELECT * FROM my_table VERSION AS OF 5

-- 回滚到版本 5
RESTORE TABLE my_table TO VERSION AS OF 5
```

### 🧠 第 3 层：Delta Lake 的机制

#### 3.1 Transaction Log
**核心**: `_delta_log/` 目录下的 JSON 文件
```
_delta_log/
├── 00000000000000000000.json  ← 版本 0
├── 00000000000000000001.json  ← 版本 1
├── 00000000000000000002.json  ← 版本 2
└── ...
```

**每个 JSON 文件记录**:
- 添加了哪些 Parquet 文件
- 删除了哪些 Parquet 文件
- Schema 信息
- 统计信息 (min/max, null count)

**读取流程**:
1. 读取所有 `_delta_log/*.json` 文件
2. 重放 (replay) 所有操作，得到当前版本的文件列表
3. 读取这些 Parquet 文件

#### 3.2 ACID 事务的实现
**原子性 (Atomicity)**:
- 写入新 Parquet 文件 (可能失败，但不影响已有数据)
- 写入新的 transaction log JSON 文件 (原子操作)
- 如果 JSON 写入失败，新 Parquet 文件不会被读取到

**隔离性 (Isolation)**:
- 使用 Optimistic Concurrency Control
- 写入时检查版本号，如果冲突则重试

**示例冲突**:
```
Writer A: 读取版本 10 → 写入 → 尝试提交版本 11
Writer B: 读取版本 10 → 写入 → 尝试提交版本 11
→ 只有一个成功，另一个检测到冲突，重新读取版本 11，重试
```

#### 3.3 Data Skipping (核心性能优化)
**原理**: Transaction log 记录每个文件的 min/max 统计信息

**示例**:
```json
{
  "add": {
    "path": "part-00000.parquet",
    "stats": {
      "numRecords": 1000,
      "minValues": {"date": "2026-01-01", "price": 10.5},
      "maxValues": {"date": "2026-01-31", "price": 150.2}
    }
  }
}
```

**查询优化**:
```sql
SELECT * FROM crypto_data WHERE date = '2026-02-01'
```
- Spark 读取 transaction log
- 检查每个文件的 `minValues.date` 和 `maxValues.date`
- 跳过不包含 `2026-02-01` 的文件
- 只读取相关文件

**你的实战经验**: Z-ordering 后，85% 的文件被跳过

### 💡 第 4 层：Delta Lake 的 Trade-offs

#### 4.1 Trade-off 1: 小文件问题
**问题**: Streaming 写入产生大量小文件
**影响**: 读取时需要打开很多文件，I/O overhead 大

**解决**: 定期运行 `OPTIMIZE`
```sql
OPTIMIZE my_table
ZORDER BY (symbol, timestamp)
```

**Trade-off**:
- `OPTIMIZE` 需要重写文件，消耗计算资源
- 频率选择: 每小时 vs 每天 vs 每周
- 你的选择: 每天凌晨运行 (低峰期)

#### 4.2 Trade-off 2: Transaction Log 大小
**问题**: 随着版本增加，transaction log 文件越来越多
**影响**: 读取时需要重放所有 log，启动慢

**解决**: Checkpoint (每 10 个版本自动创建)
```
_delta_log/
├── 00000000000000000000.json
├── ...
├── 00000000000000000010.checkpoint.parquet  ← Checkpoint
├── 00000000000000000011.json
└── ...
```

**Checkpoint 的作用**: 快照当前状态，无需重放之前的 log

#### 4.3 Trade-off 3: Time Travel 的存储成本
**问题**: 旧版本的 Parquet 文件不会被删除，占用存储
**解决**: `VACUUM` 命令删除旧文件

```sql
-- 删除 7 天前的旧版本
VACUUM my_table RETAIN 168 HOURS
```

**Trade-off**:
- 保留时间短 → 节省存储，但无法 time travel 到很久之前
- 保留时间长 → 可以 time travel，但存储成本高
- 你的选择: 30 天 (满足审计要求，同时控制成本)

### 🔗 你的实战经验总结
> "Delta Lake is the foundation of my Financial Lakehouse. The three features I rely on most are:
>
> 1. **ACID transactions**: My streaming pipeline writes to Bronze every 30 seconds, and batch backfill writes to the same table. Without ACID, I'd have race conditions and partial writes.
>
> 2. **Schema enforcement + evolution**: When CoinGecko added new fields on 2026-02-04, Delta Lake caught the schema mismatch immediately. I used `mergeSchema=true` to safely add the new columns without breaking downstream queries.
>
> 3. **Data skipping + Z-ordering**: After Z-ordering on (symbol, timestamp), queries like 'show me BTC prices in January' skip 85% of files, making queries 6.7x faster.
>
> The trade-off is operational complexity — I need to run OPTIMIZE daily and VACUUM monthly. But the benefits far outweigh the cost."

---

# Part 2: 数据工程模式深度掌握

---

## 6. 数据建模 (Star Schema, Snowflake, Kimball vs Inmon)

### 🎯 核心问题
**面试官会问**: "Explain the difference between Star Schema and Snowflake Schema. When would you use each?"

### 📊 第 1 层：基础概念
- **Star Schema**: 事实表 (Fact Table) 在中心，维度表 (Dimension Tables) 围绕，维度表不规范化
- **Snowflake Schema**: 维度表规范化 (normalized)，形成多层结构

### 🔍 第 2 层：结构对比

#### 2.1 Star Schema 示例
```
        Dim_Date
            |
Dim_Customer - Fact_Sales - Dim_Product
            |
        Dim_Store
```

**Fact_Sales** (事实表):
| sale_id | date_id | customer_id | product_id | store_id | amount | quantity |
|---------|---------|-------------|------------|----------|--------|----------|
| 1       | 20260301| 1001        | 5001       | 101      | 150.00 | 2        |

**Dim_Product** (维度表 - 非规范化):
| product_id | product_name | category | subcategory | brand |
|------------|--------------|----------|-------------|-------|
| 5001       | iPhone 15    | Electronics | Smartphone | Apple |

#### 2.2 Snowflake Schema 示例
```
        Dim_Date
            |
Dim_Customer - Fact_Sales - Dim_Product - Dim_Category - Dim_Subcategory
            |                    |
        Dim_Store           Dim_Brand
```

**Dim_Product** (规范化):
| product_id | product_name | category_id | brand_id |
|------------|--------------|-------------|----------|
| 5001       | iPhone 15    | 10          | 1        |

**Dim_Category**:
| category_id | category_name | subcategory_id |
|-------------|---------------|----------------|
| 10          | Electronics   | 101            |

**Dim_Subcategory**:
| subcategory_id | subcategory_name |
|----------------|------------------|
| 101            | Smartphone       |

### 🧠 第 3 层：选择标准

#### 3.1 Star Schema 的优势
1. **查询性能好**: 少 join，查询简单
2. **易于理解**: 业务用户容易理解
3. **适合 OLAP**: 分析查询通常只需要 1-2 层 join

**适用场景**:
- 数据仓库 (Data Warehouse)
- BI 工具查询
- 维度表不太大 (< 1GB)

#### 3.2 Snowflake Schema 的优势
1. **节省存储**: 规范化减少冗余
2. **维护容易**: 更新维度属性只需改一处

**适用场景**:
- 维度表很大 (> 10GB)
- 维度属性经常变化
- 存储成本敏感

#### 3.3 Trade-off 总结
| 维度 | Star Schema | Snowflake Schema |
|------|-------------|------------------|
| 查询性能 | ✅ 快 (少 join) | ❌ 慢 (多 join) |
| 存储空间 | ❌ 大 (冗余) | ✅ 小 (规范化) |
| 易用性 | ✅ 简单 | ❌ 复杂 |
| 维护成本 | ❌ 高 (冗余更新) | ✅ 低 (单点更新) |

### 💡 第 4 层：Kimball vs Inmon

#### 4.1 Kimball (Bottom-Up, Dimensional Modeling)
**核心思想**: 以业务过程为中心，构建多个 Data Mart (数据集市)

**架构**:
```
Source Systems → ETL → Data Marts (Star Schema)
                         ├─ Sales Mart
                         ├─ Inventory Mart
                         └─ Customer Mart
```

**特点**:
- 快速交付 (先做一个 Mart，再扩展)
- 面向业务用户 (易于查询)
- 可能有数据冗余 (不同 Mart 有相同维度)

#### 4.2 Inmon (Top-Down, Enterprise Data Warehouse)
**核心思想**: 先构建规范化的企业数据仓库 (EDW)，再构建 Data Mart

**架构**:
```
Source Systems → ETL → EDW (3NF) → Data Marts (Star Schema)
```

**特点**:
- 数据一致性好 (单一事实来源)
- 初期投入大 (需要先建 EDW)
- 适合大型企业

#### 4.3 你的选择
> "In my experience, I lean towards Kimball's approach for most projects. Here's why:
>
> At GLP (startup), we needed to deliver value quickly. I built a Sales Mart first (loan applications, approvals, defaults) using Star Schema. This took 2 weeks and immediately provided insights. If I had tried to build a full EDW first (Inmon), it would have taken 3 months, and the business would have lost patience.
>
> However, I recognize Inmon's value for large enterprises with strict governance requirements. If Swisscom's Polaris team is building a centralized data platform for multiple business units, a hybrid approach might work — a normalized core layer (like Medallion's Silver) feeding multiple Star Schema marts (Gold layer)."

---

## 7. 数据质量框架

### 🎯 核心问题
**面试官会问**: "How do you ensure data quality in your pipelines?"

### 📊 第 1 层：基础概念
数据质量是指数据满足业务需求的程度，包括准确性、完整性、一致性、及时性等维度。

### 🔍 第 2 层：数据质量的 6 个维度

#### 2.1 Accuracy (准确性)
**定义**: 数据是否正确反映现实
**检查方法**:
- 范围检查: `age BETWEEN 0 AND 120`
- 格式检查: `email LIKE '%@%.%'`
- 参照完整性: `customer_id` 存在于 `customers` 表

#### 2.2 Completeness (完整性)
**定义**: 必填字段是否有值
**检查方法**:
```sql
SELECT COUNT(*) FROM orders WHERE customer_id IS NULL
-- 应该为 0
```

#### 2.3 Consistency (一致性)
**定义**: 同一数据在不同系统中是否一致
**检查方法**:
```sql
-- 检查跨源一致性
SELECT a.customer_id, a.name AS name_in_crm, b.name AS name_in_billing
FROM crm.customers a
JOIN billing.customers b ON a.customer_id = b.customer_id
WHERE a.name != b.name
```

#### 2.4 Timeliness (及时性)
**定义**: 数据是否及时更新
**检查方法**:
```sql
SELECT MAX(updated_at) FROM daily_sales
-- 应该是今天的日期
```

#### 2.5 Validity (有效性)
**定义**: 数据是否符合业务规则
**检查方法**:
```sql
-- 订单金额应该 = 单价 * 数量
SELECT * FROM orders
WHERE amount != unit_price * quantity
```

#### 2.6 Uniqueness (唯一性)
**定义**: 主键是否唯一
**检查方法**:
```sql
SELECT customer_id, COUNT(*)
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1
```

### 🧠 第 3 层：数据质量框架实现

#### 3.1 你在 3 家公司的数据质量实践

**GLP (Consumer Lending)**:
- **问题**: 用户输入的收入数据不可靠 (虚报收入)
- **解决**: 
  1. 范围检查: 收入 < 0 或 > 1,000,000 → 标记异常
  2. 交叉验证: 收入 vs 职业 (如清洁工收入 > 100,000 → 可疑)
  3. 外部数据源: 调用征信 API 验证收入范围
- **结果**: 虚假申请检出率提升 25%

**Baiquan Investment**:
- **问题**: 多个数据供应商的价格不一致
- **解决**: 跨源验证框架
  ```python
  # 每日收盘后
  for security in securities:
      prices = [source_A.get_price(security),
                source_B.get_price(security),
                source_C.get_price(security)]
      if max(prices) - min(prices) > 0.5% * mean(prices):
          alert("Price discrepancy for " + security)
  ```
- **结果**: 每周发现 2-3 个数据错误，避免错误交易决策

**Financial Lakehouse**:
- **问题**: CoinGecko API 偶尔返回 NULL 或异常值
- **解决**: Quarantine-and-Replay 模式
  ```python
  # Bronze → Silver 边界
  valid_df = df.filter(
      (col("price") > 0) &
      (col("volume") >= 0) &
      (col("market_cap").isNotNull())
  )
  invalid_df = df.subtract(valid_df)
  
  valid_df.write.format("delta").mode("append").save("silver/crypto_clean")
  invalid_df.write.format("delta").mode("append").save("quarantine/crypto_invalid")
  ```
- **结果**: <0.1% 的数据进入 quarantine，零数据丢失

#### 3.2 数据质量框架的组成部分

**1. Schema Validation (入口检查)**
```python
from pyspark.sql.types import StructType, StructField, StringType, DoubleType

expected_schema = StructType([
    StructField("id", StringType(), nullable=False),
    StructField("price", DoubleType(), nullable=False),
    StructField("volume", DoubleType(), nullable=True)
])

# 写入时强制 schema
df.write.format("delta") \
    .option("mergeSchema", "false") \  # 拒绝 schema 变更
    .save("path")
```

**2. Business Rule Validation (业务逻辑检查)**
```python
# 定义规则
rules = [
    ("price_positive", col("price") > 0),
    ("volume_non_negative", col("volume") >= 0),
    ("market_cap_reasonable", col("market_cap") < 1e12)
]

# 应用规则
for rule_name, condition in rules:
    invalid_count = df.filter(~condition).count()
    if invalid_count > 0:
        log_alert(f"{rule_name} failed: {invalid_count} rows")
```

**3. Monitoring & Alerting (持续监控)**
```python
# 每日数据质量报告
quality_metrics = {
    "total_rows": df.count(),
    "null_price": df.filter(col("price").isNull()).count(),
    "negative_volume": df.filter(col("volume") < 0).count(),
    "quarantine_rate": quarantine_df.count() / df.count()
}

if quality_metrics["quarantine_rate"] > 0.01:  # 超过 1%
    send_alert("Data quality degraded")
```

### 💡 第 4 层：数据质量的 Trade-offs

#### 4.1 Trade-off 1: 严格性 vs 可用性
**问题**: 规则太严格 → 拒绝太多数据 → 下游无数据可用
**示例**: 
- 严格: `price > 0` → 拒绝所有 NULL
- 宽松: `price > 0 OR price IS NULL` → 允许 NULL，下游处理

**你的选择**:
> "I use a tiered approach:
> - **Bronze layer**: Accept everything (even bad data)
> - **Silver layer**: Strict validation, bad data → quarantine
> - **Gold layer**: Business rules, aggregations handle NULLs gracefully
>
> This way, I never lose data (Bronze has everything), but downstream consumers get clean data (Silver/Gold)."

#### 4.2 Trade-off 2: 实时检查 vs 批量检查
**实时检查** (在写入时):
- 优点: 立即发现问题
- 缺点: 增加写入延迟

**批量检查** (定期运行):
- 优点: 不影响写入性能
- 缺点: 问题发现延迟

**你的选择**:
> "I do both:
> - **Real-time**: Schema validation (fast, catches obvious errors)
> - **Batch**: Complex business rules (hourly job, generates quality report)
>
> For example, checking 'price > 0' is fast and done real-time. But checking 'price is within 3 standard deviations of historical mean' requires historical data, so it's done in batch."

---

## 8. ETL vs ELT

### 🎯 核心问题
**面试官会问**: "What's the difference between ETL and ELT? When would you use each?"

### 📊 第 1 层：基础概念
- **ETL**: Extract → Transform → Load (先转换，再加载)
- **ELT**: Extract → Load → Transform (先加载，再转换)

### 🔍 第 2 层：架构对比

#### 2.1 ETL (传统方式)
```
Source DB → ETL Tool (Informatica/Talend) → Transform → Target DW
```

**特点**:
- 转换在 ETL 工具中进行 (独立的计算资源)
- 只加载转换后的数据到目标系统
- 目标系统存储空间小

**适用场景**:
- 目标系统是传统 RDBMS (Oracle, SQL Server)
- 目标系统计算能力弱
- 需要复杂的数据清洗 (如 CDC, SCD)

#### 2.2 ELT (现代方式)
```
Source DB → Load → Data Lake/Warehouse → Transform (SQL/Spark)
```

**特点**:
- 先加载原始数据 (Bronze layer)
- 转换在目标系统中进行 (利用目标系统的计算能力)
- 目标系统存储空间大 (保留原始数据)

**适用场景**:
- 目标系统是 Data Lake (S3 + Spark) 或 Cloud DW (Snowflake, BigQuery)
- 目标系统计算能力强
- 需要保留原始数据 (审计、replay)

### 🧠 第 3 层：为什么 ELT 成为主流？

#### 3.1 原因 1: 云数据仓库的崛起
**传统 DW (Oracle, Teradata)**:
- 存储昂贵 ($1000+/TB/year)
- 计算能力有限 (固定硬件)
- → 必须先转换，减少存储

**云 DW (Snowflake, BigQuery)**:
- 存储便宜 ($23/TB/month on S3)
- 计算弹性 (按需扩展)
- → 可以先加载原始数据，再转换

#### 3.2 原因 2: Schema-on-Read 的灵活性
**ETL (Schema-on-Write)**:
- 必须提前定义 schema
- 如果业务需求变化，需要重新 ETL

**ELT (Schema-on-Read)**:
- 原始数据已经在 Data Lake
- 业务需求变化 → 只需重新写转换逻辑
- 可以回溯历史数据 (replay)

#### 3.3 原因 3: 数据湖架构 (Medallion)
**Bronze (Raw)**: 原始数据，未转换
**Silver (Cleaned)**: 清洗、去重、类型转换
**Gold (Aggregated)**: 业务聚合

这是典型的 ELT 模式:
- Extract → Load to Bronze
- Transform: Bronze → Silver → Gold

### 💡 第 4 层：你的实战经验

> "My Financial Lakehouse is a pure ELT architecture:
>
> **Extract**: Kafka consumer pulls crypto market data
> **Load**: Write raw JSON to Bronze layer (no transformation)
> **Transform**: 
> - Bronze → Silver: PySpark job (schema validation, deduplication)
> - Silver → Gold: SQL queries (OHLCV aggregations)
>
> The key advantage is flexibility. When CoinGecko added new fields on 2026-02-04, I didn't need to change the ingestion pipeline — Bronze already had the new fields. I only updated the Silver transformation to parse them.
>
> If I had used ETL, I would have needed to:
> 1. Update the ETL tool to handle new fields
> 2. Redeploy the ETL pipeline
> 3. Potentially lose data during the transition
>
> With ELT, the transition was seamless — Bronze kept ingesting, and I updated Silver at my own pace."

**Trade-off**:
> "The trade-off is storage cost. Bronze layer stores raw JSON, which is less efficient than Parquet. But S3 storage is so cheap ($23/TB/month) that it's worth it for the flexibility. I also use lifecycle policies to archive Bronze data older than 90 days to Glacier, reducing cost by 80%."

---

## 9. SCD (Slowly Changing Dimensions)

### 🎯 核心问题
**面试官会问**: "Explain SCD Type 2 and how you would implement it."

### 📊 第 1 层：基础概念
SCD (Slowly Changing Dimensions) 是处理维度表变化的方法。常见类型:
- **Type 1**: 覆盖旧值 (不保留历史)
- **Type 2**: 保留历史版本 (新增行)
- **Type 3**: 保留有限历史 (新增列)

### 🔍 第 2 层：SCD Type 2 的机制

#### 2.1 示例场景
**客户维度表**: 客户搬家，地址变化

**初始状态**:
| customer_id | name | address | effective_date | end_date | is_current |
|-------------|------|---------|----------------|----------|------------|
| 1001        | Alice| NYC     | 2025-01-01     | 9999-12-31| true       |

**客户搬家到 LA (2026-03-01)**:
| customer_id | name | address | effective_date | end_date | is_current |
|-------------|------|---------|----------------|----------|------------|
| 1001        | Alice| NYC     | 2025-01-01     | 2026-02-29| false      |
| 1001        | Alice| LA      | 2026-03-01     | 9999-12-31| true       |

**关键字段**:
- `effective_date`: 该版本生效日期
- `end_date`: 该版本失效日期
- `is_current`: 是否当前版本 (方便查询)

#### 2.2 查询示例
```sql
-- 查询当前地址
SELECT * FROM dim_customer WHERE customer_id = 1001 AND is_current = true

-- 查询 2025-06-01 的地址 (历史查询)
SELECT * FROM dim_customer
WHERE customer_id = 1001
  AND '2025-06-01' BETWEEN effective_date AND end_date
```

### 🧠 第 3 层：SCD Type 2 的实现 (Delta Lake)

#### 3.1 使用 MERGE INTO 实现
```sql
MERGE INTO dim_customer AS target
USING updates AS source
ON target.customer_id = source.customer_id AND target.is_current = true

-- 如果地址变化，关闭旧记录
WHEN MATCHED AND target.address != source.address THEN
  UPDATE SET
    end_date = current_date() - INTERVAL 1 DAY,
    is_current = false

-- 插入新记录 (在 MERGE 后单独执行)
INSERT INTO dim_customer
SELECT
  customer_id,
  name,
  address,
  current_date() AS effective_date,
  '9999-12-31' AS end_date,
  true AS is_current
FROM updates
WHERE EXISTS (
  SELECT 1 FROM dim_customer
  WHERE dim_customer.customer_id = updates.customer_id
    AND dim_customer.is_current = true
    AND dim_customer.address != updates.address
)
```

#### 3.2 PySpark 实现
```python
from pyspark.sql.functions import col, current_date, lit, when

# 读取当前维度表
dim_current = spark.read.format("delta").load("dim_customer") \
    .filter(col("is_current") == True)

# 读取更新数据
updates = spark.read.format("delta").load("updates")

# 找出变化的记录
changes = updates.join(
    dim_current,
    (updates.customer_id == dim_current.customer_id) &
    (updates.address != dim_current.address),
    "inner"
).select(updates["*"])

# 关闭旧记录
dim_current.join(changes, "customer_id", "inner") \
    .withColumn("end_date", current_date() - 1) \
    .withColumn("is_current", lit(False)) \
    .write.format("delta").mode("append").save("dim_customer")

# 插入新记录
changes.withColumn("effective_date", current_date()) \
    .withColumn("end_date", lit("9999-12-31")) \
    .withColumn("is_current", lit(True)) \
    .write.format("delta").mode("append").save("dim_customer")
```

### 💡 第 4 层：SCD 的 Trade-offs

#### 4.1 Type 1 vs Type 2 vs Type 3
| 类型 | 存储 | 查询复杂度 | 历史保留 | 适用场景 |
|------|------|-----------|---------|---------|
| Type 1 | 小 | 简单 | 无 | 不重要的属性 (如昵称) |
| Type 2 | 大 | 中等 | 完整 | 重要的属性 (如地址、价格) |
| Type 3 | 中 | 简单 | 有限 (1-2 个历史值) | 偶尔变化的属性 |

#### 4.2 你的选择
> "In my projects, I default to SCD Type 2 for important dimensions like customer address, product price, and employee department. The storage cost is negligible compared to the value of historical analysis.
>
> For example, at GLP, we used SCD Type 2 for customer employment status. When analyzing default rates, we could see that customers who changed jobs (employment_status changed from 'Employed' to 'Self-Employed') had 2x higher default rates. This insight was only possible because we preserved the history.
>
> The trade-off is query complexity — analysts need to remember to filter on `is_current = true` for current state queries. I mitigate this by creating views:
> ```sql
> CREATE VIEW dim_customer_current AS
> SELECT * FROM dim_customer WHERE is_current = true
> ```
> This way, analysts can use the view for 99% of queries, and only use the base table when they need historical analysis."

---

## 10. 流处理模式与保证

### 🎯 核心问题
**面试官会问**: "How do you ensure exactly-once semantics in streaming?"

### 📊 第 1 层：基础概念
流处理的三种语义保证:
- **At-most-once**: 每条消息最多处理一次 (可能丢失)
- **At-least-once**: 每条消息至少处理一次 (可能重复)
- **Exactly-once**: 每条消息恰好处理一次 (最理想)

### 🔍 第 2 层：为什么 Exactly-Once 很难？

#### 2.1 问题场景
```
Kafka → Spark Streaming → Database

1. Spark 从 Kafka 读取 offset 100-200
2. Spark 处理数据
3. Spark 写入 Database
4. Spark 提交 offset 200 到 Kafka
   ↑ 如果在这一步失败？
```

**失败场景 1**: 写入 Database 成功，但提交 offset 失败
- 重启后，Spark 重新读取 offset 100-200
- 数据被重复写入 Database
- → At-least-once

**失败场景 2**: 提交 offset 成功，但写入 Database 失败
- 重启后，Spark 从 offset 200 开始
- offset 100-200 的数据丢失
- → At-most-once

### 🧠 第 3 层：Exactly-Once 的实现

#### 3.1 Spark Structured Streaming 的保证
**三个组件**:
1. **Replayable Source**: Kafka offset 可以重放
2. **Idempotent Sink**: 写入操作幂等 (重复写入 = 写入一次)
3. **Checkpoint**: 记录处理进度

**流程**:
```
1. 读取 checkpoint，获取上次处理的 offset
2. 从 Kafka 读取新数据 (offset 200-300)
3. 处理数据 (确定性计算)
4. 写入 sink (幂等操作)
5. 更新 checkpoint (offset 300)
   ↑ 原子操作: 要么全成功，要么全失败
```

**关键**: Checkpoint 和 Sink 的写入是原子的
- 如果 Sink 写入失败 → Checkpoint 不更新 → 重启后重新处理
- 如果 Sink 写入成功 → Checkpoint 更新 → 不会重复处理

#### 3.2 幂等 Sink 的实现

**方法 1: MERGE INTO (Delta Lake)**
```sql
MERGE INTO target AS t
USING source AS s
ON t.id = s.id AND t.timestamp = s.timestamp
WHEN NOT MATCHED THEN INSERT *
```
- 如果 `(id, timestamp)` 已存在 → 不插入
- 重复写入 = 写入一次

**方法 2: Deduplication Window**
```python
df.dropDuplicates(["id", "timestamp"]) \
    .writeStream \
    .format("delta") \
    .option("checkpointLocation", "s3://checkpoints/") \
    .start("s3://output/")
```

**方法 3: Transactional Sink (Database)**
```python
# 使用 foreachBatch 实现事务写入
def write_to_db(batch_df, batch_id):
    # batch_id 是单调递增的
    # 检查 batch_id 是否已处理
    if not is_batch_processed(batch_id):
        batch_df.write.jdbc(url, table, mode="append")
        mark_batch_processed(batch_id)

df.writeStream.foreachBatch(write_to_db).start()
```

### 💡 第 4 层：你的实战经验

> "In my Financial Lakehouse, I achieve exactly-once semantics using Spark Structured Streaming + Delta Lake:
>
> **Source**: Kafka (replayable)
> - Offsets stored in checkpoint: `s3://checkpoints/crypto_stream/offsets/`
>
> **Processing**: Deterministic transformations
> - Same input → same output (no random operations)
>
> **Sink**: Delta Lake (idempotent)
> - Use MERGE INTO based on `(id, timestamp)` composite key
> - If the same record arrives twice (due to retry), it's deduplicated
>
> **Checkpoint**: Atomic commit
> - Spark writes to Delta Lake → Delta transaction log updated
> - Spark updates checkpoint → offset committed
> - If either fails, both are rolled back
>
> **Real-world test**: I simulated a failure by killing the Spark job mid-batch. After restart:
> - Spark read the last committed offset from checkpoint
> - Reprocessed the failed batch
> - Delta Lake's MERGE INTO deduplicated the records
> - No data loss, no duplicates
>
> The trade-off is latency — MERGE INTO is slower than append-only. My micro-batch interval is 30 seconds, which is acceptable for my use case (near real-time dashboard). If I needed sub-second latency, I'd need a different approach (like Flink with two-phase commit)."

---

# 总结：10 个核心概念速查表

| # | 概念 | 核心机制 | 你的实战经验 |
|---|------|---------|-------------|
| 1 | Spark 查询执行 | Catalyst (rule-based) + Tungsten (code gen) | Z-ordering + predicate pushdown → 6.7x faster |
| 2 | Shuffle 优化 | Broadcast join, pre-partitioning, AQE | Broadcast 2MB metadata table, 避免 shuffle 100GB |
| 3 | Data Skew | Salting, broadcast join, AQE skew join | BTC/ETH salting → 6x speedup |
| 4 | Batch vs Streaming | 延迟要求、数据到达模式、计算复杂度 | 两者都用: Streaming (实时) + Batch (backfill) |
| 5 | Delta Lake | ACID, schema enforcement, time travel, data skipping | Quarantine-and-replay, 85% file skipping |
| 6 | 数据建模 | Star (性能) vs Snowflake (存储), Kimball (快速) vs Inmon (一致性) | Kimball 方法, Star Schema for Gold layer |
| 7 | 数据质量 | 6 维度 (准确性、完整性、一致性、及时性、有效性、唯一性) | 3 家公司的实践: 范围检查、跨源验证、quarantine |
| 8 | ETL vs ELT | ETL (先转换) vs ELT (先加载), Schema-on-write vs Schema-on-read | ELT (Medallion), Bronze 保留原始数据 |
| 9 | SCD Type 2 | 保留历史版本, effective_date + end_date + is_current | MERGE INTO 实现, 分析客户就业变化 → 违约率 |
| 10 | Exactly-Once | Replayable source + Idempotent sink + Checkpoint | Kafka + Delta MERGE + Checkpoint → 零丢失零重复 |

---

# 下一步：苏格拉底式对话

现在你已经有了完整的理论基础。接下来，我们将进行苏格拉底式对话，通过追问的方式，确保你真正理解每个概念到第 4 层。

**准备好了吗？我们从哪个概念开始？**

建议顺序:
1. Shuffle 优化 (最常被问到)
2. Delta Lake (你的项目核心)
3. Data Skew (实战性强)
4. Exactly-Once (技术深度)
5. 其他概念

**或者，你可以选择你最不确定的概念，我们先攻克它。**

