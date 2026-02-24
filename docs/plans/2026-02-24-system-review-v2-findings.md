# Job Hunter v2.0 — 第二轮深度审查结果

**审查日期**: 2026-02-24
**审查范围**: 4 Tracks (回归验证 / 深度挖掘 / 盲区补漏 / 跨模块交互)
**方法**: 4 个并行审查代理 + 人工综合
**第一轮健康度**: 7.5/10

---

## Track A — 回归验证

### 所有 7 个 fix commit 验证通过，无回归

| Commit | 修复内容 | 验证结果 |
|--------|---------|---------|
| `e979eb2` | Turso sync 优化 (final_sync) | PASS ✅ |
| `c5194f5` | DB cache + startup_only mode | PASS ✅ |
| `20c743d` | UTC 时间戳修复 | PASS ✅ (关键路径全修复) |
| `9a6b4de` | P3 robustness/DRY/CI | PASS ✅ |
| `d2dc0c1` | P2 security/correctness | PASS ✅ |
| `13649ee` | P1 reliability/correctness | PASS ✅ |
| `3221a9f` | 5 critical bugs | PASS ✅ |

### 🟡 P2 — 19 处残留 `datetime.now()` (无 UTC)
**位置**: scrapers (`linkedin_scraper_v6.py:937`, `greenhouse.py:65`, `lever.py:67`, `iamexpat.py:36`), 文件命名 (`resume_renderer.py:208,214`, `cover_letter_renderer.py:97,116,137`), 显示 (`job_pipeline.py:140,145,594`)

所有 **关键 DB 写入路径** 已正确修复为 UTC。残留的均为非关键路径（爬虫 `scraped_at`、文件名时间戳、HTML 显示时间）。CI runner 在 UTC 环境下无影响，仅本地 Windows (CET) 有轻微不一致。

### 🟡 P2 — 多个 JobDatabase 实例导致冗余 init sync
**位置**: `ai_analyzer.py:52`, `resume_renderer.py:37`, `cover_letter_generator.py:42`, `cover_letter_renderer.py:37`

`AIAnalyzer`、`ResumeRenderer`、`CoverLetterGenerator`、`CoverLetterRenderer` 各自创建独立的 `JobDatabase()` 实例。在 CI `startup_only` 模式下，每个实例都触发一次 init sync (pull)。数据完整性不受影响（共享同一个本地 SQLite 文件，`final_sync()` 推送完整 WAL），但浪费了 4 次冗余网络往返。

**建议**: 将 `pipeline.db` 作为参数传入各模块，消除冗余实例。

---

## Track B — 深度挖掘

### B1. AI Analyzer — 整体优秀，1 个小问题

#### 🟡 P2 — 重复 bullet ID 产生重复简历行
**位置**: `src/ai_analyzer.py:348-397`

如果 AI 返回重复 ID (如 `["glp_founding_member", "glp_founding_member"]`)，两个都被解析为相同文本并加入 `resolved` 列表。简历会渲染出两行相同的 bullet。

**建议**: 解析后去重: `if resolved_text not in resolved: resolved.append(resolved_text)`

#### ✅ JSON 解析、重试逻辑、token 计算 — 全部 PASS
- Balanced-brace 提取算法正确处理字符串内的 `{`
- 重试有 jitter (`random.uniform(0, base*0.5)`)，无 thundering herd 风险
- `tokens_used` 正确包含 input+output
- Cover letter token 正确计入每日预算 (`UNION ALL` 查询)
- 空字符串 `""` bullet ID 正确走 unknown-ID 路径
- `null` vs 缺失字段正确处理 (`parsed.get('x') or {}`)

### B2. 筛选评分 — 全部 PASS

- 理论最高分 ~23.5，被 `max(0, min(10, score))` 正确钳制
- 关键词匹配用 `\b` word boundary，case-insensitive
- `None` description 正确处理 (`(job.get('description') or '').lower()`)
- `short_jd` 在 body 循环中被遍历但无实际影响（fragile，不是 bug）
- Regex exceptions 大小写一致（title 和 exception 都 lowered）

### B3. Checklist Server — 4 个 XSS/安全问题

#### 🟡 P2 — `_esc()` 缺少单引号转义
**位置**: `src/checklist_server.py:176-178`

`_esc()` 转义了 `&`, `<`, `>`, `"` 但未转义 `'`。`abs_dir` 被注入到 `onclick="openFolder('...')"` 中，如果路径含单引号可能破坏 JS。

#### 🟡 P2 — `job_id` 未 HTML 转义
**位置**: `src/checklist_server.py:78`

