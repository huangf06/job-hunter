# Personal Brand Optimization: LinkedIn + GitHub + Blog

Generated: 2026-04-02

---

## Deliverable 1: GitHub Profile README.md

Ready to commit to `huangf06/huangf06` repo.

```markdown
# Fei Huang

Data engineer and AI practitioner based in Amsterdam. M.Sc. in Artificial Intelligence from VU Amsterdam (GPA 8.2/10). Databricks Certified Data Engineer Professional.

My career has followed a single thread: understanding complex systems through data. Industrial engineering at Tsinghua taught me to think in systems. Quantitative finance taught me to build under uncertainty. Data engineering at a fintech startup taught me to ship. Graduate school in AI brought the formal foundations together.

I write about philosophy and literature at [FeiThink](https://huangf06.github.io/FeiThink/en/) — mostly Kant, Dostoevsky, and the question of how to live well. The intellectual habits that make a good engineer (rigor, honesty about what you don't know, building from first principles) are the same ones that matter in philosophy.

## Selected Projects

**[job-hunter](https://github.com/huangf06/job-hunter)** — Automated job search pipeline. Scrapes listings from multiple platforms, applies rule-based filtering and AI-powered evaluation, generates tailored resumes, and tracks applications. Python, SQLite/Turso, Claude API, Playwright, GitHub Actions.

**[FeiThink](https://github.com/huangf06/FeiThink)** — Bilingual blog (EN/ZH) on philosophy, literature, and moral thought. Hugo + PaperMod with CI/CD deployment. 48 essays and counting.

**[LifeOS](https://github.com/huangf06/LifeOS)** — Personal productivity platform orchestrating Todoist, Notion, Telegram Bot, and Logseq with automated daily workflows via GitHub Actions. Includes vocabulary pipeline and flashcard generation.

**Financial Data Lakehouse** — Real-time market data processing on Databricks. Auto Loader + Structured Streaming, Medallion Architecture, Delta Lake with schema evolution and fault-tolerant ingestion.

## Links

- [LinkedIn](https://linkedin.com/in/huangf06)
- [Blog (English)](https://huangf06.github.io/FeiThink/en/)
- [Substack](https://feithink.substack.com)
```

---

## Deliverable 2: LinkedIn Profile Copy

### a) Headline (196 chars)

```
Data Engineer | M.Sc. Artificial Intelligence, VU Amsterdam | Databricks Certified DE Professional | Python, Spark, Delta Lake | Amsterdam
```

### b) About Section (~1900 chars)

```
Every job I've taken was a bet on the same idea: that the most interesting problems sit at the intersection of data, decisions, and uncertainty.

I started in industrial engineering at Tsinghua University, where I learned to think about systems — supply chains, operations, optimization. My first real job was at Henan Energy (Fortune Global 500), where I built the analytics framework that tracked inventory and procurement timing across 20+ business units.

I moved to Shanghai and joined Ele.me during its hyper-growth phase (pre-Alibaba acquisition), building fraud detection systems across 2.2M+ users and optimizing Hadoop queries that cut scan volumes 5x. Then quantitative finance: at BQ Investment, I built backtesting infrastructure and ran systematic alpha research across 3,000+ securities, deploying strategies with real capital.

At GLP Technology, I was the first technical hire. I designed and built the complete credit risk data platform from scratch — data ingestion, a 29-rule decision engine, borrower classification, and post-loan monitoring. PySpark, AWS Redshift, the full stack.

From 2019 to 2023, I stepped back deliberately: independent quantitative research, learning English and German, and preparing for graduate school. In 2023 I entered the M.Sc. AI program at VU Amsterdam (GPA 8.2/10). My thesis investigated uncertainty quantification in deep reinforcement learning — 150+ training runs on HPC, rigorous statistical evaluation of when models know what they don't know.

I hold the Databricks Certified Data Engineer Professional certification (2026).

I'm looking for Data Engineering or AI roles in the Netherlands. I have full work authorization (Zoekjaar) and am eligible for Kennismigrant visa sponsorship.
```

### c) Experience Entries

**GLP Technology | Data Engineer & Team Lead | Jul 2017 - Aug 2019 | Shanghai**

```
First technical hire at a lending fintech. Designed and built the complete credit risk data platform from scratch — from raw data ingestion through automated decisioning to post-loan monitoring.

Core contribution: engineered the decision engine with 29 rejection rules across 4 risk dimensions, a 36-segment borrower classification system, and an early-delinquency scorecard combining 19 weighted features for first-payment default prediction.

Built the data foundation powering all risk systems: daily ETL of 30+ production tables into AWS Redshift, plus a credit bureau report parser transforming deeply nested JSON into 5 structured analytical tables.

Extended the platform into post-loan monitoring: delinquency tracking, repayment trend analysis, and third-party fraud detection API integration.

Tech: Python, SQL, PySpark, AWS (Redshift, S3, EC2), Airflow, pandas, NumPy, Power BI
```

**Independent Quantitative Researcher | Sep 2019 - Aug 2023 | Remote**

