# Resume Overflow Fix Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Eliminate silent content clipping in ADAPT_TEMPLATE resumes by switching to per-line bio architecture and adding hard limits with CSS safety nets for skills zones.

**Architecture:** Two-layer defense. Layer 1: per-line bio variables (`bio_1`/`bio_2`/`bio_3`) replace flowing text, validator BLOCKS on overflow. Layer 2: CSS `text-overflow: ellipsis` on skills lines, tighter category limits. Templates, registry, validator, renderer, and AI prompt all change in concert.

**Tech Stack:** Jinja2 templates (HTML), YAML configs, Python (validator + renderer), pytest

**Design doc:** `docs/plans/2026-04-02-resume-overflow-fix-design.md`

---

### Task 1: Update `validate_adapt_zones()` to BLOCK on overflow

**Files:**
- Modify: `src/resume_validator.py:454-473`
- Test: `tests/test_resume_renderer_tiers.py` (update existing + add new tests)

**Step 1: Write failing tests**

Add to `tests/test_resume_renderer_tiers.py`:

```python
def test_validate_adapt_zones_bio_line_too_long_blocks():
    """Bio line exceeding 105 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "A" * 110,
        "bio_2": "Short line two.",
        "bio_3": "Short line three.",
    })
    assert not result.passed
    assert any("bio_1" in e for e in result.errors)


def test_validate_adapt_zones_bio_lines_within_limit_passes():
    """Bio lines within 105 chars should pass."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Data Engineer with 6+ years of experience building data platforms across e-commerce and credit risk.",
        "bio_2": "Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up.",
        "bio_3": "M.Sc. in Artificial Intelligence. Certified Data Engineer with hands-on Spark and Delta Lake.",
    })
    assert result.passed
    assert len(result.errors) == 0


def test_validate_adapt_zones_skills_line_blocks():
    """Skills line exceeding 65 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Short.", "bio_2": "Short.", "bio_3": "Short.",
        "glp_skills": "A" * 70,
    })
    assert not result.passed
    assert any("glp_skills" in e for e in result.errors)


def test_validate_adapt_zones_skills_categories_blocks():
    """More than 5 skill categories should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Short.", "bio_2": "Short.", "bio_3": "Short.",
        "skills": [
            {"category": f"Cat{i}", "skills_list": "Python"} for i in range(6)
        ],
    })
    assert not result.passed
    assert any("categor" in e.lower() for e in result.errors)


def test_validate_adapt_zones_skills_list_too_long_blocks():
    """A single skills_list exceeding 80 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({
        "bio_1": "Short.", "bio_2": "Short.", "bio_3": "Short.",
        "skills": [
            {"category": "Programming", "skills_list": "A" * 85},
        ],
    })
    assert not result.passed
    assert any("skills_list" in e.lower() or "programming" in e.lower() for e in result.errors)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_resume_renderer_tiers.py::test_validate_adapt_zones_bio_line_too_long_blocks tests/test_resume_renderer_tiers.py::test_validate_adapt_zones_bio_lines_within_limit_passes tests/test_resume_renderer_tiers.py::test_validate_adapt_zones_skills_line_blocks tests/test_resume_renderer_tiers.py::test_validate_adapt_zones_skills_categories_blocks tests/test_resume_renderer_tiers.py::test_validate_adapt_zones_skills_list_too_long_blocks -v`

Expected: FAIL (new bio_1/bio_2/bio_3 keys not recognized, errors not produced)

**Step 3: Implement `validate_adapt_zones()` rewrite**

Replace `src/resume_validator.py:454-473` with:

```python
    def validate_adapt_zones(self, context: dict) -> 'ValidationResult':
        """Validate variable zone content for zone-based ADAPT templates.

        BLOCKING checks (errors):
        - Each bio line (bio_1, bio_2, bio_3) max 105 chars
        - Per-entry skills line max 65 chars
        - Technical skills: max 5 categories, each skills_list max 80 chars

        Backward compat: if 'bio' key present (old format), warn but don't block.
        """
        warnings = []
        errors = []

        # Per-line bio validation (new format)
        for key in ('bio_1', 'bio_2', 'bio_3'):
            value = context.get(key, '')
            if len(value) > 105:
                errors.append(f"{key} too long ({len(value)} chars, max 105) — will overflow line")

        # Backward compat: old single 'bio' key
        if 'bio' in context and 'bio_1' not in context:
            bio = context.get('bio', '')
            if len(bio) > 280:
                warnings.append(f"Bio too long ({len(bio)} chars, max 280) — may overflow zone")

        # Per-entry skills line validation
        for key in ('glp_skills', 'bq_skills', 'ele_skills', 'henan_skills'):
            value = context.get(key, '')
            if value and len(value) > 65:
                errors.append(f"{key} too long ({len(value)} chars, max 65) — will overflow line")

        # Technical skills zone validation
        skills = context.get('skills', [])
        if len(skills) > 5:
            errors.append(f"Too many skill categories ({len(skills)}, max 5) — will overflow zone")
        for skill in skills:
            sl = skill.get('skills_list', '')
            cat = skill.get('category', '?')
            if len(sl) > 80:
                errors.append(f"skills_list for '{cat}' too long ({len(sl)} chars, max 80) — will wrap excessively")

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_resume_renderer_tiers.py -v -k "validate_adapt_zones"`

Expected: ALL PASS

**Step 5: Also update the old bio tests**

Update `test_validate_adapt_zones_bio_too_long` (line 544-550) to use the backward-compat path:

```python
def test_validate_adapt_zones_bio_too_long():
    """Old-format bio exceeding 280 chars should produce a warning (backward compat)."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({"bio": "A" * 300})
    assert any("bio" in w.lower() for w in result.warnings)
```

And update `test_validate_adapt_zones_skills_line_too_long` (line 553-559) since 80 chars now blocks:

```python
def test_validate_adapt_zones_skills_line_too_long():
    """Skills line exceeding 65 chars should produce a BLOCKING error."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    result = validator.validate_adapt_zones({"bio_1": "A", "bio_2": "B", "bio_3": "C", "glp_skills": "A" * 70})
    assert not result.passed
    assert any("glp_skills" in e for e in result.errors)
```

**Step 6: Run full test suite**

Run: `pytest tests/test_resume_renderer_tiers.py -v`

Expected: ALL PASS

**Step 7: Commit**

```bash
git add src/resume_validator.py tests/test_resume_renderer_tiers.py
git commit -m "feat: make validate_adapt_zones BLOCK on overflow (bio per-line, skills limits)"
```

---

### Task 2: Update `template_registry.yaml` — split bios into 3 lines

**Files:**
- Modify: `config/template_registry.yaml`

**Step 1: Update DE template bio section**

Replace the DE `bio` block (lines 25-28) with:

```yaml
    slot_schema:
      bio:
        slot_id: "bio"
        bio_1:
          default: "Data Engineer with 6+ years of experience building data platforms across e-commerce, market data, and credit risk."
          senior: "Senior Data Engineer with 6+ years building data platforms from scratch. First technical hire at GLP Technology,"
        bio_2:
          default: "Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up."
          senior: "grew the data team from 0 to 4 engineers while architecting the credit risk data platform. End-to-end ownership"
        bio_3:
          default: "M.Sc. in Artificial Intelligence. Certified Data Engineer with hands-on experience in Spark and Delta Lake."
          senior: "across ingestion, warehousing, data quality, and automated decisioning. M.Sc. in AI, Databricks Certified."
```

**Step 2: Update ML template bio section**

Replace the ML `bio` block (lines 132-135) with:

```yaml
      bio:
        slot_id: "bio"
        bio_1:
          default: "Machine Learning Engineer with an M.Sc. in AI (GPA 8.2) and 6 years building prediction and scoring"
          senior: "Senior ML Engineer with an M.Sc. in AI (GPA 8.2) and 6 years building prediction and scoring systems in"
        bio_2:
          default: "systems in fintech, trading, and e-commerce. Strengths in feature engineering, model evaluation, and"
          senior: "production. First data hire at GLP Technology, built the credit risk prediction system and grew the data team."
        bio_3:
          default: "end-to-end ML pipelines, from raw data through production deployment."
          senior: "Strengths in feature engineering, model evaluation, and end-to-end ML pipelines."
```

