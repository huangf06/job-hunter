# Process Log — Source.ag Data Engineer Interview Prep

**Date:** 2026-02-24 (evening before interview)
**Duration:** ~78 minutes (22:27 - 23:45 CET)
**Interview:** 2026-02-25, 10:30 CET, Round 1 of 3
**Output:** 8 dossier files, ~40 KB total, ~15,000 words

This is the reference case study for the standardized interview prep workflow.

---

## Timeline

### Phase 0: Intel Gathering (22:27 - 22:35 CET, ~8 min)

**Trigger:** User asked "请深度准备我明天的面试" ("Please deeply prepare my interview tomorrow").

**Actions:**
1. Invoked brainstorming skill to plan the approach
2. Read existing interview prep directories (Deloitte, FareHarbor, Nebius) to learn the established file structure
3. Asked user which company — user redirected: "你去google calendar上查一下" ("Go check my Google Calendar")
4. Called Google Calendar API via `src/google_calendar.py` → `list_events()`
   - First attempt failed: wrong method name (`get_events`)
   - Second attempt succeeded
5. **Calendar result:** Source.ag, Data Engineer, 10:30-11:00 CET, Google Meet, interviewer James Godlonton, ATS: Recruitee

**DB Mining (6 queries, 3 failed then corrected):**
- `SELECT * FROM jobs WHERE LOWER(company) LIKE '%source%'` → 2 Source.ag jobs found
- `PRAGMA table_info(jobs)` → schema discovery (after column name errors)
- Full JD extraction (4,941 chars)
- AI analysis from `job_analysis` table → score 6.5/10, recommendation: apply
- Tailored resume JSON → full bullet selections, bio spec, skill categories
- Application status → applied 2026-02-09

**Lesson:** Always run `PRAGMA table_info()` before querying. Column is `description` not `content`, `posted_date` not `date_posted`.

---

### Phase 1: Foundation (22:35 - 22:38 CET, ~3 min)

Created directory `20260225_Source_ag_Data_Engineer/` and wrote:
- `01_job_description.md` — Full JD with tech stack extracted
- `02_ai_analysis.md` — AI scores, gaps, mitigations
- `03_submitted_resume.md` — Resume content from tailored_resume JSON

---

### Phase 2-3: Parallel Research Wave 1 (22:38 - 22:51 CET, ~13 min)

**2 background agents launched simultaneously:**

**Agent 1 — Company Research:**
- Prompt: 10 specific research areas (product, founding, funding, tech stack, culture, etc.)
- Sources searched: source.ag website, about page, careers page, news articles, Glassdoor
- Completed: ~22:51

**Agent 2 — Interviewer Research (James Godlonton):**
- Prompt: role, background, education, thesis, career arc
- Sources: LinkedIn, TheOrg, university repos
- Completed: ~22:46

**Main thread research (while agents ran):**
- Fetched source.ag website, careers page, about page
- Fetched funding press release ($17.5M Series B, Nov 2025)
- Fetched product tiers announcement
- Searched for James on TheOrg

**Key discovery (22:41):** James Godlonton is **Engineering Manager** (promoted from Software Engineer, Aug 2025). This is a hiring manager interview, not a random engineer screen. Changed the entire strategy.

---

### Phase 4: Dossier Assembly (22:42 - 22:46 CET, ~4 min)

Created the remaining files:
- `04_company_deep_dive.md` — 10.2 KB, founding story, funding timeline, products, tech stack, competitors, Glassdoor, Harvest House case study
- `05_interview_strategy.md` — 17.5 KB, 3 narratives, 7 Q&A pairs, STAR examples, questions to ask
- `06_quick_reference.md` — 5.9 KB, dense cheat sheet for during the call
- `07_transcript_and_education.md` — Academic credentials reference

---

### Phase 4.5: Agent Results Enrichment (22:46 - 22:55 CET, ~9 min)

**Agent 2 (James) completed first.** Key findings integrated:
- Full career arc: Amazon AWS intern (Cape Town) → Cambridge BA/MSc → Utrecht MSc AI → NEC R&D → Zurich pre-doc economics → ML Consultant → Helin Data (IoT for Shell, BP) → Source.ag
- Thesis: "Increased Interpretability and Performance in CCTV Anomaly Detection"
- Product Development team: 16 people
- Values inferred: modularity, interpretability, rigorous evaluation

**Agent 1 (Company) completed second.** Key findings integrated:
- Full product suite: Plant App, Workspace, Harvest Forecast, Cultivation Management, Irrigation Control, Cloud API
- Series B: $17.5M, total $60M+
- Harvest House case study: largest tomato grower in NL, 600 ha, 30M consumers
- CEA market: $103B → $175B by 2029
- Glassdoor: 3.7/5, some post-layoff concerns but stabilizing

~15 edit operations across dossier files to incorporate findings.

---

### Phase 5: Interactive Briefing (22:55 - 23:17 CET, ~22 min)

**Briefing delivered in Chinese.** Key points:
- Round 1 of 3, personal/introductory (not technical yet)
- James's 3 likely focus areas: independence, technical foundation, motivation
- Both have MSc AI in Netherlands — shared background for rapport

**User challenge (23:07):** "James是pragmatist, 这一句话是怎么来的？" ("Where did 'pragmatist' come from? Predict his attack vectors.")

