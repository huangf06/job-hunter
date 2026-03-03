# Swisscom 面试最后 22 小时冲刺清单

**当前时间**: 2026-03-03 11:36 CET
**面试时间**: 2026-03-04 10:00 CET
**剩余时间**: 22 小时 24 分钟

---

## 📋 今天下午 (12:00-18:00) — 6小时深度学习

### ✅ 第一轮：通读核心材料 (2小时)

**必读文件（按顺序）**:
1. `08_complete_study_guide.md` (37K) — 完整备考手册，包含所有技术点的 4 层深度
2. `12_technical_deep_dive.md` (22K) — 基于真实 CoinGecko API 的技术细节
3. `10_core_concepts_cheatsheet.md` (4K) — 核心概念速查表

**阅读方法**:
- 不要死记硬背，理解每个技术点的**机制**和**为什么**
- 标记你不确定的部分，稍后重点复习
- 大声朗读关键段落，帮助记忆

---

### ✅ 第二轮：技术点深度演练 (2小时)

**重点攻克 5 个高风险技术点**:

#### 1. Checkpoint 机制 (30分钟)
- [ ] 能画出 checkpoint 目录结构
- [ ] 能解释 offsets/ commits/ state/ 的作用
- [ ] 能回答 "如果 checkpoint 损坏怎么办？"
- [ ] 记住关键代码: `.option("checkpointLocation", "s3://...")`

**练习**: 闭上眼睛，口述 checkpoint 恢复流程

#### 2. Watermarking (30分钟)
- [ ] 能解释 event-time vs processing-time
- [ ] 能画出 watermark 计算公式: `max(event_time) - threshold`
- [ ] 能解释为什么全局 watermark = min(所有 partition)
- [ ] 记住你的决策: 10分钟 watermark，基于 99th percentile 延迟

**练习**: 用白纸画出 watermark 推进过程

#### 3. Z-ordering vs Liquid Clustering (30分钟)
- [ ] 记住对比表格 (引入时间、自动优化、与 partitioning 的关系)
- [ ] 能解释为什么选 Z-ordering (学习项目、手动控制、社区资源)
- [ ] 能回答 "如何迁移到 Liquid Clustering？"
- [ ] 记住关键限制: Liquid Clustering 不能与 partitioning 同时使用

**练习**: 大声朗读 `12_technical_deep_dive.md` 第 538-609 行的回答脚本

#### 4. Quarantine-and-Replay (20分钟)
- [ ] 能画出数据流: Bronze → validation → Silver/Quarantine → Replay
- [ ] 能解释为什么不在入口就拒绝坏数据
- [ ] 记住 quarantine 表结构: raw_data, error_reason, timestamp, source_file
- [ ] 能回答 "如何保证 replay 的幂等性？"

**练习**: 在纸上写出 quarantine 表的 CREATE TABLE 语句

#### 5. Medallion Architecture (10分钟)
- [ ] 记住三层的职责表格 (存储格式、schema、数据质量、用途)
- [ ] 能解释为什么 Bronze 用 JSON、Silver/Gold 用 Parquet
- [ ] 能回答 "为什么不直接从 Bronze 到 Gold？"

**练习**: 用一句话总结每一层的核心价值

---

### ✅ 第三轮：关键数字记忆 (30分钟)

**必须记住的数字** (写在便签纸上，贴在显示器旁边):

```
Financial Lakehouse 项目:
- 26 个字段 (CoinGecko API)
- 2026-02-04 (schema 变更日期)
- Top 100 coins
- 每 5 分钟拉取
- ~29,000 records/day
- 30 秒 trigger interval
- 10 分钟 watermark
- 85% reduction in files scanned (Z-ordering 效果)
- 6.7x faster queries (Z-ordering 效果)
- <0.1% quarantine rate (正常情况)

个人背景:
- 6 years 经验
- 8.2 GPA (VU Amsterdam)
- 3,000+ securities (Baiquan)
- Databricks Data Engineer Professional (2026-01)

Swisscom Polaris:
- Billions of network events per day
- 4 人团队 (Yannis, Mani, Deepthi, Monica)
- EPFL PhD (Yannis Klonatos)
```

