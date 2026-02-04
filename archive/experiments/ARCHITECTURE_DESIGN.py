"""
Job Hunter - 系统化设计文档
=============================

架构目标:
1. 可配置化 - 所有策略参数通过YAML配置
2. 可实验性 - 内置A/B测试框架
3. 可观测性 - 完整的数据收集和分析
4. 可扩展性 - 模块化设计，易于添加新功能

核心原则: 数据驱动决策，快速迭代优化
"""

# ============================================================================
# 系统架构概览
# ============================================================================

SYSTEM_ARCHITECTURE = """
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION LAYER                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  filters    │  │  scoring    │  │  resume     │  │  experiments        │ │
│  │  .yaml      │  │  .yaml      │  │  .yaml      │  │  .yaml              │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  JobHunter (主控)                                                       │ │
│  │  - 加载配置                                                             │ │
│  │  - 管理实验                                                             │ │
│  │  - 协调各模块                                                           │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        ▼             ▼               ▼               ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
│  Crawler  │  │  Filter   │  │  Scorer   │  │  Resume   │  │  Tracker  │
│  Module   │  │  Module   │  │  Module   │  │  Module   │  │  Module   │
└───────────┘  └───────────┘  └───────────┘  └───────────┘  └───────────┘
        │             │               │               │             │
        └─────────────┴───────────────┴───────────────┴─────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA LAYER                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  jobs/      │  │  results/   │  │  metrics/   │  │  experiments/       │ │
│  │  (原始数据)  │  │  (处理结果)  │  │  (指标数据)  │  │  (实验数据)          │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ANALYTICS LAYER                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │  Dashboard / CLI Reports                                                │ │
│  │  - 转化率分析                                                           │ │
│  │  - A/B测试结果                                                          │ │
│  │  - 参数敏感性分析                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# 配置系统设计
# ============================================================================

CONFIG_SYSTEM = """
所有配置集中管理，支持环境覆盖:

config/
├── base/                       # 基础配置
│   ├── filters.yaml           # 筛选规则
│   ├── scoring.yaml           # 评分策略
│   ├── resume.yaml            # 简历模板配置
│   └── pipeline.yaml          # 流程配置
│
├── environments/              # 环境特定配置
│   ├── development.yaml       # 开发环境
│   ├── staging.yaml          # 测试环境
│   └── production.yaml       # 生产环境
│
└── experiments/              # 实验配置
    ├── exp_001_title_keywords.yaml
    ├── exp_002_summary_length.yaml
    └── exp_003_score_threshold.yaml

配置加载优先级 (从高到低):
1. 命令行参数
2. 环境变量
3. 实验配置
4. 环境特定配置
5. 基础配置
"""

# ============================================================================
# A/B测试框架设计
# ============================================================================

AB_TESTING_FRAMEWORK = """
实验定义 (YAML):

experiment:
  id: "exp_001"
  name: "summary_length_test"
  description: "测试不同summary长度对回复率的影响"
  
  # 分组策略
  variants:
    - name: "control"
      weight: 0.5
      config:
        resume:
          summary:
            max_length: 200
            style: "concise"
    
    - name: "treatment"
      weight: 0.5
      config:
        resume:
          summary:
            max_length: 400
            style: "detailed"
  
  # 成功指标
  metrics:
    primary: "response_rate"      # 主要指标: 回复率
    secondary:
      - "interview_rate"          # 次要指标: 面试率
      - "time_to_response"        # 次要指标: 回复时间
  
  # 实验参数
  parameters:
    min_sample_size: 100          # 最小样本量
    max_duration_days: 30         # 最大实验天数
    confidence_level: 0.95        # 置信水平

自动分流:
- 每个职位根据哈希值分配到不同组
- 确保同一职位始终进入同一组
- 记录分组信息用于后续分析
"""

# ============================================================================
# 数据模型设计
# ============================================================================

DATA_MODELS = """
Job (职位):
  - id: str                      # 唯一标识
  - source: str                  # 来源 (linkedin, indeed, etc.)
  - title: str
  - company: str
  - location: str
  - url: str
  - description: str
  - raw_data: dict              # 原始爬取数据
  - discovered_at: datetime
  - experiment_variant: str     # A/B测试分组

