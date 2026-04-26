# AI Evaluation Pipeline Audit — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restore AI evaluation pipeline's interview conversion rate by reverting to v3.0-era prompt simplicity and restoring interview-proven bullet content.

**Architecture:** Three parallel changes to `assets/bullet_library.yaml` (content merge), `config/ai_config.yaml` (C2 prompt simplification + config fix), then a validation run on a historical interview-winning job to confirm output quality.

**Tech Stack:** YAML config edits, Python CLI verification

**Design doc:** `docs/plans/2026-04-24-ai-evaluation-audit-design.md`

---

### Task 1: Restore 3 interview-proven bullet texts in bullet library

**Files:**
- Modify: `assets/bullet_library.yaml:257-261` (bq_de_backtest_infra)
- Modify: `assets/bullet_library.yaml:456-463` (expedia_ltr)
- Modify: `assets/bullet_library.yaml:683-687` (job_hunter_system)

**Step 1: Restore `bq_de_backtest_infra` to v3.0 text**

Find (line 261):
```yaml
        content: "Architected event-driven backtesting framework (Python + MATLAB) supporting strategy simulation, walk-forward validation, and 15+ performance metrics — adopted as core research infrastructure by the investment team."
```
Replace with:
```yaml
        content: "Architected event-driven backtesting framework supporting strategy simulation, walk-forward validation, and performance attribution — adopted as core research infrastructure by the investment team."
```

**Step 2: Restore `expedia_ltr` to v3.0 text**

Find (lines 460-463):
```yaml
        content: "Built hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered temporal, behavioral, and aggregation features (price normalization, competitor rates, estimated position); achieved NDCG@5 = 0.392 on Kaggle evaluation."

        # Alternative version with more technical detail (for ML-heavy roles)
        # content: "Developed learning-to-rank hotel recommendation system using LightGBM LambdaRank on 4.96M Expedia search records; engineered 50+ features (temporal, price normalization by search_id, competitor rates, estimated position) and optimized label gains [0,1,5] for click/booking prediction; achieved NDCG@5 = 0.392 on Kaggle test set, outperforming XGBoost+SVD ensemble (0.374)."
```
Replace with:
```yaml
        content: "Developed hotel recommendation system using learning-to-rank models (LightGBM, XGBoost+SVD) on 4.9M search records; engineered temporal, behavioral, and user-preference features for ranking optimization; achieved NDCG@5 = 0.392, placing top 5% in Kaggle competition."
```

**Step 3: Restore `job_hunter_system` to v3.0 text**

Find (line 687):
```yaml
        content: "Built a stateful job search operations platform orchestrating incremental job ingestion, rule-based filtering, AI-assisted evaluation, and application tracking; backed by SQLite with Turso embedded-replica sync for durable state across local runs and CI automation."
```
Replace with:
```yaml
        content: "Built end-to-end job application pipeline leveraging LLM APIs (Claude) for resume personalization; designed multi-stage processing (web scraping via Playwright, rule-based filtering, AI scoring, Jinja2 template rendering to PDF) with SQLite backend, YAML-driven configuration, and configurable quality gates."
```

**Step 4: Commit**

```bash
git add assets/bullet_library.yaml
git commit -m "fix(bullets): restore 3 interview-proven v3.0 bullet texts"
```

---

### Task 2: Re-add 2 deleted interview-proven bullets

**Files:**
- Modify: `assets/bullet_library.yaml` (eleme section, ~line 384; projects section, ~line 672)

**Step 1: Add `eleme_sql_reporting` after `eleme_user_segmentation` (after line 384)**

Insert after the `eleme_user_segmentation` bullet block:
```yaml

      - id: eleme_sql_reporting
        status: active
        tags: [sql, hadoop, hive, reporting]
        narrative_role: optional
        content: "Optimized complex SQL queries on Hadoop/Hive for cross-functional stakeholders, cutting reporting turnaround time by 30%."
```

**Step 2: Add `obama_tts` project section before the `lifeos` section (before line 660)**

