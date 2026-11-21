# 16 — Docker and Kubernetes

**Roles that score this chapter as core:** Cloud AI Engineer, Forward Deployed / AI Deployment (ops side), AIOps Engineer.

**Roles that still get asked:** GenAI / Agentic (you ship a service, not a notebook), AI Security (supply chain, secrets, least privilege), Solutions Architect (where it runs). Intelligent Automation and Solutions Engineer need literacy: “what happens when the pod dies,” not a CKA recitation.

This chapter trains **shipping and debugging AI workloads**, not passing a Kubernetes exam. Chapter 15 is the cloud AI *platform*. Chapter 17 is LLMOps. Chapter 22 has full incidents. Here you learn the objects, the Dockerfile, the probes, and the command sequence you will actually type in a loop.

---

## Interviewer intent

They are hiring you to put a model-backed service in a container, keep it alive, and roll it back. GPU trivia without probes and memory limits is a fail. YAML recitation without a debug order is a fail.

| Signal | Pass | Fail |
| --- | --- | --- |
| Image | Multi-stage, non-root, pin digest, healthcheck | `latest`, root, 8 GB of unused CUDA on a CPU API |
| Runtime | Limits, probes, graceful shutdown | “K8s will restart it” as the design |
| Debug | `describe` → events → logs → previous → metrics | `kubectl delete pod` as step one |
| Scale | Queue-aware for LLM; HPA is not magic | “HPA on CPU to 50 replicas of vLLM” |
| GPU | Literacy: requests, node selectors, OOM on HBM | Pretend you trained at Meta scale |
| Rollout | Pin image digest, canary, rollback | Edit prod with `kubectl edit` and hope |

**The highest-signal 2026 question in this chapter:** *The pod is in CrashLoopBackOff. What do you type, in order?*

If your first move is “increase memory,” you are guessing.

---

## Probability ranking (Cloud / Deploy / AIOps loops, 2026)

| Rank | Topic | Likelihood | Depth they want |
| --- | --- | --- | --- |
| 1 | CrashLoopBackOff debug order | Almost certain | Commands + hypotheses |
| 2 | Dockerfile for an AI API | Very high | Non-root, pin, health, size |
| 3 | Liveness vs readiness vs startup | Very high | Model load vs traffic |
| 4 | OOMKilled (CPU RAM and GPU HBM) | Very high | Limits vs leak vs batch vs KV |
| 5 | Requests/limits and throttling | High | QoS, noisy neighbor |
| 6 | ConfigMaps / Secrets | High | No keys in images or prompts |
| 7 | Rolling / canary / rollback | High | Pin digest, LLM pin together |
| 8 | Compose vs Kubernetes | High | When each is honest |
| 9 | HPA vs queue-based scaling | High for serving | LLM is not a web app |
| 10 | GPU scheduling literacy | Medium–high on Cloud/LLM | Request, taint, MIG, not a cluster from scratch |
| 11 | Image pull / supply chain | Medium–high | Digests, SBOM, non-root |
| 12 | Networking / Service / Ingress | Medium | Enough to debug 5xx |
| 13 | Helm / GitOps | Medium | You ship via git, not pets |

---

## How to study this chapter

Cover the answer. Speak 30 seconds. Then 2 minutes. Then the deep cut. If you have Docker locally, build a tiny FastAPI image and break the probe — do not only read.

Do not memorize flag encyclopedias. Interviewers change the wording: “it’s restarting,” “GPU not found,” “after deploy p95 died,” “CrashLoop.” The test is **order and attribution**.

---

## The one diagram you should be able to draw

```
 git  →  CI (test, eval gate)  →  image@sha256  →  registry
                                      │
                                      ▼
                         Deployment (n replicas)
                           ├── Pod
                           │    ├── container (non-root)
                           │    │    ports, probes, limits
                           │    ├── env from Secret/ConfigMap
                           │    └── optional GPU limit
                           └── Service → Ingress / Gateway
                                      │
                                      ▼
                         HPA or queue workers ──► not “CPU to 50”
                                      │
                         rollout: canary ──fail──► rollback digest
```

Say this out loud: **the unit of rollback is an image digest plus the model/prompt pin** (Chapter 17), not “the cluster.”

