# Phase 1: Resume Generation Pipeline — Decisions

**Date**: 2026-03-26
**Status**: Final
**Blocks**: Phase 2 (pipeline can't run without resume generation)

---

## 1.1 SVG Resume Authoring Model

**Finding**: SVG files in `templates/` are static design artifacts with all text hardcoded in `<text>`/`<tspan>` elements (~101+ elements per file). They were created in design tools (Inkscape or similar), not programmatically. There are 12 SVG variants (ML Resume v1-v9, DE Resume, template, design reference). None use placeholders or data binding.

**`svg_auto_optimizer.py`** (785 lines) is a research tool that:
1. Generates SVG programmatically via f-strings from `bullet_library.yaml`
2. Screenshots it (Playwright → PNG)
3. Feeds screenshot to Claude Vision for quality feedback
4. Applies regex-based fixes (spacing, font size, position)
5. Iterates up to 10 times until quality score >= 8/10

It's clever but fundamentally fragile — regex-based XML manipulation on programmatically generated SVGs. Not suitable for production automation.

**Relationship to bullet_library**: None in the static SVGs. The auto-optimizer reads `bullet_library.yaml` to generate content, but the manual SVGs have their text copy-pasted in.

**Decision**: SVGs are design references, not automation targets. They informed the visual direction but cannot replace the HTML/Jinja2 pipeline for automated resume generation.

---

## 1.2 Target Resume Generation Flow

**Decision: Option D (Hybrid) with HTML/Jinja2 as the renderer.**

The existing HTML/Jinja2 → Playwright → PDF pipeline is the correct automation path. It works today:

```
AI Analysis (Claude Opus)
  → tailored_resume JSON (bullet IDs + bio spec + skills)
  → ResumeValidator (5-category blocking checks)
  → Jinja2 renders base_template.html (38 variables, 363 lines)
  → Playwright converts HTML → PDF (A4, 0.55in margins)
  → output/ + ready_to_send/
```

**Why not SVG automation?**
- SVGs have hardcoded text — parameterizing 101+ text elements per file is more work than improving the HTML template
- The SVG auto-optimizer uses Vision API iteration (5-8 iterations × $0.003 each) — adds cost and latency for marginal visual gain
- Regex-based SVG fixing is inherently fragile
- HTML/CSS gives us full control over layout, is headless-friendly, and produces consistent output

**What to do with the SVG visual quality**: Port the SVG design decisions INTO the HTML template:
1. Update `base_template.html` CSS to use the typography, spacing, and color palette from the best SVG variant (v9)
2. This is a one-time CSS update, not an ongoing maintenance burden
3. The HTML template already supports print-optimized CSS, Georgia serif, A4 format

**Headless CI**: Yes — Playwright runs headless in GitHub Actions (already proven in current CI)
**Consistent output**: Yes — HTML/CSS with fixed fonts and dimensions produces identical PDFs
**Storage per resume**: ~100KB per PDF (acceptable)
**Bullet library integration**: Yes — AI selects bullet IDs from `bullet_library.yaml`, resolver maps to text, Jinja2 renders
**Validation**: Yes — `ResumeValidator` runs pre-render (structure, skills blocklist, title check, bio cleanup)

**Action items**:
1. Re-enable the HTML/Jinja2 pipeline in CI (uncomment `ANTHROPIC_API_KEY` in workflow, re-enable AI analysis step)
2. Update `base_template.html` CSS to match SVG v9 visual quality (typography, spacing, margins)
3. Keep SVG files in `templates/` as design references (no code changes)
4. Keep `svg_auto_optimizer.py` as an experimental tool (not in the pipeline)

---

## 1.3 Cover Letter Strategy

**Finding**: The CL system is architecturally sophisticated — micro-story anchoring, 20 handwritten fragments, 2 full voice examples, banned phrase detection, evidence-grounded claims, anti-AI structural rules. The infrastructure is solid.

**Root cause of "looks AI-generated"**: Despite all the anti-detection rules, the output likely still feels formulaic because:
1. **Over-coverage**: Trying to address 2-3 JD requirements still results in a systematic coverage pattern humans don't naturally write
2. **Perfect paragraph structure**: Even with length variation rules, the logical flow is too clean
3. **Compulsory elements**: Requiring ONE uncertainty + ONE informal sentence feels mechanical when forced

**Decision: Reduce scope and make CL optional.**

1. **Default to "short" format**: 100-150 words, 1-2 paragraphs. This is the `short` spec the system already generates. Short CLs are harder to detect as AI because there's less text to pattern-match on.

2. **Skip CL when not required**: Many platforms (LinkedIn Easy Apply, Greenhouse without CL field) don't need cover letters. Don't generate one unless the application form has a CL upload or the job explicitly asks for one. Add a `cl_required: bool` field to job analysis.

3. **Keep the micro-story architecture**: The handwritten fragments and voice examples are genuinely good. Don't dismantle them.

4. **Remove compulsory uncertainty/curiosity rule**: Let it emerge naturally from the voice examples rather than forcing it as a structural requirement.

5. **One concrete change to the prompt**: Replace "address 2-3 JD requirements" with "write one paragraph about why this specific role at this specific company connects to your experience — do not enumerate JD requirements."

**Action items**:
1. Change `--prepare` to skip CL generation when the platform doesn't require it (add logic to check)
2. Default to short format (100-150 words) unless `--full-cl` flag is passed
3. Update the generation prompt: remove compulsory uncertainty, change JD coverage instruction
4. No changes to `cl_knowledge_base.yaml` or voice examples

---

## 1.4 Storage and Artifact Management

**Finding**: `output/` is 116 MB (2,898 files), `ready_to_send/` is 77 MB (1,366 files across 399 company folders). Total ~193 MB. Each resume PDF is ~100KB. Each CL is ~54KB.

**This is not actually a problem.** 193 MB on disk is negligible. The "大量的存储空间" concern was likely about git bloat (none of this is committed) or CI artifact storage (none is uploaded). The real concern is organization, not capacity.

**Decision: Don't store generated PDFs in CI. Regenerate on demand.**

1. **CI does NOT upload resume/CL PDFs as artifacts**. They can be regenerated from the `tailored_resume` JSON stored in the database. This is deterministic — same JSON + same template = same PDF.

2. **Local `output/` gets a retention policy**: Keep last 30 days, auto-archive older files to `output/archive/YYYY-MM/`. Add `jh admin cleanup --older-than 30d` command.

3. **`ready_to_send/_applied/` is the audit trail**: Keep indefinitely. These are the exact materials submitted. Useful for interview prep reference.

4. **`ready_to_send/_skipped/` can be deleted after 7 days**: These were rejected by the user and have no value.

**What must be stored vs. regenerated**:
| Artifact | Store? | Why |
|----------|--------|-----|
| `tailored_resume` JSON | Yes (DB) | Source of truth, enables regeneration |
| Resume PDF | Regenerate | Deterministic from JSON + template |
| CL spec JSON | Yes (DB) | Source of truth |
| CL PDF/TXT | Regenerate | Deterministic from spec + template |
| Applied materials | Yes (files) | Audit trail, interview prep reference |
| Skipped materials | Delete after 7d | No value |

**Action items**:
1. Add cleanup command: `python scripts/job_pipeline.py --cleanup --older-than 30`
2. Auto-delete `_skipped/` folders older than 7 days during `--finalize`
3. No changes to CI workflow (it already doesn't upload PDFs)

---

## Phase 1 Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Resume renderer | HTML/Jinja2 + Playwright (keep existing) | Works, headless, consistent, parameterized |
| SVG role | Design reference only | Hardcoded text, not automatable |
| Visual quality | Port SVG CSS into HTML template | One-time update, no ongoing maintenance |
| CL strategy | Short format (100-150w), optional by default | Reduces AI detection surface, saves time |
| Storage | Regenerate PDFs on demand, keep applied materials | JSON in DB is the source of truth |
| Immediate action | Re-enable AI analysis in CI | Unblocks the entire pipeline |
