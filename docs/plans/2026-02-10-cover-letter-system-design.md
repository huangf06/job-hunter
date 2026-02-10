# Cover Letter System Design

**Date:** 2026-02-10
**Status:** Approved

## Overview

Extend Job Hunter v2.0 pipeline to auto-generate cover letters alongside resumes. The system reuses existing `job_analysis` results and `bullet_library.yaml` evidence, making a focused AI call to produce tailored cover letters.

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Trigger mode | Auto + override | Auto-generate with resume; `--requirements` for custom |
| Content approach | Semi-structured (AI writes prose, claims anchored to evidence_ids) | Natural prose, but verifiable claims |
| Output formats | Standard PDF (~300 words) + Short TXT (~150 words) | Covers PDF upload + text box paste |
| AI call strategy | Separate module, reuses job_analysis | Clean separation, cheap focused call |
| Content library | No — lightweight config only | Cover letters must feel unique, not formulaic |
| Length limits | Soft guidance, not hard validation | ~300 / ~150 words, flexible |

## Architecture

```
Existing Pipeline (unchanged):
  Job -> Filter -> Rule Score -> AI Analyze -> job_analysis table
                                                    |
                                    +---------------+---------------+
                                    v                               v
                             Resume Renderer          Cover Letter Generator (NEW)
                             (existing)               (src/cover_letter_generator.py)
                                    |                               |
                                    v                               v
                             resume PDF                  cover_letter_spec JSON
                                                                    |
                                                                    v
                                                        Cover Letter Renderer (NEW)
                                                        (src/cover_letter_renderer.py)
                                                                    |
                                                        +-----------+-----------+
                                                        v                       v
                                                  PDF (standard)           TXT (short)
```

## New Files

```
src/
  cover_letter_generator.py    # AI call -> cover_letter_spec JSON
  cover_letter_renderer.py     # Spec -> prose -> HTML/PDF + TXT

assets/
  cover_letter_config.yaml     # Angles, hooks, closers, tone rules

templates/
  cover_letter_template.html   # PDF template
```

## Cover Letter Spec (AI Output)

The AI writes actual prose, with `evidence_ids` anchoring factual claims to `bullet_library.yaml`:

```json
{
  "standard": {
    "opening_prose": "Having followed Stripe's evolution from payment processor to full financial infrastructure platform, I was excited to see the Data Engineer opening on the Pipeline team.",
    "body_paragraphs": [
      {
        "prose": "At GLP, I built the data engineering backbone for a $2B real estate portfolio from the ground up, designing pipelines that processed thousands of transactions daily. This experience directly parallels your need for engineers who can own end-to-end data infrastructure at scale.",
        "evidence_ids": ["glp_founding_member", "glp_data_engineer"]
      },
      {
        "prose": "I also bring depth in real-time streaming architectures — at my recent project I implemented Delta Lake streaming pipelines with sub-minute latency and automated quality gates, the same class of challenges your team describes in the job posting.",
        "evidence_ids": ["lakehouse_streaming", "lakehouse_quality"]
      }
    ],
    "closer_prose": "I would welcome the opportunity to discuss how my experience building fault-tolerant data platforms can contribute to Stripe's pipeline team. I look forward to connecting.",
    "narrative_angle": "builder_to_scaler"
  },
  "short": {
    "prose": "As a data engineer who built pipeline infrastructure for a $2B portfolio at GLP and implemented real-time streaming with Delta Lake, I'm excited about the Data Engineer role at Stripe. My experience in end-to-end data platform ownership directly maps to your team's needs. I'd love to discuss further.",
    "evidence_ids": ["glp_founding_member", "glp_data_engineer", "lakehouse_streaming"]
  }
}
```

## Cover Letter Config (`assets/cover_letter_config.yaml`)

```yaml
narrative_angles:
  builder_to_scaler: "From building to scaling"
  domain_expert: "Deep domain expertise"
  cross_functional: "Unique cross-domain blend"
  growth_trajectory: "Career trajectory alignment"
  problem_solver: "Proven problem solver"

opening_hooks:
  company_mission: "Lead with something specific about the company"
  role_alignment: "Lead with why this specific role fits"
  industry_passion: "Lead with genuine interest in the domain"
  shared_values: "Lead with alignment on values/approach"

closer_types:
  eager_company: "Express specific enthusiasm for this company"
  seeking_impact: "Emphasize desire to create impact"
  conversation: "Simple call-to-action for next steps"

tone_guidelines:
  - "Confident but not arrogant"
  - "Specific, never generic"
  - "Show, don't tell - back every claim with evidence_ids"
  - "No filler phrases: passionate, hard-working, team player"

banned_phrases:
  - "I am writing to apply for"
  - "I believe I would be a great fit"
  - "Thank you for your consideration"
  - "Please find attached my resume"

length_guidance:
  standard: "~300 words"
  short: "~150 words"
```