---

## Q1. Why containers for an AI service — and what is a bad image?

**Why they ask.** They still see notebooks and “it works on my GPU laptop.”

**What they expect.** Reproducible runtime, isolation, the same artifact in staging and prod. A Dockerfile that is not a crime.

**Answer structure keywords.** reproducible · pin digest · non-root · multi-stage · no secrets · small attack surface.

**30-second.** A container is the unit we test, scan, and roll back. The image pins OS packages, Python, system libs, and the app. We do not deploy “whatever is on the box.” A bad AI image is: runs as root, `FROM something:latest`, copies `.env`, installs the full CUDA stack on a CPU API, and has no healthcheck.

**2-minute.** I want **one artifact** that passed CI evals. Tag with git SHA; deploy by **digest**. Multi-stage: builder has compilers; runtime has the venv and the app. Non-root user. `.dockerignore` so we do not copy `.git`, data dumps, or keys. Healthcheck that hits a cheap `/healthz` (not a 30s model generate). For Python: pin `uv`/`pip` hashes when the org allows; at least pin versions. GPU images: only on GPU deployments — a RAG API that only calls Bedrock should be a slim CPU image.

**Senior / deep.** Supply chain: scan in CI, sign if the org does, never `latest` in prod. Distroless or slim base if the team can debug without bash — have a debug sidecar/profile if you go that far. Model weights: **not** baked into every API image unless they are small and versioned; mount from a cache volume or pull at startup with a checksum, or call a managed API. Baking 70B weights into an image is how your registry and node pull times become the incident. FDE: a Compose file for the customer laptop and a k8s manifest for their cluster should run the **same digest**.

**Weak answer.** “Docker is so we can use Kubernetes.” Circular.

**Mistakes.**

- `latest` in production manifests.
- Secrets in ENV in the Dockerfile `ENV KEY=`.
- One 12 GB image for everything.

**Follow-ups + strong replies.**

- *“COPY . . ?”* — Only after a tight dockerignore. Prefer copying `pyproject` then `src`.
- *“Do we containerize Jupyter?”* — For research, maybe. For the product path, no. The API is the product.

**Example.** FastAPI RAG service: `python:3.12-slim`, uv sync --frozen, user `app`, port 8080, healthcheck `curl -f localhost:8080/healthz`, image 280 MB. GPU worker is a **different** image.

---

## Q2. Walk through a production Dockerfile for an AI API

**Why they ask.** Live coding adjacent. They want taste.

**What they expect.** Multi-stage, non-root, pin, health, no CUDA on CPU, CMD not a notebook.

**Answer structure keywords.** FROM pin · WORKDIR · non-root · COPY lockfile · HEALTHCHECK · EXPOSE · dumb-init/signals.

**30-second.** Pin a slim base by digest. Stage 1 installs deps from a lockfile. Stage 2 copies the venv and app, `USER` non-root, `EXPOSE`, `HEALTHCHECK` on `/healthz`, `CMD` the ASGI server with a finite timeout. `.dockerignore` excludes data and `.env`.

**2-minute.** Sketch I will defend:

```
# syntax=docker/dockerfile:1
FROM python:3.12-slim@sha256:… AS deps
WORKDIR /app
RUN useradd -u 10001 -m app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv uv sync --frozen --no-dev

FROM python:3.12-slim@sha256:… AS runtime
WORKDIR /app
RUN useradd -u 10001 -m app
COPY --from=deps /app/.venv /app/.venv
COPY src ./src
USER app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8080
HEALTHCHECK CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/healthz')"
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8080"]
```

Readiness is **not** this HEALTHCHECK alone in k8s — probes live in the Pod spec (Q3). Here we catch “image cannot even listen.” I pass `stop_grace_period` so in-flight generations can finish or cancel.

**Senior / deep.** Signal handling: uvicorn/gunicorn must get SIGTERM. A shell-form `CMD python app.py` as PID 1 can ignore signals — exec form. For workers that pull models: startup may take 2–5 minutes; that belongs in a **startupProbe**, not in Docker HEALTHCHECK with a 5s timeout. I cache pip/uv mounts in CI, not by committing wheels. If we need system libs (`libgomp`), I install them in runtime explicitly and apt-pin. I do not `apt-get upgrade` unbounded in a prod Dockerfile — unreproducible.

