# 面试执行力改进计划 (2026-02-27)

## 背景
2026-02-27 两场面试均表现不佳：
- Springer Nature (MLOps Engineer): Python 基础题答不上来，且没有建 prep dossier
- 第二场: Behavioral questions 环节直接挂

**2026-03-05 更新**: FareHarbor ML Engineer 第二轮 live coding 再次失败
- 问题: K-Nearest Neighbors 从零实现
- 失败原因: 无法实现**最基础的算法** (距离计算 + 排序 + 取 top-k)
- **关键洞察**: 这是连续第二次在 trivial 问题上失败，不是偶然

系统在"拿到面试"环节已成熟，瓶颈在**面试执行层** — 具体是 **Python 基础编码能力**。

## 漏斗诊断
```
申请 ──── 拿到面试 ──── 通过面试 ──── Offer
 [强]       [还行]       [薄弱]      [未知]
```

## 面试三层博弈模型
1. **能力验证** (Can you do the job?) — 技术面、coding、system design
2. **行为信号** (Will you thrive here?) — Behavioral、culture fit、STAR 故事
3. **隐性评估** (Do I want to work with you?) — 沟通风格、不确定性下的反应、提问质量

## 优先事项

### P0: 技术基础肌肉记忆 ⚠️ CRITICAL
**状态 (2026-03-05)**: 两次 live coding 失败证明这是 BLOCKING ISSUE

- **每天 30 分钟，零 AI 辅助，手写代码** — 不是可选，是必须
- **重点 1: 基础算法实现** (KNN, binary search, two pointers, sorting, grouping)
- **重点 2: Python 数据结构操作** (list/dict/set manipulation, comprehensions, sorting with key)
- **重点 3: 数学计算** (Euclidean distance, Manhattan distance, dot product)
- 次要: decorators, generators, GIL, metaclass, `__slots__`, MRO, context managers
- 目标: 任何基础算法 5 分钟内写出 bug-free 实现
- **不是 LeetCode hard 题，是 easy/medium 的基础题** — 但要能在压力下流畅写出
- 扩展: 根据目标职位补充 Docker/K8s/SQL/System Design

**行动**: 创建 `docs/python_fundamentals_drill.md` 包含每日练习题库

### P1: 面试故事库 (Behavioral 弹药库)
- 从 bullet_library.yaml 的 50 条经历扩展为 8-10 个完整 STAR 故事
- 每个故事 2-3 分钟叙事弧，含情感锚点和量化结果
- 每个故事能覆盖 3-4 种 behavioral 问题类型
- 必须覆盖: 技术挑战 / 失败 / 冲突 / 领导力 / 跨团队协作 / 紧急情况 / 创新 / 学习
- **写在纸上 ≠ 说得出来**，需要反复口头练习

### P2: 模拟面试练习
- 对着录音练习 behavioral 回答，回听改进
- 练习重点不是"内容"而是"delivery"——语速、停顿、自信
- 技术面: 白板/口述解题练习，习惯边想边说

### P3: Post-interview 反馈循环
- 每次面试后立即写 09_post_interview_notes.md
- 记录: 问了什么、怎么答的、面试官反应、哪里卡壳
- **当前状态 (2026-03-05)**: 11 个 prep 文件夹，1 个复盘文件 (20260305_FareHarbor) — 反馈循环刚开始建立
- **模式识别**: 有了第一个复盘后，清晰看到连续失败的 pattern (两次 trivial 问题失败)

### P4: Prep 系统补充
- 每轮面试的技术刷题清单 (根据 JD 技术栈定制)
- 面试前 24 小时 checklist (不是 dossier，是上场前最后检查)
- Behavioral 故事 → 具体公司的映射表

## 系统层面待改进
- Springer Nature 没建 prep dossier — 每个进入 interview 状态的公司必须有 dossier
- 面试故事库需要新文件: `assets/interview_stories.yaml` 或类似
- Prep workflow 增加"技术刷题清单"和"behavioral 映射"两个输出