---

### ✅ 第四轮：面试官调研 (1小时)

**重点人物: Yannis Klonatos**

阅读文件: `05_interview_strategy.md` 第 "面试官画像" 部分

**必须知道的信息**:
- [ ] EPFL PhD，研究方向: 分布式查询优化
- [ ] 可能关注: 性能优化、查询计划、分布式系统设计
- [ ] 沟通风格: 学术背景 → 喜欢深度技术讨论，追问 "为什么"

**准备策略**:
- 如果他问 "为什么选这个方案？" → 回答时提到 trade-off 和替代方案
- 如果他问性能问题 → 准备好具体数字 (85% reduction, 6.7x faster)
- 如果他问分布式问题 → 提到 Spark 的 partition 策略、shuffle 优化

---

## 🌙 今晚 (18:00-23:00) — 5小时巩固与模拟

### ✅ 晚餐后：自我介绍演练 (30分钟)

**任务**: 大声朗读自我介绍 **10 遍**

文件: `08_complete_study_guide.md` 第 1-30 行

**要求**:
- 严格控制在 2 分钟内
- 录音，听自己的语速和停顿
- 注意关键数字的发音: "eight point two", "three thousand plus"
- 最后 3 遍要流畅到不需要看稿

---

### ✅ 核心技术点模拟问答 (2小时)

**方法**: 打开 `12_technical_deep_dive.md`，逐个技术点进行模拟问答

**模拟流程**:
1. 看到问题 (例如: "What is checkpoint?")
2. 闭上眼睛，大声回答 (不看答案)
3. 打开答案，对比你的回答
4. 如果漏掉关键点，重新回答一遍

**必须模拟的 10 个问题**:
1. What is checkpoint and where is it stored?
2. What happens if checkpoint is corrupted?
3. Explain watermarking in Structured Streaming
4. Why did you choose 10-minute watermark?
5. What is Z-ordering and how does it work?
6. Why Z-ordering instead of Liquid Clustering?
7. Explain your Quarantine-and-Replay pattern
8. Why not reject bad data at the entry point?
9. What is Medallion Architecture?
10. How do you handle schema evolution?

---

### ✅ 行为问题准备 (1小时)

**必须准备的 5 个 STAR 故事**:

#### 1. 最有挑战的技术问题
**文件**: `08_complete_study_guide.md` 第 "Behavioral Questions" 部分

**故事**: Schema Evolution (2026-02-04 CoinGecko API 变更)
- Situation: API 突然增加字段，Bronze 层正常但 Silver 层 schema 校验失败
- Task: 需要在不丢数据的前提下更新 pipeline
- Action: 使用 Delta Lake 的 mergeSchema 选项，先写入 Bronze，再更新 Silver schema
- Result: 零数据丢失，30 分钟内恢复 pipeline

#### 2. 与团队合作的经历
**故事**: GLP 信贷评分系统 (与风控团队合作)
- 重点: 如何将技术语言翻译成业务语言
- 结果: 评分系统上线后，坏账率降低 15%

#### 3. 处理紧急问题
**故事**: Baiquan 市场数据延迟 (交易时段数据中断)
- 重点: 快速定位问题 (上游 API 限流)，实施临时方案 (切换备用数据源)
- 结果: 15 分钟内恢复，避免交易损失

#### 4. 学习新技术
**故事**: 从零学习 Databricks 和 Delta Lake
- 重点: 系统性学习方法 (官方文档 → 认证考试 → 实战项目)
- 结果: 3 个月内获得 Professional 认证，构建完整 lakehouse

#### 5. 为什么对这个职位感兴趣
**关键点**:
- Scale: billions of events per day
- Impact: 直接影响 Swisscom 网络策略
- Team: 与 EPFL PhD 合作，学习分布式系统
- Location: 已在荷兰，无需 relocation

---

