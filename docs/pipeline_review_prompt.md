# Job Hunter Pipeline 深度审查 Prompt

## 背景信息

我是一名在荷兰求职的数据工程师/ML 工程师，有 6 年经验（数据管道 + ML 系统 + 量化研究）。我构建了一个自动化求职系统，从职位爬取到简历生成全流程自动化。

**当前签证状态**：Orientation Year (Zoekjaar)，有效期至 2026-11，需要转换为 Kennismigrant（需要雇主担保）。

**核心技能**：Python, SQL, Spark, PyTorch, TensorFlow, Airflow, 数据工程, ML 系统

**目标职位**：Data Engineer, ML Engineer, Analytics Engineer, Quantitative Researcher, Research Engineer

## 系统架构概览

```
┌──────────────────────────────────────────────────────────────────┐
│  Phase 1: Job Discovery (LinkedIn + Multi-platform Scrapers)    │
├──────────────────────────────────────────────────────────────────┤
│  • LinkedIn Scraper v6 (Playwright + cookies)                   │
│    - 6 profiles, 8 queries, 31 OR conditions                    │
│    - Full-time only, all workplace types                        │
│    - Past 24 hours, sorted by date                              │
│  • Multi-platform Scraper (Greenhouse + Lever + IamExpat)       │
│    - 18 target companies, ATS API + web scraping                │
│  • Output: Raw jobs → data/jobs.db (SQLite + Turso sync)        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  Phase 2: Hard Filtering (Rule-based, Fast)                     │
├──────────────────────────────────────────────────────────────────┤
│  • 9 hard reject rules (filters.yaml):                          │
│    1. Dutch language detection (word count ≥5)                  │
│    2. Dutch required (fluency, native)                          │
│    3. Non-target role (title must contain specific keywords)    │
│    4. Wrong tech stack (frontend, mobile, devops, java, ruby)   │
│    5. Freelance/ZZP only                                        │
│    6. Low compensation (<€1500/month)                           │
│    7. Specific tech experience (5+ years Java/C++/Azure)        │
│    8. Experience too high (8+ years)                            │
│    9. Senior management (Principal, Director, VP)               │
│  • Output: filter_results table (passed/rejected + reasons)     │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  Phase 3: Rule-based Scoring (Keyword matching)                 │
├──────────────────────────────────────────────────────────────────┤
│  • Base score: 3.0                                               │
│  • Title scoring (high weight):                                 │
│    - ML/AI roles: +2.5                                          │
│    - Research roles: +2.0                                       │
│    - Data Engineering: +2.0                                     │
│    - Quant: +2.5                                                │
│    - Senior: -1.0, Lead/Staff: -1.5                            │
│  • Body scoring (category caps):                                │
│    - Python: +1.0 (max 1.0)                                     │
│    - ML frameworks: +1.0 each (max 2.0)                         │
│    - Data tools (Spark, Airflow): +1.5 each (max 2.5)          │
│    - NLP/LLM: +1.5 each (max 2.0)                               │
│    - RL: +1.0 each (max 1.0)                                    │
│    - Visa sponsorship: +2.0 (max 2.0)                           │
│    - Target companies: +2.0/+1.5/+1.0 (tier 1/2/3)             │
│  • Thresholds: ≥7.0 APPLY_NOW, ≥5.5 APPLY, ≥4.0 MAYBE, <4.0 SKIP │
│  • Output: ai_scores table (rule_score, recommendation)         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  Phase 4: AI Analysis (Claude Opus, rule_score ≥3.0)            │
├──────────────────────────────────────────────────────────────────┤
│  • Model: Claude Opus 4.6 (via proxy)                           │
│  • Input: JD + candidate profile (from bullet_library.yaml)     │
│  • Output (single API call):                                    │
│    - AI scoring: skill_match, experience_fit, growth_potential  │
│    - Tailored resume JSON: bio spec + bullet IDs + skills       │
│  • Bullet-by-ID system: AI outputs IDs, deterministic lookup    │
│  • Bio builder: structured spec (domain_claims, closer, title)  │
│  • Validation gates: title, skill categories, min experiences   │
│  • Quota handling: DAILY_LIMIT_EXCEEDED → return None (retry)   │
│  • Output: job_analysis table (ai_score, tailored_resume JSON)  │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  Phase 5: Resume Generation (Jinja2 + Playwright, ai_score ≥5.0)│
├──────────────────────────────────────────────────────────────────┤
│  • Template: base_template.html (Jinja2)                        │
│  • Input: tailored_resume JSON from job_analysis                │
│  • Rendering: Playwright (HTML → PDF)                           │
│  • Validation: ResumeValidator v3.0 (blocking gates)            │
│  • Output: output/Fei_Huang_[Company]_[Title].pdf               │
│  • Cover Letter: AI-generated (Claude Opus) + template          │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│  Phase 6: Application Tracking & Interview Prep                 │
├──────────────────────────────────────────────────────────────────┤
│  • Local workflow: --prepare → checklist server → --finalize    │
│  • Repost detection: same company+title already applied         │
│  • Interview scheduler: Google Calendar + AI scoring + 3D model │
│  • Interview prep: 7-phase workflow (8-9 files, ~40KB, ~90min)  │
│  • Email tracking: Gmail API + mail_processor (rejection detect)│
│  • Status tracking: applications table (applied/interview/etc)  │
└──────────────────────────────────────────────────────────────────┘
```

