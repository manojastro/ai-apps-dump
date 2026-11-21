# 03 — Tech Stack Brief (current as of 2026-09-15)

**Access date:** 2026-09-15  
**Audience:** FDE / GenAI / agentic engineering career handbook  
**Method:** Official docs and specs preferred; dates taken from the page or publisher when present. Claims without a date are marked. Third-party aggregators are used only as supporting context and labeled **UNCERTAIN** if they conflict with vendor docs.

**Label legend**

| Label | Meaning |
| --- | --- |
| **FACT** | Stated by official docs, specs, or vendor product pages |
| **RECOMMENDATION** | Curriculum advice for FDE/GenAI roles |
| **UNCERTAIN** | Conflicting, undated, or third-party-only; do not treat as product truth |
| **MARKET OBSERVATION** | Hiring-pattern note, not a universal law |

Do not treat Chat Completions, Assistants API, AutoGen, or “Azure AI Studio” as current default names. Those still appear in older tutorials.

---

## 1. Models and providers

### 1.1 OpenAI

**Start here for new API work:** Responses API (`POST /v1/responses`). Chat Completions remains supported; Responses is recommended for all new projects.

**Source:** “Migrate to the Responses API,” OpenAI, https://developers.openai.com/api/docs/guides/migrate-to-responses, accessed 2026-09-15.

**Current flagship lineup (official Models page)**

| Marketing name | Model ID | Role | Input / output (per 1M tokens) | Context | Knowledge cutoff | Reasoning effort |
| --- | --- | --- | --- | --- | --- | --- |
| GPT-6 Astra | `gpt-6-astra` | Hardest end-to-end work | $10 / $50 | 1.05M | Apr 30, 2026 | `low` `medium` `high` `xhigh` `max` |
| GPT-5.6 Sol | `gpt-5.6-sol` (alias `gpt-5.6`) | Flagship professional work | $4 / $20 | 1.05M | Feb 16, 2026 | `none` `low` `medium` `high` `xhigh` `max` |
| GPT-5.6 Terra | `gpt-5.6-terra` | Intelligence / cost balance | $2 / $12 | 1.05M | Feb 16, 2026 | same as Sol |
| GPT-5.6 Luna | `gpt-5.6-luna` | Cost-sensitive high volume | $0.20 / $1.20 | 1.05M | Feb 16, 2026 | same as Sol |

**FACT:** OpenAI’s Models page says: if unsure, use GPT-6 Astra; use GPT-5.6 Terra to balance intelligence and cost, GPT-5.6 Luna for cost-sensitive high-volume workloads. Latest models support text and image input, text output, multilingual, and vision. Available via Responses API and client SDKs.

**Source:** “Models,” OpenAI, https://developers.openai.com/api/docs/models, accessed 2026-09-15.

Specialized models also listed on that page (do not confuse with the text flagship): GPT-5.6 Cyber / Daybreak (authorized cybersecurity), GPT-Rosalind (life sciences, approved orgs), GPT-Image-2.5 Sunburst/Flare, GPT-Live 1, GPT-Realtime-2.1 family, transcription/TTS models.

**Responses API (current primitive)**

**FACT:** Responses is “an evolution of Chat Completions” with:

- Built-in tools: web search, file search, computer use, code interpreter, remote MCP
- Multi-turn via `previous_response_id` or Conversations API; default storage (`store: true`)
- Agentic loop in one request (model can call multiple tools)
- Structured items (`message`, `function_call`, `function_call_output`, `reasoning`) instead of glued Chat Completions messages
- Structured Outputs via `text.format` (not `response_format`)
- Function tools are internally tagged (`type: function` + `name` at top level)
- Streaming uses typed SSE events (`response.output_text.delta`, etc.)

OpenAI claims internal evals: ~3% SWE-bench improvement vs Chat Completions with same prompt; 40–80% better cache utilization vs Chat Completions. Treat those as vendor-reported, not independently verified.

**FACT:** Starting with GPT-5.4, Chat Completions does not support tool calling with `reasoning_effort` values other than `none`. Reasoning models work better on Responses.

**Sources:**

- “Migrate to the Responses API,” OpenAI, https://developers.openai.com/api/docs/guides/migrate-to-responses, accessed 2026-09-15
- “Using tools,” OpenAI, https://developers.openai.com/api/docs/guides/tools, accessed 2026-09-15

**Tools (Responses / Agents)**

Official tool catalog includes: function calling, web search, file search, remote MCP, skills, shell, computer use, image generation, tool search, programmatic tool calling, apply patch, local shell, code interpreter.

**FACT:** Only `gpt-5.4` and later support `tool_search`. Tool search + `defer_loading` loads deferred tool definitions at runtime. Remote MCP is a first-class `type: "mcp"` tool with `server_url` / `server_label`.

There is also a managed **Agents API** (OpenAI-hosted harness with sessions, sandboxes, MCP connections, plugins, vaults, multi-agent) and an **Agents SDK** (runs in your app). Compare runtimes on the Agents overview; do not treat Agent Builder / Assistants as the current default.

**Source:** “Using tools,” OpenAI, https://developers.openai.com/api/docs/guides/tools, accessed 2026-09-15.  
**Source:** “Agents SDK,” OpenAI, https://developers.openai.com/api/docs/guides/agents/sdk, accessed 2026-09-15.

**Structured Outputs**

**FACT:** Structured Outputs constrain the model to a supplied JSON Schema. Two forms: (1) function calling strict mode, (2) `text.format` with `type: json_schema`. JSON mode (`json_object`) only guarantees valid JSON, not schema adherence. OpenAI recommends Structured Outputs over JSON mode. Available starting GPT-4o snapshots; for new projects start with `gpt-6-astra`. Python/JS helpers: `responses.parse()` with Pydantic / Zod.

**Source:** “Structured model outputs,” OpenAI, https://developers.openai.com/api/docs/guides/structured-outputs, accessed 2026-09-15.

**Prompt caching**

**FACT:** Enabled by default for supported models. Cache stores KV tensors of a matching prompt **prefix**, not the tokens. Cached input discounted up to 90%.

GPT-5.6 and later:

- Min cacheable prefix: 1,024 visible input tokens
- Cache write: 1.25× uncached input; cache read: 0.1×
- Modes: `prompt_cache_options.mode` = `implicit` (default-like automatic breakpoint) or `explicit` (developer `prompt_cache_breakpoint`)
- Up to four cache writes per request
- TTL control: `prompt_cache_options.ttl` = `"30m"` (only supported value; default)
- `prompt_cache_key` optional (accounting / anti-probing), not required for routing

Earlier models: implicit breakpoints only; `prompt_cache_key` used for routing; `prompt_cache_retention` `in_memory` or `24h` (model-dependent). Caches are org- and region-scoped, machine-local.

**Source:** “Prompt caching,” OpenAI, https://developers.openai.com/api/docs/guides/prompt-caching, accessed 2026-09-15.

