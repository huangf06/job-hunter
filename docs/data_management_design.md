# 职位数据管理方案设计

## 1. 数据流程概览

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Scraper   │───▶│  Raw Jobs   │───▶│ Hard Filter │───▶│  AI Score   │───▶│  Generate   │
│  (LinkedIn) │    │   (inbox)   │    │  (rules)    │    │  (LLM)      │    │  (Resume)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                  │                  │                  │
                          ▼                  ▼                  ▼                  ▼
                   ┌─────────────────────────────────────────────────────────────────┐
                   │                    jobs.db (SQLite)                              │
                   │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
                   │  │  jobs   │ │ filters │ │ scores  │ │ resumes │ │ outcomes│   │
                   │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
                   └─────────────────────────────────────────────────────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   Analytics &   │
                                    │   Optimization  │
                                    └─────────────────┘
```

## 2. 数据库设计 (SQLite)

### 2.1 核心表结构

```sql
-- 职位主表：存储所有抓取的职位
CREATE TABLE jobs (
    id TEXT PRIMARY KEY,                    -- 唯一ID (基于URL hash)
    source TEXT NOT NULL,                   -- 来源: linkedin, indeed, glassdoor
    source_id TEXT,                         -- 来源平台的原始ID
    url TEXT UNIQUE NOT NULL,               -- 职位链接
    title TEXT NOT NULL,                    -- 职位标题
    company TEXT NOT NULL,                  -- 公司名称
    location TEXT,                          -- 地点
    description TEXT,                       -- 职位描述 (JD全文)
    posted_date TEXT,                       -- 发布日期
    scraped_at TEXT NOT NULL,               -- 抓取时间
    search_profile TEXT,                    -- 搜索profile (ml_data, quant等)
    search_query TEXT,                      -- 搜索关键词
    raw_data TEXT,                          -- 原始JSON数据
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 筛选结果表：记录硬规则筛选
CREATE TABLE filter_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    passed BOOLEAN NOT NULL,                -- 是否通过筛选
    filter_version TEXT,                    -- 筛选规则版本
    reject_reason TEXT,                     -- 拒绝原因 (dutch_required, too_senior等)
    matched_rules TEXT,                     -- 匹配的规则 (JSON)
    processed_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, filter_version)
);

-- AI评分表：记录LLM评分
CREATE TABLE ai_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    score REAL NOT NULL,                    -- 总分 (0-10)
    model TEXT,                             -- 使用的模型
    score_breakdown TEXT,                   -- 评分细节 (JSON)
    matched_keywords TEXT,                  -- 匹配的关键词 (JSON)
    analysis TEXT,                          -- AI分析文本
    recommendation TEXT,                    -- APPLY_NOW, APPLY, MAYBE, SKIP
    scored_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, model)
);

-- 简历生成表：记录生成的简历
CREATE TABLE resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    role_type TEXT,                         -- 角色类型: mle, de, ds, quant
    template_version TEXT,                  -- 模板版本
    html_path TEXT,                         -- HTML文件路径
    pdf_path TEXT,                          -- PDF文件路径
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, role_type)
);

-- 申请状态表：跟踪申请进度
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    status TEXT NOT NULL DEFAULT 'pending', -- pending, applied, rejected, interview, offer
    applied_at TEXT,                        -- 申请时间
    response_at TEXT,                       -- 收到回复时间
    interview_at TEXT,                      -- 面试时间
    outcome TEXT,                           -- 最终结果
    notes TEXT,                             -- 备注
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id)
);

-- 反馈记录表：用于优化
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL REFERENCES jobs(id),
    feedback_type TEXT NOT NULL,            -- response, interview, offer, rejection
    days_to_response INTEGER,               -- 响应天数
    rejection_stage TEXT,                   -- 拒绝阶段: resume, phone, onsite
    rejection_reason TEXT,                  -- 拒绝原因 (如果知道)
    notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 配置快照表：记录每次运行的配置
CREATE TABLE config_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,                   -- 运行ID
    config_type TEXT NOT NULL,              -- filter_rules, score_weights, search_profiles
    config_data TEXT NOT NULL,              -- 配置内容 (JSON)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_jobs_company ON jobs(company);
