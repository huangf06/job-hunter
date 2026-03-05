# FareHarbor Live Coding Interview - Action Plan

## Interview Details
- **Date**: 2026-03-05 (TOMORROW)
- **Company**: FareHarbor (Booking Holdings)
- **Role**: Machine Learning Engineer - Pricing & Revenue Management
- **Interview Type**: Live Coding
- **AI Score**: 7.5/10 (strong match)

---

## Tonight's Drill Plan (2-3 hours)

### Priority 1: Python Fundamentals (45 min) ⚠️ CRITICAL
**Why**: Springer Nature failure was due to Python basics gaps
**Method**: Hand-write on paper, NO AI, explain out loud

**Drill List** (see `04_live_coding_drill_plan.md` Part 1):
1. Decorators (function + class)
2. Generators & iterators
3. Context managers
4. List/dict comprehensions
5. Classes & OOP (property, __slots__, ABC)

**Success Criteria**: Can write each pattern from memory in <2 minutes

---

### Priority 2: ML Production Patterns (45 min)
**Why**: This is what you'll actually code in the interview

**Drill List** (see `04_live_coding_drill_plan.md` Part 2):
1. Feature engineering pipeline (sklearn transformer)
2. Model serving with caching (Redis + LRU)
3. A/B testing framework (deterministic assignment)

**Success Criteria**: Can explain architecture + write skeleton code

---

### Priority 3: Pricing/Revenue Algorithms (30 min)
**Why**: Domain-specific to FareHarbor's business

**Drill List** (see `04_live_coding_drill_plan.md` Part 3):
1. Multi-armed bandit (epsilon-greedy)
2. Demand forecasting (gradient boosting)
3. Contextual bandit (Thompson sampling)

**Success Criteria**: Understand when to use each, can implement epsilon-greedy from scratch

---

### Priority 4: Behavioral Stories (15 min)
**Why**: Live coding interviews often have behavioral component

**Drill List** (see `04_live_coding_drill_plan.md` Part 6):
1. GLP credit scoring (technical challenge)
2. Baiquan factor engine (production issue)
3. Ele.me A/B testing (collaboration)

**Success Criteria**: Can deliver each story in <2 minutes with STAR structure

---

## Tomorrow Morning (30 min before interview)

### Technical Warm-Up (15 min)
- [ ] Write a decorator from scratch (no looking)
- [ ] Implement Fibonacci generator
- [ ] Code A/B test assignment function
- [ ] Explain bias-variance tradeoff out loud

### Environment Setup (5 min)
- [ ] Test webcam/mic
- [ ] Close unnecessary tabs
- [ ] Python REPL open
- [ ] Water, notebook, pen ready

### Mental Prep (10 min)
- [ ] Review 3 STAR stories
- [ ] Read FareHarbor mission (file 05)
- [ ] 4-7-8 breathing (see file 06)
- [ ] Mantra: "I've built production ML systems. I can do this."

---

## During Interview - Communication Protocol

### When Given a Problem
1. **Clarify** (2 min): "What's the expected input/output?"
2. **Think out loud**: "I'm considering two approaches..."
3. **Start simple**: "Let me start with brute force, then optimize"
4. **Test as you go**: "Let me test with [1, 2, 3]..."

### Red Flags to Avoid
- ❌ Silent coding for 5+ minutes
- ❌ Jumping to code without clarifying
- ❌ Not testing your code
- ❌ Giving up when stuck

---

## After Interview (CRITICAL!)

**Within 1 hour**:
- [ ] Create `09_post_interview_notes.md`
- [ ] Record: Questions asked
- [ ] Record: How you answered
- [ ] Record: What you struggled with
- [ ] Record: Interviewer reactions
- [ ] Record: What to improve

**This is the feedback loop that's been missing!**

---

## Files in This Dossier

1. **00_process_log.md** (this file) - Action plan
2. **01_job_description.md** - Full JD
3. **02_ai_analysis.md** - AI evaluation (7.5/10)
4. **03_submitted_resume.md** - What they've seen
5. **04_live_coding_drill_plan.md** - ⭐ MAIN DRILL GUIDE (9 parts, ~6000 words)
6. **05_company_quick_facts.md** - FareHarbor context
7. **06_technical_cheatsheet.md** - Quick reference during interview

---

## Key Insights

### Your Strengths (from AI analysis)
- ✅ Strong Python/SQL/ML stack match
- ✅ End-to-end ML pipeline experience (GLP, Baiquan)
- ✅ A/B testing experience (Ele.me)
- ✅ RL exposure (thesis)
- ✅ AWS, Airflow, Docker

### Gap to Address
- ⚠️ No direct dynamic pricing experience
- **Mitigation**: Study pricing algorithms tonight (Part 3 of drill plan)

### Past Failure Pattern (Springer Nature)
- **Problem**: Couldn't answer Python basics
- **Root Cause**: Lack of muscle memory
- **Fix**: Hand-write fundamentals tonight, zero AI

---

## Confidence Builders

1. **You've done this before**: GLP credit scoring = production ML with business impact
2. **You know the stack**: PyTorch, scikit-learn, gradient boosting (all in your resume)
3. **You understand the domain**: Revenue optimization = credit risk optimization (different domain, same math)
4. **You're prepared**: This dossier + tonight's drills = more prep than 95% of candidates

---

## Final Thought

The interview is not about knowing everything. It's about:
1. **Thinking clearly** under pressure
2. **Communicating** your thought process
3. **Writing clean code** that works
4. **Handling uncertainty** gracefully

You've built production systems that handle millions of dollars. You can handle a 1-hour coding interview.

**Now go drill those fundamentals. You've got this! 💪**