ProcessingResult (处理结果):
  - job_id: str
  - pipeline_version: str       # 用于追踪哪个版本的策略
  - config_version: str         # 配置版本
  
  # 筛选阶段
  - filter_passed: bool
  - filter_reject_reason: str
  - filter_rules_triggered: list
  
  # 评分阶段
  - score: float
  - score_breakdown: dict       # 分项得分
  - ai_analysis: str
  
  # 简历生成阶段
  - resume_generated: bool
  - resume_path: str
  - resume_variant: str         # A/B测试简历版本
  
  # 追踪阶段
  - status: str                 # new -> applied -> response -> interview -> offer
  - status_history: list        # 状态变更历史
  
  # 反馈数据 (手动录入或自动检测)
  - response_received: bool
  - response_date: datetime
  - response_type: str          # rejection / phone_screen / interview / offer
  
  # 元数据
  - processed_at: datetime
  - processing_duration_ms: int

Metric (指标):
  - date: date
  - metric_name: str
  - metric_value: float
  - dimensions: dict            # 维度分解 (source, variant, etc.)
"""

# ============================================================================
# 可配置参数清单
# ============================================================================

CONFIGURABLE_PARAMETERS = {
    # 筛选参数
    "filters": {
        "hard_reject.dutch_required": {
            "type": "bool",
            "default": True,
            "description": "是否拒绝要求荷兰语的职位"
        },
        "hard_reject.max_years_experience": {
            "type": "int",
            "default": 8,
            "description": "最大可接受的经验年限"
        },
        "hard_reject.senior_titles": {
            "type": "list",
            "default": ["principal", "director", "vp"],
            "description": "拒绝的职级关键词"
        },
    },
    
    # 评分参数
    "scoring": {
        "threshold.generate_resume": {
            "type": "float",
            "default": 6.0,
            "min": 0,
            "max": 10,
            "description": "生成简历的最低分数阈值"
        },
        "weights.keyword_match": {
            "type": "float",
            "default": 0.4,
            "description": "关键词匹配权重"
        },
        "weights.company_target": {
            "type": "float",
            "default": 0.3,
            "description": "目标公司权重"
        },
        "weights.experience_fit": {
            "type": "float",
            "default": 0.3,
            "description": "经验匹配权重"
        },
    },
    
    # 简历生成参数
    "resume": {
        "summary.max_length": {
            "type": "int",
            "default": 300,
            "description": "Summary最大字符数"
        },
        "summary.style": {
            "type": "choice",
            "choices": ["concise", "detailed", "technical", "business"],
            "default": "concise",
            "description": "Summary写作风格"
        },
        "bullet_points.max_per_job": {
            "type": "int",
            "default": 3,
            "description": "每份工作最多bullet点数"
        },
        "skills.highlight_top_n": {
            "type": "int",
            "default": 5,
            "description": "突出显示前N个技能"
        },
    },
    
    # 流程参数
    "pipeline": {
        "daily.max_jobs": {
            "type": "int",
            "default": 20,
            "description": "每日最大处理职位数"
        },
        "scraper.sources": {
            "type": "list",
            "default": ["linkedin", "indeed"],
            "description": "启用的数据源"
        },
        "notifications.enabled": {
            "type": "bool",
            "default": True,
            "description": "是否发送通知"
        },
    }
}

# ============================================================================
# 分析指标体系
# ============================================================================

ANALYTICS_METRICS = """
漏斗指标:
  - discovery_rate:        每日发现职位数
  - pass_rate_filter:      硬性筛选通过率
  - pass_rate_scoring:     评分通过率 (>=阈值)
  - generation_rate:       简历生成率
  - application_rate:      实际申请率
  - response_rate:         回复率 (核心指标)
  - interview_rate:        面试率
  - offer_rate:             offer率

