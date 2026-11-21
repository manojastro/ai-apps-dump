"""Load and query the versioned taxonomy."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

TAXONOMY_DIR = Path(__file__).parent


@dataclass(frozen=True)
class TaxonomyItem:
    code: str
    label: str
    statement: str
    unit: str
    period: str
    sign: str
    section: str
    total: bool
    order: int
    synonyms: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Taxonomy:
    version: str
    items: tuple[TaxonomyItem, ...]

    def by_code(self) -> dict[str, TaxonomyItem]:
        return {i.code: i for i in self.items}

    def for_statement(self, statement_type: str) -> list[TaxonomyItem]:
        return [i for i in self.items if i.statement == statement_type]

    def get(self, code: str) -> TaxonomyItem | None:
        return self.by_code().get(code)


def normalize_label(label: str) -> str:
    s = label.lower()
    s = s.replace("&", " and ")
    s = re.sub(r"\(note\s*\w+\)", " ", s)
    s = re.sub(r"^\s*(\(?[a-z]\)|\(?[ivx]+\)|\d+\.|[a-z]\.)\s+", " ", s)  # (a) (iv) 1. a.
    s = re.sub(r"^\s*(less|add)\s*:\s*", " ", s)
    s = re.sub(r"[/\\(),.:;'’\-–—]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


@lru_cache
def load_taxonomy(version: str = "spreadlens-tax-1.0") -> Taxonomy:
    path = TAXONOMY_DIR / "taxonomy_v1.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data["version"] != version:
        raise ValueError(f"taxonomy version {version} not found")
    items = tuple(
        TaxonomyItem(
            code=i["code"], label=i["label"], statement=i["statement"], unit=i["unit"], period=i["period"],
            sign=i["sign"], section=i["section"], total=bool(i["total"]), order=int(i["order"]),
            synonyms=tuple(normalize_label(s) for s in i.get("synonyms", [])) + (normalize_label(i["label"]),),
        )
        for i in data["items"]
    )
    codes = [i.code for i in items]
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate taxonomy codes")
    return Taxonomy(version=data["version"], items=items)
