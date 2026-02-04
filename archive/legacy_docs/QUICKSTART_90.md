# Job Hunter 90%自动化 - 快速开始指南

> 最后更新: 2026-02-03

---

## 🎯 核心理念

**自动化能自动化的，人工处理关键的**

- ✅ 职位爬取、筛选、评分、简历生成 → **全自动**
- ⚠️ 简历审核、最终投递 → **人工确认 (5-10分钟/天)**

---

## 🚀 快速开始

### 1. 每日自动流程 (设置定时任务)

```powershell
# Windows Task Scheduler 设置
# 每天上午9点运行

Action: Start a program
Program: python
Arguments: C:\Users\huang\.openclaw\workspace\job-hunter\simplified_hunter.py daily
```

### 2. 晚上审阅 (你只需5-10分钟)

```powershell
cd job-hunter
$env:PYTHONIOENCODING="utf-8"
python simplified_hunter.py review
```

交互界面:
```
[1/3] Machine Learning Engineer @ Picnic
    公司: Picnic
    地点: Amsterdam
    评分: 8.0/10
    简历: output/Fei_Huang_Picnic_ML_Engineer.pdf

    [Y]投递 [N]跳过 [O]打开链接 [D]详情 [Q]退出: 
```

按 `Y` → 自动打开申请页面和简历文件夹，你只需检查并提交

---

## 📁 文件结构

```
job-hunter/
├── simplified_hunter.py      # 主程序 (90%自动化)
├── process_today.py          # 处理今日抓取的数据
├── STRATEGY_90_PERCENT.md    # 策略文档
├── QUICKSTART.md            # 本文件
│
├── assets/
│   ├── bullet_library.yaml   # 简历内容库
│   └── personal_info.yaml    # 个人信息
│
├── templates/
│   └── resume_master.html   # 简历模板 (主模板)
│
├── scripts/
│   └── playwright_scraper.py # 职位爬虫
│
├── data/
│   ├── jobs_pending.json    # 待处理职位
│   ├── jobs_applied.json    # 已投递记录
│   └── linkedin_*.json      # 爬取的原始数据
│
└── output/
    └── Fei_Huang_*.pdf      # 生成的简历
```

---

## 🛠️ 可用命令

```bash
# 1. 爬取职位 (Playwright爬虫)
python scripts/playwright_scraper.py --platform linkedin --search "machine learning engineer"
python scripts/playwright_scraper.py --daily  # 抓取所有关键词

# 2. 处理今日抓取的数据 (筛选+评分+生成简历)
python process_today.py

# 3. 审阅模式 (人工确认并投递)
python simplified_hunter.py review

# 4. 查看统计
python simplified_hunter.py stats

# 5. 完整测试模式
python simplified_hunter.py test
```

---

## ⚙️ 配置调整

### 简历模板路径
模板文件位于 `templates/resume_master.html`，在 `Config` 类中配置:

```python
class Config:
    RESUME_TEMPLATE = TEMPLATES_DIR / "resume_master.html"  # 简历模板路径
    MIN_SCORE_TO_GENERATE = 6.0   # 生成简历的最低分数
    MIN_SCORE_TO_REVIEW = 7.0     # 推荐审阅的最低分数
    MAX_JOBS_TO_REVIEW = 10       # 每天最多审阅数量
```

**注意**: 如需更换模板，修改 `RESUME_TEMPLATE` 路径即可。

---

## 📊 筛选规则

### 自动过滤 (不生成简历)
- Dutch required
- German/French required
- 8+ / 10+ years experience
- Lead / Principal / Director 级别

### 警告但不过滤
- Senior 职位 (扣1分)
- 5-7 years experience (扣0.5分)

---

## 🔄 工作流程

```
Step 1: 爬取职位 (Playwright爬虫)
  python scripts/playwright_scraper.py --daily
  ↓
Step 2: 处理数据 (自动筛选+评分+生成简历)
  python process_today.py
  ↓
Step 3: 人工审阅 (5-10分钟)
  python simplified_hunter.py review
  按Y确认 → 浏览器自动打开 → 你检查并提交
  ↓
系统自动记录到 jobs_applied.json
```

---

## 🎮 实际操作示例

### 场景1: 发现好职位

```
[1/3] Machine Learning Engineer @ Picnic
    评分: 8.0/10
    简历: ✅ 已生成

    [Y]投递 [N]跳过 [O]打开链接 [D]详情 [Q]退出: Y
    
    [APPLYING] Picnic...
    [OK] 已打开申请页面和简历，请完成投递后按回车继续...
```

你只需:
1. 在浏览器中检查申请表单
2. 上传已生成的PDF简历
3. 点击提交
4. 按回车继续下一个

### 场景2: 跳过不合适的

```
[2/3] Senior Data Scientist @ Booking.com
    评分: 6.5/10
    
    [Y]投递 [N]跳过 [O]打开链接 [D]详情 [Q]退出: N
    跳过原因 (可选): 要求5年经验，我经验不够
    [SKIPPED]
```

### 场景3: 查看详情

```
    [Y]投递 [N]跳过 [O]打开链接 [D]详情 [Q]退出: D
    
    描述: We are looking for a Machine Learning Engineer to join our team. 
    You will work on recommendation systems and demand forecasting. 
    Requirements: Python, PyTorch, 3+ years experience...
```

---

## ⚠️ 为什么不做100%自动化?

1. **简历错误风险** - AI可能有事实错误，人工扫一眼可避免尴尬
2. **申请页面复杂** - 每个公司流程不同，全自动容易卡住
3. **验证码** - 频繁操作可能触发验证
4. **策略灵活性** - 人工层允许快速调整策略

---

## 📈 预期效果

| 指标 | 之前 | 现在 | 提升 |
|------|------|------|------|
| 每日职位发现 | 手动搜索 | 自动20-30个 | ∞ |
| 筛选时间 | 30分钟 | 0分钟 | 100% |
| 简历生成 | 10分钟/份 | 1分钟/份 | 90% |
| 人工投入 | ~2小时 | ~10分钟 | 92%↓ |

---

## 📝 更新日志

### 2026-02-04
- [x] 修复简历模板路径: `resume_master.html`
- [x] 更新 Bio 定制逻辑，适配新模板结构
- [x] 更新文档，明确爬虫→处理→审阅三步流程

### TODO
- [ ] 接入真实AI分析 (替换模拟评分)
- [ ] 添加更多ATS系统自动填表
- [ ] 邮件通知功能
- [ ] 投递状态自动检测

---

*为 Fei Huang 的荷兰求职之旅设计* 🌷
