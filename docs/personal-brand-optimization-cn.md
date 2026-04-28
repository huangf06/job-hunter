# 个人品牌优化：LinkedIn + GitHub + Blog

生成日期: 2026-04-02 | 与 career-strategy-2026-04.md 对齐

**战略定位**: ML/AI Engineer 主攻, MLOps 对冲, DE 保底。
所有品牌文案以 ML/AI 身份为主导。DE 经验定位为差异化优势（"我能搭建整条流水线，不只是训练模型"），而非主要身份。

---

## 交付物 1: GitHub Profile README.md

可直接提交到 `huangf06/huangf06` 仓库。

```markdown
# Fei Huang

坐标阿姆斯特丹的 ML Engineer。VU Amsterdam 人工智能硕士（GPA 8.2/10）。7+ 年数据基础设施与 ML 系统生产环境经验。

多数 ML 工程师来自研究背景或软件工程背景。我都不是——我在读 AI 硕士之前，做的是数据平台和量化交易系统。这意味着我用基础设施的思维方式来看模型：这个东西怎么会挂、怎么扩展、凌晨三点谁来维护。

我的硕士论文研究深度强化学习中的不确定性量化——模型如何知道自己"不知道什么"。之前的经历：金融科技创业公司的信用评分引擎、量化基金的系统性 alpha 研究、超高速增长外卖平台的反欺诈检测。每一步都在逼近数据系统与智能决策的交叉点。

我也在 [FeiThink](https://feithink.org) 写哲学和文学——主要是康德、陀思妥耶夫斯基，以及"如何好好活着"这个问题。

## 精选项目

**[job-hunter](https://github.com/huangf06/job-hunter)** -- AI 驱动的求职流水线。LLM 评估（Claude API）、自动简历生成、规则筛选、申请追踪。Python, SQLite/Turso, Playwright, GitHub Actions。

**Financial Data Lakehouse** -- Databricks 上的 ML 特征工程基础设施。Auto Loader + Structured Streaming 实时行情数据接入，Medallion 架构，schema evolution，quarantine-and-replay 数据质量框架。

**硕士论文: 深度 RL 不确定性量化** -- 在 HPC 上跑了 150+ 次训练，对比 5 种 UQ 方法。证明 QR-DQN 优越性（CRPS 降低 31%，p < 0.001）。发现"噪声悖论"：适度观测噪声反而提升集成模型的不确定性估计。

**[LifeOS](https://github.com/huangf06/LifeOS)** -- 个人生产力平台，编排 5 个服务（Todoist, Notion, Telegram Bot, Logseq, Eudic），通过 GitHub Actions 自动化工作流。

## 链接

- [LinkedIn](https://linkedin.com/in/huangf06)
- [Blog](https://feithink.org)
- [Substack](https://feithink.substack.com)（首发渠道）
```

---

## 交付物 2: LinkedIn 页面文案

### a) 头衔 Headline (214 字符)

```
ML Engineer | M.Sc. Artificial Intelligence, VU Amsterdam | 7+ Years Data Infrastructure & ML Systems | Databricks Certified | Python, PyTorch, Spark | Amsterdam
```

备选（更短，156 字符）:
```
ML Engineer | M.Sc. AI, VU Amsterdam | From Data Pipelines to Production ML | Databricks Certified | Amsterdam
```

### b) About 自我介绍 (~2000 字符)

