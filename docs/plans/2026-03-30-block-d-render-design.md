# Block D: Resume Renderer — 审查+精简设计

**Date**: 2026-03-30
**Status**: Pending Codex Review
**Scope**: 审查+精简现有 `resume_renderer.py`，非完整重建
**前置**: Block A (Scrape) ✅, Block B (Hard Filter) ✅, Block C (AI Evaluate+Tailor) ✅ 均已逐块完成

---

## 1. Block D 现状

### 1.1 文件清单

| 文件 | 行数 | 角色 |
|------|------|------|
| `src/resume_renderer.py` | 655 | 主渲染器：三层路由 + Jinja2 渲染 + Playwright PDF |
| `src/resume_validator.py` | 406 | 验证器：bio/title/skills/结构校验，含自动修复 |
| `src/template_registry.py` | 120 | 模板注册表：选模板、路由解析、tier2 校验 |
| `templates/base_template.html` | 325 | FULL_CUSTOMIZE 的 Jinja2 模板 |
| `templates/adapt_de.html` | ~80 | ADAPT_TEMPLATE 的 DE 模板 |
| `templates/adapt_ml.html` | ~80 | ADAPT_TEMPLATE 的 ML 模板 |
| `templates/pdf/Fei_Huang_DE.pdf` | - | USE_TEMPLATE 的 DE 预渲染 PDF |
| `templates/pdf/Fei_Huang_ML.pdf` | - | USE_TEMPLATE 的 ML 预渲染 PDF |
| `config/template_registry.yaml` | 217 | 模板元数据 + slot schema |
| `tests/test_resume_renderer_tiers.py` | 171 | 三层路由单元测试 (3 tests) |

### 1.2 三层渲染路由 (Block C 三层路由产出)

```
render_resume(job_id)
  ├─ USE_TEMPLATE           → _render_template_copy()  [PDF 文件复制]
  ├─ ADAPT_TEMPLATE (PASS)  → _render_adapt_template() [slot override + Jinja2 + Playwright]
  ├─ ADAPT_TEMPLATE (FAIL)  → _render_template_copy()  [C3 gate 拒绝，回退到复制]
  ├─ FULL_CUSTOMIZE         → render_resume() 主路径   [完整 Jinja2 + Playwright]
  └─ Legacy (tier=NULL)     → render_resume() 主路径   [同上，向后兼容]
```

### 1.3 验证通过的部分 (不改)

以下经审查确认干净、无死代码，本次不改动：

- **`resume_validator.py`** — 406 行，6 类校验，无死代码，3 处调用 (renderer + ai_analyzer x2)
- **`base_template.html`** — 325 行，纯展示模板，无 tier 逻辑
- **`template_registry.py`** — 120 行，路由逻辑清晰，已有 14 个测试覆盖
- **`config/template_registry.yaml`** — slot schema 完整，DE/ML 启用，Backend 禁用

---

## 2. 审计发现的问题

### 2.1 CRITICAL: CI workflow 缺 `--generate` 步骤

**文件**: `.github/workflows/job-pipeline-optimized.yml`
**位置**: C2 (`--ai-tailor`, line 143) 和通知 (line 148) 之间

当前 CI 流程：
```
scrape → process → ai-evaluate → ai-tailor → [缺口] → notify → stats
```

AI 分析做了，但 PDF 永远不会在 CI 中生成。`notify.py` JOIN `resumes` 表时返回空，Ready-to-apply 永远为 0。

### 2.2 HIGH: 模板路由缺防御性校验

**`_render_template_copy()` line 300**:
```python
source_pdf = PROJECT_ROOT / self.registry['templates'][template_id]['pdf']
```
如果 `template_id` 在 registry 中不存在 → `KeyError` 崩溃。

**`_render_adapt_template()` line 324**:
```python
template_meta = self.registry['templates'][template_id]
```
同样无防护。且缺 `adapt_html` 字段存在性校验。

### 2.3 MEDIUM: 代码重复

**问题 A — 输出路径生成重复**:
`render_resume()` 主路径 (lines 212-235) 和 `_build_output_paths()` (lines 269-293) 做完全相同的事。`_build_output_paths()` 已被 `_render_template_copy()` 和 `_render_adapt_template()` 使用，但主路径没用它。