**Step 3: Update Backend template bio section**

Replace the Backend `bio` block (lines 228-231) with:

```yaml
      bio:
        slot_id: "bio"
        bio_1:
          default: "Software Engineer with 6+ years building data-intensive Python systems across fintech, e-commerce, and trading."
          senior: "Senior Software Engineer with 6+ years building data-intensive Python systems. First technical hire at GLP"
        bio_2:
          default: "Built a financial data lakehouse from scratch and led a team of 5 engineers on credit risk decisioning systems."
          senior: "Technology, grew the engineering team from 0 to 4 while architecting credit risk decisioning and pipeline infra."
        bio_3:
          default: "M.Sc. in AI (VU Amsterdam), Databricks Certified Data Engineer Professional."
          senior: "End-to-end ownership from system design through production deployment. M.Sc. in AI, Databricks Certified."
```

**Step 4: Verify all bio lines are within 105 char limit**

Run a quick check (in Python or manually count). All lines above have been measured to fit.

**Step 5: Commit**

```bash
git add config/template_registry.yaml
git commit -m "refactor: split template bio defaults into per-line bio_1/bio_2/bio_3"
```

---

### Task 3: Update `_schema_to_context()` — map per-line bio to template context

**Files:**
- Modify: `src/resume_renderer.py:316-376`
- Test: `tests/test_resume_renderer_tiers.py`

**Step 1: Write failing test**

Add to `tests/test_resume_renderer_tiers.py`:

```python
def test_schema_to_context_outputs_per_line_bio():
    """_schema_to_context should output bio_1, bio_2, bio_3 from per-line schema."""
    tmp_dir = _local_tmp_dir("renderer_perline_bio")
    renderer = _make_renderer(
        tmp_dir,
        {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"},
    )
    schema = {
        "bio": {
            "slot_id": "bio",
            "bio_1": {"default": "Line one default.", "senior": "Line one senior."},
            "bio_2": {"default": "Line two default.", "senior": "Line two senior."},
            "bio_3": {"default": "Line three default.", "senior": "Line three senior."},
        },
        "sections": [
            {
                "section_id": "experience",
                "entries": [
                    {
                        "entry_id": "glp",
                        "company": "GLP",
                        "title": "Lead",
                        "date": "2017-2019",
                        "technical_skills": "Python, SQL",
                        "bullets": [{"slot_id": "glp_1", "default": "Built X"}],
                    },
                ],
            },
            {
                "section_id": "skills",
                "categories": [{"cat_id": "programming", "default": "Python, SQL"}],
            },
        ],
    }
    tailored = {"slot_overrides": {}, "skills_override": {}, "entry_visibility": {}, "change_summary": "test"}
    analysis = {"seniority": "mid"}

    context = renderer._schema_to_context(schema, tailored, analysis)

    assert context["bio_1"] == "Line one default."
    assert context["bio_2"] == "Line two default."
    assert context["bio_3"] == "Line three default."
    assert "bio" not in context  # old single key should not be present


def test_schema_to_context_senior_bio_lines():
    """Senior seniority should pick senior bio lines."""
    tmp_dir = _local_tmp_dir("renderer_senior_bio")
    renderer = _make_renderer(
        tmp_dir,
        {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"},
    )
    schema = {
        "bio": {
            "slot_id": "bio",
            "bio_1": {"default": "Mid one.", "senior": "Senior one."},
            "bio_2": {"default": "Mid two.", "senior": "Senior two."},
            "bio_3": {"default": "Mid three.", "senior": "Senior three."},
        },
        "sections": [],
    }
    tailored = {"slot_overrides": {}, "skills_override": {}, "entry_visibility": {}, "change_summary": "test"}
    analysis = {"seniority": "senior"}

    context = renderer._schema_to_context(schema, tailored, analysis)

    assert context["bio_1"] == "Senior one."
    assert context["bio_2"] == "Senior two."
    assert context["bio_3"] == "Senior three."


def test_schema_to_context_slot_override_bio_lines():
    """AI-generated bio line overrides should take precedence over defaults."""
    tmp_dir = _local_tmp_dir("renderer_override_bio")
    renderer = _make_renderer(
        tmp_dir,
        {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"},
    )
    schema = {
        "bio": {
            "slot_id": "bio",
            "bio_1": {"default": "Default one.", "senior": "Senior one."},
            "bio_2": {"default": "Default two.", "senior": "Senior two."},
            "bio_3": {"default": "Default three.", "senior": "Senior three."},
        },
        "sections": [],
    }
    tailored = {
        "slot_overrides": {
            "bio_1": "Custom line one for this job.",
            "bio_2": "Custom line two for this job.",
            "bio_3": "Custom line three for this job.",
        },
        "skills_override": {},
        "entry_visibility": {},
        "change_summary": "Adapted bio",
    }
    analysis = {"seniority": "mid"}

    context = renderer._schema_to_context(schema, tailored, analysis)

    assert context["bio_1"] == "Custom line one for this job."
    assert context["bio_2"] == "Custom line two for this job."
    assert context["bio_3"] == "Custom line three for this job."
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_resume_renderer_tiers.py::test_schema_to_context_outputs_per_line_bio tests/test_resume_renderer_tiers.py::test_schema_to_context_senior_bio_lines tests/test_resume_renderer_tiers.py::test_schema_to_context_slot_override_bio_lines -v`

