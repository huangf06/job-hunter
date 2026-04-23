# Job Hunter v3.0 - 执行指南

## 项目概述

自动化求职系统：爬取职位 → 硬规则筛选 → AI 评分+定制简历 → 渲染 PDF → 追踪申请

### v3.0 架构 (2026-03-27)

> 完整架构文档: `docs/plans/2026-03-27-pipeline-block-architecture.md`

```
┌──────────┐    ┌──────────────┐    ┌──────────────────────────────┐
│ Block A  │───▶│   Block B    │───▶│         Block C               │
│  Scrape  │    │ Hard Filter  │    │  C1: Evaluate (评分+brief)    │
│  (jobs)  │    │ (whitelist)  │    │  C2: Tailor (简历定制)        │
└──────────┘    └──────────────┘    │  score >= 5.0 触发 C2         │
                      │             │  Application Brief 替代 CL    │
                 rejected           └──────────────────────────────┘
                      ▼                          │
                 ┌─────────┐                     ▼ ai_score >= 5.0
                 │  SKIP   │          ┌──────────────────────────────┐
                 └─────────┘          │       Block D                │
                                      │  Resume Renderer (Jinja2)    │
                                      │  - 填充 base_template.html   │
                                      │  - 生成 HTML + PDF            │
                                      └──────────────────────────────┘
                                                 │
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │  output/Fei_Huang_*.pdf      │
                                  └──────────────────────────────┘
```

## 核心命令

### 1. 统一抓取职位
```bash
python scripts/scrape.py --all --save-to-db
python scripts/scrape.py --all --profile data_engineering --save-to-db
```
- `--profile`: 仅接受启用中的 profile
- `--save-to-db`: 保存到 SQLite 数据库
- `--dry-run`: 只计算 would-insert，不写库

`--all` 运行 LinkedIn + Greenhouse (主链路)。IamExpat 已冻结，仅保留手动 backfill: `--platform iamexpat`。
目标公司配置: `config/target_companies.yaml`

### 2. 处理职位流水线
```bash
# 完整流程 (导入 → 硬规则筛选)
python scripts/job_pipeline.py --process

# 分步执行
python scripts/job_pipeline.py --import-only   # 只导入
python scripts/job_pipeline.py --filter        # 只筛选
```

### 3. AI 分析与简历生成
```bash
# C1 评分 + application brief (快速，无 bullet library)
python scripts/job_pipeline.py --ai-evaluate

# C2 简历定制 (仅 score >= 5.0 的职位)
python scripts/job_pipeline.py --ai-tailor

# C1 + C2 一起执行 (向后兼容)
python scripts/job_pipeline.py --ai-analyze

# 分析单个职位 (C1+C2)
python scripts/job_pipeline.py --analyze-job JOB_ID
```

可选参数:
- `--min-score N`: 最低分数阈值
- `--limit N`: 最大处理数量

### 4. 本地投递工作流 (推荐)
```bash
# 一键生成简历 + Cover Letter + 启动 checklist server
python scripts/job_pipeline.py --prepare

# 投递完成后，归档已投递、清理跳过的
python scripts/job_pipeline.py --finalize
```

`--prepare` 流程: 同步 DB → 生成简历/CL → 收集待投递 → 生成 HTML checklist → 启动本地 server
`--finalize` 流程: 读取 state.json → 标记 applied/skipped → 归档文件 → 同步 Turso

Repost 检测: `--prepare` 自动检测同 company+title 已投递的职位，在 checklist 中标注 REPOST 警告。

### 5. 查看状态与申请跟踪
```bash
python scripts/job_pipeline.py --stats         # 漏斗统计
python scripts/job_pipeline.py --ready         # 待申请职位 (旧版)
python scripts/job_pipeline.py --generate      # 生成简历 (旧版)
python scripts/job_pipeline.py --mark-applied JOB_ID  # 标记已申请
python scripts/job_pipeline.py --tracker       # 申请状态看板
python scripts/job_pipeline.py --bullet-analytics  # Bullet 转化率分析
```

### 6. 面试调度 (Google Calendar 集成)
```bash
# 推荐最佳面试时间 (结合日历空闲 + 公司 AI 评分 + 三维评分模型)
python scripts/job_pipeline.py --schedule-interview COMPANY --duration 45 --days 14

# 列出所有可用时间段 (适用于 "选你有空的时间" 场景)
python scripts/job_pipeline.py --suggest-availability COMPANY --duration 30

# 首次授权 / 添加 Gmail 权限
python scripts/google_auth.py
```

