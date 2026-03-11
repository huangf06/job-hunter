# GitHub Projects Audit - New Session Prompt

**Date:** 2026-03-09
**Purpose:** Audit GitHub repositories and select/package projects for resume
**Context:** Completing bullet library audit after finishing work experience section

---

## Session Objective

Analyze all GitHub repositories for user `huang` and:
1. Identify projects suitable for resume inclusion
2. Evaluate technical depth and business value
3. Write evidence-backed project bullets
4. Apply same 7-point quality framework used for work experience

---

## Background Context

### **Completed Work (Previous Session)**

**Work Experience Audit (4/4 companies completed):**
1. ✅ GLP Technology (5 bullets) — Fintech, founding member
2. ✅ Baiquan Investment (4 bullets) — Quant, 14.6% return
3. ✅ Ele.me (4 bullets) — E-commerce, $651K fraud detection
4. ✅ Henan Energy (4 bullets) — Fortune 500, $42M profit
5. ✅ Independent Investor (3 bullets) — Positioned as "Independent Quantitative Researcher"

**Total: 20 high-quality work experience bullets**

**Audit Framework (7-Point Quality Standard):**
1. 事实准确性 (Factual accuracy) — Must have code evidence
2. 量化指标 (Quantification) — Specific numbers/metrics
3. 技术深度 (Technical depth) — Clear technical stack
4. 因果逻辑 (Causal logic) — Action → Result chain
5. 独特性 (Uniqueness) — Differentiated from other bullets
6. ATS 友好 (ATS-friendly) — Relevant keywords
7. 叙事角色 (Narrative role) — context_setter / depth_prover / foundation / extension / breadth

**Quality Threshold:** ≥ 5/7 to keep, < 5/7 to rewrite or delete

---

## Current Resume Structure

```
Work Experience (2010-2025, 15 years):
├─ Henan Energy (2010-2013) — Data automation, Fortune 500
├─ Ele.me (2013-2015) — Fraud detection, SQL optimization
├─ Baiquan Investment (2015-2017) — Quant research, 14.6% return
├─ GLP Technology (2017-2019) — Founding member, credit engine
├─ Independent Researcher (2019-2023) — Quant research, M.Sc. prep
└─ VU Amsterdam (2023-2025) — M.Sc. AI, Deep RL

Projects (To be audited):
├─ M.Sc. Thesis: Uncertainty Quantification in Deep RL
├─ GitHub Projects: [To be identified]
└─ [Other projects if any]
```

---

## Task Breakdown

### **Phase 1: Repository Discovery**

**Action:** Scan all GitHub repositories for user `huang`

**Evaluation Criteria:**
- ✅ Has substantial code (not just forks or trivial repos)
- ✅ Demonstrates technical skills relevant to data/ML roles
- ✅ Has clear README or documentation
- ✅ Shows completion (not abandoned halfway)
- ✅ Unique/interesting (not just tutorial follow-alongs)

**Output:** List of candidate repositories with:
- Repository name
- Description
- Tech stack
- Lines of code / commits
- Last updated date
- Initial assessment (High/Medium/Low priority)

---

### **Phase 2: Deep Dive Analysis**

**For each High/Medium priority repository:**

1. **Read README and code structure**
2. **Identify key technical contributions:**
   - What problem does it solve?
   - What technologies are used?
   - What's the technical depth?
   - Any quantifiable metrics? (performance, accuracy, scale)

3. **Assess resume-worthiness:**
   - Does it demonstrate skills relevant to target roles?
   - Is it defensible in interviews? (can explain every line)
   - Does it differentiate from other candidates?
   - Is there a clear narrative?

4. **Apply 7-point framework:**
   - Factual accuracy (code exists, claims are verifiable)
   - Quantification (metrics, benchmarks, comparisons)
   - Technical depth (algorithms, architecture, tools)
   - Causal logic (problem → solution → result)
   - Uniqueness (not just another MNIST classifier)
   - ATS-friendly (relevant keywords)
   - Narrative role (how does it fit in career story?)

---

### **Phase 3: Bullet Writing**

**For selected projects, write bullets following this structure:**

