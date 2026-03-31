# Business Logic Audit (2026-03-31)

Funnel snapshot at time of audit:
- Scraped 3872 → Filter 1813 (46.8%) → AI analyzed 1445 → High 966 (66.8%) → Resume 616 → Applied 319 → Interview 34 (10.7%) → Offer 10 (3.1%)

## High Priority (directly impacts interview conversion)

### H1. Career Note rewrite [DONE]
- Current: "2019-2023 included independent investing, language learning, and graduate preparation"
- Problem: defensive, lists 3 weak activities, "investing" reads as "unemployed day-trading" to Dutch HR
- Fix: reframe as active transition story. Option A: merge gap + MSc into one narrative. Option B: frame as "independent quantitative researcher"
- Location: `config/ai_config.yaml` line ~90 (career_note field) + `src/resume_renderer.py` default value
- **Why:** Single biggest red flag on resume; 6-second HR scan stops here
- **How to apply:** 5-minute config change, affects all future resumes

### H2. Backend template disabled = funnel leak [DONE]
- backend_engineering (P2) and backend_ai_data (P1) profiles active, but Backend template has empty slot_schema
- Software Engineer jobs routed to DE template with mismatched bio ("Data Engineer...")
- Likely part of 966→616 resume gap (350 missing)
- Fix: either enable Backend template with proper slots, or disable both backend search profiles
- Location: `config/template_registry.yaml` (Backend section)

### H3. AI score threshold 4.0 too low [DONE — raised to 5.0]
- 66.8% pass = C1 screening is nearly useless
- 4.0 = "significant skill gaps" per own guidelines
- Fix: raise to 5.0 ("core skills present, some secondary gaps")
- Validate first: query interview rate by score band (4-5 vs 5-6 vs 6-7 vs 7+)
- Location: `config/ai_config.yaml` → `thresholds.ai_score_generate_resume`

### H4. Interests line too academic [DONE]
- "Philosophy (Kant, existentialism), Dostoevsky, strategy games, analytical writing"
- Too heavy/academic for DE roles; may signal "wants academia"
- Fix: keep "philosophy" without names, add one approachable/social interest
- Location: `config/ai_config.yaml` → `interests` field

## Medium Priority (efficiency + quality)

### M1. Dutch language filter should move to scraper layer [DONE]
- 48.5% of rejects = Dutch JDs; half of all scraping is wasted
- LinkedIn supports language filter params (f_JC=en)
- Keep hard rule as fallback
- Location: `config/search_profiles.yaml` (LinkedIn URL params)

### M2. Search profile overlap and low-ROI profiles [DONE]
- backend_engineering is superset of backend_ai_data → redundant
- quant: Optiver + Flow Traders already in Greenhouse; add IMC, consider disabling LinkedIn quant search
- data_science: remove "Data Analyst", "BI Engineer" (underleveled), "Data Consultant" (consulting firms, need local language)
- Location: `config/search_profiles.yaml`

### M3. ml_research PhD problem [DONE]
- Many "Research Engineer"/"Applied Scientist" jobs in NL require PhD
- Wastes C2 tokens, near-zero interview conversion
- Fix: add PhD detection to hard rules, or strengthen C1 hard reject signal
- Location: `config/base/filters.yaml` (new rule) or C1 prompt

### M4. Diagnose 350 missing resumes [NOT STARTED]
- 966 high-score → 616 resumes = 36.2% loss
- Possible causes: C2 not run, API failures, template routing failure, validation failure
- Fix: run diagnostic query on DB first
- Query: `SELECT resume_tier, count(*) FROM job_analysis WHERE ai_score >= 4.0 GROUP BY resume_tier`

### M5. Cover Letter ROI low, deprioritize optimization [NOT STARTED]
- Most NL tech companies don't require CL
- Anti-detection rules sufficient for 150-250 word texts
- 2 voice examples sufficient
- Don't invest more; redirect effort to resume quality
- **No code change needed** — just a prioritization decision

### M6. Title whitelist too broad [DONE]
- "software", "platform", "infrastructure" alone match Product Managers, Sales, IT managers
- Fix: change to compound patterns: "software engineer", "data platform", "infrastructure engineer"
- Location: `config/base/filters.yaml` → `non_target_role.title_whitelist`