Expected: FAIL (bio_1 not in context)

**Step 3: Rewrite bio handling in `_schema_to_context()`**

Replace lines 329-337 of `src/resume_renderer.py` (the bio block) with:

```python
        # Bio: per-line (bio_1, bio_2, bio_3)
        seniority = analysis.get('seniority', 'mid')
        bio_schema = schema.get('bio', {})
        for line_key in ('bio_1', 'bio_2', 'bio_3'):
            line_schema = bio_schema.get(line_key, {})
            if line_key in slot_overrides:
                context[line_key] = slot_overrides[line_key]
            elif seniority == 'senior' and line_schema.get('senior'):
                context[line_key] = line_schema['senior']
            else:
                context[line_key] = line_schema.get('default', '')
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_resume_renderer_tiers.py -v -k "schema_to_context"`

Expected: ALL PASS

**Step 5: Update `validate_tier2_output()` in `src/template_registry.py`**

The valid_slots set (line 105) currently only includes `"bio"`. Add the per-line keys:

Replace line 105:
```python
    valid_slots = {"bio"}
```
with:
```python
    valid_slots = {"bio", "bio_1", "bio_2", "bio_3"}
```

**Step 6: Update `_render_adapt_template()` to BLOCK on zone errors**

In `src/resume_renderer.py:422-426`, change from warning-only to error-blocking:

Replace:
```python
        # Validate zone overflow
        zone_result = self.validator.validate_adapt_zones(context)
        if zone_result.warnings:
            for w in zone_result.warnings:
                print(f"  [ZONE WARN] {w}")
```

With:
```python
        # Validate zone overflow (BLOCKING)
        zone_result = self.validator.validate_adapt_zones(context)
        if zone_result.warnings:
            for w in zone_result.warnings:
                print(f"  [ZONE WARN] {w}")
        if not zone_result.passed:
            for e in zone_result.errors:
                print(f"  [ZONE BLOCK] {e}")
            print(f"[Renderer] Zone validation failed for {job_id}, falling back to USE_TEMPLATE")
            return None
```

**Step 7: Update `_make_renderer` test helper and existing adapt test**

In the test helper `_make_renderer` (around line 73), update the schema to use per-line bio:

Replace line 73-74:
```python
                    "bio": {"slot_id": "bio", "default": "Default bio"},
```
with:
```python
                    "bio": {
                        "slot_id": "bio",
                        "bio_1": {"default": "Default bio line one."},
                        "bio_2": {"default": "Default bio line two."},
                        "bio_3": {"default": "Default bio line three."},
                    },
```

