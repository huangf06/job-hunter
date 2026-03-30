# Resume Strategy Redesign — Three-Tier Template-First Architecture

**Date:** 2026-03-29
**Status:** Approved design, pending implementation plan
**Branch:** TBD (new branch off master, after `feat/block-bc-redesign` merge)
**Depends on:** `feat/block-bc-redesign` merged (C1/C2 split architecture)

---

## Problem Statement

Current C2 generates a fully customized HTML resume for every job (score >= 4.0), producing 1186+ PDFs via Jinja2 + Playwright. Issues:

1. **Low interview conversion** — AI-assembled resumes lack narrative coherence
2. **Poor narrative quality** — bullet selection is content-optimized but not story-optimized
3. **Visual inferiority** — HTML→PDF output is functional but not polished
4. **Wasted investment** — hand-crafted SVG templates (DE + ML, iterated 9+ versions) sit unused

Meanwhile, 675 applications have been submitted with AI-generated resumes, none using the polished SVG templates.

### Data-Driven Analysis

Job category distribution (score >= 4.0, N=957):

| Category | Count | % | Template Coverage |
|----------|-------|---|-------------------|
| ML/AI | 338 | 35% | ML template (exact) |
| Backend/Platform | 324 | 34% | Needs new Backend template |
| Data Engineering | 156 | 16% | DE template (exact) |
| Analyst | 68 | 7% | DE template (close) |
| Quant | 27 | 3% | ML template (close) |
| Other | 44 | 5% | No template |

DE + ML exact coverage: 52%. With Backend template: ~88%.

---

## Design

### Core Principle

**Template resumes are the default.** They have been human-reviewed through multiple iterations for narrative coherence, visual design, and cross-section resonance. AI-generated alternatives cannot replicate these qualities. When in doubt, use the template.

### Three-Tier Architecture

```
代码层: title keywords → template_id (DE/ML/Backend)

C1: 评分 + Application Brief + 路由
  输入: JD + 模板摘要 + 偏向模板决策框架
  输出: scoring, brief, resume_routing {tier, template_id, gaps, adapt_instructions}
    ↓
    ├── Tier 1: USE_TEMPLATE (~52%, expanding to ~88% with Backend template)
    │   → 拷贝预渲染 PDF → ready_to_send/
    │   → 零渲染，零 AI 成本，零审阅
    │
    ├── Tier 2: ADAPT_TEMPLATE (~37%, shrinking as templates added)
    │   → C2 基于 adapt_*.html 模板微调 (bio/bullets/skills)
    │   → C3 质量闸门: 适配版 vs 模板原版
    │   → 闸门通过 → 用适配版; 不通过 → 回退模板 PDF
    │   → 人工: 抽查
    │
    └── Tier 3: FULL_CUSTOMIZE (~12%)
        → C2 全定制 (bullet library + 简洁单栏模板)
        → 无闸门 (无模板可比)
        → 人工: 建议审阅
```

### Template Registry

```yaml
templates:
  DE:
    svg: "templates/Fei_Huang_DE_Resume.svg"
    pdf: "templates/pdf/Fei_Huang_DE.pdf"          # 预渲染，永久保存
    adapt_html: "templates/adapt_de.html"           # SVG 的 HTML 忠实复刻
    target_roles: ["data engineer", "data platform", "etl", "pipeline",
                   "big data", "analytics engineer", "bi engineer"]
    bio_positioning: "Data Engineer"
    key_strengths: ["Spark/Delta Lake", "AWS data stack", "financial domain", "Python"]
    weak_areas: ["no frontend", "no pure backend API", "no DevOps/K8s emphasis"]

  ML:
    svg: "templates/Fei_Huang_ML_Resume.svg"
    pdf: "templates/pdf/Fei_Huang_ML.pdf"
    adapt_html: "templates/adapt_ml.html"
    target_roles: ["machine learning", "ml engineer", "data scientist", "ai engineer",
                   "deep learning", "nlp", "computer vision", "research", "applied scientist",
                   "genai", "quant", "quantitative"]
    bio_positioning: "ML Engineer / Data Scientist"
    key_strengths: ["PyTorch", "thesis in RL", "research background", "model deployment"]
    weak_areas: ["no production pipeline emphasis", "no cloud infrastructure focus"]

  Backend:  # 新增，需要制作
    svg: "templates/Fei_Huang_Backend_Resume.svg"
    pdf: "templates/pdf/Fei_Huang_Backend.pdf"
    adapt_html: "templates/adapt_backend.html"
    target_roles: ["software engineer", "backend", "platform engineer",
                   "python developer", "infrastructure", "python engineer"]
    bio_positioning: "Software Engineer"
    key_strengths: ["Python", "Docker", "API design", "system architecture", "data-intensive"]
    weak_areas: ["no frontend", "less ML/model focus"]
```

