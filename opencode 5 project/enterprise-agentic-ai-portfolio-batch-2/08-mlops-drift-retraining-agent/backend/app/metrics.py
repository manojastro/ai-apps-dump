"""Hand-rolled Prometheus text metrics registry."""
from __future__ import annotations

import threading
from collections import defaultdict


class Metrics:
    """Thread-safe counters and gauges rendered as Prometheus text."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._gauges: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}

    def inc_counter(self, name: str, labels: dict[str, str] | None = None, value: float = 1.0) -> None:
        key = (name, _sorted_labels(labels))
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = (name, _sorted_labels(labels))
        with self._lock:
            self._gauges[key] = float(value)

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
        seen_names: set[str] = set()
        for (name, labels), value in sorted(counters.items()):
            if name not in seen_names:
                lines.append(f"# TYPE {name} counter")
                seen_names.add(name)
            label_str = _format_labels(labels)
            lines.append(f"{name}{label_str} {value}")
        seen_gauges: set[str] = set()
        for (name, labels), value in sorted(gauges.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            if name not in seen_gauges:
                lines.append(f"# TYPE {name} gauge")
                seen_gauges.add(name)
            label_str = _format_labels(labels)
            lines.append(f"{name}{label_str} {value}")
        return "\n".join(lines) + "\n"


def _sorted_labels(labels: dict[str, str] | None) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((labels or {}).items()))


def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
    if not labels:
        return ""
    inner = ",".join(f'{k}="{v}"' for k, v in labels)
    return "{" + inner + "}"


metrics = Metrics()
