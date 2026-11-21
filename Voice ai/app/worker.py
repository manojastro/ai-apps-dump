"""Long-running worker process: claims events and drives workflows. `python -m app.worker`.

Runs N asyncio workers plus a housekeeping loop (approval expiry, waking decided workflows). On startup it
resumes unfinished workflows from the database.
"""
from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv

from app.data.db import init_db
from app.obs.tracing import setup_tracing
from app.orchestrator.engine import Orchestrator
from app.queue.worker import Worker

log = logging.getLogger("eir.worker")


async def housekeeping(orch: Orchestrator, every: float = 5.0) -> None:
    while True:
        await asyncio.to_thread(orch.tick)
        await asyncio.sleep(every)


async def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)
    init_db()
    setup_tracing()
    orch = Orchestrator()
    n = int(os.environ.get("EIR_WORKERS", "2"))
    resumed = await asyncio.to_thread(orch.resume)
    log.info("started %s workers; resumed %s unfinished workflows (LLM mode: %s)", n, resumed, orch.llm.mode)
    workers = [Worker(f"worker-{os.getpid()}-{i}", orch.handle_event) for i in range(n)]
    await asyncio.gather(housekeeping(orch), *(w.run_forever() for w in workers))


if __name__ == "__main__":
    asyncio.run(main())
