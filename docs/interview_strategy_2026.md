# 面试执行力改进战略规划 (2026-02-27)

## 背景

**当前漏斗瓶颈**：
- 申请 → 面试: 8.8% (239 → 21)
- 面试 → Offer: 9.5% (21 → 2) ⚠️⚠️⚠️

**根本问题**：系统在"拿到面试"环节已成熟，瓶颈在**面试执行层**。

**2026-02-27 两场面试均表现不佳**：
- Springer Nature (MLOps Engineer): Python 基础题答不上来，且没有建 prep dossier
- 第二场: Behavioral questions 环节直接挂

---

## 面试三层博弈模型

1. **能力验证** (Can you do the job?) — 技术面、coding、system design
2. **行为信号** (Will you thrive here?) — Behavioral、culture fit、STAR 故事
3. **隐性评估** (Do I want to work with you?) — 沟通风格、不确定性下的反应、提问质量

---

## 优先事项

### P0: 技术基础肌肉记忆

**目标**：任何 Python 基础概念 10 秒内流利回答

**执行计划**：
- 每天 30 分钟，零 AI 辅助，手写 Python 核心概念
- 重点: decorators, generators, GIL, metaclass, `__slots__`, MRO, context managers
- 不是 LeetCode 算法，是**语言机制本身**
- 扩展: 根据目标职位补充 Docker/K8s/SQL/System Design

**资源**：
- 创建 `docs/python_fundamentals_drill.md`（20 个核心概念 + 示例代码）
- 每周五自测（录音回答 10 个随机问题）

**成功指标**：
- 能够在 10 秒内流利解释任何 Python 核心概念
- 能够手写代码示例（不依赖 IDE 自动补全）

---

### P1: 面试故事库 (Behavioral 弹药库)

**目标**：8-10 个完整 STAR 故事，覆盖所有常见 behavioral 问题类型

**执行计划**：
- 从 bullet_library.yaml 的 50 条经历扩展为 8-10 个完整 STAR 故事
- 每个故事 2-3 分钟叙事弧，含情感锚点和量化结果
- 每个故事能覆盖 3-4 种 behavioral 问题类型
- 必须覆盖: 技术挑战 / 失败 / 冲突 / 领导力 / 跨团队协作 / 紧急情况 / 创新 / 学习
- **写在纸上 ≠ 说得出来**，需要反复口头练习

**资源**：
- 创建 `assets/interview_stories.yaml`
- 每个故事包含: situation, task, action, result, lessons_learned, applicable_questions

**成功指标**：
- 能够在 2-3 分钟内流利讲述任何一个故事
- 能够根据问题快速选择最相关的故事

---

### P2: 模拟面试练习

**目标**：提升 delivery（语速、停顿、自信），而非内容

**执行计划**：
- 对着录音练习 behavioral 回答，回听改进
- 练习重点不是"内容"而是"delivery"——语速、停顿、自信
- 技术面: 白板/口述解题练习，习惯边想边说

**资源**：
- 使用手机录音 app
- 每周至少 2 次模拟面试（1 次 behavioral, 1 次 technical）

**成功指标**：
- 录音回听时，自己听起来自信、流利、有条理
- 能够在压力下保持冷静、清晰的表达

---

### P3: Post-interview 反馈循环

**目标**：每次面试后立即复盘，建立反馈循环

**执行计划**：
- 每次面试后立即写 `09_post_interview_notes.md`
- 记录: 问了什么、怎么答的、面试官反应、哪里卡壳
- 当前状态: 7 个 prep 文件夹，0 个复盘文件 — 无反馈循环

**资源**：
- 模板: `interview_prep/YYYYMMDD_Company_Role/09_post_interview_notes.md`
- 包含: questions_asked, my_answers, interviewer_reactions, what_went_well, what_went_wrong, action_items

**成功指标**：
- 每次面试后 24 小时内完成复盘
- 能够识别重复出现的问题（如某类问题总是答不好）

---

### P4: Prep 系统补充

**目标**：每轮面试的技术刷题清单 + behavioral 映射

**执行计划**：
- 每轮面试的技术刷题清单 (根据 JD 技术栈定制)
- 面试前 24 小时 checklist (不是 dossier，是上场前最后检查)
- Behavioral 故事 → 具体公司的映射表

**资源**：
- 在 prep workflow 中增加"技术刷题清单"和"behavioral 映射"两个输出
- 模板: `interview_prep/YYYYMMDD_Company_Role/08_technical_drill_list.md`

**成功指标**：
- 每个进入 interview 状态的公司必须有 prep dossier
- 面试前 24 小时完成最后检查

---

## 系统层面待改进

1. **Springer Nature 没建 prep dossier** — 每个进入 interview 状态的公司必须有 dossier
2. **面试故事库需要新文件**: `assets/interview_stories.yaml` 或类似
3. **Prep workflow 增加"技术刷题清单"和"behavioral 映射"两个输出**

---

## 预期效果

**如果严格执行 P0-P4**：
- 面试 → Offer 转化率从 9.5% 提升到 20-30%（行业平均）
- 技术面试不再因为基础概念卡壳
- Behavioral 面试能够流利讲述相关故事
- 每次面试后有清晰的改进方向

---

## 执行时间表

| 优先级 | 项目 | 时间投入 | 开始时间 |
|--------|------|----------|----------|
| P0 | 技术基础训练 | 每天 30 分钟 | 立即 |
| P1 | STAR 故事库 | 8-10 小时（一次性） | 本周内 |
| P2 | 模拟面试 | 每周 2 次，每次 1 小时 | 下周开始 |
| P3 | Post-interview 复盘 | 每次面试后 30 分钟 | 立即 |
| P4 | Prep 系统补充 | 2-3 小时（一次性） | 本周内 |

---

## 关键成功因素

1. **持续执行**：P0 技术基础训练需要每天坚持，不能间断
2. **反馈循环**：P3 post-interview 复盘是改进的关键
3. **刻意练习**：P2 模拟面试需要录音回听，不能只是"过一遍"
4. **系统化**：P1 故事库需要结构化存储，不能只是"脑子里有"

---

## 附录：常见 Behavioral 问题类型

1. **技术挑战**: "Tell me about a time you solved a difficult technical problem"
2. **失败**: "Tell me about a time you failed"
3. **冲突**: "Tell me about a time you had a conflict with a teammate"
4. **领导力**: "Tell me about a time you led a project"
5. **跨团队协作**: "Tell me about a time you worked with cross-functional teams"
6. **紧急情况**: "Tell me about a time you had to work under pressure"
7. **创新**: "Tell me about a time you came up with a creative solution"
8. **学习**: "Tell me about a time you learned a new technology quickly"

每个故事应该能覆盖 3-4 种问题类型。
