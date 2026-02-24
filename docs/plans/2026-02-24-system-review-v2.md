# Job Hunter v2.0 — 第二轮深度系统审查

**日期**: 2026-02-24
**目标**: 在第一轮审查 (2026-02-23, 健康度 7.5/10) 基础上，验证已修复问题、深挖未修复问题、覆盖第一轮盲区
**第一轮修复记录**: commits `3221a9f` → `e979eb2` (7 commits, 包括 P0-P3 修复 + Turso sync 优化)

---

## 审查策略

本轮不重复第一轮的 11 维度框架，而是采用 **问题导向 + 盲区补漏** 策略：

- **Track A (回归验证)**: 验证第一轮发现的 P0/P1 修复是否正确、完整、无引入新 bug
- **Track B (深度挖掘)**: 第一轮标记为 "整体良好" 的模块做逐行审查
- **Track C (盲区补漏)**: 第一轮完全未覆盖的逻辑路径
- **Track D (端到端场景)**: 模拟真实工作流，检查跨模块交互

---

## Track A — 回归验证 (验证 7 个修复 commit)

### A1. Turso sync 优化验证 (`e979eb2` + `c5194f5`)

**审查文件**: `src/db/job_db.py:610-678`, `scripts/job_pipeline.py`

验证要点：
- `startup_only` 模式下 `_get_conn()` post-commit 是否真的不 sync？（line 618 条件）
- `batch_mode()` exit 是否真的不 sync？（line 658 条件）
- `final_sync()` 是否覆盖了所有数据写入路径？**列举所有写入 DB 的代码路径**，确认每条路径最终到达 `final_sync()`
- `job_pipeline.py` 中 `--reprocess` 路径移除了 duplicate `pipeline = JobPipeline()`——验证只有一个实例，且 clear 操作在同一个连接上
- 所有 standalone `db = JobDatabase()` 已替换为 `pipeline.db`——是否有遗漏？（搜索整个文件）
- **边界 case**: 如果 `final_sync()` 失败（网络断开），数据只在本地——下次 CI run 的 `startup_only` init sync 是否能拉到最新远端数据？还是用了缓存的旧本地 DB？

### A2. UTC 时间戳修复验证 (`20c743d`)

**审查文件**: `src/db/job_db.py` (全文搜索 `datetime.now`)

验证要点：
- 第一轮发现 `import_from_json()` 和 `export_to_json()` 仍用 `datetime.now()`——这两处是否已修复？
- **全文搜索 `datetime.now` (无 `timezone.utc`)**，确认零残留
- 所有 SQL 中的 `DATE('now')` / `DATETIME('now')` 是否与 Python 的 UTC 一致？

### A3. 之前修复的 P1-P3 验证 (`13649ee`, `d2dc0c1`, `9a6b4de`)

快速验证这些 commit 引入的修复没有副作用：
- 逐一列出这 3 个 commit 改了什么，验证改动正确性
- 特别关注：是否有"修 A 破 B"的回归

---

## Track B — 深度挖掘 (第一轮标记为 "良好" 的模块)

### B1. AI Analyzer 逐行审查 (`src/ai_analyzer.py`)

第一轮结论是 "整体优秀，无关键问题"。本轮做逐行审查，特别关注：

**JSON 解析鲁棒性** (大约 line 700-800):
- AI 返回的 JSON 可能有 trailing comma、注释、截断——解析逻辑是否处理所有异常格式？
- `_extract_json_from_response()` 的 balanced-brace 提取算法——是否有字符串内嵌 `{` 导致错误匹配？
- 如果 AI 返回的 JSON 中某个字段值是 `null` 而非缺失，下游是否正确处理？

**AI 分析重试逻辑** (大约 line 590-630):
- `RateLimitError` vs `APITimeoutError` vs `APIConnectionError` 的处理是否有遗漏类型？
- `anthropic` SDK 版本升级后，异常类层次是否有变化？
- 重试间隔是否有 jitter？是否可能产生 thundering herd？

