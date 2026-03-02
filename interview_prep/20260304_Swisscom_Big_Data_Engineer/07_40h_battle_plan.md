# Swisscom 技术面试 — 40 小时作战计划

**起始时间**: 现在 (Day 1 开始)
**面试时间**: 2026-03-04 周三 10:00 CET
**总可用时间**: 40 小时
**原则**: 每个小时都有明确目标，80/20 法则 — 把 80% 的时间花在最可能考的 20% 上

---

## 时间分配总览

| 模块 | 时长 | 占比 | 理由 |
|------|------|------|------|
| **A. SQL 手写刷题** | 8h | 20% | Glassdoor 确认必考，Yannis 是查询引擎专家 |
| **B. Spark 深度（内部机制 + API）** | 8h | 20% | JD 核心要求，Yannis fork 了 Spark |
| **C. Python 编码题** | 5h | 12.5% | 现场编码环节，数据处理 + 算法 |
| **D. 系统设计** | 5h | 12.5% | 实时数据管道设计，Polaris 场景 |
| **E. Kafka + 流处理** | 4h | 10% | 团队核心技术，与 Spark Streaming 衔接 |
| **F. CV 故事打磨 + 口述练习** | 4h | 10% | 每个项目 2 分钟讲述，trade-off 思维 |
| **G. AWS 数据服务** | 2h | 5% | 团队迁移方向，加分项 |
| **H. 模拟面试 (自己对自己)** | 2h | 5% | 英语口述全流程演练 |
| **I. 休息 + 面试前准备** | 2h | 5% | 面试前 2h 停止学习，放松 + 检查设备 |

---

## 详细执行计划

### ═══ 第一阶段：基础功夫 (0-12h) ═══

这是最关键的阶段，解决"必须会但可能不够熟练"的问题。

---

### 模块 A1: SQL 手写刷题 — 基础巩固 (4h)

**目标**: 能在白板/屏幕上流畅手写 SQL，不依赖 IDE 补全

**Hour 1-2: Window Functions 专项**

这是 Yannis 最可能考的 SQL 题型（他研究查询执行计划）。

练习这些题目（手写，不用 IDE）:

1. **排名类**:
```sql
-- 每个部门薪资排名前3的员工
SELECT department, employee_name, salary,
       RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rnk
FROM employees
WHERE rnk <= 3;  -- 注意：这里不能直接用，需要子查询或 CTE
```
搞清楚：为什么 WHERE 里不能直接引用 window function？→ 因为 window function 在 WHERE 之后执行

正确写法:
```sql
WITH ranked AS (
    SELECT department, employee_name, salary,
           ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rk
    FROM employees
)
SELECT * FROM ranked WHERE rk <= 3;
```

2. **ROW_NUMBER vs RANK vs DENSE_RANK**:
```
数据: [100, 100, 90, 80]
ROW_NUMBER: 1, 2, 3, 4  (强制不同)
RANK:       1, 1, 3, 4  (并列后跳号)
DENSE_RANK: 1, 1, 2, 3  (并列不跳号)
```

3. **累计求和 / Running Total**:
```sql
SELECT date, revenue,
       SUM(revenue) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) as running_total
FROM daily_sales;
```

4. **LAG / LEAD — 比较前后行**:
```sql
-- 每天与前一天的收入变化
SELECT date, revenue,
       revenue - LAG(revenue, 1) OVER (ORDER BY date) as daily_change,
       ROUND((revenue - LAG(revenue, 1) OVER (ORDER BY date)) * 100.0
             / LAG(revenue, 1) OVER (ORDER BY date), 2) as pct_change
FROM daily_sales;
```

5. **移动平均**:
```sql
SELECT date, revenue,
       AVG(revenue) OVER (ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) as moving_avg_7d
FROM daily_sales;
```

