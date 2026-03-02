# TomTom Company Deep Dive

## 1. Company Overview

### At a Glance
| Field | Detail |
|-------|--------|
| **Full Name** | TomTom N.V. |
| **Founded** | 1991 (originally Palmtop Software) |
| **Founders** | Harold Goddijn, Corinne Vigreux, Pieter Geelen, Peter-Frans Pauwels |
| **HQ** | De Ruijterkade 154, Amsterdam 1011 AC, Netherlands |
| **Employees** | ~3,700 globally |
| **Ticker** | TOM2 on Euronext Amsterdam |
| **Industry** | Location Technology, Digital Mapping, Navigation |
| **Global Offices** | 42 locations: Amsterdam, Ghent, Leipzig, Barcelona, Berlin, London, Lodz, Eindhoven, Pune, Taipei, and more |

### Mission
"Engineering the first real-time map" -- TomTom's stated aspiration is to build the world's smartest, continuously-updated map that powers everything from consumer navigation to autonomous driving.

### Business Segments
1. **Location Technology** (86.9% of revenue): Maps, navigation SDKs, traffic data, location APIs for automotive OEMs and enterprises
2. **Consumer** (13.1% of revenue): Direct-to-consumer navigation products (legacy PND devices, new TomTom navigation app)

### Revenue Geographic Split
- Europe: 46%
- Americas: 35.6%
- Rest of World: 18.4%

---

## 2. Core Products & Technology

### TomTom Orbis Maps
The flagship mapping platform, announced in 2022. Combines proprietary data with open-source contributions (Overture Maps Foundation, OpenStreetMap). Features:
- AI-powered map data factory for continuous quality validation
- Customizable via APIs, SDKs, and uncompiled map content
- Supports web, mobile, and embedded platforms
- Compatible with popular open-source tools (MapLibre GL JS)
- Options for 2D/3D visualization, custom color schemes, dark mode

### Orbis Lane Model Maps (launched January 2026)
Lane-level intelligence (geometry, connectivity, markings) at urban scale. Key differentiator: HD-map richness at a fraction of traditional HD map cost, continuously refreshed via AI-powered map factory. Currently available across Germany, scaling to additional countries.

### Automotive Navigation Application (launched September 2025)
Ready-to-use navigation solution built on Orbis Maps + enhanced Navigation SDK. Cuts OEM development time from months to weeks. Features immersive 3D visualization and EV charging optimization.

### ADAS SDK (launched January 2026)
Modular, lightweight toolkit for predictive driver assistance: speed limits, lane connectivity, curvature, gradient, traffic signs. Pre-integrated with Orbis Maps out of the box.

### TomTom AI Agent (showcased CES 2026)
In-car conversational AI assistant: drivers manage complex navigation tasks through natural language. Place recommendations, charging station search near amenities, multi-waypoint route planning. Built with agentic AI and live traffic data.

### TomTom MCP Server (alpha, 2025)
Model Context Protocol server enabling AI agents (Claude, ChatGPT, Llama, Mistral) to access TomTom's live data: maps, traffic, routing, POIs. Open-source on GitHub. Use cases: travel logistics, retail analysis, urban planning, fleet management.

### TomTom Navigation App (2025)
Free smartphone navigation app using NavSDK + Orbis Maps. The first consumer app in years, showcasing the company's latest mapping technology.

### EV Charging Data
Orbis Maps now includes 2M+ verified EV charging points worldwide.

---

## 3. AI Strategy & Initiatives

### AI in Mapmaking (Core)
- Computer vision and ML automate feature detection from satellite imagery (roads, footpaths, buildings)
- AI-powered "map data factory" processes and validates data from diverse sources at scale
- Humans shifted from manual drawing to algorithm refinement, quality assurance, error-checking
- Goal: "machines do the heavy, laborious lifting" (VP Laurens Feenstra)

