# Job Match Evaluation

## Candidate Profile
Name: Fei Huang
Education: M.Sc. in Artificial Intelligence, VU Amsterdam (GPA 8.2/10, Aug 2025)
Bachelor: B.Eng. Industrial Engineering, Tsinghua University (#1 in China)
Certification: Databricks Certified Data Engineer Professional (2026)

Key Skills: Python (Expert), PyTorch, PySpark, SQL, Delta Lake, AWS, Docker, Airflow
Experience: ~6 years across data science, quantitative research, data engineering
Recent: Financial Data Lakehouse project (Databricks, Spark, AWS, Delta Lake)
Thesis: Uncertainty Quantification in Deep Reinforcement Learning

## Hard Reject Signals (score 1-2, recommendation: SKIP)
If ANY of the following is true, score overall 1-2 and recommend SKIP:
- Title indicates non-target role: recruiter, HR, policy, accountant,
  finance manager, pure marketing/sales/legal (without data/ML qualifier)
- Primary tech stack is clearly wrong: embedded systems, kernel, PLC,
  SIEM, network engineering, release engineering, pure frontend
- JD requires visa/residency candidate cannot provide:
  "no visa sponsorship", "must be located in [non-NL country]"
- JD requires 5+ years of specific tech candidate lacks
  (Java, C++, Scala, Ruby, .NET, Azure)
- Role is too senior: Director, VP, CTO, Head of, Principal
  (exception: "Senior Data/ML/AI Engineer/Scientist" is fine)
- JD requires native Dutch speaker
- Compensation far below market (< EUR 3000/month)

## Scoring Guidelines
{scoring_guidelines}

## Target Job
Title: {job_title}
Company: {job_company}

Job Description:
{job_description}

## Resume Routing
Template hint: {preselected_template_id} (confidence: {preselected_confidence})
{ambiguous_warning}
Template determines C2 role framing (DE/ML/DS) for bio, titles, project ordering.
If the pre-selected template is wrong for this role, set override to true.

## Output (JSON only, no markdown)
{{
  "scoring": {{
    "overall_score": 7,
    "skill_match": 8,
    "experience_fit": 7,
    "growth_potential": 7,
    "recommendation": "APPLY",
    "reasoning": "2-3 sentences explaining the score"
  }},
  "application_brief": {{
    "hook": "One sentence: strongest connection between candidate and role",
    "key_angle": "One sentence: main selling point for this application",
    "gap_mitigation": "One sentence: biggest gap and how to address it, or null",
    "company_connection": "Personal connection to company mission, or null if none"
  }},
  "resume_routing": {{
    "template_id": "{preselected_template_id}",
    "override": false,
    "override_reason": null
  }}
}}

recommendation values: "APPLY_NOW" (>={apply_now_threshold}), "APPLY" (>={apply_threshold}), "MAYBE" (>={maybe_threshold}), "SKIP" (<{maybe_threshold})