**Weak answer.** `FROM python`, `pip install -r requirements.txt`, `CMD python`, no user, no pin.

**Mistakes.**

- `chmod 777`.
- Installing `nvidia-cuda` on the API image “just in case.”
- Healthcheck that calls the LLM (costs money, flakes).

**Follow-ups + strong replies.**

- *“Where do weights live?”* — Volume or sidecar pull with checksum, or a model server sidecar, or an API. Not `COPY models/70b /models` every build.
- *“Distroless?”* — Fine if we have a debug image. I will not die on it in a 45-minute loop.

**Example.** Same digest runs in GitHub Actions integration tests, in Compose on the FDE laptop, and in the customer’s AKS.

---

## Q3. Liveness vs readiness vs startup — especially with model load

**Why they ask.** Wrong probe = kill the pod while it is still loading weights, or keep sending traffic to a process that cannot answer.

**What they expect.** Three different questions: should k8s *restart* me, *send traffic*, *wait for boot*.

**Answer structure keywords.** startup = boot · readiness = can serve · liveness = deadlock · cheap endpoint · never LLM on liveness.

**30-second.** **Startup:** give me N minutes to load. Failure → don’t kill yet, just wait (then fail). **Readiness:** if I fail, take me off the Service; don’t restart. **Liveness:** if I fail, restart me — I am deadlocked. Liveness hits a cheap `/live` that does not load a model or touch GPU. Readiness hits `/ready` that checks “weights in memory / downstream ping.” Startup wraps the long load.

**2-minute.** Classic outage: liveness on `/` which runs a retrieval+LLM. Slow dependency → probe timeout → kill → CrashLoop → worse. Second outage: no startup probe, liveness starts immediately, model load takes 90s, kubelet kills the pod at 30s. I set `startupProbe` with `failureThreshold * period` > measured load time + headroom. Readiness fails if the vector DB or Bedrock is down **if** we cannot serve without them; for degraded “search-only” modes I may stay ready. I never use the same endpoint for all three.

**Senior / deep.** For vLLM / TGI: startup is “model on GPU, first dummy generate succeeded.” Liveness is “process alive, queue not wedged forever” — a stuck batcher might need a careful liveness (too aggressive = kill during a long generate). I prefer a `/health/live` that checks the process and a watchdog on “no token generated in T seconds while queue > 0.” Readiness includes “queue depth < N” so we shed load. Document this; copy-paste web-app probes will page you.

**Weak answer.** “We hit `/` every 5 seconds for all probes.”

**Mistakes.**

- Liveness on an authenticated LLM route.
- No startup probe on GPU servers.
- Readiness that never fails, so a broken pod eats 100% of traffic.

**Follow-ups + strong replies.**

- *“What HTTP code?”* — 200 live/ready. 503 on ready fail. Don’t 500 on “not ready yet.”
- *“Exec probe vs HTTP?”* — HTTP for APIs. Exec if we have no server yet; it forks, be careful under memory pressure.

**Example.** RAG API: `/live` = process up. `/ready` = can reach Postgres + embed sidecar. GPU worker: startup 5 min, dummy tokenize; liveness 10s cheap; ready = GPU context created.

---

## Q4. CrashLoopBackOff — what do you type, in order?

**Why they ask.** The discriminator for Cloud / Deploy / AIOps.

**What they expect.** A command sequence and hypotheses. Do not skip `describe`.

**Answer structure keywords.** get · describe/events · logs · logs --previous · image pull · probe · OOM · config.

**30-second.** `kubectl get pod -n …` then `describe` (events at the bottom), then `logs`, then `logs --previous` if it already restarted. I classify: pull error, config, crash on boot, OOM, probe kill. I do **not** `delete pod` first — that destroys evidence and the Deployment will just loop again.

**2-minute.** Order:

1. `get deploy,po,rs` — which replica, age, restart count, ready.
2. `describe pod` — `FailedScheduling`, `ErrImagePull`, `OOMKilled`, probe failures, node.
3. `logs --previous --tail=200` — Python traceback on boot (missing env, bad pin, import).
4. Events: `FailedMount` secret, `BackOff`.
5. Compare image digest to last good rollout (`rollout history` / Git SHA).
6. Only then: rollback *or* fix the config and ship a new digest.