效率指标:
  - avg_processing_time:   平均处理时间
  - token_usage_per_job:   每个职位消耗的token
  - cost_per_application:  每次申请的成本

质量指标:
  - resume_quality_score:  简历质量评分 (人工抽样)
  - match_accuracy:        匹配准确度 (对比最终回复)

实验指标:
  - variant_performance:   各实验组表现对比
  - confidence_interval:   置信区间
  - statistical_power:     统计功效
"""

# ============================================================================
# 项目目录结构
# ============================================================================

PROJECT_STRUCTURE = """
job-hunter/
├── README.md
├── requirements.txt
├── pyproject.toml
│
├── config/                      # 配置中心
│   ├── base/
│   │   ├── filters.yaml
│   │   ├── scoring.yaml
│   │   ├── resume.yaml
│   │   └── pipeline.yaml
│   ├── environments/
│   │   ├── development.yaml
│   │   └── production.yaml
│   └── experiments/             # A/B测试配置
│       ├── README.md
│       └── (动态创建)
│
├── src/                         # 源代码
│   ├── __init__.py
│   ├── config/                  # 配置管理
│   │   ├── __init__.py
│   │   ├── loader.py           # 配置加载器
│   │   └── validator.py        # 配置验证
│   │
│   ├── core/                    # 核心模块
│   │   ├── __init__.py
│   │   ├── hunter.py           # 主控
│   │   ├── pipeline.py         # 流程编排
│   │   └── experiment.py       # 实验管理
│   │
│   ├── modules/                 # 功能模块
│   │   ├── __init__.py
│   │   ├── crawler/            # 爬虫模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── linkedin.py
│   │   │   └── indeed.py
│   │   │
│   │   ├── filter/             # 筛选模块
│   │   │   ├── __init__.py
│   │   │   ├── engine.py
│   │   │   └── rules.py
│   │   │
│   │   ├── scorer/             # 评分模块
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── rule_based.py
│   │   │   └── ai_based.py
│   │   │
│   │   ├── resume/             # 简历模块
│   │   │   ├── __init__.py
│   │   │   ├── generator.py
│   │   │   ├── tailor.py
│   │   │   └── pdf.py
│   │   │
│   │   └── tracker/            # 追踪模块
│   │       ├── __init__.py
│   │       ├── storage.py
│   │       └── analytics.py
│   │
│   └── utils/                   # 工具函数
│       ├── __init__.py
│       ├── logging.py
│       └── helpers.py
│
├── data/                        # 数据存储
│   ├── jobs/                    # 原始职位数据
│   ├── results/                 # 处理结果
│   ├── metrics/                 # 指标数据
│   └── experiments/             # 实验数据
│
├── output/                      # 输出文件
│   └── resumes/                 # 生成的简历
│
├── scripts/                     # 脚本工具
│   ├── daily_run.py            # 每日运行
│   ├── analyze.py              # 数据分析
│   └── report.py               # 生成报告
│
├── tests/                       # 测试
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
└── docs/                        # 文档
    ├── architecture.md
    ├── configuration.md
    ├── experiments.md
    └── analytics.md
"""

# ============================================================================
# 使用示例
# ============================================================================

USAGE_EXAMPLES = """
# 1. 基础运行
python -m job_hunter --config config/production.yaml

# 2. 使用特定实验配置
python -m job_hunter --experiment config/experiments/exp_001.yaml

# 3. 覆盖特定参数
python -m job_hunter --set scoring.threshold=7.0 --set resume.summary.style=detailed

# 4. 运行分析
python scripts/analyze.py --metric response_rate --by variant

# 5. 生成实验报告
python scripts/report.py --experiment exp_001
"""

if __name__ == "__main__":
    print(__doc__)
    print(SYSTEM_ARCHITECTURE)
    print(CONFIG_SYSTEM)
    print(AB_TESTING_FRAMEWORK)
    print(DATA_MODELS)
    print(ANALYTICS_METRICS)
    print(PROJECT_STRUCTURE)
    print(USAGE_EXAMPLES)