CREATE INDEX idx_jobs_source ON jobs(source);
CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at);
CREATE INDEX idx_filter_passed ON filter_results(passed);
CREATE INDEX idx_scores_score ON ai_scores(score);
CREATE INDEX idx_applications_status ON applications(status);
```

### 2.2 视图 (便于查询)

```sql
-- 待处理职位视图
CREATE VIEW v_pending_jobs AS
SELECT j.*, f.passed as filter_passed, s.score, s.recommendation
FROM jobs j
LEFT JOIN filter_results f ON j.id = f.job_id
LEFT JOIN ai_scores s ON j.id = s.job_id
LEFT JOIN applications a ON j.id = a.job_id
WHERE a.id IS NULL OR a.status = 'pending';

-- 高分职位视图
CREATE VIEW v_high_score_jobs AS
SELECT j.*, s.score, s.recommendation, r.pdf_path
FROM jobs j
JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
JOIN ai_scores s ON j.id = s.job_id AND s.score >= 7.0
LEFT JOIN resumes r ON j.id = r.job_id
ORDER BY s.score DESC;

-- 申请漏斗视图
CREATE VIEW v_application_funnel AS
SELECT
    COUNT(*) as total_scraped,
    SUM(CASE WHEN f.passed = 1 THEN 1 ELSE 0 END) as passed_filter,
    SUM(CASE WHEN s.score >= 7.0 THEN 1 ELSE 0 END) as high_score,
    SUM(CASE WHEN a.status = 'applied' THEN 1 ELSE 0 END) as applied,
    SUM(CASE WHEN a.status = 'interview' THEN 1 ELSE 0 END) as interview,
    SUM(CASE WHEN a.status = 'offer' THEN 1 ELSE 0 END) as offer
FROM jobs j
LEFT JOIN filter_results f ON j.id = f.job_id
LEFT JOIN ai_scores s ON j.id = s.job_id
LEFT JOIN applications a ON j.id = a.job_id;
```

## 3. 职位状态流转

```
                    ┌──────────────────────────────────────────────────────────┐
                    │                      Job Lifecycle                        │
                    └──────────────────────────────────────────────────────────┘

    ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
    │ scraped │────▶│filtered │────▶│ scored  │────▶│generated│────▶│ applied │
    └─────────┘     └─────────┘     └─────────┘     └─────────┘     └─────────┘
         │               │               │               │               │
         │               │               │               │               ▼
         │               │               │               │         ┌─────────┐
         │               │               │               │         │response │
         │               │               │               │         └─────────┘
         │               │               │               │               │
         │               ▼               ▼               │               ▼
         │          ┌─────────┐    ┌─────────┐          │         ┌─────────┐
         │          │rejected │    │  skip   │          │         │interview│
         │          │(filter) │    │(low score)         │         └─────────┘
         │          └─────────┘    └─────────┘          │               │
         │                                              │               ▼
         │                                              │         ┌─────────┐
         │                                              │         │ offer / │
         │                                              │         │rejected │
         │                                              │         └─────────┘
         │                                              │               │
         └──────────────────────────────────────────────┴───────────────┘
                                    │
                                    ▼
                            ┌─────────────┐
                            │  Feedback   │
                            │  & Analytics│
                            └─────────────┘
```

## 4. 配置文件结构

### 4.1 筛选规则 (`config/filter_rules.yaml`)

```yaml
version: "1.0"

# 硬性排除规则 (任一匹配即排除)
exclude:
  # 语言要求
  language_required:
    - pattern: "dutch required|dutch speaking|native dutch|vloeiend nederlands"
      reason: "dutch_required"
    - pattern: "german required|german speaking|native german"
      reason: "german_required"

  # 经验要求过高
  experience_too_high:
    - pattern: "10\\+ years|15\\+ years|20\\+ years"
      reason: "experience_too_high"
    - pattern: "principal|director|vp of|head of|chief"
      reason: "senior_management"

  # 公司黑名单
  company_blacklist:
    - "Hays"
    - "Randstad"
    - "Michael Page"
    - "Robert Half"
    - "Brunel"
    - "Experis"
    - "Manpower"

# 软性排除 (标记但不排除)
soft_exclude:
  - pattern: "junior|entry level|graduate"
    tag: "entry_level"
  - pattern: "contract|freelance|contractor"
    tag: "contract"

# 必须包含 (任一匹配即通过)
require_any:
  visa_friendly:
    - "visa sponsor"
    - "sponsorship"
    - "highly skilled migrant"
    - "relocation"
    - "international"