**问题 B — 验证重复**:
`_validate_tailored_structure()` (lines 427-485, 59 行) 与 `ResumeValidator` 大面积重叠：

| 检查项 | `_validate_tailored_structure` | `ResumeValidator` |
|--------|-------------------------------|-------------------|
| experiences 存在 | ✓ (允许 1 个) | ✓ (要求 ≥2) |
| 每个 exp 有 company/title/date | ✓ | ✗ (但上游 ai_analyzer 保证) |
| 每个 exp 有 bullets list | ✓ | ✓ (要求 ≥1 bullet) |
| projects 是 list | ✓ | ✓ (要求 ≥1) |
| skills 是 list | ✓ | ✓ (要求 ≥3 categories) |
| bio 类型检查 | ✓ | ✓ |

Renderer 的检查是 ResumeValidator 的宽松子集。且 ResumeValidator 已在两个上游点被调用 (ai_analyzer lines 804, 1014)。到 renderer 时数据已经过验证。

**问题 C — adapt 模板重复**:
`adapt_de.html` 和 `adapt_ml.html` 完全相同，仅 `<title>` 不同。

### 2.4 LOW: 死代码

**`_detect_role_type()` (lines 532-545, 14 行)**:
用关键词匹配标题返回 `ml_engineer`/`data_engineer`/`quant` 等。已被三层路由的 `template_id` (DE/ML/Backend) 完全取代。当前唯一调用在 FULL_CUSTOMIZE 主路径的 `save_resume()` (line 256)，可直接用 `template_id_final` 或 fallback `"general"` 替代。

---

## 3. 设计方案

### 3.1 设计原则

- **Renderer 只做路由→渲染→输出**，不做验证 (验证属于 Block C 的出口)
- **每条渲染路径都必须有测试**
- **最小改动**：不改动已验证干净的文件

### 3.2 改动清单

#### 改动 1: CI workflow 加 `--generate` 步骤

**文件**: `.github/workflows/job-pipeline-optimized.yml`

在 Step 4 (AI Tailor) 和 Step 5 (通知) 之间加：

```yaml
      # ==========================================
      # Step 4b: Generate resumes (Block D)
      # ==========================================
      - name: Generate resumes
        id: generate
        continue-on-error: true
        run: |
          echo "=== Generating resumes ==="
          python scripts/job_pipeline.py --generate --limit 30
```

同时在通知步骤加 generate 失败检测：
```yaml
[ "${{ steps.generate.outcome }}" == "failure" ] && FAILED_STEPS="${FAILED_STEPS:+$FAILED_STEPS, }generate"
```

#### 改动 2: 合并 adapt 模板

**删除**: `templates/adapt_de.html`, `templates/adapt_ml.html`
**新建**: `templates/adapt_template.html`

变化：`<title>` 从硬编码改为 `{{ template_title | default("Adapted Resume") }}`

**联动**: `_render_adapt_template()` 改为加载统一模板，传入 `template_title`:
```python
template = self.jinja_env.get_template("adapt_template.html")
html_content = template.render(
    ...,
    template_title=f"Adapted {template_id} Resume",
)
```

**联动**: `config/template_registry.yaml` 中 DE/ML 的 `adapt_html` 字段删除 (不再需要每模板指定)。

#### 改动 3: 消除输出路径重复

**FULL_CUSTOMIZE 主路径** (lines 212-267) 改为使用已有的 `_build_output_paths()`。

当前主路径有 24 行路径生成代码 (L212-L235) 和 `_build_output_paths()` (L269-L293) 完全重复。改后主路径直接调用：
```python
paths = self._build_output_paths(job)
html_path = paths['html_path']
pdf_path = paths['pdf_path']
submit_pdf_path = paths['submit_pdf_path']
submit_dir = paths['submit_dir']
```

净删 ~20 行。

#### 改动 4: 删除 `_validate_tailored_structure()`

**删除**: `_validate_tailored_structure()` (lines 427-485, 59 行)
**删除**: `render_resume()` 中对它的调用 (lines 150-156)

