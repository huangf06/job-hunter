# Job Hunter v2.0 — 全面系统审查结果

**审查日期**: 2026-02-23
**审查范围**: 全部 11 个维度, ~30 个文件
**方法**: 6 个并行审查代理 + 人工综合

---

## 1. 数据完整性与数据库设计

### 🔴 P0 — Sentinel 记录与合法拒绝不可区分
**位置**: `src/db/job_db.py:612-618, 674-680`

AI 分析失败时保存 `tailored_resume='{}'` 的 sentinel 记录，但它与 AI 故意拒绝的记录格式完全相同。这意味着：
- 网络超时、JSON 解析失败等**可恢复错误**被永久标记为 "已拒绝"
- `clear_rejected_analyses()` 无法区分"应该重试"和"真正不匹配"
- 没有手动方法识别哪些是失败 vs 真正拒绝

**建议**: 添加 `analysis_status` 列 (`success`/`rejected`/`failed`)，区分三态

### 🔴 P0 — 残留的非 UTC 时间戳
**位置**: `src/db/job_db.py:742, 1506`

大部分已在 commit `20c743d` 中修复，但 `import_from_json()` 和 `export_to_json()` 中仍使用 `datetime.now().isoformat()` (无 timezone)。CI (UTC) 和本地 (CET) 产生的时间戳不一致。

### 🟡 P1 — Upsert 只更新 description，忽略其他字段
**位置**: `src/db/job_db.py:749-763`

`insert_job()` 的 ON CONFLICT 只比较 description 长度，其他字段 (location, posted_date, source) 在冲突时不更新。如果同一职位从不同平台爬取，后续平台的 metadata 被静默丢弃。

### 🟡 P1 — `job_analysis.job_id` 缺少索引
**位置**: `src/db/job_db.py:352`

有 `idx_job_analysis_score` 和 `idx_job_analysis_recommendation`，但没有 `job_id` 索引。所有 JOIN 查询做全表扫描。

**建议**: `CREATE UNIQUE INDEX idx_job_analysis_job_id ON job_analysis(job_id);`

### 🟡 P1 — Batch sync 失败静默降级
**位置**: `src/db/job_db.py:642-658`

`batch_mode()` 的 finally 块中 sync 失败只打 warning，不抛异常。本地数据与 Turso 可能不一致且无人知晓。

### 🟡 P2 — `ai_scores` 表已弃用但仍被 export 使用
**位置**: `src/db/job_db.py:1548-1550`

`export_to_json` 仍查询 `ai_scores` 表获取 min_score。应改用 `job_analysis.ai_score`。

### 🟢 P3 — `emails` 表在 archive 逻辑中引用但 schema 不存在
**位置**: `src/db/job_db.py:1255`

靠 try/except 跳过。应从 `related_tables` 列表中移除。

---

## 2. AI 分析器可靠性

### 🟢 整体优秀 — 无关键问题

**Bullet-by-ID 系统** (`src/ai_analyzer.py:222-399`):
- 重复 ID 打警告并覆盖 (设计决策，可接受)
- 混合有效/无效 ID 正确处理
- 向后兼容完整 (精确文本匹配仍支持)

**Bio Builder** (`src/ai_analyzer.py:401-522`):
- 所有验证分支完备 (role_title, domain_claims, closer_options)
- 字符串 "null" → Python None 正确处理
- 年份自动 cap 到 max_years_claim

**Token 预算** (`src/db/job_db.py:1415-1427`):
- save 和 query 都用 UTC，一致
- 80% 预警 + 100% 硬停正确实现

**Prompt 安全** (`src/ai_analyzer.py:561-570`):
- `str.format()` 前做了 `{` → `{{` 转义
- `re.escape()` 用于 keyword matching
- 无 ReDoS / prompt injection 风险

### 🟡 P2 — 未配置的 experience/project 静默跳过
**位置**: `src/ai_analyzer.py:127-132`

新增到 `bullet_library.yaml` 的 section 未加到 `ai_config.yaml` 的 `experience_keys`/`project_keys` 时静默跳过，只打 INFO。

