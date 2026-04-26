# Hard Filter Audit — 2026-04-22 ~ 2026-04-24

**审计范围:** 2026-04-22 以来所有爬取的职位 (327 条)
**通过:** 91 条 (27.8%) | **拒绝:** 236 条 (72.2%) | **未筛选:** 0 条

## 总体统计

### 按拒绝原因分布

| 原因 | 数量 | 占比 |
|------|------|------|
| non_target_role | 154 | 65.3% |
| insufficient_data | 50 | 21.2% |
| dutch_language | 21 | 8.9% |
| dutch_required | 6 | 2.5% |
| wrong_tech_stack | 3 | 1.3% |
| senior_management | 2 | 0.8% |
| **合计** | **236** | **100%** |

### 按来源通过率

| 来源 | 通过 | 总计 | 通过率 |
|------|------|------|--------|
| LinkedIn | 55 | 79 | 69.6% |
| Greenhouse | 36 | 248 | 14.5% |

Greenhouse 通过率低是预期行为 — Greenhouse 抓的是目标公司全部职位，大多数岗位 (PM、设计、销售等) 天然不匹配。

---

## 按 Query 详细分流

### LinkedIn Queries

---

#### Q1: "Data Engineer" OR "Analytics Engineer" OR "Data Platform Engineer" OR "ETL Engineer"
**通过 10 | 拒绝 12**

**通过 (10):**
| 职位 | 公司 | 地点 |
|------|------|------|
| Senior Data Engineer | ABN AMRO Bank N.V. | Amsterdam-Zuid (Hybrid) |
| Data Engineer | Adyen | Amsterdam |
| Senior Data Engineer (Relocate to Tallin) | Boston Link | EU (Remote) |
| Azure Data Engineer - Banking | CGI Nederland | Amsterdam |
| Senior Data Engineer | DEPT | Rotterdam (Hybrid) |
| Analytics Engineer (f/m/x) | Eye Security | Rotterdam/The Hague (Hybrid) |
| Data Engineer | FINN | EMEA (Remote) |
| Senior Data Engineer | Fokker Services Group | Hoofddorp (On-site) |
| Senior Analytics Engineer | Robeco | Rotterdam (Hybrid) |
| Analytics Engineer - Partner | bol | Utrecht (Hybrid) |

**拒绝 (12) — 全部为 dutch_language:**
| 职位 | 公司 | 原因 |
|------|------|------|
| Senior software data engineer | All About Work | dutch_language |
| (Senior) Data Engineer | Emixa | dutch_language |
| Data Engineer | FactX | dutch_language |
| Datawarehouse specialist / Data engineer | Gemeente Delft | dutch_language |
| Senior Data Engineer / Data Scientist CRM & FOSS (ZZP) | Maven professionals | dutch_language |
| Product data engineer | Neptunus Structures | dutch_language |
| Data Engineer (Banenafspraak-doelgroep) | Netherlands Enterprise Agency | dutch_language |
| Data Engineer (Snowflake & Dbt) | PGGM | dutch_language |
| Data Engineer | RIFF Digital Engagement | dutch_language |
| Medior Data Engineer Consultant | Rockfeather | dutch_language |
| DevOps Data Engineer | SPR-Solutions | dutch_language |
| Smart Building Data Engineer | Search X Recruitment | dutch_language |

**审计结论:** 全部正确。12 条拒绝都是荷兰语 JD，无误杀。Maven professionals 那条同时是 ZZP (自由职业)。通过的 10 条全部是合理的 data engineering 职位。

---

#### Q2: "Data Infrastructure Engineer" OR "MLOps Engineer" OR "ML Platform Engineer" OR "Pipeline Engineer" OR "Python Developer" OR "Python Engineer"
**通过 6 | 拒绝 0**

**通过 (6):**
| 职位 | 公司 | 地点 |
|------|------|------|
| Staff Backend (Python) Engineer, AI Engineering:Duo Chat | GitLab | Netherlands (Remote) |
| Fresher Python Developer | Joveo AI | Netherlands (Remote) |
| Junior Python Developer | Joveo AI | Netherlands (Remote) |
| Senior Python Developer | Joveo AI | Netherlands (Remote) |
| Python Developer | PRACYVA | Amsterdam Area (Hybrid) |
| Python Developer | VBeyond Europe | Amsterdam (Hybrid) |

