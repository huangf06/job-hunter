# Cover Letter System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add cover letter generation to the Job Hunter pipeline — auto-generate standard PDF + short TXT cover letters alongside resumes, with optional custom requirements override.

**Architecture:** New `CoverLetterGenerator` (AI call → structured spec) and `CoverLetterRenderer` (spec → HTML/PDF + TXT), following the same patterns as `AIAnalyzer` + `ResumeRenderer`. Reuses existing `job_analysis` data. New `cover_letters` DB table. CLI integrated into `job_pipeline.py`.

**Tech Stack:** Python 3, Anthropic SDK, Jinja2, Playwright (PDF), SQLite, PyYAML

**Design doc:** `docs/plans/2026-02-10-cover-letter-system-design.md`

---

### Task 1: Create cover letter config (`assets/cover_letter_config.yaml`)

**Files:**
- Create: `assets/cover_letter_config.yaml`

**Step 1: Create the config file**

```yaml
# =============================================================================
# Cover Letter Configuration
# =============================================================================
# Narrative components and tone rules for cover letter generation.
# AI picks from these whitelists; assembler validates against them.
# =============================================================================

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
  - "Show, don't tell — back every claim with evidence_ids"
  - "No filler phrases: passionate, hard-working, team player"
  - "Do NOT repeat resume bullet text verbatim — paraphrase into narrative"
  - "Company-specific statements must be derived from the job description"

banned_phrases:
  - "I am writing to apply for"
  - "I believe I would be a great fit"
  - "Thank you for your consideration"
  - "Please find attached my resume"
  - "I am confident that"
  - "passionate about"
  - "hard-working"
  - "team player"

length_guidance:
  standard: "~300 words"
  short: "~150 words"
```

**Step 2: Verify file loads correctly**

Run: `python -c "import yaml; d = yaml.safe_load(open('assets/cover_letter_config.yaml')); print(list(d.keys())); print(len(d['banned_phrases']), 'banned phrases')"`

Expected output: `['narrative_angles', 'opening_hooks', 'closer_types', 'tone_guidelines', 'banned_phrases', 'length_guidance']` and `8 banned phrases`

**Step 3: Commit**

```bash
git add assets/cover_letter_config.yaml
git commit -m "feat(cover-letter): add cover letter config with narrative angles, tone rules"
```

---

### Task 2: Create cover letter HTML template (`templates/cover_letter_template.html`)

**Files:**
- Create: `templates/cover_letter_template.html`
- Reference: `templates/base_template.html` (for consistent styling)

**Step 1: Create the template**

Create a professional cover letter template matching the resume's typography (Georgia serif, A4, same accent colors). The template should render:

- Candidate header (name, contact — same as resume)
- Date
- Greeting (Dear Hiring Manager / Dear [Company] Team)
- Body paragraphs (opening + body + closer)
- Sign-off with name

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ name }} - Cover Letter</title>
    <style>