**Azure note:** Microsoft documents `gpt-6-astra` (2026-09-03) on Foundry with 1,050,000 context, 922k max input, 128k max output; tools on Responses only; Chat Completions without tools. Azure currently does not support mid-conversation `configuration_update` or `response.steer` for GPT-6 Astra.

**Source:** “Azure OpenAI reasoning models - GPT-6 Astra and GPT-5,” Microsoft Learn, https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning, updated ~2026-09-06, accessed 2026-09-15.

---

### 1.2 Anthropic Claude

**Start here:** Claude Opus 5 for most workloads; Claude Fable 5.1 for demanding reasoning / long-horizon agents when Opus 5 at higher effort is not enough.

**Source:** “Models overview,” Anthropic, https://platform.claude.com/docs/en/models/overview, accessed 2026-09-15.

| Model | API ID | Price in/out per MTok | Context | Max output | Thinking | Default effort | Knowledge cutoff |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Claude Fable 5.1 | `claude-fable-5-1` | $10 / $50 | 1M | 128K | Adaptive (always on) | `high` | Jun 2026 |
| Claude Opus 5 | `claude-opus-5` | $5 / $25 | 1M | 128K | Adaptive | `high` | May 2026 |
| Claude Sonnet 5 | `claude-sonnet-5` | $2 / $10 | 1M | 128K | Adaptive | `high` | Jan 2026 |
| Claude Haiku 4.5 | `claude-haiku-4-5-20251001` (alias `claude-haiku-4-5`) | $1 / $5 | 200K | 64K | Extended | not supported | Feb 2025 reliable / Jul 2025 training |

**FACT:** All current models support text+image in, text out, multilingual, vision, tool use. Batch API 50% off. Prompt cache reads are 10% of base input (2.5% on Fable 5.1 / Mythos 5.1). Dateless IDs from 4.6 generation onward are pinned snapshots. Extended thinking (`thinking.type=enabled` + `budget_tokens`) is deprecated on Opus 4.6 / Sonnet 4.6 and not accepted on later models; use adaptive thinking + `effort`.

Platform IDs: Bedrock `anthropic.claude-*`; Google Cloud same dateless IDs (Haiku dated `@20251001`); Microsoft Foundry uses Claude API IDs. Claude Platform on AWS uses Claude API IDs, not Bedrock-style IDs.

Legacy still listed: Fable 5, Opus 4.8 / 4.7 / 4.6 / 4.5, Sonnet 4.6 / 4.5. Retirement commitments (Anthropic-operated platforms): Fable 5.1 not sooner than 2027-09-01; Opus 5 not sooner than 2027-07-24; Sonnet 5 not sooner than 2027-06-30; Haiku 4.5 not sooner than 2026-10-15.

**Source:** “Models overview,” Anthropic, https://platform.claude.com/docs/en/models/overview, accessed 2026-09-15.  
**Source:** “How up-to-date is Claude's training data?,” Anthropic Help Center, https://support.claude.com/en/articles/8114494-how-up-to-date-is-claude-s-training-data, updated ~2026-09-01.

**Tool use**

**FACT:** Two execution sites:

- **Client tools:** your app executes; Claude returns `stop_reason: tool_use` + `tool_use` blocks; you return `tool_result`. Includes user-defined tools and Anthropic-schema tools (`bash`, `text_editor`, memory, computer use, browser use).
- **Server tools:** Anthropic executes (`web_search`, `web_fetch`, `code_execution`, `tool_search`, advisor). Default `tool_choice` is `auto`. Strict tool use: `strict: true` on custom tools. Tool Runner in SDKs can execute the loop for you.

Server tool example type string: `web_search_20260209`.

**Source:** “Tool use with Claude,” Anthropic, https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview, accessed 2026-09-15.

**MCP**

**FACT:** Messages API has an **MCP connector**: point at remote MCP servers (`mcp_servers` + `mcp_toolset` tool) without writing an MCP client. Also documented on Microsoft Foundry Claude deployments (structured outputs, web search, web fetch, MCP connector, tool search available on Azure-hosted Claude as of Aug 2026 blog).

**Source:** “Tool use with Claude,” Anthropic, https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview (MCP connector card), accessed 2026-09-15.  
**Source:** “From single call to agents…,” Microsoft Foundry Blog, https://devblogs.microsoft.com/foundry/five-new-claude-capabilities-now-available-in-foundry/, 2026-08-17.

Claude Managed Agents exist as a hosted toolset/session product; see Anthropic’s managed-agents docs rather than treating them as a replacement for the Messages API.

---

### 1.3 Google Gemini / Vertex / ADK

**Gemini API current text workhorses (Models page, last updated 2026-09-04)**

Stable Gemini 3 family:

- `gemini-3.8-flash` — “most intelligent Flash,” long-horizon SWE, autonomous agents, enterprise workflows (New Stable)
- `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`
- Image: Nano Banana 2 (`gemini-3.1-flash-image`), Nano Banana 2 Lite, Nano Banana Pro (`gemini-3-pro-image`)
- Preview: `gemini-3.1-pro-preview`, `gemini-3-flash-preview`, live/TTS/omni variants
- Gemini 2.5 still listed: `gemini-2.5-flash`, `gemini-2.5-flash-lite`, `gemini-2.5-pro`
- Tool/agent models: Computer Use (`gemini-2.5-computer-use-preview-10-2025`), Deep Research (`deep-research-preview-04-2026`), Antigravity Agent (`antigravity-preview-05-2026`)
- Embeddings: `gemini-embedding-2-preview` (multimodal), `gemini-embedding-001`

**FACT:** Gemini 2.0 Flash / Flash-Lite are shut down. Preview models may have billing and ≥2-week deprecation notice. `*-latest` aliases can hot-swap with 2-week notice for breaking changes.

**Source:** “Models,” Google AI for Developers, https://ai.google.dev/gemini-api/docs/models, last updated 2026-09-04, accessed 2026-09-15.

**Vertex / Gemini Enterprise Agent Platform**

Google Cloud docs now route many Vertex Generative AI pages into **Gemini Enterprise Agent Platform**. Vertex RAG Engine docs still list Gemini 3.1 Pro preview, Gemini 3 Flash preview, Gemini 2.5 Pro/Flash/Flash-Lite (as of 2026-05-29 page; banner says Vertex AI documentation is no longer being updated and points to Agent Platform).

**UNCERTAIN:** Exact current Vertex model IDs vs Gemini API IDs can lag; always check the Agent Platform model catalog for a given project/region.

**Sources:**

- “Google models,” Google Cloud, https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models, last updated 2026-09-03
- “Vertex AI RAG Engine supported models,” Google Cloud, https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/supported-rag-models, last updated 2026-05-29

**ADK (Agent Development Kit)**

**FACT:** Open-source, code-first framework (Python, Java, Go, TypeScript, Kotlin). PyPI `google-adk` 2.9.0 released 2026-09-10. ADK 2.0 has breaking changes vs 1.x (agent API, event model, session schema). Features: workflow runtime (graph, routing, fan-out, loops, HITL), Task API for agent-to-agent delegation, tools including MCP, Agent Config YAML, deploy to Cloud Run / Vertex AI Agent Engine. Model-agnostic though optimized for Gemini. Kotlin 1.0 GA announced 2026-09-09.