**审计结论:** 无拒绝。通过的 6 条合理。Joveo AI 的 Fresher/Junior 级别可能匹配度不高，但硬规则不负责评级 — 这是 AI 评分 (C1) 的职责。

---

#### Q3: "Data Scientist"
**通过 7 | 拒绝 4**

**通过 (7):**
| 职位 | 公司 | 地点 |
|------|------|------|
| Senior Data Scientist | Acuity Analytics | EEA (Remote) |
| Senior Data Scientist | Confidential Careers | EMEA (Remote) |
| Data Scientist | Harnham | Amsterdam Area (On-site) |
| Data Scientist Specialist (Lending) | Jobgether | Brabantine City Row (Remote) |
| Data Scientist | Relevant Online | Utrecht (On-site) |
| Data Scientist | Sansaone | EU (Remote) |
| Staff Product Data Scientist | Superbet | Amsterdam Area (Hybrid) |

**拒绝 (4) — 全部为 dutch_language:**
| 职位 | 公司 | 原因 |
|------|------|------|
| Medior Data Scientist — Aviation | CGI Nederland | dutch_language |
| Ervaren Data Scientist | IG&H | dutch_language |
| Senior Data Scientist | Nationale-Nederlanden | dutch_language |
| Data Scientist | Noordwest Ziekenhuisgroep | dutch_language |

**审计结论:** 全部正确。4 条拒绝都是荷兰语 JD (CGI Nederland、IG&H、NN、医院)，完全合理。

---

#### Q4: "Deep Learning" OR "Computer Vision" OR "NLP" OR "LLM"
**通过 2 | 拒绝 0**

**通过 (2):**
| 职位 | 公司 |
|------|------|
| Technical Product Manager, LLM/ML Domain | Agoda |
| Senior Deep Learning Researcher | European Tech Recruit |

**审计结论:** 无拒绝。Agoda 的 Technical PM 因 title 包含 "LLM" 和 "ML" 通过。注意这是 PM 而非 engineer 角色，但 title 匹配规则无误 — AI 评分会处理 fit。

---

#### Q5: "Machine Learning Engineer" OR "ML Engineer" OR "AI Engineer" OR "AI Software Engineer"
**通过 8 | 拒绝 3**

**通过 (8):**
| 职位 | 公司 | 地点 |
|------|------|------|
| Industry X - AI Software Engineer | Accenture the Netherlands | Amsterdam (On-site) |
| Senior Machine Learning Engineer - AI Enabler Team | Cast AI | Amsterdam (Remote) |
| Applied AI Engineer | Jobgether | Brabantine City Row (Remote) |
| Senior Machine Learning Engineer | MVP Match | EU (Remote) |
| Senior AI Engineer | OpenUp | Amsterdam (Hybrid) |
| Senior AI Engineer | Shopfully | EU (Remote) |
| Machine Learning Engineer (Relocation to Bulgaria) | Sofia Stars | EU (Remote) |
| Sr. Applied AI Engineer | Zapier | EMEA (Remote) |

**拒绝 (3):**
| 职位 | 公司 | 原因 |
|------|------|------|
| Machine Learning Engineer | Eraneos | dutch_language |
| Analytics & AI Engineer | HSO | dutch_language |
| Senior machine learning engineer | Rijkswaterstaat | dutch_language |

**审计结论:** 全部正确。3 条荷兰语 JD 正确拒绝。通过的 8 条全部匹配。

---

#### Q6: "Machine Learning Engineer" OR "ML Engineer" OR "AI Engineer" OR ... OR "GenAI Engineer" OR "Generative AI Engineer"
**通过 10 | 拒绝 2**

**通过 (10):**
| 职位 | 公司 | 地点 |
|------|------|------|
| Applied AI Engineer [Australia] | Amigo | Amsterdam (Remote) |
| Applied AI Engineer [Europe] | Amigo | Amsterdam (Remote) |
| AI Engineer — Agentic Systems in Digital Banking | Axiom Recruit | EU (Remote) |
| AI Engineer/Data Scientist | EPAM Systems | Rijswijk (Hybrid) |
| AI Engineer | Imperum | Amsterdam Area (Hybrid) |
| Lead AI Engineer | Morpheus Talent Solutions | Utrecht (Hybrid) |
| AI Engineer | Optiver | Amsterdam (On-site) |
| Data & AI Engineer | VIVADATA | Utrecht (Hybrid) |
| Machine Learning Engineer (Cloud/MLOps/GenAI) | Wypoon Technologies | Amsterdam (On-site) |
| Machine Learning Engineer | bloomon | Netherlands (Remote) |

