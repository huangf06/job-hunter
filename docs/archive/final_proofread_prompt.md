# Final Proofread — Bullet Library v3.0

## 核心目标

我正在求职。当务之急是**拿到更多面试邀请**。成则拿到offer，败则增加面试经验。无论哪种结果，我都赢了。

Bullet库是我简历系统的弹药——AI根据每个JD自动选取最匹配的bullets生成定制简历。

你的任务：以一个**资深hiring manager**的视角，审核这50条bullets。核心标准只有一个：

**这条bullet能不能帮我拿到面试？**

适度包装完全OK。我们不是在写学术论文，我们是在做marketing。不要用"事实准确性"的视角来审查——用"市场竞争力"的视角。

## 你需要读取的文件

1. **主文件**: `assets/bullet_library.yaml` — 50条bullets + education + config
2. **参考材料（用于理解背景和准备答辩策略）**:
   - `C:\Users\huang\github\resume_project\materials\experiences\` — 每段经历的详细记录
   - `C:\Users\huang\github\resume_project\materials\projects\msc_thesis_uq_deeprl.md`
   - `C:\Users\huang\github\resume_project\materials\education\vu_amsterdam_msc.md`
3. **旧版**: `assets/bullet_library.yaml.bak.20260207` — 原始版本，有 `can_defend` 注释供参考
4. **成绩单**: `C:\Users\huang\github\resume_project\materials\Grade list.pdf`（需pymupdf）

## 已知的包装决策（全部接受，不要flag）

以下包装点已经过深思熟虑，校对时直接跳过：
- `glp_pyspark`: 包装为动手实现
- `bq_de_backtest_infra`: "performance attribution"
- `lakehouse_streaming`: "zero data loss"
- `lakehouse_quality`: "quarantine-and-replay pattern"
- `glp_founding_member`: "Spearheaded"
- 河南能源 "Fortune Global 500"
- 所有其他已有的包装措辞

## 校对重点（按优先级排序）

### 1. 冲击力评估（最重要）
- 动词是否有力且多样？（不要全是Built/Developed）
- 有没有quantification？（数字、规模、指标）
- business impact是否清晰？（"so what" factor）
- recruiter不懂技术，能否在6秒内理解这条bullet的价值？
- 与同level竞争者相比，这条bullet是否有differentiator？

### 2. 面试答辩准备
对每条bullet，想象面试官问 "Tell me more about this"。不是判断"能不能defend"（那是我的事），而是**帮我准备怎么defend**——如果某条bullet面试时会被深问，给我一个30秒的应答框架。

### 3. 语言打磨
- 语法、拼写、标点错误（这些会让人觉得不professional）
- 技术术语拼写一致性（PyTorch, NumPy, LightGBM, PySpark等）
- 英语是否native-sounding？有没有awkward的表达？
- 动词时态统一

### 4. 冗余检查
- 同一公司的多条bullets之间是否有重叠？
- 如果AI同时选中某两条，简历上会不会显得重复？
- 特别关注：GLP 7条、Ele.me 3条、河南能源 4条、Baiquan 6条

### 5. Education & Config
- 课程成绩与Grade list.pdf是否一致？
- 不应出现的低分（论文7.0、RL 8.0）是否已排除？
- `skill_tiers`、`bio_builder`、`title_options` 与bullets内容是否匹配？

## 输出格式

### 🔴 必须修改
语法硬伤、会让recruiter直接pass的问题。附当前文本 + 建议修改。

### 🟡 可以更强
bullet没问题，但有机会增加冲击力。附改写建议。

### ✅ 逐条确认
每条bullet一行。格式：
`[bullet_id] ✅` 或 `[bullet_id] ⚠️ 问题简述`

### 🛡️ 面试答辩卡片
对最可能被深问的10条bullet，各写一个30秒答辩框架：
- 面试官可能的追问方式
- 建议的回答结构（STAR格式）
- 如果被challenge到细节，怎么优雅地转移话题

### 📋 总评
- 整体战斗力评分（1-10）
- TOP 5 王牌bullets
- BOTTOM 5 最弱bullets（考虑是否值得保留）