### M7. Missing "no visa sponsorship" hard rule [N/A]
- User has zoekjaar (orientation year permit), does not need sponsorship
- No hard rule needed
- ~~If sponsorship needed: add regex rule for "no visa sponsorship" / "EU work authorization required"~~

## Low Priority / Long-term

### L1. Missing keywords: add "MLOps Engineer" as standalone [NOT STARTED]
### L2. Closer options: 3 sufficient for now, add "startup_builder" later [NOT STARTED]
### L3. Repost: change from warning to auto-skip (unless >90 days) [NOT STARTED]
### L4. 10.7% interview rate is normal-to-high for non-EU candidate in NL [INFO]
### L5. Feedback loop: add rejection_reason + interview_rounds to applications table [NOT STARTED]

## Data Queries Needed Before Acting

| Query | Validates |
|-------|-----------|
| Interview rate by AI score band (4-5, 5-6, 6-7, 7+) | H3 threshold |
| resume_tier distribution for high-score jobs without resumes | H2/M4 gap |
| Interview rate by search profile origin | M2 profile ROI |
| Interview rate by template (DE vs ML) | H2 template impact |
| How many interviews asked about career gap | H1 career note |
| Backend-titled job application outcomes | H2 backend template |

## Data Query Results (2026-03-31)

### Q1. Interview Rate by AI Score Band

| Score Band | Analyzed | Applied | Interview | Offer | Interview Rate |
|------------|----------|---------|-----------|-------|----------------|
| 7+         | 320      | 159     | 10        | 1     | **6.3%**       |
| 6-7        | 249      | 97      | 2         | 2     | 2.1%           |
| 5-6        | 168      | 68      | 2         | 0     | 2.9%           |
| 4-5        | 238      | 20      | 2         | 0     | 10.0% (n=20)   |
| <4         | 481      | 8       | 2         | 1     | 25.0% (n=8)    |

**Interpretation:** The 7+ band clearly outperforms at 6.3%. The 4-5 and <4 bands show high rates but from tiny samples (20 and 8 applications) — statistically unreliable. The 5-7 range is a dead zone at ~2-3%.

**H3 threshold recommendation:** Raise to **6.0**, not 5.0. The 5-6 band (2.9%, 2/68) performs no better than 6-7 (2.1%, 2/97). Raising to 6.0 would cut ~406 low-yield jobs while retaining the 569 jobs in the 6+ bands where 14/256 applied jobs converted (5.5%). The 7+ band alone drives most interview value.

### Q2. Missing Resumes Root Cause (966 → 616 gap)

**Q2a. resume_tier distribution for ai_score >= 4.0:**

| resume_tier    | Count |
|----------------|-------|
| None           | 957   |
| USE_TEMPLATE   | 10    |
| ADAPT_TEMPLATE | 8     |

**Q2b. High-score jobs WITHOUT resume, by resume_tier:**

| resume_tier    | Missing Resume |
|----------------|---------------|
| None           | 349           |
| ADAPT_TEMPLATE | 8             |
| USE_TEMPLATE   | 5             |

**Root cause:** 957/975 high-score jobs have `resume_tier = None` — C2 (tailoring step) was never run for them. The 350 missing resumes are almost entirely from jobs where C2 was skipped, not template routing failures. The 13 jobs with explicit tiers but no resume suggest minor rendering failures.

**Implication for H2:** Backend template is NOT the primary cause of the gap. The gap is a C2 execution gap, not a template gap. H2 remains valid for future quality but doesn't explain the current 350 missing resumes.

### Q3. Search Profile Funnel

