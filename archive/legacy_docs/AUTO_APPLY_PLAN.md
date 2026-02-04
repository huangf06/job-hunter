# 完全自动投递方案 - Zero Intervention Mode

## 目标
实现完全自动化，无需人工审阅，每天自动运行。

## 策略: 分层自动化

### 第一层: LinkedIn Easy Apply (完全自动)
- LinkedIn 的 Easy Apply 流程标准化
- 可以自动化: 点击、填表、上传PDF、提交
- 实现: Playwright 自动化脚本

### 第二层: 标准申请页面 (半自动)
- 常见 ATS 系统 (Greenhouse, Lever, Workday)
- 自动化: 打开页面、预填信息、上传简历
- 人工: 可能需要处理验证码或复杂表单

### 第三层: 邮件申请 (自动)
- 发送简历到指定邮箱
- 自动生成求职邮件内容

### 第四层: 仅整理 (暂不自动)
- 复杂流程或不确定的申请
- 整理成清单，供人工快速处理

## 自动投递规则

```json
{
  "auto_apply": {
    "enabled": true,
    "score_threshold": 7.5,
    "daily_limit": 10,
    "platforms": {
      "linkedin_easy_apply": "full_auto",
      "greenhouse": "semi_auto",
      "lever": "semi_auto",
      "email": "full_auto",
      "other": "manual_list"
    },
    "blacklist": {
      "companies": [],
      "titles_containing": ["senior", "lead", "principal"],
      "min_experience": 3
    }
  }
}
```

## 实现步骤

### Phase 1: 配置系统 (今天)
- [x] 读取现有配置
- [ ] 创建 auto_apply 配置模块
- [ ] 实现投递决策逻辑

### Phase 2: LinkedIn Easy Apply 自动化 (今天)
- [ ] 分析 Easy Apply 流程
- [ ] 实现 Playwright 脚本
- [ ] 测试单个职位投递

### Phase 3: 邮件申请自动化 (今天)
- [ ] 生成求职邮件模板
- [ ] 实现邮件发送功能

### Phase 4: 整合与测试 (明天)
- [ ] 整合到 daily 流程
- [ ] 设置定时任务
- [ ] 测试完整流程

## 风险控制

1. **Rate Limiting**: 每个平台设置延迟和每日上限
2. **错误处理**: 失败时记录并跳过，不中断流程
3. **黑名单**: 避免重复投递或投递不合适的职位
4. **日志记录**: 所有操作记录，可追溯

## 通知机制

- 每日报告: 爬取数量、分析结果、投递状态
- 异常通知: 投递失败、需要人工介入的情况
- 周报: 申请统计、回复情况