:root {
    --primary-color: #1a1a1a;
    --secondary-color: #4a4a4a;
    --accent-color: #2c5282;
    --text-main: #1a1a1a;
    --text-muted: #555555;
    --link-color: #2c5282;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

@page { size: A4; margin: 0.75in 0.75in 0.75in 0.75in; }

body {
    font-family: Georgia, 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.5;
    color: var(--text-main);
    max-width: 8.27in;
    margin: 0 auto;
    padding: 0.75in;
    background: white;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

.header {
    margin-bottom: 20pt;
}

.name {
    font-size: 18pt;
    font-weight: bold;
    color: var(--primary-color);
    letter-spacing: 0.5pt;
    margin-bottom: 4pt;
}

.contact-info {
    font-size: 9.5pt;
    color: var(--text-muted);
    line-height: 1.5;
}

.contact-info a { color: var(--link-color); text-decoration: none; }

.date-line {
    margin-top: 20pt;
    margin-bottom: 20pt;
    font-size: 10.5pt;
    color: var(--text-muted);
}

.greeting {
    margin-bottom: 14pt;
    font-size: 11pt;
}

.body-paragraph {
    margin-bottom: 12pt;
    text-align: justify;
}

.sign-off {
    margin-top: 20pt;
}

.sign-off .closing {
    margin-bottom: 24pt;
}

.sign-off .signature {
    font-weight: bold;
}
    </style>
</head>
<body>
    <div class="header">
        <div class="name">{{ name }}</div>
        <div class="contact-info">
            {{ email }}
            {% if phone %} &middot; {{ phone }}{% endif %}
            {% if location %} &middot; {{ location }}{% endif %}
            <br>
            {% if linkedin_display %}<a href="{{ linkedin }}">{{ linkedin_display }}</a>{% endif %}
            {% if github_display %} &middot; <a href="{{ github }}">{{ github_display }}</a>{% endif %}
        </div>
    </div>

    <div class="date-line">{{ date }}</div>

    <div class="greeting">Dear {{ greeting }},</div>

    {% for paragraph in paragraphs %}
    <div class="body-paragraph">{{ paragraph }}</div>
    {% endfor %}

    <div class="sign-off">
        <div class="closing">Sincerely,</div>
        <div class="signature">{{ name }}</div>
    </div>
</body>
</html>
```

**Step 2: Verify template loads in Jinja2**

Run: `python -c "from jinja2 import Environment, FileSystemLoader; env = Environment(loader=FileSystemLoader('templates'), autoescape=True); t = env.get_template('cover_letter_template.html'); print('Template loaded OK, blocks:', list(t.blocks.keys()) if hasattr(t, 'blocks') else 'none')"`

Expected: `Template loaded OK`

**Step 3: Commit**

```bash
git add templates/cover_letter_template.html
git commit -m "feat(cover-letter): add cover letter HTML template"
```

---

### Task 3: Add `cover_letters` table + DB methods to `src/db/job_db.py`

**Files:**
- Modify: `src/db/job_db.py`

**Step 1: Add `CoverLetter` dataclass**

After the `AnalysisResult` dataclass (around line 107), add:

```python
@dataclass
class CoverLetter:
    """Cover letter 记录"""
    job_id: str
    spec_json: str = ""
    custom_requirements: str = ""
    standard_text: str = ""
    short_text: str = ""
    html_path: str = ""
    pdf_path: str = ""
    tokens_used: int = 0
```

**Step 2: Add table to SCHEMA**

After the `job_analysis` table definition (around line 226, before the indexes), add:

```sql
    -- Cover letter 表
    CREATE TABLE IF NOT EXISTS cover_letters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL UNIQUE REFERENCES jobs(id),
        spec_json TEXT,
        custom_requirements TEXT,
        standard_text TEXT,
        short_text TEXT,
        html_path TEXT,
        pdf_path TEXT,
        tokens_used INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now', 'localtime'))
    );
```

Also add an index in the indexes section:

```sql
    CREATE INDEX IF NOT EXISTS idx_cover_letters_job ON cover_letters(job_id);
```

**Step 3: Add DB methods**

After the `clear_analyses` method (around line 681), add these methods in a new section:

```python
    # ==================== Cover Letter 操作 ====================

    def save_cover_letter(self, cl: CoverLetter):
        """保存 cover letter 记录"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO cover_letters
                (job_id, spec_json, custom_requirements, standard_text, short_text,
                 html_path, pdf_path, tokens_used, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (cl.job_id, cl.spec_json, cl.custom_requirements,
                  cl.standard_text, cl.short_text,
                  cl.html_path, cl.pdf_path, cl.tokens_used,
                  datetime.now().isoformat()))

    def get_cover_letter(self, job_id: str) -> Optional[Dict]:
        """获取 cover letter 记录"""
        with self._get_conn() as conn:
            cursor = conn.execute(
                "SELECT * FROM cover_letters WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_jobs_needing_cover_letter(self, min_ai_score: float = 5.0, limit: int = 50) -> List[Dict]:
        """获取有 AI 分析+简历但无 cover letter 的职位"""
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.*, a.ai_score, a.recommendation as ai_recommendation,
                       a.tailored_resume, a.reasoning
                FROM jobs j
                JOIN job_analysis a ON j.id = a.job_id AND a.ai_score >= ?
                JOIN resumes r ON j.id = r.job_id AND r.pdf_path IS NOT NULL AND r.pdf_path != ''
                LEFT JOIN cover_letters cl ON j.id = cl.job_id
                WHERE cl.id IS NULL
                  AND a.tailored_resume IS NOT NULL
                  AND a.tailored_resume != '{}'
                ORDER BY a.ai_score DESC
                LIMIT ?
            """, (min_ai_score, limit))
            return [dict(row) for row in cursor.fetchall()]