Hypotheses: wrong secret key, model path missing, GPU driver vs image CUDA mismatch, liveness too tight, command typo, Crash on `import torch` in a CPU limit.

**Senior / deep.** I correlate with the last change: Helm values, ConfigMap checksum annotation (so pods roll when config changes), model pin. I check **one** replica first. If only some pods loop, think node (GPU, disk) not the image. If all loop, think artifact or shared config. I collect `kubectl get events --sort-by=.lastTimestamp`. I do not `kubectl exec` into a crashlooping container as step two — there may be no running container; `--previous` logs are the point. Chapter 22 incident 7 is the long form.

**Weak answer.** “I’d restart the pod / increase memory / reboot the node.”

**Mistakes.**

- Skipping `--previous`.
- Fixing prod with `kubectl edit` and no git.
- Assuming OOM because “AI uses a lot of RAM” without the event.

**Follow-ups + strong replies.**

- *“ImagePullBackOff?”* — Registry auth, tag deleted, digest not in this region, network policy. Not an app bug.
- *“Works in Docker locally.”* — Different arch, missing GPU, env from Compose not in k8s, volume not mounted.

**Example.** New tag: missing `DATABASE_URL`. App raises on import. `logs --previous` shows it. Roll back, add the Secret, new digest.

---

## Q5. OOMKilled — CPU RAM vs GPU HBM

**Why they ask.** Two different memories. Mixing them is a Cloud/LLM fail.

**What they expect.** Container memory limit vs process RSS vs GPU HBM. Batch, KV cache, leak.

**Answer structure keywords.** cgroup limit · RSS · HBM · batch · KV · leak · don’t raise limits as ritual.

**30-second.** `OOMKilled` on the **container** is the cgroup RAM limit. GPU OOM is HBM inside the process — the pod may still be “Running.” I check events vs process logs. I do not raise limits until I know which memory and why.

**2-minute.** CPU path: `describe` → OOMKilled, last state. Graph RSS vs limit. Causes: loading too much into RAM (pandas of the corpus), unbounded agent context, fork bombs from a debug probe, memory leak in a client, no batch cap on embed jobs. GPU path: logs say CUDA OOM; causes: batch too large, sequence length × concurrency × KV (Chapter 09), two processes on one GPU, fragmentation. Fixes: cap batch, cap context, reduce concurrency, smaller model, more GPU, not `resources.limits.memory: 64Gi` as superstition.

**Senior / deep.** Set requests ≈ measured p95 RSS + headroom so the scheduler is honest; limits to kill rather than freeze the node. For GPU, `nvidia.com/gpu: 1` and a node pool that matches the image CUDA. Don’t pack a training job next to latency-sensitive decode. Measure KV: concurrent × layers × seq × precision. I would rather **shed load** (readiness fail when queue high) than OOM. FDE: customer cluster may have 16 GB GPUs; your 80 GB laptop demo is not a plan.

**Weak answer.** “Pods OOM because Kubernetes is bad at AI.”

**Mistakes.**

- Raising memory 3× without a graph.
- One GPU for training and serving.

**Follow-ups + strong replies.**

- *“Why RSS grows over days?”* — Leak: caches without TTL, tokenizer caches, client sessions. Reproduce with a load test; heap dump; don’t just bounce daily.

**Example.** Embed worker OOM at 2 GB limit: batch 256 × 8k chars. Cap batch 32, limit stays 2 GB, throughput recovered via more replicas.

---

## Q6. Requests, limits, and QoS — why the app got throttled

**Why they ask.** “CPU is 2% but p95 is awful” is a real interview.

**What they expect.** Requests for scheduling, limits for cap, CPU throttle, Burstable vs Guaranteed.

**Answer structure keywords.** request = schedule · limit = cap · throttle · noisy neighbor · Guaranteed when latency matters.

**30-second.** **Request** is what the scheduler reserves. **Limit** is the ceiling. CPU over limit → throttle (slow, not kill). Memory over limit → kill. If I set request too low, I get packed onto a busy node and tail latency dies. For latency-sensitive LLM decode I want request≈limit (Guaranteed) on the serving pods.

