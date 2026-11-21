# FRAMEWORK FACTS — Neuro SAN Studio (M0 Source of Truth)

> Inspected: `neuro-san-studio` @ `9cb6965` (Sep 2026) + `neuro-san` lib `0.7.0` (`nsflow==0.7.0`, `pyhocon>=0.3.60`, `langchain-google-genai>=4.2.2,<5.0`, `python-dotenv>=1.2.2`).
> Ref clones: `C:\Users\manoj\AppData\Local\Temp\opencode\neuro-san-studio-ref`, `...\neuro-san-ref` (depth-1, Sep 6 2026).
> Rule: **real framework wins** over any assumption in the build prompt.
> Paths below prefixed `studio:` = neuro-san-studio repo root, `neuro:` = neuro-san repo root.

---

## 1. Exact HOCON network schema

Top-level keys (from `neuro:docs/agent_hocon_reference.md`):

```
commondefs, llm_config, llm_info_file, toolbox_info_file, tools[],
verbose, max_steps, max_iterations (deprecated), max_execution_seconds,
max_attempts, request_timeout_seconds, error_formatter, error_fragments,
metadata, sly_data_schema
```

- `metadata: { description, tags[], sample_queries[] }` — `studio:docs/user_guide.md#agent-network`, `neuro:docs/agent_hocon_reference.md#metadata`.
- `commondefs: { replacement_strings, replacement_values }` — `neuro:docs/agent_hocon_reference.md#commondefs`.
- `llm_config` may appear **top-level** (network default) and **per-agent** (override). Per-agent wins; dicts merged via `DefaultsConfigFilter` — `neuro:neuro_san/internals/graph/filters/defaults_config_filter.py:40-61`.
- Inherited top→agent: `llm_config, verbose, max_steps, max_iterations, max_execution_seconds, max_attempts, error_formatter, error_fragments` (+ `sly_data_schema→function.sly_data_schema` front-man only).
- `max_steps` default `10000` (LangGraph recursion/super-step limit); `max_execution_seconds` default `300` (5 min wall clock); `max_attempts` default `3` (only rate-limit/timeout/transient retried) — `neuro:neuro_san/internals/run_context/langchain/core/run_context_runnable.py:122-208`.
- `error_formatter: "string" (default) | "json"` (`{error, tool, details?}`); `error_fragments[]` marks error; system always adds `"Agent stopped"` — `neuro:neuro_san/internals/errors/error_formatter_factory.py:27-43`.
- Verbatim production example (`studio:registries/agent_network_designer.hocon:35-38`):
  ```hocon
  "max_steps": 40000,
  "max_execution_seconds": 6000,
  "error_formatter": "json",
  "error_fragments": ["Error:", "Exception:", "Traceback (most recent call last)"],
  ```
- Minimal network (`studio:registries/basic/music_nerd.hocon:16-34`):
  ```hocon
  {
      "metadata": { "description": "..." "tags": [] "sample_queries": ["Which band wrote Yellow Submarine?",] },
      include "registries/expertise_scoping_instructions.hocon",
      include "config/llm_config.hocon",
      "tools": [ { "name": "MusicNerd", "function": {...}, "instructions": ..., "tools": [] } ]
  }
  ```
- HOCON mechanics (`studio:docs/user_guide.md#import-and-substitution`):
  - `include "config/llm_config.hocon"` — top-level includes resolve **relative to server root**; nested includes resolve relative to their own file. JSON-notation files must put `include` inside `{ }`.
  - Substitution: `"instructions": ${expertise_scoping_instructions} """..."""`, `"function": ${aaosa_call}`, `"project": ${GCP_PROJECT_ID}`, optional `"x": ${?OPTIONAL_VAR}` (no error if unset).
  - Extra top-level keys (e.g. `"pii_patterns": {...}` in `studio:registries/agent_network_designer.hocon:46-73`) are legal as substitution sources.

## 2. Exact agent definition schema

Table source: `studio:docs/user_guide.md#agent-specifications` + full key list `neuro:docs/agent_hocon_reference.md#single-agent-specification`.

