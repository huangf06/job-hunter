# 简历模板回滚设计 (2026-04-17)

## 背景

2026-04-01 ~ 04-02 期间，简历管道进行了一次结构性升级：
- 引入 zone-based 单页绝对定位模板 (`base_template_DE.html` / `base_template_ML.html`)
- 切换到 per-line bio 架构 (`bio_1 / bio_2 / bio_3`)
- 收缩到 1 页硬压缩
- 技能类别从 6 → 4
- Experience bullets **硬编码在 HTML 里**，AI 只能替换技能标签、bio、少量插槽

效果：
- 升级前 (2026-01 ~ 03)：~400 次投递 → ~14 次面试邀请 (~3.5%)
- 升级后 (2026-04-02 ~ 04-17)：77 次投递 → **0 次面试邀请** (100% 拒信，Aon 不算)

定量对比 (见 `/tmp/resume_compare/count.py`)：

| 维度 | PRE (面试版) | POST (当前) | 差值 |
|------|-------------|-------------|------|
| 词数 | ~550 | ~420 | −23% |
| Bullets | 15 | 9 | −40% |
| 独立技术词 | 31 | 22 | **−29%** |
| 技能类别 | 6 | 4 | −33% |
| 数字/量化 | 12 | 20 | +68% |
| 强动词 | 7 | 13 | +86% |

POST 在"单条 bullet 密度"上更强，但在 **关键词表面积、阅读节奏、可信度堆叠** 上显著退化。6 秒招聘官扫描 + ATS 关键词匹配两关都吃亏。

## 用户核心判断

> "新简历严格遵守诚实原则，从而使 bullet 的力度下降。整体可信性下降。"
> "是不是最好降级简历的模板，回滚到原有两页自由模式？"

结论：**回滚，不是打补丁**。

---

## Section A — 核心决策

### A.1 模板层：回滚到 2 页 Jinja2 flow-layout 基座

**动作：**
1. 从 commit `67724e8` 取出 `templates/base_template.html`，作为新的单一基座
2. 保留 DE/ML/DS 三档路由逻辑 (ai_score_tier, template_id_initial/final)，但三档共享**同一个** flow-layout 基座
3. 归档 zone-based 单页模板：
   - `templates/base_template_DE.html` → `templates/archive/2026-04-02-zone-DE.html`
   - `templates/base_template_ML.html` → `templates/archive/2026-04-02-zone-ML.html`
   - `templates/base_template_DS.html` → `templates/archive/2026-04-07-zone-DS.html`

**基座的关键特性 (取自 67724e8)：**
- `@page { size: A4; margin: 0.55in; }` + `break-inside: avoid`，自然多页流式排版
- `{% for exp in experiences %}` + `{% for bullet in exp.bullets %}`，**bullets 完全 per-job 可变**
- 6 个技能类别 (Languages & Core / Data Engineering / Cloud & DevOps / Databases / ML/AI Frameworks / Research Methods)
- Additional section：Languages、Interests、Blog
- 语义化 `<ul><li>` 标记，ATS 可读

**不回滚的部分：**
- `resume_renderer.py` 里的 three-tier routing、Turso 同步、简历验证器 → 保留
- `cover_letter_*` 整条链路 → 保留
- AI 分析器 (`ai_analyzer.py`) 打分逻辑 → 保留

### A.2 内容层：把 POST 期间挖出来的强素材回填到 bullet library

POST 期间 AI 分析 + 面试准备过程积累了一批**强但被单页压缩埋没**的 bullet，必须保留。

**待迁移素材 (进入 `assets/bullet_library.yaml`)：**

- **BQ Investment (交易/量化)**
  - 14.6% 年化真实资本收益 (CSI 指数期货日内策略)
  - 4 个因子家族跨 3,000+ 标的的横截面回归验证流水线

- **GLP Technology (信贷/ML)**
  - 19 个 feature engineered，36-segment 借款人评分卡
  - First-payment default scorecard 进生产承保
  - 30+ 生产表 + 征信局数据自动化入湖

- **Ele.me (异常检测)**
  - 51,000+ 可疑订单簇识别，覆盖 2.2M+ 用户
  - 同号、高频、重复下单 3 种模式匹配算法

- **Financial Data Lakehouse (Databricks 项目)**
  - Medallion + quarantine-and-replay + Z-ordering 压缩
  - Auto Loader + Structured Streaming 零数据丢失
  - Airflow + Docker 编排

- **论文 (UQ Benchmark)**
  - 150+ HPC SLURM runs，QR-DQN 31% 更低 CRPS (p < 0.001)
  - Noise paradox 发现
  - 6-stage calibration pipeline

- **Expedia LambdaRank**
  - 4.96M 搜索记录，50+ 时序/行为/价格归一化特征
  - NDCG@5 = 0.392

- **IMU ML4QS**
  - 4 subjects × 6 activities，Kalman 滤波 12 通道
  - 576 FFT 特征，LightGBM + BiLSTM，94-99% 准确率

迁移策略：按 `(role, context_tag, strength)` 结构化，每条带 `domain_tags: [de, ml, ds, quant]` 以便 AI 按岗位类型选择。