**Sources:**

- “Agent Development Kit,” Google Cloud, https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk, last updated 2026-09-03
- google-adk PyPI, https://pypi.org/project/google-adk/, released 2026-09-10
- ADK Python README, https://github.com/google/adk-python, accessed 2026-09-15
- “Announcing ADK for Kotlin 1.0,” Google Developers Blog, 2026-09-09

---

### 1.4 Meta Llama (and Muse)

**FACT (Llama 4, official Meta page):** Llama 4 is natively multimodal MoE.

- **Llama 4 Scout:** class-leading multimodal, single-H100 efficiency, **10M context**
- **Llama 4 Maverick:** stronger general multimodal / reasoning / coding

Official Llama 4 announcement (2025-04-05): Scout is 17B active / 16 experts; Maverick is 17B active / 128 experts; Behemoth (288B active / 16 experts) was a teacher still training at announcement. Models remain downloadable via Meta Llama downloads.

**Sources:**

- “Llama 4,” Meta, https://developer.meta.com/ai/models/llama-4/, accessed 2026-09-15
- “The Llama 4 herd,” Meta AI Blog, https://ai.meta.com/blog/llama-4-multimodal-intelligence/, 2025-04-05

**FACT (Meta site nav, 2026-09-15):** Meta’s current model family on developer.meta.com also lists **Muse Spark 1.3**, **Muse Glimmer**, **Muse Image**, **Muse Voice Transcribe** alongside Llama 4 and Llama 3. Muse is the newer Meta Superintelligence Labs line; Llama 4 remains the documented open Llama generation.

**UNCERTAIN (third-party, do not treat as Meta-official unless confirmed):** Reports that Meta shut down its first-party hosted Llama API on 2026-07-06; Muse Glimmer 30B Apache 2.0 (2026-08-10); Muse Spark proprietary. Confirm on https://developer.meta.com/ai/ and https://dev.meta.ai/docs/ before citing in interviews.

**RECOMMENDATION:** For FDE interviews, know Llama 4 Scout vs Maverick (open weights, multimodal, long context) and that enterprise serving is typically Bedrock / Together / Fireworks / self-host (vLLM/SGLang), not “the Meta Llama API.”

---

### 1.5 Mistral

**FACT (Mistral Docs featured models):**

- **Mistral Large 3** (`mistral-large-2512`), Apache 2.0, GA v25.12, 675B total / 41B active MoE, multimodal, ~256k context, official list price $0.50 / $1.50 per MTok. Features: chat, function calling, agents, built-in tools, structured outputs, OCR/document QnA.
- **Mistral Medium 3.5** (`mistral-medium-3-5`), v26.04, Modified MIT, frontier-class multimodal for agentic/coding, `reasoning_effort` parameter. Changelog: released 2026-04-27.
- **Mistral Small 4**, Apache 2.0, v26.03, hybrid instruct/reasoning/coding.
- **Ministral 3** 3B / 8B / 14B (2512), compact vision-capable, Apache 2.0.

Magistral (reasoning) Small/Medium 1.2 are on deprecation paths toward Medium 3.5 / Small 4 (retirement windows through mid/late 2026 per Mistral changelog table).

**Sources:**

- “Mistral Large 3,” Mistral Docs, https://docs.mistral.ai/models/mistral-large-3-25-12, accessed 2026-09-15
- “Changelog,” Mistral Docs, https://docs.mistral.ai/resources/changelogs, accessed 2026-09-15
- “Model Selection Guide,” Mistral Docs, https://docs.mistral.ai/models/model-selection-guide, accessed 2026-09-15

---

### 1.6 Qwen (Alibaba Cloud Model Studio)

**FACT (Alibaba Cloud Model Studio text-generation docs, updated 2026-09-11):** Recommended coding-tool models: `qwen3.7-plus` (balanced, full tool calling, 1M context); strongest reasoning `qwen3.8-max`. Table of current IDs includes `qwen3.8-max`, `qwen3.8-max-0902`, `qwen3.8-flash`, `qwen3.7-plus`, `qwen3.7-flash` — all 1M context, thinking mode, function calling, built-in tools, structured output. Older Qwen3 (`qwen3-max`, `qwen3-235b-a22b*`) still listed at 256k.

**Source:** “Text generation models - Qwen, DeepSeek, GLM,” Alibaba Cloud Model Studio, https://www.alibabacloud.com/help/en/model-studio/text-generation-model/, last updated 2026-09-11.

Open-weight Qwen3.x variants are widely hosted; confirm license (some large Max weights have commercial-revenue clauses) before enterprise redistribution. **UNCERTAIN:** Wikipedia/aggregators describe Qwen3.8-2.4T-A95B open weights (Aug 2026); use Model Studio IDs above for API work.

---

### 1.7 Cohere

**FACT (Cohere Models overview):**

Command family (Chat endpoint, RAG/tool/agents): `command-a-plus-05-2026` (first Command MoE, vision + agentic + translation, 128k / 64k out), `command-a-03-2025` (256k / 8k out), `command-r7b-12-2024`, `command-a-translate-08-2025`, `command-a-reasoning-08-2025` (256k / 32k), `command-a-vision-07-2025`. Older Command R / R+ 03/04-2024 **deprecated 2025-09-15**.

Also live: North Small Translate / North Mini Code (Model Vault for production), Embed `embed-v4.0` (text+image+PDF, 256–1536 dims, 128k), Rerank `rerank-v4.0-pro` and `rerank-v4.0-fast` (32k, multilingual + JSON), Parse `parse-v5.0`, Transcribe `cohere-transcribe-03-2026`, Aya Expanse/Vision 32B and Tiny Aya.

Platforms: Cohere API, SageMaker, Bedrock, Azure/Foundry, Oracle GenAI. Command A+ Bedrock ID listed N/A on Cohere’s platform table as of this page.

**Source:** “An Overview of Cohere's Models,” Cohere, https://docs.cohere.com/docs/models, accessed 2026-09-15.

---

### 1.8 AWS Bedrock + AgentCore + Guardrails + Knowledge Bases

**Bedrock** remains the multi-model inference plane (Anthropic, Meta, Mistral, Cohere, Amazon Nova, OpenAI-on-Bedrock, etc.). Model cards are region-specific; always check the account’s model catalog.

**AgentCore (official overview)**

**FACT:** AgentCore is an agentic platform to build/deploy/operate agents with any framework and FM. Core services (usable together or independently):

| Service | What it is |
| --- | --- |
| Harness | Managed agent loop: model + system prompt + tools in one API; isolated microVM with filesystem/shell |
| Runtime | Serverless runtime for agents/tools; session isolation; MCP and A2A; CrewAI, LangGraph, LlamaIndex, Google ADK, OpenAI Agents SDK, Strands |
| Memory | Short-term and long-term memory stores |
| Gateway | Convert APIs/Lambda/MCP into MCP tools with auth |
| Identity | Agent identity compatible with Cognito, Okta, Entra ID, Auth0 |
| Code Interpreter | Isolated Python/JS/TS sandbox |
| Browser | Managed browser for agent UI automation |
| Observability | OTEL-compatible traces; CloudWatch |
| Payments | x402 / MPP microtransactions |
| Evaluations | Session/trace/span evals for Strands or LangGraph |
| Optimization | Prompt/tool-description optimization + A/B via Gateway |
| Policy | Cedar (and Dogwood) policies on Gateway tool calls; Guardrails-as-provider |
| Registry | Catalog of agents, MCP servers, tools, skills |