| Field | Notes |
|---|---|
| `name` | `[A-Za-z0-9-/_]+`, no spaces. Referenced by other agents in same file via `tools`. |
| `function` | OpenAI function spec: `{ description*, parameters{type:object, properties, required}, sly_data_schema, sly_data_output_schema, invocation }`. Only `type:object+properties` honored; `additionalProperties/anyOf/$ref` ignored; schema without `properties` rejected when called as tool. |
| `instructions` | Single long string. Required if LLM expected; CodedTools may omit. |
| `command` | Optional starter string, e.g. `"command": "Find a synonym string given the input_string"` (`studio:registries/basic/hello_world.hocon:107`). |
| `tools` | Optional list of down-chain refs: internal agent names (`"Accountant"`), same-server external (`"/expedia"` = stem of served hocon), cross-server URL (`"http://host:8080/expedia"`), MCP string/dict (see §3). First entry in top-level `tools[]` = Front Man. |
| `middleware` | Optional list `[{class*, args{}}]`, order matters. Special args auto-populated: `chat_history, origin, origin_str, progress_reporter, reservationist, sly_data`. |
| `llm_config` | Optional per-agent override, same shape as top-level. |
| `class` | CodedTool impl `module.Class` (see §4). **Disqualifies front-man.** |
| `toolbox` | Pre-registered tool name. **Disqualifies front-man.** Cannot coexist with `class`/`function`/`tools`. |
| `args` | Extra kwargs for `class`/`toolbox`; `args.tools` declares BranchActivation callees. Example: `{ "name": "web_searcher", "toolbox": "tavily_search", "args": { "max_results": 3 } }`. |
| `allow` | Sly-data gates (see §7). Forms: `to_downstream/from_downstream/to_upstream/to_tracing + connectivity`. Front-man-only: `to_upstream, to_tracing`. |
| `display_as` | Auto: `external_agent\|coded_tool\|langchain_tool\|llm_agent` if absent. |
| `max_message_history` | Front-man only; `None`=unlimited; sent back as `chat_context`. |
| `structure_formats` | Front-man only; only `"json"` supported; parsed into `ChatMessage.structure`. |
| `verbose, max_steps, max_execution_seconds, max_attempts` | Per-agent overrides of top-level. |

Front-man rules (verbatim comment in every example, e.g. `studio:registries/basic/music_nerd.hocon:38-41`):
```
# 1) Cannot use a CodedTool "class" definition
# 2) Cannot use a Tool "toolbox" definition
```
- Position = `tools[0]`. Enforced: `DefaultsConfigFilter` assumes `idx==0` is front-man (`neuro:.../defaults_config_filter.py:108-110`); `UnreachableNodesNetworkValidator` errors if 0 or >1 front-men (`neuro:.../unreachable_nodes_network_validator.py:55-127`).
- Typical user-facing front-man has **no** `function.parameters` ("primary way to identify front-man"). If network is called externally, declare ≥1 param (e.g. required `inquiry`); else caller synthesizes default required `inquiry` + warns.

## 3. Exact tool declaration syntax (3 forms — DO NOT MIX)

Source: `studio:docs/user_guide.md#tool-specifications` (table: `name` unique id; `class` = `<module>.<Class>`; `function` = OpenAI schema; `toolbox` = predefined name, must NOT set `class`/`function`).

### (a) CodedTool: `class` + `function` (+ optional `args`)
```hocon
{
    "name": "create_new_network",
    "class": "coded_tools.agent_network_editor.create_network.CreateNetwork",
    "function": {
        "description": "Create a new network",
        "parameters": { "type": "object", "properties": { "agent_network_name": {"type": "string"} }, "required": ["agent_network_name"] }
    }
}
```
`studio:registries/agent_network_editor.hocon:221-249`. No-params form legal: `{"name":"get_subnetwork","class":"...GetSubnetwork","function":{"description":"Retrieve..."}}` (`:...:322-328`).

