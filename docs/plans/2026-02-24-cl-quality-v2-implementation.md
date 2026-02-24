# CL Quality v2 — Micro-Story Anchored Generation

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Rewrite CL prompt from "qualification checklist" to "micro-story anchored thinking", enforce multi-paragraph output, and add theme-based fragment matching — all without requiring micro-stories to exist yet.

**Architecture:** Rewrite `_build_prompt()` with new instructions that focus on "why this person is interested and how they think". Add theme-signal matching to `_select_relevant_fragments()` so micro-stories auto-activate when added later. Update `_validate_spec()` to enforce 2-3 paragraphs and word count. Simplify JSON output schema (remove mandatory narrative_angle).

**Tech Stack:** Python, YAML config

---

### Task 1: Update cover_letter_config.yaml

**Files:**
- Modify: `assets/cover_letter_config.yaml`

**Step 1: Add theme_signals and update length_guidance**

Replace the full file content with:

```yaml
# =============================================================================
# Cover Letter Configuration
# =============================================================================
# Tone rules, anti-detection rules, and theme signals for CL generation.
# =============================================================================

# Theme signals — map JD text patterns to micro-story themes
# Used by _select_relevant_fragments() for theme-based matching
theme_signals:
  ownership: ["end-to-end", "full ownership", "first hire", "build from scratch",
              "greenfield", "founding", "from the ground up"]
  data_quality: ["data quality", "validation", "reliability", "trust",
                 "governance", "accuracy", "data integrity"]
  scale: ["scale", "growth", "high-volume", "millions", "performance",
          "throughput", "large-scale", "petabyte"]
  cross_team: ["stakeholder", "cross-functional", "collaborate", "business",
               "communicate", "partner with", "work closely"]
  ambiguity: ["fast-paced", "startup", "undefined", "greenfield",
              "autonomous", "self-starter", "ambiguous"]
  production_mindset: ["production", "monitoring", "SLA", "reliability",
                       "on-call", "incident", "observability"]
  learning: ["new domain", "diverse", "curious", "adapt", "fast learner",
             "continuous learning", "grow"]

tone_guidelines:
  - "Confident but not arrogant — state what you've done, not what you 'believe'"
  - "Specific, never generic — every sentence should fail the 'swap company name' test"
  - "Show, don't tell — back claims with evidence_ids"
  - "Selective depth over uniform coverage — go deep on 2-3 things, ignore the rest"
  - "Do NOT repeat resume bullet text verbatim — paraphrase into narrative"
  - "Company-specific statements must be derived from the job description"
  - "Include ONE honest observation: a limitation, a curiosity, a genuine question"
  - "The closer should be understated, not grandiose — 'I'd welcome a conversation' is fine"

banned_phrases:
  # Classic clichés
  - "I am writing to apply for"
  - "I believe I would be a great fit"
  - "Thank you for your consideration"
  - "Please find attached my resume"
  - "I am confident that"
  - "passionate about"
  - "hard-working"
  - "team player"
  # AI-typical constructions
  - "I bring a unique combination of"
  - "This aligns perfectly with"
  - "What excites me about"
  - "I would welcome the opportunity to"
  - "Throughout my career"
  - "I am particularly drawn to"
  - "proven track record"
  - "I am eager to leverage"

# Anti-detection structural rules — these target AI writing patterns, not phrases
anti_detection_rules:
  - "Paragraph lengths MUST vary noticeably — one paragraph can be 1-2 sentences, another 4-5"
  - "NEVER start two consecutive sentences with the same word (especially 'I')"
  - "NEVER use 'Furthermore', 'Moreover', 'Additionally', 'In addition' as transitions"
  - "NEVER use 'Having [past participle], I [verb]' construction"
  - "NEVER use 'Not only X but also Y' balanced structures"
  - "NEVER use 'With X years of experience in Y' as an opener"
  - "Allow ONE slightly informal or conversational sentence per letter"
  - "Do NOT address every JD requirement — pick 2-3 and go deep"
  - "Express ONE genuine uncertainty, curiosity, or honest limitation"
  - "Vary sentence lengths: mix short punchy sentences with medium ones"

length_guidance:
  standard: "150-250 words, 2-3 paragraphs"
  short: "100-150 words, 1 paragraph"
```