---

## 3. 简历验证与渲染

### 🟡 P1 — Playwright PDF 生成资源泄漏风险
**位置**: `src/resume_renderer.py:446-491`

`browser.close()` 在 finally 中，正常工作。但如果 `close()` 本身挂起 (Windows Chromium 已知问题)，进程泄漏。无超时保护。

### 🟡 P2 — Cover Letter job_id 未做文件名清理
**位置**: `src/cover_letter_renderer.py:113-114`

`job_id_short = job.get('id', 'unknown')[:8]` 未经 `_safe_filename()` 处理。

### 🟡 P2 — 模板 href 属性 autoescape 不足
**位置**: `templates/base_template.html:206-215`

`autoescape=True` 不保护 URL context (`href="tel:{{ phone }}"`)。实际风险极低 (数据来自自控 YAML)。

### 🟢 P3 — 验证门控完备
- Title validation: BLOCKING ✓
- Skill category whitelist (10 categories): BLOCKING ✓
- Excluded skills: BLOCKING ✓
- 最少 2 experiences, 3 skill categories, 1 project: BLOCKING ✓
- 每个 experience/project 至少 1 bullet: BLOCKING ✓
- Post-render QA check: 额外安全层 ✓

---

## 4. 爬虫系统健壮性

### 🔴 P1 — Lever/Greenhouse 无 429 Rate Limit 处理
**位置**: `src/scrapers/lever.py:31-41`, `src/scrapers/greenhouse.py:39-49`

retry 只 catch `ConnectionError` 和 `Timeout`。`raise_for_status()` 抛出的 `HTTPError` (包括 429) 不在 catch 范围。单个 429 响应导致整个爬虫崩溃。

**建议**:
```python
except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
    if hasattr(e, 'response') and e.response.status_code in (429, 503):
        wait = int(e.response.headers.get('Retry-After', 60))
        time.sleep(wait)
```

### 🟡 P1 — IamExpat 选择器单一无降级
**位置**: `src/scrapers/iamexpat.py:43-48`

只依赖 `a[href*='/career/jobs-netherlands/']`。网站改版即静默返回空列表。

### 🟡 P1 — IamExpat 详情页复用列表页 page 对象
**位置**: `src/scrapers/iamexpat.py:122`

详情页加载失败后，page URL 停留在详情页，后续列表页可能异常。应使用独立 page。

### 🟡 P2 — LinkedIn cookie 过期检测不完整
**位置**: `scripts/linkedin_scraper_v6.py:314-317`

只检查 URL redirect，不检查页面内容。

### 🟡 P2 — LinkedIn JD HTML 清理丢失列表结构
**位置**: `scripts/linkedin_scraper_v6.py:840`

`re.sub(r'<[^>]+>', ' ', jsonld)` 丢失 `<li>` 列表结构。应使用 greenhouse.py 的 `_html_to_text()`。

### 🟡 P2 — Multi-scraper 部分失败不报告
**位置**: `scripts/multi_scraper.py:112-117`

各平台错误内部 catch，聚合统计隐藏哪个平台失败。

---

## 5. 筛选与评分系统

### 🟢 整体良好

- Regex 规则 exception 只查 title (**设计正确**)
- 评分权重在 `scoring.yaml` 集中配置
- Filter 结果保存到 `filter_results` 表

### 🟡 P2 — Body 评分 `short_jd` 类别被误作关键词处理
**位置**: `scripts/job_pipeline.py:444-469`

`short_jd` 是 penalty dict，但循环当关键词类处理。无实际影响 (因 "threshold"/"penalty" 不出现在 JD 中)。

### 🟡 P2 — 多规则匹配只记录第一个
只记录第一条拒绝原因，无法看到完整拒绝理由。

---

## 6. 本地工作流

### 🟡 P1 — Windows 上 `file:///` URI 用反斜杠
**位置**: `scripts/job_pipeline.py:616`

`<a href="file:///{submit_pdf}">` 在 Windows 上无法打开。应用 `Path(submit_pdf).as_uri()`。

