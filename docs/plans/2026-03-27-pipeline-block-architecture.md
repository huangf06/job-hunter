# Pipeline Block Architecture v3.0

**Date**: 2026-03-27
**Status**: Approved
**Decision**: Scheme B → v3.1 — Hard Filter whitelist-only, AI split C1 (evaluate) + C2 (tailor)

---

## 总览

```
┌────────────┐     ┌────────────┐     ┌──────────────────┐     ┌────────────┐     ┌────────────┐     ┌────────────┐
│  Block A   │────▶│  Block B   │────▶│    Block C        │────▶│  Block D   │────▶│  Block E   │────▶│  Block F   │
│  Scrape    │     │Hard Filter │     │  AI Evaluate      │     │  Render    │     │  Deliver   │     │  Notify    │
│            │     │            │     │                    │     │            │     │            │     │            │
│ LinkedIn   │     │ 6 条硬规则  │     │ C1: 评分+brief    │     │ HTML→PDF   │     │ Prepare    │     │ Telegram   │
│ Greenhouse │     │ whitelist  │     │ C2: 简历定制       │     │ Jinja2 +   │     │ Apply      │     │ Discord    │
│ (IamExpat) │     │ only       │     │ 两步 AI 调用      │     │ Playwright │     │ Finalize   │     │            │
└────────────┘     └────────────┘     └──────────────────┘     └────────────┘     └────────────┘     └────────────┘
     ✅ 完成           ✅ 完成              待重建                  待重建              待重建            待重建
```

**设计前提**:
- AI 成本模型: Claude Code Max 5x ($100/month flat subscription), 边际成本 ≈ 0
- 运行环境: GitHub Actions CI, 使用 `anthropics/claude-code-action@v1` + Max plan 认证
- 日均量: ~40 scraped → ~15-20 通过 Hard Filter → 全部进 AI 分析
- 关键决策: **删除 Rule Score (旧 Block B-2)**，因为 flat subscription 下 "省 token" 的理由不成立

---

## Block A: Scrape (已完成)

**职责**: 从多平台抓取职位信息，写入数据库。

**状态**: ✅ 已重建完成

**入口**: `python scripts/scrape.py --all --save-to-db`

**核心契约**:
- 统一 `BaseScraper.run()` 接口，返回 `ScrapeReport`
- `ScrapeReport` 携带 `diagnostics` 对象（elapsed_seconds, session_status, per-query summaries）
- URL-hash 去重 via `JobDatabase.generate_job_id()`

**平台**:
| 平台 | 模块 | 状态 |
|------|------|------|
| LinkedIn | `src/scrapers/linkedin.py` + `linkedin_browser.py` + `linkedin_parser.py` | 主链路 |
| Greenhouse | `src/scrapers/greenhouse.py` | 主链路 |
| IamExpat | `src/scrapers/iamexpat.py` | 冻结，仅手动 backfill |

**文件**:
- `src/scrapers/base.py` — BaseScraper 抽象类, 黑名单过滤, URL-hash 去重, dry-run, 结构化报告
- `src/scrapers/registry.py` — 平台注册表和别名 (`ats`, `all`)
- `scripts/scrape.py` — CLI 入口
- `config/search_profiles.yaml` — 搜索配置
- `config/target_companies.yaml` — 目标公司 ATS 配置

**输出**: `jobs` 表 (id, source, url, title, company, location, description, ...)

**运维文档**:
- `docs/runbooks/block-a-operations.md`
- `docs/runbooks/block-a-checklist.md`

---

## Block B: Hard Filter

**职责**: 对 Block A 产出的职位做二元 pass/reject 判定。纯规则，CPU-only，零成本。

### 核心设计原则: Block B vs Block C 分工

> **Block B 只拦"100% 确定不要的"，灰色地带一律放给 Block C (AI) 打分。**

