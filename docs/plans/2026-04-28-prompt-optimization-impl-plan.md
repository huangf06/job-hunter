# Prompt x Config x Bullet Library Optimization — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Execute the 10 changes from `docs/plans/2026-04-28-prompt-bullet-config-optimization.md` — remove artificial limits, consolidate title sources, trim dead routing, add course selection, make career_note AI-controllable, and improve C1→C2 data flow.

**Architecture:** All changes modify the C1/C2 prompt pipeline (ai_config.yaml templates + ai_analyzer.py prompt construction) and downstream consumers (resume_renderer.py, resume_validator.py). No DB schema changes. No new dependencies.

**Tech Stack:** Python 3, PyYAML, Jinja2, pytest

**Design doc:** `docs/plans/2026-04-28-prompt-bullet-config-optimization.md`

---

### Task 1: C2 prompt — Remove artificial content limits and bullet distribution guidance

**Files:**
- Modify: `config/ai_config.yaml:271-330`

**Step 1: Edit the CONTENT SELECTION PRINCIPLE section**

In `config/ai_config.yaml`, replace the `### CONTENT SELECTION PRINCIPLE` block (lines 271-273) with:

```yaml
    ### CONTENT SELECTION PRINCIPLE
    Include every bullet that strengthens the application for THIS specific role.
    Exclude content that doesn't add signal. Quality and relevance over quantity.
    Sections order: Education → Projects → Experience → Skills → Additional.
    Education and Additional are static. You control: bio (optional), experiences, projects, skills.
```

Remove the 2-page constraint and "8-12 bullets" guidance entirely.

**Step 2: Remove the BULLET DISTRIBUTION section**

Delete the entire `### BULLET DISTRIBUTION (GUIDANCE, NOT HARD LIMITS)` block (lines 323-330):

```yaml
    ### BULLET DISTRIBUTION (GUIDANCE, NOT HARD LIMITS)
    Include bullets based on JD relevance. Typical ranges:
    - Most relevant experience: 2-4 bullets
    ...
```

**Step 3: Run tests**

Run: `pytest tests/ -x -q`
Expected: All pass (prompt text only, no code change)

**Step 4: Commit**

```bash
git add config/ai_config.yaml
git commit -m "C2 prompt: remove artificial page/bullet limits, trust AI judgment"
```

---

### Task 2: Remove language guidance from C2 + simplify C1 routing output

**Files:**
- Modify: `src/ai_analyzer.py:678,750`
- Modify: `config/ai_config.yaml:115-157`

**Step 1: Remove language guidance injection from C2**

In `src/ai_analyzer.py`, in `_build_tailor_prompt()`:

Remove the import usage at line 678:
```python
language_guidance = format_language_guidance_for_prompt("experience_bullet")
```

And the injection at line 750, change:
```python
return f"{language_guidance}\n\n{prompt_body}"
```
to:
```python
return prompt_body
```

Keep the import of `format_language_guidance_for_prompt` at the top (it may be used by cover_letter_generator via shared module).

**Step 2: Simplify C1 routing section in prompt**

In `config/ai_config.yaml`, replace the entire `## Resume Routing Decision` section (lines 115-131) with:

```yaml
    ## Resume Routing
    Template hint: {preselected_template_id} (confidence: {preselected_confidence})
    {ambiguous_warning}
    Template determines C2 role framing (DE/ML/DS) for bio, titles, project ordering.
    If the pre-selected template is wrong for this role, set override to true.
```

Replace the `resume_routing` object in the output schema (lines 149-157) with:

```yaml
      "resume_routing": {{
        "template_id": "{preselected_template_id}",
        "override": false,
        "override_reason": null
      }}
```

Remove: `tier`, `gaps`, `adapt_instructions` fields.

**Step 3: Run tests**

Run: `pytest tests/test_ai_analyzer.py -x -q`
Expected: All pass. The routing tests (`test_evaluate_job_resolves_routing_with_c1_override`) use mock `_call_claude` that returns full routing JSON — `_parse_response` will still find the fields, and `resolve_routing()` only reads `override` + `template_id`.

**Step 4: Commit**