三维评分模型:
- **候选人状态**: 上午 10:00-11:30 最佳，下午略低
- **面试官状态**: 周二三上午最投入，周一上午在清邮件/开 standup
- **策略加成**: "黄金窗口" = 周二/三 10:00-11:30 双方同时巅峰
- 个人能量曲线可在 `config/ai_config.yaml` → `interview_scheduler.candidate_energy` 调整

### 7. 面试准备 (标准化工作流)

收到面试通知后，使用标准化 7 阶段工作流生成完整面试档案 (~40 KB, ~15,000 字)。

**触发方式:** 用户说 "帮我准备 [公司] 的面试" 或类似请求。

**7 个阶段:**
| 阶段 | 名称 | 操作 | 并行 Agent | 输出 |
|------|------|------|-----------|------|
| 0 | 情报收集 | Google Calendar 查询 + DB 查询 (JD、AI 分析、简历、申请状态) | 0 | 原始数据 |
| 1 | 基础文件 | 创建目录 `YYYYMMDD_Company_Role/`，写入 01 (JD)、02 (AI 分析)、03 (已提交简历) | 0 | 文件 01-03 |
| 2 | 公司调研 | 官网、融资、产品、领导层、Glassdoor、新闻、**GitHub org** | 2-3 | 调研笔记 |
| 3 | 面试官调研 | LinkedIn、论文/出版物、职业轨迹、思维风格 | 1-2 | 面试官画像 |
| 4 | 档案组装 | 写入 04 (公司深度)、05 (面试策略)、06 (速查表)、07 (学历) | 0 | 文件 04-07 |
| 5 | 深度调研 | 公司 GitHub (take-home!)、团队组成、HN/技术论坛、技术博客 | 2-4 | 情报 |
| 6 | 充实 + 简报 | 更新文件、写 08 (take-home 准备)、向用户呈现关键发现 | 0 | 最终档案 |

**面试后:** 创建 `09_post_interview_notes.md` 记录面试经过和反思。

**详细工作流:** `memory/interview_prep_workflow.md` (含检查清单、Agent 提示词、文件模板)
**参考案例:** `interview_prep/20260225_Source_ag_Data_Engineer/00_process_log.md`

**文件结构:**
```
interview_prep/YYYYMMDD_Company_Role/
├── 00_process_log.md               ← 准备过程记录
├── 01_job_description.md           ← 完整 JD + 元数据
├── 02_ai_analysis.md               ← AI 评分、推理、建议
├── 03_submitted_resume.md          ← 已提交简历内容 (+ CL)
├── 04_company_deep_dive.md         ← 公司调研档案
├── 05_interview_strategy.md        ← 叙事策略、Q&A、面试官画像
├── 06_quick_reference.md           ← 面试时的速查表
├── 07_transcript_and_education.md  ← 学历背景
├── 08_take_home_prep.md            ← (多轮面试) 编程作业情报
├── 09_post_interview_notes.md      ← (面试后) 复盘笔记
└── Fei_Huang_Resume.pdf            ← 已提交简历副本
```

**高价值操作 (务必执行):**
- 搜索公司 GitHub org — 经常有公开的 take-home assignment
- 获取 careers page JD — LinkedIn 经常夸大要求 (Source.ag: 10+ 年 → 实际 4+ 年)
- 查找面试官论文/学位论文 — 推断思维风格和价值观
- **主动问用户** 是否与公司使命有个人联系

### 8. CI/CD (GitHub Actions)
流水线自动运行: `.github/workflows/job-pipeline.yml`
- 定时触发: 工作日 2 次 (NL 时间 ~09:37 / ~13:37 CEST)，周末 1 次 (~12:23 CEST)
- 使用 Turso 云数据库，无需本地 DB

## 文件结构