**必须搞清楚的概念**:
- `ROWS BETWEEN` vs `RANGE BETWEEN` 的区别
- `UNBOUNDED PRECEDING`, `CURRENT ROW`, `UNBOUNDED FOLLOWING`
- SQL 执行顺序: FROM → WHERE → GROUP BY → HAVING → SELECT → WINDOW → ORDER BY → LIMIT

**Hour 3: JOIN 深度 + 子查询**

不只是会写，要能解释执行计划：

```sql
-- Self-join: 找出同一部门内薪资高于部门平均的员工
SELECT e.name, e.salary, d.avg_salary
FROM employees e
JOIN (
    SELECT department_id, AVG(salary) as avg_salary
    FROM employees
    GROUP BY department_id
) d ON e.department_id = d.department_id
WHERE e.salary > d.avg_salary;
```

JOIN 类型整理:
- INNER JOIN: 两边都有
- LEFT JOIN: 左表全保留，右表没有的为 NULL
- CROSS JOIN: 笛卡尔积 (M * N 行)
- ANTI JOIN: `WHERE NOT EXISTS (...)` 或 `LEFT JOIN ... WHERE right.id IS NULL`

**Hour 4: 实战模拟题 — 电信场景**

用 Swisscom 的场景练习:

```sql
-- 题目: 给定 network_events 表
-- (event_id, timestamp, cell_tower_id, event_type, user_hash, signal_strength)
-- 找出每小时每个基站的事件数、平均信号强度、以及基站在该小时的排名

WITH hourly_stats AS (
    SELECT
        DATE_TRUNC('hour', timestamp) AS hour,
        cell_tower_id,
        COUNT(*) AS event_count,
        AVG(signal_strength) AS avg_signal
    FROM network_events
    WHERE timestamp >= '2026-03-01'
    GROUP BY DATE_TRUNC('hour', timestamp), cell_tower_id
)
SELECT
    hour,
    cell_tower_id,
    event_count,
    ROUND(avg_signal, 2) as avg_signal,
    RANK() OVER (PARTITION BY hour ORDER BY event_count DESC) as busy_rank
FROM hourly_stats
ORDER BY hour, busy_rank;
```

```sql
-- 题目: 找出信号强度连续3小时下降的基站 (可能存在故障)
WITH hourly AS (
    SELECT
        cell_tower_id,
        DATE_TRUNC('hour', timestamp) AS hour,
        AVG(signal_strength) AS avg_signal
    FROM network_events
    GROUP BY cell_tower_id, DATE_TRUNC('hour', timestamp)
),
with_lag AS (
    SELECT *,
        LAG(avg_signal, 1) OVER (PARTITION BY cell_tower_id ORDER BY hour) AS prev_1,
        LAG(avg_signal, 2) OVER (PARTITION BY cell_tower_id ORDER BY hour) AS prev_2
    FROM hourly
)
SELECT cell_tower_id, hour, avg_signal, prev_1, prev_2
FROM with_lag
WHERE avg_signal < prev_1 AND prev_1 < prev_2;
```

---

### 模块 B1: Spark 深度 — 内部机制 (4h)

**目标**: 能回答 Yannis 级别的 "why" 问题

**Hour 5-6: Spark 架构与执行模型**

**必须能画出并解释这张图**:
```
Driver Program
  ├── SparkContext
  │     ├── DAG Scheduler → 将 job 拆分为 stages (以 shuffle 为边界)
  │     └── Task Scheduler → 将 tasks 分配到 executors
  │
  └── Cluster Manager (YARN / K8s / Standalone)
        ├── Executor 1 (JVM)
        │     ├── Task 1 (1 partition)
        │     ├── Task 2 (1 partition)
        │     └── Cache (内存/磁盘)
        └── Executor 2 (JVM)
              └── ...
```

**Narrow vs Wide Dependencies** (Yannis 会关心这个):
- **Narrow** (map, filter, union): 1 parent partition → 1 child partition，无 shuffle
- **Wide** (groupBy, join, repartition): 多个 parent → 多个 child，需要 shuffle
- **为什么重要**: Narrow transformations 可以 pipeline 在同一个 task 内，Wide 需要新的 stage

