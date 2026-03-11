# Resume v7 Improvements - 2026-03-11

## Context
Second round of improvements based on hiring manager feedback. The v6 resume was "much better" but still had critical issues preventing it from being "send widely without hesitation."

## Critical Issues Addressed

### 1. **2019-2023 Gap Explanation** ✅
**Problem:** Unexplained 4-year chronology gap from August 2019 to September 2023.

**Solution:** Added new experience entry:
```
Independent Investor - Self-Employed
SEPTEMBER 2019 - AUGUST 2023
Managed personal investment portfolio while preparing for graduate studies in AI.
```

**Impact:** Closes the chronology loop without being defensive. Truthful and low-drama.

### 2. **Projects Section Rewrite** ✅
**Problem:** Projects felt "smaller and more academic/personal than the seniority implied by experience section."

**Solutions:**

**Greenhouse Sensor Pipeline:**
- **Before:** "Built a PySpark batch ETL pipeline for 3.8K+ greenhouse sensor snapshots..."
- **After:** "Built a PySpark batch ETL pipeline with Bronze/Silver/Gold data modeling, replayable processing, and explicit data quality checks for sensor telemetry ingestion..."
- **Change:** Removed small scale numbers (3.8K), emphasized architecture and patterns

**Job Search Pipeline:**
- **Before:** "Automated Job Search Pipeline"
- **After:** "Multi-Source Application Tracking Pipeline"
- **Change:** Renamed to sound less self-referential, reframed as employer-relevant data engineering

**Impact:** Projects now support the "credible production DE" narrative instead of weakening it.

## Medium-Severity Improvements

### 3. **Bio Refinement** ✅
**Before:** "...and now seeking full-time Data Engineering roles in the Netherlands."
**After:** "...Recently completed M.Sc. in AI (VU Amsterdam, 8.2 GPA), adding modern ML systems context to production data engineering experience."

**Impact:** Removes passive "seeking" language, ends on capability instead of intention.

### 4. **BQ Investment Bullet Strengthening** ✅
**Before:** "...to ensure data integrity for downstream research and trading."
**After:** "...to ensure data quality for downstream research and trading systems."

**Impact:** More unmistakably DE-focused, emphasizes systems and consumers.

### 5. **Henan Energy Compression** ✅
**Before:** 6 lines + Tech Skills line (9 lines total)
**After:** 3 lines, no Tech Skills line

**Impact:** Reduces clutter from ancient (2010-2013) work, frees space for gap explanation.

### 6. **Project Tech Skills Removal** ✅
**Removed:** "Tech Skills: Python, SQLite, Turso Embedded Replica, CI/CD, Web Scraping, GitHub Actions"

**Impact:** Reduces repetitive clutter, information already in main Technical Skills section.

## Summary of Changes

| Section | Change | Rationale |
|---------|--------|-----------|
| Bio | Removed "seeking" language, emphasized capability | End on strength, not intention |
| GLP Technology | (No change from v6) | Already strong |
| BQ Investment | "data integrity" → "data quality for...systems" | More DE-focused |
| Ele.me | (No change from v6) | Already strong |
| Henan Energy | Compressed from 9 lines to 3 lines | Ancient work, low value |
| **NEW** Independent Investor | Added 2019-2023 entry | Closes chronology gap |
| Projects - Greenhouse | Removed scale, emphasized architecture | Avoid "toy project" signal |
| Projects - Job Search | Renamed, reframed | Less self-referential |
| Projects - Tech Skills | Removed redundant line | Reduce clutter |

## Files Generated
- `templates/de_resume_toni_v7.pdf` - Updated resume
- `templates/de_resume_toni_v6.svg` - Source file (modified in place)

## Remaining Considerations

### Databricks Certification
**Current:** "Databricks Certified Data Engineer Professional (2026)"
**Risk:** If not yet earned, this is a credibility landmine.
**Action needed:** Verify certification status. If not earned, either:
- Remove the line entirely, OR
- Change to "Databricks Data Engineer Professional, scheduled 2026"

### Header Links
**Current:** "LinkedIn | GitHub" (text links)
**Suggestion:** Could be more polished with full URLs, but not critical.

## Expected Outcome

The resume should now:
1. ✅ Pass recruiter 10-second scan (no chronology gaps)
2. ✅ Create interest in hiring manager first read (projects support narrative)
3. ✅ Reduce interview risks (gap explained, projects credible)
4. ✅ Read as "experienced data engineer" not "quant pivot"

**Status:** Should be ready to send widely, pending Databricks cert verification.