### (b) Toolbox: `toolbox` (+ optional `args`), NO `class`/`function`/`tools`
```hocon
{ "name": "current_date_time", "toolbox": "get_current_date_time" "args": { "utc_offset": 0 } }
```
`neuro:neuro_san/registries/date_time_timezone.hocon:63-75`. Quote: "an agent using `toolbox` cannot have a `tools` field... it cannot invoke other tools" (`neuro:docs/agent_hocon_reference.md#toolbox`). Caller side: `{ "name": "X", "toolbox": "name_from_toolbox_info" }` (`studio:docs/user_guide.md#usage-in-agent-network-config`). Catalog: `studio:neuro_san_studio/toolbox/toolbox_info.hocon`; custom via `toolbox_info_file` key or `AGENT_TOOLBOX_INFO_FILE` env. Defaults include LangChain `requests_*` + coded `get_current_date_time`.

### (c) MCP: string or dict inside an LLM agent's `tools[]`
Recognition: `http|https`, host required, no fragment, literal `mcp` as host label (`mcp.example.com`) or path segment (`/mcp`) — else dict form required (`studio:docs/user_guide.md#mcp-servers`, `neuro:docs/agent_hocon_reference.md#mcp-servers`).
```hocon
"tools": ["https://api.you.com/mcp"]              // all tools
"tools": [{ "url": "https://mcp.deepwiki.com/mcp", "tools": ["read_wiki_structure"] }]  // filtered
```
Auth: `sly_data.http_headers{"<URL>": {Authorization:...}}` wins over `MCP_SERVERS_INFO_FILE` HOCON; info-file filter only if no inline filter. OAuth gating via `sly_data_schema.http_headers.required` (nsflow redirects until connected).

## 4. Exact coded-tool Python interface

Base: `neuro:neuro_san/interfaces/coded_tool.py:22-99`:
```python
from neuro_san.interfaces.coded_tool import CodedTool
class CodedTool:
    def invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Any: ...
    async def async_invoke(self, args: Dict[str, Any], sly_data: Dict[str, Any]) -> Any:
        raise NotImplementedError
```
- `async_invoke` preferred; `invoke` sync fallback ("prefers async_invoke, falls back to invoke" — `studio:docs/tutorial.md:556-558`). Sync blocking blocks the event loop — offload via `await asyncio.to_thread(self.invoke, args, sly_data)` (docstring `:77-83`, live `studio:coded_tools/basic/advanced_calculator/calculator_tool.py:153-179`).
- `args`: LLM-filled from `function.parameters` + static `args{}` in HOCON (static wins/merge; treat as read-only). `sly_data`: hidden bulletin-board dict, never in prompts by default; may add NEW keys once if producer responsibility is clear (`coded_tool.py:56-61`).
- No-args ctor required; import executes top-level code (= code-equivalent trust); resolution via `AGENT_TOOL_PATH` (see §5).
- Advanced: inherit `BranchActivation` (+ `CodedTool`) when needing `run_context`/`session.function({})` (reservations, subnetwork listing) — e.g. `studio:coded_tools/agent_network_editor/get_subnetwork.py:42` (`class GetSubnetwork(BranchActivation, CodedTool)`), `neuro:neuro_san/coded_tools/copy_cat/copyist.py:29`.

## 5. Exact coded-tool registration mechanism

1. Write `coded_tools/<network>/<module>.py:Class(CodedTool)` (scoped to that network if folder matches HOCON stem; shared if directly in tool path) — `studio:docs/tutorial.md:561-572`.
2. Declare in network HOCON `tools[]` with `class: "<module>.<Class>"` + `function` schema (§3a).
3. Set env (tutorial `:...:231-232,428-429`):
   ```bash
   export AGENT_MANIFEST_FILE="./registries/manifest.hocon"
   export AGENT_TOOL_PATH="./coded_tools"
   ```
   `AGENT_TOOL_PATH` default = `neuro_san/coded_tools` / `coded_tool/`; `AGENT_TOOL_PATH_ONLY=true` restricts to it. Fully-qualified `module.Class` on `PYTHONPATH` also works.
4. Validate: `ns check-config --hocon-path <file>`; list: `ns chat <network> --connectivity`.
- Toolbox registration is SEPARATE: central `toolbox_info.hocon` (`class+description+parameters` for coded, `class` for LangChain) + `toolbox_info_file` / `AGENT_TOOLBOX_INFO_FILE` — `studio:docs/user_guide.md:1273-1276`.

