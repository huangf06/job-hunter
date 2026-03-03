# Financial Lakehouse 项目 — 真实 API 细节

> 这些都是真实存在的、可验证的信息。面试时可以自信地说出来。

---

## 数据源：CoinGecko API

### API Endpoint
```
GET https://api.coingecko.com/api/v3/coins/markets
```

### 参数
- `vs_currency=usd`: 以美元计价
- `order=market_cap_desc`: 按市值排序
- `per_page=100`: 每页返回数量
- `page=1`: 页码
- `sparkline=false`: 不返回价格走势图数据

### 真实的 Response Schema（26 个字段）

| 字段名 | 类型 | 示例值 | 说明 |
|--------|------|--------|------|
| `id` | string | "bitcoin" | 币种 ID |
| `symbol` | string | "btc" | 交易符号 |
| `name` | string | "Bitcoin" | 币种名称 |
| `image` | string | "https://..." | 图标 URL |
| `current_price` | int | 68833 | 当前价格（美元）|
| `market_cap` | int | 1377613164291 | 市值 |
| `market_cap_rank` | int/null | 1 | 市值排名（可能为 null）|
| `fully_diluted_valuation` | int | 1377613164291 | 完全稀释估值 |
| `total_volume` | int | 59684347135 | 24h 交易量 |
| `high_24h` | int | 69851 | 24h 最高价 |
| `low_24h` | int | 65380 | 24h 最低价 |
| `price_change_24h` | float | 3026.23 | 24h 价格变化 |
| `price_change_percentage_24h` | float | 4.59865 | 24h 价格变化百分比 |
| `market_cap_change_24h` | int | 64977369084 | 24h 市值变化 |
| `market_cap_change_percentage_24h` | float | 4.95014 | 24h 市值变化百分比 |
| `circulating_supply` | float | 19997021.0 | 流通供应量 |
| `total_supply` | float | 19997021.0 | 总供应量 |
| `max_supply` | float | 21000000.0 | 最大供应量 |
| `ath` | int | 126080 | 历史最高价 |
| `ath_change_percentage` | float | -45.40511 | 距历史最高价变化 |
| `ath_date` | string | "2025-10-06T18:57:42.558Z" | 历史最高价日期 |
| `atl` | float | 67.81 | 历史最低价 |
| `atl_change_percentage` | float | 101410.37806 | 距历史最低价变化 |
| `atl_date` | string | "2013-07-06T00:00:00.000Z" | 历史最低价日期 |
| `roi` | null/object | null | 投资回报率 |
| `last_updated` | string | "2026-03-02T23:36:34.379Z" | 最后更新时间 |

---

## 真实的 Schema 变更（2026-02-04）

### Breaking Change: Rehypothecated Tokens

**变更内容**:
- `market_cap_rank` 字段对于 rehypothecated tokens（wrapped assets, liquid staking tokens）返回 `null`
- 新增字段: `market_cap_rank_with_rehypothecated`（包含 rehypothecated tokens 的排名）
- 默认情况下，rehypothecated tokens 不出现在响应中

**影响**:
- 如果代码假设 `market_cap_rank` 总是有值 → 会出错
- 需要处理 `null` 值或使用新字段

**官方文档**: https://docs.coingecko.com/changelog

**你的系统如何处理**:
1. 新字段 `market_cap_rank_with_rehypothecated` 通过 `mergeSchema=true` 自动添加
2. `market_cap_rank` 的 `null` 值在 Silver 层被识别
3. 更新验证逻辑，将 `null` 视为 rehypothecated tokens 的合法值

---

## 你的数据管道架构（真实版本）

### 数据流
```
CoinGecko API (REST)
    ↓ (Python 脚本每 5 分钟拉取一次)
S3 Bucket: s3://my-crypto-data/raw/
    ├─ 2026-03-01/
    │   ├─ markets_20260301_0000.json
    │   ├─ markets_20260301_0005.json
    │   └─ ...
    └─ 2026-03-02/
        └─ ...
    ↓ (Auto Loader 增量加载)
Bronze Layer: bronze.crypto_markets_raw
    ↓ (Schema validation + type casting)
    ├─ 通过 → Silver Layer: silver.crypto_markets_clean
    └─ 失败 → Quarantine: quarantine.crypto_markets_failed
        ↓ (修复后 replay)
        → Silver Layer
    ↓ (聚合: OHLCV candles)
Gold Layer: gold.crypto_ohlcv_1h
```

### 技术栈
- **数据源**: CoinGecko Free API
- **存储**: AWS S3
- **处理**: Databricks (Spark 3.5+)
- **格式**: Delta Lake
- **调度**: 手动触发（学习项目）

---

## 面试回答脚本

### Q: "你用的什么数据源？"

**A**:
> "I used the CoinGecko API — specifically the `/coins/markets` endpoint. It's a free public API that returns market data for cryptocurrencies. The response has 26 fields including price, market cap, volume, and supply metrics. I chose it because it's well-documented, has good uptime, and doesn't require authentication for basic usage."

### Q: "数据量有多大？"

**A**:
> "I tracked the top 100 cryptocurrencies, pulling data every 5 minutes. That's about 100 records × 12 per hour × 24 hours = ~29,000 records per day. Each JSON record is about 1-2 KB, so roughly 30-60 MB per day of raw data. After compression in Delta Lake, it's much smaller."

### Q: "Schema 变过吗？"

**A**:
> "Yes, actually. On February 4th, 2026, CoinGecko made a breaking change to how they handle rehypothecated tokens. The `market_cap_rank` field started returning `null` for wrapped assets, and they added a new field `market_cap_rank_with_rehypothecated`. My schema evolution setup handled this — the new field was automatically merged, and I updated my validation logic to treat null as valid for those token types."

### Q: "你怎么发现这个变更的？"

**A**:
> "I check their changelog at docs.coingecko.com/changelog periodically. They announced this change in advance, which is good API practice. I tested my pipeline with data from before and after the change date to verify it handled the schema evolution correctly."

### Q: "为什么不用 Kafka？"

**A**:
> "This is a learning project focused on Structured Streaming and Delta Lake concepts. I chose to pull data to S3 first, then use Auto Loader for incremental ingestion. This simulates a common production pattern where data lands in object storage before processing. It also avoids API rate limits and gives me full control for testing. The streaming concepts — watermarking, stateful operations, checkpointing — are the same whether the source is Kafka or S3."

---

## 可验证的细节（面试时可以说）

✅ **API URL**: `https://api.coingecko.com/api/v3/coins/markets`
✅ **字段数量**: 26 个字段
✅ **真实字段名**: `current_price`, `market_cap`, `total_volume`, `high_24h`, `low_24h`, `circulating_supply`, `ath`, `atl`, etc.
✅ **真实变更**: 2026-02-04 的 rehypothecated tokens 变更
✅ **变更内容**: `market_cap_rank` → `null`，新增 `market_cap_rank_with_rehypothecated`
✅ **文档**: https://docs.coingecko.com/changelog

---

## 注意事项

1. **不要说你处理了"数十亿条记录"** — 这个规模不现实
2. **不要说你用了 Kafka** — 避开这个盲区
3. **承认这是学习项目** — 诚实但不影响技术深度
4. **强调学到的概念** — Watermarking, Schema Evolution, Delta Lake, Medallion Architecture

---

Sources:
- [CoinGecko API Changelog](https://docs.coingecko.com/changelog)