```
Most ML engineers come from research or software engineering. I come from data infrastructure -- and that turns out to be a useful place to start.

I spent 7 years building systems where data quality and pipeline reliability directly determined whether decisions were good or catastrophic. At a fintech startup (GLP Technology), I was the first technical hire: I built the credit scoring decision engine from scratch -- 29 rejection rules, 36-segment borrower classification, a scorecard model combining 19 weighted features for default prediction. The entire system, from data ingestion through model-driven decisioning to post-loan monitoring.

Before that: systematic alpha research at a quant fund (factor modeling, backtesting with real capital), and fraud detection at Ele.me during hyper-growth (51K suspicious clusters identified across 2.2M users). Each role pushed me deeper into the question of how to make reliable automated decisions from messy, high-stakes data.

In 2023 I entered the M.Sc. AI program at VU Amsterdam (GPA 8.2/10). My thesis tackled uncertainty quantification in deep reinforcement learning -- 150+ training runs on HPC, evaluating when models know what they don't know. I hold the Databricks Certified Data Engineer Professional certification.

What I bring to ML engineering that pure ML graduates don't: I've built the data platforms that feed models. I know what happens upstream. I think about ML systems the way an infrastructure person does -- failure modes, data drift, pipeline reliability, monitoring. Bridging data pipelines and production ML is not an aspiration for me; it's what I've been doing from both sides.

Looking for ML/AI Engineering roles in the Netherlands. Full work authorization (Zoekjaar), eligible for Kennismigrant visa sponsorship.
```

**中文逐段解读：**

1. **开场 hook**: 大多数 ML 工程师来自研究或软件工程。我来自数据基础设施——这反而是个好的起点。
2. **GLP 经历（核心卖点）**: 金融科技创业公司第一个技术员工，从零搭建信用评分决策引擎——29 条拒绝规则、36 段借款人分类、19 个加权特征的首逾记分卡。从数据接入到模型驱动决策到贷后监控的完整系统。
3. **前序经历**: 量化基金的因子建模（真金白银回测），饿了么超高速增长期的反欺诈（220 万用户中识别 5.1 万可疑聚类）。
4. **学术转型**: 2023 年入读 VU Amsterdam AI 硕士（GPA 8.2/10）。论文做深度 RL 不确定性量化——HPC 上 150+ 次训练。持有 Databricks 认证。
5. **差异化价值主张**: 我搭建过喂养模型的数据平台。我知道上游发生了什么。我用基础设施的思维看 ML 系统——故障模式、数据漂移、流水线可靠性、监控。
6. **收尾**: 在荷兰找 ML/AI 工程岗。有完整工作许可（Zoekjaar），可申请 Kennismigrant 签证担保。

### c) 工作经历

**GLP Technology | ML & Data Engineering Lead | 2017.7 - 2019.8 | 上海**

```
First technical hire at a lending fintech. Designed and built the complete credit risk ML platform from scratch -- from raw data ingestion through model-driven automated decisioning to post-loan monitoring.

Core system: engineered the credit scoring decision engine with 29 rejection rules across 4 risk dimensions, a 36-segment borrower classification model, and an early-delinquency scorecard combining 19 weighted features for first-payment default prediction. This was a production ML system making real lending decisions.

Built the underlying data infrastructure: daily ETL of 30+ production tables into AWS Redshift, credit bureau report parser (deeply nested JSON to 5 structured analytical tables), and post-loan monitoring with delinquency tracking and fraud detection API integration.

Tech: Python, SQL, PySpark, AWS (Redshift, S3, EC2), Airflow, scikit-learn, pandas, NumPy
```

> **要点**: 标题从 "Data Engineer & Team Lead" 改为 "ML & Data Engineering Lead"。把信贷评分系统框架为"生产环境 ML 系统"。这是整个 profile 最关键的重新包装。

**Independent Quantitative Researcher | 2019.9 - 2023.8 | 远程**

```
Deliberate career transition: independent research + graduate school preparation.

Built automated equity research pipeline processing 83K+ daily records across 3,600+ stocks. Implemented institutional flow tracking and momentum signal detection for systematic market analysis.

Concurrent: self-directed deep dive into ML/DL (PyTorch, deep learning theory), English and German language acquisition. Admitted to M.Sc. AI at VU Amsterdam (2023).
```

> **要点**: 4 年空窗期定位为"主动选择的职业转型"，不是失业。强调持续技术输出。