**2-minute.** I size from load tests, not from “4 CPU because four workers.” I watch `container_cpu_cfs_throttled_seconds`. Throttle looks like “the model is slow.” For RAG APIs, CPU can spike on JSON/tokenization; I don’t copy the GPU node’s huge requests onto the API. I leave headroom on the node for kubelet/daemons. I never set CPU limit=1 on a Python service that must JIT and then wonder why p99 is 10×.

**Senior / deep.** HPA on CPU for LLM serving is often wrong (Q8). For the API tier it can work. I document QoS class. Spot/preemptible GPU nodes: fine for batch embed, not for interactive p95 unless we can drain. FDE: I ask what the customer’s namespace quota is before I draw 16 GPUs.

**Weak answer.** “Set them high so we don’t OOM.”

**Mistakes.**

- Requests 0 (BestEffort) in prod.
- Memory request << actual RSS → eviction.

**Follow-ups + strong replies.**

- *“Limitless CPU?”* — Some teams omit CPU limits to avoid throttle. I can defend that for serving if isolation is via node pools. I still set memory limits.

**Example.** After deploy, p95 doubled, CPU graph 30%. `throttled_seconds` up. Limit was 250m copied from a sidecar example. Raised to 2 cores; throttle gone.

---

## Q7. ConfigMaps, Secrets, and “no keys in the image”

**Why they ask.** Cloud + Security overlap. Keys in Dockerfiles still happen.

**What they expect.** Env from Secret, rotation, not logging secrets, not putting API keys in prompts (Chapter 15/19).

**Answer structure keywords.** Secret vs ConfigMap · mount vs env · rotate · checksum annotation · never in git or image.

**30-second.** Config (non-secret) in ConfigMap; credentials in Secret or an external manager (AWS Secrets Manager, Key Vault, GSM) with a CSI driver or a sidecar. Image has no keys. Pod env or files. Rotate by changing the Secret and rolling the Deployment (checksum annotation). I do not `kubectl apply` a Secret from a Slack message as the long-term process.

**2-minute.** Pattern: CI gets short-lived registry creds. Runtime gets a cloud identity (IRSA / Workload Identity / Entra Workload ID) and fetches the model API key from the manager. If we must use a k8s Secret, RBAC it, encrypt at rest, don’t dump `env` in debug traces. ConfigMap for prompt **version id**, not for the entire 20k-token prompt if it changes independently — prompts belong in the prompt registry (Chapter 17). Mount config read-only.

**Senior / deep.** Env vars are easy to leak into crash logs and child processes. File mounts with mode 0400 are better for material secrets. I still assume env will leak and I redact (Chapter 17). For FDE, customers will want keys in a `.env` Compose file for week 1; I will do it for a laptop PoC and refuse it for the cluster path.

**Weak answer.** “We put `.env` in the image but it’s a private registry.”

**Mistakes.**

- Base64 Secrets as “encryption.”
- Logging `os.environ` on startup.

**Follow-ups + strong replies.**

- *“How does the pod get AWS rights?”* — Workload identity, not an access key in a Secret, unless the customer is stuck; then rotate and scope.

**Example.** Bedrock app: no AWS keys in k8s. IRSA role scoped to `bedrock:InvokeModel` on one model ARN plus S3 for the corpus bucket.

---

## Q8. HPA vs queue-based scaling for LLM workloads

**Why they ask.** Copy-paste HPA from a web app will either do nothing (GPU CPU is idle while HBM is full) or explode cost.

**What they expect.** Scale on the bottleneck: queue depth, tokens/s, GPU duty — not blindly CPU.

**Answer structure keywords.** bottleneck · queue · GPU util ≠ CPU · scale workers · max replicas · cold start.

**30-second.** HPA on CPU is fine for a JSON API. For GPU decode, CPU may be low while the GPU is saturated. I scale on **queue depth** or a custom metric (in-flight generations, KV bytes). I cap `maxReplicas` because each replica is a GPU. Cold start includes model load — HPA that scales from 0 on every blip will miss SLO.

