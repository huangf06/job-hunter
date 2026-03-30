# Resume Strategy Redesign — v2 Design Addendum (rev4)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Resolve the 5 P0 design flaws identified in Codex review of v1, making the three-tier architecture implementation-ready.

**Architecture:** Extends the existing `job_analysis` table with new routing columns (no new tables), defines an explicit two-phase routing contract with audit trail, specifies a canonical slot schema for Tier 2 templates, restructures C3 inputs for before/after comparison, and adds deterministic safety checks for low-confidence Tier 1 routing.

**Tech Stack:** SQLite/Turso (schema migration), Python, Jinja2, Claude API (C1/C2/C3)

**Parent document:** `docs/plans/2026-03-29-resume-strategy-redesign.md`

**Revision history:**
- rev1 (2026-03-29): Initial addendum addressing 5 P0s
- rev2 (2026-03-30): Fix 5 issues from Codex review of rev1
- rev3 (2026-03-30): Fix 5 issues from Codex review of rev2
- rev4 (2026-03-30): Fix 3 partial issues from Codex review of rev3 (see Codex Review Fixes sections)

---

## Codex Review Fixes (rev1 → rev2)

| # | Codex finding | Fix in rev2 |
|---|---------------|-------------|
| 1 | C1 routing payload (gaps/adapt_instructions) not persisted; `--ai-tailor` batch cannot reconstruct C1 instructions | Added `routing_payload` JSON column to store full C1 routing output |
| 2 | Enum mismatch: DB says `TIER_1` but C1 outputs `USE_TEMPLATE` | Unified: DB stores C1 output values directly (`USE_TEMPLATE`/`ADAPT_TEMPLATE`/`FULL_CUSTOMIZE`), no mapping layer |
| 3 | `get_jobs_needing_tailor()` and `clear_rejected_analyses()` not updated — Tier 1 rows would be sent to C2 or deleted | Added affected-query list with tier-aware rewrites |
| 4 | `tailored_resume` is polymorphic (legacy full JSON vs Tier 2 slot overrides) with no discriminator contract for non-renderer consumers | `resume_tier` is the discriminator; added consumer contract table |
| 5 | C3 `confidence` has no storage column; change density only counts bullet slot_overrides | Added `c3_confidence` column; revised density formula to count all change types |
| X1 | Safeguard reads AI confidence instead of code confidence | Fixed: safeguard keys off `code_decision.confidence` only |
| X2 | `routing_override_reason` conflates C1 overrides and safety escalations | Split into `routing_override_reason` (C1) + `escalation_reason` (safeguard) |
| X3 | `section_order` / `dropped_slots` overengineered for v1 | Moved to Future section; v1 ships with `slot_overrides` + `entry_visibility` + `skills_override` only |
| X4 | Task sequence missing query updates and cover-letter adapter | Reordered; query/CL updates before C2/renderer |

## Codex Review Fixes (rev2 → rev3)

| # | Codex finding | Fix in rev3 |
|---|---------------|-------------|
| 1 | Affected-query list missed `get_jobs_needing_cover_letter()` (`job_db.py:1026`), `notify.py:96`, `pipeline_gaps.py:47,81` | Added to exhaustive query list |
| 2 | `_init_db()` recreates views before `_migrate()` adds columns — views referencing new columns will crash on existing DBs | Added migration order constraint: `_migrate()` must run BEFORE view creation |
| 3 | Fix table says "TIER_ENUM_MAP" but body says "no mapping" — self-contradiction | Removed TIER_ENUM_MAP reference from fix table (already fixed above); single truth: DB stores C1 values directly |
| 4 | `analyze_job()` runs C1→C2 in-memory without DB write; `routing_payload` persistence only helps batch flow | Added explicit single-job flow contract: `analyze_job` passes routing in-memory, persists all fields atomically after C2 |
| 5 | Polymorphism consumer table missing CLI preview (`ai_analyzer.py:1055`, `job_pipeline.py:606`) | Added all preview/inspection consumers to contract table |
| X1 | C3 density denominator only counts entries present in C2 output, not all hideable entries in schema | Fixed: denominator uses schema entry count, not C2 output keys |

## Codex Review Fixes (rev3 → rev4)

| # | Codex finding | Fix in rev4 |
|---|---------------|-------------|
| 1 | Affected-query list still missing `clear_transient_failures()` (`job_db.py:991`) and write-path `save_analysis()` (`job_db.py:872`) | Added both; `save_analysis` gets explicit column-extension spec; `AnalysisResult` dataclass gets new fields |
| 2 | Old enum `TIER_1` still appears in Design Decisions Log | Replaced with `USE_TEMPLATE` |
| 3 | Single-job flow says "atomic write via `save_analysis()`" but current signature only supports legacy columns; batch flow omits Tier 1 `resumes` row creation | Extended `save_analysis()` and `AnalysisResult` spec; added `resumes` row creation to both flows |

---

## P0-1: DB State Model

### Problem

The current system uses a single sentinel convention: `tailored_resume = '{}'` means "C2 not run" and valid JSON means "C2 succeeded." The three-tier architecture introduces states that this convention cannot represent:

| State | Current representation | Problem |
|-------|----------------------|---------|
| C1 done, C2 not run | `tailored_resume = '{}'` | OK |
| Tier 1: use template PDF | ??? | Indistinguishable from "C2 not run" |
| Tier 2: adapted resume | valid JSON in `tailored_resume` | Same as old C2, but semantically different |
| Tier 2: C3 rejected, fell back to template | ??? | No representation |
| Tier 3: full custom | valid JSON in `tailored_resume` | Same as old C2 |
| Legacy: old C2 resume | valid JSON in `tailored_resume` | Indistinguishable from Tier 2/3 |

### Solution: Add routing columns to `job_analysis`