```bash
git add src/ai_analyzer.py config/ai_config.yaml
git commit -m "remove language guidance from C2, simplify C1 routing output"
```

---

### Task 3: Consolidate title_options into work_experience

**Files:**
- Modify: `assets/bullet_library.yaml:543-564` (delete title_options block)
- Modify: `src/ai_analyzer.py:302-317` (`_build_title_context`)
- Modify: `src/resume_validator.py:228-268` (`_validate_titles`)
- Modify: `tests/test_ai_analyzer.py:358-384` (TestTitleContextPerSection)

**Step 1: Write the failing test**

In `tests/test_ai_analyzer.py`, rewrite `TestTitleContextPerSection`:

```python
class TestTitleContextPerSection:
    """Title context reads from work_experience[key].titles (single source of truth)."""

    def test_title_context_reads_from_work_experience(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._parsed_bullets = {
            'active_sections': {
                'experience_keys': ['glp_technology', 'baiquan_investment'],
            },
            'work_experience': {
                'glp_technology': {
                    'company': 'GLP Technology',
                    'titles': {
                        'default': 'Senior Data Engineer',
                        'data_scientist': 'Senior Data Scientist',
                        'ml_engineer': 'Senior Data Scientist',
                    },
                },
                'baiquan_investment': {
                    'company': 'BQ Investment',
                    'titles': {
                        'default': 'Quantitative Researcher',
                        'data_engineer': 'Quantitative Developer',
                    },
                },
            },
        }

        context = analyzer._build_title_context()

        assert "GLP Technology" in context
        assert "Senior Data Engineer" in context
        assert "Senior Data Scientist" in context
        assert "BQ Investment" in context
        assert "Quantitative Developer" in context

    def test_title_context_empty_when_no_titles(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._parsed_bullets = {
            'active_sections': {'experience_keys': []},
            'work_experience': {},
        }

        context = analyzer._build_title_context()

        assert "most relevant title" in context.lower()
```

Run: `pytest tests/test_ai_analyzer.py::TestTitleContextPerSection -v`
Expected: FAIL (old implementation reads `self._title_options`, not `self._parsed_bullets`)

**Step 2: Rewrite `_build_title_context()`**

In `src/ai_analyzer.py`, replace `_build_title_context()` (lines 302-317):

```python
def _build_title_context(self) -> str:
    """Build dynamic title options context from work_experience[].titles."""
    active = self._parsed_bullets.get('active_sections', {})
    exp_keys = active.get('experience_keys', self.DEFAULT_EXPERIENCE_KEYS)
    work_exp = self._parsed_bullets.get('work_experience', {})

    lines = ["Choose the title for each experience that BEST matches the JD:"]
    found_any = False
    for key in exp_keys:
        data = work_exp.get(key, {})
        titles = data.get('titles', {})
        if not isinstance(titles, dict) or not titles:
            continue
        company_name = data.get('company', key.replace('_', ' ').title())
        unique_titles = list(dict.fromkeys(titles.values()))
        title_list = [f'"{t}"' for t in unique_titles]
        lines.append(f"  - {company_name}: {', '.join(title_list)}")
        found_any = True

    if not found_any:
        return "Choose the most relevant title for each experience."
    return '\n'.join(lines)
```

**Step 3: Update `ResumeValidator._validate_titles()`**

In `src/resume_validator.py`, the validator reads `self._title_options` at line 231. After removing `title_options` from YAML, this returns `{}` and validation is skipped. We need to rebuild it from work_experience.

Replace `_load_config()` (lines 82-101) to also extract titles from work_experience:

```python
def _load_config(self, lib_path: Path):
    """Load skill_tiers, title options, bio_constraints, allowed categories from bullet_library.yaml."""
    if not lib_path.exists():
        print(f"[CRITICAL] bullet_library.yaml not found at {lib_path} — ALL resumes will be REJECTED!")
        print(f"[CRITICAL] Restore bullet_library.yaml to enable resume validation and generation.")
        self._skill_tiers = {}
        self._title_options = {}
        self._bio_constraints = {}
        self._allowed_categories = []
        self._library_loaded = False
        return

    with open(lib_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}

    self._skill_tiers = data.get('skill_tiers', {})
    self._bio_constraints = data.get('bio_constraints', {})
    self._allowed_categories = data.get('allowed_skill_categories', [])
    self._library_loaded = True

    # Build title_options from work_experience[].titles (single source of truth)
    self._title_options = {}
    for key, exp_data in data.get('work_experience', {}).items():
        if isinstance(exp_data, dict) and 'titles' in exp_data:
            self._title_options[key] = exp_data['titles']
```

**Step 4: Delete `title_options` from bullet_library.yaml**

Remove lines 543-564 (the entire `title_options:` top-level block).

**Step 5: Run tests**

Run: `pytest tests/test_ai_analyzer.py::TestTitleContextPerSection tests/test_template_registry.py -v`
Expected: All pass

**Step 6: Commit**

```bash
git add assets/bullet_library.yaml src/ai_analyzer.py src/resume_validator.py tests/test_ai_analyzer.py
git commit -m "consolidate title_options into work_experience.titles (single source of truth)"
```

---

### Task 4: Trim domain_claims + elevate C1 brief in C2 prompt

**Files:**
- Modify: `assets/bullet_library.yaml` (bio_builder.domain_claims)
- Modify: `config/ai_config.yaml` (prompts.tailor — task section)
- Modify: `src/ai_analyzer.py:673-750` (`_build_tailor_prompt`)

**Step 1: Trim domain_claims in bullet_library.yaml**

In `assets/bullet_library.yaml`, in `bio_builder.domain_claims`:

- Delete `anomaly_detection` entry (lines ~608-610)
- Delete `streaming_data` entry (lines ~629-631)
- Delete `data_governance` entry (lines ~632-634)
- Update `data_pipelines.text` from `"scalable data pipelines and ETL systems"` to `"scalable data pipelines and data platform engineering"`

Result: 10 domain_claims (was 13).

**Step 2: Elevate C1 brief in C2 prompt template**

In `config/ai_config.yaml`, replace the `## C1 Analysis Context` + `## Your Task` sections (lines 191-206) with:

```yaml
    ## Your Task
    **Strategic angle (from C1 evaluation, score {c1_score}/10 — {c1_recommendation}):**
    - Hook: {c1_hook}
    - Key angle: {c1_key_angle}
    - Gap to mitigate: {c1_gap_mitigation}
    - Company connection: {c1_company_connection}
    If no brief is available, infer the strongest angle from the JD and score.

    **Tailor the resume** to execute this angle:
    - MUST select 2-3 different work experiences from different companies
    - Select 1-3 projects based on JD relevance
    - Select bullets BY THEIR ID (shown in [square brackets] in the library above)
    - Provide 4-6 skill categories from the allowed list
    - Focus on RELEVANCE — use the brief's key_angle and hook to guide narrative choices
```

**Step 3: Update `_build_tailor_prompt()` to parse brief fields individually**

In `src/ai_analyzer.py`, `_build_tailor_prompt()`, replace the C1 context extraction (lines 711-722):

```python
# Extract C1 context — parse brief fields individually for structured prompt injection
c1_score = analysis.get('ai_score', 0)
c1_recommendation = analysis.get('recommendation', 'UNKNOWN')
c1_reasoning_raw = analysis.get('reasoning', '')

c1_hook = 'N/A'
c1_key_angle = 'N/A'
c1_gap_mitigation = 'None identified'
c1_company_connection = 'None'
try:
    reasoning_data = json.loads(c1_reasoning_raw)
    brief = reasoning_data.get('application_brief', {})
    if isinstance(brief, dict):
        c1_hook = brief.get('hook') or 'N/A'
        c1_key_angle = brief.get('key_angle') or 'N/A'
        c1_gap_mitigation = brief.get('gap_mitigation') or 'None identified'
        c1_company_connection = brief.get('company_connection') or 'None'
except (json.JSONDecodeError, TypeError):
    pass
```

And update the `.format()` call to include the new variables (replacing `c1_reasoning` and `c1_brief`):