**2-minute.** Architecture: API Deployment (CPU) + worker Deployment (GPU) pulling from a queue (Redis/SQS). Scale API on CPU/RPS. Scale workers on queue lag. For in-process vLLM, use its scheduler and replica count on GPU util / waiting requests. Embed jobs: scale on queue. I test scale-up time including **startupProbe**. I would rather queue and shed than spawn 20 GPUs that pull 15 GB images.

**Senior / deep.** KEDA or custom metrics if the org has them. Scale-to-zero for batch, not for interactive chat unless TTFT budget allows. Mixed workloads: don’t HPA training. Cost: GPU replicas are the bill; I show a graph of queue vs replica vs $ in the design (Chapter 20). Cloud AI managed endpoints (Bedrock, Foundry, Vertex) move this problem to the vendor — I still need app-level concurrency caps and 429 handling (Chapter 15).

**Weak answer.** “HPA CPU 70% min 2 max 50.”

**Mistakes.**

- Scaling GPU pods on CPU.
- maxReplicas unbounded.

**Follow-ups + strong replies.**

- *“What about serverless GPUs?”* — Fine for spiky embed. Interactive p95 needs warm replicas.

**Example.** Chat: 3 warm GPU replicas, HPA on `vllm_waiting_requests` 2→8, max 8. API 2→20 on RPS. Queue timeout returns 503 with retry-after.

---

## Q9. GPU scheduling literacy (you are not the cluster admin)

**Why they ask.** Cloud AI / LLM track. They want enough to debug “GPU not scheduled,” not to write a device plugin.

**What they expect.** `nvidia.com/gpu`, node selectors/taints, drivers vs image, sharing vs exclusive.

**Answer structure keywords.** resource name · taint/toleration · CUDA match · exclusive GPU · MIG literacy.

**30-second.** The pod **requests** `nvidia.com/gpu: 1`. The scheduler needs a node with that resource. If it sits `Pending`, `describe` the pod: usually taints, insufficient GPU, or wrong node pool. The image CUDA must match the driver on the node. I do not “install CUDA in the pod” as a fix.

**2-minute.** Node pool labeled `workload=gpu`, taint `nvidia.com/gpu=true:NoSchedule`, pods tolerate it so CPU pods stay off those nodes. One process per GPU unless we know MIG or time-slicing. `nvidia-smi` in a debug container to see HBM. Pending: `FailedScheduling`, 0/3 nodes: 2 CPU, 1 GPU already allocated. ImagePull of a 10 GB CUDA image on a small disk will also fail — that’s disk, not scheduling.

**Senior / deep.** MIG: slice an A100 for small models; operational complexity. Time-slicing: throughput up, p99 worse — bad for interactive. Fractional GPUs in clouds are a product; I read the quota. I never run privileged just to see the GPU. Security: GPU nodes still get non-root, still get NetworkPolicy. FDE: ask if the customer has GPU quota in that region *before* promising a local vLLM.

**Weak answer.** “We’ll use Kubernetes GPU operator” as the entire answer.

**Mistakes.**

- Requesting GPU on the stateless API.
- Assuming `nvidia-smi` in the API image.

**Follow-ups + strong replies.**

- *“Pods Running but GPU idle, latency high.”* — Work queued in the app, wrong device, or CPU-bound tokenize. Chapter 22.

**Example.** Inference pods Pending 20 min: CPU node group autoscaled, GPU group min=0 and scale-up cooldown. Fix: GPU pool minCount=1 for the demo, or use Bedrock.

---

## Q10. Rolling updates, canary, and rollback for model-backed services

**Why they ask.** A bad prompt+image+index can ship together. Rollback must be one motion.

**What they expect.** Digest pin, maxUnavailable, canary on eval, rollback command, don’t “fix forward” blindly.

**Answer structure keywords.** image digest · rollout · canary · eval gate · rollback · pin model+prompt+index.

**30-second.** I deploy by digest. Rolling update with a readiness gate so we never drop all replicas. Canary 5–10% with the Chapter 17 eval bar. Fail → `rollout undo` to the last digest. The model ID and prompt version roll with the app or are pinned in config with a checksum so pods restart together.