**BQ Investment | Quantitative Researcher | 2015.7 - 2017.6 | 北京**

```
Quantitative hedge fund, 5-person team.

Built systematic alpha research pipeline: Fama-MacBeth regression validating 4 factor families (value, momentum, money flow, event-driven) across 3,000+ securities. Factors integrated into live portfolio. Developed and deployed R-Breaker intraday trading strategy achieving 14.6% annualized return with real capital.

Architected event-driven backtesting framework (Python + MATLAB) with walk-forward validation and 15+ performance metrics -- adopted as core research infrastructure.

Built end-to-end market data pipeline: 3,000+ securities, 5+ years tick-level futures data, corporate action handling, deduplication.

Tech: Python, MATLAB, SAS, SQL, NumPy, pandas, scipy
```

> **要点**: 强调"真金白银"——14.6% 年化收益。因子研究本质上就是 feature engineering，量化回测本质上就是 offline evaluation。

**Ele.me (被阿里收购) | Data Analyst | 2013.9 - 2015.7 | 上海**

```
Joined during hyper-growth, pre-Alibaba acquisition.

Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern-matching algorithms (same-phone, high-frequency, repeat-order), preventing fraudulent subsidy claims. This was effectively an anomaly detection / classification problem at scale.

Optimized 90+ Hadoop/Hive queries (partition pruning, subquery pushdown), cutting scan volume 5x (500GB to 100GB). Engineered user segmentation pipeline across 4 behavioral cohorts for targeted marketing.

Tech: SQL, Hadoop, Hive, Python, pandas, A/B Testing
```

> **要点**: 反欺诈重新框架为"规模化异常检测/分类问题"——用 ML 术语包装实际工作。

**Henan Energy | Business Analyst | 2010.7 - 2013.8 | 郑州**

```
Fortune Global 500 (#328). Built automated data consolidation pipeline across 20+ business units (2 days to 2 hours). Designed supply chain analytics framework -- EUR 32M documented profit impact over 3 years.
```

> **要点**: 最早经历从简处理。两个数字（20+ 业务单元、3200 万欧元）足够。

### d) 教育

**VU Amsterdam | M.Sc. Artificial Intelligence | 2023 - 2025**
```
GPA: 8.2/10

Thesis: Uncertainty Quantification in Deep Reinforcement Learning under Noisy Environments
- Benchmarked 5 UQ methods across 150+ HPC training runs (SLURM)
- QR-DQN superiority: 31% lower CRPS (p < 0.001) over ensemble and dropout baselines
- Discovered "noise paradox": moderate observation noise improves ensemble-based UQ

Selected courses (all 9.0+): Deep Learning (9.5), Multi-Agent Systems (9.5), ML for Quantified Self (9.5), NLP (9.0), Data Mining (9.0), Evolutionary Computing (9.0)
```

> **要点**: 论文是最强 ML 信号。课程成绩全部 9.0+，展示学术实力。

### e) Featured 精选栏目建议

置顶优先级：
1. **硕士论文** -- 链接到论文/仓库。最强 ML 信号。
2. **Databricks Certified Data Engineer Professional** -- 认证链接
3. **GitHub: job-hunter** -- "AI-powered job search pipeline (Claude API, Python, GitHub Actions)"
4. **博客文章: "What My M.Sc. Thesis Taught Me About Uncertainty"** -- 最高优先级待写
5. **博客文章: "Skin in the Game"** -- 分析思维，Taleb 在技术圈有共鸣

**避免置顶**: 政治评论类文章（李文亮、香港、白纸运动）。保留发布，不在 LinkedIn 推广。

### f) Skills 技能排序（ML/AI Engineer 定位）

**置顶 3 个:**
1. Machine Learning
2. Python
3. PyTorch

**其余 12 个:**
4. Deep Learning
5. Data Engineering
6. Apache Spark / PySpark
7. SQL
8. Databricks
9. scikit-learn
10. Docker
11. AWS
12. Delta Lake
13. Statistical Modeling
14. CI/CD
15. Airflow