```python
prompt_body = prompt_template.format(
    bullet_library=bullet_lib_safe,
    job_title=job_title,
    job_company=job_company,
    job_description=jd_safe,
    c1_score=c1_score,
    c1_recommendation=c1_recommendation,
    c1_hook=c1_hook.replace('{', '{{').replace('}', '}}'),
    c1_key_angle=c1_key_angle.replace('{', '{{').replace('}', '}}'),
    c1_gap_mitigation=c1_gap_mitigation.replace('{', '{{').replace('}', '}}'),
    c1_company_connection=c1_company_connection.replace('{', '{{').replace('}', '}}'),
    skill_context=skill_ctx_safe,
    title_context=title_ctx_safe,
    bio_constraints=bio_cstr_safe,
    bio_allowed_titles_list=bio_titles_str,
    bio_domain_claims_list=domain_claims_str,
    allowed_skill_categories_list=cat_str,
)
```

Remove the old `c1_reasoning_safe` and `c1_brief_safe` variables.

**Step 4: Run tests**

Run: `pytest tests/test_ai_analyzer.py -x -q`
Expected: All pass

**Step 5: Commit**

```bash
git add assets/bullet_library.yaml config/ai_config.yaml src/ai_analyzer.py
git commit -m "trim 3 overlapping domain_claims, elevate C1 brief in C2 prompt"
```

---

### Task 5: Generate C2 candidate summary dynamically

**Files:**
- Modify: `src/ai_analyzer.py` (new method `_build_candidate_summary`)
- Modify: `config/ai_config.yaml` (prompts.tailor — replace hardcoded profile)
- Create test: `tests/test_ai_analyzer.py` (new test class)

**Step 1: Write the failing test**

In `tests/test_ai_analyzer.py`, add:

```python
class TestCandidateSummary:
    """C2 candidate summary is generated from bullet_library, not hardcoded."""

    def test_summary_includes_education_and_certification(self):
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer.__new__(AIAnalyzer)
        analyzer._parsed_bullets = {
            'education': {
                'master': {
                    'degree': 'M.Sc. in Artificial Intelligence',
                    'school': 'VU Amsterdam',
                    'thesis': 'Uncertainty Quantification in Deep RL',
                },
                'certification': 'Databricks Certified Data Engineer Professional (2026)',
            },
            'active_sections': {
                'experience_keys': ['glp_technology'],
            },
            'work_experience': {
                'glp_technology': {
                    'company': 'GLP Technology',
                    'titles': {'default': 'Senior Data Engineer'},
                    'verified_bullets': [
                        {'id': 'glp_founding_member', 'content': 'Joined as founding data engineer...', 'status': 'active'},
                    ],
                },
            },
            'skill_tiers': {
                'verified': {
                    'languages': ['Python (Expert)', 'SQL (Expert)', 'Bash'],
                },
            },
        }

        summary = analyzer._build_candidate_summary()

        assert 'M.Sc. in Artificial Intelligence' in summary
        assert 'VU Amsterdam' in summary
        assert 'Databricks Certified' in summary
        assert 'GLP Technology' in summary
        assert 'Senior Data Engineer' in summary
        assert 'Python' in summary
```