```

### 4.2 评分权重 (`config/score_weights.yaml`)

```yaml
version: "1.0"

# 基础分 (所有通过筛选的职位)
base_score: 5.0

# 关键词权重
keywords:
  # 核心技能 (高权重)
  high_weight: 1.5
  high_keywords:
    - "machine learning"
    - "deep learning"
    - "pytorch"
    - "tensorflow"
    - "quantitative"
    - "quant"
    - "alpha"
    - "backtesting"

  # 相关技能 (中权重)
  medium_weight: 1.0
  medium_keywords:
    - "python"
    - "sql"
    - "spark"
    - "databricks"
    - "aws"
    - "docker"
    - "kubernetes"

  # 加分项 (低权重)
  low_weight: 0.5
  low_keywords:
    - "visa sponsor"
    - "sponsorship"
    - "relocation"
    - "remote"
    - "hybrid"

# 公司权重
company_tiers:
  tier_1:  # 顶级公司
    weight: 2.0
    companies:
      - "Optiver"
      - "Flow Traders"
      - "IMC"
      - "Booking.com"
      - "Adyen"
      - "ASML"
  tier_2:  # 优质公司
    weight: 1.0
    companies:
      - "Picnic"
      - "Coolblue"
      - "bol.com"
      - "ING"
      - "ABN AMRO"
  tier_3:  # 普通公司
    weight: 0.0

# 推荐阈值
thresholds:
  apply_now: 8.0    # >= 8.0: 立即申请
  apply: 6.0        # >= 6.0: 建议申请
  maybe: 4.0        # >= 4.0: 可以考虑
  skip: 0.0         # < 4.0: 跳过
```

## 5. 目录结构

```
job-hunter/
├── config/
│   ├── search_profiles.yaml      # 搜索配置 (已有)
│   ├── filter_rules.yaml         # 筛选规则
│   ├── score_weights.yaml        # 评分权重
│   └── linkedin_cookies.json     # 登录凭证
│
├── data/
│   ├── jobs.db                   # SQLite 数据库 (核心)
│   ├── inbox/                    # 待处理的原始数据
│   │   └── linkedin_YYYYMMDD_HHMM.json
│   ├── archive/                  # 已处理的历史数据
│   │   └── 2026-02/
│   │       └── linkedin_*.json
│   └── exports/                  # 导出的报告
│       └── weekly_report_2026W05.csv
│
├── output/
│   └── resumes/                  # 生成的简历
│       └── 2026-02-04/
│           ├── Fei_Huang_Optiver_Quant.pdf
│           └── Fei_Huang_Booking_MLE.pdf
│
├── scripts/
│   ├── linkedin_scraper_v6.py    # 抓取脚本
│   ├── job_processor.py          # 处理流水线
│   ├── job_db.py                 # 数据库操作
│   └── analytics.py              # 数据分析
│
└── logs/
    └── job_hunter_2026-02-04.log
```

## 6. 处理流水线

### 6.1 主流程 (`job_processor.py`)

```python
class JobProcessor:
    """职位处理流水线"""

    def __init__(self, db_path: str):
        self.db = JobDatabase(db_path)
        self.filter = JobFilter("config/filter_rules.yaml")
        self.scorer = JobScorer("config/score_weights.yaml")
        self.generator = ResumeGenerator()

    def process_inbox(self):
        """处理 inbox 中的所有新职位"""
        for json_file in Path("data/inbox").glob("*.json"):
            jobs = self.load_jobs(json_file)

            for job in jobs:
                # 1. 去重检查
                if self.db.job_exists(job["url"]):
                    continue

                # 2. 保存到数据库
                job_id = self.db.insert_job(job)

                # 3. 硬规则筛选
                filter_result = self.filter.apply(job)
                self.db.save_filter_result(job_id, filter_result)

                if not filter_result.passed:
                    continue

                # 4. AI 评分
                score_result = self.scorer.score(job)
                self.db.save_score(job_id, score_result)

                if score_result.score < 6.0:
                    continue

                # 5. 生成简历
                resume = self.generator.generate(job, score_result)
                self.db.save_resume(job_id, resume)

            # 6. 归档已处理文件
            self.archive_file(json_file)

    def get_ready_to_apply(self) -> List[Job]:
        """获取待申请的职位"""
        return self.db.query("""
            SELECT j.*, s.score, r.pdf_path
            FROM jobs j
            JOIN filter_results f ON j.id = f.job_id AND f.passed = 1
            JOIN ai_scores s ON j.id = s.job_id AND s.score >= 6.0
            JOIN resumes r ON j.id = r.job_id
            LEFT JOIN applications a ON j.id = a.job_id
            WHERE a.id IS NULL
            ORDER BY s.score DESC
        """)