```
job-hunter/
├── scripts/                    # CLI 入口
│   ├── job_pipeline.py             # 主流水线 (统一入口)
│   ├── scrape.py                   # 统一爬虫 CLI
│   ├── pipeline_gaps.py             # 漏斗诊断工具
│   ├── deep_analysis.py            # 深度分析工具
│   ├── resume_visual_diff.py       # 简历可视化对比
│   ├── todoist_manager.py          # Todoist 任务管理
│   ├── google_auth.py              # Google OAuth 授权 (Calendar + Gmail)
│   └── notify.py                   # Telegram 通知 (CI/CD)
│
├── src/                        # 可复用模块
│   ├── __init__.py
│   ├── hard_filter.py               # 硬规则筛选器 (Block B)
│   ├── ai_analyzer.py              # AI 分析器 (Claude)
│   ├── resume_renderer.py          # 简历渲染器 (Jinja2 + Playwright)
│   ├── resume_validator.py         # 简历验证器 (v3.0)
│   ├── resume_visual_diff.py       # 简历可视化对比
│   ├── cover_letter_generator.py   # Cover Letter AI 生成
│   ├── cover_letter_renderer.py    # Cover Letter 渲染
│   ├── checklist_server.py         # 本地 checklist HTTP server
│   ├── google_calendar.py          # Google Calendar REST 客户端 (通用)
│   ├── gmail_client.py             # Gmail IMAP 客户端
│   ├── interview_scheduler.py      # 智能面试调度 (日历+DB+评分)
│   ├── language_guidance.py        # 语言检测辅助
│   ├── template_registry.py        # 模板注册表
│   ├── scrapers/                   # 多平台爬虫模块
│   │   ├── base.py                     # BaseScraper 抽象类
│   │   ├── greenhouse.py               # Greenhouse ATS API
│   │   ├── linkedin.py                 # LinkedIn 编排
│   │   ├── linkedin_browser.py         # LinkedIn 浏览器/会话层
│   │   ├── linkedin_parser.py          # LinkedIn 解析 helpers
│   │   ├── iamexpat.py                 # IamExpat Jobs (Playwright)
│   │   └── registry.py                 # 爬虫注册表
│   └── db/
│       ├── __init__.py
│       └── job_db.py               # SQLite + Turso 云数据库模块
│
├── config/
│   ├── ai_config.yaml          # AI 配置 (模型、阈值、prompt)
│   ├── search_profiles.yaml    # 搜索配置 (LinkedIn + IamExpat)
│   ├── target_companies.yaml   # 目标公司 ATS 配置 (Greenhouse)
│   ├── template_registry.yaml  # 简历模板注册表
│   ├── private/                # 私密配置 (不提交 git)
│   │   └── salary.yaml            # 薪资期望
│   └── base/                   # 基础配置
│       └── filters.yaml            # 硬规则 v2.0
│
├── templates/
│   ├── base_template.html      # 主模板 (Jinja2)
│   ├── cover_letter_template.html  # Cover Letter 模板
│   └── resume_master.html      # 完整参考简历
│
├── assets/
│   ├── bullet_library.yaml     # 已验证的经历库 (51 bullets, v6.0 interview-data rewrite)
│   ├── cover_letter_config.yaml    # Cover Letter 配置
│   └── cl_knowledge_base.yaml      # CL 手写片段库
│
├── data/
│   ├── jobs.db                 # SQLite 数据库 (本地缓存，云端通过 Turso HTTP)
│   └── inbox/                  # 待导入 JSON
│
├── .github/
│   └── workflows/
│       ├── job-pipeline.yml  # CI/CD 自动化流水线
│       └── test.yml                    # pytest on push/PR
│
├── output/                     # 生成的简历
├── ready_to_send/              # --prepare 生成的投递材料 + checklist
├── interview_prep/             # 面试准备档案 (按公司/日期归档)
│   ├── README.md                   # 面试中心 + 工作流说明
│   └── YYYYMMDD_Company_Role/      # 每次面试的完整档案 (文件 00-09)
└── .gitignore
```

## 数据库结构

SQLite 本地数据库 + Turso 云同步 (HTTP 模式，通过 `TursoHTTPClient`)。
设置 `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` 环境变量启用云同步。

| 表名 | 用途 |
|------|------|
| `jobs` | 所有爬取的职位 |
| `filter_results` | 硬规则筛选结果 |
| `job_analysis` | AI 分析结果 + 定制简历 JSON |
| `resumes` | 生成的简历记录 |
| `cover_letters` | Cover Letter 记录 |
| `applications` | 申请状态跟踪 |
| `interview_rounds` | 面试轮次记录 |
| `bullet_versions` | Bullet 内容版本追踪 (id + content_hash) |
| `bullet_usage` | 每份简历使用了哪些 bullet |
| `scrape_watermarks` | 爬虫水位线 (增量抓取) |

**常用表列名 (ad-hoc 查询时直接用，不要猜):**
- `jobs`: id, source, source_id, url, title, company, location, description, posted_date, scraped_at, search_profile, search_query, raw_data, created_at, manual_source
- `job_analysis`: id, job_id, ai_score, skill_match, experience_fit, growth_potential, recommendation, reasoning, tailored_resume, model, tokens_used, analyzed_at, resume_tier, template_id_initial, template_id_final, routing_confidence, routing_override_reason, escalation_reason, routing_payload, c3_decision, c3_confidence, c3_reason
- `applications`: id, job_id, status, applied_at, response_at, interview_at, outcome, notes, updated_at, rejection_reason, rejection_stage
- `cover_letters`: id, job_id, spec_json, custom_requirements, standard_text, short_text, html_path, pdf_path, tokens_used, created_at

