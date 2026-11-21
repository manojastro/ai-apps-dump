# A5 — Interview Intelligence — August 2026

**Profile this dossier serves:** Manoj Kumar, 8.5 YOE Service Desk Lead / IT Ops at Cognizant, current CTC ~11 LPA, targeting GenAI / Agentic / LLM / AIOps / AI Automation roles in India. Not a Java/SQL-first developer. Not an Applied Scientist.

**Scope:** Real interview processes and questions for India AI / GenAI / MLOps / LLMOps / AIOps / AI automation roles, with emphasis on 6–12 years experience where evidence exists. **Zero fabricated questions.** If a question is from a prep blog without a named candidate review, it is labeled **SECONDARY**.

**Recency:** Prefer 2024–2026. Older items are marked **OLDER**.

---

## Method and source quality ranking

Research date: 23 August 2026. Sources were retrieved via public web search and page fetches. Glassdoor.co.in and AmbitionBox HTML were frequently Cloudflare-blocked; those items are cited from **search-indexed snippets of the original review pages** and, where possible, from third-party mirrors (Taro/JoinTaro copies Glassdoor-style reviews). Reddit JSON endpoints were blocked; Reddit items are cited from search-indexed snippets of `r/developersIndia`, `r/dataengineersindia`, and related threads, plus an X post that quotes a developersIndia-style career switch.

### Evidence labels used throughout

| Label | Meaning |
| --- | --- |
| **VERIFIED FACT** | A named candidate review (Glassdoor, AmbitionBox, GeeksforGeeks, LinkedIn post by a named person, LeetCode Discuss, Taro mirror of a dated review) that states a specific question or round. |
| **COMMUNITY EXPERIENCE** | Anonymous but specific candidate narrative (Reddit, X, unnamed Glassdoor) that describes process shape or question *themes* with enough detail to be useful, not a question bank. |
| **SECONDARY BLOG** | Interview-prep article, coaching site, DataCamp, Dataford, CloudSoft, Learnbay, IGotAnOffer, Analytics Vidhya Q&A lists. **Not treated as “asked at Company X” unless a named review corroborates.** |

### Source quality ranking (highest first)

1. **Named first-person reviews with dates and role titles:** LinkedIn posts (Shanmukha Sai Srinivas Nunna on TCS; Arunabha Sarkar on Infosys), GeeksforGeeks campus writeups, LeetCode Discuss Adobe 2026, Taro mirrors of Glassdoor GenAI reviews, Glassdoor snippets that quote the actual Question 1 field.
2. **Anonymous first-person Glassdoor / AmbitionBox with company, role, month/year, and quoted questions.**
3. **Community synthesis with corroboration:** Arsh Goyal X summary of a services-to-GenAI switch; `r/developersIndia` process comments that match Glassdoor independently.
4. **Prep blogs and “50 questions for 2026” lists.** Used only to describe *what the market believes interviewers ask*, never as proof a company asked that exact question.

### What this dossier is *not*

- Not a complete census of every India GenAI loop. Sample sizes per company are often **n = 1 to 6** public reviews.
- Not 8.5-YOE Service Desk → GenAI transcripts. **No named Service Desk / ITSM lead interview writeup for a GenAI IC role was found.** Transition advice in the last section is **INFERENCE**.
- Not a substitute for a mock with a recent interviewer at the target team.

---

## Process maps by company type (services / GCC / product / startup)

### A. Indian IT services and Big 4 consulting (TCS, Infosys, Wipro, Cognizant, Accenture, Capgemini, IBM, Deloitte, GlobalLogic)

**Typical shape (2024–2026 candidate reports):** 1 recruiter/HR screen → 1–2 technical rounds (sometimes labeled L1/L2) → managerial / “partner” → HR CTC/notice. Deloitte and some Accenture/Capgemini loops add a **client round**. Duration: ~1–4 weeks when moving; Deloitte Bengaluru April 2025 reported **4 elimination rounds including client**.