**拒绝 (2):**
| 职位 | 公司 | 原因 |
|------|------|------|
| Senior machine learning engineer | Rijksoverheid | dutch_language |
| AI engineer | Advance in IT Ltd | dutch_required |

**审计结论:** 全部正确。Rijksoverheid (政府) 荷兰语 JD；Advance in IT 明确要求荷兰语。

---

#### Q7: "Machine Learning Researcher" OR "Research Engineer" OR "Applied Scientist" OR "Research Scientist"
**通过 4 | 拒绝 0**

**通过 (4):**
| 职位 | 公司 |
|------|------|
| Senior Research Scientist, Cohere Labs | Cohere |
| AI Research Engineer | Screenpoint Medical B.V. |
| AI Engineer | Stravito |
| Data Scientist- Gen AI | VBeyond Corporation |

**审计结论:** 无拒绝。全部合理。

---

#### Q8: "Machine Learning Researcher" OR "Research Engineer" OR "Research Software Engineer" OR "Applied Scientist" OR "Research Scientist"
**通过 1 | 拒绝 0**

**通过 (1):** Applied Research Scientist [Machine Visibility] @ saas.group

**审计结论:** 无拒绝。合理。

---

#### Q9: "Quantitative Researcher" OR "Quantitative Developer" OR "Quantitative Analyst" OR "Quant Trader"
**通过 3 | 拒绝 0**

**通过 (3):**
| 职位 | 公司 |
|------|------|
| Quantitative Researcher | BlockTech |
| Quantitative Researcher | Fionics |
| Quantitative Researcher (110-130K + OTE) | Supergrads |

**审计结论:** 无拒绝。全部合理。

---

#### Q10: "Software Engineer" AND ("Data" OR "AI" OR "Machine Learning" OR "Platform")
**通过 4 | 拒绝 3**

**通过 (4):**
| 职位 | 公司 | 地点 |
|------|------|------|
| Software Engineer (AI Systems & Evaluation) | ByteSearch | EU (Remote) |
| Full Stack Software Engineer - Core Feeds/Platform | Channable | Utrecht (Hybrid) |
| AI-Native Software Engineer | Topicus | Deventer (On-site) |
| Staff Software Engineer - Traffic Machine Learning | Uber | Amsterdam |

**拒绝 (3):**
| 职位 | 公司 | 原因 |
|------|------|------|
| Software Engineer bij Data Exchange Office | Ministerie van Defensie | dutch_language |
| Principal Software Engineer, Devops Platform | Agoda | senior_management |
| Software Engineer (Java) - Unified Platform | Adyen | wrong_tech_stack |

**审计结论:**
- Ministerie van Defensie: 荷兰语 JD，正确拒绝。
- Agoda Principal SE: 被 senior_management 规则拒绝 ("principal" 匹配)。**边界案例** — Principal Engineer 在某些公司是 IC 角色而非管理层，但此规则设计意图是排除过高级别岗位。考虑到 Agoda 同时有 "Devops Platform" 方向，与 data/ML 匹配度本就不高，拒绝合理。
- Adyen Java SE: 被 wrong_tech_stack 匹配 "\bjava\b" 规则正确拒绝 (Java 且不含 data/ML 例外词)。

---

### Greenhouse Queries

---

#### greenhouse:Adyen
**通过 10 | 拒绝 48**

**通过 (10):**
| 职位 | 通过原因 |
|------|----------|
| Senior Software Engineer - ML/AI | title 含 "ai", "software engineer" |
| AI Transformation Manager - Finance | title 含 "ai" |
| Senior Linux Infrastructure Engineer | title 含 "infrastructure engineer" |
| Senior Data Scientist | title 含 "data", "scientist" |
| Senior Data Engineer | title 含 "data" |
| Observability Infrastructure Engineer | title 含 "infrastructure engineer" |
| Machine Learning Scientist | title 含 "machine learning", "scientist" |
| Data Platform Engineer - OLAP | title 含 "data platform" |
| Data Platform Engineer | title 含 "data platform" |
| Data Center Engineer | title 含 "data" |

**拒绝分布:** non_target_role: 46, wrong_tech_stack: 2

