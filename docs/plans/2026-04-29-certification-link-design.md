# Certification Verify Link on Resume

**Date:** 2026-04-29
**Status:** Approved

## Goal

Add a clickable "Verify" hyperlink next to the Databricks certification on the resume PDF. Update certification date from "2026" to "Apr. 2026".

Credential URL: `https://credentials.databricks.com/bac509e4-83a6-4985-8b61-90786d2013f6`

## Design

### Rendered output

```
Certification: Databricks Certified Data Engineer Professional (Apr. 2026) — Verify
                                                                             ^^^^^^
                                                                         clickable link
```

### Changes

**1. `assets/bullet_library.yaml` — data layer**

```yaml
# Before
certification: "Databricks Certified Data Engineer Professional (2026)"

# After
certification:
  name: "Databricks Certified Data Engineer Professional"
  date: "Apr. 2026"
  url: "https://credentials.databricks.com/bac509e4-83a6-4985-8b61-90786d2013f6"
```

Also update `skills.technical.certifications` list: `"(2026)"` -> `"(Apr. 2026)"`.

**2. `templates/base_template.html` — template layer**

Replace the single `{{ certification }}` with structured fields:

```html
{% if certification_name %}
<div class="cert-text">
  <span class="cert-label">Certification:</span> {{ certification_name }} ({{ certification_date }})
  {% if certification_url %} — <a href="{{ certification_url }}">Verify</a>{% endif %}
</div>
{% endif %}
```

Add minimal link styling (inherit color, no underline clutter in PDF).

**3. `src/resume_renderer.py` — renderer**

Update `_build_base_context()` to extract structured certification:

```python
cert = edu.get('certification', '')
if isinstance(cert, dict):
    context['certification_name'] = cert.get('name', '')
    context['certification_date'] = cert.get('date', '')
    context['certification_url'] = cert.get('url', '')
else:
    # backward compat: plain string
    context['certification_name'] = cert
    context['certification_date'] = ''
    context['certification_url'] = ''
```

Remove the old `'certification': edu.get('certification', '')` line.

**4. `src/ai_analyzer.py` — AI profile + bio generation**

Two call sites read `education.certification`:

- `_generate_candidate_summary()` (line ~383): builds candidate profile for C2 prompt
- `_render_bio()` (line ~653-660): builds bio text, strips year suffix

Both need to handle the new dict format:

```python
cert_raw = edu.get('certification', '')
if isinstance(cert_raw, dict):
    cert = f"{cert_raw.get('name', '')} ({cert_raw.get('date', '')})"
else:
    cert = cert_raw
```

The bio renderer's year-stripping regex (`\s*\(\d{4}\)\s*$`) needs updating to also strip month+year: `\s*\([A-Z][a-z]+\.?\s*\d{4}\)\s*$`.

**5. `tests/test_ai_analyzer.py` — test fixtures**

Update certification strings in test data to use the new dict format.

### Files NOT changed

- `assets/bullet_library_versions/*.yaml` — historical snapshots, never modified
- `assets/cl_knowledge_base.yaml` — references "certification" in prose, not as structured data
- `templates/resume_master.html` — static reference resume, not generated

### Risk

Low. The backward-compatible `isinstance(cert, dict)` check means old string-format data still works. The only visible change is the "Verify" link text appearing on newly generated PDFs.