## 6. Exact AAOSA / delegation mechanism

- AAOSA = "Adaptive Agent Oriented Software Architecture... agents decide if they can answer or need to call other agents" (`studio:docs/user_guide.md:1746-1750`).
- Reusable snippet `studio:registries/aaosa.hocon:23-81` (short variant `aaosa_basic.hocon`). Networks opt in:
  ```hocon
  include "registries/aaosa.hocon"
  "instructions": ${instructions_prefix} """You are X...""" ${aaosa_instructions},
  "function": ${aaosa_call} { "description": "Controls the TV..." },
  ```
  Live: `studio:registries/basic/smart_home.hocon:31,68-77` (`"tools": ["TV","Lights","Book","Radio"]` etc.).
- `aaosa_call` params: required `inquiry: string`, `mode: string` (`Determine|Fulfill|Follow up`). `aaosa_instructions` 5-step loop: (1) not-relevant → reply so; (2) maybe-relevant → call down-chains, never assume; (3) pick strongest claims (ambiguous → ask clarification); (4) compile; (5) format by mode (`Determine`→claim JSON `{Name,Inquiry,Mode,Relevant,Strength 1-10,Claim:All|Partial,Requirements}`, `Fulfill/Follow up`→answer+`{Name,Inquiry,Mode:Fulfill,Response}`).
- Delegation = `tools[]` = down-chain list. LLM decides calls via OpenAI function-calling; CodedTools receive `args{inquiry, mode}`. Graph may have cycles; `UnreachableNodesNetworkValidator` requires single connected front-man.
- External delegation (`studio:docs/user_guide.md:1767-1779`): same-server `"/expedia"` (stem of served hocon), cross-server `"http://host:8080/expedia"`, MCP URL/dict. `connectivity:false` hides from `Connectivity()`.
- `aaosa_command` deprecated (empty string for back-compat) — `studio:registries/aaosa.hocon:83-86`.

## 7. Exact sly_data behavior

- Def (`studio:docs/user_guide.md:1106-1111`): "dict passed with `ChatRequest`... will not be seen by LLMs, and by default, will not leave the network. Within the network visible to coded tools as bulletin-board."
- Client in: `ChatRequest.sly_data` / CLI `--sly_data JSON` (`studio:docs/cli/chat.md:54`) / nsflow `sly_data` field (e.g. `{"time":"1 am"}` in `studio:docs/examples/basic/coffee_finder_advanced.md:97-114`).
- In-tool: `sly_data.get("k")` read; `sly_data["k"]=v` write-once bulletin (e.g. `Accountant`: `sly_data["running_cost"]=...` in `studio:coded_tools/basic/accountant.py:55-63`; `order_api.py:61-69` username fallback+write-back).
- Gates (default NOTHING shared; must allow explicitly — `studio:docs/user_guide.md:1113-1176`):
  ```hocon
  "allow": { "to_downstream": { "sly_data": ["x","y"] } }
  "allow": { "from_downstream": { "sly_data": ["equals"] } }
  "allow": { "to_upstream": { "sly_data": ["equals"] } }   // front-man → client
  ```
  Live: `studio:registries/basic/music_nerd_pro_sly.hocon:72-78` (`to_upstream: running_cost`), `studio:registries/experimental/copy_cat.hocon:124-130` (`agent_reservations`).
