# Block B+C Unified Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Simplify Block B to whitelist-only objective rules, split Block C into C1 (Evaluate) + C2 (Tailor Resume), remove Anthropic SDK dependency.

**Architecture:** Block B drops all semantic rules (reject patterns, body keyword counting, location/experience checks) to a whitelist-only filter. Block C becomes two Claude Code CLI calls: C1 scores + produces application brief, C2 tailors resume for high-scoring jobs only.

**Tech Stack:** Python 3.11, PyYAML, pytest, Claude Code CLI (`claude -p`)

**Design Doc:** `docs/plans/2026-03-28-block-bc-unified-design.md`

---

### Task 1: Simplify Block B — Strip filters.yaml

**Files:**
- Modify: `config/base/filters.yaml:93-122` (non_target_role rule)
- Modify: `config/base/filters.yaml:141-156` (wrong_tech_stack body keywords)
- Delete sections: `config/base/filters.yaml:201-215` (specific_tech_experience)
- Delete sections: `config/base/filters.yaml:217-233` (experience_too_high)
- Delete sections: `config/base/filters.yaml:255-267` (location_restricted)

**Step 1: Remove reject patterns from non_target_role (rule 2)**

In `config/base/filters.yaml`, delete `title_hard_reject_patterns`, `title_reject_patterns`, and `reject_exceptions` from the `non_target_role` rule. Keep only `title_must_contain_one_of` and metadata fields.

Before (lines 57-122):
```yaml
  non_target_role:
    enabled: true
    priority: 2
    type: "title_check"
    description: "Job title doesn't match any target role category"
    title_must_contain_one_of:
      - "data"
      # ... (32 keywords)
      - "applied scientist"
    # === hard reject patterns ===
    title_hard_reject_patterns:
      - "\\bpolicy\\b"
      # ... (13 patterns)
    # === soft reject patterns ===
    title_reject_patterns:
      - "\\bmarketing\\b"
      # ... (5 patterns)
    reject_exceptions:
      - "data"
      # ... (7 keywords)
```

After:
```yaml
  non_target_role:
    enabled: true
    priority: 2
    type: "title_check"
    description: "Job title doesn't match any target role category"
    title_must_contain_one_of:
      - "data"
      - "dataflow"
      - "machine learning"
      - "ml"
      - "ai"
      - "genai"
      - "artificial intelligence"
      - "computer vision"
      - "machine vision"
      - "vision"
      - "python"
      - "quant"
      - "quantitative"
      - "analytics"
      - "bi"
      - "scientist"
      - "research"
      - "researcher"
      - "algorithm"
      - "deep learning"
      - "nlp"
      - "llm"
      - "mlops"
      - "software"
      - "backend"
      - "infrastructure"
      - "platform"
      - "pipeline"
      - "applied scientist"
```

**Step 2: Remove body_irrelevant_keywords from wrong_tech_stack (rule 3)**

Keep only `title_patterns` and `exceptions`. Delete `body_irrelevant_keywords` and `body_irrelevant_threshold`.

After:
```yaml
  wrong_tech_stack:
    enabled: true
    priority: 3
    type: "tech_stack"
    description: "Primary tech stack doesn't match candidate skills"
    title_patterns:
      - "\\b(flutter|swift|kotlin|scala)\\s*(developer|engineer)\\b"
      - "\\b(android|ios|mobile)\\s*(developer|engineer)\\b"
      - "\\b(frontend|front-end|front end|ui/ux)\\s*(developer|engineer)\\b"
      - "\\b(devops|sre|site reliability)\\s*(engineer)\\b"
      - "\\bdotnet\\b|\\.net(?!\\w)|\\bc#(?!\\w)"
      - "\\bjava\\b(?!.*(?:script|data|ml|machine learning|ai))"
      - "\\bruby\\b"
      - "\\breact\\b.*\\b(developer|engineer)\\b"
      - "\\bangular\\b.*\\b(developer|engineer)\\b"
    exceptions:
      - "data"
      - "machine learning"
      - "ml"
      - "ai"
      - "quant"
      - "scientist"
      - "research"
      - "analytics"
```

