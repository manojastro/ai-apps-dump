"""Make and apply unified diffs (pure Python, strict context matching, no external `patch`)."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path


class PatchError(RuntimeError):
    pass


def make_unified_diff(old_files: dict[str, str], new_files: dict[str, str]) -> str:
    chunks = []
    for path in sorted(new_files):
        old = old_files.get(path, "")
        new = new_files[path]
        if old == new:
            continue
        chunks.append(
            "".join(
                difflib.unified_diff(
                    old.splitlines(keepends=True),
                    new.splitlines(keepends=True),
                    fromfile=f"a/{path}" if path in old_files else "/dev/null",
                    tofile=f"b/{path}",
                )
            )
        )
    return "".join(c if c.endswith("\n") else c + "\n" for c in chunks)


@dataclass
class _Hunk:
    old_start: int
    lines: list[str] = field(default_factory=list)


@dataclass
class _FilePatch:
    old_path: str | None
    new_path: str
    hunks: list[_Hunk] = field(default_factory=list)


_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def parse_unified_diff(diff: str) -> list[_FilePatch]:
    files: list[_FilePatch] = []
    lines = diff.splitlines(keepends=True)
    i = 0
    while i < len(lines):
        if lines[i].startswith("--- "):
            old = lines[i][4:].strip().split("\t")[0]
            if i + 1 >= len(lines) or not lines[i + 1].startswith("+++ "):
                raise PatchError("malformed diff: '---' without '+++'")
            new = lines[i + 1][4:].strip().split("\t")[0]
            fp = _FilePatch(None if old == "/dev/null" else old.removeprefix("a/"), new.removeprefix("b/"))
            files.append(fp)
            i += 2
            continue
        m = _HUNK.match(lines[i])
        if m:
            if not files:
                raise PatchError("hunk before file header")
            hunk = _Hunk(int(m.group(1)))
            files[-1].hunks.append(hunk)
            i += 1
            while (
                i < len(lines) and lines[i][:1] in (" ", "+", "-", "\\") and not lines[i].startswith("--- ")
            ):
                if not lines[i].startswith("\\"):
                    hunk.lines.append(lines[i])
                i += 1
            continue
        i += 1
    return files


def _apply_file(original: list[str], fp: _FilePatch) -> list[str]:
    out: list[str] = []
    pos = 0
    for h in fp.hunks:
        old_block = [ln[1:] for ln in h.lines if ln[0] in (" ", "-")]
        new_block = [ln[1:] for ln in h.lines if ln[0] in (" ", "+")]
        start = max(h.old_start - 1, 0) if old_block else h.old_start
        # Exact position first, then search nearby (offset tolerance), never fuzzy content.
        candidates = [start] + [start + d for r in range(1, 50) for d in (-r, r)]
        found = next(
            (s for s in candidates if s >= pos and original[s : s + len(old_block)] == old_block),
            None,
        )
        if found is None:
            raise PatchError(f"hunk at line {h.old_start} of {fp.new_path} does not apply")
        out += original[pos:found] + new_block
        pos = found + len(old_block)
    return out + original[pos:]


def apply_unified_diff(root: Path, diff: str) -> list[str]:
    """Apply `diff` to files under `root`. Returns touched paths. Atomic per call."""
    root = Path(root).resolve()
    staged: dict[Path, str] = {}
    for fp in parse_unified_diff(diff):
        target = (root / fp.new_path).resolve()
        if root not in target.parents:
            raise PatchError(f"path escapes sandbox: {fp.new_path}")
        original = target.read_text(encoding="utf-8").splitlines(keepends=True) if fp.old_path else []
        staged[target] = "".join(_apply_file(original, fp))
    for target, content in staged.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    return [str(p.relative_to(root)).replace("\\", "/") for p in staged]