```sql
ALTER TABLE job_analysis ADD COLUMN resume_tier TEXT;
-- Values: 'USE_TEMPLATE' | 'ADAPT_TEMPLATE' | 'FULL_CUSTOMIZE' | NULL (legacy/unrouted)
-- Matches C1 output enum directly. No mapping needed at write time.

ALTER TABLE job_analysis ADD COLUMN template_id_initial TEXT;
-- Code-selected template: 'DE' | 'ML' | 'Backend' | NULL

ALTER TABLE job_analysis ADD COLUMN template_id_final TEXT;
-- After C1 override (if any): 'DE' | 'ML' | 'Backend' | NULL

ALTER TABLE job_analysis ADD COLUMN routing_confidence REAL;
-- 0.0-1.0, from deterministic selector (code_decision.confidence)
-- This is ALWAYS the code selector's confidence, not C1's.
-- Used by Tier 1 safeguard to decide escalation.

ALTER TABLE job_analysis ADD COLUMN routing_override_reason TEXT;
-- NULL if no C1 override; free-text if C1 overrode code template selection

ALTER TABLE job_analysis ADD COLUMN escalation_reason TEXT;
-- NULL if no escalation; set when safeguard auto-escalates USE_TEMPLATE → ADAPT_TEMPLATE
-- Separate from routing_override_reason to avoid conflating two different events.

ALTER TABLE job_analysis ADD COLUMN routing_payload TEXT;
-- Full C1 routing JSON, stored verbatim: {"tier", "template_id", "override",
--   "override_reason", "routing_confidence", "gaps", "adapt_instructions"}
-- Critical: --ai-tailor batch reads gaps + adapt_instructions from here
--   when running C2 separately from C1.

ALTER TABLE job_analysis ADD COLUMN c3_decision TEXT;
-- 'PASS' | 'FAIL' | NULL (not applicable: Tier 1, Tier 3, legacy)
-- PASS = use adapted resume; FAIL = fell back to template PDF

ALTER TABLE job_analysis ADD COLUMN c3_confidence REAL;
-- 0.0-1.0, from C3 output. NULL if C3 not run.
-- Stored for calibration and manual sampling, not used in runtime decisions.

ALTER TABLE job_analysis ADD COLUMN c3_reason TEXT;
-- One-sentence C3 reasoning, NULL if not applicable
```

**Migration strategy:** Run ALTER TABLE statements in `job_db.py` `_migrate()` method (same pattern as existing `submit_dir` migration). All new columns are nullable — legacy rows remain valid with NULL values.

**CRITICAL: Migration order change required.** Current `_init_db()` order is: create tables → drop/recreate views → `_migrate()`. But if views reference new columns (e.g., `resume_tier` in `v_high_score_jobs`), they will fail on existing DBs where columns don't exist yet. **Fix:** `_migrate()` must run BEFORE view creation. New order: create tables → `_migrate()` → drop/recreate views.

**Total new columns: 10** (resume_tier, template_id_initial, template_id_final, routing_confidence, routing_override_reason, escalation_reason, routing_payload, c3_decision, c3_confidence, c3_reason)

### State machine

```
C1 completes
  → writes: resume_tier, template_id_initial, template_id_final,
            routing_confidence, routing_override_reason, routing_payload
  → tailored_resume = '{}'  (unchanged sentinel)

USE_TEMPLATE path (both batch and single-job flows):
  → No C2 call. tailored_resume stays '{}'.
  → Create a `resumes` table row with pdf_path = template PDF from registry.
    This is required because --prepare readiness depends on resumes.pdf_path (job_db.py:491).
  → In batch flow: `--ai-evaluate` creates the resumes row after persisting routing.
  → In single-job flow: `analyze_job()` creates the resumes row after atomic write.
  → --prepare reads template_id_final → copies PDF from registry path.
  → Detection: resume_tier = 'USE_TEMPLATE' AND escalation_reason IS NULL

ADAPT_TEMPLATE path:
  → C2 runs in adapt mode. Input: routing_payload.gaps + routing_payload.adapt_instructions
  → tailored_resume = JSON (Tier 2 slot-override format, see P0-3)
  → C3 runs → c3_decision = 'PASS' or 'FAIL', c3_confidence, c3_reason
  → If FAIL: tailored_resume preserved for debug (NOT reset to '{}')
    Runtime uses c3_decision to choose: PASS → render adapted; FAIL → copy template PDF
  → Detection: resume_tier = 'ADAPT_TEMPLATE' AND c3_decision IS NOT NULL

FULL_CUSTOMIZE path:
  → C2 runs in full-customize mode → tailored_resume = JSON (legacy full-resume format)
  → No C3. c3_decision stays NULL.
  → Detection: resume_tier = 'FULL_CUSTOMIZE'

Legacy (unrouted):
  → resume_tier IS NULL → treated as old pipeline
  → --prepare uses existing behavior (render from tailored_resume via base_template.html)
```

### Single-job vs batch flow contract

There are two execution paths. Both must produce identical DB state:

**Batch flow** (`--ai-evaluate` then `--ai-tailor`):
1. `--ai-evaluate` runs C1 → writes `job_analysis` row with routing columns + `routing_payload` + `tailored_resume='{}'`
2. `--ai-tailor` reads the persisted row → reads `routing_payload` for `gaps`/`adapt_instructions` → runs C2 → updates `tailored_resume` + C3 columns

**Single-job flow** (`--analyze-job` / `analyze_job()`):
1. C1 runs in-memory → produces `AnalysisResult` with routing fields
2. Routing fields are passed **in-memory** to C2 (no DB round-trip needed)
3. C2 runs → result merged into same `AnalysisResult`
4. **Single atomic write** to `job_analysis`: all fields (C1 scores + routing + tailored_resume + C3) written at once via `save_analysis()`

