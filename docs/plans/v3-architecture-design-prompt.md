# Job Hunter v3.0 Architecture Design — Guided Prompt

**Purpose**: Step-by-step architecture design session. Each section is a self-contained design question. Answer them in order — later sections depend on earlier decisions.

**Context**: Job Hunter is a single-user Python job automation system. Current stack: Python scripts + Turso (libSQL cloud DB) + GitHub Actions CI/CD + Claude Opus API. The user (Fei Huang) is an M.Sc. AI targeting DE/MLE roles in the Netherlands.

**Current pain (in priority order)**:
1. Pipeline has been offline for 3 weeks — resume generation flow broken due to SVG transition
2. Resume/cover letter output quality not reliable — CL looks obviously AI-generated
3. No feedback loop — applications go out but outcomes aren't tracked back
4. No full cloud automation — local steps still required (prepare, finalize)
5. Codebase coupling makes changes risky and slow

**Hard constraints**:
- Python stack (no language rewrite)
- Single user, few thousand jobs, low write concurrency
- CI writes → local reads (no simultaneous multi-writer)
- Must be incrementally deployable (can't stop job hunting for weeks)
- Budget-conscious but willing to pay if justified

---

## Phase 1: Resume Generation Pipeline (BLOCKING — do this first)

The resume generation flow is the critical path. Without it, no applications go out. The user recently designed SVG-based resumes with better visual quality, but the automation pipeline was built around HTML/Jinja2 → Playwright → PDF.

### Questions to answer:

**1.1 What is the SVG resume authoring model?**

Examine the SVG resume templates in `templates/`. Understand:
- How are they created? (Figma export? Hand-coded SVG? Inkscape?)
- What is parameterized vs. hardcoded? (Are bullet texts embedded in the SVG? Or is there a data layer?)
- How does the current `svg_auto_optimizer.py` work? What does it take as input and produce as output?
- How does `svg_to_pdf.py` work? What are its dependencies?
- What is the relationship between the SVG templates and the `bullet_library.yaml` system?

**1.2 What should the target resume generation flow be?**

Design the end-to-end flow from "AI analysis says this job scores 7.0" to "PDF ready to submit". Consider:

- Option A: Keep HTML/Jinja2 flow for automation, use SVG only for manual/high-priority applications
- Option B: Parameterize SVG templates (text injection into SVG XML), convert SVG → PDF
- Option C: Use a different rendering approach entirely (e.g., Typst, LaTeX, WeasyPrint)
- Option D: Hybrid — AI generates structured resume JSON, a renderer (SVG or HTML) consumes it

For each option, evaluate:
- Can it run headless in GitHub Actions? (No GUI, no display server)
- Does it produce consistent visual output? (No layout drift across runs)
- How much storage per resume? (Current concern: "大量的存储空间")
- Can the bullet_library system feed into it?
- Can it be validated before rendering? (Current ResumeValidator checks)

**1.3 What should the cover letter strategy be?**

Current CL output "looks obviously AI-generated". Options:
- Better prompting (few-shot with hand-written CL examples from `cl_knowledge_base.yaml`)
- Template-driven: fixed structure with AI filling only specific sections
- Reduce scope: shorter CL with 2-3 high-signal paragraphs, not full-page essays
- Skip CL entirely for platforms that don't require it

What does the user's `cl_knowledge_base.yaml` contain? How is it used today? What makes a good CL in the user's domain?

**1.4 Storage and artifact management**

Current problem: resume PDFs take "大量的存储空间" — this blocks full cloud automation.
- How large are the generated PDFs? (Check `output/` directory)
- How many are generated per pipeline run?
- Options: GitHub Actions artifact storage (90-day retention), cloud object storage (R2/S3), git LFS, or just don't store — regenerate on demand from the spec
- What actually needs to be stored vs. what can be regenerated?

### Deliverable for Phase 1:
A concrete resume+CL generation flow that:
- Runs in GitHub Actions without local steps
- Integrates SVG design quality with automated parameterization
- Produces resume + optional CL as artifacts
- Uses bullet_library + ResumeValidator
- Has a clear storage strategy

---

## Phase 2: Application Pipeline (restore daily operation)

Once resumes can be generated, restore the scrape → filter → score → analyze → generate → submit-ready pipeline.

### Questions to answer:

**2.1 What is the minimal viable daily pipeline?**

Map out the exact steps that need to run automatically every day:
```
Trigger (cron) → Scrape → Filter → Score → [AI Analyze] → [Generate Resume] → [Notify User]
```

For each step:
- What runs in CI vs. what needs human decision?
- Where is the "human checkpoint"? (e.g., user reviews AI-selected jobs before resume generation, or fully automatic?)
- What notification does the user need? (Telegram? Email? Discord?)
- What is the failure mode and recovery? (If AI analysis fails for 3 jobs, do the other 47 still proceed?)

**2.2 The "prepare → apply → finalize" workflow**

Currently requires local commands. Options for making this cloud-native:
- Option A: CI generates ready-to-send packages → uploads to cloud storage → user downloads and applies manually
- Option B: CI generates + publishes a checklist → user marks applied/skipped via Telegram bot or web form → CI finalizes
- Option C: CI does everything including auto-apply (Greenhouse/Lever API) for high-confidence matches

Which option fits the user's actual workflow? How does the user currently apply? (Copy-paste from ready_to_send? Upload PDF on job sites? Click "Easy Apply"?)

**2.3 Database: keep Turso or migrate?**

Given:
- Few thousand rows, single writer (CI), occasional reader (local)
- Turso free tier works but UX is "一般"
- libsql has Windows bugs requiring workarounds
- No multi-writer concurrency needed

Evaluate:
- **Keep Turso**: It works, free, already integrated. Pain is mainly the libsql client bugs.
- **Turso but HTTP-only**: Skip libsql embedded replica entirely. Use Turso's HTTP API from both CI and local. Simpler code, no sync/replica complexity. Latency is fine for this scale.
- **Supabase (Postgres)**: Free tier, proper SQL, better tooling, but more complex than SQLite dialect.
- **PlanetScale / Neon**: Similar to Supabase.
- **SQLite in git**: For this scale, could just commit the DB file. CI updates it, pushes. Local pulls. Zero infrastructure. Crude but effective for a single-user system.
- **SQLite on Cloudflare D1**: Free tier, HTTP API, SQLite-compatible.

Recommendation criteria: simplicity > features > cost. The current Turso integration is 200+ lines of sync/recovery/workaround code. Can we get to 20 lines?

### Deliverable for Phase 2:
A working daily pipeline definition with:
- Clear CI workflow steps
- Human checkpoint strategy
- Notification design
- Database decision
- No local commands required for normal operation

---

## Phase 3: Feedback Loop (track outcomes)

Applications go out but outcomes aren't tracked back. This breaks the ability to improve.

### Questions to answer:

**3.1 What outcomes matter?**

Define the states an application can be in:
```
applied → [no response / rejected / phone screen → technical → offer → accepted/declined]
```

Where does outcome data come from?
- User manually updates (simplest)
- Gmail parsing (automated but complex)
- Calendar events (interview scheduled = progressing)
- Recruiter email patterns (rejection template detection)

**3.2 What is the minimum viable feedback loop?**

Not "auto-parse all recruiter emails". Start with:
- User can mark application status via Telegram bot command or simple CLI
- Daily/weekly summary: "You have 15 pending (>7 days), 3 interviews scheduled, 2 rejections this week"
- Monthly report: "Conversion rate: 12% screen rate, top-scoring jobs convert 2x better"

Is this enough? Or does the user need automated email parsing from day one?

**3.3 How does feedback improve the pipeline?**

Once we have outcome data:
- Can we retrain scoring thresholds? (If AI score 7+ jobs get interviews but 5-6 don't, adjust)
- Can we improve resume selection? (If certain bullet combinations lead to more callbacks)
- Or is this just for the user's situational awareness?

### Deliverable for Phase 3:
Application state tracking design with:
- State machine definition
- Data entry method (manual, semi-auto, or auto)
- Reporting/notification format
- How feedback connects back to scoring/generation

---

## Phase 4: Code Architecture (make changes safe)

Only after the pipeline works and feedback flows should we refactor the code.

### Questions to answer:

**4.1 What refactoring is actually needed now?**

Not "what would be ideal" but "what prevents us from making the changes in Phase 1-3 safely?"
- Is the DB coupling actually blocking anything in Phase 1-3?
- Is the monolithic CLI actually a problem if CI only runs 3-4 commands?
- Is the config scatter actually causing bugs?

Only refactor what's in the way. List the specific changes from Phase 1-3 that are hard to make with the current code structure.

**4.2 What is the minimal architectural change?**

Maybe it's not "6 repository protocols + UnitOfWork + stage engine". Maybe it's:
- Extract a `ResumeService` that owns the full generate flow
- Extract an `ApplicationTracker` that owns state transitions
- Keep everything else as-is

**4.3 Migration strategy**

Whatever architecture changes are needed:
- Can they be done as "strangler fig" (new code beside old, switch over gradually)?
- What is the testing strategy? (Golden-master comparison? Manual smoke test? Pytest?)
- What is the rollback plan for each change?

### Deliverable for Phase 4:
Minimal refactoring plan driven by actual Phase 1-3 requirements, not theoretical cleanliness.

---

## Phase 5: Future Features (only after Phase 1-4 stable)

Park these here. Do not design them until the pipeline is running and producing quality output daily.

- Email auto-classification and application status update
- Auto-apply for specific platforms (Greenhouse/Lever API)
- Tracer links in resume PDFs
- Archetype-based resume framing
- Web dashboard
- Interview prep automation

For each: write one sentence on "what would have to be true before we build this?"

---

## How to Use This Prompt

Run this as a multi-session design process:

1. **Session 1**: Phase 1 only. Read all SVG/resume/CL related code. Make concrete decisions about the rendering pipeline. Output: resume generation design doc.

2. **Session 2**: Phase 2 only. Map the full daily pipeline. Make the database decision. Output: pipeline design doc + CI workflow draft.

3. **Session 3**: Phase 3 only. Design the feedback loop. Output: application tracking design doc.

4. **Session 4**: Phase 4 only. Based on decisions from Sessions 1-3, identify what code changes are actually needed. Output: refactoring plan.

5. **Session 5**: Review all decisions together. Check for consistency. Write the implementation plan with ordering and dependencies.

Each session should:
- Start by reading the relevant code (not just the design docs)
- Ask clarifying questions before committing to decisions
- End with a concrete, implementable design (not "we could do A or B")
- Identify what to prototype/spike before committing
