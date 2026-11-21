"""In-process metrics registry with Prometheus text rendering."""
from __future__ import annotations

import threading
from collections import defaultdict
from time import time


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._gauges: dict[str, float] = {}
        self._start = time()

    def incr(self, name: str, labels: dict[str, str] | None = None,
             value: float = 1.0) -> None:
        key = (name, tuple(sorted((labels or {}).items())))
        with self._lock:
            self._counters[key] += value

    def set_gauge(self, name: str, value: float) -> None:
        with self._lock:
            self._gauges[name] = value

    def render(self) -> str:
        lines: list[str] = []
        counters: dict[str, list[tuple[tuple[str, str], ...], float]] = defaultdict(list)
        with self._lock:
            for (name, labels), value in self._counters.items():
                counters[name].append((labels, value))
            gauges = dict(self._gauges)
        for name, entries in sorted(counters.items()):
            lines.append(f"# TYPE {name} counter")
            for labels, value in entries:
                label_str = ""
                if labels:
                    pairs = ",".join(f'{k}="{v}"' for k, v in labels)
                    label_str = "{" + pairs + "}"
                lines.append(f"{name}{label_str} {value}")
        for name, value in sorted(gauges.items()):
            lines.append(f"# TYPE {name} gauge")
            lines.append(f"{name} {value}")
        lines.append("# TYPE process_uptime_seconds gauge")
        lines.append(f"process_uptime_seconds {int(time() - self._start)}")
        return "\n".join(lines) + "\n"

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            data = {f"{n}|{dict(l)}": v for (n, l), v in self._counters.items()}
            data.update(self._gauges)
        return data


METRICS = Metrics()
