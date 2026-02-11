# GitHub Actions 自动化 Pipeline 设计

> 日期: 2026-02-11
> 状态: 待实现

## 目标

将职位爬取 → 筛选 → 评分 → AI 分析的全流程部署到 GitHub Actions，数据通过 Turso 云数据库持久化。简历生成保留在本地执行。

## 架构

```
┌─────────────────────────────────────────────────┐
│  GitHub Actions (ubuntu-latest, 定时/手动)       │
│                                                  │
│  1. Playwright headless → LinkedIn 爬取           │
│  2. Import JSON → Turso 云数据库                  │
│  3. Hard Filter → Rule Score                     │
│  4. AI Analyze (Claude Opus API)                 │
│                                                  │
│  所有数据写入 Turso ↕ 云同步                      │
└─────────────────────────────────────────────────┘
                    ↕ Turso sync
┌─────────────────────────────────────────────────┐
│  本地                                            │
│                                                  │
│  - Turso embedded replica 自动同步               │
│  - python job_pipeline.py --generate  (本地渲染)  │
│  - python job_pipeline.py --ready     (查看待申请) │
└─────────────────────────────────────────────────┘
```

## GitHub Secrets

| Secret | 用途 |
|--------|------|
| `LINKEDIN_COOKIES` | `li_at` cookie 值（过期后手动更新） |
| `ANTHROPIC_API_KEY` | Claude API key |
| `ANTHROPIC_BASE_URL` | API proxy 地址 |
| `TURSO_DATABASE_URL` | `libsql://xxx.turso.io` |
| `TURSO_AUTH_TOKEN` | Turso 认证 token |

## 触发方式

### 定时触发 (Cron)
- `0 8 * * 1-5` — 工作日 UTC 8:00（荷兰时间 9:00/10:00）
- 自动跑全部启用的 profile（ml_data, backend_data, quant）

### 手动触发 (workflow_dispatch)
可选参数：
- `profile`: 搜索配置（ml_data / backend_data / quant / all），默认 all
- `run_ai_analyze`: 是否跑 AI 分析，默认 true
- `ai_limit`: AI 分析数量上限，默认 10

## Workflow 步骤

```yaml
jobs:
  scrape-and-process:
    runs-on: ubuntu-latest
    steps:
      # 1. Checkout 代码
      - uses: actions/checkout@v4

      # 2. Python 环境
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      # 3. 安装依赖
      - run: |
          pip install -r requirements.txt
          playwright install chromium

      # 4. 写入配置文件
      - run: |
          echo '${{ secrets.LINKEDIN_COOKIES }}' > config/linkedin_cookies.json
          cat <<EOF > .env
          ANTHROPIC_API_KEY=${{ secrets.ANTHROPIC_API_KEY }}
          ANTHROPIC_BASE_URL=${{ secrets.ANTHROPIC_BASE_URL }}
          TURSO_DATABASE_URL=${{ secrets.TURSO_DATABASE_URL }}
          TURSO_AUTH_TOKEN=${{ secrets.TURSO_AUTH_TOKEN }}
          EOF

      # 5. 爬取（每个 profile 串行）
      - run: |
          python scripts/linkedin_scraper_v6.py --profile ml_data --save-to-db --headless
          python scripts/linkedin_scraper_v6.py --profile backend_data --save-to-db --headless
          python scripts/linkedin_scraper_v6.py --profile quant --save-to-db --headless

      # 6. 处理流水线
      - run: python scripts/job_pipeline.py --process

      # 7. AI 分析（可选）
      - if: inputs.run_ai_analyze != 'false'
        run: python scripts/job_pipeline.py --ai-analyze --limit ${{ inputs.ai_limit || 10 }}

      # 8. 输出统计
      - run: python scripts/job_pipeline.py --stats
```

## 需要的代码改动

### 1. 爬虫 CI 适配 (`scripts/linkedin_scraper_v6.py`)

**现状**: 只从 `config/linkedin_cookies.json` 文件读取 cookie，交互式登录 fallback。

**改动**:
- 添加 `--headless` 参数（不连接 CDP，直接用 Playwright headless）
- 检测非 TTY 环境时跳过交互式登录，直接报错退出
- Cookie 文件由 workflow 从 secrets 写入，爬虫代码无需改动读取逻辑

### 2. 确保 Turso 环境变量传递

**现状**: `src/db/job_db.py` 已支持从环境变量读取 `TURSO_DATABASE_URL` 和 `TURSO_AUTH_TOKEN`。

**改动**: 无（workflow 写入 `.env` 文件，`python-dotenv` 自动加载）

### 3. Pipeline 无交互模式

**现状**: `job_pipeline.py` 本身无交互操作。

**改动**: 无

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| Cookie 过期 | Playwright 登录失败 → workflow 失败 → GitHub 邮件通知 → 手动更新 secret |
| LinkedIn 反爬 | 爬取 0 条 → 正常退出（`exit 0`），不影响后续步骤 |
| API 限流 | AI analyzer 内置重试 → 超限后跳过剩余 |
| Turso 连接失败 | 降级到本地 SQLite（但 CI 里数据不持久） |
| Playwright 安装失败 | workflow 失败 → 检查 runner 环境 |

## 安全考虑

- 所有敏感信息通过 GitHub Secrets 管理，不进入代码
- `config/linkedin_cookies.json` 和 `.env` 在 `.gitignore` 中
- Workflow 日志不会打印 secret 值（GitHub 自动 mask）
- Repo 建议设为 private（包含个人求职数据）

## 成本估算

- **GitHub Actions**: 免费额度 2000 分钟/月，每次运行约 5-10 分钟，工作日跑 ≈ 100-200 分钟/月
- **Turso**: 免费额度 9GB 存储 + 500M 行读取/月，足够
- **Claude API**: 取决于 `ai_limit`，每个职位约 $0.05-0.10

## 本地工作流（CI 部署后）

```bash
# 简历生成（本地，Turso 自动同步最新数据）
python scripts/job_pipeline.py --generate

# 查看待申请
python scripts/job_pipeline.py --ready

# 标记已申请
python scripts/job_pipeline.py --mark-applied JOB_ID
```

## 实现顺序

1. 爬虫 CI 适配（`--headless` 参数 + 非 TTY 检测）
2. 编写 `.github/workflows/job-pipeline.yml`
3. 配置 GitHub Secrets
4. 测试 `workflow_dispatch` 手动触发
5. 启用 cron 定时触发
