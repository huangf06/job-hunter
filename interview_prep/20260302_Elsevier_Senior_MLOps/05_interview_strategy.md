# Interview Strategy — Elsevier Senior MLOps (First Round)

## Interview Context
- **Date**: 2026-03-02, 15:00
- **Round**: First round
- **Role**: ML Engineer — Research Products (Senior MLOps)
- **Team**: Data Science A&G and STMJ
- **Reports to**: Manager, Data Science

---

## 1. NARRATIVE STRATEGY

### Core Positioning
**"ML Engineer who bridges Data Science and Engineering — exactly what this role asks for."**

Don't position as pure MLOps specialist (gaps there). Instead: ML Engineer with strong data engineering foundation who has owned the full ML lifecycle and is passionate about bringing GenAI/RAG systems to production over scholarly data.

### Three Pillars of Your Story
1. **Full ML Lifecycle Ownership**: GLP — first data hire, owned everything from data ingestion to model deployment to monitoring
2. **Large-Scale Data Engineering**: PySpark pipelines, Databricks lakehouse, data quality frameworks — the infrastructure that makes ML production-ready
3. **AI/NLP Academic Foundation + Hands-on GenAI**: MSc AI (8.2 GPA), NLP coursework, LLM APIs in production (job-hunter system), recommendation systems (NDCG optimization)

### Opening Pitch (30 seconds)
"I'm an ML Engineer with about 6 years of experience building production ML systems and data pipelines, plus a recent MSc in AI from VU Amsterdam. What excites me about this role is that it sits at the exact intersection I thrive in — bridging data science and engineering to turn experimental models into reliable, scalable services. At my previous roles, I've owned the full ML lifecycle: from building PySpark data pipelines and data quality frameworks, to training and deploying models, to monitoring them in production. Most recently, I've been working with LLM APIs and building a recommendation system optimized on NDCG, which maps directly to the search and ranking work you do at Elsevier."

---

## 2. EXPERIENCE MAPPING TO JD

| JD Requirement | Your Experience | Bridge |
|---|---|---|
| ML workflows across AWS, Azure, Databricks | Databricks lakehouse project, AWS, Docker, Airflow, CI/CD | Direct experience with Databricks + AWS |
| CI/CD for ML | CI/CD pipelines in job-hunter (automated testing, deployment), Airflow orchestration | Strong foundation, can ramp up ML-specific CI/CD (SageMaker) |
| SageMaker, MLflow, Azure ML | MLflow on resume (Databricks cert), no direct SageMaker | Databricks cert covers MLflow; SageMaker concepts are transferable |
| GAR+RAG systems | LLM APIs (Claude) in production, prompt engineering, structured output | Direct RAG experience is limited but have strong LLM API + prompt eng skills |
| Elasticsearch/OpenSearch, vector DBs, Neo4j | No direct experience | Transferable: worked with large-scale data querying (Hadoop/Hive, SQL), understand search concepts from recommendation system |
| IR metrics (NDCG, MAP, MRR) | Expedia recommendation: NDCG@5 = 0.392, learning-to-rank | **Direct experience** — strong talking point |
| LLM evaluation | Built AI analyzer with quality gates, validation pipelines | Practical experience evaluating LLM outputs |
| PySpark, large-scale data processing | GLP PySpark ETL, Databricks lakehouse, Hadoop/Hive at Ele.me | **Strong match** |
| PyTorch, TensorFlow | PyTorch (thesis, GNN, NLP projects), no TensorFlow | PyTorch is primary — very strong |
| 4+ years ML Engineering | ~6 years total (data engineering/ML), 2 in pure ML research | Meets the bar — position as 6 years of data+ML |

---

## 3. GAP MITIGATION STRATEGIES

### Gap 1: No direct MLOps platform experience (SageMaker, MLflow in production)
**Strategy**: "I haven't used SageMaker in production, but I'm Databricks Certified Data Engineer Professional, which includes MLflow. My experience building end-to-end ML pipelines — from data ingestion through model deployment and monitoring — means I understand the MLOps lifecycle deeply. The platform-specific tooling is learnable; the engineering mindset is not."

### Gap 2: No Elasticsearch/vector DB/graph DB experience
**Strategy**: "I don't have production Elasticsearch experience, but I've worked with large-scale data querying extensively — Hadoop/Hive at Ele.me processing millions of user records, PySpark at GLP for credit data. I built a recommendation system optimized on NDCG, which is the same metric you use for search quality. The concepts of ranking, relevance, and retrieval are familiar territory."