```yaml
projects:

  # M.Sc. Thesis (already exists in bullet_library.yaml)
  thesis_uq_rl:
    title: "Uncertainty Quantification Benchmark for Deep RL"
    institution: "VU Amsterdam"
    period: "Feb. 2025 - Aug. 2025"

    verified_bullets:
      - id: thesis_uq_framework
        narrative_role: depth_prover
        content: "[Evidence-backed bullet with quantification]"

  # GitHub Project 1 (example structure)
  project_name:
    title: "[Project Title]"
    github_url: "https://github.com/huang/repo-name"
    period: "[Date range]"
    technical_skills: "[Tech stack]"

    verified_bullets:
      - id: project_bullet_id
        narrative_role: [role]
        content: "[Evidence-backed bullet]"
```

**Bullet Template:**
> "Built/Developed/Implemented [WHAT] using [TECH STACK], achieving [QUANTIFIABLE RESULT] — [BUSINESS VALUE / TECHNICAL INSIGHT]."

**Examples from work experience:**
- "Built anti-fraud detection system identifying 51,000+ suspicious order clusters using 3 pattern detection algorithms..."
- "Architected event-driven backtesting framework (Python + MATLAB) supporting strategy simulation, walk-forward validation, and 15+ performance metrics..."

---

### **Phase 4: Strategic Selection**

**Recommended number of projects:**
- **Minimum:** 1 (M.Sc. thesis only)
- **Standard:** 2-3 (thesis + 1-2 GitHub projects)
- **Maximum:** 4 (thesis + 3 GitHub projects)

**Selection criteria:**
1. **Relevance to target roles** (Data Engineer, Data Analyst, Quant)
2. **Technical differentiation** (shows skills not in work experience)
3. **Recency** (prefer projects from 2020+)
4. **Completeness** (finished projects > abandoned experiments)
5. **Uniqueness** (interesting problem/approach)

**Strategic positioning:**
- If applying to **Data Engineer**: Prioritize infrastructure/pipeline projects
- If applying to **Data Analyst**: Prioritize analysis/visualization projects
- If applying to **Quant Researcher**: Prioritize ML/statistical modeling projects

---

## Known Projects (From Previous Context)

### **M.Sc. Thesis (Confirmed)**
- **Title:** Uncertainty Quantification Benchmark for Deep RL
- **Institution:** VU Amsterdam
- **Period:** Feb 2025 - Aug 2025
- **Tech Stack:** Python, PyTorch, JAX, HPC (SLURM)
- **Key Result:** QR-DQN superiority with 31% lower CRPS (p < 0.001)
- **Status:** Already has bullet in bullet_library.yaml (lines 291-299)

### **Potential GitHub Projects (To be verified)**
Based on previous mentions in conversation:
- Deribit options trading analysis
- GraphSAGE implementation
- ObamaTTS (text-to-speech)
- LifeOS (personal productivity system)
- Python-dojo (LeetCode practice)

**Note:** These need verification — check if repos exist, have substantial code, and are resume-worthy.

---

## Deliverables

### **1. Repository Inventory Report**
```markdown
# GitHub Projects Inventory

## High Priority (Resume-Worthy)
1. [Repo Name] - [Brief description] - [Tech stack] - [LOC/Commits]
2. ...

## Medium Priority (Potential)
1. ...

## Low Priority (Skip)
1. ...
```

### **2. Deep Dive Analysis (Per Selected Project)**
```markdown
# Project: [Name]

## Overview
- Repository: [URL]
- Tech Stack: [List]
- Period: [Date range]
- Status: [Complete/In-progress]

## Technical Depth
- Problem: [What problem does it solve?]
- Approach: [How does it solve it?]
- Key Contributions: [What's unique/interesting?]

## 7-Point Evaluation
1. Factual Accuracy: ✅/⚠️/❌
2. Quantification: ✅/⚠️/❌
3. Technical Depth: ✅/⚠️/❌
4. Causal Logic: ✅/⚠️/❌
5. Uniqueness: ✅/⚠️/❌
6. ATS-Friendly: ✅/⚠️/❌
7. Narrative Role: [context_setter/depth_prover/foundation/extension/breadth]

**Score:** X/7

## Recommended Bullet
```yaml
- id: project_id
  narrative_role: [role]
  content: "[Bullet text]"
```

## Interview Defense
- Can explain: [Key technical details]
- Can demo: [Yes/No]
- Can discuss trade-offs: [Yes/No]
```

### **3. Updated bullet_library.yaml**
Add selected projects to the `projects:` section with:
- Project metadata (title, URL, period, tech stack)
- Verified bullets with narrative roles
- Recommended sequences (if applicable)

---

## Quality Standards (Same as Work Experience)

### **Must Have:**
- ✅ Code evidence (repository exists, substantial commits)
- ✅ Technical depth (not trivial, shows expertise)
- ✅ Clear narrative (problem → solution → result)
- ✅ Interview defensible (can explain every detail)

