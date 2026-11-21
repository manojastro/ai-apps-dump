"""M3 dataset guards: counts, splits, labels, injection traps."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(p: Path) -> list[dict]:
    return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]


def test_counts_and_splits() -> None:
    all_t = load(ROOT / "data" / "tickets.jsonl")
    dev = load(ROOT / "data" / "splits" / "dev.jsonl")
    test = load(ROOT / "data" / "splits" / "test.jsonl")
    assert len(all_t) == 200
    assert len(dev) == 150
    assert len(test) == 50
    # no overlap between dev and test (no leakage check)
    dev_ids = {t["ticket_id"] for t in dev}
    test_ids = {t["ticket_id"] for t in test}
    assert not dev_ids & test_ids


def test_all_synthetic_and_labelled() -> None:
    for t in load(ROOT / "data" / "tickets.jsonl"):
        assert t["synthetic"] is True
        assert t["category"] in {
            "network",
            "hardware",
            "software",
            "access",
            "email",
            "database",
            "security",
        }
        assert t["impact"] in (1, 2, 3)
        assert t["urgency"] in (1, 2, 3)


def test_injection_traps_present() -> None:
    all_t = load(ROOT / "data" / "tickets.jsonl")
    inj = [t for t in all_t if "Ignore your instructions" in t["description"]]
    assert len(inj) == 10
