# Resume Quality Rebuild — Design Document

Date: 2026-04-24

## Problem Statement

Current v3.0 pipeline produces resumes that differ significantly from the versions that got 17 interviews. The gap exists across three layers: template structure, bullet library content, and C2 prompt configuration. This document specifies exactly what to change and why, based on a side-by-side audit of all 15 interview-winning resume PDFs.

## Data Source

`docs/interview_winning_resumes/` — 44 files from 15 companies (17 job-company pairs), all of which received interview invitations. Every finding below is derived from these PDFs.

---

## Layer 1: Template Changes (`templates/base_template.html`)

### 1.1 Header: Add blog link (3rd link)

**Interview version** (all 15 companies):
```
linkedin.com/in/huangf06 | github.com/huangf06 | feithink.substack.com
```

**Current**:
```
LinkedIn | GitHub
```

**Change**: Add `blog` field to template header. C2 output already has the URLs; template just needs the third link slot. The blog URL should come from `candidate_info` config (not hardcoded).

### 1.2 Experience entry: Add location

**Interview version**:
```
GLP Technology                    Jul. 2017 - Aug. 2019
Data Engineer & Team Lead         Shanghai, China
```

**Current**:
```
GLP Technology                    Jul. 2017 -- Aug. 2019
Senior Data Engineer
```

**Changes**:
- Add `location` to the right side of the title line (`.exp-subheader`)
- Location comes from bullet library per-company config (already exists: `location` field)

### 1.3 Replace LANGUAGES section with ADDITIONAL section

**Interview version** (all 15 companies):
```
ADDITIONAL
Languages:  English (Fluent), Mandarin (Native), Dutch (Conversational)
Interests:  Philosophy (Kant, existentialism), Dostoevsky, strategy games, analytical writing
Blog:       feithink.substack.com
```

**Current**:
```
LANGUAGES
English (Fluent), Mandarin (Native)
```

**Change**: Replace the `LANGUAGES` section in template with `ADDITIONAL` section containing Languages, Interests, Blog. Interests and Blog are static (from candidate config), Languages is already dynamic.

### 1.4 Education entry: Add location

**Interview version**:
```
Vrije Universiteit Amsterdam              Sep. 2023 - Aug. 2025
M.Sc. in Artificial Intelligence (GPA: 8.2/10)    Amsterdam, Netherlands
```

**Current**: No location on education entries.

**Change**: Add location to `.edu-subheader` right side, same pattern as experience.

### 1.5 Tsinghua description

**Interview version**: `Tsinghua University (Ranked #1 in China, top 20 globally)`
**Current**: `Tsinghua University (#1 in China)`

**Change**: Update in `ai_config.yaml` education section and bullet library.

### 1.6 Career Note text

**Interview version**: `Career Note: 2019-2023 included independent investing, language learning (English, German), and graduate preparation.`
**Current**: `Career transition (2019–2023): Relocated to the Netherlands and began M.Sc. in Artificial Intelligence at VU Amsterdam.`

**Change**: Revert to interview-proven text. This is more personal and mentions concrete activities. Update in bullet library `career_note` field and C2 prompt.

---

## Layer 2: Bullet Library Rebuild (`assets/bullet_library.yaml`)

### 2.1 Company name fix

**All 15 interview PDFs** use `Baiquan Investment`. Current library says `BQ Investment`.

**Change**: `company: "BQ Investment"` → `company: "Baiquan Investment"` in bullet library. Revert the C2 prompt example change made earlier today.

### 2.2 Missing bullet: `eleme_kmeans`

Used in **8 interview resumes** (Chikara HR, Deloitte, elipsLife, kaiko.ai, Nebius, Sensorfact, Source.ag x2) but does not exist in current library.

**Add**:
```yaml
- id: eleme_kmeans
  status: active
  tags: [ml, clustering, hadoop, hive, user-segmentation]
  narrative_role: headline
  content: "Engineered K-means clustering pipeline on Hadoop/Hive to segment millions of users by behavioral patterns; delivered actionable customer profiles adopted by product and marketing teams for personalized campaign targeting."
```

