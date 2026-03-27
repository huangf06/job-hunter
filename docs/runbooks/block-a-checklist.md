# Block A Operational Checklist

## When Daily Scrape Looks Wrong

1. Open [data/scrape_metrics.json](C:/Users/huang/github/job-hunter/.worktrees/block-a-rebuild/data/scrape_metrics.json).
2. Check `total.severity`.
3. Identify which platform has `errors` or `targets_failed > 0`.
4. Rerun only the failing platform with `--dry-run`.

## LinkedIn Checklist

1. Run:

```bash
python scripts/scrape.py --platform linkedin --profile data_engineering --dry-run
```

2. Inspect `platforms.linkedin.diagnostics` in `data/scrape_metrics.json`.
3. If `session_status=auth_redirect`, refresh `config/linkedin_cookies.json`.
4. If `session_status=challenge`, inspect `challenge_marker` and `last_url` before changing cookies.
5. If `last_stage=navigation_timeout`, retry once before assuming cookie or parser failure.
6. If `query_failures>0`, use `diagnostics.queries` to isolate the exact failing query.
7. If `cards_found=0` across healthy queries, suspect DOM or search-result layout drift.

## Greenhouse Checklist

1. Run:

```bash
python scripts/scrape.py --platform greenhouse --dry-run
```

2. Inspect `target_errors`.
3. If one company returns `404`, fix or remove that board in `config/target_companies.yaml`.
4. Treat isolated board failure as config drift unless multiple boards fail at once.

## IamExpat Checklist

1. Remember it is frozen out of `--all` by design.
2. Only run it manually when you explicitly want backfill:

```bash
python scripts/scrape.py --platform iamexpat --dry-run
```

3. If it is slow, that is not a daily-pipeline regression.
4. Do not move it back into `--all` without revisiting runtime budget and scrape semantics.

## Before Escalating A Failure

1. Confirm the failing platform can be reproduced in isolated `--dry-run`.
2. Capture the relevant `diagnostics` block from `scrape_metrics.json`.
3. Capture any `target_errors`.
4. Only then decide whether this is:
   - runtime environment issue
   - config drift
   - parser/layout regression
   - auth/cookie failure