```python
def analyze_job(self, job: Dict) -> Optional[AnalysisResult]:
    """Single-job: C1 evaluate + route + C2 tailor (combined flow)."""
    # C1: evaluate + route
    c1_result = self.evaluate_job(job)  # Returns AnalysisResult with routing fields
    if not c1_result:
        return None

    # Route
    code_decision = select_template(job['title'], self.registry)
    c1_routing = json.loads(c1_result.routing_payload)
    routing = resolve_routing(code_decision, c1_routing)
    routing = apply_tier1_safeguard(routing, code_decision)

    # Update c1_result with routing (in-memory, no DB write yet)
    c1_result.resume_tier = routing['resume_tier']
    c1_result.template_id_initial = routing['template_id_initial']
    c1_result.template_id_final = routing['template_id_final']
    c1_result.routing_confidence = routing['routing_confidence']
    c1_result.routing_override_reason = routing.get('routing_override_reason')
    c1_result.escalation_reason = routing.get('escalation_reason')

    # C2: conditional on tier
    if routing['resume_tier'] == 'USE_TEMPLATE':
        pass  # No C2 needed
    elif routing['resume_tier'] in ('ADAPT_TEMPLATE', 'FULL_CUSTOMIZE'):
        resume_json = self.tailor_resume(job, c1_result, c1_routing)
        if resume_json:
            c1_result.tailored_resume = resume_json
            # C3 gate (ADAPT_TEMPLATE only)
            if routing['resume_tier'] == 'ADAPT_TEMPLATE':
                c3 = self.run_c3_gate(c1_result, c1_routing, job)
                c1_result.c3_decision = c3['decision']
                c1_result.c3_confidence = c3['confidence']
                c1_result.c3_reason = c3['reason']

    # Single atomic DB write (all routing + C2 + C3 fields at once)
    self.db.save_analysis(c1_result)

    # Tier 1: create resumes record pointing to template PDF
    if routing['resume_tier'] == 'USE_TEMPLATE':
        template_pdf = self.registry['templates'][routing['template_id_final']]['pdf']
        self.db.insert_resume(job_id=job['id'], pdf_path=template_pdf)

    return c1_result
```

**Key constraints:**
- `tailor_resume()` in single-job mode receives `c1_routing` dict directly (in-memory). In batch mode, it reads `routing_payload` JSON from DB and parses it. Both paths must produce identical C2 input.
- Both flows create a `resumes` row for USE_TEMPLATE jobs. Batch flow does this in `evaluate_batch()` after C1; single-job flow does it in `analyze_job()` after `save_analysis()`.

### tailored_resume polymorphism contract

`resume_tier` serves as the discriminator. Every consumer of `tailored_resume` MUST branch on it:

| resume_tier | tailored_resume shape | Renderer path | CL generator input | CLI preview display |
|-------------|----------------------|---------------|-------------------|---------------------|
| `NULL` (legacy) | Full resume JSON: `{bio, experiences, projects, skills}` | `base_template.html` (existing) | `tailored_resume` JSON directly (existing behavior) | Bio excerpt + experience count (existing) |
| `USE_TEMPLATE` | `'{}'` (sentinel) | Copy template PDF, no rendering | Registry metadata (`bio_positioning`, `key_strengths`) + Application Brief | `"Template: {template_id_final} (no adaptation)"` |
| `ADAPT_TEMPLATE` + `c3_decision='PASS'` | Slot-override JSON: `{slot_overrides, skills_override, entry_visibility, change_summary}` | `adapt_{tid}.html` with slot schema | Merged content: template defaults + slot_overrides + Application Brief | `"Adapted {template_id_final}: {n} slots overridden"` |
| `ADAPT_TEMPLATE` + `c3_decision='FAIL'` | Slot-override JSON (preserved for debug) | Copy template PDF (same as USE_TEMPLATE) | Same as USE_TEMPLATE | `"Adapted {template_id_final}: C3 FAIL, using template"` |
| `FULL_CUSTOMIZE` | Full resume JSON: `{bio, experiences, projects, skills}` | `customize_template.html` (new single-column) | `tailored_resume` JSON directly (same as legacy) | Bio excerpt + experience count (same as legacy) |

**Every consumer of `tailored_resume` MUST branch on `resume_tier`.** This includes: renderer (`resume_renderer.py:126`), CL generator (`cover_letter_generator.py:237`), CLI preview in `analyze_single` (`ai_analyzer.py:1055`), CLI preview in `analyze` (`job_pipeline.py:606`), and any future consumers.

### Affected queries — exhaustive list

Every query that touches `tailored_resume` or assumes the old state model must be updated:

| Query/Method | Location | Current behavior | Required change |
|---|---|---|---|
| `get_jobs_needing_tailor()` | `job_db.py:905` | `WHERE tailored_resume = '{}'` → selects all un-tailored | Add: `AND (resume_tier IS NULL OR resume_tier IN ('ADAPT_TEMPLATE','FULL_CUSTOMIZE'))` — excludes USE_TEMPLATE rows |
| `clear_rejected_analyses()` | `job_db.py:978` | Deletes rows with `tailored_resume = '{}'` | Add: `AND resume_tier IS NULL` — never delete routed Tier 1 rows |
| `get_analyzed_jobs_for_resume()` | `job_db.py:945` | `WHERE tailored_resume != '{}'` | Replace with tier-aware query (see below) |
| `get_jobs_needing_cover_letter()` | `job_db.py:1026` | `WHERE tailored_resume != '{}'` — excludes USE_TEMPLATE and ADAPT_TEMPLATE+FAIL | Add: `OR resume_tier = 'USE_TEMPLATE' OR (resume_tier = 'ADAPT_TEMPLATE' AND c3_decision = 'FAIL')` — all tiers can generate CLs |
| `v_high_score_jobs` view | `job_db.py:485` | `an.tailored_resume != '{}'` | Add: `OR an.resume_tier = 'USE_TEMPLATE'` |
| `get_funnel_stats()` | `job_db.py:510` | Counts `tailored_resume != '{}'` as "resume ready" | Add tier-aware counting |
| `update_analysis_resume()` | `job_db.py:896` | Updates `tailored_resume` only | Add optional `c3_decision`, `c3_confidence`, `c3_reason` params |
| Notify stats query | `notify.py:96` | `tailored_resume != '{}'` for daily counts | Add: `OR resume_tier = 'USE_TEMPLATE'` |
| Pipeline gaps queries | `pipeline_gaps.py:47,81` | `tailored_resume != ?` for gap analysis | Add tier-aware filter (same pattern as funnel stats) |
| `render_resume()` | `resume_renderer.py:126` | Validates `tailored_resume` as full JSON | Branch on `resume_tier` before validation |
| Cover letter prompt injection | `cover_letter_generator.py:237,362` | Injects raw `tailored_resume` | Branch on `resume_tier` per contract table above |
| CLI preview (`analyze_single`) | `ai_analyzer.py:1055` | `json.loads(tailored_resume)`, reads `.experiences` | Branch on `resume_tier`; show slot override count for Tier 2 |
| CLI preview (`analyze`) | `job_pipeline.py:606` | `json.loads(tailored_resume)`, reads `.bio`, `.experiences` | Branch on `resume_tier`; show template_id for Tier 1 |
| `clear_transient_failures()` | `job_db.py:991` | Deletes rows with `tailored_resume = '{}'` AND error-like `reasoning` | Add: `AND (resume_tier IS NULL)` — never delete routed rows (USE_TEMPLATE has `tailored_resume='{}'` legitimately) |
| `save_analysis()` (write path) | `job_db.py:872` | INSERT OR REPLACE with 11 legacy columns only | Extend to include all 10 new routing/C3 columns (see AnalysisResult extension below) |

