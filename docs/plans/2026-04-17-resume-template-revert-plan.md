# Resume Template Revert Implementation Plan (2026-04-17)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Stop sending static pre-made PDFs (82% of recent applications) and zone-compressed single-page resumes. Route every application through per-job customized flow-layout 2-page resume using the existing `base_template.html`.

**Architecture:**
- **Current problem**: C1 AI prompt defaults to `USE_TEMPLATE` tier → 82% of post-2026-04-02 apps were **identical PDFs with zero tailoring**; 16% were zone-compressed `ADAPT_TEMPLATE`; only 1% used the flow-layout `FULL_CUSTOMIZE` path.
- **Fix**: Force all jobs to `FULL_CUSTOMIZE` tier. Keep three-tier registry only for `target_roles` keyword matching (DE/ML/DS label, used by AI to prioritize bullets). Everything renders through `base_template.html` (flow-layout, 2 pages, `{% for exp in experiences %}` + `{% for bullet in exp.bullets %}`). Archive zone templates and `USE_TEMPLATE`/`ADAPT_TEMPLATE` rendering paths.
- The flow-layout path (`_build_context` in `resume_renderer.py` + `base_template.html` + bullet library v5.0's `verified_bullets[].content`) is already fully wired; AI just needs to produce `{experiences: [...], projects: [...], skills: [...]}` JSON consistently.

**Tech Stack:** Python 3.12, Jinja2, Playwright (Chromium PDF), Claude Code CLI, SQLite + Turso, YAML bullet library v5.0.

**Reference context:**
- Design doc: `docs/plans/2026-04-17-resume-template-revert-design.md`
- Pre-upgrade reference template: `git show 67724e8:templates/base_template.html` (~363 lines, already ~identical to current `base_template.html`)
- Tier distribution query (for before/after comparison):
  ```sql
  SELECT a.resume_tier, a.template_id_final, COUNT(*) as n
  FROM job_analysis a JOIN applications app ON a.job_id = app.job_id
  WHERE app.applied_at >= '2026-04-02'
  GROUP BY a.resume_tier, a.template_id_final;
  ```

**Section B risk register (applies across all tasks):**
- **Risk 1**: Renderer API skew in `_build_context`. Mitigation: Task 1 smoke-tests the FULL_CUSTOMIZE path before changing anything.
- **Risk 2**: C2 `FULL_CUSTOMIZE` prompt may not output `experiences[].bullets` cleanly. Mitigation: Task 3 inspects the prompt and patches if needed.
- **Risk 3**: Bullet library v5.0 `verified_bullets[].content` paragraphs may need the `narrative_role` ordering respected for readability. Mitigation: Task 3 enforces `recommended_sequences` in prompt.
- **Risk 4**: Removing `USE_TEMPLATE`/`ADAPT_TEMPLATE` branches could break existing `job_analysis` rows already stored with those tiers. Mitigation: Task 5 adds a backfill/re-analyze path for pre-existing high-score rows.
- **Rollback checkpoint**: After each phase, run `git status`; if validation fails, `git revert HEAD` + re-open task.

---

## Phase 0 — Baseline Capture

### Task 0.1: Capture current tier distribution

**Files:**
- Create: `docs/plans/2026-04-17-baseline-tier-snapshot.md`

**Step 1: Run query**

```bash
cd C:/Users/huang/github/job-hunter && python -c "
from src.db.job_db import JobDatabase
db = JobDatabase()
rows = db.execute('''
    SELECT a.resume_tier, a.template_id_final, COUNT(*) as n
    FROM job_analysis a JOIN applications app ON a.job_id = app.job_id
    WHERE app.applied_at >= '2026-04-02'
    GROUP BY a.resume_tier, a.template_id_final
    ORDER BY n DESC
''')
for r in rows:
    print(r['resume_tier'], r['template_id_final'], r['n'])
" | tee docs/plans/2026-04-17-baseline-tier-snapshot.md
```

Expected output (as of 2026-04-17):
```
USE_TEMPLATE DE 35
USE_TEMPLATE ML 21
ADAPT_TEMPLATE DE 10
USE_TEMPLATE DS 5
ADAPT_TEMPLATE ML 2
FULL_CUSTOMIZE DE 1
```

**Step 2: Commit**

```bash
git add docs/plans/2026-04-17-baseline-tier-snapshot.md
git commit -m "docs: capture pre-revert tier distribution baseline"
```

---

### Task 0.2: Smoke-test current FULL_CUSTOMIZE path on one existing job

Verify the flow-layout path still works end-to-end before making changes. Pick the one job already stored with `FULL_CUSTOMIZE` tier.

**Files:**
- Read-only: `src/resume_renderer.py`, `templates/base_template.html`

**Step 1: Find the test job**

```bash
cd C:/Users/huang/github/job-hunter && python -c "
from src.db.job_db import JobDatabase
db = JobDatabase()
rows = db.execute(\"SELECT job_id, template_id_final FROM job_analysis WHERE resume_tier='FULL_CUSTOMIZE' LIMIT 1\")
for r in rows: print(r['job_id'], r['template_id_final'])
"
```

Expected: one job_id is printed.

**Step 2: Render it**

```bash
python scripts/job_pipeline.py --analyze-job <JOB_ID>  # skip if already analyzed
python -m src.resume_renderer --job <JOB_ID>
```

Expected:
- HTML written to `output/Fei_Huang_*.html`
- PDF generated via Playwright
- 2-page flow layout (not single-page compressed)
- `experiences` loop visible in HTML (grep: `<div class="experience-item">` appears ≥ 2 times)

**Step 3: Sanity check**

```bash
grep -c 'class="experience-item"' output/Fei_Huang_*.html | head -1
```

Expected: >= 2 (proves the `{% for exp in experiences %}` loop ran).

**Step 4: No commit — read-only smoke test.**

**If smoke test fails**, STOP and diagnose before continuing. This would invalidate the whole plan.

---

## Phase 1 — Force All Jobs to FULL_CUSTOMIZE Tier

The single highest-leverage change. After this, every new application goes through per-job customization.

### Task 1.1: Locate and update the C1 AI prompt tier selection

**Files:**
- Read: `config/ai_config.yaml` lines ~185-220 (the C1 prompt text containing the tier instructions)
- Modify: `config/ai_config.yaml`

**Step 1: Inspect current C1 prompt tier instructions**

```bash
grep -n "USE_TEMPLATE\|ADAPT_TEMPLATE\|FULL_CUSTOMIZE" config/ai_config.yaml
```

Expected to find (around line 190-215):
```
- USE_TEMPLATE: Default. Choose unless hiring manager would question fit at first glance.
- ADAPT_TEMPLATE: Only when structural positioning mismatch exists: bio positioning is wrong,
- FULL_CUSTOMIZE: Only when no template is remotely close.
...
"tier": "USE_TEMPLATE",
```

**Step 2: Rewrite the tier section in C1 prompt**

Replace the tier description block with:

```
TIER SELECTION (always FULL_CUSTOMIZE after 2026-04-17 revert):

- FULL_CUSTOMIZE: ALWAYS use this tier. The resume must be tailored per-job with bullets
  selected from the bullet library. Static pre-made PDFs and zone-compressed single-page
  templates have been retired because they produced 0 interviews across 77 applications.

OUTPUT template_id based on target_roles keyword match (DE / ML / DS). The template_id
controls which bullet sequences and skill categories the C2 prompt prioritizes, but all
tiers now share the same flow-layout 2-page base_template.html.
```

And update the example JSON output block (around line 213) from:
```yaml
"tier": "USE_TEMPLATE",
```
to:
```yaml
"tier": "FULL_CUSTOMIZE",
```

**Step 3: Commit**

```bash
git add config/ai_config.yaml
git commit -m "feat(ai-analyzer): force FULL_CUSTOMIZE tier for all jobs

Pre-made PDFs (USE_TEMPLATE, 82% of post-2026-04-02 apps) and zone templates
(ADAPT_TEMPLATE, 16%) produced 0 interviews. All jobs now flow through per-job
customized base_template.html. template_id (DE/ML/DS) still used by C2 prompt
to prioritize bullet sequences and skill categories."
```

---

### Task 1.2: Backfill default tier in `evaluate_job` fallback

**Files:**
- Modify: `src/ai_analyzer.py` lines 739-746 (the fallback routing dict when `resume_routing` key missing from C1 response)

**Step 1: Read the fallback**

```bash
grep -n "'tier': 'USE_TEMPLATE'" src/ai_analyzer.py
```

Expected: line ~740.

**Step 2: Change default**

In `src/ai_analyzer.py`, find:
```python
c1_routing = parsed.get('resume_routing') or {
    'tier': 'USE_TEMPLATE',
    'template_id': code_decision.template_id,
    ...
}
```

Change `'tier': 'USE_TEMPLATE'` to `'tier': 'FULL_CUSTOMIZE'`.

**Step 3: Run tests**

```bash
cd C:/Users/huang/github/job-hunter && python -m pytest tests/ -v -k "c1 or routing" 2>&1 | tail -20
```

Expected: tests still pass (or clearly identify any that assumed USE_TEMPLATE default — those need updating to FULL_CUSTOMIZE).

**Step 4: Commit**

```bash
git add src/ai_analyzer.py
git commit -m "fix(ai-analyzer): default missing resume_routing to FULL_CUSTOMIZE

When C1 response lacks resume_routing key, fallback used to pick USE_TEMPLATE
(static PDF). Revert path now defaults to FULL_CUSTOMIZE so tailoring happens
even when AI forgets the field."
```

---

### Task 1.3: Remove tier-1 auto-escalation safeguard (now a no-op but confusing)

**Files:**
- Modify: `src/template_registry.py` lines 89-100 (`apply_tier1_safeguard`)

**Step 1: Read the safeguard**

The function escalates `USE_TEMPLATE` → `ADAPT_TEMPLATE` when code confidence is low. With FULL_CUSTOMIZE as default, this is dead code.

**Step 2: Simplify to pass-through**

Replace function body with:

```python
def apply_tier1_safeguard(routing: Dict, code_decision: RoutingDecision) -> Dict:
    """Historical escalation from USE_TEMPLATE to ADAPT_TEMPLATE.

    After 2026-04-17 revert, both USE_TEMPLATE and ADAPT_TEMPLATE are retired
    in favor of unified FULL_CUSTOMIZE. This function is kept as a no-op for
    backward compatibility with callers.
    """
    return routing
```

**Step 3: Run tests**

```bash
python -m pytest tests/ -v -k "template_registry or safeguard" 2>&1 | tail -20
```

**Step 4: Commit**

```bash
git add src/template_registry.py
git commit -m "refactor(template_registry): retire tier-1 auto-escalation safeguard

USE_TEMPLATE and ADAPT_TEMPLATE are retired in favor of unified FULL_CUSTOMIZE,
making the auto-escalation a no-op. Function body simplified to pass-through."
```

---

## Phase 2 — Simplify Renderer

Remove the dead `USE_TEMPLATE` and `ADAPT_TEMPLATE` render paths now that every job goes FULL_CUSTOMIZE.

### Task 2.1: Write a regression test asserting USE_TEMPLATE path is never taken

**Files:**
- Create: `tests/test_resume_renderer_full_customize_only.py`

**Step 1: Write failing test**

```python
"""Regression tests for resume_renderer after 2026-04-17 tier revert.

Every job with analysis must render through the FULL_CUSTOMIZE path
(base_template.html + experiences loop). USE_TEMPLATE (static PDF copy)
and ADAPT_TEMPLATE (zone DE/ML/DS) are retired.
"""
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.resume_renderer import ResumeRenderer


def test_render_resume_rejects_use_template_tier():
    """A tier='USE_TEMPLATE' analysis should NOT copy a static PDF anymore."""
    renderer = ResumeRenderer()
    with patch.object(renderer.db, 'get_analysis') as mock_get, \
         patch.object(renderer, '_render_template_copy') as mock_copy:
        mock_get.return_value = {
            'resume_tier': 'USE_TEMPLATE',
            'template_id_final': 'DE',
            'tailored_resume': '{}',
        }
        renderer.render_resume('fake-job-id')
        mock_copy.assert_not_called()


def test_render_resume_rejects_adapt_template_tier():
    """A tier='ADAPT_TEMPLATE' analysis should NOT use zone rendering anymore."""
    renderer = ResumeRenderer()
    with patch.object(renderer.db, 'get_analysis') as mock_get, \
         patch.object(renderer, '_render_adapt_template') as mock_adapt:
        mock_get.return_value = {
            'resume_tier': 'ADAPT_TEMPLATE',
            'template_id_final': 'DE',
            'tailored_resume': '{}',
        }
        renderer.render_resume('fake-job-id')
        mock_adapt.assert_not_called()
```

**Step 2: Run test to verify failure**

```bash
python -m pytest tests/test_resume_renderer_full_customize_only.py -v
```

Expected: FAIL (both `_render_template_copy` and `_render_adapt_template` currently get called for those tiers).

**Step 3: Commit the failing test**

```bash
git add tests/test_resume_renderer_full_customize_only.py
git commit -m "test: add failing regression tests for tier retirement"
```

---

### Task 2.2: Route legacy `USE_TEMPLATE` / `ADAPT_TEMPLATE` tiers through FULL_CUSTOMIZE

**Files:**
- Modify: `src/resume_renderer.py` lines 144-152 (the tier dispatch block)

**Step 1: Read current dispatch**

```python
# Lines 144-156 current shape:
if tier == 'USE_TEMPLATE':
    return self._render_template_copy(job_id, analysis)
if tier == 'ADAPT_TEMPLATE':
    result = self._render_adapt_template(job_id, analysis)
    if result is None:
        print(f"[Renderer] ADAPT_TEMPLATE failed for {job_id}, falling back to USE_TEMPLATE")
        return self._render_template_copy(job_id, analysis)
    return result
```

**Step 2: Replace with unified FULL_CUSTOMIZE path**

Replace lines 144-156 with:

```python
# 2026-04-17 revert: USE_TEMPLATE (static PDF) and ADAPT_TEMPLATE (zone) are retired.
# Legacy tiers stored in pre-revert job_analysis rows are transparently upgraded.
if tier in ('USE_TEMPLATE', 'ADAPT_TEMPLATE'):
    print(f"[Renderer] Upgrading legacy tier {tier} -> FULL_CUSTOMIZE for {job_id}")
    tier = 'FULL_CUSTOMIZE'
    # Fall through to FULL_CUSTOMIZE block below
```

The existing `tailored_json = analysis.get('tailored_resume', '')` block continues as before.

**Caveat**: Legacy rows may have `tailored_resume` in zone schema format (`slot_overrides`, `entry_visibility`). Task 2.3 adds detection + re-analyze request.

**Step 3: Run regression test from 2.1**

```bash
python -m pytest tests/test_resume_renderer_full_customize_only.py -v
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/resume_renderer.py
git commit -m "refactor(renderer): retire USE_TEMPLATE and ADAPT_TEMPLATE dispatch

Legacy tiers are transparently upgraded to FULL_CUSTOMIZE. Static PDF copy and
zone rendering branches no longer run for new jobs. Old job_analysis rows with
zone-schema tailored_resume are handled by Task 2.3."
```

---

### Task 2.3: Detect legacy zone-schema `tailored_resume` and flag for re-analyze

**Files:**
- Modify: `src/resume_renderer.py` after the `tailored = json.loads(tailored_json)` block (around line 159-170)

**Step 1: Add schema detection**

After the `json.loads` block, insert:

```python
# 2026-04-17: detect legacy zone-schema output (slot_overrides / entry_visibility)
# and refuse to render — require re-analysis under FULL_CUSTOMIZE prompt.
is_zone_schema = (
    'slot_overrides' in tailored
    or 'skills_override' in tailored
    or 'entry_visibility' in tailored
)
has_flow_schema = 'experiences' in tailored and isinstance(tailored.get('experiences'), list)
if is_zone_schema and not has_flow_schema:
    print(
        f"[Renderer] Legacy zone-schema tailored_resume for {job_id}. "
        f"Re-run: python scripts/job_pipeline.py --analyze-job {job_id}"
    )
    return None
```

**Step 2: Add test**

Append to `tests/test_resume_renderer_full_customize_only.py`:

```python
def test_render_resume_rejects_zone_schema_tailored_json():
    """Pre-revert tailored_resume with slot_overrides must be re-analyzed, not rendered."""
    renderer = ResumeRenderer()
    with patch.object(renderer.db, 'get_analysis') as mock_get, \
         patch.object(renderer.db, 'get_job') as mock_job:
        mock_get.return_value = {
            'resume_tier': 'FULL_CUSTOMIZE',
            'template_id_final': 'DE',
            'tailored_resume': json.dumps({
                'slot_overrides': {'bio_1': 'something'},
                'entry_visibility': {'glp': True},
                'change_summary': 'zone edit',
            }),
        }
        mock_job.return_value = {'id': 'fake-job-id', 'company': 'Test', 'title': 'DE'}
        result = renderer.render_resume('fake-job-id')
        assert result is None, "Legacy zone schema must not render"
```

**Step 3: Run test**

```bash
python -m pytest tests/test_resume_renderer_full_customize_only.py -v
```

Expected: PASS.

**Step 4: Commit**

```bash
git add src/resume_renderer.py tests/test_resume_renderer_full_customize_only.py
git commit -m "feat(renderer): detect legacy zone-schema JSON and skip render

Pre-revert job_analysis rows whose tailored_resume is slot_overrides-shaped
get a clear re-analyze hint instead of rendering garbage HTML."
```

---

### Task 2.4: Mark zone-path methods as deprecated (no delete yet)

**Files:**
- Modify: `src/resume_renderer.py` methods `_render_template_copy`, `_render_adapt_template`, `_schema_to_context`

**Step 1: Add deprecation docstrings**

At the top of each method, add:

```python
# DEPRECATED 2026-04-17: zone-based and static-PDF render paths are retired.
# Kept for reference only; not reachable from render_resume() after tier revert.
# Delete after 2 weeks of stable FULL_CUSTOMIZE operation (target: 2026-05-01).
```

**Step 2: Commit**

```bash
git add src/resume_renderer.py
git commit -m "refactor(renderer): mark zone render methods deprecated, delete 2026-05-01"
```

---

## Phase 3 — Archive Zone Templates

### Task 3.1: Move zone templates to archive

**Files:**
- Move: `templates/base_template_DE.html` → `templates/archive/2026-04-02-zone-DE.html`
- Move: `templates/base_template_ML.html` → `templates/archive/2026-04-02-zone-ML.html`
- Move: `templates/base_template_DS.html` → `templates/archive/2026-04-07-zone-DS.html`

**Step 1: Move files**

```bash
cd C:/Users/huang/github/job-hunter
git mv templates/base_template_DE.html templates/archive/2026-04-02-zone-DE.html
git mv templates/base_template_ML.html templates/archive/2026-04-02-zone-ML.html
git mv templates/base_template_DS.html templates/archive/2026-04-07-zone-DS.html
```

**Step 2: Verify no remaining references**

```bash
grep -rn "base_template_DE\|base_template_ML\|base_template_DS" src/ config/ tests/ 2>&1 | grep -v archive
```

Expected: only `src/resume_renderer.py:_render_adapt_template` (the `template_map` dict inside the deprecated method) references these. That's OK — deprecated method, will be deleted 2026-05-01.

**Step 3: Commit**

```bash
git commit -m "chore: archive zone-based DE/ML/DS templates (retired 2026-04-17)

Single-page absolute-positioned zone templates produced 0 interviews across
12 ADAPT_TEMPLATE applications. Moved to templates/archive/ for reference."
```

---

### Task 3.2: Trim `config/template_registry.yaml` — keep target_roles, drop slot_schema

Zone templates are archived, but DE/ML/DS routing label is still used by C2 prompt to pick bullet priorities. Keep only what's needed.

**Files:**
- Modify: `config/template_registry.yaml`

**Step 1: Rewrite each enabled template (DE, ML, DS) to minimal shape**

For each, keep only:
- `enabled`
- `target_roles` (keyword list for code-side matching)
- `bio_positioning` (used by C2 prompt to write bio)
- `key_strengths` (used by C2 prompt for emphasis)

Delete:
- `svg`, `pdf` (static PDF paths — no longer copied)
- `slot_schema` entirely (zone-only concept)

Keep the disabled `Backend` template untouched (it's already `enabled: false`).

Target shape:

```yaml
templates:
  DE:
    enabled: true
    target_roles:
      - "data engineer"
      - "data platform"
      - "etl"
      - "pipeline"
      - "big data"
      - "analytics engineer"
      - "bi engineer"
    bio_positioning: "Data Engineer"
    key_strengths:
      - "Spark/Delta Lake"
      - "AWS data stack"
      - "financial domain"
      - "Python"

  ML:
    enabled: true
    target_roles:
      - "machine learning"
      - "ml engineer"
      # ... (keep all existing entries)
    bio_positioning: "ML Engineer / Data Scientist"
    key_strengths:
      - "PyTorch"
      - "RL thesis"
      - "research background"
      - "model deployment"

  DS:
    enabled: true
    target_roles:
      - "data scientist"
      # ...
    bio_positioning: "Data Scientist"
    key_strengths:
      - "A/B Testing"
      - "Statistical Modeling"
      - "Feature Engineering"
      - "Python/SQL"
```

**Step 2: Update `validate_tier2_output` to tolerate missing slot_schema**

In `src/template_registry.py`, modify:

```python
def validate_tier2_output(output: Dict, schema: Dict) -> List[str]:
    """DEPRECATED 2026-04-17: zone-schema validator, not called by FULL_CUSTOMIZE path."""
    if not schema:
        return ["template has no slot_schema (retired 2026-04-17)"]
    # ... existing body
```

**Step 3: Run tests**

```bash
python -m pytest tests/ -v -k "registry or template_registry" 2>&1 | tail -20
```

Expected: tests pass or reveal stale assertions about `slot_schema` — fix those by removing the assertions.

**Step 4: Commit**

```bash
git add config/template_registry.yaml src/template_registry.py
git commit -m "chore(registry): drop slot_schema from DE/ML/DS

slot_schema was zone-only. target_roles / bio_positioning / key_strengths are
still used by C2 FULL_CUSTOMIZE prompt for bullet prioritization."
```

---

## Phase 4 — Verify and Strengthen the C2 FULL_CUSTOMIZE Prompt

The critical loop: C2 must produce `{experiences: [...], projects: [...], skills: [...]}` with bullets selected from the bullet library.

### Task 4.1: Inspect the current C2 FULL_CUSTOMIZE prompt

**Files:**
- Read: `config/ai_config.yaml` — find the prompt used by `_build_tailor_prompt` (ai_analyzer.py line 785)
- Read: `src/ai_analyzer.py` `_build_tailor_prompt` (find via grep)

**Step 1: Find and read the prompt template**

```bash
grep -n "_build_tailor_prompt\|c2_prompt\|tailor_prompt" src/ai_analyzer.py config/ai_config.yaml | head -10
```

Read the prompt text and inspect:
- Does it instruct AI to output `experiences[].bullets` as a list of strings?
- Does it reference bullet library IDs (via the `_load_bullet_library` block that builds `sections`)?
- Does it enforce `recommended_sequences` from bullet_library.yaml for narrative order?
- Does it include 6 skill categories (matching flow-layout template)?

**Step 2: Capture baseline in a note file**

Write findings to `docs/plans/2026-04-17-c2-prompt-audit.md` (≤ 300 words): list 3-5 concrete gaps/OK items.

**Step 3: Commit the audit**

```bash
git add docs/plans/2026-04-17-c2-prompt-audit.md
git commit -m "docs: audit C2 FULL_CUSTOMIZE prompt for flow-layout coverage"
```

---

### Task 4.2: Patch C2 prompt gaps (if any)

**Files:**
- Modify: `config/ai_config.yaml` (the prompt text) and/or `src/ai_analyzer.py:_build_tailor_prompt`

**Only proceed if Task 4.1 found gaps.** For each gap, write a failing test first. Common gap candidates:

1. **Missing `recommended_sequences` enforcement** — C2 prompt must instruct AI to follow `recommended_sequences[role_type]` ordering in bullet_library.yaml.
2. **Missing 6-category skill enforcement** — prompt should require at least 5 of the 6 categories: Languages & Core, Data Engineering, Cloud & DevOps, Databases, ML/AI Frameworks, Research Methods.
3. **Missing "select 3-5 bullets per role" guidance** — prompt should explicitly cap bullets to 3-5 per experience, 2-3 per project.
4. **Missing Interests/Languages default** — the Additional section (Interests: "Philosophy, strategy games, distance running, analytical writing"; Languages: "English (Fluent), Mandarin (Native)") is currently baked into `base_context`, so C2 doesn't need to emit it. Verify.

**Step 1: Write one failing test per gap**

Example for gap (3):

```python
# tests/test_c2_prompt_coverage.py
def test_c2_prompt_caps_bullets_per_experience():
    from src.ai_analyzer import AIAnalyzer
    analyzer = AIAnalyzer()
    prompt = analyzer._build_tailor_prompt(
        job={'id': 'x', 'title': 'Data Engineer', 'company': 'Test',
             'description': 'spark kafka aws'},
        analysis={'ai_score': 7.0, 'template_id_final': 'DE'}
    )
    assert '3-5' in prompt or '3 to 5' in prompt or '3–5' in prompt, \
        "C2 prompt must cap bullets per experience to 3-5"
```

**Step 2: Run test to verify failure**

```bash
python -m pytest tests/test_c2_prompt_coverage.py -v
```

**Step 3: Patch the prompt text**

Update the C2 prompt in `config/ai_config.yaml` with explicit instructions. Keep each addition ≤ 3 lines.

**Step 4: Run test to verify pass**

```bash
python -m pytest tests/test_c2_prompt_coverage.py -v
```

**Step 5: Commit**

```bash
git add config/ai_config.yaml tests/test_c2_prompt_coverage.py
git commit -m "fix(c2-prompt): enforce bullet caps, skill categories, sequence order"
```

---

## Phase 5 — End-to-End Validation on 3 Sample Jobs

Prove the pipeline produces high-quality 2-page resumes for DE, ML, and DS variants.

### Task 5.1: Select 3 reference jobs from recent analysis

**Step 1: Pick 3 recent high-scoring jobs, one per template**

```bash
python -c "
from src.db.job_db import JobDatabase
db = JobDatabase()
for tid in ['DE', 'ML', 'DS']:
    rows = db.execute(\"\"\"
        SELECT a.job_id, j.title, j.company, a.ai_score
        FROM job_analysis a JOIN jobs j ON a.job_id = j.id
        WHERE a.template_id_final = ? AND a.ai_score >= 6.0
        ORDER BY a.ai_score DESC LIMIT 1
    \"\"\", (tid,))
    for r in rows:
        print(tid, r['job_id'], r['ai_score'], r['title'], '@', r['company'])
"
```

Record the 3 job IDs (e.g., `DE_JOB_ID`, `ML_JOB_ID`, `DS_JOB_ID`).

### Task 5.2: Re-analyze all 3 jobs under FULL_CUSTOMIZE prompt

```bash
python scripts/job_pipeline.py --analyze-job <DE_JOB_ID>
python scripts/job_pipeline.py --analyze-job <ML_JOB_ID>
python scripts/job_pipeline.py --analyze-job <DS_JOB_ID>
```

Expected: each one stores `resume_tier='FULL_CUSTOMIZE'` and a `tailored_resume` JSON with `experiences[]`, `projects[]`, `skills[]`.

Verify:

```bash
python -c "
from src.db.job_db import JobDatabase
import json
db = JobDatabase()
for jid in ['<DE_JOB_ID>', '<ML_JOB_ID>', '<DS_JOB_ID>']:
    a = db.get_analysis(jid)
    t = json.loads(a.get('tailored_resume') or '{}')
    print(jid, a.get('resume_tier'),
          'exps=', len(t.get('experiences', [])),
          'projs=', len(t.get('projects', [])),
          'skills=', len(t.get('skills', [])))
"
```

Expected:
- `resume_tier == FULL_CUSTOMIZE` for all 3
- `exps >= 2`, `projs >= 1`, `skills >= 5` for all 3

### Task 5.3: Render all 3 to HTML+PDF

```bash
python -m src.resume_renderer --job <DE_JOB_ID>
python -m src.resume_renderer --job <ML_JOB_ID>
python -m src.resume_renderer --job <DS_JOB_ID>
```

Expected: each one produces a PDF in `output/` and a submit copy in `ready_to_send/`.

### Task 5.4: Quantitative visual diff against pre-upgrade reference

**Files:**
- Reference: any of `interview_prep/20260225_*`, `interview_prep/20260302_*`, `interview_prep/20260320_*` (the pre-upgrade interview-winning versions)
- Tool: `scripts/resume_visual_diff.py`

**Step 1: Run visual diff**

```bash
python scripts/resume_visual_diff.py \
    --a output/Fei_Huang_<DE_JOB>_*.pdf \
    --b interview_prep/20260225_Source_ag_Data_Engineer/Fei_Huang_Resume.pdf
```

Expected output: page count, unique tech keyword count, bullet count per section. The new resume should match or exceed pre-upgrade on:
- Pages: 2 (not 1)
- Unique techs: ≥ 28
- Total bullets: ≥ 12
- Skill categories: 6

**Step 2: Document in a validation note**

Write `docs/plans/2026-04-17-validation-results.md` with:
- The 3 job_ids tested
- Metrics table (pages, unique techs, bullets, skill categories) for each
- PASS / FAIL verdict per metric
- Screenshot references (PDF thumbnails if useful)

**Step 3: Commit**

```bash
git add docs/plans/2026-04-17-validation-results.md
git commit -m "docs: validate 3 sample resumes post-revert (DE/ML/DS)"
```

---

## Phase 6 — Controlled Rollout

### Task 6.1: Do NOT run `--prepare` on the full backlog

**Explicit guard:** Do not run `python scripts/job_pipeline.py --prepare` until Phase 6.2 is complete.

**Reason:** The backlog contains dozens of pre-revert `job_analysis` rows with `USE_TEMPLATE`/`ADAPT_TEMPLATE` tiers. Task 2.2 upgrades them transparently, but Task 2.3 skips zone-schema `tailored_resume` — so a blind `--prepare` would output nothing for most of them, confusing downstream steps.

### Task 6.2: Re-analyze the next-5-to-apply backlog

**Step 1: Identify the 5 highest-scoring un-applied jobs**

```bash
python -c "
from src.db.job_db import JobDatabase
db = JobDatabase()
rows = db.execute('''
    SELECT a.job_id, j.title, j.company, a.ai_score
    FROM job_analysis a JOIN jobs j ON a.job_id = j.id
    LEFT JOIN applications app ON a.job_id = app.job_id
    WHERE app.status IS NULL AND a.ai_score >= 6.0
    ORDER BY a.ai_score DESC LIMIT 5
''')
for r in rows: print(r['job_id'], r['ai_score'], r['title'], '@', r['company'])
"
```

**Step 2: Re-analyze each**

```bash
for JOB_ID in ...; do
    python scripts/job_pipeline.py --analyze-job $JOB_ID
done
```

### Task 6.3: Run `--prepare` on the 5 re-analyzed jobs only

```bash
python scripts/job_pipeline.py --prepare --limit 5
```

Expected: 5 PDFs in `ready_to_send/`, all 2-page flow-layout, all unique per job.

### Task 6.4: Manual visual QC before sending

For each of the 5 PDFs:
- Open and verify 2 pages, flow-layout
- Verify bullets match the JD's emphasis (fintech bullets surface for fintech JDs, ML bullets for ML JDs, etc.)
- Verify no hardcoded "Greenhouse Sensor" bullets from the zone-era slot_schema appear

Only after all 5 pass QC, resume sending applications.

---

## Section C — Parallel Supply-Side Triage (Manual, out of scope for this plan)

Tracked in the design doc (`2026-04-17-resume-template-revert-design.md` Section C):

1. Pause `--prepare` auto pipeline (enforced by Phase 6.1 guard above)
2. Hand-pick 5-8 high-conviction targets (fintech / MLOps / Senior DE in regulated domains)
3. For each, manually review the AI-generated bullet selection before sending
4. Personalize the first 2 sentences of the cover letter (per ENPICOM Jorrit feedback)

**Owner:** User (Fei Huang) — manual execution. Not automated.

**Checkpoint date:** 2026-05-01. If ≥ 1 interview invitation from the 5-8 precision investments, the revert is validated. If 0, escalate to strategic review of `memory/project_job_search_strategy_2026_04.md`.

---

## Done Criteria

- [ ] Phase 0: Baseline snapshot captured, smoke test passes
- [ ] Phase 1: C1 prompt defaults to FULL_CUSTOMIZE; fallback tier is FULL_CUSTOMIZE; auto-escalation is a no-op
- [ ] Phase 2: Renderer upgrades legacy tiers; regression tests pass; zone methods deprecated
- [ ] Phase 3: Zone templates archived; registry trimmed to target_roles + bio_positioning + key_strengths
- [ ] Phase 4: C2 prompt audited and patched; prompt-coverage tests pass
- [ ] Phase 5: 3 sample resumes (DE/ML/DS) render as 2-page flow-layout with ≥ 28 unique techs, 6 skill categories, ≥ 12 bullets
- [ ] Phase 6: 5 precision applications sent and manually QC'd
- [ ] 2 weeks later (2026-05-01): assess interview invitation rate; if still zero, escalate to Section C manual supply-side review