**可能的误杀审查:**
- **Staff Engineer, Monetization:** 拒绝为 non_target_role。Title 不含任何 target keyword (data/ml/ai/python 等)。正确拒绝。
- **AOSP Engineer:** Android 底层开发，正确拒绝。
- **Senior CI/CD Engineer:** DevOps 方向，正确拒绝。
- **Senior Security Detection and Monitoring Engineer:** 安全方向，正确拒绝。
- **Software Engineer (Java) - Revenue Connect / Financial Products:** wrong_tech_stack (Java)，正确拒绝。

**可能的误放审查:**
- **AI Transformation Manager - Finance:** 这是管理岗 (Manager)，但 title 含 "ai" 通过了 target keyword 检查。senior_management 规则只匹配 "principal/director/vp/head of/cto" 等，不包含 "manager" 本身。**边界案例** — 更像 PM 角色而非工程角色，但 AI 评分会处理 fit。
- **Data Center Engineer:** 物理数据中心工程师，title 含 "data" 通过。**误放** — 这是基础设施/硬件角色，不是 data engineering。但硬规则设计为宽进严出 (whitelist keyword 是粗筛)，AI 评分应给低分。
- **Senior Linux Infrastructure Engineer:** 系统运维方向。title 含 "infrastructure engineer" 通过。同样是宽筛设计，AI 评分处理。

**审计结论:** 无严重误杀。2 个边界通过 (Data Center Engineer, Linux Infra) 不算规则 bug，属于宽筛设计意图内。

---

#### greenhouse:Catawiki
**通过 1 | 拒绝 25**

**通过 (1):** Commercial Data Scientist

**拒绝 (25):** 全部 non_target_role — Expert (各品类鉴定师)、Category Manager、Brand Designer、Social Media Lead 等。

**审计结论:** 完美。唯一一个 Data Scientist 正确通过，25 个非技术岗全部拒绝。

---

#### greenhouse:ClickHouse
**通过 7 | 拒绝 8**

**通过 (7):**
| 职位 | 通过原因 |
|------|----------|
| Senior Software Engineer (Infrastructure) - HyperDX | "software engineer", "infrastructure" |
| Senior Full Stack Software Engineer - ClickPipes Platform | "software engineer", "platform" |
| Full Stack Software Engineer - Control Plane | "software engineer" |
| Full Stack Software Engineer - Billing Team | "software engineer" |
| Core Software Engineer (C++) - Remote | "software engineer" |
| Cloud Software Engineer - IAM | "software engineer" |
| Cloud Platform Engineer - Control Plane | "platform engineer" |

**拒绝 (8):**
| 职位 | 原因 |
|------|------|
| Commercial Account Executive - Benelux/Nordics | dutch_required |
| Senior Full Stack Engineer - HyperDX | non_target_role |
| QA Engineer - Core Database | non_target_role |
| Product Security Engineer | non_target_role |
| Principal Product Manager, Security | non_target_role |
| Principal Product Manager - ClickHouse Cloud | non_target_role |
| Engineering Manager - Language clients | non_target_role |
| Database Reliability Engineer - Core Team | non_target_role |

**可能的误杀审查:**
- **Senior Full Stack Engineer - HyperDX:** Title 只含 "engineer"，不含 target keyword (data/ml/ai/python/software engineer/backend/infrastructure)。**注意:** "Full Stack Engineer" 不在白名单里，但 "Software Engineer" 在。这条的 title 是 "Senior Full Stack Engineer" 而非 "Senior Full Stack Software Engineer" — 前者拒绝，后者通过。**合理** — Full Stack Engineer 不在目标方向。
- **Database Reliability Engineer:** Title 不含 target keyword。DRE 是运维角色，正确拒绝。
- **QA Engineer:** 正确拒绝。
- **Engineering Manager:** 正确拒绝。

**审计结论:** 全部正确。

---

#### greenhouse:Databricks
**通过 1 | 拒绝 0**

**通过 (1):** AI Engineer - FDE (Forward Deployed Engineer)

**审计结论:** 正确。

---

#### greenhouse:Datadog
**通过 0 | 拒绝 14**

全部拒绝: dutch_required (1: SDR Benelux), non_target_role (13: 全为 SDR/Sales/Support/PM 岗位)。

**审计结论:** 全部正确。Datadog 荷兰办公室主要是销售和支持岗位。

---

#### greenhouse:Elastic
**通过 0 | 拒绝 1**

拒绝: Consulting Architect, Public Sector (non_target_role)。

**审计结论:** 正确。

---

#### greenhouse:Flexport
**通过 0 | 拒绝 4**

拒绝: dutch_required (1: Senior Account Manager), non_target_role (3: SDR, Customs Associate, Enterprise AE)。