### AnalysisResult and save_analysis() extension

The `AnalysisResult` dataclass (`job_db.py:106`) must be extended with routing fields:

```python
@dataclass
class AnalysisResult:
    """AI analysis result (scoring + routing + resume tailoring)"""
    job_id: str
    ai_score: float = 0.0
    skill_match: float = 0.0
    experience_fit: float = 0.0
    growth_potential: float = 0.0
    recommendation: str = ""
    reasoning: str = ""
    tailored_resume: str = ""  # JSON
    model: str = ""
    tokens_used: int = 0
    # --- New routing fields (rev4) ---
    resume_tier: str = ""           # USE_TEMPLATE | ADAPT_TEMPLATE | FULL_CUSTOMIZE
    template_id_initial: str = ""   # Code-selected
    template_id_final: str = ""     # After C1 override
    routing_confidence: float = 0.0 # Code selector confidence
    routing_override_reason: str = ""
    escalation_reason: str = ""
    routing_payload: str = ""       # Full C1 routing JSON
    c3_decision: str = ""           # PASS | FAIL
    c3_confidence: float = 0.0
    c3_reason: str = ""
```

`save_analysis()` (`job_db.py:872`) must include all new columns in its INSERT OR REPLACE:

```python
def save_analysis(self, result: AnalysisResult):
    with self._get_conn(sync_before=False) as conn:
        conn.execute("""
            INSERT OR REPLACE INTO job_analysis
            (job_id, ai_score, skill_match, experience_fit, growth_potential,
             recommendation, reasoning, tailored_resume, model, tokens_used,
             analyzed_at,
             resume_tier, template_id_initial, template_id_final,
             routing_confidence, routing_override_reason, escalation_reason,
             routing_payload, c3_decision, c3_confidence, c3_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (result.job_id, result.ai_score, result.skill_match,
              result.experience_fit, result.growth_potential,
              result.recommendation, result.reasoning,
              result.tailored_resume, result.model, result.tokens_used,
              datetime.now(timezone.utc).isoformat(),
              result.resume_tier or None, result.template_id_initial or None,
              result.template_id_final or None, result.routing_confidence or None,
              result.routing_override_reason or None, result.escalation_reason or None,
              result.routing_payload or None, result.c3_decision or None,
              result.c3_confidence or None, result.c3_reason or None))
```

Note: empty strings map to `None` for nullable columns, ensuring legacy callers that don't set routing fields produce NULL in the DB (not empty strings).

### Funnel stats extension

```python
# New counters for --stats
tier_1_count  = "COUNT(CASE WHEN a.resume_tier = 'USE_TEMPLATE' THEN 1 END)"
tier_2_pass   = "COUNT(CASE WHEN a.resume_tier = 'ADAPT_TEMPLATE' AND a.c3_decision = 'PASS' THEN 1 END)"
tier_2_fail   = "COUNT(CASE WHEN a.resume_tier = 'ADAPT_TEMPLATE' AND a.c3_decision = 'FAIL' THEN 1 END)"
tier_3_count  = "COUNT(CASE WHEN a.resume_tier = 'FULL_CUSTOMIZE' THEN 1 END)"
legacy_count  = "COUNT(CASE WHEN a.resume_tier IS NULL AND a.tailored_resume != '{}' THEN 1 END)"
override_count = "COUNT(CASE WHEN a.routing_override_reason IS NOT NULL THEN 1 END)"
escalation_count = "COUNT(CASE WHEN a.escalation_reason IS NOT NULL THEN 1 END)"
```

---

## P0-2: Routing Contract

### Problem

v1 says "deterministic code selects, C1 may override" but never defines precedence, audit, or conflict resolution. Ambiguous titles like "ML Platform Engineer" will hit multiple keyword lists.

### Solution: Two-phase routing with explicit audit trail

**Phase 1: Deterministic selector (zero tokens)**

```python
from dataclasses import dataclass
from typing import List

@dataclass
class RoutingDecision:
    template_id: str           # 'DE' | 'ML' | 'Backend'
    confidence: float          # 0.0-1.0
    matched_keywords: List[str]
    ambiguous: bool            # True if title matches >1 template family

def select_template(title: str, registry: dict) -> RoutingDecision:
    """Deterministic template selection from job title.

    Returns the best match with confidence score.
    Confidence is reduced when title matches multiple template families.
    """
    title_lower = title.lower()
    matches = {}  # template_id -> matched_keywords

    for tid, meta in registry['templates'].items():
        if not meta.get('enabled', True):
            continue
        matched = [kw for kw in meta['target_roles'] if kw in title_lower]
        if matched:
            matches[tid] = matched

    if len(matches) == 0:
        # No match — default DE, low confidence
        return RoutingDecision('DE', confidence=0.3, matched_keywords=[], ambiguous=False)

    if len(matches) == 1:
        tid = list(matches.keys())[0]
        return RoutingDecision(tid, confidence=0.9, matched_keywords=matches[tid], ambiguous=False)

    # Multiple matches — pick by keyword count, flag ambiguous
    best = max(matches, key=lambda t: len(matches[t]))
    return RoutingDecision(
        best, confidence=0.5, matched_keywords=matches[best], ambiguous=True
    )
```

