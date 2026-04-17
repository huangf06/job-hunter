# Pre-Revert Tier Distribution Baseline (2026-04-17)

Query: tier distribution of applications submitted 2026-04-02 to 2026-04-17.

```sql
SELECT a.resume_tier, a.template_id_final, COUNT(*) as n
FROM job_analysis a JOIN applications app ON a.job_id = app.job_id
WHERE app.applied_at >= '2026-04-02'
GROUP BY a.resume_tier, a.template_id_final
ORDER BY n DESC;
```

Result:

| resume_tier | template_id_final | n |
|-------------|-------------------|---|
| USE_TEMPLATE | DE | 35 |
| USE_TEMPLATE | ML | 21 |
| ADAPT_TEMPLATE | DE | 10 |
| USE_TEMPLATE | DS | 5 |
| ADAPT_TEMPLATE | ML | 2 |
| FULL_CUSTOMIZE | DE | 1 |

**Totals:**
- USE_TEMPLATE (static PDF copy, zero tailoring): **61 / 74 = 82%**
- ADAPT_TEMPLATE (zone single-page): **12 / 74 = 16%**
- FULL_CUSTOMIZE (flow-layout per-job): **1 / 74 = 1%**

**Outcome:** 0 interview invitations across all 74.

After the revert (Phases 1-3 of implementation plan), this distribution must shift to 100% FULL_CUSTOMIZE. Compared against the pre-upgrade ~3.5% interview baseline.
