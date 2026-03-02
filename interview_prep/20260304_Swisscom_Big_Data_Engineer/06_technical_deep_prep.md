# Swisscom Big Data Engineer - 第二轮技术面试深度准备

## 面试基本信息

- **日期**: 2026-03-04（周三）10:00 CET
- **平台**: Microsoft Teams
- **性质**: 第二轮技术面试（已通过 CoderPad 编程测试）
- **时长**: 预计 1-2 小时

### 面试官

| 姓名 | 角色 | 备注 |
|------|------|------|
| **Ioannis (Yannis) Klonatos** | 主要技术面试官 | EPFL PhD, VLDB 2014 最佳论文奖, 693 citations |
| **Mani Bastaniparizi** | 主要技术面试官 | 高级工程师（公开信息有限）|
| **Deepthi Thachett** (optional) | Scrum Master / Lean Agile Leader | 过程方法论，非深度技术 |
| **Monica Nicoara** (optional) | 高级领导 (DNA Division) | IMD 商学院，可能有 CS 研究背景 |

---

## 第一部分：了解你的面试官 — Yannis Klonatos

**这是你面试中最关键的变量。** Yannis 不是一般的工程师，他是一位有深厚学术功底的系统专家。

### 学术背景
- **EPFL 博士** (2017)：导师 Christoph Koch (DATA Lab)
- **博士论文**: "Building Efficient Query Engines using High-Level Languages"
- **VLDB 2014 最佳论文奖**: LegoBase — 用 Scala 编写的查询引擎，通过生成式编程生成优化的 C 代码
- **核心哲学**: **"Abstraction Without Regret"** — 高层抽象不必牺牲性能
- **早期研究** (University of Crete): SSD 缓存、块级压缩、存储 I/O 优化
- **发表论文**: VLDB, SIGMOD (x2), EuroSys, ACM TODS — 数据库系统顶级会议全覆盖

### 技术专长
- **查询编译与优化**: 他的 PhD 就是构建查询引擎
- **生成式编程/元编程**: Scala → 生成优化 C 代码
- **存储系统与 I/O**: SSD 缓存、块级压缩
- **分布式处理**: Squall (Storm 上的实时分析), Spark (GitHub 上 fork 了)
- **编程语言**: Scala (主力), Java, C, Python

### 这意味着什么？

**他会问"为什么"而不仅仅是"怎么做"。** 准备好解释：
- 为什么选择这个数据结构/算法
- 性能 trade-off 是什么
- 如何从高层抽象映射到底层执行
- 你的设计决策背后的推理

**他对 Spark 的理解可能比你深。** 他研究查询优化器 — 这就是 Spark Catalyst 做的事情。不要只停留在 API 层面，准备好讨论 Catalyst optimizer、Tungsten 内存管理等内部机制。

**他重视"clean code that performs well"。** 如果有编码环节，写出既优雅又高效的代码。

---

## 第二部分：面试格式预测

根据 Glassdoor 上 Rotterdam Data Engineer 面试的精确描述：

> "A presentation, questions about your CV, technical verbal questions, and a live coding challenge (SQL followed by a Java/programming exercise)."

### 预期结构

| 环节 | 时长 | 内容 |
|------|------|------|
| 1. 自我介绍 / CV 讨论 | 15-20 min | 项目经验深挖，技术选型追问 |
| 2. 技术口头问答 | 20-30 min | Spark, SQL, 分布式系统, 数据建模 |
| 3. 现场编码 | 20-30 min | SQL 题 + Python/编程题 |
| 4. 你的提问 | 10-15 min | 展示调研深度 |

**关键情报**: 面试官卡住时**会给提示**（Glassdoor 多人证实）。这说明他们看重的是**思维过程**，不是完美答案。

---

## 第三部分：你的简历 — 面试官会深挖的点

根据你提交的简历，以下是面试官最可能追问的技术细节：

### 3.1 Financial Data Lakehouse（最重要 — 最近的项目）

**他们会问的**：
1. "Tell me about the watermarking and event-time windowing you implemented. Why watermarking instead of processing-time windows?"
2. "How does your quarantine-and-replay pattern work? Walk me through what happens when a malformed record arrives."
3. "You mention Auto Loader and Structured Streaming — what's the difference and when do you use each?"
4. "How did you handle schema evolution? What happens when a new field is added to the upstream feed?"
5. "What does Z-ordering do and why did you choose it over other optimization strategies?"