| Company | Role (as labeled) | Date | Rounds | Coding? | GenAI depth | Source |
| --- | --- | --- | --- | --- | --- | --- |
| **TCS** | GenAI Developer / Consultant (R&D-focused) | ~Jun 2025 (LinkedIn “1y” as of Aug 2026 ≈ Jun 2025) | Phone screen (Naukri) → Senior Engineer deep-dive → Senior Manager | Python/OOP theory, **no LeetCode-hard DSA reported** | Vector DB, RAG flow, similarity, LangChain agents/tools/memory, BLEU/ROUGE/perplexity, FT vs RAG, hallucination | VERIFIED FACT — Shanmukha Sai Srinivas Nunna, [LinkedIn](https://www.linkedin.com/posts/shanmuknunna_genai-tcs-interviewexperience-activity-7336343348636545025-1tG7) |
| **Infosys** | Gen AI Engineer | Recruiter-sourced, undated on Glassdoor (indexed Jun 2025 page) | **1 technical + HR** (notice period + salary) | Not specified in this review | “Mostly questions were related to my project and the RAG.” | VERIFIED FACT — Glassdoor Infosys Gen AI Engineer |
| **Infosys** | Gen AI Engineer | Bengaluru, Oct 2024 (posted 10 Nov 2024) | SHL OA → in-person technical → HR (~2 weeks) | OA on SHL; tech round was **classical ML algorithms**, not RAG | Clustering, Linear Regression, K-means, KNN | VERIFIED FACT — Glassdoor |
| **Infosys** | Gen AI Engineer | Pune, Aug 2026 | Not fully enumerated | “coding question were easy”; Python `*args`/`**kwargs` | Types of prompting, GenAI vs Agentic AI, fine-tuning, hallucination | VERIFIED FACT — Glassdoor Infosys Gen AI Engineer (updated 10 Aug 2026) |
| **Infosys** | GenAI Developer (friend’s interview, posted by Arunabha Sarkar) | ~Feb 2026 (LinkedIn “6mo”) | L1 Applied AI + backend → L2 consulting use-cases | Implementation depth, not DSA | Token limits, rate limits, caching, streaming, RFP design, data leak, cost, ROI | COMMUNITY EXPERIENCE (second-hand named poster) — [LinkedIn](https://www.linkedin.com/posts/arunabha-sarkar-alex_infosysinterview-genaiinterview-llmengineering-activity-7427924490401103872-e3y0) |
| **Infosys** | GenAI Engineer (AmbitionBox role page, updated 10 Aug 2026) | Undated individual Qs | Mixed | One Q: “Advanced dsa more than 6 questions”; another: transformer + cosine + projects | Transformer architecture, cosine similarity, project depth | VERIFIED FACT (AmbitionBox Q list, unnamed) |
| **Deloitte** | Gen AI Engineer, India | Dec 2024 | **2 rounds** | Easy Python (even/odd, prime) | RAG, PDFs with images, agents, chunking, SCD, duplicates | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-india-december-1-2024-no-offer-negative-6302fac4/) mirroring Glassdoor |
| **Deloitte** | Gen AI Engineer, Bengaluru | Jun 2025 | **1 tech hour** (rescheduled) | Two basic Python questions | 45 min GenAI: RAG vs Agent, shared memory, design an agent, embeddings, “very big RAG” | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-bengaluru-karnataka-june-1-2025-no-offer-positive-5eb74f34/) |
| **Deloitte** | Gen AI Engineer, Bengaluru | Apr 2025 | **4 rounds: 2 tech + partner + client**; all elimination | Not specified | “RAG and agentic framework and its application.” Cleared 3, **failed client round** | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-bengaluru-karnataka-april-1-2025-no-offer-neutral-7ea08313/) |
| **Deloitte** | Gen AI Engineer, India | Dec 2024 (second review) | First round Python + NLP + GenAI + DL + ML + RAG + LLM | Coding on Python | “What is one-bit quantization?” | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-india-december-1-2024-no-offer-negative-2c45121c/) |
| **Capgemini** | GenAI engineer | Gurgaon, Dec 2025 | Screening + technical | Not specified | **Multi-tenant RAG**: cannot use another client’s documents | VERIFIED FACT — Glassdoor Capgemini RVW101720117 |
| **Capgemini** | GenAI AIML | 21 Jul 2025 | Not specified | Not specified | “What are the two most important components of RAG and how will you evaluate a RAG model performance.” | VERIFIED FACT — Glassdoor India genai engineer questions |
| **Capgemini** | GenAI engineer | 2 Sep 2025 | Not specified | Not specified | Transformer architecture, self-attention | VERIFIED FACT — same index |
| **Capgemini** | Gen AI Engineer | Hyderabad, 29 Mar 2025 | L1 basics | Not specified | Prompting, various LLMs, vector DBs, then NLP projects | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/capgemini/experiences/gen-ai-engineer-hyderabad-march-29-2025-declined-offer-positive-ed8bdb1e/) |
| **Capgemini** | Gen AI Engineer | Mumbai, 19 Mar 2025 | Not specified | Python language theory | Key features, interpreted, data types, list/tuple/set/dict, memory management | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/capgemini/experiences/gen-ai-engineer-mumbai-march-19-2025-accepted-offer-positive-e201b3f2/) |
| **Capgemini** | Gen AI Engineer | India, 23 Sep 2025 | L2 | Easy Python; interviewer insisted on *her* solution | **No project questions.** Candidate: interviewer “never worked on Gen AI.” | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/capgemini/experiences/gen-ai-engineer-india-september-23-2025-no-offer-negative-d93e7716/) |
| **Capgemini** | (undated Glassdoor snippet) | Face-to-face L1+L2 | L1 Pandas, data cleaning, basic RAG, projects; L2 went well | — | **Rejected because YOE did not match JD** | VERIFIED FACT — Glassdoor |
| **Accenture** | Gen AI developer | Glassdoor QTN_8348946 | Not specified | Not specified | Agentic AI vs AI agents, retrievers in RAG, similarity for semantic search, how LLM performance is checked | VERIFIED FACT — Glassdoor question page |
| **Accenture** | AI ML Engineer | Updated 1 Aug 2026 (India) | 2 stages: online then interview | Online | LangChain, prompting techniques, RAG, retrieval | VERIFIED FACT — Glassdoor India |
| **Accenture** | Analyst | Glassdoor QTN_8719740 | — | — | “Question on Gen AI, RAG pipeline was asked. Follow up questions on projects.” | VERIFIED FACT |
| **Accenture** | (undated) | Glassdoor QTN_7354214 | — | — | RAG full form, Responsible AI, estimation | VERIFIED FACT |
| **Cognizant** | Generative AI developer | Austin TX, Nov 2023 (**OLDER, US**) | Short Q&A | None reported | “What is the meaning of RAG?” Interviewer allegedly said increasing temperature *decreases* randomness | VERIFIED FACT — Glassdoor 3 Jan 2024 |
| **Cognizant** | Gen AI Engineer | 31 Mar 2026 | 2 rounds | Python coding | R1: Agentic AI create/orchestrate, RAG pipeline, evaluation, metrics. R2: ML, DL, NLP, GenAI, Cloud, scenarios | VERIFIED FACT — Glassdoor |
| **Cognizant** | Gen AI Engineer | Amsterdam, Dec 2024 | Recruiter + leadership + technical | Analytic problems + presentation | “What are the biggest problem to tackle with generative AI implementation for businesses” | VERIFIED FACT — Glassdoor (not India) |
| **Wipro** | Gen AI Engineer | Posted 25 Nov 2024 | 2 technical, Phase 2 Hinjawadi | Not specified | “RAG Pipeline What are difficulty you faced” | VERIFIED FACT — Glassdoor |
| **Wipro** | Gen AI Engineer | Pune, Jul 2024 (posted 7 Aug 2024) | ~4 weeks | Python | Fine-tuning, RAG, LLM, cloud, LangChain, NLP from scratch, MLOps, deployment | VERIFIED FACT — Glassdoor |
| **Wipro** | AI/ML Engineer | Jun 2025 | 2 Wipro tech + **harder client round** | Second largest element in a list | How RAG works, why vector DB, **what chunk size you used and why**, how BERT works and limitations | VERIFIED FACT — Glassdoor |
| **Wipro** | Software Engineer (AI-based interview) | ~Aug 2026 | 1 round “fully Ai based interview” | — | “Explain RAG and what is chunking” | VERIFIED FACT — Glassdoor (NL locale snippet) |
| **IBM** | AI Engineer | Bengaluru, Aug 2025 | Resume-based | One easy coding Q | RNN, Transfer Learning, RAG | VERIFIED FACT — Glassdoor |
| **IBM** | AI Engineer | Bengaluru, Feb 2025 | HackerRank (coding + 2 MySQL) → Python/ML/DL → senior manager/architect | OA + easy coding | RAG, LLMs, DL, performance metrics | VERIFIED FACT — [Taro](https://www.jointaro.com/interviews/companies/ibm/experiences/ai-engineer-bengaluru-february-1-2025-no-offer-positive-c881d31a/) |
| **IBM** | AI Engineer | Pune, Jun 2026 | Assignment (coding + SQL) then office TR + MR | HackerRank gate | “How would you integrate a machine learning model into an existing enterprise system?” | VERIFIED FACT — Glassdoor |
| **IBM** | SDE campus | Sep 2025, GFG | OA 2 easy coding → TR → MR | String compression, LC 198 | **“What is RAG?” on resume** plus C++/OOP/puzzles | VERIFIED FACT — [GFG](https://www.geeksforgeeks.org/interview-experiences/ibm-india-interview-experience-for-software-developer-on-campus/) |
| **GlobalLogic** | **GenAI engineer** | Hyderabad, 7 Sep 2025 | OA → tech → manager → HR | **DSA + SQL + CS fundamentals** | Projects on resume | VERIFIED FACT — Glassdoor |
| **GlobalLogic** | GenAI engineer | Nagpur, 2 Sep 2025 | OA: **2 DSA** (arrays, strings, hashmaps, DP, recursion, BS, greedy, graphs) → live coding medium DSA + OOP/DBMS/OS | Heavy DSA | Process description does **not** mention RAG | VERIFIED FACT — Glassdoor |

**Services process invariants from the evidence**

- **HR almost always asks notice period and salary.** Infosys Glassdoor: “HR round that asked me about my notice period as well as my salary expectations.”
- **Client/partner rounds exist and eliminate.** Deloitte Apr 2025: cleared three internal rounds, failed client. Wipro Jun 2025: “client round which was much more difficult… Indepth knowledge of GenAI was tested.”
- **Interviewer quality is uneven.** Capgemini Sep 2025 L2: interviewer eating, handling a baby, “never worked on Gen AI,” no project questions. Cognizant US 2023: interviewer asserted wrong temperature fact.
- **Title “GenAI” does not guarantee a GenAI loop.** Infosys Bengaluru Oct 2024 asked K-means/KNN. GlobalLogic “GenAI engineer” OA was generic SDE DSA. Capgemini Mumbai Mar 2025 offer loop was Python language 101.

### B. Analytics / AI boutiques (Tiger Analytics, Fractal)

These are closer to **applied ML + GenAI engineering** than to services L1 quizzes. More rounds, more live Python, more RAG depth, sometimes SQL.

| Company | Role | Date | Process | Coding | GenAI | Source |
| --- | --- | --- | --- | --- | --- | --- |
| **Tiger Analytics** | AI Engineer | Hyderabad, Nov 2025 (posted 1 Dec 2025) | 3 technical, 2 weeks | Not the focus of this review | Past RAG: embeddings, data updates, chatbot; preprocessing, **chunking**, vector DBs, retrieval, evaluation, production troubleshooting | VERIFIED FACT — Glassdoor |
| **Tiger Analytics** | AI Engineer | Hyderabad, 16 Jan 2026 | 1st DSA, 2nd ML/DL | Factorial; **3-sum** | RAG architecture, Agentic AI, deployment, AWS, Azure, rollback | VERIFIED FACT — Glassdoor |
| **Tiger Analytics** | AI Engineer | (undated on same page) | — | “coding questions asked were not relevant for the role of AI. **No questions were asked about AI**” | Transformers architecture maths (another review) | VERIFIED FACT — Glassdoor |
| **Tiger Analytics** | Senior AI Engineer | Bengaluru, Jun 2025 (posted 6 Jul 2025) | **4 rounds**, first 3 technical, 3 weeks, recruiter | — | DL basics through RAG, fine-tuning, system design, API, Docker, Kubernetes; business use case | VERIFIED FACT — Glassdoor |
| **Tiger Analytics** | Senior AI Engineer | (CoderPad review) | Live coding | Sum of digits until single digit; SQL second-highest salary by dept | — | VERIFIED FACT — Glassdoor |
| **Fractal** | Gen AI Engineer | Interviewed Sep 2025, posted 16 Mar 2026; **process 6 months** | Python live coding 1–1.5h → pure technical → fitment → HR | **2 Python live coding** | Transfer, Agentic AI, LangGraph, project detail | VERIFIED FACT — Glassdoor |
| **Fractal** | Sr Data Scientist Generative AI | Noida, Oct 2025 (posted 3 Nov 2025) | 3 rounds | Printing series patterns; list/dict comprehension | R1: ML preprocess/eval, DL optimizers/GD, RAG/LLMs. R2: sentence transformers, benchmarking, RAG, **RAGAs, DSPy**, transformer, embeddings, positional encoding | VERIFIED FACT — Glassdoor |
| **Fractal** | Senior Data Scientist | New Delhi, Sep 2025 (posted 14 Oct 2025) | 2 tech + HR, **1 week** | Python data manipulation | R1: agentic frameworks, RAG, retrievers. R2: Agent implementations, **MCPs**, evaluation. Q: **Difference between RAG and Agentic RAG**; how to evaluate/improve a deployed model/agent | VERIFIED FACT — Glassdoor |
| **Fractal** | Data Scientist (GenAI profile) | Bengaluru, Jul 2026 | HackerEarth with interviewer | Easy–medium coding | LangGraph, LangChain, vector DB, pandas, “think about a GenAI usecase” | VERIFIED FACT — Glassdoor |
| **Fractal** | Data Scientist | Feb 2025 | OA: ML MCQ, **2 LC Medium**, Git | LeetCode | Separate review: “fine tune and rag difference” | VERIFIED FACT — Glassdoor |

**r/dataengineersindia** snippet (search-indexed, Reddit full page blocked): “Tiger Analytics AI Engineer Interview — They will touch up on your recently worked project, types of rag, chunking types, deployment strategies and 2 python questions.” **COMMUNITY EXPERIENCE.** Matches Glassdoor Nov 2025.

### C. Product / GCC (Microsoft, Amazon, Adobe, ServiceNow) — contrast with services “GenAI”

These loops **are not the same job**. Applied Scientist / MLE / Senior Backend-GenAI at product companies combine **DSA or from-scratch ML coding** with transformer internals. A services GenAI engineer who can recite LangChain is under-prepared.

| Company | Role | Date | Process | DSA / coding | GenAI | Source |
| --- | --- | --- | --- | --- | --- | --- |
| **Amazon** | Applied Scientist | Bengaluru, Nov 2024 | Recruiter + **5 rounds**: 2 tech, 1 system design, 1 behavioural, 1 LeetCode | Yes | Transformers; “If you have a task where order of words/tokens didn’t matter, how would you train for it?” | VERIFIED FACT — Glassdoor |
| **Amazon** | Applied Scientist | Bangalore Rural, 22 Jan 2026 | — | — | “Describe what would happen if we change the loss function… Cross entropy to MSE”; “Explain what would happen if **Wq = Wk = Wv** in a transformer” | VERIFIED FACT — Glassdoor |
| **Amazon** | Applied Scientist II | Hyderabad, 7 Apr 2026 | HR + 4 tech (coding+depth+breadth) + project depth + DS + system design | Yes | Pipeline for translating multimodal objects | VERIFIED FACT — Glassdoor |
| **Amazon** | Applied Scientist II | (US, May 2026) | Phone + 4 loop: ML breadth, ML depth, system design, **agentic product thinking**, behavioural | — | “Design an agentic recommendation system.” | VERIFIED FACT — Glassdoor |
| **Amazon** | Applied Scientist | (undated Glassdoor) | Onsite coding **not LC** | Write cosine similarity on sparse vectors; top-k | — | VERIFIED FACT — Glassdoor |
| **Microsoft** | Applied Scientist | Bengaluru | 3 rounds | Easy–medium coding; write logistic-regression loss in NumPy | Basic ML; LLM questions; HR team skills | VERIFIED FACT — Glassdoor |
| **Microsoft** | Applied Scientist II | Bengaluru, 18 Dec 2025 | Screening (NLP/ML basics) → technical → coding | Yes | PCA, regression, logistic, bias-variance, regularization | VERIFIED FACT — Glassdoor |
| **Microsoft** | Applied Scientist II | 30 Jul 2026 | Coding → ML theory → ML theory | Yes | “Space complexity of various parts of the Transformer.” | VERIFIED FACT — Glassdoor |
| **Microsoft** | Applied Scientist II | Redmond, Jan 2026 | HM + 4 | Coding | “Transformer architecture and **implement self-attention from scratch**” | VERIFIED FACT — Glassdoor |
| **Microsoft** | Applied Scientist | (HM screen) | — | — | “Design a RAG system that can generate slides based on user's prompt”; “Design chatbot for advertisement org”; hallucinations and RAG | VERIFIED FACT — Glassdoor |
| **Adobe** | Senior Backend Engineer – Python / Gen AI | Noida, 2026 (LeetCode Discuss) | 5 rounds planned; first 3 documented | **DSA + system design + RAG design** | Design document Q&A; attention in transformers; **how do you evaluate RAG in production** (RAGAS + LLM-as-judge + latency/cost) | VERIFIED FACT — [LeetCode Discuss](https://leetcode.com/discuss/post/8317558/adobe-interview-experience-senior-backen-7zp1/) |
| **Adobe** | Machine Learning Engineer | Bengaluru, Apr 2026 (posted 2 Aug 2026) | 2 rounds | R1: ML rapid-fire + 1 simple DSA pseudocode. R2: **3 LC medium** (did 2) | Types of attention; BERT vs GPT for classification; summarisation metrics **without ground truth**; ROUGE/BLEU without GT | VERIFIED FACT — Glassdoor |
| **ServiceNow** | GenAI Architect | 16 May 2025 | Not fully described | Not reported | “Did I have to deal with repercussions of deploying AI, like to job, training or org?”; “What metrics have I used to assess GenAI impact”; security/data privacy project | VERIFIED FACT — Glassdoor |

**Google India GenAI IC loops:** No 2024–2026 India *Generative AI Engineer* first-person question list was found. IGotAnOffer cites “Design a small language learning model that could run on a phone while making sure it’s polite” as a **Google GenAI system design** example compiled from Glassdoor/Reddit — **SECONDARY BLOG** unless corroborated. Do not treat as verified Google India 2025.

### D. Other product / SaaS / offshore product (Freshworks, Zoho, Thoughtworks, Money Forward, Techolution, Publicis Sapient)

| Company | Evidence | Label |
| --- | --- | --- |
| **Zoho** | 2025–2026 public interviews remain **aptitude + 5–6 coding/LLD rounds**. No GenAI-titled interview question bank found. | Process VERIFIED for SDE; **GenAI-specific: insufficient evidence** |
| **Freshworks** | Staff Engineer Data Scientist Anshuman Guha describes production RAG/Freddy Copilot in a 2025 featured interview — **job content, not interview questions**. Freshworks Chennai Glassdoor 2025 loops still JS/DSA/SQL. | **Insufficient reliable interview Qs for GenAI IC** |
| **Thoughtworks India** | Careers page: candidates **may use GenAI** in applications if answers remain authentic; AI does not reject candidates. InterviewQuery 2026 AI Engineer guide: one report of “design a production RAG system” then evals/guardrails — **SECONDARY** (InterviewQuery) unless a named TW India writeup is found. Named LinkedIn “5–6 rounds including 2 online tests” is for Backend & AI but not a question list. | Process policy VERIFIED; question bank thin |
| **Publicis Sapient** | No 2024–2026 India *GenAI Engineer* question list found. Frontend/Java/AWS loops dominate public posts. Manager Data Science Medium (Mar 2026) exists but the page was blocked here. | **Insufficient reliable evidence** |
| **Money Forward** | Generative AI Engineer, **Chennai, Sep 2025**, offer accepted: **3 technical + HR**. R1: projects, Python, DS, GenAI, **2 coding (strings, lists, dicts, optimized)**. R2: Japan panel, agentic project on resume. R3: techno-managerial, projects + **LLMOps**. Q: Multi-agentic systems, RAG, LLM evaluation; ML train/preprocess. | VERIFIED FACT — Glassdoor |
| **Techolution** | GenAI Engineer: 3 interviews + coding assessment (OOP project). Dec 2024: “Lemonade change questions from leetcode and a basic array manipulation.” Nov 2024: “They asked about how transformers work.” | VERIFIED FACT — Glassdoor |
| **Clarity AI** | Senior GenAI Engineer, 11 Mar 2025: “How would you create (at a high-level) a system to detect the language of a piece of text?” | VERIFIED FACT — Glassdoor |

### E. Community-level process shape (India 2025–2026)

**Arsh Goyal (@arsh_goyal), 1 May 2026, X** — COMMUNITY EXPERIENCE (named amplifier of an unnamed switcher):

> “GenAI roles got him 100+ calls whereas SDE roles got him 2 out of 1000 applications. … Joined Wipro/TCS type company at 7.2 LPA. Worked for 2.5 years. … He rewrote his CV, ditched the DSA prep, and started applying only to GenAI roles. Got 100+ calls. 40 interviews. 2 offers. Highest at 15 LPA as an AI Engineer in NCR. … Most GenAI interviews are just plain discussions about your past work. They ask about RAG pipelines, hallucination handling, latency, MCP, guardrails, AI testing, cost optimization.”

**r/developersIndia** “Doing my first switch…” (search snippet) — COMMUNITY EXPERIENCE:

> “genai interviews are just plain discussions on what work you have done so far. Mostly, you will get question related to rag pipelines…”

**r/developersIndia** “After 36 technical interviews…” (search snippet) — COMMUNITY EXPERIENCE:

> “GenAI : Get the entire flow of RAGs nailed down: Tokens, chunking, embedding, VectorDBs, semantic searches, reranking judges (that's the most ...”

**r/developersIndia** ML interview compilation — COMMUNITY EXPERIENCE:

> unnamed company GenAI: “First round was assessment mostly on async programming. Second round involved **building a rag in a live environment**, I successfully built it but got rejected.” IDFC First Bank: “First round was dsa, ML (t statistic/p value) and Gen ai in depth (transformers/decoding strategy/graph rag).”

**r/indiafreshers** 16 months of AI/ML learning — COMMUNITY EXPERIENCE:

> “I can explain RAG architectures and LangGraph state machines, then a recruiter asks me to reverse a linked list in optimal time and it's over.”

These four community sources **agree on services/startup GenAI being RAG-discussion-heavy** and **disagree on DSA**: some loops never touch it; some still kill on linked-list.

---

## DSA vs no-DSA evidence

This is the question that most determines prep time for an 8.5 YOE ops lead.

### Finding (descriptive, not a survey)

Public 2024–2026 evidence does **not** support “GenAI interviews never do DSA.” It supports **three distinct distributions**:

1. **Services “GenAI Engineer / Developer” (TCS, Infosys, Wipro, Capgemini, Deloitte, Accenture, Cognizant)**  
   **DSA is usually absent or trivial Python**, not LeetCode medium graphs/DP.  
   Evidence: Deloitte even/odd + prime; Infosys Pune Aug 2026 “coding question were easy”; TCS LinkedIn OOP/decorators not arrays; Capgemini Mumbai Python types; Wipro “second largest in list”; Cognizant Mar 2026 “python coding questions” next to RAG evals.  
   **Exceptions:** Infosys AmbitionBox “Advanced dsa more than 6 questions”; Infosys Bengaluru Oct 2024 SHL OA (unknown coding content); IBM/GlobalLogic reuse SDE OA (HackerRank/SQL/DSA) even when the **title** is AI/GenAI.

2. **Analytics boutiques (Tiger, Fractal) and hybrid product-services (Money Forward Chennai, Techolution)**  
   **Light-to-medium DSA + Python live coding + RAG.**  
   Evidence: Tiger 3-sum + factorial; Fractal 2 Python live coding + LC Medium in some DS OAs; Money Forward optimized strings/lists/dicts; Techolution lemonade-change LeetCode.

3. **Product GCC Applied Scientist / MLE / Senior Backend-GenAI (Amazon, Microsoft, Adobe)**  
   **DSA is expected**, plus from-scratch ML (self-attention, cosine, NumPy loss).  
   Evidence: Amazon Bengaluru 1 LeetCode round in a 5-round loop; Adobe MLE Apr 2026 3 LC medium; Adobe Senior Backend-GenAI 2026 LeetCode Discuss hybrid DSA + RAG design; Microsoft “Leetcode + LLM knowledge.”

### How often is DSA required? Honest quantification

There is **no public frequency table**. Counting **distinct 2024–2026 reviews in this dossier** that mention coding:

| Segment | Reviews with **no / easy Python** coding | Reviews with **LC-style DSA** | Reviews **silent** on coding |
| --- | --- | --- | --- |
| Services GenAI titled roles | Majority of TCS/Deloitte/Capgemini/Wipro/Infosys Pune/Cognizant Mar 2026 | Minority (GlobalLogic GenAI OA, Infosys AmbitionBox DSA, IBM OA) | Several Accenture one-liners |
| Analytics (Tiger/Fractal) | Some project-only Tiger Nov 2025 | Tiger Jan 2026 3-sum; Fractal LC OA; live Python | Few |
| Product AS/MLE | Rare | Dominant | Rare |

**INFERENCE (clearly labeled):** For Manoj targeting **Cognizant-like / Infosys / TCS / Accenture / Capgemini GenAI or AIOps automation**, the binding constraint in public reviews is **RAG + agents + Python fluency + project story**, not 200 LeetCode problems. For **Tiger/Fractal/Adobe-like** roles, **Python live coding (lists, dicts, pandas, 3-sum class)** is reported often enough to practice. For **Amazon/Microsoft Applied Scientist**, skip unless also grinding DSA + ML math — that is a different career.

**Do not** assume “I will only get RAG discussion.” GlobalLogic titled the role GenAI and still ran a 2-question DSA OA. The `r/indiafreshers` candidate cleared AI rounds and died on reverse linked list.

---

## Question bank (each with source, date, company if known)

**Rule:** Only questions that appear in a candidate review, named post, or dated Glassdoor/Taro/GFG/LeetCode item. Prep-blog questions are **not** numbered here; they appear later as SECONDARY themes.

**N = 72 sourced questions** below (well above the 20 minimum). Duplicates across companies are kept when independently asked.

### Round tags

`HR` recruiter/HR · `TECH` technical IC · `HM` hiring manager / senior manager · `SD` system design / case · `CLIENT` client/partner · `OA` online assessment / take-home-like test · `LIVE` live coding

---

**Q1.** What is RAG? / What is the meaning of RAG?  
**Company/role:** Cognizant Generative AI developer (Austin, Nov 2023); Deloitte Gen AI Engineer (India, Dec 2024); IBM India SDE campus (Sep 2025, resume section).  
**Round:** TECH. **Label:** VERIFIED FACT. **Recency:** Cognizant OLDER (2023 US); Deloitte 2024; IBM 2025.  
**Sources:** [Glassdoor Cognizant](https://www.glassdoor.co.in/Interview/Cognizant-Generative-AI-developer-Interview-Questions-EI_IE8014.0,9_KO10,33.htm); [Taro Deloitte](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-india-december-1-2024-no-offer-negative-6302fac4/); [GFG IBM](https://www.geeksforgeeks.org/interview-experiences/ibm-india-interview-experience-for-software-developer-on-campus/).

**Q2.** Explain the current project you are working on.  
**Company/role:** Deloitte Gen AI Engineer, India, Dec 2024. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Taro Deloitte Dec 2024.

**Q3.** How do you deal with PDFs containing images?  
**Company/role:** Deloitte Gen AI Engineer, India, Dec 2024. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Taro Deloitte Dec 2024.  
**Quote:** “How do you deal with PDFs containing images?” (same theme repeated in round 2 as unstructured PDFs).

**Q4.** Write a program to print even and odd numbers from a given list.  
**Company/role:** Deloitte Gen AI Engineer, India, Dec 2024. **Round:** LIVE. **Label:** VERIFIED FACT.  
**Source:** Taro Deloitte Dec 2024.

**Q5.** Write a program to determine if a number is prime.  
**Company/role:** Deloitte, same review. **Round:** LIVE. **Label:** VERIFIED FACT.

**Q6.** What is an imbalanced dataset? What is F1 score?  
**Company/role:** Deloitte Gen AI Engineer, India, Dec 2024. **Round:** TECH. **Label:** VERIFIED FACT.  
**Note:** Classical ML sitting inside a “Gen AI” loop.

**Q7.** What prompt-engineering techniques do you know? What are agents?  
**Company/role:** Deloitte, Dec 2024. Candidate had ~1 YOE; **failed agents**. Recommended LangChain, LangGraph, prompt methods. **Round:** TECH. **Label:** VERIFIED FACT.

**Q8.** What are the types of chunking?  
**Company/role:** Deloitte, Dec 2024, round 2. **Round:** TECH. **Label:** VERIFIED FACT.  
**Quote:** “What are the types of chucking?” (reviewer’s spelling).

**Q9.** What is SCD? Explain how you remove duplicates from a table.  
**Company/role:** Deloitte, Dec 2024, round 2. **Round:** TECH. **Label:** VERIFIED FACT.  
**Note:** Data-engineering concepts inside GenAI loop.

**Q10.** How do RAG and Agent LLM models work? RAG versus Agent? Shared memory between agents? How would you design an agent? Embedding models? How to access a very big RAG?  
**Company/role:** Deloitte Gen AI Engineer, Bengaluru, Jun 2025. **Round:** TECH (45 min of a 60 min loop after 2 basic Python Qs). **Label:** VERIFIED FACT.  
**Source:** [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-bengaluru-karnataka-june-1-2025-no-offer-positive-5eb74f34/).  
**Quote:** “Like how RAG and Agent LLM models work, RAG versus Agent, shared memory between agents. Scenario-based questions on how I would design an agent, embedding models, and how to access a very big RAG.”

**Q11.** What is one-bit quantization?  
**Company/role:** Deloitte Gen AI Engineer, India, Dec 2024 (separate review). **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-india-december-1-2024-no-offer-negative-2c45121c/). First round also: Python coding, NLP, GenAI, DL, ML, RAG, LLM.

**Q12.** RAG and agentic framework and its application.  
**Company/role:** Deloitte Bengaluru, Apr 2025, **client round** after 2 tech + partner. **Round:** CLIENT. **Label:** VERIFIED FACT.  
**Source:** [Taro](https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-bengaluru-karnataka-april-1-2025-no-offer-neutral-7ea08313/). Candidate cleared first three, rejected in client.

**Q13.** What is a Vector DB?  
**Company/role:** TCS GenAI Developer/Consultant, virtual, ~Jun 2025. **Round:** TECH (Senior Engineer). **Label:** VERIFIED FACT.  
**Source:** [LinkedIn — Shanmukha Sai Srinivas Nunna](https://www.linkedin.com/posts/shanmuknunna_genai-tcs-interviewexperience-activity-7336343348636545025-1tG7).

**Q14.** RAG architecture — components and flow.  
**Company/role:** TCS, same. **Round:** TECH. **Label:** VERIFIED FACT.

**Q15.** Similarity techniques — cosine, dot-product, Euclidean — and when to use each.  
**Company/role:** TCS, same. **Round:** TECH. **Label:** VERIFIED FACT.

**Q16.** Which vector DBs (FAISS, Chroma, Weaviate, Pinecone) — pros/cons.  
**Company/role:** TCS, same. **Round:** TECH. **Label:** VERIFIED FACT.

**Q17.** How to improve a QA chatbot built on RAG.  
**Company/role:** TCS, same. **Round:** TECH. **Label:** VERIFIED FACT.

**Q18.** Python: decorators; list comprehensions; parallel processing vs multiprocessing; inheritance; polymorphism; class method vs static method.  
**Company/role:** TCS, same. **Round:** TECH. **Label:** VERIFIED FACT.

**Q19.** LangChain use cases (agents, tools, chains, memory).  
**Company/role:** TCS, same. **Round:** HM (Senior Manager). **Label:** VERIFIED FACT.

**Q20.** LLM evaluation metrics: BLEU, ROUGE, perplexity, F1. Fine-tuning vs RAG — when to prefer what. How to fine-tune an LLM.  
**Company/role:** TCS, same. **Round:** HM. **Label:** VERIFIED FACT.

**Q21.** Tackling hallucination, context size, grounding.  
**Company/role:** TCS, same. **Round:** HM. **Label:** VERIFIED FACT.  
**Quote:** “Highlighted the biggest challenge: prompt hallucination and how I mitigated it using context chunk optimization and system prompts.”

**Q22.** How would you fine-tune a pre-trained LLM for a domain-specific use case? Difference between fine-tuning and prompt engineering?  
**Company/role:** Infosys GenAI Developer (friend’s interview posted by Arunabha Sarkar), ~Feb 2026. **Round:** L1 TECH. **Label:** COMMUNITY EXPERIENCE (second-hand, named poster).  
**Source:** [LinkedIn](https://www.linkedin.com/posts/arunabha-sarkar-alex_infosysinterview-genaiinterview-llmengineering-activity-7427924490401103872-e3y0).

**Q23.** How do token limits impact GenAI application design?  
**Company/role:** Infosys, same. **Round:** L1. **Label:** COMMUNITY EXPERIENCE.

**Q24.** How would you manage rate limits in OpenAI/Azure APIs? How do you log and monitor LLM API failures in production?  
**Company/role:** Infosys, same. **Round:** L1. **Label:** COMMUNITY EXPERIENCE.

**Q25.** What is temperature and top_p? When would you adjust them?  
**Company/role:** Infosys, same. **Round:** L1. **Label:** COMMUNITY EXPERIENCE.

**Q26.** How would you cache LLM responses to reduce cost? Explain how streaming responses work in LLM APIs.  
**Company/role:** Infosys, same. **Round:** L1. **Label:** COMMUNITY EXPERIENCE.

**Q27.** A client wants to automate RFP analysis using GenAI. How would you design the solution?  
**Company/role:** Infosys, same. **Round:** L2 SD/consulting. **Label:** COMMUNITY EXPERIENCE.

**Q28.** How do you prevent sensitive enterprise data from leaking into public models?  
**Company/role:** Infosys, same. **Round:** L2. **Label:** COMMUNITY EXPERIENCE.

**Q29.** What KPIs would you define to measure GenAI solution success?  
**Company/role:** Infosys, same. **Round:** L2. **Label:** COMMUNITY EXPERIENCE.

**Q30.** How would you compare OpenAI vs an open-source LLM? When would you choose a small model over a large model? How do you reduce inference cost in high-traffic applications?  
**Company/role:** Infosys, same. **Round:** L2. **Label:** COMMUNITY EXPERIENCE.

**Q31.** What risks do you see in deploying GenAI in regulated industries? How would you convince a non-technical stakeholder about ROI of GenAI?  
**Company/role:** Infosys, same. **Round:** L2. **Label:** COMMUNITY EXPERIENCE.

**Q32.** Mostly questions related to my project and the RAG. HR: notice period and salary expectations.  
**Company/role:** Infosys Gen AI Engineer, recruiter-sourced. **Round:** TECH + HR. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Infosys Gen AI Engineer.

**Q33.** Clustering, Linear Regression, K-means, KNN (all ML algorithms).  
**Company/role:** Infosys Gen AI Engineer, Bengaluru, Oct 2024. **Round:** TECH after SHL OA. **Label:** VERIFIED FACT.  
**Source:** Glassdoor 10 Nov 2024.

**Q34.** Easy coding; Python `*args` vs `**kwargs`; types of prompting; difference between GenAI and Agentic AI; what is fine-tuning; how it handles hallucination.  
**Company/role:** Infosys Gen AI Engineer, Pune, Aug 2026. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor updated 10 Aug 2026.  
**Quote:** “coding question were easy ,also asked some python theory q like arbitary aruguments,diffence of args n kwargs,types of prompting, diffence bet gen ai n agentic ai ,what is fine tuning ,how it handle hallucination,etc”

**Q35.** Explain transformer architecture. What is cosine similarity. Tell me about yourself. Tell me about your projects.  
**Company/role:** Infosys GenAI Engineer. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** [AmbitionBox Infosys GenAI Engineer](https://www.ambitionbox.com/interviews/infosys-interview-questions/genai-engineer) (updated 10 Aug 2026). Separate AmbitionBox item: “Advanced dsa more than 6 questions”; “About my project in depth especially about genai.”

**Q36.** What is agentic AI and AI agents? Which is better? What are retrievers in RAG? Which similarity search to use for semantic search? How is performance of LLM model checked?  
**Company/role:** Accenture Gen AI developer. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** [Glassdoor QTN_8348946](https://www.glassdoor.com/Interview/I-had-appplied-for-Gen-AI-developer-position-Below-were-the-question-asked-What-is-agentic-ai-and-ai-agents-Which-is-b-QTN_8348946.htm).

**Q37.** What is RAG, LLM-based learning?  
**Company/role:** Accenture Machine Learning Engineer. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** [Glassdoor QTN_7836327](https://www.glassdoor.com/Interview/Q-What-is-RAG-LLM-based-Learning-QTN_7836327.htm).

**Q38.** Question on Gen AI, RAG pipeline. Follow-up on projects.  
**Company/role:** Accenture Analyst. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** [Glassdoor QTN_8719740](https://www.glassdoor.com/Interview/Question-on-Gen-AI-RAG-pipeline-was-asked-Follow-up-questions-on-projects-QTN_8719740.htm).

**Q39.** Explain what you have done in AI/ML; RAG full form in GenAI; What is Responsible AI; How you do the estimation.  
**Company/role:** Accenture (undated on Q page). **Round:** TECH/HM. **Label:** VERIFIED FACT.  
**Source:** [Glassdoor QTN_7354214](https://www.glassdoor.com/Interview/Explain-what-you-have-done-in-AI-ML-explain-how-it-works-What-is-RAG-full-form-in-GenAI-What-is-Responsible-AI-How-QTN_7354214.htm).

**Q40.** Online: LangChain, prompting techniques, RAG, retrieval.  
**Company/role:** Accenture AI ML Engineer, India, process described on page updated 1 Aug 2026. **Round:** OA + TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor.co.in Accenture AI ML Engineer.

**Q41.** Given you need to design a RAG solution for multiple clients where you cannot use the documents of other clients if users from another client ask a query.  
**Company/role:** Capgemini GenAI engineer, Gurgaon, Dec 2025. **Round:** SD. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Capgemini RVW101720117.  
**Quote:** “Given you need to design a RAG solution for multiple clients where the requirement is you cannot use the documents of other client if users from another client is asking a query?”

**Q42.** What are the two most important components of RAG and how will you evaluate a RAG model performance.  
**Company/role:** Capgemini GenAI AIML, 21 Jul 2025. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor India genai engineer questions.

**Q43.** Transformer architecture, self-attention mechanism.  
**Company/role:** Capgemini GenAI engineer, 2 Sep 2025. **Round:** TECH. **Label:** VERIFIED FACT.

**Q44.** RAG, hallucination management, prompt engineering, evaluation metrics, unstructured data, OpenCV, pandas, LangGraph, LangChain, LLMs.  
**Company/role:** Capgemini, face-to-face L1+L2 (Glassdoor snippet). **Round:** TECH. **Label:** VERIFIED FACT.

**Q45.** Prompting and various LLMs; vector databases available; NLP projects.  
**Company/role:** Capgemini Gen AI Engineer, Hyderabad, 29 Mar 2025. **Round:** TECH L1. **Label:** VERIFIED FACT.  
**Source:** Taro Capgemini Hyderabad.

**Q46.** What are Python’s key features? How is Python an interpreted language? Built-in data types? Difference between list, tuple, set, and dictionary? How is memory managed in Python?  
**Company/role:** Capgemini Gen AI Engineer, Mumbai, 19 Mar 2025 (offer). **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Taro Capgemini Mumbai.

**Q47.** Easy Python coding; interviewer wanted the solution the way she would have solved it.  
**Company/role:** Capgemini Gen AI Engineer L2, India, 23 Sep 2025. **Round:** LIVE. **Label:** VERIFIED FACT.  
**Source:** Taro Capgemini Sep 2025. Process note: no project questions; interviewer not a GenAI practitioner.

**Q48.** RAG pipeline; what difficulties you faced.  
**Company/role:** Wipro Gen AI Engineer, posted 25 Nov 2024. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Wipro Gen AI Engineer.

**Q49.** LLM fine-tuning how to make it and host [on] cloud services. (Also: RAG, LLM, cloud, LangChain, Python, NLP from scratch, MLOps.)  
**Company/role:** Wipro Gen AI Engineer, Pune, Jul 2024. **Round:** TECH. **Label:** VERIFIED FACT.

**Q50.** How RAG works; why do we need a vector database; **what was the chunk size you used in the project and why**; how BERT works and its limitations; Python: find second largest element in a list.  
**Company/role:** Wipro AI/ML Engineer, Jun 2025; **client round harder than internal**. **Round:** TECH + CLIENT + LIVE. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Wipro AI ML Engineer.

**Q51.** Explain RAG and what is chunking.  
**Company/role:** Wipro Software Engineer, AI-based interview, ~Aug 2026. **Round:** TECH. **Label:** VERIFIED FACT.

**Q52.** How does transformer work and what will change if we make changes in encoder/decoder blocks?  
**Company/role:** Wipro AI/ML Engineer. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Wipro AI ML Engineer.

**Q53.** Round 1: Agentic AI — how to create, orchestrate agents; RAG pipeline, evaluation, metrics; Python coding. Round 2: ML, DL, NLP, GenAI, Cloud, scenario-based.  
**Company/role:** Cognizant Gen AI Engineer, 31 Mar 2026 (accepted offer). **Round:** TECH ×2. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Cognizant Gen AI Engineer.

**Q54.** What are the biggest problems to tackle with generative AI implementation for businesses?  
**Company/role:** Cognizant Gen AI Engineer, Amsterdam, Dec 2024. **Round:** TECH/HM. **Label:** VERIFIED FACT. (Not India; included as Cognizant process contrast.)

**Q55.** What is GEN AI and why it is booming?  
**Company/role:** Cognizant Full Stack Developer, Chennai, Aug 2025. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Cognizant FSD. Shows even non-GenAI titles now get a GenAI awareness question.

**Q56.** Types of RAG; chunking types; deployment strategies; 2 Python questions; recently worked project.  
**Company/role:** Tiger Analytics AI Engineer. **Round:** TECH. **Label:** COMMUNITY EXPERIENCE.  
**Source:** r/dataengineersindia search snippet; corroborated by Glassdoor Nov 2025 Hyderabad.

**Q57.** 1st round DSA, 2nd ML/DL: RAG architecture, Agentic AI, deployment, AWS, Azure; factorial; 3-sum; types of deployments; deployment rollback; why you want to change.  
**Company/role:** Tiger Analytics AI Engineer, Hyderabad, 16 Jan 2026. **Round:** TECH + LIVE + HR-ish. **Label:** VERIFIED FACT.  
**Source:** Glassdoor.

**Q58.** Transformers architecture to show maths involved.  
**Company/role:** Tiger Analytics AI Engineer. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor (same company page). Another candidate on that page: coding not relevant, **no AI questions**.

**Q59.** Deep learning questions, RAG, fine-tuning, explanation of business use case; also system design, API, Docker, Kubernetes.  
**Company/role:** Tiger Analytics Senior AI Engineer, Bengaluru, Jun 2025. **Round:** TECH ×3 of 4. **Label:** VERIFIED FACT.

**Q60.** CoderPad: sum of digits until a single digit; SQL: second-highest salary by department.  
**Company/role:** Tiger Analytics Senior AI Engineer. **Round:** LIVE. **Label:** VERIFIED FACT.

**Q61.** Transfer; Agentic AI; LangGraph; detail about project; 2 Python live coding.  
**Company/role:** Fractal Gen AI Engineer, interviewed Sep 2025 (posted Mar 2026). **Round:** LIVE + TECH. **Label:** VERIFIED FACT. Process took **6 months**.

**Q62.** Printing series patterns; list/dictionary comprehension; ML preprocessing and model evaluation; DL optimizers and gradient descent; RAG and LLMs.  
**Company/role:** Fractal Sr Data Scientist Generative AI, Noida, Oct 2025, Round 1. **Round:** TECH + LIVE. **Label:** VERIFIED FACT.

**Q63.** Sentence transformers; benchmarking; RAG architecture; evaluation frameworks **RAGAs, DSPy**; transformer fundamentals; training word embeddings; contextual awareness; positional encoding.  
**Company/role:** Fractal, same, Round 2. **Round:** TECH. **Label:** VERIFIED FACT.

**Q64.** Difference between RAG and Agentic RAG. How to evaluate and improve the performance of a deployed model/agent. Also: MCPs.  
**Company/role:** Fractal Senior Data Scientist, New Delhi, Sep 2025. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor.ca Fractal Senior Data Scientist.

**Q65.** Fine-tune and RAG difference.  
**Company/role:** Fractal Data Scientist. **Round:** TECH. **Label:** VERIFIED FACT.  
**Source:** Glassdoor.co.in Fractal Data Science.

**Q66.** LangGraph, LangChain, vector DB, Python, pandas; easy–medium coding; think about a GenAI use case.  
**Company/role:** Fractal Data Scientist, Bengaluru, Jul 2026. **Round:** TECH + LIVE. **Label:** VERIFIED FACT.

**Q67.** Multi-agentic systems, RAG, LLM evaluation; 2 coding from strings and lists (optimized); how to train a model, data preprocessing.  
**Company/role:** Money Forward Generative AI Engineer, Chennai, Sep 2025. **Round:** TECH ×3 + HR. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Money Forward. R3 explicitly **LLMOps**.

**Q68.** Lemonade change (LeetCode) and a basic array manipulation.  
**Company/role:** Techolution Generative AI Engineer, 22 Dec 2024. **Round:** LIVE. **Label:** VERIFIED FACT.

**Q69.** They asked about how transformers work.  
**Company/role:** Techolution Generative AI Engineer, 27 Nov 2024. **Round:** TECH. **Label:** VERIFIED FACT. Candidate: “Missed the opportunity by not being well prepared… prepare well on how AI works.”

**Q70.** Design a scalable document Q&A system where enterprise users upload documents and ask questions. Explain how attention works in transformers and why it matters for RAG. How do you evaluate a RAG pipeline in production?  
**Company/role:** Adobe Senior Backend Engineer – Python / Gen AI, Noida, 2026. **Round:** SD + TECH. **Label:** VERIFIED FACT.  
**Source:** [LeetCode Discuss](https://leetcode.com/discuss/post/8317558/adobe-interview-experience-senior-backen-7zp1/). Candidate (~5 YOE LangChain/LangGraph/RAG/LLMOps) used RAGAS (faithfulness, answer relevancy, context precision/recall), LLM-as-judge, golden dataset, latency/cost.

**Q71.** Types of attention in transformers. BERT vs GPT for text classification (representations, train/infer efficiency, why GPT if bidirectional is useful). Text summarisation metrics without ground truth; how ROUGE/BLEU work without GT. Explain one project. 3 LC medium (60 min).  
**Company/role:** Adobe Machine Learning Engineer, Bengaluru, Apr 2026. **Round:** TECH + LIVE. **Label:** VERIFIED FACT.  
**Source:** Glassdoor Adobe 2 Aug 2026.

**Q72.** Did I have to deal with repercussions of deploying AI, like to job, training or org? What metrics have I used to assess GenAI impact? Tell me about a project where I handled security / data privacy.  
**Company/role:** ServiceNow GenAI Architect, 16 May 2025. **Round:** HM / behavioural-technical. **Label:** VERIFIED FACT.  
**Source:** Glassdoor ServiceNow GenAI Architect; [QTN_8234637](https://www.glassdoor.com/Interview/Did-I-have-to-deal-with-repercussions-of-deploying-AI-like-to-job-training-or-org-QTN_8234637.htm).

**Additional sourced items (not double-counted in the 72 if overlapping):**

- **IBM Bengaluru Aug 2025:** About RNN, Transfer Learning and RAG — VERIFIED FACT Glassdoor.  
- **IBM Bengaluru Feb 2025:** RAG, LLMs, Deep Learning, performance metrics — VERIFIED FACT Taro.  
- **IBM Pune Jun 2026:** How would you integrate an ML model into an existing enterprise system? — VERIFIED FACT Glassdoor.  
- **GlobalLogic Hyderabad Sep 2025 GenAI:** Basics of SQL, DSA, CS fundamentals, projects — VERIFIED FACT Glassdoor.  
- **Amazon Bengaluru Nov 2024 AS:** If order of tokens didn’t matter, how would you train? — VERIFIED FACT Glassdoor.  
- **Amazon Bangalore Rural Jan 2026 AS:** Cross-entropy → MSE; Wq=Wk=Wv in a transformer — VERIFIED FACT Glassdoor.  
- **Amazon AS:** Cosine similarity on sparse vectors, then top-k — VERIFIED FACT Glassdoor.  
- **Amazon AS II:** Design an agentic recommendation system — VERIFIED FACT Glassdoor.  
- **Microsoft AS II:** Implement self-attention from scratch — VERIFIED FACT Glassdoor.  
- **Microsoft AS:** Design RAG that generates slides from a prompt; design chatbot for advertisement org — VERIFIED FACT Glassdoor.  
- **Microsoft AS II Jul 2026:** Space complexity of various parts of the Transformer — VERIFIED FACT Glassdoor.  
- **Microsoft Bengaluru AS:** Write logistic-regression loss through NumPy — VERIFIED FACT Glassdoor.  
- **Adam Technologies Gen AI Engineer, 7 May 2025:** How does an AI agent work? — VERIFIED FACT Glassdoor India gen-ai-engineer questions.  
- **Force Factor Gen AI intern, 4 Aug 2025:** Explain Transformers Attention, RAG, TTS, projects — VERIFIED FACT Glassdoor.  
- **NTT DATA Gen AI Engineer, 23 Dec 2024:** ML algorithms — which to use, why, when not — VERIFIED FACT Glassdoor.  
- **Clarity AI Senior GenAI Engineer, 11 Mar 2025:** High-level language-detection system — VERIFIED FACT Glassdoor.

---

## AIOps-specific questions

**Honest status: Insufficient reliable India 2024–2026 candidate-labeled AIOps interview transcripts (N_named ≈ 0–2).**

What exists:

### Near-AIOps / ITSM+AI (still not a full AIOps loop)

- **ServiceNow GenAI Architect, 16 May 2025 (VERIFIED FACT):** repercussions of deploying AI on jobs/training/org; metrics of GenAI impact; security/data privacy. This is **change-management + GenAI**, which maps to AIOps *organizational* risk, not anomaly-detection math.  
- **IBM Pune Jun 2026 AI Engineer (VERIFIED FACT):** “How would you integrate a machine learning model into an existing enterprise system?” — closest production-ops question in the AI Engineer set.  
- **Accenture India JD (not an interview, but hiring signal, Aug 2026):** AI / API Engineer – Agentic AI Solutions, Payroll: “mentoring internal talent transitioning into AI roles”; agentic workflows on Azure OpenAI. **Not a question list.**  
- **Accenture services Pvt Ltd LinkedIn JD, Gurugram 2026:** Backend Engineer on an **AI Ops platform**: incident ingestion, AI root-cause enrichment, escalation routing, FinOps, SLA tracking. **Job description, not interview Qs.**

### SECONDARY (do not treat as “asked at Company X in India”)

- ServiceNow Community “Predictive AIOps scenario-based questions 2025” (LinkedIn Pulse / community articles): What is Predictive AIOps; how it differs from traditional event management. **SECONDARY BLOG.**  
- aiofferly “ServiceNow ML Interview Questions – 2026”: “What do you log for debugging an AI agent, and what must you not log?” **SECONDARY.**  
- snbuddy ServiceNow Generative AI Qs: token limits when incident history exceeds context window. **SECONDARY.**  
- Towards AI “101 ML/LLM/Agentic AIOPS Interview Questions” (29 Sep 2025). **SECONDARY.**  
- DataCamp / Learnbay / CloudSoft GenAI lists that mention observability, Kubernetes serving, Azure OpenAI vs Bedrock. **SECONDARY** unless matched to a review above.

### Topics requested in the research brief vs evidence

| Requested AIOps topic | Found in a named India/GenAI review? |
| --- | --- |
| Incident classification | **No named review** |
| Anomaly detection | **No named GenAI-role review** |
| Log NLP | **No named review** |
| ITSM + LLM | ServiceNow GenAI Architect is org-impact, not ITSM ticket NLP |
| On-call | **No named review** |
| SLO/SLI | **No named review** |
| Runbook automation | **No named review** |

**INFERENCE:** An 8.5 YOE Service Desk lead interviewing for **AIOps / ITSM+LLM** should not expect a public question bank. Closest verified patterns are: (1) **enterprise RAG with tenancy** (Capgemini multi-client docs), (2) **production LLM failures/logging/rate limits** (Infosys L1 second-hand), (3) **change impact of AI on jobs** (ServiceNow), (4) **integrating a model into an existing system** (IBM). Build stories from **incident queues, runbooks, and ticket taxonomy** and be ready to map them onto RAG/agents — but that mapping is prep strategy, not a documented interview script.

---

## GenAI / RAG / agents questions (thematic index of *verified* asks)

This section regroups the question bank. No new questions.

### RAG architecture, chunking, embeddings, vector DBs

Asked at: **TCS** (full RAG flow + vector DB comparison + cosine/dot/Euclidean); **Deloitte** (what is RAG, types of chunking, PDFs/images, “very big RAG”); **Wipro** (RAG pipeline difficulties; **chunk size you used and why**; why vector DB); **Capgemini** (two most important RAG components + eval; **multi-tenant RAG**); **Accenture** (RAG pipeline, retrievers, similarity for semantic search); **Cognizant** (RAG pipeline + eval metrics); **Tiger** (types of RAG, chunking, embeddings, data updates); **Fractal** (RAG architecture, retrievers, RAG vs Agentic RAG); **Infosys** (project + RAG; hallucination); **Adobe Noida** (design document Q&A); **Money Forward** (RAG + LLM eval).

### Hallucination, evals, function calling, agents

Asked at: **TCS** (hallucination, BLEU/ROUGE/perplexity/F1); **Deloitte** (what are agents; RAG vs Agent; shared memory; design an agent); **Infosys Pune** (how fine-tuning handles hallucination; GenAI vs Agentic); **Infosys L1/L2 second-hand** (cache, streaming, KPIs); **Fractal** (LangGraph, MCP, evaluate deployed agent, RAGAs/DSPy); **Cognizant Mar 2026** (orchestrate agents; eval metrics); **Accenture** (agentic vs agents; how LLM performance is checked); **Adobe** (RAGAS + LLM-as-judge); **Money Forward** (multi-agentic, LLM evaluation, LLMOps round); **Adam Technologies** (how does an AI agent work).

### LangChain vs raw API, token costs, safety, prompt injection, hybrid search, caching, observability, K8s serving, Azure OpenAI vs Bedrock

| Topic | Verified in a candidate review? |
| --- | --- |
| LangChain (as named tool) | **Yes** — TCS managerial; Wipro Pune; Capgemini L1/L2; Accenture online; Fractal LangChain/LangGraph |
| Raw API vs LangChain | **Not found as an explicit “LangChain vs raw API” question** |
| Token costs | **Yes** — Infosys L1 token limits + cache to reduce cost; Infosys L2 inference cost; Adobe eval latency/cost |
| Safety / Responsible AI | **Yes** — Accenture Responsible AI; ServiceNow privacy; Infosys L2 data leak + regulated industries |
| Prompt injection | **Not found in a named India review in this research window** |
| Hybrid search | **Not found as the words “hybrid search”** in named reviews; TCS asked cosine vs dot vs Euclidean |
| Caching | **Yes** — Infosys L1 “How would you cache LLM responses to reduce cost?” |
| Observability of LLM apps | **Yes (partial)** — Infosys L1 log/monitor API failures; Fractal evaluate deployed agent |
| Kubernetes for model serving | **Yes (partial)** — Tiger Senior AI Engineer Bengaluru Jun 2025: Docker and Kubernetes among engineering questions |
| Azure OpenAI vs Bedrock | **Not found as an explicit comparison question.** Infosys L1 mentioned OpenAI/**Azure** rate limits; Infosys L2 OpenAI vs **open-source**; Tiger asked AWS **and** Azure. |

### Transformers / internals (more ML than services GenAI)

Asked at: **Capgemini** (self-attention); **Techolution** (how transformers work); **Tiger** (transformer maths); **Fractal** (transformer, positional encoding); **Wipro** (encoder/decoder changes; BERT); **Amazon AS** (Wq=Wk=Wv; order-invariant training); **Microsoft AS** (implement self-attention; transformer space complexity); **Adobe** (attention types; BERT vs GPT); **Force Factor intern** (Transformers Attention, RAG, TTS).

---

## Behavioural / transition questions

### What was actually asked (verified)

| Question / theme | Where | Round | Label |
| --- | --- | --- | --- |
| Tell me about yourself | TCS GenAI; Infosys AmbitionBox; nearly universal | TECH/HR | VERIFIED FACT |
| Notice period and salary expectations | Infosys Gen AI Engineer HR | HR | VERIFIED FACT |
| Why you want to change | Tiger Analytics AI Engineer, Jan 2026 | TECH/HR | VERIFIED FACT |
| Project walkthrough / “explain current project” | Deloitte, TCS, Infosys, Fractal, Wipro, IBM, Cognizant | TECH/HM | VERIFIED FACT |
| Leadership & ownership, initiative, continuous learning | TCS Senior Manager round | HM | VERIFIED FACT |
| Biggest challenge (candidate volunteered hallucination mitigation) | TCS | HM | VERIFIED FACT |
| Repercussions of deploying AI on jobs, training, org | ServiceNow GenAI Architect, May 2025 | HM | VERIFIED FACT |
| Metrics used to assess GenAI impact | ServiceNow GenAI Architect | HM | VERIFIED FACT |
| Security / data privacy project | ServiceNow GenAI Architect | HM | VERIFIED FACT |
| Convince a non-technical stakeholder of GenAI ROI | Infosys L2 (second-hand) | HM | COMMUNITY EXPERIENCE |
| Team skills (HR) | Microsoft AS Bengaluru | HR | VERIFIED FACT |
| YOE vs JD mismatch (rejection reason, not a question) | Capgemini L2 “yrs of experience did not match with JD” | HM | VERIFIED FACT |

### What was **not** found as a quoted question

- “Why are you transitioning from support?”  
- “Your current CTC is 11 LPA — justify.”  
- “Are you a developer?”  
- “You have a gap in coding.”  

Those are **reasonable HR questions** but **not documented** in the GenAI reviews collected. Do not treat them as verified asks.

**Closest verified analogues:** Tiger “why you want to change”; Infosys HR salary + notice; Capgemini rejecting on YOE vs JD; ServiceNow “repercussions of deploying AI on jobs” (the inverse of a support-to-AI story — they asked a *deployer* about workforce impact).

Infosys HR quote (Glassdoor): “There was just one technical round and then the HR round that asked me about my notice period as well as my salary expectations.”

TCS quote (LinkedIn): managerial round included “Leadership & Ownership – problem solving, initiative, and continuous learning.”

---

## Take-home and portfolio review

### Take-home / OA / live-build (verified)

| Pattern | Company | Date | Detail | Label |
| --- | --- | --- | --- | --- |
| SHL online assessment | Infosys Gen AI Engineer, Bengaluru | Oct 2024 | OA → in-person tech → HR | VERIFIED FACT |
| HackerRank coding + SQL | IBM AI Engineer, Bengaluru / Pune | 2025–2026 | Gate before office interviews | VERIFIED FACT |
| 2 DSA questions OA | GlobalLogic **GenAI engineer** | Sep 2025 | Arrays/strings/hashmaps/DP/graphs listed | VERIFIED FACT |
| Live **build a RAG** in the interview environment | Unnamed, r/developersIndia ML compilation | ~2025 | Built successfully, still rejected | COMMUNITY EXPERIENCE |
| Python live coding 1–1.5 hours | Fractal Gen AI Engineer | Sep 2025 | Then pure technical, fitment, HR | VERIFIED FACT |
| CoderPad live | Tiger Senior AI Engineer | — | Digit-sum variants; SQL | VERIFIED FACT |
| HackerEarth with interviewer (code + flow diagrams) | Fractal DS | Jul 2026 | LangGraph/LangChain/vector DB | VERIFIED FACT |
| Coding assessment: design an OOP project | Techolution GenAI | 2024–2025 | Plus later LeetCode lemonade change | VERIFIED FACT |
| ML MCQ + 2 LC Medium + Git | Fractal DS OA | Feb 2025 | Then tech OOP | VERIFIED FACT |
| Thoughtworks assessments | Thoughtworks India careers | 2026 policy | GenAI tools allowed if thinking is authentic | VERIFIED FACT (policy, not a specific assignment) |

**No widely reported multi-day take-home “build a RAG overnight” for TCS/Infosys/Wipro/Cognizant GenAI** in this sample. Services loops prefer **live discussion of a project already on the resume** plus easy Python. Analytics and product prefer **live coding in the round**.

### Portfolio review patterns (what interviewers actually drilled)

1. **Chunk size you used and why** — Wipro Jun 2025 client round. If the resume says “RAG chatbot,” expect this.  
2. **Difficulties in the RAG pipeline** — Wipro Nov 2024.  
3. **How you mitigated hallucination** — TCS candidate used chunk optimization + system prompts.  
4. **PDFs with images / unstructured data** — Deloitte.  
5. **Data updates to the index** — Tiger Nov 2025.  
6. **Multi-tenant isolation** — Capgemini Dec 2025.  
7. **Agent orchestration, memory, MCP** — Cognizant Mar 2026; Fractal Sep 2025; Deloitte Jun 2025.  
8. **Evaluation: RAGAS / DSPy / BLEU-ROUGE** — Fractal; TCS; Adobe.  
9. **LLMOps** as a dedicated round — Money Forward Chennai R3.  
10. **Toy LangChain demos vs production** — Infosys L1 second-hand: “They checked whether you’ve actually built something — not just read about it.”

**INFERENCE:** For an ops lead without a shipped RAG, a public GitHub “LangChain tutorial clone” will fail Wipro-style “what chunk size and why” and Infosys-style implementation L1. A **single domain RAG** (e.g., ITSM runbooks / incident notes) with documented chunking, evals, and failure cases matches the verified drill pattern better than five certificates.

---

## Rejection patterns

Only patterns with a source. No invented “career switcher from L1 support” stories.

| Pattern | Evidence | Label |
| --- | --- | --- |
| **Failed a topic you had not prepared (agents)** | Deloitte Dec 2024: “Some questions were asked on agents which im not aware of.” Recommend LangChain, LangGraph, prompt methods. | VERIFIED FACT |
| **Cleared internal rounds, died on client round** | Deloitte Bengaluru Apr 2025: 4 elimination rounds; failed final client. Wipro Jun 2025: client round “much more difficult… Indepth knowledge of GenAI.” | VERIFIED FACT |
| **YOE vs JD mismatch after a good L2** | Capgemini: “L2 went good, but yrs of experience did not match with JD, so they informed will not be able to move further.” | VERIFIED FACT |
| **Interviewer not a GenAI practitioner; process noise** | Capgemini Sep 2025 L2: interviewer eating, baby, mute issues, wanted *her* Python solution, no project Qs. Cognizant US 2023: interviewer stated incorrect temperature fact. | VERIFIED FACT |
| **Built the RAG live, still rejected, “dk why”** | r/developersIndia ML compilation | COMMUNITY EXPERIENCE |
| **Cleared AI/ML rounds, failed DSA** | r/indiafreshers: LangGraph + RAG then reverse linked list | COMMUNITY EXPERIENCE |
| **Superficial RAG answers** | Medium, Abhinaba Banerjee, 3 Apr 2026: Senior DS-AI Engineer interview at a Big Tech (non-FAANG). “I did answer about the PDF loading and embedding questions, but those were half-baked and superficial. … I didn’t get the job.” | COMMUNITY EXPERIENCE (named, not India-tagged) |
| **SDE applications dead; GenAI applications alive but low conversion** | Arsh Goyal X 1 May 2026: 1000 SDE apps → 2 interviews, both rejected on **live backend modification**, not DSA. Then GenAI: 100+ calls, 40 interviews, **2 offers**, 15 LPA. | COMMUNITY EXPERIENCE |
| **Limited experience / ghosting after 2–3 rounds** | Glassdoor Tech India forum, Oct 2025: M.Tech AI/ML, 10 months exp, 14 calls, 8 rejected for limited experience, 3–4 ghosted. | COMMUNITY EXPERIENCE |
| **Classical ML asked in a “GenAI” title; candidate may have been mismatched** | Infosys Bengaluru Oct 2024: K-means/KNN after SHL. GlobalLogic GenAI OA = DSA. | VERIFIED FACT (mismatch risk) |
| **6-month Fractal process** | Fractal Gen AI Engineer accepted offer, process **6 months** (interviewed Sep 2025, posted Mar 2026). Slow loops kill notice-period candidates. | VERIFIED FACT |
| **Taro computed 0% pass rate** on 4 Deloitte India Gen AI Engineer public experiences | Small-n, selection-biased (rejects post more), but directionally harsh | SECONDARY statistic on VERIFIED reviews |

**What is missing:** No named review that says “rejected because I came from Service Desk / L1–L2 support.” That does not mean it does not happen; it means **it is not in the public evidence set**.

---

## Prep implications for 8.5 YOE ops lead (INFERENCE clearly labeled)

Everything in this section is **INFERENCE** from the evidence above, mapped to Manoj’s profile (Cognizant Service Desk Lead, 8.5 YOE, ~11 LPA, no Java/SQL-first, targeting GenAI/Agentic/LLM/AIOps/AI automation in India). It is not a claim that any company asked him these things.

1. **Target the loop you can actually pass.**  
   Public evidence says **TCS / Infosys / Wipro / Capgemini / Cognizant / Accenture / Deloitte “GenAI Engineer”** loops are mostly **RAG + agents + Python + project grilling**, sometimes with a **client round**. **Amazon/Microsoft Applied Scientist** and **Adobe MLE** are **DSA + transformer math**. Do not prep as if they are the same job.

2. **A resume line “RAG chatbot (LangChain)” will be dissected.**  
   Wipro asked **chunk size and why**. TCS asked vector-DB tradeoffs and how to improve a QA bot. Tiger asked **index updates**. Capgemini asked **cross-tenant leakage**. Infosys L1 (second-hand) asked **rate limits, caching, streaming, logging failures**. If those answers are not lived, the review pattern is rejection or “superficial embeddings” (Banerjee).

3. **Agents are no longer optional even at 1 YOE Deloitte.**  
   The Dec 2024 Deloitte candidate with 1 year was already asked agents and told to study LangGraph. Cognizant Mar 2026 R1 was “how to create, orchestrate agents.” Fractal asked LangGraph + MCP. **INFERENCE:** An 8.5 YOE candidate who cannot explain ReAct/tool-calling/memory vs a chatbot will look junior relative to 2025–2026 services bars.

4. **Python must be fluent, not LeetCode-hard.**  
   Recurring live tasks: even/odd, prime, second-largest, args/kwargs, list/dict comprehensions, decorators, OOP, 3-sum (Tiger), optimized string/list (Money Forward). **INFERENCE:** 20–40 hours of Python (collections, files, HTTP, pandas-light) is better ROI than 200 LC hards **unless** the JD is Fractal DS OA or Adobe MLE.

5. **Do not skip classical ML entirely.**  
   Infosys “Gen AI Engineer” asked KNN/K-means. Deloitte asked F1 and imbalanced data. Fractal R1 asked optimizers and gradient descent. Wipro asked BERT. **INFERENCE:** A 2-page cheat sheet (precision/recall/F1, overfitting, transformers at a block-diagram level) prevents a title-mismatch fail.

6. **HR will ask notice and CTC; they may not ask “why support.” Prepare it anyway.**  
   Verified: notice + salary (Infosys). Verified: why change (Tiger). Unverified but high-risk: “are you a developer?” **INFERENCE:** Answer as **ITSM domain expert automating the queue you already own** (ticket classification, runbook RAG, major-incident summarisation), not as “I want to escape support.” ServiceNow asked *deployers* about job repercussions — a support lead who can talk **human-in-the-loop** and **change management** has a rare authentic story.

7. **Client rounds are the hidden bar.**  
   Deloitte and Wipro both show internal pass → client fail. **INFERENCE:** Practice a 10-minute design of “ITSM copilot for L1 agents” covering data residency, hallucination, citations, fallback to human, cost per ticket — that is the Infosys L2 / Deloitte client shape.

8. **Portfolio > certificates.**  
   Financial Express (17 Jul 2026) quotes recruiter Chandra: “Build one serious end-to-end AI system and prepare to defend every decision.” That article is **SECONDARY** as a question source, but it matches Infosys L1 and Wipro client behaviour. **INFERENCE:** One ITSM RAG with evals beats five Udemy badges.

9. **Conversion is low even when calls are high.**  
   Arsh Goyal’s switcher: 40 GenAI interviews → 2 offers. Deloitte public n=4 all no-offer. **INFERENCE:** Plan a **volume** of services/analytics loops, not one “dream GCC AS” loop.

10. **AIOps-titled roles: do not wait for a public question bank.**  
    Insufficient evidence. **INFERENCE:** Walk in with **incident taxonomy, SLO language, runbook structure, and a prototype that classifies/summarises tickets**, then map interviewer questions onto the verified RAG/agent list.

---

## Evidence gaps

1. **Zero named Service Desk / ITSM Lead → GenAI IC interview transcripts** in this research window. Transition Qs in the brief (support, 11 LPA, “are you a developer?”, coding gap) are **not documented**.  
2. **AIOps / LLMOps / MLOps dedicated loops:** almost no first-person India 2024–2026 question lists. Money Forward R3 “LLMOps” is the clearest labeled round; content not itemized beyond projects.  
3. **8–12 YOE specifically:** Fractal Gen AI Engineer (6-month process, LangGraph, live Python) and Tiger Senior AI Engineer (RAG + k8s + DL) are the closest. Most Glassdoor GenAI reviews look **1–5 YOE**. Deloitte client/partner rounds may be the 6–12 YOE shape, but the published reviews are thin.  
4. **Google India, Freshworks GenAI IC, Zoho GenAI, Publicis Sapient GenAI, Thoughtworks AI Engineer question-level India reviews:** insufficient.  
5. **Prompt injection, hybrid search (BM25+dense), Azure OpenAI vs Bedrock as explicit interview Qs:** not found in named reviews (Bedrock/Azure appear in JDs).  
6. **Take-home multi-day assignments** for services GenAI: not found; live RAG build is community-only (one Reddit report).  
7. **Salary discussion scripts** beyond “HR asked salary expectations / notice period”: not found.  
8. **Glassdoor/AmbitionBox/Reddit full-page access** was blocked for many URLs; some items depend on **search snippets**. Snippets can truncate. Where a Taro mirror or LinkedIn full text existed, that was preferred.  
9. **Selection bias:** public reviews over-represent rejects and juniors. Fractal “accepted offer” and Money Forward “accepted offer” are useful counters.  
10. **SECONDARY blogs** (Dataford “every question Cognizant asks”, Learnbay 50 Qs, CloudSoft 110 Azure Qs, DataCamp 36 Qs) were **not** mixed into the numbered bank. They systematically invent or genericize.

---

## Source appendix

### Named first-person / dated company reviews (primary)

1. Shanmukha Sai Srinivas Nunna — TCS GenAI Developer Interview Experience. LinkedIn, ~Jun 2025. https://www.linkedin.com/posts/shanmuknunna_genai-tcs-interviewexperience-activity-7336343348636545025-1tG7  
2. Arunabha Sarkar (Banerjee) — Infosys GenAI Developer L1/L2 (friend’s interview). LinkedIn, ~Feb 2026. https://www.linkedin.com/posts/arunabha-sarkar-alex_infosysinterview-genaiinterview-llmengineering-activity-7427924490401103872-e3y0  
3. Deloitte Gen AI Engineer, India, 1 Dec 2024 (agents, RAG, even/odd, chunking). Taro: https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-india-december-1-2024-no-offer-negative-6302fac4/  
4. Deloitte Gen AI Engineer, Bengaluru, 1 Jun 2025 (RAG vs Agent, big RAG). Taro: https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-bengaluru-karnataka-june-1-2025-no-offer-positive-5eb74f34/  
5. Deloitte Gen AI Engineer, Bengaluru, 1 Apr 2025 (4 rounds, client fail). Taro: https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-bengaluru-karnataka-april-1-2025-no-offer-neutral-7ea08313/  
6. Deloitte Gen AI Engineer, India, 1 Dec 2024 (one-bit quantization). Taro: https://www.jointaro.com/interviews/companies/deloitte/experiences/gen-ai-engineer-india-december-1-2024-no-offer-negative-2c45121c/  
7. Capgemini Gen AI Engineer, India, 23 Sep 2025. Taro: https://www.jointaro.com/interviews/companies/capgemini/experiences/gen-ai-engineer-india-september-23-2025-no-offer-negative-d93e7716/  
8. Capgemini Gen AI Engineer, Hyderabad, 29 Mar 2025. Taro: https://www.jointaro.com/interviews/companies/capgemini/experiences/gen-ai-engineer-hyderabad-march-29-2025-declined-offer-positive-ed8bdb1e/  
9. Capgemini Gen AI Engineer, Mumbai, 19 Mar 2025. Taro: https://www.jointaro.com/interviews/companies/capgemini/experiences/gen-ai-engineer-mumbai-march-19-2025-accepted-offer-positive-e201b3f2/  
10. IBM AI Engineer, Bengaluru, 1 Feb 2025. Taro: https://www.jointaro.com/interviews/companies/ibm/experiences/ai-engineer-bengaluru-february-1-2025-no-offer-positive-c881d31a/  
11. IBM India SDE campus, Sep 2025 (RAG on resume). GFG: https://www.geeksforgeeks.org/interview-experiences/ibm-india-interview-experience-for-software-developer-on-campus/  
12. Adobe Senior Backend Engineer Python/Gen AI, Noida, 2026. LeetCode Discuss: https://leetcode.com/discuss/post/8317558/adobe-interview-experience-senior-backen-7zp1/  
13. Abhinaba Banerjee — failed AI Engineer interview, then built zero-egress RAG. Medium, 3 Apr 2026. https://medium.datadriveninvestor.com/from-losing-an-ai-engineer-interview-to-architecting-a-zero-egress-enterprise-rag-pipeline-a258f9d3ea94  

### Glassdoor / AmbitionBox (company interview pages and QTN IDs)

14. Glassdoor India — Generative AI Engineer questions: https://www.glassdoor.co.in/Interview/india-generative-ai-engineer-interview-questions-SRCH_IL.0,5_KO6,28.htm  
15. Glassdoor India — Gen AI Engineer questions (166 Qs): https://www.glassdoor.co.in/Interview/india-gen-ai-engineer-interview-questions-SRCH_IL.0,5_KO6,21.htm  
16. Glassdoor — Genai engineer questions (Capgemini transformer / RAG eval; ServiceNow architect): https://www.glassdoor.co.in/Interview/genai-engineer-interview-questions-SRCH_KO0,14.htm  
17. Infosys Gen AI Engineer: https://www.glassdoor.com/Interview/Infosys-Gen-AI-Engineer-Interview-Questions-EI_IE7927.0,7_KO8,23.htm  
18. Infosys GenAI Engineer AmbitionBox: https://www.ambitionbox.com/interviews/infosys-interview-questions/genai-engineer  
19. Infosys interviews (includes “Advanced dsa more than 6 questions”): https://www.ambitionbox.com/interviews/infosys-interview-questions  
20. Accenture Gen AI developer Qs: https://www.glassdoor.com/Interview/I-had-appplied-for-Gen-AI-developer-position-Below-were-the-question-asked-What-is-agentic-ai-and-ai-agents-Which-is-b-QTN_8348946.htm  
21. Accenture RAG/LLM: https://www.glassdoor.com/Interview/Q-What-is-RAG-LLM-based-Learning-QTN_7836327.htm  
22. Accenture RAG pipeline: https://www.glassdoor.com/Interview/Question-on-Gen-AI-RAG-pipeline-was-asked-Follow-up-questions-on-projects-QTN_8719740.htm  
23. Accenture RAG full form / Responsible AI: https://www.glassdoor.com/Interview/Explain-what-you-have-done-in-AI-ML-explain-how-it-works-What-is-RAG-full-form-in-GenAI-What-is-Responsible-AI-How-QTN_7354214.htm  
24. Accenture AI ML Engineer India: https://www.glassdoor.co.in/Interview/Accenture-AI-ML-Engineer-Interview-Questions-EI_IE4138.0,9_KO10,24.htm  
25. Capgemini GenAI engineer Gurgaon Dec 2025: https://www.glassdoor.co.in/Interview/Capgemini-Interview-E3803-RVW101720117.htm  
26. Cognizant Generative AI developer: https://www.glassdoor.co.in/Interview/Cognizant-Generative-AI-developer-Interview-Questions-EI_IE8014.0,9_KO10,33.htm  
27. Cognizant Gen AI Engineer: https://www.glassdoor.com/Interview/Cognizant-Gen-AI-Engineer-Interview-Questions-EI_IE8014.0,9_KO10,25.htm  
28. Wipro Gen AI Engineer: https://www.glassdoor.com/Interview/Wipro-Gen-AI-Engineer-Interview-Questions-EI_IE9936.0,5_KO6,21.htm  
29. Wipro AI ML Engineer: https://www.glassdoor.com.au/Interview/Wipro-AI-ML-Engineer-Interview-Questions-EI_IE9936.0,5_KO6,20.htm  
30. IBM AI Engineer: https://www.glassdoor.co.in/Interview/IBM-AI-Engineer-Interview-Questions-EI_IE354.0,3_KO4,15.htm  
31. GlobalLogic GenAI engineer: https://www.glassdoor.com/Interview/GlobalLogic-GenAI-engineer-Interview-Questions-EI_IE23009.0,11_KO12,26.htm  
32. Tiger Analytics AI Engineer: https://www.glassdoor.com/Interview/Tiger-Analytics-AI-Engineer-Interview-Questions-EI_IE717029.0,15_KO16,27.htm  
33. Tiger Analytics Senior AI Engineer: https://www.glassdoor.com/Interview/Tiger-Analytics-Senior-AI-Engineer-Interview-Questions-EI_IE717029.0,15_KO16,34.htm  
34. Fractal Gen AI Engineer: https://www.glassdoor.co.in/Interview/Fractal-Gen-AI-Engineer-Interview-Questions-EI_IE270403.0,7_KO8,23.htm  
35. Fractal Sr Data Scientist Generative AI: https://www.glassdoor.com/Interview/Fractal-Sr-Data-Scientist-Generative-AI-Interview-Questions-EI_IE270403.0,7_KO8,39.htm  
36. Fractal Senior Data Scientist: https://www.glassdoor.ca/Interview/Fractal-Senior-Data-Scientist-Interview-Questions-EI_IE270403.0,7_KO8,29.htm  
37. Money Forward Generative AI Engineer, Chennai: https://www.glassdoor.ie/Interview/Money-Forward-Generative-AI-Engineer-Interview-Questions-EI_IE3841421.0,13_KO14,36.htm  
38. Techolution Generative AI Engineer: https://www.glassdoor.co.in/Interview/Techolution-Generative-AI-Engineer-Interview-Questions-EI_IE1397522.0,11_KO12,34.htm  
39. ServiceNow GenAI Architect: https://www.glassdoor.com/Interview/ServiceNow-GenAI-Architect-Interview-Questions-EI_IE403326.0,10_KO11,26.htm  
40. ServiceNow repercussions Q: https://www.glassdoor.com/Interview/Did-I-have-to-deal-with-repercussions-of-deploying-AI-like-to-job-training-or-org-QTN_8234637.htm  
41. Amazon Applied Scientist: https://www.glassdoor.co.nz/Interview/Amazon-Applied-Scientist-Interview-Questions-EI_IE6036.0,6_KO7,24.htm  
42. Microsoft Applied Scientist / AS II: https://www.glassdoor.co.in/Interview/Microsoft-Applied-Scientist-Interview-Questions-EI_IE1651.0,9_KO10,27.htm  
43. Adobe interviews (MLE Bengaluru Apr 2026): https://www.glassdoor.co.in/Interview/Adobe-Interview-Questions-E1090.htm  
44. Accenture AI ML Engineer AmbitionBox (RAG Q ~1 week before 24 Jul 2026 crawl): https://www.ambitionbox.com/interviews/accenture-interview-questions/ai-ml-engineer  

### Community

45. Arsh Goyal, X, 1 May 2026 — services → GenAI switch, 40 interviews, 2 offers: https://x.com/arsh_goyal/status/2050260640514871368  
46. r/developersIndia — first switch / market trend (GenAI = RAG discussion): https://www.reddit.com/r/developersIndia/comments/1syby35/doing_my_first_switch_and_sharing_current_market/  
47. r/developersIndia — ML interviews compilation (live RAG build; IDFC DSA+GenAI): https://www.reddit.com/r/developersIndia/comments/1q065gd/my_ml_engineer_interviews_compilation_along_with/  
48. r/developersIndia — after 36 interviews (RAG flow: tokens, chunking, embeddings, rerank judges): https://www.reddit.com/r/developersIndia/comments/1virlnf/after_36_technical_interviews_i_finally_bagged_an/  
49. r/dataengineersindia — Tiger Analytics AI Engineer: https://www.reddit.com/r/dataengineersindia/comments/1telohg/tiger_analytics_ai_engineer_interview/  
50. r/indiafreshers — RAG/LangGraph then reverse linked list: https://www.reddit.com/r/indiafreshers/comments/1sux4jn/16_months_of_learning_aiml_finally_getting/  
51. r/IndianEngineers — RAG interview Q GitHub pointer (repo, not company): https://www.reddit.com/r/IndianEngineers/comments/1pryhv4/rag_interview_questions_and_answers_useful_for  
52. Glassdoor Tech India forum — M.Tech AI/ML limited experience rejections: https://www.glassdoor.com/Community/tech-india/hi-everyone-my-experience-10-months-with-an-m-tech-background-in-aiml-for-the-past-6-months-i-have-been-applying-for-data-scientist  

### Policy / hiring-signal (not question banks)

53. Thoughtworks India application process / GenAI policy: https://www.thoughtworks.com/en-in/careers/our-process  
54. Infosys GenAI / Agentic AI Engineer JD (Python, Bedrock, RAG, LangGraph): Glassdoor job listing jl=1010157961831  
55. Accenture AI/API Engineer Agentic AI Solutions Manager, Bengaluru JD: Glassdoor jl=1010123827269  

### SECONDARY blogs (not used as “Company X asked Q”)

56. DataCamp — Top 36 Generative AI Interview Questions (updated Dec 2025): https://www.datacamp.com/blog/genai-interview-questions  
57. IGotAnOffer — Generative AI System Design Interview: https://igotanoffer.com/en/advice/generative-ai-system-design-interview  
58. Financial Express — AI interview questions for Indian professionals abroad, 17/20 Jul 2026 (Chandra sample: design support assistant 1M queries/month): https://www.financialexpress.com/world-news/nri/ai-interview-questions-for-indian-professionals-seeking-jobs-abroad/4294866/  
59. Dataford company “guides” (Cognizant/Infosys/Accenture/Tiger) — generic extracted topics, **not first-person**.  
60. CloudSoft Azure/GCP AI interview Qs, 18 Aug 2026 — coaching content.  
61. Learnbay LinkedIn Pulse — GenAI & Agentic AI Interview Questions 2026 Edition.  
62. Analytics Vidhya — 40 RAG Interview Questions, Feb 2026.  
63. jobsbyculture — 50+ AI Engineer Interview Questions 2026.  
64. CampusX YouTube — “How Do You Evaluate Your RAG App?” as **the #1 GenAI interview question** (coaching, 6 Aug 2026).  

---

*End of A5. No questions in the numbered bank were invented. Where evidence was missing (AIOps scripts, support-transition HR, Azure vs Bedrock as an asked question), the gap is stated rather than filled.*
