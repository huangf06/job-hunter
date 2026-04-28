# Credibility Audit Prompt — 外国人如何取信于荷兰雇主

**用途**: 新会话中执行，对 bullet library 做全面可信度审计并产出具体改动
**前置工作**: v7.3 hook amplification 已完成（句式重构+序列重组），本 prompt 聚焦下一层问题：可信度

---

## Prompt

```
任务：Bullet Library 可信度审计 — 让荷兰 hiring manager 相信一个中国候选人的实力

## 背景

我是一个在荷兰求职的中国候选人（清华本科 + VU Amsterdam AI 硕士）。最近一个月投递的简历几乎全部在初筛阶段被静默淘汰。

我们刚完成了 bullet library v7.3 的 hook amplification（句式重构、序列重组、A-hook 前置）。文本层面的优化已经到位。但一个更深层的问题浮出水面：

**可信度（credibility）**。

荷兰 hiring manager 看到中国背景的候选人简历时，面临一个根本性的信任问题：

1. 中国公司不可验证 — 他们搜不到 GLP Technology，打不了电话给你的前上司，找不到 Glassdoor 评价
2. 中国职级不可对标 — "Senior Data Engineer" 在中国创业公司是什么含金量？他们不知道
3. 数字不可感知 — "2.2M users" 在中国外卖平台是多还是少？他们没有参照系
4. 4 年 career gap — "Independent Quantitative Researcher" 2019-2023，没有雇主、没有外部验证

面对这些不确定性，hiring manager 的默认行为是：选一个在 Booking/ING/Adyen 待过的本地候选人，因为那个人的背景他一眼就能验证。

我们的任务是：在不编造任何事实的前提下，最大化简历中的可信度信号，让 hiring manager 有足够的信任基础来给我一个面试机会。

## 分析框架：四层可信度模型

### 第 1 层：机构可信（Institutional Credibility）
"学历和认证是否来自我认可的机构？"
- 大学声誉（VU Amsterdam 本地可验证，Tsinghua Top 20 globally）
- 专业认证（Databricks Certified DE Professional）
- 竞赛排名（Kaggle top 5%）
- 学术成果（论文、GPA、课程成绩）

审计要求：检查这些信号在简历中的曝光是否充分。education section 的内容是否被 AI tailor 正确利用？Databricks 认证的定位是否足够突出？

### 第 2 层：公司可信（Company Credibility）
"这些公司是什么？我能信任他们的背书吗？"
- company_note 是否出现在所有中国公司旁边
- 公司标签是否让荷兰人能立刻归类（"consumer lending fintech" vs 只写 "GLP Technology"）
- Ele.me 的 Alibaba 连接是否被充分利用
- Henan Energy 的 Fortune 500 标签是否在需要时出现

当前状态：v7.3 已添加 company_notes（GLP: "consumer lending fintech", BQ: "quantitative hedge fund", Ele.me: "acquired by Alibaba", HE: "Fortune Global 500"）。审计这些标签在渲染后的 PDF 上是否正确出现，以及 AI tailor 是否在所有生成的简历中都正确设置了 company_note。

### 第 3 层：技术可信（Technical Credibility）
"这个人描述的工作，是我认识的工作吗？"

这是最微妙的一层。问题不是 "这些技术词对不对"，而是 "这些描述读起来像一个真正做过这个工作的人写的，还是像一个在模仿这个工作的人写的？"

荷兰 DE/MLE hiring manager 能闻到的真实性信号：
- 提到了 debug / troubleshoot / 失败处理（"不只是建了系统，还维护过"）
- 提到了和下游团队的协作（"不只是自己写代码，还服务过用户"）
- 技术细节的颗粒度恰到好处（太粗 = 可能没做过；太细 = 可能在堆砌关键词）
- 使用了领域内的自然表达（"partition pruning" 而不是 "optimized data access patterns"）

审计要求：逐条扫描 47 条 active bullet，标记：
- V（Verified）：有独立可验证的证据（GitHub, 认证, 学术机构, 竞赛）
- S（Specific）：细节足够具体，伪造成本高（具体数字、具体算法、具体工具版本）
- P（Plausible）：合理但不可验证（标准工作描述，没有外部证据）
- W（Weak）：模糊或难以评估（缺少规模、缺少结果、缺少上下文）

对所有 P 和 W 级别的 bullet，给出具体的可信度提升建议。建议必须基于现有事实，不能编造数字。

### 第 4 层：证据可信（Evidence Credibility）
"有没有我能自己去验证的东西？"

这是对中国候选人最关键的一层。因为前三层都有结构性折扣（学历折扣小，但公司和技术经验都有折扣），第 4 层是唯一能完全补偿的层。

证据类型（按可信度排序）：
1. **公开代码**（GitHub repo + README + tests + CI badge）— 最强：任何人都能去看
2. **学术输出**（论文、thesis、VU Amsterdam 公开记录）— 强：机构背书
3. **认证**（Databricks, 未来可以考 AWS/Azure）— 强：第三方验证
4. **公开竞赛**（Kaggle ranking）— 中强：有公开排行榜
5. **技术博客**（feithink.org）— 中：展示思考深度，但自我发布
6. **项目内证据**（test count, CI badge, coverage %）— 中：在 bullet 里提到，但需要 GitHub 才能验证

审计要求：
- 列出所有 portfolio 项目的当前证据状态（有无 GitHub 链接、有无公开 README、有无 CI、有无 test count）
- 对于缺少证据的高频项目，建议最低可行的证据补充方案
- 评估 feithink.org 博客在简历中的可信度贡献

## 关键文件

- 当前 bullet library: `assets/bullet_library.yaml`（v7.3, 47 active bullets）
- AI tailor 配置和 C2 prompt: `config/ai_config.yaml`
- 简历模板: `templates/base_template.html`
- 渲染器: `src/resume_renderer.py`
- Hook amplification 设计文档: `docs/plans/2026-04-28-bullet-library-hook-amplification-design.md`
- 叙事校准报告: `docs/plans/2026-04-27-bullet-library-v7.1-narrative-calibration.md`

## 候选人事实概要（不可编造，审计中使用）

- 清华大学 工业工程学士（2006-2010），中国 #1
- VU Amsterdam AI 硕士（2023-2025），GPA 8.2/10，Deep Learning 9.5
- Databricks Certified Data Engineer Professional（2026）
- Kaggle top 5%（Expedia Hotel Recommendation）
- GLP Technology（2017-2019）：消费信贷金融科技，~50 人，机构投资约 3 亿人民币。Fei 是第一个数据岗，从零建设信用评分体系
- Baiquan Investment（2015-2017）：量化对冲基金，5 人团队。Fei 做因子研究和策略开发，14.6% 年化收益（CSI 期货，实盘）
- Ele.me（2013-2015）：中国外卖平台，后被阿里巴巴收购（$9.5B, 2018）。Fei 在超高速增长期做数据分析
- Henan Energy（2010-2013）：国有企业，Fortune Global 500 #328。Fei 的第一份工作，业务分析
- Independent Researcher（2019-2023）：独立量化研究、语言学习、硕士准备。这是一个 4 年的 career gap
- Portfolio 项目：DocBridge (document AI), Financial Data Lakehouse (Databricks), Greenhouse Sensor Pipeline (PySpark), Deribit Options (trading system), Thesis (Deep RL UQ)
- 签证状态：Zoekjaar 至 2026 年 11 月，之后需要 Kennismigrant 签证（雇主需要是 IND 认可 sponsor）
- 博客：feithink.org

## 期望输出

1. **47 条 bullet 的可信度评级表**（V/S/P/W），附每条的关键风险点
2. **公司可信度渲染验证**：确认 company_notes 在实际 PDF 中正确出现
3. **证据缺口清单**：哪些高频项目缺少可验证证据，以及最低可行的补充方案
4. **5-8 条具体的可信度提升建议**，分为：
   - (a) 可以直接在 bullet_library.yaml 中修改的（措辞调整、上下文补充）
   - (b) 需要候选人行动的（公开 GitHub repo、写 README、考新认证）
   - (c) 需要在 AI tailor prompt 中调整的（选择策略、项目优先级）
5. **一个明确的回答："如果荷兰 hiring manager 只花 30 秒看这份简历，他的可信度判断会是什么？v7.3 之前 vs 之后有什么变化？还缺什么？"**

## 约束

- 所有建议必须基于已有事实，不可编造
- 不使用 em dash（用逗号或分号代替）
- 不给空洞建议（"增加可信度" 不是建议，"给 DocBridge 的 GitHub repo 加一个 README 包含 F1 score screenshot" 才是）
- 从荷兰 hiring manager 的视角思考，不是从候选人的视角
- 如果某个可信度问题是结构性的、无法通过简历修改解决的（比如 career gap），直接说明，不要回避
```

---

**执行说明**: 在新会话中粘贴上述 prompt（```之间的内容）。该 prompt 是自包含的，新会话不需要之前的对话上下文。