**你的深度回答准备**：

**Watermarking + Event-time windowing**:
- Event-time = 事件实际发生的时间，不是到达处理系统的时间
- 在 crypto 市场数据中，延迟数据很常见（网络延迟、交易所 API 不稳定）
- Watermark 定义了"多久之前的数据我们还愿意等待" — 例如 watermark = 10 minutes 意味着如果数据晚到超过 10 分钟就丢弃
- **与 Swisscom 的关联**: 网络事件数据同样面临延迟问题（手机信号弱时事件可能延迟上报），watermarking 是通用解决方案

**Quarantine-and-replay 模式**:
```
Bronze层: 接收所有原始数据（包括坏数据）
  ↓ schema 验证
Silver层: 通过验证的 → 正常处理
  ↓ 失败的 → quarantine 表
Quarantine表: 记录错误原因、原始数据、时间戳
  ↓ 修复 schema/逻辑后
Replay: 从 quarantine 重新处理 → Silver层
```
- 关键原则: **永不丢弃数据** — Bronze 层保留一切，quarantine 允许事后修复

**Auto Loader vs Structured Streaming**:
- Auto Loader: 增量处理**文件**（新到达的 JSON/CSV/Parquet 文件），自动发现新文件，exactly-once 语义
- Structured Streaming: 处理**流数据源**（Kafka, Event Hubs 等），微批或连续处理
- 我的用法: Auto Loader 处理历史批量数据文件，Structured Streaming 处理实时 Kafka feeds

**Z-ordering**:
- 多维排序优化，将数据按指定列在物理存储上 co-locate
- 减少需要读取的文件数量（data skipping）
- 我选择按 `symbol` 和 `timestamp` Z-order，因为查询模式通常是 "某个 symbol 在某个时间段" — 这让 Spark 可以跳过 90%+ 的文件

### 3.2 GLP Technology（展示从零构建的能力）

**他们会问的**：
1. "As the first data hire, how did you decide what to build first?"
2. "Walk me through the PySpark ETL pipeline — what was the source, transformation, and target?"
3. "How did you implement the credit scoring model? What features were most predictive?"
4. "How did you handle data quality in a startup environment?"

**你的深度回答准备**：

**优先级决策**:
- 第一周: 理解业务 — 消费信贷的核心指标（违约率、催收率、获客成本）
- 第一个月: 数据摄取管道 — 从贷款申请系统拉取数据到分析环境
- 第二个月: 特征工程 + 初版信贷评分模型
- 第三个月+: 自动化决策系统、监控、迭代改进
- **原则**: Start with data ingestion, then analytics, then automation

**PySpark ETL 管道**:
- Source: 消费贷款系统 (MySQL)、第三方征信数据、用户行为数据
- Transform: 清洗 → 特征工程（申请特征、行为特征、征信特征） → 聚合
- Target: 分析数据库 + 模型训练数据集
- 全贷款生命周期: 申请 → 审批 → 放款 → 还款 → 逾期 → 催收

### 3.3 Baiquan Investment（展示数据质量意识）

**他们会问的**：
1. "How did you detect vendor data gaps? What metrics did you monitor?"
2. "3000+ securities — what was the data volume and how did you scale?"
3. "What was the factor computation engine? How did you optimize with vectorization?"

**你的回答要点**：
- 数据完整性检查: 每个交易日，每只证券都应有 OHLCV 数据 → 缺失 = 告警
- 跨源验证: 比较多个供应商的价格，差异超过阈值 = 标记
- 向量化: 使用 NumPy broadcasting 而不是 Python for 循环 — 100x+ 性能提升
- **与 Swisscom 的关联**: 网络数据同样需要跨源验证（不同系统的数据应该一致）

### 3.4 Expedia Hotel Recommendation（展示 ML 能力）

**他们会问的**：
1. "Walk me through the NDCG metric — why NDCG instead of accuracy?"
2. "What features were most important? How did you do feature engineering?"
3. "XGBoost vs other models — why?"

**关键回答**：
- NDCG@5 = 衡量排名质量的指标，不是二分类问题，而是推荐排序问题
- Top 5% on Kaggle = 从 4.9M booking records 中识别用户偏好
- XGBoost: 处理缺失值好、特征重要性可解释、在结构化数据上表现优于深度学习

