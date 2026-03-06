# Live Coding Daily Practice Plan

**Created**: 2026-03-06
**Context**: Two consecutive FareHarbor live coding failures (basic coding + KNN) revealed fundamental execution gap
**Goal**: Rebuild Python coding muscle memory to pass live coding screens within 1-2 weeks

## Root Cause

The problem is NOT lack of ML knowledge — it's basic coding execution under pressure.
KNN is a trivial algorithm (compute distances, sort, take top k) but implementation failed.
This means: arrays, sorting, dict/list operations are not reflexive yet.

## Platform & Setup

- **Primary**: [NeetCode.io](https://neetcode.io) Roadmap → NeetCode 150
- **Coding**: LeetCode web editor (Python 3) — matches CoderPad interview feel
- **Tracking**: `practice/log.md` in this repo — date, problem, difficulty, time, pattern
- **Time budget**: 1.5-2 hours/day
- **Status**: Continue interviewing simultaneously

## Daily Routine (1.5-2h)

```
Phase 1: Warm-up (10 min)
├── Re-solve yesterday's problem from MEMORY (no looking)
├── If stuck → flag for review, move on
└── Purpose: builds muscle memory through spaced repetition

Phase 2: New Problems (60 min)
├── 2 problems from current NeetCode topic
├── 25 min per problem:
│   ├── 5 min: read, clarify, plan approach
│   ├── 15 min: code solution
│   └── 5 min: test + optimize
├── If stuck >20 min → look at hint (not full solution)
└── If stuck >25 min → watch NeetCode video, then re-implement yourself

Phase 3: Review & Notes (20 min)
├── For each problem write down:
│   ├── What PATTERN did this use?
│   ├── What was the key insight?
│   └── Time/space complexity?
└── Write 1-line summary in practice/log.md

Phase 4: Mock Interview Simulation (30 min)
├── 1 random problem from completed topics
├── SIMULATE interview conditions:
│   ├── 25-min hard timer
│   ├── Talk out loud (even alone)
│   ├── No IDE hints, no Google
│   └── Write solution in LeetCode editor
└── Grade yourself: Solved? Clean? Under time?
```

## Topic Progression

### Week 1-2 (CRITICAL — weakest areas from KNN failure)

| Priority | Topic | # Problems | Why |
|----------|-------|------------|-----|
| P0 | Arrays & Hashing | 9 | Core of KNN failure — sorting, grouping, dict ops |
| P0 | Two Pointers | 5 | Sorted array manipulation, distance problems |
| P0 | Sorting | 5 | Sorting must be reflexive, not deliberate |

### Week 3-4

| Priority | Topic | # Problems | Why |
|----------|-------|------------|-----|
| P1 | Sliding Window | 6 | Common pattern, builds on arrays |
| P1 | Stack | 7 | Fundamental data structure |
| P1 | Binary Search | 7 | Efficient search, common in interviews |

### Week 5-6

| Priority | Topic | # Problems | Why |
|----------|-------|------------|-----|
| P2 | Linked List | 11 | Classic interview topic |
| P2 | Trees | 15 | Recursion practice |
| P2 | Heap / Priority Queue | 7 | Directly relevant to KNN (top-k pattern!) |

### Week 7+ (only if needed for specific interviews)

Graphs, Dynamic Programming, Backtracking, Tries, etc.

## Day 1 Special: KNN Recovery

Before starting NeetCode, solve KNN from scratch to establish baseline:

```python
def knn(points, query, k):
    """
    points: list of (x, y) tuples
    query: (x, y) tuple
    k: int
    Returns: k nearest points to query
    """
    # Solve this cold. No looking at solutions.
```

After 2 weeks of NeetCode practice, re-do this and measure improvement.

## Panic Recovery Protocol (for real interviews)

1. **Stop coding. Breathe.** (5 seconds)
2. **Restate the problem out loud**: "OK so I need to..."
3. **Write the simplest brute force**: nested loops, O(n^2), whatever works
4. **Get brute force working FIRST**
5. **Then optimize** — interviewer will help if you have working code
6. **If truly stuck**: "I'm thinking about using X because Y, does that make sense?"

Key insight: **working brute force > elegant solution you can't finish**.

## Weekly Review (Sunday, 30 min)

- Count problems solved this week
- Review log.md for patterns: which topics are weakest?
- Adjust next week's focus accordingly
- Re-attempt any problems that were unsolved or took >25 min

## Success Metrics

- **Week 1**: Can solve Easy array/hashing problems in <15 min
- **Week 2**: Can solve Easy problems cold + Medium arrays in <25 min
- **Week 4**: Can solve Medium problems across 3+ topics in <25 min
- **Ongoing**: Mock interview pass rate >80%
