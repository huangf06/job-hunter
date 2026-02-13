# 简历系统全面审计报告：Fei Huang / ABN AMRO 数据工程师

---

## 执行摘要

**总体评估：** 系统架构设计良好（教育优先排序、项目突出展示、职业空白处理得当），但在可辩护性方面存在严重隐患——AI 生成的简介（bio）与 bullet library 自身的诚实记录相矛盾。简介中的多项声明，bullet library 本身就能推翻。

**评分：58/100**

**优先修复项：**
1. **立即修复简介** —— "6+ years building production data pipelines" 和 "deep expertise in PySpark" 无法在面试中自圆其说
2. **解决 PySpark 矛盾** —— GLP 的 `skills_only` 明确写着"无生产项目"，但 `glp_pyspark` bullet 却写"Led PySpark batch processing workflows"
3. **修复认证声明** —— 列为已获得，但实际状态是 `ready_to_exam`

---

## 1. 内容分析

### 叙事优势
- **Career note 处理得极好。** 一行话，HR 已验证通过，诚实简洁。不要改动。
- **教育优先排序是正确策略。** 清华 + VU Amsterdam + Databricks 认证前置 = 即时建立信任。
- **项目放在工作经历之前是正确选择。** Financial Data Lakehouse 比任何工作经历都更贴合这个 JD。
- **清华的注释** "(Ranked #1 in China, top 20 globally)" 对可能不了解清华的荷兰/欧洲雇主来说是必要的。

### 叙事弱点
- **简介过度包装。** "6+ years building production data pipelines across fintech and investment management" 暗示持续的、专职的数据工程工作。实际情况：GLP 是信贷风控/运营岗（附带 PySpark 接触），百泉是因子研究的 Python 脚本，饿了么是 SQL 报表。大方估计：2-3 年"和管道相关"的工作，不是 6+ 年"建设生产级数据管道"。
- **"Deep expertise in PySpark"** —— bullet library 白纸黑字写着 `skills_only: "Exposure to PySpark (learned but no production project)"`。这在技术面试中是定时炸弹。ABN AMRO 的面试官一定会追问 PySpark 生产经验，而你没有具体案例可讲。
- **"cutting-edge ML knowledge"** 对数据工程师岗位没有附加值，是填充语。

### 职业空白处理：**A-**
Career note 的方式近乎完美。唯一改进建议：如果荷兰语已达到日常对话水平（bullet library 确认了），考虑改为 "(English, German, Dutch)" —— 在荷兰银行，这是加分项。

### 差异化分析
- **未充分利用：** Databricks 认证被提及但没有突出。对这个 JD，它应该是第一差异化因素。
- **未充分利用：** 金融领域专长。ABN AMRO 是银行。信贷风控 + 量化金融的背景直接相关，但简介用了通用的表述。
- **过度使用：** 通用的"数据管道"表述，听起来和其他所有申请者一样。

---

## 2. 技术审计

### 事实准确性报告

| 声明 | Bullet Library 记载 | 结论 |
|------|---------------------|------|
| "6+ years building production data pipelines" | GLP：2年信贷风控运营，PySpark"无生产项目"。百泉：2年因子研究 Python 脚本。饿了么：SQL 报表。 | **不可辩护。** 应改为"4+ years working with data systems"或类似表述 |
| "Deep expertise in PySpark" | `skills_only: "Exposure to PySpark (learned but no production project)"` | **与 bullet library 直接矛盾** |
| "Databricks Certified Data Engineer Professional (2026)" | `status: "ready_to_exam"`，"考试已安排在2026年2月6日" | **声明过早** —— 应写"expected Feb 2026"或通过后再更新 |
| GLP 职位："Data Engineer & Team Lead" | 已验证职位："Data Analyst / Risk Operations Lead" | **职位虚高。** 已验证的职位中不包含"Data Engineer" |
| "Led PySpark batch processing workflows"（GLP bullet） | `can_defend: "Did work with PySpark"`，`skills_only: "Exposure to PySpark"` | **"Led"对"接触过"来说太强了** |
| 饿了么任期：Sep 2013 - Jul 2015 | `actual_duration: "4-5个月"`，验证日志："从河南能源借了时间——背调风险" | **已知背调风险** |
| 百泉数据工程 bullets | 已验证，可辩护 | **OK** |
| Lakehouse 项目 bullets | 已验证，进行中的个人项目 | **OK** |
| 饿了么 A/B 测试声明 | 已验证，2倍召回率准确 | **OK** |