**Phase 2: C1 override (only when meaningful)**

C1 receives the deterministic decision and may override it. The contract:

```
Pre-selected template: {template_id} (confidence: {confidence})
{" ⚠ AMBIGUOUS: title matched multiple templates" if ambiguous else ""}

Your routing output MUST include:
{
  "tier": "USE_TEMPLATE" | "ADAPT_TEMPLATE" | "FULL_CUSTOMIZE",
  "template_id": "DE" | "ML" | "Backend",
  "override": true | false,
  "override_reason": "JD core requirements are backend API design, not data pipelines" | null,
  "gaps": ["specific gap 1", "specific gap 2"],
  "adapt_instructions": "Change bio from DE to Backend positioning; swap Spark bullets for API bullets" | null
}
```

Note: C1 does NOT output `routing_confidence`. The DB `routing_confidence` column always stores the deterministic selector's confidence. This keeps the safeguard (P0-5) purely deterministic.

**Precedence rule (hardcoded in code, not in prompt):**

```python
def resolve_routing(code_decision: RoutingDecision, c1_routing: dict) -> dict:
    """Merge deterministic and C1 routing decisions.

    Rules:
    1. C1 override wins IF c1 provides override=true with a reason.
    2. Otherwise, code decision's template_id wins.
    3. C1 always decides tier (USE_TEMPLATE / ADAPT_TEMPLATE / FULL_CUSTOMIZE).
    4. All decisions are recorded for audit.
    """
    final_template = code_decision.template_id
    override_reason = None

    if c1_routing.get('override') and c1_routing.get('override_reason'):
        final_template = c1_routing['template_id']
        override_reason = c1_routing['override_reason']

    return {
        'resume_tier': c1_routing['tier'],  # C1 enum, stored directly in DB
        'template_id_initial': code_decision.template_id,
        'template_id_final': final_template,
        'routing_confidence': code_decision.confidence,  # ALWAYS code confidence
        'routing_override_reason': override_reason,
        'routing_payload': json.dumps(c1_routing, ensure_ascii=False),  # Full C1 output
    }
```

**Audit:** Every routing decision is persisted in `job_analysis` columns (see P0-1). `routing_payload` stores the full C1 output for downstream consumption by `--ai-tailor`. `--template-stats` can report override frequency and reasons.

---

## P0-3: Tier 2 Slot Schema

### Problem

v1 says C2 outputs `bio_override`, `bullet_overrides`, `skills` but never defines the canonical slot identifiers, never maps them to HTML template positions.

### Solution: Canonical slot schema defined in registry, enforced by renderer

### Slot naming convention

Each overridable position in a template has a unique slot ID:

```
{company_prefix}_{bullet_index}
```

Examples: `glp_1` (GLP, 1st bullet), `ele_3` (Elegen, 3rd bullet), `vu_2` (VU Amsterdam, 2nd bullet)

### Registry extension

```yaml
templates:
  DE:
    # ... existing fields from v1 (svg, pdf, adapt_html, target_roles, etc.) ...
    slot_schema:
      bio:
        slot_id: "bio"
        default: "Data Engineer with 6 years of experience in building scalable data pipelines..."

      sections:
        - section_id: "experience"
          entries:
            - entry_id: "glp"
              company: "GLP Technology"
              title: "Data Scientist & Team Lead"
              bullets:
                - slot_id: "glp_1"
                  default: "Founded data science team of 5, built real-time credit scoring engine..."
                - slot_id: "glp_2"
                  default: "Designed Spark-based ETL pipeline processing 2B+ records daily..."
                - slot_id: "glp_3"
                  default: "..."
            - entry_id: "ele"
              company: "Elegen"
              bullets:
                - slot_id: "ele_1"
                  default: "..."
                - slot_id: "ele_2"
                  default: "..."
            - entry_id: "vu"
              company: "VU Amsterdam"
              bullets:
                - slot_id: "vu_1"
                  default: "..."

        - section_id: "projects"
          entries:
            - entry_id: "proj_1"
              # ...

        - section_id: "skills"
          categories:
            - cat_id: "languages"
              default: "Python (Expert), SQL, Scala, Go"
            - cat_id: "frameworks"
              default: "Spark, Delta Lake, Airflow, dbt, Kafka"
            - cat_id: "cloud"
              default: "AWS (Glue, EMR, Redshift, S3), GCP (BigQuery)"
```

### C2 output contract (Tier 2 mode) — v1 scope

For the initial implementation, Tier 2 supports three override types. Structural operations (section reordering, slot dropping) are deferred to Future (see bottom).

```json
{
  "slot_overrides": {
    "bio": "Software Engineer with 6 years building data-intensive backend systems...",
    "glp_1": "Architected REST API layer handling 50K requests/sec with <50ms p99 latency..."
  },
  "skills_override": {
    "languages": "Python (Expert), Go, SQL, TypeScript",
    "frameworks": "FastAPI, Docker, Kubernetes, PostgreSQL, Redis"
  },
  "entry_visibility": {
    "glp": true,
    "ele": true,
    "vu": false
  },
  "change_summary": "Repositioned from DE to Backend; replaced 2 Spark bullets with API design bullets; hid VU entry; reordered skills for backend emphasis"
}
```

**Constraints enforced by validator (before rendering):**

