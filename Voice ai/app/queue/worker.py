from __future__ import annotations

import asyncio
import logging
from typing import Callable

from app.queue import outbox

log = logging.getLogger("eir.worker")


class Worker:
    def __init__(self, worker_id: str, handler: Callable[[outbox.ClaimedEvent], None]):
        self.worker_id = worker_id
        self.handler = handler

    def run_once(self) -> bool:
        """Claim and process one event. Returns False when nothing was available.

        Only `Exception` is caught: a hard crash (BaseException / process kill) leaves the event
        CLAIMED, and the lease expiry in `reclaim_expired` makes it retry.
        """
        outbox.reclaim_expired()
        ev = outbox.claim(self.worker_id)
        if ev is None:
            return False
        try:
            self.handler(ev)
        except Exception as exc:  # noqa: BLE001
            status = outbox.fail(ev.id, self.worker_id, f"{type(exc).__name__}: {exc}")
            log.warning("event %s failed (%s) -> %s", ev.id, exc, status)
        else:
            outbox.complete(ev.id, self.worker_id)
        return True

    def run_until_empty(self, max_events: int = 10_000) -> int:
        n = 0
        while n < max_events and self.run_once():
            n += 1
        return n

    async def run_forever(self, poll_seconds: float = 1.0) -> None:
        while True:
            did = await asyncio.to_thread(self.run_once)
            if not did:
                await asyncio.sleep(poll_seconds)
