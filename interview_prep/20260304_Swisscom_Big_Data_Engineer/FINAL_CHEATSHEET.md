# Swisscom Big Data Engineer - 面试速查表 (A4)
**面试时间**: 2026-03-04 10:00 CET | Yannis Klonatos (EPFL PhD) + Mani

---

## 📊 关键数字 (必须记住)

### 个人背景
- **6 years** 数据工程经验
- **8.2 GPA** (VU Amsterdam AI 硕士)
- **3,000+ securities** (Baiquan 市场数据)
- **Databricks Professional** (2026-01)

### Financial Lakehouse 项目
- **26 fields** (CoinGecko API)
- **Top 100 coins** 实时追踪
- **每 5 分钟** 拉取一次
- **~29,000 records/day**
- **30 秒** trigger interval
- **10 分钟** watermark (基于 P99 延迟 ~8 min)
- **85% ↓** files scanned (Z-ordering)
- **6.7x faster** queries
- **<0.1%** quarantine rate

### Swisscom Polaris
- **Billions** of network events/day
- **2TB/day** 数据量
- **4-person team** (Yannis, Mani, Deepthi, Monica)

---

## 🎤 自我介绍 (< 2 分钟)

> "Hi, I'm Fei. Data engineer, **6 years** experience, Amsterdam based.
>
> **Master's in AI from VU Amsterdam (GPA 8.2)**, **Databricks Data Engineer Professional** certified.
>
> Three domains: **founding data hire at GLP** (credit scoring from scratch), **market data pipelines at Baiquan** (3000+ securities), **real-time financial lakehouse** on Databricks.
>
> Excited about Polaris — transforming **billions of network events/day** into actionable insights is exactly my kind of challenge."

---

## 🔥 核心技术点 (一句话回答)

| 技术 | 一句话 |
|------|--------|
| **Checkpoint** | Stores offsets, commits, state to S3; crash recovery from last commit; exactly-once semantics |
| **Watermarking** | `max(event_time) - threshold`; I use 10 min (P99 latency ~8 min); controls late data cutoff |
| **Z-ordering** | Multi-dimensional sorting; co-locates data by columns; 85% fewer files scanned, 6.7x faster |
| **Quarantine-Replay** | Bronze captures all → validation → Silver/Quarantine → fix → replay → never lose data |
| **Medallion** | Bronze (raw JSON, schema-on-read) → Silver (Parquet, enforced) → Gold (business aggregates) |
| **Shuffle** | Redistribute data by key hash across partitions; 3 costs: disk I/O, network, serialization |
| **Data Skew** | Hot keys cause partition imbalance; solve with salting, broadcast join, or AQE |
| **Catalyst** | Query optimizer: parse → resolve → optimize (pushdown, pruning) → physical plan (CBO) |
| **Tungsten** | Execution engine: off-heap memory, cache-aware layout, whole-stage code generation |

---

## 🔀 Join 策略对比

| Join 类型 | 何时用 | Shuffle? | 内存要求 | 速度 |
|----------|--------|---------|---------|------|
| **Broadcast Hash** | 小表 < 10MB | ❌ | 小表装进每个 executor | 🚀 最快 |
| **Shuffle Hash** | 一个表明显小 | ✅ | 小表每个 partition 装进内存 | 🏃 快 |
| **Sort Merge** | 两个表都很大 | ✅ | 只需两个指针 | 🚶 慢 |

**关键点**:
- Partition ≠ Machine (逻辑 vs 物理)
- `partition_id = hash(key) % num_partitions` 保证相同 key 在同一 partition
- 推荐 partition 数 = 核心数 × 2-3 倍

---

## 📝 SQL 常考语句

### 1. Window Function - Top N per Group
```sql
WITH ranked AS (
    SELECT
        category, product_name, SUM(revenue) AS total_revenue,
        ROW_NUMBER() OVER (PARTITION BY category ORDER BY SUM(revenue) DESC) AS rk
    FROM sales
    GROUP BY category, product_name
)
SELECT category, product_name, total_revenue
FROM ranked
WHERE rk <= 3;
```

### 2. Cumulative Sum
```sql
SELECT
    date, amount,
    SUM(amount) OVER (ORDER BY date ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative
FROM transactions;
```

### 3. LAG/LEAD (前后行对比)
```sql
SELECT
    date, price,
    LAG(price, 1) OVER (ORDER BY date) AS prev_price,
    price - LAG(price, 1) OVER (ORDER BY date) AS price_change
FROM stock_prices;
```

### 4. SCD Type 2 (Slowly Changing Dimension)
```sql
MERGE INTO dim_users AS target
USING source_users AS source
ON target.user_id = source.user_id AND target.is_current = true
WHEN MATCHED AND target.name != source.name THEN
    UPDATE SET is_current = false, valid_to = current_date()
WHEN NOT MATCHED THEN
    INSERT (user_id, name, is_current, valid_from, valid_to)
    VALUES (source.user_id, source.name, true, current_date(), '9999-12-31');
```