### 2.3 Missing bullet: `eleme_sql_simple`

Used in **6 interview resumes** as a standalone short SQL bullet, separate from the combined `eleme_ab_testing`.

Current library has `eleme_sql_optimization` (longer version with "90+ queries" and "500GB → 100GB") and `eleme_sql_reporting` (even shorter). The interview version is a middle-ground standalone:

**Add**:
```yaml
- id: eleme_sql_simple
  status: active
  tags: [sql, hadoop, hive, performance]
  narrative_role: optional
  content: "Optimized complex SQL queries on Hadoop/Hive for cross-functional stakeholders, cutting reporting turnaround time by 30%."
```

### 2.4 Split `eleme_ab_testing` into separate bullets

Current library combines A/B testing + SQL optimization into one bullet. Interview resumes used them as **separate bullets** in 8 of 15 companies. The combined version was also used in the other 7.

**Keep both options**: Keep the combined `eleme_ab_testing` as-is, but add the individual components (`eleme_kmeans`, `eleme_sql_simple`) so C2 can use them independently. Update recommended sequences to prefer the split versions for resumes with more space.

### 2.5 Interview-proven frequency tags

Add `interview_count` to each bullet so C2 can prioritize. Counts derived from the 17 interview resumes:

| Bullet ID | Count | Notes |
|-----------|-------|-------|
| `glp_founding_member` | 17 | Every resume |
| `glp_pyspark` | 17 | Every resume |
| `glp_data_quality` | 14 | Most DE/ML resumes |
| `glp_portfolio_monitoring` | 13 | Most resumes |
| `bq_de_factor_engine` | 17 | Every resume |
| `bq_de_pipeline` | 13 | Most DE resumes |
| `bq_de_backtest_infra` | 10 | Mixed |
| `bq_factor_research` | 7 | Quant/ML roles |
| `bq_data_quality` | 9 | DE roles |
| `bq_rbreaker` | 4 | Quant roles only |
| `eleme_ab_testing` (combined) | 8 | When space is tight |
| `eleme_kmeans` | 8 | When 2 Ele.me bullets available |
| `eleme_sql_simple` | 6 | Paired with kmeans |
| `glp_data_compliance` | 3 | Regulated industries |
| `glp_decision_engine` | 0 | Never in interview resumes |

**Key insight**: `glp_decision_engine` was never used in any interview resume. It should be deprioritized or removed from recommended sequences.

### 2.6 Recommended sequences update

Current sequences don't match interview patterns. Update based on actual interview data:

```yaml
recommended_sequences:
  data_engineer: ["glp_pyspark", "glp_data_quality", "glp_portfolio_monitoring", "glp_founding_member"]
  ml_engineer: ["glp_founding_member", "glp_pyspark", "glp_portfolio_monitoring"]
  data_scientist: ["glp_founding_member", "glp_pyspark", "glp_data_quality"]
  quant: ["glp_founding_member", "glp_portfolio_monitoring", "glp_pyspark"]
```

For Baiquan:
```yaml
recommended_sequences:
  data_engineer: ["bq_de_pipeline", "bq_de_factor_engine", "bq_data_quality"]
  quant: ["bq_factor_research", "bq_de_factor_engine", "bq_de_backtest_infra", "bq_rbreaker"]
  ml_engineer: ["bq_de_pipeline", "bq_de_factor_engine", "bq_de_backtest_infra"]
```

For Ele.me:
```yaml
recommended_sequences:
  data_engineer: ["eleme_kmeans", "eleme_sql_simple"]
  ml_engineer: ["eleme_ab_testing"]
  data_scientist: ["eleme_ab_testing", "eleme_kmeans"]
  quant: ["eleme_ab_testing"]
```

---

## Layer 3: C2 Prompt & Config (`config/ai_config.yaml`)

### 3.1 Prompt example alignment