- Block B 是粗筛，**宁可放过，不可误杀**。一个 "Vision Systems Engineer" 漏进来没关系，AI 会给低分自然淘汰。
- Block B 适合做的：语言检测、公司黑名单、头衔黑名单等**精确业务逻辑**，正则比 AI 更快、更可靠、更可控。
- Block B 不该做的：判断 "Marketing Data Analyst 到底是 marketing 岗还是 data 岗" — 这是语义理解，交给 AI。
- 收紧白名单 = 增加误杀风险，违反分工原则。宽松白名单 + AI 打分是正确的漏斗形态。

### 规则集

**入口**: `python scripts/job_pipeline.py --filter`

#### 规则优先级表 (v3.0 — whitelist-only)

| # | 规则名 | 类型 | 逻辑 |
|---|--------|------|------|
| 0 | 荷兰语 JD 检测 | word_count | ≥8 个荷兰语指示词 → reject |
| 1 | 荷兰语要求 | regex | "dutch required/mandatory/native" 等 → reject |
| 2 | 非目标角色 | title_check | 白名单 only: 标题必须含目标关键词 (见下方) |
| 3 | 错误技术栈 | tech_stack | 标题模式 only (无正文关键词计数) |
| 4 | 仅自由职业 | regex | "zzp", "freelance only" 等 (有 "full-time" 例外) |
| 5 | 极低薪酬 | regex | "$1000-1500/month" 等 |
| 7 | 高管角色 | title_check | "director/vp/head of/cto" 等 (senior data analyst 等例外) |

**v3.0 删除的规则**: specific_tech_experience, experience_too_high, location_restricted — 这些语义判断移至 Block C (AI)。

#### 非目标角色 (规则 2) — 白名单设计

v3.0 简化: 只保留白名单，删除所有 reject patterns。

**白名单** (`title_must_contain_one_of`): 标题必须含至少一个目标关键词，否则拒绝。
- 27 个关键词: data, dataflow, machine learning, ml, ai, genai, artificial intelligence, computer vision, machine vision, vision, python, quant, quantitative, analytics, bi, scientist, research, researcher, algorithm, deep learning, nlp, llm, mlops, software, backend, infrastructure, platform, pipeline, applied scientist

**设计理由**: 旧的三层设计 (硬拒绝/软拒绝/白名单) 在判断边界情况时过于复杂 (如 "Data Security Engineer" 是安全还是数据?)。whitelist-only 设计: 有目标关键词就放行，让 AI 判断具体匹配度。

#### C#/.NET 正则边界处理

`filters.yaml` 中的 `title_patterns` 使用原始正则，需要特殊处理非 word 字符:
- `.net`: 用 `\.net(?!\w)` — 前面不加 `\b` (因为 `.` 是 non-word char，`\b` 在 non-word→non-word 间不匹配)
- `c#`: 用 `\bc#(?!\w)` — 后面用 `(?!\w)` 替代 `\b` (因为 `#` 是 non-word char)
- 这与 `keyword_boundary_pattern()` helper 的逻辑一致

**额外过滤**:
- 公司黑名单 (从 `search_profiles.yaml` 加载)
- 头衔黑名单 (intern/trainee/student)
- 数据不足 (标题空、描述空、描述 <50 字符)

**输入**: `jobs` 表中未筛选的职位
**输出**: `filter_results` 表 (job_id, passed, reject_reason, matched_rules)

**配置**: `config/base/filters.yaml`
**代码**: `src/hard_filter.py`
**测试**: `tests/test_hard_filter.py` (61 tests)

**性能**: <1 秒处理 500 个职位，纯 CPU

### 与旧版的区别

**删除**: Rule Score (旧 Block B-2)。原因:
1. Rule Score 是 AI Score 的劣化近似——两者评估相同维度（技能匹配、经验水平），但 Rule Score 用关键词计数，AI 用语义理解
2. Rule Score 存在假阴性风险——JD 用不同术语时 (如 "data pipelines" 而非 "spark")，好职位可能被卡在 3.0 门槛外
3. Flat subscription 下 "省 token" 的经济理由不成立
4. 删除后不再需要维护 `scoring.yaml` 中 80+ 关键词的权重

