"""Versioned prompt files. Each file has a front-matter block, a '## system' and a '## user' section."""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROMPT_DIR = Path(__file__).resolve().parent
_SECTION = re.compile(r"^## (system|user)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class PromptTemplate:
    name: str
    version: str
    system: str
    user: str

    def render_user(self, **values: str) -> str:
        out = self.user
        for k, v in values.items():
            out = out.replace("{{" + k + "}}", v)
        return out.strip() + "\n"


def available_versions(name: str = "explain") -> list[str]:
    return sorted(p.stem.split("_", 1)[1] for p in PROMPT_DIR.glob(f"{name}_v*.md"))


@lru_cache(maxsize=16)
def load_prompt(version: str, name: str = "explain") -> PromptTemplate:
    path = PROMPT_DIR / f"{name}_{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"prompt {name}_{version}.md not found; have {available_versions(name)}")
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    parts = _SECTION.split(text)
    sections = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts) - 1, 2)}
    return PromptTemplate(name=name, version=version, system=sections["system"], user=sections["user"])
