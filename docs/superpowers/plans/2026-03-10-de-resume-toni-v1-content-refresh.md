# DE Resume Toni v1 Content Refresh Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refresh `templates/de_resume_toni_v1.svg` with the approved standard Data Engineer master content while preserving the current two-column Toni layout.

**Architecture:** Keep the existing SVG structure, typography, and section order. Replace text blocks with the approved DE-focused copy, adjust only the specific line breaks and `y` positions needed to fit the content cleanly, then render a local preview/PDF for visual verification.

**Tech Stack:** SVG, PowerShell, existing local preview/PDF scripts

---

## Chunk 1: SVG Content Update

### Task 1: Update approved resume copy in the existing SVG

**Files:**
- Modify: `templates/de_resume_toni_v1.svg`

- [ ] Replace the Bio copy with the approved DE master bio.
- [ ] Reorder GLP bullets to emphasize DE identity before analytical depth.
- [ ] Rewrite BQ and thesis text to be more DE-oriented and less quant/ML-forward.
- [ ] Narrow the skills section to the standard DE master categories and items.
- [ ] Keep layout changes minimal and limited to local line-break / coordinate tuning.

## Chunk 2: Visual Verification

### Task 2: Render and inspect output

**Files:**
- Verify: `templates/de_resume_toni_v1.svg`
- Generate: local preview or PDF derived from the SVG

- [ ] Run the existing preview/PDF script if available.
- [ ] Check for obvious overflow, clipping, or spacing regressions.
- [ ] Make one more SVG adjustment pass if the rendered output shows layout issues.