**删除的文件/配置**:
- `config/base/scoring.yaml` → `config/archive/scoring.yaml.archived`
- `ai_scores` 表 — 不再写入新数据（保留旧数据做兼容）
- `job_pipeline.py` 中的 `_calculate_score()`, `score_jobs()` 方法
- `job_db.py` 中的 `save_score()`, `get_unscored_jobs()`, `clear_scores()` 方法

---

## Block C: AI Evaluate + Tailor (v3.1 — two-step)

**职责**: 对通过 Hard Filter 的职位做**两步 AI 调用**:
1. **C1 Evaluate**: 评分 + Application Brief (短 prompt, 无 bullet library)
2. **C2 Tailor**: 简历定制 (长 prompt, 含 bullet library, 仅 score >= 4.0)

**设计原则**: 分步执行 — C1 快速筛选，C2 仅对值得投递的职位生成简历。Cover Letter 被 Application Brief (素材包) 取代，合并在 C1 输出中。

**入口**:
- `python scripts/job_pipeline.py --ai-evaluate` — C1 only
- `python scripts/job_pipeline.py --ai-tailor` — C2 only
- `python scripts/job_pipeline.py --ai-analyze` — C1 + C2 sequentially

### C1: Evaluate (评分 + Application Brief)

**模型**: Claude Code CLI (`claude -p`)

**Prompt 输入**:
- 候选人资料摘要
- Hard Reject Signals (让 AI 也拦截 Block B 漏过的语义问题)
- 评分标准和校准指导
- JD 全文 (截断到 10,000 字符)

**Prompt 输出** (structured JSON):
```json
{
  "scoring": {
    "overall_score": 7.5,
    "skill_match": 8.0,
    "experience_fit": 7.0,
    "growth_potential": 7.5,
    "recommendation": "APPLY",
    "reasoning": "..."
  },
  "application_brief": {
    "hook": "strongest connection",
    "key_angle": "main selling point",
    "gap_mitigation": "biggest gap + mitigation",
    "company_connection": "personal connection or null"
  }
}
```

### C2: Tailor Resume (简历定制)

**仅对 C1 score >= 4.0 的职位运行。**

**Prompt 输入**:
- 候选人资料 + Bullet Library 全文
- JD 全文
- C1 分析结果 (score, reasoning, application_brief) 作为上下文

**Prompt 输出** (structured JSON):
```json
{
  "tailored_resume": {
    "bio": { "role_title": "...", "years": 6, ... },
    "experiences": [ { "company": "...", "bullets": ["bullet_id_1", ...] }, ... ],
    "projects": [ { "name": "...", "bullets": ["bullet_id_1", ...] }, ... ],
    "skills": [ { "category": "...", "skills_list": "..." }, ... ]
  },
  "cover_letter": {
    "needed": true,
    "spec": {
      "paragraphs": [ { "prose": "...", "evidence_ids": ["bullet_id"] } ],
      "short_text": "..."
    }
  }
}
```

### 推荐阈值

| 档位 | overall_score | 动作 |
|------|--------------|------|
| APPLY_NOW | >= 7.0 | 高优先级，立即生成简历 |
| APPLY | >= 5.0 | 正常申请 |
| MAYBE | >= 3.0 | 待定，不自动生成简历 |
| SKIP | < 3.0 | 跳过 |

### Validation (内嵌在 Block C 输出后)

AI 输出后立即运行 `ResumeValidator`:
- 标题白名单检查
- 技能排除列表检查
- 技能类别白名单
- 结构完整性 (2+ 经历, 3+ 技能类别, 1+ 项目)
- Bio 禁用词自动替换

验证通过的才写入 `job_analysis` 表。验证失败的标记 sentinel 防止重复分析。

**输入**: Hard Filter 通过的职位 (`filter_results.passed = true`)
**输出**: `job_analysis` 表 (ai_score, skill_match, experience_fit, growth_potential, recommendation, reasoning, tailored_resume JSON, cover_letter spec)

