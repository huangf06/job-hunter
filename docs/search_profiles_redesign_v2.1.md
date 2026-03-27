# Search Profiles Redesign - v2.1 (Updated)
**Date:** 2026-02-27
**Update:** Added Group 6 (ML Research) to maximize coverage
**Backup:** `config/search_profiles.yaml.backup-*`

## 设计理念

从"关键词堆砌"转向"职位类型分组"，按照 Fei 的背景和目标职位的核心技能来组织搜索。

**核心原则：最大化覆盖率，用硬规则和 AI 评分来筛选，而不是在搜索阶段预先排除。**

## 新配置（6 组）

| Group | Profile Name | Keywords (OR count) | Priority | Target |
|-------|-------------|---------------------|----------|--------|
| 1 | data_engineering | Data Engineer, Analytics Engineer, Data Platform Engineer, ETL Engineer (4) | 1 | 数据管道建设（主战场） |
| 2 | ml_engineering | ML Engineer, AI Engineer, MLOps Engineer (4) | 1 | ML 系统工程（差异化） |
| 3 | backend_engineering | Software Engineer, Backend Engineer, Python Developer, Backend Developer (4) | 2 | 通用后端（保底） |
| 4 | data_science | Data Scientist, Data Analyst, BI Engineer, Data Consultant (4) | 3 | 数据科学/分析（边缘） |
| 5 | quant | Quantitative Researcher/Developer/Analyst, Quant Trader (4) | 1 | 量化交易（高价值） |
| 6 | ml_research | ML Researcher, Research Engineer, Applied Scientist, Research Scientist (4) + Deep Learning, Computer Vision, NLP, LLM (4) | 2 | ML 研究（学术导向） |

**Total:** 6 profiles, 7 queries, 28 OR conditions

## 旧配置（3 组）

| Profile | Keywords (OR count) | Issues |
|---------|---------------------|--------|
| ml_data | 10 OR conditions (ML/DL/CV/NLP/Data/MLOps/AI/LLM/Analytics/Consultant) | ❌ 触发 LinkedIn 反爬限流 |
| backend_data | 3 OR conditions | ✅ 正常 |
| quant | 5 OR conditions | ✅ 正常 |

**Total:** 3 profiles, 3 queries, 18 OR conditions

## 关键改进

### 1. 解决反爬问题
- **旧配置**：ml_data 有 10 个 OR 条件 → `ERR_FAILED`
- **新配置**：每个 query 最多 4 个 OR → 避免触发限流

### 2. 更精准的职位定位
- **旧配置**：混合了不同类型的职位（ML 研究 + 数据工程 + 分析）
- **新配置**：按职位类型分组，每组有明确的目标和优先级

### 3. 更好的匹配度控制
- **Group 1 (data_engineering)**：最匹配 Fei 的 6 年数据管道经验
- **Group 2 (ml_engineering)**：突出 ML 系统工程能力（非纯研究）
- **Group 3 (backend_engineering)**：保底选项，覆盖通用软件工程
- **Group 4 (data_science)**：边缘匹配，可能偏分析但保留以防遗漏
- **Group 5 (quant)**：独立保持，因为目标公司和要求完全不同

### 4. 保留研究岗关键词（重要更新）

**初始设计错误**：移除了 Deep Learning, Computer Vision, NLP, LLM
**用户反馈**："我也可以做研究岗的不是吗？只要能帮助我找到职位，我什么都可以干。"

**修正后的策略**：
- ✅ 新增 Group 6 (ml_research)：专门覆盖研究导向的职位
- ✅ 保留所有学术关键词：Deep Learning, Computer Vision, NLP, LLM
- ✅ 新增研究职位名：ML Researcher, Research Engineer, Applied Scientist, Research Scientist
- ✅ 最大化覆盖率：让硬规则和 AI 评分来筛选，而不是在搜索阶段预先排除

**Fei 的研究背景支持**：
- 硕士论文：Uncertainty Quantification in RL（150 training runs, 5 UQ methods, SLURM HPC）
- 深度学习实战：PyTorch, TensorFlow, ML4QS 课程项目
- 完全有资格申请 ML Research Engineer / Applied Scientist 岗位

## 预期效果

### LinkedIn 搜索成功率
- **旧配置**：ml_data 100% 失败，backend_data/quant 成功
- **新配置**：预期所有 5 组都能成功（每组 ≤4 OR）

### 职位覆盖率
- **旧配置**：18 个关键词，但 10 个在失败的 query 中
- **新配置**：28 个关键词，分布在 7 个成功的 queries 中
- **预期**：覆盖率提升 ~100%（不仅修复了失败的 queries，还新增了研究岗关键词）

### 匹配质量
- **旧配置**：混合了研究岗（Deep Learning, NLP）和工程岗
- **新配置**：聚焦工程岗，减少不相关职位
- **预期**：硬规则通过率提升 ~20%

## 回滚方法

如果新配置有问题，可以快速回滚：

```bash
# 查看备份文件
ls -lh config/search_profiles.yaml.backup-*

# 回滚到最新备份
cp config/search_profiles.yaml.backup-YYYYMMDD-HHMMSS config/search_profiles.yaml

# 或者启用 legacy profiles
# 编辑 config/search_profiles.yaml，设置 ml_data.enabled = true
```

## 测试建议

1. **本地测试单个 profile**：
   ```bash
   python scripts/scrape.py --platform linkedin --profile data_engineering --dry-run
   ```

2. **CI 测试（手动触发）**：
   - 在 GitHub Actions 中手动触发 workflow
   - 观察 5 个 profiles 是否都能成功爬取

3. **监控指标**：
   - LinkedIn 搜索成功率（目标：100%）
   - 新职位数量（目标：≥ 旧配置的 150%）
   - 硬规则通过率（目标：≥ 旧配置的 120%）

## IamExpat 配置

同步更新了 IamExpat 搜索关键词，与 LinkedIn 保持一致：

- data_engineering: data engineer, analytics engineer, data platform engineer
- ml_engineering: machine learning engineer, ml engineer, mlops engineer
- backend_engineering: python developer, backend engineer, software engineer
- data_science: data scientist, data analyst, data consultant
- quant: quantitative

## 下一步

1. ✅ 备份旧配置
2. ✅ 实施新配置
3. ⏳ 本地测试（可选）
4. ⏳ 提交到 git
5. ⏳ 观察下一次 CI run 的效果