**2-minute.** `maxUnavailable` small for GPU (you only have 3). `maxSurge` may be 0 on GPU if you have no extra cards — then you need a **blue/green node** or accept brief capacity loss. I never `latest`. I annotate the Deployment with git SHA and eval digest. If only the prompt changes, I still treat it as a release. Shadow traffic: send a copy to the new replica, don’t return it, compare judge scores.

**Senior / deep.** For indexes: switching an index alias is a release. I can canary by sending 5% of queries to the new alias (app flag) without a new image. I would rather that than rebuild in place. Rollback of an alias is a pointer flip. Document the **order**: app that understands the new metadata must land before the new index, or be backward compatible. FDE: customer Friday deploys are a conversation; I prefer a flag.

**Weak answer.** “Kubernetes rolling update handles it.”

**Mistakes.**

- Changing weights on a PVC in place with no pin.
- Canary without metrics.

**Follow-ups + strong replies.**

- *“How fast is rollback?”* — Image already on nodes: seconds to a minute. If the old image was GC’d, pull time. I pin `imagePullPolicy` and keep last N images.

**Example.** Prompt v12 dropped faithfulness 0.06 on canary. Undo Deployment; alias unchanged; incident 12 minutes, no GPU reshuffle.

---

## Q11. Compose vs Kubernetes — when is each honest?

**Why they ask.** FDE and career-switchers overclaim k8s. Seniors pick the smallest runtime.

**What they expect.** Compose for local/PoC; k8s when you need scheduling, probes at scale, multi-node, GPU pools.

**Answer structure keywords.** Compose = laptop/single box · k8s = orchestration · don’t k8s a demo to look senior.

**30-second.** Docker Compose is the right answer for a single-box PoC, FDE week-1 on a customer VM, and local tests. Kubernetes is the right answer when we have multiple nodes, need rolling updates, node pools, and a platform team. I will not draw EKS for a three-container demo that will live on one VM.

**2-minute.** Compose: API, worker, Postgres, maybe a CPU embed. Healthchecks, bind mounts for dev. K8s: same images, manifests or Helm, Secrets, HPA, Ingress. Migration path: **same digest**. If the customer is Cloud-AI-native, I prefer their container apps (ECS/Fargate, Azure Container Apps, Cloud Run) before a cluster — less GPU, less ops. If they already have AKS/EKS/GKE, I land there.

**Senior / deep.** The fail is “we must use k8s because we are serious.” Serious is evals, IAM, and rollback. I have shipped production RAG on Cloud Run + managed DB + Bedrock. I have also needed k8s for GPU daemons and sidecars. Architect loops: pick from constraints (GPU, VPC, team skill), not from a resume keyword.

**Weak answer.** “Everything in k8s, even the laptop.”

**Mistakes.**

- Helm for a two-service Compose.
- Claiming k8s experience that was Compose.

**Follow-ups + strong replies.**

- *“OpenShift / serverless?”* — Same images. I map probes to the platform’s health story.

**Example.** Week 1 FDE: Compose on a 16 GB VM, CPU-only, Bedrock. Week 6: same API image in the customer’s EKS, GPU worker added because they insisted on a local model for one air-gapped flow.

---

## Q12. Services, Ingress, and “it’s 5xx but pods are 1/1 Ready”

**Why they ask.** Networking is half of “k8s is down.”

**What they expect.** Pod ready ≠ user path works. Service selector, Ingress, timeouts, body size, websocket/SSE.

**Answer structure keywords.** selector labels · endpoints · Ingress timeout · SSE · 502/504 · NetworkPolicy.

**30-second.** Ready pods with empty Endpoints means the Service selector does not match labels. 502/504 often is Ingress timeout shorter than LLM generation, or the Service pointed at the old ReplicaSet. I check Endpoints, Ingress annotations, and whether streaming (SSE) is being buffered.

**2-minute.** `kubectl get ep,svc,ing`. Mismatch labels after a Helm rename. Ingress `proxy-read-timeout` 60s, model takes 90s → 504, pods fine. SSE: disable buffering. Body size: large RAG POST with a PDF. NetworkPolicy: API cannot reach the DB. mTLS sidecar. I do not blame the model first when the status is 502 from the gateway.

