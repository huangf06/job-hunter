# Job Hunter - 完全自动投递指南

## 快速开始

### 1. 测试模式（推荐先跑几天）
```powershell
# 每日运行（仅分析，不投递）
.\run_daily.ps1

# 或手动运行
python job_hunter_cli.py daily
```

### 2. 全自动模式
```powershell
# 启用自动投递
python job_hunter_cli.py daily --auto-apply

# 或
.\run_daily.ps1 -AutoApply
```

### 3. 设置定时任务
```powershell
# 每天上午10点自动运行（测试模式）
.\setup_scheduler.ps1 -Hour 10 -Minute 0

# 每天上午10点自动运行（全自动投递）
.\setup_scheduler.ps1 -Hour 10 -Minute 0 -AutoApply

# 删除定时任务
.\setup_scheduler.ps1 -Remove
```

## 配置说明

### 自动投递阈值
编辑 `config.json`:
```json
{
  "auto_apply": {
    "enabled": true,           // 总开关
    "score_threshold": 7.5,    // 自动投递最低分数
    "daily_limit": 10,         // 每日最多投递数
    "delay_ms": 30000          // 每次投递间隔（毫秒）
  }
}
```

### 黑名单设置
```json
{
  "blacklist": {
    "companies": [],                    // 跳过这些公司
    "titles_containing": ["senior"],    // 跳过包含这些词的职位
    "min_years_experience": 4           // 跳过要求4年以上经验的
  }
}
```

### 个人信息
```json
{
  "personal_info": {
    "first_name": "Fei",
    "last_name": "Huang",
    "email": "huangf06@gmail.com",
    "phone": "+31612345678",
    "visa_status": "Search Year Visa"
  }
}
```

## 支持的自动投递平台

| 平台 | 支持程度 | 说明 |
|------|---------|------|
| LinkedIn Easy Apply | ✅ 完全自动 | 自动点击、填表、上传、提交 |
| Greenhouse | ⚠️ 半自动 | 自动填写标准字段，自定义问题需人工 |
| Lever | ⚠️ 半自动 | 同上 |
| 邮件申请 | ⚠️ 待实现 | 生成邮件内容，需手动发送 |
| 其他 | ❌ 人工 | 整理成清单，手动处理 |

## 安全机制

1. **Rate Limiting**: 每次投递间隔 30 秒，每日上限 10 个
2. **黑名单过滤**: 自动跳过不符合条件的职位
3. **分数阈值**: 只有 7.5 分以上的职位才会自动投递
4. **日志记录**: 所有操作记录，可追溯

## 监控与报告

### 每日报告
运行后会生成报告，包含：
- 爬取到的职位数量
- 分析结果（高/中/低优先级）
- 生成的简历数量
- 投递状态（成功/失败/跳过）

### 日志文件
日志保存在 `logs/` 目录：
- `daily_YYYYMMDD_HHMM.log` - 每日运行日志

### 追踪文件
- `data/job_tracker.json` - 所有职位追踪
- `data/applications.json` - 申请记录

## 故障排除

### 投递失败
1. 检查 `config.json` 中的个人信息是否正确
2. 查看日志文件了解具体错误
3. 手动测试该职位的申请流程

### 定时任务不运行
```powershell
# 检查任务状态
schtasks /query /tn JobHunter-Daily /v

# 手动运行测试
schtasks /run /tn JobHunter-Daily
```

### 浏览器自动化问题
- LinkedIn 可能要求重新登录
- 某些页面结构变化可能导致脚本失效
- 验证码需要人工处理

## 进阶用法

### 只投递特定公司
```powershell
python job_hunter_cli.py apply --company "Picnic" --no-dry-run --auto
```

### 查看统计
```powershell
python job_hunter_cli.py stats
```

### 手动添加职位
```powershell
python job_hunter_cli.py add --interactive
```

## 注意事项

⚠️ **重要提醒**:
1. 先在测试模式跑几天，确认一切正常再启用自动投递
2. 自动投递前确保简历内容正确
3. 定期检查 LinkedIn 登录状态
4. 注意每日投递上限，避免被封号

## 更新记录

- 2026-02-03: 实现 LinkedIn Easy Apply 自动化
- 2026-02-03: 添加定时任务支持
