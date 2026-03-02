# Company Deep Dive — Elsevier (RELX Group)

*Updated: 2026-03-02 — Comprehensive research for interview preparation*

---

## 1. Company Overview

### RELX Group (Parent Company)
- **Ticker**: LSE: REL, NYSE: RELX — global information analytics company
- **CEO**: Erik Engstrom (since 2009; McKinsey alum, ex-Random House COO)
- **HQ**: London, UK
- **Employees**: ~36,000 (incl. ~9,000 technologists and data scientists)
- **Market Cap**: ~GBP 70B+ (one of UK's largest listed companies)
- **Founded**: 1993 (merger of Reed International and Elsevier)
- **Operations**: 40 countries, serving customers in 180+ nations
- **Revenue model**: >80% subscriptions, >90% digital, print down to just 4% of revenue (from 64% 25 years ago)

### Four RELX Divisions
| Division | Revenue Focus | Growth Driver |
|----------|---------------|---------------|
| **Risk & Business Analytics** (LexisNexis Risk) | ~37-40% of revenue | Fraud detection, identity verification, insurance analytics |
| **Scientific, Technical & Medical** (Elsevier) | ~33% of revenue | Journals, databases, AI tools, clinical decision support |
| **Legal** (LexisNexis Legal & Professional) | ~20% of revenue | Legal analytics, Lexis+ AI, workflow tools |
| **Exhibitions** (RX) | ~10% of revenue | Global trade shows, digital lead-gen |

### Elsevier Specifically
- **HQ**: Amsterdam (Radarweg 29, 1043 NX)
- **Founded**: 1880 — one of the world's oldest publishers
- **CEO**: **Kumsal Bayazit** (since 2019; ex-RELX Chief Strategy Officer, ex-Chair of RELX Technology Forum overseeing all 9,000 technologists)
- **CTO**: **Jill Luber** (since Dec 2021; 21+ years in data/engineering/security, led 350 engineers at LexisNexis Risk before managing 2,000+ global engineers at Elsevier)
- **Chairman**: YS Chi
- **Core mission**: Help researchers, clinicians, and life sciences professionals advance discovery and improve health outcomes through trusted content, data, and analytics

---

## 2. Financials (RELX Full-Year 2025 Results, released Feb 12, 2026)

### Group-Level
| Metric | 2025 | 2024 | Growth |
|--------|------|------|--------|
| **Total Revenue** | GBP 9,590m | GBP 9,434m | +7% underlying |
| **Adjusted Operating Profit** | GBP 3,342m | GBP 3,199m | +9% underlying |
| **Operating Margin** | **34.8%** | 33.9% | +90bps |
| **Adjusted EPS** | 128.5p | 120.1p | +10% constant currency |
| **Cash Flow Conversion** | 99% | 97% | Best-in-class |
| **Full Year Dividend** | 67.5p | 63.0p | +7% |
| **Share Buybacks (2025)** | GBP 1,500m | | |
| **Share Buybacks (2026 planned)** | GBP 2,250m | | |

### STM (Elsevier) Division
- **Underlying revenue growth**: 5% (accelerating from prior years)
- **Underlying operating profit growth**: 7%
- **Growth drivers**: Databases, tools, electronic reference, primary research
- **Key metric**: Article processing charges + transformative OA agreements growing; OA articles exceeded 120,000/year, OA mix >30% of new articles in many regions

### 2026 Outlook
- RELX expects "continued positive momentum across the group" — strong underlying revenue and profit growth
- Continued investment in AI-enabled tools across Risk, Science, and Legal
- AI investment expected to support long-term margin expansion

---

## 3. Key Products & Platforms

### Scopus (YOUR Team's Product)
- **World's largest abstract & citation database**: 100M+ records from 27,000+ journals, 7,000+ publishers
- 2.4 billion citations, 19.6 million author profiles
- Publisher-neutral (indexes content from Springer Nature, Wiley, etc.)
- **Revenue model**: Institutional subscriptions

#### Scopus AI (Your Direct Work Area)
- **Launched**: January 2024 (alpha August 2023)
- **Led by**: **Maxim Khan**, SVP Analytics Products and Data Platform
  - Cambridge Chemistry MA, CIMA-qualified
  - Career-long Elsevier executive (VP Product Management, Business Development Lead)
- **Architecture**: Custom RAG (Retrieval-Augmented Generation)
  - **Vector search**: Small language models convert queries to embeddings; cosine similarity against abstracts (2003+)
  - **LLM**: OpenAI GPT hosted on **Microsoft Azure private cloud** (data not shared with OpenAI)
  - **Reranking**: miniLM model
  - **Patent-pending RAG Fusion**: Generates multiple query variants from user input, runs vector search on each, merges & deduplicates via **reciprocal rank fusion**, then feeds top results to LLM
  - **Copilot query tool**: Analyzes query to decide vector search vs. keyword search vs. both; handles complex queries by decomposing them, adds Boolean operators for keyword channel
  - **Prompt engineering**: Uses relevancy, recency, citation count to prioritize sources; strict instructions to refuse answering if insufficient evidence (hallucination mitigation)
  - **Evaluation**: Two frameworks — response quality (relevancy, coherency, safety) + continuous hallucination/bias/toxicity monitoring
- **Features**:
  - Topic Summary + Expanded Summary (with inline numbered citations)
  - Foundational Documents (high-impact papers cited by summary sources)
  - Interactive Concept Maps (keyword-based from abstracts)
  - Emerging Themes (established, rising, novel categorization)
  - Topic Experts
  - **Deep Research** (NEW): Agentic AI with reasoning engine — develops research plan, conducts extensive searches, refines strategy iteratively, produces multi-page reports
- **Content scope**: Abstracts/metadata only (not full text), from 2003 onward for summaries, full corpus for foundational documents

#### ScienceDirect
- Houses **22M+ scientific publications** (full text)
- **ScienceDirect AI** (launched March 2025):
  - "Ask ScienceDirect AI": Query database, get summary with references and source snippets
  - "Reading Assistant": Ask questions about a specific document, answers linked to original text
  - "Compare Experiments": Table comparing experimental goals, methods, results across articles
  - Developed with input from **30,000+ researchers and librarians** from 70 universities
  - Designed to reduce literature review time by **up to 50%**
  - Complementary to Scopus AI: "telescope" (Scopus AI, broad landscape) vs. "microscope" (ScienceDirect AI, full-text deep dive)

#### LeapSpace (Next-Gen Platform, Q1 2026)
- **AI-assisted research workspace** combining Scopus AI + ScienceDirect AI into one seamless experience
- **Publisher-neutral**: Includes subscription and open access content from multiple publishers
- **Trust Cards**: Transparency into every result, supporting critical thinking
- All-in-one: brainstorming, project planning, literature review, collaborator discovery, funding opportunities
- Technologies: Agentic AI, generative AI, reasoning engines, RAG
- **15M+ full-text articles** + **100M+ Scopus abstracts** at launch
- Independent Advisory Board for algorithm transparency and publisher-neutrality
- Existing ScienceDirect AI customers auto-upgraded to LeapSpace

### Knowledge Graph Infrastructure
- **Scopus search powered by Neo4j** — 4B+ relationships
- Entities: works, abstracts, authors, topics, journals, organizations
- **SciVal Knowledge Graph**: ~70M research articles, Neo4j + AWS (Kafka MSK, Lambda)
- **Fingerprint Engine**: Topic identification using NLP
- GraphQL-based query layer
- **Peer review conflict detection** via co-author/co-employment graph traversal
- **ELSSIE Platform**: Knowledge graph + intelligent search system using Apache Spark, Hadoop, Cassandra, Kafka, Solr, GridGain (all on AWS)

### Other AI Products
- **ClinicalKey AI**: Clinical decision support (major expansion Feb 2026 — AI use in healthcare doubled in 2025)
- **PharmaPendium**: Life sciences platform
- **Reaxys AI Search** (Aug 2025): NLP-powered chemistry database — first chemistry DB with natural language search
- **Reaxys Predictive Retrosynthesis**: ML-powered chemical synthesis path prediction
- **SciBite** (acquired): Semantic technologies for biomedical data science

---

## 4. Technology Stack

### Confirmed Tech Stack (from job postings + public sources)
| Layer | Technology |
|-------|-----------|
| **Cloud** | AWS (primary: SageMaker, Bedrock, Lambda, MSK, S3) + Azure (OpenAI hosting, Azure ML) |
| **ML Platforms** | SageMaker, MLflow, Azure ML, Databricks |
| **LLMs** | OpenAI GPT (Azure-hosted), proprietary Elsevier LLMs, Bedrock foundation models |
| **Search & Retrieval** | Elasticsearch/OpenSearch/Solr, vector search (embeddings), Neo4j (graph DB) |
| **Reranking** | miniLM, cross-encoder models |
| **RAG Architecture** | RAG Fusion (patent-pending), GAR+RAG, hybrid retrieval, prompt libraries, guardrails |
| **Data Processing** | Apache Spark/PySpark, Apache Kafka (AWS MSK), Apache Hadoop, Apache Cassandra |
| **Data Platform** | Databricks, Snowflake, Delta Lake, Data Mesh architecture |
| **ML Frameworks** | PyTorch, TensorFlow |
| **Languages** | Python (primary), Java, Scala |
| **Evaluation** | NDCG, MAP, MRR (offline IR), faithfulness/grounding (LLM quality), A/B testing |
| **Infrastructure** | CI/CD for ML, model registries, artifact stores |

### Key Technical Patterns
- **RAG Fusion pipeline**: Query -> LLM generates multiple query variants -> parallel vector search -> reciprocal rank fusion -> reranking -> LLM generation with prompt constraints
- **Hybrid search**: Vector (semantic) + keyword (Boolean) search combined by Copilot query orchestrator
- **GAR+RAG**: Generation-Augmented Retrieval + Retrieval-Augmented Generation (query interpretation, reflection, chunking, embeddings, hybrid retrieval)
- **Evaluation-driven development**: Offline IR metrics (NDCG, MAP, MRR) + LLM quality (faithfulness, grounding) + A/B testing
- **Responsible AI guardrails**: Prompt engineering for hallucination prevention, toxicity filtering, bias detection

---

## 5. Leadership (Key People to Know)

### RELX Level
| Role | Name | Background |
|------|------|------------|
| CEO & Executive Director | **Erik Engstrom** | Since 2009; McKinsey, Random House COO, General Atlantic |
| CFO | **Nick Luff** | Since 2014; ex-Centrica Group Finance Director |
| Chairman | **Paul Walker** | Since 2021; also Chairman of Ashtead & Halma |

### Elsevier Level
| Role | Name | Background |
|------|------|------------|
| CEO | **Kumsal Bayazit** | Since 2019; ex-RELX Chief Strategy Officer, chaired RELX Technology Forum (9,000 technologists) |
| CTO | **Jill Luber** | Since Dec 2021; 21+ years in data/engineering/security; managed 350 engineers at LexisNexis Risk, now 2,000+ at Elsevier. Strong advocate for Responsible AI, diversity (5/10 direct reports are women), culture of experimentation |
| SVP Analytics Products & Data Platform | **Maxim Khan** | Leads Scopus AI; Cambridge Chemistry MA; career Elsevier executive |
| President, Academic & Government | **Judy Verses** | |
| Managing Director, Journals | **Laura Hassink** | |
| President, Health Markets | **Jan Herzhoff, PhD** | |
| EVP Strategy | **Dr. Kieran West, MBE** | |

### CTO Jill Luber's Vision (Important for Interview)
- **Privacy as competitive advantage**: "Trust is a competitive advantage, and losing it through misuse of data can be far more damaging than falling behind in a technology race"
- **Continual learning culture**: "The most important capability any technology team can build is a culture of continual learning and curiosity"
- **Speed with ethics**: "The challenge is to move at speed without compromising core commitments to privacy, transparency and equity"
- **Agentic AI as next frontier**: New questions around autonomy, accountability, and ethics
- **20+ years of AI at Elsevier**: "While Elsevier has been using AI and ML technologies in its products for more than 20 years, we're currently hitting a stride with generative AI"

---

## 6. Culture & Working Environment

### Glassdoor Ratings (2,500+ reviews)
| Metric | Score |
|--------|-------|
| **Overall** | 4.1/5 (trending up) |
| **Software Engineers** | **4.3/5** (78 reviews, 98% would recommend!) |
| **Work-Life Balance** (engineers) | **4.8/5** |
| **Diversity & Inclusion** (engineers) | **4.8/5** |
| **Culture & Values** (engineers) | **4.5/5** |
| **Career Opportunities** (engineers) | 4.0/5 |
| **Compensation** | 3.7/5 |
| **Amsterdam-specific Culture** | 4.3/5 (17.6% above company-wide) |
| **Positive business outlook** | 74% |

### Pros (From Engineer Reviews)
- Excellent work-life balance and flexibility
- Family-focused, ethical treatment of employees and clients
- Small agile teams with autonomy — each team decides how and where to work
- Access to good tools, docs, and dedicated learning time
- Large company = internal mobility, project changes, new technologies
- Company culture that encourages skill development
- Five days annually for community service
- International, diverse environment

### Cons (Be Aware)
- Legacy systems in some areas (important but not well-funded)
- Tech leadership sometimes pivots suddenly on tools/technologies
- Limited pay transparency, low salary increases
- Management restructuring can impact morale and cross-team collaboration
- Career progression pathways not always clear
- Promotion criteria not fully transparent

### Benefits (Amsterdam)
- Dutch Share Purchase Plan
- Annual Profit Share Bonus
- Comprehensive Pension Plan
- Home/office/commuting allowance
- Generous vacation + sabbatical options
- Maternity/paternity leave
- Flexible working hours
- Personal choice budget
- Online training courses + wellbeing programs
- Gym facility in the office
- Work-from-anywhere policy

### Amsterdam Tech Hub
- Elsevier's primary tech hub in Amsterdam
- Collaboration with **Amsterdam Data Science (ADS)** — advancing Amsterdam as talent hub for DS/AI
- Yearly **Data Science master student program** and **Graduate Program** for tech talent
- International, diverse workforce

---

## 7. Competitive Landscape

### Direct Competitors (AI Research Tools)
| Competitor | Key Product | AI Approach | Differentiation |
|-----------|-------------|-------------|-----------------|
| **Springer Nature** | Curie (AI writing assistant) | Manuscript editing/NLP trained on 447 disciplines, 1M+ editorial corrections | Focus on author-side AI, strong OA via SpringerOpen |
| **Clarivate** | Web of Science + AI | Citation analytics, research intelligence | Traditional bibliometrics leader |
| **Semantic Scholar** (Allen AI) | Free AI search engine | ML-based relevance ranking (not just citations) | Best free discovery tool, strong in CS/biomedical |
| **Google Scholar** | Free broad search | Simple, massive coverage | Ubiquitous but less curated |
| **Digital Science** | Dimensions, Altmetric, Figshare | Research data ecosystem | Alternative metrics, data sharing |
| **ResearchGate** | Social network + discovery | Researcher networking | Community-driven |
| **Iris.ai** | AI literature mapping | Concept-based exploration | Startup, niche |

### Market Context
- Global AI for Research Collaboration market: **USD 640M (2024) -> USD 3.45B (2033)**, CAGR 23.2%
- Elsevier's moat: **scale of curated content** (100M+ records, 22M+ full text) + institutional relationships + publisher-neutral positioning

---

## 8. Challenges & Opportunities

### Challenges
1. **Open Access Movement**: Pressure from Plan S, funder mandates, institutional push for free research access; Elsevier responding with transformative Read-and-Publish agreements (285,000+ OA articles in 2025, 3,600+ institutional agreements)
2. **Responsible AI in High-Stakes Context**: Hallucinations in scholarly/clinical context = potentially dangerous; requires robust guardrails, evaluation, and transparency
3. **Content Rights**: Balancing AI features with publisher/author rights — training LLMs on copyrighted content is sensitive
4. **Free Tool Competition**: Semantic Scholar, Google Scholar, open-source tools competing for researcher attention
5. **Legacy Systems**: Some important internal platforms are aging and underfunded
6. **AI Policy Complexity**: All major publishers prohibit AI authorship; Elsevier must enforce this while building AI tools
7. **Pace of AI Change**: GenAI evolving so fast that what was cutting-edge 6 months ago feels outdated (per CTO Jill Luber)

### Opportunities
1. **LeapSpace as Platform Play**: Unified AI workspace could become the "OS for research" — massive lock-in potential
2. **Agentic AI**: Deep Research (Scopus AI) shows the way toward autonomous research agents
3. **Publisher-Neutral Positioning**: Including competitor content builds trust and comprehensiveness
4. **Clinical AI Growth**: AI use in healthcare doubled in 2025; ClinicalKey AI positioned to capture this
5. **Knowledge Graph Advantage**: 4B+ relationships in Neo4j = unique structural data moat
6. **RAG Fusion IP**: Patent-pending technology = defensible technical advantage
7. **Cross-Division AI Synergy**: Learnings from Risk (fraud detection), Legal (Lexis+ AI) can transfer to STM

---

## 9. Why This Role Matters

- Elsevier is in the middle of a **massive AI transformation** — from traditional publisher to AI-powered analytics company
- The Data Science team is the **engine behind Scopus AI, ScienceDirect AI, and LeapSpace**
- This role **bridges experimental models and production systems** — the critical gap in AI product development
- The role covers the **full MLOps lifecycle**: from RAG pipeline engineering to evaluation to deployment
- Growing from search/ranking into **GenAI/RAG/Agentic AI** — one of the highest-growth areas in tech
- Working on products used by **millions of researchers worldwide** — genuine societal impact
- The tech stack (SageMaker, Bedrock, RAG, knowledge graphs) is **highly transferable** to any AI company

---

## 10. Visa & Sponsorship

- Elsevier BV is headquartered in Amsterdam, Netherlands
- As a major international employer, Elsevier is almost certainly an **IND-recognised sponsor** (erkend referent) for Kennismigrant visas
- **Verify**: Check the [IND Public Register of Recognised Sponsors](https://ind.nl/en/public-register-recognised-sponsors) for "Elsevier" or "RELX"
- The Zoekjaar -> Kennismigrant transition is a straightforward path for this type of role
- Salary threshold for Kennismigrant (reduced rate, post-Zoekjaar): EUR 3,122/month — well below expected ML Engineer salary

---

## 11. Key Talking Points for Interview

### Show You Understand Their Products
- "I've researched Scopus AI's RAG Fusion architecture — the approach of generating multiple query variants and merging via reciprocal rank fusion is an elegant solution to the query intent ambiguity problem"
- "The distinction between Scopus AI (telescope, abstracts) and ScienceDirect AI (microscope, full text) makes strategic sense — and LeapSpace unifying them is the obvious next step"
- "The move toward Agentic AI with Deep Research is exciting — it changes the interaction model from single-query to iterative research planning"

### Show You Understand Their Challenges
- "Hallucination mitigation in scholarly context is much higher-stakes than in consumer AI — a wrong citation could undermine research integrity"
- "Balancing speed of AI innovation with Responsible AI principles is the central tension — and getting it right is a competitive advantage"
- "The RAG evaluation problem (faithfulness, grounding, relevance) is technically fascinating and commercially critical"

### Connect Your Experience
- Your experience with production ML systems, data pipelines, and evaluation frameworks directly maps to this role
- Knowledge of search/ranking metrics (NDCG, MAP, MRR) is core to the role
- Experience with cloud platforms (AWS) and ML frameworks (PyTorch) aligns perfectly

---

## 12. Open Source & GitHub Presence

Elsevier maintains several GitHub organizations:
- **[elsevierlabs-os](https://github.com/elsevierlabs-os)** (28 repos): AnnotationQuery, spark-xml-utils, JATS XML transformations
- **[elsevier-research](https://github.com/elsevier-research)** (30 repos): Various research tools
- **[elsevierlabs](https://github.com/elsevierlabs)**: OA corpus, SentenceSimplification
- **[elsevierPTG](https://github.com/elsevierPTG)** (4 repos): **Coding challenges for job applicants** — worth checking before interview!

---

## Sources

- [RELX 2025 Full-Year Results](https://www.relx.com/media/press-releases/year-2026/relx-2025-results)
- [RELX Wikipedia](https://en.wikipedia.org/wiki/RELX)
- [RELX Business Leaders](https://www.relx.com/our-business/business-leaders)
- [Elsevier Leadership](https://www.elsevier.com/about/leadership)
- [Kumsal Bayazit Bio](https://www.elsevier.com/about/leadership/kumsal-bayazit)
- [Jill Luber Bio](https://www.elsevier.com/about/leadership/jill-luber)
- [Jill Luber — Raconteur Interview](https://www.raconteur.net/leadership/elseviers-cto-on-the-new-rules-of-tech-leadership)
- [Jill Luber — Diginomica Interview](https://diginomica.com/what-id-say-me-back-then-elsevier-cto-jill-luber-taking-scary-step-away-leadership-prioritize)
- [Scopus AI Product Page](https://www.elsevier.com/products/scopus/scopus-ai)
- [Scopus AI Under the Hood — Maxim Khan Interview](https://scholarlykitchen.sspnet.org/2024/07/25/interview-with-maxim-khan-about-scopus-ai/)
- [Scopus AI RAG Fusion Flyer](https://researcheracademy.elsevier.com/uploads/2024-08/Scopus%20AI%20RAG%20fusion%20flyer%20(1).pdf)
- [ScienceDirect AI Launch](https://www.elsevier.com/about/press-releases/elsevier-launches-sciencedirect-ai-to-transform-research-with-rapid-mission)
- [LeapSpace Launch](https://www.prnewswire.com/news-releases/elsevier-launches-leapspace-an-ai-assisted-workspace-to-accelerate-research-and-discovery-302618902.html)
- [Elsevier Amsterdam Tech Hub](https://www.elsevier.com/about/careers/technology-careers/amsterdam-tech-hub)
- [Senior MLOps Engineer Job Posting](https://magnet.me/en/opportunity/985776/senior-mlops-engineer)
- [Elsevier Glassdoor Reviews](https://www.glassdoor.com/Reviews/Elsevier-Reviews-E230096.htm)
- [Elsevier Software Engineer Reviews](https://www.glassdoor.com/Reviews/Elsevier-Software-Engineer-Reviews-EI_IE230096.0,8_KO9,26.htm)
- [Elsevier Amsterdam Glassdoor](https://www.glassdoor.com/Reviews/Elsevier-Amsterdam-Reviews-EI_IE230096.0,8_IL.9,18_IM1112.htm)
- [Elsevier Open Access](https://www.elsevier.com/open-access)
- [ClinicalKey AI Expansion](https://www.prnewswire.com/news-releases/elsevier-announces-expansion-flagship-clinical-decision-support-solution-clinicalkey-ai-302689963.html)
- [Elsevier GitHub: elsevierlabs-os](https://github.com/elsevierlabs-os)
- [Elsevier GitHub: elsevierPTG](https://github.com/elsevierPTG)
- [NashTech ELSSIE Platform Case Study](https://www.nashtechglobal.com/our-thinking/case-studies/elsevier/)