### 🟡 P2 — Checklist server 无 CORS 头
**位置**: `src/checklist_server.py`

localhost 内工作正常，但 `127.0.0.1` vs `localhost` 场景 CORS 失败。

### 🟢 — `--finalize` 幂等性良好
state.json 删除后再次运行安全退出。

---

## 7. 面试调度系统

### 🟡 P1 — Token `_save_tokens()` Windows 原子性
**位置**: `src/google_calendar.py`

Windows 上 `os.rename()` 目标已存在时抛异常。与 MCP 并发写入有竞态窗口。

### 🟢 — 时区处理正确
`_generate_candidate_slots()` 正确使用 `astimezone(self.tz)` 转换。三维评分模型与设计一致。

---

## 8. CI/CD 与部署

### 🟢 — notify.py funnel 统计已修复
`funnel.get("rejected", 0)` 正确 (commit 1945ca7 修复)。

### 🟡 P2 — Turso CI 连接无重试
服务暂时不可用时流水线直接失败。

---

## 9. 配置管理与安全

### 🟢 安全实践良好
- `.gitignore` 覆盖 `.env`, `*.db`, cookies, tokens ✓
- `yaml.safe_load()` ✓
- SQL 参数化查询 ✓

### 🟡 P2 — YAML 配置无 schema 验证
Key 拼错时静默使用默认值。

### 🟡 P2 — 依赖版本未锁定
无 `requirements.txt` 精确版本锁定。

---

## 10. 代码质量

### 🟢 架构清晰
- `scripts/` vs `src/` 分离严格
- 无 bare except

### 🟡 P2 — Pipeline 全部用 print() 不用 logging
CI 无法控制日志级别。

### 🟡 P3 — 死代码
`scripts/job_parser.py`, `scraper_incremental.py`, `scraper_incremental_v32.py` 未使用。

---

## 11. 已知问题根因

### Rejection 追踪缺口
**根因**: mail_processor 的 `lookback_days: 2` + `unread_only=True` + `mark_as_read=True`
**job-hunter 侧补救**: 添加 `--check-stale-applied` 命令列出 >30 天仍 "applied" 的职位

### Windows Turso 栈溢出
**当前 workaround**: 禁用 Turso 回退本地 SQLite
**更好方案**: Turso HTTP API / WSL2 / 等 libsql-python 修复

---

## 总结

### Top 5 最紧急问题

| # | 问题 | 位置 | 优先级 |
|---|------|------|--------|
| 1 | Sentinel 记录无法区分失败/拒绝 | job_db.py:612-680 | P0 |
| 2 | 残留的 `datetime.now()` (无 UTC) | job_db.py:742, 1506 | P0 |
| 3 | Lever/Greenhouse 无 429 处理 | lever.py:31, greenhouse.py:39 | P1 |
| 4 | Windows file:/// URI 路径错误 | job_pipeline.py:616 | P1 |
| 5 | `job_analysis.job_id` 缺索引 | job_db.py:352 | P1 |

### Top 5 最有价值的改进

| # | 改进 | 影响 |
|---|------|------|
| 1 | 添加 `analysis_status` 列 | 解决 sentinel 歧义，支持失败重试 |
| 2 | Scraper 统一 rate limiter | 所有 API 爬虫的 429/503 弹性 |
| 3 | Pipeline 日志 print → logging | CI 可观测性大幅提升 |
| 4 | YAML config schema 验证 | 消除配置拼写错误导致的静默降级 |
| 5 | `--check-stale-applied` 命令 | 部分弥补 rejection 追踪缺口 |

### 整体架构健康度: 7.5 / 10

**优势**:
- 清晰的流水线架构 (Scrape → Filter → Score → AI → Render)
- 强大的验证门控 (title, category, skill, structure, bio 全阻断)
- Bullet-by-ID + Bio Builder 消除 AI 幻觉
- Prompt 注入防护完善
- 数据库设计合理

**弱势**:
- 错误恢复粒度不够 (sentinel 二态问题)
- 爬虫 rate limiting 缺失
- 混合 print/logging
- 配置无 schema 验证
- Windows 兼容性多处小问题