## 当前配置快照

### 搜索配置 (search_profiles.yaml)
- **6 profiles, 8 queries, 31 OR conditions**
- Group 1 (data_engineering): 2 queries, 7 keywords
- Group 2 (ml_engineering): 1 query, 4 keywords
- Group 3 (backend_engineering): 1 query, 4 keywords
- Group 4 (data_science): 1 query, 4 keywords
- Group 5 (quant): 1 query, 4 keywords
- Group 6 (ml_research): 2 queries, 8 keywords

### 硬规则 (filters.yaml)
- 9 hard reject rules
- Dutch detection: word count ≥5
- Title whitelist: 19 specific keywords (removed "engineer", "developer")
- Tech stack blacklist: frontend, mobile, devops, java, ruby (removed "full stack")

### 评分规则 (scoring.yaml)
- Base: 3.0, Range: 0-10
- Title scoring: 4 categories (ML/AI, Research, Data Eng, Quant)
- Body scoring: 10+ categories with caps
- Target companies: 28 companies (14 tier 1, 7 tier 2, 7 tier 3)

### AI 配置 (ai_config.yaml)
- Model: Claude Opus 4.6
- Thresholds: rule_score ≥3.0 for AI, ai_score ≥5.0 for resume
- Budget: daily_limit, warn_threshold
- Bullet library: 50 bullets, 10 skill categories

### CI/CD (GitHub Actions)
- Frequency: 2x/day (workdays 09:37, 15:37 CET) + 1x/weekend (12:23 CET)
- Turso embedded replica (cloud sync)
- Auto AI analysis (limit = new_jobs + 20)

## 审查维度

请从以下维度深度审查整个 pipeline，找出潜在问题和改进空间：

### 1. 搜索策略 (Job Discovery)

**关键问题**：
- 搜索关键词是否覆盖了所有相关职位？是否有遗漏的高价值职位名称？
- 6 个 profiles 的分组是否合理？是否有重复或冗余？
- LinkedIn 搜索参数（Full-time only, all workplace types）是否最优？
- Multi-platform scraper 的目标公司列表是否完整？
- IamExpat 搜索关键词是否充分利用了平台特性？

**深入分析**：
- 是否有职位因为关键词不匹配而被遗漏？
- 搜索频率（2x/day）是否足够？是否会错过快速填补的职位？
- LinkedIn 反爬风险：每个 query ≤4 OR 是否足够安全？
- 是否应该增加更多平台（Indeed, Glassdoor, etc.）？

### 2. 硬规则过滤 (Hard Filtering)

**关键问题**：
- 9 条硬规则是否过于严格？是否误杀了好职位？
- Dutch detection (≥5 words) 阈值是否合理？
- Title whitelist (19 keywords) 是否过于宽泛或过于狭窄？
- Tech stack blacklist 是否准确？是否有误杀（如 Full Stack）？
- 经验年限过滤（8+ years）是否合理？我有 6 年经验。

**深入分析**：
- 是否有规则之间的冲突或重复？
- 是否有应该硬拒绝但没有被覆盖的情况？
- 是否有应该软拒绝（扣分）而不是硬拒绝的规则？
- Exceptions 列表是否完整？

### 3. 评分系统 (Rule-based Scoring)

