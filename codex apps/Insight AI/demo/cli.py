import argparse
import asyncio
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

import httpx


def token():
    path = Path(".productionlens/demo-control.txt")
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        path.write_text(secrets.token_urlsafe(32))
        path.chmod(0o600)
    return path.read_text().strip()


def up():
    children = []
    try:
        for name, port in [("checkout", 8100), ("payment", 8101), ("inventory", 8102)]:
            env = {**os.environ, "DEMO_SERVICE": name, "DEMO_CONTROL_TOKEN": token()}
            child = subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "demo.app:app",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                    "--no-access-log",
                ],
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            children.append(child)
        print(
            "Demo checkout: http://127.0.0.1:8100. Use python -m demo.cli traffic to generate real requests.",
            flush=True,
        )
        while all(c.poll() is None for c in children):
            time.sleep(1)
    finally:
        for child in children:
            child.terminate()
        for child in children:
            child.wait(timeout=10)


async def traffic(count=60):
    latencies, errors = [], 0
    async with httpx.AsyncClient(timeout=3) as client:
        for _ in range(count):
            start = time.perf_counter()
            try:
                response = await client.post("http://127.0.0.1:8100/request")
                errors += int(response.status_code >= 400)
            except httpx.HTTPError:
                errors += 1
            latencies.append((time.perf_counter() - start) * 1000)
            await asyncio.sleep(0.04)
    return {
        "mode": "live_demo",
        "samples": count,
        "errors": errors,
        "error_rate": errors / count,
        "p95_ms": round(sorted(latencies)[min(count - 1, int(count * 0.95))], 2),
        "observed_at": time.time(),
    }


def fault(name, seconds):
    target = 8101 if name == "payment_delay" else 8100
    ports = [8100, 8101] if name == "reset" else [target]
    for port in ports:
        response = httpx.post(
            f"http://127.0.0.1:{port}/control/fault",
            headers={"x-demo-control": token()},
            json={"fault": name, "seconds": seconds},
            timeout=5,
        )
        response.raise_for_status()
    print(f"Demo operation {name} applied with maximum duration {seconds}s.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["up", "traffic", "fault", "reset"])
    parser.add_argument(
        "--fault",
        choices=["payment_delay", "config_regression", "pool_exhaustion", "cpu_saturation"],
        default="payment_delay",
    )
    parser.add_argument("--seconds", type=int, default=30)
    parser.add_argument("--count", type=int, default=60)
    args = parser.parse_args()
    if args.command == "up":
        up()
    elif args.command == "traffic":
        if not 1 <= args.count <= 1000:
            parser.error("count must be 1..1000")
        print(json.dumps(asyncio.run(traffic(args.count)), indent=2))
    else:
        fault("reset" if args.command == "reset" else args.fault, args.seconds)
