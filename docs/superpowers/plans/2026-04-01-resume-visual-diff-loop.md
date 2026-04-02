# Resume Visual Diff Loop Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a repeatable HTML -> PDF -> PNG -> diff pipeline that compares the editable HTML resume against the canonical PDF and emits artifacts plus metrics for iterative layout tuning.

**Architecture:** Add a focused Python utility module for rendering and comparison primitives, then expose it through a small CLI script. The pipeline will render the candidate HTML to PDF with Playwright, rasterize both reference and candidate PDFs to PNG, compute an absolute-difference image plus summary metrics, and write all artifacts to a deterministic output directory.

**Tech Stack:** Python 3.12, Playwright, subprocess-based local raster tool invocation, pytest, pathlib, json

---

## Chunk 1: Test The Comparison Primitives

### Task 1: Add red tests for tool resolution and artifact planning

**Files:**
- Create: `tests/test_resume_visual_diff.py`
- Modify: `src/` new module to satisfy tests later

- [ ] **Step 1: Write the failing test**

Add tests for:
- selecting an available raster backend from explicit command candidates
- rejecting missing backends with a clear error
- producing deterministic artifact paths from reference PDF and candidate HTML inputs

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_resume_visual_diff.py -q`
Expected: FAIL because module/functions do not exist yet

### Task 2: Add red tests for metric parsing and diff summary

**Files:**
- Create: `tests/test_resume_visual_diff.py`

- [ ] **Step 1: Write the failing test**

Add tests for:
- parsing image comparison output into numeric metrics
- computing a summary payload with dimensions, mean error, normalized score, and artifact paths

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_resume_visual_diff.py -q`
Expected: FAIL on missing implementation

## Chunk 2: Implement The Utility Module

### Task 3: Implement minimal render/diff helpers

**Files:**
- Create: `src/resume_visual_diff.py`

- [ ] **Step 1: Write minimal implementation**

Implement:
- backend/tool detection
- artifact path planning
- PDF raster command construction
- image diff summary parsing

- [ ] **Step 2: Run targeted tests**

Run: `pytest tests/test_resume_visual_diff.py -q`
Expected: PASS for pure utility tests

## Chunk 3: Expose CLI And Integrate Rendering

### Task 4: Add CLI entrypoint for full pipeline

**Files:**
- Create: `scripts/resume_visual_diff.py`
- Modify: `src/resume_renderer.py` only if a small reusable HTML->PDF helper extraction is needed

- [ ] **Step 1: Write the failing CLI/integration test**

Add a test that stubs subprocess calls and validates:
- reference PDF rasterization is invoked
- candidate HTML is printed to PDF first
- diff PNG and JSON summary paths are produced

- [ ] **Step 2: Run the focused test to verify it fails**

Run: `pytest tests/test_resume_visual_diff.py -q`
Expected: FAIL on missing CLI/integration behavior

- [ ] **Step 3: Implement the minimal CLI**

Support arguments:
- `--reference-pdf`
- `--candidate-html`
- `--output-dir`
- `--dpi`

- [ ] **Step 4: Re-run tests**

Run: `pytest tests/test_resume_visual_diff.py -q`
Expected: PASS

## Chunk 4: Verify With Real Files

### Task 5: Run end-to-end on the DE resume

**Files:**
- Use: `templates/pdf/Fei_Huang_DE.pdf`
- Use: `templates/Fei_Huang_DE_Resume.html`
- Output: `output/visual_diff/` or similarly scoped artifact directory

- [ ] **Step 1: Execute the real pipeline**

Run: `python scripts/resume_visual_diff.py --reference-pdf templates/pdf/Fei_Huang_DE.pdf --candidate-html templates/Fei_Huang_DE_Resume.html --output-dir output/visual_diff/de_resume --dpi 144`

Expected:
- candidate PDF exists
- reference PNG exists
- candidate PNG exists
- diff PNG exists
- summary JSON exists

- [ ] **Step 2: Inspect metrics and identify worst visual regions**

Record the first-pass score and note the main mismatches for the next HTML tuning cycle.