```

### 6.2 每日工作流

```bash
# 1. 抓取新职位
python scripts/linkedin_scraper_v6.py --profile ml_data
python scripts/linkedin_scraper_v6.py --profile quant

# 2. 处理新职位 (筛选 -> 评分 -> 生成简历)
python scripts/job_processor.py --process-inbox

# 3. 查看待申请列表
python scripts/job_processor.py --list-ready

# 4. 记录申请结果
python scripts/job_processor.py --mark-applied <job_id>

# 5. 生成周报
python scripts/analytics.py --weekly-report
```

## 7. 分析与优化

### 7.1 关键指标

| 指标 | 计算方式 | 用途 |
|------|----------|------|
| 筛选通过率 | passed / total_scraped | 优化筛选规则 |
| 高分率 | score>=7 / passed | 优化搜索关键词 |
| 申请转化率 | applied / high_score | 评估简历质量 |
| 响应率 | response / applied | 评估匹配度 |
| 面试率 | interview / response | 评估简历效果 |
| Offer率 | offer / interview | 评估面试表现 |

### 7.2 优化反馈循环

```
┌─────────────────────────────────────────────────────────────────┐
│                     Optimization Feedback Loop                   │
└─────────────────────────────────────────────────────────────────┘

    ┌─────────────┐
    │  Outcomes   │ ◀─────────────────────────────────────────────┐
    │ (feedback)  │                                                │
    └──────┬──────┘                                                │
           │                                                       │
           ▼                                                       │
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
    │  Analyze    │────▶│  Identify   │────▶│   Adjust    │       │
    │  Patterns   │     │  Issues     │     │   Config    │       │
    └─────────────┘     └─────────────┘     └──────┬──────┘       │
                                                   │               │
                                                   ▼               │
                                            ┌─────────────┐        │
                                            │  New Jobs   │────────┘
                                            │  Pipeline   │
                                            └─────────────┘

分析示例:
- 如果某公司响应率高 → 提升该公司权重
- 如果某关键词匹配的职位面试率低 → 降低该关键词权重
- 如果某类职位总是被拒 → 添加到排除规则
```

### 7.3 周报模板

```markdown
# Job Hunter Weekly Report - 2026 Week 05

## Summary
- Total Scraped: 150
- Passed Filter: 85 (56.7%)
- High Score (>=7): 32 (37.6%)
- Applied: 20
- Responses: 5 (25%)
- Interviews: 2 (40%)

## Top Performing
| Company | Title | Score | Status |
|---------|-------|-------|--------|
| Optiver | Quant Researcher | 9.2 | Interview |
| Booking | ML Engineer | 8.5 | Response |

## Filter Analysis
| Reject Reason | Count | % |
|---------------|-------|---|
| dutch_required | 25 | 38% |
| company_blacklist | 20 | 31% |
| experience_too_high | 12 | 18% |

## Recommendations
1. Consider adding "German" to language filter
2. Increase weight for "MLOps" keyword (high response rate)
3. Remove "Coolblue" from tier_2 (no responses)
```

## 8. 实施计划

### Phase 1: 数据库迁移
- [ ] 创建 SQLite 数据库和表结构
- [ ] 编写 `job_db.py` 数据库操作类
- [ ] 迁移现有 JSON 数据到数据库

### Phase 2: 处理流水线
- [ ] 创建 `filter_rules.yaml` 配置
- [ ] 创建 `score_weights.yaml` 配置
- [ ] 实现 `job_processor.py` 流水线

### Phase 3: 集成与自动化
- [ ] 修改 scraper 直接写入数据库
- [ ] 创建每日自动化脚本
- [ ] 添加日志记录

### Phase 4: 分析与优化
- [ ] 实现 `analytics.py` 分析脚本
- [ ] 创建周报生成功能
- [ ] 建立反馈优化机制