**Catalyst Optimizer** (直击 Yannis 的研究领域):
```
未优化逻辑计划
  ↓ Analysis (解析列名、类型)
解析后逻辑计划
  ↓ Logical Optimization (规则)
      • 谓词下推 (Predicate Pushdown): WHERE 条件推到 scan 层
      • 列裁剪 (Column Pruning): 只读需要的列
      • 常量折叠 (Constant Folding): 2+3 → 5
      • Join 重排序 (基于成本)
优化后逻辑计划
  ↓ Physical Planning (选择物理算子)
      • Sort-Merge Join vs Broadcast Hash Join vs Shuffle Hash Join
物理计划
  ↓ Code Generation (Tungsten)
      • Whole-stage code generation
      • 将多个操作符融合为一个 Java 方法
RDD 执行
```

**关键问答准备**:

Q: "What is predicate pushdown and why does it matter?"
A: "Predicate pushdown moves filter conditions as close to the data source as possible. For example, if I'm reading from Parquet files and filtering by date, Spark can use the file-level and row-group-level statistics to skip entire files that don't match. In our Financial Lakehouse, this combined with Z-ordering meant Spark could skip 90%+ of the data for typical queries."

Q: "When does Spark choose Broadcast Join vs Sort-Merge Join?"
A: "Broadcast Join when one side is small enough (default < 10MB, configurable via spark.sql.autoBroadcastJoinThreshold). The small table is sent to all executors. Sort-Merge Join for large-large joins — both sides are sorted by join key, then merged. Broadcast is O(n) with no shuffle; Sort-Merge is O(n log n) with shuffle on both sides."

**Hour 7-8: Spark 性能调优实战**

这些是面试中最容易被深挖的性能问题:

**1. Shuffle 优化**:
- 默认 `spark.sql.shuffle.partitions = 200` — 数据量小时太多（overhead），大时太少（OOM）
- AQE 自动合并小分区: `spark.sql.adaptive.enabled = true`
- Salting 处理 data skew: 给热 key 加 `CONCAT(key, '_', FLOOR(RAND() * 10))`

**2. 内存管理**:
```
Executor Memory = Execution Memory (60%) + Storage Memory (40%)
                  (shuffles, joins)       (cached data)

spark.executor.memory = 8g        # 堆内存
spark.executor.memoryOverhead = 2g # 堆外 (Python workers, etc.)
```

**3. 常见 OOM 排查**:
- Shuffle 阶段 OOM → 增加 partition 数 或 增加 executor memory
- Driver OOM → `collect()` 拉了太多数据到 driver
- Python worker OOM → pandas UDF 处理大 partition

**4. 文件格式选择**:
| 格式 | 列式 | 压缩 | Schema | 用途 |
|------|------|------|--------|------|
| Parquet | ✅ | Snappy/Zstd | 内嵌 | 分析查询 (最推荐) |
| ORC | ✅ | Zlib | 内嵌 | Hive 生态 |
| Avro | ❌ (行式) | Deflate | 内嵌 | 消息序列化 (Kafka) |
| Delta | ✅ | 同 Parquet | ACID 事务日志 | Data lakehouse |

---

### ═══ 第二阶段：核心技术补强 (12-24h) ═══

---

### 模块 A2: SQL 手写刷题 — 进阶 (4h)

**Hour 9-10: 复杂查询模式**

**MERGE INTO (SCD Type 2)** — Yannis 的 CleanerVersion 项目就是做这个的:
```sql
-- Delta Lake / Spark SQL 语法
MERGE INTO dim_customer AS target
USING staging_customer AS source
ON target.customer_id = source.customer_id AND target.is_current = true

WHEN MATCHED AND target.address <> source.address THEN
    UPDATE SET is_current = false, end_date = CURRENT_DATE

WHEN NOT MATCHED THEN
    INSERT (customer_id, address, start_date, end_date, is_current)
    VALUES (source.customer_id, source.address, CURRENT_DATE, NULL, true);
```