```

**Step 4: Update the import in `__init__` of `CoverLetter` dataclass**

Ensure `CoverLetter` is importable. No changes needed since it's defined in the same file — but verify the dataclass is accessible:

Run: `python -c "import sys; sys.path.insert(0, '.'); from src.db.job_db import JobDatabase, CoverLetter; db = JobDatabase(); print('DB OK, tables:', len(db.SCHEMA.split('CREATE TABLE'))-1); cl = CoverLetter(job_id='test'); print('CoverLetter dataclass OK')"`

Expected: `DB OK, tables: 8` (was 7, now 8) and `CoverLetter dataclass OK`

**Step 5: Commit**

```bash
git add src/db/job_db.py
git commit -m "feat(cover-letter): add cover_letters table and DB methods"
```

---

### Task 4: Implement `src/cover_letter_generator.py`

**Files:**
- Create: `src/cover_letter_generator.py`
- Reference: `src/ai_analyzer.py` (for AI call pattern, retry logic, JSON parsing)
- Reference: `assets/bullet_library.yaml` (evidence pool)
- Reference: `assets/cover_letter_config.yaml` (narrative config)
- Reference: `config/ai_config.yaml` (model config, API keys)

**Step 1: Create the generator module**

This is the largest file. It follows `ai_analyzer.py` patterns closely:
- Same import structure (`PROJECT_ROOT`, `sys.path.insert`, dotenv)
- Same Anthropic client initialization
- Same retry logic (3 attempts, exponential backoff)
- Same JSON parsing (`_parse_json_response` with balanced-brace fallback)
- Same bullet ID lookup (`_build_bullet_id_lookup` reuse)

```python
#!/usr/bin/env python3
"""
Cover Letter Generator — AI 驱动的求职信生成
=============================================

基于已有的 job_analysis 结果，调用 Claude 生成结构化的 cover letter spec。
AI 输出 JSON spec（包含 prose + evidence_ids），验证后存入 cover_letters 表。

不改动 ai_analyzer.py — 独立模块，复用分析结果。
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=True)
except ImportError:
    pass

from anthropic import Anthropic, RateLimitError, APITimeoutError, APIConnectionError
from src.db.job_db import JobDatabase, CoverLetter


class CoverLetterGenerator:
    """AI 驱动的 cover letter 生成器"""

    def __init__(self, config_path: Path = None, model_override: str = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()

        # Model setup (same pattern as AIAnalyzer)
        active = model_override or self.config.get('active_model', 'opus')
        model_cfg = self.config.get('models', {}).get(active, {})
        self.model_name = model_cfg.get('model', 'claude-opus-4-6')
        self.max_tokens = model_cfg.get('max_tokens', 4096)
        self.temperature = model_cfg.get('temperature', 0.3)

        # API credentials
        env_key = model_cfg.get('env_key', 'ANTHROPIC_API_KEY')
        env_url = model_cfg.get('env_url', 'ANTHROPIC_BASE_URL')
        api_key = os.environ.get(env_key, '')
        base_url = os.environ.get(env_url, None)
        auth_type = model_cfg.get('auth_type', 'api_key')

        # Init Anthropic client
        client_kwargs = {}
        if base_url:
            client_kwargs['base_url'] = base_url
        if auth_type == 'bearer':
            client_kwargs['auth_token'] = api_key
        else:
            client_kwargs['api_key'] = api_key
        self.client = Anthropic(**client_kwargs)

        # Load bullet library + cover letter config
        self.bullet_library = self._load_yaml(PROJECT_ROOT / "assets" / "bullet_library.yaml")
        self.cl_config = self._load_yaml(PROJECT_ROOT / "assets" / "cover_letter_config.yaml")
        self.bullet_id_lookup = self._build_bullet_id_lookup()

    def _load_config(self, config_path: Path = None) -> dict:
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _load_yaml(self, path: Path) -> dict:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    def _build_bullet_id_lookup(self) -> Dict[str, str]:
        """Map bullet ID -> verified text from bullet_library.yaml"""
        lookup = {}
        if not self.bullet_library:
            return lookup

        # Config-driven experience/project keys
        prompt_settings = self.config.get('prompt_settings', {})
        exp_keys = prompt_settings.get('experience_keys', [])
        proj_keys = prompt_settings.get('project_keys', [])

        for key in exp_keys:
            section = self.bullet_library.get('work_experience', {}).get(key, {})
            for bullet in section.get('verified_bullets', []):
                if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                    lookup[bullet['id']] = bullet['content']

        for key in proj_keys:
            section = self.bullet_library.get('projects', {}).get(key, {})
            for bullet in section.get('verified_bullets', []):
                if isinstance(bullet, dict) and 'id' in bullet and 'content' in bullet:
                    lookup[bullet['id']] = bullet['content']

        return lookup

    def _build_evidence_pool(self) -> str:
        """Format bullet library as [id] text for prompt"""
        lines = []
        for bid, text in self.bullet_id_lookup.items():
            lines.append(f"[{bid}] {text}")
        return "\n".join(lines)

    def _build_prompt(self, job: Dict, analysis: Dict,
                      custom_requirements: str = None) -> str:
        """Build the cover letter generation prompt"""
        company = job.get('company', 'the company')
        title = job.get('title', 'the position')
        description = (job.get('description', '') or '')[:10000]

        # Extract analysis context
        ai_score = analysis.get('ai_score', 0)
        reasoning = analysis.get('reasoning', '')
        tailored_resume = analysis.get('tailored_resume', '{}')

        # Cover letter config sections
        angles = self.cl_config.get('narrative_angles', {})
        hooks = self.cl_config.get('opening_hooks', {})
        closers = self.cl_config.get('closer_types', {})
        tone = self.cl_config.get('tone_guidelines', [])
        banned = self.cl_config.get('banned_phrases', [])
        length = self.cl_config.get('length_guidance', {})

        angles_str = "\n".join(f"  - {k}: {v}" for k, v in angles.items())
        hooks_str = "\n".join(f"  - {k}: {v}" for k, v in hooks.items())
        closers_str = "\n".join(f"  - {k}: {v}" for k, v in closers.items())
        tone_str = "\n".join(f"  - {t}" for t in tone)
        banned_str = "\n".join(f'  - "{b}"' for b in banned)

        evidence_pool = self._build_evidence_pool()

        requirements_section = ""
        if custom_requirements:
            requirements_section = f"""
## Custom Requirements (from application page)
The applicant has specific requirements from the application page. Address these directly:
{custom_requirements}
"""
        else:
            requirements_section = """
## Custom Requirements
None — generate a standard cover letter tailored to the job description.
"""

        prompt = f"""You are writing a cover letter for a job application. Generate a structured JSON spec.

## Job Context
- Title: {title}
- Company: {company}
- AI Match Score: {ai_score}/10
- AI Reasoning: {reasoning}

## Job Description
{description}

## Tailored Resume (already generated for this job)
{tailored_resume}
{requirements_section}
## Evidence Pool (ONLY use these IDs for evidence_ids)
{evidence_pool}

## Available Narrative Components
Narrative angles (pick ONE that best fits):
{angles_str}

Opening hook styles:
{hooks_str}

Closer types:
{closers_str}

## Tone Rules
{tone_str}

## Banned Phrases (NEVER use these)
{banned_str}

## Output Format
Return a single JSON object with this exact structure:

```json
{{{{
  "standard": {{{{
    "opening_prose": "A compelling 2-3 sentence opening. Reference something specific about the company from the JD. State the role. Hint at why you're a great fit.",
    "body_paragraphs": [
      {{{{
        "prose": "A narrative paragraph connecting your experience to the role's needs. Paraphrase, don't copy bullets verbatim. ~80-120 words.",
        "evidence_ids": ["bullet_id_1", "bullet_id_2"]
      }}}},
      {{{{
        "prose": "A second paragraph with different angle. ~80-120 words.",
        "evidence_ids": ["bullet_id_3"]
      }}}}
    ],
    "closer_prose": "2-3 sentences. Express enthusiasm, forward-looking, call to action.",
    "narrative_angle": "one_of_the_angle_ids"
  }}}},
  "short": {{{{
    "prose": "A concise ~150 word version suitable for email body or text box. Cover the same ground more briefly.",
    "evidence_ids": ["bullet_id_1", "bullet_id_2", "bullet_id_3"]
  }}}}
}}}}
```

## Rules
1. evidence_ids MUST come from the Evidence Pool above — use exact IDs
2. Do NOT copy bullet text verbatim — paraphrase achievements into narrative
3. Company-specific statements MUST come from the job description — do NOT invent facts about the company
4. Standard cover letter: ~250-300 words total (flexible, not strict)
5. Short version: ~120-150 words (flexible)
6. Standard has exactly 2 body_paragraphs
7. narrative_angle must be one of: {', '.join(angles.keys())}
8. Answer three questions: Why this company? Why you? Why now?
9. Be specific and concrete — generic statements are worthless