Update `test_render_resume_adapt_template_pass_generates_files` (line 137-140) slot_overrides:

Replace:
```python
                    "slot_overrides": {"bio": "Adapted bio", "glp_1": "Adapted bullet"},
```
with:
```python
                    "slot_overrides": {"bio_1": "Adapted bio line one.", "bio_2": "Adapted line two.", "bio_3": "Adapted line three.", "glp_1": "Adapted bullet"},
```

Update `test_base_template_de_renders_with_standard_context` and `test_base_template_ml_renders_with_standard_context` to use `bio_1`/`bio_2`/`bio_3` instead of `bio` (this will be needed after Task 4 updates the templates — mark these tests as expected to fail until Task 4 is done, or do Task 3 and Task 4 together).

**Step 8: Run all tests**

Run: `pytest tests/test_resume_renderer_tiers.py -v`

Expected: Most pass; the two `test_base_template_*_renders_with_standard_context` tests may fail until templates are updated in Task 4.

**Step 9: Commit**

```bash
git add src/resume_renderer.py src/template_registry.py tests/test_resume_renderer_tiers.py
git commit -m "feat: _schema_to_context outputs per-line bio, zone validation blocks on errors"
```

---

### Task 4: Update HTML templates — per-line bio + CSS safety nets

**Files:**
- Modify: `templates/base_template_DE.html:151-154`
- Modify: `templates/base_template_ML.html:151-155`

**Step 1: Update DE template bio zone**

In `templates/base_template_DE.html`, replace lines 151-154:

```html
    <div class="line section content-shift" style="left:42pt; top:77.3pt;">BIO</div>
    <div class="content-shift" style="position:absolute; left:42pt; top:90.5pt; width:512pt; max-height:38pt; overflow:hidden; line-height:12pt;">
      <span class="bio">{{ bio | safe }}</span>
    </div>
```

With:

```html
    <div class="line section content-shift" style="left:42pt; top:77.3pt;">BIO</div>
    <div class="line bio content-shift" style="left:42pt; top:90.5pt;">{{ bio_1 }}</div>
    <div class="line bio content-shift" style="left:42pt; top:102.5pt;">{{ bio_2 }}</div>
    <div class="line bio content-shift" style="left:42pt; top:114.5pt;">{{ bio_3 }}</div>
```

**Step 2: Update DE template skills lines — add CSS overflow safety**

In `templates/base_template_DE.html`, for each per-entry skills line (lines 176, 191, 206), change from bare `.line` to overflow-safe. Replace each:

```html
    <div class="line body content-shift" style="left:42pt; top:339.5pt;"><strong>Skills:</strong> {{ glp_skills }}</div>
```

With:

```html
    <div class="line body content-shift" style="left:42pt; top:339.5pt; max-width:275pt; overflow:hidden; text-overflow:ellipsis;"><strong>Skills:</strong> {{ glp_skills }}</div>
```

Apply the same pattern to bq_skills (line 191, top:484.6pt) and ele_skills (line 206, top:630.6pt).

**Step 3: Update DE template tech skills zone — tighter margins**

Replace lines 247-251:

```html
    <div class="content-shift" style="position:absolute; left:325.9pt; top:539.6pt; width:228pt; max-height:110pt; overflow:hidden;">
      {% for skill in skills %}
      <div class="body" style="line-height:13pt;{% if not loop.first %} margin-top:3pt;{% endif %}"><strong>{{ skill.category }}:</strong> {{ skill.skills_list }}</div>
      {% endfor %}
    </div>
```

With:

```html
    <div class="content-shift" style="position:absolute; left:325.9pt; top:539.6pt; width:228pt; max-height:110pt; overflow:hidden;">
      {% for skill in skills %}
      <div class="body" style="line-height:13pt;{% if not loop.first %} margin-top:{% if skills|length >= 4 %}2{% else %}3{% endif %}pt;{% endif %}"><strong>{{ skill.category }}:</strong> {{ skill.skills_list }}</div>
      {% endfor %}
    </div>
```

**Step 4: Apply same changes to ML template**