```
Career transition period combining active technical work with graduate school preparation.

Built automated equity research pipeline processing 83K+ daily records across 3,600+ stocks via Tushare API and MySQL. Implemented institutional flow tracking and momentum signal detection for systematic market analysis.

Concurrently: self-directed study in data science and ML, English and German language acquisition, and admission to M.Sc. AI at VU Amsterdam (2023).
```

**BQ Investment | Quantitative Researcher | Jul 2015 - Jun 2017 | Beijing**

```
Quantitative hedge fund, 5-person team.

Built end-to-end market data ingestion pipeline processing 3,000+ A-share securities and 5+ years of tick-level futures data. Implemented corporate action handling and deduplication logic.

Architected event-driven backtesting framework (Python + MATLAB) supporting strategy simulation, walk-forward validation, and 15+ performance metrics — adopted as core research infrastructure.

Built systematic alpha research pipeline using Fama-MacBeth regression to validate 4 factor families across 3,000+ securities. Developed and deployed R-Breaker intraday trading strategy achieving 14.6% annualized return with real capital.

Tech: Python, MATLAB, SAS, SQL, Wind API, NumPy, pandas, scipy
```

**Ele.me (acquired by Alibaba) | Data Analyst | Sep 2013 - Jul 2015 | Shanghai**

```
Joined during hyper-growth, pre-Alibaba acquisition.

Built anti-fraud detection system identifying 51,000+ suspicious order clusters across 2.2M+ users using 3 pattern algorithms (same-phone, high-frequency, repeat-order matching), preventing fraudulent subsidy claims.

Optimized 90+ Hadoop/Hive queries through partition pruning and subquery pushdown, cutting scan volume 5x (500GB to 100GB) and unlocking real-time analytics on 30+ warehouse tables.

Engineered SQL-based user segmentation pipeline analyzing 2.2M+ users across 4 behavioral cohorts — delivered actionable profiles adopted by marketing for targeted campaigns.

Tech: SQL, Hadoop, Hive, Python, pandas, A/B Testing
```

**Henan Energy | Business Analyst | Jul 2010 - Aug 2013 | Zhengzhou**

```
Fortune Global 500 (#328), state-owned enterprise.

Built automated pipeline to ingest, validate, and consolidate non-standardized Excel reports from 20+ business units into unified operational reporting — reduced monthly processing from 2 days to under 2 hours.

Designed the group's supply chain analytics framework from scratch, tracking daily sales and inventory to guide procurement timing. Optimization guided by this framework contributed to EUR 32M in documented profit improvements over 3 years.
```

### d) Featured Section Suggestions

Pin in this order:
1. **Databricks Certified Data Engineer Professional** — credential link/image
2. **GitHub: job-hunter** — link to repo with description "Automated job search pipeline (Python, Claude API, Playwright)"
3. **Blog post: "Why We Read Kant"** — shows intellectual depth without being politically charged
4. **Blog post: "Skin in the Game"** — connects philosophical thinking to practical decision-making (Taleb resonates with technical/business audiences)
5. **GitHub: FeiThink** — demonstrates CI/CD, bilingual content

Avoid featuring: political commentary posts (Hong Kong articles, White Paper Protests, Li Wenliang tribute). These are honest and well-written but create unnecessary risk in a hiring context.

### e) Skills (ordered by priority, top 3 pinned)

**Pin these 3:**
1. Python
2. Apache Spark / PySpark
3. Data Engineering

**Remaining 12:**
4. SQL
5. Databricks
6. ETL/ELT
7. Delta Lake
8. AWS
9. Machine Learning
10. PyTorch
11. Data Pipelines
12. PostgreSQL
13. Docker
14. Airflow
15. Statistical Analysis

---

## Deliverable 3: Blog Strategy Memo

### Existing Post Assessment

**Professional assets** (would impress a hiring manager who reads them):
- "Skin in the Game" — shows analytical thinking about incentive structures, directly relevant to engineering culture
- "Why We Read Kant" — demonstrates rigorous thinking, originality, commitment to first principles
- "IKIRU" — shows values (meaning, purpose) without political risk
- "Subjectivity: How to Become the Protagonist" — agency, self-direction
- "Reason and Emotion" — shows balanced thinking, relevant to team dynamics
- "History of Thought" series (4 parts) — shows systematic, long-form intellectual work

