# ML Resume V4 General Polish Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a stronger general-purpose ML Engineer resume by refining the selected base SVG without adding unsupported claims or changing the overall layout system.

**Architecture:** Start from `templates/Fei_Huang_ML_Resume.svg` as the approved base. Keep the existing two-column structure, then tighten the bio, compress weaker legacy phrasing, and prioritize projects and skills that reinforce production ML, ranking, and evaluation rigor. Apply a second pass focused on sentence quality, using a senior, restrained, hiring-manager-friendly tone across every section.

**Tech Stack:** SVG, resume content editing, PowerShell verification

---

### Task 1: Create the v4 SVG

**Files:**
- Create: `templates/Fei_Huang_ML_Resume_v4.svg`
- Modify: `templates/Fei_Huang_ML_Resume.svg`

- [ ] **Step 1: Copy the approved base content into a new v4 file**
- [ ] **Step 2: Tighten the bio for general ML Engineer positioning**
- [ ] **Step 3: Preserve GLP as the main production ML proof point while compressing lower-signal phrasing**
- [ ] **Step 4: Keep only the highest-signal projects and reorder skills toward ML-first ATS readability**

### Task 2: Refine language quality section by section

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v4.svg`

- [ ] **Step 1: Rewrite the bio to be tighter and more executive-readable**
- [ ] **Step 2: Rewrite each experience block so the language consistently follows scope, action, and outcome**
- [ ] **Step 3: Rewrite education and project copy to emphasize method and evaluation rather than coursework tone**
- [ ] **Step 4: Rewrite skills labels and ordering to read as a mature ML profile rather than a keyword list**

### Task 3: Verify the output

**Files:**
- Verify: `templates/Fei_Huang_ML_Resume_v4.svg`

- [ ] **Step 1: Parse the SVG as XML to catch malformed markup**
- [ ] **Step 2: Review the diff against the base SVG**
- [ ] **Step 3: Report the final content changes and any residual layout risk**