**递归 CTE** (可能的加分题):
```sql
-- 找出组织架构中所有下属 (Swisscom 后端挑战中有类似 parentId 遍历)
WITH RECURSIVE org_tree AS (
    SELECT employee_id, name, manager_id, 0 as level
    FROM employees
    WHERE manager_id IS NULL

    UNION ALL

    SELECT e.employee_id, e.name, e.manager_id, t.level + 1
    FROM employees e
    JOIN org_tree t ON e.manager_id = t.employee_id
)
SELECT * FROM org_tree ORDER BY level;
```

**Hour 11-12: 性能分析题**

Q: "This query is slow. How would you optimize it?"
```sql
SELECT u.name, COUNT(o.order_id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE o.created_at > '2025-01-01'
GROUP BY u.name
ORDER BY order_count DESC;
```

问题分析:
1. LEFT JOIN + WHERE on right table → 等效于 INNER JOIN（WHERE 过滤掉了 NULL）
2. 如果 orders 表很大，需要在 `(user_id, created_at)` 上建索引
3. 如果只需要 top N，加 `LIMIT` 避免全排序
4. 考虑先 filter orders 再 join:
```sql
WITH recent_orders AS (
    SELECT user_id, COUNT(*) as order_count
    FROM orders
    WHERE created_at > '2025-01-01'
    GROUP BY user_id
)
SELECT u.name, ro.order_count
FROM users u
JOIN recent_orders ro ON u.id = ro.user_id
ORDER BY ro.order_count DESC;
```

---

### 模块 B2: Spark API 实战 (4h)

**Hour 13-14: PySpark DataFrame 操作**

不看文档，手写以下操作:

```python
from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("practice").getOrCreate()

# 读取数据
df = spark.read.parquet("s3://data/network_events/")

# 基本操作
df_filtered = (
    df
    .filter(F.col("event_type") == "handover")
    .filter(F.col("timestamp") >= "2026-03-01")
    .select("cell_tower_id", "timestamp", "signal_strength")
)

# 聚合
hourly_stats = (
    df_filtered
    .withColumn("hour", F.date_trunc("hour", "timestamp"))
    .groupBy("hour", "cell_tower_id")
    .agg(
        F.count("*").alias("event_count"),
        F.avg("signal_strength").alias("avg_signal"),
        F.percentile_approx("signal_strength", 0.95).alias("p95_signal")
    )
)

# Window function
window_spec = Window.partitionBy("hour").orderBy(F.desc("event_count"))
ranked = hourly_stats.withColumn("rank", F.row_number().over(window_spec))
top5 = ranked.filter(F.col("rank") <= 5)

# 写入 Delta
top5.write.format("delta").mode("overwrite").partitionBy("hour").save("/output/top_towers/")
```

**Hour 15-16: Structured Streaming**

```python
# 从 Kafka 读取流
stream_df = (
    spark
    .readStream
    .format("kafka")
    .option("kafka.bootstrap.servers", "broker:9092")
    .option("subscribe", "network_events")
    .load()
)

# 解析 JSON value
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType

schema = StructType([
    StructField("event_id", StringType()),
    StructField("timestamp", TimestampType()),
    StructField("cell_tower_id", StringType()),
    StructField("signal_strength", DoubleType()),
])

parsed = (
    stream_df
    .select(F.from_json(F.col("value").cast("string"), schema).alias("data"))
    .select("data.*")
)

# Watermark + Window 聚合
windowed = (
    parsed
    .withWatermark("timestamp", "10 minutes")  # 允许 10 分钟延迟
    .groupBy(
        F.window("timestamp", "5 minutes"),  # 5分钟窗口
        "cell_tower_id"
    )
    .agg(F.count("*").alias("count"), F.avg("signal_strength").alias("avg_signal"))
)

# 写入 sink
query = (
    windowed
    .writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", "/checkpoints/network_agg/")
    .start("/output/streaming_agg/")
)
```