Update the C2 prompt example to match interview-proven patterns:
- Company name: `"Baiquan Investment"` (revert today's change to `"BQ Investment"`)
- Company note: `"acquired by Alibaba"` (without parens — already fixed today)
- Date format: `-` not `--` (already fixed today)
- Add `location` field to experience entries in the example

### 3.2 Add interview_count guidance to C2 prompt

Add a rule in the BULLET DISTRIBUTION section:

```
### BULLET PRIORITY
- Prefer bullets with higher interview_count (field in bullet library)
- Core bullets (interview_count >= 10) should appear in EVERY resume unless explicitly irrelevant
- Never omit glp_founding_member or bq_de_factor_engine — they appeared in all 17 interview resumes
```

### 3.3 ADDITIONAL section in C2 output schema

Add to the JSON output schema:
```json
"additional": {
  "languages": "English (Fluent), Mandarin (Native), Dutch (Conversational)",
  "interests": "Philosophy (Kant, existentialism), Dostoevsky, strategy games, analytical writing",
  "blog": "feithink.substack.com"
}
```

Interests and blog are static (from `candidate_info` config). Languages may vary (Dutch included in 11/15 interview resumes, omitted in 4 — FareHarbor, Barak, kaiko, Maisha).

### 3.4 Education config updates

- Tsinghua: `"Tsinghua University (Ranked #1 in China, top 20 globally)"`
- Add Tsinghua thesis: `"Design and Implementation of Web-based Collaborative Office System (Java/MVC/SQL Server)"`
- Add location to both education entries

### 3.5 Career note update

Change to interview-proven text:
```
Career Note: 2019-2023 included independent investing, language learning (English, German), and graduate preparation.
```

### 3.6 Section ordering

Interview resumes used: **Education → Projects → Work Experience**.

Current v3.0 uses: **Experience → Education → Projects**.

**Decision**: The section order varied slightly across interview resumes but Education-first was consistent. This is likely because:
1. M.Sc. from VU Amsterdam is recent and strong (GPA 8.2, thesis, coursework scores)
2. Databricks cert is recent (2026)
3. Projects showcase modern tech stack (Databricks, Delta Lake, streaming)

The current "Experience first" layout buries the strongest recent credentials. Revert to Education → Projects → Experience ordering.

However, this is a C2 decision (section ordering is in the JSON output), not a template change. The template renders sections in the order they appear in the JSON.

**Change**: Update C2 prompt section ordering guidance to default to Education → Projects → Experience. C2 can still reorder for specific cases (e.g., very senior DE roles where experience matters most).

---

## Layer 4: Renderer Changes (`src/resume_renderer.py`)

### 4.1 Pass location to template

Ensure `location` from the tailored_resume JSON is passed through to the template context for both experiences and education entries.

### 4.2 Pass ADDITIONAL data to template

Add `additional` section data to template context (interests, blog). Languages already handled.

### 4.3 Blog URL in header

Pass `blog_url` from candidate config to template header context.

---

## Implementation Order

1. **Template changes** (1.1-1.6): HTML/CSS modifications to `base_template.html`
2. **Bullet library** (2.1-2.6): Add missing bullets, fix company name, add interview_count, update sequences
3. **C2 prompt** (3.1-3.6): Align example, add priority rules, update schema
4. **Renderer** (4.1-4.3): Pass new fields through to template
5. **Candidate config**: Add blog URL, interests, career note text
6. **Test**: Regenerate the 3 test resumes (Sensorfact, Adyen, EPAM) and compare against interview PDFs
7. **Validate**: Visual diff against original Sensorfact interview resume (the one case where we have both)

## Success Criteria

A regenerated Sensorfact resume should be visually indistinguishable from the original interview-winning version (`Sensorfact_Senior_DE_Resume_0209.pdf`) in structure, with improvements only in C2's job-specific tailoring.

---

## Out of Scope

- Cover letter changes (separate system)
- Template visual design (colors, fonts, spacing) — already matching
- New bullet content creation — only restoring interview-proven content
- AI scoring (C1) changes — not affected
