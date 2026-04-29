# Resume Quality Fixes Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix 13 resume generation quality issues across bullet library data, HTML template/CSS, AI prompt, and renderer fallback logic.

**Architecture:** Three independent layers of fixes: (1) bullet_library.yaml data cleanup, (2) base_template.html CSS/layout, (3) tailor.md prompt + resume_renderer.py fallback logic. Layer 3 implements "double insurance" — the renderer fills deterministic data (company notes, certification, dates) from the bullet library rather than trusting AI output.

**Tech Stack:** Python, Jinja2, YAML, CSS, HTML

---

### Task 1: Bullet Library Data Cleanup

**Files:**
- Modify: `assets/bullet_library.yaml`

**Step 1: Delete Deribit Options project**

Remove the entire `deribit_options` block (lines ~393-409) from the `projects:` section, and remove `deribit_options` from `active_sections.project_keys`.

**Step 2: Delete evolutionary_robotics_research**

The project is NOT in the current `bullet_library.yaml` `projects:` section (it was already removed in v7.x), but `evolutionary_robotics_research` IS listed in `active_sections.project_keys`. Remove it from there.

**Step 3: Delete deep_learning_fundamentals**

Remove `deep_learning_fundamentals` from `active_sections.project_keys`.

**Step 4: Fix Greenhouse Sensor Pipeline date**

In the `greenhouse_sensor_pipeline` project block, change:
```yaml
period: "2025"
```
to:
```yaml
period: "Feb. 2026 - Mar. 2026"
```

**Step 5: Fix GraphSAGE GNN date**

In the `graphsage_gnn` project block, change:
```yaml
period: "2025"
```
to:
```yaml
period: "Dec. 2024 - Jan. 2025"
```

**Step 6: Fix blog URL**

In the `personal_info` section, change:
```yaml
blog_url: "https://feithink.org"
```
to:
```yaml
blog_url: "https://www.feithink.org/"
```

Also fix the hardcoded substack URL in `templates/resume_master.html` line 354:
Change `https://feithink.substack.com` to `https://www.feithink.org/` and `feithink.substack.com` to `feithink.org`.

**Step 7: Update library version header**

Change the first line from `# VERIFIED BULLET LIBRARY v7.4 (2026-04-28)` to `# VERIFIED BULLET LIBRARY v7.5 (2026-04-29)`.

**Step 8: Run tests to verify no breakage**

Run: `python -m pytest tests/ -v --tb=short -x`
Expected: All existing tests pass (bullet library changes are data-only).

**Step 9: Commit**

```bash
git add assets/bullet_library.yaml templates/resume_master.html
git commit -m "fix(bullet-library): cleanup projects, fix dates and blog URL (v7.5)"
```

---

### Task 2: Template CSS Fixes (Certification Layout + Link Visibility)

**Files:**
- Modify: `templates/base_template.html`

**Step 1: Redesign certification section with flex layout**

In `base_template.html`, replace the current certification CSS and HTML.

CSS changes — replace the existing cert styles (lines ~267-273):
```css
/* ── Certifications ── */
.cert-text {
    font-size: 10pt;
    font-weight: normal;
    color: var(--primary-color);
}
.cert-label { font-weight: bold; }
.cert-verify { color: var(--primary-color); text-decoration: none; }
```
with:
```css
/* ── Certifications ── */
.cert-item { margin-bottom: 8pt; }
.cert-header {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 1pt;
}
.cert-name {
    font-weight: bold;
    font-size: 10.5pt;
    color: var(--primary-color);
}
.cert-date {
    font-size: 9.5pt;
    color: var(--text-muted);
    font-style: italic;
}
.cert-detail {
    font-size: 10pt;
    color: var(--primary-color);
}
.cert-verify {
    color: var(--link-color);
    text-decoration: none;
}
```

