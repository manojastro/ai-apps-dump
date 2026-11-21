# -*- coding: utf-8 -*-
"""Role modules 1-2: AIOps Engineer, Cloud AI Engineer."""
from docx_builder import H, P, BULLETS, NUMBERS, CODE, CALLOUT, TABLE, PAGEBREAK, RICH


# =====================================================================
# ROLE 1: AIOPS ENGINEER
# =====================================================================
def build_aiops(doc):
    H(doc, "Role Module 1 - AIOps Engineer", 1, page_break_before=True)
    P(doc,
      "The AIOps Engineer owns the machine-learning layer of incident management: ingesting metrics, "
      "logs, and traces; suppressing noise; correlating events into probable root cause; and increasingly "
      "attaching LLM copilots to the incident timeline. It is the highest-leverage transition role for "
      "NOC, sysadmin, SRE, and IT Service Desk backgrounds because it converts operational scar tissue "
      "into a differentiator instead of a liability.")

    # ---------------- MODULE A
    H(doc, "Module A - Labor Telemetry & Hiring Dynamics", 2)
    H(doc, "Quantitative Openings by Geography", 3)
    TABLE(
        doc,
        ["Geography", "Est. Active Openings", "Demand Character"],
        [
            ["United States", "1,800 - 2,400", "Concentrated in financial services, SaaS observability vendors, and federal/defense modernization programs."],
            ["Europe / EMEA", "700 - 1,000", "Telecom and banking (Deutsche Telekom, BT, ING); GDPR-aware telemetry architecture valued."],
            ["India / APAC (GCC)", "2,500 - 3,500", "Largest pool; managed-services and GCC NOC-to-AIOps conversion programs at TCS, Infosys, Wipro, HCLTech, LTIMindtree, Accenture."],
            ["Global Remote", "350 - 500", "Observability vendors (Datadog, Grafana Labs, Dynatrace) and AIOps startups (BigPanda, Shoreline, Kleryt)."],
        ],
        widths=[1.6, 1.5, 3.9],
        caption="Active openings estimate, sampling window September 2026",
    )

    H(doc, "Compensation Bands (Annual, Base Salary)", 3)
    TABLE(
        doc,
        ["Percentile", "US (USD)", "India (INR LPA)", "Europe (EUR)"],
        [
            ["25th", "$96,000", "9 - 12", "55,000 - 65,000"],
            ["50th (median)", "$128,000", "16 - 22", "75,000 - 85,000"],
            ["75th", "$162,000", "28 - 38", "95,000 - 110,000"],
            ["90th", "$198,000", "45 - 60", "125,000+"],
        ],
        widths=[1.5, 1.8, 1.8, 1.9],
        caption="AIOps Engineer base salary composites; US TTC adds 10-20% bonus/equity",
    )
    CALLOUT(
        doc,
        "AIOps pay lags Cloud AI and GenAI roles by roughly 15-20% at the median, but the premium for "
        "candidates who can wire LLM incident copilots on top of classic observability (Module D) is "
        "re-opening the gap. India's GCC tier (JPMC, Standard Chartered, Walmart Global Tech, Target) "
        "pays 20-40% above the services tier for the same title.",
        title="Pay positioning.",
    )

    H(doc, "Top 15 Active Hiring Organizations", 3)
    TABLE(
        doc,
        ["Category", "Organizations"],
        [
            ["Observability / AIOps vendors", "Datadog, Splunk (Cisco), Dynatrace, IBM (instana / watsonx AIOps), ServiceNow (ITOM), PagerDuty, Grafana Labs"],
            ["AIOps-native startups (Series B-D)", "BigPanda, Shoreline.io, Moogsoft, Kleryt, Cleric, Resolve.ai"],
            ["Hyperscalers", "AWS (CloudWatch / Application Signals), Microsoft (Azure Monitor), Google (Cloud Operations suite)"],
            ["Enterprise & GCC", "JPMorganChase, Standard Chartered, Walmart Global Tech, TCS, Infosys, Accenture, HCLTech, LTIMindtree"],
        ],
        widths=[2.2, 4.8],
        caption="Where AIOps Engineers are being hired right now",
    )

    H(doc, "Experience Baseline & Transition Backgrounds", 3)
    P(doc,
      "Minimum tenure is 2-3 years in a monitoring-adjacent role; preferred is 4-6 years mixing "
      "infrastructure operations with scripting. There is no demand for fresh-graduate AIOps hires "
      "without an operations internship. The canonical feeder backgrounds, in observed order of frequency:")
    BULLETS(doc, [
        ("NOC / IT Service Desk / Sysadmin -> AIOps: ",
         "strongest volume path; requires adding Python + one metrics stack (Prometheus or Datadog) + "
         "basic statistics to existing incident fluency."),
        ("SRE / DevOps -> AIOps: ",
         "shortest path (3-6 months of skill-adjacency); already owns telemetry, needs anomaly-detection "
         "and event-correlation theory."),
        ("Network Engineer -> AIOps: ",
         "flows into telemetry-pipeline and eBPF-heavy teams; SNMP/NetFlow intuition maps directly to "
         "cardinality and sampling problems."),
        ("Data Analyst -> AIOps: ",
         "viable when paired with time-series forecasting skills (Prophet, Holt-Winters) and an "
         "observability-domain project."),
    ])

    # ---------------- MODULE B
    H(doc, "Module B - Role Taxonomy & Daily Operational Reality", 2)
    H(doc, "Boundary Mapping", 3)
    TABLE(
        doc,
        ["Adjacent Role", "They Own", "AIOps Owns", "Flashpoint"],
        [
            ["Data Engineering", "Business data pipelines (ETL, warehouse)", "Telemetry pipelines (metrics/log/trace ingest, cardinality control)", "Who pays for the log pipeline when it explodes in cost"],
            ["ML Research / Data Science", "Model development and experiments", "Deploying detection models into the alert path and measuring their precision/recall in production", "False-positive accountability after a model ships"],
            ["Platform DevOps / SRE", "CI/CD, cluster runtime, SLO definitions", "Noise reduction, correlation, post-incident automation of the detection layer", "Whether an alert that fired was 'actionable' - AIOps gets graded on it"],
            ["Solutions Architecture", "Customer-facing architecture decisions", "Internal telemetry architecture and MTTR outcomes", "Tool procurement recommendations (AIOps is the internal expert witness)"],
        ],
        widths=[1.5, 2.1, 2.2, 1.2],
        caption="Ownership boundaries",
    )

    H(doc, "Five Concrete Daily Operational Artifacts", 3)
    BULLETS(doc, [
        ("Alert-suppression pull request: ",
         "a reviewed change adding a maintenance window or dynamic threshold to a service's alert rules, "
         "with evidence (30-day alert history) that the suppressed volume was non-actionable."),
        ("Correlation-rule configuration: ",
         "YAML or visual-rule definitions that group related alerts (deployment event + latency spike + "
         "error-rate rise) into a single incident with a probable-cause annotation."),
        ("Incident post-mortem with detection analysis: ",
         "a blameless post-mortem that additionally grades the detection layer - time-to-detect, which "
         "alert fired first, which signals were ignored, what rule change prevents recurrence."),
        ("Anomaly-detector evaluation notebook: ",
         "a Jupyter notebook backtesting a candidate detector (e.g., Isolation Forest on 90 days of "
         "latency data) reporting precision, recall, and alert-volume delta against the current static "
         "thresholds."),
        ("Dashboard- and alerts-as-code commit: ",
         "Grafana dashboard JSON or Terraform for a monitor, applied through the same PR review pipeline "
         "as application code."),
    ])

    H(doc, "Core Daily Toolchain", 3)
    TABLE(
        doc,
        ["Layer", "Tools Used Daily"],
        [
            ["IDE / editors", "VS Code (+ Jupyter extension), PyCharm for detector services"],
            ["CLI utilities", "kubectl, promtool, curl, jq, logcli (Loki), AWS/Azure CLI, psql"],
            ["Metrics stores", "Prometheus (+ Thanos/Mimir), Datadog, CloudWatch, Dynatrace"],
            ["Log platforms", "Loki, Elasticsearch/OpenSearch, Splunk, Azure Log Analytics"],
            ["Tracing", "Tempo, Jaeger, Zipkin, OpenTelemetry Collector"],
            ["Alerting / paging", "Grafana Alerting, Alertmanager, PagerDuty, Opsgenie"],
            ["Incident / workflow", "Jira, ServiceNow ITSM, Slack workflows, Confluence"],
            ["Analysis", "Python (pandas, numpy, scikit-learn), Jupyter, Prophet, InfluxDB"],
        ],
        widths=[1.5, 5.5],
        caption="Daily driver toolchain",
    )

    # ---------------- MODULE C
    H(doc, "Module C - Exhaustive Technical Skills, Tools & Services Matrix", 2)
    TABLE(
        doc,
        ["Category", "Skill / Tool / Service", "Frequency"],
        [
            ["Core systems & languages", "Python (pandas, numpy, scikit-learn, requests)", "Critical"],
            ["Core systems & languages", "YAML/JSON authoring (alert rules, dashboards, collector configs)", "Critical"],
            ["Core systems & languages", "Go or Rust (reading and extending collector/exporter code)", "High"],
            ["Core systems & languages", "SQL for metric/log store queries", "Critical"],
            ["Telemetry collection", "OpenTelemetry (SDK, Collector pipelines, semantic conventions)", "Critical"],
            ["Telemetry collection", "Prometheus exporters, PromQL, recording rules, Thanos/Mimir long-term storage", "Critical"],
            ["Telemetry collection", "Fluent Bit / Vector / Logstash log shippers", "High"],
            ["Telemetry collection", "eBPF-based observability (Cilium Hubble, Pixie, bpftrace)", "Emerging"],
            ["Platforms", "Datadog (monitors, Watchdog, log pipelines), Dynatrace (Davis AI), Splunk (ITSI)", "Critical"],
            ["Platforms", "Elasticsearch / OpenSearch (index lifecycle, DSL queries)", "High"],
            ["Platforms", "Kubernetes (events, HPA signals, kube-state-metrics)", "Critical"],
            ["Platforms", "CloudWatch / Azure Monitor / Google Cloud Operations", "High"],
            ["Event correlation & alerting", "BigPanda, Moogsoft, IBM Watson AIOps, ServiceNow ITOM/ITSA", "High"],
            ["Event correlation & alerting", "Alertmanager (grouping, silences, inhibition), PagerDuty event orchestration", "Critical"],
            ["Anomaly detection & ML", "Isolation Forest, LOF, one-class SVM (scikit-learn)", "High"],
            ["Anomaly detection & ML", "Time-series decomposition and forecasting: STL, Holt-Winters, Prophet, ARIMA", "High"],
            ["Anomaly detection & ML", "Autoencoders / LSTM-AE for multivariate anomaly detection", "Emerging"],
            ["Anomaly detection & ML", "LLM incident copilots (RAG over runbooks and post-mortems)", "Emerging"],
            ["Automation", "Ansible / Runbook automation (Rundeck, Shoreline)", "High"],
            ["Automation", "GitHub Actions / Jenkins for alert-rule CI", "High"],
            ["Observability practice", "SLO/SLI engineering, error budgets, MTTR/MTTD measurement", "Critical"],
            ["ITSM & process", "ITIL v4 incident/problem/change management", "High"],
            ["Security-adjacent", "Audit-log pipelines, security monitoring handoff to SIEM", "Emerging"],
        ],
        widths=[1.7, 4.3, 1.0],
        caption="Skills matrix with market frequency (Critical / High / Emerging)",
    )

    # ---------------- MODULE D
    H(doc, "Module D - Deep Technical Reference Manual (The Living Textbook)", 2)
    H(doc, "Deep Theory: The Telemetry Data Flow", 3)
    P(doc,
      "Every AIOps architecture is a lossy funnel that trades fidelity for signal. The canonical "
      "production data flow, which you must be able to draw and defend in interviews:")
    CODE(doc, r"""
  APPLICATIONS / INFRA
   |  metrics (numeric, high-cardinality)      logs (discrete, verbose)      traces (sampled)
   v                v                v
 +---------------------------------------------------------------+
 |  COLLECTION LAYER                                             |
 |  OpenTelemetry SDK/Collector, node exporters, Fluent Bit      |
 |  - enrichment: k8s metadata, env, team ownership tags         |
 |  - filtering / tail-sampling (cost + cardinality control)     |
 +---------------------------------------------------------------+
   |                        |                        |
   v                        v                        v
 +---------------+  +----------------+  +---------------------+
 | METRICS TSDB  |  | LOG STORE      |  | TRACE STORE         |
 | Prom/Mimir/   |  | Loki/OpenSearch|  | Tempo/Jaeger        |
 | Thanos        |  |                |  | (tail-based sampling)|
 +---------------+  +----------------+  +---------------------+
   |                        |                        |
   +----------+-------------+-----------+------------+
              v
 +---------------------------------------------------------------+
 | STREAM / FEATURE LAYER                                        |
 | Kafka / vectorized windows: per-service rolling features      |
 | (p95 latency, error ratio, saturation, rate-of-change)        |
 +---------------------------------------------------------------+
              v
 +---------------------------------------------------------------+
 | DETECTION & CORRELATION LAYER  (the AIOps core)               |
 | 1. anomaly scoring per series (static, statistical, ML)       |
 | 2. event grouping: time-window + topology + similarity        |
 | 3. probable-cause ranking (dependency graph + change events)  |
 | 4. suppression / dedup (fingerprinting)                       |
 +---------------------------------------------------------------+
              v
 +---------------------------+     +---------------------------+
 | ALERT ROUTING             | --> | LLM INCIDENT COPILOT      |
 | Alertmanager/PagerDuty    |     | RAG over runbooks,        |
 | actionable pages only     |     | post-mortems, dashboards  |
 +---------------------------+     +---------------------------+
""", caption="Figure 1.1 - Canonical AIOps telemetry and detection pipeline")

    H(doc, "Deep Theory: Anomaly Detection Mathematics", 3)
    P(doc,
      "AIOps interviews test whether you know why a detector fires. Master these five formulations "
      "and their failure modes:")
    BULLETS(doc, [
        ("Z-score / robust Z (MAD): ",
         "z = (x - mean) / sigma flags |z| > 3; robust variant replaces mean/sigma with median and MAD "
         "(median absolute deviation scaled by 1.4826) because latency distributions are heavy-tailed. "
         "Failure mode: meaningless on strongly seasonal series."),
        ("EWMA control bands: ",
         "ewma_t = lambda*x_t + (1-lambda)*ewma_{t-1} with control limits mean +/- L*sigma*sqrt(lambda/"
         "(2-lambda)); lambda ~ 0.2-0.4 for metrics. Catches slow drifts that z-scores miss. Failure "
         "mode: adapts TO the anomaly if lambda too high (the boiling-frog failure)."),
        ("STL decomposition + residual bands: ",
         "decompose series into trend + seasonal + residual (STL, period = daily/weekly), alarm on "
         "residual exceeding k MADs. This is the correct baseline for traffic metrics with daily "
         "seasonality; Prophet generalizes it with changepoints and holiday regressors."),
        ("Isolation Forest: ",
         "ensemble of random split trees; anomaly score = 2^(-E(h)/c(n)) where h is path length and "
         "c(n) the average BST path length. O(n log n), no distance metric needed - the default choice "
         "for multivariate snapshot features. Failure mode: score drifts when feature distributions "
         "shift after a deploy; must retrain on rolling windows."),
        ("Autoencoder reconstruction error: ",
         "train AE/LSTM-AE on healthy windows, alarm when ||x - x_hat|| exceeds a calibrated "
         "percentile. Powerful for multivariate correlation but opaque; always ship with a "
         "counterfactual explanation (which features contributed most to the error)."),
    ])
    P(doc,
      "Detection is only half the job; correlation is the other. Event grouping combines three "
      "similarities: temporal (events within a sliding window), topological (events on services sharing "
      "a dependency path in the service graph), and content (Jaccard/cosine similarity of alert labels "
      "and log templates - production systems use log-template extraction, e.g., Drain-style parsing, "
      "then cluster templates). Probable-cause ranking multiplies these by change proximity: deploys, "
      "config changes, and autoscaling events inside the window raise a service's causal score.")

    H(doc, "Deep Theory: Alert Quality Economics", 3)
    CODE(doc, r"""
precision = TP / (TP + FP)          # of pages, fraction worth waking someone
recall    = TP / (TP + FN)          # of real incidents, fraction detected
MTTD      = mean(detect_time - fault_start)
MTTR      = mean(resolve_time - detect_time)
alert_budget = pages / on-call-week  # typically <= 2 pages/shift is sustainable

Noise spiral: 1 noisy page -> on-call ignores next -> recall drops silently.
The AIOps mandate: raise precision (fewer pages) without lowering recall (no missed
real incidents). Any detector change must report BOTH numbers on a backtest window.
""", caption="Figure 1.2 - The four numbers every AIOps change is graded on")

    H(doc, "Master Syllabus: What to Actually Study", 3)
    BULLETS(doc, [
        ("Foundations: ",
         "Google SRE Book (chapters on alerting philosophy) and Google SRE Workbook chapter 5 "
         "(alerting on SLOs) - the canonical texts for precision-first alerting."),
        ("OpenTelemetry: ",
         "the OTel specification (semantic conventions, Collector pipeline: receivers/processors/"
         "exporters) at opentelemetry.io/docs; tail-sampling processor docs."),
        ("Prometheus ecosystem: ",
         "Prometheus docs (data model, PromQL functions histogram_quantile, rate vs irate), Thanos "
         "and Mimir architecture docs for long-term storage and multi-tenancy."),
        ("Anomaly detection papers: ",
         "Liu et al., 'Isolation Forest' (ICDM 2008); Cleveland et al., 'STL: A Seasonal-Trend "
         "Decomposition Procedure' (1990); Hyndman & Athanasopoulos, 'Forecasting: Principles and "
         "Practice' (free online) chapters on exponential smoothing and ARIMA."),
        ("Log anomaly papers: ",
         "Du et al., 'DeepLog: Anomaly Detection from System Logs' (OSDI 2018); He et al., "
         "'Drain: An Online Log Parsing Approach' (ICWS 2017) - the template-extraction algorithm "
         "behind most log clustering."),
        ("AIOps platforms: ",
         "vendor docs: Datadog Watchdog and anomaly monitors, Dynatrace Davis causal engine docs, "
         "BigPanda correlation concepts, ServiceNow Predictive Intelligence."),
        ("LLM-for-ops: ",
         "RAG architecture chapters in this manual (Module 6D) plus PagerDuty/Cleric incident-copilot "
         "write-ups; learn retrieval over runbooks + structured incident timelines."),
    ])

    H(doc, "Canonical Code Pattern 1.1 - EWMA + Seasonal Baseline Anomaly Scorer", 3)
    P(doc,
      "A production-grade detector service pattern: stateful EWMA with robust control limits, seasonal "
      "guard, and hysteresis so a flapping metric cannot storm the pager. Memorize the structure - "
      "typed state, explicit None-guards, structured logging, and the two-out-of-three confirmation.")
    CODE(doc, r'''
from __future__ import annotations

import logging
import math
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

logger = logging.getLogger("aiops.detector")


@dataclass
class DetectorConfig:
    """Tunables for one metric stream. Percentiles are on the residual scale."""
    ewma_lambda: float = 0.30          # adaptivity; higher = faster forget
    z_alarm: float = 4.0               # robust-z threshold (MAD-scaled)
    z_warn: float = 2.5                # soft threshold, needs confirmation
    min_history: int = 40              # warmup before scoring
    mad_floor: float = 1e-6            # avoid div-by-zero on flat series
    confirm_windows: int = 2           # consecutive breaches to escalate
    seasonal_period: Optional[int] = None  # e.g. 1440 for per-minute daily


@dataclass
class DetectorState:
    ewma: float = 0.0
    sq_dev: float = 0.0                # EW variance estimate
    n: int = 0
    residuals: list[float] = field(default_factory=list)
    breach_streak: int = 0


class EWMAAnomalyDetector:
    """Streaming anomaly score for one metric series with hysteresis.

    Score = robust z of residual against EWMA baseline, where residual is the
    raw value minus a seasonal expectation (if configured). Emits one of:
    "normal", "warn", "alarm". Two consecutive warn-level breaches escalate
    to alarm; a normal reading resets the streak (hysteresis).
    """

    def __init__(self, config: DetectorConfig) -> None:
        if not 0.0 < config.ewma_lambda <= 1.0:
            raise ValueError("ewma_lambda must be in (0, 1]")
        self.cfg = config
        self.state = DetectorState()

    def _seasonal_expectation(self, ts: float) -> float:
        if not self.cfg.seasonal_period:
            return 0.0
        slot = int(ts // 60) % self.cfg.seasonal_period
        hist = [r for i, r in enumerate(self.state.residuals) if i % self.cfg.seasonal_period == slot]
        return float(np.median(hist)) if len(hist) >= 3 else 0.0

    def update(self, value: float, ts: Optional[float] = None) -> str:
        ts = ts if ts is not None else time.time()
        st = self.state
        st.n += 1

        if st.n == 1:  # first observation initializes the baseline
            st.ewma = value
            return "normal"

        residual = value - st.ewma - self._seasonal_expectation(ts)
        st.residuals.append(residual)
        if len(st.residuals) > 5 * (self.cfg.seasonal_period or 100):
            st.residuals = st.residuals[-2 * (self.cfg.seasonal_period or 100):]

        # Robust scale from a rolling window of residuals (MAD * 1.4826 ~ sigma)
        window = np.asarray(st.residuals[-200:], dtype=float)
        mad = float(np.median(np.abs(window - np.median(window))))
        sigma = max(1.4826 * mad, self.cfg.mad_floor)

        # Update EWMA baseline AFTER scoring so the alarm cannot hide itself
        prev = st.ewma
        st.ewma += self.cfg.ewma_lambda * (value - st.ewma)
        st.sq_dev += (value - prev) * (value - st.ewma)

        z = (value - prev) / sigma
        if st.n < self.cfg.min_history:
            return "normal"

        if abs(z) >= self.cfg.z_alarm:
            st.breach_streak += 1
            level = "alarm" if st.breach_streak >= self.cfg.confirm_windows else "warn"
            logger.warning("z=%.2f streak=%d metric_value=%.4f level=%s", z, st.breach_streak, value, level)
            return level
        if abs(z) >= self.cfg.z_warn:
            st.breach_streak += 1
            return "warn"
        st.breach_streak = 0
        return "normal"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    det = EWMAAnomalyDetector(DetectorConfig())
    rng = np.random.default_rng(7)
    for t in range(200):
        level = det.update(float(100 + rng.normal(0, 2)))
    level = det.update(160.0)  # injected spike
    print("spike verdict:", level)
''', caption="Code 1.1 - ewma_detector.py: streaming anomaly scorer with hysteresis")

    H(doc, "Canonical Code Pattern 1.2 - Token-Bucket Rate Limiter with Backoff and Jitter", 3)
    P(doc,
      "The rate limiter below is the cross-role canonical version (it reappears in Modules 6D and 7D); "
      "AIOps teams use exactly this pattern to protect alert-webhook and incident-API integrations "
      "from upstream rate limits during incident storms - precisely when you can afford a 429 storm "
      "least. Full theory and failure modes are documented here once.")
    CODE(doc, r'''
from __future__ import annotations

import asyncio
import logging
import random
import time
from dataclasses import dataclass

logger = logging.getLogger("aiops.ratelimit")


@dataclass
class TokenBucket:
    """Classic token bucket: refill rate caps sustained throughput, capacity
    absorbs bursts. Thread-safe via a single asyncio loop assumption."""
    capacity: float
    refill_per_sec: float
    tokens: float
    last_refill: float = 0.0

    def __post_init__(self) -> None:
        if self.last_refill == 0.0:
            self.last_refill = time.monotonic()
        if self.tokens > self.capacity:
            raise ValueError("tokens cannot exceed capacity")

    def _refill(self) -> None:
        now = time.monotonic()
        self.tokens = min(self.capacity, self.tokens + (now - self.last_refill) * self.refill_per_sec)
        self.last_refill = now

    def try_acquire(self, amount: float = 1.0) -> bool:
        self._refill()
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False

    def wait_time(self, amount: float = 1.0) -> float:
        self._refill()
        deficit = amount - self.tokens
        return max(0.0, deficit / self.refill_per_sec)


class AdaptiveClient:
    """HTTP-call wrapper with token-bucket admission, capped exponential
    backoff, and full jitter on 429/5xx. Admission control BEFORE the call
    protects the upstream; backoff AFTER protects the retry loop from
    retry-storm amplification during incidents."""

    def __init__(self, capacity: float = 10.0, refill_per_sec: float = 5.0,
                 max_retries: int = 6, base_delay: float = 0.5) -> None:
        self.bucket = TokenBucket(capacity=capacity, refill_per_sec=refill_per_sec,
                                  tokens=capacity)
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def call(self, fn, *args, **kwargs):
        """fn: any awaitable factory (e.g. lambda: session.get(url))."""
        if not self.bucket.try_acquire(1.0):
            wait = self.bucket.wait_time(1.0)
            logger.info("rate limited locally, sleeping %.2fs", wait)
            await asyncio.sleep(wait)

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = await fn(*args, **kwargs)
                status = getattr(resp, "status", None)
                if status is not None and (status == 429 or status >= 500):
                    raise _TransientError(f"upstream status {status}")
                return resp
            except (_TransientError, asyncio.TimeoutError, ConnectionError) as exc:
                last_exc = exc
                # exponential backoff with FULL jitter: delay uniform in
                # [0, min(cap, base * 2**attempt)] - full jitter beats equal
                # jitter because it decorrelates synchronized retryers.
                cap = 30.0
                delay = random.uniform(0.0, min(cap, self.base_delay * (2 ** attempt)))
                retry_after = getattr(resp, "headers", {}).get("Retry-After") \
                    if "resp" in locals() and resp is not None else None
                if retry_after is not None and retry_after.isdigit():
                    delay = max(delay, float(retry_after))
                logger.warning("attempt %d failed (%s), backing off %.2fs",
                               attempt + 1, exc, delay)
                await asyncio.sleep(delay)
        raise RuntimeError(f"exhausted {self.max_retries} retries") from last_exc


class _TransientError(Exception):
    pass


if __name__ == "__main__":
    async def _demo() -> None:
        client = AdaptiveClient()
        async def fake_call():
            return type("R", (), {"status": 200, "headers": {}})()
        result = await client.call(fake_call)
        print("status:", result.status)

    asyncio.run(_demo())
''', caption="Code 1.2 - rate_limiter.py: token bucket + exponential backoff with full jitter")

    H(doc, "Failure Modes & Edge Cases (AIOps)", 3)
    BULLETS(doc, [
        ("Seasonality drift: ",
         "static baselines retrained weekly miss traffic-pattern shifts (new market launch). Fix: STL "
         "residuals + rolling retrain + changepoint detection (PELT) on the baseline itself."),
        ("The boiling-frog EWMA: ",
         "lambda too high lets the baseline absorb a slow leak; the anomaly becomes the new normal. "
         "Fix: dual-timescale baselines (fast EWMA + slow daily median) and alert on their divergence."),
        ("Alert storms / dedup fingerprint collisions: ",
         "one upstream failure fans out to hundreds of child alerts. Fingerprint on (service, check, "
         "topology parent) not raw labels; add inhibition: child alerts suppressed while the parent "
         "resource is alarming."),
        ("Metric cardinality explosion: ",
         "a single unbounded label (user_id, request_id) turns a 50k-series TSDB into 50M series and "
         "OOMs Prometheus. Guardrails in the collector: drop/rewrite rules, cardinality budgets per "
         "team, and label allow-lists reviewed like code."),
        ("Silent trace sampling bias: ",
         "head-based sampling drops exactly the slow traces you need; error and high-latency traces "
         "are systematically under-represented. Fix: tail-based sampling with latency and error "
         "policies before it silently truncates your SLO evidence."),
        ("Clock skew between collectors: ",
         "misaligned timestamps reorder events inside correlation windows and split one incident into "
         "two. Enforce NTP, and use collector-side ingestion timestamps with bounded clock-skew "
         "tolerance in grouping."),
        ("Backtest flattery: ",
         "a detector backtested on data it was tuned against overstates precision. Hold out entirely "
         "separate incident windows (and always include the boring weeks with no incidents - false-"
         "positive rate is measured there)."),
        ("Vector index staleness (for runbook RAG): ",
         "retrieval serves last quarter's runbook after an architecture change; the LLM copilot then "
         "confidently prescribes an obsolete remediation. Fix: source-controlled embeddings with "
         "content-hash freshness checks and invalidation on doc merge."),
    ])

    # ---------------- MODULE E
    H(doc, "Module E - Interview Mechanics & Hidden Hiring Patterns", 2)
    H(doc, "ATS Screening Triggers", 3)
    BULLETS(doc, [
        ("Must-appear keywords: ",
         "AIOps, observability, Prometheus or Datadog or Splunk, MTTR/MTTD reduction (with a number), "
         "incident management, root cause analysis, OpenTelemetry, SLO, Python, Kubernetes, ITIL."),
        ("Phrasing that ranks: ",
         "quantified outcomes - 'reduced paging volume 63% via correlation rules and dynamic "
         "thresholds', 'cut MTTD from 18m to 90s with trace-informed alerting'."),
        ("Immediate-rejection anti-patterns: ",
         "'familiar with monitoring tools' with no named stack; zero numbers anywhere in the resume; "
         "describing only ticket-queue work without any automation; resume keyword-stuffing ML terms "
         "(deep learning, LLM) with no artifact or project behind them."),
    ])

    H(doc, "Interview Loop Breakdown", 3)
    TABLE(
        doc,
        ["Round", "Format", "What Is Actually Being Tested"],
        [
            ["Recruiter screen (30m)", "Background + motivation", "Coherent story from ops to AIOps; salary alignment; incident-war stories told calmly"],
            ["Technical screen (60m)", "Live coding / tooling Q&A", "Python fluency (pandas, generators, datetime handling), PromQL/SQL, practical alerting judgment"],
            ["Take-home or panel (2-4h)", "Detector or dashboard exercise", "Does the candidate backtest before shipping? Are precision/recall reported? Code quality under time pressure"],
            ["System design (60m)", "Design observability for a 200-service platform", "Cardinality control, sampling strategy, multi-tenant cost isolation, correlation architecture"],
            ["Behavioral / on-call (45m)", "STAR incident deep-dive", "Ownership during 3am incidents, blameless post-mortem instincts, communication under pager pressure"],
        ],
        widths=[1.5, 1.9, 3.6],
        caption="Typical loop: 4-5 rounds",
    )

    H(doc, "Five Real Interview Questions with Model Answers", 3)
    NUMBERS(doc, [
        ("Design an anomaly-detection strategy for p95 latency of a checkout API. ",
         "Model answer: start with SLO-based static alerts (fast, explainable); layer STL residuals "
         "for seasonal adjustment; add EWMA robust-z for drift; only then consider Isolation Forest on "
         "multivariate features (latency + traffic + error ratio + saturation). Require backtest on 90 "
         "days with held-out incident windows; report precision, recall, and page-volume delta; ship "
         "behind a shadow mode first. Mention the boiling-frog EWMA failure and hysteresis."),
        ("You inherit a system producing 4,000 alerts/week and 70% of pages are ignored. What do you do first? ",
         "Model answer: measure before touching - label 2 weeks of pages actionable/not; deduplicate by "
         "fingerprint and compute the true distinct-alert count; identify the top 10 alert sources "
         "(usually 3 rules produce 60% of noise); fix by dynamic thresholds or alert removal with "
         "evidence; add inhibition for dependency fan-out; set an alert budget per service and gate new "
         "alerts on backtest evidence. Quote the noise-spiral mechanism as the business risk."),
        ("Prometheus is OOMing after a new microservice ships. Diagnose. ",
         "Model answer: check series count growth (increase of active series and head-chunk memory); "
         "find the unbounded label (grep scrape targets and metric HELP lines; kube-state-metrics "
         "cardinality tools); apply collector-level drop/rewrite immediately, then negotiate which "
         "dimensions the team actually queries; add cardinality budgets and a CI check that rejects "
         "metrics with high-cardinality labels; consider splitting to a dedicated Prometheus or "
         "federated hierarchy for that team."),
        ("How do you correlate a latency spike across 40 microservices without drowning in alerts? ",
         "Model answer: build the dependency graph (from traces/OTel resource attributes, service mesh, "
         "or cmdb), ingest deploy/config events into the same timeline, group alerts within a sliding "
         "window by topology adjacency and label similarity, rank probable causes by graph distance to "
         "the change events, and present one incident with an annotated timeline; validate with "
         "post-mortem ground truth on the last 20 incidents."),
        ("Where does an LLM copilot genuinely help incident response, and where does it hurt? ",
         "Model answer: helps - summarizing the incident timeline, retrieving similar past incidents "
         "and their fixes (RAG over post-mortems), drafting the first-pass post-mortem, translating "
         "runbooks into next actions; hurts - as the primary detector (hallucinated root causes erode "
         "trust), on live blast-radius decisions without human approval, and when the runbook index is "
         "stale. Guardrails: citations required, read-only tools by default, HITL for any mutation, "
         "and evals on historical incidents with known causes."),
    ])

    # ---------------- MODULE F
    H(doc, "Module F - Production Capstone Specifications", 2)
    H(doc, "Capstone 1.1 - Self-Hosted AIOps Platform with LLM Incident Copilot", 3)
    P(doc,
      "Proves you can build the entire funnel of Figure 1.1 on open source, including cardinality "
      "control and an evaluable detector. This is the strongest possible artifact for AIOps interviews "
      "because it demonstrates every layer, not just one tool.")
    BULLETS(doc, [
        ("Architecture: ",
         "docker-compose stack: OTel Collector (receivers: hostmetrics, redis, sample app; processors: "
         "batch, filter, resource-detection) -> Prometheus (metrics) + Loki (logs) + Tempo (traces); "
         "Grafana for visualization; a Python 'detector-service' consuming Prometheus remote-write or "
         "the HTTP API, running Code 1.1 per series; Alertmanager routing to a webhook; a FastAPI "
         "'incident-copilot' that receives webhooks, retrieves runbooks from a pgvector-backed RAG "
         "index, and posts a cited summary to Slack."),
        ("Verification tests: ",
         "(1) chaos test: kill the sample app's dependency and assert a grouped incident - not N alerts - "
         "arrives in Slack within 60s; (2) detector backtest: replay 7 days of synthetic series with 5 "
         "injected faults, assert precision >= 0.8 and recall >= 1.0 on fault windows; (3) cardinality "
         "test: ship a bad label and prove the collector drop-rule rejects it; (4) copilot citation "
         "test: every Slack answer must contain >= 1 runbook citation resolvable to a source document."),
    ])
    H(doc, "Capstone 1.2 - MTTR Reduction Engine for an Existing Monitoring Stack", 3)
    P(doc,
      "Targets the enterprise reality that you cannot rip out Datadog/Splunk. Demonstrates "
      "platform-agnostic value: analytics and automation on top of incumbent tooling.")
    BULLETS(doc, [
        ("Architecture: ",
         "Datadog (or Splunk) webhooks -> FastAPI ingest -> Postgres incident store (dedup fingerprints, "
         "topology tags, change events from GitHub Actions/CDC) -> correlation worker (time-window + "
         "topology grouping in Python) -> Jira/ServiceNow incident creation -> weekly analytics job "
         "computing MTTD/MTTR, precision of pages, and top-noise report -> optional RAG copilot over "
         "the accumulated incident corpus (LlamaIndex + pgvector)."),
        ("Verification tests: ",
         "replay harness that feeds 30 days of historical webhooks and asserts grouping matches the "
         "human-curated incident list with >= 85% F1; idempotency test (duplicate webhook replay "
         "creates one incident); latency test (webhook-to-incident creation p95 < 5s); a one-page "
         "before/after report generated automatically."),
    ])
    CALLOUT(
        doc,
        "Package both capstones with a README that leads with the numbers (page-volume delta, precision/"
        "recall, MTTD/MTTR), not the architecture diagram. AIOps interviewers are precision-recall "
        "people; give them the confusion matrix in the first ten lines.",
        title="Portfolio packaging.",
    )


