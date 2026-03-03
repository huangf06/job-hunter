# 🎯 Swisscom 面试速查卡 (打印/第二屏幕)

**面试时间**: 2026-03-04 10:00 CET | MS Teams | 1小时
**面试官**: Yannis Klonatos (EPFL PhD), Mani Bastaniparizi

---

## 📊 关键数字 (必须记住)

```
Financial Lakehouse:
• 26 字段 (CoinGecko API)
• 2026-02-04 (schema 变更)
• Top 100 coins
• 每 5 分钟拉取
• ~29,000 records/day
• 30 秒 trigger interval
• 10 分钟 watermark
• 85% ↓ files scanned
• 6.7x faster queries
• <0.1% quarantine rate

个人:
• 6 years 经验
• 8.2 GPA (VU Amsterdam)
• 3,000+ securities (Baiquan)
• Databricks Professional (2026-01)
```

---

## 🎤 自我介绍 (2分钟)

> Hi, I'm Fei. I'm a data engineer with about **6 years** of experience, currently based in Amsterdam.
>
> I recently completed my Master's in AI at VU Amsterdam with a GPA of **8.2**, and earned my **Databricks Data Engineer Professional** certification earlier this year.
>
> My career has spanned three data-intensive domains. At GLP, a consumer lending startup, I was the **founding data hire** — I built the entire data infrastructure from scratch. At Baiquan Investment, I engineered market data pipelines for **3,000-plus securities**. And most recently, I've been building a **real-time financial data lakehouse** on Databricks.
>
> What excites me about the Polaris team is the **scale** — transforming **billions of network events per day** into actionable insights is exactly the kind of challenge I thrive on.

---

## 🔥 5 个高风险技术点 (快速回答模板)

### 1. Checkpoint

**Q: What is checkpoint?**
> Checkpoint is Spark Structured Streaming's mechanism for exactly-once semantics and fault tolerance. It stores offsets, commits, and state to S3.

**目录结构**:
```
checkpoints/
├── offsets/    # 每个 batch 的数据范围
├── commits/    # batch 完成标记
├── state/      # stateful operations 状态
└── metadata    # stream 元数据
```

**恢复流程**: 读取最后一个 commit → 从 offsets 恢复 → 重新处理未 commit 的 batch

---

### 2. Watermarking

**Q: Explain watermarking**
> Watermarking tells Spark when to stop waiting for late data in event-time windows.

**公式**:
```
Watermark = max(event_time) - threshold
Global Watermark = min(所有 partition 的 watermark)
```

**我的决策**: 10 分钟 watermark，基于 99th percentile 延迟 ~8 分钟

**Trade-off**:
- 更大 (30min) → 更完整但延迟高
- 更小 (1min) → 丢弃 15-20% 延迟数据

---

### 3. Z-ordering vs Liquid Clustering

**Q: Why Z-ordering instead of Liquid Clustering?**
> Great question. Liquid Clustering is newer and generally recommended now. I chose Z-ordering because:
> 1. **Learning project** — wanted to understand fundamentals manually
> 2. **Community resources** — most tutorials in 2025 still used Z-ordering
> 3. **For production**, I'd use Liquid Clustering — it's automated and handles incremental updates better

**关键区别**:
| 特性 | Z-ordering | Liquid Clustering |
|------|-----------|------------------|
| 引入 | 2019 | 2023 (GA) |
| 自动优化 | ❌ 手动 | ✅ 自动 |
| 与 Partitioning | ✅ 可共存 | ❌ 互斥 |

---

### 4. Quarantine-and-Replay

**Q: How do you handle bad data?**
> I use a Quarantine-and-Replay pattern:

```
Bronze (raw JSON)
  ↓ schema validation
  ├─ Pass → Silver
  └─ Fail → Quarantine 表
             ↓ 修复后
             Replay → Silver
```

**为什么不在入口拒绝？**
- 数据永久丢失，无法 replay
- Bronze 存储便宜，数据丢失成本高
- Quarantine 提供可观测性

**幂等性**: 使用 `merge` 而非 `append`，基于 `(id, timestamp)` 去重

---

### 5. Medallion Architecture

**Q: Explain your Medallion Architecture**

