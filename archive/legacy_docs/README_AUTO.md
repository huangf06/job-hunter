# Job Hunter - 全自动模式 🤖

## 架构

```
定时触发 (Windows Task Scheduler)
    ↓
全自动流水线 (full_auto_pipeline.py)
    ↓
├─ 登录爬取 (auto_login_scraper.py)
│   ├─ LinkedIn 登录 + 搜索
│   └─ IamExpat 搜索
│
├─ AI 分析 (job_pipeline.py)
│   └─ 匹配度评分
│
├─ 简历生成 (ResumeTailor)
│   └─ 定制 HTML → PDF
│
└─ 投递准备 (Auto-apply)
    └─ 生成申请记录
```

## 设置步骤

### 1. 配置登录凭据

编辑 `config/credentials.json`：

```json
{
  "linkedin": {
    "email": "your-email@example.com",
    "password": "your-password",
    "logged_in": false
  }
}
```

### 2. 安装依赖

```powershell
pip install playwright
playwright install chromium
```

### 3. 设置定时任务（以管理员身份运行）

```powershell
.\setup_scheduler.ps1
```

这会创建定时任务：
- 每天 9:00, 12:00, 15:00, 18:00 运行
- 每次自动爬取 → 分析 → 生成简历

### 4. 手动测试

```powershell
# 测试登录
python scripts/auto_login_scraper.py --login --platform linkedin

# 测试搜索
python scripts/auto_login_scraper.py --search "Quant Researcher" --platform all

# 完整自动流程（单次）
python scripts/full_auto_pipeline.py
```

## 运行模式

### 模式 A：全自动定时运行（推荐）

```powershell
# 设置定时任务后，系统会自动运行
# 查看任务状态：
Get-ScheduledTask -TaskName "JobHunterAutoRun"
```

### 模式 B：手动单次运行

```powershell
# 完整流程
python scripts/full_auto_pipeline.py

# 仅爬取
python scripts/auto_login_scraper.py --auto

# 仅分析现有数据
python job_hunter_cli.py analyze

# 仅生成简历
python job_hunter_cli.py generate --company "Company Name"
```

### 模式 C：交互式（调试用）

```powershell
# 可见浏览器模式（便于调试）
python scripts/auto_login_scraper.py --login --platform linkedin --headless=false
```

## 关键词配置

编辑 `scripts/full_auto_pipeline.py` 中的 `CONFIG["search_keywords"]`：

```python
"search_keywords": [
    "Quant Researcher", "Quantitative Analyst", "Algorithmic Trading",
    "Machine Learning Engineer", "Deep Learning Engineer", 
    "Data Engineer", "Python Developer"
]
```

## 投递策略

当前实现：
- ✅ 自动爬取职位
- ✅ AI 分析匹配度
- ✅ 自动生成定制简历
- ⚠️ 自动投递（需要确认）

**安全考虑**：自动投递需要你的最终确认，避免误投。

要启用完全自动投递，修改 `full_auto_pipeline.py`：

```python
# 在 apply_jobs 方法中
async def apply_jobs(self):
    # 改为实际投递逻辑
    for job in self.high_priority_jobs:
        await self.actually_apply(job)  # 实现实际投递
```

## 监控与日志

### 查看运行日志

```powershell
# 查看最新报告
cat data/report_*.txt | tail -50

# 查看追踪数据
python job_hunter_cli.py stats
```

### 任务状态

```powershell
# 查看定时任务
Get-ScheduledTask -TaskName "JobHunterAutoRun"

# 查看上次运行结果
Get-ScheduledTaskInfo -TaskName "JobHunterAutoRun"

# 手动触发
Start-ScheduledTask -TaskName "JobHunterAutoRun"

# 删除任务
Unregister-ScheduledTask -TaskName "JobHunterAutoRun" -Confirm:$false
```

## 故障排除

### LinkedIn 登录失败

1. 检查凭据是否正确
2. 可能需要 2FA 验证码（首次登录）
3. LinkedIn 可能有反爬虫检测

**解决方案**：
- 使用 `--headless=false` 手动登录一次
- 保存登录状态（cookies）

### 爬取不到职位

1. 检查页面是否加载完成
2. 可能是动态内容，增加等待时间
3. 网站结构可能变化

**调试**：
```powershell
# 查看保存的调试文件
cat data/iamexpat_debug.html
```

### 定时任务不运行

1. 检查任务是否创建成功
2. 检查 Python 路径是否正确
3. 查看 Windows 事件查看器

## 安全提示

⚠️ **重要**：
- 凭据存储在本地 `config/credentials.json`
- 不要将凭据提交到 Git
- 建议添加 `.gitignore`：

```
config/credentials.json
*.log
data/debug_*
```

## 下一步优化

1. **验证码处理** - 集成 2FA 自动处理
2. **代理轮换** - 避免 IP 被封
3. **申请流程自动化** - 处理各种申请表单
4. **邮件通知** - 运行完成后发送邮件报告
5. **Web 界面** - 可视化监控面板

---

*系统已就绪，开始全自动求职！* 🚀