**Source:** “What is Amazon Bedrock AgentCore?,” AWS, https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html, accessed 2026-09-15.

**Guardrails**

**FACT:** Configurable filters on inputs and model responses: content filters (Hate, Insults, Sexual, Violence, Misconduct, Prompt Attack), denied topics, word filters, sensitive-information (PII + regex), contextual grounding (RAG hallucination/relevance), automated reasoning checks. `ApplyGuardrail` API works with Bedrock models and self-hosted / third-party models. Can attach to agents, knowledge bases, and flows.

AgentCore Policy can invoke Guardrails at the Gateway perimeter (prompt attack, content filter, sensitive information; confidence 0–1). GA announcement 2026-06-17.

**Sources:**

- “Detect and filter harmful content by using Amazon Bedrock Guardrails,” AWS, https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html, accessed 2026-09-15
- “Guardrails in policies,” AgentCore, https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-guardrails-in-policies.html, accessed 2026-09-15
- “Amazon Bedrock AgentCore now supports Bedrock Guardrails in policy,” AWS What’s New, 2026-06-17

**Knowledge Bases**

**FACT:** Two types:

1. **Managed Knowledge Base** (recommended): AWS manages ingest/index/storage/retrieval; multimodal ingest; auto-scaling; agentic multi-hop retrieval; native AgentCore Gateway MCP tool; connectors (S3, SharePoint, Confluence, Google Drive, OneDrive, Web Crawler); **document-level ACL filtering** (except Web Crawler) at retrieval time; Smart Parsing; reranking; AgentCore Observability.
2. **Customer-managed:** you bring OpenSearch Serverless, Aurora (pgvector), Neptune, etc.

Also: structured data stores, Kendra GenAI index, Neptune graphs, image queries via multimodal embeddings, citations.

**Source:** “Retrieve data and generate AI responses with Amazon Bedrock Knowledge Bases,” AWS, https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html, accessed 2026-09-15.

---

### 1.9 Microsoft Foundry (current naming)

**FACT:** Product naming evolution:

Azure AI Studio → **Azure AI Foundry** → **Microsoft Foundry** (current).  
Azure Cognitive Services → Azure AI Services → **Foundry Tools** (current).  
Azure resource type remains `Microsoft.CognitiveServices/accounts`.

Two portals: **Foundry (classic)** and **Foundry (current)**. Banner toggle. Current portal shows **Foundry projects only**. Hub-based projects and standalone Azure OpenAI resources stay on classic until upgraded.

**Key migration dates (Microsoft Learn, updated 2026-09-11 / page updated 2026-09-14):**

- **2026-08-26:** `azure-ai-inference` package retires → use `openai` package
- **2026-08-26:** Assistants API sunsets → Microsoft Foundry Agents (Responses API / Agents v2)

Terminology: Assistants → Agent Versions; Threads → Conversations; Messages → Items; Runs → Responses; MaaS → Foundry Direct Models. SDK: `openai` + `azure-ai-projects` 2.x. Endpoint shape: `https://<project>.services.ai.azure.com/openai/v1`.

A2A: v1.0 GA in current portal; v0.3 Preview.

**Sources:**

- “Migrate from the Foundry (classic) portal,” Microsoft Learn, https://learn.microsoft.com/en-us/azure/foundry/how-to/navigate-from-classic, ms.date 2026-09-11, updated_at 2026-09-14
- “What is Microsoft Foundry (classic) portal,” Microsoft Learn, https://learn.microsoft.com/en-us/azure/foundry-classic/what-is-foundry, 2026-08-25

**AutoGen / Semantic Kernel / Agent Framework**

**FACT:** AutoGen GitHub README (accessed 2026-09-15): AutoGen is in **maintenance mode** (no new features; community-managed). New users should start with **Microsoft Agent Framework (MAF)**. Migration guide: https://learn.microsoft.com/en-us/agent-framework/migration-guide/from-autogen/

MAF: production-grade agents and multi-agent workflows in .NET and Python (`pip install agent-framework` / `Microsoft.Agents.AI` packages). Successor combining AutoGen orchestration + Semantic Kernel enterprise foundations. Foundry Agent Service is the hosted runtime; MAF is the SDK. Semantic Kernel Agent Framework docs still exist (ChatCompletionAgent, OpenAIResponsesAgent, AzureAIAgent) but Microsoft positions MAF as the path forward.

**Sources:**

- AutoGen README, https://github.com/microsoft/autogen, accessed 2026-09-15
- Microsoft Agent Framework README, https://github.com/microsoft/agent-framework, accessed 2026-09-15
- “Semantic Kernel Agent Framework,” Microsoft Learn, https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/, 2026-08-25
- “Transparency Note for Foundry Agent Service,” Microsoft Learn, 2026-08-24

---

## 2. Agent frameworks (production fit, not hype)

Compare on: control vs convenience, multi-agent, durability/HITL, observability, job-market signal, FDE fit.