| 层 | 格式 | Schema | 用途 |
|----|------|--------|------|
| Bronze | JSON | Schema-on-read | 保真、审计、replay |
| Silver | Parquet | Enforced | 分析基础 |
| Gold | Parquet | 业务视图 | 直接服务查询 |

**核心原则**: 永不丢弃数据。Bronze 收一切，Silver 清洗，Gold 聚合。

---

## 🎯 行为问题 STAR 故事

### 1. 最有挑战的技术问题

**Schema Evolution (2026-02-04)**
- **S**: CoinGecko API 突然增加字段，Silver 层 schema 校验失败
- **T**: 需要在不丢数据的前提下更新 pipeline
- **A**: 使用 Delta Lake 的 `mergeSchema` 选项，先写入 Bronze，再更新 Silver schema
- **R**: 零数据丢失，30 分钟内恢复 pipeline

---

### 2. 与团队合作

**GLP 信贷评分系统**
- **S**: 风控团队需要信贷评分模型，但不懂技术细节
- **T**: 需要将技术语言翻译成业务语言
- **A**: 创建可视化仪表板，展示评分分布和特征重要性；定期与风控团队开会，解释模型逻辑
- **R**: 评分系统上线后，坏账率降低 15%

---

### 3. 处理紧急问题

**Baiquan 市场数据延迟**
- **S**: 交易时段数据中断，影响交易决策
- **T**: 15 分钟内恢复数据流
- **A**: 快速定位问题 (上游 API 限流)，实施临时方案 (切换备用数据源)
- **R**: 15 分钟内恢复，避免交易损失

---

### 4. 学习新技术

**从零学习 Databricks**
- **S**: 需要构建 lakehouse，但没有 Databricks 经验
- **T**: 3 个月内掌握 Databricks 和 Delta Lake
- **A**: 系统性学习方法 (官方文档 → 认证考试 → 实战项目)
- **R**: 3 个月内获得 Professional 认证，构建完整 lakehouse

---

### 5. 为什么对这个职位感兴趣

**关键点**:
- **Scale**: billions of events per day — 我喜欢大规模数据挑战
- **Impact**: 直接影响 Swisscom 网络策略 — 我想做有影响力的工作
- **Team**: 与 EPFL PhD 合作 — 我想学习分布式系统
- **Location**: 已在荷兰 — 无需 relocation，可以立即开始

---

## ❓ 提问环节 (必须问的 3 个问题)

### 1. 技术深度问题
> "You mentioned the team processes billions of network events per day. I'm curious about the data pipeline architecture — are you using a Lambda architecture, Kappa architecture, or something custom? And how do you handle late-arriving events?"

### 2. 团队协作问题
> "I noticed the team is relatively small — 4 people handling such a large-scale system. How do you balance feature development with operational maintenance? And what does on-call look like?"

### 3. 成长机会问题
> "What are the biggest technical challenges the team is facing in the next 6-12 months? And what would success look like for someone joining in this role?"

---

## 🚨 如果遇到不会的问题

**策略 1: 第一性原理推理**
> "I haven't worked with that specific technology, but based on my understanding of [related concept], I would approach it like this..."

**策略 2: 诚实 + 学习能力**
> "That's a great question. I haven't encountered that exact scenario, but here's how I would think through it... [推理过程]. How does your team handle this?"

**策略 3: 反问**
> "That's an interesting problem. Could you share how the Polaris team currently approaches this? I'd love to learn from your experience."

---

## ✅ 面试中的 5 个关键原则

1. **先给概述，再分层展开** — 让面试官知道你理解问题
2. **主动提供例子** — 代码片段、数字、图表
3. **观察面试官反应** — 如果他点头，继续；如果他皱眉，停下来问
4. **展现学习能力** — 强调你如何从零学习 Databricks
5. **保持热情和好奇心** — 这是你的优势

---

## 💪 最后的信心加持

**你的优势**:
✅ 6 年经验 (超过 JD 要求的 4+)
✅ Databricks 认证 (证明技术深度)
✅ 完整项目经验 (覆盖所有技术栈)
✅ 学习能力强 (3 个月从零到认证)
✅ 已在荷兰 (无需 relocation)

**你已经准备好了。相信自己，展现实力！**

---

**Good luck! 💪**