常用视图: `v_funnel_stats`, `v_pending_jobs`, `v_high_score_jobs`, `v_ready_to_apply`, `v_bullet_conversion`

查看统计:
```python
from src.db.job_db import JobDatabase
db = JobDatabase()
print(db.get_funnel_stats())
```

### Ad-hoc 数据库查询 (重要)

**正确方式** — 用 `db.execute()` 返回 `list[dict]`:
```python
db = JobDatabase()
rows = db.execute("SELECT id, title, company FROM jobs LIMIT 5")
for r in rows:
    print(r['title'], r['company'])
```

**或用上下文管理器** `db._get_conn()` 获取 connection (支持 fetchone/fetchall):
```python
with db._get_conn() as conn:
    row = conn.execute("SELECT COUNT(*) as c FROM jobs").fetchone()
    print(row['c'])
```

**不存在的 API (不要用):** `db.conn`, `db._get_connection`, `db._get_connection()`, `db.cursor()`

完整漏斗报告: `python scripts/pipeline_gaps.py`

## 日常工作流

1. **每日抓取** (建议早上):
   ```bash
   python scripts/scrape.py --all --save-to-db
   ```

2. **处理新职位**:
   ```bash
   python scripts/job_pipeline.py --process
   ```

3. **AI 分析高分职位** (消耗 token):
   ```bash
   python scripts/job_pipeline.py --ai-analyze --limit 10
   ```

4. **一键准备投递材料** (生成简历/CL + 启动 checklist):
   ```bash
   python scripts/job_pipeline.py --prepare
   ```

5. **投递完成后归档**:
   ```bash
   python scripts/job_pipeline.py --finalize
   ```

6. **收到面试通知 → 准备面试档案** (详见第 7 节):
   - 触发: "帮我准备 XX 公司的面试"
   - 输出: `interview_prep/YYYYMMDD_Company_Role/` 下 8-9 个文件
   - 面试后: 补充 `09_post_interview_notes.md`

7. **每日 Live Coding 练习** (1.5-2h, P0 优先级):
   - 独立项目: `C:\Users\huang\github\python-dojo`
   - 平台: NeetCode 150 (neetcode.io) + LeetCode
   - 重点: Arrays & Hashing → Two Pointers → Sorting (前 2 周)

## 配置说明

### AI 配置 (`config/ai_config.yaml`)
- `models.analyzer`: Claude 用于智能分析
- `thresholds.ai_score_generate_resume`: 生成简历的最低 AI 分 (默认 5.0)
- `budget.daily_limit`: 每日 token 预算

### 硬规则筛选 (`config/base/filters.yaml`)
- 6 条硬拒绝规则 (whitelist-only: 荷兰语检测、白名单角色、标题技术栈等)
- 通过 Hard Filter 的职位进入 C1 评分，score >= 5.0 进入 C2 简历定制

## 不可违反的工程约束

### LinkedIn 爬虫: scroll-to-reveal 是必需的

LinkedIn 搜索结果使用 occludable DOM — 只有滚动进 viewport 的 card 才会加载实际内容 (title/company/url)，未滚动到的 card 是空壳。**任何对 `linkedin_browser.py` 的重构都必须保留 `_scroll_to_reveal_all_cards()` 逻辑** (在 `_extract_cards()` 之前调用)，否则每个 query 只能抓到 ~7 条而非全部 25+ 条。

历史教训: 2026-03-27 重构删掉了旧的 `scroll_into_view_if_needed()` 逻辑，导致近一个月丢失 ~70% 的搜索结果，2026-04-23 才发现并修复。

验证方法: 跑 `scrape.py --dry-run`，检查 diagnostics 中 `cards_found` 是否接近手动搜索数量 (通常 20-30)。如果只有个位数 (~7)，说明滚动逻辑丢失。

## 注意事项

- LinkedIn cookies 在 `config/linkedin_cookies.json`
- 数据文件 (*.db, *.json) 不提交到 git
- AI 分析消耗 token，注意预算控制
- Playwright PDF 需要: `playwright install chromium`
- Turso 云同步: 设置 `.env` 中的 `TURSO_DATABASE_URL` 和 `TURSO_AUTH_TOKEN`
- Turso 已切换为 HTTP 模式 (不再使用 libsql embedded replica)，如遇连接问题可取消 Turso 环境变量回退到本地 SQLite
- Google Calendar: token 文件在 `~/.config/google-calendar-mcp/tokens.json`，与 MCP 共享 (原子读写)
- Google OAuth 凭据在 `~/.config/gcp-oauth.keys.json`，首次使用或添加 scope 时运行 `python scripts/google_auth.py`
- 面试调度评分可通过 `config/ai_config.yaml` → `interview_scheduler.candidate_energy` 调整个人能量曲线
