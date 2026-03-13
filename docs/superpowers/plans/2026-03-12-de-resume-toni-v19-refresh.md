# DE Resume Toni v19 Refresh Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create `templates/de_resume_toni_v19.svg` as a refined mid-market Data Engineer resume variant with sharper positioning and a single high-credibility project.

**Architecture:** Copy the current `v18` SVG into a new `v19` file, then update only the text nodes and right-column vertical layout needed for the approved narrative changes. Preserve the established visual system and avoid broad structural edits.

**Tech Stack:** SVG, PowerShell file operations, manual patch editing

---

## Chunk 1: Content refresh and file creation

### Task 1: Create the v19 working file

**Files:**
- Create: `templates/de_resume_toni_v19.svg`
- Modify: `templates/de_resume_toni_v18.svg`

- [ ] **Step 1: Copy the current SVG into a new versioned file**

Run: `Copy-Item templates\de_resume_toni_v18.svg templates\de_resume_toni_v19.svg`

- [ ] **Step 2: Confirm the new file exists**

Run: `Get-Item templates\de_resume_toni_v19.svg`
Expected: file metadata is returned

### Task 2: Refresh the approved content

**Files:**
- Modify: `templates/de_resume_toni_v19.svg`

- [ ] **Step 1: Update the bio copy**
- [ ] **Step 2: Rewrite the GLP opening bullet**
- [ ] **Step 3: Reframe the BQ bullets around trading and research value**
- [ ] **Step 4: Replace `PROJECTS` with a single `SELECTED PROJECT` block for Greenhouse**
- [ ] **Step 5: Remove the Financial Data Lakehouse block**
- [ ] **Step 6: Simplify the skills section and move right-column blocks upward**

### Task 3: Verify the edited SVG

**Files:**
- Modify: `templates/de_resume_toni_v19.svg`

- [ ] **Step 1: Read back the updated text nodes**

Run: `Select-String -Path templates\de_resume_toni_v19.svg -Pattern 'SELECTED PROJECT|Greenhouse|Data Engineer with hands-on experience|Built market data pipelines|Infrastructure:'`
Expected: all updated anchors are present

- [ ] **Step 2: Confirm the removed project text is gone**

Run: `Select-String -Path templates\de_resume_toni_v19.svg -Pattern 'Financial Data Lakehouse|Auto Loader'`
Expected: no matches
