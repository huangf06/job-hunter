# DE Toni SVG Design

Date: 2026-03-10
Status: Approved for implementation

## Goal

Create a Data Engineer resume SVG by filling Fei Huang's approved DE content baseline into `templates/toni_copy.svg` while preserving Toni Kendel's original visual language as closely as possible.

## Layout Rules

- Preserve Toni's two-column layout, typography hierarchy, and spacing rhythm.
- Preserve Toni's header, bio, education, experience, projects, skills, certifications, and languages sections.
- Left column starts `PROFESSIONAL EXPERIENCE`.
- If the left column cannot contain the full experience section, the remaining experience entries continue at the top of the right column.
- The right column only starts `SELECTED PROJECTS` after all carried-over experience entries are complete.
- Do not add soft-skills blocks.
- Do not redesign the template; adapt content to the existing template.

## Content Rules

- Use the canonical DE content baseline from `docs/plans/2026-03-10-de-resume-content-spec.md`.
- Prioritize the standard one-page DE baseline:
  - Canonical DE bio
  - VU Amsterdam + Tsinghua education
  - GLP, Baiquan, Ele.me, Henan
  - Greenhouse project
  - Thesis project
  - Technical skills
  - Certification
  - Languages
- Use compressed wording where needed to preserve the Toni layout.

## Output

- Create a new file: `templates/de_resume_toni_v1.svg`
- Keep `templates/toni_copy.svg` unchanged