### **Should Have:**
- ✅ Quantification (metrics, benchmarks, comparisons)
- ✅ Uniqueness (differentiated from common projects)
- ✅ Recency (prefer 2020+)
- ✅ Completion (finished, not abandoned)

### **Nice to Have:**
- ✅ Documentation (README, comments)
- ✅ Tests (shows engineering rigor)
- ✅ Real-world application (not just toy example)
- ✅ Novel approach (interesting algorithm/architecture)

---

## Strategic Considerations

### **What Makes a Good Resume Project?**

**Good:**
- ✅ Solves a real problem (not just "learning X")
- ✅ Shows technical depth (algorithms, architecture, optimization)
- ✅ Has measurable results (accuracy, performance, scale)
- ✅ Demonstrates skills relevant to target roles
- ✅ Unique/interesting (stands out from other candidates)

**Bad:**
- ❌ Tutorial follow-along (no original contribution)
- ❌ Abandoned halfway (shows lack of follow-through)
- ❌ Trivial scope (too simple, no depth)
- ❌ Irrelevant to target roles (game dev for data engineer role)
- ❌ Can't defend in interview (copied code, don't understand)

---

## Interview Preparation

**For each selected project, prepare:**

1. **Elevator pitch (30 seconds):**
   > "I built [WHAT] to solve [PROBLEM]. I used [TECH] and achieved [RESULT]. The interesting challenge was [TECHNICAL DETAIL]."

2. **Technical deep dive (5 minutes):**
   - Architecture overview
   - Key algorithms/techniques
   - Trade-offs and decisions
   - Results and learnings

3. **Demo readiness:**
   - Can you run it live?
   - Can you show code?
   - Can you explain every line?

---

## Reference Materials

**Completed Work Evidence Reports:**
- `docs/work_evidence/glp_technology_deep_work_report.md` (not created, but GLP bullets audited)
- `docs/work_evidence/baiquan_ronghui_deep_work_report.md` (965 lines)
- `docs/work_evidence/eleme_deep_work_report.md` (965 lines)
- `docs/work_evidence/henan_energy_deep_work_report.md` (851 lines)

**Audit Summary Reports:**
- `docs/work_evidence/baiquan_bullet_audit_summary.md`
- `docs/work_evidence/eleme_bullet_audit_summary.md`
- `docs/work_evidence/henan_energy_bullet_audit_summary.md`

**Strategic Positioning:**
- `docs/work_evidence/independent_investor_strategic_positioning.md`
- `docs/work_evidence/aoshen_business_deletion_decision.md`

**Current Bullet Library:**
- `assets/bullet_library.yaml` (lines 286-299 for thesis project)

---

## Success Criteria

**Session is successful if:**
1. ✅ All GitHub repositories scanned and categorized
2. ✅ 2-4 projects selected for resume inclusion
3. ✅ Each selected project has evidence-backed bullets (7-point framework)
4. ✅ Projects added to bullet_library.yaml with narrative roles
5. ✅ Interview defense strategy prepared for each project
6. ✅ Strategic recommendations for which projects to use for which roles

---

## Next Steps After This Session

1. **Cover Letter Templates** — Generate role-specific cover letters
2. **Interview STAR Stories** — Prepare detailed stories for each bullet
3. **Resume Assembly** — Generate final resume versions for different roles
4. **Application Strategy** — Prioritize companies and roles

---

## Important Notes

**Maintain 100% Honesty:**
- Only include projects with substantial code evidence
- Don't exaggerate technical complexity
- Don't claim results you can't defend
- If a project is incomplete, either finish it or don't include it

**Strategic Positioning:**
- Projects should complement work experience, not duplicate
- Show skills not evident in work history (e.g., specific ML techniques)
- Demonstrate continuous learning and initiative
- Connect to career narrative (why these projects?)

**Quality Over Quantity:**
- 2 excellent projects > 5 mediocre projects
- Each project should pass 7-point framework (≥ 5/7)
- Focus on depth, not breadth

---

## GitHub Access

**User's GitHub username:** [To be confirmed in session]

**Potential usernames to check:**
- `huang`
- `huangfei`
- `fei-huang`
- [User should provide correct username]

**Access method:**
- Public repositories: Can access directly via GitHub API or web
- Private repositories: May need user to share or make public temporarily

---

**Ready to start! Please provide your GitHub username and we'll begin the audit.**