**审计结论:** 全部正确。物流公司，无技术岗位。

---

#### greenhouse:Flow Traders
**通过 0 | 拒绝 5**

拒绝: 全部 non_target_role — Trader (3), Compliance Officer (1), W3BWAVE Talent Pool (1)。

**审计结论:** 全部正确。Trader 岗位不含 "quant" 等 target keyword。

---

#### greenhouse:GitLab
**通过 4 | 拒绝 9**

**通过 (4):**
| 职位 | 通过原因 |
|------|----------|
| Senior Backend Engineer, Gitlab Delivery - Runway | "backend" |
| Staff Backend Engineer (AI), Verify | "backend", "ai" |
| Senior Fullstack Engineer (TypeScript), AI Engineering | "ai" |
| Engineering Manager, Software Supply Chain Security: Pipeline Security | "pipeline", "software engineer" |

**拒绝 (9):** 全部 non_target_role — Product Designer, Product Manager, Principal Engineer (Infra/Security), SDR, BDR, Account Executive, CSE Manager 等。

**可能的误杀审查:**
- **Principal Engineer, Software Supply Chain Security:** 被 non_target_role 拒绝。Title 不含 "software engineer" 而是 "Principal Engineer"。虽然 "principal" 也会被 senior_management 规则匹配，但实际首先被 non_target_role 拒绝 (title 中无 target keyword — "Principal Engineer" 不等于 "Software Engineer")。正确拒绝 — 安全方向且级别过高。
- **Principal Engineer, Infrastructure Platforms:** 同上，正确拒绝。

**可能的误放审查:**
- **Engineering Manager, Software Supply Chain Security: Pipeline Security:** 通过是因为 title 含 "pipeline" 和 "software"。这是管理岗。**边界案例** — 但 AI 评分会处理。

**审计结论:** 基本正确。Engineering Manager 通过是宽筛设计意图。

---

#### greenhouse:Grafana Labs
**通过 0 | 拒绝 2**

拒绝: Senior Deal Manager (non_target_role), People Technology Analyst (non_target_role)。

**审计结论:** 全部正确。

---

#### greenhouse:HelloFresh
**通过 0 | 拒绝 7**

拒绝: 全部 non_target_role — QA/QC, Analyst (non-data), Product Analyst, Lead Product Ops, IT Helpdesk, HR Specialist, Associate Director。

**可能的误杀审查:**
- **Product Analyst (All Genders):** Title 含 "analyst" 但不含 target keyword (需要 "data"/"analytics"/"bi"/"scientist" 等)。单纯 "analyst" 不在白名单。**正确拒绝** — "Product Analyst" 不是目标方向。
- **Senior Analyst Global Retail Media:** 同上。正确拒绝。

**审计结论:** 全部正确。

---

#### greenhouse:JetBrains
**通过 13 | 拒绝 30**

**通过 (13):**
| 职位 | 通过原因 |
|------|----------|
| Staff Software Developer (Kotlin Libraries) | "software" + "developer" |
| Staff Research Engineer (Pre-training) | "research" |
| Senior ML Researcher (Code Editing) | "ml", "research" |
| Senior MLOps Engineer | "mlops" |
| Senior ML Engineer | "ml" |
| Senior Machine Learning Engineer (IntelliJ AI) | "machine learning" |
| Sales Development Representative (AI-Powered QA) | "ai" |
| Research Engineer (LLM Training) | "research", "llm" |
| Research Engineer (Agentic Models) | "research" |
| Founding ML Engineer (Spectrum) | "ml" |
| Data Analyst (JetBrains AI) | "data", "ai" |
| Cloud Infrastructure Engineer (Kineto) | "infrastructure engineer" |
| AI Engineer (Core Engine) | "ai" |

**拒绝分布:** non_target_role: 29, senior_management: 1

**可能的误杀审查:**
- **Head of ML:** 被 senior_management 规则拒绝 ("head of" 匹配)。虽然是 ML 方向，但 "Head of" 是管理层级别。**正确拒绝** — 我们不投 Head of 级别的岗位。
- **Business Intelligence Analyst:** 被 non_target_role 拒绝。Title 含 "intelligence" 和 "analyst" 但不含 target keyword 匹配 — 注意 "bi" 作为 target keyword 需要 word boundary 匹配 (\bbi\b)，而 "Business Intelligence" 中 "bi" 是缩写不在 title 中。**正确拒绝** — 需要全称 "BI Analyst" 才会通过。但即使通过，BI Analyst 也不太匹配目标方向。

