# LinkedIn Search Interface Update - 2026-02-27

## LinkedIn UI Changes (2026)

LinkedIn 更新了职位搜索界面，主要变化：

### 1. Workplace Type 简化
**旧版**：
- On-site (1)
- Remote (2)
- Hybrid (3)

**新版**：
- 只有一个 "Remote" 开关（没有 Hybrid/On-site 分离）

### 2. Job Type 选项
- Full-time
- Part-time
- Contract
- Internship
- Volunteer

### 3. 新增过滤器
- Easy Apply
- Under 10 applicants
- In my network
- AI-powered search (beta)

## 我们的应对策略

### 1. Job Type：专注 Full-time ✅

**决策**：只搜索 Full-time 职位

**理由**：
- ✅ Kennismigrant 签证要求全职雇佣
- ✅ Contract 通常不提供签证担保
- ✅ Part-time 不符合签证要求
- ❌ Internship/Volunteer 不适用

**实施**：
```yaml
defaults:
  job_type: "F"  # F=Full-time
```

LinkedIn URL 参数：`f_JT=F`

### 2. Workplace Type：不设限制 ✅

**决策**：移除 `workplace_type` 过滤，搜索所有类型

**理由**：
- ❌ 新版 LinkedIn 只有 "Remote" 开关，没有 Hybrid/On-site 分离
- ✅ 如果选 "Remote"，会错过所有 Hybrid 和 On-site 职位
- ✅ 荷兰大部分科技公司是 Hybrid（2-3 天 office）
- ✅ 不设限制 = 搜索所有类型（Remote, Hybrid, On-site）

**实施**：
```yaml
defaults:
  # workplace_type removed
  # Leaving unset to capture all workplace types
```

**硬规则保护**：
- `location_restricted` 规则会过滤 "onsite only" 和 "no relocation/visa"
- 保留灵活性，不错过 Hybrid 机会

### 3. 其他新选项：不启用 ❌

**Easy Apply**：
- ❌ 不启用：会限制结果，很多好公司不用 Easy Apply
- 我们的系统已经自动化了申请流程

**Under 10 applicants**：
- ❌ 不启用：会大幅减少结果
- 虽然竞争小，但会错过很多好机会

**In my network**：
- ❌ 不启用：LinkedIn network 可能不够大

## 代码修改

### 1. `config/search_profiles.yaml`
```yaml
defaults:
  location: "Netherlands"
  date_posted: "r86400"      # Past 24 hours
  job_type: "F"              # F=Full-time (NEW)
  # workplace_type removed   # (REMOVED)
  sort_by: "DD"              # DD=Date
  max_jobs: 999
```

### 2. `scripts/scrape.py` + `src/scrapers/linkedin*.py`
```python
params = {
    "keywords": keywords,
    "location": location,
    "f_TPR": defaults.get("date_posted", "r86400"),
    "sortBy": defaults.get("sort_by", "DD")
}

# Add job_type if specified (NEW)
if "job_type" in defaults:
    params["f_JT"] = defaults["job_type"]

# Add workplace_type if specified (OPTIONAL)
if "workplace_type" in defaults:
    params["f_WT"] = defaults["workplace_type"]
```

## LinkedIn URL 参数参考

| 参数 | 说明 | 可选值 |
|------|------|--------|
| `f_JT` | Job Type | F=Full-time, P=Part-time, C=Contract, I=Internship, V=Volunteer |
| `f_WT` | Workplace Type | 1=On-site, 2=Remote, 3=Hybrid |
| `f_TPR` | Time Posted Range | r86400=24h, r604800=7d, r2592000=30d |
| `sortBy` | Sort Order | DD=Date, R=Relevance |

## 预期效果

### 覆盖率变化
- **Full-time 职位**：100%（之前可能包含 Part-time/Contract）
- **Workplace Type**：+50%（之前只搜 On-site + Hybrid，现在包含所有类型）
- **Remote 职位**：+100%（之前被排除，现在包含）

### 质量控制
- ✅ 硬规则过滤 "onsite only" 和 "no visa"
- ✅ 硬规则过滤 "freelance/ZZP only"
- ✅ 保留灵活性，不错过 Hybrid 机会

## 测试建议

1. **本地测试**：
   ```bash
   python scripts/scrape.py --platform linkedin --profile data_engineering --dry-run
   ```
   检查生成的 URL 是否包含 `f_JT=F` 且不包含 `f_WT`

2. **观察下一次 CI run**：
   - 检查新职位数量是否增加（预期 +30-50%）
   - 检查是否包含 Remote 和 Hybrid 职位
   - 检查是否有 Part-time/Contract 误入（应该没有）

## 回滚方法

如果新配置有问题，可以回滚：

```yaml
defaults:
  workplace_type: "1,3"  # 恢复 On-site + Hybrid
  # job_type: "F"        # 移除 Full-time 限制
```

## 参考

- LinkedIn Job Search URL 结构：`https://www.linkedin.com/jobs/search?keywords=...&location=...&f_JT=F&f_TPR=r86400&sortBy=DD`
- 用户反馈：2026-02-27，观察到 LinkedIn 新界面变化