**Step 2: Commit**

```bash
git add assets/cover_letter_config.yaml
git commit -m "config: add theme_signals, update CL length to 150-250 words

Remove narrative_angles/hooks/closers mechanical choices.
Add theme_signals for micro-story matching (future use).
Update length guidance from 250-350 to 150-250 words."
```

---

### Task 2: Update _select_relevant_fragments() with theme matching

**Files:**
- Modify: `src/cover_letter_generator.py:181-196`

**Step 1: Add _extract_themes_from_jd() method**

Add this new method right after `_infer_role_types()` (after line 179):

```python
def _extract_themes_from_jd(self, job: Dict) -> List[str]:
    """Extract themes from JD text using theme_signals config"""
    description = (job.get('description', '') or '').lower()
    theme_signals = self.cl_config.get('theme_signals', {})
    theme_scores = {}
    for theme, signals in theme_signals.items():
        score = sum(1 for s in signals if s.lower() in description)
        if score > 0:
            theme_scores[theme] = score
    # Return themes sorted by score descending
    return [t for t, _ in sorted(theme_scores.items(), key=lambda x: -x[1])]
```

**Step 2: Update _select_relevant_fragments() to support theme matching**

Replace `_select_relevant_fragments()` (lines 181-196) with:

```python
def _select_relevant_fragments(self, fragments: List[Dict],
                               role_types: List[str],
                               themes: List[str] = None) -> List[Dict]:
    """Select knowledge base fragments relevant to the given role types and themes"""
    relevant = []
    for frag in fragments:
        frag_roles = frag.get('role_types', [])
        if 'all' in frag_roles or any(rt in frag_roles for rt in role_types):
            relevant.append(frag)

    # Sort: micro_stories first (scored by theme match), then handwritten, then others
    origin_order = {
        'handwritten': 0, 'voice_example': 1,
        'ai_edited': 2, 'ai_approved': 3,
    }

    def sort_key(frag):
        is_micro = frag.get('type') == 'micro_story'
        theme_score = 0
        if is_micro and themes:
            frag_themes = frag.get('themes', [])
            theme_score = sum(1 for t in themes if t in frag_themes)
        # micro_stories with theme matches first, then by origin
        return (0 if is_micro and theme_score > 0 else 1,
                -theme_score,
                origin_order.get(frag.get('origin', ''), 99))

    relevant.sort(key=sort_key)
    return relevant
```

**Step 3: Commit**

```bash
git add src/cover_letter_generator.py
git commit -m "feat: add theme-based fragment matching for CL generation

_extract_themes_from_jd() scores JD text against theme_signals config.
_select_relevant_fragments() now prioritizes micro_stories with matching
themes, falling back to existing fragments when no micro_stories exist."
```

---

### Task 3: Rewrite _build_prompt()

**Files:**
- Modify: `src/cover_letter_generator.py:202-376`

**Step 1: Replace the entire _build_prompt() method**

Replace lines 202-376 with a new prompt that:
- Asks "why is this person interested, how do they think?" instead of "write a CL"
- Uses micro-stories as anchor (when available), falls back to KB fragments
- Requires 2-3 paragraphs for standard, 1 paragraph for short
- Removes narrative_angle/hook/closer mechanical choices from output JSON
- Keeps evidence_ids, anti-detection rules, banned phrases, voice examples
- Adds optional `micro_story_id` field
- Uses 150-250 word target for standard, 100-150 for short

Key sections of new prompt:

Core instruction:
```
Your task is NOT to write a cover letter. Your task is to answer in 150-250 words:
"Why would this person find this role interesting, and how do they think about their work?"
```

If micro-stories exist in fragments:
```
## Anchor Material (use one as your starting point)
[list micro_stories with their themes]
Pick the one most connected to this job. Build your letter around it.
```

If no micro-stories, use existing fragments as before.