Return ONLY the JSON object, no other text."""

        return prompt

    def _parse_json_response(self, text: str) -> Optional[Dict]:
        """Parse JSON from AI response (same strategy as ai_analyzer.py)"""
        # Attempt 1: Direct parse
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        # Attempt 2: Extract from code blocks
        patterns = [r'```json\s*(.*?)\s*```', r'```\s*(.*?)\s*```']
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1).strip())
                except json.JSONDecodeError:
                    continue

        # Attempt 3: Balanced brace extraction
        start = text.find('{')
        if start >= 0:
            depth = 0
            in_string = False
            escape = False
            for i in range(start, len(text)):
                ch = text[i]
                if escape:
                    escape = False
                    continue
                if ch == '\\':
                    escape = True
                    continue
                if ch == '"' and not escape:
                    in_string = not in_string
                    continue
                if in_string:
                    continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i+1])
                        except json.JSONDecodeError:
                            break
        return None

    def _validate_spec(self, spec: Dict, job: Dict) -> Tuple[bool, List[str]]:
        """Validate cover letter spec against config constraints"""
        errors = []

        # Check top-level keys
        if 'standard' not in spec:
            errors.append("Missing 'standard' section")
            return False, errors
        if 'short' not in spec:
            errors.append("Missing 'short' section")
            return False, errors

        std = spec['standard']

        # Validate narrative_angle
        valid_angles = set(self.cl_config.get('narrative_angles', {}).keys())
        angle = std.get('narrative_angle', '')
        if angle and angle not in valid_angles:
            errors.append(f"Invalid narrative_angle: '{angle}'. Valid: {valid_angles}")

        # Validate evidence_ids in standard
        all_evidence_ids = []
        for para in std.get('body_paragraphs', []):
            for eid in para.get('evidence_ids', []):
                all_evidence_ids.append(eid)
                if eid not in self.bullet_id_lookup:
                    errors.append(f"Unknown evidence_id in standard: '{eid}'")

        # Validate evidence_ids in short
        for eid in spec['short'].get('evidence_ids', []):
            all_evidence_ids.append(eid)
            if eid not in self.bullet_id_lookup:
                errors.append(f"Unknown evidence_id in short: '{eid}'")

        if not all_evidence_ids:
            errors.append("No evidence_ids found in spec — cover letter has no grounded claims")

        # Check banned phrases
        banned = self.cl_config.get('banned_phrases', [])
        all_prose = self._extract_all_prose(spec)
        for phrase in banned:
            if phrase.lower() in all_prose.lower():
                errors.append(f"Banned phrase found: '{phrase}'")

        return len(errors) == 0, errors

    def _extract_all_prose(self, spec: Dict) -> str:
        """Extract all prose text from spec for validation"""
        parts = []
        std = spec.get('standard', {})
        parts.append(std.get('opening_prose', ''))
        for para in std.get('body_paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('closer_prose', ''))
        parts.append(spec.get('short', {}).get('prose', ''))
        return ' '.join(parts)

    def generate(self, job_id: str, custom_requirements: str = None,
                 force: bool = False) -> Optional[Dict]:
        """Generate cover letter spec for a job.

        Args:
            job_id: Job ID from database
            custom_requirements: Optional requirements from application page
            force: If True, regenerate even if cover letter already exists

        Returns:
            cover_letter_spec dict, or None on failure
        """
        # Check existing
        if not force:
            existing = self.db.get_cover_letter(job_id)
            if existing and existing.get('spec_json'):
                print(f"[CoverLetter] Already exists for {job_id}. Use --regen to regenerate.")
                return json.loads(existing['spec_json'])

        # Load job + analysis
        job = self.db.get_job(job_id)
        if not job:
            print(f"[CoverLetter] Job not found: {job_id}")
            return None

        analysis = self.db.get_analysis(job_id)
        if not analysis:
            print(f"[CoverLetter] No AI analysis for job: {job_id}. Run --ai-analyze first.")
            return None

        company = job.get('company', '')[:20]
        title = job.get('title', '')[:45]
        print(f"[CoverLetter] Generating for: {title} @ {company}")

        # Build prompt
        prompt = self._build_prompt(job, analysis, custom_requirements)

        # AI call with retry (same pattern as ai_analyzer.py)
        import random
        for attempt in range(3):
            try:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{"role": "user", "content": prompt}]
                )
                break
            except RateLimitError:
                wait = 30 * (attempt + 1) + random.uniform(0, 5)
                print(f"  [RATE LIMIT] Waiting {wait:.0f}s...")
                time.sleep(wait)
            except (APITimeoutError, APIConnectionError) as e:
                wait = 2 ** (attempt + 1)
                print(f"  [RETRY] {type(e).__name__}, waiting {wait}s...")
                time.sleep(wait)
        else:
            print(f"[CoverLetter] Failed after 3 attempts")
            return None

        # Extract response
        if not response.content or not response.content[0].text:
            print(f"[CoverLetter] Empty response from AI")
            return None

        raw_text = response.content[0].text
        tokens_used = (response.usage.input_tokens + response.usage.output_tokens
                       if response.usage else 0)

        # Parse JSON
        spec = self._parse_json_response(raw_text)
        if not spec:
            print(f"[CoverLetter] Failed to parse JSON response")
            print(f"  Raw (first 500 chars): {raw_text[:500]}")
            return None

        # Validate
        is_valid, errors = self._validate_spec(spec, job)
        if not is_valid:
            print(f"[CoverLetter] Validation failed:")
            for err in errors:
                print(f"  - {err}")
            return None
        if errors:  # non-blocking warnings
            for err in errors:
                print(f"  [WARN] {err}")

        # Assemble prose texts
        standard_text = self._assemble_standard_text(spec)
        short_text = spec.get('short', {}).get('prose', '')

        # Save to DB
        cl = CoverLetter(
            job_id=job_id,
            spec_json=json.dumps(spec, ensure_ascii=False),
            custom_requirements=custom_requirements or '',
            standard_text=standard_text,
            short_text=short_text,
            tokens_used=tokens_used,
        )
        self.db.save_cover_letter(cl)
        print(f"  -> Saved spec ({tokens_used} tokens)")

        return spec

    def _assemble_standard_text(self, spec: Dict) -> str:
        """Assemble full cover letter text from spec"""
        std = spec.get('standard', {})
        parts = []
        parts.append(std.get('opening_prose', ''))
        for para in std.get('body_paragraphs', []):
            parts.append(para.get('prose', ''))
        parts.append(std.get('closer_prose', ''))
        return '\n\n'.join(p for p in parts if p)

    def generate_batch(self, min_ai_score: float = None, limit: int = 50) -> int:
        """Batch generate cover letters for jobs that have resumes but no cover letter"""
        threshold = min_ai_score
        if threshold is None:
            threshold = self.config.get('thresholds', {}).get('ai_score_generate_resume', 5.0)

        jobs = self.db.get_jobs_needing_cover_letter(min_ai_score=threshold, limit=limit)
        if not jobs:
            print("[CoverLetter] No jobs need cover letter generation")
            return 0

        print(f"\n[CoverLetter] Generating cover letters for {len(jobs)} jobs...")
        generated = 0

        for i, job in enumerate(jobs):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            ai_score = job.get('ai_score', 0)
            print(f"  [{i+1}/{len(jobs)}] [{ai_score:.1f}] {title} @ {company}")

            result = self.generate(job['id'])
            if result:
                generated += 1

        print(f"\n[CoverLetter] Done: {generated}/{len(jobs)} cover letters generated")
        return generated
```

**Step 2: Verify the module imports and initializes**

Run: `python -c "import sys; sys.path.insert(0, '.'); from src.cover_letter_generator import CoverLetterGenerator; print('Import OK')"`

Expected: `Import OK` (may warn about missing API key in env, that's fine)

**Step 3: Commit**

```bash
git add src/cover_letter_generator.py
git commit -m "feat(cover-letter): implement CoverLetterGenerator with AI call, validation, batch"
```

---

### Task 5: Implement `src/cover_letter_renderer.py`

**Files:**
- Create: `src/cover_letter_renderer.py`
- Reference: `src/resume_renderer.py` (for rendering pattern, PDF generation, file organization)

**Step 1: Create the renderer module**

```python
#!/usr/bin/env python3
"""
Cover Letter Renderer — 求职信渲染器
=====================================

从 cover_letters 表获取 spec，渲染为 HTML/PDF + 纯文本。

流程:
1. 从 cover_letters 表获取 spec + assembled text
2. 使用 Jinja2 渲染 cover_letter_template.html
3. 使用 Playwright 转换为 PDF
4. 生成纯文本版本 (TXT)
5. 复制到 ready_to_send/ 目录
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import yaml
from jinja2 import Environment, FileSystemLoader

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.db.job_db import JobDatabase, CoverLetter


