# Resume Template Unification Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix resume rendering quality by aligning templates to their intended routing tiers.

**Architecture:** Three routing tiers, each with the right template:
- Route 1 (USE_TEMPLATE): PDF copy (unchanged)
- Route 2 (ADAPT_TEMPLATE): Per-template pixel-perfect HTML (DE/ML), slot overrides for micro-adjustments
- Route 3 (FULL_CUSTOMIZE): Single-column layout, no left-right balance risk

**Tech Stack:** Jinja2, CSS Grid, Playwright PDF

---

## SVG-Extracted Layout Parameters (shared by DE and ML)

```
Page: 595pt x 842pt (A4)
Margins: 42pt all sides (body padding in screen, Playwright margin in print)
Content area: 511pt wide

Left column:  x=42, width=268pt
Right column: x=326, width=227pt
Gap: 16pt
Check: 268 + 16 + 227 = 511 ✓

Name: Georgia 34px bold #1f1b1b (at y=55)
Contact: Arial 10px #2f2f2f (at x=326, y=34-70)
Section: Arial 8px bold #33455a, letter-spacing 0.4px
Body: Arial 10px #4f4f4f, line-height ~13pt
Date: Arial 8px #6a6a6a, letter-spacing 0.2px
Org: Georgia 10px bold #211b1b
Role: Georgia 10px italic #4a4040

Bullet paragraph gap: ~16pt
Skill line after bullets: ~16pt gap
Section gap: ~24pt
```

## Column Structure Difference

| Column | DE Template | ML Template |
|--------|------------|-------------|
| Left   | Experience (4 companies) | Experience (3 companies) + Technical Skills |
| Right  | Education + Cert + Project(s) + Technical Skills + Languages | Education + Cert + Projects (3) + Languages |

---

### Task 1: Create base_template_DE.html

**Files:**
- Create: `templates/base_template_DE.html`

Pixel-perfect HTML reproduction of DE SVG. Two-column CSS Grid with fixed pt widths.
Jinja2 slots for all dynamic content (bio, experiences, projects, skills, education, etc.)
Uses same variable names as current base_template.html for compatibility.

Left column: Experience + career_note
Right column: Education + Certification + Projects + Technical Skills + Languages

### Task 2: Create base_template_ML.html

**Files:**
- Create: `templates/base_template_ML.html`

Same CSS/typography as DE, but different column structure:
Left column: Experience + Technical Skills
Right column: Education + Certification + Projects + Languages

### Task 3: Convert base_template.html to single-column

**Files:**
- Modify: `templates/base_template.html`

Remove CSS Grid two-column layout. Convert to single-column stacked sections.
Reference: resume_master.html style (centered header, horizontal rules, bullet lists).
This template serves FULL_CUSTOMIZE where content volume is unpredictable.

### Task 4: Add _schema_to_context() to renderer

**Files:**
- Modify: `src/resume_renderer.py`

New method converts slot_schema + overrides into the same context dict that Jinja2 templates expect.
Maps schema entries to experiences/projects/skills lists.
Respects entry_visibility, slot_overrides, skills_override.

### Task 5: Update _render_adapt_template() routing

**Files:**
- Modify: `src/resume_renderer.py`

Change ADAPT path to:
1. Determine template_id (DE or ML)
2. Select `base_template_DE.html` or `base_template_ML.html`
3. Call `_schema_to_context()` to build context
4. Render with base_template + Playwright PDF

### Task 6: Update tests

**Files:**
- Modify: `tests/test_resume_renderer.py` (or relevant test files)

Verify ADAPT routing selects correct template per template_id.
Verify _schema_to_context produces valid context.
Verify single-column FULL_CUSTOMIZE still renders.

### Task 7: Re-render ADAPT_TEMPLATE jobs

Re-run renderer for the 4 ADAPT_TEMPLATE jobs to verify output quality.
