# Resume Quality Fixes Design

**Date:** 2026-04-29
**Status:** Approved

## Problem

Audit of 50+ generated resumes (April 24 batch) revealed 13 issues across template, data, AI prompt, and renderer layers. Core problems: incomplete career timeline, missing company context, invisible links, and AI ignoring prompt instructions for project selection.

## Confirmed Decisions

1. **All 5 work experiences always included** — AI controls bullet depth, not experience selection
2. **Delete Deribit Options project** — not yet built, remove entirely
3. **Delete `evolutionary_robotics_research` and `deep_learning_fundamentals`** — cleanup
4. **Keep Financial Data Lakehouse** — user will build soon
5. **Certification stays in Education section** — flex layout, right-aligned date, blue Verify link
6. **All PDF links blue** (`#2c5282`) — no underline, consistent across print/screen
7. **Company notes**: lowercase descriptive phrases, proper noun capitalization preserved
8. **Blog URL**: `https://www.feithink.org/`, display: `feithink.org`

## Fix Plan (3 Layers, 13 Items)

### Layer 1: Bullet Library Data (6 items)

| # | Fix | Detail |
|---|-----|--------|
| 1 | Delete Deribit Options | Remove from `projects` + `active_sections.project_keys` |
| 2 | Delete `evolutionary_robotics_research` | Remove from `projects` + `active_sections.project_keys` |
| 3 | Delete `deep_learning_fundamentals` | Remove from `active_sections.project_keys` |
| 4 | Greenhouse Sensor Pipeline date | `"2025"` → `"Feb. 2026 - Mar. 2026"` |
| 5 | GraphSAGE GNN date | `"2025"` → `"Dec. 2024 - Jan. 2025"` |
| 6 | Blog URL fix | `blog_url` → `"https://www.feithink.org/"` |

### Layer 2: Template / CSS (3 items)

| # | Fix | Detail |
|---|-----|--------|
| 7 | Certification flex layout | Match edu-header: cert name left, date right-aligned |
| 8 | Verify link blue | `.cert-verify { color: var(--link-color); }` |
| 9 | PDF links global blue | `@media print { a { color: var(--link-color); } }` |

### Layer 3: AI Prompt + Renderer (4 items)

| # | Fix | Detail |
|---|-----|--------|
| 10 | All 5 experiences always included | Change prompt from "select 2-3" to "include ALL, control depth" |
| 11 | Company notes fallback in renderer | If AI omits `company_note`, renderer fills from bullet library |
| 12 | DocBridge priority for AI/ML roles | Strengthen prompt language |
| 13 | Certification date/URL fallback | Renderer fills from bullet library when AI output incomplete |

### Design Principle

**Prompt constraints + renderer fallback = double insurance.** AI prompt is unreliable (proven by audit). For deterministic data (company notes, certification, blog URL, experience dates), renderer reads directly from bullet library. AI only controls selection decisions (which bullets, how many, skill categories).