- Reservations convention (`studio:docs/examples/experimental/copy_cat.md:29-150`): creator returns `sly_data["agent_reservations"]=[{reservation_id, lifetime_in_seconds, expiration_time_in_seconds}]`; consumer HOCON needs `"allow": {"reservations": True}` to get `reservationist` in `args`. Iface: `neuro:neuro_san/interfaces/reservation.py:19-58`.
- MCP auth: `sly_data["http_headers"]["<MCP_URL>"]={Authorization:...}` (+ `sly_data_schema.http_headers.required` gating for nsflow OAuth).
- `chat_context` ≠ `sly_data`: `chat_context={chat_histories:[{origin,messages}]}` is resumable LLM history (`neuro:neuro_san/internals/chat/data_driven_chat_session.py:372-399`); `sly_data` is hidden out-of-band state.
- Secret pattern for this project: put `GOOGLE_API_KEY`, ServiceNow creds, hostnames/IPs ONLY in env/`sly_data`/coded-tool locals; never in `instructions`/`function.description`. Optional `PIIMiddleware` (`langchain.agents.middleware.PIIMiddleware`, `pii_type:api_key`, `detector` = alternation of `pii_patterns.*` via `${...}"|"${...}`) redacts `sk-ant-*, sk-proj-*, sk-*, AKIA*, AIza*, gh[pousr]_*, xox*, glpat-*, sk_live/test_*, Bearer *, ${VAR}` — `studio:registries/agent_network_designer.hocon:46-73,150-190`.

## 8. How networks are registered

- Manifest keys = `.hocon` filenames relative to manifest dir; values = `bool | {serve, public, mcp, periodic}` (`neuro:docs/manifest_hocon_reference.md`, `studio:docs/user_guide.md#manifest`).
  ```hocon
  { "basic/music_nerd.hocon": true, }
  "agent_network_editor.hocon": { "serve": true, "public": false },
  "music_nerd_pro.hocon": { "serve": true, "mcp": true },  // mcp:true implies public:true
  ```
  `true`=serve+list in Concierge; `false`=neither; `serve:false` logs warning; `public:false` still callable as `/name` external agent.
- Grouping via `include "registries/basic/manifest.hocon"` etc. (`studio:registries/manifest.hocon:24-36`); sub-manifest `studio:registries/basic/manifest.hocon:24-32`.
- `periodic` only if front-man `function.invocation:"event"`: `true`=every-min `"Do your thing"`; string=cron `Min Hour DoM Month DoW [Sec]`; dict=`{interactions:[{enable,cron_schedule,second_at_beginning,text,sly_data,metadata}]}`.
- Env: `AGENT_MANIFEST_FILE="./registries/manifest.hocon"` (single) or `os.pathsep`-separated overlay (`:` Linux/macOS, `;` Windows), later overlays earlier (`studio:registries/manifest_multiuser_overlay.hocon:40-47`, `studio:deploy/Dockerfile:183`). Default if unset: `<root>/registries/manifest.hocon` (`studio:neuro_san_studio/commands/project_environment.py:70-71`). Hot-reload: `AGENT_MANIFEST_UPDATE_PERIOD_SECONDS=0` off; `>0`=rescan secs.
- Designer flow writes HOCON to `registries/` + updates `manifest.hocon` via `AgentNetworkPersistenceMiddleware` (or reservations if `AGENT_NETWORK_DESIGNER_USE_RESERVATIONS=true`) — `studio:docs/examples/agent_network_designer.md`.

## 9. How `ns run` discovers the network

- Scaffold: `ns init` (choose LLM provider → creates `config/`, `mcp/`, `registries/` + simple network) — `studio:README.md:210-223`. Import: `ns import [group|network|all|<file.hocon|zip>] [--force]` merges sorted JSON into `registries/manifest.hocon`; running server auto-reloads ~5s (`studio:docs/cli/import.md:140`, `studio:neuro_san_studio/commands/run.py:90` sets `AGENT_MANIFEST_UPDATE_PERIOD_SECONDS=5`).
- Resolve: `ProjectEnvironment.resolve_manifest_file()` = `$AGENT_MANIFEST_FILE` or `<root>/registries/manifest.hocon` (`studio:neuro_san_studio/commands/project_environment.py:69-71`); `run.py:104,165,174` exports it + prints `AGENT_MANIFEST_FILE set to: ...`.
- Serve: `ns run [--server-host localhost] [--server-http-port 8080] [--nsflow-port 4173] [--log-level] [--thinking-file] [--client-only|--server-only]` (`studio:neuro_san_studio/commands/cli.py:106-120`, `studio:neuro_san_studio/commands/run.py:87-96`, env overrides `NEURO_SAN_SERVER_HOST/PORT`, `NSFLOW_HOST/PORT`). Server `localhost:8080`, nsflow `http://localhost:4173/`, logs `logs/{server.log,nsflow.log,thinking_dir/}` (`studio:README.md:286-299`).
- Chat/discover: `ns chat <stem> (e.g. basic/music_nerd)`, `ns chat --list`, `ns chat <stem> --connectivity` (graph probe) (`studio:docs/cli/chat.md:15-57`). Legacy: `export AGENT_MANIFEST_FILE=...; export AGENT_TOOL_PATH=...; python -m neuro_san_studio run` (`studio:docs/tutorial.md:230-234,427-431`).
- Validate: `ns check-config --hocon-path config/llm_config.hocon` (expands `fallbacks`, tests each model once); `ns check-llm-keys` validates `OPENAI/ANTHROPIC/GOOGLE/AWS/AZURE` keys (Tier3 live `google.genai.Client(api_key).models.list()`).