---

## 交付物 3: 博客策略备忘录

### 现有文章评估

现有 48 篇文章全部是哲学/文学类。

**职业资产**: "Skin in the Game"、"Why We Read Kant"、"IKIRU"、"Reason and Emotion"、"History of Thought" 系列
**中性**: 文学分析、个人反思
**风险区**: 政治评论（保留发布，不在 LinkedIn 推广）

### 待写技术博客（5 篇，按 ML 优先排序）

**1. "What My M.Sc. Thesis Taught Me About Uncertainty" [最高优先级]**
为什么排第一: 这是最强 ML 背书。写成面向从业者的版本，证明你做的是真正的 ML 研究，不是跑教程。
大纲: 什么是不确定性量化？为什么生产 ML 需要它（模型置信度 != 准确率）。噪声悖论发现。150 次 HPC 训练教会我的可复现性。QR-DQN vs 集成方法——何时用哪个。
目标读者: ML 工程师、评估 ML 深度的 hiring manager。

**2. "From Data Pipelines to Production ML: Why Infrastructure Experience Matters"**
为什么: 这就是你的差异化叙事本身。这篇文章应该是"为什么我的背景是资产而非负债"的权威版本。
大纲: 因子研究就是特征工程。信用评分就是生产 ML 系统（即使 2017 年你没这么叫它）。回测就是离线评估。数据质量是生产 ML 的头号杀手。Jupyter 到生产的鸿沟是数据工程问题。
目标读者: 犹豫"DE 能做 ML 吗？"的 hiring manager。这篇文章给出肯定回答，带证据。

**3. "Automating Job Search with Python and Claude"**
为什么: 传播潜力 + 展示 LLM 集成到生产系统。
大纲: 架构、筛选流水线、LLM 评估（结构化输出的 prompt engineering）、简历生成、经验教训。
目标读者: 广泛的开发者受众。

**4. "Building a Real-Time Data Lakehouse on Databricks"**
为什么: Databricks 认证背书 + 展示当前技能。若转向 MLOps（feature store 基础设施）也相关。
大纲: Medallion 架构、Auto Loader vs 批处理、schema evolution、quarantine pattern。含架构图。
目标读者: Data/ML 工程师、Databricks 社区。

**5. "Credit Scoring from Scratch: Building an ML Decision System at a Startup"**
为什么: 将 GLP 重新框架为 ML 经验。
大纲: 第一个技术员工的故事。29 条规则引擎。记分卡方法论作为 ML。信用报告数据的特征工程。
目标读者: 金融科技工程师、认为"真正的 ML"只意味着神经网络的 ML 工程师。

### 博客组织

不分类，用标签（`technical`, `ml`, `philosophy`, `career`）。技术文章达到 3+ 篇后添加 "Technical Writing" 菜单项。

### Hugo 配置改进

- 更新站点描述: "Fei Huang writes about machine learning, data systems, philosophy, and moral thought"
- 更新关键词以 ML 术语开头: "machine learning, ML engineering, uncertainty quantification, deep reinforcement learning, data infrastructure, philosophy, Kant"

---

## 交付物 4: 跨平台一致性审计

### 叙事对齐（ML 优先策略）

| 元素 | 简历（待更新） | LinkedIn（提案） | GitHub（提案） | 博客（待建设） |
|------|---------------|-----------------|---------------|---------------|
| 主要身份 | ML Engineer | ML Engineer | ML Engineer | 需要技术文章 |
| 职业弧线 | IE -> DA -> Quant -> DE -> ML/AI | 同上 | 同上 | 文章 #2 讲述这个故事 |
| 差异化 | "桥接数据管道和生产 ML" | 同上 | "用基础设施思维看模型" | 文章 #2 + #5 |
| 论文突出度 | Projects 顶部 | Education 详述 | Selected Projects 含指标 | 文章 #1（最高优先级） |
| GLP 包装 | "ML 驱动的决策系统" | "信用风险 ML 平台" | 不详述 | 文章 #5 |
| 空窗期包装 | Career note | "主动职业转型" | 不提及 | 不需要 |
| Lakehouse 包装 | "特征工程基础设施" | About 中不提（太细） | "ML 特征工程基础设施" | 文章 #4 |

