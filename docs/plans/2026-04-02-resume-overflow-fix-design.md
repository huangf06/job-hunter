# Resume Overflow Fix: Per-Line Bio + Constrained Skills

**Date:** 2026-04-02
**Status:** Approved
**Problem:** ADAPT_TEMPLATE resumes silently clip content — bio truncated, skills overflow into adjacent columns.

## Root Cause

Zone-based templates use absolute positioning with fixed `max-height` + `overflow: hidden`. AI generates variable-length content that exceeds container capacity. The validator warns but does not block.

| Zone | Container limit | Typical AI output | Content loss |
|------|----------------|-------------------|--------------|
| Bio | 38pt (~3 lines) | 380-450 chars (4-5 lines) | 25-30% |
| Per-entry skills | single line, ~51 chars visible | Sometimes >70 chars | Overlaps right column |
| Tech skills | 110pt DE / 118pt ML | 4 cats with long lists | Last category clipped |

## Design: Two-Layer Defense

### Layer 1: Per-Line Bio Architecture

Replace flowing bio `<span>` with 3 absolutely-positioned lines, matching the rest of the template:

```html
<!-- Before -->
<div style="...max-height:38pt; overflow:hidden; line-height:12pt;">
  <span class="bio">{{ bio | safe }}</span>
</div>

<!-- After -->
<div class="line bio content-shift" style="left:42pt; top:90.5pt;">{{ bio_1 }}</div>
<div class="line bio content-shift" style="left:42pt; top:102.5pt;">{{ bio_2 }}</div>
<div class="line bio content-shift" style="left:42pt; top:114.5pt;">{{ bio_3 }}</div>
```

**Character budget:** ~100 chars/line at 512pt width, 10pt Arial. Hard limit: **105 chars/line** (BLOCK).

**Upstream changes:**
- `template_registry.yaml`: default/senior bios split into `bio_1`, `bio_2`, `bio_3`
- `ai_config.yaml` tailor_adapt prompt: output `bio_1`/`bio_2`/`bio_3` instead of single `bio`
- `_schema_to_context()`: map 3 bio lines to template context
- `validate_adapt_zones()`: validate each line <= 105 chars (BLOCK, not warn)

**Default bio split (DE):**
```yaml
bio:
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

### Layer 2: Per-Entry Skills Hard Limit + CSS Safety

Measured capacity: ~51 total chars in left column at 283.9pt width.

**Changes:**
- Validator: BLOCK if any `{entry}_skills` > 65 chars (current: warn at 70)
- Template CSS: add `max-width: 275pt; overflow: hidden; text-overflow: ellipsis` to skills lines
- This ensures even if something slips through, it truncates with "..." instead of overlapping

### Layer 3: Technical Skills Zone Constraints

**Changes:**
- Validator: BLOCK if > 5 categories (current: block at 7)
- Validator: BLOCK if any single `skills_list` > 80 chars
- Template CSS: reduce `margin-top` from 3pt to 2pt when >= 4 categories (Jinja2 conditional)
- AI prompt: explicitly state "max 5 categories, each skills_list under 80 characters"

### Summary of Limits

| Zone | Hard limit (BLOCK) | CSS safety net |
|------|-------------------|----------------|
| bio_1 | <= 105 chars | Per-line absolute positioning (overflow impossible) |
| bio_2 | <= 105 chars | Same |
| bio_3 | <= 105 chars | Same |
| {entry}_skills | <= 65 chars | `text-overflow: ellipsis` + `max-width: 275pt` |
| Tech skills categories | <= 5 count | Tighter margins when >= 4 |
| Tech skills per-category | <= 80 chars | Flowing text in constrained container |

## Files to Modify

1. **`templates/base_template_DE.html`** — Bio zone: 3 lines; skills: CSS safety
2. **`templates/base_template_ML.html`** — Same changes
3. **`config/template_registry.yaml`** — Split default/senior bios into 3 lines per template
4. **`config/ai_config.yaml`** — Update `tailor_adapt` prompt for per-line bio output
5. **`src/resume_validator.py`** — `validate_adapt_zones()`: BLOCK on bio line >105, skills >65, categories >5, per-cat >80
6. **`src/resume_renderer.py`** — `_schema_to_context()`: map bio_1/2/3 and handle backward compat
7. **`src/template_registry.py`** — `validate_tier2_output()`: accept bio_1/2/3 in slot_overrides

## Non-Goals

- No changes to FULL_CUSTOMIZE tier (different template, different problems)
- No changes to USE_TEMPLATE tier (static PDF, no rendering)
- No visual diff integration (existing tool, separate concern)
- No font-size auto-scaling (unnecessary with per-line architecture)