### Generative AI Strategy
TomTom adopted a **hub-and-spoke model** to democratize GenAI:
- **Hub**: Compact central team of GenAI specialists (strategic direction, oversight)
- **Spokes**: Domain-specific teams with modest budgets, fast prototyping, deep area knowledge
- **Guiding policy**: Democratize innovation, prioritize by impact + team readiness, align with business goals

### Key AI Products & Tools
| Product | Description |
|---------|-------------|
| **TomTom AI Agent** | In-car conversational AI navigation assistant (agentic AI + live data) |
| **Visteon Partnership** | World's first in-car LOCAL AI navigation -- on-device VLM, privacy-first, no cloud required |
| **ChatGPT Location Plugin** | First mapmaker to release ChatGPT plugin (2023) |
| **TomTom MCP Server** | MCP protocol connecting LLMs to TomTom data APIs |
| **Tommy** | AI assistant for in-car digital cockpits |

### Internal AI Tools ("AI @ Work")
- **GitHub Copilot**: 85% of users feel more productive, 70% can focus on more satisfying work
- **Chatty**: Open-source, internally hosted ChatGPT alternative for enhanced data privacy (https://github.com/rijnb/chatty-server/)
- **AI Code Review Tool**: Automated code review assistance
- **Microsoft 365 CoPilot**: Beta trial across the organization
- GenAI used internally for: search log analysis, search intent classification, confidence calibration, social media live events, release notes generation, ticket triage, internal document interaction

### BentoML Partnership (LLM Infrastructure)
- BentoML + OpenLLM for high-performance LLM serving and deployment
- Enables rapid experimentation with open-source models alongside Azure OpenAI APIs
- Key optimization: replacing large models with smaller ones, mini-batching, continuous batching, token streaming
- Results: ~50% decrease in both latency and cost

### Technical AI Stack
- **Foundation Models**: Azure OpenAI APIs (prototyping) + open-source models via BentoML/OpenLLM (production)
- **LLM Serving**: BentoML, OpenLLM
- **Vision**: Computer vision for satellite imagery analysis, Visteon VLM for in-car
- **Key techniques**: LLM fine-tuning, prompt engineering, agentic AI, evaluation systems

---

## 4. Leadership Team

### Management Board
| Name | Role | Background |
|------|------|-----------|
| **Harold Goddijn** | CEO & Co-founder | Founded TomTom in 1991. Still running the company after 30+ years. Also on supervisory board of Coolblue. |
| **Taco Titulaer** | CFO | At TomTom since 2005 in various finance roles; CFO since 2015. Previously at KPN. MSc Business Economics, University of Groningen. |
| **Alain De Taeye** | Management Board Member | Long-standing board member. |

### Senior Leadership Team
| Name | Role | Background |
|------|------|-----------|
| **Corinne Vigreux** | CMO & Co-founder | Co-founded TomTom (originally Palmtop Software). Vice Chair of supervisory board at Just Eat Takeaway. Chair at TechLeap. Board member at Dutch National Opera & Ballet. |
| **Manuela Locarno Ajayi** | SVP Product Engineering | Leads product engineering. Quoted in Visteon partnership announcement. |
| **Michael Harrell** | SVP Maps Engineering | Leads the maps engineering organization. |
| **Mike Schoofs** | Chief Revenue Officer | Leads commercial / sales. |
| **Arne-Christian van der Tang** | CHRO | "We grow leaders at every level, defined by behaviors and principles, rather than by positions and titles." |
| **Benoit Joly** | SVP Global Sales | Leads global sales organization. |
| **Simon Hughes** | General Counsel & CLO | Legal leadership. |
| **Bart Bolger** | VP Human Resources | HR leadership. |

### Key AI & Engineering Leaders
| Name | Role | Background |
|------|------|-----------|
| **Ferenc Szeli** | Head of AI / VP of Engineering | Former Director of Software Engineering at Booking.com (7 years, led 300+ person ML Services & Experimentation Platform team). Former VP Engineering at GeoPhy. MSc IT from Budapest University of Technology. "AI is not new. It's been around for over twenty years." |
| **Bahram Zonooz** | VP of Engineering & Applied Science | PhD, AI assistant professor at Eindhoven University of Technology. ~15 years AI/ML expertise in neuroscience & AI. Former chief AI Scientist at a mapping company. Multiple patents in autonomous driving & map creation. Vision: put "the map at the forefront of a new tech revolution." |
| **Koen Denecker** | VP Platform Engineering | Infrastructure and platform leadership. |
| **Brian Coleman** | VP Product Management | Product strategy. |
| **Gianluca Brugnoli** | VP Design | UX/Design leadership. |

### CTO Situation
Eric Bowman was TomTom's long-standing CTO (rejoined 2019). He left for King (Candy Crush) in March 2024. No public announcement of a direct CTO replacement -- the role may have been restructured or distributed across SVP Product Engineering (Manuela Locarno) and the VPs of Engineering.

### Supervisory Board
- **Derk Haank** (Chairman)
- **Maaike Schipperheijn** (Deputy Chair)
- **Gemma Postlethwaite**
- **Pete Thompson** (joined April 2025)
- **Marili 't Hooft-Bolle**

### Ownership
Founders collectively hold 48.4% of shares (as of July 2025), giving substantial voting influence.

---

## 5. Financials (FY 2025)

| Metric | Value |
|--------|-------|
| **Revenue** | EUR 555M (down from EUR 574M in 2024) |
| **Location Technology Revenue** | EUR 482M |
| **Consumer Revenue** | ~EUR 73M |
| **Gross Margin** | 88% (up from 85% in 2024) |
| **EBITDA** | EUR 20.4M (margin 8.19%) |
| **Free Cash Flow** | EUR 32M inflow (vs EUR 4M outflow in 2024) |
| **Net Cash Position** | EUR 263M |
| **EPS** | -$0.06 (slight loss) |
| **OpEx Reduction** | -9% YoY |
| **Restructuring Charge** | EUR 25M (Q2 2025, from 300-person layoff) |
| **Expected Annual Savings** | EUR 35M from restructuring |
| **Automotive Backlog** | EUR 2.4 billion (record) |

### Stock Performance (TOM2, Euronext Amsterdam)
- Current price: ~EUR 5.18 (as of Feb 2026)
- Dropped 12.64% after Q4/FY2025 results on Feb 4, 2026
- Down 24.49% over past month, but +21.99% over past year
- Analyst targets: EUR 4.50 (low) to EUR 8.00 (high)
- All-time high: EUR 56.33 (Oct 2007); all-time low: EUR 1.75 (Mar 2009)

### 2026 Outlook
Revenue expected to be steady or lower due to customer transitions. However:
- Record automotive backlog (EUR 2.4B) signals mid-term growth
- 88% gross margin shows strong pricing power
- EUR 263M net cash provides financial cushion
- EUR 35M annual savings from restructuring to flow through

---

## 6. Recent News (Last 6 Months)

### Layoffs & Restructuring (June 30, 2025)
- **300 jobs cut** (~6% of workforce) as part of pivot to AI-driven, product-led strategy
- EUR 25M restructuring charge; expected EUR 35M in annual savings
- "Product-led strategy driven by AI" -- consolidating around fewer, higher-impact products
- Phased out portable GPS sales in the US

### Partnerships (Late 2025 - Early 2026)
| Partner | Announcement | Details |
|---------|-------------|---------|
| **Visteon** | Jan 2026 | World's first in-car local AI navigation (on-device VLM, privacy-first) |
| **AECOM** | Feb 2026 | Global traffic data for infrastructure planning |
| **Miovision** | Jan 2026 | Advanced traffic data analytics |
| **Hyundai AutoEver** | 2025 | Multi-year real-time traffic + speed cameras for Hyundai/Kia/Genesis in Europe |
| **CARIAD (VW Group)** | 2025 | Powering automated driving with Lane Model Maps |
| **GeoInt** | Nov 2025 | African telematics and mobility innovation |
| **Uber** | 2025 | Enhanced on-demand travel experiences |
| **smart** | 2025 | All-electric vehicle brand partnership |

### Product Launches (2025-2026)
- Orbis Lane Model Maps (Jan 2026)
- ADAS SDK (Jan 2026)
- TomTom AI Agent (CES 2026)
- Automotive Navigation Application (Sep 2025)
- Area Analytics for precision traffic insights (Jan 2026)
- TomTom Navigation App (smartphone, 2025)
- TomTom MCP Server (alpha, 2025)

### Financial Results (Feb 4, 2026)
- FY2025 revenue EUR 555M (down 3%), stock dropped 12.64%
- But: improved margins, positive free cash flow, record backlog

---

## 7. Tech Stack (Engineering)

### Programming Languages
- **Python** (primary for AI/ML, data pipelines, automation)
- **Java** (core platform services, JVM tools like James agent)
- **Go** (platform engineering, macOS runner controller)

### Cloud & Infrastructure
- **Azure** (primary cloud, AKS, Azure OpenAI APIs)
- **AWS** (EC2, Kinesis, Lambda, SQS, Cognito)
- **Kubernetes** (AKS, multi-tenancy via Capsule, Helm, GitOps)
- **Docker** (containerization)

### Data & ML
- **Databricks** (cloud data platform, Spark jobs)
- **Apache Spark** (big data processing)
- **Apache Airflow** (workflow orchestration, pipeline management)
- **BentoML / OpenLLM** (LLM serving and deployment)
- **Azure OpenAI APIs** (foundation models)
- **GitHub Copilot** (AI-assisted development)

### DevOps & Observability
- **GitHub Actions** (CI/CD)
- **OpenTelemetry** (vendor-neutral telemetry)
- **Prometheus** (metrics)
- **Grafana + Loki** (dashboards, log aggregation)
- **Jaeger/Tempo** (distributed tracing)
- **PagerDuty** (alerting)
- **Scalyr** (log management)
- Infrastructure as Code (IaC)

### Open-Source Projects (GitHub: tomtom-international)
| Repository | Description |
|-----------|-------------|
| **tomtom-mcp** | MCP server for AI agents to access TomTom data |
| **OpenLR** | Map-agnostic dynamic location referencing |
| **Digital Cockpit** | In-car digital cockpit platform |
| **James** | Java agent for JVM runtime analysis |
| **AsciiDoxy** | API documentation from Doxygen XML to AsciiDoc |
| **Vault Prometheus Exporter** | HashiCorp Vault monitoring |
| **Navkit 2 Build Infrastructure** | Build system for navigation platform |

### Engineering Blog Highlights (engineering.tomtom.com)
- "Generative AI Journey at TomTom" -- Hub-and-spoke model, Chatty, GitHub Copilot adoption
- "TomTom and BentoML are advancing location-based AI together" -- LLM serving, 50% cost reduction
- "Scaling macOS GitHub Actions Runners" -- Custom control plane, etcd, 83% queue time reduction
- "Boosting Developer Productivity with GitHub Copilot" -- 85% productivity improvement
- "Kubernetes multi-tenancy with Capsule" -- Platform engineering, DevOps
- "OpenTelemetry - Simplifying Observability" -- Monitoring stack
- "Triggering dynamic Spark tasks on Databricks with Apache Airflow" -- Data pipeline orchestration
- "Integrating TomTom APIs into the GPT Plugin Ecosystem" -- ChatGPT plugin development

---

## 8. Leadership Foundation (CRITICAL for Interview)

TomTom's Leadership Foundation is their cultural framework AND their candidate evaluation criteria. It consists of three layers:

### Four Leadership Behaviors
| Behavior | Definition | Example |
|----------|-----------|---------|
| **Ownership** | Seeing an opportunity and taking the initiative to make it happen | Encounter a blocker on a map update project? Gather colleagues, lead the meeting, put the problem to paper. |
| **Accountability** | Being responsible for the result of what you've taken ownership over | Test the process at every step. Learn from failures rather than viewing them as permanent setbacks. |
| **Influence** | Motivating people to reach their highest levels | When a team has to start from scratch, remind everyone of previous successes and encourage commitment. |
| **Multiplying** | Using your expertise to amplify the capabilities of those around you | Share knowledge, tell teammates where they slipped up and how to prevent it. Pass on expertise to make others experts. |

### Five Leadership Principles
| Principle | Definition |
|-----------|-----------|
| **Start with Yes** | Have a positive attitude and listen to new ideas before discussing possibilities. |
| **Impress the Customer** | Take a solution and ensure it reaches the customer with maximum impact. |
| **Simplify the Complex** | Make anything you deliver easy to use and provide feedback on. Hide complexity from end users. |
| **Better Every Day** | Develop skills together to ensure the team is optimized for effective decision-making. Continuous learning and knowledge sharing. |
| **Disagree and Commit** | Ensure mutual respect, hear each other out, and follow through on team decisions even if you personally disagreed. |

### Six Values
The exact six values are not publicly enumerated in detail. They are described as "our DNA" and "build up the TomTom experience." They are integrated into daily operations and decision-making, revolving around integrity, passion, and drive for excellence.

### How It's Used in Hiring
- **Leadership Foundation is explicitly evaluated in interviews** -- TomTom says "familiarize yourself with the Leadership Foundation, as it will help you stand out"
- Your interview Step 1 includes "2 Leadership Behaviors" evaluated in STARR format
- The panel interviews (Step 2) all include "+ Leadership" components
- STARR = Situation, Task, Action, Result, Reflection
- Eric Bowman (former CTO): "The most effective way to look at leadership is not that it is some authority granted to you, but that it is a complex set of behaviors that people can learn."
- Arne-Christian van der Tang (CHRO): "We grow leaders at every level, defined by behaviors and principles, rather than by positions and titles."

### Practical Tips for Your Interview
1. Prepare STARR stories that demonstrate **Ownership** and **Accountability** (most likely behaviors to be tested for an engineering role)
2. Show how you **Multiply** -- sharing knowledge, helping teammates improve
3. Reference "Start with Yes" when discussing collaboration scenarios
4. "Simplify the Complex" maps perfectly to AI/ML -- making complex AI accessible to end users
5. "Disagree and Commit" -- have a story about disagreeing but committing to team direction

---

## 9. Culture & Glassdoor

### Overall Rating: 3.8/5 (Amsterdam), 3.9/5 (Global)
- 79% would recommend to a friend (Amsterdam)
- Work-Life Balance: 4.1/5
- Culture & Values: 4.0/5
- Career Opportunities: 3.6/5
- Compensation & Benefits: 3.4/5

### Top Pros (from 1,281 reviews)
1. **Work-life balance** (mentioned in 135 reviews) -- healthy respect for personal time
2. **Great colleagues** (mentioned in 127 reviews) -- supportive, collaborative culture
3. **Flexibility** -- significant autonomy in how work is managed
4. **Learning opportunities** -- leadership programs, global events, growth focus
5. **Office location** -- Amsterdam HQ near Central Station

### Top Cons
1. **Frequent reorganizations** -- "every half year a new top priority project starts, forcing employees to drop something else"
2. **Low salary / hard promotions** (mentioned in 51 reviews) -- below market for Amsterdam tech
3. **Management quality varies** -- "some managers are good, some are not" (29 reviews)
4. **Slow decision-making** -- internal politics, hierarchical layers
5. **Layoff concerns** -- "brutal for folks on visas" (13 reviews -- RELEVANT for you on Zoekjaar)
6. **Outdated practices** -- some waterfall approach to product development still in place

### Key Insight for Interview
The culture is collaborative and flexible, but salary negotiation and career growth require proactive effort. The recent restructuring (300 jobs) may have improved focus but also created uncertainty. Frame your questions around team stability and the AI team's roadmap to show you're thoughtful about joining post-restructuring.

---

## 10. Competitive Landscape

### Market Position
TomTom ranks **#2 globally** in location platform effectiveness (Counterpoint Research), behind HERE and ahead of Google Maps and Mapbox.

### Key Competitors
| Competitor | Strengths | TomTom Advantage |
|-----------|-----------|-----------------|
| **HERE Technologies** | #1 overall, dominant in automotive HD maps, 200+ countries, owned by German automakers (Audi, BMW, Daimler) | More agile/innovative AI strategy, open-source approach with Orbis Maps, cost-effective Lane Model Maps vs traditional HD maps |
| **Google Maps** | Billions of users, best global coverage, massive POI database | Privacy (partners won't share data with Google as a potential competitor), automotive-grade quality, no conflict of interest |
| **Mapbox** | Developer-friendly, highly customizable, lower cost | Enterprise-grade quality, automotive OEM relationships, comprehensive traffic data, deeper vertical integration |
| **ESRI** | GIS market leader, enterprise analytics | Different market focus -- TomTom provides mapping data, ESRI builds analysis tools (they actually partner: Microsoft + Esri + TomTom) |

### TomTom's Differentiators
1. **Open approach**: Orbis Maps combines proprietary + open-source (Overture Maps Foundation, OSM) -- no single mapmaker could achieve this alone
2. **Automotive DNA**: 30+ years in automotive navigation, trusted by VW/CARIAD, Hyundai, Stellantis, Mercedes
3. **AI-powered map factory**: Scalable lane-level maps at fraction of traditional HD map cost
4. **Privacy advantage**: Unlike Google, no conflict of interest with partners' data
5. **EUR 2.4B automotive backlog**: Locked-in revenue from OEM contracts

---

## 11. Office & Work Arrangements

### Amsterdam HQ
- **Address**: De Ruijterkade 154, Amsterdam 1011 AC
- **Location**: Directly opposite Amsterdam Centraal Station -- exceptional public transit access
- **Facilities**: Modern open-plan offices with flexible seating, quiet zones, collaboration spaces, conference rooms, advanced technology infrastructure, bike storage, parking
- **Team Size**: HQ houses shared services and engineering teams

### Hybrid Policy
- The job posting mentions **"Hybrid" in Amsterdam** (2 days in office per week based on JD you noted)
- Employee reviews confirm strong flexibility: "a lot of flexibility in how work is done"
- Remote work culture well-established post-COVID

### Global Engineering Presence
Key engineering offices beyond Amsterdam: Ghent (Belgium), Leipzig (Germany), Lodz (Poland), Eindhoven (Netherlands), Pune (India), Berlin (Germany)

---

## 12. Interview-Relevant Talking Points

### Why TomTom Now?
- Pivoting from legacy mapping to AI-first -- you'd be joining at the inflection point
- The AI Agent, MCP Server, and Visteon partnership show real product momentum in GenAI
- EUR 2.4B automotive backlog provides revenue stability while AI strategy matures
- Post-restructuring: leaner, more focused on product-led strategy

### Connection to Your Background
- **LLM fine-tuning + prompt engineering** = direct match to AI model improvement responsibility
- **Evaluation systems** = your thesis work (5 UQ methods, 150+ training runs) maps perfectly
- **CI/CD + MLOps** = your Docker/Airflow/GitHub Actions experience
- **Python-first** = your strongest language
- **Production AI** = Job Hunter project demonstrates end-to-end AI product building

### Questions to Ask
1. "How is the AI team structured after the June 2025 restructuring? What's the current team size and composition?"
2. "Which TomTom products does the AI team's work feed into -- is it primarily the AI Agent, or also map factory/LLM infrastructure?"
3. "I read about TomTom's BentoML partnership for LLM serving. What's the current state of self-hosted vs Azure OpenAI models in production?"
4. "How does the evaluation system you're building relate to the map quality validation pipeline?"
5. "What does 'client integration' look like concretely for the AI team -- is this internal teams or external OEM partners?"

---

## Sources

### TomTom Official
- [TomTom Company Page](https://www.tomtom.com/company/)
- [TomTom Boards & Committees](https://www.tomtom.com/company/boards-and-committees/)
- [TomTom Careers - How We Hire](https://www.tomtom.com/careers/how-we-hire/)
- [TomTom Newsroom - Product Focus](https://www.tomtom.com/newsroom/product-focus/)
- [TomTom Investor Relations](https://corporate.tomtom.com/investors/overview/)
- [TomTom Engineering Blog](https://engineering.tomtom.com/)
- [TomTom Developer Portal](https://developer.tomtom.com/)
- [TomTom GitHub (tomtom-international)](https://github.com/tomtom-international)

### Leadership Foundation
- [Understanding TomTom's Five Leadership Principles](https://www.tomtom.com/newsroom/life-at-tomtom/understanding-tomtom-s-five-leadership-principles/)
- [Encouraging Leadership at Every Level](https://www.tomtom.com/newsroom/life-at-tomtom/encouraging-leadership-at-every-level/)
- [How TomTom'ers Take the Lead in Their Everyday Role](https://www.tomtom.com/newsroom/life-at-tomtom/how-tomtomers-take-the-lead-in-their-everyday-role/)

### AI Strategy
- [Bahram Zonooz: Leading TomTom's AI Journey](https://www.tomtom.com/newsroom/life-at-tomtom/bahram-zonooz-taking-the-lead-on-tomtom-s-journey-in-ai/)
- [TomTom MCP Server](https://www.tomtom.com/newsroom/explainers-and-insights/introducing-tomtom-model-context-protocol-server/)
- [Making Maps with AI and ML](https://www.tomtom.com/newsroom/behind-the-map/making-maps-at-scale-with-ai/)
- [Delivering Real Customer Value with AI (Ferenc Szeli)](https://www.tomtom.com/newsroom/behind-the-map/upskilling-the-workforce-with-ai-to-benefit-customers/)
- [Generative AI Journey at TomTom (Engineering Blog)](https://engineering.tomtom.com/GenAI-journey/)
- [TomTom and BentoML Partnership](https://engineering.tomtom.com/ai-partnership-bentoml/)

### News & Financials
- [300 Job Cuts in AI-Driven Restructuring](https://bits-chips.com/article/tomtom-navigates-300-job-cuts-in-ai-driven-restructuring/)
- [Visteon + TomTom: World's First In-Car Local AI Navigation](https://www.prnewswire.com/news-releases/visteon-and-tomtom-launch-worlds-first-in-car-local-ai-navigation-system-302652671.html)
- [TomTom Q4 2025 Results](https://www.investing.com/news/company-news/tomtom-q4-2025-slides-revenue-drops-3-stock-falls-despite-growing-backlog-93CH-4484696)
- [CES 2026 Demos](https://www.tomtom.com/newsroom/product-focus/tomtom-ces-2026-product-demos-what-you-can-expect-to-see-in-las-vegas/)
- [Orbis Lane Model Maps Launch](https://www.globenewswire.com/news-release/2026/01/02/3212048/0/en/TomTom-launches-Orbis-Lane-Model-Maps-for-fresh-lane-level-precision-at-scale.html)

### Reviews & Market Position
- [TomTom Glassdoor Reviews (Amsterdam)](https://www.glassdoor.com/Reviews/TomTom-Amsterdam-Reviews-EI_IE38808.0,6_IL.7,16_IM1112.htm)
- [Counterpoint Research: Location Platform Rankings](https://counterpointresearch.com/en/insights/maintains-location-platform-leadership-tomtom-surpasses-google-take-second-position-mapbox-moves-fourth)

### Eric Bowman (Former CTO)
- [The Leadership Lab Podcast: CTO at TomTom](https://www.deeprec.ai/blog/the-leadership-lab-podcast-cto-at-tomtom-eric-bowman)
- [King Appoints Eric Bowman as CTO](https://www.pocketgamer.biz/king-appoints-ex-tomtom-and-zalando-exec-eric-bowman-as-cto/)
