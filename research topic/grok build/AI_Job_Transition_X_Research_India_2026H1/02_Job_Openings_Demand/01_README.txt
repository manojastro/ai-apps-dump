01_README — Folder 02 Job openings / demand
Date window: 2026-03-11 to 2026-09-11. Queries: since:2026-03-11 until:2026-09-12.
Research date: 2026-09-11. Source: public X only.

HOW X-PROXY % WAS CALCULATED
- Collected India hiring posts that name a company (or clearly unnamed-but-real req) + role + India location.
- Mapped each to one of 8 primary roles.
- Excluded intern-only posts from the percentage denominator.
- Deduped by (company, primary role) so Bolna's two Solutions Engineer posts count once, Infosys bundle is one AI Security row, etc.
- Denominator in this scrape = 49 distinct company+role pairs.
- Raw actual-opening posts before intern filter / before company+role dedup = 50 (see Distinct_Hiring_Posts).
- Label every percentage X-proxy. This is NOT official market share.

QUERIES USED (native then semantic)
Hiring pack from the brief (min_faves then dropped when thin):
1. ("AIOps Engineer" OR "AI Ops" OR AIOps) (hiring OR "we're hiring" OR "open role" OR opening) (India OR Bengaluru OR Bangalore OR Hyderabad OR Chennai OR Pune OR Coimbatore) min_faves:5
2. Same AIOps query without min_faves
3. ("Cloud AI Engineer" OR "Azure AI" OR "GCP AI Engineer") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5  → ZERO HITS
4. Widened: ("Azure AI" OR "Azure OpenAI" OR "Cloud AI" OR "GCP AI" OR "Vertex AI") (hiring) (India OR Bengaluru OR Bangalore OR Hyderabad OR Chennai)
5. ("Intelligent Automation" OR "AI automation engineer" OR "automation + AI") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5
6. ("n8n" OR UiPath OR "Power Automate" OR "intelligent automation") (hiring OR job OR engineer) (India OR Bengaluru OR Hyderabad OR Chennai)
7. ("AI Security Engineer" OR "GenAI security" OR "AI governance") (hiring OR "open role") (India OR Bengaluru OR Hyderabad) min_faves:5
8. ("prompt injection" OR guardrails OR "AI security") (hiring OR engineer OR job) (India OR Bengaluru OR Hyderabad)
9. ("Forward Deployed Engineer" OR FDE OR "AI deployment engineer" OR "forward deployed") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5
10. ("Agentic AI" OR "GenAI Engineer" OR "AI Engineer") (hiring OR "we're hiring" OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai OR Pune) min_faves:10
11. ("AI Solutions Engineer" OR "AI Solutions Architect" OR "GenAI architect") (hiring OR "open role") (India OR Bengaluru OR Hyderabad OR Chennai) min_faves:5
12. ("AI Solutions Architect" OR "Applied AI Architect" OR "GenAI architect" OR "AI architect") (hiring OR "we're hiring") (India OR Bengaluru OR Hyderabad OR Chennai)
13. ("LangGraph" OR FastAPI OR Langfuse OR "Azure AI Foundry") (hiring OR "we're hiring") (Bengaluru OR Bangalore OR Hyderabad OR Chennai OR India) min_faves:5
14. ("8 years" OR "8 yrs" OR "8+ years" OR "10 years") ("AI engineer" OR AIOps OR agentic OR GenAI) (India OR interview OR offer) min_faves:5
15. ("broke into AI" OR "transitioned to AI" OR "moved to AI" OR "from support to AI" OR "service desk to AI" OR "ITSM to AIOps") (India OR Indian OR Bengaluru OR Hyderabad) min_faves:10 -filter:replies
16. Semantic: India hiring AIOps / FDE / Solutions Architect / Cloud AI 2026

CONFIDENCE
- FDE and GenAI/Agentic actual posts: MEDIUM (many aggregator copies; several first-hand: OpenAI @arjun_gupta95, Lyzr, BytePlus @ayushpranav3, Aman @kapoor015, Manali @mange_manali).
- Cloud AI titled "Cloud AI Engineer": LOW. Azure/GCP GenAI JDs exist via aggregators.
- AIOps Engineer mid-senior: LOW.
- AI Security / Solutions Architect: LOW-MEDIUM, few posts.
- Switcher 8 YOE Service Desk→AI: INSUFFICIENT X evidence.

WHAT IS MISSING
See Gaps sheet. Do not fill with training memory or Naukri counts.