Insert before the `lifeos` section comment:
```yaml
  # ---------------------------------------------------------------------------
  # VOICE CLONING SYSTEM (XTTS v2)
  # ---------------------------------------------------------------------------
  obama_tts:
    title: "Voice Cloning System (XTTS v2)"
    institution: "Personal Project"
    period: "2025"

    verified_bullets:

      - id: obama_tts_voice_cloning
        status: active
        tags: [llm, voice-cloning, hpc, deployment]
        narrative_role: optional
        content: "Fine-tuned Coqui XTTS v2 voice cloning model with hybrid deployment architecture: GPU training on Snellius HPC cluster via SLURM job arrays, CPU inference served through FastAPI REST API and Gradio web UI; implemented 5 configurable speaking styles for text-to-speech generation."

```

**Step 3: Commit**

```bash
git add assets/bullet_library.yaml
git commit -m "fix(bullets): restore 2 deleted interview-proven bullets (eleme_sql_reporting, obama_tts)"
```

---

### Task 3: Simplify C2 prompt — delete narrative and page balance rules

**Files:**
- Modify: `config/ai_config.yaml:329-445` (C2 tailor prompt rules section)

**Step 1: Replace CONTENT SELECTION PRINCIPLE (lines 329-333)**

Find:
```yaml
    ### CONTENT SELECTION PRINCIPLE
    Select content that builds the strongest possible narrative for THIS specific job.
    Quality over quantity — 3 well-chosen bullets that tell a coherent story beat 5 relevant-but-disconnected bullets.
    The resume can be 1-2 pages. Sections order: Education → Projects → Experience → Skills → Interests.
    Education and Interests are static. You control: bio (optional), experiences, projects, skills.
```
Replace with:
```yaml
    ### CONTENT SELECTION PRINCIPLE
    Include ALL content that is relevant to the JD. Exclude content that doesn't strengthen the application.
    The resume can be 1-2 pages — do NOT artificially cut content to fit 1 page.
    Sections order: Education → Projects → Experience → Skills → Interests.
    Education and Interests are static. You control: bio (optional), experiences, projects, skills.
```

**Step 2: Delete PAGE BALANCE section (lines 356-360)**

Delete entirely:
```yaml
    ### PAGE BALANCE (CRITICAL)
    The resume uses a two-column layout: Experience on the left, Education/Projects/Skills on the right.
    Both columns MUST be roughly balanced in height. The right column tends to overflow because it
    contains multiple sections (Education, Certification, Projects, Skills, Languages).
    Be CONSERVATIVE with right-column content (projects, skill categories).

```

**Step 3: Replace BULLET DISTRIBUTION (lines 362-369)**

Find:
```yaml
    ### BULLET DISTRIBUTION (GUIDANCE, NOT HARD LIMITS)
    Include bullets based on JD relevance. Typical ranges:
    - Most relevant experience: 2-4 bullets
    - Second experience: 2-3 bullets
    - Third experience (if included): 1-2 bullets
    - Main project: 2-3 bullets
    - Second project: 1-2 bullets
    - Total project bullets across ALL projects: max 5
```
Replace with:
```yaml
    ### BULLET DISTRIBUTION (GUIDANCE, NOT HARD LIMITS)
    Include bullets based on JD relevance. Typical ranges:
    - Most relevant experience: 2-4 bullets
    - Second experience: 2-3 bullets
    - Third experience (if included): 1-2 bullets
    - Main project: 2-4 bullets (include all that are relevant)
    - Second project: 1-2 bullets
    - Third project (if relevant): 1 bullet
```

**Step 4: Delete NARRATIVE COMPOSITION section (lines 371-402)**