## 10. How nsflow displays the network

- Repo contains NO nsflow render code; `nsflow==0.7.0` pinned (`studio:requirements.txt:4`). Start: `python -u -m uvicorn nsflow.backend.main:app --host <nsflow_host> --port <nsflow_port> --reload` (`studio:neuro_san_studio/commands/run.py:262-279`).
- Listing controlled by `serve/public/mcp` (§8); `serve:true/public:false` hidden from list but callable (`studio:registries/manifest.hocon:46-51`).
- Designer: nsflow `NEW` button → prompts → creates agents, links, writes instructions+queries, saves `registries/generated/*`, blue `Launch` to chat, pen icon to edit (`studio:README.md:305-323`).
- Graph alternatives in-repo: `Connectivity()` API (`ns chat --connectivity`), HTML graph via `agent_network_html_generator` toolbox + `pyvis~=0.3.2` (`studio:docs/examples.md:340-345`), CRUSE at `/cruse` (`studio:docs/examples/experimental/cruse_*.md:11`). MCP OAuth gating redirects in nsflow until `sly_data_schema.http_headers.required` servers connected (`studio:docs/examples/tools/google_workspace.md:23-58`). Pixel-level graph logic lives in EXTERNAL `nsflow` package, not this repo.

## 11. Gemini provider configuration (DO NOT GUESS — verified)

- Canonical env: **`GOOGLE_API_KEY` ONLY** (`studio:.env.example:40-41`, `studio:docs/api_key.md:156-162`, `studio:tests/apps/gemini_api_key.py:33-34`, `studio:neuro_san_studio/commands/check_llm_keys.py:113-138,365-366`). `GEMINI_API_KEY` appears ONLY in image-gen comment/doc (`studio:registries/tools/gemini_image_generation.hocon:22`, `studio:docs/examples/tools/gemini_image_generation.md:44`) — never validated, never `os.getenv`’d — DO NOT USE for chat LLMs. `GOOGLE_GEMINI_API_KEY`/`GOOGLE_GENAI`: 0 hits.
- Standard chat (`studio:docs/user_guide.md:489-510`):
  ```hocon
  "llm_config": { "model_name": "gemini-3-flash", "temperature": 1.0 }
  ```
  Prereq: `langchain-google-genai` already included; `export GOOGLE_API_KEY="XXX"`. ⚠️ Gemini 3.0+ REQUIRES `temperature: 1.0`; `0.7` may infinite-loop (`:...:506`).
- VertexAI/ADC (`:...:531-573`): `pip install langchain-google-vertexai` + `gcloud auth application-default login`; HOCON MUST use `class` (project/location not in default defs):
  ```hocon
  llm_config: { class: "langchain_google_vertexai.chat_models.ChatVertexAI"  model_name: "gemini-2.5-flash"  temperature: 0.2  max_tokens: 2048  project: ${GCP_PROJECT_ID}  location: ${GCP_REGION} }
  ```
  Env `GCP_PROJECT_ID`, `GCP_REGION` (e.g. `us-central1`). ⚠️ NEVER set `GOOGLE_API_KEY` with ADC — mutually exclusive, key wins unexpectedly.