**配置**: `config/ai_config.yaml`

**性能**: ~5-30 秒/职位 (取决于模型和调用方式)

### 与旧版的区别

1. **不再需要 rule_score 门控**: Hard Filter 通过 = 直接进 AI
2. **合并 CL 生成**: 旧版 CL 是单独的 `cover_letter_generator.py` 做第二次 AI 调用，新版合并到同一次调用
3. **合并 CL needed 判断**: AI 根据平台类型判断是否需要 CL (LinkedIn Easy Apply 通常不需要)

---

## Block D: Render

**职责**: 将 Block C 产出的 JSON spec 渲染为 PDF 文件。纯本地、无状态、零 AI 调用。

**设计原则**: Render 只做模板填充 + PDF 生成，不做任何评分或内容决策。输入是确定性的 JSON，输出是确定性的 PDF。

**入口**: `python scripts/job_pipeline.py --generate`

### 渲染流程

```
job_analysis.tailored_resume (JSON)
  → Jinja2 填充 base_template.html
  → Post-render QA (页数估算, 空 bullet 检查, HTML 转义检查)
  → Playwright (Chromium headless) → PDF
  → 输出到 output/ 和 ready_to_send/

job_analysis.cover_letter (JSON, 如果 needed=true)
  → Jinja2 填充 cover_letter_template.html
  → Playwright → PDF
  → 同时输出 TXT 版本 (用于粘贴到申请表)
  → 与简历放在同一 ready_to_send/ 目录
```

### 产物

| 产物 | 格式 | 存储位置 | 用途 |
|------|------|---------|------|
| Resume PDF | A4 PDF | `output/` + `ready_to_send/YYYYMMDD_Company/` | 投递 |
| Resume HTML | HTML | `output/` | 调试/预览 |
| Cover Letter PDF | A4 PDF | `ready_to_send/YYYYMMDD_Company/` | 投递 |
| Cover Letter TXT | 纯文本 | `ready_to_send/YYYYMMDD_Company/` | 粘贴到表单 |

**输入**: `job_analysis` 表中 recommendation 为 APPLY 或 APPLY_NOW 的记录
**输出**: `resumes` 表 + `cover_letters` 表 (file paths), 文件系统上的 PDF/HTML/TXT

**依赖**:
- `templates/base_template.html` — 简历 Jinja2 模板
- `templates/cover_letter_template.html` — CL Jinja2 模板
- `assets/bullet_library.yaml` — bullet ID → 文本解析
- Playwright + Chromium — PDF 生成

**性能**: ~1-2 秒/职位 (Playwright PDF 渲染)

---

## Block E: Deliver

**职责**: 管理投递材料的生命周期——从 "准备好" 到 "已投递" 到 "有结果"。

**设计原则**: Block E 是人机交互的边界。Pipeline 自动生成材料，但投递决策由人做。

### 子流程

#### E.1 Prepare (生成投递清单)

```
同步 DB → 收集待投递职位 → 生成 HTML checklist → 启动本地 server (或上传到云端)
```

- 收集 `v_ready_to_apply` 视图中的所有职位
- 丰富元数据: repost 检测 (同 company+title 已投递), rejection 历史
- 生成 `apply_checklist.html` + `state.json`
- 本地模式: 启动 HTTP server (localhost:8234)
- CI 模式 (未来): 上传到 Cloudflare R2, 通过 Telegram 发送链接

#### E.2 Apply (人工操作)

- 用户在 checklist 中勾选 applied/skipped
- 状态通过 POST 写入 `state.json`
- 这一步完全手动

#### E.3 Finalize (归档)

```
读取 state.json → 标记 applied/skipped → 移动文件夹 → 检测编辑过的 CL → 同步 DB
```

- Applied: 写入 `applications` 表, 文件移到 `_applied/`
- Skipped: 写入 `applications` 表, 文件移到 `_skipped/`
- 检测手动编辑的 CL → 提取到 `_edited_cls/` (用于改进知识库)