### Template Selection (Deterministic Code)

```python
def select_template(title: str) -> str:
    """基于 title 关键词选择最佳模板。零 token 消耗。"""
    title = title.lower()
    ml_kw = ["machine learning", "ml ", "data scientist", "ai engineer",
             "deep learning", "nlp", "computer vision", "research",
             "applied scientist", "genai", "quant"]
    backend_kw = ["software engineer", "backend", "platform engineer",
                  "python developer", "infrastructure", "python engineer"]
    if any(kw in title for kw in ml_kw):
        return "ML"
    if any(kw in title for kw in backend_kw):
        return "Backend"
    return "DE"  # 默认
```

C1 可以覆盖代码的选择（比如 JD 内容明显偏向另一个模板）。

### C1 Prompt Extension (~20 lines)

C1 现有输出 (scoring + application_brief) 不变，新增 `resume_routing`:

```
## Resume Routing Decision

We have professionally designed template resumes, human-reviewed through multiple
iterations for narrative coherence, visual design, and cross-section resonance.
AI-generated alternatives CANNOT replicate these qualities.

PRINCIPLE: When in doubt, USE the template. Minor content gaps do NOT justify
replacing a polished template with an AI-generated alternative.

Available templates:
- DE: Data Engineer positioning. Strengths: Spark/Delta Lake, AWS, financial domain.
- ML: ML Engineer positioning. Strengths: PyTorch, RL thesis, research.
- Backend: Software Engineer positioning. Strengths: Python, Docker, API design.

Pre-selected template: {template_id}

Routing rules:
- USE_TEMPLATE: Default. Choose unless hiring manager would question fit at first glance.
  Acceptable gaps (still use template): missing a mentioned technology, different domain
  emphasis, slightly different experience years.
- ADAPT_TEMPLATE: ONLY when structural positioning mismatch exists. Specifically:
  bio positioning is wrong for the role, OR >50% of template bullets are irrelevant
  to the JD's core requirements, OR skills ordering misrepresents candidate fit.
- FULL_CUSTOMIZE: ONLY when no template is remotely close (<15% of jobs).

Output in resume_routing:
{
  "tier": "USE_TEMPLATE" | "ADAPT_TEMPLATE" | "FULL_CUSTOMIZE",
  "template_id": "DE",
  "gaps": ["specific gap descriptions"],
  "adapt_instructions": "what to change, only if ADAPT_TEMPLATE"
}
```

### C2 Redesign: Two Modes

**Tier 2 Mode (ADAPT_TEMPLATE):**

Input: adapt_instructions from C1 + JD + 模板的 HTML 内容
Task: 只做指定的微调，不重写整份简历
Output:
```json
{
  "bio_override": "Software Engineer with 6 years..." | null,
  "bullet_overrides": {
    "glp_1": "Redesigned API layer serving 10M daily requests..." | null,
    "ele_2": null
  },
  "skills": [{"name": "Languages", "items": "Python (Expert), SQL, Go"}],
  "change_summary": "Changed bio positioning from DE to Backend; replaced 2 Spark bullets with API design bullets; reordered skills"
}
```

Prompt: 短 (~1000 字)，无 bullet library，只有模板内容 + 改动指令。

**Tier 3 Mode (FULL_CUSTOMIZE):**

当前 C2 逻辑基本不变 (bullet library + 全量 prompt)。
渲染模板改为简洁单栏 `customize_template.html`。

### Tier 2 HTML Template Design

`adapt_de.html` = SVG 简历的 HTML 忠实复刻：

```html
<!-- 硬编码内容 = 模板原文，Jinja2 插槽只在允许改动处 -->
<div class="bio">
  {% if bio_override %}{{ bio_override }}{% else %}
  Data Engineer with 6 years of experience in scalable data pipelines...
  {% endif %}
</div>

<div class="experience">
  <h3>GLP Technology — Data Scientist & Team Lead</h3>
  <ul>
    {% if bullet_overrides.glp_1 %}
    <li>{{ bullet_overrides.glp_1 }}</li>
    {% else %}
    <li>Founded data science team of 5, built real-time credit scoring engine...</li>
    {% endif %}
    <!-- 未 override 的 bullet 保持模板原文 -->
  </ul>
</div>

<div class="skills">
  {% for cat in skills %}
  <span class="category">{{ cat.name }}:</span> {{ cat.items }}<br>
  {% endfor %}
</div>
```

