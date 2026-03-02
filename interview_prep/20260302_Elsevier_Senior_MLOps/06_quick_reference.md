# Quick Reference — Elsevier Senior MLOps Interview
## 面试速查表 (打印这页！)

---

## YOUR PITCH (30 sec)
"ML Engineer, 6 years experience, MSc AI from VU Amsterdam (8.2 GPA). I bridge data science and engineering — exactly what this role asks for. Built production ML systems end-to-end: PySpark pipelines, data quality frameworks, credit scoring models. Recently: Databricks lakehouse, LLM-powered applications, recommendation system optimized on NDCG. Excited about bringing GenAI/RAG to scholarly content at Elsevier."

---

## ELSEVIER KEY FACTS
- Part of RELX Group (£9.6B revenue, STM division growing 5%, margin 34.8%)
- **CEO**: Kumsal Bayazit | **CTO**: Jill Luber (21+ years, manages 2,000+ engineers)
- **Scopus**: 100M+ records, 27K journals, 2.4B citations, 19.6M author profiles
- **Scopus AI** (your direct work area):
  - RAG Fusion (patent-pending): Multiple query variants → parallel vector search → **reciprocal rank fusion** → rerank (miniLM) → OpenAI GPT on Azure
  - **Copilot query tool**: Decides vector vs keyword vs both
  - **Deep Research**: Agentic AI, multi-page reports
  - Led by **Maxim Khan** (SVP Analytics Products)
- **ScienceDirect AI**: Launched March 2025, full-text RAG chat, experiment comparison tables
- **LeapSpace** (Q1 2026, NOW LIVE): Unified AI workspace = Scopus AI + ScienceDirect AI
  - Trust Cards, Claim Radar, Deep Research, Funding Discovery
  - "Grounded AI" — RELX's core strategy: RAG over trusted content, <1% hallucination
- **Neo4j knowledge graph**: 4B+ relationships, GraphQL layer, powers Scopus search + peer review conflict detection
- **ELSSIE Platform**: Spark, Hadoop, Cassandra, Kafka, Solr (all on AWS)
- **Glassdoor**: Software engineers 4.3/5, 98% recommend, work-life balance 4.8/5

---

## YOUR STRENGTHS (Hit These!)
1. **NDCG optimization** — Expedia recommendation system, NDCG@5 = 0.392, top 5%
2. **Full ML lifecycle** — GLP: first data hire, owned everything
3. **PySpark/Databricks** — ETL pipelines, lakehouse, Medallion Architecture
4. **Data quality** — Quarantine-and-replay pattern, schema validation
5. **LLM quality gates** — Job-hunter: bullet ID validation, blocking gates, no hallucination
6. **NLP academic foundation** — MSc AI, NLP 9.0/10, Deep Learning 9.5/10

---

## YOUR GAPS (Honest + Bridge)
| Gap | Bridge |
|-----|--------|
| No SageMaker production | Databricks cert covers MLflow; platform-specific tooling is learnable |
| No Elasticsearch | Large-scale querying with Hadoop/Hive, understand search concepts from rec sys |
| Limited RAG production | LLM APIs in production (Claude), prompt eng, structured output, validation |
| No Neo4j/graph DB | Understand graph concepts (GNN project with PyTorch Geometric) |
| New to scholarly domain | NLP coursework + thesis = academic foundation; excited about the mission |

---

## STAR STORIES READY
1. **ML Lifecycle** (GLP): First data hire → built everything from scratch
2. **Data Quality** (Lakehouse): Quarantine-and-replay, zero data loss
3. **NDCG Ranking** (Expedia): Learning-to-rank, 4.9M records, top 5%
4. **LLM Validation** (Job Hunter): Deterministic lookup, blocking gates, no hallucination
5. **Cross-functional** (GLP): Bridge between risk, product, ops, legal

---

## TECHNICAL QUICK-FIRE

### RAG Pipeline (Generic)
Query → Embed → Retrieve (vector + BM25 hybrid) → Rerank → Augment prompt → Generate → Validate

### Elsevier's RAG Fusion (Know This!)
User query → LLM generates **multiple query variants** → Parallel vector search on each → **Reciprocal Rank Fusion** merges results → miniLM reranking → OpenAI GPT generation with strict prompt constraints → If insufficient evidence, refuse to answer (hallucination prevention)

