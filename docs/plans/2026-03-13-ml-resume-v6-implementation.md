# ML Resume V6 — Positioning Tighten Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Apply 8 section-level changes to the ML resume SVG, tightening positioning around "production decisioning ML engineer" as the single axis.

**Architecture:** Copy v5 SVG → apply edits section-by-section → validate XML after each task → generate preview at end. All edits are SVG text content changes; no layout system or styling changes.

**Tech Stack:** SVG (hand-edited text nodes), PowerShell/Python for XML validation, `scripts/generate_svg_preview.py` for visual check

---

### Task 1: Create v6 base file

**Files:**
- Source: `templates/Fei_Huang_ML_Resume_v5.svg`
- Create: `templates/Fei_Huang_ML_Resume_v6.svg`

- [ ] **Step 1: Copy v5 to v6**

```bash
cp templates/Fei_Huang_ML_Resume_v5.svg templates/Fei_Huang_ML_Resume_v6.svg
```

- [ ] **Step 2: Update the aria-label version tag**

Change `aria-label="Fei Huang Machine Learning Engineer resume v5 for general ML roles"` → `...v6...`

- [ ] **Step 3: Validate XML**

```bash
python -c "import xml.etree.ElementTree as ET; ET.parse('templates/Fei_Huang_ML_Resume_v6.svg'); print('XML valid')"
```

Expected: `XML valid`

---

### Task 2: Tighten BIO (3 lines → 2 lines)

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (text elements id="text8" through id="text10a")

- [ ] **Step 1: Replace Bio text content**

Find these 4 text elements (ids text8, text9, text10, text10a) and replace with:

| id | old content | new content |
|----|------------|-------------|
| text8 | `<tspan style="font-weight:bold">ML Engineer</tspan> with production experience in credit risk systems and` | `<tspan style="font-weight:bold">ML Engineer</tspan> with production credit risk and decisioning systems experience.` |
| text9 | `quantitative research; M.Sc. in AI (VU Amsterdam).` | `M.Sc. in AI (VU Amsterdam); quantitative research background in finance.` |
| text10 | `Thesis on uncertainty quantification in Deep RL.` | (empty — remove text content, keep element for spacing) |
| text10a | (empty) | (keep empty) |

- [ ] **Step 2: Validate XML**

```bash
python -c "import xml.etree.ElementTree as ET; ET.parse('templates/Fei_Huang_ML_Resume_v6.svg'); print('XML valid')"
```

---

### Task 3: Fix BQ duplication bug

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (text elements around id="text40", "text41")

- [ ] **Step 1: Fix the duplicated phrase**

Current lines (ids text40, text41):
```
including Fama-MacBeth; factors informed live portfolio
informed live portfolio construction and investment decisions.
```

Replace with:
```
including Fama-MacBeth; validated factors informed live
portfolio construction and investment decisions.
```

Note: `text40` gets `including Fama-MacBeth; validated factors informed live` and `text41` gets `portfolio construction and investment decisions.`

- [ ] **Step 2: Validate XML**

---

### Task 4: Add light contextual frame to Independent period

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (text elements id="text42e", "text42f", "text42g")

- [ ] **Step 1: Rewrite the Independent bullet**

Replace 3-line bullet with contextual frame prepended:

| id | new content |
|----|-------------|
| text42e | `Conducted independent research ahead of returning to graduate study.` |
| text42f | `Built automated equity research pipeline processing 83K+ daily records` |
| text42g | `across 3,600+ stocks; implemented flow tracking and signal detection.` |

- [ ] **Step 2: Validate XML**

---

### Task 5: Expand Ele.me to 2 bullets

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (text elements id="text47" through id="text57")

This is the most complex edit. We need to fit 2 bullets + Skills line into the space currently used by 1 bullet + Skills line. The Ele.me section runs from y=645.5 to y=711.5.

- [ ] **Step 1: Replace Ele.me body text**

Rewrite text elements for Ele.me body area. Use the existing element ids and y-coordinates:

| id | y | new content |
|----|---|-------------|
| text47 | 669.5 | `Built anti-fraud detection system identifying <tspan style="font-weight:bold">51,000+</tspan>` |
| text48 | 682.5 | `suspicious order clusters across <tspan style="font-weight:bold">2.2M+ users</tspan> using 3 pattern` |
| text49 | 695.5 | `algorithms, preventing fraudulent subsidy claims during hyper-growth.` |
| text57 | 711.5 | `Optimized <tspan style="font-weight:bold">90+ Hadoop/Hive queries</tspan> via partition pruning and` |

