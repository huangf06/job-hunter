# Codex Review Prompt: Block D Render Design v2

## Your Role

You are reviewing **revision v2** of a design document for the Block D (Resume Renderer) audit+simplify redesign. The design is at `docs/plans/2026-03-30-block-d-render-design.md`.

## Context

One prior review round:
- v1 → Codex: "Request revision" (2 blocking + 7 additional findings). All addressed in v2.

Prior review prompt: `docs/plans/2026-03-30-block-d-codex-review-prompt.md`.

## What to Verify

This is a second-pass review. The core approach (6 targeted changes to an existing 655-line renderer) was not challenged. Two blocking items and several additional findings were raised. Verify they are resolved:

### Blocking #1: Change 4 scope narrowed

v1 said "renderer does no validation." v2 should say "delete only `_validate_tailored_structure()`, keep `ResumeValidator.validate()` and `_post_render_qa()`."

Verify:
- Is the distinction explicit in §3.1 (design principles) and Change 4?
- Is the defense-in-depth rationale stated (CLI direct callers at `resume_renderer.py:638`)?
- Does the test plan include a test that `ResumeValidator.validate()` still runs in the renderer?

### Blocking #2: Change 1 failure policy

v1 did not decide whether `--generate` failure should fail the workflow or only notify.

Verify:
- Is there an explicit decision with rationale?
- Is it consistent with the existing steps' `continue-on-error` policy?

### Additional findings from v1

| Finding | Expected resolution |
|---------|-------------------|
| `_render_adapt_template()` unguarded `json.loads()` | Added to Change 6 with try/except |
| Missing `slot_schema` guard | Added to Change 6 |
| `UNIQUE(job_id, role_type)` impact | Noted in Change 5 with migration decision |
| `adapt_html` removal scope unclear | Clarified: removed from registry schema entirely |
| `_detect_role_type()` called "dead code" | Corrected to "outdated code" |
| Submit-dir race condition | Documented as accepted risk |
| 6 missing test cases | Added to test plan |

### Cross-checks

- Does the test plan now cover all changed code paths? Count the tests against the changes.
- Is there anything in the "not in scope" section that should be in scope?
- Can a developer implement this design without asking clarifying questions?

## How to Review

- Read the "Revision History" section first to see what changed
- Verify each row in the table above against the actual design text
- This should be a fast review — the scope of changes is narrow
- Focus on: are there any remaining ambiguities or gaps that would block implementation?

## Output Format

- **Verdict**: Approve / Approve with notes / Request revision
- **Blocking #1 resolved?** Yes/No + rationale
- **Blocking #2 resolved?** Yes/No + rationale
- **Additional findings addressed?** Yes/No per item
- **Implementation readiness**: Ready / Not ready + what's missing
