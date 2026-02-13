# HTML Resume 完整工作流程 v1.0

> 基于实战测试确认的最佳实践

---

## 📋 完整工作流程（7步标准流程）

```
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: 获取职位信息                                            │
│  ├── 来源: LinkedIn / IamExpat / 公司官网 / 内推                 │
│  └── 输出: job_description.txt                                  │
├─────────────────────────────────────────────────────────────────┤
│  STEP 2: AI分析JD                                                │
│  ├── 检测角色类型 (Data Engineer / ML Engineer / Quant / DS)     │
│  ├── 提取关键词 (Spark, Databricks, CI/CD, etc.)                │
│  └── 确定优先级技能                                             │
├─────────────────────────────────────────────────────────────────┤
│  STEP 3: 生成定制简历                                            │
│  ├── 基于 template.html                                          │
│  ├── 匹配 bullet_library.yaml 内容                               │
│  ├── 调整Bio、经历顺序、技能标签                                 │
│  └── 输出: [Company]_[Role]_draft.html                          │
├─────────────────────────────────────────────────────────────────┤
│  STEP 4: Proofread校对                                           │
│  ├── 核对个人信息 (地址、LinkedIn等)                             │
│  ├── 验证时间线                                                  │
│  ├── 检查技能匹配度                                              │
│  └── 确认一页完整                                                │
├─────────────────────────────────────────────────────────────────┤
│  STEP 5: 生成PDF                                                 │
│  ├── 使用 html_to_pdf.py                                         │
│  ├── 边距: 0.5in (四边)                                          │
│  └── 输出: [Company]_[Role]_draft.pdf                           │
├─────────────────────────────────────────────────────────────────┤
│  STEP 6: 人工审阅                                                │
│  ├── 浏览器打开HTML检查                                          │
│  ├── Sumatra PDF查看PDF效果                                      │
│  └── 确认无误或反馈修改                                          │
├─────────────────────────────────────────────────────────────────┤
│  STEP 7: 重命名并投递                                            │
│  ├── 重命名: Fei_Huang_[Role]_[Company].pdf                      │
│  ├── 投递: 官网 / LinkedIn / 邮件                                │
│  └── 记录: applications/tracker.csv                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 文件名命名规范

### 标准格式
```
Fei_Huang_[Role]_[Company].[ext]
```

### 示例
| 场景 | 文件名 |
|------|--------|
| Adyen Data Engineer | `Fei_Huang_Data_Engineer_Adyen.pdf` |
| Booking ML Engineer | `Fei_Huang_ML_Engineer_Booking.pdf` |
| 通用Data Engineer | `Fei_Huang_Data_Engineer.pdf` |
| 带日期版本 | `Fei_Huang_Data_Engineer_2026-02-01.pdf` |

### 禁止格式
- ❌ `test_adyen_resume_final.pdf`（太随意）
- ❌ `resume.pdf`（太通用）
- ❌ `FeiHuangResume.pdf`（无角色信息）

---

## ✅ 已确认的最佳实践

### 1. 个人信息（基于 bullet_library.yaml）

| 字段 | 简历显示 | 完整信息（面试用） |
|------|----------|-------------------|
| **地址** | Amsterdam, Netherlands | Antonio Vivaldistraat 7, 1081 HP |
| **LinkedIn** | linkedin.com/in/huangf06 | https://www.linkedin.com/in/huangf06/ |
| **电话** | (+31) 645 038 614 | +31 645 038 614 |
| **邮箱** | huangf06@gmail.com | huangf06@gmail.com |

**原则**: 简历显示简化版，面试时可提供完整地址

---

### 2. 时间线排列（Chronological）

```
GLP Technology      Jul 2017 -- Aug 2019  (Data Engineer & Risk Lead)
Baiquan Investment  Jul 2015 -- Jun 2017  (Quantitative Developer)
Ele.me              Sep 2013 -- Jul 2015  (Data Analyst)
```

**原则**: 时间倒序，最新经历在前

---

### 3. 职位名称调整（按角色定制）

| 公司 | 原始Title | Data Engineer版 | ML Engineer版 | Quant版 |
|------|-----------|-----------------|---------------|---------|
| **GLP** | Data Analyst | Data Engineer & Risk Lead | ML Engineer & Team Lead | Risk Analyst |
| **Baiquan** | Quant Researcher | Quantitative Developer | Quantitative Researcher | Quantitative Researcher |
| **Ele.me** | Data Analyst | Data Analyst | Data Analyst | Data Analyst |

**原则**: 调整职位名称以匹配目标角色，但基于实际工作内容

---

### 4. Career Note 处理

**位置**: Professional Experience 最后（经历之后，Projects之前）

**格式**:
```html
<div style="font-style: italic; color: #555;">
    Career Note: 2019--2023 included independent investing, 
    language learning (English, German), and graduate preparation.
</div>
```

**原则**:
- 低调存在（斜体+灰色）
- 不主动提醒，但被发现gap时能解释
- 欧洲雇主喜欢这种"诚实但不张扬"的处理

---

### 5. 页边距设置

**HTML @media print**:
```css
@media print {
    body { padding: 0.5in; }
}
```

**PDF生成**:
```python
margin={'top': '0.5in', 'right': '0.5in', 
        'bottom': '0.5in', 'left': '0.5in'}