---

## 第四部分：核心技术深度题 — 针对 Yannis 的背景定制

### 4.1 Spark 内部机制（高概率考察）

**Q: "Explain how Spark executes a SQL query from start to finish."**

这个问题直击 Yannis 的研究领域。你的回答：

```
SQL 查询 → 解析 (Parser) → 逻辑计划 (Logical Plan)
  → Catalyst Optimizer (规则 + 成本优化)
  → 物理计划 (Physical Plan)
  → RDD 代码生成 (Tungsten Code Gen)
  → 任务调度 → 执行
```

- **Catalyst Optimizer**: 基于规则的优化（谓词下推、列裁剪、常量折叠）+ 基于成本的优化（join 重排序）
- **Tungsten**: whole-stage code generation，将多个操作符融合为单个 Java 方法，避免虚函数调用开销
- **这与 Yannis 的 LegoBase 异曲同工**: LegoBase 将 Scala 查询引擎编译为优化 C 代码，Tungsten 将 Spark 算子编译为优化 JVM 字节码 — 都是 "abstraction without regret"

**Q: "What causes data skew in Spark and how do you handle it?"**

- **原因**: key 分布不均匀 → 某些分区远大于其他分区 → 一个 task 处理大量数据，其他 task 空闲等待
- **检测**: Spark UI → 查看 stage 中 task 的运行时间差异
- **解决方案**:
  1. **Salting**: 给 skewed key 加随机前缀，分散到多个分区，然后二次聚合
  2. **Broadcast join**: 如果一个表小（<10MB），广播到所有节点避免 shuffle
  3. **AQE (Adaptive Query Execution)**: Spark 3.0+ 自动检测 skew 并拆分大分区
  4. **自定义 partitioner**: 根据数据分布设计分区策略
- **你的实际经验**: 在 Financial Lakehouse 中，某些 crypto symbol 的交易量远高于其他 — 使用 Z-ordering + 合理分区避免

**Q: "RDD vs DataFrame vs Dataset — when to use what?"**

- **RDD**: 低级 API，完全控制但没有优化
- **DataFrame**: 有 schema 的 RDD，Catalyst 优化器可以优化，推荐用于 ETL
- **Dataset**: 类型安全的 DataFrame（Scala/Java），编译时类型检查
- **实践**: 99% 的情况用 DataFrame (PySpark) 或 Dataset (Scala) — 让 Catalyst 做优化

### 4.2 SQL 深度（几乎必考）

**Q: "Write a query to find the top 3 products by revenue for each category."**

```sql
WITH ranked AS (
    SELECT
        category,
        product_name,
        SUM(revenue) AS total_revenue,
        ROW_NUMBER() OVER (
            PARTITION BY category
            ORDER BY SUM(revenue) DESC
        ) AS rk
    FROM sales
    GROUP BY category, product_name
)
SELECT category, product_name, total_revenue
FROM ranked
WHERE rk <= 3;
```

**讨论点**:
- `ROW_NUMBER` vs `RANK` vs `DENSE_RANK`: 处理并列的差异
- Window function 在 Spark SQL 中如何执行（先 sort，然后 window 计算）
- 如果数据量巨大，`PARTITION BY category` 的性能影响

**Q: "Explain star schema vs snowflake schema."**

- **Star schema**: 一个 fact 表 + 多个 dimension 表直接连接，查询简单高效
- **Snowflake schema**: dimension 表进一步 normalize（例如 location → city → country），节省存储但查询更多 join
- **在 Swisscom 的场景**: 网络事件 fact 表（cell_tower_id, timestamp, event_type, metrics）+ 维度表（cell_tower_details, device_type, network_type）
- **我的偏好**: 在分析场景中倾向 star schema — 牺牲一些存储换取查询性能

**Q: "How would you optimize a slow SQL query?"**

1. `EXPLAIN ANALYZE` 查看执行计划
2. 检查是否有 full table scan → 需要索引或分区
3. 检查 join 顺序 → 大表 join 小表时确保小表在右侧（或使用 hint）
4. 检查数据倾斜 → 某个 partition 是否远大于其他
5. 考虑物化视图或预聚合表

### 4.3 Kafka 与流处理（Polaris 团队核心）

**Q: "Design a data pipeline that processes network events in real-time."**

