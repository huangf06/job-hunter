# Process Log - kaiko.ai Senior Evaluation ML Engineer

**Prep date:** 2026-03-11
**Company:** kaiko.ai
**Role:** Senior Evaluation ML Engineer
**Interview format:** 30-minute online interview
**Interview time:** 2026-03-11 11:30-12:00
**Attendees from invite:** Irina Rusu (Senior Recruiter), Max Feucht (Machine Learning Engineer)
**Status:** Prep dossier created

## Phase 0 - Intel Gathering

- User provided the invite text and attendee names.
- Queried local SQLite database and found the target role:
  - `job_id`: `69d2dfb9a403`
  - Applied on `2026-03-02`
  - Application status: `interview`
  - Existing resume PDF and cover letter were generated on `2026-03-02`
- Extracted the full LinkedIn JD, AI analysis, tailored resume JSON, resume HTML, and cover letter text from local project data.

## Phase 0.5 - Calendar Attempt

- Attempted to query Google Calendar via `src/google_calendar.py`.
- First sandboxed attempt failed due local credential file permissions.
- Escalated attempt could read credentials, but token refresh failed with `400 Client Error` from `oauth2.googleapis.com/token`.
- Result: exact scheduled date/time and meeting link could not be auto-confirmed from Calendar in this session.

## Phase 1 - Foundation Files

- Created the dossier directory using today's date as a placeholder:
  - `interview_prep/20260311_kaiko_ai_Senior_Evaluation_ML_Engineer/`
- Wrote:
  - `01_job_description.md`
  - `02_ai_analysis.md`
  - `03_submitted_resume.md`

## Phase 2 - Company Research

- Reviewed the JD snapshot stored locally in the database.
- Pulled current company information from official public sources:
  - `https://www.kaiko.ai`
  - `https://www.kaiko.ai/insights`
  - `https://github.com/kaiko-ai`
- Key findings:
  - Mission is clinical AI for oncology and hospital workflows.
  - Public site currently says 120+ people; the March 2 JD snapshot said 80+ people.
  - kaiko highlights hospital partnerships including NKI, LUMC, UMCU, and REGA.
  - Public GitHub org exists; `eva` appears directly relevant to evaluation infrastructure.

## Phase 3 - Interviewer Research

- Public web results for the two attendees were sparse.
- Verified facts:
  - `Irina Rusu` appears in the invite as Senior Recruiter.
  - `Max Feucht` appears in the invite as Machine Learning Engineer.
- Working assumption for strategy:
  - This call is probably a hybrid first-round screen: recruiter-led with a technical peer checking substance.
- All interviewer-specific behavioral predictions in this dossier are explicitly marked as inference, not confirmed fact.

## Phase 4 - Strategy Assembly

- Wrote:
  - `04_company_deep_dive.md`
  - `05_interview_strategy.md`
  - `06_quick_reference.md`
  - `07_transcript_and_education.md`
  - `08_take_home_prep.md`
  - `09_post_interview_notes.md`

## High-Value Findings

1. This is a very strong fit on evaluation rigor: thesis benchmarking + statistical testing maps directly to the role.
2. The biggest gap is oncology vocabulary and clinical workflow familiarity, not core ML or data engineering ability.
3. The likely first-round attack surface is not "can you code" but "can you explain trustworthy evaluation, work cross-functionally, and handle high-stakes domains with humility."
4. The recruiter-plus-ML-engineer combination suggests they are checking both motivation/values and whether your examples are concrete enough for a technical team.

## Open Gaps

- Public background on Max Feucht was limited, so interviewer-specific tailoring is intentionally conservative.
- No public kaiko-specific take-home was found in this session.