### 5. Star Schema Join
```sql
SELECT
    f.order_id, f.amount,
    d_customer.name, d_product.category, d_time.year
FROM fact_orders f
JOIN dim_customer d_customer ON f.customer_id = d_customer.customer_id
JOIN dim_product d_product ON f.product_id = d_product.product_id
JOIN dim_time d_time ON f.date_id = d_time.date_id
WHERE d_time.year = 2026;
```

---

## 🛠️ Spark 优化技巧

### Data Skew 解决方案
```python
# Salting (加盐)
df_salted = df.withColumn(
    "salted_key",
    when(col("user_id").isin(hot_keys),
         concat(col("user_id"), lit("_"), (rand() * 10).cast("int"))
    ).otherwise(col("user_id"))
)

# Broadcast Join
result = large_df.join(broadcast(small_df), "key")

# AQE (Spark 3.0+)
spark.conf.set("spark.sql.adaptive.enabled", "true")
spark.conf.set("spark.sql.adaptive.skewJoin.enabled", "true")
```

### Partition 调优
```python
# 增加 partition 数
spark.conf.set("spark.sql.shuffle.partitions", "1000")

# 手动 repartition
df.repartition(500, "user_id")
```

---

## 🎯 STAR 故事速记

| 故事 | 关键数字 | 用于回答 |
|------|---------|---------|
| **Schema Evolution** | 30 min 恢复，零数据丢失 | 处理生产事故 |
| **GLP 首位数据员工** | 从零构建信贷评分基础设施 | 最大挑战 / 独立工作 |
| **Baiquan 数据中断** | 15 min 恢复，切换备用源 | 紧急问题处理 |
| **Databricks 学习** | 3 个月从零到 Professional | 学习新技术 |
| **Ele.me 用户细分** | 2x 重新激活率，30% 查询优化 | 业务影响力 |

---

## 🚨 三大弱点桥接

| 弱点 | 桥接回答 |
|------|---------|
| **Scala** | "No production experience, but understand JVM + functional programming (immutability, HOF). PySpark API is functional. Confident I can pick up Scala quickly." |
| **电信领域** | "Proven adaptability across 3 domains (credit→finance→food). Core data engineering challenges are universal: scale, quality, reliability." |
| **职业空白 (2019-2023)** | "Deliberate career pivot: independent investing + language learning + grad school prep. Led to AI master's at VU Amsterdam." |

---

## ❓ 你要问的问题 (至少 2 个)

1. **"Are you using Lambda, Kappa, or custom architecture for network data? How do you handle late-arriving events?"**
2. **"With a 4-person team at this scale, how do you balance feature development vs operational maintenance?"**
3. (备选) **"What would success look like for someone joining in this role in the first 6 months?"**

---

## 🧠 Catalyst + Tungsten 核心

### Catalyst 4 阶段
1. **Unresolved Logical Plan**: Parse SQL → AST
2. **Resolved Logical Plan**: Catalog lookup (tables, columns, types)
3. **Optimized Logical Plan**: Predicate pushdown, column pruning, constant folding, join reordering
4. **Physical Plan**: CBO (cost-based optimization) selects best execution strategy

### Tungsten 3 大优化
1. **Off-heap Memory**: Binary format, 5-10x less memory, no GC overhead
2. **Cache-aware Computation**: Contiguous layout, maximize CPU cache hits
3. **Whole-stage Code Generation**: Fuse operators, eliminate virtual function calls

**关键概念**: "Abstraction Without Regret" (Yannis 的 LegoBase 论文) — 高层抽象不牺牲性能

---

## 📐 架构模式

### Medallion Architecture
| 层 | 格式 | Schema | 用途 |
|----|------|--------|------|
| **Bronze** | JSON | Schema-on-read | 保真、审计、replay |
| **Silver** | Parquet | Enforced | 分析基础 |
| **Gold** | Parquet | 业务视图 | 直接服务查询 |

### Star Schema vs Snowflake
- **Star**: 1 fact + N dimension (直接连接) → 查询简单高效
- **Snowflake**: Dimension 进一步 normalize → 节省存储但更多 join

---

## 🎬 面试中的 5 个原则

1. **先给概述，再分层展开** — 让面试官知道你理解问题
2. **主动提供例子** — 代码片段、数字、图表
3. **观察面试官反应** — 点头继续，皱眉停下问 "Should I go deeper?"
4. **展现学习能力** — 强调 3 个月从零到 Databricks Professional
5. **保持热情和好奇心** — 这是你的优势

---

## 🚫 如果遇到不会的问题

**策略 1**: "I haven't worked with that specific technology, but based on my understanding of [related concept], I would approach it like this..."

**策略 2**: "That's a great question. Let me think through it... [第一性原理推理]. How does your team handle this?"

**策略 3**: "I don't have direct experience, but I'd start by [logical approach]. Could you share how Polaris approaches this?"

---

## 💪 信心加持

**你的优势**:
- ✅ 6 年经验 (JD 要求 4+)
- ✅ Databricks Professional 认证
- ✅ 完整项目经验 (覆盖所有技术栈)
- ✅ 学习能力强 (3 个月从零到认证)
- ✅ 已在荷兰 (无需 relocation)
- ✅ 已通过 CoderPad 编程测试

**记住**: 周三上午 10:00 = 黄金窗口 — 双方认知巅峰

---

**Good luck! 你已经准备好了！💪**
