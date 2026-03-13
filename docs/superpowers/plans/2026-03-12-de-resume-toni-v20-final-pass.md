# DE Resume Toni v20 Final Pass Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tighten `de_resume_toni_v20.svg` into a stronger final-send Data Engineer resume without changing the underlying career narrative.

**Architecture:** Work directly in the SVG template and change only the parts that materially affect scan speed and credibility: header, bio, selected project wording, and small right-column layout adjustments. Validate using rendered output rather than trusting SVG source coordinates.

**Tech Stack:** SVG text layout, `scripts/svg_to_pdf.py`, Playwright PDF export, PyMuPDF image rendering

---

## Chunk 1: Content Tightening

### Task 1: Strengthen first-scan positioning

**Files:**
- Modify: `C:\Users\huang\github\job-hunter\templates\de_resume_toni_v20.svg`

- [ ] Add an explicit `Data Engineer` title in the header.
- [ ] Replace the current bio with a shorter positioning statement that combines senior platform experience with recent skill refresh.
- [ ] Keep all claims within the bounds of existing evidence on the page.

### Task 2: Tighten recent-project wording

**Files:**
- Modify: `C:\Users\huang\github\job-hunter\templates\de_resume_toni_v20.svg`

- [ ] Rewrite the greenhouse project bullets to emphasize completed work and production-minded design choices.
- [ ] Remove or reduce speculative phrasing that weakens credibility.
- [ ] Adjust line breaks only where needed to preserve layout quality.

### Task 3: Apply minimal right-column cleanup

**Files:**
- Modify: `C:\Users\huang\github\job-hunter\templates\de_resume_toni_v20.svg`

- [ ] Reorder or tighten skills text only if it improves DE signal.
- [ ] Make small `y` position updates if the revised copy changes section rhythm.

## Chunk 2: Render Verification

### Task 4: Export the revised PDF

**Files:**
- Read: `C:\Users\huang\github\job-hunter\scripts\svg_to_pdf.py`
- Output: `C:\Users\huang\github\job-hunter\output\Fei_Huang_DE_toni_v20_review.pdf`

- [ ] Run `python scripts\\svg_to_pdf.py templates\\de_resume_toni_v20.svg output\\Fei_Huang_DE_toni_v20_review.pdf`
- [ ] Confirm the PDF is generated successfully.

### Task 5: Review the rendered page

**Files:**
- Read: `C:\Users\huang\github\job-hunter\output\Fei_Huang_DE_toni_v20_review.pdf`
- Output: `C:\Users\huang\github\job-hunter\output\de_resume_toni_v20_review_page1.png`

- [ ] Rasterize page 1 for inspection.
- [ ] Check top-of-page positioning, right-column rhythm, and bottom-page clearance.
- [ ] If needed, make one final SVG adjustment and re-render.

Plan complete and saved to `docs/superpowers/plans/2026-03-12-de-resume-toni-v20-final-pass.md`. Ready to execute?