### ✅ 睡前复习 (30分钟)

**任务**: 快速浏览速查表

文件: `10_core_concepts_cheatsheet.md`

**方法**:
- 不要深度阅读，只看标题和关键词
- 在脑海中快速回忆每个技术点的核心机制
- 如果某个点完全想不起来，标记明天早上重点复习

---

## 🌅 明天早上 (07:00-09:30) — 2.5小时最后冲刺

### ✅ 07:00-07:30: 晨间唤醒

- [ ] 洗漱、早餐、咖啡
- [ ] 不要看手机，保持专注
- [ ] 简单运动 (10 分钟拉伸或散步)

---

### ✅ 07:30-08:30: 核心材料最后一遍

**快速通读** (不要深度学习，只是激活记忆):
1. `10_core_concepts_cheatsheet.md` (5 分钟)
2. `12_technical_deep_dive.md` 的面试回答脚本部分 (20 分钟)
3. 自我介绍 (大声朗读 3 遍，15 分钟)
4. 关键数字便签纸 (5 分钟)
5. 行为问题 STAR 故事 (15 分钟)

---

### ✅ 08:30-09:00: 环境准备

**技术检查**:
- [ ] 测试 MS Teams 音视频
- [ ] 关闭所有通知 (Slack, Email, 微信)
- [ ] 准备第二台设备 (手机) 作为备用
- [ ] 测试网络稳定性

**物理环境**:
- [ ] 清理桌面，只留必要物品
- [ ] 调整摄像头角度和光线
- [ ] 准备水杯
- [ ] 确保房间安静，告知家人/室友

**材料准备**:
- [ ] 打开 `12_technical_deep_dive.md` 在第二个显示器 (或打印出来)
- [ ] 关键数字便签纸贴在显示器旁边
- [ ] 准备白纸和笔 (用于画图)

---

### ✅ 09:00-09:30: 心理准备

**放松技巧**:
- [ ] 深呼吸 5 分钟 (4 秒吸气，7 秒憋气，8 秒呼气)
- [ ] 积极心理暗示: "我已经准备充分，我能自信回答每个问题"
- [ ] 回顾你的优势: 6 年经验、Databricks 认证、完整项目经验

**最后检查**:
- [ ] 再次大声朗读自我介绍 1 遍
- [ ] 快速浏览关键数字便签纸
- [ ] 09:25 登录 MS Teams，提前 5 分钟进入等待室

---

## 🎯 面试中 (10:00-11:00) — 实战策略

### 开场 (前 5 分钟)

**自我介绍** (2 分钟):
- 流畅、自信、控制时间
- 强调关键数字: 6 years, 8.2 GPA, 3000+ securities

**寒暄**:
- 如果面试官问 "How are you?" → "I'm doing great, thank you. I'm excited to learn more about the Polaris team."
- 不要过度寒暄，保持专业

---

### 技术问题 (30-40 分钟)

**回答策略**:
1. **先给 1 句话概述** (让面试官知道你理解问题)
2. **然后分层展开** (从 what → why → how → trade-off)
3. **主动提供具体例子** (代码片段、数字、图表)
4. **观察面试官反应** (如果他点头，继续；如果他皱眉，停下来问 "Should I go deeper?")

**如果遇到不会的问题**:
- ❌ 不要说 "I don't know" 就停下来
- ✅ 说 "I haven't worked with that specific technology, but based on my understanding of [related concept], I would approach it like this..."
- ✅ 或者说 "That's a great question. Let me think through it..." (然后用第一性原理推理)

**如果面试官打断你**:
- 不要慌张，这是好信号 (说明他感兴趣)
- 立即停下来，听他的问题
- 回答他的问题后，问 "Should I continue with the previous point, or would you like to explore this further?"

---

### 行为问题 (10-15 分钟)

**STAR 结构**:
- Situation (1 句话)
- Task (1 句话)
- Action (2-3 句话，重点)
- Result (1 句话，带数字)

**总时长控制在 2 分钟内**

---

### 提问环节 (最后 5-10 分钟)