**关键概念 — 三种 outputMode**:
- `append`: 只输出新行 (用于聚合 + watermark)
- `complete`: 每次输出完整结果 (用于无 watermark 的聚合)
- `update`: 只输出变化的行 (最常用)

---

### 模块 C: Python 编码题 (5h)

**Hour 17-18: 数据结构与算法基础**

**每道题用手写/白板方式完成，不用 IDE 补全**

1. **哈希表应用 — Two Sum**:
```python
def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []
```

2. **二分查找**:
```python
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1
```

3. **合并有序数组/列表** (归并排序核心):
```python
def merge_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result
```

4. **LRU Cache** (数据结构设计):
```python
from collections import OrderedDict

class LRUCache:
    def __init__(self, capacity):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self.cache:
            return -1
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
```

**Hour 19-20: 数据处理编码题**

5. **解析日志文件 — 统计 IP 频率**:
```python
from collections import Counter

def top_ips(log_lines, n=10):
    ip_counts = Counter()
    for line in log_lines:
        ip = line.split()[0]
        ip_counts[ip] += 1
    return ip_counts.most_common(n)
```

6. **实现简易 MapReduce — Word Count**:
```python
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

def mapper(text_chunk):
    counts = defaultdict(int)
    for word in text_chunk.split():
        counts[word.lower()] += 1
    return dict(counts)

def reducer(map_results):
    final = defaultdict(int)
    for result in map_results:
        for word, count in result.items():
            final[word] += count
    return dict(final)
```

7. **时间序列异常检测**:
```python
def detect_anomalies(values, window=10, threshold=2.0):
    anomalies = []
    for i in range(window, len(values)):
        window_data = values[i-window:i]
        mean = sum(window_data) / window
        std = (sum((x - mean)**2 for x in window_data) / window) ** 0.5
        if std > 0 and abs(values[i] - mean) > threshold * std:
            anomalies.append((i, values[i]))
    return anomalies
```

**Hour 21: 面试场景编码**

8. **实现数据管道核心逻辑**:
```python
# 场景: 给定网络事件流，找出每个基站在过去1小时内的事件数
# 要求使用滑动窗口，内存友好

from collections import defaultdict, deque
from datetime import datetime, timedelta

class SlidingWindowCounter:
    def __init__(self, window_minutes=60):
        self.window = timedelta(minutes=window_minutes)
        self.events = defaultdict(deque)  # tower_id -> deque of timestamps

    def add_event(self, tower_id, timestamp):
        self.events[tower_id].append(timestamp)
        self._cleanup(tower_id, timestamp)

    def get_count(self, tower_id, current_time):
        self._cleanup(tower_id, current_time)
        return len(self.events[tower_id])

    def _cleanup(self, tower_id, current_time):
        q = self.events[tower_id]
        while q and q[0] < current_time - self.window:
            q.popleft()

    def top_k(self, current_time, k=5):
        counts = {}
        for tower_id in self.events:
            self._cleanup(tower_id, current_time)
            counts[tower_id] = len(self.events[tower_id])
        return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:k]
```

---

### ═══ 第三阶段：高级专题 + 模拟 (24-36h) ═══

---

### 模块 D: 系统设计 (5h)

**Hour 22-24: 核心系统设计题 — "设计 Swisscom 的实时网络监控管道"**

这是最可能被问到的系统设计题。你必须能在 15 分钟内画出架构并解释每个决策。

**Step 1: 需求澄清 (2 min)**
- 数据量: 200 亿事件/天 ≈ 23 万事件/秒 ≈ 2 TB/天
- 延迟要求: 实时告警 < 1 分钟，分析报表 < 1 小时
- 可用性: 99.9% (网络监控是关键业务)
- 用例: 实时异常检测 + 历史趋势分析 + 容量规划