| Framework | Strength | Weakness | State (2026-09) | Multi-agent | Production fit | Job-market signal |
| --- | --- | --- | --- | --- | --- | --- |
| **LangGraph** | Low-level graph orchestration; mix deterministic + agentic nodes; persistence, interrupts/HITL, streaming; named customers (Klarna, Uber, J.P. Morgan on official overview) | You design the graph; easy to over-abstract; LangChain version churn historically | Current core of LangChain Inc. OSS stack; pairs with LangSmith | Yes (graphs, subgraphs, Deep Agents harness) | High for long-running stateful agents | **Very high** in US agent/RAG JDs (MARKET OBSERVATION) |
| **LangChain** | Model/tool abstractions, prebuilt agent loops, huge integration catalog | Higher-level; historically leaky; many 2023 tutorials are obsolete | Current; agents sit on LangGraph | Yes, via LangGraph | Medium–high as glue, not as the runtime | High name recognition; interviewers increasingly want LangGraph specifically |
| **LlamaIndex** | Best-in-class data ingest/index/query; LlamaParse; workflows; LlamaCloud | Agent orchestration less of a differentiator than RAG/data | Current; Python + TS | Workflows + agents | High for RAG/document agents | High in RAG/enterprise-search JDs |
| **OpenAI Agents SDK** | Typed Python/TS; handoffs; guardrails; sandboxes; MCP; traces; official | OpenAI-centric (multi-provider exists but ecosystem is OpenAI-first) | Current, alongside Agents API | Handoffs / specialists-as-tools | High if the account is OpenAI/Foundry Responses | Rising in OpenAI-shop JDs |
| **Anthropic tool/MCP ecosystem** | Excellent tool use, MCP connector, computer/browser/bash, Managed Agents | Not a general multi-agent OS; you still write the loop or use a framework | Current Messages API | Possible via tools/MCP, not a graph runtime | High for Claude-centered products | High wherever Claude is the enterprise default |
| **Google ADK** | Code-first, Workflow graph, Task API, Gemini-optimized, Cloud Run / Agent Engine | ADK 2.0 breaking change; Google-cloud gravity | ADK 2.x current (PyPI 2.9.0, 2026-09-10) | Native multi-agent + Task API | High on GCP | High in Google Cloud / Vertex JDs |
| **Microsoft Agent Framework** | Official successor to AutoGen + SK; Foundry-native; A2A/MCP | Newer than LangGraph; .NET+Python | 1.0-class production SDK (repo active 2026-09-15) | Yes | High on Azure | High in Microsoft-centric enterprises; say “Agent Framework,” not AutoGen, for new work |
| **AutoGen** | Historical multi-agent research patterns | Maintenance mode | Maintenance | Yes | Legacy only | Declining as a *new* skill; migration literacy useful |
| **Semantic Kernel** | .NET enterprise plugins, still documented | Microsoft points new work to MAF | Still documented | Agent Framework inside SK | Legacy-to-MAF | Still appears in older Azure JDs |
| **CrewAI** | Role-playing crews + Flows; fast demos | Easy to demo, harder to constrain; “100k certified” is vendor claim | Current (Flows + Crews) | Yes (crews inside flows) | Medium; some AgentCore/Runtime support | Medium; more startup/automation than FDE core |
| **PydanticAI** | Typed agents, structured output, capabilities, OTel/Logfire, durable exec (Temporal/DBOS/Prefect) | Smaller JD footprint than LangGraph | Current; Harness + Coder capabilities | Sub-agents / capabilities | High for Python shops that already live on Pydantic/FastAPI | Rising among Python platform teams |

**Sources (framework overviews, accessed 2026-09-15):**

- LangGraph overview, LangChain, https://docs.langchain.com/oss/python/langgraph/overview
- LlamaIndex welcome, https://developers.llamaindex.ai/python/framework/
- OpenAI Agents SDK, https://developers.openai.com/api/docs/guides/agents/sdk
- Anthropic tool use, https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- Google ADK / PyPI / GitHub as above
- CrewAI introduction, https://docs.crewai.com/en/introduction
- Pydantic AI overview, https://pydantic.dev/docs/ai/overview/
- Microsoft Agent Framework / AutoGen READMEs as above

### What to learn deeply (FDE / GenAI)

**RECOMMENDATION:** Learn **LangGraph** deeply (state, reducers, persistence, interrupts, streaming, deployment) plus **one native provider stack**:

- OpenAI shop → Responses API + Agents SDK  
- Anthropic shop → Messages API tool use + MCP connector  
- Azure shop → Microsoft Agent Framework + Foundry Agents (Responses)  
- GCP shop → ADK + Gemini API / Agent Platform  

Second deep skill: **LlamaIndex or equivalent RAG plumbing** (parse → chunk → hybrid retrieve → rerank → ACL) — not another agent framework.

Skip collecting CrewAI + AutoGen + SK + LangChain LCEL trivia. Interviewers in 2026 punish 2023 notebook agents.

---

## 3. MCP (Model Context Protocol)

**Official spec URL (current):** https://modelcontextprotocol.io/specification/2026-07-28  
**Current protocol version:** `2026-07-28` (revision identifier is the last date of backwards-incompatible change). Previous: `2025-11-25`, `2025-06-18`.

**Sources:**

- “Specification,” MCP, https://modelcontextprotocol.io/specification/2026-07-28, accessed 2026-09-15
- “Versioning,” MCP, https://modelcontextprotocol.io/docs/2026-07-28/learn/versioning, accessed 2026-09-15
- “The 2026-07-28 Specification,” MCP Blog, https://blog.modelcontextprotocol.io/posts/2026-07-28/, 2026-07-28

**Roles (unchanged conceptually)**

- **Hosts:** LLM applications that initiate connections  
- **Clients:** connectors inside the host  
- **Servers:** services that provide tools, resources, prompts  

JSON-RPC 2.0. Inspired by LSP.

**2026-07-28 core change:** protocol is **stateless**. Removed protocol-level sessions (`Mcp-Session-Id`) and the `initialize` / `notifications/initialized` handshake. Every request carries protocol version and client capabilities in `_meta` (`io.modelcontextprotocol/protocolVersion`, `clientCapabilities`). List endpoints no longer vary per connection. Servers that need state use explicit server-minted handles as tool arguments.

**Transports (bindings)**

**FACT:** Standard transports:

1. **stdio** — newline-delimited JSON-RPC over a client-launched subprocess  
2. **Streamable HTTP** — HTTP POST to a single MCP endpoint; replies as JSON or request-scoped SSE  

Custom transports allowed if they preserve JSON-RPC, message patterns, and per-request metadata. Servers do **not** initiate JSON-RPC requests in this revision (earlier revisions allowed server-initiated requests; compatibility matrix exists).

**Source:** “Overview” (transports), MCP, https://modelcontextprotocol.io/specification/2026-07-28/basic/transports, accessed 2026-09-15.

**Auth / OAuth**

**FACT:** Authorization is **optional**. HTTP transports SHOULD follow the spec; stdio SHOULD NOT (credentials from the environment).

Based on OAuth 2.1 draft, Bearer (RFC6750), AS metadata (RFC8414), DCR (RFC7591, **deprecated** in favor of Client ID Metadata Documents), Resource Indicators (RFC8707), Protected Resource Metadata (RFC9728), issuer identification (RFC9207), OIDC Discovery.

MCP server = resource server; MCP client = OAuth client. Flow: 401 + `WWW-Authenticate` with `resource_metadata` → PRM → AS metadata → CIMD or DCR or pre-registered client → PKCE + `resource` parameter → Bearer token on every HTTP request. Tokens must be audience-bound to that MCP server. Step-up on `insufficient_scope`.

**Source:** “Authorization,” MCP, https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization, accessed 2026-09-15.

**Extensions:** Tasks (long-running, pollable), Skills over MCP, MCP Apps (inline UI). Opt-in.

**Security risks (from the spec + industry practice)**

Spec key principles: user consent; data privacy; **tool descriptions/annotations are untrusted unless the server is trusted**; hosts must obtain consent before invoking tools.

Known risk classes to discuss in interviews (map to OWASP below):

- **Prompt injection via tool outputs / resources** (indirect)  
- **Tool poisoning:** malicious tool names/descriptions that instruct the model to exfiltrate secrets or skip confirmation  
- **Confused deputy / token passthrough:** sending tokens to the wrong audience (spec forbids accepting tokens not issued for that server)  
- **Overbroad OAuth scopes**  
- **Supply chain:** unpinned MCP servers, unsigned packages  

**UNCERTAIN:** Quantitative incident rates. Do not invent them.

---

## 4. A2A vs MCP