**Reciprocal Rank Fusion formula**: score = Σ 1/(k + rank_i) across all query variants

### GAR+RAG (from JD — know the difference!)
- **GAR** (Generation-Augmented Retrieval): LLM expands/reformulates query BEFORE retrieval
- **RAG** (Retrieval-Augmented Generation): Retrieved docs ground the LLM's output
- Combined = Elsevier's approach: AI understands the query first, then retrieves, then generates grounded answers

### IR Metrics
- **NDCG**: Position-weighted relevance, graded (0-1 scale)
- **MAP**: Average precision at each relevant result
- **MRR**: Reciprocal of first relevant result's rank
- In RAG context: LLMs process all docs at once (not sequential like humans)

### LLM Evaluation
- **Faithfulness**: Every claim grounded in retrieved context?
- **Grounding**: Can trace to source document?
- **Hallucination**: Cross-reference output vs source
- **Relevance**: Does it answer the question?

### MLOps Concepts
- **Model Registry**: Version models + artifacts, reproducibility
- **CI/CD for ML**: Data validation → model testing → staging → canary deploy
- **Feature Store**: Centralized feature computation + serving
- **Monitoring**: Data drift, model drift, concept drift, latency, cost

### Chunking Strategies (for RAG)
- Fixed-size windows with overlap
- Sentence-based (spaCy, NLTK)
- Semantic chunking (group by meaning)
- For scholarly: section-based (abstract, methods, results, discussion)

---

## SHOW YOU DID RESEARCH (Impress Them!)
- "I read about Scopus AI's RAG Fusion approach — generating multiple query variants and merging via reciprocal rank fusion is elegant for handling query ambiguity"
- "The Scopus AI (telescope) vs. ScienceDirect AI (microscope) distinction makes sense — and LeapSpace unifying them is the logical next step"
- "I noticed the move to Agentic AI with Deep Research — this changes the interaction model from single-query to iterative research planning"
- "Hallucination mitigation is much higher-stakes in scholarly context — a wrong citation could undermine research integrity. Your <1% hallucination rate with grounded AI is impressive"
- Mention CTO Jill Luber's emphasis on "speed with ethics" if culture comes up

## NEW INTEL (from deep research — high-impact!)
- **Elsevier deploys self-hosted LLMs** on Kubernetes using **vLLM** (not just Azure OpenAI!) — KubeCon Europe 2025 talk by Priya Samuel (Elsevier)
  - Also use **Ollama**, **LoRAX** for multi-model serving, **Axolotl** for fine-tuning
- **Neo4j scale**: **200K queries/minute**, sub-300ms response time, replaced a 200-node distributed system with <10 Neo4j nodes
- **RELX tech spend**: £1.9 billion/year on technology, 12,000 technologists across group
- **GitHub**: `elsevierlabs-os/clip-image-search` (77 stars) — fine-tuning CLIP for medical image search; `soda` — Solr Dictionary Annotator for Spark
- **elsevierPTG/interviews** has coding challenges (C#/Java/JS) — for ML role, expect Python-based assessment instead

## QUESTIONS TO ASK (Pick 2-3)
1. "With LeapSpace now live, what's the team's focus — expanding capabilities or optimizing the RAG Fusion pipeline?"
2. "How does the Copilot query tool decide between vector search and keyword search? Is that a model-based decision or rule-based?"
3. "What's the balance between Scopus AI (abstracts) and ScienceDirect AI (full-text) in the team's roadmap?"
4. "How does the Neo4j knowledge graph integrate with the RAG pipeline — does graph context feed into retrieval or generation?"
5. "What's the biggest evaluation challenge right now — faithfulness metrics, or something else?"
6. "What does the team look like? How many ML engineers, and how do you collaborate with Ops?"

---

## VISA (If Asked)
"I'm on the Orientation Year permit with full work authorization. For long-term, I'd need a Kennismigrant visa — RELX can sponsor as a recognized sponsor. Process takes 2-4 weeks."

---

## RED FLAGS TO AVOID
- Don't oversell MLOps platform experience
- Don't pretend to know Elasticsearch deeply
- Don't downplay career transition — frame as intentional pivot to AI
- Show genuine enthusiasm for scholarly AI — this is meaningful work
- Don't be vague about NDCG — you have direct experience, be specific!