HTML changes — replace the certification block (lines ~348-352):
```html
{% if certification_name %}
<div class="edu-item">
    <div class="cert-text"><span class="cert-label">Certification:</span> {{ certification_name }}{% if certification_date %} ({{ certification_date }}){% endif %}{% if certification_url %} &mdash; <a class="cert-verify" href="{{ certification_url }}">Verify</a>{% endif %}</div>
</div>
{% endif %}
```
with:
```html
{% if certification_name %}
<div class="cert-item">
    <div class="cert-header">
        <span class="cert-name">{{ certification_name }}</span>
        {% if certification_date %}<span class="cert-date">{{ certification_date }}</span>{% endif %}
    </div>
    {% if certification_url %}
    <div class="cert-detail"><a class="cert-verify" href="{{ certification_url }}">Verify Credential</a></div>
    {% endif %}
</div>
{% endif %}
```

**Step 2: Fix PDF link visibility**

In the `@media print` block (line ~283-288), change:
```css
a { text-decoration: none; color: var(--primary-color); }
```
to:
```css
a { text-decoration: none; color: var(--link-color); }
```

This makes all links blue in PDF output (LinkedIn, GitHub, blog, Verify).

**Step 3: Run tests**

Run: `python -m pytest tests/test_resume_renderer_full_customize_only.py -v`
Expected: PASS (template changes don't affect Python tests).

**Step 4: Commit**

```bash
git add templates/base_template.html
git commit -m "fix(template): certification flex layout, blue links in PDF"
```

---

### Task 3: AI Prompt — All 5 Experiences + DocBridge Priority

**Files:**
- Modify: `assets/prompts/tailor.md`

**Step 1: Change experience selection from "2-3" to "all 5, control depth"**

In `tailor.md`, make these changes:

a) In the example JSON (around line 46-71), add the missing experiences (Independent Quantitative Researcher and Henan Energy) to the example `experiences` array with 1 bullet each, to show the AI the expected format for thin entries.

b) Replace the rule at line 203:
```
1. Use ONLY bullet IDs from the provided bullet library - do not fabricate
2. MUST include 2-3 different work experiences from different companies
```
with:
```
1. Use ONLY bullet IDs from the provided bullet library - do not fabricate
2. MUST include ALL 5 work experiences. Control depth via bullet count:
   - Most relevant 2-3 companies for the JD: 2-4 bullets each
   - Less relevant companies: 1 bullet each (use the recommended_sequences[0])
   - Order: most recent first (GLP → Independent Researcher → BQ → Ele.me → Henan Energy)
```

c) Update the `### CAREER NOTE` section (around line 185-187):
Replace:
```
### CAREER NOTE
- show_career_note: set false if Independent Quantitative Researcher is included as an experience (the 2019-2023 period is covered)
- set true only if there is a visible chronological gap not covered by any included experience
```
with:
```
### CAREER NOTE
- show_career_note: ALWAYS set false (all 5 experiences are always included, so there are no gaps)
```

**Step 2: Strengthen DocBridge priority for AI/ML roles**

In the `### PROJECT SELECTION` section (around line 173-178), change:
```
- For ML Engineer / AI Engineer / Document AI roles: prioritize DocBridge (94.8% F1, 3 fine-tuned models on A100 GPUs)
```
to:
```
- For ML Engineer / AI Engineer / Document AI roles: DocBridge is MANDATORY as first project (94.8% F1, 3 fine-tuned models on A100 GPUs, production FastAPI deployment) — this is the strongest ML engineering signal in the portfolio
```

**Step 3: Commit**

```bash
git add assets/prompts/tailor.md
git commit -m "fix(prompt): require all 5 experiences, mandate DocBridge for ML/AI"
```

---

### Task 4: Renderer Fallback — Company Notes, Certification, Dates

**Files:**
- Modify: `src/resume_renderer.py`
- Test: `tests/test_resume_renderer_full_customize_only.py`

This task implements the "double insurance" principle: the renderer fills deterministic data from the bullet library when AI output is incomplete.

**Step 1: Write failing test for company note fallback**

Add to `tests/test_resume_renderer_full_customize_only.py`:

```python
def test_build_context_injects_company_notes_from_library():
    """Renderer fills company_note from bullet library when AI omits it."""
    renderer = ResumeRenderer.__new__(ResumeRenderer)
    renderer.bullet_library = {
        'work_experience': {
            'glp_technology': {
                'company': 'GLP Technology',
                'company_note': 'fintech startup',
            },
            'baiquan_investment': {
                'company': 'BQ Investment',
                'company_note': 'quant hedge fund',
            },
        },
        'education': {},
    }
    renderer.base_context = {
        'edu_master_coursework': '',
        'edu_bachelor_thesis': '',
        'career_note': '',
    }
    renderer.validator = type('V', (), {
        'validate': lambda self, t, j, tier=None: type('R', (), {
            'passed': True, 'errors': [], 'warnings': [], 'fixes': {}
        })()
    })()

    tailored = {
        'bio': 'Test bio',
        'experiences': [
            {'company': 'GLP Technology', 'bullets': ['b1'], 'title': 'DE', 'date': 'Jul. 2017 - Aug. 2019'},
            {'company': 'BQ Investment', 'bullets': ['b2'], 'title': 'QR', 'date': 'Jul. 2015 - Jun. 2017'},
        ],
        'projects': [{'name': 'P', 'bullets': ['p1']}],
        'skills': [
            {'category': 'Languages & Core', 'skills_list': 'Python'},
            {'category': 'Data Engineering', 'skills_list': 'Spark'},
            {'category': 'Cloud & DevOps', 'skills_list': 'Docker'},
        ],
    }

    context = renderer._build_context(tailored, {'company': 'TestCorp'})

    glp = next(e for e in context['experiences'] if e['company'] == 'GLP Technology')
    bq = next(e for e in context['experiences'] if e['company'] == 'BQ Investment')
    assert glp['company_note'] == 'fintech startup'
    assert bq['company_note'] == 'quant hedge fund'
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_resume_renderer_full_customize_only.py::test_build_context_injects_company_notes_from_library -v`
Expected: FAIL (KeyError or assertion error — no company_note injected yet)

**Step 3: Write failing test for certification fallback**

Add to test file:

```python
def test_build_context_fills_certification_from_library():
    """Renderer fills certification date/URL from bullet library when AI truncates."""
    renderer = ResumeRenderer.__new__(ResumeRenderer)
    renderer.bullet_library = {
        'education': {
            'certification': {
                'name': 'Databricks Certified Data Engineer Professional',
                'date': 'Apr. 2026',
                'url': 'https://credentials.databricks.com/test-id',
            },
            'master': {},
            'bachelor': {},
        },
    }
    renderer.base_context = {
        'edu_master_coursework': '',
        'edu_bachelor_thesis': '',
        'career_note': '',
        'certification_name': 'Databricks Certified Data Engineer Professional',
        'certification_date': 'Apr. 2026',
        'certification_url': 'https://credentials.databricks.com/test-id',
    }
    renderer.validator = type('V', (), {
        'validate': lambda self, t, j, tier=None: type('R', (), {
            'passed': True, 'errors': [], 'warnings': [], 'fixes': {}
        })()
    })()

    tailored = {
        'bio': 'Test bio',
        'experiences': [
            {'company': 'A', 'bullets': ['b1'], 'title': 'T', 'date': 'D'},
            {'company': 'B', 'bullets': ['b2'], 'title': 'T', 'date': 'D'},
        ],
        'projects': [{'name': 'P', 'bullets': ['p1']}],
        'skills': [
            {'category': 'Languages & Core', 'skills_list': 'Python'},
            {'category': 'Data Engineering', 'skills_list': 'Spark'},
            {'category': 'Cloud & DevOps', 'skills_list': 'Docker'},
        ],
    }

    context = renderer._build_context(tailored, {'company': 'TestCorp'})

    # Certification data should come from base_context (built from bullet library),
    # not from AI output — so it should always be complete
    assert context['certification_date'] == 'Apr. 2026'
    assert 'credentials.databricks.com' in context['certification_url']
```

**Step 4: Run test to verify it passes (certification already comes from base_context)**

Run: `python -m pytest tests/test_resume_renderer_full_customize_only.py::test_build_context_fills_certification_from_library -v`
Expected: PASS (certification is already in base_context from `_build_base_context`, so this is a regression guard).

