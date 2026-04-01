# Zone-Based Resume Templates Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace flow-layout Jinja2 templates (`base_template_DE.html`, `base_template_ML.html`) with zone-based hybrid templates that combine pixel-perfect positioning (from the static HTML replicas) with limited Jinja2 variables for bio, experience skills lines, and technical skills sections.

**Architecture:** Each template is mostly hardcoded HTML with `position: absolute` per-line divs (copied from `Fei_Huang_*_Resume.html`). Three "variable zones" use Jinja2: bio (flowing text in a positioned container), per-experience skills lines (single-line divs), and technical skills section (flowing categories in a positioned container). `_schema_to_context()` is simplified to output only these variables. Entry visibility and full experience/project rebuilds are no longer supported in ADAPT_TEMPLATE — those scenarios use FULL_CUSTOMIZE fallback.

**Tech Stack:** Jinja2, HTML/CSS absolute positioning, Python (resume_renderer.py, resume_validator.py), pytest

---

### Task 1: Create zone-based DE template

**Files:**
- Overwrite: `templates/base_template_DE.html`
- Reference: `templates/Fei_Huang_DE_Resume.html` (source of all fixed content)

**Step 1: Build the zone-based DE template**

Start from `Fei_Huang_DE_Resume.html` and make these specific changes:

**1a. Add `| safe` filter support** — The Jinja2 env uses `autoescape=True`, so bio text containing `<strong>` would be escaped. Variable zones must use `| safe`.

**1b. Replace the bio section** (3 hardcoded divs at top:90.5/102.5/114.5) with a single flowing zone:

```html
    <div class="line section content-shift" style="left:42pt; top:77.3pt;">BIO</div>
    <div class="content-shift" style="position:absolute; left:42pt; top:90.5pt; width:512pt; max-height:38pt; overflow:hidden; line-height:12pt;">
      <span class="bio">{{ bio | safe }}</span>
    </div>
```

**1c. Replace each experience's skills line** with a Jinja2 variable. Example for GLP (top:339.5pt in the fixed HTML):

```html
    <div class="line body content-shift" style="left:42pt; top:339.5pt;"><strong>Skills:</strong> {{ glp_skills }}</div>
```

Repeat for BQ (`bq_skills` at top:484.6pt), Ele.me (`ele_skills` at top:630.6pt).

**1d. Replace the Technical Skills section** (right column, multiple hardcoded lines starting at top:539.6pt) with a flowing zone:

```html
    <div class="line section content-shift" style="left:325.9pt; top:526.4pt;">TECHNICAL SKILLS</div>
    <div class="content-shift" style="position:absolute; left:325.9pt; top:539.6pt; width:228pt; max-height:110pt; overflow:hidden;">
      {% for skill in skills %}
      <div class="body" style="line-height:13pt;{% if not loop.first %} margin-top:3pt;{% endif %}"><strong>{{ skill.category }}:</strong> {{ skill.skills_list }}</div>
      {% endfor %}
    </div>
```

**1e. Keep ALL other content hardcoded** — header, experience org/date/bullet lines, education, certifications, recent project, languages. These are copied verbatim from `Fei_Huang_DE_Resume.html`.

**Step 2: Verify template syntax**

Run: `python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('templates'), autoescape=True); t = env.get_template('base_template_DE.html'); print('OK:', len(t.render(bio='test', glp_skills='X', bq_skills='Y', ele_skills='Z', skills=[{'category':'A','skills_list':'B'}])))"`

Expected: `OK:` followed by a number (no template syntax errors)

**Step 3: Commit**

```bash
git add templates/base_template_DE.html
git commit -m "feat: replace DE Jinja2 template with zone-based hybrid layout"
```

---

### Task 2: Create zone-based ML template

**Files:**
- Overwrite: `templates/base_template_ML.html`
- Reference: `templates/Fei_Huang_ML_Resume.html` (source of all fixed content)

**Step 1: Build the zone-based ML template**

Same approach as Task 1, with ML-specific differences:

**1a. Bio zone** — same structure, same position (top:90.5pt, width:512pt).

**1b. Experience skills lines:**
- GLP: `{{ glp_skills }}` at top:337.4pt
- BQ: `{{ bq_skills }}` at top:508.4pt
- Ele.me: `{{ ele_skills }}` at top:624.4pt
- No Henan entry in ML template

**1c. Technical Skills zone** — LEFT column (not right), starting at top:652.8pt:

```html
    <div class="line section content-shift" style="left:42pt; top:652.8pt;">TECHNICAL SKILLS</div>
    <div class="content-shift" style="position:absolute; left:42pt; top:667.9pt; width:268pt; max-height:118pt; overflow:hidden;">
      {% for skill in skills %}
      <div class="body" style="line-height:13pt;{% if not loop.first %} margin-top:3pt;{% endif %}"><strong>{{ skill.category }}:</strong> {{ skill.skills_list }}</div>
      {% endfor %}
    </div>
```

Note: width is 268pt (left column) vs 228pt (DE right column). max-height is 118pt (more space available since no entries below until page bottom).

**Step 2: Verify template syntax**

Run: `python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('templates'), autoescape=True); t = env.get_template('base_template_ML.html'); print('OK:', len(t.render(bio='test', glp_skills='X', bq_skills='Y', ele_skills='Z', skills=[{'category':'A','skills_list':'B'}])))"`

Expected: `OK:` followed by a number

**Step 3: Commit**

```bash
git add templates/base_template_ML.html
git commit -m "feat: replace ML Jinja2 template with zone-based hybrid layout"
```

---

### Task 3: Update `_schema_to_context()` for zone-based templates

**Files:**
- Modify: `src/resume_renderer.py` — `_schema_to_context()` method (lines 316-420)

**Step 1: Write failing test**

Add to `tests/test_resume_renderer_tiers.py`:

```python
def test_schema_to_context_outputs_per_entry_skills():
    """_schema_to_context should output per-entry skills variables for zone-based templates."""
    tmp_dir = _local_tmp_dir("renderer_zone_skills")
    renderer = _make_renderer(
        tmp_dir,
        {"resume_tier": "ADAPT_TEMPLATE", "template_id_final": "DE"},
    )
    schema = {
        "bio": {"slot_id": "bio", "default": "Default bio"},
        "sections": [
            {
                "section_id": "experience",
                "entries": [
                    {
                        "entry_id": "glp",
                        "company": "GLP Technology (Fintech)",
                        "title": "Senior Data Engineer",
                        "date": "JULY 2017 - AUGUST 2019",
                        "technical_skills": "Python, SQL, AWS",
                        "bullets": [{"slot_id": "glp_1", "default": "Built X"}],
                    },
                    {
                        "entry_id": "bq",
                        "company": "BQ Investment (Hedge Fund)",
                        "title": "Quant Developer",
                        "date": "JULY 2015 - JUNE 2017",
                        "technical_skills": "Python, SQL, MATLAB",
                        "bullets": [{"slot_id": "bq_1", "default": "Built Y"}],
                    },
                ],
            },
            {
                "section_id": "skills",
                "categories": [
                    {"cat_id": "programming", "default": "Python, SQL"},
                ],
            },
        ],
    }
    tailored = {
        "slot_overrides": {"bio": "Custom bio"},
        "skills_override": {},
        "entry_visibility": {},
        "change_summary": "test",
    }
    analysis = {"seniority": "mid"}

    context = renderer._schema_to_context(schema, tailored, analysis)

    assert context["bio"] == "Custom bio"
    assert context["glp_skills"] == "Python, SQL, AWS"
    assert context["bq_skills"] == "Python, SQL, MATLAB"
    assert len(context["skills"]) == 1
    assert context["skills"][0]["category"] == "Programming"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_resume_renderer_tiers.py::test_schema_to_context_outputs_per_entry_skills -v`

Expected: FAIL — `KeyError: 'glp_skills'`

**Step 3: Update `_schema_to_context()`**

Add per-entry skills extraction at the end of the method. Replace the method body in `src/resume_renderer.py`:

```python
    def _schema_to_context(self, schema: Dict, tailored: Dict, analysis: Dict) -> Dict:
        """Convert slot_schema + tier-2 overrides into a zone-based template context.

        Zone-based templates hardcode most content. This method outputs:
        - bio: string (from slot_overrides or schema default)
        - {entry_id}_skills: per-experience skills line string
        - skills: list of {category, skills_list} for the Technical Skills zone
        """
        slot_overrides = tailored.get('slot_overrides', {})
        skills_override = tailored.get('skills_override', {})

        context = {}

        # Bio: use slot_override if present, else pick senior/default based on seniority
        seniority = analysis.get('seniority', 'mid')
        bio_schema = schema.get('bio', {})
        if 'bio' in slot_overrides:
            context['bio'] = slot_overrides['bio']
        elif seniority == 'senior' and bio_schema.get('senior'):
            context['bio'] = bio_schema['senior']
        else:
            context['bio'] = bio_schema.get('default', '')

        # Per-entry skills lines
        for section in schema.get('sections', []):
            if section.get('section_id') != 'experience':
                continue
            for entry in section.get('entries', []):
                entry_id = entry['entry_id']
                context[f'{entry_id}_skills'] = entry.get('technical_skills', '')

        # Build skills from schema categories + overrides
        skills = []
        for section in schema.get('sections', []):
            if section.get('section_id') != 'skills':
                continue
            for cat in section.get('categories', []):
                cat_id = cat['cat_id']
                skills_list = skills_override.get(cat_id, cat.get('default', ''))
                display_name = cat_id.replace('_', ' ').title()
                CAT_DISPLAY = {
                    'programming': 'Programming',
                    'data_engineering': 'Data Engineering',
                    'infrastructure': 'Infrastructure',
                    'analytics_ml': 'Analytics & ML',
                    'ml_modeling': 'ML & Modeling',
                    'data_infrastructure': 'Data & Infrastructure',
                    'domains': 'Domains',
                    'backend_systems': 'Backend Systems',
                    'data_systems': 'Data Systems',
                }
                display_name = CAT_DISPLAY.get(cat_id, display_name)
                skills.append({
                    'category': display_name,
                    'skills_list': skills_list,
                })

        skills = self._dedup_skills(skills)
        context['skills'] = skills

        return context
```