**Neutral** (won't help or hurt): Most literary analyses (Dostoevsky, Garcia Marquez, Vagabond), personal reflections, INTJ essay, emotional care essay. These show you're a human with depth — fine, but won't move the needle professionally.

**Risk zone** (honest writing, but a recruiter who skims could misread):
- "In Memory of Li Wenliang" — touching but politically sensitive in some contexts
- "Questions About Recent Viral Articles I & II" — Hong Kong political analysis
- "On Human Nature: What the White Paper Protests Taught Me" — direct political commentary
- "From Chosin Reservoir to Christmas" — Korea/China historical politics
- "Reflections on 12.12" — Gwangju uprising

These posts are intellectually solid. The question is risk tolerance. In the Dutch market, political awareness is generally respected, but a hiring manager at a large tech company might flag it as "potentially controversial." Recommendation: keep them published (they're part of who you are, and removing them would be dishonest), but don't feature them on LinkedIn.

### Technical Blog Posts to Write (5 suggestions)

**1. "Building a Real-Time Data Lakehouse on Databricks"**
Outline: Your Financial Data Lakehouse project. Cover: why Medallion Architecture, Auto Loader vs batch, schema evolution challenges, quarantine pattern for data quality. Include architecture diagrams. Target audience: hiring managers and peers evaluating your Databricks skills.

**2. "What My M.Sc. Thesis Taught Me About Uncertainty"**
Outline: Non-academic version of your thesis. What is uncertainty quantification? Why does it matter for production ML? The "noise paradox" finding. What 150 HPC runs look like in practice. Frame for practitioners, not reviewers. Target: ML engineers, data scientists.

**3. "Automating Job Search with Python and Claude"**
Outline: The job-hunter project. Architecture overview, the filtering pipeline, using LLMs for evaluation (not just chatbots), resume generation, lessons learned. This will get attention — job searching is universal and automating it is novel. Target: broad developer audience, potential viral reach.

**4. "From Quant Finance to Data Engineering: Why the Skills Transfer"**
Outline: Career narrative post. Factor research is feature engineering. Backtesting is pipeline testing. Real capital is production. Event-driven architecture in trading vs data systems. This directly addresses the "why did you change careers" question. Target: hiring managers, career changers.

**5. "Credit Scoring from Scratch at a Fintech Startup"**
Outline: The GLP story. What it's like being the first technical hire. Building a 29-rule decision engine. The credit bureau JSON parsing problem. Technical depth on scorecard methodology. Target: fintech engineers, startup-curious engineers.

### Blog Organization

Don't separate into two blogs. Use Hugo's tag system instead:
- Add tags: `technical`, `philosophy`, `literature`, `career`
- Create a landing page or pinned post that says: "Looking for technical writing? Start here: [list]. Looking for philosophy? Start here: [list]."
- On LinkedIn, only link to the `/en/` version and specific technical posts

### Hugo Config Improvements

- Add `description` meta tag in config for SEO: "Fei Huang's blog on data engineering, AI, philosophy, and moral thought"
- Add `author` structured data
- Consider adding `robots.txt` and `sitemap.xml` if not already present
- Add Open Graph images for social sharing (Hugo PaperMod supports `cover` in frontmatter)
- Add a "Technical Writing" section to the menu once you have 3+ technical posts

---

## Deliverable 4: Cross-Platform Consistency Audit

### Narrative Alignment

| Element | Resume | LinkedIn (proposed) | GitHub (proposed) | Blog |
|---------|--------|--------------------|--------------------|------|
| Career arc | IE -> DA -> Quant -> DE -> AI | Same | Same | Not addressed |
| Gap framing | "Career Note: independent investing, language learning, grad prep" | "Stepped back deliberately" + technical detail | Not mentioned (correct) | Not addressed |
| Core identity | Data Engineer | Data Engineer + AI | "Data engineer and AI practitioner" | "Mathematical rigor meets philosophical inquiry" |
| Intellectual depth | Interests section only | Woven into About | Explicit paragraph about philosophy | Full expression |

### Contradictions Found

1. **Resume title vs reality**: Resume bio says "Data Engineer with expertise in..." — this is the tailored version for a specific application (Picnic). The master template is fine; just note that LinkedIn/GitHub should use the broader "Data Engineer | AI" framing, not company-specific text.

2. **GLP title inconsistency**: Bullet library allows "Senior Data Engineer", "Data Engineer & Team Lead", "Senior Data Scientist" depending on context. LinkedIn should use one title consistently. Recommendation: **"Data Engineer & Team Lead"** — it's the most honest (first hire who built the team) and the most impressive.

3. **Blog tagline vs professional brand**: "Where mathematical rigor meets philosophical inquiry" is great for the blog but doesn't connect to data engineering at all. This is fine — the blog serves a different purpose. Just don't use this tagline on LinkedIn.

### Gaps to Close

1. **Zero technical blog content** — the biggest gap. Your GitHub shows you build things; your blog shows you think deeply; nothing shows you can explain technical work in writing. The 5 suggested posts above would close this completely.

2. **No "About" page on the blog that connects to professional identity** — the current blog About page should mention your professional background briefly, linking to LinkedIn/GitHub, so someone arriving from a technical post knows who you are.

3. **GitHub repos may not have good READMEs** — check that job-hunter, LifeOS, and FeiThink repos each have a README that matches the descriptions in the GitHub profile README above.

### Unified "About Me" Boilerplate

Adapt this core paragraph per platform:

> Data engineer and AI practitioner based in Amsterdam. M.Sc. in Artificial Intelligence from VU Amsterdam (GPA 8.2/10), Databricks Certified Data Engineer Professional. Career path from industrial engineering through quantitative finance and data engineering to AI — each step driven by the same interest in understanding complex systems through data. I write about philosophy, literature, and moral thought at FeiThink.

- **LinkedIn**: expand into full About section (done above)
- **GitHub**: use as-is with project links
- **Blog About page**: lead with intellectual identity, then mention professional background
- **Resume**: compress to 1-2 line bio tailored per application
