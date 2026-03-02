# Interview Strategy — Sensorfact Senior Data Engineer

## Logistics
- **Date**: Thursday, February 26, 2026
- **Time**: 10:45 - 11:15 CET (30 minutes)
- **Interviewer**: Miftah Muhammad
- **Platform**: Google Meet or phone +31 20 257 4026, PIN 240664384
- **Email**: miftah.muhammad@sensorfact.nl
- **Round**: 1 of ~4 (HR/Recruiter Screening)

## Interview Format Assessment

### This is Round 1: Recruiter Screening (30 min)
Based on Glassdoor, Sensorfact's typical process is:
1. **CV + HR call** ← YOU ARE HERE
2. Hiring manager interview
3. Technical/product interview (possibly take-home assignment)
4. Final interview (founder/CEO or team lead)

Alternative process (also reported):
1. **HR Screening** ← YOU ARE HERE
2. Team + Team Lead meeting
3. Take-home assignment
4. Assignment review + presentation
5. Result

**Key insight**: This is a screening call, not a technical deep-dive. Focus on: motivation, cultural fit, headline qualifications, logistics (visa, start date), and salary expectations.

## The Interviewer: Miftah Muhammad Miftahurrohman

### What We Know
- **Full name**: Miftah Muhammad Miftahurrohman
- **Role**: Recruiter / Talent Acquisition at Sensorfact
- **LinkedIn**: [linkedin.com/in/miftahurrohman](https://www.linkedin.com/in/miftahurrohman/)
- **Location**: Amsterdam
- **Background**: Indonesian-Dutch professional, multilingual (Indonesian, Dutch, English, German)
- **Education**: Hogeschool van Amsterdam (HBO, ~2015), Yeungnam University (South Korea)
- **Previous**: Worked in telecom, broadcast media, edtech sectors
- **Volunteer**: 13+ years at N.J. Schaaptuin (environmental organization) — genuine sustainability commitment
- **Recommendation**: Praised for "transparante en professionele aanpak" (transparent and professional approach)
- **LinkedIn tags**: #headhunter, #talentacquisition, #hr, #international
- **Confirmed**: Job postings reference "LI - MIFTAH" as sourcing channel

### Shared Background / Rapport Points
| Dimension | Miftah | You |
|-----------|--------|-----|
| International in NL | Indonesian → Netherlands (~2012) | Chinese → Netherlands (2023) |
| Asian + European edu | Yeungnam Univ (Korea) + HvA | Tsinghua (China) + VU Amsterdam |
| Sustainability | 13-year environmental volunteer | Interested in energy efficiency |
| Multilingual | Indonesian, Dutch, English, German | Chinese, English, Dutch (conv.) |
| Visa journey | Likely experienced similar process | Zoekjaar → Kennismigrant |

### Interview Style Prediction
As a recruiter screening, expect:
- **Warm, conversational tone** — he values transparency and directness
- **Checklist-style questions** — hitting key qualification requirements
- **Logistics focus** — visa, start date, salary, location (he understands visa process)
- **Motivation probing** — "Why Sensorfact?", "Why this role?" (his environmental values mean mission matters)
- **Brief resume walkthrough** — appreciates breadth of experience in career arcs
- **Not deeply technical** — save Kafka/Flink details for later rounds

## Three Key Narratives

### 1. "I build the pipelines that turn raw data into decisions" (Primary — matches their core need)
**Story**: At GLP, I was the first data hire. I built the entire data infrastructure from scratch — ingestion pipelines with PySpark, data quality frameworks, and monitoring systems. At Sensorfact, you do exactly this: turn raw sensor data into actionable insights. My Lakehouse project does the same pattern — streaming ingestion, quality checks, and serving for analytics.

**Key phrase**: "I've done exactly what Sensorfact does — take raw signals, process them through streaming and batch pipelines, ensure data quality, and deliver actionable insights."

### 2. "I understand both data engineering AND the ML it powers" (Differentiator)
**Story**: Most data engineers just build pipes. I have an MSc in AI from VU Amsterdam — I understand what the ML models downstream need. At GLP, I built the data infrastructure that fed credit scoring models. My thesis on uncertainty quantification means I think about data quality not just for storage but for model reliability.

**Key phrase**: "I don't just build pipelines — I understand what the ML models consuming the data actually need. That's rare in a data engineer."

### 3. "I thrive in scale-up environments" (Personal/Cultural fit)
**Story**: At GLP, I joined as employee #1 for data. At Ele.me, I was there during hypergrowth (Alibaba acquisition). I chose Sensorfact because you're at an exciting inflection point — ABB acquisition means global scale, and the data team is growing from 5+ engineers. I want to be part of building something.

**Key phrase**: "I've built from scratch before, and I've been through a major acquisition. I know what it takes."

## Critical Questions & Prepared Responses

### Q: "Tell me about yourself" / "Walk me through your resume"
**Framework** (2 minutes max):
> "I'm a data engineer with 6 years of experience, now looking for my next challenge in the Netherlands. Started at Ele.me — that's China's largest food delivery platform, now part of Alibaba — doing big data on Hadoop/Hive. Then moved to quantitative finance at Baiquan Investment, building high-performance data pipelines for 3,000+ securities. At GLP Technology, I was the first data hire — built the entire credit scoring infrastructure from scratch using PySpark.
>
> Then I decided to level up academically — did my MSc in AI at VU Amsterdam, graduated with an 8.2 GPA. Just got my Databricks Data Engineer Professional certification. My recent project is a financial data lakehouse with streaming ingestion, exactly the pattern you use at Sensorfact.
>
> What excited me about Sensorfact is the mission — making industry more sustainable through data — and the tech stack: streaming pipelines, real-time ML, and now scaling globally with ABB."

### Q: "Why Sensorfact?"
> "Three reasons. First, the **mission resonates**: using data to reduce industrial waste is meaningful work with measurable impact. Second, the **tech stack is exactly where I want to grow**: Kafka, Flink, Clickhouse — that's the modern streaming stack I've been building toward with my Spark Streaming and Lakehouse work. Third, the **timing is perfect**: you just partnered with ABB, which means global scale. I want to help build the data infrastructure for that expansion."

### Q: "Why are you looking for a new role?" / "Why the Netherlands?"
> "I came to the Netherlands for my master's in AI at VU Amsterdam. I fell in love with the country and the tech ecosystem. I'm on my Zoekjaar (orientation year visa) which allows me to work, and I'm looking for a role where I can transition to a Kennismigrant visa with a recognized sponsor."

### Q: "Do you need sponsorship?"
> "Yes, I'm on the Zoekjaar (orientation year visa). The transition to Kennismigrant is straightforward — the employer needs to be a recognized sponsor (erkend referent). The reduced salary threshold applies since I'm transitioning from Zoekjaar. I can start immediately."

**Note**: Check if Sensorfact/ABB is an erkend referent. ABB almost certainly is.

### Q: "What's your experience with Kafka/Flink?" (if they go technical)
> "I haven't worked with Kafka or Flink in production, but I have hands-on experience with Spark Structured Streaming, which solves the same class of problems — real-time data ingestion, processing, and exactly-once semantics. In my Lakehouse project, I handle streaming financial data with schema evolution and checkpoint-based fault tolerance. The concepts transfer directly — consumer groups, partitioning, windowed aggregation, back-pressure handling. I've also studied Kafka and Flink architecture to prepare for this transition."

### Q: "What are your salary expectations?"
- Research the market: Senior Data Engineer in Netherlands typically €65K-€90K
- Sensorfact (post-ABB) likely has competitive packages
- **Response**: "I'm looking for a competitive package that reflects senior data engineering in the Netherlands. I'm happy to discuss specific numbers once we both see there's a good fit. What's the range you have in mind for this role?"

### Q: "When can you start?"
> "I can start immediately. I'm available and my work permit allows me to work right away."

### Q: "Do you have any questions for us?"
See "Questions to Ask" below.

## Questions to Ask (ordered by impact)

### Must-ask (Round 1)
1. **"How is the data team structured? I saw you're hiring both a Senior DE and an Engineering Manager — does that mean the team is restructuring?"**
   - Shows you've researched, gets org structure intel

2. **"How has the ABB acquisition affected the tech team? Are you keeping your independent tech stack or integrating with ABB's systems?"**
   - Shows strategic thinking, gets critical info about the role's future

3. **"What does the interview process look like from here? How many rounds, and what should I expect?"**
   - Practical, shows you're organized

### Good follow-ups (if time allows)
4. "What's the biggest data engineering challenge Sensorfact faces right now?"
5. "Is Sensorfact a recognized sponsor (erkend referent) for the Kennismigrant visa?"
6. "What does a typical sprint look like for the data team?"

## Red Flags to Avoid
1. **Don't oversell Kafka/Flink experience** — be honest about the gap, strong on transferability
2. **Don't be negative about past employers** — frame career changes as growth
3. **Don't mention the career gap (2019-2023) unless asked** — if asked, frame positively (language learning, self-improvement, grad school prep)
4. **Don't ask about salary first** — let them bring it up
5. **Don't talk too long** — 30-minute call means concise answers (1-2 minutes max per question)
6. **Don't forget to show enthusiasm** — this is a screening call, energy matters

## Team Intelligence

### Who You Might Meet in Later Rounds
- **Dennis Ramondt** (VP of Technology) — likely Round 2 or final
- **Luka Sturtewagen, PhD** (Principal Data Engineer) — likely technical round
- **Pieter Broekema** (CEO) — possibly final round
- **An Engineering Manager** — if they've hired one by then

### Data Team Composition
- 5+ data engineers currently
- Principal Data Engineer: Luka Sturtewagen (PhD Wageningen, physics)
- Lead Data Scientist: Lieke Kools
- Engineering Manager - Data: open position
- Senior Data Engineer: open position (YOUR ROLE)

### Org Structure
```
Dennis Ramondt (VP Technology)
├── Data Team (5+ engineers)
│   ├── Luka Sturtewagen (Principal DE)
│   ├── [Engineering Manager - Data] ← hiring
│   ├── [Senior Data Engineer] ← YOUR ROLE
│   └── Other DEs
├── IoT Team
└── Platform Team
```