### 可辩护性评估：**C+**

最可能在面试中暴露问题的问题：

> "你提到对 PySpark 有深入专长，请讲一个你构建的生产级 PySpark 任务，你怎么监控它的，出故障时怎么处理的？"

根据 bullet library，没有好的答案可以回应这个问题。候选人有 Databricks 认证学习经验和个人项目，但没有生产级 PySpark 故事。

**建议：** 将"deep expertise"改为"hands-on experience through Databricks certification and portfolio project" —— 这可以辩护，而且仍然有说服力。

### 针对 ABN AMRO 的技术深度分析

JD 要求：
- **7年 Azure 经验** —— 候选人只有"接触过"（部署过 VPN 和个人项目）。这是一个硬性门槛。
- **TypeScript** —— 候选人技术栈中没有。简历正确地没有列出。
- **Kafka** —— 未验证。简历正确地没有列出。
- **Terraform/Bicep** —— 未验证。简历正确地没有列出。

**诚实评估：** 这是一个跨级申请。AI 给了 7.0 分，但仅 7 年 Azure 要求一项就很可能导致被拒。系统正确识别了这一点，但仍然生成了简历。技能诚实规则运作良好（Kafka、Terraform 正确地被省略），但简介过度承诺了。

---

## 3. 岗位定位

### 当前定位 vs 最优定位

**当前：** 具有管道经验的通用数据工程师
**对 ABN AMRO 的最优定位：** 具有信贷领域专长的银行/金融科技数据工程师

ABN AMRO 是银行。简历完全掩埋了金融领域的角度。简介应该以银行/信贷的相关性为主导，而不是通用的"数据管道"。

### 职位优化

| 公司 | 当前职位 | 建议 | 理由 |
|------|---------|------|------|
| GLP | "Data Engineer & Team Lead" | "Data Analyst & Team Lead" 或 "Risk Data Lead" | 不能声称未担任过的 DE 职位。"Risk Data Lead"诚实且与金融相关 |
| 百泉 | "Quantitative Developer" | 保持不变 | 对 DE 角度适当 |
| 饿了么 | "Data Analyst" | 保持不变 | 正确 |

### 经历选择：**B+**
对 DE 岗位选择得当。GLP（管道、数据质量）、百泉（数据摄取、计算引擎）、饿了么（Hadoop、SQL 规模化）。正确省略了河南能源。

### 排列策略：**A-**
最近/最相关的在前（GLP），然后百泉，然后饿了么。对这个岗位是正确的排列。

---

## 4. ATS 与格式

### ATS 兼容性：**B+**
- 干净的 HTML，不使用表格布局，语义化结构
- 段落标题清晰（`EDUCATION`、`WORK EXPERIENCE`、`TECHNICAL SKILLS`）
- 技能以文本列出，不是图片
- **问题：** `contact-divider` 的 span 和 flexbox 布局可能会让一些老旧 ATS 解析器出问题

### 格式问题
- **Delta Lake 出现两次：** 一次在"Data Engineering"下，一次在"Databases & Big Data"下。需要删除一处。
- **博客 URL 不一致：** 页头链接到 `feithink.substack.com`，兴趣部分链接到 `huangf06.github.io/FeiThink/en/`。应统一。
- **认证出现三次：** 教育部分、技能部分的"Certifications"行、以及简介中隐含提及。教育 + 技能各一次可以；简介再提是过度。

### 视觉层次：**B+**
- Georgia 衬线字体专业易读
- 分节线提供清晰分隔
- 字号层级合理（24pt 姓名 → 11pt 分节 → 10pt 正文 → 9.5pt 细节）
- **改进：** 技能类别标签的 `min-width: 120pt` 浪费空间。"Languages:" 不需要 120pt。

