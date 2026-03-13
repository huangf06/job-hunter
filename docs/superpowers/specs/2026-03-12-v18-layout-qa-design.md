# v18 Layout QA Design

**Goal:** Improve the visual consistency of `templates/de_resume_toni_v18.svg` without changing resume content.

**Scope:**
- Normalize right-column section spacing.
- Smooth a few manual line breaks so the right column reads with a more consistent width.
- Make small left-column spacing adjustments only if needed for overall balance.
- Re-export the PDF and visually verify the result.

**Non-goals:**
- No wording changes.
- No structural redesign.
- No new sections or entries.

**Recommended approach:**
Use the existing two-column SVG layout and apply small coordinate and line-break edits directly in the file. This preserves the current design while fixing the uneven rhythm the user noticed. Avoid grid-level rework because the resume is already in final-send territory and aggressive layout changes would add unnecessary risk.

**Validation:**
- Export `templates/de_resume_toni_v18.svg` to PDF.
- Inspect the exported page for:
  - section-to-section spacing consistency on the right
  - balanced line lengths in thesis/projects/skills text
  - no new crowding in the left column
  - no clipping near the bottom of the page
