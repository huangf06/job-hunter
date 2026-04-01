# Zone-Based Resume Templates

**Date:** 2026-04-02
**Status:** Approved
**Scope:** Replace `base_template_DE.html` and `base_template_ML.html` with zone-based hybrid templates

## Problem

The current ADAPT_TEMPLATE rendering path uses Jinja2 flow-layout templates (`base_template_DE.html`, `base_template_ML.html`) that produce visually imprecise PDFs compared to the hand-tuned SVG masters. Meanwhile, the new pixel-perfect HTML replicas (`Fei_Huang_DE_Resume.html`, `Fei_Huang_ML_Resume.html`) are fully static and cannot accept dynamic content.

## Goal

Combine pixel-perfect positioning with limited dynamic slots: most content stays hardcoded and visually identical to the SVG, while bio, skills lines, and technical skills sections accept Jinja2 variables for per-job adaptation.

## Design: Zone-Based Hybrid Layout

### Layout model

The page is divided into **zones**. Each zone is `position: absolute` with a fixed `left`/`top`.

- **Fixed zones**: retain per-line `<div>` positioning from the static HTML replica. Content is hardcoded.
- **Variable zones**: the zone container is absolutely positioned, but content inside flows naturally via CSS `line-height`. Jinja2 variables inject dynamic content. `max-height` + `overflow: hidden` prevents spillover.

### Variable zones (3 per template)

| Zone | Template variable | Constraint |
|------|-------------------|------------|
| Bio | `{{ bio }}` | Max ~3 lines at 10pt/12pt line-height within 512pt width |
| Experience skills lines | `{{ glp_skills }}`, `{{ bq_skills }}`, `{{ ele_skills }}` (+ `{{ henan_skills }}` for DE) | Single line each, ~60 chars max |
| Technical Skills section | `{% for skill in skills %}` loop | 4-5 categories, total height capped |

### Fixed zones (everything else)

Header, experience org/date/bullets, education, certifications, projects, languages -- all hardcoded text with exact per-line `top` values matching the SVG.

### Zone map (DE template)

```
top:24pt      Header Zone (fixed) - name, contact
top:77.3pt    Bio Zone (VARIABLE) - section title + flowing text
top:137.3pt   Experience section title (fixed)
top:150.4pt   GLP entry (fixed lines) ... top:339.5pt GLP skills (VARIABLE single line)
top:363.4pt   BQ entry (fixed lines) ... top:484.6pt BQ skills (VARIABLE single line)
top:508.5pt   Ele entry (fixed lines) ... top:630.6pt Ele skills (VARIABLE single line)
top:654.5pt   Henan entry (fixed lines)
              --- right column ---
top:151.3pt   Education zone (fixed)
top:308.9pt   Certifications zone (fixed)
top:349.4pt   Recent Project zone (fixed)
top:526.4pt   Technical Skills zone (VARIABLE) - flowing categories
top:667pt     Languages zone (fixed)
```

### Zone map (ML template)

```
top:24pt      Header Zone (fixed)
top:77.3pt    Bio Zone (VARIABLE)
top:149.3pt   Experience section title (fixed)
top:162.4pt   GLP entry (fixed) ... top:337.4pt GLP skills (VARIABLE single line)
top:372.4pt   BQ entry (fixed) ... top:508.4pt BQ skills (VARIABLE single line)
top:530.4pt   Ele entry (fixed) ... top:624.4pt Ele skills (VARIABLE single line)
top:652.8pt   Technical Skills zone (VARIABLE) - left column
              --- right column ---
top:149.3pt   Education zone (fixed)
top:290.8pt   Certifications zone (fixed)
top:342.8pt   Projects zone (fixed - 3 projects)
top:758.8pt   Languages zone (fixed)
```

## Pipeline integration

### What changes

1. **New templates** replace `base_template_DE.html` and `base_template_ML.html`
2. **`_schema_to_context()`** simplified: only outputs bio, skills list, and per-entry skills strings (not full experiences/projects structure)
3. **`_render_adapt_template()`** unchanged in flow, just renders the new templates
4. **Validator** adds character-count checks for variable zones

### What stays the same

- `USE_TEMPLATE` path (copy PDF) -- untouched
- `FULL_CUSTOMIZE` path (old `base_template.html`) -- untouched as fallback
- Template registry YAML structure -- untouched
- C1/C2/C3 AI analysis flow -- untouched
- Database schema -- untouched

### Context variables (new, simplified)

```python
{
    # Variable zones
    'bio': str,                    # Bio text (HTML allowed for <strong>)
    'glp_skills': str,             # "Python, SQL, AWS, Redshift, Airflow, Docker"
    'bq_skills': str,
    'ele_skills': str,
    'henan_skills': str,           # DE only
    'skills': [                    # Technical skills categories
        {'category': 'Programming', 'skills_list': 'Python, SQL, Bash'},
        ...
    ],
}
```

### Overflow protection

- Bio zone: `max-height: 38pt` (~3 lines at 12pt line-height + margin)
- Skills zone: `max-height` set to match available vertical space before Languages
- Experience skills lines: single `<div>` with `white-space: nowrap; overflow: hidden; text-overflow: ellipsis`
- Validator rejects if bio > 250 chars or skills line > 65 chars

## Risk assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Variable zone overflow | Medium | max-height clip + validator char limits |
| Line-height mismatch vs SVG | Low | Same font/size/line-height; <0.5pt diff |
| Skills category count changes | Low | AI prompt constrains to 4-5 categories |
| Jinja2 autoescape breaks `<strong>` in bio | Medium | Use `{{ bio \| safe }}` or `Markup()` |