**Step 2: 高层架构 (5 min)**
```
数据源 (基站/网元)
    ↓ (syslog, SNMP, YANG push)
[Kafka Producers] (每个区域一个)
    ↓
[Kafka Cluster] (3+ brokers, RF=3)
    ├── Topic: raw_events (partitioned by region_id, 100+ partitions)
    ├── Topic: alerts
    └── Topic: aggregated_metrics
         ↓                    ↓                ↓
[Flink Job: 实时告警]    [Spark Streaming:    [Spark Batch:
 (低延迟, < 30s)         5-min 聚合]          每日 ETL]
    ↓                    ↓                    ↓
[Alert Service]      [S3 / Delta Lake]    [Redshift]
[PagerDuty]          [Silver Layer]       [Analytics]
                         ↓
                    [Athena / QuickSight]
```

**Step 3: 关键设计决策 (5 min)**

为什么 Kafka 分区用 region_id 而不是 tower_id:
- 230K events/sec ÷ 100 partitions = 2.3K events/sec/partition (合理)
- 如果用 tower_id，数万个 tower → 分区太多 → overhead
- Region 保证地理相关性 → 方便区域级聚合

为什么同时用 Flink 和 Spark:
- Flink: 真正的 event-by-event 处理，延迟 < 1s，适合异常检测规则
- Spark Streaming: 微批处理，延迟 5-30s，适合大规模聚合
- 不用 Flink 做一切: Spark 的 SQL 生态更成熟，分析查询更方便

数据分层 (Medallion):
- Bronze: S3 原始 JSON，保留所有数据
- Silver: Parquet，清洗后，partitioned by date + region
- Gold: 聚合指标，直接供 BI 查询

**Step 4: 深挖点 (3 min)**

容错:
- Kafka: 副本因子 3，ISR >= 2
- Spark: checkpoint 到 S3，exactly-once via idempotent writes
- 数据质量: schema validation at Bronze→Silver 边界

监控:
- Kafka: consumer lag, throughput, partition skew
- Spark: stage duration, shuffle spill, executor memory
- 业务: 数据新鲜度 SLA (event_time - processing_time < 5 min)

**Hour 25-26: 第二个系统设计题 — "如何实现 data quality at scale"**

更贴近日常工作的题目:

```
Data Quality Framework:
1. Schema Validation (入口)
   - JSON Schema / Avro Schema Registry
   - 不符合 → quarantine

2. Completeness Check (Bronze → Silver)
   - 每个 partition 的 record count vs 预期
   - 缺失字段率 < 5%

3. Freshness Monitor
   - max(event_time) - current_time < threshold
   - 如果数据不新鲜 → 可能上游出问题

4. Cross-source Reconciliation
   - 比较多个数据源的同一指标
   - 差异 > threshold → 告警

5. Statistical Checks (Silver → Gold)
   - 指标的 z-score 检测
   - 突变检测 (day-over-day, week-over-week)

6. Data Lineage
   - 每条记录可以追溯到原始来源
   - 便于 debug 和审计
```

---

### 模块 E: Kafka + 流处理 (4h)

**Hour 27-28: Kafka 架构深度**

**必须能回答的问题**:

Q: "How does Kafka guarantee message ordering?"
A: "Ordering is guaranteed only within a single partition. Messages with the same key go to the same partition (via hash). If you need ordering across all messages, use a single partition — but this limits throughput. For Swisscom, ordering per cell_tower would mean partitioning by tower_id hash."

Q: "Explain exactly-once semantics in Kafka."
A: "Three components:
1. Idempotent producer: `enable.idempotence=true`, Kafka deduplicates based on producer_id + sequence_number
2. Transactions: producer can atomically write to multiple partitions
3. Consumer: read_committed isolation, only see committed messages
End-to-end: Kafka Streams provides exactly-once via internal state management"

Q: "Consumer group rebalancing — what happens and how to minimize disruption?"
A: "When a consumer joins/leaves, partitions are reassigned. During rebalance, NO consumer reads. Minimize via:
- Static group membership (`group.instance.id`)
- Cooperative rebalancing (incremental, not stop-the-world)
- Proper heartbeat/session timeouts"

