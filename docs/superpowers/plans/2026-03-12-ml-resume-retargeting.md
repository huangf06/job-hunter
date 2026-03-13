# ML Resume Retargeting Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the ML resume SVG so it targets standard ML Engineer roles more credibly and effectively.

**Architecture:** Make content-only edits in the existing SVG text nodes. Keep the current layout intact while changing the summary, selected bullets, and skill wording to better match the chosen narrative.

**Tech Stack:** SVG text content, manual patching, shell verification

---

## Chunk 1: Resume Content Rewrite

### Task 1: Update narrative-critical text in the SVG

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume.svg`

- [ ] Step 1: Rewrite the bio to emphasize ML engineering focused on decision systems, evaluation, and scalable data foundations.
- [ ] Step 2: Rewrite GLP bullets to clarify production decisioning, risk modeling, and supporting pipelines.
- [ ] Step 3: Tighten BQ and Ele.me wording so they support the ML story without overstating.
- [ ] Step 4: Adjust technical skills to reduce unsupported stack inflation while preserving ATS usefulness.
- [ ] Step 5: Verify the updated SVG text with targeted searches.