## Cover Letter Best Practices

A great cover letter answers three questions:

| Question | Purpose |
|----------|---------|
| **Why this company?** | Show you researched them, not mass-applying |
| **Why you for this role?** | Connect YOUR specific story to THEIR specific needs |
| **Why now?** | Mutual timing, career trajectory alignment |

Key principles:
- Do NOT repeat resume bullets verbatim — paraphrase into narrative
- Every factual claim anchored to an `evidence_id`
- Company-specific statements derived from JD text, not invented
- Standard: 2 body paragraphs max; Short: single paragraph

## AI Prompt Design

### Input context (reuses existing data)

```
- Job: title, company, description (from jobs table)
- Analysis: scores, reasoning, tailored_resume (from job_analysis table)
- Evidence pool: bullet_library.yaml (same [id] text format as resume prompt)
- Config: narrative angles, hooks, closers, tone rules
- Custom requirements: user-provided (optional, nullable)
```

### One call, two outputs

The AI generates both standard and short specs in a single response, ensuring consistency between versions.

### Prompt rules

1. `evidence_ids` MUST exist in the bullet library
2. `company_insight` MUST be derived from the job description
3. `company_connection` MUST link evidence to specific JD requirements
4. Do NOT repeat resume bullet text verbatim — paraphrase into narrative
5. Pick the narrative angle that best matches this specific role
6. Standard: ~300 words, Short: ~150 words (soft guidance)

## Validation

| Check | Blocking? |
|-------|-----------|
| All `evidence_ids` exist in `bullet_library.yaml` | Yes |
| No skills mentioned outside `skill_tiers` | Yes |
| No `banned_phrases` present | Yes (auto-fix) |
| `narrative_angle` in whitelist | Yes |
| Company name matches job record | Yes |
| Length within guidance | No (soft) |

## Database: `cover_letters` table

```sql
CREATE TABLE cover_letters (
    id INTEGER PRIMARY KEY,
    job_id TEXT REFERENCES jobs(job_id),
    spec_json TEXT,
    custom_requirements TEXT,
    standard_text TEXT,
    short_text TEXT,
    html_path TEXT,
    pdf_path TEXT,
    tokens_used INTEGER,
    created_at TIMESTAMP,
    UNIQUE(job_id)
);
```

## CLI Integration (`job_pipeline.py`)

```bash
# Auto-generate with resume (existing --generate adds cover letters)
python scripts/job_pipeline.py --generate

# Generate cover letter only for a specific job
python scripts/job_pipeline.py --cover-letter JOB_ID

# With custom requirements from application page
python scripts/job_pipeline.py --cover-letter JOB_ID --requirements "Explain your motivation..."

# Regenerate
python scripts/job_pipeline.py --cover-letter JOB_ID --requirements "..." --regen
```

## File Output

```
ready_to_send/
  20260210_Stripe/
    Fei_Huang_Resume.pdf
    Fei_Huang_Cover_Letter.pdf      # NEW
    Fei_Huang_Cover_Letter.txt      # NEW (for paste)
```

## Module API

### `CoverLetterGenerator`

```python
class CoverLetterGenerator:
    def __init__(self, config_path="config/ai_config.yaml"):
        # Load AI config, bullet library, cover letter config

    def generate(self, job_id, custom_requirements=None):
        # 1. Load job + job_analysis from DB
        # 2. Build prompt (job context + analysis + evidence pool + config)
        # 3. AI call -> cover_letter_spec JSON
        # 4. Validate spec (evidence_ids, angle, banned phrases)
        # 5. Store in cover_letters table
        # Returns: cover_letter_spec dict
```

### `CoverLetterRenderer`

```python
class CoverLetterRenderer:
    def __init__(self, config_path="config/ai_config.yaml"):
        # Load config, template

    def render(self, job_id):
        # 1. Load spec from cover_letters table
        # 2. Assemble standard text (prose from spec, formatted)
        # 3. Assemble short text
        # 4. Render HTML -> PDF (Playwright)
        # 5. Write TXT
        # 6. Copy to ready_to_send/
        # Returns: {pdf_path, txt_path, submit_dir}
```

## Implementation Order

1. Create `assets/cover_letter_config.yaml`
2. Create `templates/cover_letter_template.html`
3. Add `cover_letters` table to `src/db/job_db.py`
4. Implement `src/cover_letter_generator.py` (AI call + validation)
5. Implement `src/cover_letter_renderer.py` (assembly + PDF/TXT)
6. Integrate CLI args into `scripts/job_pipeline.py`
7. Test with a real job from the database
