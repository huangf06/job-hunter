# Spark 深入浅出 — 面试复习笔记

> 2026-03-03 复习 session，逐概念深入讲解

---

## 0. Spark 到底是什么？

### 一句话
Spark 是一个**分布式计算引擎** — 把大到单机算不动的任务，拆成小任务分配给一群机器同时算。

### 为什么需要 Spark？
- 单机方案：1TB CSV → pandas 读不进 32GB 内存，单核跑 3 小时
- Spark 方案：1TB 拆成 1000 份，分给 100 台机器，每台处理 10GB，10 分钟搞定
- **当数据大到一台机器搞不定时，你需要 Spark**

### 核心特性：Lazy Evaluation（惰性求值）

类比餐厅点菜：
- `filter`, `groupBy` 等 = 服务员记菜单（不执行）
- `.show()`, `.count()` 等 = "上菜吧"（触发执行）

好处：Spark 看到完整计划后可以做全局优化（Catalyst 优化器）

### 两种操作
| 类型 | 何时执行 | 例子 |
|------|---------|------|
| **Transformation** | 不执行，只记录 | `filter`, `select`, `groupBy`, `join`, `withColumn` |
| **Action** | 触发整个流水线 | `show()`, `count()`, `collect()`, `write()` |

### 架构：Driver + Executor
- **Driver（老板）**：解析代码 → 构建执行计划 → 分配任务 → 追踪进度
- **Executor（工人）**：实际干活，每个跑在一台机器/容器上
- **Task**：最小工作单元，一个 Task 处理一个 Partition

### Partition（分区）
- 大数据集切成多个 Partition，每个独立处理
- 一个 Partition = 一个 Task = 一个 CPU 核心
- 经验法则：每个 Partition 128MB - 1GB

### Stage 和 Shuffle
- **Narrow transformation**（不搬家）：`filter`, `select`, `map` — 数据留在原 Partition
- **Wide transformation**（Shuffle = 搬家）：`groupBy`, `join`, `distinct` — 相同 key 的数据必须聚到同一个 Partition
- **Shuffle 三大开销**：磁盘 I/O、网络传输、序列化/反序列化
- **Spark 调优的核心 = 减少 Shuffle**

### DataFrame vs SQL
两种写法生成完全相同的执行计划（都经过 Catalyst），性能一样，选哪种是个人偏好。

---

## 1. Catalyst 优化器执行流程

（下一节继续）