**关键问题**：
- Base score 3.0 是否合理？是否导致大部分职位分数偏低或偏高？
- Title scoring 权重（+2.0 ~ +2.5）是否合理？
- Body scoring 的 category caps 是否合理？是否限制了高匹配职位的分数？
- Senior 惩罚（-1.0）是否过轻或过重？
- Target companies 列表（28 家）是否完整？是否有遗漏的高价值公司？

**深入分析**：
- 评分分布是否合理？是否大部分职位集中在某个分数段？
- 是否有关键技能没有被评分？（如 Docker, Kubernetes, AWS）
- Visa sponsorship (+2.0) 权重是否足够？这对我很关键。
- 是否应该增加负面关键词（如 "PhD required", "10+ years"）？

### 4. AI 分析 (Claude Opus)

**关键问题**：
- Prompt 是否清晰、完整？是否给 AI 提供了足够的上下文？
- Bullet-by-ID 系统是否健壮？是否有 unknown ID 的处理？
- Bio builder 是否灵活？是否能适应不同类型的职位？
- Validation gates 是否过于严格？是否误杀了好职位？
- Quota handling 是否完善？DAILY_LIMIT_EXCEEDED 后是否能自动恢复？

**深入分析**：
- AI 评分是否准确？是否有系统性偏差（如偏好某类职位）？
- Tailored resume 质量如何？是否真的"定制"了？
- Token 消耗是否合理？是否有优化空间？
- 是否应该使用更便宜的模型（如 Sonnet）做初筛？

### 5. 简历生成 (Resume Rendering)

**关键问题**：
- 简历模板是否专业？是否符合荷兰/欧洲标准？
- Bullet library (50 bullets) 是否足够？是否有重复或低质量的 bullets？
- Skill categories (10 个) 是否合理？是否有遗漏的技能？
- ResumeValidator v3.0 的 blocking gates 是否过于严格？
- Cover Letter 生成是否有效？是否真的个性化了？

**深入分析**：
- 简历长度是否合适？（目标：1 页）
- 简历格式是否 ATS-friendly？
- 是否应该根据职位类型使用不同的模板？
- Bullet 选择逻辑是否合理？是否总是选最相关的？

### 6. 申请流程 (Application Workflow)

**关键问题**：
- Local workflow (--prepare → checklist → --finalize) 是否高效？
- Repost detection 是否准确？是否有误报？
- 是否应该自动化申请提交（而不是手动）？
- 申请跟踪是否完善？是否有遗漏的状态？

**深入分析**：
- Checklist server 的 UX 是否友好？
- 是否应该增加申请优先级排序？
- 是否应该增加申请截止日期提醒？
- 是否应该增加申请进度可视化？

### 7. 面试准备 (Interview Prep)

**关键问题**：
- 7-phase workflow 是否高效？是否有冗余步骤？
- 8-9 个文件是否过多？是否应该合并？
- Interview scheduler 的 3D 评分模型是否准确？
- Google Calendar 集成是否稳定？
- 是否应该增加 mock interview 功能？

**深入分析**：
- 面试准备时间（~90 min）是否合理？
- 是否应该增加技术问题准备（LeetCode, system design）？
- 是否应该增加 behavioral questions 准备（STAR stories）？
- Post-interview notes (09 file) 是否被充分利用？

### 8. 数据管理 (Database & Sync)

**关键问题**：
- SQLite + Turso embedded replica 是否稳定？
- Stale replica bug 是否已完全修复？
- 数据库 schema 是否合理？是否有冗余或缺失的字段？
- 是否应该增加数据备份机制？
- 是否应该增加数据分析功能（漏斗分析、成功率分析）？

**深入分析**：
- Turso sync 频率是否合理？
- 是否应该使用 PostgreSQL 替代 SQLite？
- 是否应该增加数据清理机制（删除旧职位）？
- 是否应该增加数据导出功能（CSV, JSON）？

### 9. CI/CD & 自动化 (GitHub Actions)

**关键问题**：
- CI 频率（2x/day + 1x/weekend）是否最优？
- AI analysis limit (new_jobs + 20) 是否合理？
- 是否应该增加失败重试机制？
- 是否应该增加通知机制（Telegram, Email）？
- 是否应该增加监控和告警？

**深入分析**：
- CI run 时间是否过长？是否有优化空间？
- 是否应该拆分 CI 为多个 jobs（并行执行）？
- 是否应该增加 staging 环境测试？
- 是否应该增加性能监控（job 数量、成功率、耗时）？