**Official spec:** https://a2a-protocol.org/latest/specification  
**Latest released version:** `1.0.0` (also listed: 0.3.0, 0.2.6, 0.1.0)

**FACT:** A2A is an open standard for communication between **independent, opaque agents**. Goals: discover capabilities, negotiate modalities, manage collaborative **tasks**, exchange information **without sharing internal state, memory, or tools**.

Three layers: (1) canonical data model (protobuf: Task, Message, AgentCard, Part, Artifact, Extension), (2) abstract operations (Send Message, streaming, Get/List/Cancel Task, subscribe, push-notification configs, extended Agent Card), (3) bindings: **JSON-RPC, gRPC, HTTP/REST**.

Discovery: **Agent Card** JSON metadata (identity, skills, endpoint, auth). Tasks are stateful with a lifecycle. Streaming and webhook push notifications are first-class. Opaque execution is a guiding principle.

**Source:** “Agent2Agent (A2A) Protocol Specification,” https://a2a-protocol.org/latest/specification, accessed 2026-09-15 (page cites latest as 1.0.0).

**vs MCP (standardized vs emerging)**

| | MCP | A2A |
| --- | --- | --- |
| Job | Agent ↔ tools/data/context | Agent ↔ agent |
| Analogy often used | USB-C for tools | HTTP for agent collaboration |
| Discovery | Server tools/resources/prompts | Agent Card |
| State (2026-07-28 MCP) | Stateless requests | Stateful tasks |
| Governance | Spec under MCP project / AAIF-Linux Foundation ecosystem | Linux Foundation; blog 2026-08-27: A2A joined Agentic AI Foundation |
| Enterprise presence | Ubiquitous in IDEs and model APIs | GA in Microsoft Foundry (v1.0); AgentCore Runtime lists A2A; younger production footprint |

They are **complementary**, not competitors. An A2A server agent commonly uses MCP internally.

**MARKET OBSERVATION:** MCP is the default interview protocol. A2A is the follow-up for “how do two vendor agents delegate?” Do not claim A2A has MCP-scale adoption.

IBM ACP merged into A2A (widely reported 2025); treat ACP as historical.

---

## 5. RAG (current production practice)

**What “production RAG” means in 2026 (not 2023 naive vector search):**

1. **Parse seriously.** Complex PDFs/tables/images: LlamaParse, Bedrock Smart Parsing, Cohere Parse, document AI — not `pypdf` alone for enterprise decks.
2. **Hybrid retrieval.** Dense vectors + lexical (BM25/OpenSearch/kNN hybrid). Vector-only fails on IDs, SKUs, policy codes.
3. **Rerank.** Cohere `rerank-v4.0-pro` / `fast`, Bedrock rerank models, or equivalent. Retrieve wide, rerank narrow.
4. **ACL before retrieval, not after.** Filter by document/row permissions at query time so the index never returns unauthorized chunks to the model. Bedrock Managed KB: document-level ACL filtering at retrieval (except Web Crawler). This is the enterprise bar.
5. **Citations and grounding checks.** Return source IDs; optionally Bedrock Guardrails contextual grounding (grounded + relevant).
6. **Agentic / multi-hop retrieval** when questions span systems (Bedrock Managed KB agentic retrieval; query decomposition). Still constrain hops and cost.
7. **Eval on your corpus** (faithfulness, recall, refusal on missing docs) — not public QA leaderboards.

**FACT (Bedrock KB):** Managed vs customer-managed; connectors; ACL filtering; multimodal; reranking; AgentCore Gateway MCP exposure.

**FACT (Cohere):** Rerank v4 is positioned as the fastest way to inject LM intelligence into existing search; Embed v4 for multimodal RAG.

**Sources:** AWS Knowledge Bases page (above); Cohere models page (above); LlamaIndex intro (RAG as primary context-augmentation pattern), https://developers.llamaindex.ai/python/framework/.

**UNCERTAIN:** There is no single “best chunk size.” Production systems tune chunking per corpus and measure retrieval@k + faithfulness.

---

## 6. Vector databases — selection and job signal

Selection criteria that actually show up in design interviews:

- **Where the system of record lives:** if Postgres is already the OLTP, **pgvector** often wins on ops cost and joins/ACLs.
- **Filter + hybrid:** first-class metadata filters, BM25, sparse+dense.
- **Multi-tenancy / ACL:** per-namespace isolation, document-level security.
- **Scale:** millions vs billions of vectors; p99 latency; streaming ingest.
- **Ops:** managed vs self-host; VPC; SOC2; backup.
- **Ecosystem:** Bedrock KB / Azure AI Search / Vertex RAG Engine may pick the store for you.

| Store | Typical fit | Job signal (MARKET OBSERVATION) |
| --- | --- | --- |
| **pgvector** | Start here for most internal apps; SQL ACLs; one database | Very high in “pragmatic RAG” / FDE roles |
| **Pinecone** | Managed, serverless, low ops; product teams | High in SaaS/startup JDs; less in regulated on-prem |
| **Qdrant** | Self-host or cloud; strong filters; Rust | High in EU/self-host and cost-control shops |
| **Weaviate** | Hybrid search, modules, GraphQL/gRPC | Medium–high |
| **Milvus / Zilliz** | Billion-scale, GPU-ish throughput | High in large-scale retrieval / ML platform roles |
| **OpenSearch** | Hybrid lexical+vector, AWS-native, Bedrock KB customer-managed | Very high in AWS enterprise JDs |

Do not memorize every ANN algorithm. Do memorize: **hybrid + metadata filter + rerank + ACL**, and why you would pick pgvector vs a purpose-built vector DB.

Official starting points (accessed 2026-09-15; confirm current feature lists on each site):

- pgvector: https://github.com/pgvector/pgvector  
- Pinecone: https://docs.pinecone.io/  
- Qdrant: https://qdrant.tech/documentation/  
- Weaviate: https://docs.weaviate.io/  
- Milvus: https://milvus.io/docs  
- OpenSearch k-NN: https://docs.opensearch.org/

---

## 7. Security

### OWASP Top 10 for LLM Applications 2026

**FACT:** OWASP published **OWASP Top 10 for LLM Applications 2026** (resource page dated 2026-08-03). PDF table of contents (community PDF on genai.owasp.org) lists:

| ID | Title |
| --- | --- |
| LLM01:2026 | Prompt Injection |
| LLM02:2026 | Sensitive Information Disclosure |
| LLM03:2026 | Excessive Agency |
| LLM04:2026 | Supply Chain |
| LLM05:2026 | Data and Model Poisoning |
| LLM06:2026 | Unbounded Consumption |
| LLM07:2026 | Misinformation |
| LLM08:2026 | Hidden Context Exposure |
| LLM09:2026 | Vector and Embedding Weaknesses |
| LLM10:2026 | Improper Output Handling |

**Note vs 2025 list:** ranking and names moved (e.g. Excessive Agency rose; Hidden Context Exposure appears as a 2026 entry). Always cite **2026**, not the 2023/2025 IDs.