**Self-correction:** Acknowledged the label was "too rough." Revised to: "someone with a strong academic foundation who deliberately chose an engineering-implementation path." Predicted 3 attack vectors:
1. **Ownership** (appeared 6 times in JD)
2. **Scale experience** (messy real-world data)
3. **Go language gap**

**User revelation (23:17):** "我就是农民的儿子。我确实对农业有兴趣" ("I'm actually a farmer's son. I'm genuinely interested in agriculture.")

**Impact:** Called this a "杀手锏" (killer advantage). Most data engineer candidates at an AgTech company have purely technical motivations. Wrote a specific 2-sentence script for natural mention. Updated strategy and quick reference files.

---

### Phase 6: Deep Research Wave 2 (23:24 - 23:39 CET, ~15 min)

**4 more background agents launched:**

**Agent 3 — James's MSc Thesis:**
- Fetched actual PDF from Utrecht University's repository (dspace.library.uu.nl)
- Finding: CCTV anomaly detection, values modular decomposition, rigorous evaluation, interpretability

**Agent 4 — Glassdoor Interview Experiences:**
- Found interview format intel, take-home assignment hints, evaluation criteria

**Agent 5 — GitHub & Technical Content:**
- **MAJOR DISCOVERY:** Source.ag GitHub org (`source-ag`) has 10 public repos
- Found `assignment-data-engineering` — the actual Round 2 take-home assignment!
- Assignment: Greenhouse Sensor Data Pipeline, Python, ~4 hours, 7 requirements
- Also found 2021 HN post: "Python, TypeScript and **a bit of** Golang" — Go is secondary!

**Agent 6 — Team Composition:**
- CTO Magnus Hilding: 24 direct/indirect reports
- **No current Data Engineer on the team** — this would be a founding role
- Identified potential Round 2/3 interviewers

**Main thread:**
- Fetched careers page JD → discovered critical JD discrepancy

**JD Discrepancy Discovery:**
| Dimension | LinkedIn | Careers Page |
|-----------|----------|-------------|
| Title | Senior Backend / Data Engineer | Data Engineer |
| Experience | 10+ years | **4+ years** |
| Go | Core requirement | "Contribute to" |
| Specific project | None | "Cloud Modules" for enterprise BI |

---

### Phase 6.5: Final Enrichment (23:39 - 23:45 CET, ~6 min)

- Created `08_take_home_prep.md` — Full assignment breakdown with experience mapping
- Updated all dossier files with Wave 2 findings
- Updated README.md with Source.ag section

---

### Phase 7: Meta-Request (23:42 CET)

User: "你挺牛逼啊。把你今天为我准备面试的完整过程，整理一下存档。并且形成一个标准化的工作流"

("You're pretty impressive. Archive the complete prep process. Create a standardized workflow for future interviews.")

→ Entered plan mode. Plan written but session ended before implementation (context window exhaustion + next morning).

---

## Statistics

| Metric | Count |
|--------|-------|
| Background agents launched | 6 (2 waves: 2 + 4) |
| Web pages fetched (main thread) | 8+ |
| Web searches (main thread) | 3+ |
| DB queries | 6 (3 failed, then corrected) |
| Files created | 8 dossier + 1 README update |
| File edit operations | ~20+ |
| User interactions (substantive) | 4 |
| Total dossier size | ~40 KB, ~15,000 words |

## Key Discoveries (Ranked by Impact)

1. **Take-home assignment on public GitHub** — pre-study the exact Round 2 exercise
2. **JD discrepancy: 4+ years (careers) vs 10+ years (LinkedIn)** — actual bar much lower
3. **James = recently promoted Engineering Manager** — hiring manager interview, not engineer screen
4. **No existing Data Engineer on team** — founding role, parallels GLP experience exactly
5. **User is a farmer's son** — authentic personal connection to AgTech mission
6. **James's career parallels user's** — both MSc AI in NL, both chose engineering path
7. **James's thesis** — values interpretability, rigor, modularity
8. **"A bit of Golang" (2021 HN)** — Go is secondary, removing major anxiety

## What Worked Best

- **Parallel agents** saved ~40 min of sequential research
- **GitHub org search** was the single highest-value action (assignment + HN post + team intel)
- **Asking the user** for personal context (farming background) transformed the strategy
- **Careers page fetch** revealed the JD discrepancy — always fetch both versions
- **Thesis retrieval** gave unique interviewer insight that no other candidate would have

## What to Improve Next Time

1. **Run schema discovery first** — wasted 3 round trips on column name errors
2. **Search GitHub org in Phase 2** — don't wait for Phase 5; it's too high-value to delay
3. **Ask for personal connections early** — the farming background came out at 23:17; should probe at Phase 0
4. **Structure for context window** — write files early, do heavy research after; the session hit context limits
5. **Copy resume PDF** — the `cp` command failed on Windows; use Python `shutil.copy` instead

## Evolution from Previous Preps

| Dimension | Deloitte/FareHarbor (Feb 23) | Source.ag (Feb 25) |
|-----------|----------------------------|-------------------|
| Total content | ~14 KB | ~40 KB (3x) |
| Files | 7 | 8 (+company deep dive, +take-home) |
| Interviewer research | None (generic recruiter) | Full career arc + thesis |
| Company research | Basic Glassdoor + facts | Founding story, funding, products, GitHub |
| Team intel | None | 7+ person org chart |
| Assignment prep | None | Full breakdown + experience mapping |
| Quick reference | 1.5 KB | 5.9 KB (4x) |
| Research agents | 0 | 6 |
