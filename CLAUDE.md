# Job Hunter - OpenClaw 执行指南

## 项目概述

自动化求职系统：爬取职位 → 筛选评分 → 生成定制简历 → 追踪申请

## 核心命令

### 1. 爬取 LinkedIn 职位
```bash
cd workspace/job-hunter
python scripts/linkedin_scraper_v6.py --profile ml_data --save-to-db --cdp
```
- `--profile`: 搜索配置 (ml_data, backend_data, quant)
- `--save-to-db`: 保存到 SQLite 数据库
- `--no-json`: 不保存 JSON 文件（仅数据库）
- `--cdp`: 连接已有浏览器 (需要 Chrome 在端口 9222 运行)
- 不加 `--cdp`: 自动启动新浏览器

配置文件: `config/search_profiles.yaml`

### 2. 处理职位流水线
```bash
python scripts/job_pipeline.py --process
```
- `--import-only`: 只导入不处理
- `--ready`: 查看待申请职位
- `--stats`: 查看统计信息
- `--mark-applied JOB_ID`: 标记已申请

### 3. 生成单份简历
```bash
python job_hunter_v42.py --job "职位标题|职位描述|公司名"
```
示例:
```bash
python job_hunter_v42.py --job "ML Engineer|PyTorch Docker AWS|Picnic"
python job_hunter_v42.py --job "Data Engineer|Spark Databricks ETL|ABN AMRO"
```

### 4. 测试角色分类器
```bash
python job_hunter_v42.py --test
```

## 文件结构 (精简后)

```
job-hunter/
├── job_hunter_v42.py           # 主控制器
├── role_classifier.py          # 角色分类器
├── content_engine.py           # 内容引擎
│
├── scripts/                    # 核心脚本 (4个)
│   ├── linkedin_scraper_v6.py      # LinkedIn爬虫 (含数据库集成)
│   ├── playwright_scraper.py       # 多平台爬虫
│   ├── job_pipeline.py             # 主流水线
│   └── job_parser.py               # JD解析器
│
├── config/
│   ├── role_templates.yaml     # 角色模板 (核心配置)
│   ├── search_profiles.yaml    # 搜索配置
│   ├── linkedin_cookies.json   # LinkedIn登录凭证 (勿提交)
│   └── base/                   # 基础配置
│
├── src/db/
│   └── job_db.py               # SQLite 数据库模块
│
├── data/
│   ├── jobs.db                 # SQLite 数据库
│   └── leads/                  # 爬取的原始数据
│
├── templates/                  # HTML简历模板
├── assets/                     # 内容库
├── output/                     # 生成的简历
└── archive/                    # 归档的旧代码
```

## 数据库结构

SQLite 数据库 `data/jobs.db`:
- `jobs` 表: 所有爬取的职位
- 字段: url, title, company, location, description, scraped_at, status

查看数据库:
```python
from src.db.job_db import JobDatabase
db = JobDatabase()
print(db.get_funnel_stats())
```

## 日常工作流

1. **每日爬取** (建议早上运行):
   ```bash
   python scripts/linkedin_scraper_v6.py --profile ml_data --save-to-db
   ```

2. **处理新职位**:
   ```bash
   python scripts/job_pipeline.py --process
   ```

3. **查看待申请**:
   ```bash
   python scripts/job_pipeline.py --ready
   ```

4. **生成简历** (选中的职位):
   ```bash
   python job_hunter_v42.py --job "职位信息"
   ```

## 注意事项

- LinkedIn cookies 在 `config/linkedin_cookies.json`，首次运行会提示手动登录
- 数据文件 (*.db, *.json) 不要提交到 git
- 归档代码在 `archive/` 目录，如需恢复可从那里找
- 爬虫使用 Playwright，需要 `playwright install chromium`

## 角色分类

系统支持4种角色，自动根据JD关键词分类:
- **ml_engineer**: Machine Learning, Deep Learning, PyTorch, TensorFlow
- **data_engineer**: Spark, Databricks, ETL, Data Pipeline
- **data_scientist**: Statistics, A/B Testing, Analytics
- **quant**: Quantitative, Trading, Risk, Alpha

配置在 `config/role_templates.yaml`