**Senior / deep.** For streaming chat, the whole path must stream: app, Service (usually OK), Ingress, corporate proxy. FDE on customer networks: a TLS-inspecting proxy will kill SSE. I test with `curl -N`. Timeouts should exceed p99 generate or we stream and keep the connection cheap. Sticky sessions are usually unnecessary if the API is stateless and the model is behind a queue.

**Weak answer.** “I’d restart nginx.”

**Mistakes.**

- Targeting pods by IP in docs.
- Load balancer idle timeout < generate time, no streaming.

**Follow-ups + strong replies.**

- *“Works in-cluster, fails outside.”* — Ingress, DNS, auth at the edge, not the app.

**Example.** Chat 504 at 60s: AWS ALB idle timeout. Raised to 120s *and* streamed tokens so the connection was not idle. Pods were always Ready.

---

## Rapid-fire (30–45 seconds each)

| Prompt | Hit these words |
| --- | --- |
| Why not `:latest`? | Reproducible rollback; pin digest |
| Why non-root? | Blast radius, many CIS/Bench controls |
| Liveness vs readiness? | Restart vs take off Service |
| Startup probe? | Model load; don’t kill during boot |
| OOMKilled vs CUDA OOM? | cgroup RAM vs GPU HBM |
| `logs --previous`? | Last crashed container |
| ImagePullBackOff? | Auth, tag, network, not app code |
| HPA on GPU CPU? | Usually wrong; queue / GPU metrics |
| Config vs Secret? | Non-secret vs credential |
| maxUnavailable on 3 GPUs? | Small; you have no spare |
| Compose vs k8s? | Box vs orchestration |
| Healthcheck that calls LLM? | Flaky, expensive; cheap /live |
| SIGTERM? | Exec-form CMD, graceful drain |
| Pending pod? | `describe` events; scheduling |

---

## Weak vs strong posture

| Weak | Strong |
| --- | --- |
| “I’d restart the pod” | describe → events → logs --previous |
| “Increase memory” | Which memory, which graph, which cap |
| “HPA CPU 70%” | Scale the bottleneck; cap GPU replicas |
| `latest` + root | Digest, non-root, scan |
| Liveness on `/chat` | Cheap /live; startup for weights |
| “We use Kubernetes” as seniority | Same digest, probes, rollback, evals |
| Helm as a personality | Git as source of truth; undo is a release |

---

## A complete example you can reuse

**Setting.** RAG API + optional GPU reranker for a customer who has EKS. p95 TTFT 1.2s. Need a laptop demo on Friday and a cluster path.

**Wrong.** One 11 GB CUDA image, `latest`, root, liveness `/chat`, HPA CPU max 20, keys in Dockerfile, Compose forgotten.

**Right.**

1. **Two images:** slim API (Bedrock + pgvector), GPU image only for the reranker Deployment.
2. **Digest pins** from CI after eval gate (Chapter 17).
3. **Probes:** API `/live` `/ready` (DB). GPU startup 3 min dummy pass.
4. **Secrets:** IRSA; no keys in git.
5. **Scale:** API HPA on RPS. Reranker replicas = GPU count; queue if saturated.
6. **Ingress:** stream SSE; idle timeout > p99.
7. **Rollback:** `rollout undo` + previous prompt pin.
8. **FDE Friday:** Compose with the **API digest**, CPU-only, Bedrock. Same code.

**One sentence close:** “The unit we ship is a pinned image with cheap probes and a rollback; GPUs are a separate Deployment we scale on queue, not CPU.”

---

## Map to the rest of the handbook

- Cloud identity, private RAG, quotas: [15-cloud-ai.md](15-cloud-ai.md)
- TTFT/TPOT, pins, eval gates: [17-llmops.md](17-llmops.md)
- KV cache, batching math: [09-llm.md](09-llm.md)
- Incidents (CrashLoop, GPU OOM): [22-troubleshooting.md](../banks/22-troubleshooting.md)
- Security of supply chain and secrets: [19-ai-security.md](19-ai-security.md)
- Design defaults: [20-system-design.md](../design/20-system-design.md)

Next drill: speak Q3, Q4, Q5, Q8 out loud while pretending you are on a shared screen with only `kubectl`. If those four are clean, you will survive most Cloud AI / Deploy screens.