```python
def validate_tier2_output(output: dict, schema: dict) -> List[str]:
    """Validate C2 Tier 2 output against template slot schema.
    Returns list of errors (empty = valid).
    """
    errors = []

    # Collect valid IDs from schema
    valid_slots = {'bio'}
    valid_entries = set()
    valid_cats = set()

    for section in schema['sections']:
        for entry in section.get('entries', []):
            valid_entries.add(entry['entry_id'])
            for b in entry.get('bullets', []):
                valid_slots.add(b['slot_id'])
        for cat in section.get('categories', []):
            valid_cats.add(cat['cat_id'])

    # Check slot_overrides reference valid slots
    for slot_id in output.get('slot_overrides', {}):
        if slot_id not in valid_slots:
            errors.append(f"Unknown slot '{slot_id}' in slot_overrides")

    # Check skills_override reference valid categories
    for cat_id in output.get('skills_override', {}):
        if cat_id not in valid_cats:
            errors.append(f"Unknown skill category '{cat_id}'")

    # Check entry_visibility references valid entries
    for entry_id in output.get('entry_visibility', {}):
        if entry_id not in valid_entries:
            errors.append(f"Unknown entry '{entry_id}' in entry_visibility")

    # change_summary is required
    if not output.get('change_summary'):
        errors.append("Missing change_summary")

    return errors
```

### Renderer contract

`adapt_de.html` uses slot IDs directly:

```html
<div class="bio">
  {{ slot_overrides.bio | default(schema.bio.default) }}
</div>

{% for section in schema.sections %}
  {% if section.section_id == "experience" %}
    {% for entry in section.entries %}
      {% if entry_visibility.get(entry.entry_id, true) %}
      <div class="entry">
        <h3>{{ entry.company }} -- {{ entry.title }}</h3>
        <ul>
        {% for bullet in entry.bullets %}
          <li>{{ slot_overrides.get(bullet.slot_id) or bullet.default }}</li>
        {% endfor %}
        </ul>
      </div>
      {% endif %}
    {% endfor %}
  {% endif %}
{% endfor %}
```

The renderer loads the slot schema from registry, merges with C2 output, and passes to Jinja2. Unoverridden slots render their defaults — the template is always complete.

---

## P0-4: C3 Structured Inputs

### Problem

v1 C3 sees only `change_summary`, `key_angle`, and `gaps` — all self-reported by C2. This is "do I like C2's self-description" rather than a real quality gate.

### Solution: Feed C3 the actual before/after content

C3 receives a structured diff constructed by code (not by C2):

```python
def build_c3_input(template_schema: dict, c2_output: dict, c1_routing: dict, jd_summary: str) -> str:
    """Build structured C3 input from actual template content and C2 overrides."""

    lines = []
    lines.append(f"## Job Summary\n{jd_summary}\n")
    lines.append(f"## Identified Gaps\n{', '.join(c1_routing['gaps'])}\n")
    lines.append("## Changes Made (before -> after)\n")

    # --- Count all change types for density ---
    change_count = 0
    total_changeable = 1  # bio is always changeable

    # Bio diff
    if c2_output.get('slot_overrides', {}).get('bio'):
        lines.append(f"**Bio:**")
        lines.append(f"  BEFORE: {template_schema['bio']['default']}")
        lines.append(f"  AFTER:  {c2_output['slot_overrides']['bio']}\n")
        change_count += 1

    # Bullet diffs
    for section in template_schema['sections']:
        for entry in section.get('entries', []):
            for bullet in entry.get('bullets', []):
                total_changeable += 1
                sid = bullet['slot_id']
                override = c2_output.get('slot_overrides', {}).get(sid)
                if override:
                    lines.append(f"**{sid}:**")
                    lines.append(f"  BEFORE: {bullet['default']}")
                    lines.append(f"  AFTER:  {override}\n")
                    change_count += 1

    # Skills diffs
    for section in template_schema['sections']:
        for cat in section.get('categories', []):
            total_changeable += 1
            cid = cat['cat_id']
            override = c2_output.get('skills_override', {}).get(cid)
            if override:
                lines.append(f"**skills.{cid}:**")
                lines.append(f"  BEFORE: {cat['default']}")
                lines.append(f"  AFTER:  {override}\n")
                change_count += 1

    # Entry visibility: count ALL hideable entries from schema (not just C2 output keys)
    all_entries = set()
    for section in template_schema['sections']:
        for entry in section.get('entries', []):
            all_entries.add(entry['entry_id'])
    total_changeable += len(all_entries)

    hidden = [e for e, v in c2_output.get('entry_visibility', {}).items() if not v]
    if hidden:
        lines.append(f"**Hidden entries:** {', '.join(hidden)}")
        change_count += len(hidden)

    # Change density (comprehensive: bio + bullets + skills + entries)
    density = change_count / max(total_changeable, 1) * 100
    lines.append(f"\n**Change density:** {change_count} of {total_changeable} changeable items modified ({density:.0f}%)")

    return '\n'.join(lines)
```

### C3 prompt (revised)

```
You are reviewing whether adapting a polished resume template improves job fit enough
to justify using the adapted version over the original.

The original template has been professionally designed through 9+ iterations for
narrative coherence, visual design, and cross-section resonance.

{structured_diff}

## Decision criteria
- Does each change demonstrably improve fit for THIS specific job?
- Are the new bullet texts of comparable quality to the originals?
- Is the change density proportionate? (>60% modified = essentially a rewrite -> FAIL)
- Would a hiring manager notice the gaps if we used the unmodified template?

Output JSON:
{{
  "decision": "PASS" | "FAIL",
  "confidence": 0.0-1.0,
  "reason": "one sentence"
}}
```

**Key improvements over v1:**
1. C3 sees actual before/after text, not C2's self-description
2. Change density is computed by code from ALL change types (slots, skills, hidden entries), preventing C2 from understating changes
3. Decision includes confidence — stored in `c3_confidence` column for calibration
4. Structured diff is deterministic — same C2 output always produces same C3 input

---

## P0-5: Tier 1 Low-Confidence Safeguard

### Problem