**Step 3: Delete specific_tech_experience, experience_too_high, location_restricted rules entirely**

Remove these three rule blocks from `filters.yaml`. Update metadata version to 3.0.

**Step 4: Commit**

```bash
git add config/base/filters.yaml
git commit -m "feat(block-b): simplify filters.yaml to whitelist-only design

Remove title_hard_reject_patterns, title_reject_patterns, reject_exceptions
from non_target_role. Remove body_irrelevant_keywords from wrong_tech_stack.
Delete specific_tech_experience, location_restricted, experience_too_high rules.
All semantic judgments moved to Block C (AI)."
```

---

### Task 2: Simplify Block B — Strip hard_filter.py

**Files:**
- Modify: `src/hard_filter.py:114-170` (title_check handler)
- Modify: `src/hard_filter.py:173-206` (tech_stack handler)

**Step 1: Simplify title_check handler**

In `src/hard_filter.py`, the `title_check` handler (lines 114-170) currently has three sections: hard_reject_patterns, soft_reject_patterns, whitelist. Simplify to: exceptions check + whitelist only.

Replace lines 114-170 with:
```python
            # --- Title-based role check ---
            elif rule_type == 'title_check':
                # Check exceptions first (against title, not body)
                exceptions = rule_config.get('exceptions', [])
                if any(
                    re.search(keyword_boundary_pattern(exc.lower().strip()), title)
                    for exc in exceptions if exc.strip()
                ):
                    continue

                # Title reject patterns (simple list, no soft/hard distinction)
                reject_patterns = rule_config.get('title_reject_patterns', [])
                for pattern in reject_patterns:
                    try:
                        if re.search(pattern, title, re.IGNORECASE):
                            return FilterResult(
                                job_id=job_id, passed=False,
                                reject_reason=rule_name,
                                filter_version="2.0",
                                matched_rules=json.dumps({"rejected_pattern": pattern})
                            )
                    except re.error:
                        continue

                # Whitelist - title must contain at least one target keyword
                must_contain = rule_config.get('title_must_contain_one_of', [])
                if must_contain:
                    found = any(
                        re.search(keyword_boundary_pattern(kw.lower().strip()), title)
                        for kw in must_contain if kw.strip()
                    )
                    if not found:
                        return FilterResult(
                            job_id=job_id, passed=False,
                            reject_reason=rule_name,
                            filter_version="2.0",
                            matched_rules=json.dumps({"no_target_keyword_in_title": title})
                        )
```

Note: `title_reject_patterns` is kept as a field name for `senior_management` rule (rule 6) which still uses it. The code just no longer has hard/soft distinction — any `title_reject_patterns` match rejects, `exceptions` bypass the whole rule.

The deleted code: `title_hard_reject_patterns` handling (lines 124-135) and `reject_exceptions` handling (lines 138-155).

**Step 2: Simplify tech_stack handler**

In `src/hard_filter.py`, the `tech_stack` handler (lines 173-206) has title_patterns + body_irrelevant_keywords. Remove body keyword counting (lines 197-206).

Replace lines 173-206 with:
```python
            # --- Tech stack check (title only) ---
            elif rule_type == 'tech_stack':
                exceptions = [e.lower().strip() for e in rule_config.get('exceptions', [])]

                # Skip if title contains an exception keyword (word-boundary match)
                title_has_exception = any(
                    re.search(keyword_boundary_pattern(exc), title) for exc in exceptions if exc
                )

                if not title_has_exception:
                    # Check title patterns
                    title_patterns = rule_config.get('title_patterns', [])
                    for pattern in title_patterns:
                        try:
                            if re.search(pattern, title, re.IGNORECASE):
                                return FilterResult(
                                    job_id=job_id, passed=False,
                                    reject_reason=rule_name,
                                    filter_version="2.0",
                                    matched_rules=json.dumps({"title_pattern": pattern})
                                )
                        except re.error:
                            continue
```