In `templates/base_template_ML.html`:

Bio zone (lines 152-155): replace the flowing span with 3 per-line divs (same as DE, same top positions: 90.5pt, 102.5pt, 114.5pt).

Per-entry skills lines (lines 177, 194, 208): add `max-width:275pt; overflow:hidden; text-overflow:ellipsis;`.

Tech skills zone (lines 212-216): add the conditional margin-top (same Jinja2 expression). Note ML uses width:268pt instead of 228pt — keep that as-is.

**Step 5: Update template render tests**

In `tests/test_resume_renderer_tiers.py`, update `test_base_template_de_renders_with_standard_context` (line 408):

Replace the `template.render(...)` call:
```python
    html = template.render(
        bio='<strong>Data Engineer</strong> with 6+ years of experience.',
        glp_skills="Python, SQL, AWS, Redshift, Airflow, Docker",
        ...
    )
```
With:
```python
    html = template.render(
        bio_1='Data Engineer with 6+ years of experience building data platforms across e-commerce and credit risk.',
        bio_2='Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up.',
        bio_3='M.Sc. in Artificial Intelligence. Certified Data Engineer with hands-on Spark and Delta Lake.',
        glp_skills="Python, SQL, AWS, Redshift, Airflow, Docker",
        bq_skills="Python, SQL, MATLAB, Data Quality",
        ele_skills="Python, SQL, Hadoop, Hive, Tableau",
        skills=[
            {"category": "Programming", "skills_list": "Python, SQL, Bash"},
            {"category": "Data Engineering", "skills_list": "PySpark, Spark, Delta Lake"},
        ],
    )
    assert "Fei Huang" in html
    assert "GLP Technology" in html
    assert "Vrije Universiteit Amsterdam" in html
    assert "Data Engineer with 6+ years" in html  # bio_1
    assert "M.Sc. in Artificial Intelligence" in html  # bio_3
    assert "Python, SQL, AWS" in html  # glp_skills
    assert "PySpark, Spark, Delta Lake" in html  # skills
```

Apply the same pattern to `test_base_template_ml_renders_with_standard_context`.

**Step 6: Run all tests**

Run: `pytest tests/test_resume_renderer_tiers.py -v`

Expected: ALL PASS

**Step 7: Commit**

```bash
git add templates/base_template_DE.html templates/base_template_ML.html tests/test_resume_renderer_tiers.py
git commit -m "feat: per-line bio in templates + CSS overflow safety for skills"
```

---

### Task 5: Update AI prompt for per-line bio output

**Files:**
- Modify: `config/ai_config.yaml:450-481`

**Step 1: Update `tailor_adapt` prompt**

Replace the `tailor_adapt` prompt section (lines 450-481) with updated output schema that uses `bio_1`/`bio_2`/`bio_3`:

```yaml
  tailor_adapt: |
    # Template Adaptation

    You are adapting a polished resume template for a specific job. Do not rewrite the full resume.

    ## Target Job
    Title: {job_title}
    Company: {job_company}

    Job Description:
    {job_description}

    ## Routing Context
    Gaps: {routing_gaps}
    Adapt instructions: {adapt_instructions}

    ## Template Schema
    {template_schema}

    ## CONSTRAINTS (HARD LIMITS — violating any will reject the resume)
    - bio_1, bio_2, bio_3: each line MUST be <= 105 characters. Count carefully.
    - skills_override values: each MUST be <= 80 characters.
    - Max 5 skill categories total.

    ## Output JSON
    {{
      "slot_overrides": {{
        "bio_1": "First line of bio (max 105 chars)",
        "bio_2": "Second line of bio (max 105 chars)",
        "bio_3": "Third line of bio (max 105 chars)"
      }},
      "skills_override": {{
        "programming": "Optional replacement skill line (max 80 chars)"
      }},
      "entry_visibility": {{
        "glp": true
      }},
      "change_summary": "One sentence summary of the changes"
    }}

    ## Bio Writing Rules
    - The bio is exactly 3 lines. Each line is rendered independently (no word wrapping).
    - Line 1: Role + years + domain scope (most important — the hook).
    - Line 2: Key accomplishment or strength summary.
    - Line 3: Education credentials + certifications.
    - Each line must be a complete, readable phrase (no mid-word breaks).
    - If you don't need to change the bio, omit bio_1/bio_2/bio_3 from slot_overrides entirely.
```