**理由**: `ResumeValidator` 已在上游 (ai_analyzer) 做过更严格的验证。到 renderer 时数据结构保证正确。如果 AI 输出未经验证就到达 renderer (绕过 ai_analyzer)，那是 pipeline 的 bug，不该在 renderer 静默吞掉。

#### 改动 5: 删除 `_detect_role_type()`

**删除**: `_detect_role_type()` (lines 532-545, 14 行)
**修改**: FULL_CUSTOMIZE 路径 `save_resume()` 调用中的 `role_type` 改为：
```python
role_type = analysis.get('template_id_final') or 'general'
```

#### 改动 6: 加固模板路由防御

**`_render_template_copy()`**:
```python
def _render_template_copy(self, job_id, analysis):
    job = self.db.get_job(job_id)
    template_id = analysis.get('template_id_final')
    if not job or not template_id:
        return None
    template_meta = self.registry.get('templates', {}).get(template_id)
    if not template_meta or 'pdf' not in template_meta:
        print(f"[Renderer] Unknown template or missing PDF config: {template_id}")
        return None
    source_pdf = PROJECT_ROOT / template_meta['pdf']
    ...
```

**`_render_adapt_template()`**:
```python
def _render_adapt_template(self, job_id, analysis):
    job = self.db.get_job(job_id)
    if not job:
        return None
    template_id = analysis.get('template_id_final')
    template_meta = self.registry.get('templates', {}).get(template_id)
    if not template_meta:
        print(f"[Renderer] Unknown template: {template_id}")
        return None
    ...
```

### 3.3 不改动的文件

| 文件 | 理由 |
|------|------|
| `src/resume_validator.py` | 审查结论：干净、无死代码、3 处调用 |
| `src/template_registry.py` | 审查结论：干净、14 个测试覆盖 |
| `templates/base_template.html` | 审查结论：干净、325 行纯模板 |
| `config/template_registry.yaml` | 仅删 `adapt_html` 字段，schema 不变 |

### 3.4 测试计划

**现有测试** (保留):
- `test_resume_renderer_tiers.py`: 3 tests (USE_TEMPLATE, ADAPT_PASS, FULL_CUSTOMIZE)

**新增测试**:

| 测试 | 覆盖路径 |
|------|---------|
| `test_render_template_copy_unknown_template_returns_none` | 改动 6: template_id 无效时优雅失败 |
| `test_render_adapt_template_unknown_template_returns_none` | 改动 6: adapt 路径同上 |
| `test_render_adapt_template_fail_falls_back_to_copy` | 已有但补充 DB 记录验证 |
| `test_render_full_customize_uses_build_output_paths` | 改动 3: 主路径用统一方法 |
| `test_render_full_customize_role_type_uses_template_id` | 改动 5: role_type 来源检查 |
| `test_adapt_template_html_renders_with_title_variable` | 改动 2: 合并模板正确渲染 |

---

## 4. 预期效果

| 指标 | 改前 | 改后 |
|------|------|------|
| `resume_renderer.py` 行数 | 655 | ~560 (净减 ~95 行) |
| 渲染路径测试覆盖 | 3 tests | 9 tests |
| adapt 模板文件数 | 2 (重复) | 1 |
| CI 能否生成 PDF | 否 | 是 |
| template_id 无效时行为 | KeyError 崩溃 | 优雅返回 None + 日志 |

---

## 5. 实施顺序

1. 先写新测试 (failing)
2. 改动 1: CI workflow 加 `--generate`
3. 改动 2: 合并 adapt 模板
4. 改动 3: 消除输出路径重复
5. 改动 4: 删 `_validate_tailored_structure()`
6. 改动 5: 删 `_detect_role_type()`
7. 改动 6: 加固模板路由防御
8. 跑全量测试验证
9. Spot check: 对真实 job 跑 `--generate` 验证 PDF 输出

---

## 6. 不在 scope 内

- `resume_validator.py` 的任何改动
- `base_template.html` 的任何改动
- Block E (Deliver: --prepare/--finalize) 的修复 — 留给 Block E 设计
- Backend 模板启用 — 当前 disabled，不在 Block D scope
- 新增渲染模式或新模板