- `class` table (`:...:969-986`, `studio:config/developer_llm_config.hocon:37-45`): Google Gemini = `"gemini"` (same pattern as `"openai"`, `"anthropic"`, `"bedrock"`, `"azure-openai"`, `"nvidia"`, `"ollama"`). Only scalars in `default_llm_info.hocon:classes.<class>.args` honored.
- BYOK (`studio:config/byok_llm_config.hocon:49-57,88-91`): `{ "model_name": "gemini-3-flash", "google_api_key": "sly_data" }` + `sly_data_schema.google_api_key: {type:string}` — client supplies key per-request in `sly_data` (NOT our path; we use server env).
- Reasoning: Gemini 3+ `thinking_level: minimal|low|medium|high`; Gemini 2.5 `thinking_budget: int` (`0` off, `-1` dynamic) (`studio:docs/user_guide.md:890-924`). Example: `{ "model_name": "gemini-3-flash", "temperature": 1.0, "thinking_level": "minimal" }`.
- Image tool (NOT chat): `toolbox: gemini_image_generation` (`studio:neuro_san_studio/toolbox/toolbox_info.hocon:172-181`, impl `studio:neuro_san_studio/coded_tools/gemini_image_generation.py:162` reads ONLY `GOOGLE_API_KEY`).

## 12. Tool-calling requirements

- Delegation = OpenAI function-calling. Model MUST support tool/function calling; else down-chain `tools[]` never fire and network collapses to single-turn answer. All `developer_llm_config` fallbacks (`gpt-5.2`, `claude-sonnet`, `gemini-3-flash`) support it; Ollama only if model explicitly supports tools (must be downloaded first).
- Each callable needs a valid `function.description` (+ `parameters{type:object,properties,required}` if args). Schema without `properties` rejected when called as tool. Front-man typically NO params; down-chains MUST have params (`inquiry`/`mode` for AAOSA).
- CodedTools return → chat stream (must be JSON-serializable or string; `error_formatter/json` wraps failures as `{error,tool,details?}`).
- Limits (§1) bound tool loops: raise `max_steps`/`max_execution_seconds` for deep investigations (designer uses `40000/6000`); keep `max_attempts≥1`.
- Env-gated models culled automatically: "Providers whose libraries and/or API keys are not available are culled... unless none available → error" (`studio:config/developer_llm_config.hocon:24-27`).

## 13. Model configuration / fallback behavior

- Shared default: `config/llm_config.hocon` = `include "developer_llm_config.hocon"` (`:...:17-19`). That file's `llm_config.fallbacks=[{class:openai,model_name:gpt-5.2},{model_name:claude-sonnet},{model_name:gemini-3-flash}]` — tried IN ORDER until one succeeds (`studio:docs/user_guide.md:790-810`, live `studio:registries/basic/music_nerd_llm_fallbacks.hocon:28-39`).
- System default if `model_name` omitted: `gpt-5.2` (`studio:docs/user_guide.md:306`).
- Variants: `cluster_llm_config` (same 3, two passes `max_retries:0` then `1`), `private_llm_config` (Azure `deployment_name`), `byok_llm_config` (`*_api_key:"sly_data"`). `config/plugins.hocon:1-17`: `PhoenixPlugin enabled=false (${?PHOENIX_ENABLED})`, `ProcessLogBridgePlugin enabled=true (${?LOGBRIDGE_ENABLED})`.
- Overrides: `${?MODEL_NAME}` optional substitution (`studio:docs/user_guide.md:744-782`); per-agent `llm_config` for specialization/cost; `class` key for custom providers (`studio:docs/user_guide.md#using-the-class-key`); custom catalogs via `llm_info_file` / `AGENT_LLM_INFO_FILE`.
- For THIS project (Gemini-only hackathon): replace fallbacks with single `{"model_name":"gemini-2.5-flash" or "gemini-3-flash","temperature":1.0}` OR keep fallbacks with Gemini last (needs only `GOOGLE_API_KEY`). Do NOT set `temperature:0.x` on Gemini 3.
- Check: `ns check-config` (fallback expansion) + `ns check-llm-keys` (live key probe).

## 14. Examples of coded tools (verified)