### 10. 用户体验 & 可维护性

**关键问题**：
- 配置文件（YAML）是否易于理解和修改？
- 文档是否完整？是否有遗漏的功能说明？
- 错误处理是否完善？是否有清晰的错误信息？
- 日志是否充分？是否便于调试？
- 代码是否模块化？是否便于扩展？

**深入分析**：
- 是否应该增加 CLI 交互式配置工具？
- 是否应该增加 Web UI（dashboard）？
- 是否应该增加单元测试和集成测试？
- 是否应该增加性能基准测试？

### 11. 成功率分析 (Metrics & Optimization)

**关键问题**：
- 当前的成功率如何？（申请 → 面试 → offer）
- 哪个阶段的转化率最低？
- 是否有系统性问题导致低成功率？
- 是否应该调整策略（如更激进的申请、更保守的筛选）？

**深入分析**：
- 漏斗分析：爬取 → 硬规则 → 评分 → AI → 简历 → 申请 → 面试 → offer
- 哪些公司/职位类型的成功率最高？
- 哪些关键词/技能的职位成功率最高？
- 是否应该根据历史数据调整评分权重？

### 12. 签证与合规 (Visa & Legal)

**关键问题**：
- 是否充分过滤了不提供签证担保的职位？
- Kennismigrant 薪资门槛（€3,122/month）是否在评分中体现？
- 是否应该增加 "erkend referent" 公司列表？
- 是否应该增加签证状态说明（在简历或 cover letter 中）？

**深入分析**：
- 是否有职位因为签证问题被拒？
- 是否应该主动联系 HR 确认签证担保？
- 是否应该增加签证相关的 FAQ？

## 审查输出格式

请按照以下格式输出审查结果：

### 发现的问题

#### 高优先级（Critical）
1. **[问题类别]** 问题描述
   - **影响**：对系统的影响
   - **根本原因**：为什么会有这个问题
   - **建议修复**：具体的修复方案
   - **预期效果**：修复后的预期改进

#### 中优先级（Important）
[同上格式]

#### 低优先级（Nice to have）
[同上格式]

### 改进建议

#### 短期改进（1-2 天可完成）
1. **[改进类别]** 改进描述
   - **收益**：预期的改进效果
   - **成本**：实施的工作量
   - **风险**：潜在的风险

#### 中期改进（1-2 周可完成）
[同上格式]

#### 长期改进（1 个月以上）
[同上格式]

### 数据驱动的洞察

- 当前漏斗统计（如果有数据）
- 瓶颈分析
- 优化建议

### 总体评估

- **系统成熟度**：1-10 分
- **主要优势**：3-5 点
- **主要劣势**：3-5 点
- **最关键的改进方向**：1-3 点

## 审查要求

1. **全面性**：覆盖所有 12 个维度，不要遗漏
2. **深度**：不要只停留在表面，要深入分析根本原因
3. **可操作性**：建议要具体、可执行，不要泛泛而谈
4. **优先级**：明确区分高/中/低优先级，帮助我决定先做什么
5. **数据驱动**：如果有数据支持，请引用具体数字
6. **批判性思维**：不要只说好话，要指出真实的问题
7. **创新性**：不要局限于现有架构，可以提出大胆的改进方案

## 参考资料

- 项目文档：`CLAUDE.md`, `docs/` 目录
- 配置文件：`config/` 目录
- 源代码：`src/`, `scripts/` 目录
- 数据库：`data/jobs.db` (SQLite)
- 记忆文件：`memory/MEMORY.md`

## 特别关注

请特别关注以下几个我最关心的问题：

1. **LinkedIn 搜索是否遗漏了重要职位？** 我担心关键词不够全面。
2. **硬规则是否过于严格？** 我担心误杀了好职位。
3. **AI 评分是否准确？** 我担心 AI 有系统性偏差。
4. **简历质量如何？** 我担心简历不够吸引人。
5. **为什么面试成功率低？** 我拿到面试但经常失败（Python 基础 + behavioral）。
6. **如何提高申请效率？** 目前手动申请很耗时。
7. **如何更好地准备面试？** 目前的 7-phase workflow 是否足够？

---

**请开始深度审查，不要有任何保留。我需要真实、尖锐、可操作的反馈。**