Delete entirely — the full block from `### NARRATIVE COMPOSITION` through the end of `#### Cross-Section Strategy`:
```yaml
    ### NARRATIVE COMPOSITION (CRITICAL FOR RESUME QUALITY)

    A hiring manager reads each experience section for 10-15 seconds. They ask:
    1. "Who was this person at this company?" → answered by the FIRST bullet
    2. "What's the most impressive thing they did?" → answered by the SECOND bullet
    3. "What else supports this?" → answered by remaining bullets

    Your bullet selection and ordering must answer these questions IN THIS ORDER.

    #### Narrative Roles
    Each bullet has a narrative_role tag shown in parentheses. Use these to compose sections:

    | Role | What it does | Where to place |
    |------|-------------|----------------|
    | context_setter | Establishes scope, seniority, why this matters | FIRST in section |
    | depth_prover | Technical crown jewel, interview hook | SECOND (or first if no context_setter) |
    | foundation | Engineering infrastructure powering the above | After depth_prover |
    | extension | System evolution, broader reach | Late in section |
    | breadth | Cross-functional, leadership | Last, only if space allows |

    Composition rules:
    1. Each section with 2+ bullets MUST lead with a context_setter or depth_prover — NEVER start with foundation or breadth
    2. NEVER select 2 bullets with the same narrative_role in one section
    3. If a RECOMMENDED SEQUENCE exists for this role type, you MUST use exactly those bullets in that order. Do not cherry-pick, reorder, or substitute. You may OMIT the last bullet(s) if space is tight, but the remaining bullets must stay in sequence order. If no sequence matches the target role, fall back to narrative_role ordering
    4. Vary sentence openings across bullets within a section — if one starts with "Built", the next MUST use a different verb pattern (not "Built/Developed/Engineered/Designed")

    #### Cross-Section Strategy
    Each experience section should contribute something UNIQUE to the overall resume:
    - The most JD-relevant experience gets 3-4 bullets and carries the narrative weight
    - Less relevant experiences get 1-2 bullets showing a different strength
    - Do NOT demonstrate the same skill/achievement across multiple sections
    - Together, all sections should cover: technical depth + engineering capability + business awareness

```

**Step 5: Change SKILLS FORMAT category count (line 405)**

Find:
```yaml
    - Provide 4-5 categories from this ALLOWED list ONLY:
```
Replace with:
```yaml
    - Provide 4-6 categories from this ALLOWED list ONLY:
```

**Step 6: Replace PROJECT SELECTION (lines 422-426)**

Find:
```yaml
    ### PROJECT SELECTION
    - Select 1-2 projects based on JD relevance (max 2 to maintain page balance)
    - For Data Engineer roles: prioritize Financial Data Lakehouse
    - For ML/DS roles: prioritize Thesis or Expedia
    - For NLP/AI roles: prioritize NLP Projects or Thesis
    - THESIS RULE: When including thesis_uq_rl, ALWAYS include thesis_noise_paradox (the original discovery) — do NOT only include thesis_uq_framework (measurement-only looks weak)
```
Replace with:
```yaml
    ### PROJECT SELECTION
    - Select 1-3 projects based on JD relevance
    - For Data Engineer roles: prioritize Financial Data Lakehouse
    - For ML/DS roles: prioritize Thesis or Expedia
    - For NLP/AI roles: prioritize NLP Projects or Thesis
    - Include a third project only if it adds clearly different skills
    - THESIS RULE: When including thesis_uq_rl, ALWAYS include thesis_noise_paradox (the original discovery) — do NOT only include thesis_uq_framework (measurement-only looks weak)
```

**Step 7: Replace OTHER RULES (lines 441-445)**

Find:
```yaml
    ### OTHER RULES
    1. Use ONLY bullet IDs from the provided bullet library - do not fabricate
    2. MUST include 2-3 different work experiences from different companies
    3. Select bullets that best match the JD requirements AND form a coherent narrative per section
    4. Prefer narrative composition over exhaustive coverage — omit a relevant bullet if it breaks the narrative flow
```
Replace with:
```yaml
    ### OTHER RULES
    1. Use ONLY bullet IDs from the provided bullet library - do not fabricate
    2. MUST include 2-3 different work experiences from different companies
    3. Select bullets that best match the JD requirements
    4. Include ALL relevant bullets for a position — do not cut for space
```

**Step 8: Commit**

```bash
git add config/ai_config.yaml
git commit -m "fix(prompt): simplify C2 tailor prompt — remove narrative rules, restore v3.0 selection philosophy"
```

---

### Task 4: Fix config — add missing project_keys and experience_keys

**Files:**
- Modify: `config/ai_config.yaml:41-61` (prompt_settings section)

**Step 1: Add `independent_investor` to experience_keys**

Find:
```yaml
  experience_keys:
    - glp_technology
    - baiquan_investment
    - eleme
    - henan_energy
```
Replace with:
```yaml
  experience_keys:
    - glp_technology
    - independent_investor
    - baiquan_investment
    - eleme
    - henan_energy
```