**Step 3: Run existing tests to see what breaks**

Run: `python -m pytest tests/test_hard_filter.py -v 2>&1 | head -80`

Expected: Many failures in tests that depend on deleted features (reject patterns, body keywords, specific_tech_experience, location_restricted).

**Step 4: Commit**

```bash
git add src/hard_filter.py
git commit -m "feat(block-b): simplify hard_filter.py to match whitelist-only design

Remove hard_reject_patterns/reject_exceptions from title_check handler.
Remove body_irrelevant_keywords counting from tech_stack handler.
Title_check now: exceptions → reject_patterns → whitelist (no hard/soft split).
Tech_stack now: title patterns only."
```

---

### Task 3: Rewrite Block B tests

**Files:**
- Rewrite: `tests/test_hard_filter.py`

**Step 1: Delete test classes for removed features**

Delete these classes entirely:
- `TestDutchRequired` lines 279-308 — **KEEP** (rule still exists)
- `TestWrongTechStack` lines 311-411 — delete body keyword tests, keep title pattern tests
- `TestSpecificTechExperience` lines 476-524 — **DELETE** (rule removed)
- `TestLocationRestricted` lines 527-564 — **DELETE** (rule removed)

In `TestWrongRole` (lines 126-193): delete tests for hard_reject vs soft_reject distinction (any test checking reject_exceptions bypass like "Marketing Data Analyst passes").

In `TestWrongTechStack`: delete tests for body_irrelevant_keywords threshold.

**Step 2: Update remaining tests**

Tests that checked `reject_reason == "non_target_role"` with `matched_rules` containing `"rejected_pattern"` need updating — now only `"no_target_keyword_in_title"` is possible from non_target_role.