Run: `pytest tests/test_ai_analyzer.py::TestCandidateSummary -v`
Expected: FAIL (`_build_candidate_summary` doesn't exist)

**Step 2: Implement `_build_candidate_summary()`**

In `src/ai_analyzer.py`, add after `_build_bio_constraints()`:

```python
def _build_candidate_summary(self) -> str:
    """Generate candidate summary from bullet_library data (replaces hardcoded profile)."""
    edu = self._parsed_bullets.get('education', {})
    master = edu.get('master', {})
    cert = edu.get('certification', '')

    lines = ["## Candidate Profile"]
    lines.append(f"Education: {master.get('degree', 'M.Sc.')} from {master.get('school', 'VU Amsterdam')}")
    if master.get('thesis'):
        lines.append(f"Thesis: {master['thesis']}")
    if cert:
        lines.append(f"Certification: {cert}")

    # Key experiences
    active = self._parsed_bullets.get('active_sections', {})
    exp_keys = active.get('experience_keys', self.DEFAULT_EXPERIENCE_KEYS)
    work_exp = self._parsed_bullets.get('work_experience', {})
    exp_lines = []
    for key in exp_keys:
        data = work_exp.get(key, {})
        if not isinstance(data, dict):
            continue
        company = data.get('company', data.get('display_name', key))
        title = data.get('titles', {}).get('default', '')
        if company and title:
            exp_lines.append(f"{title} at {company}")
    if exp_lines:
        lines.append(f"Experience: {'; '.join(exp_lines)}")

    # Core skills
    verified = self._parsed_bullets.get('skill_tiers', {}).get('verified', {})
    lang_skills = verified.get('languages', [])
    if lang_skills:
        lines.append(f"Key Skills: {', '.join(lang_skills)}")

    return '\n'.join(lines)
```

**Step 3: Update C2 prompt template**

In `config/ai_config.yaml`, replace the hardcoded `## Candidate Profile` section (lines 167-179) with the placeholder:

```yaml
    {candidate_summary}
```

**Step 4: Wire it up in `_build_tailor_prompt()`**

In `src/ai_analyzer.py`, in `_build_tailor_prompt()`, add before the `.format()` call:

```python
candidate_summary = self._build_candidate_summary()
candidate_summary_safe = candidate_summary.replace('{', '{{').replace('}', '}}')
```

Add `candidate_summary=candidate_summary_safe` to the `.format()` arguments.

**Step 5: Run tests**

Run: `pytest tests/test_ai_analyzer.py -x -q`
Expected: All pass

**Step 6: Commit**

```bash
git add src/ai_analyzer.py config/ai_config.yaml tests/test_ai_analyzer.py
git commit -m "generate C2 candidate summary dynamically from bullet_library"
```

---

### Task 6: Add course selection to C2 output + renderer

**Files:**
- Modify: `src/ai_analyzer.py:70-170` (`_load_bullet_library` — add courses section)
- Modify: `config/ai_config.yaml` (prompts.tailor — add courses to output schema + instructions)
- Modify: `src/resume_renderer.py:75-124` (`_build_base_context`, `_format_coursework`)
- Add tests in `tests/test_ai_analyzer.py` and `tests/test_resume_renderer_full_customize_only.py`

**Step 1: Write the failing test for coursework filtering**

In `tests/test_resume_renderer_full_customize_only.py`, add:

```python
def test_format_coursework_filters_by_selected_ids():
    from src.resume_renderer import ResumeRenderer
    master = {
        'courses': [
            {'id': 'deep_learning', 'name': 'Deep Learning', 'grade': '9.5'},
            {'id': 'multi_agent_systems', 'name': 'Multi-Agent Systems', 'grade': '9.5'},
            {'id': 'nlp', 'name': 'NLP', 'grade': '9.0'},
        ]
    }
    selected = ['deep_learning', 'nlp']

    result = ResumeRenderer._format_coursework(master, selected_courses=selected)

    assert 'Deep Learning (9.5)' in result
    assert 'NLP (9.0)' in result
    assert 'Multi-Agent' not in result


def test_format_coursework_all_when_no_selection():
    from src.resume_renderer import ResumeRenderer
    master = {
        'courses': [
            {'id': 'deep_learning', 'name': 'Deep Learning', 'grade': '9.5'},
            {'id': 'nlp', 'name': 'NLP', 'grade': '9.0'},
        ]
    }

    result = ResumeRenderer._format_coursework(master, selected_courses=None)

    assert 'Deep Learning (9.5)' in result
    assert 'NLP (9.0)' in result
```

Run: `pytest tests/test_resume_renderer_full_customize_only.py -v`
Expected: FAIL (signature doesn't accept `selected_courses`)

**Step 2: Update `_format_coursework()`**

In `src/resume_renderer.py`, replace `_format_coursework` (lines 119-124):

```python
@staticmethod
def _format_coursework(master: dict, selected_courses: list = None) -> str:
    courses = master.get('courses', [])
    if not courses:
        return master.get('coursework', '')
    if selected_courses is not None:
        courses = [c for c in courses if isinstance(c, dict) and c.get('id') in selected_courses]
    return ', '.join(f"{c['name']} ({c['grade']})" for c in courses if isinstance(c, dict) and 'name' in c and 'grade' in c)
```

**Step 3: Update `_build_context()` to pass selected_courses through**

In `src/resume_renderer.py`, in `_build_context()` (line 311), add after projects:

```python
# Coursework selection (AI-controlled)
selected_courses = tailored.get('selected_courses')
if selected_courses is not None:
    master = self.bullet_library.get('education', {}).get('master', {})
    context['edu_master_coursework'] = self._format_coursework(master, selected_courses=selected_courses)

# Bachelor thesis visibility (AI-controlled)
if tailored.get('show_bachelor_thesis') is False:
    context['edu_bachelor_thesis'] = ''
```

**Step 4: Add courses to bullet library prompt format**

In `src/ai_analyzer.py`, in `_load_bullet_library()`, add after the projects section (before line 163):

```python
# Coursework
edu = self._parsed_bullets.get('education', {})
master_courses = edu.get('master', {}).get('courses', [])
if master_courses:
    sections.append("\n## COURSEWORK (select courses most relevant to the JD)")
    sections.append("Master's courses (all graded 9.0+):")
    for c in master_courses:
        if isinstance(c, dict) and 'id' in c:
            relevance = ', '.join(c.get('relevance', []))
            sections.append(f"  - [{c['id']}] {c.get('name', '')} ({c.get('grade', '')}) — relevance: {relevance}")
```

**Step 5: Add to C2 output schema + instructions**

In `config/ai_config.yaml`, in the C2 output JSON example, add after `"skills"`:

```yaml
        "selected_courses": ["deep_learning", "data_mining", "nlp"],
        "show_bachelor_thesis": false,
        "show_career_note": false
```

And add an instruction block:

```yaml
    ### COURSEWORK SELECTION
    - Select master's courses most relevant to the JD (by ID from COURSEWORK section)
    - If all courses are relevant, include all
    - show_bachelor_thesis: set true only if JD specifically relates to web systems or Java

    ### CAREER NOTE
    - show_career_note: set false if Independent Quantitative Researcher is included as an experience (the 2019-2023 period is covered)
    - set true only if there is a visible chronological gap not covered by any included experience
```

**Step 6: Run tests**

Run: `pytest tests/ -x -q`
Expected: All pass

**Step 7: Commit**

```bash
git add src/ai_analyzer.py src/resume_renderer.py config/ai_config.yaml tests/test_resume_renderer_full_customize_only.py
git commit -m "add course selection + career_note AI control to C2 pipeline"
```

---

### Task 7: Final validation — full test suite + manual prompt review

**Files:**
- All modified files from Tasks 1-6

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All pass with no warnings related to our changes.

**Step 2: Verify prompt token reduction**

Run a quick Python snippet to measure prompt sizes:

```bash
python -c "
from src.ai_analyzer import AIAnalyzer
import json, sys

a = AIAnalyzer.__new__(AIAnalyzer)
a.config = a._load_config()
a.bullet_library = a._load_bullet_library()
a.registry = {'templates': {}}

# Rough char count (4 chars ≈ 1 token)
c2_prompt = a.config.get('prompts', {}).get('tailor', '')
print(f'C2 template chars: {len(c2_prompt)}')
print(f'Bullet library chars: {len(a.bullet_library)}')
print(f'Approx C2 total tokens: ~{(len(c2_prompt) + len(a.bullet_library)) // 4}')
"
```

**Step 3: Review the actual C1 and C2 prompt templates for consistency**

Read through both prompt templates in `config/ai_config.yaml` end-to-end and verify:
- No orphan `{placeholder}` variables (all have matching `.format()` args)
- No references to removed fields (adapt_instructions, c1_reasoning, c1_brief)
- No references to removed domain_claims (anomaly_detection, streaming_data, data_governance)
- Output schema matches what code expects to parse

**Step 4: Commit any fixups**

```bash
git add -A
git commit -m "final cleanup: fix any orphan references from prompt optimization"
```