#### E.4 Track (状态跟踪)

- 申请状态机: `applied → no_response_14d → ghosted`
- 手动更新: `--update-status JOB_ID phone_screen`
- 自动转换: CI 每次运行时检查超时

**输入**: Block D 的产物 (ready_to_send/ 目录下的 PDF)
**输出**: `applications` 表 (status, applied_at, outcome, ...)

**目录结构**:
```
ready_to_send/
├── YYYYMMDD_Company/           ← 待投递 (Prepare 生成)
│   ├── Fei_Huang_Resume.pdf
│   ├── Fei_Huang_Cover_Letter.pdf
│   └── Fei_Huang_Cover_Letter.txt
├── _applied/                   ← 已投递 (Finalize 归档)
├── _skipped/                   ← 已跳过 (Finalize 归档)
├── _edited_cls/                ← 手动编辑的 CL (Finalize 提取)
├── state.json                  ← 临时状态 (Prepare→Finalize 之间)
└── apply_checklist.html        ← 临时 UI (Prepare→Finalize 之间)
```

---

## Block F: Notify

**职责**: Pipeline 运行后发送结果摘要通知。

**设计原则**: 通知是只读的旁路操作，不影响 pipeline 主流程。即使通知失败，pipeline 依然成功。

### 渠道

| 渠道 | 模块 | 状态 |
|------|------|------|
| Telegram | `scripts/notify.py` | 主力，CI 每次运行后发送 |
| Discord | `scripts/notify_discord.py` | 可用但未集成 |

### Telegram 通知内容

```
📊 Pipeline Run 2026-03-27 08:23

Scraped: 42 new jobs
Filtered: 18 passed
AI Analyzed: 15
Resumes Ready: 8

Top matches:
• Company A — Senior DE — 8.2 ⭐
• Company B — MLE — 7.1
• Company C — Data Engineer — 6.8

📁 Materials ready for review
```

**触发**: CI workflow 最后一步 (`if: always()`, continues-on-error)