`<tr data-job-id="{job_id}">` 中 `job_id` 未经 `_esc()` 处理。实际 job_id 是 MD5 hash (纯字母数字)，风险极低。

#### 🟡 P2 — `/open-folder` 无路径限制
**位置**: `src/checklist_server.py:214-224`

只检查 `Path(folder).is_dir()` 但不验证路径在 `ready_dir` 内。localhost-only，风险仅限本地进程。

**建议**: 添加 `Path(folder).resolve().is_relative_to(ready_dir.resolve())` 检查。

#### 🟡 P3 — `/state` 接受任意 JSON
**位置**: `src/checklist_server.py:200-211`

无 schema 验证。恶意 POST 可写入垃圾 JSON。`--finalize` 读到后 `jobs = state.get("jobs", {})` 返回空 dict，相当于 DoS。

---

## Track C — 盲区补漏

### C1. Cover Letter — 1 个验证缺口

#### 🟡 P2 — CL spec 验证不检查关键字段存在性
**位置**: `src/cover_letter_generator.py:280-323`

不验证 `opening_prose`、`closer_prose`、`body_paragraphs` 是否存在或非空。AI 省略这些字段时静默生成不完整的 cover letter 并存入 DB。

**建议**: 添加检查:
```python
if not std.get('opening_prose'):
    errors.append("Missing 'opening_prose'")
```

#### ✅ 其他全部 PASS
- Prompt 构造正确转义花括号，无 JD injection 风险
- `autoescape=True` 保护 cover letter 模板
- CL 失败不阻塞 resume 生成 (non-blocking)
- Token 正确计入每日预算

### C2. LinkedIn 爬虫 — 2 个中等问题

#### 🟡 P1 — CDP 连接断开无重连逻辑
**位置**: `scripts/linkedin_scraper_v6.py:211-226`

初始连接有 fallback (回退到内置浏览器)，但连接成功后如果 Chrome 窗口关闭/debugger 端口死亡，所有后续 `page.goto()` 全部失败。`_safe_goto` 的 3 次重试对已死连接无效。

**建议**: 在 `_safe_goto` 中检测 `TargetClosedError`/`BrowserClosedError`，尝试重连或优雅退出。

#### 🟡 P2 — CDP 模式跳过 request interception
**位置**: `scripts/linkedin_scraper_v6.py:264-275`

非 CDP 模式阻止图片/CSS/字体/analytics 请求 (更快更隐蔽)，但 CDP 模式不做。爬取更慢且向 LinkedIn 发送更多追踪信号。

#### ✅ 其他全部 PASS
- 分页: 5 重保险防无限循环 (max_pages=20, max_jobs, page_new==0, 80% 重复检测, next_page 失败)
- 去重: `seen_keys` set + DB `ON CONFLICT` 双层去重
- JSON-LD 解析: 每元素 try/except，永不崩溃
- 反爬: CAPTCHA 检测 + 交互式解决 + 非交互优雅退出

### C3. Database Schema — 1 个设计隐患

#### 🟡 P2 — 外键无 `ON DELETE CASCADE`
**位置**: `src/db/job_db.py:236-332`

所有子表的 `REFERENCES jobs(id)` 默认 `ON DELETE NO ACTION`。配合 `PRAGMA foreign_keys=ON`，直接 `DELETE FROM jobs` 会因外键约束失败。`archive_cold_data` 手动按正确顺序删除依赖记录，但 ad-hoc 操作会出错。

**建议**: 添加 `ON DELETE CASCADE` 或保持现状但在文档中说明。

### C4. --prepare / --finalize 数据流

#### 🟡 P2 — `--finalize` 不停止 checklist server
运行 `--finalize` 后，server 继续运行但引用的文件夹已被移动到 `_applied/`/`_skipped/`。不会损坏数据，但用户体验混乱。

#### ✅ 其他 PASS
- `state.json` 原子写入 (tmp+replace)
- `--finalize` 幂等 (state.json 不存在时安全退出)
- Resume 生成增量 (已生成的不重复)

---

## Track D — 跨模块交互

### 🔴 P0 — `--generate` 路径 KeyError 崩溃
**位置**: `scripts/job_pipeline.py:662`

```python
dupes = self.db.find_applied_duplicates(job['job_id'])  # BUG: 应该是 job['id']
```

`get_analyzed_jobs_for_resume()` 返回的字段名是 `id` (来自 `j.*`)，但这里用了 `job_id`。当 `--generate` 命令遇到有 repost 候选的职位时，会抛出 `KeyError: 'job_id'` 崩溃。

**注意**: `--prepare` 路径 (line 758) 使用了正确的 `job['id']`，所以日常工作流不受影响。只有旧版 `--generate` 命令受影响。