**Step 2: Add `deribit_options` and `obama_tts` to project_keys**

Find:
```yaml
  project_keys:
    - financial_data_lakehouse
    - thesis_uq_rl
    - nlp_projects
    - expedia_recommendation
    - ml4qs
    - graphsage_gnn
    - lifeos
    - job_hunter_automation
    - greenhouse_sensor_pipeline
    - evolutionary_robotics_research
    - sequence_analysis
    - deep_learning_fundamentals
```
Replace with:
```yaml
  project_keys:
    - financial_data_lakehouse
    - deribit_options
    - thesis_uq_rl
    - nlp_projects
    - expedia_recommendation
    - ml4qs
    - graphsage_gnn
    - obama_tts
    - lifeos
    - job_hunter_automation
    - greenhouse_sensor_pipeline
    - evolutionary_robotics_research
    - sequence_analysis
    - deep_learning_fundamentals
```

**Step 3: Commit**

```bash
git add config/ai_config.yaml
git commit -m "fix(config): add deribit_options, obama_tts to project_keys; independent_investor to experience_keys"
```

---

### Task 5: Verify — run existing tests

**Step 1: Run AI analyzer tests**

```bash
python -m pytest tests/test_ai_analyzer.py -v
```

Expected: All tests PASS. These tests use bullet IDs (`glp_founding_member`, `glp_decision_engine`, etc.) that still exist — only content text changed, not IDs.

**Step 2: Run bullet tracking tests**

```bash
python -m pytest tests/test_bullet_tracking.py -v
```

Expected: All tests PASS.

**Step 3: Verify bullet library loads without error**

```bash
python -c "from src.ai_analyzer import AIAnalyzer; a = AIAnalyzer(); print(f'Loaded {len(a.bullet_id_lookup)} bullet IDs'); assert 'eleme_sql_reporting' in a.bullet_id_lookup; assert 'obama_tts_voice_cloning' in a.bullet_id_lookup; assert 'deribit_options_system' in a.bullet_id_lookup; print('All new bullets accessible')"
```

Expected: `Loaded 5X bullet IDs` + `All new bullets accessible`

---

### Task 6: Validate — dry-run on historical interview-winning job

**Step 1: Build and inspect the C2 prompt for a known interview-winning job**

```bash
python -c "
from src.ai_analyzer import AIAnalyzer
a = AIAnalyzer()
job = a.db.get_job('3f7fe46fda8d')  # Sensorfact Senior Data Engineer (interview-winning)
from src.template_registry import select_template
code_decision = select_template(job['title'], a.registry)
prompt = a._build_tailor_prompt(job, {'ai_score': 7.0, 'recommendation': 'APPLY', 'reasoning': 'Strong DE match'})
print(f'Prompt length: {len(prompt)} chars')
# Verify no narrative composition rules in prompt
assert 'NARRATIVE COMPOSITION' not in prompt, 'NARRATIVE COMPOSITION still in prompt!'
assert 'PAGE BALANCE' not in prompt, 'PAGE BALANCE still in prompt!'
assert 'narrative_role' not in prompt.split('## Important Rules')[1] if '## Important Rules' in prompt else True, 'narrative_role in rules!'
assert 'Include ALL content' in prompt, 'Missing v3.0 content selection principle!'
print('Prompt structure verified: no narrative rules, v3.0 selection philosophy present')
"
```

Expected: Prompt structure verified message. No assertion errors.

**Step 2: Verify new bullets appear in prompt**

```bash
python -c "
from src.ai_analyzer import AIAnalyzer
a = AIAnalyzer()
job = a.db.get_job('3f7fe46fda8d')
prompt = a._build_tailor_prompt(job, {'ai_score': 7.0, 'recommendation': 'APPLY', 'reasoning': 'Strong DE match'})
for bid in ['eleme_sql_reporting', 'obama_tts_voice_cloning', 'deribit_options_system', 'indie_quant_research']:
    if bid in prompt:
        print(f'  OK: {bid} present in prompt')
    else:
        print(f'  MISSING: {bid} not in prompt')
"
```

Expected: All 4 bullet IDs present in prompt.

**Step 3: Commit verification results (no code change)**

No commit needed — this is a manual verification step.
