#!/usr/bin/env python3
"""
AI Job Analyzer - 用 Claude 分析所有职位的适合度

输出：每个职位的判断结果和原因
"""
import json
import sys
from pathlib import Path
from anthropic import Anthropic

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 候选人背景
CANDIDATE_PROFILE = """
Candidate Profile:
- Name: Fei Huang
- Background: Chinese national living in Netherlands (requires visa sponsorship or already has work permit)
- Experience: 5+ years in ML/Data Engineering
- Target roles: ML Engineer, Data Engineer, Data Scientist, Quantitative roles
- Skills: Python, PyTorch, TensorFlow, Spark, Databricks, SQL, AWS/Azure, Docker, Kubernetes
- Education: M.Sc. in AI from VU Amsterdam
- Languages: English (fluent), Chinese (native), Dutch (basic/none)
- Preference: Hybrid or remote, Netherlands-based companies preferred
- NOT suitable for: Pure frontend, mobile, DevOps, security, management roles
"""

ANALYSIS_PROMPT = """
You are a job matching expert. Analyze this job posting for the candidate.

{candidate_profile}

Job Posting:
- Title: {title}
- Company: {company}
- Location: {location}
- Description:
{description}

Analyze and respond in this exact JSON format:
{{
  "suitable": true/false,
  "confidence": 0.0-1.0,
  "decision": "APPLY" / "MAYBE" / "SKIP",
  "hard_reject_reason": null or one of ["dutch_required", "wrong_role", "too_senior", "no_sponsorship", "location_impossible"],
  "score": 0-10 (only if suitable),
  "reasoning": "1-2 sentence explanation",
  "key_requirements": ["list", "of", "key", "skills"],
  "red_flags": ["list", "of", "concerns"],
  "match_highlights": ["list", "of", "good", "matches"]
}}

Important rules:
1. "dutch_required": If Dutch language is REQUIRED (not just preferred), mark as hard reject
2. "wrong_role": If role is clearly not ML/Data related (e.g., frontend, mobile, DevOps, security)
3. "too_senior": If requires 10+ years or is Director/VP/Principal level
4. "no_sponsorship": If explicitly says "no visa sponsorship" or "must have EU work authorization"
5. "location_impossible": If requires onsite in location outside Netherlands with no remote option

For scoring (if suitable):
- 8-10: Excellent match, should apply immediately
- 6-7: Good match, worth applying
- 4-5: Moderate match, apply if nothing better
- 1-3: Poor match but still possible

Be strict but fair. Many jobs don't explicitly mention sponsorship - don't reject just because it's not mentioned.
"""


def analyze_job(client: Anthropic, job: dict) -> dict:
    """Analyze a single job with Claude"""
    prompt = ANALYSIS_PROMPT.format(
        candidate_profile=CANDIDATE_PROFILE,
        title=job['title'],
        company=job['company'],
        location=job.get('location', 'Unknown'),
        description=job['description'][:4000]  # Truncate long descriptions
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse JSON response
    text = response.content[0].text
    # Find JSON in response
    start = text.find('{')
    end = text.rfind('}') + 1
    if start >= 0 and end > start:
        return json.loads(text[start:end])
    return {"error": "Failed to parse response", "raw": text}


def main():
    # Load jobs
    with open(PROJECT_ROOT / 'data' / 'all_jobs_for_analysis.json', 'r', encoding='utf-8') as f:
        jobs = json.load(f)

    print(f"Analyzing {len(jobs)} jobs with AI...\n")

    client = Anthropic()
    results = []

    for i, job in enumerate(jobs):
        print(f"[{i+1}/{len(jobs)}] {job['title'][:50]}... ", end='', flush=True)

        try:
            analysis = analyze_job(client, job)
            analysis['job_id'] = job['id']
            analysis['title'] = job['title']
            analysis['company'] = job['company']
            results.append(analysis)

            decision = analysis.get('decision', 'ERROR')
            reason = analysis.get('hard_reject_reason') or analysis.get('reasoning', '')[:30]
            print(f"{decision} - {reason}")
        except Exception as e:
            print(f"ERROR: {e}")
            results.append({
                'job_id': job['id'],
                'title': job['title'],
                'company': job['company'],
                'error': str(e)
            })

    # Save results
    output_path = PROJECT_ROOT / 'data' / 'ai_analysis_results.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\nResults saved to {output_path}")

    # Summary
    print("\n=== Summary ===")
    apply = [r for r in results if r.get('decision') == 'APPLY']
    maybe = [r for r in results if r.get('decision') == 'MAYBE']
    skip = [r for r in results if r.get('decision') == 'SKIP']
    errors = [r for r in results if 'error' in r]

    print(f"APPLY: {len(apply)}")
    print(f"MAYBE: {len(maybe)}")
    print(f"SKIP: {len(skip)}")
    print(f"ERRORS: {len(errors)}")

    # Rejection reasons
    print("\n=== Hard Reject Reasons ===")
    reasons = {}
    for r in results:
        reason = r.get('hard_reject_reason')
        if reason:
            reasons[reason] = reasons.get(reason, 0) + 1
    for reason, count in sorted(reasons.items(), key=lambda x: -x[1]):
        print(f"  {reason}: {count}")


if __name__ == "__main__":
    main()