- `studio:coded_tools/basic/accountant.py:26-69` (`Accountant.async_invoke` — args→sly_data fallback, `+3.0`, write-back, return `{running_cost}`).
- `studio:coded_tools/basic/coffee_finder_advanced/time_tool.py:28-57` (sync `invoke` + `async_invoke→invoke`; `sly_data.get("time")` else `datetime.now()`).
- `studio:coded_tools/basic/coffee_finder_advanced/order_api.py:39-69` (`customer_name` args→`sly_data.username` fallback + write-back).
- `studio:coded_tools/basic/advanced_calculator/calculator_tool.py:153-179` (`asyncio.to_thread(self.invoke,...)` pattern).
- `studio:coded_tools/agent_network_editor/get_subnetwork.py:42,505` + `neuro:neuro_san/coded_tools/copy_cat/copyist.py:29,50,94-123` (`BranchActivation+CodedTool`, reservations via `ReservationUtil.wait_for_one` → `sly_data["agent_reservations"]`).
- Tutorial skeletons: `WeatherTool` / `DateTime` (`studio:docs/tutorial.md:622-671`).
- Toolbox catalog: `studio:neuro_san_studio/toolbox/toolbox_info.hocon:21-181` (LangChain + coded + `gemini_image_generation`).

## 15. Examples of multiple-agent delegation

- `studio:registries/basic/smart_home.hocon:31,68-92` (AAOSA: `SmartHouseAssistant tools:[TV,Lights,Book,Radio]` → `TV tools:[TV_Switch_API]` etc.).
- `studio:registries/basic/music_nerd_pro.hocon:84` (internal `"tools":["Accountant"]`); `hello_world.hocon:74` (`["synonymizer"]`).
- `studio:registries/basic/music_nerd_pro_sly.hocon:43-93` (sly_data end-to-end: front-man `allow.to_upstream` + `Accountant` coded tool).
- `studio:registries/experimental/copy_cat.hocon:124-164` (reservation `allow` + `Copyist`).
- `studio:registries/agent_network_designer.hocon` (front-man `agent_network_designer` → subnetworks `agent_network_editor/instructions_editor/query_generator` + coded `get_agent_network_definition` + middleware `AgentNetworkDefinitionMiddleware` + `AgentNetworkPersistenceMiddleware` + `PIIMiddleware`).
- `studio:registries/industry/*` (e.g. `carmax/airbnb/expedia/keybank/macys.hocon:36-37` with `max_steps:2000/max_execution_seconds:600` multi-agent verticals).
- External: `"tools": ["/expedia"]` same-server, `"http://host:8080/expedia"` cross-server, MCP string/dict (see §3c).

---

## Appendix A — Commands & env (copy-paste safe)

```bash
ns init
ns import basic/music_nerd
ns run  # server :8080, nsflow :4173, logs/...
ns chat digital_workplace_autopilot/commander --list
ns check-config --hocon-path registries/digital_workplace_autopilot/commander.hocon
ns check-llm-keys
export AGENT_MANIFEST_FILE="./registries/manifest.hocon"
export AGENT_TOOL_PATH="./coded_tools"
export GOOGLE_API_KEY="..."
```

`.env` canonical keys (from `studio:.env.example`): `NEURO_SAN_SERVER_HOST/PORT`, `NSFLOW_HOST/PORT`, `AGENT_SERVICE_LOG_JSON`, `THINKING_FILE`, `OPENAI/ANTHROPIC/GOOGLE/MISTRAL/AWS/AZURE_*`, `AGENT_NETWORK_DESIGNER_*`, `SERVICENOW_INSTANCE_URL/USER/PWD_*` (note: NOT `SERVICENOW_INSTANCE/USERNAME/PASSWORD` — see Decisions).

## Appendix B — Versions pinned for this build

`neuro-san==0.7.0`, `nsflow==0.7.0`, `pyhocon>=0.3.60`, `langchain-google-genai>=4.2.2,<5.0`, `python-dotenv>=1.2.2,<2.0.0`, `pyvis~=0.3.2`, `typer>=0.12.0,<1.0`. Python `3.11.15` verified locally.