Key changes vs. old version:
- No longer builds `experiences` or `projects` lists (hardcoded in template)
- No longer copies `self.base_context` (zone templates hardcode name/contact/education)
- No longer checks `entry_visibility` (not applicable to zone-based layout)
- Adds `{entry_id}_skills` variables for per-experience skills lines

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_resume_renderer_tiers.py::test_schema_to_context_outputs_per_entry_skills -v`

Expected: PASS

**Step 5: Commit**

```bash
git add src/resume_renderer.py tests/test_resume_renderer_tiers.py
git commit -m "refactor: simplify _schema_to_context for zone-based templates"
```

---

### Task 4: Add validator constraints for variable zone overflow

**Files:**
- Modify: `src/resume_validator.py` — add `validate_zone_overflow()` method
- Modify: `src/resume_renderer.py` — call validator before rendering in `_render_adapt_template()`
- Test: `tests/test_resume_renderer_tiers.py`

**Step 1: Write failing test**

Add to `tests/test_resume_renderer_tiers.py`:

```python
def test_schema_to_context_bio_too_long_triggers_warning():
    """Bio exceeding 280 chars should be truncated with warning."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    long_bio = "A" * 300
    tailored = {"bio": long_bio, "experiences": [], "projects": [], "skills": []}
    result = validator.validate_adapt_zones(tailored)
    assert not result.passed or any("bio" in w.lower() for w in result.warnings)


def test_schema_to_context_skills_line_too_long_triggers_warning():
    """Skills line exceeding 70 chars should produce a warning."""
    from src.resume_validator import ResumeValidator

    validator = ResumeValidator()
    long_skills = "A" * 80
    tailored = {"bio": "Short bio", "glp_skills": long_skills}
    result = validator.validate_adapt_zones(tailored)
    assert any("skills" in w.lower() for w in result.warnings)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_resume_renderer_tiers.py::test_schema_to_context_bio_too_long_triggers_warning tests/test_resume_renderer_tiers.py::test_schema_to_context_skills_line_too_long_triggers_warning -v`

Expected: FAIL — `AttributeError: 'ResumeValidator' object has no method 'validate_adapt_zones'`

**Step 3: Add `validate_adapt_zones()` to ResumeValidator**

Add to `src/resume_validator.py` class `ResumeValidator`:

```python
    def validate_adapt_zones(self, context: dict) -> 'ValidationResult':
        """Validate variable zone content for zone-based ADAPT templates.

        Checks:
        - Bio length (max 280 chars for ~3 lines at 10pt in 512pt width)
        - Per-entry skills line length (max 70 chars for single line)
        """
        warnings = []
        errors = []

        # Bio length check
        bio = context.get('bio', '')
        if len(bio) > 280:
            warnings.append(f"Bio too long ({len(bio)} chars, max 280) — may overflow zone")

        # Per-entry skills line check
        for key in ('glp_skills', 'bq_skills', 'ele_skills', 'henan_skills'):
            value = context.get(key, '')
            if value and len(value) > 70:
                warnings.append(f"{key} too long ({len(value)} chars, max 70) — may overflow line")

        return ValidationResult(passed=len(errors) == 0, errors=errors, warnings=warnings)
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_resume_renderer_tiers.py::test_schema_to_context_bio_too_long_triggers_warning tests/test_resume_renderer_tiers.py::test_schema_to_context_skills_line_too_long_triggers_warning -v`

Expected: PASS

**Step 5: Wire into `_render_adapt_template()`**

In `src/resume_renderer.py`, inside `_render_adapt_template()`, after `context = self._schema_to_context(...)` and before `template.render(...)`, add:

```python
        # Validate zone overflow
        zone_result = self.validator.validate_adapt_zones(context)
        if zone_result.warnings:
            for w in zone_result.warnings:
                print(f"  [ZONE WARN] {w}")
```

**Step 6: Commit**

```bash
git add src/resume_validator.py src/resume_renderer.py tests/test_resume_renderer_tiers.py
git commit -m "feat: add zone overflow validation for ADAPT templates"
```

---

### Task 5: Update existing tests for new template contract

**Files:**
- Modify: `tests/test_resume_renderer_tiers.py`

**Step 1: Update `test_base_template_de_renders_with_standard_context`**

Replace the existing test to match the new zone-based template contract:

```python
def test_base_template_de_renders_with_standard_context():
    """Zone-based base_template_DE.html should render with bio, skills, and per-entry skills."""
    env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    template = env.get_template("base_template_DE.html")

    html = template.render(
        bio='<strong>Data Engineer</strong> with 6+ years of experience.',
        glp_skills="Python, SQL, AWS, Redshift, Airflow, Docker",
        bq_skills="Python, SQL, MATLAB, Data Quality",
        ele_skills="Python, SQL, Hadoop, Hive, Tableau",
        skills=[
            {"category": "Programming", "skills_list": "Python, SQL, Bash"},
            {"category": "Data Engineering", "skills_list": "PySpark, Spark, Delta Lake"},
        ],
    )
    # Fixed content should be present
    assert "Fei Huang" in html
    assert "GLP Technology" in html
    assert "Vrije Universiteit Amsterdam" in html
    # Variable content should be rendered
    assert "Data Engineer" in html  # bio
    assert "Python, SQL, AWS" in html  # glp_skills
    assert "PySpark, Spark, Delta Lake" in html  # skills
```

**Step 2: Update `test_base_template_ml_renders_with_standard_context`**

```python
def test_base_template_ml_renders_with_standard_context():
    """Zone-based base_template_ML.html should render with bio, skills, and per-entry skills."""
    env = Environment(loader=FileSystemLoader(str(Path("templates").resolve())), autoescape=True)
    template = env.get_template("base_template_ML.html")

    html = template.render(
        bio='<strong>Machine Learning Engineer</strong> with an M.Sc. in AI.',
        glp_skills="Python, SQL, PySpark, Feature Engineering",
        bq_skills="Python, SQL, NumPy, pandas, Statistical Modeling",
        ele_skills="Python, SQL, Clustering, Anomaly Detection",
        skills=[
            {"category": "ML & Modeling", "skills_list": "PyTorch, scikit-learn"},
            {"category": "Programming", "skills_list": "Python, SQL, Bash"},
        ],
    )
    assert "Fei Huang" in html
    assert "GLP Technology" in html
    assert "Uncertainty Quantification" in html  # fixed project content
    assert "Machine Learning Engineer" in html  # bio
    assert "Python, SQL, PySpark" in html  # glp_skills
    assert "PyTorch, scikit-learn" in html  # skills
```

**Step 3: Update `test_render_resume_adapt_template_pass_generates_files`**

The existing test uses a minimal registry stub. Add ML template support and update the stub schema to include `technical_skills` per entry:

```python
def test_render_resume_adapt_template_pass_generates_files():
    tmp_dir = _local_tmp_dir("renderer_test_workspace_adapt")
    renderer = _make_renderer(
        tmp_dir,
        {
            "resume_tier": "ADAPT_TEMPLATE",
            "template_id_final": "DE",
            "c3_decision": "PASS",
            "tailored_resume": json.dumps(
                {
                    "slot_overrides": {"bio": "Adapted bio"},
                    "skills_override": {"programming": "Python, SQL, Scala"},
                    "entry_visibility": {},
                    "change_summary": "Changed bio and skills",
                }
            ),
        },
    )
    # Update stub schema with technical_skills per entry
    renderer.registry["templates"]["DE"]["slot_schema"]["sections"][0]["entries"][0]["technical_skills"] = "Python, SQL"

    result = renderer.render_resume("job-1")

    assert result is not None
    assert Path(result["html_path"]).exists()
    assert Path(result["pdf_path"]).exists()
    # Verify the HTML contains adapted content
    html = Path(result["html_path"]).read_text()
    assert "Adapted bio" in html
```

**Step 4: Run all tests**

Run: `pytest tests/test_resume_renderer_tiers.py -v`

Expected: ALL PASS

**Step 5: Commit**

```bash
git add tests/test_resume_renderer_tiers.py
git commit -m "test: update tests for zone-based template contract"
```

---

### Task 6: Visual verification

**Step 1: Render DE template with defaults and compare**

```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
t = env.get_template('base_template_DE.html')
html = t.render(
    bio='<strong>Data Engineer</strong> with 6+ years of experience building data platforms across e-commerce, market data, and credit risk. Built end-to-end ingestion, warehousing, data quality, and decisioning systems from the ground up. <strong>M.Sc. in Artificial Intelligence</strong>. Certified Data Engineer with hands-on experience in Spark and Delta Lake.',
    glp_skills='Python, SQL, AWS, Redshift, Airflow, Docker',
    bq_skills='Python, SQL, MATLAB, Data Quality',
    ele_skills='Python, SQL, Hadoop, Hive, Tableau',
    skills=[
        {'category': 'Programming', 'skills_list': 'Python, SQL, Bash'},
        {'category': 'Data Engineering', 'skills_list': 'PySpark, Spark, Delta Lake, Databricks, Airflow, Redshift, ETL/ELT, Data Modeling, Data Quality, Structured Streaming, Schema Evolution, Medallion Architecture'},
        {'category': 'Infrastructure', 'skills_list': 'AWS, Docker, Git, CI/CD'},
        {'category': 'Analytics & ML', 'skills_list': 'Pandas, NumPy, scikit-learn, PyTorch, A/B Testing, Tableau'},
    ],
)
with open('output/_verify_de_zone.html', 'w') as f:
    f.write(html)
print('Written to output/_verify_de_zone.html')
"
```

**Step 2: Render ML template with defaults and compare**

```bash
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'), autoescape=True)
t = env.get_template('base_template_ML.html')
html = t.render(
    bio='<strong>Machine Learning Engineer</strong> with an M.Sc. in AI (GPA 8.2) and 6 years building prediction and scoring systems in fintech, trading, and e-commerce. Strengths in feature engineering, model evaluation, and end-to-end ML pipelines, from raw data through production deployment.',
    glp_skills='Python, SQL, PySpark, Feature Engineering, AWS (Redshift, S3), Airflow',
    bq_skills='Python, SQL, NumPy, pandas, Statistical Modeling',
    ele_skills='Python, SQL, Clustering, Anomaly Detection',
    skills=[
        {'category': 'ML & Modeling', 'skills_list': 'PyTorch, Hugging Face Transformers, scikit-learn, LightGBM, XGBoost, Learning-to-Rank, Deep RL, Statistical Testing'},
        {'category': 'Programming', 'skills_list': 'Python, SQL, NumPy, pandas, Bash'},
        {'category': 'Data & Infrastructure', 'skills_list': 'PySpark, Airflow, FastAPI, AWS (Redshift, S3, EC2), Delta Lake, Docker, Git'},
        {'category': 'Domains', 'skills_list': 'Feature Engineering, NLP, Time-Series, Anomaly Detection, Uncertainty Quantification'},
    ],
)
with open('output/_verify_ml_zone.html', 'w') as f:
    f.write(html)
print('Written to output/_verify_ml_zone.html')
"
```

**Step 3: Open both in browser, compare against SVG originals**

Visually verify:
- Bio text renders correctly with `<strong>` emphasis
- Skills lines per experience match expected content
- Technical Skills section flows with correct spacing
- All fixed content (experience bullets, education, projects) is pixel-identical to SVG

**Step 4: Clean up verification files**

```bash
rm output/_verify_de_zone.html output/_verify_ml_zone.html
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: zone-based resume templates complete — pixel-perfect + dynamic slots"
```
