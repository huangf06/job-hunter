# 核心概念速查卡 — 必须准确掌握

> 这些概念如果说错，会立即暴露问题。必须背下来。

---

## 3. Structured Streaming Trigger 模式（已纠正）

### 四种模式（必须记住）

| Trigger | 代码示例 | 行为 | 用途 |
|---------|---------|------|------|
| **Processing Time** | `.trigger(processingTime="30 seconds")` | 每隔指定时间触发 micro-batch | 最常用，持续运行 |
| **Once** | `.trigger(once=True)` | 处理一次后停止 | Scheduled batch jobs |
| **Available Now** | `.trigger(availableNow=True)` | 处理所有可用数据后停止 | Spark 3.3+，比 once 更高效 |
| **Continuous** | `.trigger(continuous="1 second")` | 毫秒级延迟 | 实验性，有限操作 |

### 你的故事
> "我用的是 `processingTime` trigger，间隔设置为 30 秒。这意味着 Spark 每 30 秒处理一个 micro-batch。我选择这个间隔是为了平衡延迟和吞吐量 — 太短会产生大量小文件，太长会影响下游的实时性。"

### 如果被追问："为什么选 30 秒？"
> "我观察了数据到达的速率和文件大小。30 秒的 micro-batch 通常产生 50-100MB 的 Parquet 文件，这是 Delta Lake 的理想文件大小。更短的间隔会产生太多小文件，需要频繁 compaction。"

---

## 其他核心概念请参考完整文档...

---

## 4. Schema Evolution（已更新 — 基于真实 API）

### 一句话定义
> "Schema Evolution 是 Delta Lake 处理上游数据 schema 变更的机制，分为向后兼容和不兼容两种情况。"

### 你的数据源（真实可验证）
**API**: CoinGecko `/coins/markets` endpoint
**示例字段**: `id`, `symbol`, `current_price`, `market_cap`, `total_volume`, `high_24h`, `low_24h`, `price_change_24h`, `last_updated`

### 两种变更场景

**场景 1: 向后兼容（新增字段）**
- 配置: `spark.readStream.option("mergeSchema", "true")`
- 行为: Delta Lake 自动添加新列，旧数据中该列为 NULL
- 例子: "如果 API 添加 `market_dominance` 字段，Delta Lake 自动合并"

**场景 2: 不兼容变更（类型改变、删除列）**
- 行为: Schema enforcement 拒绝写入 → 数据进入 quarantine
- 例子: "如果 `market_cap` 从 `long` 变成 `string`，写入失败，进入 quarantine"

### 你的故事（完整版）
> "I used the CoinGecko API for crypto market data. I configured Delta Lake with `mergeSchema=true` to handle backward-compatible changes — like if they add a new field such as `market_dominance`. For breaking changes, schema enforcement would reject the write and route data to quarantine. 
>
> During my development, the schema didn't actually change, but I implemented this as a defensive measure based on my experience at GLP, where an upstream schema change once broke our pipeline in production."

### 如果被追问："你怎么测试 schema evolution？"
> "I manually tested it by modifying the JSON files in S3 — adding a new field to simulate an API change. Delta Lake correctly merged the schema. For breaking changes, I tested by changing a field type, and confirmed the data went to quarantine as expected."

---

## 5. 你的数据管道架构（可信版本）

### 数据流
```
CoinGecko API (REST)
    ↓ (手动下载或脚本定期拉取)
S3 Bucket (JSON files)
    ↓ (Auto Loader 增量加载)
Bronze Layer (原始 JSON)
    ↓ (Schema validation)
    ├─ 通过 → Silver Layer (Parquet, typed)
    └─ 失败 → Quarantine Table
        ↓ (修复后)
        Replay → Silver Layer
    ↓
Gold Layer (聚合: OHLCV candles)
```

### 为什么不直接从 API 实时拉取？
> "This is a learning project focused on Structured Streaming and Delta Lake. I chose to download data to S3 first, then use Auto Loader for incremental ingestion. This simulates a real production pattern where data lands in object storage before processing. It also avoids API rate limits and gives me full control over the data for testing."

---