---

## 5. Bullet Library 审查

### 高影响力 Bullets（保留）
- `glp_founding_member`："As founding data team member, owned end-to-end development of credit scoring infrastructure" —— 强烈的 ownership 语言，已验证。
- `bq_de_pipeline`："Engineered automated data ingestion pipelines to fetch daily market data" —— 具体、技术性强，展示 ETL 能力。
- `bq_de_factor_engine`："Built high-performance factor computation engine using vectorized Pandas/NumPy" —— 展示性能优化能力。
- `lakehouse_streaming`：整个 lakehouse 项目是 DE 岗位最强素材。
- `eleme_ab_testing`：具体指标（2x 召回率），Hadoop 规模化。

### 需要改写的弱 Bullets

**`glp_pyspark`**（当前）：
> "Led PySpark batch processing workflows to process large-scale datasets, reducing processing time and enabling daily risk reporting; mentored junior analysts on best practices."

**问题：** "Led"和"large-scale"没有得到 `can_defend` 的支持——后者只说"Did work with PySpark"，而 `skills_only` 说"无生产项目"。这个 bullet 是整个系统中最大的可辩护性风险。

**建议改写：**
> "Utilized PySpark for batch processing of risk datasets, supporting daily reporting workflows; mentored junior analyst on data processing best practices."

这是诚实的，仍然展示了 PySpark，避免了"Led" + "large-scale"的过度包装。

**`glp_data_engineer`**（当前）：
> "Built automated monitoring systems for loan portfolio data quality and anomaly detection; collaborated with analysts and business teams to translate requirements into alerting pipelines and data-driven insights."

**问题：** 内容和 `glp_portfolio_monitoring` 重叠。同时出现在简历上会显得冗余。选一个。

**`bq_de_backtest_infra`**（当前）：
> "Developed the underlying event-driven backtesting infrastructure that supported strategy simulation and performance reporting."

**问题：** 模糊。没有说明"事件驱动"具体指什么，"基础设施"的范围也不清楚。

**建议改写：**
> "Developed event-driven backtesting engine in Python supporting multi-factor strategy simulation, performance attribution, and walk-forward validation."

### 缺失需要新增的 Bullets

1. **一个 Databricks 专项 bullet：** 认证验证了技能，但没有工作 bullet 展示 Databricks 在专业场景中的应用。lakehouse 项目部分覆盖了这一点，但一个关于 Delta Lake 优化或 Medallion Architecture 在工作场景中的 bullet 会加强叙事。

2. **一个数据治理/数据质量 bullet：** ABN AMRO 是银行，有严格的监管要求。lakehouse 项目提到了隔离模式（quarantine pattern），但一个关于数据质量框架、审计追踪或合规性的 bullet 会与银行业产生强烈共鸣。

3. **饿了么需要第二个 bullet（DE 岗位用）：** Hadoop/SQL 查询的 bullet（`eleme_sql_reporting`）在 job-hunter 版本中很好："Queried and processed large-scale user data from Hadoop cluster using Hive SQL; optimized complex queries and built automated reporting pipelines." 这次简历没有选用，但应该选用。

---

## 6. 模板系统分析

### 分类逻辑：**B**
- 关键词权重合理
- 量化公司的强制覆盖规则好用
- **问题：** `title_override` 的正则表达式过于简单。`(?i)data.*engineer` 会匹配"Data Quality Engineer"、"Data Platform Engineer"等——都应归为 `data_engineer`，但技能侧重不同。
- **问题：** 没有"AI Engineer"或"GenAI"角色模板。这类岗位在 2026 年越来越常见。

### 关键词权重评估

**有问题的权重：**
- `data_engineer.kafka: 7` —— Kafka 是强 DE 信号，应该是 8-9
- `data_engineer.dbt: 7` —— dbt 是 analytics engineering 的强信号
- `ml_engineer.ci/cd: 7` 和 `ml_engineer.docker: 6` —— 这些同样是 DE 信号；不应只偏向 ML

