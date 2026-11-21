# Aegis Plan India — Architecture

Educational research and financial-planning simulator. Not a broker. Not a SEBI-registered adviser. No execution endpoints exist.

```mermaid
flowchart TD
  UI[Next.js research desk] --> API[FastAPI]
  API --> Auth[Session / household abstraction]
  API --> IPS[IPS service]
  API --> Hold[Holdings + PII redactor]
  API --> Reg[Regulatory snapshot]
  API --> Mkt[Market data service]
  API --> Eng[Deterministic engine]
  API --> Graph[LangGraph orchestrator]
  API --> Risk[Risk policy engine]
  API --> Stress[Stress engine]
  API --> Cmp[Plan comparison]
  API --> PDF[ReportLab PDF]
  API --> Audit[Audit trail]
  API --> Jobs[Job / progress]
  Graph --> FC[Firecrawl v2 adapter]
  FC --> Cache[URL+schema+parser cache]
  FC --> Allow[Hostname allowlist]
  Eng --> Policy[Versioned rules.py]
```

## Deterministic vs LLM

Python owns arithmetic, weights, caps, eligibility, tax thresholds after retrieval, loan math, emergency reserve, stress, vetoes, constraints, percentages, and source coverage.

The LLM owns summarization, explanation, research synthesis, and failure-mode narrative. It cannot override a veto or invent rates.

## LangGraph

```mermaid
flowchart TD
  Onboard[Onboarding] --> Profile[Profile Analyst]
  Profile --> Holdings[Holdings Analyst]
  Holdings --> PII[PII redaction - Python]
  PII --> Reg[Regulatory Research]
  Reg --> Macro[Macro Research]
  Macro --> Univ[Universe Research]
  Univ --> Cons[Construction]
  Cons --> Det[Deterministic validation]
  Det --> Risk[Risk Officer]
  Risk -->|veto once| Cons
  Risk --> Critic[Plan Critic]
  Critic --> Compare[Compare]
  Compare --> Select[User selects]
  Select --> FAP[Financial Action Plan]
  FAP --> PDF[PDF]
```

## Provenance

Every numerical fact carries value, unit, source URL, tier, published/fetched/as-of, confidence, and verification. Freshness: market ≤ 24h preferred, bank/post-office rates ≤ 7 days, regulatory rules verified for current applicability. Stale, unverified, and conflicting states are labelled. Conflicts are never silently resolved.

## Regulatory snapshot

`app/regulatory/` builds a dated snapshot before tax- or NPS-sensitive output. Live mode should scrape allowlisted official pages via Firecrawl v2. Mock mode loads fixtures labelled MOCK/DEGRADED and still points at official homepages.

## Security

Scraped pages are untrusted. Prompt-injection phrases are detected and never treated as instructions. PII redaction is deterministic Python. Secrets stay in environment variables.
