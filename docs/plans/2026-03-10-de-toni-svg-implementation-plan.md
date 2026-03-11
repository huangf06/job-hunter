# DE Toni SVG Resume Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Toni-style Data Engineer SVG resume that uses the approved DE content baseline and supports experience continuation from the left column into the right column.

**Architecture:** Copy the Toni SVG as the visual reference, then replace all content blocks with Fei Huang's DE content while preserving the original typographic system and section rhythm. Handle overflow by moving the final experience block to the top of the right column before projects and skills.

**Tech Stack:** Static SVG editing, XML validation, optional Playwright PDF rendering

---

### Task 1: Create the DE Toni SVG file

**Files:**
- Create: `templates/de_resume_toni_v1.svg`
- Reference: `templates/toni_copy.svg`
- Reference: `docs/plans/2026-03-10-de-resume-content-spec.md`

- [ ] Replace Toni's personal information with Fei Huang's contact block
- [ ] Replace the bio with the canonical DE bio in compressed Toni-style lines
- [ ] Replace the education section with VU Amsterdam and Tsinghua entries
- [ ] Replace experience entries with GLP, Baiquan, Ele.me, and Henan
- [ ] Continue the final experience entry in the top of the right column
- [ ] Add selected projects, technical skills, certification, and languages

### Task 2: Validate the SVG

**Files:**
- Validate: `templates/de_resume_toni_v1.svg`

- [ ] Parse the SVG as XML to catch syntax errors
- [ ] Render or convert locally if possible to confirm the file is usable
- [ ] Check that the source file `templates/toni_copy.svg` remains unchanged