结合 Swisscom 实际场景（每天 200 亿网络事件, 2TB）：

```
手机 → 基站 → 网络事件系统
                    ↓
            Kafka Producer (per region)
                    ↓
            Kafka Topics (partitioned by cell_tower_id)
                    ↓
    ┌──────────────┼──────────────┐
    ↓              ↓              ↓
Spark Streaming  Flink          Real-time alerts
(aggregation)   (anomaly)      (simple rules)
    ↓              ↓              ↓
 S3/Data Lake   Alert System   Dashboard
    ↓
 Redshift (analytics)
```

**关键设计决策**:
- **为什么 Kafka 分区用 cell_tower_id**: 同一基站的事件保持顺序，方便时序分析
- **为什么同时用 Spark Streaming 和 Flink**: Spark 擅长大规模聚合（batch-like），Flink 擅长低延迟事件处理
- **Exactly-once semantics**: Kafka → Spark Streaming 通过 checkpoint + idempotent writes 实现
- **Schema evolution**: 使用 Kafka Schema Registry + Avro/Protobuf

**Q: "Kafka consumer groups — how do they work?"**

- 同一 consumer group 内的 consumer 共享 topic 的 partitions（每个 partition 只被一个 consumer 读取）
- 不同 consumer group 独立消费（广播模式）
- **Rebalancing**: consumer 加入/离开时，partition 重新分配
- **Offset management**: consumer 提交 offset 标记已处理位置 → 故障恢复从上次 offset 继续

### 4.4 数据建模（Yannis 有 SCD Type 2 经验）

**Q: "How do you handle slowly changing dimensions?"**

Yannis 的 CleanerVersion 项目就是做 SCD Type 2 的！

- **SCD Type 1**: 直接覆盖旧值（丢失历史）
- **SCD Type 2**: 新增行，加 valid_from / valid_to 字段（保留完整历史）
- **SCD Type 3**: 加列（current_value, previous_value）（只保留一次历史）
- **我的实际经验**: 在 Baiquan 处理证券元数据（公司名变更、行业重分类）时使用 SCD Type 2
- **在 Delta Lake 中**: 使用 `MERGE INTO` + `whenMatched().update()` + `whenNotMatched().insert()` 实现

### 4.5 AWS 相关（Polaris 团队迁移到 AWS）

**Q: "How would you design a data lake on AWS?"**

```
Sources → Kinesis/Kafka → S3 (Raw/Bronze)
                              ↓
                         AWS Glue (ETL)
                              ↓
                         S3 (Cleaned/Silver)
                              ↓
                    ┌─────────┼──────────┐
                    ↓         ↓          ↓
                 Athena    Redshift   SageMaker
                (ad-hoc)  (analytics)   (ML)
                              ↓
                         QuickSight (BI)
```

- **Data Catalog**: AWS Glue Data Catalog 统一元数据管理
- **Governance**: Lake Formation 控制访问权限
- **成本优化**: S3 Intelligent-Tiering + Redshift 自动暂停
- **IaC**: AWS CDK (TypeScript) — 正是 Swisscom One Data Platform 的做法

---

## 第五部分：Python 编码准备

### 可能的编码题型（基于 Glassdoor + CoderPad 后续轮次）

**题目 1: 数据处理类**

"Given a list of network events (timestamp, cell_tower_id, event_type), find the top 5 busiest cell towers in each hour."

```python
from collections import defaultdict
from datetime import datetime

def top_towers_per_hour(events):
    """
    events: list of (timestamp_str, cell_tower_id, event_type)
    returns: dict of hour -> [(tower_id, count), ...]
    """
    counts = defaultdict(lambda: defaultdict(int))

    for ts_str, tower_id, _ in events:
        ts = datetime.fromisoformat(ts_str)
        hour_key = ts.strftime('%Y-%m-%d %H:00')
        counts[hour_key][tower_id] += 1

    result = {}
    for hour, tower_counts in counts.items():
        sorted_towers = sorted(
            tower_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        result[hour] = sorted_towers

    return result
```

**优化讨论点**: 如果数据量太大装不进内存 → 使用 Spark GroupBy + Window function

**题目 2: 算法类**

"Implement a function to detect anomalies in a time series of network metrics using a sliding window approach."