class CoverLetterRenderer:
    """Cover letter 渲染器"""

    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.db = JobDatabase()
        self.template_dir = PROJECT_ROOT / "templates"
        self.output_dir = PROJECT_ROOT / self.config.get('resume', {}).get('output_dir', 'output')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.ready_dir = PROJECT_ROOT / "ready_to_send"
        self.ready_dir.mkdir(parents=True, exist_ok=True)

        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        self.candidate = self.config.get('resume', {}).get('candidate', {})

    def _load_config(self, config_path: Path = None) -> dict:
        path = config_path or PROJECT_ROOT / "config" / "ai_config.yaml"
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    @staticmethod
    def _safe_filename(text: str) -> str:
        """Convert text to safe filename"""
        import re
        safe = re.sub(r'[^\w\s-]', '', text).strip()
        safe = re.sub(r'[\s]+', '_', safe)
        return safe

    def render(self, job_id: str) -> Optional[Dict[str, str]]:
        """Render cover letter for a job (HTML/PDF + TXT)"""
        # Load cover letter record
        cl_record = self.db.get_cover_letter(job_id)
        if not cl_record:
            print(f"[CLRenderer] No cover letter found for job: {job_id}")
            return None

        standard_text = cl_record.get('standard_text', '')
        short_text = cl_record.get('short_text', '')
        if not standard_text:
            print(f"[CLRenderer] Empty standard text for job: {job_id}")
            return None

        # Get job details
        job = self.db.get_job(job_id)
        if not job:
            print(f"[CLRenderer] Job not found: {job_id}")
            return None

        company = job.get('company', 'the company')

        # Build template context
        context = {
            'name': self.candidate.get('name', ''),
            'email': self.candidate.get('email', ''),
            'phone': self.candidate.get('phone', ''),
            'location': self.candidate.get('location', ''),
            'linkedin': self.candidate.get('linkedin', ''),
            'linkedin_display': self.candidate.get('linkedin_display', ''),
            'github': self.candidate.get('github', ''),
            'github_display': self.candidate.get('github_display', ''),
            'date': datetime.now().strftime('%B %d, %Y'),
            'greeting': f'{company} Hiring Team',
            'paragraphs': [p.strip() for p in standard_text.split('\n\n') if p.strip()],
        }

        # Render HTML
        from jinja2 import TemplateNotFound
        try:
            template = self.jinja_env.get_template('cover_letter_template.html')
        except TemplateNotFound:
            print(f"[CLRenderer] Template not found: cover_letter_template.html")
            return None

        html_content = template.render(**context)

        # Generate file paths
        candidate_name = self._safe_filename(self.candidate.get('name', 'Cover_Letter'))
        company_safe = self._safe_filename(company)[:20].rstrip('_')
        job_id_short = job.get('id', 'unknown')[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")

        tracking_name = f"{candidate_name}_{company_safe}_{job_id_short}_{timestamp}_CL"
        submit_name = f"{candidate_name}_Cover_Letter"

        html_path = self.output_dir / f"{tracking_name}.html"
        pdf_path = self.output_dir / f"{tracking_name}.pdf"
        txt_path = self.output_dir / f"{tracking_name}.txt"

        # Find the resume's submit_dir for this job (place cover letter alongside resume)
        resume_record = self.db.get_resume(job_id)
        if resume_record and resume_record.get('submit_dir'):
            submit_dir = Path(resume_record['submit_dir'])
            if not submit_dir.exists():
                submit_dir.mkdir(parents=True, exist_ok=True)
        else:
            # Fallback: create new submit folder
            date_prefix = datetime.now().strftime("%Y%m%d")
            base_folder = f"{date_prefix}_{company_safe}"
            submit_dir = self.ready_dir / base_folder
            submit_dir.mkdir(parents=True, exist_ok=True)

        submit_pdf_path = submit_dir / f"{submit_name}.pdf"
        submit_txt_path = submit_dir / f"{submit_name}.txt"

        # Save HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        # Save TXT (short version for paste)
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(short_text)

        # Convert to PDF
        pdf_success = self._html_to_pdf(html_path, pdf_path)

        if pdf_success:
            import shutil
            shutil.copy2(pdf_path, submit_pdf_path)
            shutil.copy2(txt_path, submit_txt_path)
            print(f"  -> CL HTML: {html_path.name}")
            print(f"  -> CL PDF:  {pdf_path.name}")
            print(f"  -> CL TXT:  {txt_path.name}")
            print(f"  -> Send: {submit_dir.name}/{submit_name}.pdf + .txt")
        else:
            # Still copy TXT even if PDF fails
            import shutil
            shutil.copy2(txt_path, submit_txt_path)
            print(f"  -> CL HTML: {html_path.name} (PDF generation failed)")
            print(f"  -> CL TXT:  {txt_path.name}")
            print(f"  -> Send: {submit_dir.name}/{submit_name}.txt")

        # Update DB record with file paths
        cl = CoverLetter(
            job_id=job_id,
            spec_json=cl_record.get('spec_json', ''),
            custom_requirements=cl_record.get('custom_requirements', ''),
            standard_text=standard_text,
            short_text=short_text,
            html_path=str(html_path),
            pdf_path=str(pdf_path) if pdf_success else '',
            tokens_used=cl_record.get('tokens_used', 0),
        )
        self.db.save_cover_letter(cl)

        return {
            'html_path': str(html_path),
            'pdf_path': str(pdf_path) if pdf_success else None,
            'txt_path': str(txt_path),
            'submit_dir': str(submit_dir),
        }

    def _html_to_pdf(self, html_path: Path, pdf_path: Path) -> bool:
        """Convert HTML to PDF via Playwright (same as resume_renderer.py)"""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("  [WARN] Playwright not installed. PDF generation skipped.")
            return False

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                try:
                    page = browser.new_page()
                    page.goto(html_path.absolute().as_uri())
                    page.pdf(
                        path=str(pdf_path),
                        format='A4',
                        margin={
                            'top': '0.75in',
                            'right': '0.75in',
                            'bottom': '0.75in',
                            'left': '0.75in',
                        },
                        print_background=True
                    )
                finally:
                    browser.close()
            return True

        except Exception as e:
            err_str = str(e)
            if "Executable doesn't exist" in err_str or 'browserType.launch' in err_str:
                print(f"  [WARN] Chromium not installed. Run: playwright install chromium")
            else:
                print(f"  [ERROR] PDF generation failed: {e}")
            return False

    def render_batch(self, min_ai_score: float = None, limit: int = 50) -> int:
        """Batch render cover letters that have specs but no PDF"""
        threshold = min_ai_score
        if threshold is None:
            threshold = self.config.get('thresholds', {}).get('ai_score_generate_resume', 5.0)

        # Find cover letters that need rendering (have spec but no pdf_path)
        jobs_with_cl = []
        from src.db.job_db import JobDatabase
        db = self.db
        # Query: jobs with cover_letters record but empty pdf_path
        with db._get_conn() as conn:
            cursor = conn.execute("""
                SELECT j.*, cl.spec_json, a.ai_score
                FROM jobs j
                JOIN cover_letters cl ON j.id = cl.job_id
                JOIN job_analysis a ON j.id = a.job_id AND a.ai_score >= ?
                WHERE (cl.pdf_path IS NULL OR cl.pdf_path = '')
                  AND cl.standard_text IS NOT NULL
                  AND cl.standard_text != ''
                ORDER BY a.ai_score DESC
                LIMIT ?
            """, (threshold, limit))
            jobs_with_cl = [dict(row) for row in cursor.fetchall()]

        if not jobs_with_cl:
            print("[CLRenderer] No cover letters need rendering")
            return 0

        print(f"\n[CLRenderer] Rendering {len(jobs_with_cl)} cover letters...")
        rendered = 0

        for i, job in enumerate(jobs_with_cl):
            title = job.get('title', '')[:45]
            company = job.get('company', '')[:20]
            ai_score = job.get('ai_score', 0)
            print(f"  [{i+1}/{len(jobs_with_cl)}] [{ai_score:.1f}] {title} @ {company}")

            result = self.render(job['id'])
            if result:
                rendered += 1

        print(f"\n[CLRenderer] Done: {rendered}/{len(jobs_with_cl)} cover letters rendered")
        return rendered
```

**Step 2: Verify import**

Run: `python -c "import sys; sys.path.insert(0, '.'); from src.cover_letter_renderer import CoverLetterRenderer; print('Import OK')"`

Expected: `Import OK`

**Step 3: Commit**

```bash
git add src/cover_letter_renderer.py
git commit -m "feat(cover-letter): implement CoverLetterRenderer with PDF/TXT generation"
```

---

### Task 6: Integrate CLI into `scripts/job_pipeline.py`

**Files:**
- Modify: `scripts/job_pipeline.py`

**Step 1: Add CLI arguments**

In the `main()` function's argparse section (around line 925, after `--model`), add:

```python
    # Cover letter commands
    parser.add_argument('--cover-letter', type=str, metavar='JOB_ID',
                        help='Generate cover letter for a specific job')
    parser.add_argument('--cover-letters', action='store_true',
                        help='Batch generate cover letters for jobs with resumes')
    parser.add_argument('--requirements', type=str, default=None,
                        help='Custom requirements from application page (use with --cover-letter)')
    parser.add_argument('--regen', action='store_true',
                        help='Force regenerate (use with --cover-letter)')
```

**Step 2: Add to the conditional routing**

In the main routing `if` statement (around line 950), add `args.cover_letter` and `args.cover_letters` to the condition:

```python
    if args.process or args.import_only or args.filter or args.score or args.ready \
       or args.ai_analyze or args.generate or args.analyze_job \
       or args.stats or args.mark_applied or args.mark_all_applied \
       or args.update_status or args.tracker \
       or args.cover_letter or args.cover_letters:
```

**Step 3: Add handler methods to `JobPipeline` class**

After the `generate_resumes` method (around line 812), add:

```python
    def generate_cover_letter(self, job_id: str, custom_requirements: str = None,
                              force: bool = False):
        """Generate + render cover letter for a single job"""
        try:
            from src.cover_letter_generator import CoverLetterGenerator
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_generator", PROJECT_ROOT / "src" / "cover_letter_generator.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_generator.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterGenerator = module.CoverLetterGenerator

        try:
            from src.cover_letter_renderer import CoverLetterRenderer
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_renderer", PROJECT_ROOT / "src" / "cover_letter_renderer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_renderer.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterRenderer = module.CoverLetterRenderer

        generator = CoverLetterGenerator()
        result = generator.generate(job_id, custom_requirements=custom_requirements, force=force)
        if result:
            renderer = CoverLetterRenderer()
            renderer.render(job_id)

    def generate_cover_letters_batch(self, min_ai_score: float = None, limit: int = 50):
        """Batch generate + render cover letters"""
        try:
            from src.cover_letter_generator import CoverLetterGenerator
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_generator", PROJECT_ROOT / "src" / "cover_letter_generator.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_generator.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterGenerator = module.CoverLetterGenerator

        try:
            from src.cover_letter_renderer import CoverLetterRenderer
        except ImportError:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "cover_letter_renderer", PROJECT_ROOT / "src" / "cover_letter_renderer.py"
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot find cover_letter_renderer.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            CoverLetterRenderer = module.CoverLetterRenderer

        generator = CoverLetterGenerator()
        generated = generator.generate_batch(min_ai_score=min_ai_score, limit=limit)

        if generated > 0:
            renderer = CoverLetterRenderer()
            renderer.render_batch(min_ai_score=min_ai_score, limit=limit)
```

**Step 4: Add routing in the elif chain**

After the `elif args.generate:` block (around line 973), add:

```python
        elif args.cover_letter:
            pipeline.generate_cover_letter(args.cover_letter,
                                           custom_requirements=args.requirements,
                                           force=args.regen)
        elif args.cover_letters:
            pipeline.generate_cover_letters_batch(min_ai_score=args.min_score,
                                                   limit=args.limit)
```

**Step 5: Update help text**

In the help text section (around line 1082), add after the AI-powered section:

```python
    print()
    print("  Cover Letters:")
    print("  --cover-letter ID  Generate cover letter for a job")
    print("  --cover-letters    Batch generate cover letters")
    print("  --requirements TXT Custom requirements (with --cover-letter)")
    print("  --regen            Force regenerate (with --cover-letter)")
```

**Step 6: Verify CLI parses correctly**

Run: `python scripts/job_pipeline.py --help`

Expected: Should show all new arguments in help output without errors.

**Step 7: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat(cover-letter): integrate cover letter CLI commands into pipeline"
```

---

### Task 7: Integration test with real data

**Files:**
- No new files — test existing pipeline

**Step 1: Verify DB schema migration**

Run: `python -c "import sys; sys.path.insert(0, '.'); from src.db.job_db import JobDatabase; db = JobDatabase(); cl = db.get_cover_letter('nonexistent'); print('cover_letters table OK, query returned:', cl)"`

Expected: `cover_letters table OK, query returned: None`

**Step 2: Check for jobs with resumes (candidates for cover letter generation)**

Run: `python -c "import sys; sys.path.insert(0, '.'); from src.db.job_db import JobDatabase; db = JobDatabase(); jobs = db.get_jobs_needing_cover_letter(min_ai_score=5.0, limit=5); print(f'{len(jobs)} jobs ready for cover letters'); [print(f'  [{j[\"ai_score\"]:.1f}] {j[\"title\"][:40]} @ {j[\"company\"][:20]}') for j in jobs]"`

Expected: Lists jobs that have resumes but no cover letters.

**Step 3: Generate a cover letter for one job (requires API key)**

Pick a job_id from step 2 and run:

```bash
python scripts/job_pipeline.py --cover-letter <JOB_ID>
```

Expected output:
```
[CoverLetter] Generating for: <title> @ <company>
  -> Saved spec (NNNN tokens)
  -> CL HTML: Fei_Huang_<company>_<id>_<timestamp>_CL.html
  -> CL PDF:  Fei_Huang_<company>_<id>_<timestamp>_CL.pdf
  -> CL TXT:  Fei_Huang_<company>_<id>_<timestamp>_CL.txt
  -> Send: <date>_<company>/Fei_Huang_Cover_Letter.pdf + .txt
```

**Step 4: Verify output files exist**

Check `ready_to_send/` directory — the cover letter PDF and TXT should be alongside the resume PDF.

**Step 5: Test with custom requirements**

```bash
python scripts/job_pipeline.py --cover-letter <JOB_ID> --requirements "Explain your motivation for joining our team and describe your experience with real-time data pipelines" --regen
```

**Step 6: Test batch generation**

```bash
python scripts/job_pipeline.py --cover-letters --limit 3
```

**Step 7: Commit (if any fixes were needed)**

```bash
git add -A
git commit -m "fix(cover-letter): integration test fixes"
```

---

### Task 8: Update `--generate` to also generate cover letters

**Files:**
- Modify: `scripts/job_pipeline.py`

**Step 1: Modify `generate_resumes` to also trigger cover letter generation**

After the `generate_resumes` method call in the `--generate` handler (around line 973), the `--generate` command should also trigger cover letter generation. Add to the `elif args.generate:` block:

Change from:
```python
        elif args.generate:
            pipeline.generate_resumes(min_ai_score=args.min_score, limit=args.limit)
```

To:
```python
        elif args.generate:
            pipeline.generate_resumes(min_ai_score=args.min_score, limit=args.limit)
            pipeline.generate_cover_letters_batch(min_ai_score=args.min_score, limit=args.limit)
```

Also update the `process_all` method. In the resume generation section (around line 875-880), after `generate_resumes` is called, also call cover letter generation:

After the line that calls `self.generate_resumes(...)`, add:
```python
                    # Also generate cover letters
                    self.generate_cover_letters_batch(min_ai_score=ai_score_threshold, limit=limit)
```

**Step 2: Verify**

Run: `python scripts/job_pipeline.py --generate --limit 1`

Expected: Generates both resume and cover letter for eligible jobs.

**Step 3: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat(cover-letter): auto-generate cover letters with --generate"
```
