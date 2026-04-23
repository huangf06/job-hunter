# Pipeline Full Verification Prompt

> Copy the text below into a new Claude Code session.

---

## 背景

2026-04-23 诊断发现：04-17 的简历模板回滚 + 04-22 bullet library v6.0 重写的 18 个 commit 从未推送到远端，CI 一直跑旧代码。已修复（commit 已推送，74 条污染分析已修正）。现在需要逐步验证整个管道的每一环确实产出预期效果。

## 任务

请按以下 7 步，**逐步执行**，每步完成后向我展示关键结果并等待我的确认再进入下一步。不要跳步，不要合并步骤。

### Step 1: 搜索配置审查

读取以下配置文件，向我展示：
- `config/search_profiles.yaml` — 当前激活的 profile 和关键词。重点关注：是否覆盖 ML Engineer、MLOps、Data Engineer 三条赛道
- `config/target_companies.yaml` — Greenhouse 目标公司列表是否合理
- `config/base/filters.yaml` — 6 条硬规则是否仍然适用

列出你认为需要调整的地方（如果有），等我确认。

### Step 2: 爬取新职位

执行：
```bash
python scripts/scrape.py --all --save-to-db --dry-run
```

先 dry-run 看一下会抓到多少。展示结果后等我确认，然后正式执行：
```bash
python scripts/scrape.py --all --save-to-db
```

展示：新增职位数、各平台抓取结果。

### Step 3: 导入 + 硬规则筛选

执行：
```bash
python scripts/job_pipeline.py --process
```

展示：
- 导入数量
- 硬规则筛选通过/拒绝数量及拒绝原因分布
- 确认没有异常大量拒绝

### Step 4: AI 评分 (C1) — 小批量

从最近 24 小时抓取的职位中，挑 3 个 已通过硬规则但尚未 AI 分析的职位，执行：
```bash
python scripts/job_pipeline.py --analyze-job JOB_ID
```

对每个职位，展示：
- `resume_tier` 是否为 `FULL_CUSTOMIZE`（**关键检查点**）
- `ai_score` 和 `recommendation`
- `tailored_resume` JSON 的顶层 keys（应包含 `bio`, `experiences`, `projects`, `skills`）
- bio 内容 — 确认末尾提及目标公司名（Signal 1），开头针对 JD 定制（Signal 2）

如果任何一个不是 `FULL_CUSTOMIZE` 或 `tailored_resume` 为空，**立即停下**报告问题。

### Step 5: 简历渲染

对 Step 4 中成功的职位生成 PDF：
```bash
python scripts/job_pipeline.py --generate
```

展示：
- 生成的 PDF 路径
- 用 `resume_visual_diff.py` 或手动对比一份生成的简历与面试成功参考简历（`interview_prep/20260225_Source_ag_Data_Engineer/Fei_Huang_Resume.pdf`）

结构性检查清单（逐项确认）：
- [ ] 2 页 flow layout（不是 1 页绝对定位）
- [ ] 15+ experience bullets
- [ ] 6 个技能类别
- [ ] Bio 末尾包含目标公司名
- [ ] Bio 开头针对 JD 定制
- [ ] Bullet 内容来自 bullet_library.yaml v6.0（非硬编码）

### Step 6: 漏斗统计

执行：
```bash
python scripts/job_pipeline.py --stats
```

展示完整漏斗数据。重点关注：
- AI high (>=5.0) 数量是否合理
- Resume generated 是否增加了

### Step 7: 总结 + Go/No-Go

汇总每一步的结果：
- 配置：OK / 需调整
- 爬取：OK / 异常
- 筛选：OK / 异常
- AI 分析：FULL_CUSTOMIZE 比例、tailored_resume 质量
- 简历渲染：结构性检查通过项数 / 6
- 漏斗：健康 / 异常

给出你的判断：管道是否可以进入 Phase 2（3 天窗口小批量投递）。