Related: **OWASP Top 10 for Agentic Applications 2026** (announced 2025-12-09; ASI01 Goal Hijack, ASI02 Tool Misuse, ASI03 Identity & Privilege Abuse, …). Also Agent Control Standard (ACS) and GenAI Security Crosswalk (2026-09-01 resource pages).

**Sources:**

- “OWASP GenAI LLM Top 10 2026,” OWASP GenAI, https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/, 2026-08-03
- PDF ToC via https://genai.owasp.org/download/56857/ (version 2026; publication date field in PDF still placeholder — **UNCERTAIN** exact PDF pub date; resource page says August 3, 2026)
- “OWASP Top 10 for Agentic Applications for 2026,” https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/, announced 2025-12-09

Do not confuse with **OWASP Top 10:2025** (web apps), https://owasp.org/Top10/2025/.

### NIST AI guidance

**FACT:**

- NIST AI RMF 1.0, 2023-01-26, https://doi.org/10.6028/NIST.AI.100-1 (PDF: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf). Voluntary. Functions: Govern, Map, Measure, Manage.
- Generative AI Profile NIST.AI.600-1, 2024-07-26, https://doi.org/10.6028/NIST.AI.600-1
- Concept note for AI RMF Profile on Trustworthy AI in Critical Infrastructure, 2026-04-07
- **AI RMF 1.0 is being revised as part of the White House AI Action Plan** (stated on NIST page as of access date)

**Source:** “AI Risk Management Framework,” NIST, https://www.nist.gov/itl/ai-risk-management-framework, accessed 2026-09-15.

### Prompt injection and tool poisoning

**Prompt injection (LLM01):** untrusted content (user, retrieved docs, web pages, tool results) overrides system intent. Mitigations that interviews expect: treat retrieved text as data not instructions; constrain tools; require HITL on side-effecting tools; output allowlists; separate privileged instructions (system / developer) from untrusted content; grounding checks; don’t put secrets in prompts.

**Tool poisoning:** a malicious MCP/tool descriptor that steers the model (exfiltrate env, disable approvals). MCP spec: treat tool annotations as untrusted. Mitigations: pin/sign servers, allowlists, human approval for new tools, sandbox, audience-bound OAuth, never pass user IdP tokens through to arbitrary servers.

**Excessive agency (LLM03):** agents with write tools + weak policy. Map to Bedrock AgentCore Policy / Cedar, OpenAI guardrails, Anthropic permission modes.

---

## 8. Observability

| Product | What official docs claim | Fit |
| --- | --- | --- |
| **LangSmith** | Tracing, dashboards, automations, feedback, eval datasets, LangSmith Engine (detect issues in traces). Cloud/hybrid/self-host. Integrates OpenAI, Anthropic, CrewAI, Vercel AI SDK, Pydantic AI, etc. | Default with LangGraph; strong JD signal |
| **Langfuse** | OSS AI engineering platform: traces (incl. OTel), sessions, prompt management, evals, datasets. Self-hostable. Python/JS SDKs. | Strong when you must self-host; OTel-friendly |
| **Phoenix (Arize)** | OSS observability + eval on OpenTelemetry / OpenInference. Tracing, evals, prompt playground, datasets/experiments. `uvx arize-phoenix serve`. Arize AX is the managed enterprise sibling. | Strong OSS eval+trace loop; common in RAG debugging |
| **OpenTelemetry** | Becoming the interchange: Langfuse “based on OpenTelemetry”; Phoenix OTLP + OpenInference; AgentCore Observability emits OTEL; Pydantic AI Instrumentation capability. | Conceptual must for FDE: traces/spans for LLM + tool + retrieve |

**Sources (accessed 2026-09-15):**

- LangSmith Observability, https://docs.langchain.com/langsmith
- Langfuse Overview, https://langfuse.com/docs
- Arize Phoenix, https://arize.com/docs/phoenix
- AgentCore Observability (AgentCore overview table)
- Pydantic AI instrumentation, https://pydantic.dev/docs/ai/overview/

**RECOMMENDATION:** FDE interviews: instrument traces (LLM, retrieval, tools), token/cost, latency, user-feedback, and an eval dataset. Brand of UI is secondary to whether you can debug a bad tool call.

---

## 9. Inference serving (conceptual vs implement)

| Engine | Official/current notes | FDE depth |
| --- | --- | --- |
| **vLLM** | High-throughput OSS serving; PagedAttention; OpenAI-compatible server. GitHub tags include **v0.29.0** (2026-09-08) and v0.29.1rc0 (2026-09-12). Broadest hardware/default choice. | **Conceptual + light hands-on** (run a model, know continuous batching / prefix cache) |
| **SGLang** | Fast serving + RadixAttention prefix cache; strong structured/JSON/agent workloads. PyPI **0.5.19** released 2026-09-04. | Conceptual; implement if doing structured-decoding or high prefix reuse |
| **TensorRT-LLM** | NVIDIA; PyTorch is now the sole execution backend (TensorRT backend **removed** in 1.2 release notes). Release notes page dated 2026-08-28. GitHub main active 2026-09-15; 1.3.0 RCs exist. | Conceptual unless the role is NVIDIA inference engineer |
| **Triton** | Multi-framework inference server; backends include vLLM and TRT-LLM containers. Compatibility matrices exist (some public matrices still show 25.01-era tags — **verify NGC tags** before citing versions). | Conceptual: when you need multi-model production serving |
| **TGI** | Hugging Face Text Generation Inference. Third-party reports of maintenance mode (Dec 2025) and read-only archive (2026-03-21). **UNCERTAIN vs HF official** — check https://github.com/huggingface/text-generation-inference before stating deprecation in an interview. Migration guidance in the wild points to vLLM/SGLang. | Awareness only |

**Sources:**

- vLLM tags, https://github.com/vllm-project/vllm/tags, accessed 2026-09-15
- sglang PyPI, https://pypi.org/project/sglang/, 2026-09-04
- TensorRT-LLM release notes, https://nvidia.github.io/TensorRT-LLM/release-notes.html, 2026-08-28
- Triton compatibility matrix, https://docs.nvidia.com/deeplearning/triton-inference-server/user-guide/docs/introduction/compatibility.html (page content may lag)

**RECOMMENDATION:** GenAI/FDE roles: explain *why* PagedAttention / continuous batching / prefix caching cut cost. Implement vLLM only if the JD says “self-host LLMs.” Do not pretend to be a CUDA kernel engineer.

---

## 10. Evaluation

| Tool | Official positioning | Use |
| --- | --- | --- |
| **Ragas** | Library to move from vibe checks to systematic eval loops; experiments-first; custom metrics; RAG and agent how-tos; integrations with LangChain/LlamaIndex | RAG metrics + experiment loop |
| **DeepEval** | Pytest-style LLM eval harness. Metrics for agents (task completion, tool correctness), RAG triad, multi-turn, MCP, safety. CI/CD unit tests. Python + TS. Integrations include LangGraph, ADK, AgentCore, Pydantic AI | Unit/CI evals, agent trajectories |
| **promptfoo** | OSS CLI/library for evals **and** red-teaming. Declarative YAML tests; CI; local-first. Matrix views across prompts/models | Prompt regression + security scans |