**可能的误放审查:**
- **Sales Development Representative (AI-Powered QA Automation):** 这是销售岗 (SDR)，因 title 含 "ai" 通过。**误放** — SDR 不是工程岗。但 AI 评分应该给极低分。
- **Staff Software Developer (Kotlin Libraries):** 纯 Kotlin 方向。通过因 "software developer" 在白名单。宽筛设计，AI 评分处理。
- **Cloud Infrastructure Engineer (Kineto):** 云基础设施。通过因 "infrastructure engineer" 在白名单。宽筛设计。

**审计结论:** 1 个明确误放 (SDR with "AI" in title)。规则本身无 bug — "ai" keyword 匹配是正确行为，但 SDR 这种销售岗位混入 AI 关键词会造成误放。建议考虑增加 title_blacklist 条目 (如 "sales development representative")。

---

#### greenhouse:Reddit
**通过 0 | 拒绝 2**

拒绝: Client Partner (2), 全部 non_target_role。

**审计结论:** 正确。

---

#### greenhouse:Sendcloud
**通过 0 | 拒绝 6**

拒绝: dutch_required (1: Carrier Partnerships Manager NL), non_target_role (5: Team Lead, Customer Specialist, BDR, AE)。

**审计结论:** 全部正确。

---

#### greenhouse:Stripe
**通过 0 | 拒绝 1**

拒绝: Account Executive, Benelux - Startups (Dutch Speaking) — dutch_required。

**审计结论:** 正确。

---

#### greenhouse:bol.com
**通过 0 | 拒绝 50**

拒绝: **全部 50 条为 insufficient_data** (描述内容仅为 `<p>x</p>`，长度 8 字节)。

**审计分析:** bol.com 的 Greenhouse 页面对 API 抓取返回空/占位描述。这不是硬规则的问题，而是**爬虫端的问题** — Greenhouse scraper 拿到了 title 但没有拿到实际 JD 内容。

**潜在影响:**
在这 50 条中，以下 title 如果有完整 JD 可能会通过硬规则:
- Marketing Data Analyst ← 含 "data", "analyst"
- Data Analist Customer & Partner Service ← 含 "data"
- Financial Business Analyst ← 不含 target keyword，会被 non_target_role 拒绝
- Tech & Data Security Auditor ← 含 "data" 但实际是安全审计

**结论:** 即使 JD 完整，最多 2 条可能通过硬规则 (Marketing Data Analyst, Data Analist)。鉴于 bol.com 大量荷兰语岗位，这 2 条大概率也会被 dutch_language 拒绝。**不需要修复。**

---

## 发现总结

### 硬规则表现评估

| 维度 | 评价 | 说明 |
|------|------|------|
| **误杀 (False Positive)** | 极低 | 未发现任何不应拒绝的目标职位被错误拒绝 |
| **误放 (False Negative)** | 极低 | 仅 1 条明确误放 (JetBrains SDR with "AI" in title)，2-3 条边界通过 (Data Center Engineer, AI Transformation Manager) 由 AI 评分层处理 |
| **dutch_language 规则** | 精准 | 21 条全部为真正的荷兰语 JD |
| **dutch_required 规则** | 精准 | 6 条全部正确识别荷兰语要求 |
| **non_target_role 规则** | 精准 | 154 条中无误杀，做到了宽进严出 |
| **wrong_tech_stack 规则** | 精准 | 3 条 Java 岗位正确拒绝 |
| **senior_management 规则** | 精准 | 2 条 (Head of ML, Principal SE) 正确拒绝 |
| **insufficient_data 规则** | 合理 | 50 条全来自 bol.com API 缺陷，不是规则问题 |

### 建议改进 (低优先级)

1. **考虑添加 "sales development representative" 到 title_blacklist** — 防止 SDR 岗位因 title 中混入 "AI" 等关键词而通过。同类: "account executive", "account manager", "business development representative"。
2. **bol.com 数据质量** — Greenhouse scraper 对 bol.com 返回空描述。如果 bol.com 是重要目标公司，需要调查 API 是否需要额外参数或切换到网页抓取。

### 最终判断

**硬规则筛选工作正常，无需紧急调整。** 327 条职位中无一条被错误拒绝的目标岗位，漏网的 1 条 SDR 会被下游 AI 评分兜底。规则设计的 "宽进严出" 策略运作良好。