**设计原则：默认输出 = 模板原文。** AI 只提供 override，不提供的位置保持不变。

### C3 Quality Gate (仅 Tier 2)

轻量 AI 调用 (~300 token input)：

```
C2 made these changes to the {template_id} template:
{change_summary}

The job requires: {c1_brief.key_angle}
The main gap was: {c1_routing.gaps}

Question: Do these changes significantly improve JD fit enough to justify
using a newly rendered resume over the professionally polished template?
Consider: the template has superior narrative coherence and visual design
that the adapted version cannot fully replicate.

Answer YES or NO with one sentence of reasoning.
```

- YES → 用 C2 适配版 HTML→PDF
- NO → 回退到预渲染模板 PDF

### Tier 3 Rendering Template

新建 `templates/customize_template.html`：简洁单栏设计。

- 全量 Jinja2 插槽 (bio, experiences, projects, skills)
- 单栏布局，避免双栏排版复杂度
- 适用于无模板匹配的 12% 长尾岗位
- 现有 `base_template.html` (双栏) 淘汰，不纳入新架构

---

## File Changes Summary

### New Files
- `config/template_registry.yaml` — 模板注册表
- `templates/pdf/Fei_Huang_DE.pdf` — 预渲染 PDF
- `templates/pdf/Fei_Huang_ML.pdf` — 预渲染 PDF
- `templates/pdf/Fei_Huang_Backend.pdf` — 预渲染 PDF (待制作)
- `templates/Fei_Huang_Backend_Resume.svg` — Backend SVG 模板 (待制作)
- `templates/adapt_de.html` — DE 适配模板 (SVG HTML 化)
- `templates/adapt_ml.html` — ML 适配模板 (SVG HTML 化)
- `templates/adapt_backend.html` — Backend 适配模板 (待制作)
- `templates/customize_template.html` — Tier 3 简洁单栏模板

### Modified Files
- `config/ai_config.yaml` — C1 prompt 扩展 (路由指令), C2 prompt 拆分为两种模式
- `src/ai_analyzer.py` — C2 双模式, C3 质量闸门, template selection 代码
- `src/resume_renderer.py` — 三档渲染路径
- `scripts/job_pipeline.py` — `--prepare` 行为更新

### Deprecated
- `templates/base_template.html` — 双栏布局，不再使用

---

## CLI Interface

```bash
# 不变
python scripts/job_pipeline.py --ai-evaluate      # C1
python scripts/job_pipeline.py --ai-tailor         # C2 (三档分流)
python scripts/job_pipeline.py --ai-analyze        # C1 + C2

# --prepare 行为更新:
#   Tier 1: cp templates/pdf/XX.pdf → ready_to_send/
#   Tier 2: render adapt_XX.html → PDF (或回退 Tier 1)
#   Tier 3: render customize_template.html → PDF

# 新增 (可选)
python scripts/job_pipeline.py --template-stats    # 各 tier 分布统计
```

---

## Success Metrics

| Metric | Before | Target |
|--------|--------|--------|
| 模板简历使用率 | 0% | >50% (Tier 1) |
| C2 token 消耗 / job | ~3000 token | ~1000 token (Tier 2 平均) |
| 人工审阅需求 | 每份精审 | Tier 1 免审, Tier 2 抽查, Tier 3 建议审 |
| 面试转化率 | baseline | 期望提升 (模板质量 + brief 个性化) |

---

## Implementation Dependencies

1. **先决条件**: `feat/block-bc-redesign` merge 到 master
2. **Phase 1**: Backend SVG 模板制作 (独立工作流，非代码任务)
3. **Phase 2**: 架构实现 (template registry, C1 路由, C2 双模式, C3 闸门, 渲染管线)
4. **Phase 3**: adapt_*.html 模板制作 (SVG → HTML 翻版)

Phase 1 和 Phase 2 可以并行——Phase 2 先用 DE + ML 两个模板开发，Backend 模板就绪后挂入。

---

## Design References

- Block B+C redesign: `docs/plans/2026-03-28-block-bc-unified-design.md`
- DE SVG design: `docs/plans/2026-03-10-de-toni-svg-design.md`
- ML SVG design: `docs/plans/2026-03-12-ml-resume-v3-design.md`
- Narrative architecture: `docs/plans/2026-03-10-narrative-architecture-design.md`
- Bullet library: `assets/bullet_library.yaml` (v4.0)