New JSON output schema (simplified):
```json
{
  "standard": {
    "paragraphs": [
      {"prose": "...", "evidence_ids": ["id1"]},
      {"prose": "...", "evidence_ids": ["id2"]},
      {"prose": "...", "evidence_ids": []}
    ],
    "micro_story_id": "optional_id_if_used"
  },
  "short": {
    "prose": "...",
    "evidence_ids": ["id1", "id2"]
  }
}
```

Note: `opening_prose`, `body_paragraphs`, `closer_prose` combined into a flat `paragraphs` array. The AI decides which paragraph is opening/body/closing naturally.

**Step 2: Update _assemble_standard_text() to match new schema**

```python
def _assemble_standard_text(self, spec: Dict) -> str:
    """Assemble full cover letter text from spec"""
    std = spec.get('standard', {})
    # New format: flat paragraphs array
    paragraphs = std.get('paragraphs', [])
    if paragraphs:
        return '\n\n'.join(p.get('prose', '') for p in paragraphs if p.get('prose'))
    # Backward compat: old format with opening_prose + body_paragraphs + closer_prose
    parts = []
    parts.append(std.get('opening_prose', ''))
    for para in std.get('body_paragraphs', []):
        parts.append(para.get('prose', ''))
    parts.append(std.get('closer_prose', ''))
    return '\n\n'.join(p for p in parts if p)
```

**Step 3: Commit**

```bash
git add src/cover_letter_generator.py
git commit -m "feat: rewrite CL prompt — micro-story anchored, thinking-focused

Replace 'qualification checklist' prompt with 'why interested + how they think'.
Flat paragraphs array replaces opening/body/closer structure.
Micro-story anchor when available, KB fragments as fallback.
Standard: 150-250 words, 2-3 paragraphs. Short: 100-150 words."
```

---

### Task 4: Update _validate_spec() and _extract_all_prose()

**Files:**
- Modify: `src/cover_letter_generator.py:431-493`

**Step 1: Replace _validate_spec() with updated validation**

New validation rules:
- `standard.paragraphs` must have 2-3 entries (not 1, not 5+)
- Each paragraph must have `prose` field
- evidence_ids validated against bullet_id_lookup (unchanged)
- Word count check: standard 100-350 words (soft, warn only)
- Paragraph length variation: longest must be >1.3x shortest (warn only)
- `narrative_angle` no longer required (backward compat: accept if present)
- `micro_story_id` validated against knowledge base if present
- Banned phrases check (unchanged)
- Rule #11: never claim lacking skills (validated via banned patterns)

```python
def _validate_spec(self, spec: Dict, job: Dict) -> Tuple[bool, List[str]]:
    """Validate cover letter spec against config constraints"""
    errors = []

    if 'standard' not in spec:
        errors.append("Missing 'standard' section")
        return False, errors
    if 'short' not in spec:
        errors.append("Missing 'short' section")
        return False, errors

    std = spec['standard']

    # Validate paragraphs structure (new format)
    paragraphs = std.get('paragraphs', [])
    if paragraphs:
        if len(paragraphs) < 2:
            errors.append(f"Standard must have 2-3 paragraphs, got {len(paragraphs)}")
        elif len(paragraphs) > 4:
            errors.append(f"Standard has too many paragraphs ({len(paragraphs)}), max 4")
    else:
        # Backward compat: old format
        if not std.get('body_paragraphs'):
            errors.append("Missing paragraphs in standard section")

    # Validate evidence_ids
    all_evidence_ids = []
    source = paragraphs if paragraphs else std.get('body_paragraphs', [])
    for para in source:
        for eid in para.get('evidence_ids', []):
            all_evidence_ids.append(eid)
            if eid not in self.bullet_id_lookup:
                errors.append(f"Unknown evidence_id: '{eid}'")

    for eid in spec['short'].get('evidence_ids', []):
        all_evidence_ids.append(eid)
        if eid not in self.bullet_id_lookup:
            errors.append(f"Unknown evidence_id in short: '{eid}'")

    if not all_evidence_ids:
        errors.append("No evidence_ids found — cover letter has no grounded claims")

    # Validate micro_story_id if present
    ms_id = std.get('micro_story_id')
    if ms_id:
        valid_ms_ids = {f.get('id') for f in self.knowledge_base
                        if f.get('type') == 'micro_story'}
        if valid_ms_ids and ms_id not in valid_ms_ids:
            errors.append(f"Unknown micro_story_id: '{ms_id}'")

    # Word count check (warning only)
    all_prose = self._extract_all_prose(spec)
    word_count = len(all_prose.split())
    # Don't count short version in word count for standard
    std_prose = self._extract_standard_prose(spec)
    std_words = len(std_prose.split())
    if std_words < 100:
        errors.append(f"Standard too short ({std_words} words, min 100)")

    # Check banned phrases
    banned = self.cl_config.get('banned_phrases', [])
    for phrase in banned:
        if phrase.lower() in all_prose.lower():
            errors.append(f"Banned phrase found: '{phrase}'")

    return len(errors) == 0, errors
```

