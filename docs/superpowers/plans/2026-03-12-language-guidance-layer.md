# Language Guidance Layer Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a centralized soft-guidance language policy that improves wording consistency across résumé, cover letter, and analysis generation.

**Architecture:** Store guidance in one YAML asset and load only the relevant subsection for each output type. Keep the first version advisory: use it to shape prompts and optional post-generation review, without enforcing hard validation failures.

**Tech Stack:** Python 3.11, YAML configuration, existing AI generation modules, pytest

---

## Chunk 1: Policy Asset

### Task 1: Add centralized language guidance config

**Files:**
- Create: `C:\Users\huang\github\job-hunter\assets\language_guidance.yaml`

- [ ] **Step 1: Create the YAML structure**

Add sections for:

- `global_tone`
- `content_types`
- `verb_architecture`
- `anti_patterns`

- [ ] **Step 2: Populate the initial guidance**

Include:

- résumé summary guidance
- experience bullet guidance
- project bullet guidance
- cover letter guidance
- analysis output guidance

- [ ] **Step 3: Sanity-check the file**

Run:

```bash
python -c "import yaml, pathlib; print(yaml.safe_load(pathlib.Path('assets/language_guidance.yaml').read_text(encoding='utf-8')).keys())"
```

Expected:

- Prints the top-level keys without YAML parse errors

## Chunk 2: Prompt Integration

### Task 2: Locate current generation entry points

**Files:**
- Modify: `C:\Users\huang\github\job-hunter\src\ai_analyzer.py`
- Modify: `C:\Users\huang\github\job-hunter\src\cover_letter_generator.py`
- Modify: any résumé generation module identified during implementation

- [ ] **Step 1: Find where prompts are assembled**

Run:

```bash
rg -n "prompt|system|resume|cover letter|analysis" src
```

Expected:

- Clear prompt assembly locations for each generator

- [ ] **Step 2: Add a small loader/helper**

Prefer a focused helper module such as:

- `C:\Users\huang\github\job-hunter\src\language_guidance.py`

Responsibilities:

- load `assets/language_guidance.yaml`
- expose functions like `get_language_guidance("experience_bullet")`

- [ ] **Step 3: Wire guidance into résumé-related prompts**

Inject only the relevant subset of guidance into each prompt instead of dumping the whole file.

- [ ] **Step 4: Wire guidance into cover letter prompts**

Use `cover_letter` guidance plus `global_tone`.

- [ ] **Step 5: Wire guidance into analysis prompts**

Use `analysis_output` guidance plus `global_tone`.

## Chunk 3: Tests

### Task 3: Add focused tests for loading and slicing

**Files:**
- Create: `C:\Users\huang\github\job-hunter\tests\test_language_guidance.py`

- [ ] **Step 1: Write a failing test for config loading**

Test:

- config loads successfully
- required top-level keys exist

- [ ] **Step 2: Run the test and confirm failure**

Run:

```bash
pytest tests/test_language_guidance.py -v
```

Expected:

- Fails because helper/module does not exist yet

- [ ] **Step 3: Implement minimal helper logic**

Add loader and access helpers.

- [ ] **Step 4: Add a failing test for content-type slicing**

Test:

- `get_language_guidance("experience_bullet")` returns the expected subset
- unknown type raises a clear error or falls back intentionally

- [ ] **Step 5: Run the tests and make them pass**

Run:

```bash
pytest tests/test_language_guidance.py -v
```

Expected:

- PASS

## Chunk 4: Smoke Verification

### Task 4: Verify prompt integration does not break generation

**Files:**
- Modify: same files as prompt integration

- [ ] **Step 1: Add minimal logging or inspectable output if needed**

Only if current code makes integration difficult to verify.

- [ ] **Step 2: Run targeted tests**

Run:

```bash
pytest -q
```

Expected:

- Existing tests still pass, or failures are unrelated and documented

- [ ] **Step 3: Run a lightweight manual smoke check**

Use one existing résumé generation path and one cover-letter generation path to confirm prompts still assemble correctly.

- [ ] **Step 4: Document follow-up work**

List optional future improvements:

- advisory validator for verb repetition
- anti-pattern warnings
- prompt debug snapshots for generated guidance slices