**Sources (accessed 2026-09-15):**

- Ragas, https://docs.ragas.io/en/stable/
- DeepEval docs index, https://deepeval.com/
- promptfoo intro, https://www.promptfoo.dev/docs/intro/

Phoenix and LangSmith/Langfuse also run evals on traces/datasets (see §8). Production pattern: offline dataset evals in CI + sampled online judges on traces.

---

## 11. What “current” means for FDE interviews

**Know by name and API shape**

- OpenAI: `gpt-6-astra`, `gpt-5.6-{sol,terra,luna}`, Responses, `text.format`, prompt cache breakpoints, MCP tool type  
- Claude: `claude-opus-5`, `claude-sonnet-5`, `claude-fable-5-1`, `claude-haiku-4-5`, adaptive thinking, MCP connector  
- Gemini: `gemini-3.8-flash`, ADK 2.x  
- Cloud: **Microsoft Foundry** (not Studio), AgentCore (not “just Bedrock Agents”), Bedrock Guardrails + Managed KB ACLs  
- Protocols: MCP `2026-07-28` (stateless, Streamable HTTP, OAuth 2.1), A2A `1.0.0`  
- Framework: LangGraph + native SDK; MAF if Azure; ADK if GCP  
- Security: OWASP LLM Top 10 **2026** IDs  

**Do not lead with**

- Chat Completions as the new default  
- Assistants API  
- AutoGen as Microsoft’s current framework  
- Azure AI Studio  
- OWASP LLM Top 10 2023/2025 IDs as if current  
- MCP initialize-handshake / SSE-only transport as if they were the latest spec  
- “Llama 3 70B” as Meta’s current story  

---

## 12. Source register

All accessed **2026-09-15** unless a publication date is given.

1. Models — OpenAI — https://developers.openai.com/api/docs/models  
2. Migrate to the Responses API — OpenAI — https://developers.openai.com/api/docs/guides/migrate-to-responses  
3. Using tools — OpenAI — https://developers.openai.com/api/docs/guides/tools  
4. Structured model outputs — OpenAI — https://developers.openai.com/api/docs/guides/structured-outputs  
5. Prompt caching — OpenAI — https://developers.openai.com/api/docs/guides/prompt-caching  
6. Agents SDK — OpenAI — https://developers.openai.com/api/docs/guides/agents/sdk  
7. Azure OpenAI reasoning models — Microsoft — https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/reasoning — ~2026-09-06  
8. Models overview — Anthropic — https://platform.claude.com/docs/en/models/overview  
9. Tool use with Claude — Anthropic — https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview  
10. Claude training data cutoffs — Anthropic — https://support.claude.com/en/articles/8114494-how-up-to-date-is-claude-s-training-data — ~2026-09-01  
11. Models — Google AI — https://ai.google.dev/gemini-api/docs/models — 2026-09-04  
12. Google models (Agent Platform) — Google Cloud — https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/google-models — 2026-09-03  
13. Agent Development Kit — Google Cloud — https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/adk — 2026-09-03  
14. google-adk — PyPI — https://pypi.org/project/google-adk/ — 2026-09-10  
15. ADK Python — GitHub — https://github.com/google/adk-python  
16. Llama 4 — Meta — https://developer.meta.com/ai/models/llama-4/  
17. The Llama 4 herd — Meta — https://ai.meta.com/blog/llama-4-multimodal-intelligence/ — 2025-04-05  
18. Mistral Large 3 — Mistral — https://docs.mistral.ai/models/mistral-large-3-25-12  
19. Mistral changelog — Mistral — https://docs.mistral.ai/resources/changelogs  
20. Text generation models — Alibaba Cloud Model Studio — https://www.alibabacloud.com/help/en/model-studio/text-generation-model/ — 2026-09-11  
21. Cohere models — Cohere — https://docs.cohere.com/docs/models  
22. What is Amazon Bedrock AgentCore? — AWS — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html  
23. Bedrock Guardrails — AWS — https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html  
24. Guardrails in AgentCore policy — AWS — https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/policy-guardrails-in-policies.html  
25. AgentCore Guardrails in policy GA — AWS What’s New — 2026-06-17 — https://aws.amazon.com/about-aws/whats-new/2026/06/amazon-bedrock-agentcore-policy-guardrails-generally-available/  
26. Bedrock Knowledge Bases — AWS — https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html  
27. Migrate from Foundry (classic) — Microsoft — https://learn.microsoft.com/en-us/azure/foundry/how-to/navigate-from-classic — 2026-09-11/14  
28. Foundry classic portal — Microsoft — https://learn.microsoft.com/en-us/azure/foundry-classic/what-is-foundry — 2026-08-25  
29. AutoGen README — Microsoft — https://github.com/microsoft/autogen  
30. Agent Framework README — Microsoft — https://github.com/microsoft/agent-framework  
31. Semantic Kernel Agent Framework — Microsoft — https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/ — 2026-08-25  
32. LangGraph overview — LangChain — https://docs.langchain.com/oss/python/langgraph/overview  
33. LlamaIndex welcome — LlamaIndex — https://developers.llamaindex.ai/python/framework/  
34. CrewAI introduction — CrewAI — https://docs.crewai.com/en/introduction  
35. Pydantic AI overview — Pydantic — https://pydantic.dev/docs/ai/overview/  
36. MCP specification 2026-07-28 — https://modelcontextprotocol.io/specification/2026-07-28  
37. MCP transports — https://modelcontextprotocol.io/specification/2026-07-28/basic/transports  
38. MCP authorization — https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization  
39. MCP 2026-07-28 blog — https://blog.modelcontextprotocol.io/posts/2026-07-28/ — 2026-07-28  
40. A2A specification — https://a2a-protocol.org/latest/specification — v1.0.0  
41. OWASP GenAI LLM Top 10 2026 — https://genai.owasp.org/resource/owasp-genai-llm-top-10-2026/ — 2026-08-03  
42. OWASP Agentic Top 10 2026 — https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/  
43. NIST AI RMF — https://www.nist.gov/itl/ai-risk-management-framework  
44. LangSmith Observability — https://docs.langchain.com/langsmith  
45. Langfuse docs — https://langfuse.com/docs  
46. Arize Phoenix — https://arize.com/docs/phoenix  
47. Ragas — https://docs.ragas.io/en/stable/  
48. DeepEval — https://deepeval.com/  
49. promptfoo intro — https://www.promptfoo.dev/docs/intro/  
50. vLLM tags — https://github.com/vllm-project/vllm/tags  
51. SGLang PyPI — https://pypi.org/project/sglang/ — 2026-09-04  
52. TensorRT-LLM release notes — https://nvidia.github.io/TensorRT-LLM/release-notes.html — 2026-08-28  

Gaps left **UNCERTAIN** on purpose: Meta Muse Spark API pricing and Llama API shutdown; TGI official deprecation status; exact OWASP 2026 PDF publication date field; some Vertex model-ID lag vs Gemini API.