v1 treats Tier 1 as "zero review" but the routing decision (code selector + C1) is not reliable enough for zero-guard at launch. Ambiguous titles and cross-category roles are common.

### Solution: Deterministic confidence threshold with escalation

```python
TIER1_CONFIDENCE_THRESHOLD = 0.7

def apply_tier1_safeguard(routing: dict, code_decision: RoutingDecision) -> dict:
    """Post-routing safeguard for Tier 1 decisions.

    If routing says USE_TEMPLATE but code selector confidence is below threshold,
    escalate to ADAPT_TEMPLATE so C2 can validate/adapt.

    No additional AI call — purely deterministic.
    Keys off code_decision.confidence (deterministic), NOT any AI-reported confidence.
    """
    if routing['resume_tier'] != 'USE_TEMPLATE':
        return routing  # Only applies to Tier 1

    if code_decision.confidence < TIER1_CONFIDENCE_THRESHOLD:
        # Low confidence: escalate to Tier 2
        routing['resume_tier'] = 'ADAPT_TEMPLATE'
        routing['escalation_reason'] = (
            f"Auto-escalated: code selector confidence {code_decision.confidence:.2f} "
            f"< threshold {TIER1_CONFIDENCE_THRESHOLD}"
        )
        # routing_override_reason is left untouched (tracks C1 overrides only)

    return routing
```

**When this fires:**

| Scenario | Code confidence | C1 says | Final tier | Reason |
|----------|----------------|---------|------------|--------|
| "Data Engineer" -> DE | 0.9 | USE_TEMPLATE | USE_TEMPLATE | High confidence, pass |
| "ML Platform Engineer" -> ambiguous | 0.5 | USE_TEMPLATE | ADAPT_TEMPLATE | `escalation_reason` set |
| No keyword match -> DE default | 0.3 | USE_TEMPLATE | ADAPT_TEMPLATE | `escalation_reason` set |
| "Data Scientist" -> ML | 0.9 | ADAPT_TEMPLATE | ADAPT_TEMPLATE | C1 chose Tier 2, safeguard N/A |

**Properties:**
- Zero additional AI cost — purely code-based
- Keys off `code_decision.confidence` only — AI cannot override the safeguard
- `escalation_reason` is separate from `routing_override_reason` — no conflation
- Conservative: when unsure, spend one C2+C3 call to validate
- Auditable: `escalation_reason` records why
- Tunable: threshold can be raised/lowered based on observed accuracy
- Escalated Tier 2 jobs still have the C3 safety net (falls back to template if adaptation is poor)

---

## P1 Items Addressed

### P1-a: Registry `enabled` flag for phased rollout

```yaml
templates:
  Backend:
    enabled: false   # Not yet ready — assets don't exist
    # ... rest of config ...
```

The deterministic selector skips disabled templates. C1 prompt only includes enabled templates. When Backend assets are ready, flip to `enabled: true` — no code changes needed.

### P1-b: Legacy job handling

Legacy jobs (rows where `resume_tier IS NULL`) are grandfathered:

- `--prepare` checks `resume_tier` first. If NULL, falls through to existing behavior (render from `tailored_resume` via `base_template.html`).
- `--ai-tailor` skips rows that already have `tailored_resume != '{}'` AND `resume_tier IS NULL` (legacy already processed).
- `get_jobs_needing_tailor()` excludes USE_TEMPLATE rows (they don't need C2).
- `clear_rejected_analyses()` only deletes rows where `resume_tier IS NULL` (never touches routed rows).
- Optional: `--reroute` command to retroactively route legacy jobs through the new pipeline (runs C1 re-evaluation with routing extension).

### P1-c: `--analyze-job` behavior

`--analyze-job JOB_ID` executes the full new pipeline for one job:
1. C1 (evaluate + route)
2. USE_TEMPLATE -> done (store routing, create resumes record pointing to template PDF)
3. ADAPT_TEMPLATE -> C2 adapt + C3 gate
4. FULL_CUSTOMIZE -> C2 full customize

Same as batch pipeline, just for a single job.

### P1-d: Cover letter context by tier

| Tier | Resume context for CL generation |
|------|----------------------------------|
| USE_TEMPLATE | Template registry metadata (bio_positioning, key_strengths) + Application Brief from C1 |
| ADAPT_TEMPLATE (PASS) | Merged content: template defaults with C2 slot_overrides applied + Application Brief |
| ADAPT_TEMPLATE (FAIL) | Same as USE_TEMPLATE (fell back to template) |
| FULL_CUSTOMIZE | Full tailored_resume JSON + Application Brief |
| Legacy (NULL) | Existing behavior (tailored_resume JSON) |

**Implementation:** `cover_letter_generator.py` gets a new helper `get_resume_context_for_cl(job_analysis_row, registry)` that branches on `resume_tier` and returns a normalized string for prompt injection.

### P1-e: Operational metrics for `--template-stats`

```
Resume Tier Distribution (score >= 4.0):
  USE_TEMPLATE:     523 (55%)  -- template PDF as-is
  ADAPT_TEMPLATE:   332 (35%)  -- adapted template
    | C3 PASS: 198 (60%)
    | C3 FAIL: 134 (40%) -> fell back to template
  FULL_CUSTOMIZE:   102 (11%)  -- full custom
  Legacy:             0 ( 0%)  -- old pipeline

Routing:
  Code -> C1 agreement:  812/957 (85%)
  C1 overrides:          145/957 (15%)
  Safeguard escalations:  67/957 (7%)

Template usage:
  DE:      312 (33%)
  ML:      398 (42%)
  Backend: 247 (26%)

C3 calibration:
  Avg confidence (PASS): 0.82
  Avg confidence (FAIL): 0.71
```

### P1-f: Tier 1 resumes record creation

USE_TEMPLATE jobs must create a `resumes` table row because `--prepare` readiness depends on `resumes.pdf_path` (`job_db.py:491`). After C1 routing:

```python
if resume_tier == 'USE_TEMPLATE':
    template_pdf = registry['templates'][template_id_final]['pdf']
    db.insert_resume(job_id=job_id, pdf_path=template_pdf, ...)
```

This also ensures funnel stats and `--ready` correctly count Tier 1 jobs.

---

## Implementation Task Sequence

Recommended order (dependency-aware, revised from rev2):

1. **Migration order fix** — Reorder `_init_db()`: tables → `_migrate()` → views. This is a prerequisite for all other tasks because new views will reference new columns. (`job_db.py:550-575`)
2. **Schema migration** — Add 10 columns to `job_analysis` in `_migrate()` (P0-1)
3. **Query updates** — Update ALL 13 affected queries/consumers (P0-1 exhaustive list): `get_jobs_needing_tailor`, `clear_rejected_analyses`, `get_analyzed_jobs_for_resume`, `get_jobs_needing_cover_letter`, views, funnel stats, `update_analysis_resume`, `notify.py`, `pipeline_gaps.py`, CLI previews
4. **Template registry** — Create `config/template_registry.yaml` with slot schemas (P0-3)
5. **Deterministic selector** — `select_template()` with confidence scoring (P0-2)
6. **C1 prompt extension** — Add routing output contract to evaluator prompt; persist `routing_payload` (P0-2)
7. **Routing resolver + safeguard** — `resolve_routing()` + `apply_tier1_safeguard()` (P0-2, P0-5)
8. **Single-job flow** — Update `analyze_job()` to pass routing in-memory, single atomic write (P0-2)
9. **Cover letter tier adapter** — `get_resume_context_for_cl()` branching on `resume_tier` (P1-d)
10. **C2 Tier 2 mode** — Adapt prompt, slot-based output, validator (P0-3)
11. **C3 structured gate** — `build_c3_input()` + revised prompt (P0-4)
12. **Renderer update** — Three-path rendering: USE_TEMPLATE copies PDF, ADAPT_TEMPLATE renders `adapt_*.html`, FULL_CUSTOMIZE renders `customize_template.html`
13. **Tier 1 resumes record** — Create resumes row for USE_TEMPLATE jobs (P1-f)
14. **`--template-stats` command** — New CLI flag with tier/routing/C3 metrics (P1-e)
15. **Legacy compat verification** — Ensure NULL `resume_tier` rows work in all paths

---

## Explicit Assumptions

These MUST hold across prompts, DB, registry, and renderer:

1. **template_id values** (`'DE'`, `'ML'`, `'Backend'`) are stable string constants. They appear in: registry YAML keys, C1 prompt, C1 output, DB columns, renderer dispatch, cover letter adapter. Any rename requires updating all six locations.
2. **resume_tier values** (`'USE_TEMPLATE'`, `'ADAPT_TEMPLATE'`, `'FULL_CUSTOMIZE'`) match C1 output enum exactly. Code stores them as-is — no mapping layer.
3. **tailored_resume is polymorphic.** Consumers MUST branch on `resume_tier` before parsing. The shapes are defined in the polymorphism contract table above.
4. **USE_TEMPLATE still creates a `resumes` row** (pointing to template PDF) because downstream readiness checks depend on `resumes.pdf_path`.
5. **Cover letter generation branches by tier.** It does NOT assume `tailored_resume` is always full resume JSON.
6. **routing_payload stores raw C1 JSON.** The `--ai-tailor` batch command reads `gaps` and `adapt_instructions` from this column, not from `reasoning`.

---

## Future (deferred from v1 scope)

These were considered for v1 but deferred to reduce implementation risk:

- **`section_order` override** — Allow C2 to reorder experience/projects/skills sections. Requires template support for dynamic ordering.
- **`dropped_slots` override** — Allow C2 to remove individual bullets. Currently achieved via `entry_visibility` at the entry level (coarser but sufficient).
- **C3 confidence-based routing** — Use `c3_confidence` to auto-escalate borderline PASS decisions to manual review. Currently stored but not acted upon.
- **Template version tracking** — Treat pre-rendered PDFs as build artifacts from SVG + versioned metadata. Currently treated as static files.

---

## Design Decisions Log

| Decision | Chosen | Alternative considered | Reason |
|----------|--------|----------------------|--------|
| State storage | New columns on `job_analysis` | Separate `routing` table | Single-table is simpler; routing is 1:1 with analysis; no join overhead |
| Routing payload | Store full C1 JSON in `routing_payload` | Extract fields into separate columns | Batch `--ai-tailor` needs `gaps` + `adapt_instructions`; separate columns would bloat schema further |
| Enum convention | C1 output values stored directly (`USE_TEMPLATE` etc.) | Map to internal enum | Eliminates mapping bugs; prompt and DB speak same language |
| Confidence source | Always code selector confidence | Merged code+C1 confidence | Keeps safeguard purely deterministic; AI cannot bypass it |
| Escalation tracking | Separate `escalation_reason` column | Overload `routing_override_reason` | Two different events; conflating them makes queries and reporting ambiguous |
| Tier 2 FAIL behavior | Preserve `tailored_resume` for debug | Reset to `'{}'` | Enables post-hoc analysis; `c3_decision='FAIL'` is the authoritative signal |
| Slot schema location | In registry YAML | In HTML template comments | Registry is the single source of truth; HTML templates are derived artifacts |
| C3 input | Code-built structured diff | C2 self-report | Self-report is untrustworthy for a quality gate |
| v1 scope for Tier 2 | `slot_overrides` + `entry_visibility` + `skills_override` | Also `section_order` + `dropped_slots` | Simpler to ship; entry_visibility covers most structural cases |
| Migration order | `_migrate()` before views | Keep current order (tables → views → migrate) | Views that reference new columns crash on existing DBs if migrate hasn't run |
| Single-job DB write | Single atomic write after C2 | Persist C1 row, then update after C2 | Simpler; avoids partial state; `routing_payload` is only needed for batch separation |
| Legacy handling | Grandfathered (NULL resume_tier) | Force re-route all | Non-disruptive; old resumes already submitted |