**必须问的 3 个问题**:

1. **技术深度问题**:
   > "You mentioned the team processes billions of network events per day. I'm curious about the data pipeline architecture — are you using a Lambda architecture, Kappa architecture, or something custom? And how do you handle late-arriving events?"

2. **团队协作问题**:
   > "I noticed the team is relatively small — 4 people handling such a large-scale system. How do you balance feature development with operational maintenance? And what does on-call look like?"

3. **成长机会问题**:
   > "What are the biggest technical challenges the team is facing in the next 6-12 months? And what would success look like for someone joining in this role?"

**备用问题** (如果时间充裕):
- "How does the Polaris team collaborate with other teams at Swisscom?"
- "What does the onboarding process look like for new engineers?"

---

## 📊 面试后 (11:00-12:00) — 复盘与跟进

### ✅ 立即记录 (11:00-11:15)

**创建文件**: `09_post_interview_notes.md`

**记录内容**:
- 面试官问了哪些技术问题？
- 哪些问题回答得好？哪些回答得不好？
- 面试官的反应如何？(点头、追问、皱眉)
- 有哪些意外的问题？
- 团队/公司的新信息

---

### ✅ 发送 Thank-you Email (11:15-11:30)

**收件人**: Lilla Egyed (Talent Acquisition Specialist)

**邮件模板**:

```
Subject: Thank you — Big Data Engineer Interview

Hi Lilla,

Thank you for coordinating today's interview with the Polaris team. I really enjoyed the conversation with [面试官名字] and learning more about how the team is transforming billions of network events into actionable insights.

The discussion about [提到一个具体技术点，例如 "handling late-arriving events in the streaming pipeline"] was particularly interesting, and it reinforced my excitement about the scale and impact of the work.

I'm very interested in this opportunity and look forward to the next steps.

Best regards,
Fei Huang
```

**发送时间**: 面试后 2-4 小时内

---

## 🔥 关键成功因素

### ✅ 必须做到的 5 件事

1. **自我介绍流畅** — 这是第一印象，必须完美
2. **技术点有深度** — 至少 3 个技术点能回答到第 3-4 层
3. **主动提供例子** — 不要等面试官追问，主动给代码/数字/图表
4. **展现学习能力** — 强调你如何从零学习 Databricks 并获得认证
5. **提问有质量** — 问技术深度问题，展现你对系统设计的理解

---

### ❌ 必须避免的 5 个错误

1. **过度紧张** — 深呼吸，记住你已经准备充分
2. **回答过长** — 每个回答控制在 2-3 分钟，观察面试官反应
3. **说 "I don't know" 就停下来** — 用第一性原理推理
4. **忘记关键数字** — 便签纸贴在显示器旁边
5. **没有提问** — 至少问 2 个有深度的问题

---

## 📈 信心加持

### 你的优势

✅ **6 年数据工程经验** — 比 JD 要求的 4+ 年更多
✅ **Databricks 认证** — 证明你的技术深度
✅ **完整项目经验** — Financial Lakehouse 覆盖了 JD 的所有技术栈
✅ **学习能力强** — 从零到认证只用了 3 个月
✅ **已在荷兰** — 无需 relocation，可以立即开始

### 你已经准备好了

- 你有 **150KB** 的准备材料
- 你理解每个技术点的 **4 层深度**
- 你有 **真实项目经验** 支撑每个回答
- 你有 **具体数字** 证明你的影响力

**你不是在碰运气，你是在展示实力。**

---

## ✅ 最后的最后

**面试前 1 小时**:
- 不要再学习新东西
- 快速浏览速查表
- 深呼吸，放松
- 相信自己

**面试中**:
- 微笑，保持眼神交流
- 说话清晰，语速适中
- 如果卡壳，停顿 2 秒，重新组织语言
- 展现热情和好奇心

**面试后**:
- 不要过度分析
- 发送 thank-you email
- 继续准备其他面试
- 相信结果会是最好的安排

---

**Good luck! You've got this! 💪**