**修复**: `job['job_id']` → `job['id']`

### 🟡 P1 — CI cache key 永不更新导致潜在数据丢失
**位置**: `.github/workflows/job-pipeline-optimized.yml:73`

`key: turso-replica-v1` 是静态 key。`actions/cache@v4` 行为: 首次 miss 时保存，之后每次都 exact hit，**永不重新保存**。这意味着缓存中的 `data/jobs.db` 永远是第一次 CI run 的版本。

正常情况下不影响数据 (每次 init sync 从 Turso 拉取最新数据)。但如果 `final_sync()` 失败：
1. 本地 DB 有新数据，远端没有
2. 下次 CI run 恢复旧缓存 (覆盖本地新数据)
3. Init sync 从远端拉取 (远端也没有)
4. **数据丢失**

**修复**: 改用动态 key:
```yaml
key: turso-replica-v2-${{ github.run_id }}
restore-keys: |
  turso-replica-v2-
```

### 🟡 P2 — Resume DB 记录在 PDF 复制前保存
**位置**: `src/resume_renderer.py:234-254`

`save_resume()` 在 `shutil.copy2` (复制到 submit_dir) 之前执行。如果中断，DB 记录存在但 submit_dir 中没有 PDF。下次 `--prepare` 不会重新生成 (认为已完成)。

### ✅ 端到端数据一致性 — PASS
- `id` vs `job_id` 除上述 bug 外全部一致
- 数据类型一致 (scores 始终为 float, tokens 始终为 int)
- NULL 处理完善 (description, tailored_resume, submit_dir, applied_at)

### ✅ 并发安全 — PASS (低风险)
- CI + 本地操作不同表/行，无写冲突
- 两个 CI run 重叠: idempotent upsert，仅浪费 API token
- Checklist server 原子写入，单线程无 race condition

### ✅ 失败恢复 — PASS
- AI crash at job 10/50: 前 10 个独立 commit，sentinel 防止无限重试
- `--prepare` 中断: 增量恢复，只处理未完成的

---

## 总结

### 新发现统计

| 优先级 | 数量 | 关键问题 |
|--------|------|---------|
| P0 (阻塞) | 1 | `--generate` KeyError 崩溃 |
| P1 (本周) | 2 | CI cache key 永不更新; CDP 无重连 |
| P2 (下次) | 10 | XSS 加固、CL 验证、外键 CASCADE 等 |
| P3 (nice) | 1 | /state 无 schema 验证 |

### 修复回归数: 0
第一轮发现的所有已修复问题均无引入新 bug。

### Top 5 最紧急修复

| # | 问题 | 位置 | 修复量 |
|---|------|------|--------|
| 1 | `job['job_id']` → `job['id']` KeyError | `job_pipeline.py:662` | 1 行 |
| 2 | CI cache key 动态化 | `job-pipeline-optimized.yml:73` | 2 行 |
| 3 | Checklist XSS 加固 (`_esc` + onclick) | `checklist_server.py:78,84,176` | ~10 行 |
| 4 | `/open-folder` 路径限制 | `checklist_server.py:214-224` | 3 行 |
| 5 | CDP 断连检测 | `linkedin_scraper_v6.py:211-226` | ~15 行 |

### 与第一轮对比

| 维度 | 第一轮 | 第二轮 | 变化 |
|------|--------|--------|------|
| P0 问题 | 2 (sentinel, UTC) | 1 (KeyError) | ↓ 改善 |
| P1 问题 | 5 | 2 | ↓ 改善 |
| P2 问题 | 12 | 10 (6 新 + 4 第一轮未修复) | → 持平 |
| 修复回归 | N/A | 0 | ✅ |
| AI Analyzer | "优秀" | 逐行确认优秀 | ✅ |
| 筛选评分 | "良好" | 逐行确认良好 | ✅ |
| Cover Letter | 未审查 | 已审查，1 个验证缺口 | 新覆盖 |
| LinkedIn 爬虫 | 表面审查 | 深度审查，2 个问题 | 新覆盖 |
| 跨模块交互 | 未审查 | 已审查，发现 1 个 BUG | 新覆盖 |

### 更新后的架构健康度: 8.0 / 10 (↑ 0.5)

**改善点**:
- UTC 时间戳在关键路径全面修复
- Turso sync 优化大幅减少网络开销
- 所有修复 commit 无回归
- AI Analyzer 和筛选评分经逐行审查确认健壮

**仍需改善**:
- Checklist server XSS 加固
- CI cache 策略修正
- LinkedIn CDP 连接弹性
- Cover letter 验证完善
- 多 DB 实例合并 (性能优化)
