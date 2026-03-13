# DE Resume Toni v20 Final Polish Links Skills Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve link recognizability in the header and correct `AWS` categorization in the final resume SVG.

**Architecture:** Make two constrained edits in the existing SVG only. Promote `LinkedIn | GitHub` to the same visual weight as other contact items without introducing new colors or decoration, then move `AWS` from `Tools` to `Technologies` and rebalance the skills lines to preserve clean wrapping.

**Tech Stack:** SVG text layout, `scripts/svg_to_pdf.py`, Playwright PDF export, PyMuPDF image rendering

---

## Chunk 1: Final Polish

### Task 1: Strengthen header link visibility

**Files:**
- Modify: `C:\Users\huang\github\job-hunter\templates\de_resume_toni_v20.svg`

- [ ] Change the header links from `contact` styling to a stronger treatment consistent with the existing contact block.
- [ ] Preserve the current click overlays and spacing.

### Task 2: Reclassify AWS

**Files:**
- Modify: `C:\Users\huang\github\job-hunter\templates\de_resume_toni_v20.svg`

- [ ] Move `AWS` from `Tools` to `Technologies`.
- [ ] Rebalance wrapped lines in the skills block if needed.

## Chunk 2: Verification

### Task 3: Export and inspect

**Files:**
- Output: `C:\Users\huang\github\job-hunter\output\Fei_Huang_DE_toni_v20_review.pdf`
- Output: `C:\Users\huang\github\job-hunter\output\de_resume_toni_v20_review_page1_final5.png`

- [ ] Run `python scripts\\svg_to_pdf.py templates\\de_resume_toni_v20.svg output\\Fei_Huang_DE_toni_v20_review.pdf`
- [ ] Rasterize page 1 and verify the updated header and skills block visually.

Plan complete and saved to `docs/superpowers/plans/2026-03-12-de-resume-toni-v20-final-polish-links-skills.md`. Ready to execute?
