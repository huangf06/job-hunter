# Certification Verify Link — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a clickable "Verify" hyperlink next to the Databricks certification on generated resume PDFs, and update the date to "Apr. 2026".

**Architecture:** Change certification from a plain string to a structured dict (`name`/`date`/`url`) in the bullet library. Propagate through renderer and AI analyzer with backward-compatible `isinstance` checks.

**Tech Stack:** YAML data, Jinja2 template, Python (resume_renderer.py, ai_analyzer.py), pytest

**Design doc:** `docs/plans/2026-04-29-certification-link-design.md`

---

### Task 1: Update bullet_library.yaml data

**Files:**
- Modify: `assets/bullet_library.yaml:51` (education.certification)
- Modify: `assets/bullet_library.yaml:490` (skills.technical.certifications)

**Step 1: Change `education.certification` from string to dict**

```yaml
# Line 51 — replace:
  certification: "Databricks Certified Data Engineer Professional (2026)"

# With:
  certification:
    name: "Databricks Certified Data Engineer Professional"
    date: "Apr. 2026"
    url: "https://credentials.databricks.com/bac509e4-83a6-4985-8b61-90786d2013f6"
```

**Step 2: Update skills.technical.certifications date**

```yaml
# Line 490 — replace:
    certifications: ["Databricks Certified Data Engineer Professional (2026)"]

# With:
    certifications: ["Databricks Certified Data Engineer Professional (Apr. 2026)"]
```

**Step 3: Commit**

```bash
git add assets/bullet_library.yaml
git commit -m "data: change certification to structured dict with verify URL"
```

---

### Task 2: Update resume_renderer.py

**Files:**
- Modify: `src/resume_renderer.py:111`

**Step 1: Replace the single certification context line**

At line 111, replace:

```python
            'certification': edu.get('certification', ''),
```

With:

```python
            **self._extract_certification(edu),
```

**Step 2: Add the `_extract_certification` static method**

Add after the existing `_format_coursework` staticmethod (around line 119):

```python
    @staticmethod
    def _extract_certification(edu: dict) -> dict:
        cert = edu.get('certification', '')
        if isinstance(cert, dict):
            return {
                'certification_name': cert.get('name', ''),
                'certification_date': cert.get('date', ''),
                'certification_url': cert.get('url', ''),
            }
        return {
            'certification_name': cert,
            'certification_date': '',
            'certification_url': '',
        }
```

**Step 3: Run existing tests**