**数据来源**: 直接查询 DB (funnel stats, ready_to_apply, today's analysis)

### 未来扩展 (Phase 3)

- 周报: 每周日发送活跃申请统计
- 月报: 每月 1 号发送转化率分析 (按 AI 分数段)
- 状态更新: 通过 Telegram 命令更新申请状态 (`/status COMPANY_NAME phone_screen`)

---

## Database 基础层

**职责**: 为所有 Block 提供统一的数据持久化。

### 传输层

| 环境 | 传输方式 | 说明 |
|------|---------|------|
| CI | Turso HTTP | `POST /v3/pipeline`, 无状态, 每次 execute = 一次 HTTP 请求 |
| 本地 (有网) | Turso HTTP | 同 CI |
| 本地 (离线) | SQLite | 直接 `sqlite3.connect()`, WAL 模式 |

选择逻辑: `DB_TRANSPORT=http|sqlite` 环境变量，或自动检测 `TURSO_DATABASE_URL`。

### 表结构

| 表名 | 所属 Block | 用途 |
|------|-----------|------|
| `jobs` | A (Scrape) | 所有抓取的职位 |
| `scrape_watermarks` | A (Scrape) | 增量抓取游标 |
| `filter_results` | B (Hard Filter) | 筛选结果 (pass/reject + 原因) |
| `job_analysis` | C (AI Evaluate) | AI 评分 + tailored_resume JSON + CL spec |
| `resumes` | D (Render) | 生成的简历文件路径 |
| `cover_letters` | D (Render) | 生成的 CL 文件路径 |
| `applications` | E (Deliver) | 申请状态跟踪 |

**计划删除/归档**:
| 表名 | 原因 |
|------|------|
| `ai_scores` | Rule Score 产物，不再写入新数据。保留旧数据做兼容查询 |
| `feedback` | 从未使用 |
| `config_snapshots` | 从未使用 |

**视图** (4 个):
- `v_pending_jobs` — 未处理的职位 (所有 join)
- `v_high_score_jobs` — AI 高分职位
- `v_ready_to_apply` — 有简历 + 无申请记录的职位
- `v_funnel_stats` — 漏斗统计

### 核心模块

- `src/db/job_db.py` — `JobDatabase` 类 (75 个方法)
- `TursoHTTPClient` — httpx HTTP 客户端 (~50 行)

---

## Block 间数据流

```
                    jobs 表                filter_results 表         job_analysis 表
                  ┌─────────┐             ┌───────────────┐        ┌───────────────┐
Block A ────写入──▶│ id      │  Block B ──▶│ job_id        │ Block C│ job_id        │
(Scrape)          │ title   │  (Filter)   │ passed        │(AI)───▶│ ai_score      │
                  │ company │             │ reject_reason │        │ tailored_resume│
                  │ desc    │             └───────────────┘        │ cover_letter   │
                  │ url     │                                      └───────────────┘
                  └─────────┘                                             │
                                                                          ▼
                                          resumes 表              cover_letters 表
                                         ┌──────────┐           ┌───────────────┐
                              Block D ──▶│ job_id   │  Block D─▶│ job_id        │
                              (Render)   │ pdf_path │  (Render) │ pdf_path      │
                                         │submit_dir│           │ short_text    │
                                         └──────────┘           └───────────────┘
                                                │                       │
                                                ▼                       ▼
                                         applications 表     ready_to_send/ 文件
                                        ┌──────────────┐
                             Block E ──▶│ job_id       │
                             (Deliver)  │ status       │
                                        │ applied_at   │
                                        │ outcome      │
                                        └──────────────┘
                                                │
                                                ▼
                                         Block F (Notify)
                                        读取 funnel stats
                                        发送 Telegram 摘要
```

## Block 依赖关系

```
A (Scrape) ──▶ B (Hard Filter) ──▶ C (AI Evaluate) ──▶ D (Render) ──▶ E (Deliver)
                                                                            │
                                                                            ▼
                                                                       F (Notify)
```

- A → B: 严格顺序，B 只处理 A 写入的新职位
- B → C: 严格顺序，C 只处理 B 通过的职位
- C → D: 严格顺序，D 只渲染 C 产出的 APPLY/APPLY_NOW 职位
- D → E: 松耦合，E.Prepare 收集 D 的产物但可以独立运行
- E → F: 松耦合，F 读取 DB 统计但不依赖 E 的具体执行
- F: 可以在任意时间点独立运行

## CI/CD 执行序列

```yaml
# GitHub Actions: job-pipeline-optimized.yml
# 触发: 工作日 2x, 周末 1x

steps:
  - Block A: scrape.py --all --save-to-db
  - Block B: job_pipeline.py --filter
  - Block C: job_pipeline.py --ai-analyze        # Claude Code Action + Max plan
  - Block D: job_pipeline.py --generate           # Playwright headless
  - Block F: notify.py --status success/failure   # Telegram 摘要
  # Block E: 手动触发 (--prepare / --finalize)
```

---

## 重建优先级

| 顺序 | Block | 复杂度 | 依赖 | 说明 |
|------|-------|--------|------|------|
| ✅ | A (Scrape) | 高 | 无 | 已完成 |
| ✅ | B (Hard Filter) | 低 | A | 已完成：提取 src/hard_filter.py，删除 Rule Score，归档 scoring.yaml |
| 2 | C (AI Evaluate) | 高 | B | 核心改造：合并评分+简历+CL 为一次调用，接入 Claude Code CLI |
| 3 | D (Render) | 中 | C | 更新 HTML 模板，CL 渲染逻辑调整 |
| 4 | E (Deliver) | 中 | D | Prepare/Finalize 流程基本保留，状态跟踪增强 |
| 5 | F (Notify) | 低 | 全部 | 更新通知内容模板 (删除 rule score 相关字段) |
| 并行 | DB | 中 | 无 | Turso HTTP 清理、删除 ai_scores 写入、清理死代码 |