```

**原则**: 0.5in四边边距，专业排版，不贴边

---

### 6. Bio段落结构

**格式**:
```
[Role] with [核心认证/资质] and [年限] of experience in [核心领域].
Skilled in [技术栈] for [应用场景].
Experienced in [差异化技能] and [业务价值]。
```

**示例** (Data Engineer):
> Data Engineer with Databricks Data Engineer Professional certification 
> and 8+ years of experience building scalable data pipelines for financial 
> and behavioral data. Skilled in Python, Apache Spark, and Delta Lake for 
> processing high-volume transaction datasets. Experienced in CI/CD automation, 
> data governance, and delivering trusted datasets for data-driven decision-making.

**原则**: 3-4行，认证前置，关键词密集

---

### 7. 技能展示（4类别网格）

```
┌─────────────────────────────┬─────────────────────────────┐
│ Databricks & Spark          │ Data Engineering            │
│ Cloud & Streaming           │ CI/CD & DevOps              │
└─────────────────────────────┴─────────────────────────────┘
```

**原则**: 按技术类别分组，便于快速扫描

---

### 8. 关键词匹配策略

| JD关键词 | 简历体现位置 |
|----------|-------------|
| Apache Spark | Bio, Skills, 经历描述 |
| Databricks | 认证, Bio, Skills, 项目 |
| CI/CD | Bio, Skills, 经历描述 |
| Delta Lake | 认证, Skills, 项目 |
| Data governance | Bio, 经历描述 |
| Fintech/Financial | Bio, 经历描述 |

**原则**: 核心关键词在Bio、Skills、经历中重复出现3次以上

---

## 🔍 Proofread 检查清单

### 生成简历后必须检查：

- [ ] **个人信息**: 地址显示"Amsterdam, Netherlands"（非完整地址）
- [ ] **LinkedIn**: 链接为 https://www.linkedin.com/in/huangf06/
- [ ] **时间线**: 倒序排列，无时间重叠或gap未解释
- [ ] **职位名称**: 与目标角色匹配（Data Engineer/ML Engineer/Quant）
- [ ] **一页完整**: 内容在A4一页内，无溢出
- [ ] **页边距**: 四边0.5in，不贴边
- [ ] **Bio长度**: 3-4行，关键词密集
- [ ] **技能匹配**: JD要求的核心技能都有体现
- [ ] **量化指标**: 有数字支撑（100K+, 10M+, 40%等）
- [ ] **Career Note**: 位置正确，格式为斜体灰色

---

## 🛠️ 常用命令速查

```bash
# 1. 生成定制简历
python ai_resume_modifier.py template.html \
    --jd job_description.txt \
    --output generated/draft.html \
    --apply

# 2. 生成PDF
python html_to_pdf.py generated/draft.html

# 3. 重命名（PowerShell）
Copy-Item generated/draft.pdf \
    generated/Fei_Huang_Data_Engineer_[Company].pdf

# 4. 打开预览
Start-Process generated/Fei_Huang_Data_Engineer_[Company].html
& "$env:LOCALAPPDATA\SumatraPDF\SumatraPDF.exe" \
    generated/Fei_Huang_Data_Engineer_[Company].pdf
```

---

## 📊 角色定制速查表

### Data Engineer 定制要点
- **Bio强调**: 数据管道、ETL、CI/CD、数据治理
- **经历排序**: GLP → Baiquan → Ele.me
- **职位名称**: Data Engineer & Risk Lead / Quantitative Developer / Data Analyst
- **技能重点**: Databricks, Spark, Delta Lake, Airflow

### ML Engineer 定制要点
- **Bio强调**: 模型部署、MLOps、推荐系统、A/B测试
- **经历排序**: GLP → Ele.me → Baiquan
- **职位名称**: ML Engineer & Team Lead / Data Analyst / Quantitative Researcher
- **技能重点**: PyTorch, XGBoost, Model Serving, Feature Engineering

### Quant Researcher 定制要点
- **Bio强调**: 系统化交易、alpha研究、回测、统计建模
- **经历排序**: Baiquan → GLP → Ele.me
- **职位名称**: Quantitative Researcher / Risk Analyst / Data Analyst
- **技能重点**: Statistical Modeling, Backtesting, Time Series, Factor Research

---

## 📝 记忆更新（MEMORY.md）

每次生成简历后更新：

```yaml
# resume_project/html_resume/last_generated.yaml
last_generated:
  company: "Adyen"
  role: "Data Engineer"
  date: "2026-02-01"
  filename: "Fei_Huang_Data_Engineer_Adyen.pdf"
  key_customizations:
    - "强调fintech经验"
    - "突出Databricks认证"
    - "增加data governance关键词"
  result: "待投递"
```

---

## 🚀 下一步优化方向

1. **自动化爬虫**: LinkedIn/IamExpat职位自动抓取
2. **批量生成**: 多个职位并行处理
3. **投递追踪**: 与applications/tracker.csv集成
4. **反馈学习**: 根据面试反馈优化模板

---

*最后更新: 2026-02-01*
*确认版本: v1.0 (基于Adyen Data Engineer实战测试)*