### 相比上一版的关键变更

1. **LinkedIn 头衔**: "Data Engineer" -> "ML Engineer"
2. **LinkedIn 置顶技能**: Spark/DE -> Machine Learning/PyTorch
3. **GitHub README 开头**: "Data engineer and AI practitioner" -> "ML Engineer"
4. **GLP LinkedIn 标题**: "Data Engineer & Team Lead" -> "ML & Data Engineering Lead"
5. **GLP 技术栈**: 加入 "scikit-learn"（记分卡本质上是 sklearn pipeline）
6. **About 开场 hook**: 重写，将 DE 框架为 ML 差异化优势而非主要身份
7. **Featured 精选**: 论文移到第 1 位（之前没有）
8. **博客优先级**: 论文文章现在是 #1（原来是 #2），职业叙事文章从"quant 到 DE"重新框架为"数据管道到生产 ML"

### 待解决的矛盾

1. **简历主模板仍然写着 "Data Engineer with expertise in..."** -- 需要按策略文档建议更新为 ML 优先："ML Engineer with 7+ years in data infrastructure, bridging the gap between data pipelines and production ML systems"
2. **Bullet library GLP 标题选项**: 当前默认 "Senior Data Engineer" 或 "Data Engineer & Team Lead"。需要为 ML 目标申请增加 "ML & Data Engineering Lead"。
3. **Bullet library `skill_tiers`**: ML 技能在通用 "ml" 类别下。对于 ML Engineer 定位应更突出。考虑重新排序让 ML 出现在 data_engineering 之前。
4. **LinkedIn vs 简历 GLP 标题**: LinkedIn 永久显示 "ML & Data Engineering Lead"。简历按申请调整。这没问题——LinkedIn 是固定 profile，简历是定制的。

### 行动项（按优先级排序）

| 优先级 | 行动 | 位置 |
|--------|------|------|
| P0 | 按本文档更新 LinkedIn 头衔、About、Experience | LinkedIn（手动） |
| P0 | 更新 resume bio_builder 默认为 ML 优先定位 | bullet_library.yaml |
| P0 | 在 GLP title_options 中添加 "ML & Data Engineering Lead" | bullet_library.yaml |
| P1 | 写论文博客文章（上面第 1 篇） | FeiThink |
| P1 | 创建/更新 GitHub profile README | huangf06/huangf06 repo |
| P1 | 写职业叙事博客文章（上面第 2 篇） | FeiThink |
| P2 | 写 job-hunter 文章（第 3 篇） | FeiThink |
| P2 | 更新 Hugo 配置的 keywords/description | FeiThink config |
| P2 | 更新博客 About 页面连接职业身份 | FeiThink |

### 统一 "About Me" 模板（ML 优先）

> ML Engineer based in Amsterdam with 7+ years building data infrastructure and ML systems in production. M.Sc. in Artificial Intelligence from VU Amsterdam (GPA 8.2/10), Databricks Certified Data Engineer Professional. Career path from quantitative finance through data engineering to AI -- each step driven by the same question: how do you make reliable automated decisions from messy, high-stakes data. I write about philosophy, literature, and moral thought at FeiThink.

各平台适配：
- **LinkedIn**: 展开为完整 About（见上方）
- **GitHub**: 直接使用，附项目链接
- **Blog About 页**: 以知识分子身份开头，然后职业背景
- **简历**: 压缩为 1-2 行 bio，按申请通过 bio_builder 定制
