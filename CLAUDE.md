# Job Hunter v2.0 - 执行指南

## 项目概述

自动化求职系统：爬取职位 → 硬规则筛选 → 规则评分 → AI 分析 → 生成定制简历 → 追踪申请

### v2.0 架构 (2026-02-05)

```
┌──────────┐    ┌──────────────┐    ┌──────────────┐
│  Scrape  │───▶│ Hard Filter  │───▶│ Rule PreScore│
│  (jobs)  │    │  (v2.0)      │    │   (v2.0)     │
└──────────┘    └──────────────┘    └──────────────┘
                      │                   │
                 rejected             rule_score >= 3.0
                      ▼                   ▼
                 ┌─────────┐      ┌──────────────────────────────┐
                 │  SKIP   │      │  AI Analyzer (Claude Opus)   │
                 └─────────┘      │  - 评分 (skill_match, etc)   │
                                  │  - 输出 tailored resume JSON  │
                                  └──────────────────────────────┘
                                             │
                                             ▼ ai_score >= 5.0
                                  ┌──────────────────────────────┐
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

### 1. 爬取 LinkedIn 职位
```bash
python scripts/linkedin_scraper_v6.py --profile ml_data --save-to-db --cdp
```
- `--profile`: 搜索配置 (ml_data, backend_data, quant)
- `--save-to-db`: 保存到 SQLite 数据库 (默认不保存)
- `--cdp`: 连接已有浏览器 (Chrome 端口 9222)

### 2. 处理职位流水线
```bash
# 完整流程 (导入 → 筛选 → 规则评分)
python scripts/job_pipeline.py --process

# 分步执行
python scripts/job_pipeline.py --import-only   # 只导入
python scripts/job_pipeline.py --filter        # 只筛选
python scripts/job_pipeline.py --score         # 只规则评分
```

### 3. AI 分析与简历生成
```bash
# AI 分析高分职位 (调用 Claude Opus)
python scripts/job_pipeline.py --ai-analyze

# 为 AI 高分职位生成简历 + Cover Letter
python scripts/job_pipeline.py --generate

# 分析单个职位
python scripts/job_pipeline.py --analyze-job JOB_ID
```

可选参数:
- `--min-score N`: 最低分数阈值
- `--limit N`: 最大处理数量 (默认 50)

### 4. 查看状态与申请跟踪
```bash
python scripts/job_pipeline.py --stats         # 漏斗统计
python scripts/job_pipeline.py --ready         # 待申请职位
python scripts/job_pipeline.py --mark-applied JOB_ID  # 标记已申请
python scripts/job_pipeline.py --tracker       # 申请状态看板
```

### 5. CI/CD (GitHub Actions)
流水线自动运行: `.github/workflows/job-pipeline.yml`
- 定时触发: 每日自动爬取 + 处理 + AI 分析
- 使用 Turso 云数据库，无需本地 DB

## 文件结构

```
job-hunter/
├── scripts/                    # CLI 入口
│   ├── job_pipeline.py             # 主流水线 (统一入口)
│   ├── linkedin_scraper_v6.py      # LinkedIn 爬虫
│   └── job_parser.py               # JD 解析器
│
├── src/                        # 可复用模块
│   ├── __init__.py
│   ├── ai_analyzer.py              # AI 分析器 (Claude Opus)
│   ├── resume_renderer.py          # 简历渲染器 (Jinja2 + Playwright)
│   ├── resume_validator.py         # 简历验证器 (v3.0)
│   └── db/
│       ├── __init__.py
│       └── job_db.py               # SQLite + Turso 云数据库模块
│
├── config/
│   ├── ai_config.yaml          # AI 配置 (模型、阈值、prompt)
│   ├── search_profiles.yaml    # 搜索配置
│   └── base/                   # 基础配置
│       ├── filters.yaml            # 硬规则 v2.0
│       └── scoring.yaml            # 评分规则 v2.0
│
├── templates/
│   ├── base_template.html      # 主模板 (Jinja2)
│   ├── cover_letter_template.html  # Cover Letter 模板
│   └── resume_master.html      # 完整参考简历
│
├── assets/
│   ├── bullet_library.yaml     # 已验证的经历库 (核心)
│   └── cover_letter_config.yaml    # Cover Letter 配置
│
├── data/
│   ├── jobs.db                 # SQLite 数据库 (Turso embedded replica)
│   └── inbox/                  # 待导入 JSON
│
├── .github/
│   └── workflows/
│       └── job-pipeline.yml    # CI/CD 自动化流水线
│
├── output/                     # 生成的简历
└── archive/                    # 归档的旧代码
```

## 数据库结构

SQLite 本地数据库 + Turso 云同步 (embedded replica 模式)。
设置 `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` 环境变量启用云同步。

| 表名 | 用途 |
|------|------|
| `jobs` | 所有爬取的职位 |
| `filter_results` | 硬规则筛选结果 |
| `ai_scores` | 规则评分结果 |
| `job_analysis` | AI 分析结果 + 定制简历 JSON |
| `resumes` | 生成的简历记录 |
| `cover_letters` | Cover Letter 记录 |
| `applications` | 申请状态跟踪 |

查看统计:
```python
from src.db.job_db import JobDatabase
db = JobDatabase()
print(db.get_funnel_stats())
```

## 日常工作流

1. **每日爬取** (建议早上):
   ```bash
   python scripts/linkedin_scraper_v6.py --profile ml_data --save-to-db
   ```

2. **处理新职位**:
   ```bash
   python scripts/job_pipeline.py --process
   ```

3. **AI 分析高分职位** (消耗 token):
   ```bash
   python scripts/job_pipeline.py --ai-analyze --limit 10
   ```

4. **生成简历 + Cover Letter**:
   ```bash
   python scripts/job_pipeline.py --generate
   ```

5. **查看待申请**:
   ```bash
   python scripts/job_pipeline.py --ready
   ```

## 配置说明

### AI 配置 (`config/ai_config.yaml`)
- `models.analyzer`: Claude Opus 用于智能分析
- `thresholds.rule_score_for_ai`: 进入 AI 分析的最低规则分 (默认 3.0)
- `thresholds.ai_score_generate_resume`: 生成简历的最低 AI 分 (默认 5.0)
- `budget.daily_limit`: 每日 token 预算

### 评分阈值 (`config/base/scoring.yaml`)
- `apply_now`: >= 7.0 (高优先级)
- `apply`: >= 5.5 (正常申请)
- `maybe`: >= 4.0 (待定)
- `skip`: < 4.0 (跳过)

## 注意事项

- LinkedIn cookies 在 `config/linkedin_cookies.json`
- 数据文件 (*.db, *.json) 不提交到 git
- AI 分析消耗 token，注意预算控制
- 归档代码在 `archive/`
- Playwright PDF 需要: `playwright install chromium`
- Turso 云同步: 设置 `.env` 中的 `TURSO_DATABASE_URL` 和 `TURSO_AUTH_TOKEN`
- Windows 上 libsql embedded replica 有已知栈溢出 bug，如遇崩溃可取消 Turso 环境变量回退到本地 SQLite

## 归档内容 (v41 → v2.0)

以下组件已归档到 `archive/deprecated_v41/`:
- `role_classifier.py` → 被 AI Analyzer 替代
- `content_engine.py` → 被 AI Analyzer 替代
- `job_hunter_v42.py` → 功能迁移到 job_pipeline.py
- `templates/ml_engineer.html` 等 → 合并到 base_template.html
- `assets/bullet_library_simple.yaml` → 使用完整版
