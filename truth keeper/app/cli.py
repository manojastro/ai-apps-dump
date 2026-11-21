"""Small CLI for local demos.

    python -m app.cli seed        # generate data (if missing) and reset the sandbox
    python -m app.cli run         # detect + propose on the sandbox, print a summary
    python -m app.cli status      # queue stats
"""

from __future__ import annotations

import argparse
import json

from app.applier.sandbox import reset_sandbox, sandbox_ready
from app.approval.store import Store
from app.config import get_settings
from app.core import pipeline
from app.llm.client import LLMClient
from app.tracing import setup_tracing
from data.generator.generate import generate


def seed(force: bool = False) -> None:
    s = get_settings()
    if force or not (s.generated_dir / "crm.db").exists() or not s.ground_truth.exists():
        generate(42, 500, s.generated_dir, s.ground_truth)
        print(f"generated data in {s.generated_dir}")
    if force or not sandbox_ready(s.sandbox_dir):
        reset_sandbox(s.generated_dir, s.sandbox_dir)
        print(f"sandbox reset in {s.sandbox_dir}")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_seed = sub.add_parser("seed")
    p_seed.add_argument("--force", action="store_true")
    p_run = sub.add_parser("run")
    p_run.add_argument("--limit", type=int, default=None)
    p_run.add_argument("--prompt", default=None)
    sub.add_parser("status")
    args = ap.parse_args(argv)
    s = get_settings()
    if args.cmd == "seed":
        seed(args.force)
        return
    setup_tracing(s.otel_endpoint)
    store = Store(s.state_db, regressions_dir=s.regressions_dir)
    try:
        if args.cmd == "run":
            if s.llm_mode == "real" and args.limit is None:
                raise SystemExit("LLM_MODE=real: pass --limit N so the cost is bounded.")
            seed()
            r = pipeline.run(store, LLMClient(s), s.sandbox_dir, args.prompt or s.prompt_version, limit=args.limit)
            print(json.dumps(r.to_dict(), indent=2))
        print(json.dumps(store.stats(), indent=2))
    finally:
        store.close()


if __name__ == "__main__":
    main()