```python
def detect_anomalies(values, window_size=10, threshold=2.0):
    """
    Detect values that are > threshold standard deviations from the window mean.
    Returns indices of anomalous values.
    """
    anomalies = []

    for i in range(window_size, len(values)):
        window = values[i - window_size:i]
        mean = sum(window) / window_size
        variance = sum((x - mean) ** 2 for x in window) / window_size
        std = variance ** 0.5

        if std > 0 and abs(values[i] - mean) > threshold * std:
            anomalies.append(i)

    return anomalies
```

**讨论点**:
- 如何选择 window_size 和 threshold？
- 更高级: exponential moving average, ARIMA, Isolation Forest
- 在生产环境中: 还需要考虑季节性（网络流量有日/周模式）

**题目 3: 数据结构类**

"Implement an LRU cache." (考察数据结构理解)

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

---

## 第六部分：你应该问的问题（展示调研深度）

### 展示你做了功课的问题

1. **"I noticed Swisscom maintains a `swisscom-bigdata` GitHub org with forks of Spark, Flink, and Calcite. Does the Polaris team contribute patches back to these projects, or are these for internal customization?"**
   - 展示你调研了他们的技术栈

2. **"I read about Swisscom's One Data Platform on the AWS blog — the CDK-based infrastructure-as-code approach for Redshift provisioning. Is the Polaris team part of this migration from on-prem Hadoop to AWS, or is it a separate initiative?"**
   - 展示你理解他们的战略方向

3. **"The JD mentions transforming raw network data into actionable insights for mobile network planning. At what scale are we talking — I've seen references to billions of network events per day for major telecoms. Is the processing primarily batch, streaming, or a hybrid approach?"**
   - 展示你理解电信数据的规模

### 技术深度问题

4. "What does the typical data pipeline look like in the Polaris team — from data ingestion to the final data product?"
5. "How do you handle data quality at scale? Do you use something like Great Expectations, dbt tests, or a custom framework?"
6. "What's the team's approach to testing data pipelines? Unit tests, integration tests, data validation?"

### 针对 Yannis 的问题（如果合适的时机）

7. **"I'm curious about the trade-offs between Spark and Flink for your use cases. Given your background in query optimization, do you find Spark's Catalyst optimizer sufficient for your workloads, or are there cases where you need more control?"**
   - 这会触动他的研究兴趣，可能引发一段有深度的技术讨论

---

## 第七部分：面试时间线策略

### 09:30 - 面试前 30 分钟
- 打开 Teams，测试音频/视频
- 打开此文档的速查部分（第八部分）
- 深呼吸，调整心态

### 10:00 - 面试开始

**开场自我介绍（2 分钟，精练版）**：

> "Hi, I'm Fei. I'm a data engineer with about 6 years of experience, currently based in Amsterdam. I recently completed my Master's in AI at VU Amsterdam and earned my Databricks Data Engineer Professional certification.
>
> My career has spanned multiple data-intensive domains — from building credit scoring infrastructure at a consumer lending startup in Shanghai, to engineering market data pipelines for quantitative research, to most recently building a real-time financial data lakehouse on Databricks with Spark Structured Streaming.
>
> I'm particularly excited about the Polaris team because the challenge of transforming raw network data at telco scale into actionable insights is exactly the kind of problem I love — building reliable, scalable data pipelines that directly drive business decisions."

**关键原则**：
- 每个回答先给 **1 句话总结**，然后展开细节
- 卡住时说出思维过程: "Let me think about this... My first instinct is..."
- 用 **具体数字**: "3000+ securities", "4.9 million records", "2x improvement"
- 展示 **trade-off 思维**: "I chose X over Y because..."

### 面试结束时

> "Thank you for the deep technical discussion — this has really reinforced my interest in the Polaris team. The scale of network data processing and the team's approach to data engineering is exactly what I'm looking for. What would be the next steps in the process?"

---

## 第八部分：速查表（面试时打开）

### Spark 关键概念
| 概念 | 一句话 |
|------|--------|
| Catalyst | 基于规则+成本的查询优化器（谓词下推、列裁剪、join 重排序）|
| Tungsten | 内存管理+代码生成（whole-stage codegen，融合操作符）|
| Shuffle | 跨分区数据重分配（groupBy, join 触发）— 最昂贵的操作 |
| Broadcast join | 小表广播到所有节点，避免 shuffle |
| AQE | 运行时自动调整（合并小分区、处理 skew、切换 join 策略）|
| Checkpointing | 将中间结果写入可靠存储，故障时从检查点恢复 |
| Structured Streaming | 微批处理模型，将流视为无限增长的表 |
| Delta Lake | ACID 事务 + 时间旅行 + schema enforcement + Z-ordering |