### Gap 3: Limited RAG/GenAI production experience
**Strategy**: "While I haven't built production RAG systems, I've been working extensively with LLM APIs — I built an AI-powered job application pipeline that uses Claude for analyzing job descriptions, generating tailored content with structured output, and implementing quality gates to validate LLM outputs. That includes prompt engineering, structured JSON output, and validation — which maps to the guardrails and structured output mentioned in the JD."

### Gap 4: Scholarly publishing domain is new
**Strategy**: "The scholarly domain is new to me, but that's also what excites me. Working with one of the world's largest research corpora — making knowledge more discoverable through AI — is deeply meaningful. My NLP coursework (9.0/10) and thesis on uncertainty quantification give me the academic foundation to engage with research-quality standards."

---

## 4. STAR STORIES (Ready-to-Tell)

### Story 1: Full ML Lifecycle Ownership (GLP)
**S**: First data hire at consumer lending startup, no existing data infrastructure
**T**: Build credit scoring system from scratch — data pipelines, models, monitoring
**A**: Designed PySpark ETL pipelines for loan lifecycle data, built credit scoring models, implemented schema validation and data quality framework, created portfolio risk monitoring dashboard
**R**: Enabled automated credit decisions, mentored junior analyst, system processed entire loan portfolio

### Story 2: Data Quality Framework (Lakehouse Project)
**S**: Building real-time data lakehouse ingesting financial market feeds
**T**: Handle schema changes and malformed data without manual intervention
**A**: Engineered quarantine-and-replay pattern across Medallion Architecture (Bronze/Silver/Gold), schema evolution with checkpoint-based fault tolerance
**R**: Zero data loss during upstream changes, automated recovery without manual intervention

### Story 3: Recommendation System with IR Metrics (Expedia)
**S**: Kaggle competition — rank 4.9M hotel search records for personalized recommendations
**T**: Optimize ranking quality measured by NDCG@5
**A**: Engineered temporal, behavioral, and user-preference features; built learning-to-rank models (LightGBM, XGBoost+SVD); systematic feature engineering
**R**: NDCG@5 = 0.392, top 5% in competition — directly relevant to Elsevier's search ranking work

### Story 4: LLM Quality Gates (Job Hunter)
**S**: AI-powered pipeline using Claude for resume personalization
**T**: Ensure LLM outputs are reliable and validated — no hallucinated content
**A**: Built multi-stage validation: bullet ID lookup (deterministic), bio builder with whitelist constraints, blocking gates for invalid categories/titles, sentinel records for failures
**R**: System reliably generates personalized resumes with zero hallucinated content — every claim is verified against a source-of-truth library

### Story 5: Cross-functional Collaboration (GLP)
**S**: Early-stage fintech, wore many hats beyond pure ML
**T**: Translate business requirements into technical solutions across risk, product, operations
**A**: Served as bridge between risk modeling, product, and operations; collaborated with legal and external vendors; automated regulatory submissions
**R**: Built compliance reporting framework, established data-driven processes across the company

---

## 5. QUESTIONS TO ASK THEM

### About the Role
1. "What does a typical project lifecycle look like on the team — from an experimental model to production service?"
2. "How mature is the current MLOps infrastructure? Am I coming in to build from scratch or to scale existing systems?"
3. "What's the balance between building new GenAI features (like Scopus AI) versus maintaining and improving existing search/ranking systems?"

### About the Team
4. "How large is the Data Science team, and how does it collaborate with the Operations Engineering team?"
5. "What's the tech stack currently — you mention SageMaker, MLflow, and Azure ML; is there a primary platform or is it multi-cloud by design?"

### About the Technology
6. "Can you tell me more about the GAR+RAG architecture? How does knowledge graph-aware retrieval work with the scholarly corpus?"
7. "What are the biggest challenges right now in evaluating LLM quality for scholarly content — especially around faithfulness and grounding?"

### About Growth
8. "What does career growth look like for this role? Is there a path toward technical leadership or architecture?"

---

## 6. TECHNICAL DEEP-DIVE PREPARATION

### MLOps Concepts to Review
- **Model Registry**: versioning, artifact stores, reproducibility
- **CI/CD for ML**: data validation, model testing, deployment pipelines, canary vs blue-green
- **Feature Store**: concept and purpose (even if not directly experienced)
- **ML monitoring**: data drift, model drift, concept drift

### RAG/GenAI Concepts
- **RAG pipeline**: query → retrieval (vector search + keyword search) → re-rank → augment prompt → generate
- **Chunking strategies**: fixed-size, sentence-based, semantic chunking
- **Embedding models**: sentence-transformers, OpenAI embeddings
- **Hybrid retrieval**: combining dense (vector) and sparse (BM25) search
- **Guardrails**: input validation, output validation, content filtering
- **Structured output**: JSON mode, function calling, Pydantic validation

