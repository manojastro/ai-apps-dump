import threading
from datetime import timedelta

from sqlalchemy import func, select

from app import clock
from app.data import db
from app.data.models import Appointment, Observation, Outbox, Patient, Practitioner, Slot, SupplyItem
from app.data.seed import INJECTION_TEXTS, SeedConfig, fingerprint, seed
from app.queue import outbox
from app.queue.worker import Worker
from tests.conftest import SMALL, T0


def test_full_seed_counts(fresh_db):
    seed()
    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(Patient)) == 200
        assert s.scalar(select(func.count()).select_from(Practitioner)) == 8
        assert s.scalar(select(func.count()).select_from(Slot)) == 8 * 4 * 5 * 8
        assert s.scalar(select(func.count()).select_from(Appointment)) == 300
        assert s.scalar(select(func.count()).select_from(Observation)) == 150
        assert s.scalar(select(func.count()).select_from(SupplyItem)) == 40
        texts = s.scalars(select(Observation.free_text)).all()
        assert any(t in INJECTION_TEXTS for t in texts)
        above = s.scalar(select(func.count()).select_from(Observation)
                         .where((Observation.pain_score >= 7) | (Observation.temperature >= 38.0)))
        assert above > 10


def test_seed_is_reproducible(tmp_path):
    prints = []
    for i in range(2):
        clock.freeze(T0)
        db.init_db(f"sqlite:///{tmp_path / f'r{i}.db'}")
        seed(SeedConfig(**SMALL))
        prints.append(fingerprint())
    clock.reset()
    assert prints[0] == prints[1]


def test_two_workers_never_double_claim(fresh_db):
    n = 120
    for i in range(n):
        outbox.enqueue("TIMER_DUE", {"i": i})
    claimed: list[tuple[str, int]] = []
    lock = threading.Lock()

    def run(name):
        while True:
            ev = outbox.claim(name)
            if ev is None:
                return
            with lock:
                claimed.append((name, ev.id))

    threads = [threading.Thread(target=run, args=(f"w{i}",)) for i in range(6)]
    [t.start() for t in threads]
    [t.join() for t in threads]
    ids = [c[1] for c in claimed]
    assert len(ids) == n and len(set(ids)) == n


def test_crash_mid_processing_is_retried_not_lost(fresh_db):
    outbox.enqueue("TIMER_DUE", {"x": 1})

    class Boom(BaseException):  # simulates kill -9: not caught by the worker
        pass

    def dying(_ev):
        raise Boom()

    try:
        Worker("w1", dying).run_once()
    except Boom:
        pass
    with db.session() as s:
        assert s.scalars(select(Outbox.status)).one() == "CLAIMED"
    # new worker, before lease expiry: nothing to claim
    seen = []
    assert Worker("w2", lambda e: seen.append(e)).run_once() is False
    clock.advance(timedelta(seconds=120))  # lease expires
    assert Worker("w2", lambda e: seen.append(e)).run_once() is True
    assert len(seen) == 1 and seen[0].attempts == 2
    with db.session() as s:
        assert s.scalars(select(Outbox.status)).one() == "DONE"


def test_backoff_then_dead_after_max_attempts(fresh_db):
    outbox.enqueue("STOCK_LOW", {})

    def bad(_ev):
        raise RuntimeError("nope")

    w = Worker("w1", bad)
    waits = []
    for _attempt in range(1, 6):
        assert w.run_once() is True
        with db.session() as s:
            ev = s.scalars(select(Outbox)).one()
        if ev.status == "PENDING":
            waits.append((ev.available_at - clock.now()).total_seconds())
            assert w.run_once() is False  # backoff: not available yet
            clock.advance(timedelta(seconds=waits[-1]))
    assert waits == [2, 4, 8, 16]
    with db.session() as s:
        ev = s.scalars(select(Outbox)).one()
    assert ev.status == "DEAD" and ev.attempts == 5


def test_dedupe_key_makes_enqueue_idempotent(fresh_db):
    a = outbox.enqueue("TIMER_DUE", {}, dedupe_key="k1")
    b = outbox.enqueue("TIMER_DUE", {}, dedupe_key="k1")
    assert a == b