**Bullet 解析边界 case**:
- 如果 AI 返回的 bullet IDs 列表中有空字符串 `""` 会怎样？
- 如果返回重复 ID（同一个 bullet 出现两次）会怎样？
- 如果 `tailored_resume.skills` 中某个 category 的值是空列表 `[]` 会怎样？

**Token 计算准确性**:
- `result.tokens_used` 是否包含了输入+输出 token？（检查 anthropic SDK 的 `usage` 字段）
- Cover letter generation 的 token 是否也计入预算？（检查 `cover_letter_generator.py`）

### B2. 筛选评分逻辑逐行审查 (`scripts/job_pipeline.py:140-500`)

第一轮只发现了 `short_jd` 误处理和单一拒绝原因记录。本轮深入：

**硬规则筛选** (filter_jobs 方法):
- `filters.yaml` 中的每种规则类型 (`contains`, `regex`, `range`, `boolean`)——是否每种都有正确的匹配逻辑？
- `regex` 规则带 `exceptions`——exception 匹配是 case-sensitive 还是 case-insensitive？
- 如果 JD 的 `description` 字段为 `None` 或空字符串，筛选逻辑是否 crash？
- `company_blacklist` 和 `title_blacklist` 的匹配是否做了 normalize（大小写、空格、特殊字符）？

**规则评分** (score_jobs 方法):
- `scoring.yaml` 的权重求和——是否有可能超过 10 分？理论最高分是多少？
- body 评分中 `keyword_groups` 的大小写匹配——是否 case-insensitive？
- `posted_date` 评分——"今天发布" vs "30天前发布"，分数差多少？衰减函数是什么？
- 如果一个关键词同时出现在多个 `keyword_groups` 中，是否重复计分？

### B3. Checklist Server 逐行审查 (`src/checklist_server.py`)

第一轮只提到了 "无 CORS"。本轮深入安全审查：

- HTTP handler 是否处理了 path traversal？(如 `GET /../../etc/passwd`)
- POST handler 的输入验证——`job_id`、`action` 参数是否有注入风险？
- `state.json` 的读写是否有 TOCTOU race condition？
- Server 绑定地址——是 `0.0.0.0` 还是 `127.0.0.1`？如果是前者，局域网可访问
- 生成的 HTML checklist 中，job data 是否做了 HTML escape？

---

## Track C — 盲区补漏 (第一轮未覆盖)

### C1. Cover Letter 生成全流程 (`src/cover_letter_generator.py` + `src/cover_letter_renderer.py`)

第一轮几乎没审查 Cover Letter。全面审查：

- `cover_letter_generator.py` 的 prompt 构造——是否有 JD injection 风险？
- AI 返回的 cover letter JSON schema 验证——是否有字段缺失/类型错误处理？
- `cover_letter_config.yaml` 的结构和验证
- 渲染器的模板安全性 (`cover_letter_template.html`)
- 生成失败时的回退行为——是否阻塞 resume 生成？
- Token 消耗是否计入每日预算？

### C2. LinkedIn 爬虫深度审查 (`scripts/linkedin_scraper_v6.py`)

第一轮只审查了 cookie 过期和 HTML 清理。这个文件是最大最复杂的，需要深入：

- **CDP 连接** (Chrome DevTools Protocol)——连接断开时的重连逻辑
- **分页逻辑**——是否有无限循环风险？是否正确处理 "已到达最后一页"？
- **去重逻辑**——同一职位在不同搜索中出现，是否正确去重？
- **搜索 profile 切换**——多 profile 串行执行时，前一个的状态是否影响后一个？
- **headless vs CDP 模式差异**——两种模式下的行为是否一致？
- **`--save-to-db` 的 batch insert**——大量职位时内存占用
- **JSON-LD 解析**——`<script type="application/ld+json">` 提取的鲁棒性
- **反爬策略**——检测到 bot 时的表现

