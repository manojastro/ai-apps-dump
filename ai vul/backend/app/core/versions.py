"""Version comparison and NVD CPE range matching.

Software versions in the wild are messy ("8.9p1", "2.0-beta9", "5.15.0-91", "2023.11.3").
We tokenise into alternating numeric / alphabetic parts and compare token by token:
numbers numerically, text lexically, and a pre-release marker (alpha/beta/rc) sorts before
the release. This is intentionally simple, deterministic and unit tested.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import total_ordering
from typing import Any

_TOKEN = re.compile(r"\d+|[a-zA-Z]+")
_PRE_RELEASE = {"alpha", "a", "beta", "b", "rc", "pre", "preview", "dev", "snapshot"}


@total_ordering
class Version:
    def __init__(self, raw: str) -> None:
        self.raw = raw.strip()
        tokens: list[tuple[int, Any]] = []
        for tok in _TOKEN.findall(self.raw.lower()):
            if tok.isdigit():
                tokens.append((2, int(tok)))
            elif tok in _PRE_RELEASE:
                tokens.append((0, tok))  # pre-release sorts below "nothing"
            else:
                tokens.append((1, tok))
        self.tokens = tokens

    @staticmethod
    def _missing(other: tuple[int, Any]) -> tuple[int, Any]:
        # "2.15" vs "2.15.0" -> missing numeric part is 0; "9.8" vs "9.8p1" -> missing suffix
        # is an empty string (sorts first); "2.0" vs "2.0-beta9" -> release beats pre-release.
        return (2, 0) if other[0] == 2 else (1, "")

    def _cmp(self, other: Version) -> int:
        a, b = self.tokens, other.tokens
        for i in range(max(len(a), len(b))):
            x = a[i] if i < len(a) else self._missing(b[i])
            y = b[i] if i < len(b) else self._missing(a[i])
            if x == y:
                continue
            if x[0] != y[0]:
                return -1 if x[0] < y[0] else 1
            return -1 if x[1] < y[1] else 1
        return 0

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Version) and self._cmp(other) == 0

    def __lt__(self, other: Version) -> bool:
        return self._cmp(other) < 0

    def __hash__(self) -> int:
        tokens = list(self.tokens)
        while len(tokens) > 1 and tokens[-1] == (2, 0):
            tokens.pop()
        return hash(tuple(tokens))

    def __repr__(self) -> str:
        return f"Version({self.raw!r})"


def parse_cpe(criteria: str) -> dict[str, str]:
    parts = criteria.split(":")
    names = ["cpe", "spec", "part", "vendor", "product", "version", "update", "edition", "language", "sw_edition"]
    return {name: (parts[i] if i < len(parts) else "*") for i, name in enumerate(names)}


@dataclass(frozen=True)
class RangeMatch:
    matched: bool
    criteria: str | None = None
    reason: str = ""
    fixed_version: str | None = None  # first non-affected version when NVD provides versionEndExcluding
    upper_bound_inclusive: str | None = None  # affected through this version (inclusive)


def _edition_ok(range_edition: str, sw_edition: str | None) -> bool:
    if range_edition in ("*", ""):
        return True
    if range_edition == "-":
        return sw_edition in (None, "", "-")
    return (sw_edition or "").lower() == range_edition.lower()


def match_cpe_ranges(
    ranges: list[dict[str, Any]], vendor: str, product: str, version: str, sw_edition: str | None = None
) -> RangeMatch:
    """Return whether ``vendor:product@version`` falls into any NVD affected range."""
    try:
        v = Version(version)
    except Exception:  # pragma: no cover - defensive
        return RangeMatch(False, reason="unparseable version")
    for r in ranges:
        if (r.get("vendor") or "").lower() != vendor.lower() or (r.get("product") or "").lower() != product.lower():
            continue
        cpe = parse_cpe(r.get("criteria", ""))
        if not _edition_ok(cpe["sw_edition"], sw_edition):
            continue
        exact = r.get("version")
        if exact not in (None, "*", "-"):
            update = cpe["update"]
            candidate = exact + (update if update not in ("*", "-", "") else "")
            if Version(candidate) == v or (update in ("*", "-", "") and Version(exact) == v):
                return RangeMatch(True, r.get("criteria"), f"exact affected version {candidate}")
            continue
        lo_inc, lo_exc = r.get("version_start_including"), r.get("version_start_excluding")
        hi_exc, hi_inc = r.get("version_end_excluding"), r.get("version_end_including")
        if not any([lo_inc, lo_exc, hi_exc, hi_inc]):
            continue  # wildcard without bounds is too broad to assert
        if lo_inc and v < Version(lo_inc):
            continue
        if lo_exc and v <= Version(lo_exc):
            continue
        if hi_exc and v >= Version(hi_exc):
            continue
        if hi_inc and v > Version(hi_inc):
            continue
        bounds = []
        if lo_inc:
            bounds.append(f">= {lo_inc}")
        if lo_exc:
            bounds.append(f"> {lo_exc}")
        if hi_exc:
            bounds.append(f"< {hi_exc}")
        if hi_inc:
            bounds.append(f"<= {hi_inc}")
        return RangeMatch(
            True,
            r.get("criteria"),
            f"version {version} within affected range ({', '.join(bounds)})",
            fixed_version=hi_exc,
            upper_bound_inclusive=hi_inc,
        )
    return RangeMatch(False, reason="no affected range matched")
