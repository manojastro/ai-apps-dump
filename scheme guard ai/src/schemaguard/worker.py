"""Registry poller (the worker container). Detects new schema versions and starts runs.

Idempotent twice over: it remembers the last version seen per subject, and the service refuses to
start a second run for the same topic + schema.
"""

from __future__ import annotations

import time

from schemaguard.observability import get_logger
from schemaguard.schemas.registry import RegistryUnavailable, SchemaRegistry, topic_for_subject
from schemaguard.service import SchemaGuardService

log = get_logger("worker")

STATE_SQL = "create table if not exists poller_state (subject text primary key, version integer not null)"


class RegistryPoller:
    def __init__(self, svc: SchemaGuardService, registry: SchemaRegistry):
        self.svc = svc
        self.registry = registry
        svc.db.execute(STATE_SQL)

    def _seen(self, subject: str) -> int | None:
        rows = self.svc.db.query("select version from poller_state where subject = ?", (subject,))
        return int(rows[0][0]) if rows else None

    def _mark(self, subject: str, version: int) -> None:
        self.svc.db.execute("delete from poller_state where subject = ?", (subject,))
        self.svc.db.execute("insert into poller_state(subject, version) values (?, ?)", (subject, version))

    def poll_once(self) -> list[str]:
        """Returns run ids started (or found) for new versions."""
        started = []
        for subject in self.registry.subjects():
            versions = self.registry.versions(subject)
            if not versions:
                continue
            seen = self._seen(subject)
            if seen is None:  # first sight: baseline, no run
                self._mark(subject, versions[-1])
                continue
            for v in [x for x in versions if x > seen]:
                prev = max((x for x in versions if x < v), default=None)
                new = self.registry.get(subject, v)
                old = self.registry.get(subject, prev).schema if prev else None
                run_id, created = self.svc.submit_change(
                    topic_for_subject(subject),
                    new.schema,
                    old,
                    source="registry-poller",
                    subject=subject,
                    old_version=prev,
                    new_version=v,
                )
                log.info(
                    "schema version detected",
                    extra={"subject": subject, "version": v, "run": run_id, "new_run": created},
                )
                started.append(run_id)
                self._mark(subject, v)
        return started

    def run_forever(self, interval_s: float) -> None:  # pragma: no cover - loop
        backoff = interval_s
        while True:
            try:
                self.poll_once()
                backoff = interval_s
            except RegistryUnavailable as exc:
                backoff = min(backoff * 2, 300)
                log.error(
                    "registry unavailable; backing off", extra={"error": str(exc), "retry_in_s": backoff}
                )
            except Exception:
                log.exception("poll failed")
            time.sleep(backoff)