Jobs like "Security Engineer" or "Marketing Manager" that were previously hard/soft rejected now PASS Block B (they contain no whitelist keyword... wait, they DON'T contain whitelist keywords, so they still get rejected by whitelist). Verify: "Security Engineer" has no keyword from whitelist → rejected by `no_target_keyword_in_title`. "Marketing Data Analyst" has "data" + "analyst" → passes whitelist. This is correct behavior.

Update `TestWrongRole` to only test whitelist behavior:
- "Account Manager" → rejected (no whitelist keyword)
- "Data Engineer" → passes
- "Marketing Data Analyst" → passes (has "data")
- "Embedded ML Engineer" → passes (has "ml")
- "Security Engineer" → rejected (no whitelist keyword)
- "BI Analyst" → passes (has "bi")

**Step 3: Update TestWrongTechStack**

Keep title pattern tests. Remove body keyword tests. Example:
- "Flutter Developer" → rejected (title pattern match, no exception)
- "Data Flutter Developer" → passes (exception "data" in title)
- ".NET Developer" → rejected
- "React Engineer" → rejected

**Step 4: Update TestPriorityOrder**

Adjust if needed — priority order logic unchanged, but some rules are gone.

**Step 5: Run tests**

Run: `python -m pytest tests/test_hard_filter.py -v`
Expected: All pass.

**Step 6: Commit**

```bash
git add tests/test_hard_filter.py
git commit -m "test(block-b): rewrite tests for whitelist-only design

Remove tests for deleted features: reject_patterns, body_irrelevant_keywords,
specific_tech_experience, location_restricted. Update TestWrongRole to test
whitelist-only behavior. ~40-45 focused tests."
```

---

### Task 4: Clean up ai_config.yaml

**Files:**
- Modify: `config/ai_config.yaml`

**Step 1: Remove SDK model configs, budget, and stale thresholds**

Delete these sections:
- `models.opus` (lines 27-34)
- `models.kimi` (lines 37-43)
- `budget` section (lines 62-70, including `cost_per_1k_tokens`)
- `thresholds.rule_score_for_ai` (line 52)

Keep:
- `models.claude_code` (lines 19-23)
- `thresholds.ai_score_generate_resume: 4.0` (update from 5.0 to 4.0 per design)
- `thresholds.ai_score_apply_now: 7.0`

**Step 2: Remove --model choices from CLI**

In `scripts/job_pipeline.py:771-772`, remove the `--model` argument entirely:
```python
    # DELETE these lines:
    parser.add_argument('--model', type=str, default=None,
                        choices=['opus', 'kimi'],
                        help='AI model: opus (Claude) or kimi')
```

In `scripts/job_pipeline.py:246-250`, remove `model` parameter from `ai_analyze_jobs`:
```python
    def ai_analyze_jobs(self, limit: int = None) -> int:
        """AI 分析通过预筛选的职位"""
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()
        return analyzer.analyze_batch(limit=limit)
```

**Step 3: Commit**

```bash
git add config/ai_config.yaml scripts/job_pipeline.py
git commit -m "chore: remove SDK model configs, budget tracking, --model CLI flag

Flat subscription makes per-token budgeting irrelevant. Only Claude Code
CLI path remains."
```

---

### Task 5: Strip SDK from AIAnalyzer

**Files:**
- Modify: `src/ai_analyzer.py`

**Step 1: Remove SDK imports and init**

In `src/ai_analyzer.py:35`, remove:
```python
from anthropic import Anthropic, RateLimitError, APITimeoutError, AuthenticationError, APIConnectionError, InternalServerError
```

In `__init__` (lines 52-80), remove all SDK-related branches:
- Remove `model_override` parameter
- Remove provider/model/auth_type detection from config
- Remove `_init_client()` call
- Keep bullet_library loading and validator init

New `__init__`:
```python
    def __init__(self, config_path: Path = None):
        self.config = self._load_config(config_path)
        self.bullet_library = self._load_bullet_library()
        self.valid_bullets = self._extract_valid_bullets()
        self.bullet_id_lookup = self._build_bullet_id_lookup()
        self.validator = ResumeValidator()
        print(f"[AI Analyzer] Claude Code CLI mode")
        print(f"[AI Analyzer] Loaded {len(self.bullet_id_lookup)} bullet IDs")
```

**Step 2: Delete `_init_client()` method (lines 89-100)**

**Step 3: In `analyze_job()` (lines 757-905), delete the SDK branch (lines 791-905)**

Keep only the Claude Code CLI path. The method becomes:
```python
    def analyze_job(self, job: Dict) -> Optional[AnalysisResult]:
        """分析单个职位: 评分 + 简历定制"""
        job_id = job['id']
        prompt = self._build_prompt(job)

        text = self._analyze_via_claude_code(prompt)
        if not text:
            return AnalysisResult(
                job_id=job_id, ai_score=0.0,
                recommendation='REJECTED',
                reasoning='Claude Code CLI returned empty response',
                tailored_resume='{}',
                model='claude_code', tokens_used=0,
            )

        parsed = self._parse_response(text)
        if not parsed:
            preview = text[:300].replace('\n', ' ')
            print(f"  [WARN] Failed to parse response for {job_id}")
            return AnalysisResult(
                job_id=job_id, ai_score=0.0,
                recommendation='REJECTED',
                reasoning=f'[PARSE_FAIL] {preview}',
                tailored_resume='{}',
                model='claude_code', tokens_used=0,
            )

        return self._post_parse_analysis(job_id, job, parsed, tokens_used=0, prompt=prompt)
```

**Step 4: Run any existing AI analyzer tests**

Run: `python -m pytest tests/ -k "ai_anal" -v 2>&1 | head -20`
(May not have tests — that's OK, will add in Task 7)

**Step 5: Commit**

```bash
git add src/ai_analyzer.py
git commit -m "refactor(block-c): remove Anthropic SDK, keep Claude Code CLI only

Delete _init_client, bearer auth, API key handling, SDK call branch in
analyze_job. AIAnalyzer.__init__ no longer takes model_override."
```

---

### Task 6: Split AIAnalyzer into C1 (Evaluate) + C2 (Tailor)

**Files:**
- Modify: `src/ai_analyzer.py`
- Modify: `config/ai_config.yaml` (add `prompts.evaluator`)
- Modify: `scripts/job_pipeline.py` (add `--ai-evaluate`, `--ai-tailor`)
- Modify: `src/db/job_db.py` (add `update_analysis_resume`, `get_jobs_needing_tailor`)

This is the largest task. Sub-steps:

**Step 1: Add C1 evaluate prompt to ai_config.yaml**

Add `prompts.evaluator` — a short prompt for scoring + application brief. ~2000 chars. Does NOT include bullet library.

```yaml
prompts:
  evaluator: |
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

    ## Output (JSON only, no markdown)
    {{
      "scoring": {{
        "overall_score": 7.5,
        "skill_match": 8.0,
        "experience_fit": 7.0,
        "growth_potential": 7.5,
        "recommendation": "APPLY",
        "reasoning": "2-3 sentences explaining the score"
      }},
      "application_brief": {{
        "hook": "One sentence: strongest connection between candidate and role",
        "key_angle": "One sentence: main selling point for this application",
        "gap_mitigation": "One sentence: biggest gap and how to address it, or null",
        "company_connection": "Personal connection to company mission, or null if none"
      }}
    }}

    recommendation values: "APPLY_NOW" (>={apply_now_threshold}), "APPLY" (>={apply_threshold}), "MAYBE" (>={maybe_threshold}), "SKIP" (<{maybe_threshold})
```

Rename existing `prompts.analyzer` to `prompts.tailor` and strip scoring logic from it (keep only bullet library + resume tailoring rules).

**Step 2: Add DB methods for C2 workflow**

In `src/db/job_db.py`, add two methods after `save_analysis` (line 884):

```python
    def update_analysis_resume(self, job_id: str, tailored_resume: str):
        """Update tailored_resume for an existing analysis (C2 writes to C1's row)."""
        with self._get_conn(sync_before=False) as conn:
            conn.execute("""
                UPDATE job_analysis
                SET tailored_resume = ?
                WHERE job_id = ?
            """, (tailored_resume, job_id))

    def get_jobs_needing_tailor(self, min_score: float = 4.0, limit: int = None) -> List[Dict]:
        """Get jobs with C1 evaluation but no C2 tailored resume yet."""
        with self._get_conn() as conn:
            query = """
                SELECT j.*, a.ai_score, a.recommendation, a.reasoning
                FROM jobs j
                JOIN job_analysis a ON j.id = a.job_id
                LEFT JOIN applications app ON j.id = app.job_id
                WHERE a.ai_score >= ?
                  AND (a.tailored_resume IS NULL OR a.tailored_resume = '{}')
                  AND app.job_id IS NULL
                ORDER BY a.ai_score DESC
            """
            params = [min_score]
            if limit is not None:
                query += " LIMIT ?"
                params.append(limit)
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
```

**Step 3: Split AIAnalyzer methods**

Add `evaluate_job()` and `tailor_resume()` alongside existing `analyze_job()`. Keep `analyze_job()` as a convenience that calls both (for `--analyze-job JOB_ID` single-job debugging).

```python
    def evaluate_job(self, job: Dict) -> Optional[AnalysisResult]:
        """C1: Score + application brief. Short prompt, fast."""
        job_id = job['id']
        prompt = self._build_evaluate_prompt(job)
        text = self._call_claude(prompt)
        if not text:
            return AnalysisResult(
                job_id=job_id, ai_score=0.0,
                recommendation='REJECTED',
                reasoning='Claude Code CLI returned empty response',
                tailored_resume='{}',
                model='claude_code', tokens_used=0,
            )
        parsed = self._parse_response(text)
        if not parsed:
            return AnalysisResult(
                job_id=job_id, ai_score=0.0,
                recommendation='REJECTED',
                reasoning=f'[PARSE_FAIL] {text[:300]}',
                tailored_resume='{}',
                model='claude_code', tokens_used=0,
            )
        scoring = parsed.get('scoring', {})
        brief = parsed.get('application_brief', {})
        return AnalysisResult(
            job_id=job_id,
            ai_score=float(scoring.get('overall_score', 0)),
            skill_match=float(scoring.get('skill_match', 0)),
            experience_fit=float(scoring.get('experience_fit', 0)),
            growth_potential=float(scoring.get('growth_potential', 0)),
            recommendation=scoring.get('recommendation', 'SKIP'),
            reasoning=json.dumps({"reasoning": scoring.get('reasoning', ''),
                                   "application_brief": brief}, ensure_ascii=False),
            tailored_resume='{}',
            model='claude_code', tokens_used=0,
        )

    def tailor_resume(self, job: Dict, analysis: Dict) -> Optional[str]:
        """C2: Resume tailoring. Long prompt, only for high-scoring jobs.
        Returns tailored_resume JSON string, or None on failure."""
        prompt = self._build_tailor_prompt(job, analysis)
        text = self._call_claude(prompt)
        if not text:
            return None
        parsed = self._parse_response(text)
        if not parsed:
            return None
        tailored = parsed.get('tailored_resume', {})
        tailored, bullet_errors = self._resolve_bullet_ids(tailored)
        self._inject_technical_skills(tailored)
        if bullet_errors:
            for err in bullet_errors:
                print(f"    [BULLET WARN] {err}")
        # Bio assembly
        bio_spec = tailored.get('bio')
        assembled_bio, bio_errors = self._assemble_bio(bio_spec, job)
        if bio_errors:
            for err in bio_errors:
                print(f"    [BIO ERROR] {err}")
            return None
        tailored['bio'] = assembled_bio
        # Validation
        validation = self.validator.validate(tailored, job)
        if not validation.passed:
            for err in validation.errors:
                print(f"    [VALIDATION] {err}")
            return None
        return json.dumps(tailored, ensure_ascii=False)
```

**Step 4: Add `_build_evaluate_prompt()` and `_build_tailor_prompt()`**

`_build_evaluate_prompt`: Uses `prompts.evaluator` template, substitutes job fields and scoring guidelines. Does NOT include bullet library.

`_build_tailor_prompt`: Uses `prompts.tailor` template (the old `prompts.analyzer` with scoring logic stripped). Includes bullet library + C1 reasoning as context.

**Step 5: Add batch methods**

```python
    def evaluate_batch(self, limit: int = None) -> int:
        """C1: Evaluate all jobs needing analysis."""
        jobs = self.db.get_jobs_needing_analysis(limit=limit)
        count = 0
        for job in jobs:
            result = self.evaluate_job(job)
            if result:
                self.db.save_analysis(result)
                count += 1
        return count

    def tailor_batch(self, min_score: float = 4.0, limit: int = None) -> int:
        """C2: Tailor resumes for evaluated jobs above threshold."""
        jobs = self.db.get_jobs_needing_tailor(min_score=min_score, limit=limit)
        count = 0
        for job in jobs:
            analysis = self.db.get_analysis(job['id'])
            resume_json = self.tailor_resume(job, analysis)
            if resume_json:
                self.db.update_analysis_resume(job['id'], resume_json)
                count += 1
        return count
```

**Step 6: Rename `_call_claude` from `_analyze_via_claude_code`**

Rename the method for clarity. Same logic, just cleaner name.

**Step 7: Commit**

```bash
git add src/ai_analyzer.py src/db/job_db.py config/ai_config.yaml
git commit -m "feat(block-c): split AI into C1 (evaluate) + C2 (tailor)

C1: short prompt, scoring + application brief, runs on all filtered jobs.
C2: long prompt, resume tailoring, runs only on score >= 4.0.
Add evaluate_job(), tailor_resume(), evaluate_batch(), tailor_batch().
Add DB methods: update_analysis_resume(), get_jobs_needing_tailor()."
```

---

### Task 7: Add CLI commands for C1/C2

**Files:**
- Modify: `scripts/job_pipeline.py`

**Step 1: Add --ai-evaluate and --ai-tailor argparse args**

After `--ai-analyze` (line 761):
```python
    parser.add_argument('--ai-evaluate', action='store_true',
                        help='Run AI evaluation (C1: scoring + brief) on filtered jobs')
    parser.add_argument('--ai-tailor', action='store_true',
                        help='Run AI resume tailoring (C2) on evaluated jobs with score >= 4.0')
```

**Step 2: Add handler methods in JobPipeline class**

After `ai_analyze_jobs` (line 246):
```python
    def ai_evaluate_jobs(self, limit: int = None) -> int:
        """C1: AI evaluation (scoring + application brief)"""
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()
        return analyzer.evaluate_batch(limit=limit)

    def ai_tailor_jobs(self, min_score: float = 4.0, limit: int = None) -> int:
        """C2: AI resume tailoring for high-scoring jobs"""
        from src.ai_analyzer import AIAnalyzer
        analyzer = AIAnalyzer()
        return analyzer.tailor_batch(min_score=min_score, limit=limit)
```

**Step 3: Wire up in main()**

Find the section that handles `args.ai_analyze` and add:
```python
    if args.ai_evaluate:
        pipeline.ai_evaluate_jobs(limit=args.limit)
    if args.ai_tailor:
        pipeline.ai_tailor_jobs(min_score=args.min_score or 4.0, limit=args.limit)
```

Update `--ai-analyze` to call both C1 and C2 sequentially (backward compat):
```python
    if args.ai_analyze:
        pipeline.ai_evaluate_jobs(limit=args.limit)
        pipeline.ai_tailor_jobs(min_score=args.min_score or 4.0, limit=args.limit)
```

**Step 4: Commit**

```bash
git add scripts/job_pipeline.py
git commit -m "feat(cli): add --ai-evaluate and --ai-tailor commands

--ai-evaluate: C1 only (scoring + brief)
--ai-tailor: C2 only (resume tailoring for score >= 4.0)
--ai-analyze: runs both C1 + C2 sequentially (backward compat)"
```

---

### Task 8: Update CI workflow

**Files:**
- Modify: `.github/workflows/job-pipeline-optimized.yml`

**Step 1: Uncomment and split AI step into C1 + C2**

Replace the commented-out AI step (lines 128-145) with:

```yaml
      # ==========================================
      # Step 3: AI Evaluate (C1: scoring + brief)
      # ==========================================
      - name: AI Evaluate (C1)
        id: ai_evaluate
        run: |
          echo "=== Running AI evaluation (C1) ==="
          python scripts/job_pipeline.py --ai-evaluate --limit 30

      # ==========================================
      # Step 4: AI Tailor (C2: resume generation)
      # ==========================================
      - name: AI Tailor (C2)
        id: ai_tailor
        run: |
          echo "=== Running AI resume tailoring (C2) ==="
          python scripts/job_pipeline.py --ai-tailor --limit 30
```

Update notification step to check both:
```yaml
          [ "${{ steps.ai_evaluate.outcome }}" == "failure" ] && FAILED_STEPS="${FAILED_STEPS:+$FAILED_STEPS, }ai-evaluate"
          [ "${{ steps.ai_tailor.outcome }}" == "failure" ] && FAILED_STEPS="${FAILED_STEPS:+$FAILED_STEPS, }ai-tailor"
```

**Step 2: Commit**

```bash
git add .github/workflows/job-pipeline-optimized.yml
git commit -m "ci: split AI step into C1 (evaluate) + C2 (tailor)

C1 failure preserves scoring. C2 timeout can be retried with --ai-tailor."
```

---

### Task 9: Update architecture doc and CLAUDE.md

**Files:**
- Modify: `docs/plans/2026-03-27-pipeline-block-architecture.md`
- Modify: `CLAUDE.md`

**Step 1: Update Block B section in architecture doc**

Replace the "三层设计" section with whitelist-only description. Update rule table (8 rules, simplified). Remove deleted rules.

**Step 2: Update Block C section in architecture doc**

Replace single-call description with C1+C2 two-step design. Add Application Brief description. Remove CL generation section.

**Step 3: Update CLAUDE.md**

- Update CLI commands section: add `--ai-evaluate`, `--ai-tailor`
- Update "硬规则筛选" description: "8 条硬拒绝规则" → whitelist-only mention
- Remove references to `scoring.yaml`, `rule_score`
- Update daily workflow section

**Step 4: Commit**

```bash
git add docs/plans/2026-03-27-pipeline-block-architecture.md CLAUDE.md
git commit -m "docs: update architecture doc and CLAUDE.md for B+C redesign

Block B: whitelist-only. Block C: C1 evaluate + C2 tailor. CL replaced
by application brief."
```

---

### Task 10: Block C tests

**Files:**
- Create: `tests/test_ai_analyzer.py`

**Step 1: Write C1 parse tests**

```python
class TestEvaluateResponseParsing:
    """Test C1 evaluate response parsing (no AI calls)."""

    def test_valid_response(self):
        """Full scoring + brief JSON parses correctly."""

    def test_missing_recommendation_defaults_skip(self):
        """Missing recommendation field → SKIP."""

    def test_score_boundary_39(self):
        """ai_score 3.9 → recommendation preserved, no C2 triggered."""

    def test_score_boundary_40(self):
        """ai_score 4.0 → eligible for C2."""

    def test_malformed_json(self):
        """Unparseable response → REJECTED."""

    def test_application_brief_in_reasoning(self):
        """application_brief stored in reasoning JSON."""
```

**Step 2: Write C2 parse tests**

```python
class TestTailorResponseParsing:
    """Test C2 tailor response parsing (no AI calls)."""

    def test_bullet_id_resolution(self):
        """Known bullet IDs resolve to text."""

    def test_unknown_bullet_skipped(self):
        """Unknown bullet ID skipped with warning."""

    def test_bio_assembly(self):
        """Structured bio spec → assembled text."""

    def test_validation_failure_returns_none(self):
        """Validation failure → tailor_resume returns None."""
```

**Step 3: Write DB method tests**

```python
class TestJobAnalysisDB:
    """Test C1/C2 DB workflow."""

    def test_save_then_update_resume(self):
        """C1 save_analysis + C2 update_analysis_resume preserves scoring."""

    def test_get_jobs_needing_tailor(self):
        """Returns jobs with score >= threshold and empty tailored_resume."""
```

**Step 4: Run tests**

Run: `python -m pytest tests/test_ai_analyzer.py -v`
Expected: All pass.

**Step 5: Commit**

```bash
git add tests/test_ai_analyzer.py
git commit -m "test(block-c): add C1/C2 parse + DB workflow tests

No AI calls — tests cover response parsing, bullet resolution, bio
assembly, validation, and C1→C2 DB update flow."
```

---

### Task 11: Final cleanup and memory update

**Step 1: Delete stale memory**

Update `memory/project_block_b_simplification.md` — the simplification is now implemented, not "planned for after Block C".

**Step 2: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: All pass.

**Step 3: Final commit**

```bash
git add -A
git commit -m "chore: final cleanup for Block B+C redesign"
```
