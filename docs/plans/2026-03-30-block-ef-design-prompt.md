# Block E+F 设计 Prompt

## 启动指令

使用 `superpowers:brainstorming` skill 设计 Block E (Deliver) 和 Block F (Notify) 的审查+精简方案。

## 项目背景

这是一个 block-by-block pipeline 重建项目。已完成：

| Block | 名称 | 状态 |
|-------|------|------|
| A | Scrape | 已完成，合并到 master |
| B | Hard Filter | 已完成，合并到 master |
| C | AI Evaluate+Tailor (三层路由) | 已完成，合并到 master |
| D | Resume Renderer (审查+精简) | 已完成，10 commits on master |

Block D 的工作流：审计代码 → 写设计文档 → Codex review → 修订 → 再 review → 批准 → 写实施计划 → Codex 执行 → review 修补 → 完成。

## Block E: Deliver (--prepare / --finalize / --tracker)

### 功能

1. **E.1 Prepare** (`--prepare`): 同步 DB → 生成简历/CL → 收集待投递 → 检测 repost → 生成 HTML checklist → 启动本地 server (port 8234)
2. **E.2 Apply**: 用户在 checklist 网页上勾选 applied/skipped（手动步骤）
3. **E.3 Finalize** (`--finalize`): 读 state.json → 归档 applied/skipped → 检测手编辑的 CL → 写 applications 表 → 同步 Turso
4. **E.4 Track** (`--tracker`): 按状态分组查询 applications 表 → 显示天数 → 检测 stale (>30 天)

### 关键文件

- `scripts/job_pipeline.py` — `cmd_prepare()` (line ~367), `cmd_finalize()` (line ~501)
- `src/checklist_server.py` — HTML checklist 生成 + 本地 HTTP server
- `src/db/job_db.py` — `update_application_status()`, `get_ready_to_apply()`, `get_application_tracker()`

## Block F: Notify (CI 通知)

### 功能

CI 流水线最后一步，发送运行摘要到 Telegram：
- 成功：新 job 数 → 分析数 → 高分数 → ready 数 → applied/interview/rejected 汇总
- 失败：失败步骤 + GitHub Actions 链接

### 关键文件

- `scripts/notify.py` — 全部通知逻辑
- `scripts/notify_discord.py` — Discord 通知（备选，未集成到 CI）
- `.github/workflows/job-pipeline-optimized.yml` — CI workflow（Block D 刚加了 `--generate` 步骤）

## 设计方法

沿用 Block D 的方法：**审查+精简**（不是从头重写）。

1. 逐文件审计：找死代码、重复代码、缺失的防御、与三层路由的兼容性问题
2. 提出有限的、有编号的改动清单
3. 每个改动需要：what + why + risk + test

## 需要特别关注的问题

1. **E.1 与 Block D 的接口**: `--prepare` 调用了 `--generate`，Block D 刚改了 renderer——确认接口仍然正确
2. **三层路由兼容性**: `--prepare` 和 `--finalize` 是否正确处理 USE_TEMPLATE / ADAPT_TEMPLATE / FULL_CUSTOMIZE 三种情况？特别是 `ready_to_send/` 目录结构
3. **Notify 与 Block D 的 `--generate` 步骤**: Block D 刚在 CI 里加了 generate 步骤，notify.py 的 ready 统计是否能正确反映新生成的简历？
4. **E 和 F 是否应该合并成一个 Block 还是分开设计？** 它们的代码重叠度如何？
5. **checklist_server.py 的代码质量**: 这个文件可能是最复杂、最少被审查的

## 环境

- Windows 11, bash shell, Python 3.12
- 本地测试一律 `NO_TURSO=1`
- 测试命令: `NO_TURSO=1 python -m pytest tests/ -v`
- 当前测试: 182 passed, 1 skipped

## 输出期望

1. 审计每个文件，列出发现
2. 提出改动清单（编号、分优先级）
3. 写设计文档到 `docs/plans/2026-03-30-block-ef-design.md`
4. 写 Codex review prompt
