# Bullet Library Deep Audit — Session Prompt

## 背景

我们已完成简历叙事策略设计（见 `docs/plans/2026-03-09-resume-narrative-strategy.md`）。核心决策：
- 叙事内核：First-Principles Builder（"能想也能做"）
- 四层策略：关键词层(ATS) → 扫描层(招聘者) → 阅读层(HM) → 分析层(面试官)
- 两个 SVG 模板：Data Engineer + ML Engineer
- 每段经历：1 个旗舰 bullet（面试钩子）+ 1-2 个标准 bullet（关键词高效）

## 任务

逐条审阅 `assets/bullet_library.yaml` 中的所有 ~50 个 verified bullets，并新增 2 个缺失的 bullet。

### 审阅原则（每个 bullet 必须过这 7 关）

1. **事实核查** — 问候选人："如果面试官深入追问这个 bullet 的每个细节，你能自信回答吗？" 如果不能，降级或重写。
2. **叙事定位** — 这个 bullet 在 DE 模板中的角色是什么？在 ML 模板中呢？两者都不需要？（参考策略文档中的 bullet selection）
3. **ATS 关键词** — 前 8 个词是否包含强动词 + 技术名词？
4. **量化数据** — 有数字吗？数字真实吗？如果没有，能否从候选人那里获取？
5. **Impact vs Activity** — 是"做了什么"还是"产生了什么影响"？
6. **防通胀** — bullet 是否把工作描述得比实际更大？（候选人说他对此有"造假感"）
7. **旗舰 vs 标准** — 如果是旗舰 bullet，是否包含足够的深度让面试官想追问？

### 审阅顺序

按策略文档中的 bullet selection 排序（最重要的先审）：

**第一批（旗舰 bullets — 最高优先级）：**
1. `glp_founding_member` [DE 旗舰 + ML 旗舰]
2. `bq_de_pipeline` [DE 旗舰]
3. `greenhouse_etl_pipeline` [DE 旗舰]
4. `thesis_uq_framework` [ML 旗舰]
5. `thesis_noise_paradox` [ML 钩子]
6. `bq_factor_research` [ML 旗舰]

**第二批（核心 bullets — 两个模板都用）：**
7. `glp_pyspark`
8. `glp_data_engineer`
9. `glp_portfolio_monitoring`
10. `bq_de_factor_engine`
11. `bq_data_quality`
12. `bq_futures_strategy`
13. `eleme_ab_testing`
14. `pt_personal_trading`
15. `expedia_ltr`

**第三批（支撑 bullets）：**
16-30: 其余 bullets（包括 ML 模板用的项目 bullets）

**第四批（新增 bullets）：**
- `he_vba_automation` — 河南能源：VBA 自动化报表，数据质量/造假检测
- `pt_market_analysis` — 独立研究期：Python 股票筛选框架，A 股市场分析

### 工作方式

每个 bullet：
1. Claude 展示当前内容 + 7 关评估
2. 如果需要事实确认 → 问候选人
3. 候选人确认/补充后 → Claude 提出改写建议
4. 候选人确认 → 更新 `bullet_library.yaml`
5. 每审阅完一批 → 提交 git commit

### 新增 bullets 的要求

- `he_vba_automation`：候选人在河南能源（2010-2013）用 Excel/VBA 自动化处理 12 个子公司的报表，识别数据错误、非标准化和数据造假。需要候选人提供具体细节。
- `pt_market_analysis`：候选人在独立期间（2019-2023）用 Python 分析 A 股市场数据（财务报表、技术指标、券商研报），筛选 3000+ 股票。需要候选人确认具体工作内容。

## 关键文件

- `docs/plans/2026-03-09-resume-narrative-strategy.md` — 叙事策略（必读）
- `assets/bullet_library.yaml` — 经验库（审阅对象）
- `config/ai_config.yaml` — AI 配置（参考）

## 候选人背景

- 黄飞，~6 年经验（正式工作 2010-2019，独立研究 2019-2023，硕士 2023-2025）
- 核心技能：Python, SQL, Spark, PyTorch, Airflow
- 教育：VU Amsterdam MSc AI (8.2/10), Tsinghua B.Eng.
- 候选人自我认知：深度思考者，first-principles builder，技术是手段不是目的
- **重要提醒：候选人对某些 bullet 有"造假感"——审阅时要特别关注是否有夸大**

## 约束

- 所有 bullet 必须基于真实经历，不可编造
- 需要向候选人确认的事实，必须先问再写
- 保持 bullet 简洁（1-2 行），不要用叙事箭头格式
- 优先保证 ATS 关键词效率