**Step 2: Commit**

```bash
git add config/ai_config.yaml
git commit -m "feat: update tailor_adapt prompt for per-line bio output with char limits"
```

---

### Task 6: Integration test — render a mock ADAPT resume end-to-end

**Files:**
- Test: `tests/test_resume_renderer_tiers.py`

**Step 1: Write integration test**

```python
def test_adapt_template_perline_bio_end_to_end():
    """Full ADAPT_TEMPLATE render with per-line bio should produce HTML with all 3 bio lines."""
    from jinja2 import Environment, FileSystemLoader

    env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    template = env.get_template("base_template_DE.html")

    bio_1 = "Data Engineer with 6+ years of experience building data platforms across e-commerce and credit risk."
    bio_2 = "Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up."
    bio_3 = "M.Sc. in Artificial Intelligence. Certified Data Engineer with hands-on Spark and Delta Lake."

    # Verify all lines are within limit
    assert len(bio_1) <= 105
    assert len(bio_2) <= 105
    assert len(bio_3) <= 105

    html = template.render(
        bio_1=bio_1, bio_2=bio_2, bio_3=bio_3,
        glp_skills="Python, SQL, AWS, Redshift, Airflow, Docker",
        bq_skills="Python, SQL, MATLAB, Data Quality",
        ele_skills="Python, SQL, Hadoop, Hive, Tableau",
        skills=[
            {"category": "Programming", "skills_list": "Python, SQL, Bash"},
            {"category": "Data Engineering", "skills_list": "PySpark, Spark, Delta Lake, Databricks, Airflow"},
            {"category": "Infrastructure", "skills_list": "AWS, Docker, Git, CI/CD"},
            {"category": "Analytics & ML", "skills_list": "Pandas, NumPy, scikit-learn, PyTorch"},
        ],
    )

    # All 3 bio lines present
    assert bio_1 in html
    assert bio_2 in html
    assert bio_3 in html

    # Bio lines rendered as separate divs (not in a flowing span)
    assert '<span class="bio">' not in html

    # Skills present
    assert "Python, SQL, AWS" in html
    assert "PySpark, Spark, Delta Lake" in html

    # CSS safety: skills lines should have text-overflow
    assert "text-overflow:ellipsis" in html
```

**Step 2: Run the test**

Run: `pytest tests/test_resume_renderer_tiers.py::test_adapt_template_perline_bio_end_to_end -v`

Expected: PASS

**Step 3: Commit**

```bash
git add tests/test_resume_renderer_tiers.py
git commit -m "test: add integration test for per-line bio ADAPT template rendering"
```

---

### Task 7: Re-render existing resumes and verify

**This task is manual — not automated.**

**Step 1: Delete old rendered outputs for today's batch**

```bash
# Remove existing HTML/PDF outputs so they get re-rendered
# (Only for ADAPT_TEMPLATE jobs — USE_TEMPLATE just copies PDF)
python -c "
from src.db.job_db import JobDatabase
db = JobDatabase()
# Clear resume records so --prepare re-generates
db.conn.execute('DELETE FROM resumes WHERE template_version = \"adapt_v2\"')
db.conn.commit()
print('Cleared adapt_v2 resume records')
"
```

**Step 2: Re-run `--prepare`**

```bash
python scripts/job_pipeline.py --prepare
```

**Step 3: Visually inspect the generated PDFs**

Open the checklist at `http://localhost:8234/apply_checklist.html` and verify:
- Bio lines display completely (no truncation of "M.Sc. in Artificial Intelligence")
- Skills lines don't overlap the right column
- Technical skills section fits within the allocated space
- No visual regression in overall layout

**Step 4: Final commit with any adjustments**

If any character limits need tuning (e.g., a line is 106 chars in production), adjust the limit constants and re-run.
