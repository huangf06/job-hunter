# SVG Resume Overhaul — Session Prompt

## 背景

Job Hunter v3.0 重构中，我们已完成搜索优化、CL 解耦和 Streaming Daemon。现在进入最重要的一步：重构简历。

## 核心数据

- 349 次申请，15 次面试 (4.3%)，0 offer
- 面试来源：Data Engineer (7), ML/AI Engineer (4), Software Engineer-AI/Data (2), Quant (2)
- Data Science 18 次申请 0 面试（尽管 AI 评分 skill_match 7.0-9.0）
- 81.4% 幽灵率 — 简历可能是最大瓶颈
- 4 个 technical interview 全部失败 (live coding) — 但这不是简历问题

## 任务（按顺序）

### Phase 1: Bullet Library 审计
1. 读取 `assets/bullet_library.yaml`，逐条审阅所有 ~50 个 verified bullets
2. 对每个 bullet 评估：
   - 是否有量化数据？（数字、百分比、规模）
   - 是否展现 impact 而非 activity？
   - 是否符合 STAR 格式？
   - 与面试成功的角色类型(DE/ML/Backend)的相关性如何？
3. 标记需要改写的 bullets，提出改写建议
4. 检查是否缺少关键经历（比如 DS 方向的统计建模/实验设计经历）

### Phase 2: 叙事策略重构
1. 分析 15 个获得面试的职位 JD，提取共同要求和关键词
   - 查询 DB: `SELECT j.title, j.description FROM interview_rounds ir JOIN jobs j ON ir.job_id = j.id GROUP BY ir.job_id`
2. 对比当前 bullet library 覆盖度 vs 面试 JD 需求
3. 定义 3-4 个角色方向的叙事策略：
   - **Data Engineer**: 管道、规模、可靠性
   - **ML Engineer**: 模型训练、部署、MLOps
   - **Backend/Software Engineer (AI/Data)**: 系统设计、Python、数据平台
   - **Data Scientist**: 统计建模、实验设计、业务洞察（当前最弱，需要补强）
4. 每个方向确定：核心叙事主线、必选 bullets、加分 bullets

### Phase 3: SVG 模板制作
1. 先做 Data Engineer 和 ML Engineer 模板（优先，面试最多）
2. 使用 `scripts/svg_auto_optimizer.py` 迭代优化
3. 每份模板：
   - 针对该方向精选 bullets
   - 优化排版（双栏布局、技能栏位等）
   - 使用 Vision API 检查视觉质量
   - 转换为 PDF 验证
4. 后续补充 Backend 和 Data Scientist 模板

### Phase 4: AI Routing 集成
1. 修改 `src/ai_analyzer.py` — 在分析 prompt 中添加 `template_fit` 输出字段
2. 修改 `src/resume_renderer.py` — 添加 SVG 路由逻辑
3. template_fit >= 8 → 使用 SVG 模板 / < 8 → AI 定制 (Jinja2)

## 关键文件

- `assets/bullet_library.yaml` — 经验库 (核心)
- `config/ai_config.yaml` — AI 分析配置
- `src/ai_analyzer.py` — AI 分析器 prompt
- `src/resume_renderer.py` — 简历渲染器
- `scripts/svg_auto_optimizer.py` — SVG 简历生成与 Vision 迭代
- `scripts/svg_to_pdf.py` — SVG → PDF
- `templates/base_template.html` — 当前 Jinja2 模板
- `docs/plans/2026-03-08-v3-refactor-design.md` — 完整设计文档
- `docs/plans/2026-03-08-v3-implementation-plan.md` — 实施计划 (Task 4)

## 候选人背景

- 黄飞，6 年经验：数据管道 + ML 系统 + 量化研究
- 核心技能：Python, SQL, Spark, PyTorch, Airflow, Kafka
- 教育：荷兰 TU/e 硕士 (AI/Reinforcement Learning), 中国本科
- 工作经历：GLP Technology, 白泉投资, 饿了么, 河南能源
- 目标市场：荷兰
- 自我定位：Full Stack Data Scientist（但市场认知偏 DE/ML Engineer）

## 约束

- 所有 bullet 必须基于真实经历，不可编造
- SVG 模板必须 A4 大小，单页
- 简历需要 ATS 友好（虽然是 SVG，但内容要关键词优化）
- 先做 DE + ML 模板，DS 模板在 bullet 补强后再做