Run: `pytest tests/test_ai_analyzer.py -v -x`
Expected: All pass (renderer tests don't exist separately, but AI analyzer tests exercise shared data paths).

**Step 4: Commit**

```bash
git add src/resume_renderer.py
git commit -m "feat: extract structured certification fields for template"
```

---

### Task 3: Update base_template.html

**Files:**
- Modify: `templates/base_template.html:267-272` (CSS)
- Modify: `templates/base_template.html:347-351` (HTML)

**Step 1: Add link styling to the certifications CSS block**

At line 272, after `.cert-label { font-weight: bold; }`, add:

```css
.cert-verify { color: var(--primary-color); text-decoration: none; }
```

**Step 2: Replace the certification HTML block**

Replace lines 347-351:

```html
        {% if certification %}
        <div class="edu-item">
            <div class="cert-text"><span class="cert-label">Certification:</span> {{ certification }}</div>
        </div>
        {% endif %}
```

With:

```html
        {% if certification_name %}
        <div class="edu-item">
            <div class="cert-text"><span class="cert-label">Certification:</span> {{ certification_name }}{% if certification_date %} ({{ certification_date }}){% endif %}{% if certification_url %} &mdash; <a class="cert-verify" href="{{ certification_url }}">Verify</a>{% endif %}</div>
        </div>
        {% endif %}
```

**Step 3: Commit**

```bash
git add templates/base_template.html
git commit -m "feat: render certification with clickable Verify link"
```

---

### Task 4: Update ai_analyzer.py

**Files:**
- Modify: `src/ai_analyzer.py:383-390` (`_build_candidate_summary`)
- Modify: `src/ai_analyzer.py:657-660` (`_render_bio` / `_assemble_bio`)

**Step 1: Update `_build_candidate_summary` (line 383)**

Replace lines 383-390:

```python
        cert = edu.get('certification', '')

        lines = ["## Candidate Profile"]
        lines.append(f"Education: {master.get('degree', 'M.Sc.')} from {master.get('school', 'VU Amsterdam')}")
        if master.get('thesis'):
            lines.append(f"Thesis: {master['thesis']}")
        if cert:
            lines.append(f"Certification: {cert}")
```

With:

```python
        cert_raw = edu.get('certification', '')
        if isinstance(cert_raw, dict):
            cert = f"{cert_raw.get('name', '')} ({cert_raw.get('date', '')})"
        else:
            cert = cert_raw

        lines = ["## Candidate Profile"]
        lines.append(f"Education: {master.get('degree', 'M.Sc.')} from {master.get('school', 'VU Amsterdam')}")
        if master.get('thesis'):
            lines.append(f"Thesis: {master['thesis']}")
        if cert:
            lines.append(f"Certification: {cert}")
```

**Step 2: Update `_assemble_bio` certification block (line 656-660)**

Replace lines 656-660:

```python
        if include_cert:
            cert = self._parsed_bullets.get('education', {}).get('certification', 'Databricks Certified Data Engineer Professional (2026)')
            # Strip year suffix if present for cleaner bio
            cert_clean = re.sub(r'\s*\(\d{4}\)\s*$', '', cert)
            parts.append(f"{cert_clean}.")
```

With:

```python
        if include_cert:
            cert_raw = self._parsed_bullets.get('education', {}).get('certification', '')
            if isinstance(cert_raw, dict):
                cert_clean = cert_raw.get('name', 'Databricks Certified Data Engineer Professional')
            else:
                cert_clean = re.sub(r'\s*\([A-Za-z.]*\s*\d{4}\)\s*$', '', cert_raw) if cert_raw else 'Databricks Certified Data Engineer Professional'
            parts.append(f"{cert_clean}.")
```

**Step 3: Run tests**

Run: `pytest tests/test_ai_analyzer.py -v -x`
Expected: Tests that use old string format will fail — that's expected, fixed in Task 5.

**Step 4: Commit**

```bash
git add src/ai_analyzer.py
git commit -m "feat: handle structured certification dict in AI analyzer"
```

---

### Task 5: Update test fixtures

**Files:**
- Modify: `tests/test_ai_analyzer.py:306`, `tests/test_ai_analyzer.py:423`

**Step 1: Update bio test fixture (line 306)**

Replace:

```python
                "certification": "Databricks Certified Data Engineer Professional (2026)",
```

With:

```python
                "certification": {
                    "name": "Databricks Certified Data Engineer Professional",
                    "date": "Apr. 2026",
                    "url": "https://credentials.databricks.com/bac509e4-83a6-4985-8b61-90786d2013f6",
                },
```

**Step 2: Update candidate summary test fixture (line 423)**

Replace:

```python
                'certification': 'Databricks Certified Data Engineer Professional (2026)',
```

With:

```python
                'certification': {
                    'name': 'Databricks Certified Data Engineer Professional',
                    'date': 'Apr. 2026',
                    'url': 'https://credentials.databricks.com/bac509e4-83a6-4985-8b61-90786d2013f6',
                },
```

**Step 3: Run all tests**

Run: `pytest tests/test_ai_analyzer.py -v`
Expected: All pass.

**Step 4: Commit**

```bash
git add tests/test_ai_analyzer.py
git commit -m "test: update certification fixtures to structured dict format"
```

---

### Task 6: Verify end-to-end

**Step 1: Generate a test resume to verify the Verify link renders**

Pick any job with `ai_score >= 5.0` that has a tailored resume:

```bash
python scripts/job_pipeline.py --stats
```

Then generate for one job to check the PDF output visually.

**Step 2: Open the generated PDF and confirm:**
- Certification line reads: "Certification: Databricks Certified Data Engineer Professional (Apr. 2026) — Verify"
- "Verify" is a clickable link pointing to `https://credentials.databricks.com/bac509e4-83a6-4985-8b61-90786d2013f6`