### Search/IR Metrics (Your Strength!)
- **NDCG (Normalized Discounted Cumulative Gain)**: position-weighted relevance, you optimized this for Expedia
- **MAP (Mean Average Precision)**: average of precision at each relevant result
- **MRR (Mean Reciprocal Rank)**: position of first relevant result
- **A/B testing for search**: online vs offline metrics, interleaving

### LLM Evaluation
- **Faithfulness**: is the answer grounded in the retrieved context?
- **Grounding**: can every claim be traced to a source document?
- **Relevance**: does the answer address the question?
- **Hallucination detection**: cross-referencing output with source documents
- **Human evaluation**: Likert scales, side-by-side comparisons

---

## 7. POTENTIAL TECHNICAL QUESTIONS & ANSWERS

### Q: "How would you design a RAG system for scholarly papers?"
**A**: "I'd approach it in layers. First, the retrieval layer: chunk papers into meaningful units (abstract, sections, figures/tables), generate embeddings using a domain-specific model, store in a vector DB. For scholarly content, I'd use hybrid retrieval — combining vector similarity search with keyword search (BM25) since exact terminology matters in science. Then a re-ranking step to improve precision. For generation, I'd use a foundation model with careful prompt engineering including source attribution, and implement guardrails: check that every claim in the output can be traced to a retrieved chunk. The evaluation pipeline would measure faithfulness (is every claim grounded?), relevance (does it answer the query?), and compare against human annotations. Given Elsevier's corpus size, the engineering challenges around scalability and cost optimization would be critical."

### Q: "Tell me about your experience with ML pipelines in production."
**A**: "At GLP, I owned the full ML lifecycle as the first data hire. I built PySpark ETL pipelines processing consumer credit data, implemented a data quality framework with schema validation, trained credit scoring models, deployed them, and built portfolio monitoring dashboards. More recently, I built a Databricks lakehouse with real-time streaming ingestion, Medallion Architecture, and a quarantine-and-replay pattern for data quality. I've also built automated pipelines using Airflow and Docker. My Databricks certification covers MLflow for experiment tracking and model management."

### Q: "What's your experience with NDCG and search ranking?"
**A**: "Direct experience — I built a hotel recommendation system for a Kaggle competition optimizing on NDCG@5. I used learning-to-rank models (LightGBM, XGBoost with SVD) on 4.9M search records, engineering temporal, behavioral, and user-preference features. Achieved NDCG@5 of 0.392, top 5% in the competition. I understand the tradeoffs between pointwise, pairwise, and listwise ranking approaches, and how offline metrics like NDCG relate to online user satisfaction."

### Q: "How do you evaluate LLM outputs?"
**A**: "In my job application pipeline, I implemented multiple validation layers for LLM outputs. The system uses a deterministic lookup approach — the LLM outputs structured IDs rather than freeform text, and each ID maps to a verified source. I also built blocking validation gates: if the LLM outputs an invalid category, unknown ID, or hallucinated content, the entire output is rejected. For a scholarly context, I'd add faithfulness scoring (can every claim be traced to a source?), grounding checks against the retrieved documents, and human evaluation for edge cases."

### Q: "How would you handle model monitoring in production?"
**A**: "At GLP, I built portfolio monitoring tracking delinquency rates and early warning indicators — essentially model performance monitoring for credit scoring. The principles transfer: track prediction distributions over time to detect data drift, compare production performance against baseline metrics, set up alerts for degradation. For LLM-based features, monitoring would also include latency, token costs, and output quality metrics (faithfulness, hallucination rate). I'd use a combination of automated metrics and periodic human evaluation."

---

## 8. VISA & LOGISTICS

- **Current status**: Orientation Year (Zoekjaar), valid until November 2026
- **What you need**: Highly Skilled Migrant (Kennismigrant) visa
- **RELX/Elsevier**: Almost certainly an IND recognized sponsor (erkend referent) — large multinational
- **Salary threshold**: €3,122/month reduced rate (post-Zoekjaar transition)
- **Processing**: 2-4 weeks
- **Message**: "I'm currently on the Orientation Year permit with full work authorization. For a long-term arrangement, I'd need a Kennismigrant visa, which I understand RELX/Elsevier can sponsor as a recognized sponsor. The process is straightforward."

---

## 9. RED FLAGS TO AVOID
- Don't oversell MLOps platform experience (SageMaker, MLflow) — be honest about gaps
- Don't pretend to know Elasticsearch deeply — instead bridge from what you know
- Don't downplay the career transition (2019-2023) — frame as intentional pivot to AI
- Don't forget to show enthusiasm for the scholarly domain — this is meaningful work
