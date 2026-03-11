# Interview Strategy - kaiko.ai Senior Evaluation ML Engineer

**Format:** 30-minute online interview  
**Time:** 2026-03-11 11:30-12:00  
**Attendees:** Irina Rusu (Senior Recruiter), Max Feucht (Machine Learning Engineer)  
**Platform:** online meeting invite

## Interview Nature Assessment

Based on the invite, this is most likely a first-round screen with two layers:

1. Recruiter layer
   - motivation
   - communication
   - values fit
   - career narrative
2. Technical peer layer
   - are your examples real
   - do you understand trustworthy evaluation
   - can you work in an ML platform environment

This is probably not a deep coding interview. It is more likely a structured conversation checking whether to move you into a technical round.

## Confirmed vs Inferred

### Confirmed

- Irina Rusu is listed as Senior Recruiter in the invite.
- Max Feucht is listed as Machine Learning Engineer in the invite.
- The role is Senior Evaluation ML Engineer.
- The invite says they want examples from your past experience and want to assess fit with values and culture.

### Inferred

- Irina will likely lead logistics, motivation, and collaboration questions.
- Max will likely probe technical credibility and how you reason about evaluation work.

Treat these as operating assumptions, not facts.

## Three Narratives To Lead With

### Narrative 1 - "I build trustworthy evaluation systems, not just models"

Use your thesis first.

Suggested framing:

> In my thesis, I was not just training RL agents. I built a reproducible benchmarking setup across 150+ runs and compared five uncertainty quantification approaches with statistical testing. The core skill was deciding which signals were trustworthy and how to design evaluation so the conclusions held up. That is the part of my background that maps most directly to this role.

Why it works:

- directly relevant
- technically serious
- avoids generic LLM hype language

### Narrative 2 - "I have shipped reliability under high-stakes constraints"

Use GLP second.

Suggested framing:

> At GLP, as the first data hire, I owned pipelines, data quality, and model-related infrastructure for credit scoring. A wrong output had real business consequences, so reliability and data hygiene were not optional. That gave me the habit of thinking about validation, monitoring, and failure modes as part of the system, not as cleanup after the fact.

Why it works:

- bridges from finance to healthcare without overclaiming
- shows ownership
- makes "high stakes" credible

### Narrative 3 - "I bridge ML research thinking and data platform engineering"

Use Databricks / Spark as the support layer.

Suggested framing:

> A lot of my experience sits exactly in the overlap between ML experimentation and production-grade data systems. I have hands-on work with PySpark, Databricks, Delta Lake, schema evolution, and data quality controls, so I can think about evaluation not just as metrics but as an end-to-end platform problem.

Why it works:

- matches their stack
- makes you sound like a systems person

## Likely Questions And Good Response Shape

### "Tell us about yourself"

Use this structure:

1. 6 years across ML, data pipelines, and quantitative systems
2. M.Sc. AI in Amsterdam
3. thesis -> evaluation rigor
4. GLP -> ownership and reliability
5. why kaiko -> apply this to clinically meaningful AI

Keep it under 90 seconds.

### "Why kaiko?"

Strong version:

> What attracts me is that the hard problem here is not only model capability, but trustworthy evaluation in a domain where mistakes matter. That sits right at the intersection of my strongest experiences: rigorous benchmarking from my thesis, data quality and reliability from GLP, and distributed data infrastructure from my recent Databricks work. I also like that kaiko seems close to real clinicians and hospitals, because that forces evaluation to stay grounded in real decision-making instead of abstract leaderboard metrics.

### "You do not come from oncology. How do you think about that gap?"

Best move is disciplined humility:

> I do see oncology knowledge as my main gap. I would not pretend otherwise. What I would bring immediately is the ability to design reproducible evaluation systems, enforce data quality, and work systematically with subject-matter experts. In a domain like this, I think the right stance is to combine strong engineering discipline with respect for clinical expertise.

### "Tell us about a time you worked cross-functionally"

Use GLP or Ele.me:

- technical stakeholders + business stakeholders
- ambiguous requirements
- you translated practical needs into measurable systems
- highlight listening and iteration, not only execution

### "How would you think about building evaluation for a clinical AI system?"

Good structure:

1. define intended clinical use cases first
2. define failure modes and decision-critical scenarios
3. build benchmark slices, not one monolithic benchmark
4. control leakage and provenance
5. include expert review where automation is insufficient
6. make the pipeline reproducible and versioned
7. tie outputs to release decisions

## Likely Attack Vectors

### 1. Domain gap

They may test whether you respect clinical nuance or whether you treat healthcare as just another data problem.

### 2. Seniority signal

They may test whether you can own an evaluation stack instead of only contributing pieces.

### 3. Specificity

They may push on whether your examples are concrete or just well-worded.

### 4. Collaboration under disagreement

Because the JD emphasizes collaboration, they may ask how you handle differing opinions from researchers or clinicians.

## What To Avoid

- Do not claim healthcare expertise you do not have.
- Do not present yourself as only a researcher.
- Do not make the conversation only about tools.
- Do not over-rotate into generic LLM buzzwords like "agentic" or "RAG" unless asked.
- Do not answer evaluation questions with only model metrics. Bring up benchmark quality and decision relevance.

## Questions To Ask Them

Pick 2-3.

1. What parts of the evaluation stack are already in place, and what parts are still greenfield?
2. How do you work with clinicians when turning a clinical question into an evaluation task or rubric?
3. What distinguishes strong performance in this role during the first 3-6 months?
4. How do you currently decide whether an offline evaluation result is strong enough to influence release decisions?
5. For Max: where do engineering handoffs usually happen between modeling work and evaluation platform work?

## Best Closing Position

Leave them with this:

> I know my biggest gap is the medical domain itself, but I think my background is unusually strong on the other side of the equation: building rigorous, reproducible, high-stakes evaluation and data systems. That is why this role feels like a very strong fit.