**Hour 29-30: Flink vs Spark Streaming 对比**

| 特性 | Spark Structured Streaming | Apache Flink |
|------|--------------------------|-------------|
| 处理模型 | 微批 (+ continuous mode) | 真正的事件驱动 |
| 延迟 | 100ms-秒级 | 毫秒级 |
| State 管理 | 基于 checkpoint | RocksDB + checkpoint |
| Exactly-once | ✅ (via checkpoint) | ✅ (via checkpoint) |
| SQL 支持 | 强 (Spark SQL) | 良好 (Flink SQL) |
| 生态 | 最广泛 | 快速增长 |
| 适合场景 | 大规模 ETL + 分析 | 低延迟事件处理 |

**你的回答策略**: "I've primarily worked with Spark Structured Streaming because it integrates seamlessly with the batch processing stack. For ultra-low-latency use cases like real-time anomaly detection, Flink would be the better choice. The key is matching the tool to the latency requirement."

---

### 模块 F: CV 故事打磨 + 口述练习 (4h)

**Hour 31-32: 每个项目的 2 分钟讲述**

对着镜子或录音，英语大声讲述。每个项目严格控制在 2 分钟内。

**Financial Data Lakehouse (首选故事)**:
> "I built a real-time financial data lakehouse on Databricks that processes crypto market data feeds. The key challenge was handling unreliable data sources — exchange APIs could send delayed, out-of-order, or malformed data. I used Spark Structured Streaming with watermarking to handle late-arriving events, and designed a quarantine-and-replay pattern at the Bronze-Silver boundary to isolate bad records without losing any data. For query optimization, I implemented Z-ordering on the symbol and timestamp columns, which let Spark skip over 90% of the data for typical analytical queries."

**GLP Technology (展示从零构建)**:
> "As the founding data hire at a consumer lending startup, I built the entire data infrastructure from scratch. My first priority was the PySpark ETL pipeline to ingest loan data across the full lifecycle — from application through repayment and collection. I then built a credit scoring system, owning the full ML lifecycle. The most impactful work was the automated data quality framework — schema validation and integrity checks that caught issues before they could corrupt downstream credit models."

**Baiquan Investment (展示数据质量意识)**:
> "At Baiquan, I built the market data infrastructure for quantitative research. I ingested feeds from multiple vendors for 3,000+ securities and built a cross-source validation framework to detect gaps and inconsistencies — like missing trading days or stale prices. This was critical because even a small data error could lead to wrong trading signals. The factor computation engine used vectorized NumPy operations for 100x speedup over naive Python loops."

**Expedia Kaggle (展示 ML 能力)**:
> "For the Expedia Hotel Recommendation challenge, I built a ranking model on 4.9 million booking records. The key insight was treating it as a learning-to-rank problem with NDCG as the metric, not a classification problem. I engineered features around user search patterns and hotel popularity, used XGBoost for its native handling of missing values, and achieved top 5% on the Kaggle leaderboard with an NDCG@5 of 0.392."

**Hour 33-34: 行为问题练习**

大声练习回答（英语）:

1. "Why Swisscom?"
2. "Tell me about a time you dealt with ambiguity."
3. "What's your biggest technical failure and what did you learn?"
4. "How do you prioritize when there are competing deadlines?"
5. "Describe a situation where you had to convince someone of a technical approach."

---

### ═══ 第四阶段：最终冲刺 (36-40h) ═══

---

### 模块 G: AWS 数据服务速览 (2h)

**Hour 35-36: 关键服务一句话总结**

| 服务 | 一句话 | 你的经验 |
|------|--------|---------|
| S3 | 对象存储，数据湖的基础 | ✅ Financial Lakehouse |
| Glue | Serverless ETL + Data Catalog | 了解概念 |
| Redshift | 列式数据仓库 (MPP) | 了解概念 |
| Athena | Serverless SQL on S3 (Presto) | 了解概念 |
| EMR | 托管 Hadoop/Spark 集群 | ✅ 类似 Databricks |
| Kinesis | 实时流摄取 (类似 Kafka) | 了解概念 |
| SageMaker | ML 训练+部署平台 | 了解概念 |
| CDK | IaC (TypeScript/Python) | 了解概念 |