| Profile              | Scraped | Filter | High Score | Applied | Interview | Offer | Int. Rate |
|----------------------|---------|--------|------------|---------|-----------|-------|-----------|
| None (manual)        | 70      | 16     | 0          | 70      | 15        | 6     | **21.4%** |
| quant                | 86      | 77     | 63         | 30      | 3         | 0     | **10.0%** |
| backend_data         | 540     | 249    | 131        | 77      | 5         | 1     | 6.5%      |
| ml_data              | 452     | 267    | 240        | 185     | 10        | 2     | 5.4%      |
| ml_research          | 76      | 57     | 27         | 5       | 1         | 0     | 20.0% (n=5) |
| backend_engineering  | 1205    | 625    | 179        | 8       | 0         | 0     | **0.0%**  |
| data_science         | 356     | 221    | 140        | 18      | 0         | 0     | 0.0%      |
| ml_engineering       | 234     | 170    | 106        | 17      | 0         | 1*    | 0.0%      |
| data_engineering     | 81      | 59     | 28         | 7       | 0         | 0     | 0.0%      |
| iamexpat             | 179     | 33     | 11         | 3       | 0         | 0     | 0.0%      |
| ats                  | 594     | 97     | 48         | 8       | 0         | 0     | 0.0%      |
| backend_ai_data      | 10      | 10     | 2          | 0       | 0         | 0     | N/A       |

*ml_engineering shows 1 offer but 0 interviews — likely a data entry issue.

**Key findings:**
- **Manual adds (None profile) dominate:** 21.4% interview rate, 6 of 10 total offers. Manual curation is 3-4x more effective than any automated profile.
- **backend_engineering is pure waste:** 1205 scraped, 8 applied, 0 interviews. Largest scraper volume with zero ROI.
- **Top automated profiles:** quant (10.0%), backend_data (6.5%), ml_data (5.4%)
- **data_science, ml_engineering, data_engineering:** 0% interview rate across 42 applications combined — consider disabling or merging.

### Q4. Template Distribution + Interview Rate

| Template | Resumes | Applied | Interview | Offer | Int. Rate |
|----------|---------|---------|-----------|-------|-----------|
| None     | 608     | 342     | 14        | 3     | 4.1%      |
| ML       | 7       | 0       | 0         | 0     | N/A       |
| DE       | 1       | 0       | 0         | 0     | N/A       |

**Interpretation:** Template routing (C3) is essentially non-functional. 608/616 resumes have no explicit template assignment. The ML and DE templates exist but were rarely used and never led to applications. Template-based interview rate comparison is not possible with current data.

### Q5. Backend-Titled Job Outcomes

**Filter:** title contains "software engineer" or "backend", excludes "data"/"ml"/"ai"

| Metric | Value |
|--------|-------|
| Total analyzed | 604 |
| Applied | 49 |
| Interview | 2 |
| Offer | 1 |
| Interview rate | **4.1%** |

**Template assignment:** 585 = None, 19 = DE (no Backend template used)

**Top-scored unapplied backend jobs** (score 8.5, status=None):
- Software Engineer IV @ myGwork
- Research Software Engineer @ Erasmus MC
- Senior Staff SE - Unity Catalog @ Databricks
- Software Engineer - Backend @ Databricks
- Python SE - Platform @ Channable

**Interpretation:** 604 backend jobs were analyzed but only 49 applied (8.1% apply rate vs 33% overall). Many high-score backend jobs sit unapplied. The 4.1% interview rate is below the 10.7% overall, confirming that backend roles convert worse — likely because the DE template's bio ("Data Engineer...") misrepresents the candidate for pure backend roles.

---

## Updated Recommendations Based on Data

### H3 Threshold: Raise to 6.0 (revised from 5.0)

The data shows the 5-6 band converts at only 2.9% (2/68), no better than the 6-7 band. The 7+ band at 6.3% is where the real value concentrates. Raising from 4.0 → 6.0 would:
- Eliminate 406 low-yield jobs from C2 processing
- Save ~40% of C2 token spend
- Focus the pipeline on the 569 jobs in bands that actually convert
- The 4-5 band's apparent 10% rate (2/20) is not statistically significant

### H2 Backend Template: Still important but secondary

The 350 missing resumes are primarily a C2 execution gap (resume_tier=None), not a template routing failure. However, 604 backend jobs using the DE template bio confirm a quality mismatch. Priority: (1) fix C2 execution gap first, (2) then enable Backend template.

### New finding: backend_engineering profile should be disabled

1205 scraped, 0 interviews. This profile generates massive volume with zero conversion. Disabling it would reduce scraping load by 31% with no interview loss.