### A.3 AI 层：重新接 per-job bullet selection

**当前问题：** `ai_analyzer.py` 产出的 `tailored_resume.slot_overrides` 针对 zone 模板设计，不能直接填 flow-layout 的 `experiences[].bullets`。

**要求：**
- AI 输出结构改回 (或新增兼容模式) `experiences: [{company, title, date, location, bullets: [str, ...], technical_skills: str}]`
- 从 bullet library 按 JD 选择 3-5 bullets/role，不是一次性全塞
- 保留 `skills` 列表的 6 类别结构 (AI 按 JD 重排顺序 + 补充)
- 保留 `bio` 作为**单个完整段落** (不再是 3 行)，可按 role tier 调整 (DE/ML/DS)

### A.4 验收

- 生成 3 份样本简历 (DE/ML/DS 各一) 与 `interview_prep/20260316_ENPICOM_Senior_SWE/03_submitted_resume.md` 等面试版对比
- 视觉回归：2 页，流式排版，无 hard line break
- ATS 关键词：unique techs ≥ 28，skill categories = 6

---

## Section B — 风险与回退

### B.1 渲染器 API 不兼容

`67724e8` 时代的 `resume_renderer.py` 期望 `experiences[].bullets` 是 `list[str]`，当前代码可能已被改成其他结构 (slot_overrides, entry_visibility 等)。

**检查点：**
- `src/resume_renderer.py` 的 `_render_resume` 签名
- AI 输出的 `tailored_resume` JSON schema
- `src/resume_validator.py` 的校验逻辑

**回退方案：**
- 如果渲染器改动太大，`git checkout 67724e8 -- src/resume_renderer.py templates/base_template.html`
- 然后逐个把后续修复 cherry-pick 回来 (中文检测、渠道路由、Turso 同步等)

### B.2 Bullet library 与新 AI 流的对接

Bullet library v4.0 (2026-03-10) 的叙事架构可能已经是"段落级"而非"bullet 级"。如果结构不兼容，需要：
- 保留 v4.0 作为 `narrative_library.yaml`
- 新增 `bullet_library_v5.yaml` 专门服务 flow-layout 模板，格式对齐 67724e8 时代

### B.3 回滚后仍然 0 面试

如果 2 周观察 (4-17 ~ 5-01) 仍然 0 面试邀请，不是模板问题，是**供给侧**问题：
- 目标池子污染 (不合适的 JD 被 AI 评高分)
- 简历与 JD 匹配度结构性不足 (非荷兰语劣势 / 工作许可 / 资历预期)
- 市场大盘差

→ 触发 Section C 的供给侧干预升级。

### B.4 诚实原则的边界

用户原话："严格遵守诚实原则，从而使 bullet 的力度下降"。

**这不是要求放弃诚实，是要求区分：**
- **不能做**：编造数字、编造职责、编造公司
- **应该做**：用最强的合法真相 framing
  - "Spearheaded credit scoring infrastructure as first data hire" > "Contributed to credit scoring work"
  - "14.6% annualized return with real capital" > "Developed a trading model"
  - "Benchmarking framework evaluating 5 UQ methods across 150+ training runs on HPC (SLURM)" > "Ran some UQ experiments"

Kant 允许的 rhetoric 空间在这里必须用满。POST 简历的问题是把"诚实"执行成了"淡化"，这是自我惩罚，不是道德义务。

---

## Section C — 并行供给侧干预

模板回滚是**必要但不充分**。同步做：

### C.1 立即暂停 `--prepare` 自动流水线

- 本周不再自动生成投递材料
- 存量 `ready_to_send/` 清空或归档
- AI 评分仍然跑，但只做**候选池可视化**，不自动进入投递

### C.2 手工精选 5-8 个高置信度目标

范围锁定在用户真实优势 + 有面试历史的领域：
- **Fintech / Quant**：对口 GLP、BQ 经历，14.6% 收益真实可验证
- **MLOps / ML Platform**：对口 Databricks Professional + Financial Data Lakehouse
- **Senior Data Engineer (regulated-like)**：对口 first data hire 叙事

每个目标投递前：
- 读 JD 原文 (careers page，不是 LinkedIn 版本)
- 手工 review AI 选的 bullets
- 必要时个人化 CL 前 2 句 (ENPICOM Jorrit 反馈：we prefer personally written applications)

### C.3 观察指标

2 周后 (5-01) 评估：
- 5-8 次精选投递是否带来 ≥ 1 次面试邀请
- 如果是 → 验证"模板回滚 + 精选投递"组合有效，恢复 `--prepare` 但**只针对符合 C.2 三类范围**的职位
- 如果否 → 问题在简历层之外 (市场 / 资历 / 工作许可)，需要重新评估求职策略 (memory: `project_job_search_strategy_2026_04.md`)

---

## 下一步

进入 `superpowers:writing-plans`，把 A.1-A.4 拆成可执行的实施计划：
1. 归档 zone 模板 + 提取 67724e8 基座
2. 迁移 bullet library (POST 期间强素材)
3. `resume_renderer.py` / `ai_analyzer.py` schema 对接
4. 3 份样本简历视觉 + ATS 验收
5. 小范围试投 (C.2 精选目标)
