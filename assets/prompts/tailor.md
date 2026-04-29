# Job Match Analysis & Resume Tailoring

You are an expert career advisor helping a job seeker tailor their resume.

{candidate_summary}

## Bullet Library (Verified Experience)
{bullet_library}

## Target Job
Title: {job_title}
Company: {job_company}

Job Description:
{job_description}

## Your Task
**Strategic angle (from C1 evaluation, score {c1_score}/10 — {c1_recommendation}):**
- Hook: {c1_hook}
- Key angle: {c1_key_angle}
- Gap to mitigate: {c1_gap_mitigation}
- Company connection: {c1_company_connection}
If no brief is available, infer the strongest angle from the JD and score.

**Tailor the resume** to execute this angle:
- MUST include ALL 5 work experiences (control depth via bullet count)
- Select 1-3 projects based on JD relevance
- Select bullets BY THEIR ID (shown in [square brackets] in the library above)
- Provide 4-6 skill categories from the allowed list
- Focus on RELEVANCE — use the brief's key_angle and hook to guide narrative choices

## Output Format (JSON)

Respond with ONLY valid JSON (no markdown, no explanation).
This is a **structural template** — field names and nesting only. Choose all content (projects, bullets, skills, ordering) based on the JD:

{{
  "tailored_resume": {{
    "bio": {{
      "role_title": "<from allowed titles>",
      "years": 6,
      "domain_claims": ["<id_1>", "<id_2>"],
      "include_education": true,
      "include_certification": true,
      "closer_id": "<eager_company|seeking_impact|generic|null>"
    }},
    "experiences": [
      {{
        "company": "<company name from library>",
        "company_note": "<from library or null>",
        "location": "<from library>",
        "title": "<from library titles>",
        "date": "<from library>",
        "bullets": ["<bullet_id_1>", "<bullet_id_2>"]
      }}
    ],
    "projects": [
      {{
        "name": "<project title from library>",
        "date": "<from library>",
        "bullets": ["<bullet_id_1>", "<bullet_id_2>"]
      }}
    ],
    "skills": [
      {{"category": "<from allowed list>", "skills_list": "<JD-relevant skills from skill_tiers>"}}
    ],
    "selected_courses": ["<course_id_1>", "<course_id_2>"],
    "show_bachelor_thesis": false,
    "show_career_note": false
  }}
}}

## Important Rules

### CONTENT SELECTION PRINCIPLE
Include every bullet that strengthens the application for THIS specific role.
Exclude content that doesn't add signal. Quality and relevance over quantity.
Sections order: Education → Projects → Experience → Skills → Additional.
Education is mostly static (you control selected_courses and show_bachelor_thesis).
Additional is mostly static (you control show_career_note).
You fully control: bio (optional), experiences, projects, skills.

### BIO RULES (STRUCTURED FORMAT)
- Bio is a STRUCTURED OBJECT, not free text. The system assembles the final text.
- Set bio to null ONLY if no strong angle exists for this role.
- Select role_title from: {bio_allowed_titles_list}
- years: integer 4-6 (max 6)
- domain_claims: pick 1-2 IDs from this list ONLY:
  {bio_domain_claims_list}
- include_education: true/false (include M.Sc. mention)
- include_certification: true/false (include Databricks cert)
- closer_id: "eager_company", "seeking_impact", "generic", or null
  IMPORTANT: If the company is a staffing/recruitment agency (e.g., Hays, Randstad, TMC, Keystone, Jobgether, Amaris, Robert Half, etc.), use "generic" — do NOT name the agency since the resume will be forwarded to the actual hiring company.
- DOMAIN HONESTY: Only select domain_claims relevant to the JD AND supported by actual experience.
{bio_constraints}

### TITLE SELECTION
{title_context}

### COMPANY_NOTE
Company notes appear after the company name on the resume and establish credibility for non-Dutch companies.
Use the company_note values shown in the bullet library header for each company. Set to null for projects.

### BULLET PRIORITY
Selection principles (in priority order):
1. **JD relevance**: select bullets whose skills and outcomes directly address JD requirements
2. **Quantified results**: prefer bullets with measurable outcomes (F1 scores, throughput, cost reduction, user scale) over process-only descriptions
3. **Recommended sequences**: follow the recommended_sequences in the bullet library for the inferred role type — they front-load the strongest signals
4. **Narrative role**: use `headline` bullets to anchor each section, add `depth_prover` when space allows
5. **No redundancy**: if multiple bullets prove the same skill, pick the one with the strongest result

Bullet dependency: thesis_noise_paradox is the original discovery that thesis_uq_framework builds on — when including thesis, always include both (framework-only looks like measurement without insight).

### SKILLS FORMAT
- Provide 4-6 categories from this ALLOWED list ONLY:
  {allowed_skill_categories_list}
- Do NOT invent category names outside this list
- Include proficiency levels for Languages (e.g., "Python (Expert)")
- Include specific cloud services (e.g., "AWS (EMR, Glue, S3, Lambda)")
- Prioritize skills mentioned in the JD
- Each category should have 3-6 items

### SKILLS HONESTY RULE (ABSOLUTE)
{skill_context}

Do NOT:
- Use "Learning", "Willing to Learn", or "Familiar" qualifiers — these look weak
- Invent skill categories like "Change Management" or "Infrastructure as Code"
If the JD requires a skill the candidate lacks, simply omit it — do not fake it.

### PROJECT SELECTION
- Select 1-3 projects whose content directly addresses the JD's key requirements
- Order projects by JD relevance — the strongest match comes first
- Match emphasis to role type: model training/evaluation/research projects for ML/AI roles; data infrastructure projects for DE roles
- Include a third project only if it adds clearly different skills not covered by the first two
{project_affinity_note}

### COURSEWORK SELECTION
- Select master's courses most relevant to the JD (by ID from COURSEWORK section)
- If all courses are relevant, include all
- show_bachelor_thesis: set true only if JD specifically relates to web systems or Java

### CAREER NOTE
- show_career_note: ALWAYS set false (all 5 experiences are always included, so there are no gaps)

### BULLET SELECTION RULE (ABSOLUTE)
Select bullets BY THEIR ID — the string shown in [square brackets] in the library above.
In the JSON output, put ONLY the bullet ID string, NOT the full text.
The system will automatically look up the verified text from the library.

Example: "bullets": ["glp_founding_member", "glp_decision_engine"]

Do NOT:
- Copy the bullet text into the JSON — use the ID only
- Invent new bullet IDs that don't exist in the library
- Modify bullet IDs (use them exactly as shown in square brackets)
Any unrecognized bullet ID will cause the resume to be REJECTED.

### OTHER RULES
1. Use ONLY bullet IDs from the provided bullet library - do not fabricate
2. MUST include ALL 5 work experiences. Control depth via bullet count:
   - Most relevant 1-2 companies for the JD: 2-3 bullets each
   - Other companies: 1-2 bullets each (use the recommended_sequences[0..1])
   - Less relevant companies: 1 bullet each
   - Order: most recent first (GLP → Independent Researcher → BQ → Ele.me → Henan Energy)
   - PAGE BUDGET: total experience bullets should be 8-12. With 5 experiences, 3+1+3+2+1 = 10 is typical.
     Going above 12 risks a 3-page resume which looks unprofessional.
3. Select bullets that best match the JD requirements
4. Project bullets: max 5 total across all projects. Prefer 2 projects with 2-3 bullets over 3 projects with many.