### C3. Database Schema 完整性审查

不是审查代码，而是审查 **SCHEMA 本身**：

- `src/db/job_db.py` 中的 `SCHEMA` 字符串——所有 CREATE TABLE 的字段类型、NOT NULL 约束、DEFAULT 值
- 外键是否有 `ON DELETE CASCADE` 或 `ON DELETE SET NULL`？删除 job 时相关记录怎么处理？
- `VIEWS_TEMPLATE` 中的 SQL——是否有 LEFT JOIN 导致 NULL 未处理？
- `_migrate()` 方法——版本管理是否可靠？如果 migration 执行一半失败怎么办？
- 表之间的关系图——是否有孤立记录的可能？(如 job 被删但 application 还在)

### C4. `--prepare` / `--finalize` 端到端数据流

这两个命令是用户日常最常用的，逐步跟踪数据流：

**`--prepare`** (job_pipeline.py 的 `cmd_prepare` 方法):
1. 从 DB 拿 ready jobs → 检查 SQL 是否正确
2. 生成 resume → 检查 renderer 被调用的参数
3. 生成 cover letter → 检查与 resume 的关联
4. 创建 submit 目录结构 → 检查文件命名冲突
5. 生成 state.json → 检查 schema
6. 生成 checklist HTML → 检查 XSS
7. 启动 HTTP server → 检查生命周期

**`--finalize`** (job_pipeline.py 的 `cmd_finalize` 方法):
1. 读取 state.json → 检查格式错误处理
2. 标记 applied/skipped → 检查 DB 操作原子性
3. 归档文件 → 检查路径冲突（如果同名目录已存在）
4. 清理 → 检查幂等性
5. Sync to Turso → 检查 final_sync() 调用

---

## Track D — 跨模块交互场景

### D1. 端到端数据一致性

追踪一个 job 从爬取到投递的完整生命周期，检查每个阶段的数据格式是否兼容：

```
linkedin_scraper → insert_job() → filter_jobs() → score_jobs()
→ ai_analyze() → save_analysis() → render_resume() → save_resume()
→ cmd_prepare() → checklist → cmd_finalize() → update_application_status()
```

每个环节的输入输出格式是否匹配？有没有字段名不一致（如 `id` vs `job_id`）？

### D2. 并发安全

- CI 跑 pipeline 的同时，本地用户跑 `--prepare`——两者操作同一个 Turso DB，会发生什么？
- `--prepare` 启动 HTTP server 后，用户在 checklist 中操作（勾选 applied），同时在终端跑 `--finalize`——race condition？
- 两个 CI run 同时执行（手动触发 + 定时触发重叠）——Turso sync 冲突？

### D3. 失败恢复场景

模拟以下故障，检查系统行为：
1. **AI analysis 中途 crash** (处理到第 10/50 个职位时 Python 进程被 kill)——已分析的 10 个是否保存？sentinel 是否正确？
2. **`--prepare` 生成到一半断电**——部分 resume 生成，部分未生成，state.json 写到一半——下次 `--prepare` 是否能正确恢复？
3. **Turso sync 失败**——本地数据与远端不一致——下次 CI run 是否能自愈？

---

## 输出格式

每个 Track/每个检查项：
1. **结论**: PASS ✅ / ISSUE 🔴🟡🟢 / NOT APPLICABLE ⬜
2. **发现**: 具体问题描述 + 代码位置 (file:line)
3. **影响**: 用户可感知的影响是什么？
4. **修复建议**: 具体代码或配置改动
5. **优先级**: P0 (阻塞) / P1 (本周) / P2 (下次迭代) / P3 (nice-to-have)

最终总结：
- 修复回归数（已修复问题中引入了几个新问题）
- 新发现数（按优先级分布）
- 更新后的架构健康度 (1-10)
- 与第一轮对比的改进/退步
