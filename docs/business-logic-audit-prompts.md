# Business Logic Audit - Execution Prompts

Reference: `docs/business-logic-audit-2026-03-31.md`

Execution order: Session 1 first (data) → Session 2/3 in parallel → Session 4 depends on Session 1 results.

---

## Session 1: Data Diagnostics (run queries before making changes)

```
参考 docs/business-logic-audit-2026-03-31.md 的 "Data Queries Needed Before Acting" 部分。

对 Turso 数据库跑以下诊断查询，汇总结果：

1. 各 AI 分数段 (4-5, 5-6, 6-7, 7+) 的面试转化率
   - JOIN job_analysis + applications，按 ai_score 分段统计 applied / interview 数量和比率

2. 966 高分职位中未生成简历的原因
   - job_analysis WHERE ai_score >= 4.0 的 resume_tier 分布
   - 哪些 job_id 在 job_analysis 中 score >= 4.0 但不在 resumes 表中？按 resume_tier 分组统计

3. 各 search profile 来源的投递和面试转化率
   - jobs 表中是否有 source/profile 字段？如果有，按 profile 分组统计漏斗

4. DE 模板 vs ML 模板的面试转化率
   - resumes 表中 template_id 分布 + 对应的 applications 面试率

5. Backend 类职位 (title 含 "software engineer" 或 "backend" 但不含 "data"/"ml"/"ai") 的投递结果

把结果整理成一个表格写入 docs/business-logic-audit-2026-03-31.md 的新 section "## Data Query Results (2026-03-31)"，并根据数据更新 H3 的阈值建议。
```

---

## Session 2: Quick Config Fixes (H1 + H4 + M7)

```
参考 docs/business-logic-audit-2026-03-31.md，执行以下配置修改：

### H1. Career Note 重写
位置: config/ai_config.yaml (career_note) + src/resume_renderer.py (default value)

改为: "Career transition (2019–2023): Relocated to the Netherlands and completed M.Sc. in Artificial Intelligence at VU Amsterdam (GPA 8.2/10)."

要点：把 gap 和读硕合并成一个主动转型叙事，不提 investing 和 language learning。

### H4. Interests 行调整
位置: config/ai_config.yaml (interests)

改为: "Philosophy, strategy games, distance running, analytical writing"
去掉 Kant/existentialism/Dostoevsky 具体名字，加一个运动类兴趣。

### M7. 签证硬规则 (我有 zoekjaar，不需要 sponsorship，跳过此项 — 仅在文档中标记为 N/A)

完成后更新 docs/business-logic-audit-2026-03-31.md 中对应条目状态为 [DONE]。
```

---

## Session 3: Hard Rules + Search Profile Optimization (M1 + M2 + M3 + M6)

```
参考 docs/business-logic-audit-2026-03-31.md，执行以下修改：

### M6. Title whitelist 收紧
位置: config/base/filters.yaml → non_target_role.title_whitelist

把单独的 "software"、"platform"、"infrastructure" 改为复合模式：
- "software engineer", "software developer"
- "platform engineer", "data platform"
- "infrastructure engineer", "data infrastructure"

改完后确认不会误伤 "Data Platform Engineer"、"ML Infrastructure Engineer" 等目标角色。

### M2. 搜索 profile 清理
位置: config/search_profiles.yaml

- 禁用 backend_engineering (P2)，因为 Backend 模板未启用
- 从 data_science 中移除 "Data Analyst"、"BI Engineer"、"Data Consultant"
- 将 quant 降为 disabled 或 P3，确认 Optiver + Flow Traders 已在 target_companies.yaml

### M3. PhD 检测
位置: config/base/filters.yaml

新增硬规则: 如果 JD 正文中出现 "PhD required" / "PhD in [field]" 且没有 "or equivalent" / "or Master" 上下文，则 reject。注意只检测明确要求 PhD 的情况，不要误杀 "PhD preferred" 或 "PhD or equivalent experience"。

### M1. LinkedIn 语言过滤
位置: config/search_profiles.yaml (LinkedIn URL params)

检查 LinkedIn 搜索 URL 构造逻辑，加入 f_JC=en 参数过滤英文职位。保留 hard_filter 中的荷兰语检测作为 fallback。

每项改完后跑 pytest 确认不 break 现有测试，更新审计文档状态。
```

---

## Session 4: Backend Template + Threshold Adjustment (H2 + H3)

```
参考 docs/business-logic-audit-2026-03-31.md + 会话 1 的数据查询结果。

### H3. AI 评分阈值调整
位置: config/ai_config.yaml → thresholds.ai_score_generate_resume

根据会话 1 的数据结果决定新阈值 (预期 5.0)。同时更新 CLAUDE.md 中的相关描述。

### H2. Backend 模板启用
位置: config/template_registry.yaml

基于 DE 模板创建 Backend 模板:
- bio_positioning: "Software Engineer"
- bio: "Software Engineer with 6+ years building data-intensive Python systems across fintech, e-commerce, and logistics. Led a team of 5 engineers building real-time data pipelines and ML-driven decisioning systems. M.Sc. in AI."
- 复用 DE 模板的 experience slots，但重新排序: GLP 强调系统设计/Python，BQ 强调算法
- skills 重排: Python/SQL/API 优先，Spark/Delta Lake 降级
- enabled: true

确认 template routing 能正确将 "Software Engineer" / "Backend Engineer" 类 title 路由到新模板。跑测试验证。
```