**缺失关键词：**
- `data_engineer`：缺少 "medallion"、"lakehouse"、"data quality"、"data governance"、"unity catalog"、"schema evolution" —— 这些都是现代 DE 岗位的强信号
- `data_scientist`：缺少 "experiment platform"、"metric"
- 通用：缺少 "terraform"、"infrastructure as code" —— 虽然不属于任何现有类别，但 DE 岗位越来越多地要求

### 项目选择策略：**B+**
- 正确地为 DE 岗位优先选择 lakehouse
- **问题：** data_engineer 模板中的 `expedia_pipeline` 和 bullet library 中的任何项目 key 都不匹配。实际 key 是 `expedia_recommendation`。这会导致查找失败。

### 技能结构：**B**

`data_engineer` 模板的 `skills_structure` 在"Data Infrastructure"下列了 `"Databricks, PySpark, Delta Lake, Hive, Apache Airflow, Docker"` —— 不错，但已过时。应包含"Structured Streaming, Auto Loader, Schema Evolution"，因为这些是认证验证过的技能。

---

## 7. 竞争力分析

### 这个 ABN AMRO 岗位的顶级候选人画像

竞争力强的"IT Data Engineer, 7+ years Azure"候选人通常具备：
- 5-10 年在欧洲公司的持续 DE 工作经验（ING、Rabobank 等）
- 深度 Azure 原生技术栈（Azure Data Factory、Synapse、ADLS、Azure DevOps）
- 在 Azure 上的生产级 Databricks 经验（不是 AWS）
- 真实的 Kafka 流处理经验（事件驱动的银行数据）
- Terraform/IaC 管理 Azure 基础设施
- 荷兰语能力（ABN AMRO 加分项）
- 银行领域知识（风控、支付、KYC/AML）

### 我们的独特优势（别人没有的）
1. **清华 + VU Amsterdam 双学位背景** —— 罕见的学术组合
2. **双面金融领域经验** —— 信贷风控（贷款端）和量化（交易端）。大多数 DE 候选人两个都没有。
3. **Databricks 认证** —— 正式验证 vs. "我用过一次 Spark"
4. **最新 AI 硕士学位** —— 在 DE 技能之上增加 ML 能力，大多数纯 DE 候选人不具备。对正在 AI 化的银行来说有价值。

### 未充分利用的角度
1. **银行/信贷风控叙事。** ABN AMRO 的 Credit Capability Team 需要理解信贷数据的人。Fei 建设过信贷评分基础设施。这应该是主导叙事，不是被埋在通用的"数据管道"下面。
2. **"桥梁"定位。** 很少有候选人能同时横跨 DE 和数据科学。在银行，这意味着同一个人既能建设管道，又能理解消费这些管道的模型。这是真正有价值的。
3. **荷兰语。** Bullet library 显示荷兰语已达"日常对话"水平。对荷兰银行来说，即使基础荷兰语也展示了融入的诚意。考虑加入语言部分。

### 差异化机会
- **围绕银行业重写简介：** "Data Engineer with credit risk infrastructure experience and Databricks expertise, combining production pipeline skills with formal AI training from VU Amsterdam."
- **在简历中加入荷兰语** —— 即使"Dutch (Conversational)"也传递了扎根荷兰的信号。

---

## 8. 系统层面问题

### 严重问题：两个 Bullet Library 不同步

系统有两个 bullet library 文件：
- `C:\Users\huang\github\job-hunter\assets\bullet_library.yaml`（AI 系统使用）
- `C:\Users\huang\github\resume_project\bullet_library.yaml`（似乎是旧版本）

它们已经显著分化：
- GLP `glp_founding_member` 内容不同
- GLP `glp_pyspark` 内容不同（"Led" vs "Contributed"）
- 饿了么 bullets 不同（job-hunter 版本的 `eleme_ab_testing` 增加了 Hadoop 描述）
- Financial Data Lakehouse 项目只存在于 job-hunter 版本

**这很危险。** job-hunter 版本有"增强版"bullets，超出了 resume_project 版本（更接近原始验证）的声明范围。增强的方向走偏了——让 bullets 更强，但没有重新验证可辩护性。

### AI Prompt 过于信任

