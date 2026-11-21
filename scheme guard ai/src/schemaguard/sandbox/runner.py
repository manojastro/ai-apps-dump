"""Sandbox entry point: `python -I -m schemaguard.sandbox.runner --pipeline DIR --out FILE`.

Runs in a separate process with a timeout. Python-level network access is disabled before the
pipeline runs (best effort; in containers the worker also runs without extra network). DuckDB runs
in-process on a local file.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path


def disable_network() -> None:
    def _blocked(*_a: object, **_k: object) -> None:
        raise OSError("network access is disabled in the SchemaGuard sandbox")

    socket.socket.connect = _blocked  # type: ignore[method-assign,assignment]
    socket.socket.connect_ex = _blocked  # type: ignore[method-assign,assignment]
    socket.create_connection = _blocked  # type: ignore[assignment]
    socket.getaddrinfo = _blocked  # type: ignore[assignment]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pipeline", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args(argv)
    disable_network()
    from schemaguard.pipeline import run_pipeline

    try:
        result = run_pipeline(args.pipeline, args.pipeline / "warehouse.duckdb")
        payload = {**result.to_dict(), "failures": result.failures(), "error": ""}
    except Exception as exc:  # report, never crash silently
        payload = {
            "ok": False,
            "tasks": [],
            "tests": [],
            "failures": [f"runner error: {exc}"],
            "error": str(exc),
        }
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