**S3 vs HDFS**:
- S3: 对象存储，无限扩展，便宜，但延迟较高 (100ms+)
- HDFS: 块存储，低延迟，但需要管理集群
- 趋势: 所有人都在从 HDFS → S3（Swisscom 正在做）

**Redshift 关键概念**:
- DISTKEY: 决定数据如何分布到各个节点（类似 Spark partitionBy）
- SORTKEY: 决定数据在每个节点内如何排序（类似 Z-ordering）
- COPY: 从 S3 批量加载数据的命令

---

### 模块 H: 模拟面试 (2h)

**Hour 37-38: 完整模拟**

设置计时器，模拟完整面试流程:

**0:00-0:02** 自我介绍 (2 min, 英语)
**0:02-0:15** 面试官追问你的项目 (回答 + 追问)
**0:15-0:35** 技术口头题:
- "Explain how Spark processes a SQL query internally" (5 min)
- "What is data skew and how do you handle it?" (5 min)
- "Design a real-time pipeline for processing network events" (10 min)
**0:35-0:55** 编码:
- SQL: Window function 排名题 (10 min)
- Python: 滑动窗口异常检测 (10 min)
**0:55-1:00** 你的提问 (5 min)

**每个回答录音，回放检查**:
- 是否在 30 秒内给出了核心答案？
- 是否用了具体数字？
- 是否展示了 trade-off 思维？
- 英语是否流畅？

---

### 模块 I: 面试前准备 (2h)

**Hour 39 (面试前 3 小时): 复习速查表**

打开 `06_technical_deep_prep.md` 第八部分，过一遍:
- Spark 关键概念表
- Kafka 关键概念表
- SQL 速记
- 你的数字 + Swisscom 数字

**Hour 40 (面试前 1-2 小时): 停止学习**

- 测试 Teams 音频/视频
- 准备好水和纸笔
- 把速查表放在屏幕旁边
- 深呼吸，调整心态
- **不要再学新东西** — 只复习已经掌握的

---

## 时间轴一览

```
Day 1:
  [00-04h] SQL 基础 + Window Functions
  [04-08h] Spark 内部机制 (Catalyst, Tungsten, Shuffle)
  [08-12h] SQL 进阶 + Spark API 实战

Day 1 Night → Day 2:
  [12-17h] Python 编码题 (数据结构 + 算法 + 数据处理)
  [17-22h] 系统设计 (2个完整题目)
  [22-26h] Kafka + 流处理深度

Day 2:
  [26-30h] CV 故事打磨 + 行为问题 (英语口述)
  [30-32h] AWS 服务速览
  [32-34h] 模拟面试 (录音 + 回放)

Day 2 Night → 面试当天:
  [34-38h] 查漏补缺 + 复习薄弱环节
  [38-39h] 速查表复习
  [39-40h] 停止学习 + 准备设备 + 放松

  10:00 CET → 面试开始
```

---

## 如果时间不够怎么砍？

如果你最终只有 20 小时（而不是 40），按这个优先级砍:

| 优先级 | 模块 | 时长 | 说明 |
|--------|------|------|------|
| P0 | SQL 手写 | 4h | 必考，不能跳 |
| P0 | Spark 内部机制 | 4h | Yannis 的领域，必须准备 |
| P0 | 模拟面试 + 口述 | 3h | 面试是说出来的，不是想出来的 |
| P1 | Python 编码 | 3h | 现场编码环节 |
| P1 | 系统设计 | 3h | 至少准备 1 个完整题 |
| P2 | Kafka | 2h | 口头问答可能涉及 |
| P3 | AWS | 1h | 加分项 |
| 砍掉 | 详细行为问题练习 | — | 你已经有故事，需要的是技术 |
