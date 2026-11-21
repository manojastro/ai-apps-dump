"""Measures actual local demo traffic; use after python -m demo.cli up."""

import asyncio
import json
import time
from pathlib import Path

import httpx

from demo.cli import fault, traffic


async def main():
    result = {
        "mode": "live_demo",
        "timestamp": time.time(),
        "configuration": "Windows local processes; no container CPU limit",
        "samples": [],
    }
    # Warm instrumentation and connection paths; exclude warmup from measurements.
    await traffic(10)
    result["samples"].append({"scenario": "healthy", **await traffic(40)})
    for family in ["payment_delay", "config_regression", "pool_exhaustion", "cpu_saturation"]:
        fault("reset", 1)
        await asyncio.sleep(0.5)
        fault(family, 60)
        await asyncio.sleep(0.7)
        measured = await traffic(35)
        metrics = httpx.get("http://127.0.0.1:8100/metrics").text
        result["samples"].append(
            {
                "scenario": family,
                **measured,
                "observed_gauges": [
                    line
                    for line in metrics.splitlines()
                    if line.startswith(("demo_cpu_ratio{", "demo_pool_usage{", "demo_pool_wait_seconds{"))
                ],
            }
        )
        fault("reset", 1)
        await asyncio.sleep(0.5)
        result["samples"].append({"scenario": family + "_recovery", **await traffic(35)})
        print(
            f"Measured {family}: {measured['errors']}/{measured['samples']} errors; p95 {measured['p95_ms']}ms",
            flush=True,
        )
    logs = httpx.get("http://127.0.0.1:8100/telemetry/logs").json()["records"]
    result["trace_context_present"] = all(
        row["trace_id"] != "0" * 32 and len(row["span_id"]) == 16 for row in logs
    )
    result["control_denies_unauthorized"] = (
        httpx.post("http://127.0.0.1:8100/control/fault", json={"fault": "reset"}).status_code == 403
    )
    Path("docs/evidence").mkdir(exist_ok=True, parents=True)
    Path("docs/evidence/live-demo-measurements.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
