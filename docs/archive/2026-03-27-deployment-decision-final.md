# Deployment Decision Archive: 2026-03-27

## Final Conclusion

The job-hunter pipeline will **remain on GitHub Actions hosted runners**.

## Decision Summary

- No VPS migration
- No self-hosted runner
- No hybrid deployment
- Keep current hosted workflow as the primary runtime

## Why

The main constraint was not raw compute. It was whether LinkedIn stability gains would justify extra infrastructure maintenance.

The final answer was **no**.

For this project stage:

- maintainability matters more than theoretical runtime optimization
- operational simplicity matters more than environment purity
- a personal pipeline should not become an infrastructure management project without strong evidence that migration is necessary

## Revisit Trigger

Reopen this decision only if GitHub-hosted execution becomes clearly inadequate in real operation.

If that happens, the next option to evaluate is:

- **single Linux VPS for the whole main pipeline**

Not hybrid.