### Kafka 关键概念
| 概念 | 一句话 |
|------|--------|
| Topic | 消息的逻辑分类（例如 network_events）|
| Partition | Topic 的物理分片，保证分区内顺序 |
| Consumer Group | 一组 consumer 共享 partition，实现并行消费 |
| Offset | consumer 在 partition 中的位置标记 |
| Exactly-once | 通过幂等 producer + 事务性 consumer + checkpoint 实现 |
| Schema Registry | 管理消息的 Avro/Protobuf schema，确保兼容性 |
| Kafka Connect | 标准化的 source/sink connector 框架 |

### SQL 速记
| 模式 | 用法 |
|------|------|
| `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` | 分组内排名 |
| `LAG/LEAD(col, n) OVER (ORDER BY ...)` | 访问前/后 n 行 |
| `SUM(col) OVER (ORDER BY ... ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)` | 累计求和 |
| `MERGE INTO target USING source ON ... WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT` | SCD Type 2 |
| CTE `WITH x AS (...)` | 可读性好的子查询 |

### 你的数字
| 指标 | 数字 |
|------|------|
| 工作经验 | 6 年 |
| GLP 证券数 | 3000+ securities |
| Expedia 数据量 | 4.9M booking records |
| Expedia 排名 | Top 5% Kaggle (NDCG@5 = 0.392) |
| Ele.me 成果 | 2x 重新激活率, 30% 查询优化 |
| 硕士 GPA | 8.2/10 |
| 相关课程 | Deep Learning 9.5, Multi-Agent 9.5, NLP 9.0, Data Mining 9.0 |

### Swisscom 数字（展示你做了功课）
| 指标 | 数字 |
|------|------|
| 日网络事件数 | 200 亿 / 天 |
| 日数据量 | 2 TB / 天 |
| SIM 卡追踪数 | 600 万 |
| 处理吞吐量 | 600,000+ data points / second |
| 空间分辨率 | 100m x 100m quadrants |
| Rotterdam 员工数 | 400+ |
| Rotterdam 国籍数 | 60+ |
| Vodafone Italia 收购 | 80 亿欧元 (2024.12 完成) |

---

## 第九部分：风险点与应对

### 最大风险: Scala

**如果他问**: "Do you have Scala experience?"

**你的回答**:
> "I haven't used Scala in production, but I understand the JVM ecosystem well from my Java background. More importantly, I understand the functional programming concepts that Scala leverages — immutability, higher-order functions, pattern matching — from my AI coursework and from working with PySpark's functional API. I'm confident I can pick up Scala quickly, and I've been reading about it in preparation for this role."

### 风险: 职业空白期 (2019-2023)

**简短积极回答** (不超过 30 秒):
> "During that period, I was preparing for a career pivot — I invested independently, built up my English fluency, and spent a year preparing for graduate school. It was a deliberate decision to invest in a stronger foundation before moving to Europe for my AI master's degree."

### 风险: 没有电信领域经验

**桥接回答**:
> "While I haven't worked in telecom specifically, I've consistently proven my ability to quickly ramp up in new domains — from consumer lending at GLP, to quantitative finance at Baiquan, to food delivery at Ele.me. The core data engineering challenges are universal: ingestion at scale, data quality, reliable pipelines, and delivering actionable insights. And frankly, the scale of network data — billions of events per day — is the kind of challenge that excites me as a data engineer."

---

## 第十部分：心态

1. **你已经通过了编程测试** — 他们已经验证了你的编码能力，现在要看的是深度和判断力
2. **Yannis 是学术出身** — 他会欣赏你能讨论"为什么"而不只是"怎么做"
3. **周三上午 10:00 是黄金窗口** — 你和面试官都在认知巅峰
4. **他们需要人** — Swisscom DevOps Center 正在积极扩张，他们希望你成功
5. **面试是双向的** — 你也在评估他们

**最后提醒**: 如果遇到不会的问题，**说出你的思考过程**。Yannis 作为一个系统思考者，会比你想象的更重视你如何 approach 一个未知问题，而不是你是否知道答案。