We need additional text elements for the second bullet continuation and Skills line. Add new elements after text57:

| new id | y | content |
|--------|---|---------|
| text57b | 724.5 | `subquery pushdown, cutting scan volume <tspan style="font-weight:bold">5x</tspan> (500GB → 100GB).` |
| text57c | 740.5 | `<tspan class="body-bold">Skills:</tspan> Python, SQL, Hadoop, Hive` |

Note: This pushes the Ele.me section ~29pt taller. We'll need to verify this doesn't overflow the page (842pt). Current Ele.me Skills line ends at y=711.5; new ending at y=740.5. Still well within page bounds since the left column ends here.

- [ ] **Step 2: Validate XML**

---

### Task 6: Add Certifications section in right column

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (add new text elements after Languages section)

- [ ] **Step 1: Add CERTIFICATIONS header and content**

Current Languages section ends at y=747. Add after it:

| new id | class | y | content |
|--------|-------|---|---------|
| text96 | section | 771 | `CERTIFICATIONS` |
| text97 | body | 786 | `<tspan class="body-bold">Databricks</tspan> Certified Data Engineer Professional` |
| text98 | date | 799 | `FEBRUARY 2026` |

All at x=326 (right column).

- [ ] **Step 2: Validate XML**

---

### Task 7: Compress ML4QS project

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (text elements id="text80" through "text86")

- [ ] **Step 1: Replace ML4QS body text**

| id | y | new content |
|----|---|-------------|
| text80 | 507 | `Built end-to-end sensor ML pipeline: Kalman filtering,` |
| text81 | 520 | `FFT-based feature extraction (<tspan style="font-weight:bold">576+ features</tspan>),` |
| text82 | 533 | `LightGBM and bidirectional LSTM for multi-class IMU` |
| text83 | 546 | `classification.` |
| text84 | 559 | (empty — clear content) |
| text85 | 572 | (empty — clear content) |
| text86 | 585 | `<tspan class="body-bold">Skills:</tspan> PyTorch, LightGBM, Optuna, Signal Processing` |

- [ ] **Step 2: Validate XML**

---

### Task 8: Tighten Technical Skills

**Files:**
- Modify: `templates/Fei_Huang_ML_Resume_v6.svg` (text elements id="text88" through "text92")

- [ ] **Step 1: Replace skills content**

| id | y | new content |
|----|---|-------------|
| text88 | 629.5 | `<tspan class="body-bold">ML &amp; Evaluation:</tspan> PyTorch, scikit-learn, LightGBM,` |
| text89 | 642.5 | `Learning to Rank` |
| text90 | 658.5 | `<tspan class="body-bold">Programming:</tspan> Python, SQL, pandas, NumPy` |
| text91 | 674.5 | `<tspan class="body-bold">Data Systems:</tspan> PySpark, Airflow, Redshift, Databricks,` |
| text91a | 687.5 | `Hadoop, Hive` |
| text92 | 703.5 | `<tspan class="body-bold">Infrastructure:</tspan> AWS` |

Removed: MATLAB, Docker, Git, Statistical Testing, ETL/ELT

- [ ] **Step 2: Validate XML**

---

### Task 9: Final verification

**Files:**
- Verify: `templates/Fei_Huang_ML_Resume_v6.svg`

- [ ] **Step 1: Full XML validation**

```bash
python -c "import xml.etree.ElementTree as ET; ET.parse('templates/Fei_Huang_ML_Resume_v6.svg'); print('XML valid')"
```

- [ ] **Step 2: Generate PNG preview**

```bash
python scripts/generate_svg_preview.py templates/Fei_Huang_ML_Resume_v6.svg
```

- [ ] **Step 3: Review the diff**

```bash
git diff --no-index templates/Fei_Huang_ML_Resume_v5.svg templates/Fei_Huang_ML_Resume_v6.svg
```

- [ ] **Step 4: Visual check — verify no overflow, spacing looks right**

Open the generated preview image and verify:
- Left column: all 4 experience sections fit without overflow
- Right column: Education + Projects + Skills + Languages + Certifications fit
- No text overlaps or cut-off lines
