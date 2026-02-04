# Job Hunter v4.2 - 智能岗位路由简历生成系统

## 🎯 系统概述

基于角色分类器的智能简历生成系统，自动识别岗位类型并生成差异化简历。

```
JD输入 → 角色分类 → 内容生成 → 模板渲染 → PDF输出
```

## 🚀 快速开始

### 1. 环境准备
```bash
# 确保已安装依赖
pip install pyyaml jinja2 playwright
playwright install chromium
```

### 2. 生成单份简历
```bash
python job_hunter_v42.py --job "职位标题|职位描述|公司名"

# 示例
python job_hunter_v42.py --job "Machine Learning Engineer|PyTorch ML pipelines Docker AWS|Picnic"
python job_hunter_v42.py --job "Data Engineer|Spark Databricks ETL|ABN AMRO"
python job_hunter_v42.py --job "Data Scientist|Statistics A/B testing|Booking.com"
```

### 3. 测试分类器
```bash
python job_hunter_v42.py --test
```

### 4. 处理今日抓取（待实现）
```bash
python job_hunter_v42.py --daily
```

## 📁 文件结构

```
job-hunter/
├── job_hunter_v42.py           # 主控制器 ⭐ 当前使用
├── role_classifier.py          # 角色分类器
├── content_engine.py           # 内容引擎
│
├── config/
│   ├── role_templates.yaml     # 角色模板配置 ⭐ 核心配置
│   ├── credentials.json        # 认证信息
│   ├── base/                   # 基础配置
│   │   ├── crawler.yaml        # 爬虫配置
│   │   ├── filters.yaml        # 过滤规则
│   │   ├── pipeline.yaml       # 流水线配置
│   │   ├── resume.yaml         # 简历配置
│   │   └── scoring.yaml        # 评分配置
│   └── experiments/            # 实验配置
│
├── templates/                  # HTML模板
│   ├── base_template.html      # 基础Jinja2模板
│   ├── ml_engineer.html        # ML Engineer模板
│   ├── data_engineer.html      # Data Engineer模板
│   ├── data_scientist.html     # Data Scientist模板
│   ├── quant.html              # Quant模板
│   └── resume_master.html      # 原始参考模板
│
├── assets/                     # 内容库
│   ├── bullet_library.yaml         # 完整内容库
│   ├── bullet_library_simple.yaml  # 简化内容库
│   └── personal_info.yaml          # 个人信息
│
├── scripts/                    # 核心脚本 (4个)
│   ├── linkedin_scraper_v6.py      # LinkedIn爬虫 (含数据库集成, 100% JD成功率)
│   ├── playwright_scraper.py       # 多平台爬虫 (LinkedIn/IamExpat/Indeed)
│   ├── job_pipeline.py             # 主流水线 (过滤→评分→生成→追踪)
│   └── job_parser.py               # JD解析器
│
├── src/                        # 模块化源码
│   ├── config/                 # 配置加载
│   ├── core/                   # 核心逻辑
│   └── modules/                # 功能模块
│       ├── crawler/            # 爬虫模块
│       ├── filter/             # 过滤引擎
│       ├── resume/             # 简历生成
│       ├── scorer/             # 评分引擎
│       └── tracker/            # 追踪分析
│
├── data/                       # 数据存储
│   ├── applications.json       # 申请记录
│   ├── jobs_pending.json       # 待申请职位
│   └── job_tracker.json        # 职位追踪
│
├── output/                     # 生成简历输出
│   └── archived/               # 已归档简历
│
├── archive/                    # 归档文件
│   ├── old_scripts/            # 旧版脚本
│   ├── old_generators/         # 旧版生成器
│   ├── old_configs/            # 旧版配置
│   ├── tests/                  # 测试文件
│   ├── experiments/            # 实验代码
│   └── legacy_docs/            # 历史文档
│
└── README.md                   # 本文档
```

## ⚙️ 核心配置

### 角色模板配置 (`config/role_templates.yaml`)

四大角色差异化配置：

| 角色 | 经历顺序 | 职位头衔 | 项目选择 | 技能分类 |
|------|----------|----------|----------|----------|
| **ML Engineer** | GLP→Trading→Baiquan | Senior ML Engineer & Team Lead | GenAI + Thesis | ML/AI, MLOps, Cloud, Leadership |
| **Data Engineer** | GLP→Baiquan→Eleme | Data Engineer & Team Lead | Data Lakehouse | Languages, Infrastructure, Cloud |
| **Data Scientist** | GLP→Baiquan→Eleme→Henan | Data Scientist & Team Lead | Thesis + Ranking + Sensor | Programming, ML, DL, Analytics |
| **Quant** | Baiquan→GLP→Eleme→Henan | Quantitative Researcher | R-Breaker + Factor | Quant Methods, Programming, Math |

### 修改职位头衔

编辑 `config/role_templates.yaml`:
```yaml
templates:
  data_engineer:
    title_mapping:
      glp: "Data Engineer & Team Lead"  # 修改这里
```

### 添加新公司强制规则

```yaml
role_classifier:
  special_rules:
    company_override:
      new_company: "quant"  # 新公司强制使用quant模板
```

## 🎨 模板系统

基于 `resume_master.html` 的完整结构：

1. **Header** - 联系方式
2. **Bio** - 动态生成摘要
3. **Education** - 学历 + 认证
4. **Professional Experience** - 工作经历 + Career Note
5. **Projects** - 项目经历
6. **Technical Skills** - 技能列表
7. **Interests** - 兴趣 + 博客

所有模板继承 `base_template.html`，确保结构一致。

## 📝 内容库

`assets/bullet_library_simple.yaml` 包含：
- **personal_info**: 个人信息
- **education**: 教育背景
- **experiences**: 工作经历 (含 role_fit 标签)
- **projects**: 项目经历
- **skills**: 技能列表
- **languages**: 语言能力
- **career_note**: 职业说明

### 添加新 bullet

```yaml
experiences:
  - company: "GLP Technology"
    bullets:
      - content: "新bullet内容"
        role_fit: [ml_engineer, data_engineer]  # 适用角色
        tech: [python, pytorch]                  # 技术标签
```

## 🔧 故障排除

### 分类不准确
- 检查 `config/role_templates.yaml` 中的 `keyword_weights`
- 添加更多关键词或调整权重

### 内容未显示
- 检查 `assets/bullet_library_simple.yaml` 中的 `role_fit` 标签
- 确保经历/项目有匹配当前角色的标签

### 模板渲染错误
- 检查模板变量名是否匹配 (`category`/`skills_list`)
- 验证 YAML 格式是否正确

## 📊 版本历史

### v4.2 (2026-02-04)
- ✅ 基于 resume_master.html 的完整模板
- ✅ 角色分类器系统
- ✅ 差异化内容生成
- ✅ Interests 部分完整

### v4.1 (2026-02-03)
- 配置驱动生成器
- YAML 内容库
- Jinja2 模板

### v4.0 (2026-02-01)
- HTML简历系统
- Playwright爬虫

## 🎯 待办事项

- [ ] 接入真实爬虫到v4.2系统
- [ ] 接入真实AI分析 (替换模拟评分)
- [ ] 配置Windows定时任务
- [ ] 开始真实职位投递
- [ ] 简历效果追踪 (面试转化率)

---

**最后更新**: 2026-02-04