AI prompt 要求"逐字复制 bullet library 中的 bullets"，但 bullets 本身在"增强"阶段已经被膨胀了。系统有好的护栏（不捏造、仅用已验证 bullets），但它抽取的 bullets 已经偏离了验证过的原始版本。

### 缺失的质量门：简介验证

简介是 AI 自由文本生成的，没有对 bullet library 进行交叉验证。"6+ years"和"deep expertise"就是这么来的。系统需要一个质量门，将简介声明与 `can_defend` 和 `skills_only` 字段交叉校验。

### `feithink.substack.com` 硬编码 URL

base_template.html 在页头硬编码了 `feithink.substack.com`，但 bullet library 和兴趣部分使用 `huangf06.github.io/FeiThink/en/`。要么模板使用变量，要么统一一个 URL。

---

## 9. 针对这份 ABN AMRO 简历的具体建议

### 修改后的简介（可辩护版本）
> Data Engineer with hands-on credit risk infrastructure experience and Databricks Certified Data Engineer Professional credentials. Built end-to-end data pipelines for fintech credit scoring; recent M.Sc. in AI from VU Amsterdam combines engineering foundations with machine learning expertise.

改动说明：删除了"6+ years"（不可辩护），删除了"deep expertise in PySpark"（与 bullet library 矛盾），增加了信贷风控角度（与 ABN AMRO Credit Capability Team 相关），保留 Databricks 认证突出展示。

### 技能部分修复
- 从"Databases & Big Data"中删除 Delta Lake（已在"Data Engineering"中列出）
- 增加语言部分：`English (Fluent), Mandarin (Native), Dutch (Conversational)`
- 考虑在 Data Engineering 下增加"Structured Streaming, Schema Evolution"（认证已验证的技能）

### GLP 职位修复
从"Data Engineer & Team Lead"改为"Data Analyst & Team Lead"（更接近已验证的真实职位）。

### 认证修复
将"Databricks Certified Data Engineer Professional (2026)"改为：
- 如果已通过考试，保持不变
- 如果尚未通过，改为"Databricks Certified Data Engineer Professional (Expected Feb 2026)"

---

## 10. 长期系统建议

1. **合并两个 bullet library。** 在 job-hunter 项目中保留唯一的真相源。归档 resume_project 的版本。

2. **在 AI 管道中加入简介验证。** 交叉校验所有年数声明与实际工作经历日期。交叉校验"expertise"声明与 `skills_only` 和 `can_defend` 字段。

3. **加入"跨级申请"标记。** 当 AI 评分 7.0 但某个硬性要求（如"7年 Azure"）明显不满足时，系统应标记为跨级申请，以便用户做优先级判断。

4. **分离"增强版"和"已验证版"bullets。** 当前系统混为一体。一个 bullet 应该有 `verified_content`（与 Fei 确认的原始措辞）和 `enhanced_content`（优化措辞）作为独立字段，附带标记说明哪个版本经过了验证。

5. **增加"GenAI / AI Engineer"角色模板。** 市场已经转变；许多岗位现在融合了 DE + ML + LLM。当前 4 角色系统遗漏了这个增长中的类别。

6. **追踪申请结果。** 系统有 `applications` 表但没有反馈闭环。投递 20-30 份后，分析哪些简历变体获得了回复，以此校准 AI 评分。

---

## 最终裁定

系统架构确实令人印象深刻——从爬取到 AI 分析到 Jinja2 渲染的管道设计精良。Bullet library 的验证过程彻底且诚实。问题出在最后一公里：AI 增强层添加了超出验证层所确认范围的声明。

**最大的风险不是一份差的简历，而是一份让你拿到你扛不住的面试的简历。** 如果 ABN AMRO 的面试官追问"6+ 年生产级数据管道"或"PySpark 深度专长"，而诚实的回答是"我接触过 PySpark 但没有生产项目"和"我实际的管道工作是量化基金的 Python 脚本"——面试就结束了。

修复可辩护性缺口。以银行领域角度为主导。接受这个特定 JD 是跨级申请（Azure 7 年）。最重要的是：把 bullet library 的诚实带到简介中去，而不是反过来。
