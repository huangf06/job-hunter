# 面试执行力改进计划 (2026-02-27)

## 背景
2026-02-27 两场面试均表现不佳：
- Springer Nature (MLOps Engineer): Python 基础题答不上来，且没有建 prep dossier
- 第二场: Behavioral questions 环节直接挂

系统在"拿到面试"环节已成熟，瓶颈在**面试执行层**。

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

### P0: 技术基础肌肉记忆
- 每天 30 分钟，零 AI 辅助，手写 Python 核心概念
- 重点: decorators, generators, GIL, metaclass, `__slots__`, MRO, context managers
- 目标: 任何 Python 基础概念 10 秒内流利回答
- 不是 LeetCode 算法，是**语言机制本身**
- 扩展: 根据目标职位补充 Docker/K8s/SQL/System Design

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
- 当前状态: 7 个 prep 文件夹，0 个复盘文件 — 无反馈循环

### P4: Prep 系统补充
- 每轮面试的技术刷题清单 (根据 JD 技术栈定制)
- 面试前 24 小时 checklist (不是 dossier，是上场前最后检查)
- Behavioral 故事 → 具体公司的映射表

## 系统层面待改进
- Springer Nature 没建 prep dossier — 每个进入 interview 状态的公司必须有 dossier
- 面试故事库需要新文件: `assets/interview_stories.yaml` 或类似
- Prep workflow 增加"技术刷题清单"和"behavioral 映射"两个输出