**Step 5: Implement company note fallback in _build_context**

In `src/resume_renderer.py`, in the `_build_context` method, after line 346 (`context['experiences'] = experiences`), add company note injection:

```python
        # Experiences
        experiences = tailored.get('experiences', [])
        self._inject_company_notes(experiences)
        context['experiences'] = experiences
```

Add the new method to the `ResumeRenderer` class:

```python
    def _inject_company_notes(self, experiences: list):
        """Fill company_note from bullet library for known companies.

        The AI prompt instructs setting company_note, but it's frequently omitted.
        This provides a deterministic fallback from the bullet library.
        """
        work_exp = self.bullet_library.get('work_experience', {})
        # Build company name (lowercase) → company_note lookup
        note_lookup = {}
        for key, data in work_exp.items():
            if isinstance(data, dict):
                company = data.get('company', '')
                note = data.get('company_note', '')
                if company and note:
                    note_lookup[company.lower()] = note
                # Also check display_name for entries like independent_investor
                display = data.get('display_name', '')
                if display and note:
                    note_lookup[display.lower()] = note

        for exp in experiences:
            company = (exp.get('company') or '').lower()
            existing_note = exp.get('company_note') or ''
            if not existing_note and company in note_lookup:
                exp['company_note'] = note_lookup[company]
```

**Step 6: Run all tests**

Run: `python -m pytest tests/test_resume_renderer_full_customize_only.py -v`
Expected: ALL PASS

**Step 7: Commit**

```bash
git add src/resume_renderer.py tests/test_resume_renderer_full_customize_only.py
git commit -m "fix(renderer): inject company notes from bullet library as fallback"
```

---

### Task 5: Validator — Update minimum experience count

**Files:**
- Modify: `src/resume_validator.py`
- Test: `tests/test_resume_renderer_full_customize_only.py`

Since all 5 experiences are now required, update the validator's minimum check.

**Step 1: Update minimum experience count**

In `src/resume_validator.py`, line 412, change:
```python
        if len(experiences) < 2:
            errors.append(f"Need at least 2 experiences, got {len(experiences)}")
```
to:
```python
        if len(experiences) < 5:
            errors.append(f"Need all 5 experiences, got {len(experiences)}")
```

**Step 2: Fix existing tests**

The existing test `test_build_context_applies_selected_courses` and `test_build_context_preserves_defaults_without_ai_control` use a mock validator that always passes, so they won't break. But check if there are other tests using the real validator:

Run: `python -m pytest tests/ -v --tb=short -x`

If tests fail due to the new minimum, update the test fixtures to include 5 experiences.

**Step 3: Commit**

```bash
git add src/resume_validator.py
git commit -m "fix(validator): require all 5 experiences in structure check"
```

---

### Task 6: Integration Smoke Test

**Files:**
- No new files

**Step 1: Run full test suite**

Run: `python -m pytest tests/ -v --tb=short`
Expected: ALL PASS

**Step 2: Verify a rendered HTML manually**

Pick one recent job and re-render:
```bash
python -m src.resume_renderer --job <pick-a-job-id-from-db>
```

Then open the HTML output and verify:
- Certification has flex layout (name left, "Apr. 2026" right)
- "Verify Credential" link appears in blue
- Blog link in Additional section is blue
- Company notes appear for GLP, BQ, Ele.me
- Links in header are blue

**Step 3: Final commit (if any touch-ups needed)**

---

## Execution Notes

- **Task 1** (bullet library data) and **Task 2** (template CSS) are fully independent — can run in parallel.
- **Task 3** (prompt changes) is independent of Tasks 1-2 but note: prompt changes only affect NEW C2 runs, not already-generated resumes.
- **Task 4** (renderer fallback) depends on understanding Task 1's data structure but can be implemented independently.
- **Task 5** (validator update) should run after Task 4.
- **Task 6** (integration) runs last.
- Existing resumes in `output/` won't auto-update. To re-generate, re-run `--ai-tailor` then `--generate` for specific jobs.