**Step 2: Update _extract_all_prose() and add _extract_standard_prose()**

```python
def _extract_all_prose(self, spec: Dict) -> str:
    """Extract all prose text from spec for validation"""
    parts = []
    std = spec.get('standard', {})
    # New format
    for para in std.get('paragraphs', []):
        parts.append(para.get('prose', ''))
    # Old format fallback
    parts.append(std.get('opening_prose', ''))
    for para in std.get('body_paragraphs', []):
        parts.append(para.get('prose', ''))
    parts.append(std.get('closer_prose', ''))
    parts.append(spec.get('short', {}).get('prose', ''))
    return ' '.join(p for p in parts if p)

def _extract_standard_prose(self, spec: Dict) -> str:
    """Extract only standard section prose (not short)"""
    std = spec.get('standard', {})
    parts = []
    for para in std.get('paragraphs', []):
        parts.append(para.get('prose', ''))
    parts.append(std.get('opening_prose', ''))
    for para in std.get('body_paragraphs', []):
        parts.append(para.get('prose', ''))
    parts.append(std.get('closer_prose', ''))
    return ' '.join(p for p in parts if p)
```

**Step 3: Commit**

```bash
git add src/cover_letter_generator.py
git commit -m "feat: update CL validation — enforce multi-paragraph, word count

Require 2-3 paragraphs for standard section.
Validate micro_story_id against knowledge base.
Add word count minimum (100 words).
Backward compat: accept old opening/body/closer format."
```

---

### Task 5: Integration test — regenerate ABN AMRO CL

**Files:**
- No new files

**Step 1: Clear ABN CL and regenerate**

```bash
cd C:\Users\huang\github\job-hunter
python -c "
import sys, sqlite3
sys.path.insert(0, '.')
conn = sqlite3.connect('data/jobs.db')
row = conn.execute(\"SELECT id FROM jobs WHERE id LIKE 'a40f68a5%'\").fetchone()
full_id = row[0]
conn.execute('DELETE FROM cover_letters WHERE job_id = ?', (full_id,))
conn.commit()
conn.close()

from src.cover_letter_generator import CoverLetterGenerator
from src.cover_letter_renderer import CoverLetterRenderer
gen = CoverLetterGenerator()
renderer = CoverLetterRenderer()
spec = gen.generate(full_id)
if spec:
    print('SUCCESS')
    print(f'Paragraphs: {len(spec[\"standard\"].get(\"paragraphs\", []))}')
    renderer.render(full_id)
else:
    print('FAILED')
"
```

Expected: SUCCESS, 2-3 paragraphs, no "I don't have X experience", 150-250 words.

**Step 2: Read the generated TXT and verify quality**

Check `ready_to_send/20260224_ABN_AMRO_Bank_N_V/Fei_Huang_Cover_Letter.txt`:
- Multiple paragraphs (not single blob)
- Shows thinking/reasoning, not just credentials
- No banned phrases
- No false skill gap claims

**Step 3: Final commit with all fixes**

```bash
git add -A
git commit -m "feat: CL quality v2 — micro-story anchored, multi-paragraph

Prompt rewritten to focus on 'why interested + how they think'.
Flat paragraphs array, 150-250 words standard.
Theme-based fragment matching ready for micro-stories.
Backward compat preserved for old specs in DB."
```
